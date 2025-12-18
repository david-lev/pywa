from __future__ import annotations

import dataclasses
import datetime
import functools
from typing import TYPE_CHECKING

from pywa.types.others import User, Pagination, Result
from .. import utils

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


@dataclasses.dataclass(frozen=True, slots=True)
class Group:
    _client: WhatsApp = dataclasses.field(repr=False, hash=False, compare=False)
    id: str

    def get_details(self) -> GroupDetails:
        return self._client.get_group(group_id=self.id)


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class GroupDetails(utils.APIObject):
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
            creation_timestamp=datetime.datetime.strptime(
                data["creation_timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ"
            ),
            suspended=data["suspended"],
            description=data.get("description"),
            total_participant_count=data["total_participant_count"],
            participants=[
                GroupParticipant.from_dict(
                    participant_data | {"_group_id": data["id"]},
                    client,
                )
                for participant_data in data["participants"]
            ],
            join_approval_mode=GroupJoinApprovalMode(data["join_approval_mode"]),
        )

    def get_invite_link(self) -> GroupInviteLink: ...
    def reset_invite_link(self) -> GroupInviteLink: ...
    def get_join_requests(
        self, pagination: Pagination | None = None
    ) -> Result[GroupJoinRequest]: ...
    def delete(self): ...
    def remove_participants(self, participants: list[str]): ...
    def update(
        self,
        *,
        profile_picture: str | None = None,
        subject: str | None = None,
        description: str | None = None,
    ) -> None: ...


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class GroupParticipant(User):
    _group_id: str = dataclasses.field(repr=False)

    def remove(self): ...


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class GroupInviteLink:
    _client: WhatsApp = dataclasses.field(repr=False, hash=False, compare=False)
    _group_id: str = dataclasses.field(repr=False, hash=False, compare=False)
    link: str

    def reset(self) -> GroupInviteLink:
        return self._client.reset_group_invite_link(group_id=self._group_id)


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class GroupJoinRequest:
    _client: WhatsApp = dataclasses.field(repr=False, hash=False, compare=False)
    _group_id: str = dataclasses.field(repr=False, hash=False, compare=False)
    id: str
    user: User
    creation_timestamp: datetime.datetime

    def approve(self):
        self._client.approve_group_join_requests(
            group_id=self._group_id,
            request_ids=[self.id],
        )

    def reject(self):
        self._client.reject_group_join_requests(
            group_id=self._group_id,
            request_ids=[self.id],
        )


class GroupJoinApprovalsResult(Result[GroupJoinRequest]):
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
                GroupDetails.from_dict,
                client=wa,
            ),
        )
        self._group_id = group_id

    def approve_all(self, *, fetch_all: bool = False, sleep: float = 0.0):
        requests = self.all(sleep=sleep) if fetch_all else self
        self._wa.approve_group_join_requests(
            group_id=self._group_id,
            request_ids=[request.id for request in requests],
        )

    def reject_all(self, *, fetch_all: bool = False, sleep: float = 0.0):
        requests = self.all(sleep=sleep) if fetch_all else self
        self._wa.reject_group_join_requests(
            group_id=self._group_id,
            request_ids=[request.id for request in requests],
        )
