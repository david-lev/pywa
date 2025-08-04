"""This module contains the callback types."""

__all__ = [
    "CallbackButton",
    "CallbackSelection",
    "Button",
    "URLButton",
    "ButtonUrl",  # Alias for URLButton for backward compatibility
    "VoiceCallButton",
    "CallPermissionRequestButton",
    "SectionRow",
    "Section",
    "SectionList",
    "FlowButton",
    "CallbackData",
]

import dataclasses
import datetime
import enum
import types
import warnings
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Iterable,
    TypeVar,
    cast,
    get_origin,
    Union,
    get_args,
    Literal,
)

from .base_update import BaseUserUpdate  # noqa
from .flows import FlowStatus, FlowActionType
from .others import MessageType, Metadata, ReplyToMessage, InteractiveType
from .. import utils, _helpers as helpers

if TYPE_CHECKING:
    from ..client import WhatsApp
    from .templates import Template


class CallbackData:
    """
    Base class for all callback data classes. Subclass this class to create a type-safe callback data class.

        If you use :func:`dataclasses.dataclass`, which is the recommended way (You get free ordered ``__init__`` and extra features),
        you should not use ``kw_only=True``.
        This is because we are limited to 200 characters in the callback data, so we need to use positional arguments.
        So object like ``User(id=123, name='John')`` will be converted to ``123:John``.

        Currently, the following types are supported:
        :class:`str`, :class:`int`, :class:`bool`, :class:`float` and :class:`enum.Enum` that
        inherits from :class:`str` (e.g ``class State(str, Enum)``). You can also use all the types as Optional or Union
        (e.g ``Optional[int]`` or ``Union[int, None]``). the Union length must be 2 at most, and one of the types must
        be ``None``. All fields can be with default values.

        The characters ``¶`` and ``~`` cannot be used when sending callbacks, because they are used as separators.
        You can change the separators by overriding ``__callback_data_sep__`` (``~`` for individual objects) and
        ``CallbackData.__callback_sep__`` (``¶`` in the base class level, affects all child classes).

        When providing subclassed ``CallbackData`` as a ``factory`` parameter in callback handlers, a basic matching
        filter will be added automatically. So no need to create one yourself.


    Example:

        >>> from pywa.types import CallbackData
        >>> from dataclasses import dataclass # Use dataclass to get free ordered __init__
        >>> @dataclass(frozen=True, slots=True) # Do not use kw_only=True
        >>> class UserData(CallbackData): # Subclass CallbackData
        ...     id: int
        ...     name: str | None
        ...     admin: bool = False

        >>> from pywa import WhatsApp
        >>> from pywa.types import Button
        >>> wa = WhatsApp(...)
        >>> wa.send_message(
        ...     to='972987654321',
        ...     text='Click the button to get the user',
        ...     buttons=[
        ...         Button(
        ...             title='Get user',
        ...             callback_data=UserData(id=123, name='John', admin=True)
        ...         )
        ...     ]
        ... )

        >>> @wa.on_callback_button(factory=UserData) # Use the factory parameter to convert the callback data
        ... def on_user_data(client: WhatsApp, btn: CallbackButton[UserData]): # For autocomplete
        ...    if btn.data.admin: print(btn.data.id) # Access the data object as an attribute
    """

    __callback_id__: int = 0
    """Unique ID for each callback data class. Do not override this."""
    __callback_sep__: str = "¶"
    """The separator between multiple callback objects, Can be overridden globally. (Default ``¶``)"""
    __callback_data_sep__: str = "~"
    """The separator between the callback fields, Can be overridden individually. (Default ``~``)"""
    __callback_bool_true__: str = "§"
    """The string to represent ``True`` in the callback data. (Default ``§``)"""
    __callback_null__: str = "¤"
    """The string to represent ``None`` in the callback data. (Default ``¤``)"""
    __allowed_types__: tuple[type, ...] = (
        str,
        int,
        bool,
        float,
    )
    """The allowed types in the callback data."""

    def __init_subclass__(cls, *args, **kwargs):
        """Validate the callback data class and set a unique ID for it."""
        super().__init_subclass__(*args, **kwargs)
        if (
            len(
                set(
                    (
                        seps := {
                            "Callback Separator": cls.__callback_sep__,
                            "Data Separator": cls.__callback_data_sep__,
                            "Boolean True": cls.__callback_bool_true__,
                            "None Value": cls.__callback_null__,
                        }
                    ).values()
                )
            )
            != 4
        ):
            raise ValueError(
                f"Non-unique separators in callback data class `{cls.__name__}`: {seps}"
            )
        if not cls.__annotations__.items():
            raise TypeError(
                f"Callback data class `{cls.__name__}` must have at least one field."
            )
        if dataclasses.is_dataclass(cls) and getattr(
            getattr(cls, "__dataclass_params__", None), "kw_only", False
        ):
            raise TypeError(
                f"Callback data class `{cls.__name__}` cannot be a dataclass with `kw_only=True`. "
                "Use positional arguments instead."
            )
        unsupported_fields = set[tuple[str, type]]()
        for field_name, field_type in cls.__annotations__.items():
            if get_origin(field_type) in (types.UnionType, Union):
                if len(union_args := get_args(field_type)) > 2:
                    raise TypeError(
                        f"Field {field_name} in `{cls.__name__}` must be a Union of 2 types at most."
                    )
                if types.NoneType not in union_args:
                    raise TypeError(
                        f"Field `{field_name}` in `{cls.__name__}` must be an Optional[x] or Union[x, None]. "
                        f"(e.g. int | None)"
                    )
                field_type = next((a for a in union_args if a is not types.NoneType))
            if issubclass(field_type, enum.Enum) and not issubclass(field_type, str):
                raise TypeError(
                    f"Field `{field_name}` in `{cls.__name__}` must be an Enum that inherits from str."
                )
            if not issubclass(cast(type, field_type), cls.__allowed_types__):
                unsupported_fields.add((field_name, cast(type, field_type)))
        if unsupported_fields:
            raise TypeError(
                f"Unsupported types {unsupported_fields} in callback data. Use one of {cls.__allowed_types__}."
            )

        if cls.__callback_id__ == CallbackData.__callback_id__:
            cls.__callback_id__ = CallbackData.__callback_id__
            CallbackData.__callback_id__ += 1

    @classmethod
    def from_str(
        cls,
        data: str,
    ) -> "CallbackData":
        """
        Internal function to convert a callback string to a callback object.
        """
        try:
            positional_args = []
            for annotation, value in zip(
                cls.__annotations__.values(),
                data.split(cls.__callback_data_sep__)[1:],
                strict=True,
            ):
                if get_origin(annotation) in (types.UnionType, Union):
                    if value == cls.__callback_null__:
                        positional_args.append(None)
                        continue
                    annotation = next(
                        a for a in get_args(annotation) if a is not types.NoneType
                    )
                if isinstance(annotation, bool):
                    if value == cls.__callback_bool_true__:
                        positional_args.append(True)
                        continue
                    elif value == "":
                        positional_args.append(False)
                        continue
                    raise ValueError
                positional_args.append(annotation(value))

            # noinspection PyArgumentList
            return cls(*positional_args)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid callback data for {cls.__name__}: {data}") from e

    @staticmethod
    def _not_contains(value: Any, *not_) -> str:
        """Internal function to validate that the value does not contain the separator."""
        if any(sep in (str_val := str(value)) for sep in not_):
            raise ValueError(
                f"Callback data cannot contain the characters {not_} "
                f"Because they are used as separators. \nYou can change the separators by overriding "
                f"``__callback_data_sep__`` (for individual objects) and ``CallbackData.__callback_sep__`` "
                f"(In the base class level, affects all child classes)."
            )
        return str_val

    def to_str(self) -> str:
        """
        Internal function to convert a callback object to a callback string.
        """
        values = [
            str(self.__callback_id__),
        ]
        for field_name, field_type in self.__annotations__.items():
            value = getattr(self, field_name)
            if value is None:
                value = self.__callback_null__
            if isinstance(value, bool):
                value = self.__callback_bool_true__ if value else ""
            if isinstance(value, enum.Enum):
                value = value.value
            values.append(self._not_contains(value, self.__callback_sep__))
        return self.__callback_data_sep__.join(values)


_CallbackDataT = TypeVar(
    "_CallbackDataT",
    bound=CallbackData | str,
)


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class CallbackButton(BaseUserUpdate, Generic[_CallbackDataT]):
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


    Attributes:
        id: The ID of the message.
        metadata: The metadata of the message (to which phone number it was sent).
        type: The message type (:class:`MessageType.INTERACTIVE` for :class:`~pywa.types.callback.Button` presses or :class:`MessageType.BUTTON` for :class:`~pywa.types.templates.QuickReplyButton` clicks).
        from_user: The user who sent the message.
        timestamp: The timestamp when the message was sent (in UTC).
        reply_to_message: The message to which this callback button is a reply to.
        data: The data of the button (the ``callback_data`` parameter you provided in :class:`Button` or
         :class:`Template.QuickReplyButtonData`).
        title: The title of the button.
        shared_data: Shared data between handlers.
    """

    type: MessageType
    reply_to_message: ReplyToMessage
    data: _CallbackDataT
    title: str

    _txt_fields = ("data",)
    _webhook_field = "messages"

    @classmethod
    def from_update(cls, client: "WhatsApp", update: dict) -> "CallbackButton":
        msg = (value := (entry := update["entry"][0])["changes"][0]["value"])[
            "messages"
        ][0]
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
            waba_id=entry["id"],
            id=msg["id"],
            metadata=Metadata.from_dict(value["metadata"]),
            type=MessageType(msg_type),
            from_user=client._usr_cls.from_dict(value["contacts"][0], client=client),
            timestamp=datetime.datetime.fromtimestamp(
                int(msg["timestamp"]),
                datetime.timezone.utc,
            ),
            reply_to_message=ReplyToMessage.from_dict(msg["context"]),
            data=data,
            title=title,
        )

    @property
    def is_quick_reply(self) -> bool:
        """
        Check if the callback button is click at :class:`~pywa.types.templates.QuickReplyButton` (template button).

        Returns:
            bool: True if the callback button is a quick reply button, False otherwise.
        """
        return self.type == MessageType.BUTTON


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class CallbackSelection(BaseUserUpdate, Generic[_CallbackDataT]):
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

    Attributes:
        id: The ID of the message.
        metadata: The metadata of the message (to which phone number it was sent).
        type: The message type (always :class:`MessageType.INTERACTIVE`).
        from_user: The user who sent the message.
        timestamp: The timestamp when the message was sent (in UTC).
        reply_to_message: The message to which this callback selection is a reply to.
        data: The data of the selection (the ``callback_data`` parameter you provided in :class:`SectionRow`).
        title: The title of the selection.
        description: The description of the selection (optional).
    """

    type: MessageType
    reply_to_message: ReplyToMessage
    data: _CallbackDataT
    title: str
    description: str | None

    _txt_fields = ("data",)
    _webhook_field = "messages"

    @classmethod
    def from_update(cls, client: "WhatsApp", update: dict) -> "CallbackSelection":
        msg = (value := (entry := update["entry"][0])["changes"][0]["value"])[
            "messages"
        ][0]
        return cls(
            _client=client,
            raw=update,
            waba_id=entry["id"],
            id=msg["id"],
            metadata=Metadata.from_dict(value["metadata"]),
            type=MessageType(msg["type"]),
            from_user=client._usr_cls.from_dict(value["contacts"][0], client=client),
            timestamp=datetime.datetime.fromtimestamp(
                int(msg["timestamp"]),
                datetime.timezone.utc,
            ),
            reply_to_message=ReplyToMessage.from_dict(msg["context"]),
            data=msg["interactive"]["list_reply"]["id"],
            title=msg["interactive"]["list_reply"]["title"],
            description=msg["interactive"]["list_reply"].get("description"),
        )


@dataclasses.dataclass(slots=True)
class Button:
    """
    Interactive reply buttons messages allow you to send up to three predefined replies for users to choose from.
    Users can respond to a message by selecting one of the predefined buttons, which triggers an :class:`CallbackButton` update.

    Attributes:
        title: The title of the button (up to 20 characters).
        callback_data: The data to send when the user clicks on the button (up to 256 characters, for complex data
         You can use :class:`CallbackData`).
    """

    title: str
    callback_data: str | CallbackData

    def to_dict(self) -> dict:
        return {
            "type": "reply",
            "reply": {
                "id": helpers.resolve_callback_data(self.callback_data),
                "title": self.title,
            },
        }


@dataclasses.dataclass(slots=True)
class URLButton:
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
class ButtonUrl(URLButton):
    """Deprecated. Use :class:`URLButton` instead."""

    def __post_init__(self):
        warnings.warn(
            "ButtonUrl is deprecated, use `URLButton` instead.",
            DeprecationWarning,
            stacklevel=2,
        )


@dataclasses.dataclass(slots=True)
class VoiceCallButton:
    """
    Represents a button that initiates a voice call on WhatsApp.

    Attributes:
        title: The text to display on the button (up to 20 characters) default is `Call Now`.
        ttl_minutes: The time-to-live for the call in minutes (up to ``43200`` minutes (30 days)), default is ``10080``  minutes (7 days).
    """

    title: str | None = None
    ttl_minutes: int | None = None

    def to_dict(self) -> dict:
        params = {}
        if self.title:
            params["display_text"] = self.title
        if self.ttl_minutes:
            params["ttl_minutes"] = self.ttl_minutes

        return {
            "name": InteractiveType.VOICE_CALL,
            "parameters": params,
        }


@dataclasses.dataclass(slots=True)
class CallPermissionRequestButton:
    """Represents a button that requests a call on WhatsApp."""

    @staticmethod
    def to_dict() -> dict:
        return {
            "name": InteractiveType.CALL_PERMISSION_REQUEST,
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
    callback_data: str | CallbackData
    description: str | None = None

    def to_dict(self) -> dict:
        d = {
            "id": helpers.resolve_callback_data(self.callback_data),
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
    Interactive list messages allow you to present WhatsApp users with a list of options to choose from.
    When a user taps the button in the message, it displays a modal that lists the options available.

    - Users can then choose one option and their selection will be sent as a reply. When a user selects an option, a :class:`CallbackSelection` update is triggered.
    - Interactive list messages support up to 10 sections, with up to 10 rows for all sections combined, and can include an optional header and footer.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/messages/interactive-list-messages>`_.

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
        flow_id: Unique ID of the Flow provided by WhatsApp (You can provide either ``flow_id`` or ``flow_name``).
        flow_name: Name of the Flow provided by WhatsApp (You can provide either ``flow_id`` or ``flow_name``).
        flow_token: Flow token generated by the business to serve as an identifier (Default value: ``unused``)
        flow_message_version: Version of the flow message. Default is the latest version.
        flow_action_type: Type of action to be performed when the user clicks on the button.
        flow_action_screen: The ID of the screen to navigate to. Required when ``flow_action_type`` is ``FlowActionType.NAVIGATE`` (default).
        flow_action_payload: The data to provide to the navigation screen, if the screen requires it.
        mode: The mode of the flow. ``FlowStatus.PUBLISHED`` (default) or ``FlowStatus.DRAFT`` (for testing).
    """

    title: str
    flow_id: str | int | None = None
    flow_token: str | None = None
    flow_action_type: (
        Literal[FlowActionType.NAVIGATE, FlowActionType.DATA_EXCHANGE] | None
    ) = None
    flow_action_screen: str | None = None
    flow_action_payload: dict[str, Any] | None = None
    flow_message_version: int | float | str | Literal[utils.Version.FLOW_MSG] = (
        utils.Version.FLOW_MSG
    )
    mode: Literal[FlowStatus.PUBLISHED, FlowStatus.DRAFT] = FlowStatus.PUBLISHED
    flow_name: str | None = None

    def __post_init__(self):
        utils.Version.FLOW_MSG.validate_min_version(str(self.flow_message_version))
        if (
            self.flow_action_type == FlowActionType.NAVIGATE
            and self.flow_action_screen is None
        ):
            raise ValueError(
                "flow_action_screen cannot be None when flow_action_type is FlowActionType.NAVIGATE"
            )
        if (not self.flow_id and not self.flow_name) or (
            self.flow_id and self.flow_name
        ):
            raise ValueError(
                "Either flow_id or flow_name must be provided, but not both."
            )

    def to_dict(self) -> dict:
        return {
            "name": InteractiveType.FLOW,
            "parameters": {
                "mode": self.mode.lower(),
                "flow_message_version": str(self.flow_message_version),
                "flow_token": self.flow_token,
                "flow_id" if self.flow_id else "flow_name": self.flow_id
                or self.flow_name,
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
