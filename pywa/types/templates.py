"""This module contains classes and functions related to WhatsApp message templates."""

from __future__ import annotations


__all__ = [
    "TemplateStatusUpdate",
    "TemplateStatus",
    "TemplateRejectionReason",
    "TemplateCategoryUpdate",
    "TemplateCategory",
    "TemplateComponentsUpdate",
    "TemplateQualityUpdate",
    "QualityScore",
    "QualityScoreType",
    "TemplateLanguage",
    "ParamFormat",
    "TemplateBaseComponent",
    "HeaderText",
    "HeaderImage",
    "HeaderVideo",
    "HeaderDocument",
    "HeaderLocation",
    "HeaderProduct",
    "BodyText",
    "DateTime",
    "Currency",
    "AuthenticationBody",
    "FooterText",
    "AuthenticationFooter",
    "Buttons",
    "CopyCodeButton",
    "FlowButton",
    "FlowButtonIcon",
    "PhoneNumberButton",
    "VoiceCallButton",
    "QuickReplyButton",
    "URLButton",
    "AppDeepLink",
    "CatalogButton",
    "MPMButton",
    "SPMButton",
    "CallPermissionRequestButton",
    "BaseOTPButton",
    "CopyCodeOTPButton",
    "OneTapOTPButton",
    "ZeroTapOTPButton",
    "OTPSupportedApp",
    "LimitedTimeOffer",
    "Carousel",
    "CarouselCard",
    "Template",
    "CreatedTemplate",
    "UpdatedTemplate",
    "CreatedTemplates",
    "TemplateDetails",
    "TemplatesResult",
    "TemplatesCompareResult",
    "TemplateUnpauseResult",
    "MigrateTemplatesResult",
    "MigratedTemplate",
    "MigratedTemplateError",
    "LibraryTemplate",
    "LibraryTemplateBodyInputs",
    "LibraryTemplateButtonInputs",
]

import datetime
import json
import pathlib
import re

from . import CallbackData
from .base_update import BaseUpdate
from .flows import FlowActionType, FlowJSON
import abc
import dataclasses
import logging
from typing import TYPE_CHECKING, Literal, BinaryIO, cast, Iterator

from .media import Media
from .others import Result, SuccessResult, ProductsSection, _ItemFactory
from .. import utils
from .. import _helpers as helpers
from ..listeners import TemplateUpdateListenerIdentifier

if TYPE_CHECKING:
    from pywa import filters as pywa_filters
    from ..client import WhatsApp
    from .sent_update import SentTemplate

_logger = logging.getLogger(__name__)


class TemplateStatus(utils.StrEnum):
    """
    The status of the template.

    `'Template status' on
    developers.facebook.com
    <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates#template-status>`_

    Attributes:
        APPROVED: Indicates the template has been approved and can now be sent in template messages.
        DISABLED: Indicates the template has been disabled due to `user feedback <https://developers.facebook.com/docs/whatsapp/message-templates/guidelines/#quality-rating>`_.
        DELETED: Indicates the template has been deleted.
        IN_APPEAL: Indicates the template is in the `appeal <https://developers.facebook.com/docs/whatsapp/message-templates/guidelines/#appeals>`_ process.
        PENDING: Indicates the template is undergoing template review.
        REINSTATED: Indicates the template is no longer flagged or disabled and can be sent in template messages again.
        REJECTED: Indicates the template has been rejected. You can :meth:`~pywa.types.templates.Template.update` the template to have it undergo template review again or `appeal <https://developers.facebook.com/docs/whatsapp/message-templates/guidelines/#appeals>`_ the rejection.
        PENDING_DELETION: Indicates template has been deleted via WhatsApp Manager.
        FLAGGED: Indicates the template has received negative feedback and is at risk of being disabled.
        PAUSED: Indicates the template has been `paused <https://developers.facebook.com/docs/whatsapp/message-templates/guidelines/#template-pausing>`_.
        ARCHIVED: Indicates template has been archived to keep the list of templates in WhatsApp manager clean.
        LIMIT_EXCEEDED: Indicates the WhatsApp Business Account template is at its template limit.
        LOCKED: Indicates the template has been locked and cannot be edited.
        UNKNOWN: The status of the template is unknown.
    """

    APPROVED = "APPROVED"
    DISABLED = "DISABLED"
    IN_APPEAL = "IN_APPEAL"
    PENDING = "PENDING"
    REINSTATED = "REINSTATED"
    REJECTED = "REJECTED"
    DELETED = "DELETED"
    PENDING_DELETION = "PENDING_DELETION"
    FLAGGED = "FLAGGED"
    PAUSED = "PAUSED"
    LIMIT_EXCEEDED = "LIMIT_EXCEEDED"
    ARCHIVED = "ARCHIVED"
    LOCKED = "LOCKED"

    UNKNOWN = "UNKNOWN"


class TemplateRejectionReason(utils.StrEnum):
    """
    The reason the template was rejected.

    `'Rejection status' on
    developers.facebook.com
    <https://developers.facebook.com/docs/whatsapp/updates-to-pricing/new-template-guidelines#rejected-status>`_

    Attributes:
        PROMOTIONAL: Indicates template contains content that violates our policies.
        ABUSIVE_CONTENT: Indicates template contains content that violates our policies.
        INCORRECT_CATEGORY: Indicates the template's content doesn't match the category designated at the time of template creation.
        INVALID_FORMAT: Indicates template has an invalid format.
        SCAM: Indicates template contains content that violates our policies.
        TAG_CONTENT_MISMATCH: Indicates the template's content doesn't match the category designated at the time of template creation.
        NONE: Indicates template was paused.
    """

    PROMOTIONAL = "PROMOTIONAL"
    ABUSIVE_CONTENT = "ABUSIVE_CONTENT"
    INCORRECT_CATEGORY = "INCORRECT_CATEGORY"
    INVALID_FORMAT = "INVALID_FORMAT"
    TAG_CONTENT_MISMATCH = "TAG_CONTENT_MISMATCH"
    SCAM = "SCAM"
    NONE = "NONE"

    UNKNOWN = "UNKNOWN"


@dataclasses.dataclass(slots=True, frozen=True, kw_only=True)
class BaseTemplateUpdate(BaseUpdate, abc.ABC):
    """Base class for template updates."""

    template_id: str
    template_name: str
    template_language: TemplateLanguage

    @property
    def listener_identifier(self) -> TemplateUpdateListenerIdentifier:
        return TemplateUpdateListenerIdentifier(
            waba_id=self.id,
            template_id=self.template_id,
        )

    def get_template(self) -> TemplateDetails:
        """
        Fetches the template details from WhatsApp.

        Returns:
            TemplateDetails: The details of the template.
        """
        return self._client.get_template(
            template_id=self.template_id,
        )


@dataclasses.dataclass(slots=True, frozen=True, kw_only=True)
class TemplateStatusUpdate(BaseTemplateUpdate):
    """
    Represents status change of a template.

    Triggers::

        - A template is approved.
        - A template is rejected.
        - A template is disabled.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/reference/message_template_status_update>`_.

    Attributes:
        id: ID of Whatsapp Business Accounts this update belongs to.
        timestamp: Timestamp of the update (in UTC).
        new_status: The new status of the template.
        template_id: The ID of the template.
        template_name: The name of the template.
        template_language: The language of the template.
        reason: The reason the template was rejected (if status is ``REJECTED``).
        disable_date: The date the template was disabled (if status is ``DISABLED``).
        title: Title of template pause or unpause event.
        description: String describing why the template was locked or unlocked.
        shared_data: Shared data between handlers.
    """

    new_status: TemplateStatus
    reason: TemplateRejectionReason | None = None
    disable_date: datetime.datetime | None = None
    title: str | None = None
    description: str | None = None

    _webhook_field = "message_template_status_update"

    @classmethod
    def from_update(cls, client: WhatsApp, update: dict) -> TemplateStatusUpdate:
        value = (data := update["entry"][0])["changes"][0]["value"]
        return cls(
            _client=client,
            raw=update,
            id=data["id"],
            timestamp=datetime.datetime.fromtimestamp(
                data["time"],
                datetime.timezone.utc,
            ),
            new_status=TemplateStatus(value["event"]),
            template_id=str(value["message_template_id"]),
            template_name=value["message_template_name"],
            template_language=TemplateLanguage(value["message_template_language"]),
            reason=TemplateRejectionReason(value["reason"])
            if value.get("reason")
            else None,
            disable_date=datetime.datetime.fromtimestamp(
                value["disable_info"]["disable_date"],
                datetime.timezone.utc,
            )
            if "disable_info" in value
            else None,
            title=value.get("other_info", {}).get("title"),
            description=value.get("other_info", {}).get("description"),
        )

    def unpause(self) -> TemplateUnpauseResult:
        """
        Unpause the template that has been paused due to pacing.

        - You must wait 5 minutes after a template has been paused as a result of pacing before calling this method.
        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/message-templates/guidelines#unpausing>`_.

        Returns:
            A TemplateUnpauseResult object containing the result of the unpause operation.
        """
        return self._client.unpause_template(template_id=self.template_id)


@dataclasses.dataclass(slots=True, frozen=True, kw_only=True)
class TemplateUnpauseResult:
    """
    Represents the result of a template unpause operation.

    >>> wa = WhatsApp(...)
    >>> template = wa.get_template(template_id=123456)
    >>> if template.status == TemplateStatus.PAUSED:
    ...     result = template.unpause()



    Attributes:
        success: Whether the unpause operation was successful.
        reason: The reason for the unpause operation failure, if any.
    """

    success: bool
    reason: str | None = None

    def __bool__(self) -> bool:
        """
        Returns True if the unpause operation was successful, False otherwise.
        """
        return self.success


@dataclasses.dataclass(slots=True, frozen=True, kw_only=True)
class TemplateCategoryUpdate(BaseTemplateUpdate):
    """
    Represents a template category update.

    Triggers::

        - The existing category of a WhatsApp template is going to be changed by an automated process.
        - The existing category of a WhatsApp template is changed manually or by an automated process.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/reference/template_category_update>`_.

    Attributes:
        id: ID of Whatsapp Business Accounts this update belongs to.
        timestamp: Timestamp of the update (in UTC).
        template_id: The ID of the template.
        template_name: The name of the template.
        template_language: The language of the template.
        correct_category: The category that the template will be `recategorized <https://developers.facebook.com/docs/whatsapp/updates-to-pricing/new-template-guidelines/#how-we-update-a-template-s-category-after-initial-approval>`_ as in 24 hours.
        previous_category: The template's previous category.
        new_category: If ``correct_category`` is set - the ``new_category`` is the current category of the template. If ``previous_category`` is set - the ``new_category`` is the category that the template was recategorized to.
    """

    new_category: TemplateCategory
    previous_category: TemplateCategory | None = None
    correct_category: TemplateCategory | None = None

    _webhook_field = "template_category_update"

    @classmethod
    def from_update(cls, client: WhatsApp, update: dict) -> TemplateCategoryUpdate:
        value = (data := update["entry"][0])["changes"][0]["value"]
        return cls(
            _client=client,
            raw=update,
            id=data["id"],
            timestamp=datetime.datetime.fromtimestamp(
                data["time"],
                datetime.timezone.utc,
            ),
            template_id=str(value["message_template_id"]),
            template_name=value["message_template_name"],
            template_language=TemplateLanguage(value["message_template_language"]),
            new_category=TemplateCategory(value["new_category"]),
            previous_category=TemplateCategory(value["previous_category"])
            if "previous_category" in value
            else None,
            correct_category=TemplateCategory(value["correct_category"])
            if "correct_category" in value
            else None,
        )


@dataclasses.dataclass(slots=True, frozen=True, kw_only=True)
class TemplateComponentsUpdate(BaseTemplateUpdate):
    """
    Represents a template components update.

    Triggers::

        - A template is edited.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/reference/message_template_components_update>`_.

    Attributes:
        id: ID of Whatsapp Business Accounts this update belongs to.
        timestamp: Timestamp of the update (in UTC).
        template_id: The ID of the template.
        template_name: The name of the template.
        template_language: The language of the template.
        template_element: The body text of the template.
        template_title: The header text of the template.
        template_footer: The footer text of the template.
        template_buttons: A list of buttons in the template.
    """

    template_element: str | None = None
    template_title: str | None = None
    template_footer: str | None = None
    template_buttons: list[dict[str, str]] | None = None

    _webhook_field = "message_template_components_update"

    @classmethod
    def from_update(cls, client: WhatsApp, update: dict) -> TemplateComponentsUpdate:
        value = (data := update["entry"][0])["changes"][0]["value"]
        return cls(
            _client=client,
            raw=update,
            id=data["id"],
            timestamp=datetime.datetime.fromtimestamp(
                data["time"],
                datetime.timezone.utc,
            ),
            template_id=str(value["message_template_id"]),
            template_name=value["message_template_name"],
            template_language=TemplateLanguage(value["message_template_language"]),
            template_element=value.get("message_template_element"),
            template_title=value.get("message_template_title"),
            template_footer=value.get("message_template_footer"),
            template_buttons=value.get("message_template_buttons"),
        )


@dataclasses.dataclass(slots=True, frozen=True, kw_only=True)
class TemplateQualityUpdate(BaseTemplateUpdate):
    """
    Represents a template quality update.

    Triggers::

        - A template's quality score changes.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/reference/message_template_quality_update>`_.

    Attributes:
        id: ID of Whatsapp Business Accounts this update belongs to.
        timestamp: Timestamp of the update (in UTC).
        template_id: The ID of the template.
        template_name: The name of the template.
        template_language: The language of the template.
        new_quality_score: The new quality score of the template.
        previous_quality_score: The previous quality score of the template.
    """

    new_quality_score: QualityScoreType
    previous_quality_score: QualityScoreType

    _webhook_field = "message_template_quality_update"

    @classmethod
    def from_update(cls, client: WhatsApp, update: dict) -> TemplateQualityUpdate:
        value = (data := update["entry"][0])["changes"][0]["value"]
        return cls(
            _client=client,
            raw=update,
            id=data["id"],
            timestamp=datetime.datetime.fromtimestamp(
                data["time"],
                datetime.timezone.utc,
            ),
            template_id=str(value["message_template_id"]),
            template_name=value["message_template_name"],
            template_language=TemplateLanguage(value["message_template_language"]),
            new_quality_score=QualityScoreType(value["new_quality_score"]),
            previous_quality_score=QualityScoreType(value["previous_quality_score"]),
        )


class QualityScoreType(utils.StrEnum):
    """
    Every message template has a quality rating based on usage, customer feedback and engagement. A message template's rating will appear in the WhatsApp Manager whenever it has an Active status, and will be displayed after a hyphen in the message template's status:

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/message-templates/guidelines#quality-rating>`_.

    Attributes:
        GREEN: Indicates high quality.
        RED: Indicates low quality.
        YELLOW: Indicates medium quality.
        UNKNOWN:  Indicates quality pending.
    """

    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"
    UNKNOWN = "UNKNOWN"


@dataclasses.dataclass(slots=True, kw_only=True)
class LibraryTemplate:
    """
    Template Library makes it faster and easier for businesses to create utility templates for common use cases, like payment reminders, delivery updates — and authentication templates for common identity verification use cases.

    These pre-written templates have already been categorized as utility or authentication. Library templates contain fixed content that cannot be edited and parameters you can adapt for business or user-specific information.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-message-templates/template-library#template-parameters-and-restrictions>`_.
    - Browse the available templates at `business.facebook.com <https://business.facebook.com/latest/whatsapp_manager/template_library/>`_.
    Attributes:
        name: The name of the template.
        library_template_name: The exact name of the Template Library template.
        category: The category of the template.
        language: The language of the template.
        library_template_body_inputs: Optional inputs for the body of the template.
        library_template_button_inputs: Optional inputs for the buttons of the template.
    """

    name: str
    library_template_name: str
    category: TemplateCategory
    language: TemplateLanguage
    library_template_body_inputs: list[LibraryTemplateBodyInputs] | None = None
    library_template_button_inputs: list[LibraryTemplateButtonInputs] | None = None

    def to_json(self) -> str:
        return _template_to_json(self)


@dataclasses.dataclass(slots=True, kw_only=True)
class LibraryTemplateBodyInputs:
    """
    Optional data during creation of a template from Template Library. These are optional fields for the body component.

    Attributes:
        add_contact_number: Boolean value to add information to the template about contacting business on their phone number.
        add_learn_more_link: Boolean value to add information to the template about learning more information with a url link.
        add_security_recommendation: Boolean value to add information to the template about not sharing authentication codes with anyone.
        add_track_package_link: Boolean value to add information to the template to track delivery packages.
        code_expiration_minutes: Integer value to add information to the template on when the code will expire.
    """

    add_contact_number: bool | None = None
    add_learn_more_link: bool | None = None
    add_security_recommendation: bool | None = None
    add_track_package_link: bool | None = None
    code_expiration_minutes: int | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class LibraryTemplateButtonInputs:
    """
    Optional data during creation of a template from Template Library. These are optional fields for the button component.

    Attributes:
        type: The button type
        url: A dictionary with ``base_url`` and ``url_suffix_example``
        otp_type: The type of OTP button, if applicable.
        zero_tap_terms_accepted: Weather the zero tap terms were accepted by the user or not.
        supported_apps: A list of supported apps for the OTP button.
    """

    type: ComponentType
    url: dict | None = None
    otp_type: OtpType | None = None
    zero_tap_terms_accepted: bool | None = None
    supported_apps: list[OTPSupportedApp] | None = None


@dataclasses.dataclass(slots=True, frozen=True)
class QualityScore:
    """
    Represents the quality score of a template.

    Attributes:
        score: The quality score type (GREEN, YELLOW, RED).
        date: The date when the score was last updated.
    """

    score: QualityScoreType
    date: datetime.datetime

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            score=QualityScoreType(data["score"]),
            date=datetime.datetime.fromtimestamp(
                data["date"], tz=datetime.timezone.utc
            ),
        )


class TemplateCategory(utils.StrEnum):
    """
    Template category.

    `'Template Categorization' on
    developers.facebook.com
    <https://developers.facebook.com/docs/whatsapp/updates-to-pricing/new-template-guidelines#template-categorization>`_

    Attributes:
        AUTHENTICATION: Enable businesses to verify a user’s identity, potentially at various steps of the customer journey.
        MARKETING: Enable businesses to achieve a wide range of goals, from generating awareness to driving sales and retargeting customers.
        UTILITY: Enable businesses to follow up on user actions or requests, since these messages are typically triggered by user actions.
    """

    AUTHENTICATION = "AUTHENTICATION"
    MARKETING = "MARKETING"
    UTILITY = "UTILITY"

    UNKNOWN = "UNKNOWN"


class TemplateSubCategory(utils.StrEnum):
    CALL_PERMISSIONS_REQUEST = "CALL_PERMISSIONS_REQUEST"

    UNKNOWN = "UNKNOWN"


class ComponentType(utils.StrEnum):
    HEADER = "HEADER"
    BODY = "BODY"
    FOOTER = "FOOTER"
    BUTTONS = "BUTTONS"
    CAROUSEL = "CAROUSEL"
    LIMITED_TIME_OFFER = "LIMITED_TIME_OFFER"
    PHONE_NUMBER = "PHONE_NUMBER"
    URL = "URL"
    QUICK_REPLY = "QUICK_REPLY"
    OTP = "OTP"
    MPM = "MPM"
    SPM = "SPM"
    CATALOG = "CATALOG"
    COPY_CODE = "COPY_CODE"
    FLOW = "FLOW"
    VOICE_CALL = "VOICE_CALL"
    APP = "APP"
    CALL_PERMISSION_REQUEST = "CALL_PERMISSION_REQUEST"

    UNKNOWN = "UNKNOWN"


class HeaderFormatType(utils.StrEnum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    DOCUMENT = "DOCUMENT"
    LOCATION = "LOCATION"
    PRODUCT = "PRODUCT"

    UNKNOWN = "UNKNOWN"


class ParamType(utils.StrEnum):
    """
    Parameter types for template parameters

    `'Parameter object' on developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/messages#parameter-object>`_
    """

    _check_value = str.islower
    _modify_value = str.lower

    TEXT = "text"
    CURRENCY = "currency"
    DATE_TIME = "date_time"
    DOCUMENT = "document"
    IMAGE = "image"
    VIDEO = "video"
    LOCATION = "location"
    BUTTON = "button"
    PRODUCT = "product"
    COUPON_CODE = "coupon_code"
    ACTION = "action"
    PAYLOAD = "payload"
    LIMITED_TIME_OFFER = "limited_time_offer"
    CAROUSEL = "carousel"

    UNKNOWN = "UNKNOWN"


class TemplateLanguage(utils.StrEnum):
    """
    Template language and locale code.

    `'Template language and locale code' on
    developers.facebook.com
    <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/supported-languages>`_
    """

    _check_value = None
    _modify_value = None

    AFRIKAANS = "af"
    ALBANIAN = "sq"
    ARABIC = "ar"
    AZERBAIJANI = "az"
    BENGALI = "bn"
    BULGARIAN = "bg"
    CATALAN = "ca"
    CHINESE_CHN = "zh_CN"
    CHINESE_HKG = "zh_HK"
    CHINESE_TAI = "zh_TW"
    CROATIAN = "hr"
    CZECH = "cs"
    DANISH = "da"
    DUTCH = "nl"
    ENGLISH = "en"
    ENGLISH_UK = "en_GB"
    ENGLISH_US = "en_US"
    ESTONIAN = "et"
    FILIPINO = "fil"
    FINNISH = "fi"
    FRENCH = "fr"
    GEORGIAN = "ka"
    GERMAN = "de"
    GREEK = "el"
    GUJARATI = "gu"
    HAUSA = "ha"
    HEBREW = "he"
    HINDI = "hi"
    HUNGARIAN = "hu"
    INDONESIAN = "id"
    IRISH = "ga"
    ITALIAN = "it"
    JAPANESE = "ja"
    KANNADA = "kn"
    KAZAKH = "kk"
    KINYARWANDA = "rw_RW"
    KOREAN = "ko"
    KYRGYZ_KG = "ky_KG"
    LAO = "lo"
    LATVIAN = "lv"
    LITHUANIAN = "lt"
    MACEDONIAN = "mk"
    MALAY = "ms"
    MALAYALAM = "ml"
    MARATHI = "mr"
    NORWEGIAN = "nb"
    PERSIAN = "fa"
    POLISH = "pl"
    PORTUGUESE_BR = "pt_BR"
    PORTUGUESE_POR = "pt_PT"
    PUNJABI = "pa"
    ROMANIAN = "ro"
    RUSSIAN = "ru"
    SERBIAN = "sr"
    SLOVAK = "sk"
    SLOVENIAN = "sl"
    SPANISH = "es"
    SPANISH_ARG = "es_AR"
    SPANISH_SPA = "es_ES"
    SPANISH_MEX = "es_MX"
    SWAHILI = "sw"
    SWEDISH = "sv"
    TAMIL = "ta"
    TELUGU = "te"
    THAI = "th"
    TURKISH = "tr"
    UKRAINIAN = "uk"
    URDU = "ur"
    UZBEK = "uz"
    VIETNAMESE = "vi"
    ZULU = "zu"

    UNKNOWN = "UNKNOWN"


class ParamFormat(utils.StrEnum):
    """The type of parameter formatting the HEADER and BODY components of the template will use."""

    POSITIONAL = "POSITIONAL"
    NAMED = "NAMED"

    UNKNOWN = "UNKNOWN"


class TemplateBaseComponent(abc.ABC):
    """Base class for all template components"""

    type: ComponentType

    @classmethod
    def from_dict(cls, data: dict) -> TemplateBaseComponent:
        # noinspection PyArgumentList
        return cls(
            **{
                k: v
                for k, v in data.items()
                if k in {f.name for f in dataclasses.fields(cls) if f.init}
            }
        )

    def to_dict(self) -> dict:
        """
        Converts the component to a dictionary representation.

        Returns:
            dict: The dictionary representation of the component.
        """
        return dataclasses.asdict(
            obj=self,
            dict_factory=lambda d: {k: v for (k, v) in d if v is not None},
        )

    class Params(abc.ABC):
        """Base class for template component parameters."""

        @abc.abstractmethod
        def to_dict(self) -> dict: ...

    @abc.abstractmethod
    def params(self, *args, **kwargs) -> Params: ...


# =========== HEADER ===========


class BaseHeaderComponent(TemplateBaseComponent, abc.ABC):
    type = ComponentType.HEADER
    format: HeaderFormatType


class _TextParam(abc.ABC):
    @abc.abstractmethod
    def to_dict(self) -> dict: ...


@dataclasses.dataclass(slots=True, kw_only=True)
class Currency(_TextParam):
    """
    Represents a currency parameter for a text component in a template.

    Attributes:
        fallback_value: A human-readable default value shown if the client's app doesn't support localization.
        code: Currency code (ISO 4217), e.g., ``USD``, ``EUR``, ``ILS``.
        amount_1000: The amount multiplied by 1000. For example, `$19.99 → 19990`.
    """

    fallback_value: str
    code: str
    amount_1000: int

    def to_dict(self) -> dict:
        return {
            "type": ParamType.CURRENCY.value,
            ParamType.CURRENCY.value: {
                "fallback_value": self.fallback_value,
                "code": self.code,
                "amount_1000": self.amount_1000,
            },
        }


@dataclasses.dataclass(slots=True, kw_only=True)
class DateTime(_TextParam):
    """
    Represents a date and time parameter for a text component in a template.

    Attributes:
        fallback_value: A human-readable date string to display to the user, e.g., `August 5, 2025`.
    """

    fallback_value: str

    def to_dict(self) -> dict:
        return {
            "type": ParamType.DATE_TIME.value,
            ParamType.DATE_TIME.value: {
                "fallback_value": self.fallback_value,
            },
        }


class _BaseTextComponent:
    type: Literal[ComponentType.HEADER, ComponentType.BODY]

    __slots__ = ("text", "example", "param_format")

    def __init__(self, text: str, *positionals_examples, **named_examples):
        """
        Initializes a text component for a template.


        >>> positionals = HeaderText("Hi {{1}}!, How are you? Get {{2}}% OFF!", "David", 15)
        >>> named = BodyText("Hi {{name}}!, How are you? Get {{discount}}% OFF!", name="David", discount=15)
        >>> print(positionals.preview(), named.preview())

        Args:
            text: The text of the component. Use ``{{1}}``, ``{{2}}``, etc. for positional parameters, or ``{{param_name}}`` for named parameters.
            *positionals_examples: Positional examples for the text component. These will be used to fill in the template text.
            **named_examples: Named examples for the text component. These will be used to fill in the template text.
        """
        if positionals_examples and named_examples:
            raise ValueError("You can't use both positional and named args!")
        if positionals_examples:
            self.param_format = ParamFormat.POSITIONAL
            self.text = text
            self.example = positionals_examples
        elif named_examples:
            self.param_format = ParamFormat.NAMED
            self.text = text
            self.example = named_examples
        else:
            self.param_format = None
            self.example = None
            self.text = text

    def __repr__(self):
        if self.param_format == ParamFormat.POSITIONAL:
            return f"{self.__class__.__name__}(text={self.text!r}, {', '.join(map(repr, self.example))})"
        elif self.param_format == ParamFormat.NAMED:
            return f"{self.__class__.__name__}(text={self.text!r}, {', '.join(f'{k}={v!r}' for k, v in self.example.items())})"
        return f"{self.__class__.__name__}(text={self.text!r})"

    def preview(self) -> str:
        """
        Returns a preview of the template text with examples filled in.
        """
        if self.param_format == ParamFormat.POSITIONAL:
            txt = re.sub(
                r"\{\{(\d+)}}", lambda m: f"{{{int(m.group(1)) - 1}}}", self.text
            )  # Adjust for zero-based indexing
            return txt.format(*self.example)
        elif self.param_format == ParamFormat.NAMED:
            return (
                self.text.replace("{{", "{").replace("}}", "}").format(**self.example)
            )
        else:
            return self.text

    def to_dict(self) -> dict:
        match self.param_format:
            case ParamFormat.POSITIONAL:
                return {
                    "type": self.type.value,
                    "text": self.text,
                    "example": {
                        f"{self.type.lower()}_text": [list(map(str, self.example))]
                        if self.type == ComponentType.BODY
                        else list(map(str, self.example))
                    },
                }
            case ParamFormat.NAMED:
                return {
                    "type": self.type.value,
                    "text": self.text,
                    "example": {
                        f"{self.type.lower()}_text_named_params": [
                            {"param_name": k, "example": str(v)}
                            for k, v in self.example.items()
                        ]
                    },
                }
            case _:
                return {"type": self.type.value, "text": self.text}

    @classmethod
    def from_dict(cls, data: dict) -> _BaseTextComponent:
        if "example" in data:
            example = next(iter(data["example"].values()))
            if isinstance(example, list):
                if isinstance(
                    example[0], list
                ):  # {"example": {"body_text": [["example1", "example2"]]}}
                    return cls(data["text"], *example[0])
                elif isinstance(
                    example[0], str
                ):  # {"example": {"header_text": ["example"]}}
                    return cls(data["text"], *example)
                elif isinstance(
                    example[0], dict
                ):  # {"example": {"body_text_named_params": [{"param_name": "name", "example": "John"}]}}
                    return cls(
                        text=data["text"],
                        **{item["param_name"]: item["example"] for item in example},
                    )
            elif isinstance(example, str):  # {"example": "example"}
                return cls(data["text"], example)
        return cls(text=data["text"])

    class Params(TemplateBaseComponent.Params):
        typ: Literal[ComponentType.HEADER, ComponentType.BODY]

        def __init__(self, *positionals, **named):
            if positionals and named:
                raise ValueError("You can't use both positional and named args!")
            if not positionals and not named:
                raise ValueError(
                    "At least one positional or named argument is required."
                )
            self.positionals = positionals
            self.named = named

        def to_dict(self) -> dict:
            return {
                "type": self.typ.value,
                "parameters": [
                    {
                        "type": ParamType.TEXT.value,
                        ParamType.TEXT.value: str(positional_param),
                    }
                    if not isinstance(positional_param, _TextParam)
                    else positional_param.to_dict()
                    for positional_param in self.positionals
                ]
                if self.positionals
                else [
                    {
                        "type": ParamType.TEXT.value,
                        ParamType.TEXT.value: str(named_param),
                        "parameter_name": param_name,
                    }
                    if not isinstance(named_param, _TextParam)
                    else named_param.to_dict()
                    for param_name, named_param in self.named.items()
                ],
            }

    def params(self, *positionals, **named) -> _BaseTextComponent.Params:
        """
        Fill the parameters for the header/body text component.

        Args:
            *positionals: Positional parameters to fill in the template text. e.g. for `"Hi {{1}}!"`, you would pass ``"John"`` as the first positional argument.
            **named: Named parameters to fill in the template text. e.g. for `"Hi {{name}}!"`, you would pass ``name="John"`` as a named argument.
        """
        if not self.param_format:
            raise ValueError(
                f"{self.__class__.__name__} does not support parameters, as it has no example."
            )
        if self.param_format == ParamFormat.POSITIONAL:
            if named:
                raise ValueError(
                    f"{self.__class__.__name__} does not support named parameters when text is positional."
                )
            if len(positionals) != len(self.example):
                raise ValueError(
                    f"{self.__class__.__name__} requires {len(self.example)} positional parameters, got {len(positionals)}."
                )
        if self.param_format == ParamFormat.NAMED:
            if positionals:
                raise ValueError(
                    f"{self.__class__.__name__} does not support positional parameters when text is named."
                )
            missing_params = set(self.example.keys()) - set(named.keys())
            unexpected_params = set(named.keys()) - set(self.example.keys())
            if missing_params:
                raise ValueError(
                    f"{self.__class__.__name__} is missing parameters: {', '.join(missing_params)}."
                )
            if unexpected_params:
                raise ValueError(
                    f"{self.__class__.__name__} received unexpected parameters: {', '.join(unexpected_params)}."
                )

        return self.Params(*positionals, **named)


class HeaderText(_BaseTextComponent, BaseHeaderComponent):
    """
    Represents a header text component in a template.

    - All templates are limited to one header component
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#text-headers>`_.

    Example:

        >>> header_text = HeaderText("Hi {{name}}! How are you? Get {{discount}}% OFF!", name="John", discount=15)
        >>> header_text.params(name="David", discount=20)

        >>> header_text = HeaderText("Hi {{1}}! How are you? Get {{2}}% OFF!", "John", 15)
        >>> header_text.params("David", 20)

        >>> print(header_text.preview())
    """

    format = HeaderFormatType.TEXT

    def to_dict(self) -> dict:
        return {
            "format": self.format.value,
            **super().to_dict(),
        }

    class Params(_BaseTextComponent.Params):
        typ = ComponentType.HEADER


class _BaseMediaHeaderComponent(BaseHeaderComponent, abc.ABC):
    """
    Base class for media components in templates.

    - Used in :class:`HeaderImage`, :class:`HeaderVideo`, and :class:`HeaderDocument` components.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#media-headers>`_.
    """

    __slots__ = ("_example", "_handle")

    format: HeaderFormatType

    def __init__(self, example: str | Media | pathlib.Path | bytes | BinaryIO):
        """
        Initializes a media header component for a template.

        Args:
            example: An example of the media to be used in the header. This can be a media ID, a URL, a file path, or raw bytes.
        """
        self.example = example

    @property
    def example(self) -> str | Media | pathlib.Path | bytes | BinaryIO:
        """
        Returns the example media for the header component.
        """
        return self._example

    @example.setter
    def example(self, value: str | Media | pathlib.Path | bytes | BinaryIO):
        """
        Sets the example media for the header component (and resets the handle).
        """
        self._example = value
        if re.match(r"^\d:.*", str(value)):
            # If the example is a file handle (e.g., "4:cGRmLnBkZg=="),
            self._handle = str(value)
        else:
            self._handle = None

    @classmethod
    def from_dict(cls, data: dict) -> _BaseMediaHeaderComponent:
        return cls(example=data["example"]["header_handle"][0])

    def to_dict(self) -> dict:
        if self._handle is None:
            raise ValueError(
                f"{self.__class__.__name__} media example not uploaded yet."
            )
        return {
            "type": self.type.value,
            "format": self.format.value,
            "example": {"header_handle": [self._handle]},
        }

    def __repr__(self):
        return f"{self.__class__.__name__}(example={self.example!r})"


class _BaseMediaParams(TemplateBaseComponent.Params, abc.ABC):
    format: HeaderFormatType
    param_type: Literal[ParamType.IMAGE, ParamType.VIDEO, ParamType.DOCUMENT]

    def __init__(self, media: str | Media | pathlib.Path | bytes | BinaryIO):
        self.media = media
        self._resolved_media: str | None = None
        self._is_url: bool | None = None

    def to_dict(
        self,
    ) -> dict:
        if self._resolved_media is None:
            raise ValueError(f"{self.__class__.__name__} media not resolved yet")
        return {
            "type": ComponentType.HEADER.value,
            "parameters": [
                {
                    "type": self.param_type.value,
                    self.param_type.value: {
                        "link" if self._is_url else "id": self._resolved_media,
                    },
                }
            ],
        }

    def clear_media_cache(self):
        """
        Clears the cached media for this media param (if you using the same params object more than 30 days, the media ID will be expired, so you need to reupload the media).
        """
        self._resolved_media = None
        self._is_url = None


class HeaderImage(_BaseMediaHeaderComponent):
    """
    Represents a header image component in a template.

    - All templates are limited to one header component.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#media-headers>`_.

    Example:

        >>> header_image = HeaderImage(example="https://example.com/image.jpg")
        >>> header_image.params(image="https://cdn.com/image.jpg")

    Attributes:
        example: An example of the header image media.
    """

    format = HeaderFormatType.IMAGE

    class Params(_BaseMediaParams):
        format = HeaderFormatType.IMAGE
        param_type = ParamType.IMAGE

        def __init__(self, *, image: str | Media | pathlib.Path | bytes | BinaryIO):
            """
            Fill the parameters for the header image component.

            Args:
                image: The image media to be used in the header. This can be a media ID, a URL, a file path, or raw bytes.
            """
            super().__init__(media=image)

    def params(self, *, image: str | Media | pathlib.Path | bytes | BinaryIO) -> Params:
        """
        Fill the parameters for the header image component.

        Args:
            image: The image media to be used in the header. This can be a media ID, a URL, a file path, or raw bytes.

        Returns:
            An instance of Params containing the media parameter.
        """
        return self.Params(image=image)


class HeaderVideo(_BaseMediaHeaderComponent):
    """
    Represents a header video component in a template.

    - All templates are limited to one header component.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#media-headers>`_.

    Example:

        >>> header_video = HeaderVideo(example="https://example.com/video.mp4")
        >>> header_video.params(video="https://cdn.com/video.mp4")

    Attributes:
        example: An example of the header video media.
    """

    format = HeaderFormatType.VIDEO

    class Params(_BaseMediaParams):
        format = HeaderFormatType.VIDEO
        param_type = ParamType.VIDEO

        def __init__(self, *, video: str | Media | pathlib.Path | bytes | BinaryIO):
            """
            Fill the parameters for the header video component.

            Args:
                video: The video media to be used in the header. This can be a media ID, a URL, a file path, or raw bytes.
            """
            super().__init__(media=video)

    def params(self, *, video: str | Media | pathlib.Path | bytes | BinaryIO) -> Params:
        """
        Fill the parameters for the header video component.

        Args:
            video: The video media to be used in the header. This can be a media ID, a URL, a file path, or raw bytes.

        Returns:
            An instance of Params containing the media parameter.
        """
        return self.Params(video=video)


class HeaderDocument(_BaseMediaHeaderComponent):
    """
    Represents a header document component in a template.

    - All templates are limited to one header component.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#media-headers>`_.

    Example:

        >>> header_document = HeaderDocument(example="https://example.com/document.pdf")
        >>> header_document.params(document="https://cdn.com/document.pdf")

    Attributes:
        example: An example of the header document media.
    """

    format = HeaderFormatType.DOCUMENT

    class Params(_BaseMediaParams):
        format = HeaderFormatType.DOCUMENT
        param_type = ParamType.DOCUMENT

        def __init__(self, *, document: str | Media | pathlib.Path | bytes | BinaryIO):
            """
            Fill the parameters for the header document component.

            Args:
                document: The document media to be used in the header. This can be a media ID, a URL, a file path, or raw bytes.
            """
            super().__init__(media=document)

    def params(
        self, *, document: str | Media | pathlib.Path | bytes | BinaryIO
    ) -> Params:
        """
        Fill the parameters for the header document component.

        Args:
            document: The document media to be used in the header. This can be a media ID, a URL, a file path, or raw bytes.

        Returns:
            An instance of Params containing the media parameter.
        """
        return self.Params(document=document)


@dataclasses.dataclass(kw_only=True, slots=True)
class HeaderLocation(BaseHeaderComponent):
    """
    Represents a header location component in a template.

    - All templates are limited to one header component.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#location-headers>`_.

    Example:

        >>> header_location = HeaderLocation()
        >>> header_location.params(lat=37.7749, lon=-122.4194, name="San Francisco", address="California, USA")
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.HEADER,
        init=False,
        repr=False,
    )
    format: HeaderFormatType = dataclasses.field(
        default=HeaderFormatType.LOCATION,
        init=False,
        repr=False,
    )

    class Params(TemplateBaseComponent.Params):
        def __init__(self, *, lat: float, lon: float, name: str, address: str):
            """
            Fill the parameters for the header location component.

            Args:
                lat: Location latitude.
                lon: Location longitude.
                name: Text that will appear immediately below the generic map at the top of the message.
                address: Address that will appear after the ``name`` value, below the generic map at the top of the message.
            """
            self.lat = lat
            self.lon = lon
            self.name = name
            self.address = address

        def to_dict(self) -> dict:
            return {
                "type": ComponentType.HEADER.value,
                "parameters": [
                    {
                        "type": ParamType.LOCATION.value,
                        ParamType.LOCATION.value: {
                            "latitude": self.lat,
                            "longitude": self.lon,
                            "name": self.name,
                            "address": self.address,
                        },
                    }
                ],
            }

    def params(self, *, lat: float, lon: float, name: str, address: str) -> Params:
        """
        Fill the parameters for the header location component.

        Args:
            lat: Location latitude.
            lon: Location longitude.
            name: Text that will appear immediately below the generic map at the top of the message.
            address: Address that will appear after the ``name`` value, below the generic map at the top of the message.

        Returns:
            An instance of Params containing the location parameters.
        """
        return self.Params(lat=lat, lon=lon, name=name, address=address)


@dataclasses.dataclass(kw_only=True, slots=True)
class HeaderProduct(BaseHeaderComponent):
    """
    Represents a header product component in a template.

    - All templates are limited to one header component.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/spm-templates>`_.

    Example:

        >>> header_product = HeaderProduct()
        >>> header_product.params(catalog_id="1234567890", sku="SKU12345")
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.HEADER,
        init=False,
        repr=False,
    )
    format: HeaderFormatType = dataclasses.field(
        default=HeaderFormatType.PRODUCT,
        init=False,
        repr=False,
    )

    class Params(TemplateBaseComponent.Params):
        def __init__(self, *, catalog_id: str, sku: str):
            """
            Fill the parameters for the header product component.

            Args:
                catalog_id: ID of `connected ecommerce <https://www.facebook.com/business/help/158662536425974>`_ catalog containing the product.
                sku: Unique identifier of the product in a catalog (also referred to as ``Content ID`` or ``Retailer ID``).
            """
            self.catalog_id = catalog_id
            self.sku = sku

        def to_dict(self) -> dict:
            return {
                "type": ComponentType.HEADER.value,
                "parameters": [
                    {
                        "type": ParamType.PRODUCT.value,
                        ParamType.PRODUCT.value: {
                            "catalog_id": self.catalog_id,
                            "product_retailer_id": self.sku,
                        },
                    }
                ],
            }

    def params(self, *, catalog_id: str, sku: str) -> Params:
        """
        Fill the parameters for the header product component.

        Args:
            catalog_id: ID of `connected ecommerce <https://www.facebook.com/business/help/158662536425974>`_ catalog containing the product.
            sku: Unique identifier of the product in a catalog (also referred to as ``Content ID`` or ``Retailer ID``).

        Returns:
            An instance of Params containing the catalog ID and SKU.
        """
        return self.Params(catalog_id=catalog_id, sku=sku)


# =========== BODY ===========


class BaseBodyComponent(TemplateBaseComponent, abc.ABC):
    type: ComponentType


class BodyText(_BaseTextComponent):
    """
    The body component represents the core text of your message template and is a text-only template component. It is required for all templates.

    - All templates are limited to one body component.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#body>`_.

    Example:
        >>> body_text = BodyText("Hi {{name}}! How are you? Get {{discount}}% OFF!", name="John", discount=15)
        >>> body_text.params(name="David", discount=20)

        >>> body_text = BodyText("Hi {{1}}! How are you? Get {{2}}% OFF!", "John", 15)
        >>> body_text.params("David", 20)

        >>> print(body_text.preview())
    """

    type = ComponentType.BODY

    class Params(_BaseTextComponent.Params):
        typ = ComponentType.BODY


# =========== FOOTER ===========


@dataclasses.dataclass(kw_only=True, slots=True)
class BaseFooterComponent(TemplateBaseComponent, abc.ABC):
    type: ComponentType = dataclasses.field(
        default=ComponentType.FOOTER,
        init=False,
        repr=False,
    )


class _DoesNotSupportParams:
    """
    This class is used for components that do not support parameters.
    It raises an error if instantiated.
    """

    class Params(TemplateBaseComponent.Params):
        def __init__(self):
            """
            This class does not support parameters.
            """
            raise ValueError(f"{self.__class__.__name__} does not support parameters.")

        def to_dict(self) -> dict: ...

    def params(self, *args, **kwargs) -> Params:
        """
        This class does not support parameters.
        """
        return self.Params()


@dataclasses.dataclass(kw_only=True, slots=True)
class FooterText(_DoesNotSupportParams, BaseFooterComponent):
    """
    Footers are optional text-only components that appear immediately after the body component. Templates are limited to one footer component.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#footer>`_.

    Example:

        >>> footer = FooterText(text="Thank you for using our service!")

    Attributes:
        text: The footer text. 60 characters maximum.
    """

    text: str


# =========== BUTTONS ===========


class BaseButtonComponent(TemplateBaseComponent, abc.ABC): ...


@dataclasses.dataclass(kw_only=True, slots=True)
class Buttons(_DoesNotSupportParams, TemplateBaseComponent):
    """
    Buttons are optional interactive components that perform specific actions when tapped. Templates can have a mixture of up to 10 button components total, although there are limits to individual buttons of the same type as well as combination limits. These limits are described below.

    - If a template has more than three buttons, two buttons will appear in the delivered message and the remaining buttons will be replaced with a See all options button. Tapping the See all options button reveals the remaining buttons.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#buttons>`_.

    Example:

        >>> button1 = CopyCodeButton(example="SAVE20")
        >>> button2 = PhoneNumberButton(text="Call Us", phone_number="+1234567890")
        >>> button3 = URLButton(text="Visit Website", url="https://website.com")

        >>> buttons = Buttons(buttons=[button1, button2, button3])

    Attributes:
        buttons: A list of button components.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.BUTTONS,
        init=False,
        repr=False,
    )
    buttons: list[BaseButtonComponent | dict]

    @classmethod
    def from_dict(cls, data: dict) -> Buttons:
        return cls(buttons=[_parse_component(button) for button in data["buttons"]])


@dataclasses.dataclass(kw_only=True, slots=True)
class CopyCodeButton(BaseButtonComponent):
    """
    Copy code buttons copy a text string
    (defined when the template is sent in a template message) to the device's clipboard when tapped by the app user.

    - Templates are limited to one copy code button.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#copy-code-buttons>`_.

    Example:
        >>> copy_code_button = CopyCodeButton(example="SAVE20")
        >>> copy_code_button.params(coupon_code="SAVE20", index=0)

    Attributes:
        example: String to be copied to device's clipboard when tapped by the app user. Maximum 15 characters.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.COPY_CODE,
        init=False,
        repr=False,
    )
    example: str

    class Params(TemplateBaseComponent.Params):
        def __init__(self, *, coupon_code: str, index: int):
            """
            Fill the parameters for the copy code button component.

            Args:
                coupon_code: The coupon code to be copied when the customer taps the button. Only accepting alphanumeric characters.
                index: Indicates order in which button should appear, if the template uses multiple buttons. Buttons are zero-indexed, so setting value to 0 will cause the button to appear first, and another button with an index of 1 will appear next, etc.
            """
            self.coupon_code = coupon_code
            self.index = index

        def to_dict(self) -> dict:
            return {
                "type": ParamType.BUTTON.value,
                "sub_type": ComponentType.COPY_CODE.value,
                "index": self.index,
                "parameters": [
                    {
                        "type": ParamType.COUPON_CODE.value,
                        ParamType.COUPON_CODE.value: self.coupon_code,
                    }
                ],
            }

    def params(self, *, coupon_code: str, index: int) -> Params:
        """
        Fill the parameters for the copy code button component.

        Args:
            coupon_code: The coupon code to be copied when the customer taps the button. Only accepting alphanumeric characters.
            index: Indicates order in which button should appear, if the template uses multiple buttons. Buttons are zero-indexed, so setting value to 0 will cause the button to appear first, and another button with an index of 1 will appear next, etc.

        Returns:
            An instance of Params containing the coupon code and index.
        """
        return self.Params(coupon_code=coupon_code, index=index)


class FlowButtonIcon(utils.StrEnum):
    """
    The icon for the Flow button.

    Attributes:
        DOCUMENT: Icon for document flows.
        PROMOTION: Icon for promotion flows.
        REVIEW: Icon for review flows.
    """

    DOCUMENT = "DOCUMENT"
    PROMOTION = "PROMOTION"
    REVIEW = "REVIEW"

    UNKNOWN = "UNKNOWN"


class FlowButton(BaseButtonComponent):
    """
    Flows buttons are for sending `Flows Messages <https://pywa.readthedocs.io/en/latest/content/flows/overview.html>`_ as templates.

    - Flows can quickly be built in the playground and attached as JSON, or an existing Flow ID can be specified.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#flows-buttons>`_.

    Example:

        >>> flow_button = FlowButton(
        ...     text="Start Flow",
        ...     flow_id="1234567890",
        ...     flow_action=FlowActionType.NAVIGATE,
        ...     navigate_screen="entry_screen_id",
        ...     icon=FlowButtonIcon.DOCUMENT
        ... )
        >>> flow_button.params(index=0, flow_token="example_token", flow_action_data={"key": "value"})

    Attributes:
        text: Button label text. 25 characters maximum.
        flow_id: Unique identifier of the Flow provided by WhatsApp. The Flow must be published. Cannot be used with ``flow_name`` or ``flow_json``.
        flow_name: The name of the Flow. Supported in Cloud API only. The Flow ID is stored in the message template, not the name, so changing the Flow name will not affect existing message templates. The Flow must be published. Cannot be used with ``flow_id`` or ``flow_json``.
        flow_json: The JSON representation of the Flow. Cannot be used with ``flow_id`` or ``flow_name``.
        flow_action: navigate or data_exchange. Use ``NAVIGATE`` to predefine the first screen as part of the template message. Use ``DATA_EXCHANGE`` for advanced use-cases where the first screen is provided by your endpoint. Defaults to ``NAVIGATE``.
        navigate_screen: Optional only if ``flow_action`` is ``NAVIGATE``. The id of the entry screen of the Flow. Defaults to the first screen of the Flow.
        icon: Optional icon for the button.
    """

    type = ComponentType.FLOW
    text: str
    flow_id: str | None
    flow_name: str | None
    flow_json: FlowJSON | dict | str | pathlib.Path | bytes | BinaryIO | None
    flow_action: Literal[FlowActionType.DATA_EXCHANGE, FlowActionType.NAVIGATE] | None
    navigate_screen: str | None
    icon: FlowButtonIcon | None

    def __init__(
        self,
        *,
        text: str,
        flow_id: str | None = None,
        flow_name: str | None = None,
        flow_json: FlowJSON
        | dict
        | str
        | pathlib.Path
        | bytes
        | BinaryIO
        | None = None,
        flow_action: (
            Literal[FlowActionType.DATA_EXCHANGE, FlowActionType.NAVIGATE] | None
        ) = None,
        navigate_screen: str | None = None,
        icon: FlowButtonIcon | None = None,
    ):
        self.text = text
        self.flow_id = flow_id
        self.flow_name = flow_name
        self.flow_json = flow_json
        self.flow_action = flow_action
        self.navigate_screen = navigate_screen
        self.icon = icon

    def __repr__(self):
        return (
            f"FlowButton(text={self.text!r}, flow_id={self.flow_id!r}, "
            f"flow_name={self.flow_name!r}, flow_json={self.flow_json!r}, "
            f"flow_action={self.flow_action!r}, navigate_screen={self.navigate_screen!r}, "
            f"icon={self.icon!r})"
        )

    def to_dict(self) -> dict:
        return {
            k: v
            for k, v in {
                "type": self.type.value,
                "text": self.text,
                "flow_id": self.flow_id,
                "flow_name": self.flow_name,
                "flow_json": helpers.resolve_flow_json_param(self.flow_json)
                if self.flow_json
                else None,
                "flow_action": self.flow_action.value if self.flow_action else None,
                "navigate_screen": self.navigate_screen,
                "icon": self.icon.value if self.icon else None,
            }.items()
            if v is not None
        }

    @classmethod
    def from_dict(cls, data: dict) -> FlowButton:
        """
        Create a FlowButton from a dictionary representation.
        """
        return cls(
            text=data["text"],
            flow_id=data.get("flow_id"),
            flow_name=data.get("flow_name"),
            flow_json=data.get("flow_json"),
            flow_action=FlowActionType(data["flow_action"])
            if "flow_action" in data
            else None,
            navigate_screen=data.get("navigate_screen"),
            icon=FlowButtonIcon(data["icon"]) if "icon" in data else None,
        )

    class Params(TemplateBaseComponent.Params):
        def __init__(
            self,
            *,
            index: int,
            flow_token: str | None = None,
            flow_action_data: dict | None = None,
        ) -> None:
            """
            Fill the parameters for the Flow button component.

            Args:
                flow_token: optional, default is ``unused``.
                flow_action_data: Optional data to be passed to the first screen.
                index: Indicates order in which button should appear, if the template uses multiple buttons. Buttons are zero-indexed, so setting value to 0 will cause the button to appear first, and another button with an index of 1 will appear next, etc.
            """
            self.flow_token = flow_token
            self.flow_action_data = flow_action_data
            self.index = index

        def to_dict(self) -> dict:
            return {
                "type": ParamType.BUTTON.value,
                "sub_type": ComponentType.FLOW.value,
                "index": self.index,
                "parameters": [
                    {
                        "type": ParamType.ACTION.value,
                        ParamType.ACTION.value: {
                            "flow_token": self.flow_token,
                            "flow_action_data": self.flow_action_data,
                        },
                    }
                ],
            }

    def params(
        self,
        *,
        index: int,
        flow_token: str | None = None,
        flow_action_data: dict | None = None,
    ) -> Params:
        """
        Fill the parameters for the Flow button component.

        Args:
            index: Indicates order in which button should appear, if the template uses multiple buttons. Buttons are zero-indexed, so setting value to 0 will cause the button to appear first, and another button with an index of 1 will appear next, etc.
            flow_token: Optional token to be passed to the Flow.
            flow_action_data: Optional data to be passed to the first screen.

        Returns:
            An instance of Params containing the parameters for the Flow button.
        """
        return self.Params(
            index=index, flow_token=flow_token, flow_action_data=flow_action_data
        )


@dataclasses.dataclass(kw_only=True, slots=True)
class PhoneNumberButton(_DoesNotSupportParams, BaseButtonComponent):
    """
    Phone number buttons call the specified business phone number when tapped by the app user. Templates are limited to one phone number button.

    - Note that some countries have special phone numbers that have leading zeros after the country calling code (e.g., +55-0-955-585-95436). If you assign one of these numbers to the button, the leading zero will be stripped from the number. If your number will not work without the leading zero, assign an alternate number to the button, or add the number as message body text.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#phone-number-buttons>`_.

    Example:

        >>> phone_button = PhoneNumberButton(text="Call Us", phone_number="+1234567890")

    Attributes:
        text: Button label text. 25 characters maximum.
        phone_number: Alphanumeric string. Business phone number to be called when the user taps the button.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.PHONE_NUMBER,
        init=False,
        repr=False,
    )
    text: str
    phone_number: str


@dataclasses.dataclass(kw_only=True, slots=True)
class VoiceCallButton(_DoesNotSupportParams, BaseButtonComponent):
    """
    Voice call button initiates a WhatsApp voice call to the business. Templates are limited to one voice call button.

    Example:

        >>> voice_call_button = VoiceCallButton(text="Call Us On WhatsApp")

    Attributes:
        text: Button label text. 25 characters maximum.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.VOICE_CALL,
        init=False,
        repr=False,
    )
    text: str


@dataclasses.dataclass(kw_only=True, slots=True)
class QuickReplyButton(BaseButtonComponent):
    """
    Quick reply buttons are custom text-only buttons that immediately message you with the specified text string when tapped by the app user. A common use case-case is a button that allows your customer to easily opt-out of any marketing messages.

    - When this button is tapped, you will receive a :class:`~pywa.types.callback.CallbackButton` update with the text you specified in the button and the data you provided in the button parameters (You can use :attr:`~pywa.types.callback.CallbackButton.is_quick_reply` to check if the update is a quick reply button).
    - Templates are limited to 10 quick reply buttons. If using quick reply buttons with other buttons, buttons must be organized into two groups: quick reply buttons and non-quick reply buttons. If grouped incorrectly, the API will return an error indicating an invalid combination.

    - Examples of valid groupings:
        - Quick Reply, Quick Reply
        - Quick Reply, Quick Reply, URL, Phone
        - URL, Phone, Quick Reply, Quick Reply

    - Examples of invalid groupings:
        - Quick Reply, URL, Quick Reply
        - URL, Quick Reply, URL

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#quick-reply-buttons>`_.

    Example:

        >>> quick_reply_button = QuickReplyButton(text="Yes, I want to subscribe!")
        >>> quick_reply_button.params(callback_data="subscribe_yes", index=0)

    Attributes:
        text: Button label text. 25 characters maximum.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.QUICK_REPLY,
        init=False,
        repr=False,
    )
    text: str

    class Params(TemplateBaseComponent.Params):
        def __init__(self, *, callback_data: str | CallbackData, index: int):
            """
            Fill the parameters for the quick reply button component.

            Args:
                callback_data: The data to send when the user clicks on the button (up to 256 characters, for complex data
                 You can use :class:`CallbackData`).
            """
            self.callback_data = callback_data
            self.index = index

        def to_dict(self) -> dict:
            return {
                "type": ParamType.BUTTON.value,
                "sub_type": ComponentType.QUICK_REPLY.value,
                "index": self.index,
                "parameters": [
                    {
                        "type": ParamType.PAYLOAD.value,
                        ParamType.PAYLOAD.value: helpers.resolve_callback_data(
                            self.callback_data
                        ),
                    }
                ],
            }

    def params(self, *, callback_data: str | CallbackData, index: int) -> Params:
        """
        Fill the parameters for the quick reply button component.

        Args:
            callback_data: The data to send when the user clicks on the button (up to 256 characters, for complex data
             You can use :class:`CallbackData`).
            index: Indicates order in which button should appear, if the template uses multiple buttons. Buttons are zero-indexed, so setting value to 0 will cause the button to appear first, and another button with an index of 1 will appear next, etc.

        Returns:
            An instance of Params containing the callback data and index.
        """
        return self.Params(callback_data=callback_data, index=index)


@dataclasses.dataclass(kw_only=True, slots=True)
class AppDeepLink:
    """
    Track app conversions (Marketing Messages Lite API only)

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/marketing-messages-lite-api/guides/deep-links>`_.

    Attributes:
        meta_app_id: Your Meta app ID.
        android_deep_link: `Android deep link URI <https://developer.android.com/training/app-links/deep-linking>`_. The WhatsApp client will attempt to load this URI if the WhatsApp user taps the button on an Android device.
        android_fallback_playstore_url: Enter the Android fallback URL, such as your app's Google Play Store page, to redirect users if the deep link cannot be opened.
    """

    meta_app_id: int
    android_deep_link: str
    android_fallback_playstore_url: str | None = None

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> AppDeepLink:
        return cls(
            meta_app_id=data["meta_app_id"],
            android_deep_link=data["android_deep_link"],
            android_fallback_playstore_url=data.get("android_fallback_playstore_url"),
        )


class URLButton(BaseButtonComponent):
    """
    URL buttons load the specified URL in the device's default web browser when tapped by the app user. Templates are limited to two URL buttons.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#url-buttons>`_.

    Example:

        >>> url_button = URLButton(text="Visit Website", url="https://website.com?ref={{1}}", example="https://website.com?ref=template")
        >>> url_button.params(url_variable="example_variable", index=0)

    Attributes:
        text: Button label text. 25 characters maximum.
        url: URL of website that loads in the device's default mobile web browser when the button is tapped by the app user. Supports 1 variable, appended to the end of the URL string. Maximum 2000 characters.
        example: Example URL to be used in the template. Maximum 2000 characters.
        app_deep_link: Optional `app deep link <https://developers.facebook.com/docs/whatsapp/marketing-messages-lite-api/guides/deep-links>`_ to track conversions (Marketing Messages Lite API only).
    """

    type = ComponentType.URL
    text: str
    url: str
    example: str | None
    app_deep_link: AppDeepLink | None = None

    def __init__(
        self,
        *,
        text: str,
        url: str,
        example: str | None = None,
        app_deep_link: AppDeepLink | None = None,
    ):
        self.text = text
        self.url = url
        self.example = example
        self.app_deep_link = app_deep_link

    def to_dict(self) -> dict:
        data = {
            "type": self.type.value,
            "text": self.text,
            "url": self.url,
        }
        if self.example:
            data["example"] = [self.example]
        if self.app_deep_link:
            data["app_deep_link"] = self.app_deep_link.to_dict()
        return data

    def __repr__(self):
        return f"URLButton(text={self.text!r}, url={self.url!r}, example={self.example!r}, app_deep_link={self.app_deep_link!r})"

    @classmethod
    def from_dict(cls, data: dict) -> URLButton:
        return cls(
            text=data["text"],
            url=data["url"],
            example=data["example"][0] if "example" in data else None,
            app_deep_link=AppDeepLink.from_dict(data["app_deep_link"])
            if "app_deep_link" in data
            else None,
        )

    class Params(TemplateBaseComponent.Params):
        def __init__(self, *, url_variable: str, index: int):
            """
            Fill the parameters for the URL button component.

            Args:
                url_variable: The variable to be appended to the end of the URL string. Maximum 2000 characters.
                index: Indicates order in which button should appear, if the template uses multiple buttons. Buttons are zero-indexed, so setting value to 0 will cause the button to appear first, and another button with an index of 1 will appear next, etc.
            """
            self.url_variable = url_variable
            self.index = index

        def to_dict(self) -> dict:
            return {
                "type": ParamType.BUTTON.value,
                "sub_type": ComponentType.URL.value,
                "index": self.index,
                "parameters": [
                    {
                        "type": ParamType.TEXT.value,
                        ParamType.TEXT.value: self.url_variable,
                    }
                ],
            }

    def params(self, *, url_variable: str, index: int) -> Params:
        """
        Fill the parameters for the URL button component.

        Args:
            url_variable: The variable to be appended to the end of the URL string. Maximum 2000 characters.
            index: Indicates order in which button should appear, if the template uses multiple buttons. Buttons are zero-indexed, so setting value to 0 will cause the button to appear first, and another button with an index of 1 will appear next, etc.

        Returns:
            An instance of Params containing the URL variable and index.
        """
        return self.Params(url_variable=url_variable, index=index)


@dataclasses.dataclass(kw_only=True, slots=True)
class CatalogButton(BaseButtonComponent):
    """
    Catalog templates are marketing templates that allow you to showcase your product catalog entirely within WhatsApp. Catalog templates display a product thumbnail header image of your choice and custom body text, along with a fixed text header and fixed text sub-header.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/catalog-templates>`_.

    Example:

        >>> catalog_button = CatalogButton(text="View Products")
        >>> catalog_button.params(thumbnail_product_sku="SKU12345", index=0)

    Attributes:
        text: Button label text. 25 characters maximum.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.CATALOG,
        init=False,
        repr=False,
    )
    text: str

    class Params(TemplateBaseComponent.Params):
        def __init__(self, *, thumbnail_product_sku: str | None = None, index: int):
            """
            Fill the parameters for the catalog button component.

            Args:
                thumbnail_product_sku: The SKU of the product to be used as the thumbnail header image. If omitted, the product image of the first item in your catalog will be used.
                index: Indicates order in which button should appear, if the template uses multiple buttons. Buttons are zero-indexed, so setting value to 0 will cause the button to appear first, and another button with an index of 1 will appear next, etc.
            """
            self.thumbnail_product_sku = thumbnail_product_sku
            self.index = index

        def to_dict(self) -> dict:
            return {
                "type": ParamType.BUTTON.value,
                "sub_type": ComponentType.CATALOG.value,
                "index": self.index,
                **(
                    {
                        "parameters": [
                            {
                                "type": ParamType.ACTION.value,
                                ParamType.ACTION.value: {
                                    "thumbnail_product_retailer_id": self.thumbnail_product_sku,
                                },
                            }
                        ],
                    }
                    if self.thumbnail_product_sku
                    else {}
                ),
            }

    def params(self, *, thumbnail_product_sku: str | None = None, index: int) -> Params:
        """
        Fill the parameters for the catalog button component.

        Args:
            thumbnail_product_sku: The SKU of the product to be used as the thumbnail header image. If omitted, the product image of the first item in your catalog will be used.
            index: Indicates order in which button should appear, if the template uses multiple buttons. Buttons are zero-indexed, so setting value to 0 will cause the button to appear first, and another button with an index of 1 will appear next, etc.

        Returns:
            An instance of Params containing the thumbnail product SKU and index.
        """
        return self.Params(thumbnail_product_sku=thumbnail_product_sku, index=index)


@dataclasses.dataclass(kw_only=True, slots=True)
class MPMButton(BaseButtonComponent):
    """
    Multi-product message (MPM) buttons are special, non-customizable buttons that, when tapped, display up to 30 products from your ecommerce catalog, organized in up to 10 sections, in a single message.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/mpm-templates>`_.

    Example:

        >>> from pywa.types import ProductsSection, Product
        >>> mpm_button = MPMButton(text="View Products")
        >>> mpm_button.params(
        ...     thumbnail_product_sku="SKU12345",
        ...     index=0,
        ...     product_sections=[
        ...        ProductsSection(
        ...            title="Section 1",
        ...            products=[
        ...                Product(sku="SKU12345", name="Product 1", price=100.0),
        ...                Product(sku="SKU12346", name="Product 2", price=150.0),
        ...            ]
        ...        ),
        ...        ProductsSection(
        ...            title="Section 2",
        ...            products=[
        ...                Product(sku="SKU12347", name="Product 3", price=200.0),
        ...                Product(sku="SKU12348", name="Product 4", price=250.0),
        ...            ]
        ...        ),
        ...     ],
        ... )

    Attributes:
        text: Button label text. 25 characters maximum.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.MPM,
        init=False,
        repr=False,
    )
    text: str

    class Params(TemplateBaseComponent.Params):
        def __init__(
            self,
            *,
            product_sections: list[ProductsSection],
            thumbnail_product_sku: str,
            index: int,
        ):
            """
            Fill the parameters for the multi-product message button component.

            Args:
                product_sections: A list of product sections, each containing a list of products to be displayed in the button. Each section can contain up to 30 products, and there can be up to 10 sections in total.
                thumbnail_product_sku: The SKU of the product to be used as the thumbnail header image.
                index: Indicates order in which button should appear, if the template uses multiple buttons. Buttons are zero-indexed, so setting value to 0 will cause the button to appear first, and another button with an index of 1 will appear next, etc.
            """
            self.product_sections = product_sections
            self.thumbnail_product_sku = thumbnail_product_sku
            self.index = index

        def to_dict(self) -> dict:
            return {
                "type": ParamType.BUTTON.value,
                "sub_type": ComponentType.MPM.value,
                "index": self.index,
                "parameters": {
                    "type": ParamType.ACTION.value,
                    ParamType.ACTION.value: {
                        "thumbnail_product_retailer_id": self.thumbnail_product_sku,
                        "sections": [s.to_dict() for s in self.product_sections],
                    },
                },
            }

    def params(
        self,
        *,
        product_sections: list[ProductsSection],
        thumbnail_product_sku: str,
        index: int,
    ) -> Params:
        """
        Fill the parameters for the multi-product message button component.

        Args:
            product_sections: A list of product sections, each containing a list of products to be displayed in the button. Each section can contain up to 30 products, and there can be up to 10 sections in total.
            thumbnail_product_sku: The SKU of the product to be used as the thumbnail header image.
            index: Indicates order in which button should appear, if the template uses multiple buttons. Buttons are zero-indexed, so setting value to 0 will cause the button to appear first, and another button with an index of 1 will appear next, etc.

        Returns:
            An instance of Params containing the product sections, thumbnail product SKU, and index.
        """
        return self.Params(
            product_sections=product_sections,
            thumbnail_product_sku=thumbnail_product_sku,
            index=index,
        )


@dataclasses.dataclass(kw_only=True, slots=True)
class SPMButton(_DoesNotSupportParams, BaseButtonComponent):
    """
    Single-product message (SPM) buttons are special, non-customizable buttons that can be mapped to a product in your product catalog. When tapped, they load details about the product, which it pulls from your catalog. Users can then add the product to their cart and place an order.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/spm-templates>`_.

    Example:

        >>> header_product = HeaderProduct()
        >>> spm_button = SPMButton(text="View Product")

    Attributes:
        text: Button label text. 25 characters maximum.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.SPM,
        init=False,
        repr=False,
    )
    text: str


@dataclasses.dataclass(kw_only=True, slots=True)
class CallPermissionRequestButton(_DoesNotSupportParams, BaseButtonComponent):
    """
    Call permissions request buttons are used to request call permissions from the user. When tapped, they open a dialog that allows the user to grant or deny call permissions.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/user-call-permissions#create-and-send-call-permission-request-template-messages>`_.

    Example:

        >>> call_permission_button = CallPermissionRequestButton(text="Request Call Permission")
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.CALL_PERMISSION_REQUEST,
        init=False,
        repr=False,
    )


class OtpType(utils.StrEnum):
    """
    The type of the one-time password or code button.

    Attributes:
        COPY_CODE: Copy code button copies the one-time password or code to the user's clipboard.
        ONE_TAP: One-tap autofill button automatically loads and passes your app the one-time password or code.
        ZERO_TAP: Zero-tap autofill button automatically loads and passes your app the one-time password or code
    """

    COPY_CODE = "COPY_CODE"
    ONE_TAP = "ONE_TAP"
    ZERO_TAP = "ZERO_TAP"

    UNKNOWN = "UNKNOWN"


@dataclasses.dataclass(kw_only=True, slots=True)
class OTPSupportedApp:
    """
    Represents an android app that will receive the one-time password.

    - Read more about `Supported Apps <https://developers.facebook.com/docs/whatsapp/business-management-api/authentication-templates/autofill-button-authentication-templates#supported-apps>`_.

    Example:

        >>> supported_app = OTPSupportedApp(
        ...     package_name="com.example.myapp",
        ...     signature_hash="12345678901"
        ... )

    Attributes:
        package_name: Your Android app's package name. Maximum 224 characters.
        signature_hash: Your app signing key hash. See `App Signing Key Hash <https://developers.facebook.com/docs/whatsapp/business-management-api/authentication-templates/autofill-button-authentication-templates#app-signing-key-hash>`_. Must be exactly 11 characters.
    """

    package_name: str
    signature_hash: str


class _BaseOTPButtonParams:
    """
    Base class for one-time password (OTP) button parameters.
    """

    class Params(TemplateBaseComponent.Params):
        """
        Base class for button parameters.
        This class is not meant to be instantiated directly.
        """

        def __init__(self, otp: str):
            """
            Initialize the base button parameters.

            Args:
                otp: The one-time password or code to be used in the button. Maximum 15 characters.
            """
            self.otp = otp

        def to_dict(self) -> dict:
            return {
                "type": ParamType.BUTTON.value,
                "sub_type": ComponentType.URL,
                "index": 0,
                "parameters": [
                    {
                        "type": ParamType.TEXT.value,
                        ParamType.TEXT.value: self.otp,
                    }
                ],
            }

    def params(self, otp: str) -> Params:
        """
        Fill the parameters for the button component.

        Args:
            otp: The one-time password or code to be used in the button. Maximum 15 characters.

        Returns:
            An instance of Params containing the OTP.
        """
        return self.Params(otp=otp)


@dataclasses.dataclass(kw_only=True, slots=True)
class BaseOTPButton(_BaseOTPButtonParams, BaseButtonComponent, abc.ABC):
    """
    Base class for one-time password (OTP) button components.
    This class is not meant to be instantiated directly.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.OTP,
        init=False,
        repr=False,
    )
    otp_type: OtpType
    text: str | None = None


@dataclasses.dataclass(kw_only=True, slots=True)
class OneTapOTPButton(BaseOTPButton):
    """
    One-tap autofill authentication templates allow you to send a one-time password or code along with an one-tap autofill button to your users. When a WhatsApp user taps the autofill button, the WhatsApp client triggers an activity which opens your app and delivers it the password or code.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/authentication-templates/autofill-button-authentication-templates>`_.
    - Read more about `Authentication Templates <https://developers.facebook.com/docs/whatsapp/business-management-api/authentication-templates>`_.

    Example:

        >>> one_tap_button = OneTapOTPButton(
        ...     text="Autofill Code",
        ...     autofill_text="Autofill",
        ...     supported_apps=[
        ...         OTPSupportedApp(
        ...             package_name="com.example.myapp",
        ...             signature_hash="12345678901"
        ...         )
        ...     ]
        ... )
        >>> one_tap_button.params(otp="123456")

    Attributes:
        text: Copy code button label text. If omitted, the text will default to a pre-set value localized to the template's language. For example, ``Copy Code`` for English (US). Maximum 25 characters.
        autofill_text: One-tap autofill button label text. If omitted, the autofill text will default to a pre-set value, localized to the template's language. For example, ``Autofill`` for English (US). Maximum 25 characters.
        supported_apps: The supported_apps array allows you define pairs of app package names and signing key hashes for up to 5 apps. This can be useful if you have different app builds and want each of them to be able to initiate the handshake. Read more about `Supported Apps <https://developers.facebook.com/docs/whatsapp/business-management-api/authentication-templates/autofill-button-authentication-templates#supported-apps>`_.
    """

    otp_type: OtpType = dataclasses.field(
        default=OtpType.ONE_TAP,
        init=False,
        repr=False,
    )
    autofill_text: str | None = None
    supported_apps: list[OTPSupportedApp]


@dataclasses.dataclass(kw_only=True, slots=True)
class ZeroTapOTPButton(BaseOTPButton):
    """
    Zero-tap authentication templates allow your users to receive one-time passwords or codes via WhatsApp without having to leave your app.

    When a user in your app requests a password or code and you deliver it using a zero-tap authentication template, the WhatsApp client simply broadcasts the included password or code and your app can capture it immediately with a broadcast receiver.
    From your user's perspective, they request a password or code in your app and it appears in your app automatically. If your app user happens to check the message in the WhatsApp client, they will only see a message displaying the default fixed text: < code > is your verification code.
    Like one-tap autofill button authentication templates, when the WhatsApp client receives the template message containing the user's password or code, we perform a series of eligibility checks. If the message fails this check and we are unable to broadcast the password or code, the message will display either a one-tap autofill button or a copy code button. For this reason, when you create a zero-tap authentication template, you must include a one-tap autofill and copy code button in your post body payload, even if the user may never see one of these buttons.

    - Zero-tap is only supported on Android. If you send a zero-tap authentication template to a WhatsApp user who is using a non-Android device, the WhatsApp client will display a copy code button instead.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/authentication-templates/zero-tap-authentication-templates>`_.
    - Read more about `Authentication Templates <https://developers.facebook.com/docs/whatsapp/business-management-api/authentication-templates>`_.

    Example:

        >>> zero_tap_button = ZeroTapOTPButton(
        ...     text="Autofill Code",
        ...     autofill_text="Autofill",
        ...     zero_tap_terms_accepted=True,
        ...     supported_apps=[
        ...         OTPSupportedApp(
        ...             package_name="com.example.myapp",
        ...             signature_hash="12345678901"
        ...         )
        ...    ]
        ... )
        >>> zero_tap_button.params(otp="123456")

    Attributes:
        text: Copy code button label text. If omitted, the text will default to a pre-set value localized to the template's language. For example, ``Copy Code`` for English (US). Maximum 25 characters.
        autofill_text: One-tap autofill button label text. If omitted, the autofill text will default to a pre-set value, localized to the template's language. For example, ``Autofill`` for English (US). Maximum 25 characters.
        zero_tap_terms_accepted: Set to ``True`` to indicate that you understand that your use of zero-tap authentication is subject to the WhatsApp Business Terms of Service, and that it's your responsibility to ensure your customers expect that the code will be automatically filled in on their behalf when they choose to receive the zero-tap code through WhatsApp. If set to ``False``, the template will **not** be created as you need to accept zero-tap terms before creating zero-tap enabled message templates.
        supported_apps: The supported_apps array allows you define pairs of app package names and signing key hashes for up to 5 apps. This can be useful if you have different app builds and want each of them to be able to initiate the handshake. Read more about `Supported Apps <https://developers.facebook.com/docs/whatsapp/business-management-api/authentication-templates/zero-tap-authentication-templates#supported-apps>`_.
    """

    otp_type: OtpType = dataclasses.field(
        default=OtpType.ZERO_TAP,
        init=False,
        repr=False,
    )
    autofill_text: str | None = None
    zero_tap_terms_accepted: bool
    supported_apps: list[OTPSupportedApp]


@dataclasses.dataclass(kw_only=True, slots=True)
class CopyCodeOTPButton(BaseOTPButton):
    """
    Copy code authentication templates allow you to send a one-time password or code along with a copy code button to your users. When a WhatsApp user taps the copy code button, the WhatsApp client copies the password or code to the device's clipboard. The user can then switch to your app and paste the password or code into your app.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/authentication-templates/copy-code-button-authentication-templates>`_.
    - Read more about `Authentication Templates <https://developers.facebook.com/docs/whatsapp/business-management-api/authentication-templates>`_.

    Example:

        >>> copy_code_button = CopyCodeOTPButton(text="Copy Code")
        >>> copy_code_button.params(otp="123456")

    Attributes:
        text: Copy code button label text. If omitted, the text will default to a pre-set value localized to the template's language. For example, ``Copy Code`` for English (US). Maximum 25 characters.
    """

    otp_type: OtpType = dataclasses.field(
        default=OtpType.COPY_CODE,
        init=False,
        repr=False,
    )


# ========== LIMITED TIME OFFER ==========


class LimitedTimeOffer(TemplateBaseComponent):
    """
    Limited-time offer templates allow you to display expiration dates and running countdown timers for offer codes in template messages, making it easy for you to communicate time-bound offers and drive customer engagement.

    - Only templates categorized as ``MARKETING`` are supported.
    - :class:`FooterText` components are not supported.
    - Users who view a limited-time offer template message using that WhatsApp web app or desktop app will not see the offer, but will instead see a message indicating that they have received a message but that it's not supported in the client they are using.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/limited-time-offer-templates>`_.

    Example:

        >>> limited_time_offer = LimitedTimeOffer(
        ...     text="Limited Time Offer!",
        ...     has_expiration=True
        ... )
        >>> limited_time_offer.params(expiration_time=datetime.datetime.now() + datetime.timedelta(days=7))

    Attributes:
        text: Offer details text. Maximum 16 characters.
        has_expiration: Set to ``True`` to have the `offer expiration details <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/limited-time-offer-templates#offer-expiration-details>`_ appear in the delivered message.
    """

    type = ComponentType.LIMITED_TIME_OFFER
    text: str
    has_expiration: bool | None = None

    def __init__(self, *, text: str, has_expiration: bool | None = None):
        self.text = text
        self.has_expiration = has_expiration

    def __repr__(self):
        return f"LimitedTimeOffer(text={self.text!r}, has_expiration={self.has_expiration!r})"

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "limited_time_offer": {
                "text": self.text,
                **(
                    {"has_expiration": self.has_expiration}
                    if self.has_expiration is not None
                    else {}
                ),
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> LimitedTimeOffer:
        return cls(
            text=data["limited_time_offer"]["text"],
            has_expiration=data["limited_time_offer"].get("has_expiration", None),
        )

    class Params(TemplateBaseComponent.Params):
        def __init__(self, *, expiration_time: datetime.datetime | None = None):
            """
            Fill the parameters for the limited-time offer component.

            Args:
                expiration_time: The time when the offer expires. This is used to calculate the countdown timer.
            """
            self.expiration_time = expiration_time

        def to_dict(self) -> dict:
            return {
                "type": ComponentType.LIMITED_TIME_OFFER.value,
                "parameters": [
                    {
                        "type": ParamType.LIMITED_TIME_OFFER.value,
                        ParamType.LIMITED_TIME_OFFER.lower(): {
                            "expiration_time_ms": int(self.expiration_time.timestamp()),
                        },
                    }
                ],
            }

    def params(self, *, expiration_time: datetime.datetime) -> Params:
        """
        Fill the parameters for the limited-time offer component.

        Args:
            expiration_time: The time when the offer expires. This is used to calculate the countdown timer.

        Returns:
            An instance of Params containing the expiration time.
        """
        return self.Params(expiration_time=expiration_time)


# ========== CAROUSEL ==========


@dataclasses.dataclass(kw_only=True, slots=True)
class Carousel(TemplateBaseComponent):
    """
    Media card carousel templates allow you to send a single text message accompanied by a set of up to 10 media cards in a horizontally scrollable view.
    Read more about `Media Card Carousel Templates <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/media-card-carousel-templates>`_.

    Product card carousel templates allow you to send a single text message accompanied by a set of up to 10 product cards in a horizontally scrollable view.
    Read more about `Product Card Carousel Templates <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/product-card-carousel-templates>`_.

    - All cards defined on a template must have the same components.

    Example:

        >>> carousel = Carousel(cards=[
        ...     card1 := CarouselCard(
        ...         components=[
        ...             hi1 := HeaderImage(example="https://example.com/card1.jpg"),
        ...             qr1 := QuickReplyButton(text="Unsubscribe"),
        ...             u1 := URLButton(text="Website", url="https://website.com?ref={{1}}", example="https://website.com?ref=card1"),
        ...         ]
        ...     ),
        ...     card2 := CarouselCard(
        ...         components=[
        ...             hi2 := HeaderImage(example="https://example.com/card2.jpg"),
        ...             qr2 := QuickReplyButton(text="Unsubscribe"),
        ...             u2 := URLButton(text="Website", url="https://website.com?ref={{1}}", example="https://website.com?ref=card2"),
        ...         ]
        ...     ),
        ... ])

        >>> carousel.params(cards=[
        ...     card1.params(
        ...         index=0,
        ...         params=[
        ...             hi1.params(image="https://cdn.com/card1.jpg"),
        ...             qr1.params(callback_data="unsubscribe_card1", index=0),
        ...             u1.params(url_variable="card1", index=0),
        ...         ],
        ...     ),
        ...     card2.params(
        ...         index=1,
        ...         params=[
        ...             hi2.params(image="https://cdn.com/card2.jpg"),
        ...             qr2.params(callback_data="unsubscribe_card2", index=0),
        ...             u2.params(url_variable="card2", index=0),
        ...         ],
        ...     ),
        ... ])


    Attributes:
        cards: A list of :class:`CarouselMediaCard` objects, each representing a media card in the carousel.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.CAROUSEL,
        init=False,
        repr=False,
    )
    cards: list[CarouselCard]

    @classmethod
    def from_dict(cls, data: dict) -> Carousel:
        return cls(
            cards=[
                CarouselCard(
                    components=[
                        _parse_component(card_component)
                        for card_component in card["components"]
                    ]
                )
                for card in data["cards"]
            ]
        )

    class Params(TemplateBaseComponent.Params):
        cards: list[CarouselCard.Params]

        def __init__(self, *, cards: list[CarouselCard.Params]):
            """
            Fill the parameters for the carousel component.

            Args:
                cards: A list of card parameters, each representing a media card in the carousel.
            """
            self.cards = cards

        def to_dict(self) -> dict:
            return {
                "type": ParamType.CAROUSEL.value,
                "cards": [card.to_dict() for card in self.cards],
            }

        def clear_media_cache(self):
            """
            Clear the media cache for the params in the carousel (if you using the same params object more than 30 days, the media ID will be expired, so you need to reupload the media).
            """
            for card in self.cards:
                card.clear_media_cache()

    def params(self, *, cards: list[CarouselCard.Params]) -> Carousel.Params:
        """
        Fill the parameters for the carousel component.

        Args:
            cards: A list of card parameters, each representing a media card in the carousel.

        Returns:
            An instance of Params containing the parameters for the carousel.
        """
        return self.Params(cards=cards)


@dataclasses.dataclass(kw_only=True, slots=True)
class CarouselCard:
    """
    Represents a card in a carousel template.

    Example:

        >>> carousel_media_card = CarouselCard(
        ...     components=[
        ...         HeaderImage(example="https://example.com/image.jpg"),
        ...         QuickReplyButton(text="Unsubscribe"),
        ...     ]
        ... )
        >>> carousel_media_card.params(
        ...     index=0,
        ...     params=[
        ...         HeaderImage.Params(image="https://cdn.com/image.jpg"),
        ...         QuickReplyButton.Params(callback_data="unsubscribe", index=0),
        ...     ],
        ... )

    Attributes:
        components: A list of components that make up the card, such as header, body, footer, and buttons.
    """

    components: list[TemplateBaseComponent | dict]

    class Params(TemplateBaseComponent.Params):
        def __init__(self, *, params: list[TemplateBaseComponent.Params], index: int):
            """
            Initialize the parameters for the carousel card.

            Args:
                params: A list of parameters for the components in the media card.
                index: The index of the media card in the carousel (0-based).
            """
            self.params = params
            self.index = index

        def to_dict(self) -> dict:
            return {
                "card_index": self.index,
                "components": [param.to_dict() for param in self.params],
            }

        def clear_media_cache(self):
            """
            Clear the media cache for the params in the card (if you using the same params object more than 30 days, the media ID will be expired, so you need to reupload the media).
            """
            for param in self.params:
                if hasattr(param, "clear_media_cache"):
                    param.clear_media_cache()

    def params(
        self, *, params: list[TemplateBaseComponent.Params], index: int
    ) -> Params:
        """
        Fill the parameters for the carousel card.

        Args:
            params: A list of parameters for the components in the media card.
            index: The index of the media card in the carousel (0-based).

        Returns:
            An instance of Params containing the parameters for the card.
        """
        return self.Params(params=params, index=index)


# ========== AUTHENTICATION ==========


@dataclasses.dataclass(kw_only=True, slots=True)
class AuthenticationBody(BaseBodyComponent):
    """
    Authentication body component for Authentication templates.

    Example:

        >>> authentication_body = AuthenticationBody(add_security_recommendation=True)
        >>> authentication_body.params(otp="123456")

    Attributes:
        add_security_recommendation: Set to ``True`` if you want the template to include the string `For your security, do not share this code`. Set to ``False`` to exclude the string.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.BODY,
        init=False,
        repr=False,
    )
    add_security_recommendation: bool | None = None

    class Params(TemplateBaseComponent.Params):
        def __init__(self, *, otp: str):
            """
            Fill the parameters for the authentication body component.

            Args:
                otp: The one-time password or code to be used in the body text. Maximum 15 characters.
            """
            self.otp = otp

        def to_dict(self) -> dict:
            return {
                "type": ComponentType.BODY.value,
                "parameters": [
                    {
                        "type": ParamType.TEXT.value,
                        ParamType.TEXT.value: self.otp,
                    }
                ],
            }

    def params(self, *, otp: str) -> Params:
        """
        Fill the parameters for the authentication body component.

        Args:
            otp: The one-time password or code to be used in the body text. Maximum 15 characters.

        Returns:
            An instance of Params containing the OTP.
        """
        return self.Params(otp=otp)


@dataclasses.dataclass(kw_only=True, slots=True)
class AuthenticationFooter(_DoesNotSupportParams, BaseFooterComponent):
    """
    Authentication footer component for Authentication templates.

    Example:

        >>> authentication_footer = AuthenticationFooter(code_expiration_minutes=5)

    Attributes:
        code_expiration_minutes: Indicates the number of minutes the password or code is valid.
         If included, the code expiration warning and this value will be displayed in the delivered message. The button will be disabled in the delivered message the indicated number of minutes from when the message was sent.
         If omitted, the code expiration warning will not be displayed in the delivered message. In addition, the button will be disabled 10 minutes from when the message was sent.
         Minimum 1, maximum 90.
    """

    code_expiration_minutes: int


# ========== TEMPLATE ==========


@dataclasses.dataclass(kw_only=True, slots=True)
class Template:
    """
    Represents a New WhatsApp Template.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates>`_.

    Example::


        from pywa.types.templates import *

        my_template = Template(
            name="my_template",
            language=TemplateLanguage.ENGLISH_US,
            category=TemplateCategory.MARKETING,
            components=[
                HeaderText(text="Welcome to our service!"),
                BodyText(text="Hello {{name}}, thank you for joining us!", name="John"),
                FooterText(text="Best regards, The Team"),
                Buttons(
                    buttons=[
                        QuickReplyButton(text="Get Started"),
                        URLButton(text="Visit Website", url="https://website.com?ref={{1}}")
                    ]
                )
            ],
            parameter_format=ParamFormat.NAMED,
        )

        auth_template = Template(
            name="auth_template",
            language=TemplateLanguage.ENGLISH_US,
            category=TemplateCategory.AUTHENTICATION,
            components=[
                AuthenticationBody(add_security_recommendation=True),
                AuthenticationFooter(code_expiration_minutes=5),
                Buttons(
                    buttons=[
                        OneTapOTPButton(
                            text="Autofill Code",
                            autofill_text="Autofill",
                            supported_apps=[
                                OTPSupportedApp(
                                    package_name="com.example.myapp",
                                    signature_hash="12345678901"
                                )
                            ]
                        ),
                    ]
                )
            ],
        )



    Attributes:
        name: The name of the template (should be unique, maximum 512 characters).
        language: The language of the template (See `Supported Languages <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/supported-languages>`_).
        category: The category of the template (See `Template Categorization <https://developers.facebook.com/docs/whatsapp/updates-to-pricing/new-template-guidelines#template-categorization>`_).
        components: Components that make up the template. Header, BodyText, FooterText, Buttons, Cards, etc. (See `Template Components <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components>`_).
        parameter_format: The type of parameter formatting the :class:`HeaderText` and :class:`BodyText` components of the template will use. Defaults to ``POSITIONAL``.
        message_send_ttl_seconds: The time-to-live (TTL) for the template message in seconds. (See `Time-to-live (TTL) <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates#time-to-live--ttl---customization--defaults--min-max-values--and-compatibility>`_).
    """

    name: str
    language: TemplateLanguage
    category: TemplateCategory
    components: list[TemplateBaseComponent | dict]
    parameter_format: ParamFormat | None = None
    message_send_ttl_seconds: int | None = None

    def to_json(self) -> str:
        """
        Convert the template to a JSON string representation.
        """
        return _template_to_json(self)

    @classmethod
    def from_dict(cls, data: dict) -> Template:
        return cls(
            name=data["name"],
            language=TemplateLanguage(data["language"]),
            category=TemplateCategory(data["category"]),
            components=[
                _parse_component(component) for component in data["components"]
            ],
            parameter_format=ParamFormat(data["parameter_format"])
            if "parameter_format" in data
            else None,
            message_send_ttl_seconds=data.get("message_send_ttl_seconds"),
        )


@dataclasses.dataclass(kw_only=True, slots=True)
class _AuthenticationTemplates(Template):
    """Internal class for upserting authentication templates."""

    language: None = dataclasses.field(
        default=None,
        init=False,
        repr=False,
    )
    category: TemplateCategory = dataclasses.field(
        default=TemplateCategory.AUTHENTICATION,
        init=False,
        repr=False,
    )
    languages: list[TemplateLanguage]
    components: list[AuthenticationBody | AuthenticationFooter | Buttons | dict]


@dataclasses.dataclass(kw_only=True, slots=True)
class _TemplateUpdate(Template):
    name: None = dataclasses.field(
        default=None,
        init=False,
        repr=False,
    )
    language: None = dataclasses.field(
        default=None,
        init=False,
        repr=False,
    )


_comp_types_to_component: dict[ComponentType, type[TemplateBaseComponent]] = {
    ComponentType.HEADER: BaseHeaderComponent,
    ComponentType.BODY: BaseBodyComponent,
    ComponentType.OTP: BaseOTPButton,
    ComponentType.FOOTER: FooterText,
    ComponentType.BUTTONS: Buttons,
    ComponentType.CAROUSEL: Carousel,
    ComponentType.LIMITED_TIME_OFFER: LimitedTimeOffer,
    ComponentType.PHONE_NUMBER: PhoneNumberButton,
    ComponentType.URL: URLButton,
    ComponentType.QUICK_REPLY: QuickReplyButton,
    ComponentType.MPM: MPMButton,
    ComponentType.SPM: SPMButton,
    ComponentType.CATALOG: CatalogButton,
    ComponentType.COPY_CODE: CopyCodeButton,
    ComponentType.FLOW: FlowButton,
    ComponentType.CALL_PERMISSION_REQUEST: CallPermissionRequestButton,
    ComponentType.VOICE_CALL: VoiceCallButton,
}

_header_formats_to_component: dict[HeaderFormatType, type[BaseHeaderComponent]] = {
    HeaderFormatType.TEXT: HeaderText,
    HeaderFormatType.IMAGE: HeaderImage,
    HeaderFormatType.VIDEO: HeaderVideo,
    HeaderFormatType.DOCUMENT: HeaderDocument,
    HeaderFormatType.LOCATION: HeaderLocation,
    HeaderFormatType.PRODUCT: HeaderProduct,
}

_otp_types_to_component: dict[OtpType, type[BaseOTPButton]] = {
    OtpType.COPY_CODE: CopyCodeOTPButton,
    OtpType.ONE_TAP: OneTapOTPButton,
    OtpType.ZERO_TAP: ZeroTapOTPButton,
}


def _parse_component(component: dict) -> TemplateBaseComponent | dict:
    """
    Parse a component dictionary into a BaseComponent object.

    Args:
        component (dict): The component dictionary to parse.

    Returns:
        TemplateBaseComponent: The parsed BaseComponent object.
    """
    component_cls = _comp_types_to_component.get(ComponentType(component["type"]))
    if component_cls is None:
        _logger.warning(
            "Unknown component type: %s. Defaulting to dictionary representation.",
            component["type"],
        )
        return component

    if issubclass(component_cls, BaseHeaderComponent):
        header_format = HeaderFormatType(component["format"])
        header_cls = _header_formats_to_component.get(header_format)
        if header_cls is None:
            _logger.warning(
                "Unknown header format: %s. Defaulting to dictionary representation.",
                component["format"],
            )
            return component
        component_cls = header_cls

    elif issubclass(component_cls, BaseBodyComponent):
        if "add_security_recommendation" in component:
            component_cls = AuthenticationBody
        elif "text" in component:
            component_cls = BodyText
        else:
            _logger.warning(
                "Unknown body component: %s. Defaulting to dictionary representation.",
                component,
            )
            return component

    elif issubclass(component_cls, BaseFooterComponent):
        if "code_expiration_minutes" in component:
            component_cls = AuthenticationFooter
        elif "text" in component:
            component_cls = FooterText
        else:
            _logger.warning(
                "Unknown footer component: %s. Defaulting to dictionary representation.",
                component,
            )
            return component

    elif issubclass(component_cls, BaseOTPButton):
        otp_type = OtpType(component["otp_type"])
        otp_cls = _otp_types_to_component.get(otp_type)
        if otp_cls is None:
            _logger.warning(
                "Unknown OTP type: %s. Defaulting to dictionary representation.",
                component["otp_type"],
            )
            return component
        component_cls = otp_cls

    try:
        return component_cls.from_dict(component)
    except Exception:
        _logger.warning(
            "Failed to parse component: %s. Defaulting to dictionary representation.",
            component,
        )
        return component


class _TemplateJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, "to_dict"):
            return o.to_dict()
        return super().default(o)


def _template_to_json(template: Template | LibraryTemplate) -> str:
    return json.dumps(
        dataclasses.asdict(
            obj=template,
            dict_factory=lambda d: {k: v for (k, v) in d if v is not None},
        ),
        cls=_TemplateJSONEncoder,
        indent=4,
        ensure_ascii=False,
    )


@dataclasses.dataclass(kw_only=True, slots=True)
class TemplateDetails(utils.APIObject):
    """
    Represents the details of an existing WhatsApp Template.

    Attributes:
        id: The unique identifier of the template.
        name: The name of the template.
        status: The status of the template (See `Template Status <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates#template-status>`_).
        category: The category of the template (See `Template Categorization <https://developers.facebook.com/docs/whatsapp/updates-to-pricing/new-template-guidelines#template-categorization>`_).
        language: The language of the template (See `Supported Languages <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/supported-languages>`_).
        components: Components that make up the template. Header, Body, Footer, Buttons, Cards, etc. (See `Template Components <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components>`_).
        parameter_format: The type of parameter formatting the Header and BodyText components of the template will use.
        message_send_ttl_seconds: The time-to-live (TTL) for the template message in seconds (See `Time-to-live (TTL) <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates#time-to-live--ttl---customization--defaults--min-max-values--and-compatibility>`_).
        correct_category: The correct category of the template, if applicable.
        previous_category: The previous category of the template, if applicable.
        rejected_reason: The reason the message template was rejected, if applicable (See `Template Rejected Status <https://developers.facebook.com/docs/whatsapp/updates-to-pricing/new-template-guidelines#rejected-status>`_).
        library_template_name: Template Library name that this template is cloned from, if applicable.
        quality_score: The quality score of the template, if applicable (See `Template Quality Score <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates#template-quality-score>`_).
        cta_url_link_tracking_opted_out: Optional boolean field for opting out/in of link tracking at template level.
        sub_category: The sub-category of the template, if applicable.
    """

    _client: WhatsApp = dataclasses.field(repr=False, hash=False, compare=False)
    id: str
    name: str
    language: TemplateLanguage
    category: TemplateCategory
    status: TemplateStatus
    components: list[TemplateBaseComponent]
    parameter_format: ParamFormat | None
    message_send_ttl_seconds: int | None
    correct_category: TemplateCategory | None
    previous_category: TemplateCategory | None
    rejected_reason: TemplateRejectionReason | None
    library_template_name: str | None
    quality_score: QualityScore | None
    cta_url_link_tracking_opted_out: bool | None
    sub_category: TemplateSubCategory | None

    @classmethod
    def from_dict(cls, data: dict, client: WhatsApp) -> TemplateDetails:
        return TemplateDetails(
            _client=client,
            id=data["id"],
            name=data["name"],
            language=TemplateLanguage(data["language"]),
            status=TemplateStatus(data["status"]),
            category=TemplateCategory(data["category"]),
            previous_category=TemplateCategory(data["previous_category"])
            if "previous_category" in data
            else None,
            correct_category=TemplateCategory(data["correct_category"])
            if "correct_category" in data
            else None,
            parameter_format=ParamFormat(data["parameter_format"]),
            rejected_reason=TemplateRejectionReason(data["rejected_reason"])
            if "rejected_reason" in data
            else None,
            library_template_name=data.get("library_template_name"),
            message_send_ttl_seconds=int(data["message_send_ttl_seconds"])
            if "message_send_ttl_seconds" in data
            else None,
            components=[
                _parse_component(component) for component in data["components"]
            ],
            quality_score=QualityScore.from_dict(data=data["quality_score"])
            if "quality_score" in data
            else None,
            cta_url_link_tracking_opted_out=data.get("cta_url_link_tracking_opted_out"),
            sub_category=TemplateSubCategory(data["sub_category"])
            if "sub_category" in data
            else None,
        )

    def to_json(self) -> str:
        """
        Convert the template to a JSON string representation.
        """
        return _template_to_json(self)

    def delete(self) -> SuccessResult:
        """
        Delete this template

        - If you delete a template that has been sent in a template message but has yet to be delivered (e.g. because the customer's phone is turned off), the template's status will be set to ``PENDING_DELETION`` and we will attempt to deliver the message for 30 days. After this time you will receive a "Structure Unavailable" error and the customer will not receive the message.
        - Names of an approved template that has been deleted cannot be used again for 30 days.
        """
        return self._client.delete_template(
            template_name=self.name, template_id=self.id
        )

    def update(
        self,
        *,
        new_category: TemplateCategory | None = None,
        new_components: list[TemplateBaseComponent] | None = None,
        new_message_send_ttl_seconds: int | None = None,
        new_parameter_format: ParamFormat | None = None,
    ) -> UpdatedTemplate:
        """
        Update this template.

        - The template object will be updated in memory after a successful update.
        - Only templates with an ``APPROVED``, ``REJECTED``, or ``PAUSED`` status can be edited.
        - You cannot edit the category of an approved template.
        - Approved templates can be edited up to 10 times in a 30 day window, or 1 time in a 24 hour window. Rejected or paused templates can be edited an unlimited number of times.
        - After editing an approved or paused template, it will automatically be approved unless it fails template review.
        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates#edit-a-message-template>`_.

        Args:
            new_category: The new category of the template (optional, cannot be changed for approved templates).
            new_components: The new components of the template (optional, if not provided, the existing components will be used).
            new_message_send_ttl_seconds: The new message send TTL in seconds (optional, if not provided, the existing TTL will be used).
            new_parameter_format: The new parameter format (optional, if not provided, the existing format will be used).

        Returns:
            Whether the template was updated successfully.
        """
        if res := self._client.update_template(
            template_id=self.id,
            new_category=new_category,
            new_components=new_components,
            new_message_send_ttl_seconds=new_message_send_ttl_seconds,
            new_parameter_format=new_parameter_format,
        ):
            if new_category:
                self.category = new_category
            if new_components:
                self.components = new_components
            if new_message_send_ttl_seconds is not None:
                self.message_send_ttl_seconds = new_message_send_ttl_seconds
            if new_parameter_format is not None:
                self.parameter_format = new_parameter_format
        return res

    def duplicate(self, **overrides) -> CreatedTemplate:
        """
        Duplicate this template.

        - WhatsApp Cloud API does not support duplicating templates, this method creates a new template with the same components and properties as this one. It is useful for creating variations of existing templates with minor changes.

        Example:
            >>> wa = WhatsApp(...)
            >>> template = wa.get_template("my_template_id")
            >>> new_template = template.duplicate(language=TemplateLanguage.ENGLISH)

        Args:
            overrides: Optional overrides for the template properties.
        """
        return self._client.create_template(
            Template(
                name=overrides.get("name", self.name),
                language=overrides.get("language", self.language),
                category=overrides.get("category", self.category),
                components=overrides.get("components", self.components),
                parameter_format=overrides.get(
                    "parameter_format", self.parameter_format
                ),
                message_send_ttl_seconds=overrides.get(
                    "message_send_ttl_seconds", self.message_send_ttl_seconds
                ),
            )
        )

    def compare(
        self,
        *to: int | str,
        start: datetime.datetime | int,
        end: datetime.datetime | int,
    ) -> TemplatesCompareResult:
        """
        You can compare two templates by examining how often each one is sent, which one has the lower ratio of blocks to sends, and each template's top reason for being blocked.

        - Only two templates can be compared at a time.
        - Both templates must be in the same WhatsApp Business Account.
        - Templates must have been sent at least 1,000 times in the queries specified timeframe.
        - Timeframes are limited to ``7``, ``30``, ``60`` and ``90`` day lookbacks from the time of the request.
        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/template-comparison>`_.

        Args:
            to: The IDs of the templates to compare with the given template.
            start: The start date of the comparison period.
            end: The end date of the comparison period.

        Returns:
            A TemplatesCompareResult object containing the comparison results.
        """
        return self._client.compare_templates(
            template_id=self.id, *to, start=start, end=end
        )

    def unpause(self) -> TemplateUnpauseResult:
        """
        Unpause a template that has been paused due to pacing.

        - This method can only be called if the template is currently paused due to pacing.
        - You must wait 5 minutes after a template has been paused as a result of pacing before calling this method.
        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/message-templates/guidelines#unpausing>`_.

        Returns:
            A TemplateUnpauseResult object containing the result of the unpause operation.
        """
        res = self._client.unpause_template(template_id=self.id)
        if res:
            self.status = TemplateStatus.APPROVED
        return res

    def send(
        self,
        to: str | int,
        params: list[TemplateBaseComponent.Params],
        *,
        reply_to_message_id: str | None = None,
        tracker: str | CallbackData | None = None,
        sender: str | int | None = None,
    ) -> SentTemplate:
        """
        A shortcut to send a template message to WhatsApp users.

        Args:
            to: The phone ID of the WhatsApp user.
            params: The parameters to fill in the template.
            reply_to_message_id: The ID of the message to reply to (optional).
            tracker: A callback data to track the message (optional, can be a string or a :class:`CallbackData` object).
            sender: The phone ID to send the template from (optional, if not provided, the client's phone ID will be used).
        """
        return self._client.send_template(
            to=to,
            name=self.name,
            language=self.language,
            params=params,
            reply_to_message_id=reply_to_message_id,
            tracker=tracker,
            sender=sender,
        )


class TemplatesResult(Result[TemplateDetails]):
    """
    Represents the result of a templates query.

    Attributes:
        total_count: The total number of message templates that belong to a WhatsApp Business Account.
        message_template_count: The current number of message templates that belong to the WhatsApp Business Account.
        message_template_limit: The maximum number of message templates that can belong to a WhatsApp Business Account.
        are_translations_complete: The status for template translations.
    """

    total_count: int
    message_template_count: int
    message_template_limit: int
    are_translations_complete: bool

    def __init__(
        self,
        wa: WhatsApp,
        response: dict,
        item_factory: _ItemFactory,
    ):
        super().__init__(
            wa=wa,
            response=response,
            item_factory=item_factory,
        )
        self.total_count = response["summary"]["total_count"]
        self.message_template_count = response["summary"]["message_template_count"]
        self.message_template_limit = response["summary"]["message_template_limit"]
        self.are_translations_complete = response["summary"][
            "are_translations_complete"
        ]

    def __repr__(self) -> str:
        return (
            f"TemplatesResult({self._data!r}, has_next={self.has_next!r}, has_previous={self.has_previous!r}, "
            f"total_count={self.total_count!r}, "
            f"message_template_count={self.message_template_count!r}, "
            f"message_template_limit={self.message_template_limit!r}, "
            f"are_translations_complete={self.are_translations_complete!r})"
        )


class TopBlockReasonType(utils.StrEnum):
    """
    The top reason that customers reported when they blocked your WhatsApp phone number after receiving one of your message templates. The reasons include: Spam, Didn’t sign up, No longer needed, Offensive messages. Note that Top block reason is only visible when a significant number of customers block your number.

    - Read more at `facebook.com <https://www.facebook.com/business/help/511126334359303/>`_.

    Attributes:
        NO_LONGER_NEEDED: If a customer indicated they no longer needed the message, they may not need that service or product anymore. Make sure your audience is still in need of your service or product by regularly reviewing your audience lists.
        NO_REASON: A customer blocked your number but did not indicate why. Selecting a reason for blocking a message is not required.
        NO_REASON_GIVEN: A customer blocked your number but did not indicate why. Selecting a reason for blocking a message is not required.
        NO_SIGN_UP: If a customer indicated that they didn’t sign up, they may not have opted in to receiving messages. Make sure you have obtained permission from users to receive messages on WhatsApp.
        OFFENSIVE_MESSAGES: If a customer indicated the message was offensive, they may have found it inappropriate. Check your messages to ensure that they don’t contain rude, foul or harassing language, adult content, or prohibited or illegal activity.
        OTHER: A customer may choose Other as a reason for blocking your number. When the top reason for blocking has been determined to be Other, then Unknown block reason will be shown. It may also be the top block reason in cases where there is an insufficient amount of data.
        OTP_DID_NOT_REQUEST: If a customer indicated that they did not request an OTP, they may have received an OTP without requesting it. Make sure you are only sending OTPs to users who have requested them.
        SPAM: If a customer indicated that spam is the reason for blocking, they may have received too many messages in a short period of time. Try being more selective about the frequency of messages.
        UNKNOWN_BLOCK_REASON: A customer may choose Other as a reason for blocking your number. When the top reason for blocking has been determined to be Other, then Unknown block reason will be shown. It may also be the top block reason in cases where there is an insufficient amount of data.
    """

    NO_LONGER_NEEDED = "NO_LONGER_NEEDED"
    NO_REASON = "NO_REASON"
    NO_REASON_GIVEN = "NO_REASON_GIVEN"
    NO_SIGN_UP = "NO_SIGN_UP"
    OFFENSIVE_MESSAGES = "OFFENSIVE_MESSAGES"
    OTHER = "OTHER"
    OTP_DID_NOT_REQUEST = "OTP_DID_NOT_REQUEST"
    SPAM = "SPAM"
    UNKNOWN_BLOCK_REASON = "UNKNOWN_BLOCK_REASON"

    UNKNOWN = "UNKNOWN"


@dataclasses.dataclass(kw_only=True, slots=True, frozen=True)
class TemplatesCompareResult:
    """
    Represents the result of a template comparison query.

    Attributes:
        block_rate: Array of template ID strings, in increasing order of block rate (ratio of blocks to sends).
        times_sent: A dictionary mapping template IDs to the number of times each template has been sent.
        top_block_reason: A dictionary mapping template IDs to the top reason for blocking each template.
    """

    block_rate: list[str] | None = None
    times_sent: dict[str, int] | None = None
    top_block_reason: dict[str, TopBlockReasonType] | None = None

    @classmethod
    def from_dict(
        cls,
        data: dict,
    ) -> TemplatesCompareResult:
        block_rate, times_sent, top_block_reason = None, None, None
        for metric in data["data"]:
            if metric["metric"] == "BLOCK_RATE":
                block_rate = metric.get("order_by_relative_metric")
            elif metric["metric"] == "MESSAGE_SENDS":
                times_sent = {
                    item["key"]: item["value"]
                    for item in metric.get("number_values", [])
                }
            elif metric["metric"] == "TOP_BLOCK_REASON":
                top_block_reason = {
                    item["key"]: TopBlockReasonType(item["value"])
                    for item in metric.get("string_values", [])
                }

        return cls(
            block_rate=block_rate,
            times_sent=times_sent,
            top_block_reason=top_block_reason,
        )


@dataclasses.dataclass(kw_only=True, slots=True, frozen=True)
class MigrateTemplatesResult:
    """
    Represents the response from migrating templates from one WhatsApp Business Account to another.

    Attributes:
        migrated_templates:  templates that were successfully duplicated in the destination WhatsApp Business Account.
        failed_templates: templates that failed to be duplicated in the destination WhatsApp Business Account, along with the reason for failure.
    """

    migrated_templates: tuple[MigratedTemplate, ...]
    failed_templates: tuple[MigratedTemplateError, ...]

    @classmethod
    def from_dict(cls, data: dict) -> MigrateTemplatesResult:
        migrated_templates = tuple(
            MigratedTemplate(id=item) for item in data.get("migrated_templates", [])
        )
        failed_templates = tuple(
            MigratedTemplateError(id=item["id"], reason=item["reason"])
            for item in data.get("failed_templates", [])
        )
        return cls(
            migrated_templates=migrated_templates,
            failed_templates=failed_templates,
        )


@dataclasses.dataclass(kw_only=True, slots=True, frozen=True)
class MigratedTemplate:
    """
    Represents a successfully migrated template.

    Attributes:
        id: The unique identifier of the migrated template.
    """

    id: str


@dataclasses.dataclass(kw_only=True, slots=True, frozen=True)
class MigratedTemplateError(Exception):
    """
    Represents an error that occurred while migrating a template.

    Attributes:
        id: The unique identifier of the template that failed to migrate.
        reason: The reason for the migration failure. e.g. `"Incorrect category"`, `"Formatting error - dangling parameter"`.
    """

    id: str
    reason: str


@dataclasses.dataclass(frozen=True, slots=True)
class _CreatedAndUpdatedTemplateActions:
    """
    Internal class for WhatsApp Template actions.
    """

    _client: WhatsApp = dataclasses.field(repr=False, hash=False, compare=False)
    id: str
    category: TemplateCategory

    def get(self) -> TemplateDetails:
        """
        Retrieve the details of the created or updated template.

        Returns:
            TemplateDetails: The details of the created or updated template.
        """
        return self._client.get_template(template_id=self.id)

    def wait_until_approved(
        self,
        *,
        cancelers: pywa_filters.Filter | None = None,
        timeout: float | None = None,
    ) -> TemplateStatusUpdate:
        """
        Wait until the template is approved.

        Example usage:

            >>> from pywa import WhatsApp, filters
            >>> wa = WhatsApp(...)
            >>> created_template = wa.create_template(...)
            >>> status = created_template.wait_until_approved(cancelers=filters.template_status & filters.template_status_rejected)
            >>> print(f"Template {created_template.id} is approved with status: {status.new_status}")


        Args:
            cancelers: A filter to cancel the waiting process.
            timeout: The maximum time to wait for the template to be approved.

        Returns:
            TemplateStatusUpdate: An update containing the status of the template once it is approved.
        """
        return cast(
            TemplateStatusUpdate,
            self._client.listen(
                to=TemplateUpdateListenerIdentifier(
                    waba_id=self._client.business_account_id, template_id=self.id
                ),
                filters=pywa_filters.template_status
                & pywa_filters.template_status_approved,
                cancelers=cancelers,
                timeout=timeout,
            ),
        )


@dataclasses.dataclass(frozen=True, slots=True)
class CreatedTemplate(_CreatedAndUpdatedTemplateActions):
    """
    Represents a created WhatsApp Template.

    Attributes:
        id: the template ID.
        status: the template status.
        category: the template category.
    """

    status: TemplateStatus

    @classmethod
    def from_dict(cls, data: dict, client: WhatsApp) -> CreatedTemplate:
        """
        Create a CreatedTemplate instance from a dictionary.

        Args:
            data (dict): The dictionary containing template data.
            client (WhatsApp): The WhatsApp client instance.

        Returns:
            CreatedTemplate: An instance of CreatedTemplate.
        """
        return cls(
            _client=client,
            id=data["id"],
            status=TemplateStatus(data["status"]),
            category=TemplateCategory(data["category"]),
        )


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class UpdatedTemplate(_CreatedAndUpdatedTemplateActions):
    """
    Represents the result of a template update operation.

    Attributes:
        id: The unique identifier of the updated template.
        name: The name of the updated template.
        category: The category of the updated template.
        success: Indicates whether the template update was successful.
    """

    name: str
    success: bool

    @classmethod
    def from_dict(cls, data: dict, client: WhatsApp) -> UpdatedTemplate:
        return cls(
            _client=client,
            success=data["success"],
            id=data["id"],
            name=data["name"],
            category=TemplateCategory(data["category"]),
        )

    def __bool__(self) -> bool:
        """
        Returns True if the template update was successful, False otherwise.
        """
        return self.success


@dataclasses.dataclass(frozen=True, slots=True)
class CreatedTemplates:
    """
    Represents a collection of created WhatsApp Templates.

    Attributes:
        templates: A list of CreatedTemplate instances.
    """

    templates: tuple[CreatedTemplate, ...]

    @classmethod
    def from_dict(cls, data: dict, client: WhatsApp) -> CreatedTemplates:
        """
        Create a CreatedTemplates instance from a dictionary.

        Args:
            data (dict): The dictionary containing template data.
            client (WhatsApp): The WhatsApp client instance.

        Returns:
            CreatedTemplates: An instance of CreatedTemplates.
        """
        return cls(
            templates=tuple(
                CreatedTemplate.from_dict(item, client) for item in data["data"]
            )
        )

    def __iter__(self) -> Iterator[CreatedTemplate]:
        """
        Iterate over the created templates.

        Returns:
            Iterator[CreatedTemplate]: An iterator over the CreatedTemplate instances.
        """
        return iter(self.templates)
