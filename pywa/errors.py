"""
This module contains the errors that can be raised by the WhatsApp Cloud API or incoming error from the webhook.
"""

import functools
from typing import Iterable, Type

import httpx


class WhatsAppError(Exception):
    """
    Base exception for all WhatsApp errors.

    - `'Cloud API Error Codes' on developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/support/error-codes>`_.
    - `'Flow Error Codes' on developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/error-codes>`_.

    Attributes:
        error_code: The error code.
        error_subcode: The error subcode (optional).
        type: The error type (optional).
        message: The error message.
        details: The error details (optional).
        fbtrace_id: The Facebook trace ID (optional).
        href: The href to the documentation (optional).
        raw_response: The :class:`httpx.Response` obj that returned the error (optional, only if the error was raised
         from an API call).
    """

    __error_codes__: Iterable[int] | None

    def __init__(
        self,
        error_code: int,
        message: str,
        details: str | None,
        fbtrace_id: str | None,
        href: str | None,
        raw_response: httpx.Response | None,
        error_subcode: int | None = None,
        err_type: str | None = None,
    ) -> None:
        self.error_code = error_code
        self.error_subcode = error_subcode
        self.type = err_type
        self.message = message
        self.details = details
        self.fbtrace_id = fbtrace_id
        self.href = href
        self.raw_response = raw_response

    @property
    def status_code(self) -> int | None:
        """The status code (in case of raw_response, else None)."""
        return self.raw_response.status_code if self.raw_response is not None else None

    @classmethod
    def from_dict(
        cls, error: dict, response: httpx.Response | None = None
    ) -> "WhatsAppError":
        """Create an error from a response."""
        return cls._get_exception(error["code"])(
            raw_response=response,
            error_code=error["code"],
            message=error["message"],
            details=error.get("error_data", {}).get("details", None),
            fbtrace_id=error.get("fbtrace_id"),
            href=error.get("href"),
            error_subcode=error.get("error_subcode"),
            err_type=error.get("type"),
        )

    @staticmethod
    @functools.cache
    def _all_exceptions() -> tuple[Type["WhatsAppError"], ...]:
        """Get all exceptions that can be raised from this error."""
        return tuple(
            ss for s in WhatsAppError.__subclasses__() for ss in s.__subclasses__()
        )

    @staticmethod
    @functools.cache
    def _get_exception(code: int) -> Type["WhatsAppError"]:
        """Get the exception class from the error code."""
        return next(
            (e for e in WhatsAppError._all_exceptions() if code in e.__error_codes__),
            WhatsAppError,
        )

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, details={self.details!r}, code={self.error_code!r})"

    def __repr__(self) -> str:
        return self.__str__()


class AuthorizationError(WhatsAppError):
    """Base exception for all authorization errors."""

    __error_codes__ = None


class AuthException(AuthorizationError):
    """We were unable to authenticate the app user"""

    __error_codes__ = (0,)


class APIMethod(AuthorizationError):
    """Capability or permissions issue."""

    __error_codes__ = (3,)


class PermissionDenied(AuthorizationError):
    """Permission is either not granted or has been removed."""

    __error_codes__ = (10,)


class ExpiredAccessToken(AuthorizationError):
    """Your access token has expired."""

    __error_codes__ = (190,)


class APIPermission(AuthorizationError):
    """Permission is either not granted or has been removed."""

    __error_codes__ = range(200, 300)


# ====================================================================================================


class ThrottlingError(WhatsAppError):
    """Base exception for all rate limit errors."""

    __error_codes__ = None


class ToManyAPICalls(ThrottlingError):
    """The app has reached its API call rate limit."""

    __error_codes__ = (4,)


class RateLimitIssues(ThrottlingError):
    """The WhatsApp Business Account has reached its rate limit."""

    __error_codes__ = (80007,)


class RateLimitHit(ThrottlingError):
    """Cloud API message throughput has been reached."""

    __error_codes__ = (130429,)


class SpamRateLimitHit(ThrottlingError):
    """
    Message failed to send because there are restrictions on how many messages can be sent from this phone number.
    This may be because too many previous messages were blocked or flagged as spam.
    """

    __error_codes__ = (131048,)


class TooManyMessages(ThrottlingError):
    """
    Too many messages sent from the sender phone number to the same recipient phone number in a short period of time.
    """

    __error_codes__ = (131056,)


class ToManyMessages(TooManyMessages):
    """Deprecated, use :class:`TooManyMessages` instead."""

    pass


# ====================================================================================================


class IntegrityError(WhatsAppError):
    """Base exception for all integrity errors."""

    __error_codes__ = None


class TemporarilyBlocked(IntegrityError):
    """
    The WhatsApp Business Account associated with the app has been restricted or disabled for violating a platform policy.
    """

    __error_codes__ = (368,)


class AccountLocked(IntegrityError):
    """
    The WhatsApp Business Account associated with the app has been restricted or disabled for violating a platform
    policy, or we were unable to verify data included in the request against data set on the WhatsApp Business
    Account (e.g, the two-step pin included in the request is incorrect).
    """

    __error_codes__ = (131031,)


# ====================================================================================================


class SendMessageError(WhatsAppError):
    """Base exception for all message errors."""

    __error_codes__ = None


class MessageUndeliverable(SendMessageError):
    """Unable to deliver message. Reasons can include:

    - The recipient phone number is not a WhatsApp phone number.
    - Recipient has not accepted our new Terms of Service and Privacy Policy.
    - Recipient using an old WhatsApp version; must use the following WhatsApp version or greater:
        Android: 2.21.15.15
        SMBA: 2.21.15.15
        iOS: 2.21.170.4
        SMBI: 2.21.170.4
        KaiOS: 2.2130.10
        Web: 2.2132.6
    """

    __error_codes__ = (131026,)


class ReEngagementMessage(SendMessageError):
    """More than 24 hours have passed since the recipient last replied to the sender number."""

    __error_codes__ = (131047,)


class UnsupportedMessageType(SendMessageError):
    """The message type is not supported."""

    __error_codes__ = (131051,)


class MediaDownloadError(SendMessageError):
    """Unable to download the media sent by the user."""

    __error_codes__ = (131052,)


class MediaUploadError(SendMessageError):
    """Unable to upload the media used in the message."""

    __error_codes__ = (131053,)


class RecipientNotInAllowedList(SendMessageError):
    """
    When using test numbers, you can add up to 5 numbers that can receive messages. This error is raised when the
    recipient is not in the list.
    """

    __error_codes__ = (131030,)


class InvalidParameter(SendMessageError):
    """The parameter you passed is invalid."""

    __error_codes__ = (131009,)


class MissingRequiredParameter(SendMessageError):
    """You must provide a value for the required parameter."""

    __error_codes__ = (131008,)


class TemplateParamCountMismatch(SendMessageError):
    """The number of variable parameter values included in the request did not match the number of variable parameters
    defined in the template.."""

    __error_codes__ = (132000,)


class TemplateNotExists(SendMessageError):
    """The template does not exist in the specified language or the template has not been approved."""

    __error_codes__ = (132001,)


class TemplateTextTooLong(SendMessageError):
    """The template text is too long."""

    __error_codes__ = (132005,)


class TemplateContentPolicyViolation(SendMessageError):
    """The template content violates a WhatsApp policy."""

    __error_codes__ = (132007,)


class TemplateParamValueInvalid(SendMessageError):
    """Variable parameter values formatted incorrectly."""

    __error_codes__ = (132008,)


class TemplateParamFormatMismatch(SendMessageError):
    """Variable parameter values formatted incorrectly."""

    __error_codes__ = (132012,)


class TemplatePaused(SendMessageError):
    """Template is paused due to low quality so it cannot be sent in a template message."""

    __error_codes__ = (132015,)


class TemplateDisabled(SendMessageError):
    """Template has been paused too many times due to low quality and is now permanently disabled."""

    __error_codes__ = (132016,)


class FlowBlocked(SendMessageError):
    """Flow is in blocked state."""

    __error_codes__ = (132068,)


class FlowThrottled(SendMessageError):
    """Flow is in throttled state and 10 messages using this flow were already sent in the last hour."""

    __error_codes__ = (132069,)


class GenericError(SendMessageError):
    """Generic error."""

    __error_codes__ = (135000,)


class UnknownError(SendMessageError):
    """Message failed to send due to an unknown error."""

    __error_codes__ = (131000,)


class AccessDenied(SendMessageError):
    """Permission is either not granted or has been removed."""

    __error_codes__ = (131005,)


class ServiceUnavailable(SendMessageError):
    """A service is temporarily unavailable."""

    __error_codes__ = (131016,)


class RecipientCannotBeSender(SendMessageError):
    """Sender and recipient phone number is the same."""

    __error_codes__ = (131021,)


class BusinessPaymentIssue(SendMessageError):
    """Message failed to send because there were one or more errors related to your payment method."""

    __error_codes__ = (131042,)


class IncorrectCertificate(SendMessageError):
    """Message failed to send due to a phone number registration error."""

    __error_codes__ = (131045,)


class AccountInMaintenanceMode(SendMessageError):
    """Business Account is in maintenance mode"""

    __error_codes__ = (131057,)


# ====================================================================================================


class FlowError(WhatsAppError):
    """
    Base exception for all flow errors.

     Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/error-codes>`_.
    """

    __error_codes__ = None


class FlowBlockedByIntegrity(FlowError):
    """Unfortunately, we've identified an issue with integrity in your account and have prevented you from creating
    or publishing your Flow."""

    __error_codes__ = (139000,)


class FlowUpdatingError(FlowError):
    """
    Flow failed to update

    - Flow can't be updated (You attempted to update a Flow that has already been published.)
    - Error while processing Flow JSON.
    - Specify Endpoint Uri in Flow JSON (You provided endpoint_uri param for a Flow with Flow JSON version below 3.0.)
    """

    __error_codes__ = (139001,)


class FlowPublishingError(FlowError):
    """
    Flow failed to publish.

    - Publishing Flow in invalid state
    - Publishing Flow with validation errors
    - Publishing Flow without data_channel_uri
    - Publishing without specifying endpoint_uri is forbidden
      (Starting from Flow JSON version 3.0 endpoint_uri should be specified via API.)
    - Versions in Flow JSON file are not available for publishing
    - No Phone Number connected to WhatsApp Business Account
    - Missing Flows Signed Public Key
    - No Application Connected to the Flow
    - Endpoint Not Available
    - WhatsApp Business Account is not subscribed to Flows Webhooks
    """

    __error_codes__ = (139002,)


class FlowDeprecatingError(FlowError):
    """
    Flow failed to deprecate.

    - Can't deprecate unpublished flow
    - Flow is already deprecated
    """

    __error_codes__ = (139003,)


class FlowDeletingError(FlowError):
    """
    Flow failed to delete.

    - Can't delete published Flow
    """

    __error_codes__ = (139004,)
