import dataclasses

import pytest

from pywa.types import CallbackData


def test_callback_class_uniqueness():
    """Test the uniqueness of the callback data."""

    @dataclasses.dataclass(slots=True, frozen=True)
    class User(CallbackData):
        id: str
        name: str
        is_admin: bool

    @dataclasses.dataclass(slots=True, frozen=True)
    class Group(CallbackData):
        id: str
        name: str

    assert (
        User.__callback_id__ != Group.__callback_id__
    ), "The callback id must be unique for each child class."


def test_callback_class_not_empty():
    """Test if the callback data is empty."""
    with pytest.raises(TypeError):

        @dataclasses.dataclass(slots=True, frozen=True)
        class User1(CallbackData):
            pass

    with pytest.raises(TypeError):

        @dataclasses.dataclass(slots=True, frozen=True)
        class User2(CallbackData):
            id: str
            name: str
            is_admin: bool
            x: int

        @dataclasses.dataclass(slots=True, frozen=True)
        class UserChild(User2):
            pass


def test_callback_supported_types():
    """Test the supported types of the callback data."""
    with pytest.raises(TypeError):

        @dataclasses.dataclass(slots=True, frozen=True)
        class User(CallbackData):
            id: int
            name: str
            is_admin: bool
            x: dict
            y: list
            z: set


def test_data():
    """Test the callback data."""

    @dataclasses.dataclass(slots=True, frozen=True)
    class User(CallbackData):
        id: int
        name: str
        is_admin: bool

    assert User(id=1234, name="xxx", is_admin=True).to_str() == "7~1234~xxx~§"
    assert User(id=3456, name="yyy", is_admin=False).to_str() == "7~3456~yyy~"
    assert User.from_str("1~1234~xxx~§") == User(id=1234, name="xxx", is_admin=True)
    assert User.from_str("1~3456~yyy~") == User(id=3456, name="yyy", is_admin=False)

    with pytest.raises(ValueError):  # too few fields
        User.from_str("1~3456")

    with pytest.raises(ValueError):  # too many fields
        User.from_str("1~3456~yyy~§~")

    with pytest.raises(ValueError):  # invalid type
        User.from_str("1~x~yyy~§")


def test_multiple_data():
    """Test multiple callback data."""

    @dataclasses.dataclass(slots=True, frozen=True)
    class User(CallbackData):
        id: str
        name: str
        is_admin: bool

    @dataclasses.dataclass(slots=True, frozen=True)
    class Group(CallbackData):
        id: str
        name: str

    user = User(id="1234", name="xxx", is_admin=True)
    group = Group(id="3456", name="yyy")
    assert CallbackData.join_to_str(user, group) == "9~1234~xxx~§¶11~3456~yyy"
    assert (
        CallbackData.join_to_str(user, group, user)
        == "9~1234~xxx~§¶11~3456~yyy¶9~1234~xxx~§"
    )
    x, y = "3~1234~xxx~§¶5~3456~yyy".split(CallbackData.__callback_sep__)
    assert (User.from_str(x), Group.from_str(y)) == (user, group)
    x, y, z = "3~1234~xxx~§¶5~3456~yyy¶3~1234~xxx~§".split(
        CallbackData.__callback_sep__
    )
    assert (User.from_str(x), Group.from_str(y), User.from_str(z)) == (
        user,
        group,
        user,
    )


def test_data_sep():
    """Test the data separator override."""

    @dataclasses.dataclass(slots=True, frozen=True)
    class User(CallbackData):
        __callback_data_sep__ = "*"
        id: int
        name: str
        is_admin: bool

    assert User(id=1234, name="xxx", is_admin=True).to_str() == "13*1234*xxx*§"
    assert User(id=3456, name="yyy", is_admin=False).to_str() == "13*3456*yyy*"

    with pytest.raises(ValueError):
        User.from_str("1*3456*David*Lev*")

    try:
        User.from_str("1*3456*David~Lev*")
    except ValueError:
        pytest.fail("The data separator override does not work.")


def test_data_sep_multiple_data():
    """Test the data separator override with multiple data."""
    CallbackData.__callback_sep__ = "^"

    @dataclasses.dataclass(slots=True, frozen=True)
    class User(CallbackData):
        id: int
        name: str
        is_admin: bool

    @dataclasses.dataclass(slots=True, frozen=True)
    class Group(CallbackData):
        id: int
        name: str

    user = User(id=1234, name="xxx", is_admin=True)
    group = Group(id=3456, name="yyy")
    assert CallbackData.join_to_str(user, group) == "15~1234~xxx~§^17~3456~yyy"
    assert (
        CallbackData.join_to_str(user, group, user)
        == "15~1234~xxx~§^17~3456~yyy^15~1234~xxx~§"
    )
    x, y = "3~1234~xxx~§^5~3456~yyy".split(CallbackData.__callback_sep__)
    assert (User.from_str(x), Group.from_str(y)) == (user, group)
    x, y, z = "3~1234~xxx~§^5~3456~yyy^3~1234~xxx~§".split(
        CallbackData.__callback_sep__
    )
    assert (User.from_str(x), Group.from_str(y), User.from_str(z)) == (
        user,
        group,
        user,
    )
