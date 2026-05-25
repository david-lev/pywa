from __future__ import annotations

from typing import TYPE_CHECKING

from pywa.types.account_update import *  # noqa MUST BE IMPORTED FIRST
from pywa.types.account_update import (
    AccountUpdate as _AccountUpdate,  # noqa MUST BE IMPORTED FIRST
)

if TYPE_CHECKING:
    from pywa_async import WhatsApp as WhatsAppAsync


class AccountUpdate(_AccountUpdate):
    _client: WhatsAppAsync

    async def get_waba_account(self) -> WhatsAppBusinessAccount:
        """Get the WhatsApp Business Account associated with this update."""
        return await self._client.get_business_account(waba_id=self.id)
