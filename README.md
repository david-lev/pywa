# PyWa
- Python wrapper for the WhatsApp Cloud API

### Client (basic client only to send messages)
```python
from pywa import WhatsApp
from pywa.types import Button, SectionList, Section, SectionRow

wa = WhatsApp(phone_id="YOUR_PHONE_NUMBER", token="YOUR_TOKEN")
wa.send_message(to="PHONE_NUMBER", text="Hello World!")
wa.send_reaction(
    to="PHONE_NUMBER",
    message_id=wa.send_image(to="PHONE_NUMBER",image="https://i.imgur.com/4QFZJZM.jpeg"),
    emoji="👍"
)
wa.send_document(
    to="PHONE_NUMBER",
    document="https://file-examples.com/storage/fefb234bc0648a3e7a1a47d/2017/10/file-sample_150kB.pdf",
    filename="sample.pdf"
)
wa.send_message(
    to="PHONE_NUMBER",
    header="Welcome!",
    text="Please choose one of the following options:",
    keyboard=[
            Button("Help me", callback_data="menu:help"),
            Button("Contact", callback_data="menu:contact"),
    ],
    footer="Powered by PyWa"
)
wa.send_message(
    to="PHONE_NUMBER",
    header="Welcome!",
    text="Please select one of the following options:",
    keyboard=SectionList(
        button_title="Select",
        sections=[
            Section(
                title='Utilities',
                rows=[
                    SectionRow(
                        title='Help me',
                        callback_data='menu:help',
                        description='Get help'
                    ),
                    SectionRow(
                        title='Contact',
                        callback_data='menu:contact',
                        description='Contact us'
                    )
                ]
            ),
            Section(
                title='Other',
                rows=[
                    SectionRow(
                        title='About',
                        callback_data='menu:about',
                        description='About us'
                    )
                ]
            )
        ]
    ),
    footer="Powered by PyWa"
)
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

flask_app.run()  # in production use gunicorn or something similar
```

This is a work in progress, so lots of things are missing. If you want to contribute, feel free to open a PR.
- Telegram: https://t.me/davidlev

### Roadmap:
The main purpose of PyWa is to enable two-way integration against the terrible WhatsApp Cloud API.
In WhatsApp there is no connection between a phone number and a webhook, which means that every message that reaches any phone number associated with a Facebook account will reach your webhook (yes, it's horrible).
- So at the library level, client in PyWa - means a phone number. All the chats will go through it but it will only filter messages 'that were actually sent to it' (other messages will be ignored).
- To support situations where it is necessary to handle several numbers at the same time - the server is not initialized by PyWa but manually and transferred to the client. This way you can create several clients and associate them with the same Flask app (or FastAPI).
```python
from pywa import WhatsApp
from flask import Flask

flask_app = Flask(__name__)
wa_1 = WhatsApp(phone_id=12345, app=flask_app, ...)
wa_2 = WhatsApp(phone_id=67890, app=flask_app, ...)

@wa_1.on_message
@wa_2.on_message
def x(client, message): pass

flask_app.run()  # in production use gunicorn or something similar
```

### Todo:

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