🌐 Translator Bot
==================

A simple WhatsApp bot that translates text messages to other languages.


1. Initialize the client:

.. code-block:: python
    :linenos:

    from pywa import WhatsApp
    from flask import Flask  # pip3 install flask

    flask_app = Flask(__name__)

    wa = WhatsApp(
        phone_number='your_phone_number',
        token='your_token',
        server=flask_app,
        verify_token='xyzxyz',
    )


2. Register a handler for incoming text messages:

.. code-block:: python
    :linenos:

    import logging
    import googletrans  # pip3 install googletrans==4.0.0-rc1
    from pywa import WhatsApp, filters
    from pywa.types import Message, SectionList, CallbackSelection, Section, SectionRow

    translator = googletrans.Translator()

    MESSAGES_IDS_TO_TEXT: dict[str, str] = {}  # msg_id -> text
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
    def offer_translation(_: WhatsApp, msg: Message):
        """Offer to translate the text to another language."""
        msg_id = msg.reply_text(
            text='Choose language to translate to:',
            buttons=SectionList(
                button_title='🌐 Choose Language',
                sections=[
                    Section(
                        title="🌟 Popular languages",
                        rows=[
                            SectionRow(
                                title=f"{flag} {name}",
                                callback_data=f"translate:{code}",
                            )
                            for code, (name, flag) in POPULAR_LANGUAGES.items()
                        ],
                    ),
                    Section(
                        title="🌐 Other languages",
                        rows=[
                            SectionRow(
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
        MESSAGES_IDS_TO_TEXT[msg_id] = msg.text

3. Register a handler for language selection:

.. code-block:: python
    :linenos:

    @wa.on_callback_selection(filters.callback.data_startswith('translate:'))
    def translate(_: WhatsApp, sel: CallbackSelection):
        lang_code = sel.data.split(':')[-1]
        try:
            # every CallbackSelection has a reference to the original message (the selection's message)
            original_text = MESSAGES_IDS_TO_TEXT[sel.reply_to_message.message_id]
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



4. Run the server:

.. code-block:: python
    :linenos:

    flask_app.run()
