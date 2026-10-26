"""
Static typing checks for filter combinations, verified by ``ty check`` (never run by pytest).

``assert_type`` pins the inferred type of each combination, and the ``ty: ignore`` comment
pins an expected error (``ty`` reports an unused ignore if the error ever disappears).
"""

from typing import TYPE_CHECKING

from pywa import filters, types
from pywa.filters import Filter

if TYPE_CHECKING:
    from typing_extensions import assert_type


def takes_message_filter(_: Filter[types.Message]) -> None: ...


if TYPE_CHECKING:
    # same update type
    assert_type(filters.text & filters.reply, Filter[types.Message])
    assert_type(filters.text | filters.reply, Filter[types.Message])
    assert_type(~filters.text, Filter[types.Message])

    # a filter for a base update type narrows to the more specific one, in both orders
    assert_type(filters.sent_to_me & filters.text, Filter[types.Message])
    assert_type(filters.text & filters.sent_to_me, Filter[types.Message])
    assert_type(filters.sent_to_me | filters.text, Filter[types.Message])
    assert_type(filters.text | filters.sent_to_me, Filter[types.Message])

    # valid combinations are accepted where a ``Filter[Message]`` is expected
    takes_message_filter(filters.text & filters.reply)
    takes_message_filter(filters.sent_to_me & filters.text)

    # filters that accept any update (``Filter[Any]``) are still accepted
    takes_message_filter(filters.text & filters.true)
    takes_message_filter(filters.true & filters.text)

    # combining filters of unrelated update types can never match, so it is rejected once used
    takes_message_filter(filters.text & filters.callback_button)  # ty: ignore[invalid-argument-type]
    takes_message_filter(filters.text | filters.callback_button)  # ty: ignore[invalid-argument-type]
