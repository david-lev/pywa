from __future__ import annotations

import asyncio
from collections.abc import Sequence
from typing import TYPE_CHECKING

from pywa.types.others import (
    _T,
)
from pywa.types.others import BlockedUser as BlockedUser
from pywa.types.others import BlockUserFailure as BlockUserFailure
from pywa.types.others import BusinessInfo as BusinessInfo
from pywa.types.others import BusinessPhoneNumber as BusinessPhoneNumber
from pywa.types.others import BusinessProfile as BusinessProfile
from pywa.types.others import BusinessVerificationStatus as BusinessVerificationStatus
from pywa.types.others import Command as Command
from pywa.types.others import CommerceSettings as CommerceSettings
from pywa.types.others import Contact as Contact
from pywa.types.others import ContactList as ContactList
from pywa.types.others import ContactsOrigin as ContactsOrigin
from pywa.types.others import ConversationalAutomation as ConversationalAutomation
from pywa.types.others import (
    CreatedBusinessPhoneNumber as CreatedBusinessPhoneNumber,
)
from pywa.types.others import CreatedSignup as CreatedSignup
from pywa.types.others import FacebookApplication as FacebookApplication
from pywa.types.others import Industry as Industry
from pywa.types.others import InteractiveType as InteractiveType
from pywa.types.others import Location as Location
from pywa.types.others import (
    MarketingMessagesLiteAPIStatus as MarketingMessagesLiteAPIStatus,
)
from pywa.types.others import (
    MarketingMessagesOnboardingStatus as MarketingMessagesOnboardingStatus,
)
from pywa.types.others import MessageType as MessageType
from pywa.types.others import Metadata as Metadata
from pywa.types.others import Order as Order
from pywa.types.others import Pagination as Pagination
from pywa.types.others import Product as Product
from pywa.types.others import ProductsSection as ProductsSection
from pywa.types.others import (
    QRCode as _QRCode,
)
from pywa.types.others import QRCodeImageType as QRCodeImageType
from pywa.types.others import Reaction as Reaction
from pywa.types.others import Referral as Referral
from pywa.types.others import ReferredProduct as ReferredProduct
from pywa.types.others import ReplyToMessage as ReplyToMessage
from pywa.types.others import (
    Result as _Result,
)
from pywa.types.others import SignupDetails as _SignupDetails
from pywa.types.others import SignupStatus as SignupStatus
from pywa.types.others import StorageConfiguration as StorageConfiguration
from pywa.types.others import StorageStatus as StorageStatus
from pywa.types.others import SuccessResult as SuccessResult
from pywa.types.others import UnblockedUser as UnblockedUser
from pywa.types.others import Unsupported as Unsupported
from pywa.types.others import (
    UserIdentityChangeSettings as UserIdentityChangeSettings,
)
from pywa.types.others import UsernameStatus as UsernameStatus
from pywa.types.others import UsernameStatusType as UsernameStatusType
from pywa.types.others import UsersBlockedResult as UsersBlockedResult
from pywa.types.others import UsersUnblockedResult as UsersUnblockedResult
from pywa.types.others import WhatsAppBusinessAccount as WhatsAppBusinessAccount

if TYPE_CHECKING:
    from ..client import WhatsApp as WhatsAppAsync


class QRCode(_QRCode):
    """
    Customers can scan a QR code from their phone to quickly begin a conversation with your business.
    The WhatsApp Business Management API allows you to create and access these QR codes and associated short links.

    Attributes:
        code: The code of the QR code.
        prefilled_message: The message that will be prefilled when the user starts a conversation with the business using the QR code.
        deep_link_url: The deep link URL of the QR code.
        qr_image_url: The URL of the QR code image (return only when creating a QR code).
    """

    _client: WhatsAppAsync

    async def fetch_image(self, image_type: QRCodeImageType) -> QRCode | None:
        """
        Returns the same QRCode object with the specified image type.

        - Useful for getting different image formats or if the original QR code was retrieved without an image.

        >>> from pywa_async import WhatsApp
        >>> wa = WhatsApp(...)
        >>> qr_codes = (
        ...     await wa.get_qr_codes()
        ... )  # image_type is None by default for faster retrieval
        >>> svg_qr = await qr_codes[0].fetch_image(
        ...     QRCodeImageType.SVG
        ... )  # Get the SVG version of the QR code

        Args:
            image_type: The type of the image (e.g., PNG, SVG).

        Returns:
            A new QRCode object with the specified image type.
        """
        return await self._client.get_qr_code(
            code=self.code, image_type=image_type, phone_id=self._phone_id
        )

    async def update(self, *, prefilled_message: str) -> QRCode:
        """
        Updates the QR code with a new prefilled message.

        Args:
            prefilled_message: The new prefilled message for the QR code.

        Returns:
            The updated QRCode object.
        """
        return await self._client.update_qr_code(
            code=self.code, prefilled_message=prefilled_message, phone_id=self._phone_id
        )

    async def delete(self) -> SuccessResult:
        """
        Deletes the QR code.

        Returns:
            A SuccessResult indicating whether the deletion was successful.
        """
        return await self._client.delete_qr_code(
            code=self.code, phone_id=self._phone_id
        )


class SignupDetails(_SignupDetails):
    """
    Represents a signup for a WhatsApp Business Account.

    Attributes:
        id: The ID of the signup.
        waba_id: The ID of the business account.
        message: The message shown on the pre-consent screen.
        confirmation_message: The message sent to the WhatsApp user after opt-in.
        privacy_policy_url: The privacy policy URL.
        promo_code: The promotional code value, if set.
        status: The current status.
        display_name: The business-facing nickname for the signup link, if set. Not shown to WhatsApp users.
        website_url: The business website URL, if set.
    """

    _client: WhatsAppAsync

    async def disable(self) -> SuccessResult:
        """
        Disable the signup.

        Returns:
            A SuccessResult indicating whether the operation was successful.

        Example:

            >>> signup = await wa.get_signup(...)
            >>> if await signup.disable():
            ...     print("Signup disabled successfully")
        """
        return await self._client.update_signup(
            signup_id=self.id,
            status=SignupStatus.DISABLED,
        )

    async def enable(self) -> SuccessResult:
        """
        Enable the signup.

        Returns:
            A SuccessResult indicating whether the operation was successful.

        Example:
            >>> signup = await wa.get_signup(...)
            >>> await signup.enable()
            SuccessResult(success=True)
        """
        return await self._client.update_signup(
            signup_id=self.id,
            status=SignupStatus.ACTIVE,
        )

    async def update(
        self,
        *,
        status: SignupStatus | None = None,
        message: str | None = None,
        confirmation_message: str | None = None,
        website_url: str | None = None,
        promo_code: str | None = None,
        display_name: str | None = None,
    ) -> SuccessResult:
        """
        Update the signup.

        Args:
            status: Updated status: ``ACTIVE`` or ``DISABLED``.
            message: The description shown on the pre-consent screen when a WhatsApp user opens the deep link. Supports WhatsApp formatting. Must be 1-300 characters.
            confirmation_message: The description shown on the post-consent screen when a WhatsApp user successfully completes the flow. Supports WhatsApp formatting. Must be 1-300 characters.
            website_url: The URL of the website.
            promo_code: The promo code.
            display_name: The display name.

        Returns:
            A SuccessResult indicating whether the operation was successful.

        Example:

            >>> signup = await wa.get_signup(...)
            >>> if await signup.update(...):
            ...     print("Signup updated successfully")
        """
        return await self._client.update_signup(
            signup_id=self.id,
            status=status,
            message=message,
            confirmation_message=confirmation_message,
            website_url=website_url,
            promo_code=promo_code,
            display_name=display_name,
        )


class Result(_Result[_T], Sequence[_T]):
    """
    This class is used to handle paginated results from the WhatsApp API. You can iterate over the results, and also access the next and previous pages of results.

    - When using the :meth:`next` or :meth:`previous` methods, the results are returned as a new instance of the :class:`Result` class.
    - You can access the cursors using the :attr:`before` and :attr:`after` properties and use them later in the :class:`Pagination` object.

    Example:

        >>> from pywa_async import WhatsApp, types
        >>> wa = WhatsApp(...)
        >>> res = await wa.get_blocked_users(pagination=types.Pagination(limit=100))
        >>> for user in res:
        ...     print(user.name, user.wa_id)
        >>> if res.has_next:
        ...     next_res = await res.next()
        >>> print(await res.all())
    """

    _wa: WhatsAppAsync

    @property
    def empty(self) -> Result[_T]:
        """Returns an empty Result instance."""
        return Result(
            wa=self._wa,
            response={
                "data": [],
                "paging": {"next": self._next_url, "cursors": self._cursors},
            },
            item_factory=self._item_factory,
        )

    async def next(self) -> Result[_T]:
        """
        Get the next page of results. if there is no next page, it returns empty Result.

        - Check if there is a next page using the :attr:`~pywa.types.others.Result.has_next` property before calling this method.
        """
        if self.has_next:
            # noinspection PyProtectedMember
            response = await self._wa.api._request(
                method="GET", endpoint=self._next_url
            )
            return Result(
                wa=self._wa, response=response, item_factory=self._item_factory
            )
        return self.empty

    async def previous(self) -> Result[_T]:
        """
        Get the previous page of results. if there is no previous page, it returns empty Result.

        - Check if there is a previous page using the :attr:`~pywa.types.others.Result.has_previous` property before calling this method.
        """
        if self.has_previous:
            # noinspection PyProtectedMember
            response = await self._wa.api._request(
                method="GET", endpoint=self._previous_url
            )
            return Result(
                wa=self._wa, response=response, item_factory=self._item_factory
            )
        return self.empty

    async def all(
        self,
        *,
        sleep: float = 0.0,
    ) -> list[_T]:
        """
        Get all results from the current page, previous pages, and next pages.

        - Make sure to provide higher limit in the :class:`Pagination` parameter to avoid hitting rate limits.
        - Also consider using the ``sleep`` parameter to avoid hitting rate limits.

        Args:
            sleep: The number of seconds to sleep between requests to avoid hitting rate limits. Default is 0.0 (no sleep).

        Returns:
            A list of all results from the current page, previous pages, and next pages.
        """
        before_data = []
        after_data = []

        prev: Result[_T] = self
        while prev.has_previous:
            if sleep > 0:
                await asyncio.sleep(sleep)
            prev = await prev.previous()
            # noinspection PyProtectedMember
            before_data = prev._data + before_data

        next_page: Result[_T] = self
        while next_page.has_next:
            if sleep > 0:
                await asyncio.sleep(sleep)
            next_page = await next_page.next()
            after_data += next_page._data

        return before_data + self._data + after_data
