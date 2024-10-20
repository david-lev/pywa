from pywa.types.sent_message import *  # noqa MUST BE IMPORTED FIRST
from pywa.types.sent_message import SentMessage as _SentMessage

__all__ = ["SentMessage"]

from pywa_async.types.base_update import _ClientShortcuts


class SentMessage(_ClientShortcuts, _SentMessage):
    pass
