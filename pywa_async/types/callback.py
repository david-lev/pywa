"""This module contains the callback types."""

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

from pywa.types.callback import *  # noqa MUST BE IMPORTED FIRST
from pywa.types.callback import (
    CallbackButton as _CallbackButton,
    CallbackSelection as _CallbackSelection,
)  # noqa MUST BE IMPORTED FIRST
from .base_update import BaseUserUpdateAsync


import dataclasses
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from ..client import WhatsApp


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class CallbackButton(BaseUserUpdateAsync, _CallbackButton[CallbackDataT]):
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


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class CallbackSelection(BaseUserUpdateAsync, _CallbackSelection[CallbackDataT]):
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
