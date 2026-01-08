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
    "HeaderGIF",
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
    "DegreesOfFreedomSpec",
    "CreativeFeaturesSpec",
    "TapTargetConfiguration",
]

import abc
import dataclasses
import datetime
import json
import logging
import pathlib
import re
import warnings
from typing import TYPE_CHECKING, AsyncIterator, BinaryIO, Iterator, Literal, cast

from .. import _helpers as helpers
from .. import utils
from ..listeners import TemplateStatusUpdateListenerIdentifier
from . import CallbackData
from .base_update import BaseUpdate, RawUpdate
from .flows import FlowActionType, FlowJSON
from .media import Media
from .others import ProductsSection, Result, SuccessResult, _ItemFactory

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
        category: The category of the template.
        reason: The reason the template was rejected (if status is ``REJECTED``).
        disable_info: Information about the template disablement (if status is ``DISABLED``).
        other_info: Additional information about the template status update (if status is ``LOCKED`` or ``UNLOCKED``).
        rejection_info: Information about the template rejection (if status is ``REJECTED``).
        shared_data: Shared data between handlers.
    """

    new_status: TemplateStatus
    category: TemplateCategory | None = None
    reason: TemplateRejectionReason | None = None
    disable_info: DisableInfo | None = None
    other_info: OtherInfo | None = None
    rejection_info: RejectionInfo | None = None

    _webhook_field = "message_template_status_update"

    @classmethod
    def from_update(cls, client: WhatsApp, update: RawUpdate) -> TemplateStatusUpdate:
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
            category=TemplateCategory(value["message_template_category"])
            if value.get("message_template_category")
            else None,
            reason=TemplateRejectionReason(value["reason"])
            if value.get("reason")
            else None,
            disable_info=DisableInfo.from_dict(value["disable_info"])
            if "disable_info" in value
            else None,
            other_info=OtherInfo.from_dict(value["other_info"])
            if "other_info" in value
            else None,
            rejection_info=RejectionInfo.from_dict(value["rejection_info"])
            if "rejection_info" in value
            else None,
        )

    @property
    def listener_identifier(self) -> TemplateStatusUpdateListenerIdentifier:
        return TemplateStatusUpdateListenerIdentifier(
            template_id=self.template_id,
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

    @property
    def title(self) -> str | None:
        """Deprecated. Use other_info.title instead."""
        warnings.warn(
            "The 'title' property is deprecated. Use 'other_info.title' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.other_info.title if self.other_info else None

    @property
    def description(self) -> str | None:
        """Deprecated. Use other_info.description instead."""
        warnings.warn(
            "The 'description' property is deprecated. Use 'other_info.description' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.other_info.description if self.other_info else None

    @property
    def disable_date(self) -> datetime.datetime | None:
        """Deprecated. Use disable_info.disable_date instead."""
        warnings.warn(
            "The 'disable_date' property is deprecated. Use 'disable_info.disable_date' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.disable_info.disable_date if self.disable_info else None


@dataclasses.dataclass(slots=True, frozen=True, kw_only=True)
class DisableInfo:
    """
    Information about the template disablement.

    - Only present when a template is disabled.

    Attributes:
        disable_date: Timestamp indicating when the template was disabled.
    """

    disable_date: datetime.datetime

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            disable_date=datetime.datetime.fromtimestamp(
                data["disable_date"], tz=datetime.timezone.utc
            ),
        )


@dataclasses.dataclass(slots=True, frozen=True, kw_only=True)
class OtherInfo:
    """
    Additional information about the template status update.

    - Only present when a template is locked or unlocked.

    Attributes:
        title: Title of template pause or unpause event.
        description: String describing why the template was locked or unlocked.
    """

    title: str | None
    description: str | None

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            title=data.get("title"),
            description=data.get("description"),
        )


@dataclasses.dataclass(slots=True, frozen=True, kw_only=True)
class RejectionInfo:
    """
    Information about the template rejection.

    Attributes:
        reason: Provides a detailed explanation for why the template was rejected. This field describes the specific issue detected in the template content.
        recommendation: Offers actionable guidance on how to modify the template to resolve the rejection reason. This field suggests best practices for editing the template content.
    """

    reason: str | None
    recommendation: str | None

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            reason=data.get("reason"),
            recommendation=data.get("recommendation"),
        )


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
    def from_update(cls, client: WhatsApp, update: RawUpdate) -> TemplateCategoryUpdate:
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
    def from_update(
        cls, client: WhatsApp, update: RawUpdate
    ) -> TemplateComponentsUpdate:
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
    def from_update(cls, client: WhatsApp, update: RawUpdate) -> TemplateQualityUpdate:
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
    library_template_body_inputs: list[BaseLibraryBodyInput] | None = None
    library_template_button_inputs: list[BaseLibraryButtonInput] | None = None

    def to_json(self) -> str:
        return _template_to_json(self)


class BaseLibraryButtonInput(abc.ABC):
    type: ComponentType


class BaseLibraryBodyInput: ...


@dataclasses.dataclass(slots=True, frozen=True)
class QualityScore:
    """
    Represents the quality score of a template.

    Attributes:
        score: The quality score type (``GREEN``, ``YELLOW``, ``RED``).
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
        AUTHENTICATION: Enable businesses to verify a user’s identity, potentially at various steps of the customer journey. See `Authentication templates <https://developers.facebook.com/docs/whatsapp/business-management-api/authentication-templates>`_ for more details.
        MARKETING: Enable businesses to achieve a wide range of goals, from generating awareness to driving sales and retargeting customers. See `Marketing templates <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/marketing-templates>`_ for more details.
        UTILITY: Enable businesses to follow up on user actions or requests, since these messages are typically triggered by user actions. See `Utility templates <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/utility-templates>`_ for more details.
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
    GIF = "GIF"
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
    GIF = "gif"
    LOCATION = "location"
    BUTTON = "button"
    PRODUCT = "product"
    COUPON_CODE = "coupon_code"
    ACTION = "action"
    PAYLOAD = "payload"
    LIMITED_TIME_OFFER = "limited_time_offer"
    CAROUSEL = "carousel"
    TAP_TARGET_CONFIGURATION = "tap_target_configuration"

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
    """
    The type of parameter formatting the HEADER and BODY components of the template will use.

    Attributes:
        POSITIONAL: The component uses positional parameters, e.g. ``{{1}}``, ``{{2}}``, etc.
        NAMED: The component uses named parameters, e.g. ``{{param_name}}``.
    """

    POSITIONAL = "POSITIONAL"
    NAMED = "NAMED"

    UNKNOWN = "UNKNOWN"


class CreativeFeaturesSpec:
    """
    Automatic Creative Optimizations enhance the visual appeal and engagement of Marketing template messages.

    This capability tests minor variations of your existing image header with different crop orientations or color filters, and automatically selects the variant which is getting the highest click-through rate over time with no input needed from you. These creative enhancements are designed to help improve performance and visual appeal of marketing messages, while maintaining the fidelity of the message. These optimizations are similar to `Advantage+ creative <https://www.facebook.com/business/help/297506218282224?id=649869995454285>`_.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/marketing-messages-lite-api/sending-messages#automatic-creative-optimizations>`_.

    .. note::

        Automatic Creative Optimizations are currently only available to businesses participating in early access. It will be made available to all businesses on a future date.

    Attributes:
        image_brightness_and_contrast: Whether to apply brightness and contrast adjustments to images. Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/marketing-messages-lite-api/sending-messages#image-cropping>`_.
        image_touchups: Whether to apply touch-ups to images. Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/marketing-messages-lite-api/sending-messages#image-filtering>`_.
        add_text_overlay: Whether to add text overlays to images. Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/marketing-messages-lite-api/sending-messages#text-overlays>`_.
        image_animation: Whether to apply animations to images. Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/marketing-messages-lite-api/sending-messages#image-animation>`_.
        image_background_gen: Whether to generate backgrounds for images. Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/marketing-messages-lite-api/sending-messages#image-background-generation>`_.
        text_extraction_for_headline: Whether to extract text from images for headlines. Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/marketing-messages-lite-api/sending-messages#headline-extraction>`_.
        text_extraction_for_tap_target: Whether to extract text from images for tap targets. Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/marketing-messages-lite-api/sending-messages#tap-target-title-extraction>`_.
    """

    image_brightness_and_contrast: bool
    image_touchups: bool
    add_text_overlay: bool
    image_animation: bool
    image_background_gen: bool
    text_extraction_for_headline: bool
    text_extraction_for_tap_target: bool
    product_extensions: bool
    text_formatting_optimization: bool

    _fields = {
        "image_brightness_and_contrast",
        "image_touchups",
        "add_text_overlay",
        "image_animation",
        "image_background_gen",
        "text_extraction_for_headline",
        "text_extraction_for_tap_target",
        "product_extensions",
        "text_formatting_optimization",
    }

    def __init__(
        self,
        *,
        image_brightness_and_contrast: bool | None = None,
        image_touchups: bool | None = None,
        add_text_overlay: bool | None = None,
        image_animation: bool | None = None,
        image_background_gen: bool | None = None,
        text_extraction_for_headline: bool | None = None,
        text_extraction_for_tap_target: bool | None = None,
        product_extensions: bool | None = None,
        text_formatting_optimization: bool | None = None,
    ):
        """
        Initializes a CreativeFeaturesSpec instance.

        Args:
            image_brightness_and_contrast: Whether to apply brightness and contrast adjustments to images. Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/marketing-messages-lite-api/sending-messages#image-cropping>`_.
            image_touchups: Whether to apply touch-ups to images. Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/marketing-messages-lite-api/sending-messages#image-filtering>`_.
            add_text_overlay: Whether to automatically add a text overlay onto your image using your message content. Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/marketing-messages-lite-api/sending-messages#text-overlays>`_.
            image_animation: Whether to automatically transform your header image into an animated GIF. Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/marketing-messages-lite-api/sending-messages#image-animation>`_.
            image_background_gen: Whether to generate backgrounds for images. Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/marketing-messages-lite-api/sending-messages#image-background-generation>`_.
            text_extraction_for_headline: Whether to extract keywords or phrases from your message to create a headline for your body text to highlight key information. Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/marketing-messages-lite-api/sending-messages#headline-extraction>`_.
            text_extraction_for_tap_target: Whether to extract keywords or phrases from your message to create a title for the tap-target area to highlight key information. Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/marketing-messages-lite-api/sending-messages#tap-target-title-extraction>`_.
            product_extensions: Whether to encourage users to explore more products by appending additional catalog products to single-image creatives. Read more at `developers.facebook.com <https://developers.facebook.com/documentation/business-messaging/whatsapp/marketing-messages/send-marketing-messages#product-extensions>`_.
            text_formatting_optimization: Whether to update the formatting of text (e.g. remove unnecessary spaces, bold phrases) to increase performance. No text content is changed - format only. Read more at `developers.facebook.com <https://developers.facebook.com/documentation/business-messaging/whatsapp/marketing-messages/send-marketing-messages#text-formatting>`_.
        """
        for field_name, value in locals().items():
            if field_name == "self":
                continue
            setattr(self, field_name, value)

    def to_dict(self) -> dict:
        return {
            k: "OPT_IN" if v else "OPT_OUT"
            for k, v in {
                field_name: getattr(self, field_name) for field_name in self._fields
            }.items()
            if v is not None
        }

    def __repr__(self) -> str:
        field_reprs = ", ".join(
            f"{field_name}={getattr(self, field_name)!r}"
            for field_name in self._fields
            if getattr(self, field_name) is not None
        )
        return f"{self.__class__.__name__}({field_reprs})"


@dataclasses.dataclass(slots=True, kw_only=True)
class DegreesOfFreedomSpec:
    """
    Represents the degrees of freedom specification for a template.

    Attributes:
        creative_features_spec: The creative features specification for the template.
    """

    creative_features_spec: CreativeFeaturesSpec


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


class BaseParams(abc.ABC):
    """Base class for template component parameters."""

    @abc.abstractmethod
    def to_dict(self) -> dict: ...


class TapTargetConfiguration(BaseParams):
    """
    Tap target title URL override

    Tap target override enables image-based, text-based, and header-less message templates to function as interactive Call-to-Action URL buttons. These buttons display a custom title and open the destination linked to the first URL button.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-message-templates/tap-target-url-title-override>`_.

    Attributes:
        title: URL Title.
        url: The URL to open.
    """

    title: str
    url: str

    def __init__(
        self,
        title: str,
        url: str,
    ):
        self.title = title
        self.url = url

    def to_dict(self) -> dict:
        return {
            "type": ParamType.TAP_TARGET_CONFIGURATION.value,
            "parameters": [
                {
                    "type": ParamType.TAP_TARGET_CONFIGURATION.value,
                    ParamType.TAP_TARGET_CONFIGURATION.value: [
                        {"url": self.url, "title": self.title}
                    ],
                }
            ],
        }


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

    class _Params(BaseParams):
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

    def _params(
        *positionals,
        _params_cls: type[_BaseTextComponent],
        **named,
    ) -> _BaseTextComponent._Params:
        if positionals and isinstance(
            positionals[0], _BaseTextComponent
        ):  # BodyText(...).params("David")
            self, *positionals = positionals
        else:  # BodyText.params("David")
            return _params_cls(*positionals, **named)

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

        return self._Params(*positionals, **named)


class HeaderText(_BaseTextComponent, BaseHeaderComponent):
    """
    Represents a header text component in a template.

    - All templates are limited to one header component
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#text-header>`_.

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

    class _Params(_BaseTextComponent._Params):
        typ = ComponentType.HEADER

    def params(
        *positionals,
        **named,
    ) -> HeaderText._Params:
        """
        Fill the parameters for the header text component.

        Args:
            *positionals: Positional parameters to fill in the template text. e.g. for `"Hi {{1}}!"`, you would pass ``"John"`` as the first positional argument.
            **named: Named parameters to fill in the template text. e.g. for `"Hi {{name}}!"`, you would pass ``name="John"`` as a named argument.
        """
        return HeaderText._params(*positionals, _params_cls=HeaderText._Params, **named)


class _BaseMediaHeaderComponent(BaseHeaderComponent, abc.ABC):
    """
    Base class for media components in templates.

    - Used in :class:`HeaderImage`, :class:`HeaderVideo`, and :class:`HeaderDocument` components.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#media-header>`_.
    """

    __slots__ = ("_example", "_handle", "_mime_type")

    format: HeaderFormatType

    def __init__(
        self,
        example: str
        | int
        | Media
        | pathlib.Path
        | bytes
        | BinaryIO
        | Iterator[bytes]
        | AsyncIterator[bytes],
        *,
        mime_type: str | None = None,
    ):
        """
        Initializes a media header component for a template.

        Args:
            example: An example of the media to be used in the header (can be a URL, file path, bytes, bytes generator, file-like object, base64 or a :py:class:`~pywa.types.media.Media` instance).
            mime_type: The mime type of the example (optional, required when passing bytes, bytes generator, or path without extension).
        """
        self._example = example
        self._mime_type = mime_type
        self._handle = None

    @property
    def example(
        self,
    ) -> (
        str
        | int
        | Media
        | pathlib.Path
        | bytes
        | BinaryIO
        | Iterator[bytes]
        | AsyncIterator[bytes]
    ):
        """
        Returns the example media for the header component.
        """
        return self._example

    @example.setter
    def example(
        self,
        value: str
        | int
        | Media
        | pathlib.Path
        | bytes
        | BinaryIO
        | Iterator[bytes]
        | AsyncIterator[bytes],
    ):
        """
        Sets the example media for the header component (and resets the handle).
        """
        self._example = value
        self._handle, self._mime_type = None, None

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


class _BaseMediaParams(BaseParams, abc.ABC):
    format: HeaderFormatType
    param_type: Literal[ParamType.IMAGE, ParamType.VIDEO, ParamType.DOCUMENT]

    def __init__(
        self,
        media: str
        | int
        | Media
        | pathlib.Path
        | bytes
        | BinaryIO
        | Iterator[bytes]
        | AsyncIterator[bytes],
        filename: str | None = None,
        mime_type: str | None = None,
    ):
        self.media = media
        self._resolved_media: str | None = None
        self._is_url: bool | None = None
        self._filename = filename
        self._fallback_filename: str | None = None
        self._mime_type = mime_type

    def to_dict(
        self,
    ) -> dict:
        if self._resolved_media is None:
            raise ValueError(f"{self.__class__.__name__} media not resolved yet")
        if self._filename is utils.MISSING:
            self._filename = self._fallback_filename
        return {
            "type": ComponentType.HEADER.value,
            "parameters": [
                {
                    "type": self.param_type.value,
                    self.param_type.value: {
                        "link" if self._is_url else "id": self._resolved_media,
                        **({"filename": self._filename} if self._filename else {}),
                    },
                }
            ],
        }

    def clear_media_cache(self):
        """
        Clears the cached media for this media param (if you using the same params object more than 30 days, the media ID will be expired, so you need to reupload the media).
        """
        (
            self._resolved_media,
            self._is_url,
            self._filename,
            self._fallback_filename,
            self._mime_type,
        ) = (
            None,
            None,
            None,
            None,
            None,
        )


class HeaderImage(_BaseMediaHeaderComponent):
    """
    Represents a header image component in a template.

    - All templates are limited to one header component.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#media-header>`_.

    Example:

        >>> header_image = HeaderImage(example="https://example.com/image.jpg")
        >>> header_image.params(image="https://cdn.com/image.jpg")

    Attributes:
        example: An example of the header image media.
        mime_type: The mime type of the example (optional, required when passing bytes, bytes generator, or path without extension).
    """

    format = HeaderFormatType.IMAGE

    class _Params(_BaseMediaParams):
        format = HeaderFormatType.IMAGE
        param_type = ParamType.IMAGE

        def __init__(
            self,
            *,
            image: str
            | int
            | Media
            | pathlib.Path
            | bytes
            | BinaryIO
            | Iterator[bytes]
            | AsyncIterator[bytes],
            mime_type: str | None = None,
        ):
            super().__init__(media=image, mime_type=mime_type)

    @staticmethod
    def params(
        *,
        image: str
        | int
        | Media
        | pathlib.Path
        | bytes
        | BinaryIO
        | Iterator[bytes]
        | AsyncIterator[bytes],
        mime_type: str | None = None,
    ) -> HeaderImage._Params:
        """
        Fill the parameters for the header image component.

        Args:
            image: The image media to be used in the header (can be a URL, file path, bytes, bytes generator, file-like object, base64 or a :py:class:`~pywa.types.media.Media` instance).
            mime_type: The mime type of the image (optional, required when passing bytes, bytes generator, or path without extension).

        Returns:
            An instance of BaseParams containing the media parameter.
        """
        return HeaderImage._Params(image=image, mime_type=mime_type)


class HeaderVideo(_BaseMediaHeaderComponent):
    """
    Represents a header video component in a template.

    - All templates are limited to one header component.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#media-header>`_.

    Example:

        >>> header_video = HeaderVideo(example="https://example.com/video.mp4")
        >>> header_video.params(video="https://cdn.com/video.mp4")

    Attributes:
        example: An example of the header video media.
        mime_type: The mime type of the example (optional, required when passing bytes, bytes generator, or path without extension).
    """

    format = HeaderFormatType.VIDEO

    class _Params(_BaseMediaParams):
        format = HeaderFormatType.VIDEO
        param_type = ParamType.VIDEO

        def __init__(
            self,
            *,
            video: str
            | int
            | Media
            | pathlib.Path
            | bytes
            | BinaryIO
            | Iterator[bytes]
            | AsyncIterator[bytes],
            mime_type: str | None = None,
        ):
            super().__init__(media=video, mime_type=mime_type)

    @staticmethod
    def params(
        *,
        video: str
        | int
        | Media
        | pathlib.Path
        | bytes
        | BinaryIO
        | Iterator[bytes]
        | AsyncIterator[bytes],
        mime_type: str | None = None,
    ) -> HeaderVideo._Params:
        """
        Fill the parameters for the header video component.

        Args:
            video: The video media to be used in the header (can be a URL, file path, bytes, bytes generator, file-like object, base64 or a :py:class:`~pywa.types.media.Media` instance).
            mime_type: The mime type of the image (optional, required when passing bytes, bytes generator, or path without extension).

        Returns:
            An instance of BaseParams containing the media parameter.
        """
        return HeaderVideo._Params(video=video, mime_type=mime_type)


class HeaderGIF(_BaseMediaHeaderComponent):
    """
    Represents a header GIF component in a template.

    - All templates are limited to one header component.
    - GIFs are currently only available for the MM Lite API.
    - Max size: 3.5MB. Larger files will be displayed as video messages.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#media-header>`_.

    Example:

        >>> header_gif = HeaderGIF(example="https://example.com/animation.gif")
        >>> header_gif.params(gif="https://cdn.com/animation.gif")

    Attributes:
        example: An example of the header GIF media.
        mime_type: The mime type of the example (optional, required when passing bytes, bytes generator, or path without extension).
    """

    format = HeaderFormatType.GIF

    class _Params(_BaseMediaParams):
        format = HeaderFormatType.GIF
        param_type = ParamType.GIF

        def __init__(
            self,
            *,
            gif: str
            | int
            | Media
            | pathlib.Path
            | bytes
            | BinaryIO
            | Iterator[bytes]
            | AsyncIterator[bytes],
            mime_type: str | None = None,
        ):
            super().__init__(media=gif, mime_type=mime_type)

    @staticmethod
    def params(
        *,
        gif: str
        | int
        | Media
        | pathlib.Path
        | bytes
        | BinaryIO
        | Iterator[bytes]
        | AsyncIterator[bytes],
        mime_type: str | None = None,
    ) -> HeaderGIF._Params:
        """
        Fill the parameters for the header GIF component.

        Args:
            gif: The GIF media to be used in the header (can be a URL, file path, bytes, bytes generator, file-like object, base64 or a :py:class:`~pywa.types.media.Media` instance).
            mime_type: The mime type of the image (optional, required when passing bytes, bytes generator, or path without extension).

        Returns:
            An instance of BaseParams containing the media parameter.
        """
        return HeaderGIF._Params(gif=gif, mime_type=mime_type)


class HeaderDocument(_BaseMediaHeaderComponent):
    """
    Represents a header document component in a template.

    - All templates are limited to one header component.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#media-header>`_.

    Example:

        >>> header_document = HeaderDocument(example="https://example.com/document.pdf")
        >>> header_document.params(document="https://cdn.com/document.pdf")

    Attributes:
        example: An example of the header document media.
        mime_type: The mime type of the example (optional, required when passing bytes, bytes generator, or path without extension).
    """

    format = HeaderFormatType.DOCUMENT

    class _Params(_BaseMediaParams):
        format = HeaderFormatType.DOCUMENT
        param_type = ParamType.DOCUMENT

        def __init__(
            self,
            *,
            document: str
            | int
            | Media
            | pathlib.Path
            | bytes
            | BinaryIO
            | Iterator[bytes]
            | AsyncIterator[bytes],
            filename: str | None,
            mime_type: str | None = None,
        ):
            super().__init__(media=document, filename=filename, mime_type=mime_type)

    @staticmethod
    def params(
        *,
        document: str
        | int
        | Media
        | pathlib.Path
        | bytes
        | BinaryIO
        | Iterator[bytes]
        | AsyncIterator[bytes],
        filename: str | None = utils.MISSING,
        mime_type: str | None = None,
    ) -> HeaderDocument._Params:
        """
        Fill the parameters for the header document component.

        Args:
            document: The document media to be used in the header (can be a URL, file path, bytes, bytes generator, file-like object, base64 or a :py:class:`~pywa.types.media.Media` instance).
            filename: Document filename, with extension. The WhatsApp client will use an appropriate file type icon based on the extension (Optional, if not provided, if possible, the filename will be extracted from the URL or file path. pass ``None`` to skip this behavior).
            mime_type: The mime type of the image (optional, required when passing bytes, bytes generator, or path without extension).

        Returns:
            An instance of BaseParams containing the media parameter.
        """
        return HeaderDocument._Params(
            document=document, filename=filename, mime_type=mime_type
        )


@dataclasses.dataclass(kw_only=True, slots=True)
class HeaderLocation(BaseHeaderComponent):
    """
    Represents a header location component in a template.

    - All templates are limited to one header component.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#location-header>`_.

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

    class _Params(BaseParams):
        def __init__(self, *, lat: float, lon: float, name: str, address: str):
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

    @staticmethod
    def params(
        *, lat: float, lon: float, name: str, address: str
    ) -> HeaderLocation._Params:
        """
        Fill the parameters for the header location component.

        Args:
            lat: Location latitude.
            lon: Location longitude.
            name: Text that will appear immediately below the generic map at the top of the message.
            address: Address that will appear after the ``name`` value, below the generic map at the top of the message.

        Returns:
            An instance of BaseParams containing the location parameters.
        """
        return HeaderLocation._Params(lat=lat, lon=lon, name=name, address=address)


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

    class _Params(BaseParams):
        def __init__(self, *, catalog_id: str, sku: str):
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

    @staticmethod
    def params(*, catalog_id: str, sku: str) -> HeaderProduct._Params:
        """
        Fill the parameters for the header product component.

        Args:
            catalog_id: ID of `connected ecommerce <https://www.facebook.com/business/help/158662536425974>`_ catalog containing the product.
            sku: Unique identifier of the product in a catalog (also referred to as ``Content ID`` or ``Retailer ID``).

        Returns:
            An instance of BaseParams containing the catalog ID and SKU.
        """
        return HeaderProduct._Params(catalog_id=catalog_id, sku=sku)


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

    class _Params(_BaseTextComponent._Params):
        typ = ComponentType.BODY

    def params(
        *positionals,
        **named,
    ) -> BodyText._Params:
        """
        Fill the parameters for the body text component.

        Args:
            *positionals: Positional parameters to fill in the template text. e.g. for `"Hi {{1}}!"`, you would pass ``"John"`` as the first positional argument.
            **named: Named parameters to fill in the template text. e.g. for `"Hi {{name}}!"`, you would pass ``name="John"`` as a named argument.
        """
        return BodyText._params(*positionals, _params_cls=BodyText._Params, **named)

    class _LibraryInput(BaseLibraryBodyInput):
        def __init__(
            self,
            *,
            add_track_package_link: bool | None = None,
            add_learn_more_link: bool | None = None,
        ):
            self.add_track_package_link = add_track_package_link
            self.add_learn_more_link = add_learn_more_link

        def to_dict(self) -> dict:
            return {
                k: v
                for k, v in {
                    "add_track_package_link": self.add_track_package_link,
                    "add_learn_more_link": self.add_learn_more_link,
                }
                if v is not None
            }

    @staticmethod
    def library_input(
        *,
        add_track_package_link: bool | None = None,
        add_learn_more_link: bool | None = None,
    ) -> BodyText._LibraryInput:
        """
        Fill the library input for the body text component.

        Args:
            add_track_package_link: Whether to add a link to track a package.
            add_learn_more_link: Whether to add a "Learn more" link.

        Returns:
            An instance of BaseLibraryBodyInput containing the library input parameters.
        """
        return BodyText._LibraryInput(
            add_track_package_link=add_track_package_link,
            add_learn_more_link=add_learn_more_link,
        )


# =========== FOOTER ===========


@dataclasses.dataclass(kw_only=True, slots=True)
class BaseFooterComponent(TemplateBaseComponent, abc.ABC):
    type: ComponentType = dataclasses.field(
        default=ComponentType.FOOTER,
        init=False,
        repr=False,
    )


@dataclasses.dataclass(kw_only=True, slots=True)
class FooterText(BaseFooterComponent):
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
class Buttons(TemplateBaseComponent):
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

    class _Params(BaseParams):
        def __init__(self, *, coupon_code: str, index: int):
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

    @staticmethod
    def params(*, coupon_code: str, index: int) -> CopyCodeButton._Params:
        """
        Fill the parameters for the copy code button component.

        Args:
            coupon_code: The coupon code to be copied when the customer taps the button. Only accepting alphanumeric characters.
            index: Indicates order in which button should appear, if the template uses multiple buttons. Buttons are zero-indexed, so setting value to 0 will cause the button to appear first, and another button with an index of 1 will appear next, etc.

        Returns:
            An instance of BaseParams containing the coupon code and index.
        """
        return CopyCodeButton._Params(coupon_code=coupon_code, index=index)


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

    class _Params(BaseParams):
        def __init__(
            self,
            *,
            index: int,
            flow_token: str | None = None,
            flow_action_data: dict | None = None,
        ) -> None:
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

    @staticmethod
    def params(
        *,
        index: int,
        flow_token: str | None = None,
        flow_action_data: dict | None = None,
    ) -> FlowButton._Params:
        """
        Fill the parameters for the Flow button component.

        Args:
            index: Indicates order in which button should appear, if the template uses multiple buttons. Buttons are zero-indexed, so setting value to 0 will cause the button to appear first, and another button with an index of 1 will appear next, etc.
            flow_token: Optional token to be passed to the Flow.
            flow_action_data: Optional data to be passed to the first screen.

        Returns:
            An instance of BaseParams containing the parameters for the Flow button.
        """
        return FlowButton._Params(
            index=index, flow_token=flow_token, flow_action_data=flow_action_data
        )


@dataclasses.dataclass(kw_only=True, slots=True)
class PhoneNumberButton(BaseButtonComponent):
    """
    Phone number buttons call the specified business phone number when tapped by the app user. Templates are limited to one phone number button.

    - Note that some countries have special phone numbers that have leading zeros after the country calling code (e.g., ``+55-0-955-585-95436``). If you assign one of these numbers to the button, the leading zero will be stripped from the number. If your number will not work without the leading zero, assign an alternate number to the button, or add the number as message body text.
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

    class _LibraryInput(BaseLibraryButtonInput):
        def __init__(self, *, phone_number: str):
            self.phone_number = phone_number

        def to_dict(self) -> dict:
            return {
                "type": ComponentType.PHONE_NUMBER.value,
                "phone_number": self.phone_number,
            }

    @staticmethod
    def library_input(*, phone_number: str) -> PhoneNumberButton._LibraryInput:
        """
        Fill the library button input for the phone number button component.

        Args:
            phone_number: The phone number to be called when the user taps the button.

        Returns:
            An instance of BaseLibraryButtonInput containing the phone number.
        """
        return PhoneNumberButton._LibraryInput(phone_number=phone_number)


@dataclasses.dataclass(kw_only=True, slots=True)
class VoiceCallButton(BaseButtonComponent):
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

    class _Params(BaseParams):
        def __init__(self, *, callback_data: str | CallbackData, index: int):
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

    @staticmethod
    def params(
        *, callback_data: str | CallbackData, index: int
    ) -> QuickReplyButton._Params:
        """
        Fill the parameters for the quick reply button component.

        Args:
            callback_data: The data to send when the user clicks on the button (up to 256 characters, for complex data
             You can use :class:`CallbackData`).
            index: Indicates order in which button should appear, if the template uses multiple buttons. Buttons are zero-indexed, so setting value to 0 will cause the button to appear first, and another button with an index of 1 will appear next, etc.

        Returns:
            An instance of BaseParams containing the callback data and index.
        """
        return QuickReplyButton._Params(callback_data=callback_data, index=index)


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

    class _Params(BaseParams):
        def __init__(self, *, url_variable: str, index: int):
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

    @staticmethod
    def params(*, url_variable: str, index: int) -> URLButton._Params:
        """
        Fill the parameters for the URL button component.

        Args:
            url_variable: The variable to be appended to the end of the URL string. Maximum 2000 characters.
            index: Indicates order in which button should appear, if the template uses multiple buttons. Buttons are zero-indexed, so setting value to 0 will cause the button to appear first, and another button with an index of 1 will appear next, etc.

        Returns:
            An instance of BaseParams containing the URL variable and index.
        """
        return URLButton._Params(url_variable=url_variable, index=index)

    class _LibraryInput(BaseLibraryButtonInput):
        def __init__(
            self,
            *,
            base_url: str,
            url_suffix_example: str | None = None,
        ):
            self.base_url = base_url
            self.url_suffix_example = url_suffix_example

        def to_dict(self) -> dict:
            return {
                "type": ComponentType.URL.value,
                "url": {
                    "base_url": self.base_url,
                    **(
                        {"url_suffix_example": self.url_suffix_example}
                        if self.url_suffix_example
                        else {}
                    ),
                },
            }

    @staticmethod
    def library_input(
        *,
        base_url: str,
        url_suffix_example: str | None = None,
    ) -> URLButton._LibraryInput:
        """
        Fill the library button input for the URL button component.

        Args:
            base_url: The base URL of the website that loads in the device's default mobile web browser when the button is tapped by the app user.
            url_suffix_example: Optional example URL suffix to be used in the template.

        Returns:
            An instance of BaseLibraryButtonInput containing the base URL and optional URL suffix example.
        """
        return URLButton._LibraryInput(
            base_url=base_url, url_suffix_example=url_suffix_example
        )


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

    class _Params(BaseParams):
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

    @staticmethod
    def params(
        *, thumbnail_product_sku: str | None = None, index: int
    ) -> CatalogButton._Params:
        """
        Fill the parameters for the catalog button component.

        Args:
            thumbnail_product_sku: The SKU of the product to be used as the thumbnail header image. If omitted, the product image of the first item in your catalog will be used.
            index: Indicates order in which button should appear, if the template uses multiple buttons. Buttons are zero-indexed, so setting value to 0 will cause the button to appear first, and another button with an index of 1 will appear next, etc.

        Returns:
            An instance of BaseParams containing the thumbnail product SKU and index.
        """
        return CatalogButton._Params(
            thumbnail_product_sku=thumbnail_product_sku, index=index
        )


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
        ...            skus=["SKU12345", "SKU12346"],
        ...        ),
        ...        ProductsSection(
        ...            title="Section 2",
        ...            skus=["SKU12347", "SKU12348"],
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

    class _Params(BaseParams):
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
                "parameters": [
                    {
                        "type": ParamType.ACTION.value,
                        ParamType.ACTION.value: {
                            "thumbnail_product_retailer_id": self.thumbnail_product_sku,
                            "sections": [s.to_dict() for s in self.product_sections],
                        },
                    }
                ],
            }

    @staticmethod
    def params(
        *,
        product_sections: list[ProductsSection],
        thumbnail_product_sku: str,
        index: int,
    ) -> MPMButton._Params:
        """
        Fill the parameters for the multi-product message button component.

        Args:
            product_sections: A list of product sections, each containing a list of products to be displayed in the button. Each section can contain up to 30 products, and there can be up to 10 sections in total.
            thumbnail_product_sku: The SKU of the product to be used as the thumbnail header image.
            index: Indicates order in which button should appear, if the template uses multiple buttons. Buttons are zero-indexed, so setting value to 0 will cause the button to appear first, and another button with an index of 1 will appear next, etc.

        Returns:
            An instance of BaseParams containing the product sections, thumbnail product SKU, and index.
        """
        return MPMButton._Params(
            product_sections=product_sections,
            thumbnail_product_sku=thumbnail_product_sku,
            index=index,
        )


@dataclasses.dataclass(kw_only=True, slots=True)
class SPMButton(BaseButtonComponent):
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
class CallPermissionRequestButton(BaseButtonComponent):
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

    def to_dict(self) -> dict:
        return {
            "package_name": self.package_name,
            "signature_hash": self.signature_hash,
        }


class _BaseOTPButtonParams:
    """
    Base class for one-time password (OTP) button parameters.
    """

    class _Params(BaseParams):
        def __init__(self, otp: str):
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

    @staticmethod
    def params(*, otp: str) -> _BaseOTPButtonParams._Params:
        """
        Fill the parameters for the button component.

        Args:
            otp: The one-time password or code to be used in the button. Maximum 15 characters.

        Returns:
            An instance of BaseParams containing the OTP.
        """
        return _BaseOTPButtonParams._Params(otp=otp)


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

    class _LibraryInput(BaseLibraryButtonInput):
        def __init__(
            self,
            *,
            supported_apps: list[OTPSupportedApp],
        ):
            self.supported_apps = supported_apps

        def to_dict(self) -> dict:
            return {
                "type": ComponentType.OTP.value,
                "otp_type": OtpType.ONE_TAP.value,
                "supported_apps": [app.to_dict() for app in self.supported_apps],
            }

    @staticmethod
    def library_input(
        *, supported_apps: list[OTPSupportedApp]
    ) -> OneTapOTPButton._LibraryInput:
        """
        Fill the library button input for the one-tap autofill button component.

        Args:
            supported_apps: A list of supported apps, each defined by its package name and signature hash.

        Returns:
            An instance of BaseLibraryButtonInput containing the supported apps.
        """
        return OneTapOTPButton._LibraryInput(supported_apps=supported_apps)


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

    class _LibraryInput(BaseLibraryButtonInput):
        def __init__(
            self,
            *,
            supported_apps: list[OTPSupportedApp],
            zero_tap_terms_accepted: bool,
        ):
            self.supported_apps = supported_apps
            self.zero_tap_terms_accepted = zero_tap_terms_accepted

        def to_dict(self) -> dict:
            return {
                "type": ComponentType.OTP.value,
                "otp_type": OtpType.ZERO_TAP.value,
                "supported_apps": [app.to_dict() for app in self.supported_apps],
                "zero_tap_terms_accepted": self.zero_tap_terms_accepted,
            }

    @staticmethod
    def library_input(
        *,
        supported_apps: list[OTPSupportedApp],
        zero_tap_terms_accepted: bool,
    ) -> ZeroTapOTPButton._LibraryInput:
        """
        Fill the library button input for the zero-tap autofill button component.

        Args:
            supported_apps: A list of supported apps, each defined by its package name and signature hash.
            zero_tap_terms_accepted: Set to ``True`` to indicate that you understand that your use of zero-tap authentication is subject to the WhatsApp Business Terms of Service, and that it's your responsibility to ensure your customers expect that the code will be automatically filled in on their behalf when they choose to receive the zero-tap code through WhatsApp.

        Returns:
            An instance of BaseLibraryButtonInput containing the supported apps and zero-tap terms acceptance.
        """
        return ZeroTapOTPButton._LibraryInput(
            supported_apps=supported_apps,
            zero_tap_terms_accepted=zero_tap_terms_accepted,
        )


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

    class _LibraryInput(BaseLibraryButtonInput):
        @staticmethod
        def to_dict() -> dict:
            return {
                "type": ComponentType.OTP.value,
                "otp_type": OtpType.COPY_CODE.value,
            }

    @staticmethod
    def library_input() -> CopyCodeOTPButton._LibraryInput:
        """
        Fill the library button input for the copy code button component.

        Returns:
            An instance of BaseLibraryButtonInput for the copy code button.
        """
        return CopyCodeOTPButton._LibraryInput()


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

    class _Params(BaseParams):
        def __init__(self, *, expiration_time: datetime.datetime | None = None):
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

    @staticmethod
    def params(*, expiration_time: datetime.datetime) -> LimitedTimeOffer._Params:
        """
        Fill the parameters for the limited-time offer component.

        Args:
            expiration_time: The time when the offer expires. This is used to calculate the countdown timer.

        Returns:
            An instance of BaseParams containing the expiration time.
        """
        return LimitedTimeOffer._Params(expiration_time=expiration_time)


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

    class _Params(BaseParams):
        cards: list[CarouselCard._Params]

        def __init__(self, *, cards: list[CarouselCard._Params]):
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

    def params(self=None, *, cards: list[CarouselCard._Params]) -> Carousel._Params:
        """
        Fill the parameters for the carousel component.

        Args:
            cards: A list of card parameters, each representing a media card in the carousel.

        Returns:
            An instance of BaseParams containing the parameters for the carousel.
        """
        if self is None:
            return Carousel._Params(cards=cards)
        cards_len, params_len = len(self.cards), len(cards)
        if cards_len != params_len:
            raise ValueError(
                f"Expected {cards_len} card parameters, but got {params_len}."
            )
        return self._Params(cards=cards)


@dataclasses.dataclass(kw_only=True, slots=True)
class CarouselCard:
    """
    Represents a card in a carousel template.

    Example:

        >>> carousel_media_card = CarouselCard(
        ...     components=[
        ...         hi := HeaderImage(example="https://example.com/image.jpg"),
        ...         qrb := QuickReplyButton(text="Unsubscribe"),
        ...     ]
        ... )
        >>> carousel_media_card.params(
        ...     index=0,
        ...     params=[
        ...         hi.params(image="https://cdn.com/image.jpg"),
        ...         qrb.params(callback_data="unsubscribe", index=0),
        ...     ],
        ... )

    Attributes:
        components: A list of components that make up the card, such as header, body, footer, and buttons.
    """

    components: list[TemplateBaseComponent | dict]

    class _Params(BaseParams):
        def __init__(self, *, params: list[BaseParams], index: int):
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

    @staticmethod
    def params(*, params: list[BaseParams], index: int) -> CarouselCard._Params:
        """
        Fill the parameters for the carousel card.

        Args:
            params: A list of parameters for the components in the media card.
            index: The index of the media card in the carousel (0-based).

        Returns:
            An instance of BaseParams containing the parameters for the card.
        """
        return CarouselCard._Params(
            params=params,
            index=index,
        )


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

    class _Params(BaseParams):
        def __init__(self, *, otp: str):
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

    @staticmethod
    def params(*, otp: str) -> AuthenticationBody._Params:
        """
        Fill the parameters for the authentication body component.

        Args:
            otp: The one-time password or code to be used in the body text. Maximum 15 characters.

        Returns:
            An instance of BaseParams containing the OTP.
        """
        return AuthenticationBody._Params(otp=otp)

    class _LibraryInput(BaseLibraryBodyInput):
        def __init__(
            self,
            *,
            add_contact_number: bool | None = None,
            add_security_recommendation: bool | None = None,
            code_expiration_minutes: bool | None = None,
        ):
            self.add_contact_number = add_contact_number
            self.add_security_recommendation = add_security_recommendation
            self.code_expiration_minutes = code_expiration_minutes

        def to_dict(self) -> dict:
            return {
                k: v
                for k, v in {
                    "add_contact_number": self.add_contact_number,
                    "add_security_recommendation": self.add_security_recommendation,
                    "code_expiration_minutes": self.code_expiration_minutes,
                }
                if v is not None
            }

    @staticmethod
    def library_input(
        *,
        add_contact_number: bool | None = None,
        add_security_recommendation: bool | None = None,
        code_expiration_minutes: bool | None = None,
    ) -> AuthenticationBody._LibraryInput:
        """
        Fill the library body input for the authentication body component.

        Args:
            add_contact_number: Set to ``True`` to include the user's contact number in the body text.
            add_security_recommendation: Set to ``True`` to include the security recommendation in the body text.
            code_expiration_minutes: Set to ``True`` to include the code expiration minutes in the body text.

        Returns:
            An instance of BaseLibraryBodyInput containing the parameters for the authentication body.
        """
        return AuthenticationBody._LibraryInput(
            add_contact_number=add_contact_number,
            add_security_recommendation=add_security_recommendation,
            code_expiration_minutes=code_expiration_minutes,
        )


@dataclasses.dataclass(kw_only=True, slots=True)
class AuthenticationFooter(BaseFooterComponent):
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
        message_send_ttl_seconds: The time-to-live (TTL) for the template message in seconds. (See `Time-to-live (TTL) <https://developers.facebook.com/docs/whatsapp/business-management-api/time-to-live>`_).
    """

    name: str
    language: TemplateLanguage
    category: TemplateCategory
    components: list[TemplateBaseComponent | dict]
    parameter_format: ParamFormat | None = None
    message_send_ttl_seconds: int | None = None
    degrees_of_freedom_spec: DegreesOfFreedomSpec | None = None

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
    HeaderFormatType.GIF: HeaderGIF,
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
        _logger.exception(
            "Failed to parse component: %s. Defaulting to dictionary representation. please update pywa or report this issue.",
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
        message_send_ttl_seconds: The time-to-live (TTL) for the template message in seconds (See `Time-to-live (TTL) <https://developers.facebook.com/docs/whatsapp/business-management-api/time-to-live>`_).
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
        return self._client.compare_templates(self.id, *to, start=start, end=end)

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
        params: list[BaseParams],
        *,
        use_mm_lite_api: bool = False,
        message_activity_sharing: bool | None = None,
        reply_to_message_id: str | None = None,
        tracker: str | CallbackData | None = None,
        sender: str | int | None = None,
    ) -> SentTemplate:
        """
        A shortcut to send a template message to WhatsApp users.

        Args:
            to: The phone ID of the WhatsApp user.
            params: The parameters to fill in the template.
            use_mm_lite_api: Whether to use `Marketing Messages Lite API <https://developers.facebook.com/docs/whatsapp/marketing-messages-lite-api>`_ (optional, default: False).
            message_activity_sharing: Whether to share message activities (e.g. message read) for that specific marketing message to Meta to help optimize marketing messages (optional, only if ``use_mm_lite_api`` is True).
            reply_to_message_id: The ID of the message to reply to (optional).
            tracker: A callback data to track the message (optional, can be a string or a :class:`CallbackData` object).
            sender: The phone ID to send the template from (optional, if not provided, the client's phone ID will be used).
        """
        return self._client.send_template(
            to=to,
            name=self.name,
            language=self.language,
            params=params,
            use_mm_lite_api=use_mm_lite_api,
            message_activity_sharing=message_activity_sharing,
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
        cancel_on_rejection: bool = True,
        cancelers: pywa_filters.Filter = None,
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
            cancel_on_rejection: Whether to cancel the waiting process if the template is rejected. Defaults to True.
            cancelers: A filter to cancel the waiting process.
            timeout: The maximum time to wait for the template to be approved.

        Returns:
            TemplateStatusUpdate: An update containing the status of the template once it is approved.
        """
        if cancel_on_rejection:
            cancelers = (
                cancelers or pywa_filters.false | pywa_filters.template_status_rejected
            )
        return cast(
            TemplateStatusUpdate,
            self._client.listen(
                to=TemplateStatusUpdateListenerIdentifier(template_id=self.id),
                filters=pywa_filters.template_status_approved,
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
