[//]: # (Logo design by @nyatitilkesh https://github.com/nyatitilkesh | Telegram: @nyatitilkesh)
<p align="center">
  <a href="https://github.com/david-lev/pywa">
    <img src="https://pywa.readthedocs.io/en/latest/_static/pywa-logo.png" width="180" height="180" alt="PyWa Logo"/>
  </a>
</p>

<h1 align="center">PyWa</h1>

<p align="center">
  <strong>The Python framework for building WhatsApp bots.</strong><br>
  <sub>Fast. Typed. Production-ready. From prototype to production in minutes.</sub>
</p>

<p align="center">
  <a href="https://pypi.org/project/pywa/"><img src="https://img.shields.io/pypi/v/pywa?color=%2334D058&label=pypi" alt="PyPI Version"/></a>
  <a href="https://pepy.tech/project/pywa"><img src="https://static.pepy.tech/badge/pywa" alt="Downloads"/></a>
  <a href="https://pypi.org/project/pywa/"><img src="https://img.shields.io/pypi/pyversions/pywa?color=%2334D058" alt="Python Versions"/></a>
  <a href="https://github.com/david-lev/pywa/actions/workflows/tests.yml"><img src="https://img.shields.io/github/actions/workflow/status/david-lev/pywa/tests.yml?label=tests" alt="Tests"/></a>
  <a href="https://pywa.readthedocs.io"><img src="https://readthedocs.org/projects/pywa/badge/?version=latest&" alt="Docs"/></a>
  <a href="https://github.com/david-lev/pywa/blob/master/LICENSE"><img src="https://img.shields.io/github/license/david-lev/pywa?color=%2334D058" alt="License"/></a>
  <a href="https://www.codefactor.io/repository/github/david-lev/pywa/overview/master"><img src="https://www.codefactor.io/repository/github/david-lev/pywa/badge/master" alt="Code Quality"/></a>
  <a href="https://t.me/py_wa"><img src="https://badges.aleen42.com/src/telegram.svg" /></a></p>

---

**PyWa** is a comprehensive, fully-typed Python framework for
the [WhatsApp Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api).
It handles everything — sending messages, receiving webhooks, building interactive flows, managing templates,
handling calls — so you can focus on building your bot, not wrestling with the API.

```bash
pip install -U "pywa[server]"
```

---

## ✨ Why PyWa?

<table>
  <tr>
    <td>💬 <strong>Rich Messaging</strong></td>
    <td>Text, images, videos, documents, audio, stickers, locations, contacts, buttons, lists & more</td>
  </tr>
  <tr>
    <td>📩 <strong>Real-Time Webhooks</strong></td>
    <td>Messages, button clicks, delivery receipts, read receipts, reactions & account updates</td>
  </tr>
  <tr>
    <td>🔔 <strong>Listeners</strong></td>
    <td>Chain conversations naturally — wait for replies, clicks, or reactions inline</td>
  </tr>
  <tr>
    <td>📄 <strong>Templates</strong></td>
    <td>Create, send, and manage WhatsApp message templates with full parameter support</td>
  </tr>
  <tr>
    <td>♻️ <strong>Flows</strong></td>
    <td>Build rich, multi-screen interactive WhatsApp Flows in pure Python</td>
  </tr>
  <tr>
    <td>📞 <strong>Calls</strong></td>
    <td>Handle incoming and outgoing WhatsApp call events</td>
  </tr>
  <tr>
    <td>⚡ <strong>Async Support</strong></td>
    <td>Full async/await API via <code>pywa_async</code> — same interface, zero friction</td>
  </tr>
  <tr>
    <td>🔌 <strong>Server Integrations</strong></td>
    <td>Built-in webhook server, or plug into your existing FastAPI / Flask app</td>
  </tr>
  <tr>
    <td>🛡️ <strong>Type Safety</strong></td>
    <td>Fully typed - full autocomplete and static analysis everywhere</td>
  </tr>
  <tr>
    <td>🔬 <strong>Smart Filters</strong></td>
    <td>Composable filters with logical operators for precise update routing</td>
  </tr>
  <tr>
    <td>🧰 <strong>CLI Tools</strong></td>
    <td><code>pywa dev</code> for local development, <code>pywa run</code> for production</td>
  </tr>
</table>

---

## 🚀 Quick Start

### 1. Echo Bot — 5 lines of code

```python
# main.py
from pywa import WhatsApp, filters, types

wa = WhatsApp(
    phone_id="1234567890",
    token="EAA...",
    app_id=1234567890,
    app_secret="********",
    callback_url="https://your-domain.ngrok-free.app",
    verify_token="my-verify-token",
)


@wa.on_message(filters.text)
def echo(_: WhatsApp, msg: types.Message):
    msg.reply(f"You said: {msg.text}")
```

Start the webhook server:

```bash
pywa dev    # Local development
pywa run    # Production
```

### 2. Rich Messages — Buttons, Media & More

```python
from pywa import WhatsApp, types

wa = WhatsApp(phone_id="1234567890", token="EAA...")

# Text with interactive buttons
wa.send_message(
    to="9876543210",
    text="How can I help you today?",
    buttons=[
        types.Button(title="📋 Menu", callback_data="menu"),
        types.Button(title="💬 Support", callback_data="help"),
    ],
)

# Images, documents, audio — one-liners
wa.send_image(to="9876543210", image="https://example.com/photo.jpg", caption="Check this out!")
wa.send_document(to="9876543210", document="report.pdf")
```

### 3. Conversational Flows — Listeners

Handlers define entry points. Listeners let you continue the conversation naturally:

```python
@wa.on_message(filters.command("start"))
def start(_: WhatsApp, msg: types.Message):
    name = msg.reply("What's your name?").wait_for_reply(filters=filters.text).text
    msg.reply(f"Nice to meet you, {name}!")
```

### 4. Plug Into Your Own Server

```python
from fastapi import FastAPI
from pywa import WhatsApp, filters, types

app = FastAPI()
wa = WhatsApp(..., server=app, webhook_endpoint="/webhook")


@wa.on_message(filters.text)
def echo(_: WhatsApp, msg: types.Message):
    msg.reply(msg.text)


@app.get("/")
def health():
    return {"status": "ok"}
```

### 5. Full Async Support

Same API. Just swap the import and add `await`:

```python
from pywa_async import WhatsApp, filters, types

wa = WhatsApp(...)


@wa.on_message(filters.text)
async def hello(_: WhatsApp, msg: types.Message):
    await msg.react("👋")
    await msg.reply("Hello from async PyWa!")
```

### 6. Templates

Create and send [WhatsApp message templates](https://pywa.readthedocs.io/en/latest/content/templates/overview.html) with
full parameter support:

```python
from pywa import WhatsApp
from pywa.types.templates import *

wa = WhatsApp(..., waba_id=123456)

wa.create_template(
    template=Template(
        name="order_update",
        category=TemplateCategory.MARKETING,
        language=TemplateLanguage.ENGLISH_US,
        parameter_format=ParamFormat.NAMED,
        components=[
            ht := HeaderText("Your order #{{order_id}} has shipped!", order_id="12345"),
            bt := BodyText("Track it with code {{code}}.", code="ABC123"),
            FooterText(text="Powered by PyWa"),
            Buttons(buttons=[
                url := URLButton(text="Track Order", url="https://example.com/track/{{1}}", example="12345"),
                QuickReplyButton(text="Unsubscribe"),
            ]),
        ],
    ),
)

# Send it
wa.send_template(
    to="9876543210",
    name="order_update",
    language=TemplateLanguage.ENGLISH_US,
    params=[
        ht.params(order_id="67890"),
        bt.params(code="XYZ789"),
        url.params(url_variable="67890", index=0),
    ],
)
```

### 7. Interactive Flows

Build [WhatsApp Flows](https://pywa.readthedocs.io/en/latest/content/flows/overview.html) — multi-screen interactive
experiences — entirely in Python:

```python
from pywa import WhatsApp, types
from pywa.types.flows import *

wa = WhatsApp(..., waba_id=123456)

my_flow = FlowJSON(
    screens=[
        Screen(
            id="SIGNUP",
            title="Join Our Newsletter",
            layout=Layout(children=[
                TextHeading(text="Subscribe for updates"),
                name := TextInput(name="name", label="Name", input_type=InputType.TEXT),
                email := TextInput(name="email", label="Email", input_type=InputType.EMAIL, required=True),
                Footer(
                    label="Subscribe",
                    on_click_action=CompleteAction(
                        payload={"name": name.ref, "email": email.ref}
                    ),
                ),
            ]),
        )
    ]
)

wa.create_flow(name="newsletter_signup", categories=[FlowCategory.SIGN_UP], flow_json=my_flow, publish=True)


@wa.on_flow_completion
def on_signup(_: WhatsApp, flow: types.FlowCompletion):
    flow.reply(text=f"Welcome, {flow.response['name']}! You're subscribed at {flow.response['email']}.")
```

### 8. Account & Resource Management

Beyond messaging, PyWa gives you full control over your WhatsApp Business resources:

```python
from pywa import WhatsApp

wa = WhatsApp(phone_id="1234567890", token="EAA...", waba_id=123456)

# Business profile
profile = wa.get_business_profile()
wa.update_business_profile(about="Powered by PyWa", description="We build bots!", profile_picture="profile.jpg")

# Media management
media = wa.upload_media(media="photo.jpg")
media.stream(), media.download(), media.reupload(), media.delete()

# QR codes
qr = wa.create_qr_code(prefilled_message="Hi! I saw your QR code")
qr.qr_image_url, qr.code, qr.update(prefilled_message="Hello"), qr.delete()

# Usernames
wa.get_reserved_usernames()
wa.set_username(username="mybusiness")
wa.get_current_username()

# Groups
wa.create_group(subject="VIP Customers")
wa.get_groups()
wa.get_group_join_requests()

# Commerce
wa.get_commerce_settings()
wa.update_commerce_settings(is_catalog_visible=True, is_cart_enabled=
True)
# User management
wa.block_users(users=["9876543210"])
blocked = wa.get_blocked_users()
```

> See the [Client guide](https://pywa.readthedocs.io/en/latest/content/client/overview.html) for the full resource
> management API — templates, flows, media, QR codes, commerce, groups, calls, and more.

### 9. Partners & Tech Providers

Building a platform on top of WhatsApp? PyWa supports multi-WABA management, phone number provisioning, and callback
routing for [Solution Partners](https://developers.facebook.com/docs/whatsapp/solution-partners) and Tech Providers:

```python
from pywa import WhatsApp, types, filters

wa = WhatsApp(phone_id="1234567890", token="EAA...", waba_id=123456)


@wa.on_message(filters.sent_to(phone_number_id=...))
def handle_message_for_specific_phone_number(wa: WhatsApp, msg: types.Message): ...


@wa.on_account_update(filters.account_restriction)
def handle_account_restriction(wa: WhatsApp, update: types.AccountUpdate): ...


@wa.on_message(filters.account_deleted)
def handle_account_deletion(wa: WhatsApp, update: types.AccountUpdate): ...


# Get all WABAs you manage
shared_wabas = wa.get_shared_business_accounts()
owned_wabas = wa.get_owned_business_accounts()

# Provision phone numbers on a WABA
phone = wa.create_phone_number(country_calling_code="1", phone_number="5551234567", verified_name="John Doe")
wa.request_verification_code(phone_id=phone.id, code_method="SMS")
wa.verify_phone_number(code="123456", phone_id=phone.id)
wa.register_phone_number(phone_id=phone.id)

# Route webhooks per-WABA or per-phone
wa.override_waba_callback_url(callback_url="https://your-platform.com/waba/123")
wa.override_phone_callback_url(callback_url="https://your-platform.com/phone/456")

# Migrate templates & flows between WABAs
wa.migrate_templates(source_waba_id=111111, destination_waba_id=222222)
wa.migrate_flows(source_waba_id=111111, destination_waba_id=222222, source_flow_names=["flow_1"])
```

---

## 📦 Installation

```bash
# Core (sending messages, no webhook server)
pip install -U pywa

# With built-in webhook server (recommended)
pip install -U "pywa[server]"

# For Flow encryption support
pip install -U "pywa[cryptography]"

# Everything
pip install -U "pywa[server,cryptography]"
```

> **Requirements:** Python 3.10+

---

## 📚 Documentation

Full documentation is available at **[pywa.readthedocs.io](https://pywa.readthedocs.io)**.

| Topic                                                                                 | Description                                     |
|:--------------------------------------------------------------------------------------|:------------------------------------------------|
| [Getting Started](https://pywa.readthedocs.io/en/latest/content/getting-started.html) | Setup, first bot, and key concepts              |
| [Client](https://pywa.readthedocs.io/en/latest/content/client/overview.html)          | Sending messages, media, and managing resources |
| [Handlers](https://pywa.readthedocs.io/en/latest/content/handlers/overview.html)      | Decorators, filters, and webhook routing        |
| [Listeners](https://pywa.readthedocs.io/en/latest/content/listeners/overview.html)    | Conversational flows and inline waiting         |
| [Updates](https://pywa.readthedocs.io/en/latest/content/updates/overview.html)        | Message, callback, status, and system updates   |
| [Filters](https://pywa.readthedocs.io/en/latest/content/filters/overview.html)        | Composable, reusable update filtering           |
| [Templates](https://pywa.readthedocs.io/en/latest/content/templates/overview.html)    | Create, send, and manage message templates      |
| [Flows](https://pywa.readthedocs.io/en/latest/content/flows/overview.html)            | Build interactive multi-screen flows            |
| [Calls](https://pywa.readthedocs.io/en/latest/content/calls/overview.html)            | Handle voice call events                        |

---

## 🤝 Contributing

Contributions are welcome! Check out
the [Contributing Guide](https://github.com/david-lev/pywa/blob/master/CONTRIBUTING.md) to get started.

## 💬 Community

Questions? Ideas? Join the conversation:

- 💬 [Telegram Chat](https://t.me/pywachat) — Community discussions & support
- 📢 [Telegram Channel](https://t.me/py_wa) — Announcements & updates

## ⚖️ License

PyWa is open-source software licensed under the [MIT License](https://github.com/david-lev/pywa/blob/master/LICENSE).
