"""This module contains the types related to WhatsApp Flows."""

from __future__ import annotations

import abc
import dataclasses
import datetime
import json
import logging
import pathlib
from typing import Iterable, TYPE_CHECKING, Any, BinaryIO, Literal, TypeAlias

from .. import utils
from .base_update import BaseUserUpdate  # noqa
from .others import (
    WhatsAppBusinessAccount,
    FacebookApplication,
    MessageType,
    Metadata,
    User,
    ReplyToMessage,
)

if TYPE_CHECKING:
    from ..client import WhatsApp

_logger = logging.getLogger(__name__)

__all__ = [
    "FlowCompletion",
    "FlowRequest",
    "FlowResponse",
    "FlowResponseError",
    "FlowRequestCannotBeDecrypted",
    "FlowRequestSignatureAuthenticationFailed",
    "FlowTokenNoLongerValid",
    "FlowCategory",
    "FlowDetails",
    "FlowMetricName",
    "FlowMetricGranularity",
    "FlowStatus",
    "FlowPreview",
    "FlowValidationError",
    "FlowAsset",
    "FlowJSON",
    "Screen",
    "ScreenData",
    "Layout",
    "LayoutType",
    "Form",
    "DataKey",
    "FormRef",
    "TextHeading",
    "TextSubheading",
    "TextBody",
    "TextCaption",
    "RichText",
    "FontWeight",
    "TextInput",
    "InputType",
    "TextArea",
    "CheckboxGroup",
    "RadioButtonsGroup",
    "Footer",
    "OptIn",
    "Dropdown",
    "EmbeddedLink",
    "DatePicker",
    "Image",
    "PhotoPicker",
    "PhotoSource",
    "DocumentPicker",
    "ScaleType",
    "If",
    "Switch",
    "DataSource",
    "Action",
    "FlowActionType",
    "FlowRequestActionType",
    "ActionNext",
    "ActionNextType",
]


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class FlowCompletion(BaseUserUpdate):
    """
    A flow completion message. This update arrives when a user completes a flow.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/gettingstarted/receiveflowresponse>`_.

    Attributes:
        id: The message ID (If you want to reply to the message, use ``message_id_to_reply`` instead).
        metadata: The metadata of the message (to which phone number it was sent).
        type: The message type (Always ``MessageType.INTERACTIVE``).
        from_user: The user who sent the message.
        timestamp: The timestamp when the message was sent.
        reply_to_message: The message to which this message is a reply to.
        body: The body of the message.
        token: The token of the flow. can be ``None`` in some cases :|
        response: The response from the flow.
    """

    id: str
    type: MessageType
    metadata: Metadata
    from_user: User
    timestamp: datetime.datetime
    reply_to_message: ReplyToMessage | None
    body: str
    token: str | None
    response: dict[str, Any]

    @classmethod
    def from_update(cls, client: WhatsApp, update: dict) -> FlowCompletion:
        msg = (value := update["entry"][0]["changes"][0]["value"])["messages"][0]
        response: dict = json.loads(msg["interactive"]["nfm_reply"]["response_json"])
        try:
            flow_token = response.pop("flow_token")
        except KeyError:
            flow_token = None
            _logger.warning(
                "A flow completion message without flow token is received, This is a known issue on iOS devices."
            )

        return cls(
            _client=client,
            raw=update,
            id=msg["id"],
            type=MessageType(msg["type"]),
            metadata=Metadata.from_dict(value["metadata"]),
            from_user=User.from_dict(value["contacts"][0]),
            timestamp=datetime.datetime.fromtimestamp(int(msg["timestamp"])),
            reply_to_message=ReplyToMessage.from_dict(msg["context"]),
            body=msg["interactive"]["nfm_reply"]["body"],
            token=flow_token,
            response=response,
        )


class FlowRequestActionType(utils.StrEnum):
    """
    The type the action that triggered the :class:`FlowRequest`.

    Attributes:
        INIT: if the request is triggered when opening the flow (The :class:`FlowButton` was sent with flow_action_type set to ``FlowActionType.DATA_EXCHANGE``)
        BACK: if the request is triggered when pressing back (The screen has ``refresh_on_back`` set to ``True``)
        DATA_EXCHANGE: if the request is triggered when submitting the screen (And the :class:`Action` name is ``FlowActionType.DATA_EXCHANGE``)
        PING: if the request is triggered by a health check (Ignore this requests by leaving ``handle_health_check`` to ``True``)
        NAVIGATE: if the :class:`FlowButton` sent with ``FlowActionType.NAVIGATE`` and the screen is not in the routing model (the request will contain an error)
    """

    INIT = "INIT"
    BACK = "BACK"
    DATA_EXCHANGE = "data_exchange"
    PING = "ping"
    NAVIGATE = "navigate"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def _missing_(cls, value):
        _logger.warning(
            "Unknown flow request action type: %s. Defaulting to UNKNOWN.", value
        )
        return cls.UNKNOWN


@dataclasses.dataclass(slots=True, frozen=True, kw_only=True)
class FlowRequest:
    """
    Represents a flow data exchange request. This request is sent to the flow endpoint when a user interacts with a
    flow and perform an :class:`Action` that trigger a data exchange.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/guides/implementingyourflowendpoint#data_exchange_request>`_.

    Attributes:
        version: The version of the data exchange.
        flow_token: The flow token used to create the flow. ``None`` if action is ``FlowRequestActionType.PING``.
        action: The action that triggered the request.
        screen: The screen that triggered the request. ``None`` if action is ``FlowRequestActionType.PING``.
        data: The data sent from the screen. ``None`` if action is ``FlowRequestActionType.PING`` and optional if action is
         ``FlowRequestActionType.BACK`` or ``FlowRequestActionType.INIT``.
        raw: The raw data of the request.
        raw_encrypted: The raw-encrypted data of the request.
    """

    version: str
    action: FlowRequestActionType
    flow_token: str | None = None
    screen: str | None = None
    data: dict[str, Any] | None = None
    raw: dict[str, Any] = dataclasses.field(repr=False, hash=False, compare=False)
    raw_encrypted: dict[str, str] = dataclasses.field(
        repr=False, hash=False, compare=False
    )

    def respond(
        self,
        screen: str | None = None,
        data: dict[
            str,
            str
            | int
            | float
            | bool
            | dict
            | DataSource
            | Iterable[str | int | float | bool | dict | DataSource],
        ] = None,
        error_message: str | None = None,
        close_flow: bool = False,
        flow_token: str | None = None,
        version: str | None = None,
    ) -> FlowResponse:
        """
        Create a response for this request.

        - A shortcut for initializing a :class:`FlowResponse` with the same version as this request.

        Example:

            >>> wa = WhatsApp(business_private_key="...", ...)
            >>> @wa.on_flow_request("/my-flow-endpoint")
            ... def my_flow_endpoint(_: WhatsApp, req: FlowRequest) -> FlowResponse:
            ...     return req.respond(
            ...         screen="SCREEN_ID",
            ...         data={"key": "value"},
            ...     )

        Args:
            screen: The screen to display (if ``close_flow`` is ``False``).
            data: The data to send to the screen or to add to flow completion message (default to empty dict).
            error_message: This will redirect the user to ``screen`` and will trigger a snackbar error with the error_message present (if ``close_flow`` is ``False``).
            close_flow: Whether to close the flow or just navigate to the screen.
            flow_token: The flow token to close the flow (if ``close_flow`` is ``True``).
            version: The version of the data exchange (Default to the request version).
        """
        return FlowResponse(
            version=version or self.version,
            data=data or {},
            screen=screen,
            error_message=error_message,
            flow_token=flow_token,
            close_flow=close_flow,
        )

    @classmethod
    def from_dict(cls, data: dict, raw_encrypted: dict):
        return cls(
            version=data["version"],
            action=FlowRequestActionType(data["action"]),
            flow_token=data.get("flow_token"),
            screen=data.get("screen") or None,  # can be empty string
            data=data.get("data") or None,  # can be empty dict
            raw=data,
            raw_encrypted=raw_encrypted,
        )

    @property
    def has_error(self) -> bool:
        """
        Check if the request has an error.
        When True, if flow endpoint register with ``acknowledge_errors=True``,
        pywa will acknowledge the error and ignore the response from the callback. The callback still be called.
        """
        return self.data and any(
            key in self.data for key in ("error_message", "error_key")
        )

    @property
    def is_health_check(self) -> bool:
        """
        Check if the request is a health check.
        When True, if flow endpoint register with ``handle_health_check=True``,
        pywa will not call the callback and will return a health check response.
        """
        return self.action == FlowRequestActionType.PING


@dataclasses.dataclass(slots=True, kw_only=True)
class FlowResponse:
    """
    Represents a flow data exchange response. This response is sent to the flow endpoint to determine the next screen
    to display or to close the flow. You should return this response from your flow endpoint callback.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/guides/implementingyourflowendpoint#data_exchange_request>`_.
    - Use the :meth:`FlowRequest.respond` method to create a response for a request with the same version.

    Example:

        >>> from pywa import WhatsApp
        >>> from pywa.types import FlowResponse

        >>> wa = WhatsApp(business_private_key="...", ...)
        >>> @wa.on_flow_request("/my-flow-endpoint")
        ... def my_flow_endpoint(_: WhatsApp, req: FlowRequest) -> FlowResponse:
        ...     return req.respond(
        ...         screen="SCREEN_ID",
        ...         data={"key": "value"},
        ...     )

    Attributes:
        version: The version of the data exchange (You can use the same version as the request (``request.version``)).
        screen: The screen to display (if the flow is not closed).
        data: The data to send to the screen or to add to flow completion message (default to empty dict).
        error_message: This will redirect the user to ``screen`` and will trigger a snackbar error with the error_message present (if the flow is not closed).
        flow_token: The flow token to close the flow (if ``close_flow`` is ``True``).
        close_flow: Whether to close the flow or just navigate to the screen.
    """

    version: str
    data: dict[
        str,
        str
        | int
        | float
        | bool
        | dict
        | DataSource
        | Iterable[str | int | float | bool | dict | DataSource],
    ] = dataclasses.field(default_factory=dict)
    screen: str | None = None
    error_message: str | None = None
    flow_token: str | None = None
    close_flow: bool = False

    def __post_init__(self):
        if not self.close_flow and not self.screen:
            raise ValueError(
                "When the response not close the flow, the screen must be provided."
            )
        if self.close_flow:
            if not self.flow_token:
                raise ValueError(
                    "When the response close the flow, the flow token must be provided."
                )
            if self.screen:
                raise ValueError(
                    "When the response close the flow, no need to provide the screen."
                )
            if self.error_message:
                raise ValueError(
                    "When the response close the flow, message error is not supported."
                )

    def to_dict(self) -> dict[str, str | dict]:
        data = self.data.copy()
        if not self.close_flow and self.error_message:
            data["error_message"] = self.error_message
        for key, val in data.items():
            if isinstance(val, DataSource):
                data[key] = val.to_dict()
            elif isinstance(val, Iterable) and not isinstance(val, (str, bytes)):
                data[key] = [
                    v.to_dict() if isinstance(v, DataSource) else v for v in val
                ]
        return {
            "version": self.version,
            "screen": self.screen if not self.close_flow else "SUCCESS",
            "data": data
            if not self.close_flow
            else {
                "extension_message_response": {
                    "params": {"flow_token": self.flow_token, **data}
                }
            },
        }


class FlowResponseError(Exception):
    """
    Base class for all flow response errors


    - Subclass this exception to return or raise from the flow endpoint callback (@wa.on_flow_request).
    - Override the ``status_code`` attribute to set the status code of the response.
    - Override the ``body`` attribute to set the body of the response (optional).
    """

    status_code: int
    body: dict | None = None


class FlowRequestCannotBeDecrypted(FlowResponseError):
    """
    - The payload cannot be decrypted due to a private key being updated by your business.

    - This error is returned automatically by pywa when the request cannot be decrypted.
      The exception from the decryption function will still be logged.

    - The WhatsApp client will re-fetch a public key and re-send the request.
      If the request fails, an error modal appears with an acknowledge button which directs the user back
      to your chat thread.
    """

    status_code = 421


class FlowRequestSignatureAuthenticationFailed(FlowResponseError):
    """
    This exception need to be returned or raised from the flow endpoint callback when the request signature authentication fails.

    - A generic error will be shown on the client.
    """

    status_code = 432


class FlowTokenNoLongerValid(FlowResponseError):
    """
    This exception need to be returned or raised from the flow endpoint callback when the Flow token is no longer valid.

    Example:

        >>> from pywa.types.flows import FlowTokenNoLongerValid
        >>> wa = WhatsApp(...)
        >>> @wa.on_flow_request("/my-flow-endpoint")
        ... def my_flow_endpoint(wa: WhatsApp, req: FlowRequest) -> FlowResponse:
        ...     if req.flow_token == "123":  # you see the token is no longer valid
        ...         # wa.send_message(..., buttons=FlowButton(...))  # resend the flow?
        ...         raise FlowTokenNoLongerValid(error_message='Open the flow again to continue.')
        ...    ...

    - The layout will be closed and the :class:`FlowButton` will be disabled for the user.
    - You can send a new message to the user generating a new Flow token.
    - This action may be used to prevent users from initiating the same Flow again.
    - You are able to set an error message to display to the user. e.g. “The order has already been placed”
    """

    status_code = 427

    def __init__(self, error_message: str):
        self.body = {"error_msg": error_message}


class FlowStatus(utils.StrEnum):
    """
    The status of the flow

    Attributes:
        DRAFT: This is the initial status. The Flow is still under development.
         The Flow can only be sent with "mode": "draft" for testing.
        PUBLISHED: The Flow has been marked as published by the developer so now it can be sent to customers.
         This Flow cannot be deleted or updated afterwards.
        DEPRECATED: The developer has marked the Flow as deprecated (since it cannot be deleted after publishing).
         This prevents sending and opening the Flow, to allow the developer to retire their endpoint.
         Deprecated Flows cannot be deleted or deprecated.
        BLOCKED: Monitoring detected that the endpoint is unhealthy and set the status to Blocked.
         The Flow cannot be sent or opened in this state; the developer needs to fix the endpoint to get it back to
         Published state (more details in Flows Health and Monitoring).
        THROTTLED: Monitoring detected that the endpoint is unhealthy and set the status to Throttled.
         Flows with throttled status can be opened, however only 10 messages of the Flow could be sent per hour.
         The developer needs to fix the endpoint to get it back to the PUBLISHED state
         (more details in Flows Health and Monitoring
         on `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/qualmgmtwebhook>`_).
    """

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    DEPRECATED = "DEPRECATED"
    BLOCKED = "BLOCKED"
    THROTTLED = "THROTTLED"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def _missing_(cls, value):
        _logger.warning("Unknown flow status: %s. Defaulting to UNKNOWN.", value)
        return cls.UNKNOWN


class FlowCategory(utils.StrEnum):
    """
    The category of the flow

    Attributes:
        SIGN_UP: Sign up
        SIGN_IN: Sign in
        APPOINTMENT_BOOKING: Appointment booking
        LEAD_GENERATION: Lead generation
        CONTACT_US: Contact us
        CUSTOMER_SUPPORT: Customer support
        SURVEY: Survey
        OTHER: Other
    """

    SIGN_UP = "SIGN_UP"
    SIGN_IN = "SIGN_IN"
    APPOINTMENT_BOOKING = "APPOINTMENT_BOOKING"
    LEAD_GENERATION = "LEAD_GENERATION"
    CONTACT_US = "CONTACT_US"
    CUSTOMER_SUPPORT = "CUSTOMER_SUPPORT"
    SURVEY = "SURVEY"
    OTHER = "OTHER"

    @classmethod
    def _missing_(cls, value):
        _logger.warning("Unknown flow category: %s. Defaulting to OTHER.", value)
        return cls.OTHER


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class FlowValidationError(Exception, utils.FromDict):
    """
    Represents a validation error of a :class:`FlowJSON`.

    Attributes:
        error: The error code.
        error_type: The type of the error.
        message: The error message.
        line_start: The start line of the error.
        line_end: The end line of the error.
        column_start: The start column of the error.
        column_end: The end column of the error.
    """

    error: str
    error_type: str
    message: str
    line_start: int
    line_end: int
    column_start: int
    column_end: int


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class FlowPreview:
    """
    Represents the preview of a flow.

    Attributes:
        url: The URL to the preview.
        expires_at: The expiration date of the preview.
    """

    url: str
    expires_at: datetime.datetime

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            url=data["preview_url"],
            expires_at=datetime.datetime.strptime(
                data["expires_at"], "%Y-%m-%dT%H:%M:%S%z"
            ),
        )


@dataclasses.dataclass(slots=True, kw_only=True)
class FlowDetails:
    """
    Represents the details of a flow.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowsapi#details>`_.

    Attributes:
        id: The unique ID of the Flow.
        name: The user-defined name of the Flow which is not visible to users.
        status: The status of the flow.
        updated_at: The last time the flow was updated (name, categories, endpoint_uri, json, etc.).
        json_version: The version specified by the developer in the Flow JSON asset uploaded.
        data_api_version: The version of the Data API specified by the developer in the Flow JSON asset uploaded. Only for Flows with an Endpoint.
        categories: The categories of the flow.
        validation_errors: The validation errors of the flow (All errors must be fixed before the Flow can be published).
        endpoint_uri: The URL of the WA Flow Endpoint specified by the developer via API or in the Builder UI (Was ``data_channel_uri`` before v19.0).
        preview: The URL to the web preview page to visualize the flow and its expiry time.
        whatsapp_business_account: The WhatsApp Business Account which owns the Flow.
        application: The Facebook developer application used to create the Flow initially.
        health_status: A summary of the Flows health status.
    """

    _client: WhatsApp = dataclasses.field(repr=False, hash=False, compare=False)
    id: str
    name: str
    status: FlowStatus
    json_version: str | None
    data_api_version: str | None
    categories: tuple[FlowCategory, ...]
    validation_errors: tuple[FlowValidationError, ...] | None
    endpoint_uri: str | None
    preview: FlowPreview | None
    whatsapp_business_account: WhatsAppBusinessAccount | None
    application: FacebookApplication | None
    updated_at: datetime.datetime | None = None
    health_status: dict | None = None

    @classmethod
    def from_dict(cls, data: dict, client: WhatsApp) -> FlowDetails:
        return cls(
            _client=client,
            id=data["id"],
            name=data["name"],
            status=FlowStatus(data["status"]),
            categories=tuple(FlowCategory(c) for c in data["categories"]),
            validation_errors=tuple(
                FlowValidationError.from_dict(e) for e in data["validation_errors"]
            )
            or None,
            json_version=data.get("json_version"),
            data_api_version=data.get("data_api_version"),
            endpoint_uri=data.get("endpoint_uri")
            or data.get("data_channel_uri"),  # data_channel_uri removed at v19.0
            preview=FlowPreview.from_dict(data["preview"])
            if data.get("preview")
            else None,
            whatsapp_business_account=WhatsAppBusinessAccount.from_dict(
                data["whatsapp_business_account"]
            )
            if data.get("whatsapp_business_account")
            else None,
            application=FacebookApplication.from_dict(data["application"])
            if data.get("application")
            else None,
            updated_at=datetime.datetime.strptime(
                data["updated_at"], "%Y-%m-%dT%H:%M:%S%z"
            ),
            health_status=data.get("health_status"),
        )

    def publish(self) -> bool:
        """
        Update the status of this flow to ``FlowStatus.PUBLISHED``.
            - A shortcut for :meth:`pywa.client.WhatsApp.publish_flow`.

        - This action is not reversible.
        - The Flow and its assets become immutable once published.
        - To update the Flow after that, you must create a new Flow. You specify the existing Flow ID as the clone_flow_id parameter while creating to copy the existing flow.

            You can publish your Flow once you have ensured that:

            - All validation errors and publishing checks have been resolved.
            - The Flow meets the design principles of WhatsApp Flows
            - The Flow complies with WhatsApp Terms of Service, the WhatsApp Business Messaging Policy and, if applicable, the WhatsApp Commerce Policy

        Returns:
            Whether the flow was published.

        Raises:
            FlowPublishingError: If this flow has validation errors or not all publishing checks have been resolved.
        """
        if self._client.publish_flow(self.id):
            self.status = FlowStatus.PUBLISHED
            return True
        return False

    def delete(self) -> bool:
        """
        When the flow is in ``FlowStatus.DRAFT`` status, you can delete it.
            - A shortcut for :meth:`pywa.client.WhatsApp.delete_flow`.

        Returns:
            Whether the flow was deleted.

        Raises:
            FlowDeletingError: If this flow is already published.
        """
        if self._client.delete_flow(self.id):
            self.status = FlowStatus.DEPRECATED  # there is no `DELETED` status
            return True
        return False

    def deprecate(self) -> bool:
        """
        When the flow is in ``FlowStatus.PUBLISHED`` status, you can only deprecate it.
            - A shortcut for :meth:`pywa.client.WhatsApp.deprecate_flow`.

        Returns:
            Whether the flow was deprecated.

        Raises:
            FlowDeprecatingError: If this flow is not published or already deprecated.
        """
        if self._client.deprecate_flow(self.id):
            self.status = FlowStatus.DEPRECATED
            return True
        return False

    def get_assets(self) -> tuple[FlowAsset, ...]:
        """
        Get all assets attached to this flow.
            - A shortcut for :meth:`pywa.client.WhatsApp.get_flow_assets`.

        Returns:
            The assets of the flow.
        """
        return self._client.get_flow_assets(self.id)

    def update_metadata(
        self,
        name: str | None = None,
        categories: Iterable[FlowCategory | str] | None = None,
        endpoint_uri: str | None = None,
        application_id: int | None = None,
    ) -> bool:
        """
        Update the metadata of this flow.
            - A shortcut for :meth:`pywa.client.WhatsApp.update_flow_metadata`.

        Args:
            name: The name of the flow (optional).
            categories: The new categories of the flow (optional).
            endpoint_uri: The URL of the FlowJSON Endpoint. Starting from FlowJSON 3.0 this property should be
             specified only gere. Do not provide this field if you are cloning a FlowJSON with version below 3.0.
            application_id: The ID of the Meta application which will be connected to the Flow. All the flows with endpoints need to have an Application connected to them.

        Example:

            >>> from pywa.types.flows import FlowCategory
            >>> wa = WhatsApp(business_account_id='1234567890', ...)
            >>> my_flows = wa.get_flows()
            >>> my_flows[0].update_metadata(
            ...     name='Feedback',
            ...     categories=[FlowCategory.SURVEY, FlowCategory.OTHER],
            ...     endpoint_uri='https://my-api-server/feedback_flow'
            ... )

        Returns:
            Whether the flow was updated.

        Raises:
            ValueError: If neither ``name``, ``categories`` or ``endpoint_uri`` is provided.
        """
        success = self._client.update_flow_metadata(
            flow_id=self.id,
            name=name,
            categories=categories,
            endpoint_uri=endpoint_uri,
            application_id=application_id,
        )
        if success:
            if name:
                self.name = name
            if categories:
                self.categories = tuple(FlowCategory(c) for c in categories)
            if endpoint_uri:
                self.endpoint_uri = endpoint_uri
        return success

    def update_json(
        self, flow_json: FlowJSON | dict | str | pathlib.Path | bytes | BinaryIO
    ) -> bool:
        """
        Update the json of this flow.
            - A shortcut for :meth:`pywa.client.WhatsApp.update_flow_json`.

        Args:
            flow_json: The new json of the flow. Can be a :class:`FlowJSON` object, :class:`dict`, json :class:`str`,
             json file path or json bytes.

        Returns:
            Whether the flow was updated.

        Raises:
            FlowUpdatingError: If the flow json is invalid or this flow is already published.
        """
        is_success, errors = self._client.update_flow_json(
            flow_id=self.id,
            flow_json=flow_json,
        )
        self.validation_errors = errors or None
        return is_success


class FlowMetricName(utils.StrEnum):
    """
    The name of the metric

    See `Available Metrics <https://developers.facebook.com/docs/whatsapp/flows/reference/metrics_api#available_metrics>`_.

    Attributes:
        ENDPOINT_REQUEST_COUNT: Flow endpoint request count.
        ENDPOINT_REQUEST_ERROR: Flow endpoint errors.
        ENDPOINT_REQUEST_ERROR_RATE: Flow endpoint request error rate.
        ENDPOINT_REQUEST_LATENCY_SECONDS_CEIL: Flow endpoint latency in seconds.
        ENDPOINT_AVAILABILITY: Flow endpoint request error rate.
    """

    ENDPOINT_REQUEST_COUNT = "ENDPOINT_REQUEST_COUNT"
    ENDPOINT_REQUEST_ERROR = "ENDPOINT_REQUEST_ERROR"
    ENDPOINT_REQUEST_ERROR_RATE = "ENDPOINT_REQUEST_ERROR_RATE"
    ENDPOINT_REQUEST_LATENCY_SECONDS_CEIL = "ENDPOINT_REQUEST_LATENCY_SECONDS_CEIL"
    ENDPOINT_AVAILABILITY = "ENDPOINT_AVAILABILITY"


class FlowMetricGranularity(utils.StrEnum):
    """
    The granularity of the metric

    Attributes:
        DAY: Daily granularity.
        HOUR: Hourly granularity.
        LIFETIME: Lifetime granularity.
    """

    DAY = "DAY"
    HOUR = "HOUR"
    LIFETIME = "LIFETIME"


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class FlowAsset:
    """
    Represents an asset in a flow.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowsapi#asset-list>`_.

    Attributes:
        name: The name of the asset (e.g. ``"flow.json"``).
        type: The type of the asset (e.g. ``"FLOW_JSON"``).
        url: The URL to the asset.
    """

    name: str
    type: str
    url: str

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            name=data["name"],
            type=data["asset_type"],
            url=data["download_url"],
        )


_UNDERSCORE_FIELDS = {
    "routing_model",
    "data_api_version",
    "data_channel_uri",
    "refresh_on_back",
}

_SKIP_KEYS = {
    "init_value",  # Default value copied to Form.init_values
    "error_message",  # Error message copied to Form.error_messages
}


@dataclasses.dataclass(slots=True, kw_only=True)
class FlowJSON:
    """
    Represents a WhatsApp Flow JSON.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson>`_.

    Attributes:
        screens: The screens of the flow (Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#screens>`_).
        version: The Flow JSON version. (Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/versioning>`_).
        data_api_version: The version to use during communication with the WhatsApp Flows Data Endpoint. Use ``utils.Version.FLOW_DATA_API`` to get the latest version
        routing_model: Defines the rules for the screen by limiting the possible state transition. (Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#routing-model>`_).
        data_channel_uri: The endpoint to use to communicate with your server (When using v3.0 or higher, this field need to be set via :meth:`WhatsApp.update_flow_metadata`).
    """

    screens: Iterable[Screen]
    version: str | float | Literal[utils.Version.FLOW_JSON]
    data_api_version: str | float | Literal[utils.Version.FLOW_DATA_API] | None = None
    routing_model: dict[str, Iterable[str]] | None = None
    data_channel_uri: str | None = None

    def __post_init__(self):
        self.version = str(self.version)
        utils.Version.FLOW_JSON.validate_min_version(self.version)
        if self.data_api_version:
            self.data_api_version = str(self.data_api_version)
            utils.Version.FLOW_DATA_API.validate_min_version(self.data_api_version)

    def to_dict(self):
        return dataclasses.asdict(
            obj=self,
            dict_factory=lambda d: {
                k.replace("_", "-").rstrip("-") if k not in _UNDERSCORE_FIELDS else k: v
                for (k, v) in d
                if k not in _SKIP_KEYS and v is not None
            },
        )


@dataclasses.dataclass(slots=True, kw_only=True)
class DataSource:
    """
    The data source of a component.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#data-sources>`_.

    Example:

        >>> option_1 = DataSource(id='1', title='Option 1')
        >>> option_2 = DataSource(id='2', title='Option 2')
        >>> checkbox_group = CheckboxGroup(data_source=[option_1, option_2], ...)

    Attributes:
        id: The ID of the data source.
        title: The title of the data source. Limited to 30 characters.
        description: The description of the data source. Limited to 300 characters.
        metadata: The metadata of the data source. Limited to 20 characters.
        enabled: Whether the data source is enabled or not. Default to ``True``.
        image: The base64 encoded image of the data source. Limited to 1MB (added in v5.0).
        alt_text: The alt text of the image. (added in v5.0).
        color: 6-digit hex color code. (added in v5.0).
    """

    id: str
    title: str
    description: str | None = None
    metadata: str | None = None
    enabled: bool | None = None
    image: str | None = None
    alt_text: str | None = None
    color: str | None = None

    def to_dict(self):
        """Called when used in :class:`FlowResponse`."""
        return dataclasses.asdict(
            obj=self,
            dict_factory=lambda d: {
                k.replace("_", "-"): v for (k, v) in d if v is not None
            },
        )


@dataclasses.dataclass(slots=True, kw_only=True)
class ScreenData:
    """
    Represents a screen data that a screen should get from the previous screen or from the data endpoint.

    - You can use the ``.data_key`` property or the :class:`DataKey` to reference this data in the screen children or in the action payloads.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#dynamic-properties>`_.

    Example:

        >>> Screen(
        ...     id='START',
        ...     data=[
        ...         dynamic_welcome := ScreenData(key='welcome', example='Welcome to my store!')
        ...         is_email_required := ScreenData(key='is_email_required', example=False)
        ...     ],
        ...     layout=Layout(children=[Form(children=[
        ...         TextHeading(text=dynamic_welcome.data_key, ...),
        ...         TextInput(required=is_email_required.data_key, input_type=InputType.EMAIL, ...)
        ...     ])])
        ... )

    Attributes:
        key: The key of the data (To use later in the screen children with ``.data_key`` or with :class:`DataKey`).
        example: The example of the data that the screen should get from the previous screen or from the data endpoint (or the previous screen).
    """

    key: str
    example: (
        str
        | int
        | float
        | bool
        | dict
        | DataSource
        | Iterable[str | int | float | bool | dict | DataSource]
    )

    @property
    def data_key(self) -> DataKey:
        """
        The key for this data to use in the same screen children.
            - Use this property to reference this data in the screen children. Use the :meth:`data_key_of(screen)` to reference this data in ANOTHER screen children.
            - A shortcut for :class:`DataKey` with this key.

        Example:

            >>> FlowJSON(
            ...     screens=[
            ...         Screen(
            ...             id='START',
            ...             data=[dynamic_welcome := ScreenData(key='welcome', example='Welcome to my store!')],
            ...             layout=Layout(children=[TextHeading(text=dynamic_welcome.data_key, ...)])  # Use the data key here
            ...         )
            ...     ],
            ...     ...
            ... )
        """
        # noinspection PyTypeChecker
        return DataKey(key=self.key)

    def data_key_of(self, screen: Screen | str) -> DataKey:
        """
        The key for this data to use in ANOTHER screen children.
            - If you want to reference this data in the same screen children, use the :meth:`data_key` property.
            - A shortcut for :class:`DataKey` with this key and screen.
            - Added in v4.0.

        Example:

            >>> FlowJSON(
            ...     screens=[
            ...         start := Screen(
            ...             id='START',
            ...             data=[dynamic_welcome := ScreenData(key='welcome', example='Welcome to my store!')],
            ...             layout=Layout(children=[...])
            ...         ),
            ...         Screen(
            ...             id='END',
            ...             layout=Layout(children=[TextHeading(text=dynamic_welcome.data_key_of(start), ...)]) # Use the data key with the screen here
            ...         )
            ...     ],
            ...     ...
            ... )

        Args:
            screen: The screen id to reference this data in its children.
        """
        # noinspection PyTypeChecker
        return DataKey(key=self.key, screen=screen)


_PY_TO_JSON_TYPES = {
    str: "string",
    int: "number",
    float: "number",
    bool: "boolean",
}


@dataclasses.dataclass(slots=True, kw_only=True)
class Screen:
    """
    Represents a screen (page) in a WhatsApp flow.

    - The maximum number of components (children) per screen is 50.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#screens>`_.

    Example:

        >>> Screen(
        ...     id='START',
        ...     title='Welcome',
        ...     data=[ScreenData(key='welcome', example='Welcome to my store!')],
        ...     terminal=True,
        ...     layout=Layout(children=[Form(children=[...])]),
        ...     refresh_on_back=True
        ... )

    Attributes:
        id: Unique identifier of the screen for navigation purposes. ``SUCCESS`` is a reserved keyword and should not be
         used as a screen id.
        title: Screen level attribute that is rendered in the top navigation bar.
        data: Declaration of dynamic data that this screen should get from the previous screen or from the data endpoint.
         In the screen children and in :class:`Action` ``.payload``, you can use the ``.data_key`` or :class:`DataKey`
         to reference this data.
        terminal: Each Flow should have a terminal state where we terminate the experience and have the Flow completed.
         Multiple screens can be marked as terminal. It's mandatory to have a :class:`Footer` on the terminal screen.
        refresh_on_back: Whether to trigger a data exchange request with the data endpoint when the user presses
         the back button while on this screen (Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#additional-information-on-refresh-on-back>`_).
        layout: Associated screen UI Layout that is shown to the user (Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#layout>`_).
        success: To indicate whether terminating on that screen results in a successful flow completion.
        sensitive: This array contains the names of the fields in the screen that contain sensitive data, and should be hidden in the response summary displayed to the user. (added in v5.1)
    """

    id: str
    title: str | None = None
    data: Iterable[ScreenData] | dict[str, dict] | None = None
    terminal: bool | None = None
    success: bool | None = None
    refresh_on_back: bool | None = None
    layout: Layout
    sensitive: Iterable[str] | None = None

    def __post_init__(self):
        if not self.data or isinstance(self.data, dict):
            return

        data = {}
        for item in self.data:
            try:
                data[item.key] = dict(
                    **_get_json_type(item.example), __example__=item.example
                )
            except KeyError as e:
                raise ValueError(
                    f"Invalid example type {type(item.example)!r} for {item.key!r}. "
                    f"{e}"
                )

        self.data = data or None


def _get_json_type(
    example: str
    | int
    | float
    | bool
    | DataSource
    | Iterable[str | int | float | bool | DataSource],
) -> dict[str, str | dict[str, str]]:
    if isinstance(example, (str, int, float, bool)):
        return {"type": _PY_TO_JSON_TYPES[type(example)]}
    elif isinstance(example, (dict, DataSource)):
        return {"type": "object", "properties": _get_obj_props(example)}
    elif isinstance(example, Iterable):
        try:
            first = next(iter(example))
        except StopIteration:
            raise ValueError("At least one example is required when using Iterable")
        if isinstance(first, (str, int, float, bool)):
            return {"type": "array", "items": {"type": _PY_TO_JSON_TYPES[type(first)]}}
        elif isinstance(first, (dict, DataSource)):
            return {
                "type": "array",
                "items": {"type": "object", "properties": _get_obj_props(first)},
            }
    else:
        raise KeyError("Invalid example type")


def _get_obj_props(item: dict | DataSource):
    return {
        k: dict(type=_PY_TO_JSON_TYPES[type(v)])
        for k, v in (
            dataclasses.asdict(item).items()
            if isinstance(item, DataSource)
            else item.items()
        )
        if v is not None
    }


class LayoutType(utils.StrEnum):
    """
    The type of layout that is used to display the components.
        - Currently, only ``LayoutType.SINGLE_COLUMN`` is supported.

    Attributes:
        SINGLE_COLUMN: A single column layout.
    """

    SINGLE_COLUMN = "SingleColumnLayout"


@dataclasses.dataclass(slots=True, kw_only=True)
class Layout:
    """
    Layout is the top level component that holds the other components.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#layout>`_.
    - Before v4.0, the following components must be wrapped in a :class:`Form` and can't be used directly in the layout: :class:`TextInput`, :class:`TextArea`, :class:`CheckboxGroup`, :class:`RadioButtonsGroup`, :class:`OptIn`, :class:`Dropdown` and :class:`DatePicker`.

    Attributes:
        type: The type of layout that is used to display the components (Default: ``LayoutType.SINGLE_COLUMN``).
        children: The components that are part of the layout.
    """

    type: LayoutType = LayoutType.SINGLE_COLUMN
    children: Iterable[Form | _SUPPOERTED_COMPONENTS]


class Component(abc.ABC):
    """Base class for all components"""

    @property
    @abc.abstractmethod
    def type(self) -> ComponentType: ...

    @property
    @abc.abstractmethod
    def visible(self) -> bool | str | None: ...


class ComponentType(utils.StrEnum):
    """Internal component types"""

    FORM = "Form"
    TEXT_HEADING = "TextHeading"
    TEXT_SUBHEADING = "TextSubheading"
    TEXT_BODY = "TextBody"
    TEXT_CAPTION = "TextCaption"
    RICH_TEXT = "RichText"
    TEXT_INPUT = "TextInput"
    TEXT_AREA = "TextArea"
    CHECKBOX_GROUP = "CheckboxGroup"
    RADIO_BUTTONS_GROUP = "RadioButtonsGroup"
    FOOTER = "Footer"
    OPT_IN = "OptIn"
    DROPDOWN = "Dropdown"
    EMBEDDED_LINK = "EmbeddedLink"
    DATE_PICKER = "DatePicker"
    IMAGE = "Image"
    PHOTO_PICKER = "PhotoPicker"
    DOCUMENT_PICKER = "DocumentPicker"
    IF = "If"
    SWITCH = "Switch"


class _Ref:
    """Base class for all references"""

    def __new__(
        cls, prefix: str, field: str, screen: Screen | str | None = None
    ) -> str:
        return "${%s%s.%s}" % (
            f"screen.{screen.id if isinstance(screen, Screen) else screen}."
            if screen
            else "",
            prefix,
            field,
        )


class DataKey(_Ref):
    """
    Represents a data key (converts to ``${data.<key>}`` | ``${screen.<screen>.data.<key>}``).

    Example:

            - Hint: use the ``.data_key`` property of :class:`ScreenData` to get the data key of a screen data.
            - Hint: use the ``.data_key_of(screen)`` method of :class:`ScreenData` to get the data key from another screen.

            >>> FlowJSON(
            ...     screens=[
            ...         other := Screen(id='OTHER', data=[is_visible := ScreenData(key='is_visible', example=True)]),
            ...         Screen(
            ...             id='START',
            ...             data=[welcome := ScreenData(key='welcome', example='Welcome to my store!')],
            ...             layout=Layout(children=[
            ...                 TextHeading(
            ...                     text=welcome.data_key, # data in the same screen
            ...                     visible=is_visible.data_key_of(other) # data from other screen
            ...                 )
            ...             ])
            ...         )
            ...     ]
            ... )

            - Or if you want to use DataKey directly:

            >>> FlowJSON(
            ...     screens=[
            ...         Screen(id='OTHER', data=[ScreenData(key='welcome', example='Welcome to my store!')])
            ...         Screen(id='START', layout=Layout(children=[TextHeading(text=DataKey(key='welcome', screen='OTHER'))]))
            ...     ]
            ... )

    Args:
        key: The key to get from the :class:`Screen` .data attribute.
        screen: The screen that contains the data (needed if the data is from another screen). Added in v4.0.
    """

    def __new__(cls, key: str, screen: Screen | str | None = None):
        return super().__new__(cls, prefix="data", field=key, screen=screen)


class FormRef(_Ref):
    """
    Represents a form reference variable (converts to ``${form.<child>}`` | ``${screen.<screen>.form.<child>}``).

    Example:

        - Hint: use the ``.form_ref`` property of each component to get the form reference variable of that component.
        - Hint: use the ``.form_ref_of(screen)`` method of each component to get the form reference variable of that component with the given screen name.

        >>> FlowJSON(
        ...     screens=[
        ...         other := Screen(
        ...             id='OTHER',
        ...             layout=Layout(children=[Form(children=[email := TextInput(name='email', ...), ...])])
        ...         ),
        ...         Screen(
        ...             id='START',
        ...             layout=Layout(children=[
        ...                 phone := TextInput(name='phone', ...),
        ...                 TextBody(text=phone.form_ref, ...),  # form reference from the same screen
        ...                 TextCaption(text=email.form_ref_of(other), ...)  # form reference from another screen
        ...             ])
        ...         )
        ...     ]
        ... )

        - Or if you want to use FormRef directly:

        >>> FlowJSON(
        ...     screens=[
        ...         Screen(
        ...             id='OTHER',
        ...             layout=Layout(children=[Form(children=[email := TextInput(name='email', ...), ...])])
        ...         ),
        ...         Screen(
        ...             id='START',
        ...             layout=Layout(children=[
        ...                 phone := TextInput(name='phone', ...),
        ...                 TextBody(text=FormRef('phone')),
        ...                 TextCaption(text=FormRef('email', screen='OTHER'))
        ...             ])
        ...         )
        ...     ]
        ... )


    Args:
        child_name: The name of the :class:`Form` child to get the value from.
        screen: The name of the screen that contains the form. Added in v4.0.
    """

    def __new__(cls, child_name: str, screen: Screen | str | None = None):
        return super().__new__(cls, prefix="form", field=child_name, screen=screen)


@dataclasses.dataclass(slots=True, kw_only=True)
class Form(Component):
    """
    The form component is a container for other components that collects user input.

    - Before v4.0, the following components must be inside Form: :class:`TextInput`, :class:`TextArea`, :class:`CheckboxGroup`,
      :class:`RadioButtonsGroup`, :class:`OptIn`, :class:`Dropdown` and :class:`DatePicker`.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#forms-and-form-properties>`_.

    Attributes:
        name: The name of the form (the convention is to use ``"form"``).
        children: The components that are part of the form.
        init_values: The initial values of the form (you can use ``.init_value`` property of each component to set the
         initial value instead of setting this attribute. Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#form-configuration>`_).
        error_messages: The error messages of the form (you can use ``.error_message`` property of each component to set
         the error message instead of setting this attribute. Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#form-configuration>`_).
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.FORM, init=False, repr=False
    )
    visible: None = dataclasses.field(default=None, init=False, repr=False)
    name: str
    children: Iterable[_SUPPOERTED_COMPONENTS]
    init_values: dict[str, Any] | str | DataKey | FormRef | None = None
    error_messages: dict[str, str] | str | DataKey | FormRef | None = None

    def __post_init__(self):
        if not self.children:
            raise ValueError("At least one child is required")
        if not isinstance(self.init_values, str):
            init_values = self.init_values or {}
            for child in self.children:
                if getattr(child, "init_value", None) is not None:
                    if child.name in init_values:
                        raise ValueError(
                            f"Duplicate init value for {child.name!r} in form {self.name!r}"
                        )
                    if isinstance(self.init_values, str):
                        raise ValueError(
                            f"No need to set init value for {child.name!r} if form init values is a dynamic DataKey"
                        )
                    init_values[child.name] = child.init_value
            self.init_values = init_values or None

        if not isinstance(self.error_messages, str):
            error_messages = self.error_messages or {}
            for child in self.children:
                if getattr(child, "error_message", None) is not None:
                    if child.name in error_messages:
                        raise ValueError(
                            f"Duplicate error msg for {child.name!r} in form {self.name!r}"
                        )
                    if isinstance(self.error_messages, str):
                        raise ValueError(
                            f"No need to set error msg for {child.name!r} if form error messages is a dynamic DataKey"
                        )
                    error_messages[child.name] = child.error_message
            self.error_messages = error_messages or None


class FormComponent(Component, abc.ABC):
    """Base class for all components that must be inside a form (if FlowJSON version is below 4.0)"""

    @property
    @abc.abstractmethod
    def name(self) -> str: ...

    @property
    @abc.abstractmethod
    def label(self) -> str | DataKey | FormRef: ...

    @property
    @abc.abstractmethod
    def required(self) -> bool | str | DataKey | None: ...

    @property
    @abc.abstractmethod
    def enabled(self) -> bool | str | DataKey | None: ...

    @property
    @abc.abstractmethod
    def init_value(self) -> bool | str | DataKey | FormRef | None: ...

    @property
    def form_ref(self) -> FormRef:
        """
        The form reference variable for this component.
            - Use this when the reference is in the same screen. Use ``.form_ref_of(screen)`` when the reference is in another screen.
            - A shortcut for :class:`FormRef` with this component name.

        Example:

            >>> FlowJSON(
            ...     screens=[
            ...         Screen(
            ...             id='START',
            ...             layout=Layout(children=[
            ...                 Form(children=[
            ...                     text_input := TextInput(name='email', ...),
            ...                     TextHeading(text="Your email is:", ...)
            ...                     TextCaption(text=text_input.form_ref, ...)
            ...                 ]),
            ...                 Footer(label='Submit', action=Action(payload={'email': text_input.form_ref}))
            ...         ])
            ...     ]
            ... )
        """
        # noinspection PyTypeChecker
        return FormRef(self.name)

    def form_ref_of(self, screen: Screen | str) -> FormRef:
        """
        The form reference variable for this component with the given form name.
            - A shortcut for :class:`FormRef` with the given screen name and this component name.
            - Use ``.form_ref`` property when the reference is in the same screen.
            - Added in v4.0.

        Example:

            >>> FlowJSON(
            ...     screens=[
            ...         other := Screen(
            ...             id='OTHER',
            ...             layout=Layout(children=[Form(children=[email := TextInput(name='email', ...), ...])])
            ...         ),
            ...         Screen(
            ...             id='START',
            ...             layout=Layout(children=[
            ...                 TextCaption(text=email.form_ref_of(other), ...)  # form reference from another screen
            ...             ])
            ...         )
            ...     ]
            ... )

        Args:
            screen: The screen that contains the form.
        """
        # noinspection PyTypeChecker
        return FormRef(child_name=self.name, screen=screen)


class TextComponent(Component, abc.ABC):
    """
    Base class for all text components

    https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#text
    """

    @property
    @abc.abstractmethod
    def text(self) -> str | DataKey | FormRef: ...


class FontWeight(utils.StrEnum):
    """
    The text weight

    Attributes:
        BOLD: **Bold text**
        ITALIC: `Italic text`
        BOLD_ITALIC: Bold and italic text
        NORMAL: Normal text
    """

    BOLD = "bold"
    ITALIC = "italic"
    BOLD_ITALIC = "bold_italic"
    NORMAL = "normal"


@dataclasses.dataclass(slots=True, kw_only=True)
class TextHeading(TextComponent):
    """
    Represents text that is displayed as a heading.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#heading>`_.

    Example:

        >>> TextHeading(text='Heading', visible=True)

    Attributes:
        text: The text of the heading. Limited to 80 characters. Can be dynamic.
        visible: Whether the heading is visible or not. Default to ``True``, Can be dynamic.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.TEXT_HEADING, init=False, repr=False
    )
    text: str | DataKey | FormRef
    visible: bool | str | DataKey | FormRef | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class TextSubheading(TextComponent):
    """
    Represents text that is displayed as a subheading.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#subheading>`_.

    Example:

        >>> TextSubheading(text='Subheading', visible=True)

    Attributes:
        text: The text of the subheading. Limited to 80 characters. Can be dynamic.
        visible: Whether the subheading is visible or not. Default to ``True``, Can be dynamic.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.TEXT_SUBHEADING, init=False, repr=False
    )
    text: str | DataKey | FormRef
    visible: bool | str | DataKey | FormRef | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class TextBody(TextComponent):
    """
    Represents text that is displayed as a body.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#body>`_.

    Example:

        >>> TextBody(
        ...     text='Body',
        ...     font_weight=FontWeight.BOLD,
        ...     strikethrough=True,
        ...     visible=True
        ... )

    Attributes:
        text: The text of the body. Limited to 4096 characters. Can be dynamic.
        markdown: Whether the text is markdown or not (Added in v5.1).
        font_weight: The weight of the text. Can be dynamic.
        strikethrough: Whether the text is strikethrough or not. Can be dynamic.
        visible: Whether the body is visible or not. Default to ``True``, Can be dynamic.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.TEXT_BODY, init=False, repr=False
    )
    text: str | Iterable[str] | DataKey | FormRef
    markdown: bool | None = None
    font_weight: FontWeight | str | DataKey | FormRef | None = None
    strikethrough: bool | str | DataKey | FormRef | None = None
    visible: bool | str | DataKey | FormRef | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class TextCaption(TextComponent):
    """
    Represents text that is displayed as a caption.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#caption>`_.

    Example:

        >>> TextCaption(
        ...     text='Caption',
        ...     font_weight=FontWeight.ITALIC,
        ...     strikethrough=True,
        ... )


    Attributes:
        text: The text of the caption (array of strings supported since v5.1). Limited to 4096 characters. Can be dynamic.
        markdown: Whether the text is markdown or not (Added in v5.1).
        font_weight: The weight of the text. Can be dynamic.
        strikethrough: Whether to strike through the text or not. Can be dynamic.
        visible: Whether the caption is visible or not. Default to ``True``, Can be dynamic.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.TEXT_CAPTION, init=False, repr=False
    )
    text: str | Iterable[str] | DataKey | FormRef
    markdown: bool | None = None
    font_weight: FontWeight | str | DataKey | FormRef | None = None
    strikethrough: bool | str | DataKey | FormRef | None = None
    visible: bool | str | DataKey | FormRef | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class RichText(TextComponent):
    """
    Represents text that is displayed as a rich text.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#richtext>`_.
    - The goal of the component is to provide a rich formatting capabilities and introduce the way to render large texts (Terms of Condition, Policy Documents, User Agreement and etc) without facing limitations of basic text components (TextHeading, TextSubheading, TextBody and etc)
    - RichText component utilizes a select subset of the Markdown specification. It adheres strictly to standard Markdown syntax without introducing any custom modifications. Content created for the RichText component is fully compatible with standard Markdown documents.
    - Added in v5.1.

    Example:

        >>> RichText(
        ...     text=[
        ...         "# Heading 1",
        ...         "## Heading 2",
        ...         "Let’s make a **bold** statement",
        ...         "Let's make this text *italic*",
        ...         "Let's make this text ~~Strikethrough~~",
        ...         "This text is ~~***really important***~~",
        ...         "This is a [pywa docs](https://pywa.readthedocs.io/)",
        ...         "This is a ordered list:",
        ...         "1. Item 1",
        ...         "2. Item 2",
        ...         "This is a unordered list:",
        ...         "- Item 1",
        ...         "- Item 2",
        ...         "![image](data:image/png;base64,<base64 content>)",
        ...         "| Tables        | Are           | Cool  |",
        ...         "| ------------- | ------------- | ----- |",
        ...         "| col 3 is      | right-aligned | $1600 |",
        ...         "| col 2 is      | centered      |   $12 |",
        ...     ],
        ... )


    Attributes:
        text: The markdown text (array of strings supported). Limited to 4096 characters. Can be dynamic.
        visible: Whether the caption is visible or not. Default to ``True``, Can be dynamic.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.RICH_TEXT, init=False, repr=False
    )
    text: str | Iterable[str] | DataKey | FormRef
    visible: bool | str | DataKey | FormRef | None = None


class TextEntryComponent(FormComponent, abc.ABC):
    """
    Base class for all text entry components

    https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#textentry
    """

    @property
    @abc.abstractmethod
    def helper_text(self) -> str | DataKey | FormRef | None: ...

    @property
    @abc.abstractmethod
    def error_message(self) -> str | DataKey | FormRef | None: ...


class InputType(utils.StrEnum):
    """
    The input type of the text entry component.

    - This is used by the WhatsApp client to determine the keyboard layout and validation rules.

    Attributes:
        TEXT: A single line of text (for multi-line text use :class:`TextArea`).
        NUMBER: A number (keyboard layout is numeric, with a decimal separator).
        EMAIL: An email address (keyboard layout is alphanumeric, with a special character for the @ symbol).
        PASSWORD: A password (the input is masked).
        PASSCODE: A passcode (keyboard layout is numeric, the input is masked).
        PHONE: A phone number (keyboard layout is numeric, with a special character for the + symbol).
    """

    TEXT = "text"
    NUMBER = "number"
    EMAIL = "email"
    PASSWORD = "password"
    PASSCODE = "passcode"
    PHONE = "phone"


@dataclasses.dataclass(slots=True, kw_only=True)
class TextInput(TextEntryComponent):
    """
    Represents a text entry component that allows for a single line of text.

    - This component must be inside a :class:`Form` (if FlowJSON version is below 4.0).
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#textinput>`_.

    Example:

        >>> TextInput(
        ...     name='email',
        ...     label='Email',
        ...     input_type=InputType.EMAIL,
        ...     required=True,
        ...     min_chars=5,
        ...     max_chars=50,
        ...     helper_text='Enter your email address',
        ... )

    Attributes:
        name: The unique name (id) for this component (to be used dynamically or in action payloads).
        label: The label of the text input. Limited to 20 characters. Can be dynamic.
        input_type: The input type of the text input (for keyboard layout and validation rules). Can be dynamic.
        required: Whether the text input is required or not. Can be dynamic.
        min_chars: The minimum number of characters allowed in the text input. Can be dynamic.
        max_chars: The maximum number of characters allowed in the text input. Can be dynamic.
        helper_text: The helper text of the text input. Limited to 80 characters. Can be dynamic.
        enabled: Whether the text input is enabled or not. Default to ``True``. Can be dynamic.
        visible: Whether the text input is visible or not. Default to ``True``. Can be dynamic.
        init_value: The default value of the text input. Shortcut for ``init_values`` of the parent :class:`Form`. Can be dynamic.
        error_message: The error message of the text input. Shortcuts for ``error_messages`` of the parent :class:`Form`. Can be dynamic.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.TEXT_INPUT, init=False, repr=False
    )
    name: str
    label: str | DataKey | FormRef
    input_type: InputType | str | DataKey | FormRef | None = None
    required: bool | str | DataKey | FormRef | None = None
    min_chars: int | str | DataKey | FormRef | None = None
    max_chars: int | str | DataKey | FormRef | None = None
    helper_text: str | DataKey | FormRef | None = None
    enabled: bool | str | DataKey | FormRef | None = None
    visible: bool | str | DataKey | FormRef | None = None
    init_value: str | DataKey | FormRef | None = None
    error_message: str | DataKey | FormRef | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class TextArea(TextEntryComponent):
    """
    Represents a text entry component that allows for multiple lines of text.

    - This component must be inside a :class:`Form` (if FlowJSON version is below 4.0).
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#textarea>`_.

    Example:

        >>> TextArea(
        ...     name='description',
        ...     label='Description',
        ...     required=True,
        ...     max_length=100,
        ...     helper_text='Enter your description',
        ... )

    Attributes:
        name: The unique name (id) for this component (to be used dynamically or in action payloads).
        label: The label of the text area. Limited to 20 characters. Can be dynamic.
        required: Whether the text area is required or not. Can be dynamic.
        max_length: The maximum number of characters allowed in the text area. Can be dynamic.
        helper_text: The helper text of the text area. Limited to 80 characters. Can be dynamic.
        enabled: Whether the text area is enabled or not. Default to ``True``. Can be dynamic.
        visible: Whether the text area is visible or not. Default to ``True``. Can be dynamic.
        init_value: The default value of the text area. Shortcut for ``init_values`` of the parent :class:`Form`. Can be dynamic.
        error_message: The error message of the text area. Shortcuts for ``error_messages`` of the parent :class:`Form`. Can be dynamic.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.TEXT_AREA, init=False, repr=False
    )
    name: str
    label: str | DataKey | FormRef
    required: bool | str | DataKey | FormRef | None = None
    max_length: int | str | DataKey | FormRef | None = None
    helper_text: str | DataKey | FormRef | None = None
    enabled: bool | str | DataKey | FormRef | None = None
    visible: bool | str | DataKey | FormRef | None = None
    init_value: str | DataKey | FormRef | None = None
    error_message: str | DataKey | FormRef | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class CheckboxGroup(FormComponent):
    """
    CheckboxGroup component allows users to pick multiple selections from a list of options.

    - This component must be inside a :class:`Form` (if FlowJSON version is below 4.0).
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#checkbox>`_.

    Example:

        >>> CheckboxGroup(
        ...     name='options',
        ...     data_source=[
        ...         DataSource(id='1', title='Option 1'),
        ...         DataSource(id='2', title='Option 2'),
        ...         DataSource(id='3', title='Option 3'),
        ...     ],
        ...     label='Options',
        ...     min_selected_items=1,
        ...     max_selected_items=2,
        ...     required=True,
        ...     init_value=['1', '2']
        ... )

    Attributes:
        name: The unique name (id) for this component (to be used dynamically or in action payloads).
        data_source: The data source of the checkbox group. Can be dynamic.
        label: The label of the checkbox group. Limited to 30 characters. Can be dynamic. Required starting from v4.0.
        description: The description of the checkbox group. Limited to 300 characters. Can be dynamic. Added in v4.0.
        min_selected_items: The minimum number of items that can be selected. Minimum value is 1. Can be dynamic.
        max_selected_items: The maximum number of items that can be selected. Maximum value is 20. Can be dynamic.
        required: Whether the checkbox group is required or not. Can be dynamic.
        visible: Whether the checkbox group is visible or not. Default to ``True``. Can be dynamic.
        enabled: Whether the checkbox group is enabled or not. Default to ``True``. Can be dynamic.
        init_value: The default values (IDs of the data sources). Shortcut for ``init_values`` of the parent :class:`Form`. Can be dynamic.
        on_select_action: The action to perform when an item is selected.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.CHECKBOX_GROUP, init=False, repr=False
    )
    name: str
    data_source: Iterable[DataSource] | str | DataKey | FormRef
    label: str | DataKey | FormRef | None = None
    description: str | DataKey | FormRef | None = None
    min_selected_items: int | str | DataKey | FormRef | None = None
    max_selected_items: int | str | DataKey | FormRef | None = None
    required: bool | str | DataKey | FormRef | None = None
    visible: bool | str | DataKey | FormRef | None = None
    enabled: bool | str | DataKey | FormRef | None = None
    init_value: list[str] | str | DataKey | FormRef | None = None
    on_select_action: Action | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class RadioButtonsGroup(FormComponent):
    """
    RadioButtonsGroup component allows users to pick a single selection from a list of options.

    - This component must be inside a :class:`Form` (if FlowJSON version is below 4.0).
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#radio>`_.

    Example:

        >>> RadioButtonsGroup(
        ...     name='options',
        ...     data_source=[
        ...         DataSource(id='1', title='Option 1'),
        ...         DataSource(id='2', title='Option 2'),
        ...         DataSource(id='3', title='Option 3'),
        ...     ],
        ...     label='Options',
        ...     required=True,
        ...     init_value='1'
        ... )

    Attributes:
        name: The unique name (id) for this component (to be used dynamically or in action payloads).
        data_source: The data source of the radio buttons group. Can be dynamic.
        label: The label of the radio buttons group. Limited to 30 characters. Can be dynamic. Required starting from v4.0.
        description: The description of the radio buttons group. Limited to 300 characters. Can be dynamic. Added in v4.0.
        required: Whether the radio buttons group is required or not. Can be dynamic.
        visible: Whether the radio buttons group is visible or not. Default to ``True``. Can be dynamic.
        enabled: Whether the radio buttons group is enabled or not. Default to ``True``. Can be dynamic.
        init_value: The default value (ID of the data source). Shortcut for ``init_values`` of the parent :class:`Form`. Can be dynamic.
        on_select_action: The action to perform when an item is selected.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.RADIO_BUTTONS_GROUP, init=False, repr=False
    )
    name: str
    data_source: Iterable[DataSource] | str | DataKey | FormRef
    label: str | DataKey | FormRef | None = None
    description: str | DataKey | FormRef | None = None
    required: bool | str | DataKey | FormRef | None = None
    visible: bool | str | DataKey | FormRef | None = None
    enabled: bool | str | DataKey | FormRef | None = None
    init_value: str | DataKey | FormRef | None = None
    on_select_action: Action | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class Dropdown(FormComponent):
    """
    Dropdown component allows users to pick a single selection from a list of options.

    - This component must be inside a :class:`Form` (if FlowJSON version is below 4.0).
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#drop>`_.

    Example:

        >>> Dropdown(
        ...     name='options',
        ...     data_source=[
        ...         DataSource(id='1', title='Option 1'),
        ...         DataSource(id='2', title='Option 2'),
        ...         DataSource(id='3', title='Option 3'),
        ...     ],
        ...     label='Options',
        ...     required=True,
        ...     init_value='1'
        ... )

    Attributes:
        name: The unique name (id) for this component (to be used dynamically or in action payloads).
        label: The label of the dropdown. Limited to 30 characters. Can be dynamic.
        data_source: The data source of the dropdown. minimum 1 and maximum 200 items. Can be dynamic.
        enabled: Whether the dropdown is enabled or not. Default to ``True``. Can be dynamic.
        required: Whether the dropdown is required or not. Can be dynamic.
        visible: Whether the dropdown is visible or not. Default to ``True``. Can be dynamic.
        init_value: The default value (ID of the data source). Shortcut for ``init_values`` of the parent :class:`Form`. Can be dynamic.
        on_select_action: The action to perform when an item is selected.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.DROPDOWN, init=False, repr=False
    )
    name: str
    label: str | DataKey | FormRef
    data_source: Iterable[DataSource] | str | DataKey | FormRef
    enabled: bool | str | DataKey | FormRef | None = None
    required: bool | str | DataKey | FormRef | None = None
    visible: bool | str | DataKey | FormRef | None = None
    init_value: str | DataKey | FormRef | None = None
    on_select_action: Action | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class Footer(Component):
    """
    Footer component allows users to navigate to other screens or submit the flow.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#foot>`_.

    Example:

        - Exchange data with your server (@wa.on_flow_request(...))

        >>> Footer(
        ...     label='Sign up',
        ...     on_click_action=Action(
        ...         name=FlowActionType.DATA_EXCHANGE,
        ...         payload={'email': '...', 'phone': '...'}
        ...     )
        ... )

        - Go to the next screen:

        >>> Footer(
        ...     label='Next',
        ...     on_click_action=Action(
        ...         name=FlowActionType.NAVIGATE,
        ...         next=ActionNext(name='NEXT_SCREEN')
        ...     )
        ... )

        - Complete the flow when the user clicks the footer:

        >>> Footer(
        ...     label='Submit',
        ...     on_click_action=Action(
        ...         name=FlowActionType.COMPLETE,
        ...         payload={'email': '...', 'phone': '...'}
        ...     )
        ... )


    Attributes:
        label: The label of the footer. Limited to 35 characters. Can be dynamic.
        on_click_action: The action to perform when the footer is clicked. Required.
        left_caption: Can set left_caption and right_caption or only center_caption, but not all 3 at once. Limited to 15 characters. Can be dynamic.
        center_caption: Can set center-caption or left-caption and right-caption, but not all 3 at once. Limited to 15 characters. Can be dynamic.
        right_caption: Can set right-caption and left-caption or only center-caption, but not all 3 at once. Limited to 15 characters. Can be dynamic.
        enabled: Whether the footer is enabled or not. Default to ``True``. Can be dynamic.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.FOOTER, init=False, repr=False
    )
    visible: None = dataclasses.field(default=None, init=False, repr=False)
    label: str | DataKey | FormRef
    on_click_action: Action
    left_caption: str | DataKey | FormRef | None = None
    center_caption: str | DataKey | FormRef | None = None
    right_caption: str | DataKey | FormRef | None = None
    enabled: bool | str | DataKey | FormRef | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class OptIn(FormComponent):
    """
    OptIn component allows users to check a box to opt in for a specific purpose.

    - This component must be inside a :class:`Form` (if FlowJSON version is below 4.0).
    - Max number of Opt-Ins Per Screen is 5.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#opt>`_.

    Example:

        >>> OptIn(
        ...     name='opt_in',
        ...     label='I agree to the terms and conditions',
        ...     required=True,
        ...     init_value=True
        ... )

    Attributes:
        name: The unique name (id) for this component (to be used dynamically or in action payloads).
        label: The label of the opt in. Limited to 30 characters. Can be dynamic.
        required: Whether the opt in is required or not. Can be dynamic.
        visible: Whether the opt in is visible or not. Default to ``True``. Can be dynamic.
        init_value: The default value of the opt in. Shortcut for ``init_values`` of the parent :class:`Form`. Can be dynamic.
        on_click_action: The action to perform when the opt in is clicked.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.OPT_IN, init=False, repr=False
    )
    enabled: None = dataclasses.field(default=None, init=False, repr=False)
    name: str
    label: str | DataKey | FormRef
    required: bool | str | DataKey | FormRef | None = None
    visible: bool | str | DataKey | FormRef | None = None
    init_value: bool | str | DataKey | FormRef | None = None
    on_click_action: Action | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class EmbeddedLink(Component):
    """
    EmbeddedLink component allows users to navigate to another screen.

    - Max Number of Embedded Links Per Screen is 2.
    - Empty or Blank value is not accepted for the text field.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#embed>`_.

    Example:

        >>> EmbeddedLink(
        ...     text='Sign up',
        ...     on_click_action=Action(
        ...         name=FlowActionType.NAVIGATE,
        ...         next=ActionNext(name='SIGNUP_SCREEN'),
        ...         payload={'data': 'value'}
        ...     )
        ... )

    Attributes:
        text: The text of the embedded link. Limited to 35 characters. Can be dynamic.
        on_click_action: The action to perform when the embedded link is clicked.
        visible: Whether the embedded link is visible or not. Default to ``True``. Can be dynamic.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.EMBEDDED_LINK, init=False, repr=False
    )
    text: str | DataKey | FormRef
    on_click_action: Action
    visible: bool | str | DataKey | FormRef | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class DatePicker(FormComponent):
    """
    DatePicker component allows users to select a date

    - This component must be inside a :class:`Form` (if FlowJSON version is below 4.0).
    - Starting from FlowJSON version 5.0, you can use date/datetime python objects or a formatted date string in the format "YYYY-MM-DD", such as "2024-10-21" or
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#dp>`_.

    Example:

        >>> DatePicker(
        ...     name='date',
        ...     label='Appointment Date',
        ...     min_date=datetime.date(2024, 7, 21),
        ...     max_date=datetime.date(2024, 10, 21),
        ...     unavailable_dates=[
        ...         datetime.date(2024, 7, 25),
        ...         datetime.date(2024, 7, 26),
        ...     ],
        ...     helper_text='Select a date',
        ...     required=True
        ... )


    Attributes:
        name: The unique name (id) for this component (to be used dynamically or in action payloads).
        label: The label of the date picker. Limited to 40 characters. Can be dynamic.
        min_date: The minimum date (date/datetime/timestamp) that can be selected. Can be dynamic.
        max_date: The maximum date (date/datetime/timestamp) that can be selected. Can be dynamic.
        unavailable_dates: The dates (dates/datetimes/timestamps) that cannot be selected. Can be dynamic.
        helper_text: The helper text of the date picker. Limited to 80 characters. Can be dynamic.
        enabled: Whether the date picker is enabled or not. Default to ``True``. Can be dynamic.
        required: Whether the date picker is required or not. Can be dynamic.
        visible: Whether the date picker is visible or not. Default to ``True``. Can be dynamic.
        init_value: The default value. Shortcut for ``init_values`` of the parent :class:`Form`. Can be dynamic.
        error_message: The error message of the date picker. Shortcuts for ``error_messages`` of the parent :class:`Form`. Can be dynamic.
        on_select_action: The action to perform when a date is selected.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.DATE_PICKER, init=False, repr=False
    )
    name: str
    label: str | DataKey | FormRef
    min_date: datetime.date | str | DataKey | FormRef | None = None
    max_date: datetime.date | str | DataKey | FormRef | None = None
    unavailable_dates: (
        Iterable[datetime.date | str] | str | DataKey | FormRef | None
    ) = None
    helper_text: str | DataKey | FormRef | None = None
    enabled: bool | str | DataKey | FormRef | None = None
    required: bool | str | DataKey | FormRef | None = None
    visible: bool | str | DataKey | FormRef | None = None
    init_value: datetime.date | str | DataKey | FormRef | None = None
    error_message: str | DataKey | FormRef | None = None
    on_select_action: Action | None = None

    def __post_init__(self):
        date_fmt = "%Y-%m-%d"
        for attr in {"min_date", "max_date", "init_value"}:
            value = getattr(self, attr)
            if isinstance(value, datetime.date):
                setattr(self, attr, value.strftime(date_fmt))
        if self.unavailable_dates:
            self.unavailable_dates = [
                date.strftime(date_fmt) if isinstance(date, datetime.date) else date
                for date in self.unavailable_dates
            ]


class ScaleType(utils.StrEnum):
    """
    The scale type of the image.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#image-scale-types>`_.

    Attributes:
        COVER: Image is clipped to fit the image container.
        CONTAIN: Image is contained within the image container with the original aspect ratio.
    """

    COVER = "cover"
    CONTAIN = "contain"


@dataclasses.dataclass(slots=True, kw_only=True)
class Image(Component):
    """
    Image component that displays an image.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#img>`_.
    - Supported images formats are JPEG PNG
    - Recommended image size is up to 300kb
    - Max number of images per screen is 3

    Example:

        >>> Image(
        ...     src='iVBORw0KGgoAAAANSUhEUgAAAlgAAAM...',
        ...     width=100,
        ...     height=100,
        ...     scale_type=ScaleType.CONTAIN,
        ...     aspect_ratio=1,
        ...     alt_text='Image of a cat'
        ... )

    Attributes:
        src: Base64 of an image. Can be dynamic.
        width: The width of the image. Can be dynamic.
        height: The height of the image. Can be dynamic.
        scale_type: The scale type of the image. Defaule to ``ScaleType.CONTAIN`` Can be dynamic. Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#image-scale-types>`_.
        aspect_ratio: The aspect ratio of the image. Default to ``1``. Can be dynamic.
        alt_text: Alternative Text is for the accessibility feature, eg. Talkback and Voice over. Can be dynamic.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.IMAGE, init=False, repr=False
    )
    src: str | DataKey | FormRef
    width: int | str | DataKey | FormRef | None = None
    height: int | str | DataKey | FormRef | None = None
    scale_type: ScaleType | str | DataKey | FormRef | None = None
    aspect_ratio: int | str | DataKey | FormRef
    alt_text: str | DataKey | FormRef | None = None
    visible: bool | str | DataKey | FormRef | None = None


class PhotoSource(utils.StrEnum):
    """
    The source where the image can be selected from.

    Attributes:
        CAMERA_GALLERY: User can select from gallery or take a photo
        CAMERA: User can select only from gallery
        GALLERY: User can only take a photo
    """

    CAMERA_GALLERY = "camera_gallery"
    CAMERA = "camera"
    GALLERY = "gallery"


@dataclasses.dataclass(slots=True, kw_only=True)
class PhotoPicker(FormComponent):
    """
    PhotoPicker component allows uploading media from camera or gallery

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components/media_upload#photopicker--early-release->`_.
    - Added in v4.0
    - Only 1 PhotoPicker is allowed per screen
    - Using both :class:`PhotoPicker` and :class:`DocumentPicker` components on a single screen is not allowed.


    Example:

        >>> PhotoPicker(
        ...     name='photo',
        ...     label='Take a photo',
        ...     description='We need your photo for verification',
        ...     photo_source=PhotoSource.CAMERA,
        ...     max_file_size_kb=10_000,  # 10MB
        ...     min_uploaded_photos=1,
        ...     max_uploaded_photos=3,
        )

    Attributes:
        name: The unique name (id) for this component (to be used dynamically or in action payloads).
        label: The label of the photo picker. Limited to 30 characters. Can be dynamic.
        description: The description of the photo picker. Limited to 300 characters. Can be dynamic.
        photo_source: The source where the image can be selected from. Default to ``PhotoSource.CAMERA_GALLERY``. Can be dynamic.
        max_file_size_kb: The maximum file size in KB. Can be dynamic. Default value: 25600 (25 MiB)
        min_uploaded_photos: The minimum number of photos that can be uploaded. Can be dynamic. This property determines whether the component is optional (set to 0) or required (set above 0).
        max_uploaded_photos: The maximum number of photos that can be uploaded. Can be dynamic. Default value: 30
        enabled: Whether the photo picker is enabled or not. Default to ``True``. Can be dynamic.
        visible: Whether the photo picker is visible or not. Default to ``True``. Can be dynamic.
        error_message: The error message of the photo picker. Can be dynamic.

    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.PHOTO_PICKER, init=False, repr=False
    )
    required: None = dataclasses.field(default=None, init=False, repr=False)
    init_value: None = dataclasses.field(default=None, init=False, repr=False)
    name: str
    label: str | DataKey | FormRef
    description: str | DataKey | FormRef | None = None
    photo_source: PhotoSource | str | DataKey | FormRef | None = None
    max_file_size_kb: int | str | DataKey | FormRef | None = None
    min_uploaded_photos: int | str | DataKey | FormRef | None = None
    max_uploaded_photos: int | str | DataKey | FormRef | None = None
    enabled: bool | str | DataKey | FormRef | None = None
    visible: bool | str | DataKey | FormRef | None = None
    error_message: str | DataKey | FormRef | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class DocumentPicker(FormComponent):
    """
    DocumentPicker component allows uploading files from the device

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components/media_upload#document-picker>`_.
    - Added in v4.0
    - Only 1 DocumentPicker is allowed per screen
    - Using both :class:`PhotoPicker` and :class:`DocumentPicker` components on a single screen is not allowed.
    - Note: some old Android and iOS OS versions don’t understand all mime types above. As a result, a user might be able to select a file with a different mime type to the ones specified.

    Example:

        >>> DocumentPicker(
        ...     name='document',
        ...     label='Upload your Driving License',
        ...     description='We need your document for verification',
        ...     max_file_size_kb=5_000,  # 5MB
        ...     min_uploaded_documents=1,
        ...     max_uploaded_documents=1,
        ...     allowed_mime_types=['application/pdf', 'image/jpeg', 'image/png'],
        )

    Attributes:
        name: The unique name (id) for this component (to be used dynamically or in action payloads).
        label: The label of the document picker. Limited to 30 characters. Can be dynamic.
        description: The description of the document picker. Limited to 300 characters. Can be dynamic.
        max_file_size_kb: The maximum file size in KB. Can be dynamic. Default value: 25600 (25 MiB)
        min_uploaded_documents: The minimum number of documents that can be uploaded. Can be dynamic. This property determines whether the component is optional (set to 0) or required (set above 0).
        max_uploaded_documents: The maximum number of documents that can be uploaded. Can be dynamic. Default value: 30
        allowed_mime_types: Specifies which document mime types can be selected. If it contains “image/jpeg”, picking photos from the gallery will be available as well. Can be dynamic. Default value: Any document from the supported mime types can be selected.
        enabled: Whether the document picker is enabled or not. Default to ``True``. Can be dynamic.
        visible: Whether the document picker is visible or not. Default to ``True``. Can be dynamic.
        error_message: The error message of the document picker. Can be dynamic.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.DOCUMENT_PICKER, init=False, repr=False
    )
    required: None = dataclasses.field(default=None, init=False, repr=False)
    init_value: None = dataclasses.field(default=None, init=False, repr=False)
    name: str
    label: str | DataKey | FormRef
    description: str | DataKey | FormRef | None = None
    max_file_size_kb: int | str | DataKey | FormRef | None = None
    min_uploaded_documents: int | str | DataKey | FormRef | None = None
    max_uploaded_documents: int | str | DataKey | FormRef | None = None
    allowed_mime_types: Iterable[str] | str | DataKey | FormRef | None = None
    enabled: bool | str | DataKey | FormRef | None = None
    visible: bool | str | DataKey | FormRef | None = None
    error_message: str | DataKey | FormRef | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class If(Component):
    """
    If component allows users to add components based on a condition.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#if>`_.
    - It is allowed to nest up to 3 :class:`If` components.
    - Should have at least one dynamic value (e.g. screen_data.data_key / form_comp.form_ref) in the condition.
    - Should always be resolved into a boolean (i.e. no strings or number values).
    - Can be used with literals but should not only contain literals.
    - :class:`Footer` can be added within :class:`If` only in the first level, not inside a nested :class:`If`.
    - If there is a :class:`Footer` within :class:`If`, it should exist in both branches (i.e. ``then`` and ``else``). This means that ``else`` becomes mandatory.
    - If there is a :class:`Footer` within :class:`If` it cannot exist a footer outside, because the max count of :class:`Footer` is 1 per screen.

    Example:

            >>> age = ScreenData(key="age", example=20)
            >>> opt_in = OptIn(name="opt_in", ...)
            >>> If(
            ...     condition=f"{age.data_key} > 21 && {opt_in.form_ref}",
            ...     then=[
            ...         TextHeading(text="Welcome to the club!"),
            ...         TextInput(
            ...             name='email',
            ...             label='Email',
            ...         ),
            ...     ],
            ...     else_=[
            ...         TextHeading(text="You are not eligible!"),
            ...     ]
            ... )

    Attributes:
        condition: Boolean expression, You can use both dynamic and static values. See `Supported Operators <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#supported-operators>`_.
        then: The components that will be rendered when ``condition`` is ``True``.
        else_: The components that will be rendered when ``condition`` is ``False``.

    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.IF, init=False, repr=False
    )
    visible: None = dataclasses.field(default=None, init=False, repr=False)
    condition: str
    then: Iterable[_SUPPOERTED_COMPONENTS]
    else_: Iterable[_SUPPOERTED_COMPONENTS] | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class Switch(Component):
    """
    Switch component allows users to add components based on a value of a data key / form ref.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#switch>`_.

    Example:

            >>> age = TextInput(name='age', label='Age')
            >>> switch = Switch(
            ...     value=age.form_ref,
            ...     cases={
            ...         '10': [TextHeading(text='Under 18')],
            ...         ...
            ...         '20': [TextInput(name='email', label='Email')],
            ...     }

    Attributes:
        value: The key / ref to the data that will be used to determine which components to render.
        cases: The components that will be rendered based on the value.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.SWITCH, init=False, repr=False
    )
    visible: None = dataclasses.field(default=None, init=False, repr=False)
    value: DataKey | FormRef | str
    cases: dict[str, Iterable[_SUPPOERTED_COMPONENTS]]


class FlowActionType(utils.StrEnum):
    """
    Flow JSON provides a generic way to trigger asynchronous actions handled by a client through interactive UI elements.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#action>`_.

    Attributes:
        COMPLETE: Triggers the termination of the Flow with the provided payload
         (Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#complete-action>`_).
        DATA_EXCHANGE: Sending Data to WhatsApp Flows Data Endpoint
         (Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#data-exchange-action>`_).
        NAVIGATE: Triggers the next screen with the payload as its input. The CTA button will be disabled until the
         payload with data required for the next screen is supplied.
         (Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#navigate-action>`_).
    """

    COMPLETE = "complete"
    DATA_EXCHANGE = "data_exchange"
    NAVIGATE = "navigate"


class ActionNextType(utils.StrEnum):
    """
    The type of the next action

    Attributes:
        SCREEN: Navigate to the next screen
        PLUGIN: Trigger a plugin
    """

    SCREEN = "screen"
    PLUGIN = "plugin"


@dataclasses.dataclass(slots=True, kw_only=True)
class ActionNext:
    """
    The next action

    Attributes:
        name: The name of the next screen or plugin
        type: The type of the next action (Default: ``ActionNextType.SCREEN``)
    """

    name: str
    type: ActionNextType | str = ActionNextType.SCREEN


@dataclasses.dataclass(slots=True, kw_only=True)
class Action:
    """
    Action component allows users to trigger asynchronous actions that are handled by a client through interactive UI elements.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#actions>`_.

    Example:

        >>> complete_action = Action(
        ...     name=FlowActionType.COMPLETE,
        ...     payload={'data': 'value'}
        ... )
        >>> data_exchange_action = Action(
        ...     name=FlowActionType.DATA_EXCHANGE,
        ...     payload={'data': 'value'}
        ... )
        >>> navigate_action = Action(
        ...     name=FlowActionType.NAVIGATE,
        ...     next=ActionNext(name='NEXT_SCREEN'),
        ...     payload={'data': 'value'}
        ... )

    Attributes:
        name: The type of the action
        next: The next action to perform (only for ``FlowActionType.NAVIGATE``)
        payload: The payload of the action (Pass data to the next screen or to the WhatsApp Flows Data Endpoint).
         This payload can take data from form components or from the data of the screen.
    """

    name: FlowActionType | str
    next: ActionNext | None = None
    payload: dict[str, str | DataKey | FormRef] | None = None

    def __post_init__(self):
        if self.name == FlowActionType.NAVIGATE.value:
            if self.next is None:
                raise ValueError("next is required for FlowActionType.NAVIGATE")
        if self.name == FlowActionType.COMPLETE.value:
            if self.payload is None:
                raise ValueError(
                    "payload is required for FlowActionType.COMPLETE (use {} for empty payload)"
                )


_SUPPOERTED_COMPONENTS: TypeAlias = (
    TextHeading
    | TextSubheading
    | TextBody
    | TextCaption
    | TextInput
    | TextArea
    | CheckboxGroup
    | RadioButtonsGroup
    | OptIn
    | Dropdown
    | DatePicker
    | EmbeddedLink
    | Image
    | PhotoPicker
    | DocumentPicker
    | If
    | Switch
    | Footer
    | dict[str, Any]
)
