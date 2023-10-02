__all__ = [
    'CallbackButton',
    'CallbackSelection',
    'Button',
    'SectionRow',
    'Section',
    'SectionList',
    'CallbackData',
    'CallbackDataT'
]

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Iterable, TypeVar, Generic, Callable, Any
from .base_update import BaseUserUpdate
from .others import Metadata, User, ReplyToMessage, MessageType

if TYPE_CHECKING:
    from pywa.client import WhatsApp


class CallbackData:
    """
    Base class for all callback data classes. Subclass this class to create a type-safe callback data class.

        If you use dataclasses, which is the recommended way, you should not use ``kw_only=True``.
        This is because we are limited to 200 characters in the callback data, so we need to use positional arguments.
        So object like User(id=123, name='John') will be converted to ``123:John``.

        Currently, the following types are supported:
        ``str``, ``int``, ``bool``, ``float`` (and ``Enum`` that inherits from ``str`` e.g ``class State(str, Enum)``).

        Also, you cannot use the characters ``:`` and ``;`` in the callback data, because they are used as separators.
        You can change the separators by overriding ``__callback_sep__`` (for individual objects) and
        ``CallbackData.__callback_sep__`` (In the base class level, affects all child classes).


    Example:

        >>> from pywa import WhatsApp
        >>> from pywa.types import CallbackData, Button
        >>> from dataclasses import dataclass # Use dataclass to get free ordered __init__
        >>> @dataclass(frozen=True, slots=True) # Do not use kw_only=True
        >>> class UserData(CallbackData): # Subclass CallbackData
        ...     id: int
        ...     admin: bool

        >>> wa = WhatsApp(...)
        >>> wa.send_message(
        ...     to='972987654321',
        ...     text='Click the button to get the user',
        ...     buttons=[Button(title='Get user', callback_data=UserData(id=123, admin=True))]
        ... )

        >>> @wa.on_callback_button(factory=UserData) # Use the factory parameter to convert the callback data
        ... def on_user_data(client: WhatsApp, btn: CallbackButton[UserData]): # For autocomplete
        ...    if btn.data.admin: print(btn.data.id) # Access the data object as an attribute
    """
    __callback_id__: int = 0
    """Unique ID for each callback data class. Do not override this."""
    __callback_sep__: str = ';'
    """The separator between multiple callback objects. (e.g ``123:John;456:Jane``)"""
    __callback_data_sep__: str = ':'
    """The separator between the callback fields, Can be overridden in subclasses (e.g ``123:John``)."""
    __allowed_types__: tuple[type, ...] = (str, int, bool, float)
    """The allowed types in the callback data."""

    def __init_subclass__(cls, **kwargs):
        """Validate the callback data class and set a unique ID for it."""
        super().__init_subclass__(**kwargs)
        if not (annotations := cls.__annotations__.items()):
            raise TypeError(f"Callback data class {cls.__name__} must have at least one field.")
        if unsupported_fields := {
            (field_name, field_type) for field_name, field_type in annotations
            if not issubclass(field_type, (types := cls.__allowed_types__))
        }:
            raise TypeError(f"Unsupported types {unsupported_fields} in callback data. Use one of {types}.")
        cls.__callback_id__ = CallbackData.__callback_id__
        CallbackData.__callback_id__ += 1

    @classmethod
    def from_str(
            cls,
            data: str,
    ) -> 'CallbackData':
        """
        Internal function to convert a callback string to a callback object.
        """
        try:
            # noinspection PyArgumentList
            return cls(*(
                annotation(value) for annotation, value in zip(
                    cls.__annotations__.values(),
                    data.split(cls.__callback_data_sep__)[1:],
                    strict=True
                )
            ))
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid callback data for {cls.__name__}: {data}") from e

    @staticmethod
    def _not_contains(value: Any, *not_) -> str:
        """Internal function to validate that the value does not contain the separator."""
        if any(sep in (str_val := str(value)) for sep in not_):
            raise ValueError(f"Callback data cannot contain the characters {not_} "
                             f"Because they are used as separators. \nYou can change the separators by overriding "
                             f"``__callback_sep__`` (for individual objects) and ``CallbackData.__callback_sep__`` "
                             f"(In the base class level, affects all child classes).")
        return str_val

    def to_str(self) -> str:
        """
        Internal function to convert a callback object to a callback string.
        """
        return self.__callback_data_sep__.join((str(self.__callback_id__), *(
            self._not_contains(getattr(self, field_name), self.__callback_sep__, self.__callback_data_sep__)
            if not issubclass(field_type, (bool, Enum)) else (' ' if getattr(self, field_name) else '')
            if field_type is bool else self._not_contains(
                getattr(self, field_name).value, self.__callback_sep__, self.__callback_data_sep__
            )
            for field_name, field_type in self.__annotations__.items()
        )))

    @classmethod
    def join_to_str(cls, *datas: Any) -> str:
        """Internal function to join multiple callback objects to a callback string."""
        return cls.__callback_sep__.join(
            data.to_str() if isinstance(data, CallbackData)
            else cls._not_contains(data, cls.__callback_data_sep__)
            for data in datas
        )


CallbackDataT = TypeVar('CallbackDataT', bound=CallbackData | Iterable[type[CallbackData]] | str | Callable[[str], Any])


@dataclass(frozen=True, slots=True, kw_only=True)
class CallbackButton(BaseUserUpdate, Generic[CallbackDataT]):
    """
    Represents a callback button.

    Attributes:
        id: The ID of the message.
        metadata: The metadata of the message (to which phone number it was sent).
        type: The message type (always ``interactive``).
        from_user: The user who sent the message.
        timestamp: The timestamp when the message was sent.
        reply_to_message: The message to which this callback button is a reply to.
        data: The data of the button.
        title: The title of the button.
    """
    id: str
    type: MessageType
    metadata: Metadata
    from_user: User
    timestamp: datetime
    reply_to_message: ReplyToMessage
    data: CallbackDataT
    title: str

    @property
    def message_id_to_reply(self) -> str:
        """The ID of the message to reply to."""
        return self.reply_to_message.message_id

    @classmethod
    def from_dict(cls, client: 'WhatsApp', data: dict):
        message = data['messages'][0]
        return cls(
            _client=client,
            id=message['id'],
            metadata=Metadata.from_dict(data['metadata']),
            type=MessageType(message['type']),
            from_user=User.from_dict(data['contacts'][0]),
            timestamp=datetime.fromtimestamp(int(message['timestamp'])),
            reply_to_message=ReplyToMessage.from_dict(message['context']),
            data=message['interactive']['button_reply']['id'],
            title=message['interactive']['button_reply']['title']
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class CallbackSelection(BaseUserUpdate, Generic[CallbackDataT]):
    """
    Represents a callback selection.

    Attributes:
        id: The ID of the message.
        metadata: The metadata of the message (to which phone number it was sent).
        type: The message type (always ``interactive``).
        from_user: The user who sent the message.
        timestamp: The timestamp when the message was sent.
        reply_to_message: The message to which this callback selection is a reply to.
        data: The data of the selection.
        title: The title of the selection.
        description: The description of the selection (optional).
    """
    id: str
    type: MessageType
    metadata: Metadata
    from_user: User
    timestamp: datetime
    reply_to_message: ReplyToMessage
    data: CallbackDataT
    title: str
    description: str | None

    @classmethod
    def from_dict(cls, client: 'WhatsApp', data: dict):
        message = data['messages'][0]
        return cls(
            _client=client,
            id=message['id'],
            metadata=Metadata.from_dict(data['metadata']),
            type=MessageType(message['type']),
            from_user=User.from_dict(data['contacts'][0]),
            timestamp=datetime.fromtimestamp(int(message['timestamp'])),
            reply_to_message=ReplyToMessage.from_dict(message['context']),
            data=message['interactive']['list_reply']['id'],
            title=message['interactive']['list_reply']['title'],
            description=message['interactive']['list_reply'].get('description')
        )


@dataclass(frozen=True, slots=True)
class Button:
    """
    Represents a button in the button list.

    Attributes:
        title: The title of the button (up to 20 characters).
        callback_data: The payload to send when the user clicks on the button (up to 256 characters).
    """
    title: str
    callback_data: CallbackDataT

    def to_dict(self) -> dict:
        return {
            "type": "reply",
            "reply":
                {
                    "id": self.callback_data.to_str()
                    if isinstance(self.callback_data, CallbackData) else self.callback_data
                    if isinstance(self.callback_data, str) else self.callback_data.join_to_str(*self.callback_data),
                    "title": self.title
                }
        }


@dataclass(frozen=True, slots=True)
class SectionRow:
    """
    Represents a row in a section.

    Attributes:
        title: The title of the row (up to 24 characters).
        callback_data: The payload to send when the user clicks on the row (up to 200 characters).
        description: The description of the row (optional, up to 72 characters).
    """
    title: str
    callback_data: CallbackDataT
    description: str | None = None

    def to_dict(self) -> dict:
        d = {
            "id": self.callback_data.to_str() if isinstance(self.callback_data, CallbackData)
            else self.callback_data if isinstance(self.callback_data, str)
            else self.callback_data.join_to_str(*self.callback_data),
            "title": self.title
        }
        if self.description:
            d["description"] = self.description
        return d


@dataclass(frozen=True, slots=True)
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
            "rows": tuple(row.to_dict() for row in self.rows)
        }


@dataclass(frozen=True, slots=True)
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
            "sections": tuple(section.to_dict() for section in self.sections)
        }
