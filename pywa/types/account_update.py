from __future__ import annotations

import dataclasses
import datetime
from typing import TYPE_CHECKING

from .. import _helpers as helpers
from . import RawUpdate
from .base_update import BaseUpdate
from .message_status import PricingCategory

if TYPE_CHECKING:
    from .. import WhatsApp


class AccountUpdateEvent(helpers.StrEnum):
    """
    WhatsApp Business Account (“WABA”) event.

    Attributes:
        ACCOUNT_DELETED: Indicates WABA was deleted.
        ACCOUNT_RESTRICTION: Indicates WABA has been restricted due to `policy violations <https://developers.facebook.com/documentation/business-messaging/whatsapp/policy-enforcement>`_. See ``restriction_info`` for restriction details.
        ACCOUNT_VIOLATION: Indicates WABA violated Meta `policies or terms <https://developers.facebook.com/documentation/business-messaging/whatsapp/policy-enforcement>`_.
        AD_ACCOUNT_LINKED: Indicates WABA has been onboarded onto Marketing Messages API for WhatsApp through Embedded Signup or Intent API and gives the partner access to its ad accounts.
        AUTH_INTL_PRICE_ELIGIBILITY_UPDATE: Indicates WABA is eligible for `authentication-international rates <https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing/authentication-international-rates>`_.
        BUSINESS_PRIMARY_LOCATION_COUNTRY_UPDATE: Indicates WABA’s `primary business location <https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing/authentication-international-rates#primary-business-location>`_ has been set.
        DISABLED_UPDATE: Indicates WABA violated Meta `policies or terms <https://developers.facebook.com/documentation/business-messaging/whatsapp/policy-enforcement>`_.
        MM_LITE_TERMS_SIGNED: Indicates that the WABA has successfully accepted the MM API for WhatsApp terms of service.
        PARTNER_ADDED: Indicates WABA has been shared with a `Solution Partner <https://developers.facebook.com/documentation/business-messaging/whatsapp/solution-providers/overview>`_.
        PARTNER_APP_INSTALLED: Indicates a business customer granted the app one or more permissions.
        PARTNER_APP_UNINSTALLED: Indicates a business customer deauthenticated or uninstalled the app.
        PARTNER_CLIENT_CERTIFICATION_STATUS_UPDATE: Indicates the WABA’s `partner-led business verification <https://developers.facebook.com/documentation/business-messaging/whatsapp/solution-providers/partner-led-business-verification>`_ submission is approved, rejected, or discarded.
        PARTNER_REMOVED: Indicates WABA has been unshared with a `Solution Partner <https://developers.facebook.com/documentation/business-messaging/whatsapp/solution-providers/overview>`_.
        VOLUME_BASED_PRICING_TIER_UPDATE: Indicates WABA’s volume-based pricing tier has been updated.
        ACCOUNT_OFFBOARDED: Indicates WABA has been offboarded due to a device change or phone number reregistration.
        ACCOUNT_RECONNECTED: Indicates WABA has been reconnected after a device change or phone number reregistration.
    """

    ACCOUNT_DELETED = "ACCOUNT_DELETED"
    ACCOUNT_RESTRICTION = "ACCOUNT_RESTRICTION"
    ACCOUNT_VIOLATION = "ACCOUNT_VIOLATION"
    AD_ACCOUNT_LINKED = "AD_ACCOUNT_LINKED"
    AUTH_INTL_PRICE_ELIGIBILITY_UPDATE = "AUTH_INTL_PRICE_ELIGIBILITY_UPDATE"
    BUSINESS_PRIMARY_LOCATION_COUNTRY_UPDATE = (
        "BUSINESS_PRIMARY_LOCATION_COUNTRY_UPDATE"
    )
    DISABLED_UPDATE = "DISABLED_UPDATE"
    MM_LITE_TERMS_SIGNED = "MM_LITE_TERMS_SIGNED"
    PARTNER_ADDED = "PARTNER_ADDED"
    PARTNER_APP_INSTALLED = "PARTNER_APP_INSTALLED"
    PARTNER_APP_UNINSTALLED = "PARTNER_APP_UNINSTALLED"
    PARTNER_CLIENT_CERTIFICATION_STATUS_UPDATE = (
        "PARTNER_CLIENT_CERTIFICATION_STATUS_UPDATE"
    )
    PARTNER_REMOVED = "PARTNER_REMOVED"
    VOLUME_BASED_PRICING_TIER_UPDATE = "VOLUME_BASED_PRICING_TIER_UPDATE"
    ACCOUNT_OFFBOARDED = "ACCOUNT_OFFBOARDED"
    ACCOUNT_RECONNECTED = "ACCOUNT_RECONNECTED"

    UNKNOWN = "UNKNOWN"


class DisconnectionInitiatedBy(helpers.StrEnum):
    """
    Indicates whether the disconnection was initiated by your client or the system.

    Attributes:
        SYSTEM: The disconnection was system-initiated (for example, due to device inactivity or `enforcement <https://developers.facebook.com/documentation/business-messaging/whatsapp/policy-enforcement>`_).
        USER: The disconnection was client-initiated (for example, your client changed their phone number, re-registered on a new device, deleted their WhatsApp account, or registered their business phone number with the consumer WhatsApp app).
    """

    SYSTEM = "SYSTEM"
    USER = "USER"

    UNKNOWN = "UNKNOWN"


class DisconnectionReason(helpers.StrEnum):
    """
    Reason for the disconnection.

    Attributes:
        ACCOUNT_DISCONNECTED: Your client’s account was disconnected due to `enforcement <https://developers.facebook.com/documentation/business-messaging/whatsapp/policy-enforcement>`_ or because your client explicitly deleted their WhatsApp account. Can be initiated by either ``USER`` or ``SYSTEM``.
        BUSINESS_DOWNGRADE: Your client registered their business phone number with the consumer WhatsApp app.
        CHANGE_NUMBER: Your client changed their phone number.
        COMPANION_INACTIVITY: A companion device was inactive for approximately 30 days.
        PRIMARY_INACTIVITY: The primary device was inactive for approximately 14 days.
        USER_RE_REGISTERED: Your client re-registered on a new device.
    """

    ACCOUNT_DISCONNECTED = "ACCOUNT_DISCONNECTED"
    BUSINESS_DOWNGRADE = "BUSINESS_DOWNGRADE"
    CHANGE_NUMBER = "CHANGE_NUMBER"
    COMPANION_INACTIVITY = "COMPANION_INACTIVITY"
    PRIMARY_INACTIVITY = "PRIMARY_INACTIVITY"
    USER_RE_REGISTERED = "USER_RE_REGISTERED"

    UNKNOWN = "UNKNOWN"


class RestrictionType(helpers.StrEnum):
    """
    Type of restriction applied to the account.

    Attributes:
        RESTRICTED_ADD_PHONE_NUMBER_ACTION: Business cannot add new phone numbers to the account.
        RESTRICTED_BIZ_INITIATED_AND_USER_INITIATED_CALLING: Business cannot make or receive calls.
        RESTRICTED_BIZ_INITIATED_MESSAGING: Business cannot initiate conversations with customers.
        RESTRICTED_BUSINESS_INITIATED_CALLING: Business cannot initiate outbound calls.
        RESTRICTED_CUSTOMER_INITIATED_MESSAGING: Business cannot respond to customer-initiated messages.
        RESTRICTED_DIRECT_SEND_UTILITY_TEMPLATES: Business cannot send utility templates via Direct Send.
        RESTRICTED_USER_INITIATED_CALLING: Business cannot receive inbound calls from users.
        RESTRICTED_USER_INITIATED_CALLING_CALL_BUTTON_HIDDEN: Call button is hidden from users due to low pickup rates.
        RESTRICTED_UTILITY_TEMPLATES: Business cannot create utility templates.
    """

    RESTRICTED_ADD_PHONE_NUMBER_ACTION = "RESTRICTED_ADD_PHONE_NUMBER_ACTION"
    RESTRICTED_BIZ_INITIATED_AND_USER_INITIATED_CALLING = (
        "RESTRICTED_BIZ_INITIATED_AND_USER_INITIATED_CALLING"
    )
    RESTRICTED_BIZ_INITIATED_MESSAGING = "RESTRICTED_BIZ_INITIATED_MESSAGING"
    RESTRICTED_BUSINESS_INITIATED_CALLING = "RESTRICTED_BUSINESS_INITIATED_CALLING"
    RESTRICTED_CUSTOMER_INITIATED_MESSAGING = "RESTRICTED_CUSTOMER_INITIATED_MESSAGING"
    RESTRICTED_DIRECT_SEND_UTILITY_TEMPLATES = (
        "RESTRICTED_DIRECT_SEND_UTILITY_TEMPLATES"
    )
    RESTRICTED_USER_INITIATED_CALLING = "RESTRICTED_USER_INITIATED_CALLING"
    RESTRICTED_USER_INITIATED_CALLING_CALL_BUTTON_HIDDEN = (
        "RESTRICTED_USER_INITIATED_CALLING_CALL_BUTTON_HIDDEN"
    )
    RESTRICTED_UTILITY_TEMPLATES = "RESTRICTED_UTILITY_TEMPLATES"

    UNKNOWN = "UNKNOWN"


class WABABanState(helpers.StrEnum):
    """
    WABA ban state.

    Attributes:
        DISABLE: Indicates WABA is disabled.
        REINSTATE: Indicates the WABA has been reinstated.
        SCHEDULE_FOR_DISABLE: Indicates the WABA has been scheduled to be disabled.
    """

    DISABLE = "DISABLE"
    REINSTATE = "REINSTATE"
    SCHEDULE_FOR_DISABLE = "SCHEDULE_FOR_DISABLE"

    UNKNOWN = "UNKNOWN"


@dataclasses.dataclass(frozen=True, slots=True)
class ViolationInfo:
    """
    Violation information for WABA ban state.

    Attributes:
        type: Violation type. See `Violations <https://developers.facebook.com/documentation/business-messaging/whatsapp/policy-enforcement#violations>`_ for a list of possible values.
    """

    type: str


@dataclasses.dataclass(frozen=True, slots=True)
class BanInfo:
    _date_fmt = "%B %d, %Y"  # January 2, 2026
    """
    Ban information for WABA ban state.

    Attributes:
        state: WABA ban state.
        date: Indicates when the WABA was banned.
    """

    state: WABABanState
    date: datetime.date

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            state=WABABanState(data["waba_ban_state"]),
            date=datetime.datetime.strptime(
                data["waba_ban_date"], cls._date_fmt
            ).date(),
        )


@dataclasses.dataclass(frozen=True, slots=True)
class RestrictionInfo:
    """
    Restriction info for WABA ban state.

    Attributes:
        type: Type of restriction applied to the account.
        expiration: Indicates when the restriction expires.
        remediation: Steps the business can take to remediate the restriction.
    """

    type: RestrictionType
    expiration: datetime.datetime
    remediation: str | None

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            type=RestrictionType(data["restriction_type"]),
            expiration=datetime.datetime.fromtimestamp(
                data["expiration"], tz=datetime.timezone.utc
            ),
            remediation=data.get("remediation"),
        )


@dataclasses.dataclass(frozen=True, slots=True)
class DisconnectionInfo:
    """
    Disconnection info for WABA ban state.

    Attributes:
        reason: Reason for the disconnection.
        initiated_by: Indicates whether the disconnection was initiated by your client or the system.
    """

    reason: DisconnectionReason
    initiated_by: DisconnectionInitiatedBy

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            reason=DisconnectionReason(data["reason"]),
            initiated_by=DisconnectionInitiatedBy(data["initiated_by"]),
        )


@dataclasses.dataclass(frozen=True, slots=True)
class WABAInfo:
    """
    The WABA information for ``AD_ACCOUNT_LINKED``, ``PARTNER_*`` events, and ``MM_LITE_TERMS_SIGNED`` event.

    Attributes:
        id: WhatsApp Business Account ID.
        owner_business_id: Business portfolio ID.
        partner_app_id: Partner app ID. Only included for ``PARTNER_APP_INSTALLED``, ``PARTNER_APP_UNINSTALLED`` events.
        solution_id: Multi-Partner Solution solution ID. Only included for ``PARTNER_APP_INSTALLED`` events, omitted from ``PARTNER_APP_UNINSTALLED`` events.
        solution_partner_business_ids: Business portfolio IDs of the Tech Provider (or Tech Partner) and Solution Partner associated with the Multi-Partner Solution. Only included for ``PARTNER_APP_INSTALLED`` events, omitted from ``PARTNER_APP_UNINSTALLED`` events.
        ad_account_linked: Ad account ID. Only included for ``AD_ACCOUNT_LINKED`` event.
    """

    id: str
    owner_business_id: str
    partner_app_id: str | None
    solution_id: str | None
    solution_partner_business_ids: tuple[str, ...]
    ad_account_linked: str | None

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data["waba_id"],
            owner_business_id=data["owner_business_id"],
            partner_app_id=data.get("partner_app_id"),
            solution_id=data.get("solution_id"),
            solution_partner_business_ids=tuple(
                data.get("solution_partner_business_ids", [])
            ),
            ad_account_linked=data.get("ad_account_linked"),
        )


@dataclasses.dataclass(frozen=True, slots=True)
class ExceptionCountry:
    """
    Represents a country where Authentication-International rates apply.

    - Read more at `developers.facebook.com <https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing/authentication-international-rates#exception-countries>`_.

    Attributes:
        country_code: The ISO 3166-1 alpha-2 country code (e.g., 'US' for the United States) representing the exception country.
        start_time: A UTC timestamp indicating exactly when newly initiated authentication messages to this country become subject to Authentication-International rates.
    """

    country_code: str
    start_time: datetime.datetime

    @classmethod
    def from_dict(cls, data: dict) -> ExceptionCountry:
        return cls(
            country_code=data["country_code"],
            start_time=datetime.datetime.fromtimestamp(
                data["start_time"], tz=datetime.timezone.utc
            ),
        )


@dataclasses.dataclass(frozen=True, slots=True)
class AuthInternationalRateEligibility:
    """
    Represents a business's eligibility footprint for WhatsApp Authentication-International rates.

    According to Meta's pricing model, businesses sending authentication messages (OTPs) that exceed a specific threshold (e.g., 750,000 messages in a moving 30-day window) trigger international rates across exception markets if their primary business location is outside of those countries.

    - Read more at `developers.facebook.com <https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing/authentication-international-rates>`_.

    Attributes:
        exception_countries: A tuple containing individual exception countries and their respective rate activation dates.
        start_time: The general evaluation or notification timestamp determining when the overall eligibility was processed or communicated by Meta.
    """

    exception_countries: tuple[ExceptionCountry, ...]
    start_time: datetime.datetime

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            exception_countries=tuple(
                ExceptionCountry.from_dict(c)
                for c in data.get("exception_countries", [])
            ),
            start_time=datetime.datetime.fromtimestamp(
                data["start_time"], tz=datetime.timezone.utc
            ),
        )


@dataclasses.dataclass(frozen=True, slots=True)
class VolumeTierInfo:
    """
    Represents the details of a volume-based pricing tier update for a WhatsApp Business Account (WABA).

    Attributes:
        tier_update_time: UTC timestamp indicating when the pricing tier was updated.
        pricing_category: Pricing category for the volume-based pricing tier update.
        tier: Volume range for the pricing tier. tuple of (min, max).
        effective_month: Effective month for the volume-based pricing tier update.
        region: Region for the volume-based pricing tier update.
    """

    tier_update_time: datetime.datetime
    tier: tuple[int, int]
    pricing_category: PricingCategory
    effective_month: datetime.date
    region: str

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            tier_update_time=datetime.datetime.fromtimestamp(
                data["tier_update_time"], tz=datetime.timezone.utc
            ),
            tier=tuple(int(c) for c in data["tier"].split(":")),
            pricing_category=PricingCategory(data["pricing_category"]),
            effective_month=datetime.datetime.strptime(
                data["effective_month"], "%Y-%m"
            ).date(),
            region=data["region"],
        )


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class AccountUpdate(BaseUpdate):
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

    event: AccountUpdateEvent
    waba_info: WABAInfo | None
    violation_info: ViolationInfo | None
    ban_info: BanInfo | None
    restriction_info: tuple[RestrictionInfo, ...]
    disconnection_info: DisconnectionInfo | None
    auth_international_rate_eligibility: AuthInternationalRateEligibility | None
    volume_tier_info: VolumeTierInfo | None

    _webhook_field = "account_update"

    @classmethod
    def from_update(cls, client: WhatsApp, update: RawUpdate) -> BaseUpdate:
        value = (data := update["entry"][0])["changes"][0]["value"]
        return cls(
            _client=client,
            raw=update,
            id=data["id"],
            timestamp=datetime.datetime.fromtimestamp(
                data["time"], tz=datetime.timezone.utc
            ),
            event=AccountUpdateEvent(value["event"]),
            waba_info=WABAInfo.from_dict(value["waba_info"])
            if "waba_info" in value
            else None,
            violation_info=ViolationInfo(type=value["violation_info"]["violation_type"])
            if "violation_info" in value
            else None,
            ban_info=BanInfo.from_dict(value["ban_info"])
            if "ban_info" in value
            else None,
            restriction_info=tuple(
                RestrictionInfo.from_dict(r) for r in value.get("restriction_info", [])
            ),
            disconnection_info=DisconnectionInfo.from_dict(value["disconnection_info"])
            if "disconnection_info" in value
            else None,
            auth_international_rate_eligibility=AuthInternationalRateEligibility.from_dict(
                value["auth_international_rate_eligibility"]
            )
            if "auth_international_rate_eligibility" in value
            else None,
            volume_tier_info=VolumeTierInfo.from_dict(value["volume_tier_info"])
            if "volume_tier_info" in value
            else None,
        )
