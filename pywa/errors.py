from __future__ import annotations

"""
This module contains the errors that can be raised by the WhatsApp Cloud API or incoming error from the webhook.
"""
import warnings
import dataclasses
import functools
from typing import Iterable, ClassVar

import httpx


@dataclasses.dataclass(slots=True, frozen=True)
class WhatsAppError(Exception):
    """
    Base dataclass for WhatsApp errors.

    - `'Cloud API Error Codes' on developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/support/error-codes>`_.
    - `'Flow Error Codes' on developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/error-codes>`_.
    - `'Calling Error Codes' on developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/troubleshooting>`_.
    - `'Block User Error Codes' on developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/block-users#error-codes>`_.

    Attributes:
        code: The error code.
        message: The error message.
        details: The error details (optional).
        fbtrace_id: The Facebook trace ID (optional).
        href: The href to the documentation (optional).
        raw_response: The :class:`httpx.Response` obj that returned the error (optional, only if the error was raised
            from an API call).
        subcode: The error subcode (optional).
        type: The error type (optional).
        is_transient: Whether the error is transient (optional).
        user_title: The user-facing title for the error (optional).
        user_msg: The user-facing message for the error (optional).
    """

    __error_codes__: ClassVar[Iterable[int] | None] = None

    code: int
    message: str
    details: str | None = None
    fbtrace_id: str | None = None
    href: str | None = None
    raw_response: httpx.Response | None = None
    subcode: int | None = None
    type: str | None = None
    is_transient: bool | None = None
    user_title: str | None = None
    user_msg: str | None = None

    @classmethod
    def from_dict(
        cls, error: dict, response: httpx.Response | None = None
    ) -> WhatsAppError:
        """Create an error from a response."""
        return cls._get_exception(code=(int_code := int(error["code"])))(
            code=int_code,
            message=error["message"],
            details=error.get("error_data", {}).get("details", None),
            fbtrace_id=error.get("fbtrace_id"),
            href=error.get("href"),
            raw_response=response,
            subcode=error.get("error_subcode"),
            type=error.get("type"),
            is_transient=error.get("is_transient"),
            user_title=error.get("error_user_title"),
            user_msg=error.get("error_user_msg"),
        )

    @property
    def status_code(self) -> int | None:
        """The status code (in case of ``raw_response``, else None)."""
        return self.raw_response.status_code if self.raw_response is not None else None

    @classmethod
    def _get_exception(cls, code: int) -> type[WhatsAppError]:
        """Get the exception class from the error code."""
        return _all_exceptions().get(code, WhatsAppError)

    @property
    def error_code(self) -> int:
        """Deprecated, use `code` instead."""
        warnings.warn(
            "WhatsAppError.error_code is deprecated, use WhatsAppError.code instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.code

    @property
    def error_subcode(self) -> int | None:
        """Deprecated, use `subcode` instead."""
        warnings.warn(
            "WhatsAppError.error_subcode is deprecated, use WhatsAppError.subcode instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.subcode

    def __str__(self) -> str:
        """Return a string representation of the error."""
        return self.__repr__()


@functools.cache
def _all_exceptions() -> dict[int, type[WhatsAppError]]:
    """Get all exceptions that can be raised from this error."""
    return {
        code: ssc
        for sc in WhatsAppError.__subclasses__()
        for ssc in sc.__subclasses__()
        for code in ssc.__error_codes__
    }


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


class AccountRestrictedFromCountry(IntegrityError):
    """
    The WhatsApp Business Account is restricted from messaging to users in certain countries.

    See WhatsApp Business Messaging Policy for details on allowed countries for messaging in your business category.
    """

    __error_codes__ = (130497,)


# ====================================================================================================


class SendMessageError(WhatsAppError):
    """Base exception for all message errors."""

    __error_codes__ = None


class UserIsInExperimentGroup(SendMessageError):
    """The user is part of an experiment group and the message was not sent as part of an experiment.

    See `Marketing Message Experiment <https://developers.facebook.com/docs/whatsapp/cloud-api/guides/experiments#marketing-message-experiment>`_.
    """

    __error_codes__ = (130472,)


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

    __error_codes__ = (131042, 131044)  # 131044 is for calling


class IncorrectCertificate(SendMessageError):
    """Message failed to send due to a phone number registration error."""

    __error_codes__ = (131045,)


class AccountInMaintenanceMode(SendMessageError):
    """Business Account is in maintenance mode"""

    __error_codes__ = (131057,)


class UserStoppedMarketingMessages(SendMessageError):
    """User has stopped marketing messages from the business account. you should listen to UserMarketingPreferences updates"""

    __error_codes__ = (131050,)


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


# ====================================================================================================


class BlockUserError(WhatsAppError):
    """
    Base exception for all block user errors.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/block-users#error-codes>`_.
    """

    __error_codes__ = None


class BulkBlockingFailed(BlockUserError):
    """
    Failed to block/unblock some users

    Bulk blocking failed to block some or all of the users.
    """

    __error_codes__ = (139100,)


class BlockListLimitReached(BlockUserError):
    """
    Blocklist limit reached

    The blocklist limit is reached when the 64k limit is met.
    """

    __error_codes__ = (139101,)


class BlockListConcurrentUpdate(BlockUserError):
    """
    Blocklist concurrent update

    Occurs when the block list is updated while performing a pagination request and version_id does not match.
    """

    __error_codes__ = (139102,)


class BlockUserInternalError(BlockUserError):
    """
    Internal error

    Internal error, please try again.
    """

    __error_codes__ = (139103,)


# ====================================================================================================


class CallingError(WhatsAppError):
    """
    Base exception for all calling errors.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/troubleshooting>`_.
    """

    __error_codes__ = None


class CallingNotEnabled(CallingError):
    """
    Calling is not enabled on the business phone number.

    `Configure call settings to enable Calling API features <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/call-settings>`_.
    """

    __error_codes__ = (138000,)


class CallingCannotBeEnabled(CallingError):
    """
    WhatsApp Business calling cannot be enabled because technical pre-requisites are not met.

    See `prerequisites <https://developers.facebook.com/docs/whatsapp/cloud-api/calling#step-1--prerequisites>`_ for more details

    `Configure SIP <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/sip>`_ or ensure there is at-least one app subscribed to the WhatsApp Business Account that also has subscription to the calls webhook field.
    """

    __error_codes__ = (138018,)


class ReceiverUncallable(CallingError):
    """
    Receiver is unable to receive calls

    Reasons can include:

    - The recipient phone number is not a WhatsApp phone number.
    - The recipient has not accepted our new Terms of Service and Privacy Policy.
    - Recipient using an unsupported client. The currently supported clients are Android, iOS, SMB Android and SMB iOS

    Confirm with the recipient that they agree to be contacted by you over WhatsApp and are using the latest version of WhatsApp.
    """

    __error_codes__ = (138001,)


class ConcurrentCallsLimit(CallingError):
    """
    Limit reached for maximum concurrent calls (1000) for the given number

    Try again later or reduce the frequency or amount of API calls the app is making.
    """

    __error_codes__ = (138002,)


class DuplicateCall(CallingError):
    """
    A call is already ongoing with the receiver

    Try again later when the current call ends.
    """

    __error_codes__ = (138003,)


class CallConnectionError(CallingError):
    """
    Error while connecting the call

    Try again later or investigate the connection params provided to the API.
    """

    __error_codes__ = (138004,)


class CallRateLimitExceeded(CallingError):
    """
    Limit reached for maximum calls that can be initiated by the business phone number

    Try again later or reduce the frequency or amount of API calls the app is making.
    """

    __error_codes__ = (138005,)


class CallPermissionNotFound(CallingError):
    """
    No approved `call permission <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/user-call-permissions>`_ from the recipient

    Ensure a call permission has been accepted by the consumer
    """

    __error_codes__ = (138006,)


class CallConnectionTimeout(CallingError):
    """
    Call was unable to connect due to a timeout

    Business did not apply the offer/answer SDP from Cloud API in time. Connect API was not invoked with the answer SDP in time
    """

    __error_codes__ = (138007,)


class CallPermissionRequestLimitHit(CallingError):
    """
    Limit reached for call permission request sends for the given business and consumer pair

    When a business sends more than the limit of call permission requests per time period, Call Permission Requests are rate limited. A connected call with a consumer will reset the limits.
    """

    __error_codes__ = (138009,)


class BusinessInitiatedCallsLimitHit(CallingError):
    """
    Limit reached for maximum business initiated calls allowed in 24 hours. Currently 5 connected business initiated calls are allowed within 24 hours.

    Exact error details will be listed in the error_data section of the response payload. Details will include a timestamp when the next call is allowed.
    """

    __error_codes__ = (138012,)


class FetchCallPermissionLimitHit(CallingError):
    """
    Limit reached for requests to the fetch call permission status API.

    Try again later or reduce the frequency or amount of requests to the API the app is making.
    """

    __error_codes__ = (
        138013,
        613,
    )  # WhatsApp changed the error code from 138013 to 613
