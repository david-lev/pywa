"""This module contains the types related to WhatsApp Flows."""

from __future__ import annotations

import abc
import dataclasses
import datetime
import functools
import json
import logging
import pathlib
import re
from urllib import parse as urllib_parse
import warnings
from typing import (
    Iterable,
    TYPE_CHECKING,
    Any,
    BinaryIO,
    Literal,
    Type,
    Generic,
    TypeAlias,
    TypeVar,
)

import httpx

from .media import BaseUserMedia
from .. import utils
from .base_update import BaseUserUpdate  # noqa
from .others import (
    WhatsAppBusinessAccount,
    FacebookApplication,
    MessageType,
    Metadata,
    ReplyToMessage,
    Result,
    SuccessResult,
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
    "FlowJSONUpdateResult",
    "FlowValidationError",
    "FlowAsset",
    "CreatedFlow",
    "MigratedFlow",
    "MigratedFlowError",
    "MigrateFlowsResponse",
    "FlowJSON",
    "Screen",
    "ScreenData",
    "ScreenDataUpdate",
    "Layout",
    "LayoutType",
    "Form",
    "ScreenDataRef",
    "ComponentRef",
    "FlowStr",
    "TextHeading",
    "TextSubheading",
    "TextBody",
    "TextCaption",
    "RichText",
    "FontWeight",
    "TextInput",
    "InputType",
    "LabelVariant",
    "TextArea",
    "CheckboxGroup",
    "ChipsSelector",
    "RadioButtonsGroup",
    "Footer",
    "OptIn",
    "Dropdown",
    "EmbeddedLink",
    "NavigationList",
    "NavigationItem",
    "NavigationItemStart",
    "NavigationItemMainContent",
    "NavigationItemEnd",
    "DatePicker",
    "CalendarPicker",
    "CalendarPickerMode",
    "CalendarRangeValues",
    "CalendarDay",
    "Image",
    "ImageCarouselItem",
    "ImageCarousel",
    "PhotoPicker",
    "PhotoSource",
    "DocumentPicker",
    "ScaleType",
    "If",
    "Switch",
    "DataSource",
    "DataExchangeAction",
    "NavigateAction",
    "CompleteAction",
    "UpdateDataAction",
    "OpenUrlAction",
    "FlowActionType",
    "FlowRequestActionType",
    "Next",
    "NextType",
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
        timestamp: The timestamp when the message was sent (in UTC).
        reply_to_message: The message to which this message is a reply to.
        body: The body of the message.
        token: The token of the flow. can be ``None`` in some cases :|
        response: The response from the flow.
        shared_data: Shared data between handlers.
    """

    type: MessageType
    reply_to_message: ReplyToMessage | None
    body: str
    token: str | None
    response: dict[str, Any]

    _txt_fields = ("token", "body")
    _webhook_field = "messages"

    @classmethod
    def from_update(cls, client: WhatsApp, update: dict) -> FlowCompletion:
        msg = (value := (entry := update["entry"][0])["changes"][0]["value"])[
            "messages"
        ][0]
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
            waba_id=entry["id"],
            id=msg["id"],
            type=MessageType(msg["type"]),
            metadata=Metadata.from_dict(value["metadata"]),
            from_user=client._usr_cls.from_dict(value["contacts"][0], client=client),
            timestamp=datetime.datetime.fromtimestamp(
                int(msg["timestamp"]),
                datetime.timezone.utc,
            ),
            reply_to_message=ReplyToMessage.from_dict(msg["context"])
            if msg.get("context", {}).get("id")
            else None,
            body=msg["interactive"]["nfm_reply"]["body"],
            token=flow_token,
            response=response,
        )

    def get_media(self, media_cls: Type[BaseUserMedia], key: str) -> BaseUserMedia:
        """
        Get the media object from the response.

        Example:
            >>> from pywa import WhatsApp, types
            >>> wa = WhatsApp(...)
            >>> @wa.on_flow_completion()
            ... def on_flow_completion(_: WhatsApp, flow: types.FlowCompletion):
            ...     img = flow.get_media(types.Image,key="image")
            ...     img.download()

        Args:
            media_cls: The media class to create the media object (e.g. ``types.Image``).
            key: The key of the media in the response.

        Returns:
            The media object.

        Raises:
            KeyError: If the key is not found in the response.
        """
        return media_cls.from_flow_completion(self._client, self.response[key])


class FlowRequestActionType(utils.StrEnum):
    """
    The type the action that triggered the :class:`FlowRequest`.

    Attributes:
        INIT: if the request is triggered when opening the flow (The :class:`FlowButton` was sent with ``flow_action_type`` set to :class:`FlowActionType.DATA_EXCHANGE`)
        BACK: if the request is triggered when pressing back (The screen's ``refresh_on_back`` attr set to ``True``)
        DATA_EXCHANGE: if the request is triggered by :class:`DataExchangeAction`
        NAVIGATE: if the :class:`FlowButton` sent with ``FlowActionType.NAVIGATE`` and the ``screen`` is not in the ``routing_model`` (the request will contain an error)
    """

    INIT = "INIT"
    BACK = "BACK"
    DATA_EXCHANGE = "data_exchange"
    NAVIGATE = "navigate"

    UNKNOWN = "UNKNOWN"


@dataclasses.dataclass(slots=True, frozen=True, kw_only=True)
class FlowRequest:
    """
    Represents a flow request. This request is sent to the flow endpoint when a user interacts with a flow.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/guides/implementingyourflowendpoint#data_exchange_request>`_.

    Attributes:
        version: The version of the ``data_api_version`` specified on the flow json.
        flow_token: The flow token used to create the flow
        action: The action that triggered the request.
        screen: The screen that triggered the request. If action is ``FlowRequestActionType.INIT`` or ``FlowRequestActionType.BACK``, this field may be ``None``.
        data: The data sent from the screen. If action is ``FlowRequestActionType.BACK`` or ``FlowRequestActionType.INIT``, this field may be ``None``.
        raw: The raw data of the request.
        raw_encrypted: The raw-encrypted data of the request.
    """

    version: str
    action: FlowRequestActionType
    flow_token: str
    screen: str | None
    data: dict[str, Any] | None
    raw: dict[str, Any] = dataclasses.field(repr=False, hash=False, compare=False)
    raw_encrypted: dict[str, str] = dataclasses.field(
        repr=False, hash=False, compare=False
    )

    def respond(
        self,
        screen: str | None = None,
        data: _FlowResponseDataType | None = None,
        error_message: str | None = None,
        close_flow: bool = False,
        flow_token: str | None = None,
        version: str | None = None,
    ) -> FlowResponse:
        """
        Create a response for this request.

        - A shortcut for initializing a :class:`FlowResponse` with the same version and flow token as this request.

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
            data: The data to send to the screen or to add to flow completion ``.response`` dict (default to empty dict).
            error_message: This will redirect the user to ``screen`` and will trigger a snackbar error with the error_message present (if ``close_flow`` is ``False``).
            close_flow: Whether to close the flow or just navigate to the screen.
            flow_token: The flow token to close the flow (if ``close_flow`` is ``True``, default to the request flow token).
            version: The version of the data exchange (Default to the request version).
        """
        return FlowResponse(
            version=version or self.version,
            data=data or {},
            screen=screen,
            error_message=error_message,
            flow_token=(flow_token or self.flow_token) if close_flow else None,
            close_flow=close_flow,
        )

    def token_no_longer_valid(self, error_message: str):
        """
        Raise a :class:`FlowTokenNoLongerValid` exception with the provided error message.

        Example:

            >>> wa = WhatsApp(...)
            >>> @wa.on_flow_request("/my-flow-endpoint")
            ... def my_flow_endpoint(_: WhatsApp, req: FlowRequest) -> FlowResponse:
            ...     if req.flow_token == "v1.0": # you see the token is no longer valid
            ...         req.token_no_longer_valid("Open the flow again to continue.")
            ...    ...

        Args:
            error_message: The error message to display to the user.

        Raises:
            FlowTokenNoLongerValid: Well, always.
        """
        raise FlowTokenNoLongerValid(error_message)

    @classmethod
    def from_dict(cls, data: dict, raw_encrypted: dict):
        return cls(
            version=data["version"],
            action=FlowRequestActionType(data["action"]),
            flow_token=data.get(
                "flow_token"
            ),  # some ios devices may not send the flow token :| # type: ignore
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
        return bool(
            self.data
            and any(
                # the docs and the examples are not clear about the error key :|
                key in self.data
                for key in ("error", "error_message", "error_key")
            )
        )

    def decrypt_media(
        self, key: str, index: int = 0, dl_session: httpx.Client | None = None
    ) -> utils.FlowRequestDecryptedMedia:
        """
        Decrypt the encrypted media file from the flow request.

        Example:

            >>> from pywa import WhatsApp, types
            >>> wa = WhatsApp(...)
            >>> @wa.on_flow_request("/my-flow-endpoint")
            ... def my_flow_endpoint(_: WhatsApp, req: types.FlowRequest):
            ...     media_id, filename, decrypted_data = req.decrypt_media(key="driver_license", index=0)
            ...     with open(filename, "wb") as file:
            ...         file.write(decrypted_data)
            ...     return req.respond(...)

        Args:
            key: The key of the media in the data (e.g. ``"driver_license"``).
            index: The index of the media in the data (default to ``0``).
            dl_session: The HTTPX session to download the media (optional, new session will be created if not provided).

        Returns:
            A tuple of (media_id, filename, decrypted_data) where:
                - media_id: The media ID of the decrypted media.
                - filename: The filename of the decrypted media.
                - decrypted_data: The decrypted data of the media.
        Raises:
            ValueError: If the request has no data.
            KeyError: If the key is not found in the data.
            IndexError: If the index is out of range.
        """
        if not self.data:
            raise ValueError("No data to decrypt.")
        return utils.flow_request_media_decryptor(
            encrypted_media=self.data[key][index],
            dl_session=dl_session,
        )


@dataclasses.dataclass(slots=True, kw_only=True)
class FlowResponse:
    """
    Represents a flow response. This response is sent to the flow endpoint to determine the next screen
    to display or to close the flow. You should return this response from your flow endpoint callback.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/guides/implementingyourflowendpoint#data_exchange_request>`_.
    - Use the :meth:`FlowRequest.respond` method to create a response for a request with the same version and flow token as the request.

    Example:

        >>> from pywa import WhatsApp
        >>> from pywa.types import FlowResponse

        >>> wa = WhatsApp(business_private_key="...", ...)
        >>> @wa.on_flow_request("/my-flow-endpoint")
        ... def my_flow_endpoint(_: WhatsApp, req: FlowRequest) -> FlowResponse:
        ...     return req.respond(  # shortcut for return FlowResponse(version=req.version, flow_token=req.flow_token, ...)
        ...         screen="SCREEN_ID",
        ...         data={"key": "value"},
        ...     )

    Attributes:
        version: The same version as the request.
        screen: The screen to display (if the flow is not closed).
        data: The data to send to the screen or to add to flow completion ``.response`` dict (default to empty dict).
        error_message: This will redirect the user to ``screen`` and will trigger a snackbar error with the ``error_message`` present (if the flow is not closed).
        flow_token: The flow token to close the flow (if ``close_flow`` is ``True``).
        close_flow: Whether to close the flow or just navigate to the screen (``flow_token`` must be provided if ``True``).
    """

    version: str
    data: _FlowResponseDataType = dataclasses.field(default_factory=dict)
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

    def to_dict(self) -> dict:
        data = self.data.copy()
        if not self.close_flow and self.error_message:
            data["error_message"] = self.error_message
        for key, val in data.items():
            if isinstance(val, DataSource):
                data[key] = val.to_dict()
            elif isinstance(val, Iterable) and not isinstance(val, (str, bytes)):
                data[key] = [
                    v.to_dict() if isinstance(v, (DataSource, NavigationItem)) else v
                    for v in val
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

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/error-codes#endpoint_error_codes>`_.
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
        ... def my_flow_endpoint(_: WhatsApp, req: FlowRequest) -> FlowResponse:
        ...     if req.flow_token == "v1.0":  # you see the token is no longer valid
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

    UNKNOWN = "UNKNOWN"


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class FlowJSONUpdateResult(SuccessResult):
    """
    Represents the result of updating a flow JSON.

    Attributes:
        success: Whether the operation was successful.
        validation_errors: The validation errors of the flow, if any.
    """

    validation_errors: tuple[FlowValidationError, ...]

    def __iter__(self):
        warnings.warn(
            "WhatsApp.update_flow_json() is no longer return (success, validation_errors) tuple, but FlowJSONUpdateResult object.",
            DeprecationWarning,
            stacklevel=2,
        )
        return iter((self.success, self.validation_errors))

    @classmethod
    def from_dict(cls, data: dict, **kwargs):
        return cls(
            success=data["success"],
            validation_errors=tuple(
                FlowValidationError.from_dict(e)
                for e in data.get("validation_errors", [])
            ),
        )


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

    def with_params(
        self,
        interactive: bool | None = None,
        flow_token: str | None = None,
        flow_action: Literal[
            FlowRequestActionType.NAVIGATE, FlowRequestActionType.DATA_EXCHANGE
        ]
        | None = None,
        flow_action_payload: dict | None = None,
        phone_number: str | None = None,
        debug: bool | None = None,
    ) -> str:
        """
        Configure the interactive Web Preview.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowsapi#preview>`_.

        Args:
            interactive: If true, the preview will run in interactive mode. Defaults to false.
            flow_token: It will be sent as part of each request. You should always verify that token on your server to block any other unexpected requests. Required for Flows with endpoint.
            flow_action: First action when Flow starts. data_exchange if it will make a request to the endpoint, or navigate if it won't (this will also require flow_action_payload to be provided).
            flow_action_payload: Initial screen data. Required if flow_action is navigate. Should be omitted otherwise.
            phone_number: Phone number that will be used to send the Flow, from which the public key will be used to encrypt the request payload. Required for Flows with endpoint.
            debug: Show actions in a separate panel while interacting with the preview.

        Returns:
            The URL of the preview with the parameters added.
        """
        params = {}

        if flow_token is not None:
            params["flow_token"] = flow_token
        if interactive is not None:
            params["interactive"] = str(interactive).lower()
        if flow_action is not None:
            params["flow_action"] = flow_action
        if flow_action_payload is not None:
            params["flow_action_payload"] = json.dumps(
                flow_action_payload, separators=(",", ":")
            )
        if phone_number is not None:
            params["phone_number"] = phone_number
        if debug is not None:
            params["debug"] = str(debug).lower()
        if not params:
            return self.url

        url_parts = list(urllib_parse.urlparse(self.url))
        query = dict(urllib_parse.parse_qsl(url_parts[4]))
        query.update(params)
        url_parts[4] = urllib_parse.urlencode(query)
        return str(urllib_parse.urlunparse(url_parts))


@dataclasses.dataclass(slots=True, kw_only=True)
class FlowDetails(utils.APIObject):
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
    @functools.cache
    def _api_fields(
        cls, invalidate_preview: bool | None, phone_number_id: str | None
    ) -> tuple[str, ...]:
        fields = list(super(FlowDetails, cls)._api_fields())
        if invalidate_preview is not None:
            fields[fields.index("preview")] = (
                f"preview.invalidate({'true' if invalidate_preview else 'false'})"
            )
        if phone_number_id is not None:
            fields[fields.index("health_status")] = (
                f"health_status.phone_number({phone_number_id})"
            )
        return tuple(fields)

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

    def publish(self) -> SuccessResult:
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
        if res := self._client.publish_flow(self.id):
            self.status = FlowStatus.PUBLISHED
        return res

    def delete(self) -> SuccessResult:
        """
        When the flow is in ``FlowStatus.DRAFT`` status, you can delete it.
            - A shortcut for :meth:`pywa.client.WhatsApp.delete_flow`.

        Returns:
            Whether the flow was deleted.

        Raises:
            FlowDeletingError: If this flow is already published.
        """
        if res := self._client.delete_flow(self.id):
            self.status = FlowStatus.DEPRECATED  # there is no `DELETED` status
        return res

    def deprecate(self) -> SuccessResult:
        """
        When the flow is in ``FlowStatus.PUBLISHED`` status, you can only deprecate it.
            - A shortcut for :meth:`pywa.client.WhatsApp.deprecate_flow`.

        Returns:
            Whether the flow was deprecated.

        Raises:
            FlowDeprecatingError: If this flow is not published or already deprecated.
        """
        if res := self._client.deprecate_flow(self.id):
            self.status = FlowStatus.DEPRECATED
        return res

    def get_assets(self) -> Result[FlowAsset]:
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
    ) -> SuccessResult:
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
    ) -> FlowJSONUpdateResult:
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
        res = self._client.update_flow_json(
            flow_id=self.id,
            flow_json=flow_json,
        )
        self.validation_errors = res.validation_errors or None
        return res


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

    UNKNOWN = "UNKNOWN"


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

    UNKNOWN = "UNKNOWN"


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


@dataclasses.dataclass(frozen=True, slots=True)
class CreatedFlow:
    """
    Represents a created flow.

    Attributes:
        id: The ID of the created flow.
        success: Whether the flow json is valid (Only if created with flow json).
        validation_errors: The validation errors of the flow json. Only available if success is ``False``.
    """

    id: str
    success: bool
    validation_errors: tuple[FlowValidationError, ...] | None

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data["id"],
            success=data.get("success", True),
            validation_errors=tuple(
                FlowValidationError.from_dict(e)
                for e in data.get("validation_errors", [])
            )
            or None,
        )


@dataclasses.dataclass(frozen=True, slots=True)
class MigratedFlow(utils.FromDict):
    """
    Successfully migrated flow.

    Attributes:
        source_id: The ID of the flow in the source.
        source_name: The name of the flow in the source.
        migrated_id: The ID of the new flow in the destination.
    """

    source_id: str
    source_name: str
    migrated_id: str


@dataclasses.dataclass(frozen=True, slots=True)
class MigratedFlowError(Exception, utils.FromDict):
    """
    Failed to migrate flow.

    - See `Flows API Troubleshooting <https://developers.facebook.com/docs/whatsapp/flows/reference/flowsapi#troubleshooting>`_.

    Attributes:
        source_name: The name of the flow in the source.
        error_code: The error code.
        error_message: The error message.
    """

    source_name: str
    error_code: str
    error_message: str


@dataclasses.dataclass(frozen=True, slots=True)
class MigrateFlowsResponse:
    """
    Represents the response of the migrate flows endpoint.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowsapi#migrate>`_.

    Attributes:
        migrated_flows: The flows that were successfully migrated.
        failed_flows: The flows that failed to migrate.
    """

    migrated_flows: tuple[MigratedFlow, ...]
    failed_flows: tuple[MigratedFlowError, ...]

    @classmethod
    def from_dict(cls, data: dict) -> MigrateFlowsResponse:
        return cls(
            migrated_flows=tuple(
                MigratedFlow.from_dict(flow) for flow in data.get("migrated_flows", [])
            ),
            failed_flows=tuple(
                MigratedFlowError.from_dict(flow)
                for flow in data.get("failed_flows", [])
            ),
        )


_UNDERSCORE_FIELDS = {
    "routing_model",
    "data_api_version",
    "data_channel_uri",
    "refresh_on_back",
}

_PY_TO_JSON_TYPES = {
    str: "string",
    bool: "boolean",  # MUST BE BEFORE int!!
    int: "number",
    float: "number",
}

_DATA_SOURCE_SKIP_FIELDS = {
    "on_select_action",
    "on-select-action",
    "on_unselect_action",
    "on-unselect-action",
}

_NAVIGATION_ITEM_SKIP_FIELDS = {
    "start",
    "end",
    "badge",
    "tags",
    "on-click-action",
}


class _FlowJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, _Expr):
            return o.to_str()
        elif isinstance(o, _ScreenDatasContainer):
            data = {}
            for item in o:
                if isinstance(item, ScreenDataUpdate):
                    data[item.key] = item.new_value
                    continue

                try:
                    data[item.key] = dict(
                        **self._get_json_type(item.example), __example__=item.example
                    )
                except KeyError as e:
                    raise ValueError(
                        f"ScreenData: Invalid example type {type(item.example)!r} for {item.key!r}."
                    ) from e
            return data
        elif isinstance(o, (DataSource, NavigationItem)):
            return o.to_dict()
        elif isinstance(o, datetime.date):
            return o.strftime("%Y-%m-%d")
        elif isinstance(o, re.Pattern):
            return o.pattern
        return super().default(o)

    def _get_json_type(
        self,
        example: str
        | int
        | float
        | bool
        | DataSource
        | Iterable[str | int | float | bool | DataSource | NavigationItem],
    ) -> dict:
        for (
            py_type,
            json_type,
        ) in _PY_TO_JSON_TYPES.items():  # check for subtypes - e.g. enum
            if isinstance(example, py_type):
                return {"type": json_type}

        if isinstance(example, (dict, DataSource)):
            return {"type": "object", "properties": self._get_obj_props(example)}
        elif isinstance(example, Iterable):
            try:
                first = next(iter(example))
            except StopIteration:
                raise ValueError("At least one example is required when using Iterable")
            if isinstance(first, (str, int, float, bool)):
                return {
                    "type": "array",
                    "items": self._get_json_type(first),
                }
            elif isinstance(first, (dict, DataSource, NavigationItem)):
                return {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": self._get_obj_props(first),
                    },
                }
            else:
                raise ValueError(f"Invalid example type {type(first)!r} for {first!r}.")
        else:
            raise KeyError(f"Invalid example type {type(example)!r} for {example!r}.")

    def _get_obj_props(self, item: dict | DataSource | NavigationItem):
        _skip_fields = (
            _DATA_SOURCE_SKIP_FIELDS
            if isinstance(item, DataSource)
            else _NAVIGATION_ITEM_SKIP_FIELDS
            if isinstance(item, NavigationItem)
            else ()
        )
        return {
            k: self._get_json_type(v)
            for k, v in (
                item.items() if isinstance(item, dict) else item.to_dict().items()
            )
            if v is not None and k not in _skip_fields
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

    screens: list[Screen]
    version: str | float | Literal[utils.Version.FLOW_JSON]
    data_api_version: str | float | Literal[utils.Version.FLOW_DATA_API] | None = None
    routing_model: dict[str, list[str]] | None = None
    data_channel_uri: str | None = None

    def __post_init__(self):
        self.version = str(self.version)
        utils.Version.FLOW_JSON.validate_min_version(self.version)
        if self.data_api_version:
            self.data_api_version = str(self.data_api_version)
            utils.Version.FLOW_DATA_API.validate_min_version(self.data_api_version)

    def to_json(self):
        return json.dumps(
            dataclasses.asdict(
                obj=self,
                dict_factory=lambda d: {
                    k.replace("_", "-").rstrip("-")
                    if k not in _UNDERSCORE_FIELDS
                    else k: v
                    for (k, v) in d
                    if v is not None
                },
            ),
            cls=_FlowJSONEncoder,
            indent=4,
            ensure_ascii=False,
        )


_TO_DICT_FACTORY = lambda d: {k.replace("_", "-"): v for (k, v) in d if v is not None}


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
        on_select_action: The update data action to perform when the data source is selected. (added in v6.0).
        on_unselect_action: The update data action to perform when the data source is unselected. (added in v6.0).
    """

    id: str | ScreenDataRef[str] | ComponentRef[str]
    title: str | ScreenDataRef[str] | ComponentRef[str]
    on_select_action: UpdateDataAction | None = None
    on_unselect_action: UpdateDataAction | None = None
    description: str | ScreenDataRef[str] | ComponentRef[str] | None = None
    metadata: str | ScreenDataRef[str] | ComponentRef[str] | None = None
    enabled: bool | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    image: str | ScreenDataRef[str] | ComponentRef[str] | None = None
    alt_text: str | ScreenDataRef[str] | ComponentRef[str] | None = None
    color: str | ScreenDataRef[str] | ComponentRef[str] | None = None

    def to_dict(self):
        """Called when used in :class:`FlowResponse`."""
        return dataclasses.asdict(
            obj=self,
            dict_factory=_TO_DICT_FACTORY,
        )


_ScreenDataValTypeVar = TypeVar(
    "_ScreenDataValTypeVar",
    # bound=_ScreenDataValType,
)


class ScreenData(Generic[_ScreenDataValTypeVar]):
    """
    Represents a screen data that a screen should get from the previous screen or from the data endpoint.

    - You can use the ``.ref`` property or the :class:`ScreenDataRef` to reference this data in the screen children or in the action payloads.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#dynamic-properties>`_.

    Example:

        >>> Screen(
        ...     id='START',
        ...     data=[
        ...         dynamic_welcome := ScreenData(key='welcome', example='Welcome to my store!')
        ...         is_email_required := ScreenData(key='is_email_required', example=False)
        ...     ],
        ...     layout=Layout(children=[Form(children=[
        ...         TextHeading(text=dynamic_welcome.ref, ...),
        ...         TextInput(required=is_email_required.ref, input_type=InputType.EMAIL, ...)
        ...     ])])
        ... )
    """

    __slots__ = "key", "example"

    def __init__(
        self,
        *,
        key: str,
        example: _ScreenDataValTypeVar,
    ) -> None:
        """
        Initialize the screen data.

        Args:
            key: The key of the data (if you using ``:=`` to assign this object, the convention is to use the same key as the variable name).
            example: The example of the data that the screen should get from the previous screen or from the data endpoint.
        """
        self.key = key
        self.example = example

    @property
    def ref(self) -> ScreenDataRef[_ScreenDataValTypeVar]:
        """
        The refernece for this data to use in the same screen children.
            - Use this property to reference this data in the screen children. Use the :meth:`ref_in(screen)` to reference this data in ANOTHER screen children.

        Example:

            >>> FlowJSON(
            ...     screens=[
            ...         Screen(
            ...             id='START',
            ...             data=[dynamic_welcome := ScreenData(key='welcome', example='Welcome to my store!')],
            ...             layout=Layout(children=[TextHeading(text=dynamic_welcome.ref, ...)])  # Use the .ref here
            ...         )
            ...     ],
            ...     ...
            ... )
        """
        return ScreenDataRef(key=self.key)

    def ref_in(self, screen: Screen | str) -> ScreenDataRef[_ScreenDataValTypeVar]:
        """
        The key for this data to use in ANOTHER screen children.
            - If you want to reference this data in the same screen children, use the :meth:`ref` property.
            - A shortcut for :class:`ScreenDataRef` with this key and screen.
            - You can also use ``screen / data.ref`` to reference this data in other screens.
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
            ...             layout=Layout(
            ...                 children=[
            ...                     TextHeading(text=dynamic_welcome.ref_in("START"), ...),  # using the `.ref_in(screen)` method
            ...                     TextHeading(text=start/dynamic_welcome.ref, ...)  # using the `screen / data.ref` syntax
            ...                 ]
            ...             )
            ...         )
            ...     ],
            ...     ...
            ... )

        Args:
            screen: The screen id to reference this data in its children.
        """
        return ScreenDataRef(key=self.key, screen=screen)

    def update(
        self, new_value: _ScreenDataValTypeVar
    ) -> ScreenDataUpdate[_ScreenDataValTypeVar]:
        """
        Update the value of this data. Use this inside the :class:`UpdateDataAction` ``.payload``.

        Example::

            >>> is_visible = ScreenData(key='is_visible', example=True)
            >>> UpdateDataAction(payload=[is_visible.update(False)])

        Args:
            new_value: The new value of the data.

        Returns:
            The update action for this data.
        """
        return ScreenDataUpdate(key=self.key, new_value=new_value)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(key={self.key!r}, example={self.example!r})"


class ScreenDataUpdate(Generic[_ScreenDataValTypeVar]):
    """
    Represents an update action for a screen data.

    - Use the :meth:`ScreenData.update` method to create an instance of this class from a :class:`ScreenData`.

    .. code-block:: python
        :emphasize-lines: 4, 14-19, 23
        :linenos:

        Screen(
            id="DEMO_SCREEN",
            data=[
                is_txt_visible := ScreenData(
                    key="is_txt_visible",
                    example=False,
                ),
            ],
            layout=Layout(
                children=[
                    OptIn(
                        label="Show the text",
                        name="show_txt",
                        on_select_action=UpdateDataAction(
                            payload=[is_txt_visible.update(True)]  # a much cleaner way
                        ),
                        on_unselect_action=UpdateDataAction(
                            payload=[ScreenDataUpdate(key="is_txt_visible", new_value=False)]  # only when you don't have access to the `ScreenData` object
                        ),
                    ),
                    TextBody(
                        text="You clicked the button!",
                        visible=is_txt_visible.ref,
                    ),
                ]
            )
        )
    """

    __slots__ = "key", "new_value"

    def __init__(
        self,
        *,
        key: str,
        new_value: _ScreenDataValTypeVar,
    ) -> None:
        """
        Initialize the screen data update

        Args:
            key: The key of the data to update (The same key as the :class:`ScreenData` object).
            new_value: The new value of the data.
        """
        self.key = key
        self.new_value = new_value

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(key={self.key!r}, new_value={self.new_value!r})"
        )


class _ScreenDatasContainer:
    """A wrapper to prevent ``dataclasses.asdict()`` from converting ScreenData|Update objects."""

    def __init__(self, datas: list[ScreenData | ScreenDataUpdate]):  # not mixed
        self._datas = datas

    def __iter__(self):
        return iter(self._datas)

    def __repr__(self):
        return f"ScreenDatasContainer({self._datas})"


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
        id: Unique identifier of the screen which works as a page url. ``SUCCESS`` is a reserved keyword and should not be used as a screen id.
        title: Screen level attribute that is rendered in the top navigation bar.
        data: Declaration of dynamic data that this screen should get from the previous screen or from the flow endpoint.
         In the screen children and in :class:`DataExchangeAction` ``.payload``, you can use the :attr:`~ScreenData.ref` or :class:`ScreenDataRef`
         to reference this data.
        terminal: The business flow is the end state machine. It means that each Flow should have a terminal state where
         we terminate the experience and have the Flow completed. Multiple screens can be marked as terminal. It's mandatory to have a :class:`Footer` component on the terminal screen.
         Multiple screens can be marked as terminal. It's mandatory to have a :class:`Footer` on the terminal screen.
        refresh_on_back: Whether to trigger a :class:`FlowRequest` (``action`` will be :class:`FlowRequestActionType.BACK`) with the flow endpoint when the user presses
         the back button while on this screen. The property is useful when you need to reevaluate the screen data when returning to the previous screen (Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#additional-information-on-refresh-on-back>`_).
        layout: Associated screen UI Layout that is shown to the user (Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#layout>`_).
        success: Defaults to true. A Flow can have multiple terminal screens with different business outcomes. This property marks whether terminating on a terminal screen should be considered a successful business outcome.
        sensitive: This array contains the names of the fields in the screen that contain sensitive data, and should be hidden in the response summary displayed to the user. (added in v5.1)
    """

    id: str
    title: str | None = None
    data: list[ScreenData] | dict[str, dict] | None = None
    terminal: bool | None = None
    success: bool | None = None
    refresh_on_back: bool | None = None
    layout: Layout
    sensitive: list[str] | None = None

    def __post_init__(self):
        # preventing `data` from being converted to a Iterable[dict] by `dataclasses.asdict()`
        # this is because we need to extract the key attr from the ScreenData and use it as the key in the json data obj
        self.data = (
            _ScreenDatasContainer(self.data)  # type: ignore
            if isinstance(self.data, Iterable) and not isinstance(self.data, dict)
            else self.data
        )

    def __truediv__(self, ref: _RefT) -> _RefT:
        """A shortcut to reference screen data / form components in this screen."""
        return ref.__class__(ref._field, screen=self.id)  # type: ignore


class LayoutType(utils.StrEnum):
    """
    The type of layout that is used to display the components.
        - Currently, only ``LayoutType.SINGLE_COLUMN`` is supported.

    Attributes:
        SINGLE_COLUMN: A vertical flexbox container that stacks the components in a single column.
    """

    _check_value = None
    _modify_value = None

    SINGLE_COLUMN = "SingleColumnLayout"

    UNKNOWN = "UNKNOWN"


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
    children: list[Form | Component | dict[str, Any]]


class Component(abc.ABC):
    """Base class for all components"""

    @property
    @abc.abstractmethod
    def type(self) -> TemplateComponentType: ...

    @property
    @abc.abstractmethod
    def visible(self) -> bool | str | Condition | None: ...

    def __post_init__(self):
        if isinstance(self.visible, Condition):
            self.visible.wrap_with_backticks = (
                True  # visible condition should be wrapped with backticks
            )


class TemplateComponentType(utils.StrEnum):
    """Internal component types"""

    _check_value = None
    _modify_value = None

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
    CALENDAR_PICKER = "CalendarPicker"
    IMAGE = "Image"
    IMAGE_CAROUSEL = "ImageCarousel"
    PHOTO_PICKER = "PhotoPicker"
    DOCUMENT_PICKER = "DocumentPicker"
    IF = "If"
    SWITCH = "Switch"
    NAVIGATION_LIST = "NavigationList"
    CHIPS_SELECTOR = "ChipsSelector"

    UNKNOWN = "UNKNOWN"


class _Expr(abc.ABC):
    """Base for refs, conditions, and expressions"""

    @abc.abstractmethod
    def to_str(self) -> str: ...

    def __str__(self) -> str:
        return self.to_str()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.to_str()})"

    @staticmethod
    def _format_value(val: _Expr | bool | int | float | str) -> str:
        if isinstance(val, _Expr):
            return val.to_str()
        elif isinstance(val, str):
            return f"'{val}'"
        elif isinstance(val, bool):
            return str(val).lower()
        return str(val)


class _Math(_Expr, abc.ABC):
    """Base for math expressions"""

    def _to_math(self, left: _MathT, operator: str, right: _MathT) -> MathExpression:
        return MathExpression(
            f"({self._format_value(left)} {operator} {self._format_value(right)})"
        )

    def __add__(self, other: _MathT) -> MathExpression:
        return self._to_math(self, "+", other)

    def __radd__(self, other: _MathT) -> MathExpression:
        return self._to_math(other, "+", self)

    def __sub__(self, other: _MathT) -> MathExpression:
        return self._to_math(self, "-", other)

    def __rsub__(self, other: _MathT) -> MathExpression:
        return self._to_math(other, "-", self)

    def __mul__(self, other: _MathT) -> MathExpression:
        return self._to_math(self, "*", other)

    def __rmul__(self, other: _MathT) -> MathExpression:
        return self._to_math(other, "*", self)

    def __truediv__(self, other: _MathT) -> MathExpression:
        return self._to_math(self, "/", other)

    def __rtruediv__(self, other: _MathT) -> MathExpression:
        return self._to_math(other, "/", self)

    def __mod__(self, other: _MathT) -> MathExpression:
        return self._to_math(self, "%", other)

    def __rmod__(self, other: _MathT) -> MathExpression:
        return self._to_math(other, "%", self)


class _Combine(_Expr, abc.ABC):
    """ "Base for combining refs and conditions"""

    def _get_left_right(self, right: Ref | Condition) -> tuple[str, str]:
        return self.to_str() if isinstance(
            self, Ref
        ) else self._expression, right.to_str() if isinstance(
            right, Ref
        ) else right._expression

    def __and__(self, other: Ref | Condition) -> Condition:
        left, right = self._get_left_right(other)
        return Condition(f"({left} && {right})")

    def __or__(self, other: Ref | Condition) -> Condition:
        left, right = self._get_left_right(other)
        return Condition(f"({left} || {right})")

    def __invert__(self) -> Condition:
        return Condition(
            f"!{self.to_str() if isinstance(self, Ref) else self._expression}"
        )


class Ref(_Math, _Combine, Generic[_ScreenDataValTypeVar]):
    """Base class for all references"""

    def __init__(self, prefix: str, field: str, screen: Screen | str | None = None):
        self._prefix = prefix
        self._field = field
        self._screen = (
            f"screen.{screen.id if isinstance(screen, Screen) else screen}."
            if screen
            else ""
        )

    def to_str(self) -> str:
        return "${%s%s.%s}" % (
            self._screen,
            self._prefix,
            self._field,
        )

    def _to_condition(
        self, right: Ref | bool | int | float | str, operator: str
    ) -> Condition:
        return Condition(f"({self.to_str()} {operator} {self._format_value(right)})")

    def __eq__(self, other: Ref | bool | int | float | str) -> Condition:
        return self._to_condition(other, "==")

    def __ne__(self, other: Ref | bool | int | float | str) -> Condition:
        return self._to_condition(other, "!=")

    def __gt__(self, other: Ref | int | float) -> Condition:
        return self._to_condition(other, ">")

    def __ge__(self, other: Ref | int | float) -> Condition:
        return self._to_condition(other, ">=")

    def __lt__(self, other: Ref | int | float) -> Condition:
        return self._to_condition(other, "<")

    def __le__(self, other: Ref | int | float) -> Condition:
        return self._to_condition(other, "<=")


class MathExpression(_Math):
    """
    This class automatically created when using the arithmetic operators on :class:`Ref` objects.

    Example::

        # Display the year you born in by subtracting the age from 2025:
        >>> age = TextInput(name="age", input_type=InputType.NUMBER)
        >>> text = TextBody(text=FlowStr("You born in {year}", year=2025 - age.ref))

        # Calculating tip:
        >>> bill = TextInput(name="bill", input_type=InputType.NUMBER)
        >>> tip_percent = TextInput(name="tip_percent", input_type=InputType.NUMBER)
        >>> total = TextBody(text=FlowStr("Total: {total}", total=bill.ref + (bill.ref * tip_percent.ref / 100)))


    Supported Operators:

    .. role:: python(code)
       :language: python

    .. list-table::
        :widths: 10 5 15 30
        :header-rows: 1

        * - Operator
          - Symbol
          - Types allowed
          - Python

        * - Add
          - ``+``
          - :class:`int`, :class:`float`
          - :python:`age.ref + 20`
        * - Subtract
          - ``-``
          - :class:`int`, :class:`float`
          - :python:`age.ref - 20`
        * - Multiply
          - ``*``
          - :class:`int`, :class:`float`
          - :python:`age.ref * 20`
        * - Divide
          - ``/``
          - :class:`int`, :class:`float`
          - :python:`age.ref / 20`
        * - Modulus
          - ``%``
          - :class:`int`, :class:`float`
          - :python:`age.ref % 20`
    """

    def __init__(self, expression: str):
        self._expression = expression

    def __repr__(self) -> str:
        return f"MathExpression({self._expression})"

    def to_str(self) -> str:
        return self._expression


_MathT: TypeAlias = _Math | MathExpression | Ref | int | float

_RefT = TypeVar("_RefT", bound=Ref)


class Condition(_Combine):
    """
    This class automatically created when using the comparison operators on :class:`Ref` objects.

    Example::


        >>> age = TextInput(name="age", input_type=InputType.NUMBER)
        >>> opt_in = OptIn(name="opt_in")
        >>> text = TextBody(text=..., visible=(age.ref > 20) & opt_in.ref)


    Supported Operators:

    .. role:: python(code)
       :language: python

    .. list-table::
        :widths: 10 5 15 30
        :header-rows: 1

        * - Operator
          - Symbol
          - Types allowed
          - Python
        * - Equal
          - ``==``
          - :class:`str`, :class:`int`, :class:`float`
          - :python:`age.ref == 20`
        * - Not Equal
          - ``!=``
          - :class:`str`, :class:`int`, :class:`float`
          - :python:`age.ref != 20`
        * - Greater
          - ``>``
          - :class:`int`, :class:`float`
          - :python:`age.ref > 20`
        * - Greater Equal
          - ``>=``
          - :class:`int`, :class:`float`
          - :python:`age.ref >= 20`
        * - Less
          - ``<``
          - :class:`int`, :class:`float`
          - :python:`age.ref < 20`
        * - Less Equal
          - ``<=``
          - :class:`int`, :class:`float`
          - :python:`age.ref <= 20`
        * - And
          - ``&&``
          - <Condition>
          - :python:`(age.ref > 20) & opt_in.ref`
        * - Or
          - ``||``
          - <Condition>
          - :python:`(age.ref > 20) | opt_in.ref`
        * - Not
          - ``!``
          - <Condition>
          - :python:`~opt_in.ref`
    """

    def __init__(self, expression: str):
        self._expression = expression
        self.wrap_with_backticks = False

    def __repr__(self) -> str:
        return f"Condition({self._expression})"

    def to_str(self) -> str:
        return (
            self._expression
            if not self.wrap_with_backticks
            else f"`{self._expression}`"
        )


class ScreenDataRef(Ref, Generic[_ScreenDataValTypeVar]):
    """
    Represents a :class:`ScreenData` reference (converts to ``${data.<key>}`` | ``${screen.<screen>.data.<key>}``).

    Example:
            - Hint: use this class directly only if you don't have access to the :class:`ScreenData` object.
            - Hint: use the ``.ref`` property of :class:`ScreenData` to get reference to a ScreenData.
            - Hint: use the ``.ref_in(screen)`` method of :class:`ScreenData` to get the data ref from another screen (or ``screen/ref``).

            >>> FlowJSON(
            ...     screens=[
            ...         other := Screen(id='OTHER', data=[is_visible := ScreenData(key='is_visible', example=True)]),
            ...         Screen(
            ...             id='START',
            ...             data=[welcome := ScreenData(key='welcome', example='Welcome to my store!')],
            ...             layout=Layout(children=[
            ...                 TextHeading(
            ...                     text=welcome.ref, # data in the same screen
            ...                     visible=is_visible.ref_in(other) # data from other screen
            ...                 ),
            ...                 TextBody(
            ...                     text=ScreenDataRef(key='welcome', screen='START'), # using the class directly
            ...             ])
            ...         )
            ...     ]
            ... )

    Args:
        key: The key to get from the :class:`Screen` .data attribute.
        screen: The screen that contains the data (needed if the data is from another screen). Added in v4.0.
    """

    def __init__(self, key: str, screen: Screen | str | None = None):
        super().__init__(prefix="data", field=key, screen=screen)


class ComponentRef(Ref, Generic[_ScreenDataValTypeVar]):
    """
    Represents a componenent reference variable (converts to ``${form.<child>}`` | ``${screen.<screen>.form.<child>}``).

    Example:

        - Hint: use this class directly only if you don't have access to the component object.
        - Hint: use the ``.ref`` property of each component to get a reference to this component.
        - Hint: use the ``.ref_in(screen)`` method of each component to get the component reference variable of that component with the given screen name.

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
        ...                 TextBody(text=phone.ref, ...),  # component reference from the same screen
        ...                 TextCaption(text=email.ref_in(other), ...)  # component reference from another screen
        ...                 TextHeading(text=ComponentRef('phone', screen='START'), ...)  # using the class directly
        ...             ])
        ...         )
        ...     ]
        ... )

    Args:
        component_name: The name of the component to get the value from.
        screen: The name of the screen that contains the form. Added in v4.0.
    """

    def __init__(self, component_name: str, screen: Screen | str | None = None):
        super().__init__(prefix="form", field=component_name, screen=screen)


class FlowStr(_Expr):
    """
    Dynamic string that uses variables and math expressions. This is a helper class to avoid all the
    escaping and wrapping with quotes when using string concatenation.

    - Added in v6.0.

    Example::

            >>> FlowJSON(
            ...     screens=[
            ...         Screen(
            ...             id='START',
            ...             layout=Layout(children=[
            ...                 age := TextInput(name='age', input_type=InputType.NUMBER),
            ...                 email := TextInput(name='email', input_type=InputType.EMAIL),
            ...                 TextHeading(text=FlowStr("Your age is {age} and your email is {email}", age=age.ref, email=email.ref), ...)
            ...             ])
            ...         )
            ...     ]
            ... )

            >>> FlowJSON(
            ...     screens=[
            ...         Screen(
            ...             id='START',
            ...             layout=Layout(children=[
            ...                 bill := TextInput(name='bill', input_type=InputType.NUMBER),
            ...                 tip := TextInput(name='tip', input_type=InputType.NUMBER),
            ...                 TextHeading(text=FlowStr("Your total bill is {bill}", bill=bill.ref + (bill.ref * tip.ref / 100)), ...)
            ...             ])
            ...         )
            ...     ]
            ... )

    """

    def __init__(self, string: str, **variables: Ref | MathExpression):
        """
        Initialize the dynamic string.

        Args:
            string: The string with placeholders for the variables.
            **variables: The variables to replace in the string.
        """
        self.string = string
        self.variables = variables

    def to_str(self) -> str:
        escaped = re.sub(r"(?<!\\)([`'])", r"\\\\\1", self.string)
        wrapped = re.sub(r"([^{}]+)(?=\{|$)", r" '\1' ", escaped)
        return f"`{wrapped.format(**self.variables)}`"


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

    type: TemplateComponentType = dataclasses.field(
        default=TemplateComponentType.FORM, init=False, repr=False
    )
    visible: None = dataclasses.field(default=None, init=False, repr=False)
    name: str
    children: list[Component | FormComponent | dict[str, Any]]
    init_values: dict[str, Any] | str | ScreenDataRef[dict[str, Any]] | None = None
    error_messages: dict[str, str] | str | ScreenDataRef[dict[str, str]] | None = None

    def __post_init__(self):
        if not self.children:
            raise ValueError("At least one child is required")

        # Extract init-value's from children
        init_values = self.init_values or {}
        for child in self.children:
            if getattr(child, "init_value", None) is not None:
                if isinstance(self.init_values, Ref | str):
                    raise ValueError(
                        f"No need to set init value for {child.name!r} if form init values is a dynamic ScreenDataRef"
                    )
                if child.name in init_values:
                    raise ValueError(
                        f"Duplicate init value for {child.name!r} in form {self.name!r}"
                    )
                init_values[child.name] = child.init_value
                child.init_value = None
        self.init_values = init_values or None

        # Extract error-message's from children
        error_messages = self.error_messages or {}
        for child in self.children:
            if getattr(child, "error_message", None) is not None:
                if isinstance(self.error_messages, Ref | str):
                    raise ValueError(
                        f"No need to set error msg for {child.name!r} if form error messages is a dynamic ScreenDataRef"
                    )
                if child.name in error_messages:
                    raise ValueError(
                        f"Duplicate error msg for {child.name!r} in form {self.name!r}"
                    )
                error_messages[child.name] = child.error_message
                child.error_message = None
        self.error_messages = error_messages or None


class FormComponent(Component, abc.ABC, Generic[_ScreenDataValTypeVar]):
    """Base class for all components that must be inside a form (if FlowJSON version is below 4.0)"""

    @property
    @abc.abstractmethod
    def name(self) -> str: ...

    @property
    @abc.abstractmethod
    def label(self) -> str | FlowStr | ScreenDataRef[str] | ComponentRef[str]: ...

    @property
    @abc.abstractmethod
    def required(self) -> bool | str | ScreenDataRef[bool] | None: ...

    @property
    @abc.abstractmethod
    def enabled(self) -> bool | str | ScreenDataRef[bool] | None: ...

    @property
    @abc.abstractmethod
    def init_value(
        self,
    ) -> (
        bool
        | str
        | ScreenDataRef[_ScreenDataValTypeVar]
        | ComponentRef[_ScreenDataValTypeVar]
        | None
    ): ...

    @property
    def ref(self) -> ComponentRef[_ScreenDataValTypeVar]:
        """
        The reference variable for this component.
            - Use this when the reference is in the same screen. Use ``.ref_in(screen)`` when the reference is in another screen.
            - A shortcut for :class:`ComponentRef` with this component name.

        Example:

            >>> FlowJSON(
            ...     screens=[
            ...         Screen(
            ...             id='START',
            ...             layout=Layout(children=[
            ...                 Form(children=[
            ...                     text_input := TextInput(name='email', ...),
            ...                     TextHeading(text="Your email is:", ...)
            ...                     TextCaption(text=text_input.ref, ...)
            ...                 ]),
            ...                 Footer(label='Submit', action=Action(payload={'email': text_input.ref}))
            ...         ])
            ...     ]
            ... )
        """
        return ComponentRef(self.name)

    def ref_in(self, screen: Screen | str) -> ComponentRef[_ScreenDataValTypeVar]:
        """
        The component reference variable for this component in another screen.
            - Use ``.ref`` property when the reference is in the same screen.
            - You can also use ``screen/component.ref`` to get the reference variable in another screen.
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
            ...                 TextCaption(text=email.ref_in('OTHER'), ...)  # using the `.ref_in(screen)` method
            ...                 TextCaption(text=other/email.ref, ...)  # using the screen/component.ref syntax
            ...             ])
            ...         )
            ...     ]
            ... )

        Args:
            screen: The screen that contains the component.
        """
        return ComponentRef(component_name=self.name, screen=screen)


class TextComponent(Component, abc.ABC):
    """
    Base class for all text components

    https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#text
    """

    @property
    @abc.abstractmethod
    def text(self) -> str | FlowStr | ScreenDataRef[str] | ComponentRef[str]: ...


class FontWeight(utils.StrEnum):
    """
    The text weight

    Attributes:
        BOLD: **Bold text**
        ITALIC: `Italic text`
        BOLD_ITALIC: Bold and italic text
        NORMAL: Normal text
    """

    _check_value = str.islower
    _modify_value = str.lower

    BOLD = "bold"
    ITALIC = "italic"
    BOLD_ITALIC = "bold_italic"
    NORMAL = "normal"

    UNKNOWN = "UNKNOWN"


@dataclasses.dataclass(slots=True, kw_only=True)
class TextHeading(TextComponent):
    """
    Represents text that is displayed as a heading.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#heading>`_.

    Example:

        >>> TextHeading(text='Heading', visible=True)

    Attributes:
        text: The text of the heading. Limited to 80 characters.
        visible: Whether the heading is visible or not. Default to ``True``,
    """

    type: TemplateComponentType = dataclasses.field(
        default=TemplateComponentType.TEXT_HEADING, init=False, repr=False
    )
    text: str | FlowStr | ScreenDataRef[str] | ComponentRef[str]
    visible: bool | Condition | ScreenDataRef[bool] | ComponentRef[bool] | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class TextSubheading(TextComponent):
    """
    Represents text that is displayed as a subheading.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#subheading>`_.

    Example:

        >>> TextSubheading(text='Subheading', visible=True)

    Attributes:
        text: The text of the subheading. Limited to 80 characters.
        visible: Whether the subheading is visible or not. Default to ``True``,
    """

    type: TemplateComponentType = dataclasses.field(
        default=TemplateComponentType.TEXT_SUBHEADING, init=False, repr=False
    )
    text: str | FlowStr | ScreenDataRef[str] | ComponentRef[str]
    visible: bool | Condition | ScreenDataRef[bool] | ComponentRef[bool] | None = None


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
        text: The text of the body. Limited to 4096 characters.
        markdown: Whether the text is markdown or not (Added in v5.1).
        font_weight: The weight of the text.
        strikethrough: Whether the text is strikethrough or not.
        visible: Whether the body is visible or not. Default to ``True``,
    """

    type: TemplateComponentType = dataclasses.field(
        default=TemplateComponentType.TEXT_BODY, init=False, repr=False
    )
    text: (
        str
        | FlowStr
        | list[str | FlowStr]
        | ScreenDataRef[str]
        | ScreenDataRef[list[str]]
        | ComponentRef[str]
    )
    markdown: bool | None = None
    font_weight: FontWeight | str | ScreenDataRef[str] | ComponentRef[str] | None = None
    strikethrough: bool | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    visible: bool | Condition | ScreenDataRef[bool] | ComponentRef[bool] | None = None


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
        text: The text of the caption (array of strings supported since v5.1). Limited to 4096 characters.
        markdown: Whether the text is markdown or not (Added in v5.1).
        font_weight: The weight of the text.
        strikethrough: Whether to strike through the text or not.
        visible: Whether the caption is visible or not. Default to ``True``,
    """

    type: TemplateComponentType = dataclasses.field(
        default=TemplateComponentType.TEXT_CAPTION, init=False, repr=False
    )
    text: (
        str
        | FlowStr
        | list[str | FlowStr]
        | ScreenDataRef[str | list[str]]
        | ComponentRef[str]
    )
    markdown: bool | None = None
    font_weight: FontWeight | str | ScreenDataRef[str] | ComponentRef[str] | None = None
    strikethrough: bool | ScreenDataRef[str] | ComponentRef[str] | None = None
    visible: bool | Condition | ScreenDataRef[bool] | ComponentRef[bool] | None = None


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
        text: The markdown text (array of strings supported).
        visible: Whether the caption is visible or not. Default to ``True``,
    """

    type: TemplateComponentType = dataclasses.field(
        default=TemplateComponentType.RICH_TEXT, init=False, repr=False
    )
    text: (
        str
        | FlowStr
        | list[str | FlowStr]
        | ScreenDataRef[str]
        | ComponentRef[str]
        | ScreenDataRef[list[str]]
    )
    visible: bool | Condition | ScreenDataRef[bool] | ComponentRef[bool] | None = None


class TextEntryComponent(FormComponent[str], abc.ABC):
    """
    Base class for all text entry components

    https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#textentry
    """

    @property
    @abc.abstractmethod
    def helper_text(
        self,
    ) -> str | FlowStr | ScreenDataRef[str] | ComponentRef[str] | None: ...

    @property
    @abc.abstractmethod
    def error_message(self) -> str | ScreenDataRef[str] | ComponentRef[str] | None: ...


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

    _check_value = str.islower
    _modify_value = str.lower

    TEXT = "text"
    NUMBER = "number"
    EMAIL = "email"
    PASSWORD = "password"
    PASSCODE = "passcode"
    PHONE = "phone"

    UNKNOWN = "UNKNOWN"


class LabelVariant(utils.StrEnum):
    """
    The label variant of the text entry component.

    Attributes:
        LARGE: Label will have a more prominent style and will be displayed across multiple lines if needed.
    """

    _check_value = str.islower
    _modify_value = str.lower

    LARGE = "large"

    UNKNOWN = "UNKNOWN"


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
        name: The unique name (id) for this component.
        label: The label of the text input. Limited to 20 characters.
        input_type: The input type of the text input (for keyboard layout and validation rules).
        label_variant: Display the label in a more prominent style and allow it to be displayed across multiple lines if needed. Added in v7.0.
        pattern: The regex pattern to validate the text input. Added in v6.2.
        required: Whether the text input is required or not.
        min_chars: The minimum number of characters allowed in the text input.
        max_chars: The maximum number of characters allowed in the text input.
        helper_text: The helper text of the text input. Limited to 80 characters.
        enabled: Whether the text input is enabled or not. Default to ``True``.
        visible: Whether the text input is visible or not. Default to ``True``.
        init_value: The default value of the text input.
        error_message: The error message of the text input.
    """

    type: TemplateComponentType = dataclasses.field(
        default=TemplateComponentType.TEXT_INPUT, init=False, repr=False
    )
    name: str
    label: str | FlowStr | ScreenDataRef[str] | ComponentRef[str]
    input_type: InputType | str | ScreenDataRef[str] | ComponentRef[str] | None = None
    label_variant: (
        LabelVariant | str | ScreenDataRef[str] | ComponentRef[str] | None
    ) = None
    pattern: str | re.Pattern | ScreenDataRef[str] | ComponentRef[str] | None = None
    required: bool | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    min_chars: int | ScreenDataRef[int] | None = None
    max_chars: int | ScreenDataRef[int] | None = None
    helper_text: str | FlowStr | ScreenDataRef[str] | ComponentRef[str] | None = None
    enabled: bool | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    visible: bool | Condition | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    init_value: str | ScreenDataRef[str] | ComponentRef[str] | None = None
    error_message: str | ScreenDataRef[str] | ComponentRef[str] | None = None


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
        name: The unique name (id) for this component.
        label: The label of the text area. Limited to 20 characters.
        label_variant: Display the label in a more prominent style and allow it to be displayed across multiple lines if needed. Added in v7.0.
        required: Whether the text area is required or not.
        max_length: The maximum number of characters allowed in the text area.
        helper_text: The helper text of the text area. Limited to 80 characters.
        enabled: Whether the text area is enabled or not. Default to ``True``.
        visible: Whether the text area is visible or not. Default to ``True``.
        init_value: The default value of the text area.
        error_message: The error message of the text area.
    """

    type: TemplateComponentType = dataclasses.field(
        default=TemplateComponentType.TEXT_AREA, init=False, repr=False
    )
    name: str
    label: str | FlowStr | ScreenDataRef[str] | ComponentRef[str]
    label_variant: (
        LabelVariant | str | ScreenDataRef[str] | ComponentRef[str] | None
    ) = None
    required: bool | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    max_length: int | ScreenDataRef[int] | None = None
    helper_text: str | FlowStr | ScreenDataRef[str] | ComponentRef[str] | None = None
    enabled: bool | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    visible: bool | Condition | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    init_value: str | ScreenDataRef[str] | ComponentRef[str] | None = None
    error_message: str | ScreenDataRef[str] | ComponentRef[str] | None = None


class MediaSize(utils.StrEnum):
    """
    The media size of the image.

    Attributes:
        REGULAR: Regular size
        LARGE: Large size
    """

    _check_value = str.islower
    _modify_value = str.lower

    REGULAR = "regular"
    LARGE = "large"

    UNKNOWN = "UNKNOWN"


@dataclasses.dataclass(slots=True, kw_only=True)
class CheckboxGroup(FormComponent[list[str]]):
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
        name: The unique name (id) for this component.
        data_source: The data source of the checkbox group.
        label: The label of the checkbox group. Limited to 30 characters. Required starting from v4.0.
        description: The description of the checkbox group. Limited to 300 characters. Added in v4.0.
        min_selected_items: The minimum number of items that can be selected. Minimum value is 1.
        max_selected_items: The maximum number of items that can be selected. Maximum value is 20.
        required: Whether the checkbox group is required or not.
        visible: Whether the checkbox group is visible or not. Default to ``True``.
        enabled: Whether the checkbox group is enabled or not. Default to ``True``.
        init_value: The default values (IDs of the data sources).
        media_size: The media size of the image. Added in v5.0.
        on_select_action: The action to perform when an item is selected.
        on_unselect_action: The action to perform when an item is unselected. Added in v6.0.
    """

    type: TemplateComponentType = dataclasses.field(
        default=TemplateComponentType.CHECKBOX_GROUP, init=False, repr=False
    )
    name: str
    data_source: list[DataSource] | ScreenDataRef[list[DataSource]]
    label: str | FlowStr | ScreenDataRef[str] | ComponentRef[str] | None = None
    description: str | FlowStr | ScreenDataRef[str] | ComponentRef[str] | None = None
    min_selected_items: int | ScreenDataRef[int] | None = None
    max_selected_items: int | ScreenDataRef[int] | None = None
    required: bool | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    visible: bool | Condition | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    enabled: bool | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    init_value: list[str] | ScreenDataRef[list[str]] | None = None
    media_size: MediaSize | str | ScreenDataRef[str] | ComponentRef[str] | None = None
    on_select_action: DataExchangeAction | UpdateDataAction | None = None
    on_unselect_action: UpdateDataAction | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class RadioButtonsGroup(FormComponent[str]):
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
        name: The unique name (id) for this component.
        data_source: The data source of the radio buttons group.
        label: The label of the radio buttons group. Limited to 30 characters. Required starting from v4.0.
        description: The description of the radio buttons group. Limited to 300 characters. Added in v4.0.
        required: Whether the radio buttons group is required or not.
        visible: Whether the radio buttons group is visible or not. Default to ``True``.
        enabled: Whether the radio buttons group is enabled or not. Default to ``True``.
        init_value: The default value (ID of the data source).
        media_size: The media size of the image. Added in v5.0.
        on_select_action: The action to perform when an item is selected.
        on_unselect_action: The action to perform when an item is unselected. Added in v6.0.
    """

    type: TemplateComponentType = dataclasses.field(
        default=TemplateComponentType.RADIO_BUTTONS_GROUP, init=False, repr=False
    )
    name: str
    data_source: list[DataSource] | ScreenDataRef[list[DataSource]]
    label: str | FlowStr | ScreenDataRef[str] | ComponentRef[str] | None = None
    description: str | FlowStr | ScreenDataRef[str] | ComponentRef[str] | None = None
    required: bool | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    visible: bool | Condition | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    enabled: bool | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    init_value: str | ScreenDataRef[str] | ComponentRef[str] | None = None
    media_size: MediaSize | str | ScreenDataRef[str] | ComponentRef[str] | None = None
    on_select_action: DataExchangeAction | UpdateDataAction | None = None
    on_unselect_action: UpdateDataAction | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class Dropdown(FormComponent[str]):
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
        name: The unique name (id) for this component.
        label: The label of the dropdown. Limited to 30 characters.
        data_source: The data source of the dropdown. minimum 1 and maximum 200 items.
        enabled: Whether the dropdown is enabled or not. Default to ``True``.
        required: Whether the dropdown is required or not.
        visible: Whether the dropdown is visible or not. Default to ``True``.
        init_value: The default value (ID of the data source).
        on_select_action: The action to perform when an item is selected.
        on_unselect_action: The action to perform when an item is unselected. Added in v6.0.
    """

    type: TemplateComponentType = dataclasses.field(
        default=TemplateComponentType.DROPDOWN, init=False, repr=False
    )
    name: str
    label: str | FlowStr | ScreenDataRef[str] | ComponentRef[str]
    data_source: list[DataSource] | ScreenDataRef[list[DataSource]]
    enabled: bool | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    required: bool | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    visible: bool | Condition | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    init_value: str | ScreenDataRef[str] | ComponentRef[str] | None = None
    on_select_action: DataExchangeAction | UpdateDataAction | None = None
    on_unselect_action: UpdateDataAction | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class ChipsSelector(FormComponent[list[str]]):
    """
    Chips Selector component allows users to pick multiple selections from a list of options.

    - Added in v6.3
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/components#chips_selector>`_.

    Example:

        >>> ChipsSelector(
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
        name: The unique name (id) for this component.
        data_source: The data source of the chips selector.
        label: The label of the chips selector. Limited to 80 characters.
        description: The description of the chips selector. Limited to 300 characters
        min_selected_items: The minimum number of items that can be selected. Minimum value is 1.
        max_selected_items: The maximum number of items that can be selected. Maximum value is 20.
        required: Whether the chips selector is required or not.
        visible: Whether the chips selector is visible or not. Default to ``True``.
        enabled: Whether the chips selector is enabled or not. Default to ``True``.
        init_value: The default values (IDs of the data sources).
        on_select_action: The action to perform when an item is selected. UpdateDataAction supported since v7.1.
        on_unselect_action: The action to perform when an item is unselected. if not set, the on_select_action will handle both selection and unselection events. Added in v7.1.
    """

    type: TemplateComponentType = dataclasses.field(
        default=TemplateComponentType.CHIPS_SELECTOR, init=False, repr=False
    )
    name: str
    data_source: list[DataSource] | ScreenDataRef[list[DataSource]]
    label: str | FlowStr | ScreenDataRef[str] | ComponentRef[str]
    description: str | FlowStr | ScreenDataRef[str] | ComponentRef[str] | None = None
    min_selected_items: int | ScreenDataRef[int] | None = None
    max_selected_items: int | ScreenDataRef[int] | None = None
    required: bool | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    visible: bool | Condition | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    enabled: bool | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    init_value: list[str] | ScreenDataRef[list[str]] | None = None
    on_select_action: DataExchangeAction | UpdateDataAction | None = None
    on_unselect_action: UpdateDataAction | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class Footer(Component):
    """
    Footer component allows users to navigate to other screens or submit the flow.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#foot>`_.

    Attributes:
        label: The label of the footer. Limited to 35 characters.
        on_click_action: The action to perform when the footer is clicked. Required.
        left_caption: Can set left_caption and right_caption or only center_caption, but not all 3 at once. Limited to 15 characters.
        center_caption: Can set center-caption or left-caption and right-caption, but not all 3 at once. Limited to 15 characters.
        right_caption: Can set right-caption and left-caption or only center-caption, but not all 3 at once. Limited to 15 characters.
        enabled: Whether the footer is enabled or not. Default to ``True``.
    """

    type: TemplateComponentType = dataclasses.field(
        default=TemplateComponentType.FOOTER, init=False, repr=False
    )
    visible: None = dataclasses.field(default=None, init=False, repr=False)
    label: str | FlowStr | ScreenDataRef[str] | ComponentRef[str]
    on_click_action: CompleteAction | DataExchangeAction | NavigateAction
    left_caption: str | FlowStr | ScreenDataRef[str] | ComponentRef[str] | None = None
    center_caption: str | FlowStr | ScreenDataRef[str] | ComponentRef[str] | None = None
    right_caption: str | FlowStr | ScreenDataRef[str] | ComponentRef[str] | None = None
    enabled: bool | ScreenDataRef[bool] | ComponentRef[bool] | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class OptIn(FormComponent[bool]):
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
        name: The unique name (id) for this component.
        label: The label of the opt in. Limited to 30 characters.
        required: Whether the opt in is required or not.
        visible: Whether the opt in is visible or not. Default to ``True``.
        init_value: The default value of the opt in.
        on_click_action: The action to perform when the opt in is clicked.
    """

    type: TemplateComponentType = dataclasses.field(
        default=TemplateComponentType.OPT_IN, init=False, repr=False
    )
    enabled: None = dataclasses.field(default=None, init=False, repr=False)
    name: str
    label: str | FlowStr | ScreenDataRef[str] | ComponentRef[str]
    required: bool | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    visible: bool | Condition | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    init_value: bool | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    on_click_action: OpenUrlAction | DataExchangeAction | NavigateAction | None = None
    on_select_action: UpdateDataAction | None = None
    on_unselect_action: UpdateDataAction | None = None


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
        ...     on_click_action=NavigateAction(
        ...         next=Next(name='SIGNUP_SCREEN'),
        ...         payload={'data': 'value'}
        ...     )
        ... )

    Attributes:
        text: The text of the embedded link. Limited to 35 characters.
        on_click_action: The action to perform when the embedded link is clicked.
        visible: Whether the embedded link is visible or not. Default to ``True``.
    """

    type: TemplateComponentType = dataclasses.field(
        default=TemplateComponentType.EMBEDDED_LINK, init=False, repr=False
    )
    text: str | FlowStr | ScreenDataRef[str] | ComponentRef[str]
    on_click_action: (
        DataExchangeAction | UpdateDataAction | NavigateAction | OpenUrlAction
    )
    visible: bool | Condition | ScreenDataRef[bool] | ComponentRef[bool] | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class NavigationList(Component):
    """
    The NavigationList component allows users to navigate effectively between different screens in a Flow,
    by exploring and interacting with a list of options. Each list item can display rich content such as text, images and tags.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/components#navlist>`_.
    - Added in v6.2
    - The on_click_action is required for this component and can be defined either at the component level or in each :class:`NavigationItem`.
    - There can be at most 2 :class:`NavigationList` components per screen.
    - The :class:`NavigationList` components cannot be used in combination with any other components in the same screen.

    Example:

        >>> NavigationList(
        ...     name='navigation_list',
        ...     list_items=[
        ...         NavigationItem(
        ...             id='1',
        ...             main_content=NavigationItemMainContent(title='Title 1', description='Description 1'),
        ...             start=NavigationItemStart(image='base64image...'),
        ...             end=NavigationItemEnd(title="$100", description="/ month"),
        ...             badge='New',
        ...             on_click_action=NavigateAction(next=Next(name='SCREEN_1'))
        ...         ),
        ...         ...
        ...     ],
        ... )


    Attributes:
        name: The unique name (id) for this component.
        list_items: The list items of the navigation list. Minimum 1 and maximum 20 items. Content will not be rendered if the limit is reached.
        label: The label of the navigation list. Limited to 80 characters.
        description: The description of the navigation list. Limited to 300 characters.
        media_size: The media size of the image. Default to ``REGULAR``.
        on_click_action: The action to perform when an item is clicked (can be defined at the component level or in each :class:`NavigationItem`).
    """

    type: TemplateComponentType = dataclasses.field(
        default=TemplateComponentType.NAVIGATION_LIST, init=False, repr=False
    )
    visible: None = dataclasses.field(default=None, init=False, repr=False)
    name: str
    list_items: list[NavigationItem] | ScreenDataRef[list[NavigationItem]]
    label: str | FlowStr | ScreenDataRef[str] | ComponentRef[str] | None = None
    description: str | FlowStr | ScreenDataRef[str] | ComponentRef[str] | None = None
    media_size: MediaSize | str | ScreenDataRef[str] | ComponentRef[str] | None = None
    on_click_action: NavigateAction | DataExchangeAction | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class NavigationItem:
    """
    The NavigationItem represents an item in the NavigationList component.

    - There can be only one item with a ``badge`` per list.
    - The ``end`` add-on cannot be used in combination with ``media_size`` set to ``LARGE``.
    - The ``on_click_action`` cannot be defined simultaneously on component-level and on item-level.

    Attributes:
        main_content: The main content of the navigation item.
        start: The start content of the navigation item (An image, limited to 100KB).
        end: The end content of the navigation item.
        badge: The badge of the navigation item. Limited to 15 characters.
        tags: The tags of the navigation item. Maximum 3 tags, each limited to 15 characters.
    """

    id: str
    main_content: NavigationItemMainContent
    start: NavigationItemStart | None = None
    end: NavigationItemEnd | None = None
    badge: str | None = None
    tags: list[str] | None = None
    on_click_action: NavigateAction | DataExchangeAction | None = None

    def to_dict(self) -> dict:
        return dataclasses.asdict(obj=self, dict_factory=_TO_DICT_FACTORY)


_FlowResponseDataType: TypeAlias = dict[
    str,
    str
    | int
    | float
    | bool
    | dict
    | DataSource
    | list[str | int | float | bool | dict | DataSource | NavigationItem],
]


@dataclasses.dataclass(slots=True, kw_only=True)
class NavigationItemMainContent:
    """
    The main content of the NavigationItem component.

    Attributes:
        title: The title of the item content. Limited to 30 characters.
        description: The description of the item content. Limited to 20 characters.
        metadata: The metadata of the item content. Limited to 80 characters.
    """

    title: str
    description: str | None = None
    metadata: str | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class NavigationItemStart:
    """
    The start content of the NavigationItem component.

    Attributes:
        image: The image of the item content (base64 encoded, limited to 100KB).
    """

    image: str


@dataclasses.dataclass(slots=True, kw_only=True)
class NavigationItemEnd:
    """
    The end content of the NavigationItem component.

    Attributes:
        title: The title of the end content. Limited to 10 characters.
        description: The description of the end content. Limited to 20 characters.
        metadata: The metadata of the end content. Limited to 80 characters.
    """

    title: str | None = None
    description: str | None = None
    metadata: str | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class DatePicker(FormComponent[str]):
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
        name: The unique name (id) for this component.
        label: The label of the date picker. Limited to 40 characters.
        min_date: The minimum date (date/datetime/timestamp) that can be selected.
        max_date: The maximum date (date/datetime/timestamp) that can be selected.
        unavailable_dates: The dates (dates/datetimes/timestamps) that cannot be selected.
        helper_text: The helper text of the date picker. Limited to 80 characters.
        enabled: Whether the date picker is enabled or not. Default to ``True``.
        required: Whether the date picker is required or not.
        visible: Whether the date picker is visible or not. Default to ``True``.
        init_value: The default value.
        error_message: The error message of the date picker.
        on_select_action: The action to perform when a date is selected.
    """

    type: TemplateComponentType = dataclasses.field(
        default=TemplateComponentType.DATE_PICKER, init=False, repr=False
    )
    name: str
    label: str | FlowStr | ScreenDataRef[str] | ComponentRef[str]
    min_date: (
        datetime.date
        | str
        | ScreenDataRef[datetime.date]
        | ScreenDataRef[str]
        | ComponentRef[str]
        | None
    ) = None
    max_date: (
        datetime.date
        | str
        | ScreenDataRef[datetime.date]
        | ScreenDataRef[str]
        | ComponentRef[str]
        | None
    ) = None
    unavailable_dates: (
        list[datetime.date | str]
        | str
        | ScreenDataRef[list[str]]
        | ScreenDataRef[list[datetime.date]]
        | None
    ) = None
    helper_text: str | FlowStr | ScreenDataRef[str] | ComponentRef[str] | None = None
    enabled: bool | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    required: bool | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    visible: bool | Condition | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    init_value: (
        datetime.date
        | str
        | ScreenDataRef[datetime.date]
        | ScreenDataRef[str]
        | ComponentRef[str]
        | None
    ) = None
    error_message: str | ScreenDataRef[str] | ComponentRef[str] | None = None
    on_select_action: DataExchangeAction | None = None


class CalendarPickerMode(utils.StrEnum):
    """
    The mode of the calendar picker.

    Attributes:
        SINGLE: Allows to select one date.
        RANGE: Allows to select start and end dates.
    """

    _check_value = str.islower
    _modify_value = str.lower

    SINGLE = "single"
    RANGE = "range"

    UNKNOWN = "UNKNOWN"


class CalendarDay(utils.StrEnum):
    """
    The days of the week.

    Attributes:
        MON: Monday
        TUE: Tuesday
        WED: Wednesday
        THU: Thursday
        FRI: Friday
        SAT: Saturday
        SUN: Sunday
    """

    _check_value = str.istitle
    _modify_value = str.title

    MON = "Mon"
    TUE = "Tue"
    WED = "Wed"
    THU = "Thu"
    FRI = "Fri"
    SAT = "Sat"
    SUN = "Sun"

    UNKNOWN = "UNKNOWN"


_StartEndTypeVar = TypeVar("_StartEndTypeVar", bound=datetime.date | str | bool)


@dataclasses.dataclass(slots=True, kw_only=True)
class CalendarRangeValues(Generic[_StartEndTypeVar]):
    """
    The values of the start and end dates for the calendar picker in range mode.

    Attributes:
        start_date: The value of the start date.
        end_date: The value of the end date.
    """

    start_date: _StartEndTypeVar
    end_date: _StartEndTypeVar


@dataclasses.dataclass(slots=True, kw_only=True)
class CalendarPicker(FormComponent[str]):
    """
    CalendarPicker component allows users to select a single date or a range of dates from a full calendar interface.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/components/#calendarpicker>`_.
    - Added in v6.1

    Example:

        >>> CalendarPicker(
        ...     name='date',
        ...     label='Appointment Date',
        ...     mode=CalendarPickerMode.SINGLE,
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
        name: The unique name (id) for this component.
        label: The label of the calendar picker. Limited to 40 characters.
        title: The title of the calendar picker. Only available when mode is ``CalendarMode.RANGE``.
        description: The description of the calendar picker. Limited to 300 characters. Only available when mode is ``CalendarMode.RANGE``.
        mode: The mode of the calendar picker. Default to ``CalendarMode.SINGLE``.
        min_date: The minimum date (date/datetime) that can be selected.
        max_date: The maximum date (date/datetime) that can be selected.
        unavailable_dates: The dates (dates/datetimes) that cannot be selected.
        include_days: The days of the week to include in the calendar picker. Default to all days.
        min_days: The minimum number of days that can be selected in the range mode.
        max_days: The maximum number of days that can be selected in the range mode.
        helper_text: The helper text of the calendar picker. Limited to 80 characters.
        enabled: Whether the calendar picker is enabled or not. Default to ``True``.
        required: Whether the calendar picker is required or not.
        visible: Whether the calendar picker is visible or not. Default to ``True``.
        init_value: The default value. Only available when component is outside Form component.
        error_message: The error message of the calendar picker. Only available when component is outside Form component.
        on_select_action: The action to perform when a date is selected.
    """

    type: TemplateComponentType = dataclasses.field(
        default=TemplateComponentType.CALENDAR_PICKER, init=False, repr=False
    )
    name: str
    title: str | FlowStr | ScreenDataRef[str] | ComponentRef[str] | None = None
    description: str | FlowStr | ScreenDataRef[str] | ComponentRef[str] | None = None
    label: str | ScreenDataRef[str] | ComponentRef[str] | CalendarRangeValues[str]
    mode: CalendarPickerMode | str | ScreenDataRef[str] | ComponentRef[str] | None = (
        None
    )
    min_date: (
        datetime.date
        | str
        | ScreenDataRef[datetime.date]
        | ScreenDataRef[str]
        | ComponentRef[str]
        | None
    ) = None
    max_date: (
        datetime.date
        | str
        | ScreenDataRef[datetime.date]
        | ScreenDataRef[str]
        | ComponentRef[str]
        | None
    ) = None
    unavailable_dates: (
        list[datetime.date | str]
        | str
        | ScreenDataRef[list[datetime.date]]
        | ScreenDataRef[list[str]]
        | None
    ) = None
    min_days: int | ScreenDataRef[int] | None = None
    max_days: int | ScreenDataRef[int] | None = None
    include_days: list[CalendarDay | str] | ScreenDataRef[list[str]] | None = None
    helper_text: (
        str
        | ScreenDataRef[str]
        | ComponentRef[str]
        | CalendarRangeValues[str]
        | ScreenDataRef[CalendarRangeValues[str]]
        | None
    ) = None
    enabled: bool | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    required: (
        bool
        | ScreenDataRef[bool]
        | ComponentRef[bool]
        | CalendarRangeValues[bool]
        | ScreenDataRef[CalendarRangeValues[bool]]
        | None
    ) = None
    visible: bool | Condition | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    init_value: (
        datetime.date
        | str
        | ScreenDataRef[datetime.date]
        | ScreenDataRef[str]
        | ComponentRef[str]
        | CalendarRangeValues[str | datetime.date]
        | ScreenDataRef[CalendarRangeValues[str | datetime.date]]
        | None
    ) = None
    error_message: (
        str
        | ScreenDataRef[str]
        | ComponentRef[str]
        | CalendarRangeValues[str]
        | ScreenDataRef[CalendarRangeValues[str]]
        | None
    ) = None
    on_select_action: (
        DataExchangeAction | CalendarRangeValues[DataExchangeAction] | None
    ) = None


class ScaleType(utils.StrEnum):
    """
    The scale type of the image.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#image-scale-types>`_.

    Attributes:
        COVER: Image is clipped to fit the image container.
        CONTAIN: Image is contained within the image container with the original aspect ratio.
    """

    _check_value = str.islower
    _modify_value = str.lower

    COVER = "cover"
    CONTAIN = "contain"

    UNKNOWN = "UNKNOWN"


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
        src: Base64 of an image.
        width: The width of the image.
        height: The height of the image.
        scale_type: The scale type of the image. Defaule to ``ScaleType.CONTAIN`` Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#image-scale-types>`_.
        aspect_ratio: The aspect ratio of the image. Default to ``1``.
        alt_text: Alternative Text is for the accessibility feature, eg. Talkback and Voice over.
        visible: Whether the image is visible or not. Default to ``True``.
    """

    type: TemplateComponentType = dataclasses.field(
        default=TemplateComponentType.IMAGE, init=False, repr=False
    )
    src: str | ScreenDataRef[str] | ComponentRef[str]
    width: int | ScreenDataRef[int] | None = None
    height: int | ScreenDataRef[int] | None = None
    scale_type: ScaleType | str | ScreenDataRef[str] | ComponentRef[str] | None = None
    aspect_ratio: int | ScreenDataRef[int]
    alt_text: str | ScreenDataRef[str] | ComponentRef[str] | None = None
    visible: bool | Condition | ScreenDataRef[bool] | ComponentRef[bool] | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class ImageCarouselItem:
    """
    ImageCarouselItem represents an item in the `ImageCarousel` component.

    - Supported images formats are JPEG PNG
    - Recommended image size is up to 300kb

    Example:

        >>> ImageCarouselItem(
        ...     src='iVBORw0KGgoAAAANSUhEUgAAAlgAAAM...',
        ...     alt_text='Image of a cat'
        ... )

    Attributes:
        src: Base64 of an image.
        alt_text: Alternative Text is for the accessibility feature, eg. Talkback and Voice over.
    """

    src: str | ScreenDataRef[str] | ComponentRef[str]
    alt_text: str | ScreenDataRef[str] | ComponentRef[str]


@dataclasses.dataclass(slots=True, kw_only=True)
class ImageCarousel(Component):
    """
    ImageCarousel component that displays a carousel of images.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#image_carousel>`_.
    - Added in v7.1
    - Max number of images is 3.
    - Max number of :class:`ImageCarousel` per screen is 2
    - Max number of :class:`ImageCarousel` per Flow is 3

    Example:
        >>> ImageCarousel(
        ...     images=[
        ...         ImageCarouselItem(src='iVBORw0KGgoAAAANSUhEUgAAAlgAAAM...', alt_text='Image 1'),
        ...         ImageCarouselItem(src='iVBORw0KGgoAAAANSUhEUgAAAlgAAAN...', alt_text='Image 2'),
        ...     ],
        ...     aspect_ratio='4:3',
        ...     scale_type=ScaleType.CONTAIN
        ... )

    Attributes:
        images: A list of images to display in the carousel. Each image is represented by an :class:`ImageCarouselItem` object.
        aspect_ratio: The aspect ratio of the images in the carousel. Default to ``4:3``.
        scale_type: The scale type of the images in the carousel. Default to ``ScaleType.CONTAIN``.
        visible: Whether the image carousel is visible or not. Default to ``True``.
    """

    type: TemplateComponentType = dataclasses.field(
        default=TemplateComponentType.IMAGE_CAROUSEL, init=False, repr=False
    )
    images: list[ImageCarouselItem] | ScreenDataRef[list[ImageCarouselItem]]
    aspect_ratio: str | ScreenDataRef[str] | ComponentRef[str] | None = None
    scale_type: ScaleType | str | ScreenDataRef[str] | ComponentRef[str] | None = None
    visible: bool | Condition | ScreenDataRef[bool] | ComponentRef[bool] | None = None


class PhotoSource(utils.StrEnum):
    """
    The source where the image can be selected from.

    Attributes:
        CAMERA_GALLERY: User can select from gallery or take a photo
        CAMERA: User can select only from gallery
        GALLERY: User can only take a photo
    """

    _check_value = str.islower
    _modify_value = str.lower

    CAMERA_GALLERY = "camera_gallery"
    CAMERA = "camera"
    GALLERY = "gallery"

    UNKNOWN = "UNKNOWN"


@dataclasses.dataclass(slots=True, kw_only=True)
class PhotoPicker(FormComponent):
    """
    PhotoPicker component allows uploading media from camera or gallery

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/media_upload>`_.
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
        name: The unique name (id) for this component.
        label: The label of the photo picker. Limited to 30 characters.
        description: The description of the photo picker. Limited to 300 characters.
        photo_source: The source where the image can be selected from. Default to ``PhotoSource.CAMERA_GALLERY``.
        max_file_size_kb: The maximum file size in KB. Default value: 25600 (25 MiB)
        min_uploaded_photos: The minimum number of photos that can be uploaded. This property determines whether the component is optional (set to 0) or required (set above 0).
        max_uploaded_photos: The maximum number of photos that can be uploaded. Default value: 30
        enabled: Whether the photo picker is enabled or not. Default to ``True``.
        visible: Whether the photo picker is visible or not. Default to ``True``.
        error_message: The error message of the photo picker.

    """

    type: TemplateComponentType = dataclasses.field(
        default=TemplateComponentType.PHOTO_PICKER, init=False, repr=False
    )
    required: None = dataclasses.field(default=None, init=False, repr=False)
    init_value: None = dataclasses.field(default=None, init=False, repr=False)
    name: str
    label: str | FlowStr | ScreenDataRef[str] | ComponentRef[str]
    description: str | FlowStr | ScreenDataRef[str] | ComponentRef[str] | None = None
    photo_source: PhotoSource | str | ScreenDataRef[str] | ComponentRef[str] | None = (
        None
    )
    max_file_size_kb: int | ScreenDataRef[int] | None = None
    min_uploaded_photos: int | ScreenDataRef[int] | None = None
    max_uploaded_photos: int | ScreenDataRef[int] | None = None
    enabled: bool | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    visible: bool | Condition | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    error_message: str | ScreenDataRef[str] | ComponentRef[str] | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class DocumentPicker(FormComponent):
    """
    DocumentPicker component allows uploading files from the device

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/media_upload>`_.
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
        name: The unique name (id) for this component.
        label: The label of the document picker. Limited to 30 characters.
        description: The description of the document picker. Limited to 300 characters.
        max_file_size_kb: The maximum file size in KB. Default value: 25600 (25 MiB)
        min_uploaded_documents: The minimum number of documents that can be uploaded. This property determines whether the component is optional (set to 0) or required (set above 0).
        max_uploaded_documents: The maximum number of documents that can be uploaded. Default value: 30
        allowed_mime_types: Specifies which document mime types can be selected. If it contains “image/jpeg”, picking photos from the gallery will be available as well. Default value: Any document from the supported mime types can be selected.
        enabled: Whether the document picker is enabled or not. Default to ``True``.
        visible: Whether the document picker is visible or not. Default to ``True``.
        error_message: The error message of the document picker.
    """

    type: TemplateComponentType = dataclasses.field(
        default=TemplateComponentType.DOCUMENT_PICKER, init=False, repr=False
    )
    required: None = dataclasses.field(default=None, init=False, repr=False)
    init_value: None = dataclasses.field(default=None, init=False, repr=False)
    name: str
    label: str | FlowStr | ScreenDataRef[str] | ComponentRef[str]
    description: str | FlowStr | ScreenDataRef[str] | ComponentRef[str] | None = None
    max_file_size_kb: int | ScreenDataRef[int] | None = None
    min_uploaded_documents: int | ScreenDataRef[int] | None = None
    max_uploaded_documents: int | ScreenDataRef[int] | None = None
    allowed_mime_types: list[str] | ScreenDataRef[list[str]] | None = None
    enabled: bool | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    visible: bool | Condition | ScreenDataRef[bool] | ComponentRef[bool] | None = None
    error_message: str | ScreenDataRef[str] | ComponentRef[str] | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class If(Component):
    """
    If component allows users to add components based on a condition.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#if>`_.
    - It is allowed to nest up to 3 :class:`If` components.
    - Should have at least one dynamic value (e.g. screen_data.ref / form_comp.ref) in the condition.
    - Should always be resolved into a boolean (i.e. no strings or number values).
    - Can be used with literals but should not only contain literals.
    - :class:`Footer` can be added within :class:`If` only in the first level, not inside a nested :class:`If`.
    - If there is a :class:`Footer` within :class:`If`, it should exist in both branches (i.e. ``then`` and ``else``). This means that ``else`` becomes mandatory.
    - If there is a :class:`Footer` within :class:`If` it cannot exist a footer outside, because the max count of :class:`Footer` is 1 per screen.


    Example:

            >>> age = ScreenData(key="age", example=20)
            >>> opt_in = OptIn(name="opt_in", ...)
            >>> If(
            ...     condition=(age.ref > 21) && opt_in.ref,
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

    type: TemplateComponentType = dataclasses.field(
        default=TemplateComponentType.IF, init=False, repr=False
    )
    visible: None = dataclasses.field(default=None, init=False, repr=False)
    condition: Condition | str
    then: list[Component | dict[str, Any]]
    else_: list[Component | dict[str, Any]] | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class Switch(Component):
    """
    Switch component allows users to add components based on a value of a screen data ref or form component ref.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#switch>`_.

    Example:

            >>> age = TextInput(name='age', label='Age')
            >>> switch = Switch(
            ...     value=age.ref,
            ...     cases={
            ...         '10': [TextHeading(text='Under 18')],
            ...         ...
            ...         '20': [TextInput(name='email', label='Email')],
            ...     }

    Attributes:
        value: The key / ref to the data that will be used to determine which components to render.
        cases: The components that will be rendered based on the value. {case: [components, ...], ...}.
    """

    type: TemplateComponentType = dataclasses.field(
        default=TemplateComponentType.SWITCH, init=False, repr=False
    )
    visible: None = dataclasses.field(default=None, init=False, repr=False)
    value: str | ScreenDataRef | ComponentRef
    cases: dict[str, list[Component | dict[str, Any]]]


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
        OPEN_URL: Opens a URL in the browser. Added in v6.0
         (Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#open-url-action
        UPDATE_DATA: Update the data of the current screen. Added in v6.0
         (Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#update-data-action>`_).
    """

    _check_value = str.islower
    _modify_value = str.lower

    COMPLETE = "complete"
    DATA_EXCHANGE = "data_exchange"
    NAVIGATE = "navigate"
    OPEN_URL = "open_url"
    UPDATE_DATA = "update_data"

    UNKNOWN = "UNKNOWN"


class NextType(utils.StrEnum):
    """
    The type of the next action

    Attributes:
        SCREEN: Navigate to the next screen
        PLUGIN: Trigger a plugin
    """

    _check_value = str.islower
    _modify_value = str.lower

    SCREEN = "screen"
    PLUGIN = "plugin"

    UNKNOWN = "UNKNOWN"


@dataclasses.dataclass(slots=True, kw_only=True)
class Next:
    """
    The next action

    Attributes:
        name: The name of the next screen or plugin
        type: The type of the next action (Default: ``NextType.SCREEN``)
    """

    name: str
    type: NextType | str = NextType.SCREEN


class BaseAction(abc.ABC):
    """The base class for all actions"""

    @property
    @abc.abstractmethod
    def name(self) -> FlowActionType: ...

    @property
    @abc.abstractmethod
    def payload(
        self,
    ) -> dict[str, str | bool | list[DataSource] | ScreenDataRef | ComponentRef]: ...


@dataclasses.dataclass(slots=True, kw_only=True)
class DataExchangeAction(BaseAction):
    """
    Data Exchange Action. Sending Data to WhatsApp Flows Data Endpoint


    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#data-exchange-action>`_.

    Example:

        >>> DataExchangeAction(
        ...     payload={'data': 'value'}
        ... )

    Attributes:
        payload: The payload of the action (Pass data to the WhatsApp Flows Data Endpoint).
         This payload can take data from form components or from the data of the screen.
    """

    name: FlowActionType = dataclasses.field(
        default=FlowActionType.DATA_EXCHANGE, init=False, repr=False
    )
    payload: dict[str, str | bool | list[DataSource] | ScreenDataRef | ComponentRef] = (
        dataclasses.field(default_factory=dict)
    )


@dataclasses.dataclass(slots=True, kw_only=True)
class NavigateAction(BaseAction):
    """
    Navigate Action. Triggers the next screen with the payload as its input.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#navigate-action>`_.

    Example:

        >>> NavigateAction(
        ...     next=Next(name='NEXT_SCREEN'),
        ...     payload={'data': 'value'}
        ... )

    Attributes:
        next: The next action to perform
        payload: The payload of the action (Pass data to the next screen).
         This payload can take data from form components or from the data of the screen.
    """

    name: FlowActionType = dataclasses.field(
        default=FlowActionType.NAVIGATE, init=False, repr=False
    )
    next: Next
    payload: dict[str, str | bool | list[DataSource] | ScreenDataRef | ComponentRef] = (
        dataclasses.field(default_factory=dict)
    )


@dataclasses.dataclass(slots=True, kw_only=True)
class OpenUrlAction(BaseAction):
    """
    Open URL Action. Triggers a link to open in the device’s default web browser.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#open-url-action>`_.

    Example:

        >>> OpenUrlAction(
        ...     url='https://example.com'
        ... )

    Attributes:
        url: The URL to open
    """

    name: FlowActionType = dataclasses.field(
        default=FlowActionType.OPEN_URL, init=False, repr=False
    )
    payload: None = dataclasses.field(default=None, init=False, repr=False)
    url: str


@dataclasses.dataclass(slots=True, kw_only=True)
class UpdateDataAction(BaseAction, Generic[_ScreenDataValTypeVar]):
    """
    Update Data Action. Triggers an immediate update to the screen's state, reflecting user input changes.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#update-data-action>`_.

    Example:

        >>> is_visible = ScreenData(key='is_visible', example=True)
        >>> UpdateDataAction(
        ...     payload=[
        ...         is_visible.update(value=False)
        ...     ]
        ... )

    Attributes:
        payload: The data to update for the current screen.
    """

    name: FlowActionType = dataclasses.field(
        default=FlowActionType.UPDATE_DATA, init=False, repr=False
    )
    payload: (
        list[ScreenDataUpdate[_ScreenDataValTypeVar]] | dict[str, _ScreenDataValTypeVar]
    )

    def __post_init__(self):
        if not isinstance(self.payload, dict):
            self.payload = _ScreenDatasContainer(self.payload)  # type: ignore


@dataclasses.dataclass(slots=True, kw_only=True)
class CompleteAction(BaseAction):
    """
    Complete Action. Triggers the termination of the Flow with the provided payload

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#complete-action>`_.

    Example:

        >>> CompleteAction(
        ...     payload={'data': 'value'}
        ... )

    Attributes:
        payload: The payload to include in the :class:`FlowCompletion` `.response` attribute.
    """

    name: FlowActionType = dataclasses.field(
        default=FlowActionType.COMPLETE, init=False, repr=False
    )
    payload: dict[str, str | bool | ScreenDataRef | ComponentRef] = dataclasses.field(
        default_factory=dict
    )
