🔬 Filters
============

.. currentmodule:: pywa.filters

- See all the `Helper filters`_.

Filters are used by the handlers to determine if they should handle an update or not.
You can create your own filters by providing a function that takes the client and the update and returns a boolean.
If the function returns True, the handler will handle the update, otherwise it will be ignored.

.. code-block:: python

    from pywa import WhatsApp
    from pywa.types import Message

    def my_filter(wa: WhatsApp, msg: Message) -> bool:
        return 'xyz' not in msg.text

    wa = WhatsApp(...)

    @wa.on_message(my_filter)
    def handle_only_messages_without_xyz(wa: WhatsApp, msg: Message):
        msg.reply('You said something without xyz!')

    # Or with lambda:
    @wa.on_message(lambda wa, msg: 'xyz' not in msg.text)
    def handle_only_messages_without_xyz(wa: WhatsApp, msg: Message):
        msg.reply('You said something without xyz!')


The library provides some built-in filters that you can use. The filters are located in the :mod:`pywa.filters` module
and separated by classes, for example, the :class:`text` filter will only handle text messages, while the
:class:`callback` filter will only handle callbacks.

Here is an example of how to use them:

.. code-block:: python

    from pywa import WhatsApp
    from pywa.types import Message, CallbackButton, InlineButton
    from pywa.filters import text, callback

    wa = WhatsApp(...)

    @wa.on_message(text.matches('hello', 'hi', ignore_case=True))
    def handle_hello(wa: WhatsApp, msg: Message):
        msg.reply(f'Hello {msg.from_user.name}!', keyboard=[InlineButton('Click me!', 'click')])

    @wa.on_callback(callback.data_matches('click'))
    def handle_click(wa: WhatsApp, clb: CallbackButton):
        clb.reply('You clicked me!')


----------------------------------------

Combining Filters
-----------------

If you need to combine (``&``, ``|``) or negate (``not``) filters, you can use the
:meth:`all_`, :meth:`any_` and :meth:`not_` functions.

Here is some examples:

.. code-block:: python

    from pywa import filters as fil  # short name for convenience

    fil.all_(fil.text.startswith("Hello"), fil.any_(fil.text.endswith("World"), fil.text.length((1, 10))))
    fil.any_(fil.image.any, fil.all_(fil.video.mimetypes("video/mp4"), fil.video.has_caption))
    fil.not_(fil.text.contains("bad word"))


Keep in mind that all match-filters (``matches``, ``startswith``, ``endswith``, ``contains`` etc.) returns True if
ANY of the given matches are found. so there is no need to use ``fil.any_`` with them.


----------------------------------------


Helper filters
~~~~~~~~~~~~~~

.. autofunction:: all_
.. autofunction:: any_
.. autofunction:: not_
.. autofunction:: from_users
.. autoattribute:: pywa.filters.forwarded
.. autoattribute:: pywa.filters.forwarded_many_times
.. autoattribute:: pywa.filters.reply

----------------

Message Filters
~~~~~~~~~~~~~~~

.. autoclass:: text
.. automethod:: text.matches
.. automethod:: text.contains
.. automethod:: text.startswith
.. automethod:: text.endswith
.. automethod:: text.regex
.. automethod:: text.length
.. automethod:: text.is_command
.. automethod:: text.command

.. autoclass:: media
.. automethod:: media.mimetypes

.. autoclass:: image
.. autoattribute:: image.has_caption

.. autoclass:: video
.. autoattribute:: video.has_caption

.. autoclass:: audio
.. autoattribute:: audio.voice
.. autoattribute:: audio.audio

.. autoclass:: document
.. autoattribute:: document.has_caption

.. autoclass:: sticker
.. autoattribute:: sticker.animated
.. autoattribute:: sticker.static

.. autoclass:: reaction
.. autoattribute:: reaction.added
.. autoattribute:: reaction.removed
.. automethod:: reaction.emojis

.. autoclass:: location
.. autoattribute:: location.current_location
.. automethod:: location.in_radius

.. autoclass:: contacts
.. autoattribute:: contacts.has_wa
.. automethod:: contacts.count
.. automethod:: contacts.phones

.. autoclass:: order
.. automethod:: order.price
.. automethod:: order.count
.. automethod:: order.has_product

.. autoclass:: unsupported

----------------

Callback Filters
~~~~~~~~~~~~~~~~

.. autoclass:: callback
.. automethod:: callback.data_matches
.. automethod:: callback.data_contains
.. automethod:: callback.data_startswith
.. automethod:: callback.data_endswith
.. automethod:: callback.data_regex

----------------

Message Status Filters
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: message_status
.. autoattribute:: message_status.sent
.. autoattribute:: message_status.delivered
.. autoattribute:: message_status.read
.. autoattribute:: message_status.failed
.. automethod:: message_status.failed_with

