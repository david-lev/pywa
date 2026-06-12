# 03 — Conversation with listeners

A two-question sign-up dialog implemented as **straight-line Python**: each `wait_for_reply` / `wait_for_click` blocks the handler until the user responds (or times out, or hits *Cancel*).

This is the killer feature of PyWa's listener system — no FSM, no per-user dict, no DB lookup just to know "what step is this user on?"

## Run

```bash
cp ../.env.example .env
fastapi dev main.py
```

Send `/signup`.

## Notes

- **One handler per worker.** Listeners hold the handler's frame open. If you run multiple workers, each user's conversation is pinned to the worker that picked up the first message. For multi-worker / serverless deploys you need to share listener state — see the [docs on listeners](https://pywa.readthedocs.io/en/latest/content/listeners/overview.html).
- **`cancelers`** lets the user bail out at any point — here, a *Cancel* button on every step.
- **`filters.new(lambda ...)`** lets you write inline validation (here: age must be a number 1–120).
- **Timeouts always.** Never call `wait_for_*` without one in production — otherwise an idle user keeps a handler frame alive forever.
