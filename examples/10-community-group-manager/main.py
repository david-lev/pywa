"""
Community Group Concierge Bot
===============================
Feature focus: the WhatsApp Groups API (`pywa.types.groups`) — creating and managing WhatsApp
groups, generating invite links, and approving/rejecting join requests, all via chat commands.
"""

import os

import dotenv

from pywa_async import WhatsApp, filters, types
from pywa_async.types.groups import GroupJoinApprovalMode, GroupJoinRequest
from pywa_async.utils import start_ngrok_tunnel

dotenv.load_dotenv()

callback_url = os.getenv("CALLBACK_URL")
if not callback_url:
    callback_url = start_ngrok_tunnel(auth_token=os.environ["NGROK_AUTH_TOKEN"])

wa = WhatsApp(
    phone_id=os.environ["WHATSAPP_PHONE_ID"],
    token=os.environ["WHATSAPP_TOKEN"],
    app_id=os.environ["WHATSAPP_APP_ID"],
    app_secret=os.environ["WHATSAPP_APP_SECRET"],
    callback_url=callback_url,
    verify_token=os.environ.get("WHATSAPP_VERIFY_TOKEN", "xyzxyz"),
)

ADMIN_NUMBERS = {
    n.strip() for n in os.getenv("ADMIN_NUMBERS", "").split(",") if n.strip()
}
is_admin = filters.from_users(*ADMIN_NUMBERS)

# request_id -> GroupJoinRequest, so callback buttons can act on it without re-fetching.
PENDING_REQUESTS: dict[str, GroupJoinRequest] = {}


@wa.on_message(~is_admin)
async def deny_non_admins(_: WhatsApp, msg: types.Message):
    await msg.reply("This number is not authorized to manage community groups.")


@wa.on_message(filters.command("create_group", ignore_case=True) & is_admin)
async def create_group(_: WhatsApp, msg: types.Message):
    name = msg.text.partition(" ")[2]
    if not name:
        await msg.reply("Usage: /create_group <group name>")
        return
    op = await wa.create_group(
        subject=name,
        join_approval_mode=GroupJoinApprovalMode.ADMIN_APPROVAL,
    )
    await msg.reply(
        f"⏳ Creating group '{name}' (request: {op.request_id}). "
        "Send /groups in a few seconds to see it and grab its invite link."
    )


@wa.on_message(filters.command("groups", ignore_case=True) & is_admin)
async def list_groups(_: WhatsApp, msg: types.Message):
    groups = list(await wa.get_groups())
    if not groups:
        await msg.reply("No groups yet — create one with /create_group <name>.")
        return
    lines = [
        f"• {g.subject} (id: {g.id}, {g.total_participant_count} members)"
        for g in groups
    ]
    await msg.reply("*Your groups:*\n" + "\n".join(lines))


@wa.on_message(filters.command("invite", ignore_case=True) & is_admin)
async def invite_link(_: WhatsApp, msg: types.Message):
    group_id = msg.text.partition(" ")[2].strip()
    if not group_id:
        await msg.reply("Usage: /invite <group_id>")
        return
    group = await wa.get_group(group_id)
    invite = await group.get_invite_link()
    await msg.reply(f"🔗 Invite link for '{group.subject}':\n{invite.link}")


@wa.on_message(filters.command("requests", ignore_case=True) & is_admin)
async def pending_join_requests(_: WhatsApp, msg: types.Message):
    group_id = msg.text.partition(" ")[2].strip()
    if not group_id:
        await msg.reply("Usage: /requests <group_id>")
        return
    requests = list(await wa.get_group_join_requests(group_id))
    if not requests:
        await msg.reply("No pending join requests for that group.")
        return
    for req in requests:
        PENDING_REQUESTS[req.id] = req
        await msg.reply(
            text=f"🙋 {req.user.name or req.user.bsuid} wants to join.",
            buttons=[
                types.Button(
                    title="✅ Approve", callback_data=f"group_req:approve:{req.id}"
                ),
                types.Button(
                    title="❌ Reject", callback_data=f"group_req:reject:{req.id}"
                ),
            ],
        )


@wa.on_callback_button(filters.startswith("group_req:approve:") & is_admin)
async def approve_request(_: WhatsApp, clb: types.CallbackButton):
    req = PENDING_REQUESTS.pop(clb.data.split(":")[2], None)
    if req is None:
        await clb.reply(
            "This request already expired — send /requests <group_id> again."
        )
        return
    await req.approve()
    await clb.reply(f"✅ Approved {req.user.name or req.user.bsuid}.")


@wa.on_callback_button(filters.startswith("group_req:reject:") & is_admin)
async def reject_request(_: WhatsApp, clb: types.CallbackButton):
    req = PENDING_REQUESTS.pop(clb.data.split(":")[2], None)
    if req is None:
        await clb.reply(
            "This request already expired — send /requests <group_id> again."
        )
        return
    await req.reject()
    await clb.reply(f"❌ Rejected {req.user.name or req.user.bsuid}.")


@wa.on_message(filters.command("remove", ignore_case=True) & is_admin)
async def remove_participant(_: WhatsApp, msg: types.Message):
    parts = msg.text.split()
    if len(parts) != 3:
        await msg.reply("Usage: /remove <group_id> <participant_wa_id>")
        return
    _, group_id, wa_id = parts
    await wa.remove_group_participants(group_id, [wa_id])
    await msg.reply(f"🚫 Removed {wa_id} from group {group_id}.")


@wa.on_message(filters.command("delete_group", ignore_case=True) & is_admin)
async def delete_group(_: WhatsApp, msg: types.Message):
    group_id = msg.text.partition(" ")[2].strip()
    if not group_id:
        await msg.reply("Usage: /delete_group <group_id>")
        return
    await wa.delete_group(group_id)
    await msg.reply(f"🗑️ Deleting group {group_id}.")


@wa.on_message(filters.command("help", "start", ignore_case=True) & is_admin)
async def help_(_: WhatsApp, msg: types.Message):
    await msg.reply(
        "*Community group concierge*\n"
        "/create_group <name> — create a new group\n"
        "/groups — list your groups\n"
        "/invite <group_id> — get an invite link\n"
        "/requests <group_id> — review pending join requests\n"
        "/remove <group_id> <wa_id> — remove a participant\n"
        "/delete_group <group_id> — delete a group"
    )


# Run with: pywa dev
