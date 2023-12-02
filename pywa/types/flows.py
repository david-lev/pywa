from __future__ import annotations

import abc
import dataclasses
from typing import Iterable

from pywa import utils

__all__ = [
    "Flow",
    "FlowData",
    "Screen",
    "Layout",
    "LayoutType",
    "TextHeading",
    "TextSubheading",
    "TextBody",
    "TextCaption",
    "TextInput",
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
]


@dataclasses.dataclass
class FlowData(abc.ABC):
    __types__ = {
        str: "string",
        int: "number",
        float: "number",
        bool: "boolean",
        list: "array",
        tuple: "array",
        set: "array",
        dict: "object",
    }

    @classmethod
    def to_dict(cls):
        data = {}
        for field in dataclasses.fields(cls):
            try:
                data[field.name] = {
                    "type": cls.__types__[field.type],
                    "__example__": field.default,
                }
            except KeyError:
                raise TypeError(
                    f"Field {field.name} has wrong type. use one of {cls.__types__.keys()}"
                )
        return {"data": data}


@dataclasses.dataclass(slots=True, kw_only=True)
class Flow:
    version: str | float
    screens: Iterable[Screen]


@dataclasses.dataclass(slots=True, kw_only=True)
class Screen:
    id: str
    layout: Layout
    terminal: bool | None = None
    data: Iterable[type[FlowData]] | None = None
    title: str | None = None
    refresh_on_back: bool = False


class LayoutType(utils.StrEnum):
    SINGLE_COLUMN = "SingleColumnLayout"


@dataclasses.dataclass(slots=True, kw_only=True)
class Layout:
    type: LayoutType = LayoutType.SINGLE_COLUMN
    children: Iterable[Component]


class Component(abc.ABC):
    @abc.abstractmethod
    @property
    def type(self) -> utils.StrEnum:
        ...

    @abc.abstractmethod
    @property
    def visible(self) -> bool:
        ...

    class Type(utils.StrEnum):
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


class TextComponent(Component, abc.ABC):
    @abc.abstractmethod
    @property
    def text(self) -> str:
        ...

    class FontWeight(utils.StrEnum):
        BOLD = "bold"
        ITALIC = "italic"
        BOLD_ITALIC = "bold_italic"
        NORMAL = "normal"


@dataclasses.dataclass(slots=True, kw_only=True)
class TextHeading(TextComponent):
    type: TextComponent.Type = dataclasses.field(
        default=TextComponent.Type.TEXT_HEADING, init=False
    )
    text: str
    visible: bool = True


@dataclasses.dataclass(slots=True, kw_only=True)
class TextSubheading(TextComponent):
    type: TextComponent.Type = dataclasses.field(
        default=TextComponent.Type.TEXT_SUBHEADING, init=False
    )
    text: str
    visible: bool = True


@dataclasses.dataclass(slots=True, kw_only=True)
class TextBody(TextComponent):
    type: TextComponent.Type = dataclasses.field(
        default=TextComponent.Type.TEXT_BODY, init=False
    )
    text: str
    visible: bool = True
    font_weight: FontWeight | str = TextComponent.FontWeight.NORMAL
    strikethrough: bool = False

    FontWeight = TextComponent.FontWeight


@dataclasses.dataclass(slots=True, kw_only=True)
class TextCaption(TextComponent):
    type: TextComponent.Type = dataclasses.field(
        default=TextComponent.Type.TEXT_CAPTION, init=False
    )
    text: str
    visible: bool = True
    font_weight: FontWeight | str = TextComponent.FontWeight.NORMAL
    strikethrough: bool = False

    FontWeight = TextComponent.FontWeight


class TextEntryComponent(Component, abc.ABC):
    @abc.abstractmethod
    @property
    def label(self) -> str:
        ...

    @abc.abstractmethod
    @property
    def required(self) -> bool:
        ...

    @abc.abstractmethod
    @property
    def name(self) -> str:
        ...

    @abc.abstractmethod
    @property
    def visible(self) -> bool:
        ...

    @abc.abstractmethod
    @property
    def helper_text(self) -> str:
        ...

    class InputType(utils.StrEnum):
        TEXT = "text"
        NUMBER = "number"
        EMAIL = "email"
        PASSWORD = "password"
        PASSCODE = "passcode"
        PHONE = "phone"


@dataclasses.dataclass(slots=True, kw_only=True)
class TextInput(TextEntryComponent):
    type: TextEntryComponent.Type = dataclasses.field(
        default=TextEntryComponent.Type.TEXT_INPUT, init=False
    )
    label: str
    input_type: TextInput.InputType | str
    required: bool
    min_chars: int | str
    max_chars: int | str
    helper_text: str
    visible: bool
    name: str

    InputType = TextEntryComponent.InputType


@dataclasses.dataclass(slots=True, kw_only=True)
class TextArea(TextEntryComponent):
    type: TextEntryComponent.Type = dataclasses.field(
        default=TextEntryComponent.Type.TEXT_AREA, init=False
    )
    name: str
    label: str
    required: bool | None = None
    max_length: int | str | None = None
    helper_text: str | None = None
    enabled: bool = True
    visible: bool = True


@dataclasses.dataclass(slots=True, kw_only=True)
class DataSource:
    id: str
    title: str
    description: str | None = None
    metadata: str | None = None
    enabled: bool | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class CheckboxGroup(Component):
    type: Component.Type = dataclasses.field(
        default=Component.Type.CHECKBOX_GROUP, init=False
    )
    name: str
    label: str
    required: bool
    visible: bool
    min_selected_items: int
    max_selected_items: int
    data_source: list[DataSource]
    on_select_action: Action | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class RadioButtonsGroup(Component):
    type: Component.Type = dataclasses.field(
        default=Component.Type.RADIO_BUTTONS_GROUP, init=False
    )
    name: str
    label: str
    required: bool = True
    visible: bool = True
    data_source: list[DataSource]
    on_select_action: Action | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class Footer(Component):
    type: Component.Type = dataclasses.field(default=Component.Type.FOOTER, init=False)
    label: str
    left_caption: str
    center_caption: str
    right_caption: str
    enabled: bool
    visible: bool
    on_click_action: Action


@dataclasses.dataclass(slots=True, kw_only=True)
class OptIn(Component):
    type: Component.Type = dataclasses.field(default=Component.Type.OPT_IN, init=False)
    label: str
    required: bool
    name: str
    on_click_action: Action | None = None
    visible: bool = True


@dataclasses.dataclass(slots=True, kw_only=True)
class Dropdown(Component):
    type: Component.Type = dataclasses.field(
        default=Component.Type.DROPDOWN, init=False
    )
    label: str
    data_source: list[DataSource]
    name: str
    enabled: bool
    required: bool
    visible: bool
    on_select_action: Action | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class EmbeddedLink(Component):
    type: Component.Type = dataclasses.field(
        default=Component.Type.EMBEDDED_LINK, init=False
    )
    text: str
    on_click_action: Action | None = None
    visible: bool


@dataclasses.dataclass(slots=True, kw_only=True)
class DatePicker(Component):
    type: Component.Type = dataclasses.field(
        default=Component.Type.DATE_PICKER, init=False
    )
    label: str
    min_date: str
    max_date: str
    name: str
    unavailable_dates: list[str]
    visible: bool
    helper_text: str
    enabled: bool
    on_select_action: Action | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class Image(Component):
    type: Component.Type = dataclasses.field(default=Component.Type.IMAGE, init=False)
    src: str
    width: int
    height: int
    scale_type: str
    aspect_ratio: int
    alt_text: str
    visible: bool


@dataclasses.dataclass(slots=True, kw_only=True)
class Action:
    name: Type | str
    next: Next | None = None
    payload: dict[str, str] | None = None

    class Type(utils.StrEnum):
        COMPLETE = "complete"
        DATA_EXCHANGE = "data_exchange"
        NAVIGATE = "navigate"

    @dataclasses.dataclass(slots=True, kw_only=True)
    class Next:
        type: str
        name: str
