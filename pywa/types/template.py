from __future__ import annotations

__all__ = [
    'Template',
    'TemplateResponse',
    'AuthenticationTemplate',
]

import abc
import re
from dataclasses import dataclass, field
from typing import Iterable
from pywa import utils

DEFAULT = object()


def _extract_examples(
        string: str,
        start: str = '{',
        end: str = '}'
) -> tuple[str, tuple[str]]:
    """
    Extracts the examples from a string.

    Example:

        >>> _extract_examples('Hello, {john}, today is {day}')
        ('Hello, {{0}}, today is {{1}}', ('john', 'day'))
        >>> _extract_examples('Hello, (john), today is (day)', start='(', end=')')

    Args:
      string: The string to extract the examples from.
      start: The start of the example (default: ``'{'``).
      end: The end of the example (default: ``'}'``).

    Returns:
      A tuple of the formatted string and the examples.
    """
    examples: list[str] = []
    for example in re.finditer(r'\%s(.*?)\%s' % (start, end), string):
        examples.append(example.group(1))
    for idx, example in enumerate(examples):
        string = string.replace(f"{start}{example}{end}", "{{" + str(idx) + "}}")
    return string, tuple(examples)


@dataclass(frozen=True, slots=True)
class TemplateResponse(utils.FromDict):
    """

    Attributes:
        id: Template ID.

    """
    id: str
    status: str
    category: Template.Category


class TemplateComponentType(utils.StrEnum):
    HEADER = 'HEADER'
    BODY = 'BODY'
    FOOTER = 'FOOTER'
    BUTTONS = 'BUTTONS'


class TemplateHeaderFormatType(utils.StrEnum):
    TEXT = 'TEXT'
    IMAGE = 'IMAGE'
    VIDEO = 'VIDEO'
    DOCUMENT = 'DOCUMENT'
    LOCATION = 'LOCATION'


class TemplateButtonType(utils.StrEnum):
    PHONE_NUMBER = 'PHONE_NUMBER'
    URL = 'URL'
    QUICK_REPLY = 'QUICK_REPLY'
    OTP = 'OTP'


class TemplateComponentABC(abc.ABC):
    @property
    @abc.abstractmethod
    def type(self) -> TemplateComponentType: ...


class TemplateHeaderABC(TemplateComponentABC, abc.ABC):
    @property
    @abc.abstractmethod
    def format(self) -> TemplateHeaderFormatType: ...


class ButtonABC(abc.ABC):
    @property
    @abc.abstractmethod
    def type(self) -> TemplateButtonType: ...


@dataclass(frozen=True, slots=True)
class Template:
    """
    Represents a template.

    Attributes:
        body: Body of the template.
        header: Header of the template (optional).
        footer: Footer of the template (optional).
        buttons: Buttons to send with the template (optional).

    Example:

        >>> from pywa.types import Template as Temp
        >>> Temp(
        ...     header=Temp.TextHeader(text='Hello, {John}!'),
        ...     body=Temp.Body(
        ...         text='Shop now through {the end of August} and use '
        ...                 'code {25OF} to get {25%} off of all merchandise',
        ...     ),
        ...     footer=Temp.Footer(text='Use the link below to log in to your account.'),
        ...     buttons=[
        ...         Temp.PhoneNumberButton(title='Call Us', phone_number='12125552368'),
        ...         Temp.UrlButton(
        ...             title='Log In',
        ...             url='https://x.com/login?email={john@example}'
        ...         )
        ...     ]
        ... )


    Templates are limited to 10 quick reply buttons. If using quick reply buttons with other buttons, buttons must be
    organized into two groups: quick reply buttons and non-quick reply buttons. If grouped incorrectly, error will be
    raised when submitting the template.

    Examples of valid groupings:
        - ``Quick Reply``, ``Quick Reply``
        - ``Quick Reply``, ``Quick Reply``, ``URL``, ``Phone``
        - ``URL``, ``Phone``, ``Quick Reply``, ``Quick Reply``

    Examples of invalid groupings:
        - ``Quick Reply``, ``URL``, ``Quick Reply``
        - ``URL``, ``Quick Reply``, ``URL``

    When using the Cloud API to send a template that has multiple quick reply buttons, you can use the index property
    to designate the order in which buttons appear in the template message.
    """
    body: Body
    header: TextHeader | ImageHeader | VideoHeader | DocumentHeader | LocationHeader | None = None
    footer: Footer | None = None
    buttons: Iterable[PhoneNumberButton | UrlButton | QuickReplyButton] | None = None

    class Category(utils.StrEnum):
        """
        Template category.
    
        `\`Template Categorization\` on
        developers.facebook.com
        <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates#categories>`_
        """
        AUTHENTICATION = 'AUTHENTICATION'
        MARKETING = 'MARKETING'
        UTILITY = 'UTILITY'

    @dataclass(frozen=True, slots=True)
    class TextHeader(TemplateHeaderABC):
        """
        Represents a text header.
    
        Example:
    
            >>> from pywa.types import Template
            >>> Template.TextHeader(text='Hello, {John}!')
    
        Attributes:
            text: Text to send with the header (Up to 60 characters. Supports 1 variable)
        """
        type: TemplateComponentType = field(default=TemplateComponentType.HEADER, init=False)
        format: TemplateHeaderFormatType = field(default=TemplateHeaderFormatType.TEXT, init=False)
        text: str

        def to_dict(self, formatting: tuple[str, str] = None) -> dict[str, str | None]:
            formatted_text, examples = _extract_examples(self.text, *(formatting if formatting else ()))
            return dict(
                type=self.type.value,
                format=self.format.value,
                text=formatted_text,
                **(dict(example=dict(header_text=examples)) if examples else {})
            )

    @dataclass(frozen=True, slots=True)
    class ImageHeader(TemplateHeaderABC):
        """
        Represents an image header.
    
        Example:
            >>> from pywa.types.template import Template
            >>> Template.ImageHeader(examples=["2:c2FtcGxl..."])
    
        Attributes:
            examples: List of image handles (Use the `Resumable Upload API
             <https://developers.facebook.com/docs/graph-api/guides/upload>`_ to upload the images)
        """
        type: TemplateComponentType = field(default=TemplateComponentType.HEADER, init=False)
        format: TemplateHeaderFormatType = field(default=TemplateHeaderFormatType.IMAGE, init=False)
        examples: Iterable[str]

        def to_dict(self) -> dict[str, str | dict[str, tuple[str, ...]]]:
            return dict(
                type=self.type.value,
                format=self.format.value,
                example=dict(header_handle=tuple(self.examples))
            )

    @dataclass(frozen=True, slots=True)
    class VideoHeader(TemplateHeaderABC):
        """
        Represents a video header.
    
        Example:
            >>> from pywa.types import Template
            >>> Template.VideoHeader(examples=["2:c2FtcGxl..."])
    
        Attributes:
            examples: List of video handles (Use the `Resumable Upload API
             <https://developers.facebook.com/docs/graph-api/guides/upload>`_ to upload the videos)
        """
        type: TemplateComponentType = field(default=TemplateComponentType.HEADER, init=False)
        format: TemplateHeaderFormatType = field(default=TemplateHeaderFormatType.VIDEO, init=False)
        examples: Iterable[str]

        def to_dict(self) -> dict[str, str | dict[str, tuple[str, ...]]]:
            return dict(
                type=self.type.value,
                format=self.format.value,
                example=dict(header_handle=tuple(self.examples))
            )

    @dataclass(frozen=True, slots=True)
    class DocumentHeader(TemplateHeaderABC):
        """
        Represents a document header.
    
        Example:
            >>> from pywa.types.template import Template
            >>> Template.DocumentHeader(examples=["2:c2FtcGxl..."])
    
        Attributes:
            examples: List of document handles (Use the `Resumable Upload API
             <https://developers.facebook.com/docs/graph-api/guides/upload>`_ to upload the documents)
        """
        type: TemplateComponentType = field(default=TemplateComponentType.HEADER, init=False)
        format: TemplateHeaderFormatType = field(default=TemplateHeaderFormatType.DOCUMENT, init=False)
        examples: Iterable[str]

        def to_dict(self) -> dict[str, str | dict[str, tuple[str, ...]]]:
            return dict(
                type=self.type.value,
                format=self.format.value,
                example=dict(header_handle=tuple(self.examples))
            )

    @dataclass(frozen=True, slots=True)
    class LocationHeader(TemplateHeaderABC):
        """
        Location headers appear as generic maps at the top of the template and are useful for order tracking, delivery
        updates, ride hailing pickup/dropoff, locating physical stores, etc. When tapped, the app user's default map app
        will open and load the specified location. Locations are specified when you send the template.
    
        - Location headers can only be used in templates categorized as ``UTILITY`` or ``MARKETING``. Real-time locations are not supported.
    
        Example:
            >>> from pywa.types import Template
            >>> Template.LocationHeader()
        """
        type: TemplateComponentType = field(default=TemplateComponentType.HEADER, init=False)
        format: TemplateHeaderFormatType = field(default=TemplateHeaderFormatType.LOCATION, init=False)

        def to_dict(self) -> dict[str, str]:
            return dict(
                type=self.type.value,
                format=self.format.value,
            )

    @dataclass(frozen=True, slots=True)
    class Body(TemplateComponentABC):
        """
        Represents a template body.
    
        Example:
    
            >>> from pywa.types import Template
            >>> Template.Body(
            ...     text='Shop now through {the end of August} and '
            ...         'use code {25OF} to get {25%} off of all merchandise',
            ... )
    
        Attributes:
            text: Text to send with the body (Up to 1024 characters. Supports multiple variables).
        """
        type: TemplateComponentType = field(default=TemplateComponentType.BODY, init=False)
        text: str

        def to_dict(self, formatting: tuple[str, str] = None) -> dict[str, str | None]:
            formatted_text, examples = _extract_examples(self.text, *(formatting if formatting else ()))
            return dict(
                type=self.type.value,
                text=formatted_text,
                **(dict(example=dict(body_text=examples)) if examples else {})
            )

    @dataclass(frozen=True, slots=True)
    class Footer(TemplateComponentABC):
        """
        Represents a template footer.
    
        Example:
            >>> from pywa.types.template import Template
            >>> Template.Footer(text='Use the link below to log in to your account.')
    
        Attributes:
            text: Text to send with the footer (Up to 60 characters, no variables allowed).
        """
        type: TemplateComponentType = field(default=TemplateComponentType.FOOTER, init=False)
        text: str

        def to_dict(self) -> dict[str, str | None]:
            return dict(
                type=self.type.value,
                text=self.text
            )

    @dataclass(frozen=True, slots=True)
    class PhoneNumberButton(ButtonABC):
        """
        Phone number buttons call the specified business phone number when tapped by the app user.
        Templates are limited to one phone number button.

        Example:
            >>> from pywa.types import Template
            >>> Template.PhoneNumberButton(title='Call Us', phone_number='12125552368')

        Attributes:
            title: Button text (Up to 25 characters, no variables allowed).
            phone_number: Alphanumeric string. Business phone number to be (display phone number)
             called when the user taps the button (Up to 20 characters, no variables allowed).
        """
        type: TemplateButtonType = field(default=TemplateButtonType.PHONE_NUMBER, init=False)
        title: str
        phone_number: int | str

        def to_dict(self, formatting: None = None) -> dict[str, str]:
            return dict(type=self.type.value, text=self.title, phone_number=str(self.phone_number))

    @dataclass(frozen=True, slots=True)
    class UrlButton(ButtonABC):
        """
        URL buttons load the specified URL in the device's default web browser when tapped by the app user.
        Templates are limited to two URL buttons.

        Example:
            >>> from pywa.types import Template
            >>> Template.UrlButton(
            ...     title='Log In',
            ...     url='https://x.com/login?email={john@example}'
            ... )

        Attributes:
            title: Button text (Up to 25 characters, supports 1 variable).
            url: URL to be loaded when the user taps the button (Up to 2000 characters, supports 1 variable
             appended to the end of the URL).
        """
        type: TemplateComponentType = field(default=TemplateButtonType.URL, init=False)
        title: str
        url: str

        def to_dict(self, formatting: tuple[str, str] = None) -> dict[str, str]:
            formatted_title, title_examples = _extract_examples(self.title, *(formatting if formatting else ()))
            formatted_url, url_examples = _extract_examples(self.url, *(formatting if formatting else ()))
            examples = title_examples + url_examples
            return dict(
                type=self.type.value,
                text=formatted_title,
                url=formatted_url,
                **(dict(example=tuple(examples)) if examples else {})
            )

    @dataclass(frozen=True, slots=True)
    class QuickReplyButton(ButtonABC):
        """
        Quick reply buttons are custom text-only buttons that immediately message you with the specified text string when
        tapped by the app user. A common use case-case is a button that allows your customer to easily opt-out of any
        marketing messages.

        Templates are limited to 10 quick reply buttons. If using quick reply buttons with other buttons, buttons must be
        organized into two groups: quick reply buttons and non-quick reply buttons. If grouped incorrectly, the API will
        return an error indicating an invalid combination.

        Example:

            >>> from pywa.types import Template
            >>> Template.QuickReplyButton(text='Unsubscribe from Promos')
            >>> Template.QuickReplyButton(text='Unsubscribe from All')

        Attributes:
            text: The text to send when the user taps the button (Up to 25 characters, no variables allowed).
        """
        type: TemplateComponentType = field(default=TemplateButtonType.QUICK_REPLY, init=False)
        text: str

        def to_dict(self, formatting: None = None) -> dict[str, str]:
            return dict(type=self.type.value, text=self.text)

    def to_dict(
            self,
            formatting: tuple[str, str] = None
    ) -> tuple[dict[str, str | None] | dict[str, str] | dict[str, str | tuple[dict[str, str], ...]], ...]:
        return tuple(component for component in (
            self.body.to_dict(formatting),
            self.header.to_dict(formatting) if self.header else None,
            self.footer.to_dict() if self.footer else None,
            dict(
                type=TemplateComponentType.BUTTONS.value,
                buttons=tuple(button.to_dict(formatting) for button in self.buttons)
            ) if self.buttons else None
        ) if component is not None)


@dataclass(frozen=True, slots=True)
class AuthenticationTemplate:
    """
    Represents an authentication template.

    Example:

        >>> from pywa.types import AuthenticationTemplate as AuthTemp
        >>> AuthTemp(
        ...     button=AuthTemp.OTPButton(
        ...         otp_type=AuthTemp.OTPButton.OtpType.ONE_TAP,
        ...         title='Copy Code',
        ...         autofill_text='Autofill',
        ...         package_name='com.example.app',
        ...         signature_hash='1234567890ABCDEF1234567890ABCDEF12345678'
        ...     ),
        ...     code_expiration_minutes=5,
        ...     add_security_recommendation=True
        ... )

    Attributes:
        button: Button to send with the template.
        code_expiration_minutes: Indicates number of minutes the password or code is valid. If omitted, the code
         expiration warning will not be displayed in the delivered message. (Minimum ``1``, maximum ``90``).
        add_security_recommendation: Set to ``True`` if you want the template to include the string, ``"For your security,
         do not share this code"``. Set to ``False`` to exclude the string. Defaults to ``False``.
    """
    button: OTPButton
    code_expiration_minutes: int | None = None
    add_security_recommendation: bool = False

    @dataclass(frozen=True, slots=True)
    class OTPButton(ButtonABC):
        """
        Represents a button that can be used to send an OTP.

        Example for ONE_TAP:

            >>> from pywa.types import AuthenticationTemplate as AuthTemp
            >>> AuthTemp.OTPButton(
            ...     otp_type=AuthTemp.OTPButton.OtpType.ONE_TAP,
            ...     title='Copy Code',
            ...     autofill_text='Autofill',
            ...     package_name='com.example.app',
            ...     signature_hash='1234567890ABCDEF1234567890ABCDEF12345678'
            ... )

        Example for COPY_CODE:

            >>> from pywa.types import AuthenticationTemplate as AuthTemp
            >>> AuthTemp.OTPButton(
            ...     otp_type=AuthTemp.OTPButton.OtpType.COPY_CODE,
            ...     title='Copy Code'
            ... )


        Attributes:
            otp_type: Type of OTP to send. A copy code button copies the one-time password or code to the user's clipboard.
             The user can then manually switch to your app and paste the password or code into your app's interface. A
             one-tap autofill button automatically loads and passes your app the one-time password or code.
            title: Copy code button text. If omitted, the text will default to a pre-set value localized to the template's
             language. For example, ``Copy Code`` for English (US).
            autofill_text: One-tap autofill button text. If omitted, the text will default to a pre-set value localized to
                the template's language. For example, ``Autofill`` for English (US).
            package_name: Android package name of your app. Required if ``otp_type`` is ``OtpType.ONE_TAP``.
            signature_hash: Your app signing key hash. See `App Signing Key Hash
             <https://developers.facebook.com/docs/whatsapp/business-management-api/authentication-templates#app-signing-key-hash>`_
                for more information. Required if ``otp_type`` is ``OtpType.ONE_TAP``.
        """
        type: TemplateComponentType = field(default=TemplateButtonType.OTP, init=False)
        otp_type: OtpType
        title: str | None = None
        autofill_text: str | None = None
        package_name: str | None = None
        signature_hash: str | None = None

        class OtpType(utils.StrEnum):
            """The type of the button"""
            COPY_CODE = 'COPY_CODE'
            ONE_TAP = 'ONE_TAP'

        def __post_init__(self):
            if self.otp_type == self.OtpType.ONE_TAP and not (self.package_name and self.signature_hash):
                raise ValueError('package_name and signature_hash are required for ONE_TAP')

        def to_dict(self) -> dict[str, str | None]:
            base = dict(type=self.type.value, otp_type=self.otp_type.value, text=self.title)
            if self.otp_type == self.OtpType.ONE_TAP:
                base.update(
                    package_name=self.package_name,
                    signature_hash=self.signature_hash,
                    **(dict(autofill_text=self.autofill_text) if self.autofill_text else {})
                )
            return base

    def to_dict(self) -> tuple[dict[str, str | None] | dict[str, str] | dict[str, str | tuple[dict[str, str], ...]], ...]:
        return tuple(component for component in (
            dict(type=TemplateComponentType.BUTTONS.value, buttons=(self.button.to_dict())),
            dict(type=TemplateComponentType.BODY.value, add_security_recommendation=self.add_security_recommendation),
            dict(type=TemplateComponentType.FOOTER.value, code_expiration_minutes=self.code_expiration_minutes)
            if self.code_expiration_minutes else None,
        ) if component is not None)

