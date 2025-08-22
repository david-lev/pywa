"""This module contains the callback types."""

from pywa.types.callback import *  # noqa MUST BE IMPORTED FIRST
from pywa.types.callback import (
    CallbackButton as _CallbackButton,
    CallbackSelection as _CallbackSelection,
    _CallbackDataT,
)  # noqa MUST BE IMPORTED FIRST
from .base_update import BaseUserUpdateAsync


import dataclasses
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from ..client import WhatsApp


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class CallbackButton(BaseUserUpdateAsync, _CallbackButton[_CallbackDataT]):
    """
    Represents a callback button (Incoming update when user clicks on :class:`~pywa.types.callback.Button` or on :class:`~pywa.types.templates.QuickReplyButton`'s template).

    ``CallbackButton`` is a generic class, so when providing a ``factory`` parameter in callback handlers, you can
    specify the type of the factory to get autocomplete in the ``data`` attribute.

    Here is an example:

        >>> from pywa_async.types import CallbackData
        >>> from dataclasses import dataclass
        >>> @dataclass(frozen=True, slots=True)
        >>> class UserData(CallbackData): # Subclass CallbackData
        ...     id: int
        ...     name: str
        ...     admin: bool

        >>> from pywa_async import WhatsApp
        >>> from pywa_async.types import Button, CallbackButton
        >>> wa = WhatsApp(...)
        >>> wa.send_message(
        ...     to='972987654321',
        ...     text='Click the button to get the user',
        ...     buttons=[Button(title='Get user', callback_data=UserData(id=123, name='david', admin=True))]
        ... )                                     # Here ^^^ we use the UserData class as the callback data

        >>> @wa.on_callback_button(factory=UserData) # Use the factory parameter to convert the callback data
        ... def on_user_data(_: WhatsApp, btn: CallbackButton[UserData]): # For autocomplete
        ...    if btn.data.admin: print(btn.data.id) # Access the data object as an attribute


    Attributes:
        id: The ID of the message.
        metadata: The metadata of the message (to which phone number it was sent).
        type: The message type (:class:`MessageType.INTERACTIVE` for :class:`~pywa.types.callback.Button` presses or :class:`MessageType.BUTTON` for :class:`~pywa.types.templates.QuickReplyButton` clicks).
        from_user: The user who sent the message.
        timestamp: The timestamp when the message was sent (in UTC).
        reply_to_message: The message to which this callback button is a reply to.
        data: The data of the button (the ``callback_data`` parameter you provided in :class:`~pywa.types.callback.Button` or :class:`~pywa.types.templates.QuickReplyButton`).
        title: The title of the button.
        shared_data: Shared data between handlers.
    """


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class CallbackSelection(BaseUserUpdateAsync, _CallbackSelection[_CallbackDataT]):
    """
    Represents a callback selection (Incoming update when user clicks on :class:`~pywa.types.callback.SectionRow` in :class:`~pywa.types.callback.SectionList`).

    ``CallbackSelection`` is a generic class, so when providing a ``factory`` parameter in callback handlers, you can
    specify the type of the factory to get autocomplete in the ``data`` attribute.

    Here is an example:

        >>> from pywa_async.types import CallbackData
        >>> from dataclasses import dataclass
        >>> @dataclass(frozen=True, slots=True)
        >>> class UserData(CallbackData): # Subclass CallbackData
        ...     id: int
        ...     name: str
        ...     admin: bool

        >>> from pywa_async import WhatsApp
        >>> from pywa_async.types import SectionList, Section, SectionRow, CallbackSelection
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

    Attributes:
        id: The ID of the message.
        metadata: The metadata of the message (to which phone number it was sent).
        type: The message type (always :class:`MessageType.INTERACTIVE`).
        from_user: The user who sent the message.
        timestamp: The timestamp when the message was sent (in UTC).
        reply_to_message: The message to which this callback selection is a reply to.
        data: The data of the selection (the ``callback_data`` parameter you provided in :class:`~pywa.types.callback.SectionRow`).
        title: The title of the selection.
        description: The description of the selection (optional).
    """
