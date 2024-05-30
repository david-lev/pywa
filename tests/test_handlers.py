import dataclasses
import datetime
import enum
import functools
import pytest

from pywa import handlers, types, WhatsApp
from pywa_async import WhatsApp as WhatsAppAsync
from pywa.handlers import Handler

FAKE_WA = WhatsApp(phone_id="1234567890", token="1234567890:1234567890")
FAKE_WA_ASYNC = WhatsAppAsync(phone_id="1234567890", token="1234567890:1234567890")

CallbackButtonOnlyDataIsNeeded = functools.partial(
    types.CallbackButton,
    _client=FAKE_WA,
    raw={},
    id="123",
    type=types.MessageType.INTERACTIVE,
    metadata=types.Metadata(
        display_phone_number="1234567890",
        phone_number_id="1234567890",
    ),
    from_user=types.User(
        wa_id="1234567890",
        name="John",
    ),
    timestamp=datetime.datetime.now(),
    reply_to_message=types.ReplyToMessage(
        message_id="123",
        from_user_id="1234567890",
        referred_product=None,
    ),
    title="Click me",
)


def test_all_updates_are_overridden():
    assert (
        FAKE_WA._handlers_to_update_constractor.keys()
        == FAKE_WA_ASYNC._handlers_to_update_constractor.keys()
    )


def test_safe_issubclas():
    assert not handlers._safe_issubclass("None", str)


@pytest.mark.asyncio
async def test_resolve_factory_iterable_with_callback_data_subclasses():
    @dataclasses.dataclass
    class User(types.CallbackData):
        id: int
        name: str

    @dataclasses.dataclass
    class Post(types.CallbackData):
        id: int
        title: str

    tuple_factory = (User, Post)
    callback_data = (User(id=1, name="John"), Post(id=1, title="Hello"))
    constructor, factory_filter = handlers._resolve_factory(tuple_factory, "data")
    button_data = types.Button(title="Click me", callback_data=callback_data).to_dict()[
        "reply"
    ]["id"]
    constructed_data = await constructor(button_data)
    assert constructed_data == callback_data

    update = CallbackButtonOnlyDataIsNeeded(data=button_data)
    assert factory_filter(FAKE_WA, update)


@pytest.mark.asyncio
async def test_resolve_factory_iterable_with_just_one_callback_data_subclass():
    @dataclasses.dataclass
    class User(types.CallbackData):
        id: int
        name: str

    @dataclasses.dataclass
    class User2:
        id: int
        name: str

        @classmethod
        async def from_split(cls, data: str):
            _id, name = data.split(":")
            return cls(int(_id), name)

        def to_str(self):
            return f"{self.id}:{self.name}"

    callback_data_constructed = [User(id=1, name="John"), User2(1, "Hello")]
    constructor, factory_filter = handlers._resolve_factory(
        [User, User2.from_split], "data"
    )
    button_data = types.Button(
        title="Click me",
        callback_data=[
            callback_data_constructed[0],
            callback_data_constructed[1].to_str(),
        ],
    ).to_dict()["reply"]["id"]
    constructed_data = await constructor(button_data)
    assert constructed_data == callback_data_constructed

    update = CallbackButtonOnlyDataIsNeeded(data=button_data)
    assert factory_filter(FAKE_WA, update)


@pytest.mark.asyncio
async def test_resolve_factory_iterable_without_callback_data_subclasses():
    @dataclasses.dataclass
    class User:
        id: int
        name: str

        @classmethod
        async def from_split(cls, data: str):
            _id, name = data.split(":")
            return cls(int(_id), name)

        def to_str(self):
            return f"{self.id}:{self.name}"

    @dataclasses.dataclass
    class Post:
        id: int
        title: str

        @classmethod
        async def from_split(cls, data: str):
            _id, title = data.split(":")
            return cls(int(_id), title)

        def to_str(self):
            return f"{self.id}:{self.title}"

    callback_data_constructed = [User(1, "John"), Post(1, "Hello")]
    constructor, factory_filter = handlers._resolve_factory(
        [User.from_split, Post.from_split], "data"
    )
    assert factory_filter is None
    button_data = types.Button(
        title="Click me",
        callback_data=f"{callback_data_constructed[0].to_str()}"
        f"{types.CallbackData.__callback_sep__}"
        f"{callback_data_constructed[1].to_str()}",
    ).to_dict()["reply"]["id"]
    constructed_data = await constructor(button_data)
    assert constructed_data == callback_data_constructed


def test_resolve_factory_callback_data_subclass():
    @dataclasses.dataclass
    class User(types.CallbackData):
        id: int
        name: str

    callback_data = User(id=1, name="John")
    constructor, factory_filter = handlers._resolve_factory(User, "data")
    button_data = types.Button(title="Click me", callback_data=callback_data).to_dict()[
        "reply"
    ]["id"]
    constructed_data = constructor(button_data)
    assert constructed_data == callback_data

    update = CallbackButtonOnlyDataIsNeeded(data=button_data)
    assert factory_filter(FAKE_WA, update)


def test_resolve_factory_custom():
    class UserType(str, enum.Enum):
        USER = enum.auto()
        ADMIN = enum.auto()

    constructor, factory_filter = handlers._resolve_factory(UserType, "data")
    assert factory_filter is None
    button_data = types.Button(title="Click me", callback_data=UserType.USER).to_dict()[
        "reply"
    ]["id"]
    constructed_data = constructor(button_data)
    assert constructed_data == UserType.USER

    def to_int(data: str):
        return int(data)

    constructor, factory_filter = handlers._resolve_factory(to_int, "data")
    assert factory_filter is None
    button_data = types.Button(title="Click me", callback_data="123").to_dict()[
        "reply"
    ]["id"]
    constructed_data = constructor(button_data)
    assert constructed_data == 123


@pytest.mark.asyncio
async def test_get_factored_update_factory_before_filters_false():
    @dataclasses.dataclass
    class User(types.CallbackData):
        id: int
        name: str

    pass_filter = lambda _, b: b.data.startswith(str(User.__callback_id__))
    not_pass_filter = lambda _, b: not b.data.startswith(str(User.__callback_id__))

    handler = handlers.CallbackButtonHandler(
        lambda _, __: None,
        pass_filter,
        factory=User,
    )
    assert handler.filters
    assert handler.factory_filter is not None
    assert handler.factory is not None

    update = CallbackButtonOnlyDataIsNeeded(
        data=types.Button(
            title="Click me", callback_data=User(id=1, name="John")
        ).to_dict()["reply"]["id"],
    )

    assert handler.factory_filter(None, update)
    assert handler.filters[0](FAKE_WA, update)

    constructed_update = await handlers._get_factored_update(
        handler=handler,
        wa=FAKE_WA,
        update=update,
        field_name="data",
    )
    assert constructed_update.data == User(id=1, name="John")

    handler.filters = (not_pass_filter,)
    assert not handler.filters[0](None, update)
    assert handler.factory_filter(None, update)
    should_be_none = await handlers._get_factored_update(
        handler=handler,
        wa=FAKE_WA,
        update=update,
        field_name="data",
    )
    assert should_be_none is None


@pytest.mark.asyncio
async def test_get_factored_update_factory_before_filters_true():
    @dataclasses.dataclass
    class User(types.CallbackData):
        id: int
        name: str

    pass_filter = lambda _, b: b.data.id == 1
    not_pass_filter = lambda _, b: b.data.id != 1

    handler = handlers.CallbackButtonHandler(
        lambda _, __: None,
        pass_filter,
        factory=User,
        factory_before_filters=True,
    )
    assert handler.filters
    assert handler.factory_filter is not None
    assert handler.factory is not None

    update = CallbackButtonOnlyDataIsNeeded(
        data=types.Button(
            title="Click me", callback_data=User(id=1, name="John")
        ).to_dict()["reply"]["id"],
    )

    assert handler.factory_filter(None, update)

    constructed_update = await handlers._get_factored_update(
        handler=handler,
        wa=FAKE_WA,
        update=update,
        field_name="data",
    )
    assert constructed_update.data == User(id=1, name="John")
    assert handler.factory_filter(None, update)

    handler.filters = (not_pass_filter,)
    should_be_none = await handlers._get_factored_update(
        handler=handler,
        wa=FAKE_WA,
        update=update,
        field_name="data",
    )
    assert should_be_none is None


@pytest.mark.asyncio
async def test_access_to_attr_from_filter_when_factory_before_filters_false():
    @dataclasses.dataclass
    class User(types.CallbackData):
        id: int
        name: str

    handler = handlers.CallbackButtonHandler(
        lambda _, __: None,
        lambda _, b: b.data.id == 1,
        factory=User,
        factory_before_filters=False,
    )
    update = CallbackButtonOnlyDataIsNeeded(
        data=types.Button(
            title="Click me", callback_data=User(id=1, name="John")
        ).to_dict()["reply"]["id"],
    )

    with pytest.raises(AttributeError):
        await handlers._get_factored_update(
            handler=handler,
            wa=FAKE_WA,
            update=update,
            field_name="data",
        )
