from __future__ import annotations

import datetime
import functools
import json
import pathlib
import re

from . import Result, FlowJSON
from .base_update import BaseUpdate
from .flows import FlowActionType
import abc
import dataclasses
import logging
from typing import TYPE_CHECKING, Literal, Iterable, BinaryIO
from .others import _ItemFactory
from .. import utils
from .. import _helpers as helpers

if TYPE_CHECKING:
    from ..client import WhatsApp
    from .sent_message import SentTemplate

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
        REJECTED: Indicates the template has been rejected. You can :meth:`~pywa.types.template.Template.update` the template to have it undergo template review again or `appeal <https://developers.facebook.com/docs/whatsapp/message-templates/guidelines/#appeals>`_ the rejection.
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
class _BaseTemplateUpdate(BaseUpdate, abc.ABC):
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
class TemplateStatusUpdate(_BaseTemplateUpdate):
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
            template_id=value["message_template_id"],
            template_name=value["message_template_name"],
            template_language=TemplateLanguage(value["message_template_language"]),
            reason=TemplateRejectionReason(value["reason"])
            if "reason" in value
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
class TemplateCategoryUpdate(_BaseTemplateUpdate):
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
            template_id=value["message_template_id"],
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
class TemplateComponentsUpdate(_BaseTemplateUpdate):
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
            template_id=value["message_template_id"],
            template_name=value["message_template_name"],
            template_language=TemplateLanguage(value["message_template_language"]),
            template_element=value.get("message_template_element"),
            template_title=value.get("message_template_title"),
            template_footer=value.get("message_template_footer"),
            template_buttons=value.get("message_template_buttons"),
        )


@dataclasses.dataclass(slots=True, frozen=True, kw_only=True)
class TemplateQualityUpdate(_BaseTemplateUpdate):
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
            template_id=value["message_template_id"],
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
        body_inputs: Optional inputs for the body of the template.
        button_inputs: Optional inputs for the buttons of the template.
    """

    name: str
    library_template_name: str
    category: TemplateCategory
    language: TemplateLanguage
    body_inputs: LibraryTemplateBodyInputs | None = None
    button_inputs: LibraryTemplateButtonInputs | None = None

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
        url: A dictionary with base_url and url_suffix_example
        otp_type: The type of OTP button, if applicable.
        zero_tap_terms_accepted: Weather the zero tap terms were accepted by the user or not.
        supported_apps: A list of supported apps for the OTP button.
    """

    type: ComponentType | None = None
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
    def from_dict(cls, data: dict[str, str | int]):
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
    __check_value = str.islower
    __modify_value = str.lower

    TEXT = "text"
    CURRENCY = "currency"
    DATE_TIME = "date_time"
    DOCUMENT = "document"
    IMAGE = "image"
    VIDEO = "video"
    LOCATION = "location"
    BUTTON = "button"

    UNKNOWN = "UNKNOWN"


class TemplateLanguage(utils.StrEnum):
    """
    Template language and locale code.

    `'Template language and locale code' on
    developers.facebook.com
    <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/supported-languages>`_
    """

    __check_value = None
    __modify_value = None

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


class TemplateBaseComponent:
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


# =========== HEADER ===========


class BaseHeaderComponent(TemplateBaseComponent, abc.ABC):
    type: ComponentType
    format: HeaderFormatType


class TemplateText:
    """
    Represents a template text with examples for positional or named parameters.

    >>> positionals = TemplateText("Hi {{1}}!, How are you? Get {{2}}% OFF!","David",15)
    >>> named = TemplateText("Hi {{name}}!, How are you? Get {{discount}}% OFF!",name="David",discount=15)
    >>> print(positionals.preview(), named.preview())

    Attributes:
        text: The template text with placeholders for parameters.
        example: A list of positional parameters or a dictionary of named parameters.
        param_format: The format of the parameters (positional or named).
    """

    __slots__ = ("text", "example", "param_format", "_param_type")

    def __init__(self, text: str, *positionals, **named):
        if positionals and named:
            raise ValueError("You can't use both positional and named args!")
        if positionals:
            self.param_format = ParamFormat.POSITIONAL
            self.text = text
            self.example = positionals
        elif named:
            self.param_format = ParamFormat.NAMED
            self.text = text
            self.example = named
        else:
            self.param_format = None
            self.example = None
            self.text = text

        self._param_type: Literal["header", "body", None] = None

    @property
    def param_type(self) -> Literal["header", "body"] | None:
        return self._param_type

    @param_type.setter
    def param_type(self, value: Literal["header", "body"]):
        if self._param_type is not None and self._param_type != value:
            raise ValueError("TemplateText type cannot be changed once set.")
        self._param_type = value

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
        if self.param_type is None:
            raise ValueError(
                "TemplateText must have a param_type set (either 'header' or 'body') before converting to dict."
            )
        match self.param_format:
            case ParamFormat.POSITIONAL:
                return {
                    "text": self.text,
                    "example": {
                        f"{self.param_type}_text": [list(map(str, self.example))]
                        if self.param_type == "body"
                        else list(map(str, self.example))
                    },
                }
            case ParamFormat.NAMED:
                return {
                    "text": self.text,
                    "example": {
                        f"{self.param_type}_text_named_params": [
                            {"param_name": k, "example": str(v)}
                            for k, v in self.example.items()
                        ]
                    },
                }
            case _:
                return {"text": self.text}

    @classmethod
    def from_dict(cls, data: dict) -> TemplateText | str:
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
                        data["text"],
                        **{item["param_name"]: item["example"] for item in example},
                    )
            elif isinstance(example, str):  # {"example": "example"}
                return cls(data["text"], example)
        return data["text"]

    def __repr__(self):
        return f"TemplateText(text={self.text!r}, example={self.example!r}, param_format={self.param_format!r})"


class HeaderText(BaseHeaderComponent):
    """
    Represents a header text component in a template.

    - All templates are limited to one header component
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#text-headers>`_.

    Attributes:
        text: The header text. Can be a string or a :class:`TemplateText` object. 60 character maximum.
    """

    __slots__ = ("type", "format", "text")

    text: str | TemplateText

    def __init__(self, *, text: str | TemplateText):
        self.type = ComponentType.HEADER
        self.format = HeaderFormatType.TEXT
        self.text = text
        if isinstance(self.text, TemplateText):
            self.text.param_type = "header"

    def __repr__(self):
        return f"HeaderText(text={self.text})"

    @classmethod
    def from_dict(cls, data: dict) -> HeaderText:
        return cls(text=TemplateText.from_dict(data))

    def to_dict(self) -> dict[str, str | dict]:
        data = {
            "type": self.type.value,
            "format": self.format.value,
        }
        data.update(
            {"text": self.text} if isinstance(self.text, str) else self.text.to_dict()
        )
        return data


class HeaderMediaExample:
    """
    Represents an example of media used in a header component.

    - Used in :class:`HeaderImage`, :class:`HeaderVideo`, and :class:`HeaderDocument` components.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#media-headers>`_.

    Attributes:
        handle: Uploaded media asset handle. Use the `Resumable Upload API <https://developers.facebook.com/docs/graph-api/guides/upload>`_ to generate an asset handle.
    """

    __slots__ = ("handle",)

    handle: str

    def __init__(self, *, handle: str):
        self.handle = handle

    def __repr__(self):
        return f"HeaderMediaExample(handle={self.handle!r})"

    def to_dict(self) -> dict[str, list[str]]:
        return {"header_handle": [self.handle]}

    @classmethod
    def from_dict(cls, data: dict) -> HeaderMediaExample:
        return cls(handle=data["header_handle"][0])


@dataclasses.dataclass(kw_only=True, slots=True)
class HeaderImage(BaseHeaderComponent):
    """
    Represents a header image component in a template.

    - All templates are limited to one header component.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#media-headers>`_.

    Attributes:
        example: An example of the header image media.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.HEADER,
        init=False,
        repr=False,
    )
    format: HeaderFormatType = dataclasses.field(
        default=HeaderFormatType.IMAGE,
        init=False,
        repr=False,
    )
    example: HeaderMediaExample

    @classmethod
    def from_dict(cls, data: dict) -> HeaderImage:
        return cls(example=HeaderMediaExample.from_dict(data["example"]))


@dataclasses.dataclass(kw_only=True, slots=True)
class HeaderVideo(BaseHeaderComponent):
    """
    Represents a header video component in a template.

    - All templates are limited to one header component.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#media-headers>`_.

    Attributes:
        example: An example of the header video media.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.HEADER,
        init=False,
        repr=False,
    )
    format: HeaderFormatType = dataclasses.field(
        default=HeaderFormatType.VIDEO,
        init=False,
        repr=False,
    )
    example: HeaderMediaExample

    @classmethod
    def from_dict(cls, data: dict) -> HeaderVideo:
        return cls(example=HeaderMediaExample.from_dict(data["example"]))


@dataclasses.dataclass(kw_only=True, slots=True)
class HeaderDocument(BaseHeaderComponent):
    """
    Represents a header document component in a template.

    - All templates are limited to one header component.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#media-headers>`_.

    Attributes:
        example: An example of the header document media.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.HEADER,
        init=False,
        repr=False,
    )
    format: HeaderFormatType = dataclasses.field(
        default=HeaderFormatType.DOCUMENT,
        init=False,
        repr=False,
    )
    example: HeaderMediaExample

    @classmethod
    def from_dict(cls, data: dict) -> HeaderDocument:
        return cls(example=HeaderMediaExample.from_dict(data["example"]))


@dataclasses.dataclass(kw_only=True, slots=True)
class HeaderLocation(BaseHeaderComponent):
    """
    Represents a header location component in a template.

    - All templates are limited to one header component.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#location-headers>`_.
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


@dataclasses.dataclass(kw_only=True, slots=True)
class HeaderProduct(BaseHeaderComponent):
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


# =========== BODY ===========


class BaseBodyComponent(TemplateBaseComponent, abc.ABC):
    type: ComponentType


class Body(BaseBodyComponent):
    """
    The body component represents the core text of your message template and is a text-only template component. It is required for all templates.

    - All templates are limited to one body component.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#body>`_.

    Attributes:
        text: The body text. Can be a string or a :class:`TemplateText` object. 1024 characters maximum.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.BODY,
        init=False,
        repr=False,
    )
    text: str | TemplateText

    def __init__(self, *, text: str | TemplateText):
        self.type = ComponentType.BODY
        self.text = text
        if isinstance(self.text, TemplateText):
            self.text.param_type = "body"

    def __repr__(self):
        return f"Body(text={self.text!r})"

    @classmethod
    def from_dict(cls, data: dict) -> Body:
        return cls(text=TemplateText.from_dict(data))

    def to_dict(self) -> dict[str, str | dict]:
        data = {"type": self.type.value}
        if isinstance(self.text, str):
            data["text"] = self.text
        else:
            data.update(self.text.to_dict())
        return data


# =========== FOOTER ===========


@dataclasses.dataclass(kw_only=True, slots=True)
class BaseFooterComponent(TemplateBaseComponent, abc.ABC):
    type: ComponentType = dataclasses.field(
        default=ComponentType.FOOTER,
        init=False,
        repr=False,
    )


@dataclasses.dataclass(kw_only=True, slots=True)
class Footer(BaseFooterComponent):
    """
    Footers are optional text-only components that appear immediately after the body component. Templates are limited to one footer component.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#footer>`_.

    Attributes:
        text: The footer text. Can be a string or a TemplateText object. 60 characters maximum.
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

    Attributes:
        buttons: A list of button components. Can contain a mixture of :class:`QuickReply
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.BUTTONS,
        init=False,
        repr=False,
    )
    buttons: list[BaseButtonComponent | dict]


@dataclasses.dataclass(kw_only=True, slots=True)
class CopyCodeButton(BaseButtonComponent):
    """
    Copy code buttons copy a text string
    (defined when the template is sent in a template message) to the device's clipboard when tapped by the app user.

    - Templates are limited to one copy code button.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#copy-code-buttons>`_.

    Attributes:
        example: String to be copied to device's clipboard when tapped by the app user. Maximum 15 characters.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.COPY_CODE,
        init=False,
        repr=False,
    )
    example: str


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

    Attributes:
        text: Button label text. 25 characters maximum.
        flow_id: Unique identifier of the Flow provided by WhatsApp. The Flow must be published. Cannot be used with ``flow_name`` or ``flow_json``.
        flow_name: The name of the Flow. Supported in Cloud API only. The Flow ID is stored in the message template, not the name, so changing the Flow name will not affect existing message templates. The Flow must be published. Cannot be used with ``flow_id`` or ``flow_json``.
        flow_json: The JSON representation of the Flow. Cannot be used with ``flow_id`` or ``flow_name``.
        flow_action: navigate or data_exchange. Use ``NAVIGATE`` to predefine the first screen as part of the template message. Use ``DATA_EXCHANGE`` for advanced use-cases where the first screen is provided by your endpoint. Defaults to ``NAVIGATE``.
        navigate_screen: Optional only if ``flow_action`` is ``NAVIGATE``. The id of the entry screen of the Flow. Defaults to the first screen of the Flow.
        icon: Optional icon for the button.

    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.FLOW,
        init=False,
        repr=False,
    )
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
        self.type = ComponentType.FLOW
        self.text = text
        self.flow_id = flow_id
        self.flow_name = flow_name
        self.flow_json = flow_json
        self.flow_action = flow_action
        self.navigate_screen = navigate_screen
        self.icon = icon

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

    def __repr__(self):
        return (
            f"FlowButton(text={self.text!r}, flow_id={self.flow_id!r}, "
            f"flow_name={self.flow_name!r}, flow_json={self.flow_json!r}, "
            f"flow_action={self.flow_action!r}, navigate_screen={self.navigate_screen!r}, "
            f"icon={self.icon!r})"
        )

    def to_dict(self) -> dict[str, str | dict | None]:
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


@dataclasses.dataclass(kw_only=True, slots=True)
class PhoneNumberButton(BaseButtonComponent):
    """
    Phone number buttons call the specified business phone number when tapped by the app user. Templates are limited to one phone number button.

    - Note that some countries have special phone numbers that have leading zeros after the country calling code (e.g., +55-0-955-585-95436). If you assign one of these numbers to the button, the leading zero will be stripped from the number. If your number will not work without the leading zero, assign an alternate number to the button, or add the number as message body text.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#phone-number-buttons>`_.

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
class QuickReplyButton(BaseButtonComponent):
    """
    Quick reply buttons are custom text-only buttons that immediately message you with the specified text string when tapped by the app user. A common use case-case is a button that allows your customer to easily opt-out of any marketing messages.

    - Templates are limited to 10 quick reply buttons. If using quick reply buttons with other buttons, buttons must be organized into two groups: quick reply buttons and non-quick reply buttons. If grouped incorrectly, the API will return an error indicating an invalid combination.
    - Examples of valid groupings:
        Quick Reply, Quick Reply
        Quick Reply, Quick Reply, URL, Phone
        URL, Phone, Quick Reply, Quick Reply

    - Examples of invalid groupings:
        Quick Reply, URL, Quick Reply
        URL, Quick Reply, URL
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#quick-reply-buttons>`_.

    Attributes:
        text: Button label text. 25 characters maximum.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.QUICK_REPLY,
        init=False,
        repr=False,
    )
    text: str


class URLButton(BaseButtonComponent):
    """
    URL buttons load the specified URL in the device's default web browser when tapped by the app user. Templates are limited to two URL buttons.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components#url-buttons>`_.

    Attributes:
        text: Button label text. 25 characters maximum.
        url: URL of website that loads in the device's default mobile web browser when the button is tapped by the app user. Supports 1 variable, appended to the end of the URL string. Maximum 2000 characters.
        example: Example URL to be used in the template. Maximum 2000 characters.
    """

    text: str
    url: str
    example: str | None

    def __init__(self, *, text: str, url: str, example: str | None = None):
        self.type = ComponentType.URL
        self.text = text
        self.url = url
        self.example = example

    def to_dict(self) -> dict[str, str | list[str]]:
        data: dict[str, str | list[str]] = {
            "type": self.type.value,
            "text": self.text,
            "url": self.url,
        }
        if self.example:
            data["example"] = [self.example]
        return data

    def __repr__(self):
        return (
            f"URLButton(text={self.text!r}, url={self.url!r}, example={self.example!r})"
        )

    @classmethod
    def from_dict(cls, data: dict) -> URLButton:
        return cls(
            text=data["text"],
            url=data["url"],
            example=[data["example"][0]] if "example" in data else None,
        )


@dataclasses.dataclass(kw_only=True, slots=True)
class CatalogButton(BaseButtonComponent):
    """
    Catalog templates are marketing templates that allow you to showcase your product catalog entirely within WhatsApp. Catalog templates display a product thumbnail header image of your choice and custom body text, along with a fixed text header and fixed text sub-header.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/catalog-templates>`_.

    Attributes:
        text: Button label text. 25 characters maximum.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.CATALOG,
        init=False,
        repr=False,
    )
    text: str


@dataclasses.dataclass(kw_only=True, slots=True)
class MPMButton(BaseButtonComponent):
    """
    Multi-product message (MPM) buttons are special, non-customizable buttons that, when tapped, display up to 30 products from your ecommerce catalog, organized in up to 10 sections, in a single message.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/mpm-templates>`_.

    Attributes:
        text: Button label text. 25 characters maximum.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.MPM,
        init=False,
        repr=False,
    )
    text: str


@dataclasses.dataclass(kw_only=True, slots=True)
class SPMButton(BaseButtonComponent):
    """
    Single-product message (SPM) buttons are special, non-customizable buttons that can be mapped to a product in your product catalog. When tapped, they load details about the product, which it pulls from your catalog. Users can then add the product to their cart and place an order.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/spm-templates>`_.

    Attributes:
        text: Button label text. 25 characters maximum.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.SPM,
        init=False,
        repr=False,
    )
    text: str


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

    Attributes:
        package_name: Your Android app's package name. Maximum 224 characters.
        signature_hash: Your app signing key hash. See `App Signing Key Hash <https://developers.facebook.com/docs/whatsapp/business-management-api/authentication-templates/autofill-button-authentication-templates#app-signing-key-hash>`_. Must be exactly 11 characters.
    """

    package_name: str
    signature_hash: str


@dataclasses.dataclass(kw_only=True, slots=True)
class OneTapOTPButton(BaseButtonComponent):
    """
    One-tap autofill authentication templates allow you to send a one-time password or code along with an one-tap autofill button to your users. When a WhatsApp user taps the autofill button, the WhatsApp client triggers an activity which opens your app and delivers it the password or code.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/authentication-templates/autofill-button-authentication-templates>`_.
    - Read more about `Authentication Templates <https://developers.facebook.com/docs/whatsapp/business-management-api/authentication-templates>`_.

    Attributes:
        text: Copy code button label text. If omitted, the text will default to a pre-set value localized to the template's language. For example, ``Copy Code`` for English (US). Maximum 25 characters.
        autofill_text: One-tap autofill button label text. If omitted, the autofill text will default to a pre-set value, localized to the template's language. For example, ``Autofill`` for English (US). Maximum 25 characters.
        supported_apps: The supported_apps array allows you define pairs of app package names and signing key hashes for up to 5 apps. This can be useful if you have different app builds and want each of them to be able to initiate the handshake. Read more about `Supported Apps <https://developers.facebook.com/docs/whatsapp/business-management-api/authentication-templates/autofill-button-authentication-templates#supported-apps>`_.
    """

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
    text: str | None = None
    autofill_text: str | None = None
    supported_apps: list[OTPSupportedApp]


@dataclasses.dataclass(kw_only=True, slots=True)
class ZeroTapOTPButton(BaseButtonComponent):
    """
    Zero-tap authentication templates allow your users to receive one-time passwords or codes via WhatsApp without having to leave your app.

    When a user in your app requests a password or code and you deliver it using a zero-tap authentication template, the WhatsApp client simply broadcasts the included password or code and your app can capture it immediately with a broadcast receiver.
    From your user's perspective, they request a password or code in your app and it appears in your app automatically. If your app user happens to check the message in the WhatsApp client, they will only see a message displaying the default fixed text: < code > is your verification code.
    Like one-tap autofill button authentication templates, when the WhatsApp client receives the template message containing the user's password or code, we perform a series of eligibility checks. If the message fails this check and we are unable to broadcast the password or code, the message will display either a one-tap autofill button or a copy code button. For this reason, when you create a zero-tap authentication template, you must include a one-tap autofill and copy code button in your post body payload, even if the user may never see one of these buttons.

    - Zero-tap is only supported on Android. If you send a zero-tap authentication template to a WhatsApp user who is using a non-Android device, the WhatsApp client will display a copy code button instead.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/authentication-templates/zero-tap-authentication-templates>`_.
    - Read more about `Authentication Templates <https://developers.facebook.com/docs/whatsapp/business-management-api/authentication-templates>`_.

    Attributes:
        text: Copy code button label text. If omitted, the text will default to a pre-set value localized to the template's language. For example, ``Copy Code`` for English (US). Maximum 25 characters.
        autofill_text: One-tap autofill button label text. If omitted, the autofill text will default to a pre-set value, localized to the template's language. For example, ``Autofill`` for English (US). Maximum 25 characters.
        zero_tap_terms_accepted: Set to ``True`` to indicate that you understand that your use of zero-tap authentication is subject to the WhatsApp Business Terms of Service, and that it's your responsibility to ensure your customers expect that the code will be automatically filled in on their behalf when they choose to receive the zero-tap code through WhatsApp. If set to ``False``, the template will **not** be created as you need to accept zero-tap terms before creating zero-tap enabled message templates.
        supported_apps: The supported_apps array allows you define pairs of app package names and signing key hashes for up to 5 apps. This can be useful if you have different app builds and want each of them to be able to initiate the handshake. Read more about `Supported Apps <https://developers.facebook.com/docs/whatsapp/business-management-api/authentication-templates/zero-tap-authentication-templates#supported-apps>`_.
    """

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
    text: str | None = None
    autofill_text: str | None = None
    zero_tap_terms_accepted: bool
    supported_apps: list[OTPSupportedApp]


@dataclasses.dataclass(kw_only=True, slots=True)
class CopyCodeOTPButton(BaseButtonComponent):
    """
    Copy code authentication templates allow you to send a one-time password or code along with a copy code button to your users. When a WhatsApp user taps the copy code button, the WhatsApp client copies the password or code to the device's clipboard. The user can then switch to your app and paste the password or code into your app.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/authentication-templates/copy-code-button-authentication-templates>`_.
    - Read more about `Authentication Templates <https://developers.facebook.com/docs/whatsapp/business-management-api/authentication-templates>`_.

    Attributes:
        text: Copy code button label text. If omitted, the text will default to a pre-set value localized to the template's language. For example, ``Copy Code`` for English (US). Maximum 25 characters.
    """

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


# ========== LIMITED TIME OFFER ==========


@dataclasses.dataclass(kw_only=True, slots=True)
class LimitedTimeOfferConfig:
    """
    Configuration for a limited-time offer in a WhatsApp template.

    Attributes:
        text: Offer details text. Maximum 16 characters.
        has_expiration: Set to ``True`` to have the `offer expiration details <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/limited-time-offer-templates#offer-expiration-details>`_ appear in the delivered message.
    """

    text: str
    has_expiration: bool | None = None


@dataclasses.dataclass(kw_only=True, slots=True)
class LimitedTimeOffer(TemplateBaseComponent):
    """
    Limited-time offer templates allow you to display expiration dates and running countdown timers for offer codes in template messages, making it easy for you to communicate time-bound offers and drive customer engagement.

    - Only templates categorized as MARKETING are supported.
    - Footer components are not supported.
    - Users who view a limited-time offer template message using that WhatsApp web app or desktop app will not see the offer, but will instead see a message indicating that they have received a message but that it's not supported in the client they are using.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/limited-time-offer-templates>`_.

    Attributes:
        limited_time_offer: Configuration for the limited-time offer, including text and expiration settings.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.LIMITED_TIME_OFFER,
        init=False,
        repr=False,
    )
    limited_time_offer: LimitedTimeOfferConfig


# ========== CAROUSEL ==========


@dataclasses.dataclass(kw_only=True, slots=True)
class Carousel(TemplateBaseComponent):
    """
    Media card carousel templates allow you to send a single text message accompanied by a set of up to 10 media cards in a horizontally scrollable view:

    Carousel templates are composed of message body text and up to 10 media cards. Each card in the template has an :class:`HeaderImage` or :class:`HeaderVideo` header asset, card :class:`Body`, and up to two buttons. Button combinations can be a mix of :class:`QuickReplyButton` buttons, :class:`PhoneNumberButton` buttons, and :class:`URLButton` buttons.

    - All cards defined on a template must have the same components.
    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/media-card-carousel-templates>`_.

    Attributes:
        cards: A list of :class:`CarouselMediaCard` objects, each representing a media card in the carousel.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.CAROUSEL,
        init=False,
        repr=False,
    )
    cards: list[CarouselMediaCard]


@dataclasses.dataclass(kw_only=True, slots=True)
class CarouselMediaCard:
    """
    Carousel templates are composed of message body text and up to 10 media cards. Each card in the template has an :class:`HeaderImage` or :class:`HeaderVideo` header asset, card :class:`Body`, and up to two buttons. Button combinations can be a mix of :class:`QuickReplyButton` buttons, :class:`PhoneNumberButton` buttons, and :class:`URLButton` buttons.

    Attributes:
        components: A list of components that make up the media card, such as header, body, footer, and buttons.
    """

    components: list[TemplateBaseComponent | dict]


# ========== AUTHENTICATION ==========


@dataclasses.dataclass(kw_only=True, slots=True)
class AuthenticationBody(BaseBodyComponent):
    """
    Authentication body component for Authentication templates.

    Attributes:
        add_security_recommendation: Set to ``True`` if you want the template to include the string `For your security, do not share this code`. Set to ``False`` to exclude the string.
    """

    type: ComponentType = dataclasses.field(
        default=ComponentType.BODY,
        init=False,
        repr=False,
    )
    add_security_recommendation: bool | None = None


@dataclasses.dataclass(kw_only=True, slots=True)
class AuthenticationFooter(BaseFooterComponent):
    """
    Authentication footer component for Authentication templates.

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

    Attributes:
        name: The name of the template (should be unique, maximum 512 characters).
        language: The language of the template (See `Supported Languages <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/supported-languages>`_).
        category: The category of the template (See `Template Categorization <https://developers.facebook.com/docs/whatsapp/updates-to-pricing/new-template-guidelines#template-categorization>`_).
        components: Components that make up the template. Header, Body, Footer, Buttons, Cards, etc. (See `Template Components <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components>`_).
        parameter_format: The type of parameter formatting the Header and Body components of the template will use. Defaults to ``POSITIONAL``.
        message_send_ttl_seconds: The time-to-live (TTL) for the template message in seconds. (See `Time-to-live (TTL) <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates#time-to-live--ttl---customization--defaults--min-max-values--and-compatibility>`_).
    """

    name: str
    language: TemplateLanguage
    category: TemplateCategory
    components: list[TemplateBaseComponent]
    parameter_format: ParamFormat | None = None
    message_send_ttl_seconds: int | None = None

    def to_json(self) -> str:
        """
        Convert the template to a JSON string representation.
        """
        return _template_to_json(self)


_comp_types_to_component: dict[ComponentType, type[TemplateBaseComponent]] = {
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
        return header_cls.from_dict(component)

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
class TemplateDetails(Template):
    """
    Represents the details of an existing WhatsApp Template.

    Attributes:
        id: The unique identifier of the template.
        name: The name of the template.
        status: The status of the template (See `Template Status <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates#template-status>`_).
        category: The category of the template (See `Template Categorization <https://developers.facebook.com/docs/whatsapp/updates-to-pricing/new-template-guidelines#template-categorization>`_).
        language: The language of the template (See `Supported Languages <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/supported-languages>`_).
        components: Components that make up the template. Header, Body, Footer, Buttons, Cards, etc. (See `Template Components <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components>`_).
        parameter_format: The type of parameter formatting the Header and Body components of the template will use.
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
    status: TemplateStatus
    correct_category: TemplateCategory | None
    previous_category: TemplateCategory | None
    rejected_reason: TemplateRejectionReason | None
    library_template_name: str | None
    quality_score: QualityScore | None
    cta_url_link_tracking_opted_out: bool | None
    sub_category: TemplateCategory | None

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
            sub_category=TemplateCategory(data["sub_category"])
            if "sub_category" in data
            else None,
        )

    def to_json(self) -> str:
        """
        Convert the template to a JSON string representation.
        """
        return _template_to_json(self)

    def delete(self) -> bool:
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
    ) -> bool:
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
        if self._client.update_template(
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
            return True
        return False

    def compare(
        self,
        to: Iterable[int | str],
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
            template_id=self.id, template_ids=to, start=start, end=end
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

    def send(self) -> SentTemplate: ...


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
    ):
        super().__init__(
            wa=wa,
            response=response,
            item_factory=functools.partial(
                TemplateDetails.from_dict,
                client=wa,
            ),
        )
        self.total_count = response["summary"]["total_count"]
        self.message_template_count = response["summary"]["message_template_count"]
        self.message_template_limit = response["summary"]["message_template_limit"]
        self.are_translations_complete = response["summary"][
            "are_translations_complete"
        ]


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
    top_block_reason: dict[str, str] | None = None

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
                    item["key"]: item["value"]
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
class CreatedTemplate:
    """
    Represents a created WhatsApp Template.

    Attributes:
        id: the template ID.
        status: the template status.
        category: the template category.
    """

    _client: WhatsApp = dataclasses.field(repr=False, hash=False, compare=False)

    id: str
    status: TemplateStatus
    category: TemplateCategory

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

    def get(self) -> TemplateDetails:
        """
        Retrieve the details of the created template.

        Returns:
            TemplateDetails: The details of the created template.
        """
        return self._client.get_template(template_id=self.id)
