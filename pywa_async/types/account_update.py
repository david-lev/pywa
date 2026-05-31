from __future__ import annotations

from typing import TYPE_CHECKING

from pywa.types.account_update import *  # noqa MUST BE IMPORTED FIRST
from pywa.types.account_update import (
    AccountUpdate as _AccountUpdate,  # noqa MUST BE IMPORTED FIRST
)

if TYPE_CHECKING:
    from pywa_async import WhatsApp as WhatsAppAsync


class AccountUpdate(_AccountUpdate):
    """
    The account_update webhook notifies of changes to a WhatsApp Business Account’s partner-led business verification submission, its authentication-international rate eligibility, or primary business location, when it is shared with a Solution Partner, policy or terms violations, offboarding, reconnection, or when it is deleted.

    Attributes:
        id: Business Portfolio ID.
        timestamp: Timestamp of the update (in UTC).
        event: WhatsApp Business Account (“WABA”) event.
        waba_info: The WABA information for ``AD_ACCOUNT_LINKED``, ``PARTNER_*`` events, and ``MM_LITE_TERMS_SIGNED`` event.
        violation_info: Violation information for WABA ban state. Only included for ``ACCOUNT_VIOLATION`` event.
        ban_info: Ban information for WABA ban state. Only included for ``DISABLED_UPDATE`` event.
        restriction_info: Restriction info for WABA ban state. Only included for ``ACCOUNT_RESTRICTION`` event.
        disconnection_info: Disconnection info for WABA ban state. Only included for ``PARTNER_REMOVED`` events where the business was using both the WhatsApp Business app and Cloud API.
        auth_international_rate_eligibility: Authentication-international rate eligibility info. Only included for ``AUTH_INTL_PRICE_ELIGIBILITY_UPDATE`` event.
        volume_tier_info: Volume tier info. Only included for ``VOLUME_BASED_PRICING_TIER_UPDATE`` event.
        shared_data: Shared data between handlers.
    """

    _client: WhatsAppAsync

    async def get_waba_account(self) -> WhatsAppBusinessAccount:
        """Get the WhatsApp Business Account associated with this update."""
        return await self._client.get_business_account(waba_id=self.id)
