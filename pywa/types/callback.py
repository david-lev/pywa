__all__ = [
    'CallbackButton',
    'CallbackSelection',
    'Button',
    'SectionRow',
    'Section',
    'SectionList',
    'CallbackData',
    'CallbackDataT',
    'CALLBACK_SEP',
]

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Iterable, TypeVar, Generic, Callable, Any
from .base_update import BaseUpdate
from .others import Metadata, User, ReplyToMessage, MessageType

if TYPE_CHECKING:
    from pywa.client import WhatsApp

ALLOWED_TYPES = (str, int, bool, float, datetime)
CALLBACK_SEP = ','
CALLBACK_DATA_SEP = ':'


class CallbackData:
    """
    Base class for all callback data classes. Subclass this class to create a type-safe callback data class.

        If you use dataclasses, which is the recommended way, you should not use ``kw_only=True``.
        This is because we are limited to 200 characters in the callback data, so we need to use positional arguments.

        Also, use only primitive types (str, int, bool, etc.) in the dataclass, because we need to convert the data to
        a string.

    Example:

        >>> from pywa import WhatsApp
        >>> from pywa.types import CallbackData, Button
        >>> from dataclasses import dataclass # Use dataclass to get free __init__
        >>> @dataclass(frozen=True) # Do not use kw_only=True
        >>> class User(CallbackData): # Subclass CallbackData
        ...     id: int
        ...     name: str
        >>> user = User(id=123, name='John')
        >>> wa = WhatsApp(...)
        >>> wa.send_message(
        ...     to='972987654321',
        ...     text='Click the button to get the user',
        ...     buttons=[Button(title='Get user', callback_data=user)]
        ... )

        >>> @wa.on_callback_button(factory=User) # Register a handler for the callback data
        ... def on_video(client: WhatsApp, btn: CallbackButton[User]): # For autocomplete
        ...     print(btn.data.name) # Access the data object as an attribute
    """

    __callback_id__: int = 0

    def __init_subclass__(cls, **kwargs):
        """Generate a unique ID for each subclass."""
        super().__init_subclass__(**kwargs)
        cls.__unique_id__ = CallbackData.__callback_id__
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
                    data.split(CALLBACK_DATA_SEP)[1:],
                    strict=True
                )
            ))
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid callback data for {cls.__name__}: {data}") from e

    def to_str(self) -> str:
        """
        Internal function to convert a callback object to a callback string.
        """
        values = []
        for annotation, value in zip(self.__annotations__.values(), self.__dict__.values()):
            if annotation not in ALLOWED_TYPES:
                raise TypeError(f"Unsupported type {annotation} for callback data. Use one of {ALLOWED_TYPES}.")
            if issubclass(annotation, bool):
                value = '1' if value else ''  # convert bool to 1 or empty string
            values.append(str(value))
        return CALLBACK_DATA_SEP.join((str(self.__unique_id__), *values))

    @staticmethod
    def join_to_str(*datas: Iterable['CallbackData']) -> str:
        """Internal function to join multiple callback objects to a callback string."""
        return CALLBACK_SEP.join(data.to_str() for data in datas)


CallbackDataT = TypeVar('CallbackDataT', bound=CallbackData | Iterable[CallbackData] | Callable[[str], Any])


@dataclass(frozen=True, slots=True, kw_only=True)
class CallbackButton(BaseUpdate, Generic[CallbackDataT]):
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
    def from_dict(cls, client: WhatsApp, data: dict):
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
class CallbackSelection(BaseUpdate, Generic[CallbackDataT]):
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
    def from_dict(cls, client: WhatsApp, data: dict):
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
        return {"type": "reply", "reply": {"id": self.callback_data, "title": self.title}}  #  TODO: convert callback_data to str


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
        d = {"id": self.callback_data, "title": self.title}  # TODO: convert callback_data to str
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
