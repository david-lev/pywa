from __future__ import annotations

import abc
import dataclasses
from typing import Iterable, Literal

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
    "DataSource",
    "Action",
    "ActionType",
    "ActionNext",
    "ActionNextType",
]


class FlowCategory(utils.StrEnum):
    """The category of the flow"""

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
    """Flow is the top level component that holds the screens."""

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
    """Screen is a top level component that holds the data and layout."""

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
    """Layout holds the components that are displayed on a screen."""

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
    """Form component is the top level component that can hold other components."""

    type: ComponentType = dataclasses.field(default=ComponentType.FORM, init=False)
    visible: None = dataclasses.field(default=None, init=False)
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
    """The text weight"""

    BOLD = "bold"
    ITALIC = "italic"
    BOLD_ITALIC = "bold_italic"
    NORMAL = "normal"


@dataclasses.dataclass(slots=True, kw_only=True)
class TextHeading(TextComponent):
    """
    This is the top level title of a page.

    https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#heading
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.TEXT_HEADING, init=False
    )
    text: str
    visible: bool | str | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class TextSubheading(TextComponent):
    """
    This is a subheading of a page.

    https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#subheading
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.TEXT_SUBHEADING, init=False
    )
    text: str
    visible: bool | str | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class TextBody(TextComponent):
    """
    This is the main body text of a page.

    https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#body
    """

    type: ComponentType = dataclasses.field(default=ComponentType.TEXT_BODY, init=False)
    text: str
    font_weight: FontWeight | str | None = None
    strikethrough: bool | str | None = None
    visible: bool | str | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class TextCaption(TextComponent):
    """
    This is a caption text of a page.

    https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#caption
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.TEXT_CAPTION, init=False
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
    """The input type"""

    TEXT = "text"
    NUMBER = "number"
    EMAIL = "email"
    PASSWORD = "password"
    PASSCODE = "passcode"
    PHONE = "phone"


@dataclasses.dataclass(slots=True, kw_only=True)
class TextInput(TextEntryComponent):
    """
    This is a text entry component that allows for a single line of text.

    https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#textinput
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.TEXT_INPUT, init=False
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
    This is a text entry component that allows for multiple lines of text.

    https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#textarea
    """

    type: ComponentType = dataclasses.field(default=ComponentType.TEXT_AREA, init=False)
    name: str
    label: str
    required: bool | str | None = None
    max_length: int | str | None = None
    helper_text: str | None = None
    enabled: bool | str | None = None
    visible: bool | str | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class DataSource:
    id: str
    title: str
    description: str | None = None
    metadata: str | None = None
    enabled: bool | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class CheckboxGroup(Component):
    """
    CheckboxGroup component allows users to pick multiple selections from a list of options.

    https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#checkbox
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.CHECKBOX_GROUP, init=False
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

    https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#radio
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.RADIO_BUTTONS_GROUP, init=False
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

    https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#foot
    """

    type: ComponentType = dataclasses.field(default=ComponentType.FOOTER, init=False)
    visible: None = dataclasses.field(default=None, init=False)
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

    https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#opt
    """

    type: ComponentType = dataclasses.field(default=ComponentType.OPT_IN, init=False)
    name: str
    label: str
    required: bool | str | None = None
    visible: bool | str | None = None
    on_click_action: Action | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class Dropdown(Component):
    """
    Dropdown component allows users to pick a single selection from a list of options.

    https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#drop
    """

    type: ComponentType = dataclasses.field(default=ComponentType.DROPDOWN, init=False)
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

    https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#embed
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.EMBEDDED_LINK, init=False
    )
    text: str
    on_click_action: Action
    visible: bool | str | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class DatePicker(Component):
    """
    DatePicker component allows users to select a date

    https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#dp
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.DATE_PICKER, init=False
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


@dataclasses.dataclass(slots=True, kw_only=True)
class Image(Component):
    """
    Image component allows users to pick multiple selections from a list of options.

    https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components#img
    """

    type: ComponentType = dataclasses.field(default=ComponentType.IMAGE, init=False)
    src: str
    width: int | str | None = None
    height: int | str | None = None
    scale_type: Literal["cover", "contain"] | None = None
    aspect_ratio: int | str
    alt_text: str | None = None
    visible: bool | str | None = None


class ActionType(utils.StrEnum):
    COMPLETE = "complete"
    DATA_EXCHANGE = "data_exchange"
    NAVIGATE = "navigate"


class ActionNextType(utils.StrEnum):
    SCREEN = "screen"
    PLUGIN = "plugin"


@dataclasses.dataclass(slots=True, kw_only=True)
class ActionNext:
    type: ActionNextType | str
    name: str


@dataclasses.dataclass(slots=True, kw_only=True)
class Action:
    name: ActionType | str
    next: ActionNext | None = None
    payload: dict[str, str] | None = None
