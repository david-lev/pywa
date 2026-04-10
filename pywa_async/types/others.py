from __future__ import annotations

import asyncio

from pywa.types.others import *  # noqa MUST BE IMPORTED FIRST
from pywa.types.others import (
    _T,
)
from pywa.types.others import (
    QRCode as _QRCode,
)
from pywa.types.others import (
    Result as _Result,
)

if TYPE_CHECKING:
    from ..client import WhatsApp as WhatsAppAsync


@dataclasses.dataclass(frozen=True, slots=True)
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

    _client: WhatsAppAsync = dataclasses.field(repr=False, hash=False, compare=False)

    async def fetch_image(self, image_type: QRCodeImageType) -> QRCode:
        """
        Returns the same QRCode object with the specified image type.

        - Useful for getting different image formats or if the original QR code was retrieved without an image.

        >>> from pywa_async import WhatsApp
        >>> wa = WhatsApp(...)
        >>> qr_codes = await wa.get_qr_codes() # image_type is None by default for faster retrieval
        >>> svg_qr = await qr_codes[0].fetch_image(QRCodeImageType.SVG) # Get the SVG version of the QR code

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
        ...
        >>> if res.has_next:
        ...     next_res = await res.next()
        ...
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

        prev = self
        while prev.has_previous:
            if sleep > 0:
                await asyncio.sleep(sleep)
            prev = await prev.previous()
            # noinspection PyProtectedMember
            before_data = prev._data + before_data

        next_page = self
        while next_page.has_next:
            if sleep > 0:
                await asyncio.sleep(sleep)
            next_page = await next_page.next()
            after_data += next_page._data

        return before_data + self._data + after_data
