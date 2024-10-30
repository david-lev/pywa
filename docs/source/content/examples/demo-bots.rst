🤖 Demo Bots
============

This page contains some examples of bots you can create using pywa.
Every example is a complete working bot that you can run on your own server.

👋 Hello Bot
--------------

This is a simple bot that welcomes the user when they send a message.

.. code-block:: python
    :linenos:

    import flask  # pip3 install flask
    from pywa import WhatsApp, types

    flask_app = flask.Flask(__name__)

    wa = WhatsApp(
        phone_id='your_phone_number',
        token='your_token',
        server=flask_app,
        verify_token='xyzxyz',
    )

    @wa.on_message
    def hello(_: WhatsApp, msg: types.Message):
        msg.react('👋')
        msg.reply(f'Hello {msg.from_user.name}!')

    # Run the server
    flask_app.run()


📝 Echo Bot
-----------

This is a simple bot that echoes back the user's message.


.. code-block:: python
    :linenos:

    import flask  # pip3 install flask
    from pywa import WhatsApp, types

    flask_app = flask.Flask(__name__)

    wa = WhatsApp(
        phone_id='your_phone_number',
        token='your_token',
        server=flask_app,
        verify_token='xyzxyz',
    )

    @wa.on_message
    def echo(_: WhatsApp, msg: types.Message):
        try:
            msg.copy(to=msg.sender, reply_to_message_id=msg.message_id_to_reply)
        except ValueError:
            msg.reply_text("I can't echo this message")

    # Run the server
    flask_app.run()



⬆️ Url Uploader Bot
--------------------

This is a simple bot that uploads files from URLs.

.. code-block:: python
    :linenos:

    import flask  # pip3 install flask
    from pywa import WhatsApp, types, filters, errors
    from pywa.types import Message, MessageStatus

    flask_app = flask.Flask(__name__)

    wa = WhatsApp(
        phone_id='your_phone_number',
        token='your_token',
        server=flask_app,
        verify_token='xyzxyz',
    )

    @wa.on_message(filters.startswith('http'))
    def download(_: WhatsApp, msg: types.Message):
        msg.reply_document(msg.text, filename=msg.text.split('/')[-1])

    # When a file fails to download/upload, the bot will reply with an error message.
    @wa.on_message_status(filters.failed_with(errors.MediaDownloadError, errors.MediaUploadError))
    def on_media_download_error(_: WhatsApp, status: types.MessageStatus):
        status.reply_text(f"I can't download/upload this file: {status.error.details}")

    # Run the server
    flask_app.run()


🔢 Calculator WhatsApp Bot
---------------------------

This is a simple calculator bot for WhatsApp. It can perform basic arithmetic operations on integers.

Usage:

>>> 1 + 2
>>> 1 - 2
>>> 1 * 2
>>> 1 / 2

.. code-block:: python

    import re
    import flask  # pip3 install flask
    from pywa import WhatsApp, types, filters

    flask_app = flask.Flask(__name__)

    wa = WhatsApp(
        phone_id='your_phone_number',
        token='your_token',
        server=flask_app,
        verify_token='xyzxyz',
    )

    pattern = re.compile(r'^(\d+)\s*([+*/-])\s*(\d+)$')

    @wa.on_message(filters.regex(pattern))
    def calculator(_: WhatsApp, msg: types.Message):
        a, op, b = re.match(pattern, msg.text).groups()
        a, b = int(a), int(b)
        match op:
            case '+':
                result = a + b
            case '-':
                result = a - b
            case '*':
                result = a * b
            case '/':
                try:
                    result = a / b
                except ZeroDivisionError:
                    msg.react('❌')
                    msg.reply('Division by zero is not allowed')
                    return
            case _:
                msg.react('❌')
                msg.reply('Unknown operator')
                return
        msg.reply(f'{a} {op} {b} = *{result}*')

    # Run the server
    flask_app.run()


🌐 Translator Bot
-----------------

A simple WhatsApp bot that translates text messages to other languages.

.. code-block:: python
    :linenos:

    import logging
    import flask  # pip3 install flask
    import googletrans  # pip3 install googletrans==4.0.0-rc1
    from pywa import WhatsApp, types, filters

    flask_app = flask.Flask(__name__)
    translator = googletrans.Translator()

    wa = WhatsApp(
        phone_id='your_phone_number',
        token='your_token',
        server=flask_app,
        verify_token='xyzxyz',
    )

    MESSAGE_ID_TO_TEXT: dict[str, str] = {}  # msg_id -> text
    POPULAR_LANGUAGES = {
        "en": ("English", "🇺🇸"),
        "es": ("Español", "🇪🇸"),
        "fr": ("Français", "🇫🇷")
    }
    OTHER_LANGUAGES = {
        "iw": ("עברית", "🇮🇱"),
        "ar": ("العربية", "🇸🇦"),
        "ru": ("Русский", "🇷🇺"),
        "de": ("Deutsch", "🇩🇪"),
        "it": ("Italiano", "🇮🇹"),
        "pt": ("Português", "🇵🇹"),
        "ja": ("日本語", "🇯🇵"),
    }


    @wa.on_message(filters.text)
    def offer_translation(_: WhatsApp, msg: types.Message):
        msg_id = msg.reply_text(
            text='Choose language to translate to:',
            buttons=types.SectionList(
                button_title='🌐 Choose Language',
                sections=[
                    types.Section(
                        title="🌟 Popular languages",
                        rows=[
                            types.SectionRow(
                                title=f"{flag} {name}",
                                callback_data=f"translate:{code}",
                            )
                            for code, (name, flag) in POPULAR_LANGUAGES.items()
                        ],
                    ),
                    types.Section(
                        title="🌐 Other languages",
                        rows=[
                            types.SectionRow(
                                title=f"{flag} {name}",
                                callback_data=f"translate:{code}",
                            )
                            for code, (name, flag) in OTHER_LANGUAGES.items()
                        ],
                    ),
                ]
            )
        )
        # Save the message ID so we can use it later to get the original text.
        MESSAGE_ID_TO_TEXT[msg_id] = msg.text

    @wa.on_callback_selection(filters.startswith('translate:'))
    def translate(_: WhatsApp, sel: types.CallbackSelection):
        lang_code = sel.data.split(':')[-1]
        try:
            # every CallbackSelection has a reference to the original message (the selection's message)
            original_text = MESSAGE_ID_TO_TEXT[sel.reply_to_message.message_id]
        except KeyError:  # If the bot was restarted, the message ID is no longer valid.
            sel.react('❌')
            sel.reply_text(
                text='Original message not found. Please send a new message.'
            )
            return
        try:
            translated = translator.translate(original_text, dest=lang_code)
        except Exception as e:
            sel.react('❌')
            sel.reply_text(
                text='An error occurred. Please try again.'
            )
            logging.exception(e)
            return

        sel.reply_text(
            text=f"Translated to {translated.dest}:\n{translated.text}"
        )


    # Run the server
    flask_app.run()


🖼 Random image bot
-------------------

This example shows how to create a simple bot that replies with a random image from Unsplash.


.. code-block:: python
    :linenos:

    import requests
    import flask
    from pywa import WhatsApp, types

    flask_app = flask.Flask(__name__)

    wa = WhatsApp(
        phone_id='your_phone_number',
        token='your_token',
        server=flask_app,
        verify_token='xyzxyz',
    )

    @wa.on_message
    def send_random_image(_: WhatsApp, msg: types.Message):
        msg.reply_image(
            image='https://source.unsplash.com/random',
            caption='🔄 Random image',
            buttons=types.ButtonUrl(title='Unsplash', url='https://unsplash.com')
        )

    # Run the server
    flask_app.run()


📸 Remove background from image
--------------------------------

This example shows how to create a bot that removes the background from an image using the remove.bg API.

.. code-block:: python
    :linenos:

    import requests
    import flask
    from pywa import WhatsApp, types

    flask_app = flask.Flask(__name__)

    wa = WhatsApp(
        phone_id='your_phone_number',
        token='your_token',
        server=flask_app,
        verify_token='xyzxyz',
    )

    REMOVEBG_API_KEY = "your_api_key"  # https://www.remove.bg/api


    def get_removed_bg_image(original_img: bytes) -> bytes:
        url = "https://api.remove.bg/v1.0/removebg"
        files = {'image_file': original_img}
        data = {'size': 'auto'}
        headers = {'X-Api-Key': REMOVEBG_API_KEY}
        response = requests.post(url, files=files, data=data, headers=headers)
        response.raise_for_status()
        return response.content


    @wa.on_message(filters.image)
    def on_image(_: WhatsApp, msg: types.Message):
        try:
            original_img = msg.image.download(in_memory=True)
            image = get_removed_bg_image(original_img)
        except requests.HTTPError as e:
            msg.reply_text(f"A error occurred")
            logging.exception(e)
            return
        msg.reply_image(
            image=image,
            caption="Here you go",
            mime_type='image/png',  # when sending bytes, you must specify the mime type
        )

    # Run the server
    flask_app.run()
