from __future__ import annotations

import abc
import dataclasses
import datetime
import json
import pathlib
from typing import Iterable, TYPE_CHECKING, Any, BinaryIO

from pywa import utils
from pywa.types.base_update import BaseUserUpdate  # noqa
from pywa.types.others import (
    WhatsAppBusinessAccount,
    FacebookApplication,
    MessageType,
    Metadata,
    User,
    ReplyToMessage,
)

if TYPE_CHECKING:
    from pywa import WhatsApp

__all__ = [
    "FlowCompletion",
    "FlowRequest",
    "FlowResponse",
    "FlowCategory",
    "FlowDetails",
    "FlowStatus",
    "FlowPreview",
    "FlowValidationError",
    "FlowAsset",
    "FlowJSON",
    "Screen",
    "Layout",
    "LayoutType",
    "Form",
    "TextHeading",
    "TextSubheading",
    "TextBody",
    "TextCaption",
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
    "ScaleType",
    "DataSource",
    "Action",
    "FlowActionType",
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
        token: The token of the flow.
        response: The response from the flow.
    """

    id: str
    type: MessageType
    metadata: Metadata
    from_user: User
    timestamp: datetime.datetime
    reply_to_message: ReplyToMessage | None
    body: str
    token: str
    response: dict[str, Any]

    @classmethod
    def from_update(cls, client: WhatsApp, update: dict) -> FlowCompletion:
        msg = (value := update["entry"][0]["changes"][0]["value"])["messages"][0]
        response = json.loads(msg["interactive"]["nfm_reply"]["response_json"])
        return cls(
            _client=client,
            id=msg["id"],
            type=MessageType(msg["type"]),
            metadata=Metadata.from_dict(value["metadata"]),
            from_user=User.from_dict(value["contacts"][0]),
            timestamp=datetime.datetime.fromtimestamp(int(msg["timestamp"])),
            reply_to_message=ReplyToMessage.from_dict(msg["context"]),
            body=msg["interactive"]["nfm_reply"]["body"],
            token=response["flow_token"],
            response=response,
        )


class FlowRequestActionType(utils.StrEnum):
    """
    The type the action that triggered the request.

    Attributes:
        INIT: if the request is triggered when opening the Flow
        BACK: if the request is triggered when pressing "back" (The screen has ``refresh_on_back`` set to ``True``)
        DATA_EXCHANGE: if the request is triggered when submitting the screen
        PING: if the request is triggered by a health check (ignore this requests by leaving ``handle_health_check`` to ``True``)
    """

    INIT = "INIT"
    BACK = "BACK"
    DATA_EXCHANGE = "data_exchange"
    PING = "ping"


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
    """

    version: str
    action: FlowRequestActionType
    flow_token: str | None = None
    screen: str | None = None
    data: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            version=data["version"],
            action=FlowRequestActionType(data["action"]),
            flow_token=data.get("flow_token"),
            screen=data.get("screen") or None,  # can be empty string
            data=data.get("data") or None,  # can be empty dict
        )

    @property
    def has_error(self) -> bool:
        """
        Check if the request has an error.
        When True, if flow endpoint register with ``acknowledge_errors=True``,
        pywa will acknowledge the error and ignore the response from the callback. The callback still be called.
        """
        return any(
            key in self.data for key in ("error_message", "error_key") if self.data
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

    Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/guides/implementingyourflowendpoint#data_exchange_request>`_.

    Attributes:
        version: The version of the data exchange.
        screen: The screen to display (if the flow is not closed).
        data: The data to send to the screen or to add to flow completion message (received to the webhook).
        error_message: This will redirect the user to ``screen`` and will trigger a snackbar error with the error_message present (if the flow is not closed).
        flow_token: The flow token to close the flow (if the flow is closed).
        close_flow: Whether to close the flow or just navigate to the screen.
    """

    version: str
    data: dict[str, Any]
    screen: str | None = None
    error_message: str | None = None
    flow_token: str | None = None
    close_flow: bool = False

    def to_dict(self) -> dict[str, str | dict]:
        if not self.close_flow and not self.screen:
            raise ValueError(
                "When the response not close the flow, the screen must be provided."
            )
        if self.close_flow and not self.flow_token:
            raise ValueError(
                "When the response close the flow, the flow token must be provided."
            )
        data = self.data.copy()
        if not self.close_flow and self.error_message:
            data["error_message"] = self.error_message
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
        return cls.OTHER


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class FlowValidationError(Exception, utils.FromDict):
    """
    Represents a validation error of a flow.

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
            expires_at=datetime.datetime.fromisoformat(data["expires_at"]),
        )


@dataclasses.dataclass(slots=True, kw_only=True)
class FlowDetails:
    """
    Represents the details of a flow.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowsapi#details>`_.

    Attributes:
        id: The ID of the flow.
        name: The name of the flow.
        status: The status of the flow.
        json_version: The version of the flow JSON.
        data_api_version: The version to use during communication with the WhatsApp Flows Data Endpoint.
        categories: The categories of the flow.
        validation_errors: The validation errors of the flow.
        endpoint_uri: The endpoint URI of the flow.
        preview: The preview of the flow.
        whatsapp_business_account: The WhatsApp Business Account that owns the flow.
        application: The application that owns the flow.
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
        )

    def publish(self) -> bool:
        if self._client.publish_flow(self.id):
            self.status = FlowStatus.PUBLISHED
            return True
        return False

    def delete(self) -> bool:
        if self._client.delete_flow(self.id):
            self.status = FlowStatus.DEPRECATED
            return True
        return False

    def deprecate(self) -> bool:
        if self._client.deprecate_flow(self.id):
            self.status = FlowStatus.DEPRECATED
            return True
        return False

    def get_assets(self) -> tuple[FlowAsset, ...]:
        return self._client.get_flow_assets(self.id)

    def update_metadata(
        self,
        name: str | None = None,
        categories: Iterable[FlowCategory | str] | None = None,
        endpoint_uri: str | None = None,
    ) -> bool:
        success = self._client.update_flow_metadata(
            flow_id=self.id,
            name=name,
            categories=categories,
            endpoint_uri=endpoint_uri,
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
        is_success, errors = self._client.update_flow_json(
            flow_id=self.id,
            flow_json=flow_json,
        )
        self.validation_errors = errors
        return is_success


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class FlowAsset:
    """Represents an asset in a flow."""

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


@dataclasses.dataclass(slots=True, kw_only=True)
class FlowJSON:
    """
    Represents a WhatsApp Flow JSON.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson>`_.

    Attributes:
        version: The Flow JSON version (Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/versioning>`_).
        screens: The screens that are part of the flow (Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#screens>`_).
        data_api_version: The version to use during communication with the WhatsApp Flows Data Endpoint. Required if the data channel is set.
        data_channel_uri: The endpoint to use to communicate with your server (If you using the WhatsApp Flows Data Endpoint).
        routing_model: Defines the rules for the screen by limiting the possible state transition. (Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#routing-model>`_).
    """

    version: str
    screens: list[Screen] | tuple[Screen]
    data_api_version: str | None = None
    data_channel_uri: str | None = None
    routing_model: dict[str, Iterable[str]] | None = None

    def to_dict(self):
        return dataclasses.asdict(
            obj=self,
            dict_factory=lambda d: {
                k.replace("_", "-") if k not in _UNDERSCORE_FIELDS else k: v
                for (k, v) in d
                if v is not None
            },
        )


@dataclasses.dataclass(slots=True, kw_only=True)
class Screen:
    """
    Represents a screen (page) in a WhatsApp flow.

    - The maximum number of components (children) per screen is 50.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#screens>`_.

    Attributes:
        id: Unique identifier of the screen which works as a page url. ``SUCCESS`` is a reserved keyword and should not be used as a screen id.
        layout: Associated screen UI Layout that is shown to the user (Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#layout>`_).
        title: Screen level attribute that is rendered in the top navigation bar.
        data: Declaration of dynamic data that fills the components field in the Flow JSON. It uses JSON Schema to define the structure and type of the properties.
        terminal: Each Flow should have a terminal state where we terminate the experience and have the Flow completed. Multiple screens can be marked as terminal. It's mandatory to have a Footer component on the terminal screen.
        refresh_on_back: Whether to trigger a data exchange request with the WhatsApp Flows Data Endpoint when using the back button while on this screen (Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#additional-information-on-refresh-on-back>`_).
    """

    id: str
    layout: Layout
    title: str | None = None
    data: dict[str, dict] | None = None
    terminal: bool | None = None
    refresh_on_back: bool | None = None


class LayoutType(utils.StrEnum):
    """LayoutType is the type of layout that is used to display the components."""

    SINGLE_COLUMN = "SingleColumnLayout"


@dataclasses.dataclass(slots=True, kw_only=True)
class Layout:
    """
    Layout is the top level component that holds the other components.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#layout>`_.

    Attributes:
        type: The type of layout that is used to display the components (Default: ``LayoutType.SINGLE_COLUMN``).
        children: The components that are part of the layout.
    """

    type: LayoutType = LayoutType.SINGLE_COLUMN
    children: list[Component] | tuple[Component]


class Component(abc.ABC):
    """Base class for all components"""

    @property
    @abc.abstractmethod
    def type(self) -> ComponentType:
        ...

    @property
    @abc.abstractmethod
    def visible(self) -> bool | str | None:
        ...


class ComponentType(utils.StrEnum):
    """Internal component types"""

    FORM = "Form"
    TEXT_HEADING = "TextHeading"
    TEXT_SUBHEADING = "TextSubheading"
    TEXT_BODY = "TextBody"
    TEXT_CAPTION = "TextCaption"
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


@dataclasses.dataclass(slots=True, kw_only=True)
class Form(Component):
    """
    To get and submit the data entered from users, Flow JSON uses a straightforward concept from HTML - Forms.

    - The following components must be inside Form: :class:`TextInput`, :class:`TextArea`, :class:`CheckboxGroup`,
      :class:`RadioButtonsGroup`, :class:`OptIn`, :class:`Dropdown` and :class:`DatePicker`.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#forms-and-form-properties>`_.

    Attributes:
        name: The name of the form.
        children: The components that are part of the form.
        init_values: The initial values of the form (Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#form-configuration>`_).
        error_messages: The error messages of the form (Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#form-configuration>`_).
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.FORM, init=False, repr=False
    )
    visible: None = dataclasses.field(default=None, init=False, repr=False)
    name: str
    children: Iterable[Component]
    init_values: dict[str, str | list[str, ...] | tuple[str, ...]] | str | None = None
    error_messages: dict[str, str] | str | None = None


class TextComponent(Component, abc.ABC):
    """
    Base class for all text components

    https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#text
    """

    @property
    @abc.abstractmethod
    def text(self) -> str:
        ...


class FontWeight(utils.StrEnum):
    """
    The text weight

    Attributes:
        BOLD: Bold text
        ITALIC: Italic text
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

    Attributes:
        text: The text of the heading. Limited to 4096 characters. Can be dynamic (e.g ``${data.text}``).
        visible: Whether the heading is visible or not. Default to ``True``, Can be dynamic (e.g ``${data.is_visible}``).
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.TEXT_HEADING, init=False, repr=False
    )
    text: str
    visible: bool | str | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class TextSubheading(TextComponent):
    """
    Represents text that is displayed as a subheading.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#subheading>`_.

    Attributes:
        text: The text of the subheading. Limited to 60 characters. Can be dynamic (e.g ``${data.text}``).
        visible: Whether the subheading is visible or not. Default to ``True``, Can be dynamic (e.g ``${data.is_visible}``).
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.TEXT_SUBHEADING, init=False, repr=False
    )
    text: str
    visible: bool | str | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class TextBody(TextComponent):
    """
    Represents text that is displayed as a body.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#body>`_.

    Attributes:
        text: The text of the body. Limited to 80 characters. Can be dynamic (e.g ``${data.text}``).
        font_weight: The weight of the text. Can be dynamic (e.g ``${data.font_weight}``).
        strikethrough: Whether the text is strikethrough or not. Can be dynamic (e.g ``${data.strikethrough}``).
        visible: Whether the body is visible or not. Default to ``True``, Can be dynamic (e.g ``${data.is_visible}``).
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.TEXT_BODY, init=False, repr=False
    )
    text: str
    font_weight: FontWeight | str | None = None
    strikethrough: bool | str | None = None
    visible: bool | str | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class TextCaption(TextComponent):
    """
    Represents text that is displayed as a caption.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#caption>`_.

    Attributes:
        text: The text of the caption. Limited to 4096 characters. Can be dynamic (e.g ``${data.text}``).
        font_weight: The weight of the text. Can be dynamic (e.g ``${data.font_weight}``).
        strikethrough: Whether the text is strikethrough or not. Can be dynamic (e.g ``${data.strikethrough}``).
        visible: Whether the caption is visible or not. Default to ``True``, Can be dynamic (e.g ``${data.is_visible}``).
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.TEXT_CAPTION, init=False, repr=False
    )
    text: str
    font_weight: FontWeight | str | None = None
    strikethrough: bool | str | None = None
    visible: bool | str | None = None


class TextEntryComponent(Component, abc.ABC):
    """
    Base class for all text entry components

    https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#textentry
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        ...

    @property
    @abc.abstractmethod
    def label(self) -> str:
        ...

    @property
    @abc.abstractmethod
    def required(self) -> bool | str | None:
        ...

    @property
    @abc.abstractmethod
    def helper_text(self) -> str | None:
        ...


class InputType(utils.StrEnum):
    """
    The input type of the text entry component.

    - This is used by the WhatsApp client to determine the keyboard layout and validation rules.

    Attributes:
        TEXT: A single line of text
        NUMBER: A number
        EMAIL: An email address
        PASSWORD: A password
        PASSCODE: A passcode
        PHONE: A phone number
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

    - This component must be inside a :class:`Form`.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#textinput>`_.

    Attributes:
        name: The name of this component (to be used dynamically or in action payloads).
        label: The label of the text input. Limited to 20 characters. Can be dynamic (e.g ``${data.label}``).
        input_type: The input type of the text input (for keyboard layout and validation rules). Can be dynamic (e.g ``${data.input_type}``).
        required: Whether the text input is required or not. Can be dynamic (e.g ``${data.required}``).
        min_chars: The minimum number of characters allowed in the text input. Can be dynamic (e.g ``${data.min_chars}``).
        max_chars: The maximum number of characters allowed in the text input. Can be dynamic (e.g ``${data.max_chars}``).
        helper_text: The helper text of the text input. Limited to 80 characters. Can be dynamic (e.g ``${data.helper_text}``).
        enabled: Whether the text input is enabled or not. Default to ``True``. Can be dynamic (e.g ``${data.enabled}``).
        visible: Whether the text input is visible or not. Default to ``True``. Can be dynamic (e.g ``${data.is_visible}``).
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.TEXT_INPUT, init=False, repr=False
    )
    name: str
    label: str
    input_type: InputType | str | None = None
    required: bool | str | None = None
    min_chars: int | str | None = None
    max_chars: int | str | None = None
    helper_text: str | None = None
    enabled: bool | str | None = None
    visible: bool | str | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class TextArea(TextEntryComponent):
    """
    Represents a text entry component that allows for multiple lines of text.

    - This component must be inside a :class:`Form`.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#textarea>`_.

    Attributes:
        name: The name of this component (to be used dynamically or in action payloads).
        label: The label of the text area. Limited to 20 characters. Can be dynamic (e.g ``${data.label}``).
        required: Whether the text area is required or not. Can be dynamic (e.g ``${data.required}``).
        max_length: The maximum number of characters allowed in the text area. Can be dynamic (e.g ``${data.max_length}``).
        helper_text: The helper text of the text area. Limited to 80 characters. Can be dynamic (e.g ``${data.helper_text}``).
        enabled: Whether the text area is enabled or not. Default to ``True``. Can be dynamic (e.g ``${data.enabled}``).
        visible: Whether the text area is visible or not. Default to ``True``. Can be dynamic (e.g ``${data.is_visible}``).
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.TEXT_AREA, init=False, repr=False
    )
    name: str
    label: str
    required: bool | str | None = None
    max_length: int | str | None = None
    helper_text: str | None = None
    enabled: bool | str | None = None
    visible: bool | str | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class DataSource:
    """
    The data source of a component.

    Attributes:
        id: The ID of the data source.
        title: The title of the data source. Limited to 30 characters.
        description: The description of the data source. Limited to 300 characters.
        metadata: The metadata of the data source. Limited to 20 characters.
        enabled: Whether the data source is enabled or not. Default to ``True``.
    """

    id: str
    title: str
    description: str | None = None
    metadata: str | None = None
    enabled: bool | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class CheckboxGroup(Component):
    """
    CheckboxGroup component allows users to pick multiple selections from a list of options.

    - This component must be inside a :class:`Form`.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#checkbox>`_.

    Attributes:
        name: The name of this component (to be used dynamically or in action payloads).
        data_source: The data source of the checkbox group. Can be dynamic (e.g ``${data.data_source}``).
        label: The label of the checkbox group. Limited to 30 characters. Can be dynamic (e.g ``${data.label}``).
        min_selected_items: The minimum number of items that can be selected. Minimum value is 1. Can be dynamic (e.g ``${data.min_selected_items}``).
        max_selected_items: The maximum number of items that can be selected. Maximum value is 20. Can be dynamic (e.g ``${data.max_selected_items}``).
        required: Whether the checkbox group is required or not. Can be dynamic (e.g ``${data.required}``).
        visible: Whether the checkbox group is visible or not. Default to ``True``. Can be dynamic (e.g ``${data.is_visible}``).
        enabled: Whether the checkbox group is enabled or not. Default to ``True``. Can be dynamic (e.g ``${data.enabled}``).
        on_select_action: The action to perform when an item is selected.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.CHECKBOX_GROUP, init=False, repr=False
    )
    name: str
    data_source: list[DataSource] | tuple[DataSource] | str
    label: str | None = None
    min_selected_items: int | str | None = None
    max_selected_items: int | str | None = None
    required: bool | str | None = None
    visible: bool | str | None = None
    enabled: bool | str | None = None
    on_select_action: Action | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class RadioButtonsGroup(Component):
    """
    RadioButtonsGroup component allows users to pick a single selection from a list of options.

    - This component must be inside a :class:`Form`.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#radio>`_.

    Attributes:
        name: The name of this component (to be used dynamically or in action payloads).
        data_source: The data source of the radio buttons group. Can be dynamic (e.g ``${data.data_source}``).
        label: The label of the radio buttons group. Limited to 30 characters. Can be dynamic (e.g ``${data.label}``).
        required: Whether the radio buttons group is required or not. Can be dynamic (e.g ``${data.required}``).
        visible: Whether the radio buttons group is visible or not. Default to ``True``. Can be dynamic (e.g ``${data.is_visible}``).
        enabled: Whether the radio buttons group is enabled or not. Default to ``True``. Can be dynamic (e.g ``${data.enabled}``).
        on_select_action: The action to perform when an item is selected.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.RADIO_BUTTONS_GROUP, init=False, repr=False
    )
    name: str
    data_source: list[DataSource] | tuple[DataSource] | str
    label: str | None = None
    required: bool | str | None = None
    visible: bool | str | None = None
    enabled: bool | str | None = None
    on_select_action: Action | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class Footer(Component):
    """
    Footer component allows users to navigate to other screens or submit the flow.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#foot>`_.

    Attributes:
        label: The label of the footer. Limited to 35 characters. Can be dynamic (e.g ``${data.label}``).
        on_click_action: The action to perform when the footer is clicked. Required.
        left_caption: Can set left_caption and right_caption or only center_caption, but not all 3 at once. Limited to 15 characters. Can be dynamic (e.g ``${data.left_caption}``).
        center_caption: Can set center-caption or left-caption and right-caption, but not all 3 at once. Limited to 15 characters. Can be dynamic (e.g ``${data.center_caption}``).
        right_caption: Can set right-caption and left-caption or only center-caption, but not all 3 at once. Limited to 15 characters. Can be dynamic (e.g ``${data.right_caption}``).
        enabled: Whether the footer is enabled or not. Default to ``True``. Can be dynamic (e.g ``${data.enabled}``).
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.FOOTER, init=False, repr=False
    )
    visible: None = dataclasses.field(default=None, init=False, repr=False)
    label: str
    on_click_action: Action
    left_caption: str | None = None
    center_caption: str | None = None
    right_caption: str | None = None
    enabled: bool | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class OptIn(Component):
    """
    OptIn component allows users to check a box to opt in for a specific purpose.

    - This component must be inside a :class:`Form`.
    - Max number of Opt-Ins Per Screen is 5.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#opt>`_.

    Attributes:
        name: The name of this component (to be used dynamically or in action payloads).
        label: The label of the opt in. Limited to 30 characters. Can be dynamic (e.g ``${data.label}``).
        required: Whether the opt in is required or not. Can be dynamic (e.g ``${data.required}``).
        visible: Whether the opt in is visible or not. Default to ``True``. Can be dynamic (e.g ``${data.is_visible}``).
        on_click_action: The action to perform when the opt in is clicked.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.OPT_IN, init=False, repr=False
    )
    name: str
    label: str
    required: bool | str | None = None
    visible: bool | str | None = None
    on_click_action: Action | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class Dropdown(Component):
    """
    Dropdown component allows users to pick a single selection from a list of options.

    - This component must be inside a :class:`Form`.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#drop>`_.

    Attributes:
        name: The name of this component (to be used dynamically or in action payloads).
        label: The label of the dropdown. Limited to 30 characters. Can be dynamic (e.g ``${data.label}``).
        data_source: The data source of the dropdown. minimum 1 and maximum 200 items. Can be dynamic (e.g ``${data.data_source}``).
        enabled: Whether the dropdown is enabled or not. Default to ``True``. Can be dynamic (e.g ``${data.enabled}``).
        required: Whether the dropdown is required or not. Can be dynamic (e.g ``${data.required}``).
        visible: Whether the dropdown is visible or not. Default to ``True``. Can be dynamic (e.g ``${data.is_visible}``).
        on_select_action: The action to perform when an item is selected.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.DROPDOWN, init=False, repr=False
    )
    name: str
    label: str
    data_source: list[DataSource] | tuple[DataSource] | str
    enabled: bool | str | None = None
    required: bool | str | None = None
    visible: bool | str | None = None
    on_select_action: Action | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class EmbeddedLink(Component):
    """
    EmbeddedLink component allows users to click on a link that opens a web page.

    - This component must be inside a :class:`Form`.
    - Max Number of Embedded Links Per Screen is 2.
    - Empty or Blank value is not accepted for the text field.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#embed>`_.

    Attributes:
        text: The text of the embedded link. Limited to 35 characters. Can be dynamic (e.g ``${data.text}``).
        on_click_action: The action to perform when the embedded link is clicked.
        visible: Whether the embedded link is visible or not. Default to ``True``. Can be dynamic (e.g ``${data.is_visible}``).
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.EMBEDDED_LINK, init=False, repr=False
    )
    text: str
    on_click_action: Action
    visible: bool | str | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class DatePicker(Component):
    """
    DatePicker component allows users to select a date

    - This component must be inside a :class:`Form`.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#dp>`_.

    Attributes:
        name: The name of this component (to be used dynamically or in action payloads).
        label: The label of the date picker. Limited to 40 characters. Can be dynamic (e.g ``${data.label}``).
        min_date: The minimum date (timestamp in ms) that can be selected. Can be dynamic (e.g ``${data.min_date}``).
        max_date: The maximum date (timestamp in ms) that can be selected. Can be dynamic (e.g ``${data.max_date}``).
        unavailable_dates: The dates (timestamp in ms) that cannot be selected. Can be dynamic (e.g ``${data.unavailable_dates}``).
        helper_text: The helper text of the date picker. Limited to 80 characters. Can be dynamic (e.g ``${data.helper_text}``).
        enabled: Whether the date picker is enabled or not. Default to ``True``. Can be dynamic (e.g ``${data.enabled}``).
        required: Whether the date picker is required or not. Can be dynamic (e.g ``${data.required}``).
        visible: Whether the date picker is visible or not. Default to ``True``. Can be dynamic (e.g ``${data.is_visible}``).
        on_select_action: The action to perform when a date is selected.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.DATE_PICKER, init=False, repr=False
    )
    name: str
    label: str
    min_date: str | str | None = None
    max_date: str | str | None = None
    unavailable_dates: Iterable[str] | str | None = None
    helper_text: str | None = None
    enabled: bool | str | None = None
    required: bool | str | None = None
    visible: bool | str | None = None
    on_select_action: Action | None = None


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
    Image component allows users to pick multiple selections from a list of options.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#img>`_.
    - Supported images formats are JPEG PNG
    - Recommended image size is up to 300kb
    - Max number of images per screen is 3

    Attributes:
        src: Base64 of an image.
        width: The width of the image. Can be dynamic (e.g ``${data.width}``).
        height: The height of the image. Can be dynamic (e.g ``${data.height}``).
        scale_type: The scale type of the image. Defaule to ``ScaleType.CONTAIN`` Can be dynamic (e.g ``${data.scale_type}``). Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#image-scale-types>`_.
        aspect_ratio: The aspect ratio of the image. Default to ``1``. Can be dynamic (e.g ``${data.aspect_ratio}``).
        alt_text: Alternative Text is for the accessibility feature, eg. Talkback and Voice over. Can be dynamic (e.g ``${data.alt_text}``).
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.IMAGE, init=False, repr=False
    )
    src: str
    width: int | str | None = None
    height: int | str | None = None
    scale_type: ScaleType | str | None = None
    aspect_ratio: int | str
    alt_text: str | None = None
    visible: bool | str | None = None


class FlowActionType(utils.StrEnum):
    """
    Flow JSON provides a generic way to trigger asynchronous actions handled by a client through interactive UI elements.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#action>`_.

    Attributes:
        COMPLETE: Triggers the termination of the Flow with the provided payload
         (Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#complete-action>`_).
        DATA_EXCHANGE: TSending Data to WhatsApp Flows Data Endpoint
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
        type: The type of the next action
        name: The name of the next screen or plugin
    """

    type: ActionNextType | str
    name: str


@dataclasses.dataclass(slots=True, kw_only=True)
class Action:
    """
    Action component allows users to trigger asynchronous actions handled by a client through interactive UI elements.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#action>`_.

    Attributes:
        name: The type of the action
        next: The next action (only for ``FlowActionType.NAVIGATE``)
        payload: The payload of the action
    """

    name: FlowActionType | str
    next: ActionNext | None = None
    payload: dict[str, str] | None = None
