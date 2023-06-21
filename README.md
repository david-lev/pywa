# PyWa
- Python wrapper for the WhatsApp Cloud API

## Contents
- [Installation](#installation)
- [Usage](#usage)
- [Getting started](#getting-started)
- [Documentation](#documentation)
- [Examples](#examples)
- [Todo](#todo)
- [Contributing](#contributing)
- [License](#license)
- [Credits](#credits)

## Installation

---
- Install using pip
```bash
pip3 install -U pywa

# or if you want to use webhooks
pip3 install -U pywa[flask]
# or:
pip3 install -U pywa[fastapi]
```
- Install from source (if you love living on the edge)
```bash
pip3 install git+https://github.com/david-lev/pywa
```

## Usage
- Back to [Contents](#contents)
---
#### Sending messages
- Create a WhatsApp client and send a message
```python
from pywa import WhatsApp

wa = WhatsApp(phone_id='100458559237541', token='xxxxxxxxxxxxxxx')

wa.send_message(
    to='9876543210',
    text='Hello from PyWa!'
)
```

#### Handling incoming messages
- Create a WhatsApp client, pass a flask app and start handling incoming updates
```python
from pywa import WhatsApp
from flask import Flask
from pywa.types import Message, CallbackButton, InlineButton
from pywa.filters import TextFilter, CallbackFilter

flask_app = Flask(__name__)
wa = WhatsApp(
    phone_id='1234567890',
    token='xxxxxxxxxxxxxxx',
    app=flask_app,
    verify_token='XYZXYZ',
)

@wa.on_message(filters=TextFilter.EQUALS(('Hello', 'Hi')))
def hello(client: WhatsApp, message: Message):
    message.react('👋')
    message.reply_text(
        text='Hello from PyWa!',
        keyboard=[
            InlineButton(
                title='Click me!',
                callback_data='click_me'
            )
        ]
    )

@wa.on_callback_button(filters=CallbackFilter.DATA_EQUALS('click_me'))
def click_me(client: WhatsApp, clb: CallbackButton):
    clb.reply_text('You clicked me!', quote=True)

flask_app.run()  # Run the flask app to start the webhook
```

## Getting started
- Back to [Contents](#contents)

---
To get started, you need `TOKEN` and `PHONE_ID` from the [Facebook Developer Portal](https://developers.facebook.com/).
You can get these by following the steps below:

1. Create a new app on the [Facebook Developer Portal](https://developers.facebook.com/apps/create/). Select Business >> Business.
2. Enter basic app information when prompted.
3. Add `WhatsApp Messenger` as a product for your app.
4. If you just want to test, go to `API Setup` (under `Products` in the sidebar) and copy the `Temporary access token` and the `Phone number ID`
   - Note: The temporary access token expires after 24 hours. You can generate a new one by clicking on `Generate new token` under `API Setup`.
   - Note: In test mode you can only send messages up to 5 phone numbers. You can add phone numbers to the list by clicking on `To` >> `Manage phone numbers list` under `API Setup`.
5. If you want to go live, go to `API Setup` (under `Products` in the sidebar) and click on `Add phone number`. Fill in the required details and submit the form. You will receive a confirmation email once your request is approved.

## Documentation
- Back to [Contents](#contents)

---
Work in progress

## Examples
- Back to [Contents](#contents)

---
Work in progress

## Todo
- Back to [Contents](#contents)

---
Work in progress

## Contributing
- Back to [Contents](#contents)

---
Work in progress

## License
- Back to [Contents](#contents)

---
Work in progress

## Credits
- Back to [Contents](#contents)

---
Work in progress

