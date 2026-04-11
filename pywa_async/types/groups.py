from __future__ import annotations

from typing import TYPE_CHECKING, AsyncIterator

from pywa.types.groups import *  # noqa MUST BE IMPORTED FIRST
from pywa.types.groups import (
    GroupDetails as _GroupDetails,
)
from pywa.types.groups import (
    GroupInviteLink as _GroupInviteLink,
)
from pywa.types.groups import (
    GroupJoinRequest as _GroupJoinRequest,
)
from pywa.types.groups import GroupMessageStatuses as _GroupMessageStatuses
from pywa.types.groups import (
    GroupParticipant as _GroupParticipant,
)

from .message_status import MessageStatus as MessageStatusAsync
from .others import Result
from .user import BaseUserAsync

if TYPE_CHECKING:
    from pywa_async import WhatsApp as WhatsAppAsync


class GroupDetails(_GroupDetails):
    """
    Represents the details of a WhatsApp group.

    Attributes:
        id: The unique identifier of the group.
        subject: The subject for the group.
        description: The description of the group.
        creation_timestamp: The timestamp when the group was created.
        suspended: Indicates if the group is suspended by WhatsApp.
        total_participant_count: The total number of participants in the group, excluding your business.
        participants: The list of participants in the group, excluding your business.
        join_approval_mode: Indicates if WhatsApp users who click the invitation link can join the group with or without being approved first.
    """

    _client: WhatsAppAsync = dataclasses.field(repr=False, hash=False, compare=False)

    async def get_invite_link(self) -> GroupInviteLink:
        """
        Get the invite link for the group.

        Returns:
            The invite link for the group.
        """
        return await self._client.get_group_invite_link(group_id=self.id)

    async def reset_invite_link(self) -> GroupInviteLink:
        """
        Reset the invite link for the group.

        Returns:
            A new invite link for the group.
        """
        return await self._client.reset_group_invite_link(group_id=self.id)

    async def get_join_requests(
        self, pagination: Pagination | None = None
    ) -> Result[GroupJoinRequest]:
        """
        You can create groups that require join request approval. Once enabled, WhatsApp users who click the group invitation link can submit a request to join the group, or cancel a prior request:

        Args:
            pagination: The pagination to use.

        Returns:
            A Result iterable containing the join requests for the group.
        """
        return await self._client.get_group_join_requests(
            group_id=self.id,
            pagination=pagination,
        )

    async def delete(self) -> GroupOperation:
        """
        Delete the group.

        Returns:
            An operation representing the delete group request. You can use the returned request ID to track the status of the delete operation.
        """
        return await self._client.delete_group(group_id=self.id)

    async def remove_participants(self, participants: Iterable[str]) -> GroupOperation:
        """
        Remove participants from the group.

        Args:
            participants: The participants to remove.

        Returns:
            An operation representing the remove participants request. You can use the returned request ID to track the
        """
        return await self._client.remove_group_participants(
            group_id=self.id,
            participants=participants,
        )

    async def remove_all_participants(self) -> GroupOperation:
        """
        Remove all participants from the group.

        Returns:
            An operation representing the remove all participants request. You can use the returned request ID to track
        """
        return await self._client.remove_group_participants(
            group_id=self.id,
            participants=(p.preferred_id for p in self.participants),
        )

    async def update(
        self,
        *,
        subject: str | None = None,
        description: str | None = None,
        profile_picture: bytes | str | pathlib.Path | BinaryIO | AsyncIterator[bytes],
    ) -> GroupOperation:
        """
        Update group settings.

        - Read more at `developers.facebook.com <https://developers.facebook.com/documentation/business-messaging/whatsapp/groups/reference#update-group-settings>`_.

        Args:
            subject: Group subject, Maximum 128 characters.
            description: Group description. Maximum 2048 characters.
            profile_picture: The new group profile picture. Can be a bytes object, a file path, a file-like object, or an iterator that yields bytes.

        Returns:
            An operation representing the update group settings request. You can use the returned request ID to track the status of the update operation.
        """
        return await self._client.update_group_settings(
            group_id=self.id,
            subject=subject,
            description=description,
            profile_picture=profile_picture,
        )


class GroupParticipant(BaseUserAsync, _GroupParticipant):
    """
    Represents an participant in a WhatsApp group.

    Attributes:
        bsuid: The WhatsApp user’s BSUID. See `developers.facebook.com <https://developers.facebook.com/documentation/business-messaging/whatsapp/business-scoped-user-ids>`_ for more information.
        wa_id: The user's phone number in international format (without the '+' sign). Will be unavailable if the user enables the username feature. See `developers.facebook.com <https://developers.facebook.com/documentation/business-messaging/whatsapp/business-scoped-user-ids#phone-numbers>`_ for more information.
        username: The username of the user.
        parent_bsuid: The Parent business-scoped user ID. See `developers.facebook.com <https://developers.facebook.com/documentation/business-messaging/whatsapp/business-scoped-user-ids#parent-business-scoped-user-ids>`_ for more information.
    """

    _client: WhatsAppAsync = dataclasses.field(repr=False, hash=False, compare=False)

    async def remove(self) -> GroupOperation:
        """
        Remove the participant from the group.
        """
        return await self._client.remove_group_participants(
            group_id=self._group_id,
            participants=(self.preferred_id,),
        )


class GroupInviteLink(_GroupInviteLink):
    """
    Represents an invite link for a WhatsApp group.
    """

    _client: WhatsAppAsync = dataclasses.field(repr=False, hash=False, compare=False)

    async def reset(self) -> GroupInviteLink:
        """
        Reset the invite link.

        Returns:
            A new invite link for the group.
        """
        return await self._client.reset_group_invite_link(group_id=self._group_id)


class GroupJoinRequest(_GroupJoinRequest):
    """
    Represents a join request for a WhatsApp group.

    Attributes:
        id: The unique identifier of the join request.
        user: The user who submitted the join request.
        creation_timestamp: The timestamp when the join request was created.
    """

    _client: WhatsAppAsync = dataclasses.field(repr=False, hash=False, compare=False)

    async def approve(self) -> GroupOperation:
        """Approve the join request."""
        return await self._client.approve_group_join_requests(
            group_id=self._group_id,
            request_ids=(self.id,),
        )

    async def reject(self) -> GroupOperation:
        """Reject the join request."""
        return await self._client.reject_group_join_requests(
            group_id=self._group_id,
            request_ids=(self.id,),
        )


class GroupJoinRequestsResult(Result[GroupJoinRequest]):
    """Represents a paginated result of group join requests for a WhatsApp group."""

    def __init__(
        self,
        wa: WhatsAppAsync,
        response: dict,
        group_id: str,
    ):
        super().__init__(
            wa=wa,
            response=response,
            item_factory=functools.partial(
                GroupJoinRequest.from_dict, client=wa, group_id=group_id
            ),
        )
        self._group_id = group_id

    async def approve_all(
        self, *, fetch_all: bool = False, sleep: float = 0.0
    ) -> GroupOperation:
        """
        Approve all join requests.

        Args:
            fetch_all: Whether to fetch all join requests before approving. If False, only the current page of join requests will be approved.
            sleep: The number of seconds to sleep between approving each join request when ``fetch_all`` is True. This can help avoid hitting rate limits.
        """
        requests = await self.all(sleep=sleep) if fetch_all else self
        return await self._wa.approve_group_join_requests(
            group_id=self._group_id,
            request_ids=[request.id for request in requests],
        )

    async def reject_all(
        self, *, fetch_all: bool = False, sleep: float = 0.0
    ) -> GroupOperation:
        """
        Reject all join requests.

        Args:
            fetch_all: Whether to fetch all join requests before rejecting. If False, only the current page of join requests will be rejected.
            sleep: The number of seconds to sleep between rejecting each join request when ``fetch_all`` is True. This can help avoid hitting rate limits.
        """
        requests = await self.all(sleep=sleep) if fetch_all else self
        return await self._wa.reject_group_join_requests(
            group_id=self._group_id,
            request_ids=[request.id for request in requests],
        )


class GroupMessageStatuses(_GroupMessageStatuses, Sequence[MessageStatusAsync]):
    """
    Represents an update for message statuses in a WhatsApp group.

    Attributes:
        group_id: The unique identifier of the group.
        statuses: A tuple of message statuses for messages sent to the group.
    """

    _msg_status_cls: ClassVar[type[MessageStatusAsync]] = MessageStatusAsync

    statuses: tuple[MessageStatusAsync, ...]
