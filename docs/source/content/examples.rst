

## Examples
- Back to [Contents](#contents)

- [Sending messages](#sending-messages)
- [Handling incoming messages](#handling-incoming-messages)
---
### Sending messages
- Back to [Examples](#examples)

#### Simple text message
```python
from pywa import WhatsApp

wa = WhatsApp(phone_id='100458559237541', token='xxxxxxxxxxxxxxx')
wa.send_message(
    to='9876543210',
    text='Hello from PyWa! (https://github.com/david-lev/pywa)',
   preview_url=True
)
```

#### Message with buttons
- Buttons are only available in messages of type `text`, `image`, `video`, `audio`, and `document`
- The keyboard is limited to 3 `InlineButton`s
```python
from pywa import WhatsApp
from pywa.types import InlineButton

wa = WhatsApp(phone_id='100458559237541', token='xxxxxxxxxxxxxxx')
wa.send_message(
    to='9876543210',
    header='Hello from PyWa!',
    text='_Click on the buttons below_', # italic
    keyboard=[
        InlineButton(
            title='Menu',
            callback_data='menu'
        ),
        InlineButton(
            title='Help',
            callback_data='help'
        ),
        InlineButton(
            title='Contact us',
            callback_data='contact_us'
        )
    ],
    footer='Sent from PyWa'
)
```

#### Message with selection keyboard
- Selection keyboard is only available in text messages
- The keyboard is limited to 10 `SectionRow`s
```python
from pywa import WhatsApp
from pywa.types import SectionList, Section, SectionRow

wa = WhatsApp(phone_id='100458559237541', token='xxxxxxxxxxxxxxx')

wa.send_message(
    to='9876543210',
    header='*Welcome to GameBot!*', # bold
    text='_Here you can play games in WhatsApp_', # italic
    keyboard=SectionList(
       button_title='Select an game',
        sections=[
            Section(
                title='Card games',
                rows=[
                    SectionRow(
                        title='Blackjack',
                        callback_data='game:blackjack'
                    ),
                    SectionRow(
                        title='Poker',
                        callback_data='game:poker'
                    )
                ]
            ),
            Section(
                title='Board games',
                rows=[
                    SectionRow(
                        title='Chess',
                        callback_data='game:chess'
                    ),
                    SectionRow(
                        title='Checkers',
                        callback_data='game:checkers'
                    )
                ]
            )
        ]
    ),
    footer='Sent from PyWa'
)
```

#### Send image
```python
from pywa import WhatsApp

wa = WhatsApp(phone_id='100458559237541', token='xxxxxxxxxxxxxxx')
wa.send_image(
    to='9876543210',
    image='https://pbs.twimg.com/media/ErK-NWxXUAAI6TK.jpg',
    caption='```Sent from PyWa```'
)
```

#### Send video
```python
from pywa import WhatsApp

wa = WhatsApp(phone_id='100458559237541', token='xxxxxxxxxxxxxxx')
wa.send_video(
    to='9876543210',
    video='https://file-examples.com/storage/fefb234bc0648a3e7a1a47d/2017/04/file_example_MP4_480_1_5MG.mp4',
    caption='```Sent from PyWa```'
)
```

#### Send document
```python
from pywa import WhatsApp

wa = WhatsApp(phone_id='100458559237541', token='xxxxxxxxxxxxxxx')
wa.send_document(
    to='9876543210',
    document='https://www.africau.edu/images/default/sample.pdf',
    filename='sample.pdf',
)
```
#### Send audio
```python
from pywa import WhatsApp

wa = WhatsApp(phone_id='100458559237541', token='xxxxxxxxxxxxxxx')
wa.send_audio(
    to='9876543210',
    audio='https://file-examples-com.github.io/uploads/2017/11/file_example_MP3_700KB.mp3',
)
```

#### Sending location

```python
from pywa import WhatsApp

wa = WhatsApp(phone_id='100458559237541', token='xxxxxxxxxxxxxxx')
wa.send_location(
    to='9876543210',
    latitude=31.776796375930925,
    longitude=35.234690893383714,
    name='Western Wall',
    address='Jerusalem'
)
```

#### Sending contact

```python
from pywa import WhatsApp
from pywa.types import Contact as C

wa = WhatsApp(phone_id='100458559237541', token='xxxxxxxxxxxxxxx')
wa.send_contact(
    to='9876543210',
    contact=C(
        name=C.Name(
            first_name='John',
            last_name='Doe',
            formatted_name='John Doe'
        ),
        phones=[
            C.Phone(
                phone='+1234567890',
                wa_id='1234567890',
                type='MOBILE'
            )
        ],
        emails=[
            C.Email(
                email='john.doe@wa.com',
                type='WORK'
            )
        ],
        urls=[
            C.Url(
                url='https://wa.com',
                type='WORK'
            )
        ],
        addresses=[
            C.Address(
                street='1 Hacker Way',
                city='Menlo Park',
                state='CA',
                zip='94025',
                country='United States',
                type='WORK'
            )
        ],
        org=C.Org(
            company='Facebook',
            department='WhatsApp',
            title='Software Engineer'
        )
    )
)
```

#### React to messages

```python
from pywa import WhatsApp

wa = WhatsApp(phone_id='100458559237541', token='xxxxxxxxxxxxxxx')
wa.send_reaction(
    to='9876543210',
    message_id='wamid.XXX',
    emoji='👍'
)
wa.remove_reaction(
   to='9876543210',
   message_id='wamid.XXX',
)
```