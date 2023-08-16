"""
This module contains the errors that can be raised by the WhatsApp Cloud API or incoming error from the webhook.
"""

import functools
from typing import Type


class WhatsAppError(Exception):
    """
    Base exception for all WhatsApp errors.

    - `\`Cloud API Error Codes\` on developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/support/error-codes>`_.


    Attributes:
        error_code: The error code.
        message: The error message.
        details: The error details (optional).
        fbtrace_id: The Facebook trace ID (optional).
        href: The href to the documentation (optional).
        status_code: The status code (in case of response, else None).
    """
    __error_codes__ = ()

    def __init__(
            self,
            error_code: int,
            message: str,
            details: str | None,
            fbtrace_id: str | None,
            href: str | None,
            status_code: int | None,
    ) -> None:
        self.error_code = error_code
        self.message = message
        self.details = details
        self.fbtrace_id = fbtrace_id
        self.href = href
        self.status_code = status_code

    @classmethod
    def from_response(
            cls,
            status_code: int,
            error: dict
    ) -> "WhatsAppError":
        """Create an error from a response."""
        return cls._get_exception(error["code"])(
            status_code=status_code,
            error_code=error["code"],
            message=error["message"],
            details=error.get("error_data", {}).get("details", None),
            fbtrace_id=error.get("fbtrace_id"),
            href=error.get('href')
        )

    @classmethod
    def from_incoming_error(
            cls,
            error: dict
    ) -> "WhatsAppError":
        """Create an error from an incoming error."""
        return cls._get_exception(error["code"])(
            status_code=None,
            error_code=error["code"],
            message=error["message"],
            details=error.get("error_data", {}).get("details", None),
            fbtrace_id=error.get("fbtrace_id"),
            href=error.get('href')
        )

    @staticmethod
    @functools.cache
    def _all_exceptions() -> tuple[Type["WhatsAppError"], ...]:
        """Get all exceptions that can be raised from this error."""
        return tuple(ss for s in WhatsAppError.__subclasses__() for ss in s.__subclasses__())

    @staticmethod
    @functools.cache
    def _get_exception(code: int) -> Type["WhatsAppError"]:
        """Get the exception class from the error code."""
        return next((e for e in WhatsAppError._all_exceptions() if code in e.__error_codes__), WhatsAppError)

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


class ToManyMessages(ThrottlingError):
    """
    Too many messages sent from the sender phone number to the same recipient phone number in a short period of time.
    """
    __error_codes__ = (131056,)


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
