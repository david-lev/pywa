# PyWa Examples

Runnable, end-to-end examples for [PyWa](https://github.com/david-lev/pywa). Each folder is a self-contained bot you can launch in under a minute.

| # | Example | What it shows | Stack |
|---|---|---|---|
| [01](01_echo_bot/) | **Echo bot** | Minimal webhook + first reply | FastAPI |
| [02](02_menu_buttons/) | **Menu with buttons & sections** | `Button`, `SectionList`, typed `CallbackData` | FastAPI |
| [03](03_conversation_listeners/) | **Conversation with listeners** | `wait_for_reply`, `wait_for_click`, filters | FastAPI |
| [04](04_flows_newsletter/) | **Flow: newsletter signup** | `FlowJSON`, `on_flow_request`, `on_flow_completion`, encryption | FastAPI |
| [05](05_templates/) | **Templates** | Create + send a marketing template | Script (no webhook) |
| [06](06_media_handling/) | **Media: receive, download, send** | `Image`/`Audio`/`Document`, upload, reply with media | FastAPI |
| [07](07_async_fastapi/) | **Full async bot** | `pywa_async`, `async def` handlers | FastAPI |
| [08](08_flask_app/) | **Flask alternative** | Same idea as 01, on Flask | Flask |

---

## ⚙️ Prerequisites

1. A **Meta Developer account** with a WhatsApp Business app — [setup guide](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started).
2. A **test phone number** (Meta provides one for free).
3. A **public URL** for the webhook during local development. Pick one:
   - [`ngrok`](https://ngrok.com/) — `ngrok http 8000`
   - [`cloudflared`](https://github.com/cloudflare/cloudflared) — `cloudflared tunnel --url http://localhost:8000`

You'll need these values handy:

| Name | Where to find it |
|---|---|
| `WA_PHONE_ID` | WhatsApp → API Setup → "Phone number ID" |
| `WA_TOKEN` | WhatsApp → API Setup → "Temporary access token" (or a permanent system-user token) |
| `WA_VERIFY_TOKEN` | Any random string you choose (e.g. `openssl rand -hex 16`) |
| `WA_APP_ID` | App dashboard → Settings → Basic |
| `WA_APP_SECRET` | App dashboard → Settings → Basic |
| `WA_BUSINESS_ACCOUNT_ID` | WhatsApp Manager → Business account info (only needed for templates/flows) |
| `WA_CALLBACK_URL` | Your public tunnel URL (e.g. `https://abc123.ngrok.io`) |

---

## 🚀 Quick start

```bash
# from the repo root
python -m venv .venv && source .venv/bin/activate
pip install -e ".[fastapi,cryptography]"

# pick an example
cp examples/.env.example examples/01_echo_bot/.env
# edit the .env with your values

# expose your local server
ngrok http 8000      # in another terminal

# run
cd examples/01_echo_bot
fastapi dev main.py
```

Send a WhatsApp message to your test number — the bot will reply.

---

## 🧩 Conventions used in every example

- **Env vars over hardcoded secrets.** Each example loads from a local `.env` (via `os.environ`). Never commit real tokens.
- **Single file (`main.py`).** Long enough to demonstrate, short enough to read in one sitting.
- **Sync by default.** Example `07_async_fastapi` shows the async variant — the API surface is identical except for the imports (`pywa_async` instead of `pywa`) and `async def` handlers.
- **Comments explain *why*, not *what*.** The code is the documentation; comments call out non-obvious decisions or links to the official docs.

---

## 🐛 Troubleshooting

- **Webhook verification fails** → `WA_VERIFY_TOKEN` must match exactly what you typed in the Meta dashboard. The bot prints the resolved value on startup.
- **`401 Unauthorized` when sending** → Token expired (the temporary token from Meta lasts 24h). Generate a permanent system-user token.
- **No incoming updates** → Make sure your tunnel is alive (`curl https://<your-tunnel>/`) and that the `Messages` webhook field is subscribed in the App dashboard.
- **Flow keeps timing out** → Check the encryption keys in `04_flows_newsletter/README.md`. The Meta side rejects flows with mismatched keys silently from the user's view.

---

## 📚 Going deeper

- Full docs: <https://pywa.readthedocs.io>
- API reference: <https://pywa.readthedocs.io/en/latest/content/client/overview.html>
- Telegram community: <https://t.me/pywachat>
