from __future__ import annotations

import datetime

from . import Result
from .flows import FlowActionType
import abc
import dataclasses
import logging
from typing import TYPE_CHECKING, Literal, Iterable

from .others import _ItemFactory
from .. import utils


if TYPE_CHECKING:
    from ..client import WhatsApp

_logger = logging.getLogger(__name__)


class TemplateStatus(utils.StrEnum):
    """
    The status of the template.

    `'Template status' on
    developers.facebook.com
    <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates#template-status>`_

    Attributes:
        APPROVED: The template is approved and can be used.
        DISABLED: The template is disabled and cannot be used.
        IN_APPEAL: The template is in appeal and cannot be used.
        PENDING: The template is pending approval and cannot be used.
        REINSTATED: The template has been reinstated and can be used.
        REJECTED: The template has been rejected and cannot be used.
        PENDING_DELETION: The template is pending deletion and cannot be used.
        FLAGGED: The template has been flagged for review and cannot be used.
        PAUSED: The template is paused and cannot be used.
        ARCHIVED: The template is archived and cannot be used.
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

    UNKNOWN = "UNKNOWN"


class TemplateRejectionReason(utils.StrEnum):
    """
    The reason the template was rejected (if applicable).

    `'Rejection status' on
    developers.facebook.com
    <https://developers.facebook.com/docs/whatsapp/updates-to-pricing/new-template-guidelines#rejected-status>`_

    Attributes:
        PROMOTIONAL: The template was rejected because it was promotional.
        ABUSIVE_CONTENT: The template was rejected because it contained abusive content.
        INCORRECT_CATEGORY: The template was rejected because it was in the wrong category.
        INVALID_FORMAT: The template was rejected because it was in the wrong format.
        SCAM: The template was rejected because it was a scam.
        NONE: The template was not rejected.
    """

    PROMOTIONAL = "PROMOTIONAL"
    ABUSIVE_CONTENT = "ABUSIVE_CONTENT"
    INCORRECT_CATEGORY = "INCORRECT_CATEGORY"
    INVALID_FORMAT = "INVALID_FORMAT"
    TAG_CONTENT_MISMATCH = "TAG_CONTENT_MISMATCH"
    SCAM = "SCAM"
    NONE = "NONE"

    UNKNOWN = "UNKNOWN"


class QualityScoreType(utils.StrEnum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"
    UNKNOWN = "UNKNOWN"


@dataclasses.dataclass(slots=True, kw_only=True)
class LibraryTemplateBodyInputs:
    add_contact_number: bool | None = None
    add_learn_more_link: bool | None = None
    add_security_recommendation: bool | None = None
    add_track_package_link: bool | None = None
    code_expiration_minutes: int | None = None


@dataclasses.dataclass(slots=True, kw_only=True)
class LibraryTemplateButtonInputs:
    type: ComponentType | None = None
    url: dict | None = None
    otp_type: OtpType | None = None
    zero_tap_terms_accepted: bool | None = None
    supported_apps: list[OTPSupportedApp] | None = None


@dataclasses.dataclass(slots=True, frozen=True)
class QualityScore:
    score: QualityScoreType
    date: datetime.datetime

    @classmethod
    def from_dict(cls, data: dict[str, str | int]):
        return cls(
            score=QualityScoreType(data["score"]),
            date=datetime.datetime.fromtimestamp(data["date"]),
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


class HeaderFormatType(utils.StrEnum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    DOCUMENT = "DOCUMENT"
    LOCATION = "LOCATION"
    PRODUCT = "PRODUCT"


class ParamType(utils.StrEnum):
    TEXT = "text"
    CURRENCY = "currency"
    DATE_TIME = "date_time"
    DOCUMENT = "document"
    IMAGE = "image"
    VIDEO = "video"
    LOCATION = "location"
    BUTTON = "button"


class TemplateLanguage(utils.StrEnum):
    """
    Template language and locale code.

    `'Template language and locale code' on
    developers.facebook.com
    <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/supported-languages>`_
    """

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


@dataclasses.dataclass(kw_only=True, slots=True)
class BaseComponent(abc.ABC):
    type: ComponentType

    @classmethod
    def from_dict(cls, data: dict) -> BaseComponent:
        """
        Create a BaseComponent object from a dictionary.

        Args:
            data (dict): The dictionary to convert.

        Returns:
            BaseComponent: The created BaseComponent object.
        """
        return cls(
            **{
                k: v
                for k, v in data.items()
                if k in {f.name for f in dataclasses.fields(cls) if f.init}
            }
        )


# =========== HEADER ===========


@dataclasses.dataclass(kw_only=True, slots=True)
class BaseHeaderComponent(BaseComponent, abc.ABC):
    type: ComponentType = dataclasses.field(
        default=ComponentType.HEADER,
        init=False,
        repr=False,
    )
    format: HeaderFormatType


@dataclasses.dataclass(kw_only=True, slots=True)
class HeaderText(BaseHeaderComponent):
    format: HeaderFormatType = dataclasses.field(
        default=HeaderFormatType.TEXT,
        init=False,
        repr=False,
    )
    text: str
    example: HeaderTextExample | None = None


@dataclasses.dataclass(kw_only=True, slots=True)
class TextNamedParam:
    param_name: str
    example: str


@dataclasses.dataclass(kw_only=True, slots=True)
class HeaderTextExample:
    header_text: list[str] | None = None
    header_text_named_params: list[TextNamedParam] | None = None

    def __post_init__(self):
        if self.header_text is None and self.header_text_named_params is None:
            raise ValueError(
                "Either header_text or header_text_named_params must be provided."
            )
        if self.header_text is not None and self.header_text_named_params is not None:
            raise ValueError(
                "Only one of header_text or header_text_named_params can be provided."
            )


@dataclasses.dataclass(kw_only=True, slots=True)
class HeaderMediaExample:
    header_handle: list[str]


@dataclasses.dataclass(kw_only=True, slots=True)
class HeaderImage(BaseHeaderComponent):
    format: HeaderFormatType = dataclasses.field(
        default=HeaderFormatType.IMAGE,
        init=False,
        repr=False,
    )
    example: HeaderMediaExample


@dataclasses.dataclass(kw_only=True, slots=True)
class HeaderVideo(BaseHeaderComponent):
    format: HeaderFormatType = dataclasses.field(
        default=HeaderFormatType.VIDEO,
        init=False,
        repr=False,
    )
    example: HeaderMediaExample


@dataclasses.dataclass(kw_only=True, slots=True)
class HeaderDocument(BaseHeaderComponent):
    format: HeaderFormatType = dataclasses.field(
        default=HeaderFormatType.DOCUMENT,
        init=False,
        repr=False,
    )
    example: HeaderMediaExample


@dataclasses.dataclass(kw_only=True, slots=True)
class HeaderLocation(BaseHeaderComponent):
    format: HeaderFormatType = dataclasses.field(
        default=HeaderFormatType.LOCATION,
        init=False,
        repr=False,
    )


@dataclasses.dataclass(kw_only=True, slots=True)
class HeaderProduct(BaseHeaderComponent):
    format: HeaderFormatType = dataclasses.field(
        default=HeaderFormatType.PRODUCT,
        init=False,
        repr=False,
    )


# =========== BODY ===========


@dataclasses.dataclass(kw_only=True, slots=True)
class BaseBodyComponent(BaseComponent, abc.ABC):
    type: ComponentType = dataclasses.field(
        default=ComponentType.BODY,
        init=False,
        repr=False,
    )


@dataclasses.dataclass(kw_only=True, slots=True)
class Body(BaseBodyComponent):
    text: str
    example: BodyTextExample | None = None


@dataclasses.dataclass(kw_only=True, slots=True)
class BodyTextExample:
    body_text: list[list[str]] | str | None = None
    body_text_named_params: list[TextNamedParam] | None = None

    def __post_init__(self):
        if self.body_text is None and self.body_text_named_params is None:
            raise ValueError(
                "Either body_text or body_text_named_params must be provided."
            )
        if self.body_text is not None and self.body_text_named_params is not None:
            raise ValueError(
                "Only one of body_text or body_text_named_params can be provided."
            )


# =========== FOOTER ===========


@dataclasses.dataclass(kw_only=True, slots=True)
class BaseFooterComponent(BaseComponent, abc.ABC):
    type: ComponentType = dataclasses.field(
        default=ComponentType.FOOTER,
        init=False,
        repr=False,
    )


@dataclasses.dataclass(kw_only=True, slots=True)
class Footer(BaseFooterComponent):
    text: str


# =========== BUTTONS ===========


@dataclasses.dataclass(kw_only=True, slots=True)
class BaseButtonComponent(BaseComponent, abc.ABC): ...


@dataclasses.dataclass(kw_only=True, slots=True)
class CopyCodeButton(BaseButtonComponent):
    type: ComponentType = dataclasses.field(
        default=ComponentType.COPY_CODE,
        init=False,
        repr=False,
    )
    example: str


class FlowButtonIcon(utils.StrEnum):
    DOCUMENT = "DOCUMENT"
    PROMOTION = "PROMOTION"
    REVIEW = "REVIEW"


@dataclasses.dataclass(kw_only=True, slots=True)
class FlowButton(BaseButtonComponent):
    type: ComponentType = dataclasses.field(
        default=ComponentType.FLOW,
        init=False,
        repr=False,
    )
    flow_id: str | None = None
    flow_name: str | None = None
    flow_json: dict | None = None
    flow_action: Literal[FlowActionType.DATA_EXCHANGE, FlowActionType.NAVIGATE]
    navigate_screen: str | None = None
    icon: FlowButtonIcon | None = None

    def __post_init__(self):
        if self.flow_id is None and self.flow_name is None and self.flow_json is None:
            raise ValueError(
                "Either flow_id, flow_name, or flow_json must be provided."
            )
        if (
            len([x is not None for x in (self.flow_id, self.flow_name, self.flow_json)])
            > 1
        ):
            raise ValueError(
                "Only one of flow_id, flow_name, or flow_json can be provided."
            )


@dataclasses.dataclass(kw_only=True, slots=True)
class PhoneNumberButton(BaseButtonComponent):
    type: ComponentType = dataclasses.field(
        default=ComponentType.PHONE_NUMBER,
        init=False,
        repr=False,
    )
    text: str
    phone_number: str


@dataclasses.dataclass(kw_only=True, slots=True)
class QuickReplyButton(BaseButtonComponent):
    type: ComponentType = dataclasses.field(
        default=ComponentType.QUICK_REPLY,
        init=False,
        repr=False,
    )
    text: str


@dataclasses.dataclass(kw_only=True, slots=True)
class URLButton(BaseButtonComponent):
    type: ComponentType = dataclasses.field(
        default=ComponentType.URL,
        init=False,
        repr=False,
    )
    text: str
    url: str
    example: list[str] | None = None


@dataclasses.dataclass(kw_only=True, slots=True)
class CatalogButton(BaseButtonComponent):
    type: ComponentType = dataclasses.field(
        default=ComponentType.CATALOG,
        init=False,
        repr=False,
    )
    text: str


@dataclasses.dataclass(kw_only=True, slots=True)
class MPMButton(BaseButtonComponent):
    type: ComponentType = dataclasses.field(
        default=ComponentType.MPM,
        init=False,
        repr=False,
    )
    text: str


@dataclasses.dataclass(kw_only=True, slots=True)
class SPMButton(BaseButtonComponent):
    type: ComponentType = dataclasses.field(
        default=ComponentType.SPM,
        init=False,
        repr=False,
    )
    text: str


class OtpType(utils.StrEnum):
    """
    The type of the button

    Attributes:
        COPY_CODE: Copy code button copies the one-time password or code to the user's clipboard.
        ONE_TAP: One-tap autofill button automatically loads and passes your app the one-time password or code.
        ZERO_TAP: Zero-tap autofill button automatically loads and passes your app the one-time password or code
    """

    COPY_CODE = "COPY_CODE"
    ONE_TAP = "ONE_TAP"
    ZERO_TAP = "ZERO_TAP"


@dataclasses.dataclass(kw_only=True, slots=True)
class OTPSupportedApp:
    package_name: str
    signature_hash: str


@dataclasses.dataclass(kw_only=True, slots=True)
class OneTapOTPButton(BaseButtonComponent):
    type: ComponentType = dataclasses.field(
        default=ComponentType.OTP,
        init=False,
        repr=False,
    )
    otp_type: OtpType = dataclasses.field(
        default=OtpType.ONE_TAP,
        init=False,
        repr=False,
    )
    supported_apps: list[OTPSupportedApp]
    text: str | None = None
    autofill_text: str | None = None


@dataclasses.dataclass(kw_only=True, slots=True)
class ZeroTapOTPButton(BaseButtonComponent):
    type: ComponentType = dataclasses.field(
        default=ComponentType.OTP,
        init=False,
        repr=False,
    )
    otp_type: OtpType = dataclasses.field(
        default=OtpType.ZERO_TAP,
        init=False,
        repr=False,
    )
    supported_apps: list[OTPSupportedApp]
    zero_tap_terms_accepted: bool
    text: str | None = None
    autofill_text: str | None = None


@dataclasses.dataclass(kw_only=True, slots=True)
class CopyCodeOTPButton(BaseButtonComponent):
    type: ComponentType = dataclasses.field(
        default=ComponentType.OTP,
        init=False,
        repr=False,
    )
    otp_type: OtpType = dataclasses.field(
        default=OtpType.COPY_CODE,
        init=False,
        repr=False,
    )
    text: str | None = None


@dataclasses.dataclass(kw_only=True, slots=True)
class Buttons(BaseComponent):
    type: ComponentType = dataclasses.field(
        default=ComponentType.BUTTONS,
        init=False,
        repr=False,
    )
    buttons: list[BaseButtonComponent | dict]


# ========== LIMITED TIME OFFER ==========


@dataclasses.dataclass(kw_only=True, slots=True)
class LimitedTimeOfferConfig:
    text: str
    has_expiration: bool


@dataclasses.dataclass(kw_only=True, slots=True)
class LimitedTimeOffer(BaseComponent):
    type: ComponentType = dataclasses.field(
        default=ComponentType.LIMITED_TIME_OFFER,
        init=False,
        repr=False,
    )
    limited_time_offer: LimitedTimeOfferConfig


# ========== CAROUSEL ==========


@dataclasses.dataclass(kw_only=True, slots=True)
class Carousel(BaseComponent):
    type: ComponentType = dataclasses.field(
        default=ComponentType.CAROUSEL,
        init=False,
        repr=False,
    )
    cards: list[CarouselMediaCard]


@dataclasses.dataclass(kw_only=True, slots=True)
class CarouselMediaCard:
    components: list[BaseComponent | dict]


# ========== AUTHENTICATION ==========


@dataclasses.dataclass(kw_only=True, slots=True)
class AuthenticationBody(BaseBodyComponent):
    add_security_recommendation: bool


@dataclasses.dataclass(kw_only=True, slots=True)
class AuthenticationFooter(BaseFooterComponent):
    code_expiration_minutes: int


# ========== TEMPLATE ==========


@dataclasses.dataclass(kw_only=True, slots=True)
class TemplateV2:
    """
    Represents a WhatsApp template.

    Attributes:
        name: The name of the template (should be unique).
        language: The language of the template.
        category: The category of the template (See `Template Categorization <https://developers.facebook.com/docs/whatsapp/updates-to-pricing/new-template-guidelines#template-categorization>`_).
        components: Components that make up the template. Header, body, footer, buttons, cards, etc.
        parameter_format: The type of parameters inside texts (positional or named).
        message_send_ttl_seconds: The time-to-live (TTL) for the template message in seconds. (See `Time-to-live (TTL) <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates#time-to-live--ttl---customization--defaults--min-max-values--and-compatibility>`_).
    """

    name: str
    language: TemplateLanguage
    category: TemplateCategory
    components: list[BaseComponent]
    parameter_format: ParamFormat | None = None
    message_send_ttl_seconds: int | None = None

    def to_dict(self) -> dict:
        return dataclasses.asdict(
            self, dict_factory=lambda d: {k: v for k, v in d if v is not None}
        )


_comp_types_to_component: dict[ComponentType, type[BaseComponent]] = {
    ComponentType.HEADER: BaseHeaderComponent,
    ComponentType.BODY: Body,
    ComponentType.FOOTER: Footer,
    ComponentType.BUTTONS: Buttons,
    ComponentType.CAROUSEL: Carousel,
    ComponentType.LIMITED_TIME_OFFER: LimitedTimeOffer,
    ComponentType.PHONE_NUMBER: PhoneNumberButton,
    ComponentType.URL: URLButton,
    ComponentType.QUICK_REPLY: QuickReplyButton,
    ComponentType.OTP: OneTapOTPButton,
    ComponentType.MPM: MPMButton,
    ComponentType.SPM: SPMButton,
    ComponentType.CATALOG: CatalogButton,
    ComponentType.COPY_CODE: CopyCodeOTPButton,
    ComponentType.FLOW: FlowButton,
}

_header_formats_to_component: dict[HeaderFormatType, type[BaseHeaderComponent]] = {
    HeaderFormatType.TEXT: HeaderText,
    HeaderFormatType.IMAGE: HeaderImage,
    HeaderFormatType.VIDEO: HeaderVideo,
    HeaderFormatType.DOCUMENT: HeaderDocument,
    HeaderFormatType.LOCATION: HeaderLocation,
    HeaderFormatType.PRODUCT: HeaderProduct,
}


def _parse_component(component: dict) -> BaseComponent | dict:
    """
    Parse a component dictionary into a BaseComponent object.

    Args:
        component (dict): The component dictionary to parse.

    Returns:
        BaseComponent: The parsed BaseComponent object.
    """
    try:
        comp_type = ComponentType(component["type"])
    except ValueError:
        _logger.warning(
            "Unknown component type: %s. Defaulting to dictionary representation.",
            component["type"],
        )
        return component
    component_cls = _comp_types_to_component[comp_type]

    if issubclass(component_cls, BaseHeaderComponent):
        try:
            header_format = HeaderFormatType(component["format"])
        except ValueError:
            _logger.warning(
                "Unknown header format: %s. Defaulting to dictionary representation.",
                component["format"],
            )
            return component
        return _header_formats_to_component[header_format].from_dict(component)

    elif issubclass(component_cls, BaseBodyComponent):
        if "add_security_recommendation" in component:
            return AuthenticationBody.from_dict(component)
        elif "text" in component:
            return Body.from_dict(component)
        _logger.warning(
            "Unknown body component: %s. Defaulting to dictionary representation.",
            component,
        )
        return component

    elif issubclass(component_cls, BaseFooterComponent):
        if "code_expiration_minutes" in component:
            return AuthenticationFooter.from_dict(component)
        elif "text" in component:
            return Footer.from_dict(component)
        _logger.warning(
            "Unknown footer component: %s. Defaulting to dictionary representation.",
            component,
        )
        return component

    elif issubclass(component_cls, Buttons):
        return Buttons(
            buttons=[_parse_component(button) for button in component["buttons"]]
        )
    elif issubclass(component_cls, Carousel):
        return Carousel(
            cards=[
                CarouselMediaCard(
                    components=[
                        _parse_component(card_component)
                        for card_component in card["components"]
                    ]
                )
                for card in component["cards"]
            ]
        )
    elif issubclass(component_cls, LimitedTimeOffer):
        return LimitedTimeOffer(
            limited_time_offer=LimitedTimeOfferConfig(
                text=component["limited_time_offer"]["text"],
                has_expiration=component["limited_time_offer"]["has_expiration"],
            )
        )

    try:
        return component_cls.from_dict(component)
    except Exception:
        _logger.warning(
            "Failed to parse component: %s. Defaulting to dictionary representation.",
            component,
        )
        return component


@dataclasses.dataclass(kw_only=True, slots=True)
class RetrievedTemplate(TemplateV2):
    _client: WhatsApp = dataclasses.field(repr=False, hash=False, compare=False)
    id: int
    status: TemplateStatus
    correct_category: TemplateCategory | None
    previous_category: TemplateCategory | None
    rejected_reason: TemplateRejectionReason | None
    library_template_name: str | None
    quality_score: QualityScore | None
    cta_url_link_tracking_opted_out: bool | None
    sub_category: TemplateCategory | None

    @classmethod
    def from_dict(cls, data: dict, client: WhatsApp) -> RetrievedTemplate:
        return RetrievedTemplate(
            _client=client,
            id=int(data["id"]),
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
            sub_category=TemplateCategory(data["sub_category"])
            if "sub_category" in data
            else None,
        )

    def delete(self) -> bool:
        """Delete this template"""
        return self._client.delete_template(
            template_name=self.name, template_id=self.id
        )

    def update(
        self,
        *,
        new_category: TemplateCategory | None = None,
        new_components: list[BaseComponent] | None = None,
        new_message_send_ttl_seconds: int | None = None,
        new_parameter_format: ParamFormat | None = None,
    ) -> bool:
        return self._client.update_template(
            template_id=self.id,
            new_category=new_category,
            new_components=new_components,
            new_message_send_ttl_seconds=new_message_send_ttl_seconds,
            new_parameter_format=new_parameter_format,
        )

    def compare(
        self,
        others: Iterable[int | str],
        start: datetime.datetime,
        end: datetime.datetime,
    ):
        return self._client.compare_templates(
            template_ids=[self.id, *others], start=start, end=end
        )

    def migrate(self): ...

    def send(self): ...


class TemplatesResult(Result[RetrievedTemplate]):
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
        super().__init__(wa=wa, response=response, item_factory=item_factory)
        self.total_count = response["summary"]["total_count"]
        self.message_template_count = response["summary"]["message_template_count"]
        self.message_template_limit = response["summary"]["message_template_limit"]
        self.are_translations_complete = response["summary"][
            "are_translations_complete"
        ]

    def compare(self, start: datetime.datetime, end: datetime.datetime):
        return self._wa.compare_templates(
            template_ids=[t.id for t in self], start=start, end=end
        )
