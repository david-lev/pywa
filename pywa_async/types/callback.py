"""This module contains the callback types."""

from pywa.types.callback import *  # noqa MUST BE IMPORTED FIRST

__all__ = [
    "CallbackButton",
    "CallbackSelection",
    "Button",
    "ButtonUrl",
    "SectionRow",
    "Section",
    "SectionList",
    "FlowButton",
    "CallbackData",
    "CallbackDataT",
]

import dataclasses
import datetime
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Iterable,
    Literal,
)

from .base_update import BaseUserUpdate  # noqa
from .flows import FlowStatus, FlowActionType
from .others import MessageType, Metadata, ReplyToMessage, User, InteractiveType
from .. import utils

if TYPE_CHECKING:
    from ..client import WhatsApp


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class CallbackButton(BaseUserUpdate, Generic[CallbackDataT]):
    """
    Represents a callback button (Incoming update when user clicks on :class:`Button` or chooses
    :class:`Template.QuickReplyButtonData`).

    ``CallbackButton`` is a generic class, so when providing a ``factory`` parameter in callback handlers, you can
    specify the type of the factory to get autocomplete in the ``data`` attribute.

    Here is an example:

        >>> from pywa.types import CallbackData
        >>> from dataclasses import dataclass
        >>> @dataclass(frozen=True, slots=True)
        >>> class UserData(CallbackData): # Subclass CallbackData
        ...     id: int
        ...     name: str
        ...     admin: bool

        >>> from pywa import WhatsApp
        >>> from pywa.types import Button, CallbackButton
        >>> wa = WhatsApp(...)
        >>> wa.send_message(
        ...     to='972987654321',
        ...     text='Click the button to get the user',
        ...     buttons=[Button(title='Get user', callback_data=UserData(id=123, name='david', admin=True))]
        ... )                                     # Here ^^^ we use the UserData class as the callback data

        >>> @wa.on_callback_button(factory=UserData) # Use the factory parameter to convert the callback data
        ... def on_user_data(_: WhatsApp, btn: CallbackButton[UserData]): # For autocomplete
        ...    if btn.data.admin: print(btn.data.id) # Access the data object as an attribute

    You can even use multiple factories, and not only ``CallbackData`` subclasses!

        >>> from enum import Enum
        >>> class State(str, Enum):
        ...     START = 's'
        ...     END = 'e'

        >>> wa.send_message(
        ...     to='972987654321',
        ...     text='Click the button to get the user and state',
        ...     buttons=[Button(title='Get user', callback_data=(UserData(id=123, name='david', admin=True), State.START))]
        ... )                                     # Here ^^^ we send a tuple of UserData and State

        >>> @wa.on_callback_button(factory=(UserData, State)) # Use the factory parameter to convert the callback data
        ... def on_user_data(_: WhatsApp, btn: CallbackButton[tuple[UserData, State]]): # For autocomplete
        ...    user, state = btn.data # Unpack the tuple
        ...    if user.admin: print(user.id, state)


    Attributes:
        id: The ID of the message.
        metadata: The metadata of the message (to which phone number it was sent).
        type: The message type (:class:`MessageType.INTERACTIVE` for :class:`Button` presses or
        type: The message type (:class:`MessageType.INTERACTIVE` for :class:`Button` presses or
         :class:`MessageType.BUTTON` for :class:`Template.QuickReplyButtonData` choices).
        from_user: The user who sent the message.
        timestamp: The timestamp when the message was sent.
        reply_to_message: The message to which this callback button is a reply to.
        data: The data of the button (the ``callback_data`` parameter you provided in :class:`Button` or
         :class:`Template.QuickReplyButtonData`).
        title: The title of the button.
    """

    id: str
    type: MessageType
    metadata: Metadata
    from_user: User
    timestamp: datetime.datetime
    reply_to_message: ReplyToMessage
    data: CallbackDataT
    title: str

    _txt_fields = ("data",)

    @classmethod
    def from_update(cls, client: "WhatsApp", update: dict) -> "CallbackButton":
        msg = (value := update["entry"][0]["changes"][0]["value"])["messages"][0]
        match msg_type := msg["type"]:
            case MessageType.INTERACTIVE:
                title = msg["interactive"]["button_reply"]["title"]
                data = msg["interactive"]["button_reply"]["id"]
            case MessageType.BUTTON:
                title = msg["button"]["text"]
                data = msg["button"]["payload"]
            case _:
                raise ValueError(f"Invalid message type {msg_type}")
        return cls(
            _client=client,
            raw=update,
            id=msg["id"],
            metadata=Metadata.from_dict(value["metadata"]),
            type=MessageType(msg_type),
            from_user=User.from_dict(value["contacts"][0]),
            timestamp=datetime.datetime.fromtimestamp(int(msg["timestamp"])),
            reply_to_message=ReplyToMessage.from_dict(msg["context"]),
            data=data,
            title=title,
        )


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class CallbackSelection(BaseUserUpdate, Generic[CallbackDataT]):
    """
    Represents a callback selection (Incoming update when user clicks on :class:`SectionRow` in :class:`SectionList`).

    ``CallbackSelection`` is a generic class, so when providing a ``factory`` parameter in callback handlers, you can
    specify the type of the factory to get autocomplete in the ``data`` attribute.

    Here is an example:

        >>> from pywa.types import CallbackData
        >>> from dataclasses import dataclass
        >>> @dataclass(frozen=True, slots=True)
        >>> class UserData(CallbackData): # Subclass CallbackData
        ...     id: int
        ...     name: str
        ...     admin: bool

        >>> from pywa import WhatsApp
        >>> from pywa.types import SectionList, Section, SectionRow, CallbackSelection
        >>> wa = WhatsApp(...)
        >>> wa.send_message(
        ...     to='972987654321',
        ...     text='Click the button to get the user',
        ...     buttons=SectionList(
        ...         button_title='Get user', sections=[
        ...             Section(title='Users', rows=[
        ...                 SectionRow(title='Get user', callback_data=UserData(id=123, name='david', admin=True))
        ...             ])                              # Here ^^^ we use the UserData class as the callback data
        ...         ]
        ...     )
        ... )

        >>> @wa.on_callback_selection(factory=UserData) # Use the factory parameter to convert the callback data
        ... def on_user_data(_: WhatsApp, sel: CallbackSelection[UserData]): # For autocomplete
        ...    if sel.data.admin: print(sel.data.id) # Access the data object as an attribute

    You can even use multiple factories, and not only ``CallbackData`` subclasses!

        >>> from enum import Enum
        >>> class State(str, Enum):
        ...     START = 's'
        ...     END = 'e'

        >>> wa.send_message(
        ...     to='972987654321',
        ...     text='Click the button to get the user and state',
        ...     buttons=SectionList(
        ...         button_title='Get user', sections=[
        ...             Section(title='Users', rows=[
        ...                 SectionRow(title='Get user', callback_data=(UserData(id=123, name='david', admin=True), State.START))
        ...             ])                              # Here ^^^ we send a tuple of UserData and State
        ...         ]
        ...     )
        ... )

        >>> @wa.on_callback_selection(factory=(UserData, State)) # Use the factory parameter to convert the callback data
        ... def on_user_data(_: WhatsApp, sel: CallbackSelection[tuple[UserData, State]]): # For autocomplete
        ...    user, state = sel.data # Unpack the tuple
        ...    if user.admin: print(user.id, state)

    Attributes:
        id: The ID of the message.
        metadata: The metadata of the message (to which phone number it was sent).
        type: The message type (always :class:`MessageType.INTERACTIVE`).
        from_user: The user who sent the message.
        timestamp: The timestamp when the message was sent.
        reply_to_message: The message to which this callback selection is a reply to.
        data: The data of the selection (the ``callback_data`` parameter you provided in :class:`SectionRow`).
        title: The title of the selection.
        description: The description of the selection (optional).
    """

    id: str
    type: MessageType
    metadata: Metadata
    from_user: User
    timestamp: datetime.datetime
    reply_to_message: ReplyToMessage
    data: CallbackDataT
    title: str
    description: str | None

    _txt_fields = ("data",)

    @classmethod
    def from_update(cls, client: "WhatsApp", update: dict) -> "CallbackSelection":
        msg = (value := update["entry"][0]["changes"][0]["value"])["messages"][0]
        return cls(
            _client=client,
            raw=update,
            id=msg["id"],
            metadata=Metadata.from_dict(value["metadata"]),
            type=MessageType(msg["type"]),
            from_user=User.from_dict(value["contacts"][0]),
            timestamp=datetime.datetime.fromtimestamp(int(msg["timestamp"])),
            reply_to_message=ReplyToMessage.from_dict(msg["context"]),
            data=msg["interactive"]["list_reply"]["id"],
            title=msg["interactive"]["list_reply"]["title"],
            description=msg["interactive"]["list_reply"].get("description"),
        )


def _resolve_callback_data(data: CallbackDataT) -> str:
    """Internal function to convert callback data to a string."""
    if isinstance(data, str):
        return data
    elif isinstance(data, CallbackData):
        return data.to_str()
    elif isinstance(data, Iterable):
        if any(isinstance(item, CallbackData) for item in data):
            return CallbackData.join_to_str(*data)
    raise TypeError(f"Invalid callback data type {type(data)}")


@dataclasses.dataclass(slots=True)
class Button:
    """
    Represents a button in the button list.

    Attributes:
        title: The title of the button (up to 20 characters).
        callback_data: The data to send when the user clicks on the button (up to 256 characters, for complex data
         You can use :class:`CallbackData`).
    """

    title: str
    callback_data: CallbackDataT

    def to_dict(self) -> dict:
        return {
            "type": "reply",
            "reply": {
                "id": _resolve_callback_data(self.callback_data),
                "title": self.title,
            },
        }


@dataclasses.dataclass(slots=True)
class ButtonUrl:
    """
    Represents a button in the bottom of the message that opens a URL.

    Attributes:
        title: The title of the button (up to 20 characters).
        url: The URL to open when the user clicks on the button.
    """

    title: str
    url: str

    def to_dict(self) -> dict:
        return {
            "name": InteractiveType.CTA_URL,
            "parameters": {"display_text": self.title, "url": self.url},
        }


@dataclasses.dataclass(slots=True)
class SectionRow:
    """
    Represents a choice row in a section rows.

    Attributes:
        title: The title of the row (up to 24 characters).
        callback_data: The payload to send when the user clicks on the row (up to 200 characters, for complex data
            You can use :class:`CallbackData`).
        description: The description of the row (optional, up to 72 characters).
    """

    title: str
    callback_data: CallbackDataT
    description: str | None = None

    def to_dict(self) -> dict:
        d = {
            "id": _resolve_callback_data(self.callback_data),
            "title": self.title,
        }
        if self.description:
            d["description"] = self.description
        return d


@dataclasses.dataclass(slots=True)
class Section:
    """
    Represents a section in a section list.

    Attributes:
        title: The title of the section (up to 24 characters).
        rows: The rows in the section (at least 1, no more than 10).
    """

    title: str
    rows: Iterable[SectionRow]

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "rows": tuple(row.to_dict() for row in self.rows),
        }


@dataclasses.dataclass(slots=True)
class SectionList:
    """
    Represents a section list in an interactive message.

    Attributes:
        button_title: The title of the button that opens the section list (up to 20 characters).
        sections: The sections in the section list (at least 1, no more than 10).
    """

    button_title: str
    sections: Iterable[Section]

    def to_dict(self) -> dict:
        return {
            "button": self.button_title,
            "sections": tuple(section.to_dict() for section in self.sections),
        }


@dataclasses.dataclass(slots=True)
class FlowButton:
    """
    Represents a button that opens a flow.

    Attributes:
        title: Text on the CTA button. e.g ``SignUp``, Up to 20 characters, no emojis)
        flow_id: Unique ID of the Flow provided by WhatsApp.
        flow_token: Flow token generated by the business to serve as an identifier for data exchange.
        flow_message_version: Version of the flow message. Default is the latest version.
        flow_action_type: Type of action to be performed when the user clicks on the CTA button.
        flow_action_screen: The ID of the first Screen.
         Required when ``flow_action_type`` is ``FlowActionType.NAVIGATE`` (default).
        flow_action_payload: The payload to send when the user clicks on the button
         (optional, only when ``flow_action_type`` is ``FlowActionType.NAVIGATE``).
        mode: The mode of the flow. ``FlowStatus.PUBLISHED`` (default) or ``FlowStatus.DRAFT`` (for testing).
    """

    title: str
    flow_id: str | int
    flow_token: str
    flow_action_type: (
        Literal[FlowActionType.NAVIGATE, FlowActionType.DATA_EXCHANGE] | None
    ) = None
    flow_action_screen: str | None = None
    flow_action_payload: dict[str, Any] | None = None
    flow_message_version: int | float | str | Literal[utils.Version.FLOW_MSG] = (
        utils.Version.FLOW_MSG
    )
    mode: Literal[FlowStatus.PUBLISHED, FlowStatus.DRAFT] = FlowStatus.PUBLISHED

    def __post_init__(self):
        utils.Version.FLOW_MSG.validate_min_version(str(self.flow_message_version))
        if (
            self.flow_action_type == FlowActionType.NAVIGATE
            and self.flow_action_screen is None
        ):
            raise ValueError(
                "flow_action_screen cannot be None when flow_action_type is FlowActionType.NAVIGATE"
            )

    def to_dict(self) -> dict:
        return {
            "name": InteractiveType.FLOW,
            "parameters": {
                "mode": self.mode.lower(),
                "flow_message_version": str(self.flow_message_version),
                "flow_token": self.flow_token,
                "flow_id": self.flow_id,
                "flow_cta": self.title,
                **(
                    {"flow_action": str(self.flow_action_type)}
                    if self.flow_action_type is not None
                    else {}
                ),
                **(
                    {
                        "flow_action_payload": {
                            "screen": self.flow_action_screen,
                            **(
                                {"data": self.flow_action_payload}
                                if self.flow_action_payload is not None
                                else {}
                            ),
                        }
                    }
                    if self.flow_action_type == FlowActionType.NAVIGATE
                    else {}
                ),
            },
        }
