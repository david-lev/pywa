<img alt="PyWa Logo" height="250" src="https://pywa.readthedocs.io/en/latest/_static/pywa-logo.png" width="250"/>

________________________

# [PyWa](https://github.com/david-lev/pywa) • Python wrapper for the WhatsApp Cloud API

[![PyPi Downloads](https://img.shields.io/pypi/dm/pywa)](https://pypi.org/project/pywa/)
[![PyPI Version](https://badge.fury.io/py/pywa.svg)](https://pypi.org/project/pywa/)
![Tests](https://img.shields.io/github/actions/workflow/status/david-lev/pywa/tests.yml?label=Tests)
[![Docs](https://readthedocs.org/projects/pywa/badge/?version=latest&)](https://pywa.readthedocs.io)
[![License](https://img.shields.io/github/license/david-lev/pywa)](https://github.com/david-lev/pywa/blob/master/LICENSE)
[![CodeFactor](https://www.codefactor.io/repository/github/david-lev/pywa/badge/master)](https://www.codefactor.io/repository/github/david-lev/pywa/overview/master)
[![Telegram](https://badges.aleen42.com/src/telegram.svg)](https://t.me/py_wa)

________________________

**PyWa is a Fast, Simple, Modern and easy-to-use asynchronous Python framework for building WhatsApp bots using the WhatsApp Cloud API.**

> ⚠️ Important: pywa has introduced breaking changes. Please see the [Migration Guide](https://github.com/david-lev/pywa/blob/master/MIGRATION.md) for instructions on updating from earlier versions.


📄 **Quick Documentation Index**
--------------------------------

> [Get Started](https://pywa.readthedocs.io/en/latest/content/getting-started.html)
• [WhatsApp Client](https://pywa.readthedocs.io/en/latest/content/client/overview.html)
• [Handlers](https://pywa.readthedocs.io/en/latest/content/handlers/overview.html)
• [Listeners](https://pywa.readthedocs.io/en/latest/content/listeners/overview.html)
• [Filters](https://pywa.readthedocs.io/en/latest/content/filters/overview.html)
• [Updates](https://pywa.readthedocs.io/en/latest/content/updates/overview.html)
• [Flows](https://pywa.readthedocs.io/en/latest/content/flows/overview.html)
• [Examples](https://pywa.readthedocs.io/en/latest/content/examples/overview.html)

------------------------

⚡ **Features**
---------------
- 🚀 Fast and simple to use. No need to worry about the low-level details.
- 💬 Send text messages with interactive keyboards, images, videos, documents, audio, locations, contacts, etc.
- 📩 Receive messages, callbacks, message status updates, etc.
- ♻️ Create, send and listen to Flows (NEW!)
- 🔄 Built-in support for webhooks (Flask, FastAPI, etc.)
- 🔬 Filters for handling incoming updates
- 📄 Send and create templates
- ✅ Fully typed, documented and tested

------------------------

👨‍💻 **Usage**
----------------

- Create a WhatsApp client and send a message
> See [Getting Started](https://pywa.readthedocs.io/en/latest/content/getting-started.html) for more information.

```python
from pywa import WhatsApp

wa = WhatsApp(
    phone_id="100458559237541",
    token="EAAEZC6hUxkTIB"
)

wa.send_message(
    to="9876543210",
    text="Hello from PyWa!"
)
```

- To listen to updates, create a `WhatsApp` client, pass a web server app ([FastAPI](https://fastapi.tiangolo.com/) in this example) and register callbacks:

> See [Handlers](https://pywa.readthedocs.io/en/latest/content/handlers/overview.html) for more information.

```python
# wa.py
from pywa import WhatsApp, filters, types
from fastapi import FastAPI

fastapi_app = FastAPI()
wa = WhatsApp(
    phone_id="1234567890",
    token="xxxxxxx",
    server=fastapi_app,
    callback_url="https://yourdomain.com/",
    verify_token="xyz123",
    app_id=123456,
    app_secret="yyyyyy"
)

@wa.on_message(filters.matches("Hello", "Hi"))
def hello(client: WhatsApp, msg: types.Message):
    msg.react("👋")
    msg.reply_text(
        text=f"Hello {msg.from_user.name}!",
        buttons=[
            types.Button(
                title="Click me!",
                callback_data="id:123"
            )
        ]
    )

@wa.on_callback_button(filters.startswith("id"))
def click_me(client: WhatsApp, clb: types.CallbackButton):
    clb.reply_text("You clicked me!")
```

- To run the server, use [fastapi-cli](https://fastapi.tiangolo.com/#run-it) (`pip install "fastapi[standard]"`):

```bash
fastapi dev wa.py  # see uvicorn docs for more options (port, host, reload, etc.)
```

💫 **Async Usage**

- PyWa has async support! To use the async version, replace **all** the imports from `pywa` to `pywa_async` and use `async`/`await`:

```python
# wa.py
import fastapi
from pywa_async import WhatsApp, types

fastapi_app = fastapi.FastAPI()
wa = WhatsApp(..., server=fastapi_app)

async def main():
    await wa.send_message(...)

@wa.on_message()
async def hello(_: WhatsApp, msg: types.Message):
    await msg.react("👋")
    await msg.reply(...)
```

```bash
fastapi dev wa.py
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

☑️ **TODO**
------------

- ~~Add support for async~~
- ~~Add support for more web frameworks (Django, aiohttp, etc.)~~
- ~~Add support for flows~~
- Add support for more types of updates (``account_alerts``, ``phone_number_quality_updates``, ``template_category_updates``, etc.)
- Add more examples and guides

Feel free to open an issue if you have any suggestions. or even better - submit a PR!

⚖️ **License**
---------------

This project is licensed under the MIT License - see the
[LICENSE](https://github.com/david-lev/pywa/blob/master/LICENSE) file for details


🔱 **Contributing**
--------------------

Contributions are welcome! Please see the [Contributing Guide](https://github.com/david-lev/pywa/blob/master/CONTRIBUTING.md) for more information.
