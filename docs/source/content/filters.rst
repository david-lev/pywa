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
and separated by classes, for example, the :class:`TextFilter` filter will only handle text messages, while the
:class:`CallbackFilter` filter will only handle callbacks.

Here is an example of how to use them:

.. code-block:: python

    from pywa import WhatsApp
    from pywa.types import Message, CallbackButton, InlineButton
    from pywa.filters import TextFilter, CallbackFilter

    wa = WhatsApp(...)

    @wa.on_message(TextFilter.matches('hello', 'hi', ignore_case=True))
    def handle_hello(wa: WhatsApp, msg: Message):
        msg.reply(f'Hello {msg.from_user.name}!', keyboard=[InlineButton('Click me!', 'click')])

    @wa.on_callback(CallbackFilter.data_matches('click'))
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
    from pywa.filters import TextFilter, ImageFilter, VideoFilter

    fil.all_(TextFilter.startswith("Hello"), fil.any_(TextFilter.endswith("World"), TextFilter.length((1, 10))))
    fil.any_(ImageFilter(), fil.all_(VideoFilter.mimetypes("video/mp4"), VideoFilter.has_caption))
    fil.not_(TextFilter.contains("bad word"))


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

.. autoclass:: TextFilter
.. autoattribute:: TextFilter.any
.. automethod:: TextFilter.matches
.. automethod:: TextFilter.contains
.. automethod:: TextFilter.startswith
.. automethod:: TextFilter.endswith
.. automethod:: TextFilter.regex
.. automethod:: TextFilter.length
.. automethod:: TextFilter.is_command
.. automethod:: TextFilter.command

.. autoclass:: MediaFilter
.. autoattribute:: MediaFilter.any
.. automethod:: MediaFilter.mimetypes

.. autoclass:: ImageFilter
.. autoattribute:: ImageFilter.any
.. autoattribute:: ImageFilter.has_caption

.. autoclass:: VideoFilter
.. autoattribute:: VideoFilter.any
.. autoattribute:: VideoFilter.has_caption

.. autoclass:: AudioFilter
.. autoattribute:: AudioFilter.any
.. autoattribute:: AudioFilter.voice
.. autoattribute:: AudioFilter.audio

.. autoclass:: DocumentFilter
.. autoattribute:: DocumentFilter.any
.. autoattribute:: DocumentFilter.has_caption

.. autoclass:: StickerFilter
.. autoattribute:: StickerFilter.any
.. autoattribute:: StickerFilter.animated
.. autoattribute:: StickerFilter.static

.. autoclass:: ReactionFilter
.. autoattribute:: ReactionFilter.any
.. autoattribute:: ReactionFilter.added
.. autoattribute:: ReactionFilter.removed
.. automethod:: ReactionFilter.emojis

.. autoclass:: LocationFilter
.. autoattribute:: LocationFilter.any
.. automethod:: LocationFilter.in_radius

.. autoclass:: ContactsFilter
.. autoattribute:: ContactsFilter.any
.. autoattribute:: ContactsFilter.has_wa
.. automethod:: ContactsFilter.count
.. automethod:: ContactsFilter.phones

.. autoclass:: UnsupportedMsgFilter
.. autoattribute:: UnsupportedMsgFilter.any

----------------

Callback Filters
~~~~~~~~~~~~~~~~

.. autoclass:: CallbackFilter
.. autoattribute:: CallbackFilter.any
.. automethod:: CallbackFilter.data_matches
.. automethod:: CallbackFilter.data_contains
.. automethod:: CallbackFilter.data_startswith
.. automethod:: CallbackFilter.data_endswith
.. automethod:: CallbackFilter.data_regex

----------------

Message Status Filters
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: MessageStatusFilter
.. autoattribute:: MessageStatusFilter.sent
.. autoattribute:: MessageStatusFilter.delivered
.. autoattribute:: MessageStatusFilter.read
.. autoattribute:: MessageStatusFilter.failed
.. automethod:: MessageStatusFilter.failed_with

