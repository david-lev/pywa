from __future__ import annotations

import dataclasses
import datetime

from pywa.types import User, Pagination, Result
from pywa import utils


class JoinApprovalMode(utils.StrEnum):
    AUTO_APPROVE = "auto_approve"
    APPROVAL_REQUIRED = "approval_required"

    UNKNOWN = "UNKNOWN"


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Group(utils.APIObject):
    id: str
    subject: str
    creation_timestamp: datetime.datetime
    suspended: bool
    description: str | None = None
    total_participant_count: int
    participants: list[User]
    join_approval_mode: JoinApprovalMode

    def get_invite_link(self) -> GroupInviteLink: ...
    def reset_invite_link(self) -> GroupInviteLink: ...
    def get_join_requests(
        self, pagination: Pagination | None = None
    ) -> Result[JoinRequest]: ...
    def delete(self): ...
    def remove_participants(self, users: list[str]): ...
    def update(
        self,
        *,
        profile_picture: str | None = None,
        subject: str | None = None,
        description: str | None = None,
    ) -> None: ...


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class GroupInviteLink:
    link: str


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class JoinRequest:
    id: str
    user: User
    creation_timestamp: datetime.datetime

    def approve(self): ...
    def reject(self): ...


class JoinApprovalsResult(Result[JoinRequest]):
    def approve_all(self): ...
    def reject_all(self): ...
