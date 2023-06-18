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

I started working on a bot for WhatsApp and discovered that the integration with the WhatsApp Cloud API is super annoying.
So it's true, there are libraries like heyoo and others, but they don't do much except to allow sending of basic messages through the client as well as to map the messages that arrive (you will have to do the webhook yourself and map using the client's class.. what?). The really annoying things (e.g. keyboards) you will have to do yourself and transfer as a dict)
in brief. I got fed up and decided to start working on PyWa (yes, all the good names have already been taken in Pypi)
So for now it is not possible to use the library, but I hope that in the near future I will finish working on it.
You are more than welcome to give comments about the structure or about features you would like to have. Of course, PR's are also welcome.
- Telegram: https://t.me/davidlev

By the way, the style of the library is influenced by a library called Pyrogram that allows building bots for Telegram.