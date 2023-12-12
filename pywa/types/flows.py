from __future__ import annotations

import abc
import dataclasses
from typing import Iterable

from pywa import utils

__all__ = [
    "FlowCategory",
    "Flow",
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
    "ActionType",
    "ActionNext",
    "ActionNextType",
]


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


_UNDERSCORE_FIELDS = {
    "routing_model",
    "data_api_version",
    "data_channel_uri",
    "refresh_on_back",
}


@dataclasses.dataclass(slots=True, kw_only=True)
class Flow:
    """
    Represents a WhatsApp flow which is a collection of screens.

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

    Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson#forms-and-form-properties>`_.

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

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#opt>`_.
    - Max number of Opt-Ins Per Screen is 5.

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

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#embed>`_.
    - Max Number of Embedded Links Per Screen is 2.
    - Empty or Blank value is not accepted for the text field.

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


class ActionType(utils.StrEnum):
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
        next: The next action (only for ``ActionType.NAVIGATE``)
        payload: The payload of the action
    """

    name: ActionType | str
    next: ActionNext | None = None
    payload: dict[str, str] | None = None
