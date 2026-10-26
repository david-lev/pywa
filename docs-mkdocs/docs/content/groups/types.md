# Groups Types

::: pywa.types.groups.GroupDetails
    options:
      members: ["get_invite_link", "reset_invite_link", "get_join_requests", "remove_participants", "remove_all_participants", "update", "delete"]
      inherited_members: ["get_invite_link", "reset_invite_link", "get_join_requests", "remove_participants", "remove_all_participants", "update", "delete"]

::: pywa.types.groups.GroupParticipant
    options:
      members: ["remove"]
      inherited_members: ["remove"]

::: pywa.types.groups.GroupInviteLink
    options:
      members: ["reset"]
      inherited_members: ["reset"]

::: pywa.types.groups.GroupJoinRequest
    options:
      members: ["approve", "reject"]
      inherited_members: ["approve", "reject"]

::: pywa.types.groups.GroupJoinRequestsResult
    options:
      members: ["approve_all", "reject_all"]
      inherited_members: ["approve_all", "reject_all"]
      show_bases: true

::: pywa.types.groups.GroupJoinApprovalMode
    options:
      members: false

::: pywa.types.groups.GroupOperation
    options:
      members: false
