from __future__ import annotations

import dataclasses
import datetime
import functools
from typing import TYPE_CHECKING, Iterable

from .. import utils
from . import MessageStatus, RawUpdate
from .base_update import BaseUpdate
from .others import Pagination, Result
from .user import BaseUser

if TYPE_CHECKING:
    from pywa import WhatsApp


class GroupJoinApprovalMode(utils.StrEnum):
    """
    Indicates if WhatsApp users who click the invitation link can join the group with or without being approved first.

    Attributes:
        AUTO_APPROVE: Indicates WhatsApp users can join the group without approval.
        APPROVAL_REQUIRED: Indicates WhatsApp users must be approved via `join request <https://developers.facebook.com/documentation/business-messaging/whatsapp/groups/reference#groups-with-join-requests>`_ before they can access the group.
    """

    AUTO_APPROVE = "auto_approve"
    APPROVAL_REQUIRED = "approval_required"

    UNKNOWN = "UNKNOWN"

    _check_value = str.islower
    _modify_value = str.lower


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class GroupDetails(utils.APIObject):
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

    _client: WhatsApp = dataclasses.field(repr=False, hash=False, compare=False)
    id: str
    subject: str
    creation_timestamp: datetime.datetime
    suspended: bool
    description: str | None
    total_participant_count: int
    participants: list[GroupParticipant]
    join_approval_mode: GroupJoinApprovalMode

    @classmethod
    def from_dict(cls, data: dict, client: WhatsApp) -> GroupDetails:
        return cls(
            _client=client,
            id=data["id"],
            subject=data["subject"],
            creation_timestamp=datetime.datetime.fromtimestamp(
                data["creation_timestamp"],
                datetime.timezone.utc,
            ),
            suspended=data["suspended"],
            description=data.get("description"),
            total_participant_count=data["total_participant_count"],
            participants=[
                client._group_participant_cls.from_dict(
                    group_id=data["id"], client=client, data=participant
                )
                for participant in data["participants"]
            ],
            join_approval_mode=GroupJoinApprovalMode(data["join_approval_mode"]),
        )

    def get_invite_link(self) -> GroupInviteLink:
        """
        Get the invite link for the group.

        Returns:
            The invite link for the group.
        """
        return self._client.get_group_invite_link(group_id=self.id)

    def reset_invite_link(self) -> GroupInviteLink:
        """
        Reset the invite link for the group.

        Returns:
            A new invite link for the group.
        """
        return self._client.reset_group_invite_link(group_id=self.id)

    def get_join_requests(
        self, pagination: Pagination | None = None
    ) -> Result[GroupJoinRequest]:
        """
        You can create groups that require join request approval. Once enabled, WhatsApp users who click the group invitation link can submit a request to join the group, or cancel a prior request:

        Args:
            pagination: The pagination to use.

        Returns:
            A Result iterable containing the join requests for the group.
        """
        return self._client.get_group_join_requests(
            group_id=self.id,
            pagination=pagination,
        )

    def delete(self) -> None:
        """
        Delete the group.
        """
        return self._client.delete_group(group_id=self.id)

    def remove_participants(self, participants: Iterable[str]) -> None:
        """
        Remove participants from the group.

        Args:
            participants: The participants to remove.
        """
        return self._client.remove_group_participants(
            group_id=self.id,
            participants=participants,
        )

    def remove_all_participants(self) -> None:
        """Remove all participants from the group."""
        return self._client.remove_group_participants(
            group_id=self.id,
            participants=(p.preferred_id for p in self.participants),
        )

    def update(
        self,
        *,
        profile_picture: str | None = None,
        subject: str | None = None,
        description: str | None = None,
    ) -> None: ...


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class GroupParticipant(BaseUser):
    """
    Represents an participant in a WhatsApp group.

    Attributes:
        bsuid: The WhatsApp user’s BSUID. See `developers.facebook.com <https://developers.facebook.com/documentation/business-messaging/whatsapp/business-scoped-user-ids>`_ for more information.
        wa_id: The user's phone number in international format (without the '+' sign). Will be unavailable if the user enables the username feature. See `developers.facebook.com <https://developers.facebook.com/documentation/business-messaging/whatsapp/business-scoped-user-ids#phone-numbers>`_ for more information.
        username: The username of the user.
        parent_bsuid: The Parent business-scoped user ID. See `developers.facebook.com <https://developers.facebook.com/documentation/business-messaging/whatsapp/business-scoped-user-ids#parent-business-scoped-user-ids>`_ for more information.
    """

    _group_id: str = dataclasses.field(repr=False)

    @classmethod
    def from_dict(cls, group_id: str, data: dict, client: WhatsApp) -> GroupParticipant:
        return cls(
            _client=client,
            _group_id=group_id,
            bsuid=data["user_id"],
            wa_id=data.get("wa_id"),
            parent_bsuid=data.get("parent_user_id"),
            username=data.get("username"),
        )

    def remove(self) -> None:
        """
        Remove the participant from the group.
        """
        return self._client.remove_group_participants(
            group_id=self._group_id,
            participants=(self.preferred_id,),
        )


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class GroupInviteLink:
    """
    Represents an invite link for a WhatsApp group.
    """

    _client: WhatsApp = dataclasses.field(repr=False, hash=False, compare=False)
    _group_id: str = dataclasses.field(repr=False, hash=False, compare=False)
    link: str

    def reset(self) -> GroupInviteLink:
        """
        Reset the invite link.

        Returns:
            A new invite link for the group.
        """
        return self._client.reset_group_invite_link(group_id=self._group_id)


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class GroupJoinRequest:
    """
    Represents a join request for a WhatsApp group.

    Attributes:
        id: The unique identifier of the join request.
        user: The user who submitted the join request.
        creation_timestamp: The timestamp when the join request was created.
    """

    _client: WhatsApp = dataclasses.field(repr=False, hash=False, compare=False)
    _group_id: str = dataclasses.field(repr=False, hash=False, compare=False)
    id: str
    user: GroupParticipant
    creation_timestamp: datetime.datetime

    @classmethod
    def from_dict(cls, group_id: str, data: dict, client: WhatsApp) -> GroupJoinRequest:
        return cls(
            _client=client,
            _group_id=group_id,
            id=data["join_request_id"],
            user=client._group_participant_cls.from_dict(
                group_id=group_id, client=client, data=data
            ),
            creation_timestamp=datetime.datetime.fromtimestamp(
                data["creation_timestamp"]
            ),
        )

    def approve(self) -> None:
        """Approve the join request."""
        return self._client.approve_group_join_requests(
            group_id=self._group_id,
            request_ids=(self.id,),
        )

    def reject(self) -> None:
        """Reject the join request."""
        return self._client.reject_group_join_requests(
            group_id=self._group_id,
            request_ids=(self.id,),
        )


class GroupJoinRequestsResult(Result[GroupJoinRequest]):
    """Represents a paginated result of group join requests for a WhatsApp group."""

    def __init__(
        self,
        wa: WhatsApp,
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

    def approve_all(self, *, fetch_all: bool = False, sleep: float = 0.0) -> None:
        """
        Approve all join requests.

        Args:
            fetch_all: Whether to fetch all join requests before approving. If False, only the current page of join requests will be approved.
            sleep: The number of seconds to sleep between approving each join request when ``fetch_all`` is True. This can help avoid hitting rate limits.
        """
        requests = self.all(sleep=sleep) if fetch_all else self
        return self._wa.approve_group_join_requests(
            group_id=self._group_id,
            request_ids=[request.id for request in requests],
        )

    def reject_all(self, *, fetch_all: bool = False, sleep: float = 0.0) -> None:
        """
        Reject all join requests.

        Args:
            fetch_all: Whether to fetch all join requests before rejecting. If False, only the current page of join requests will be rejected.
            sleep: The number of seconds to sleep between rejecting each join request when ``fetch_all`` is True. This can help avoid hitting rate limits.
        """
        requests = self.all(sleep=sleep) if fetch_all else self
        return self._wa.reject_group_join_requests(
            group_id=self._group_id,
            request_ids=[request.id for request in requests],
        )


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class GroupMessageStatus(BaseUpdate):
    group_id: str
    statuses: tuple[MessageStatus, ...]

    _webhook_field = "messages"

    @classmethod
    def from_update(cls, client: WhatsApp, update: RawUpdate) -> BaseUpdate:
        status = (value := (entry := update["entry"][0])["changes"][0]["value"])[
            "statuses"
        ][0]
        contact_map = {
            contact["user_id"]: idx for idx, contact in enumerate(value["contacts"])
        }
        return cls(
            _client=client,
            raw=update,
            id=entry["id"],
            timestamp=datetime.datetime.fromtimestamp(
                int(status["timestamp"]),
                datetime.timezone.utc,
            ),
            group_id=status["recipient_id"],
            statuses=tuple(
                MessageStatus.from_update(
                    client=client,
                    update=update,
                    contact_idx=contact_map[
                        status.get["recipient_participant_user_id"]
                    ],
                    status_idx=s_idx,
                )
                for s_idx, status in enumerate(value["statuses"])
            ),
        )
