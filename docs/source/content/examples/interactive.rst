📲 Sending Interactive Messages
===============================

Interactive messages let you present structured options to your users — such as selection lists or quick-reply buttons — instead of relying on them to type plain text.

.. note::

   These examples focus on **sending** interactive messages. To learn how to listen for and process the user's choice when they tap a button or select an option, check out the `Handlers Overview <../handlers/overview.html>`_ and `Filters Overview <../filters/overview.html>`_ guides.

Send a message with selection keyboard
--------------------------------------

- You can use selection keyboards only with text messages.
- The maximum number of section rows is 10.


.. code-block:: python
    :caption: Color selection message
    :linenos:

    from pywa import WhatsApp, types

    wa = WhatsApp(phone_id='972123456789', token='xxxxx')
    recipient = '972987654321'

    wa.send_message(
        to=recipient,
        header='Select your favorite color',
        text='Tap a button to select your favorite color:',
        footer='⚡ Powered by PyWa',
        buttons=types.SectionList(
            button_title='Colors',
            sections=[
                types.Section(
                    title='Popular Colors',
                    rows=[
                        types.SectionRow(
                            title='🟥 Red',
                            callback_data='color:red',
                            description='The color of blood',
                        ),
                        types.SectionRow(
                            title='🟩 Green',
                            callback_data='color:green',
                            description='The color of grass',
                        ),
                        types.SectionRow(
                            title='🟦 Blue',
                            callback_data='color:blue',
                            description='The color of the sky',
                        )
                    ],
                ),
                types.Section(
                    title='Other Colors',
                    rows=[
                        types.SectionRow(
                            title='🟧 Orange',
                            callback_data='color:orange',
                            description='The color of an orange',
                        ),
                        types.SectionRow(
                            title='🟪 Purple',
                            callback_data='color:purple',
                            description='The color of a grape',
                        ),
                        types.SectionRow(
                            title='🟨 Yellow',
                            callback_data='color:yellow',
                            description='The color of the sun',
                        )
                    ]
                )
            ]
        )
    )

**How it looks on WhatsApp:**

.. list-table::
   :widths: 50 50
   :align: center

   * - .. figure:: ../../../../_static/examples/selection-message.webp
          :alt: Selection message example
          :align: center
          :width: 90%

          *Interactive message view*
     - .. figure:: ../../../../_static/examples/selection-keyboard.webp
          :alt: Selection keyboard example
          :align: center
          :width: 90%

          *Selection menu view*

Send a message with buttons keyboard
------------------------------------

- You can attach up to 3 buttons to a message.

.. code-block:: python
    :caption: YouTube video info message
    :linenos:

    from pywa import WhatsApp, types

    wa = WhatsApp(phone_id='972123456789', token='xxxxx')

    recipient = '972987654321'
    requested_vid_id = 'T9RRe4ZsSGw'

    wa.send_image(
        to=recipient,
        image=f'https://i.ytimg.com/vi/{requested_vid_id}/hqdefault.jpg',
        caption='Chandler Jokes | Friends • 2.9M views • 1 year ago',
        footer='⚡ Powered by PyWa',
        buttons=[
            types.Button(title='⬇️ Download', callback_data=f'dl:{requested_vid_id}'),
            types.Button(title='💬 Comments', callback_data=f'cmnts:{requested_vid_id}'),
            types.Button(title='🎬 Info', callback_data=f'info:{requested_vid_id}'),
        ]
    )

**How it looks on WhatsApp:**

.. figure:: ../../../../_static/examples/buttons-message.webp
    :alt: Buttons message example
    :align: center
    :width: 60%

    *Interactive buttons view*
