💡 Examples
==============

.. note::

    WORK IN PROGRESS

Send a text message
-------------------

.. code-block:: python
    :caption: Text message
    :linenos:

    from pywa import WhatsApp

    wa = WhatsApp(phone_id='972123456789', token='xxxxx')

    recipient = '972987654321'
    wa.send_message(to=recipient, text='Hello world!')

    # Message with link preview
    wa.send_message(
        to=recipient,
        text='PyWa Documentation: https://pywa.readthedocs.io',
        preview_url=True
    )

Send a message with a media
---------------------------

.. code-block:: python
    :caption: Media message
    :linenos:

    from pywa import WhatsApp

    wa = WhatsApp(phone_id='972123456789', token='xxxxx')
    recipient = '972987654321'

    # - From URL
    wa.send_image(to=recipient, image='https://cdn.pixabay.com/photo/2014/10/01/10/44/animal-468228_1280.jpg')

    # - From local file
    wa.send_video(to=recipient, video='/path/to/video.mp4')

    # - From file id (You need to upload the media first with WhatsApp.upload_media to get the file id)
    wa.send_audio(to=recipient, audio='audio_file_id')

    # - From bytes
    content = requests.get('https://cdn.pixabay.com/photo/2014/10/01/10/44/animal-468228_1280.jpg').content
    wa.send_document(to=recipient, document=content)

Send a message with selection keyboard
--------------------------------------

- You can use selection keyboard only with text messages.
- The maximum number of section rows is 10.

.. sidebar:: 📱 ScreenShots

    .. tip:: How the message displayed in WhatsApp:

        .. image:: ../../_static/examples/selection-message.webp
            :alt: Selection message example
            :width: 90%

    .. tip:: How the keyboard displayed in WhatsApp:

        .. image:: ../../_static/examples/selection-keyboard.webp
            :alt: Selection keyboard example
            :width: 90%

.. code-block:: python
    :caption: Color selection message
    :linenos:

    from pywa import WhatsApp
    from pywa.types import SectionList, Section, SectionRow

    wa = WhatsApp(phone_id='972123456789', token='xxxxx')
    recipient = '972987654321'

    wa.send_message(
        to=recipient,
        header='Select your favorite color',
        text='Tap a button to select your favorite color:',
        footer='⚡ Powered by PyWa',
        buttons=SectionList(
            button_title='Colors',
            sections=[
                Section(
                    title='Popular Colors',
                    rows=[
                        SectionRow(
                            title='🟥 Red',
                            callback_data='color:red',
                            description='The color of blood',
                        ),
                        SectionRow(
                            title='🟩 Green',
                            callback_data='color:green',
                            description='The color of grass',
                        ),
                        SectionRow(
                            title='🟦 Blue',
                            callback_data='color:blue',
                            description='The color of the sky',
                        )
                    ],
                ),
                Section(
                    title='Other Colors',
                    rows=[
                        SectionRow(
                            title='🟧 Orange',
                            callback_data='color:orange',
                            description='The color of an orange',
                        ),
                        SectionRow(
                            title='🟪 Purple',
                            callback_data='color:purple',
                            description='The color of a grape',
                        ),
                        SectionRow(
                            title='🟨 Yellow',
                            callback_data='color:yellow',
                            description='The color of the sun',
                        )
                    ]
                )
            ]
        )
    )



Send a message with buttons keyboard
------------------------------------

- You can attach up to 3 buttons to a message.

.. sidebar:: 📱 ScreenShots

    .. tip:: How the message displayed in WhatsApp:

        .. image:: ../../_static/examples/buttons-message.webp
            :alt: Buttons message example
            :width: 90%


.. code-block:: python
    :caption: YouTube video info message
    :linenos:

    from pywa import WhatsApp
    from pywa.types import Button

    wa = WhatsApp(phone_id='972123456789', token='xxxxx')

    recipient = '972987654321'
    requested_vid_id = 'T9RRe4ZsSGw'

    wa.send_image(
        to=recipient,
        image=f'https://i.ytimg.com/vi/{requested_vid_id}/hqdefault.jpg',
        caption='Chandler Jokes | Friends • 2.9M views • 1 year ago',
        footer='⚡ Powered by PyWa',
        buttons=[
            Button(title='⬇️ Download', callback_data=f'dl:{requested_vid_id}'),
            Button(title='💬 Comments', callback_data=f'cmnts:{requested_vid_id}'),
            Button(title='🎬 Info', callback_data=f'info:{requested_vid_id}'),
        ]
    )
