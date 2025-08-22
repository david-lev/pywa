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
  <a href="https://github.com/david-lev/pywa/actions/workflows/tests.yml"><img src="https://img.shields.io/github/actions/workflow/status/david-lev/pywa/tests.yml?label=Tests" /></a>
  <a href="https://codecov.io/gh/david-lev/pywa"><img src="https://img.shields.io/codecov/c/github/david-lev/pywa" /></a>
  <a href="https://pywa.readthedocs.io"><img src="https://readthedocs.org/projects/pywa/badge/?version=latest&" /></a>
  <a href="https://github.com/david-lev/pywa/blob/master/LICENSE"><img src="https://img.shields.io/github/license/david-lev/pywa" /></a>
  <a href="https://www.codefactor.io/repository/github/david-lev/pywa/overview/master"><img src="https://www.codefactor.io/repository/github/david-lev/pywa/badge/master" /></a>
  <a href="https://t.me/py_wa"><img src="https://badges.aleen42.com/src/telegram.svg" /></a>
</p>

---

**💫 PyWa is an all-in-one Python framework for the WhatsApp Cloud API.**

Send **rich media messages**, use **interactive buttons**, listen to **real-time events**, build and send **flows**, design and send **template messages**, and enjoy **blazing-fast async support** with full integration for **FastAPI, Flask**, and more.
Fully **typed**, **documented**, and **production-ready** — build powerful bots in minutes.

---

📄 **Quick Documentation Index**
--------------------------------

> [Get Started](https://pywa.readthedocs.io/en/latest/content/getting-started.html)
• [Client](https://pywa.readthedocs.io/en/latest/content/client/overview.html)
• [Handlers](https://pywa.readthedocs.io/en/latest/content/handlers/overview.html)
• [Listeners](https://pywa.readthedocs.io/en/latest/content/listeners/overview.html)
• [Updates](https://pywa.readthedocs.io/en/latest/content/updates/overview.html)
• [Filters](https://pywa.readthedocs.io/en/latest/content/filters/overview.html)
• [Templates](https://pywa.readthedocs.io/en/latest/content/templates/overview.html)
• [Flows](https://pywa.readthedocs.io/en/latest/content/flows/overview.html)
• [Calls](https://pywa.readthedocs.io/en/latest/content/calls/overview.html)

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
- **🔄 Webhook-Ready** – Native support for Flask, FastAPI, and more.
- **🔬 Filters** – Advanced filtering for incoming updates.
- **✅ Production-Ready** – Typed, documented, and fully tested.

------------------------

👨‍💻 **How to Use**
------------------

- **Send a message**
> See [WhatsApp Client](https://pywa.readthedocs.io/en/latest/content/client/overview.html) for all the options.

```python
from pywa import WhatsApp, types

# Create a WhatsApp client
wa = WhatsApp(
    phone_id="100458559237541",
    token="EAAEZC6hUxkTIB"
)

# Send a text message with buttons
wa.send_message(
    to="9876543210",
    text="Hello from PyWa!",
    buttons=[
        types.Button(title="Menu", callback_data="menu"),
        types.Button(title="Help", callback_data="help")
    ]
)

# Send a image message from URL
wa.send_image(
    to="9876543210",
    image="https://example.com/image.jpg",
    caption="Check out this image!",
)
```

- **Handle incoming updates** (with [FastAPI](https://fastapi.tiangolo.com/) in this example)
> See [Handlers](https://pywa.readthedocs.io/en/latest/content/handlers/overview.html) for fully detailed guide.

```python
# wa.py
from pywa import WhatsApp, filters, types
from fastapi import FastAPI

fastapi_app = FastAPI() # FastAPI server

# Create a WhatsApp client
wa = WhatsApp(
    phone_id=1234567890,
    token="************",
    server=fastapi_app, # the server to listen to incoming updates
    callback_url="https://yourdomain.com/",  # the public URL of your server
    verify_token="xyz123", # some random string to verify the webhook
    app_id=123456, # your app id
    app_secret="*******" # your app secret
)

# Register callback to handle incoming messages
@wa.on_message(filters.matches("Hello", "Hi")) # Filter to match text messages that contain "Hello" or "Hi"
def hello(client: WhatsApp, msg: types.Message):
    msg.react("👋") # React to the message with a wave emoji
    msg.reply_text( # Short reply to the message
        text=f"Hello {msg.from_user.name}!", # Greet the user
        buttons=[ # Add buttons to the reply
            types.Button(
                title="About me",
                callback_data="about_me" # Callback data to identify the click
            )
        ]
    )
    # Use the `wait_for_reply` listener to wait for a reply from the user
    age = msg.reply(text="What's your age?").wait_for_reply(filters=filters.text).text
    msg.reply_text(f"Your age is {age}.")

# Register another callback to handle incoming button clicks
@wa.on_callback_button(filters.matches("about_me")) # Filter to match the button click
def click_me(client: WhatsApp, clb: types.CallbackButton):
    clb.reply_text(f"Hello {clb.from_user.name}, I am a WhatsApp bot built with PyWa!") # Reply to the button click
```

- To run the server, use [fastapi-cli](https://fastapi.tiangolo.com/#run-it) (`pip install "fastapi[standard]"`):

```bash
fastapi dev wa.py  # see uvicorn docs for more options (port, host, etc.)
```

- **Async Usage**

- PyWa also supports async usage with the same API. This is useful if you want to use async/await in your code. To use the async version, replace **all** the imports from `pywa` to `pywa_async`:

```python
# wa.py
import fastapi
from pywa_async import WhatsApp, types  # Same API, just different imports

fastapi_app = fastapi.FastAPI()
wa = WhatsApp(..., server=fastapi_app)

async def main():
    await wa.send_message(...) # async call

@wa.on_message
async def hello(_: WhatsApp, msg: types.Message): # async callback
    await msg.react("👋")
    await msg.reply("Hello from PyWa Async!")
```

- **Create and send template messages**
> See [Templates](https://pywa.readthedocs.io/en/latest/content/templates/overview.html) for more details and examples.

```python
from pywa import WhatsApp
from pywa.types.templates import *

wa = WhatsApp(..., business_account_id=123456)

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

- **Create and send flows**
> See [Flows](https://pywa.readthedocs.io/en/latest/content/flows/overview.html) for much more details and examples.

```python
from pywa import WhatsApp, types
from pywa.types.flows import *

# Create a WhatsApp client
wa = WhatsApp(..., business_account_id=123456)

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
                            payload={ # Payload to send to the server
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

- **Install from source (the bleeding edge):**

```bash
pip3 install -U git+https://github.com/david-lev/pywa.git
```

- **If you going to use the webhook features, here is shortcut to install the required dependencies:**

```bash
pip3 install -U "pywa[fastapi]"
pip3 install -U "pywa[flask]"
```

- **If you going to use the Flow features and want to use the default FlowRequestDecryptor and the default FlowResponseEncryptor, here is shortcut to install the required dependencies:**

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

Contributions are welcome! Please see the [Contributing Guide](https://github.com/david-lev/pywa/blob/master/CONTRIBUTING.md) for more information.

🗣 **Community**
--------------------

Join the [Telegram Group](https://t.me/pywachat) to discuss, ask questions, and share your projects built with PyWa!
