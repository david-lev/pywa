# PyWa
- Python wrapper for the WhatsApp Cloud API

### Client (basic client only to send messages)
```python
from pywa import WhatsApp

wa = WhatsApp(phone_id="YOUR_PHONE_NUMBER", token="YOUR_TOKEN")
wa.send_message(to="PHONE_NUMBER", text="Hello World!")
wa.send_image(to="PHONE_NUMBER", image="PATH_TO_IMAGE")
```

### Webhook (server to receive messages)
```python
from pywa import WhatsApp
from pywa.types import Message, CallbackButtonReply
from flask import Flask

flask_app = Flask(__name__)
wa = WhatsApp(
    phone_id="YOUR_PHONE_NUMBER",
    token="YOUR_TOKEN",
    app=flask_app,
    verify_token="YOUR_VERIFY_TOKEN"
)

@wa.on_message(filters=lambda _, msg: msg.text == "Hello World!")
def hello_world(client, message):
    message.reply(text="Hello from PyWa!", quote=True)
    

@wa.on_button_callback(filters=lambda _, clb: clb.data == "id:123")
def button_callback(client: WhatsApp, callback: CallbackButtonReply):
    name, url = client.get_book(id=callback.data.split(":")[1])
    client.send_document(
        to=callback.from_user.wa_id,
        document=url,
        filename=name
    )

```

This is a work in progress, so lots of things are missing. If you want to contribute, feel free to open a PR.
- Telegram: https://t.me/davidlev

Roadmap:
- [x] Basic client
- [ ] Bound methods
- [ ] Send media
- [ ] Send keyboards
- [ ] Async support
- [x] Webhook
- [x] Message filters
- [x] Message handlers
- [ ] Documentation
- [ ] Examples
- [ ] Tests
- [ ] Publish to PyPi

--------------------

This project is inspired by Pyrogram.