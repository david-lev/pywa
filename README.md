[//]: # (Logo design by @nyatitilkesh https://github.com/nyatitilkesh | Telegram: @nyatitilkesh)
<p align="center">
  <a href="https://github.com/david-lev/pywa">
    <img src="https://pywa.readthedocs.io/en/latest/_static/pywa-logo.png" width="200" height="200" alt="PyWa Logo"/>
  </a>
</p>

<p align="center">
  <strong>🚀 Build WhatsApp Bots in Python • Fast. Effortless. Powerful.</strong>
</p>

<p align="center">
  <small><em>🤖 Hey there! I am using PyWa.</em></small>
</p>


<p align="center">
  <a href="https://pypi.org/project/pywa/"><img src="https://img.shields.io/pypi/v/pywa.svg" /></a>
  <a href="https://pypi.org/project/pywa/"><img src="https://static.pepy.tech/badge/pywa" /></a>
  <a href="https://github.com/david-lev/pywa/actions/workflows/tests.yml"><img src="https://img.shields.io/github/actions/workflow/status/david-lev/pywa/tests.yml?label=tests" /></a>
 <a href="https://pywa.readthedocs.io"><img src="https://readthedocs.org/projects/pywa/badge/?version=latest&" /></a>
  <a href="https://github.com/david-lev/pywa/blob/master/LICENSE"><img src="https://img.shields.io/github/license/david-lev/pywa" /></a>
  <a href="https://www.codefactor.io/repository/github/david-lev/pywa/overview/master"><img src="https://www.codefactor.io/repository/github/david-lev/pywa/badge/master" /></a>
  <a href="https://t.me/py_wa"><img src="https://badges.aleen42.com/src/telegram.svg" /></a>
</p>

---

**💫 PyWa is an all-in-one Python framework for the WhatsApp Cloud API.**

Send **rich media messages**, use **interactive buttons**, listen to **real-time events**, build and send **flows**,
design and send **template messages**, and enjoy **blazing-fast async support** with full integration for **FastAPI,
Flask**, and more.
Fully **typed**, **documented**, and **production-ready** — build powerful bots in minutes.


📄 **Quick Documentation Index**
--------------------------------

> [Get Started](https://pywa.readthedocs.io/en/latest/content/getting-started.html)
> • [Client](https://pywa.readthedocs.io/en/latest/content/client/overview.html)
> • [Handlers](https://pywa.readthedocs.io/en/latest/content/handlers/overview.html)
> • [Listeners](https://pywa.readthedocs.io/en/latest/content/listeners/overview.html)
> • [Updates](https://pywa.readthedocs.io/en/latest/content/updates/overview.html)
> • [Filters](https://pywa.readthedocs.io/en/latest/content/filters/overview.html)
> • [Templates](https://pywa.readthedocs.io/en/latest/content/templates/overview.html)
> • [Flows](https://pywa.readthedocs.io/en/latest/content/flows/overview.html)
> • [Calls](https://pywa.readthedocs.io/en/latest/content/calls/overview.html)

------------------------

⚡ **Why PyWa?**
---------------

- **🚀 Fast & Simple** – Focus on building, not boilerplate.
- **💬 Rich Messaging** – Text, images, files, audio, locations, contacts, buttons & more.
- **📩 Real-Time Updates** – Messages, callbacks, delivery/read receipts, account updates, and more.
- **🔔 Listeners** – Wait for user replies, clicks, or reactions with ease.
- **📄 Templates** – Create and send powerful WhatsApp templates.
- **♻️ Flows** – Build interactive WhatsApp flows effortlessly.
- **📞 Calls Support** – Receive and handle call events.
- **🔄 Webhook-Ready** – Built-in server for development and production, or attach to your own FastAPI/Flask app.
- **🔬 Filters** – Advanced filtering for incoming updates.
- **✅ Production-Ready** – Typed, documented, and fully tested.

------------------------

👨‍💻 **How to Use**
------------------

### 1. Handle incoming messages

Start with a `WhatsApp` client and register handlers for the updates you want to receive.
During development, run the webhook server with `pywa dev`. For production, use `pywa run`.

```python
# main.py
from pywa import WhatsApp, filters, types, utils

callback_url = utils.start_ngrok_tunnel(
    auth_token="NGROK_AUTH_TOKEN",
    domain="your-domain.ngrok-free.app",
)

wa = WhatsApp(
    phone_id="1234567890",
    token="EAA...",
    app_id="1234567890",
    app_secret="********",
    callback_url=callback_url,
    verify_token="my-verify-token",
)


@wa.on_message(filters.text)
def echo(client: WhatsApp, msg: types.Message):
    msg.reply(f"You said: {msg.text}")
```

Run it:

```bash
pywa dev
```

Use this when deploying:

```bash
pywa run
```

> See the [Handlers guide](https://pywa.readthedocs.io/en/latest/content/handlers/overview.html) for decorators,
> filters, callback URL registration, custom servers, and handler flow.

### 2. Send messages, media, templates, flows, and manage resources

Use the same client to send messages, media, templates, flows, and to manage WhatsApp Business resources.

```python
from pywa import WhatsApp, types

wa = WhatsApp(
    phone_id="1234567890",
    token="EAA...",
)

wa.send_message(
    to="9876543210",
    text="Hello from PyWa!",
    buttons=[
        types.Button(title="Menu", callback_data="menu"),
        types.Button(title="Help", callback_data="help"),
    ],
)

wa.send_image(
    to="9876543210",
    image="https://example.com/image.jpg",
    caption="Check out this image!",
)
```

> See the [Client guide](https://pywa.readthedocs.io/en/latest/content/client/overview.html) for the full API.

### 3. Listen for the next user response

Handlers are great for entry points. When you need to continue a conversation, use listeners.

```python
from pywa import WhatsApp, filters, types

wa = WhatsApp(...)


@wa.on_message(filters.command("start"))
def start(client: WhatsApp, msg: types.Message):
    name = msg.reply("What's your name?").wait_for_reply(filters=filters.text).text
    msg.reply(f"Nice to meet you, {name}!")
```

> See the [Listeners guide](https://pywa.readthedocs.io/en/latest/content/listeners/overview.html) for timeouts,
> filters, callbacks, and waiting for clicks or replies.

### 4. Use your own server when needed

The CLI is the easiest way to run pywa, but you can also attach pywa to an existing
[FastAPI](https://fastapi.tiangolo.com/) or [Flask](https://flask.palletsprojects.com/) app.

```python
from fastapi import FastAPI
from pywa import WhatsApp, filters, types

app = FastAPI()

wa = WhatsApp(
    ...,
    server=app,  # Pass your FastAPI or Flask app here
    webhook_endpoint="/whatsapp",  # Use different endpoint from "/" to avoid conflicts with your own routes
)


@wa.on_message(filters.text)
def echo(client: WhatsApp, msg: types.Message):
    msg.reply(msg.text)


# Serve your own routes alongside pywa's webhook
@app.get("/")
def read_root():
    return {"Hello": "World"}
```

Run your server normally

### 5. Async usage

PyWa also supports async usage with the same API. Replace imports from `pywa` with `pywa_async`
and use `await`.

```python
from pywa_async import WhatsApp, filters, types, utils

callback_url = utils.start_ngrok_tunnel(auth_token="NGROK_AUTH_TOKEN")

wa = WhatsApp(..., callback_url=callback_url)


@wa.on_message(filters.text)
async def hello(client: WhatsApp, msg: types.Message):
    await msg.react("👋")
    await msg.reply("Hello from PyWa Async!")
```

### 6. Create and send template messages

> See [Templates](https://pywa.readthedocs.io/en/latest/content/templates/overview.html) for more details and examples.

```python
from pywa import WhatsApp
from pywa.types.templates import *

wa = WhatsApp(..., waba_id=123456)

# Create a template
wa.create_template(
    template=Template(
        name="buy_new_iphone_x",
        category=TemplateCategory.MARKETING,
        language=TemplateLanguage.ENGLISH_US,
        parameter_format=ParamFormat.NAMED,
        components=[
            ht := HeaderText("The New iPhone {{iphone_num}} is here!", iphone_num=15),
            bt := BodyText("Buy now and use the code {{code}} to get {{per}}% off!", code="WA_IPHONE_15", per=15),
            FooterText(text="Powered by PyWa"),
            Buttons(
                buttons=[
                    url := URLButton(text="Buy Now", url="https://example.com/shop/{{1}}", example="iphone15"),
                    PhoneNumberButton(text="Call Us", phone_number="1234567890"),
                    qrb1 := QuickReplyButton(text="Unsubscribe from marketing messages"),
                    qrb2 := QuickReplyButton(text="Unsubscribe from all messages"),
                ]
            ),

        ]
    ),
)

# Send the template message
wa.send_template(
    to="9876543210",
    name="buy_new_iphone_x",
    language=TemplateLanguage.ENGLISH_US,
    params=[
        ht.params(iphone_num=30),
        bt.params(code="WA_IPHONE_30", per=30),
        url.params(url_variable="iphone30", index=0),
        qrb1.params(callback_data="unsubscribe_from_marketing_messages", index=1),
        qrb2.params(callback_data="unsubscribe_from_all_messages", index=2),
    ]
)
```

### 7. Create and send flows

> See [Flows](https://pywa.readthedocs.io/en/latest/content/flows/overview.html) for much more details and examples.

```python
from pywa import WhatsApp, types
from pywa.types.flows import *

# Create a WhatsApp client
wa = WhatsApp(..., waba_id=123456)

# Build a flow
my_flow_json = FlowJSON(
    screens=[
        Screen(
            id="NEWSLETTER",
            title="PyWa Newsletter",
            layout=Layout(
                children=[
                    TextHeading(text="Subscribe to our newsletter"),
                    name := TextInput(
                        name="name",
                        label="Name",
                        input_type=InputType.TEXT,
                        required=False,
                    ),
                    email := TextInput(
                        name="email",
                        label="Email",
                        input_type=InputType.EMAIL,
                        required=True,
                    ),
                    Footer(
                        label="Subscribe",
                        on_click_action=CompleteAction(
                            payload={  # Payload to send to the server
                                "name": name.ref,
                                "email": email.ref,
                            }
                        )
                    )
                ]
            )
        )
    ]
)

# Create the flow
wa.create_flow(
    name="subscribe_to_newsletter",
    categories=[FlowCategory.SIGN_UP, FlowCategory.OTHER],
    flow_json=my_flow_json,
    publish=True
)

# Send the flow to a user
wa.send_text(
    to="9876543210",
    text="Hello from PyWa!",
    buttons=types.FlowButton(
        title="Subscribe to our newsletter!",
        flow_name="subscribe_to_newsletter",
    )
)


# Handle the flow response
@wa.on_flow_completion
def handle_flow_response(_: WhatsApp, flow: types.FlowCompletion):
    flow.reply(
        text=f"Thank you for subscribing to our newsletter, {flow.response['name']}! "
             f"We will send you updates to {flow.response['email']}.",
        buttons=[types.Button(title="Unsubscribe", callback_data="unsubscribe")]
    )
```

🎛 **Installation**
--------------------

- **Install using pip3:**

```bash
pip3 install -U pywa
```

- **Install the built-in webhook server for `pywa dev` and `pywa run`:**

```bash
pip3 install -U "pywa[server]"
```

- **Install ngrok if you want to use `utils.start_ngrok_tunnel()` for local development:**

```bash
pip3 install -U ngrok
```

- **Install from source (the bleeding edge):**

```bash
pip3 install -U git+https://github.com/david-lev/pywa.git
```

- **If you use Flows and want pywa's default encryption helpers:**

```bash
pip3 install -U "pywa[cryptography]"
```

💾 **Requirements**
--------------------

- Python 3.10 or higher - https://www.python.org

📖 **Setup and Usage**
-----------------------

See the [Documentation](https://pywa.readthedocs.io/) for detailed instructions


⚖️ **License**
---------------

This project is licensed under the MIT License - see the
[LICENSE](https://github.com/david-lev/pywa/blob/master/LICENSE) file for details


🔱 **Contributing**
--------------------

Contributions are welcome! Please see
the [Contributing Guide](https://github.com/david-lev/pywa/blob/master/CONTRIBUTING.md) for more information.

🗣 **Community**
--------------------

Join the [Telegram Group](https://t.me/pywachat) to discuss, ask questions, and share your projects built with PyWa!
