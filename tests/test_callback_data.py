import dataclasses
from pywa.types import CallbackData


def test_data_sep():
    """Test the data separator."""
    @dataclasses.dataclass(slots=True, frozen=True)
    class User(CallbackData):
        __callback_data_sep__ = '#'
        id: str
        name: str
        is_admin: bool
    assert User(id='1234', name='xxx', is_admin=True).to_str() == '1#1234#xxx# '
    assert User(id='3456', name='yyy', is_admin=False).to_str() == '1#3456#yyy#'
    assert User.from_str('1#1234#xxx# ') == User(id='1234', name='xxx', is_admin=True)
    assert User.from_str('1#3456#yyy#') == User(id='3456', name='yyy', is_admin=False)


def test_callback_sep():
    """Test the callbacks separator."""
    CallbackData.__callback_sep__ = '!'

    @dataclasses.dataclass(slots=True, frozen=True)
    class User(CallbackData):
        id: str
        name: str
        is_admin: bool

    @dataclasses.dataclass(slots=True, frozen=True)
    class Group(CallbackData):
        id: str
        name: str

    user = User(id='1234', name='xxx', is_admin=True)
    group = Group(id='3456', name='yyy')
    assert CallbackData.join_to_str(user, group) == '3:1234:xxx: !5:3456:yyy'
    assert CallbackData.join_to_str(user, group, user) == '3:1234:xxx: !5:3456:yyy!3:1234:xxx: '
    x, y = '3:1234:xxx: !5:3456:yyy'.split(CallbackData.__callback_sep__)
    assert (User.from_str(x), Group.from_str(y)) == (user, group)
    x, y, z = '3:1234:xxx: !5:3456:yyy!3:1234:xxx: '.split(CallbackData.__callback_sep__)
    assert (User.from_str(x), Group.from_str(y), User.from_str(z)) == (user, group, user)

