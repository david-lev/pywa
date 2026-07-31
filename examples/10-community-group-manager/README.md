# 👥 Community Group Concierge Bot

> 🤖 **AI-generated example.** This bot and its README were written by an AI coding assistant
> for pywa's example gallery. It's meant as a learning reference, not vetted
> production code — please read through it before running it.

**Feature focus:** the [WhatsApp Groups API](https://pywa.readthedocs.io/en/latest/content/groups/overview.html)
(`pywa.types.groups`) — creating and managing WhatsApp groups, generating invite links, and
approving/rejecting join requests, all via chat commands.

## What it demonstrates

- `wa.create_group(subject=..., join_approval_mode=...)`
- `wa.get_groups()` / `wa.get_group(group_id)`
- `group.get_invite_link()` — an object shortcut instead of the equivalent client method
- `wa.get_group_join_requests(group_id)`, and approving/rejecting a specific request with
  `req.approve()` / `req.reject()` shortcuts triggered from callback buttons
- `wa.remove_group_participants(...)` and `wa.delete_group(...)`

## Prerequisites

- Python 3.10+
- A Meta App with the WhatsApp product added, with the **Groups** feature enabled

## Setup

```bash
cd examples/10-community-group-manager
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env — set ADMIN_NUMBERS to your own WhatsApp ID!
```

## Run

```bash
pywa dev
```

## Try it

From an `ADMIN_NUMBERS` number, send `/help`, then:

1. `/create_group Book Club` → creates a new group (creation is asynchronous on WhatsApp's side).
2. `/groups` → lists your groups and their IDs.
3. `/invite <group_id>` → get an invite link to share with people you want to join.
4. Once someone requests to join, `/requests <group_id>` shows each pending request with
   "Approve"/"Reject" buttons.
5. `/remove <group_id> <participant_wa_id>` / `/delete_group <group_id>` for cleanup.

## Notes

`PENDING_REQUESTS` is an in-memory cache mapping a join request ID to its `GroupJoinRequest`
object, purely so the callback buttons can call `.approve()`/`.reject()` directly without
re-fetching — swap it for a real store (or re-fetch by ID) in production.

## Async / sync

This example is written with `pywa_async`. Run `pywa new examples 10-community-group-manager --async`
to fetch it as-is, or omit `--async` to get an automatically generated synchronous (`pywa`)
version instead.
