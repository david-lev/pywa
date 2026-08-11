# pywa examples

> 🤖 **AI-generated.** Every bot, README, and the manifest in this directory were written by an AI
> coding assistant, then reviewed by a maintainer. They're meant as learning references —
> read the code before you run it, and don't treat them as vetted, production-ready software.

Twelve complete, runnable WhatsApp bots — most built around a single core pywa feature. Every
directory is self-contained: an async `main.py`, a `.env.example`, a `requirements.txt`, and a
`README.md` with setup/run/try-it instructions.

| # | Bot | Feature focus |
|---|-----|----------------|
| [01](01-message-router) | 🧭 Smart Support Router Bot | [`filters`](https://pywa.readthedocs.io/en/latest/content/filters/overview.html) |
| [02](02-order-bot) | 🍕 Quick-Serve Restaurant Ordering Bot | [`types`](https://pywa.readthedocs.io/en/latest/content/types/overview.html) (keyboards & media) |
| [03](03-delivery-tracker) | 📬 Delivery Status Notifier Bot | [`updates`](https://pywa.readthedocs.io/en/latest/content/updates/overview.html) (message status) |
| [04](04-otp-verification) | 🔐 Account Verification (OTP) Bot | [`templates`](https://pywa.readthedocs.io/en/latest/content/templates/overview.html) |
| [05](05-loan-application-flow) | 🏦 Loan Application Flow Bot | [`flows`](https://pywa.readthedocs.io/en/latest/content/flows/overview.html) |
| [06](06-onboarding-survey) | 🧑‍🚀 New Customer Onboarding Survey Bot | [`listeners`](https://pywa.readthedocs.io/en/latest/content/listeners/overview.html) |
| [07](07-helpdesk-ticket-bot) | 🎫 Multi-Channel Helpdesk Ticket Bot | [`handlers`](https://pywa.readthedocs.io/en/latest/content/handlers/overview.html) |
| [08](08-business-profile-manager) | 🛠️ WhatsApp-Native Admin Console Bot | [`client`](https://pywa.readthedocs.io/en/latest/content/client/overview.html) (business profile) |
| [09](09-call-center-bot) | 📞 Voice Call-Back Bot | [`calls`](https://pywa.readthedocs.io/en/latest/content/calls/overview.html) |
| [10](10-community-group-manager) | 👥 Community Group Concierge Bot | [`groups`](https://pywa.readthedocs.io/en/latest/content/groups/overview.html) |
| [11](11-media-inbox-bot) | 📥 Media Inbox Bot | `types` (media download/upload) |
| [12](12-existing-app-integration) | 🧩 Existing FastAPI App Integration | `client` (`server=` an app you own) |

## Getting one locally

Clone the repo and `cd` into any directory, or use the `pywa` CLI to fetch just one:

```bash
pip install pywa   # the `pywa` CLI ships with the base package

pywa new examples                        # list all examples
pywa new examples 01-message-router      # download it into ./01-message-router
pywa new examples 01-message-router --async -o ./my-bot
```

Every example ships as `pywa_async` (async) code. Add `--async` to `pywa new examples <slug>` to
get it verbatim, or omit it (the default) to get an automatically generated synchronous (`pywa`)
version — the CLI does the `pywa_async` → `pywa` / `async def` → `def` / `await` removal for you.

## Running any example

```bash
cd <example-dir>
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your credentials
pywa dev
```

Each README has example-specific setup steps (e.g. running a one-time `setup_template.py` or
`setup_flow.py` script) where relevant.
