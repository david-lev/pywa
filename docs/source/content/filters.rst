🔬 Filters
============

.. currentmodule:: pywa.filters

- See all the `Built-in Filters`_.

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

    @wa.on_message(TextFilter.match('hello', 'hi', ignore_case=True))
    def handle_hello(wa: WhatsApp, msg: Message):
        msg.reply(f'Hello {msg.from_user.name}!', keyboard=[InlineButton('Click me!', 'click')])

    @wa.on_callback(CallbackFilter.data_match('click'))
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
    fil.any_(ImageFilter.ANY, fil.all_(VideoFilter.mimetype("video/mp4"), VideoFilter.HAS_CAPTION))
    fil.not_(TextFilter.contains("bad word"))


Keep in mind that all match-filters (``match``, ``startswith``, ``endswith``, ``contains`` etc.) returns True if
any of the given matches are found. so there is no need to use ``FC.any`` with them.

----------------------------------------


Helper functions
~~~~~~~~~~~~~~~~


.. autodata:: FORWARDED
.. autofunction:: all_
.. autofunction:: any_
.. autofunction:: not_
.. autofunction:: from_user

----------------------------------------

Built-in Filters
----------------

----------------

Message Filters
~~~~~~~~~~~~~~~

.. autoclass:: TextFilter
.. autoattribute:: TextFilter.ANY
.. automethod:: TextFilter.match
.. automethod:: TextFilter.contain
.. automethod:: TextFilter.startswith
.. automethod:: TextFilter.endswith
.. automethod:: TextFilter.regex
.. automethod:: TextFilter.length
.. automethod:: TextFilter.command

.. autoclass:: ImageFilter
.. autoattribute:: ImageFilter.ANY
.. autoattribute:: ImageFilter.HAS_CAPTION
.. automethod:: ImageFilter.mimetype

.. autoclass:: VideoFilter
.. autoattribute:: VideoFilter.ANY
.. autoattribute:: VideoFilter.HAS_CAPTION
.. automethod:: VideoFilter.mimetype

.. autoclass:: AudioFilter
.. autoattribute:: AudioFilter.ANY
.. autoattribute:: AudioFilter.VOICE
.. autoattribute:: AudioFilter.AUDIO

.. autoclass:: DocumentFilter
.. autoattribute:: DocumentFilter.ANY
.. autoattribute:: DocumentFilter.HAS_CAPTION
.. automethod:: DocumentFilter.mimetype

.. autoclass:: StickerFilter
.. autoattribute:: StickerFilter.ANY
.. autoattribute:: StickerFilter.ANIMATED
.. autoattribute:: StickerFilter.STATIC

.. autoclass:: ReactionFilter
.. autoattribute:: ReactionFilter.ANY
.. autoattribute:: ReactionFilter.ADDED
.. autoattribute:: ReactionFilter.REMOVED
.. automethod:: ReactionFilter.emoji

.. autoclass:: LocationFilter
.. autoattribute:: LocationFilter.ANY
.. automethod:: LocationFilter.in_radius

.. autoclass:: ContactsFilter
.. autoattribute:: ContactsFilter.ANY
.. autoattribute:: ContactsFilter.HAS_WA
.. automethod:: ContactsFilter.count
.. automethod:: ContactsFilter.phone


.. autoclass:: UnsupportedMsgFilter
.. autoattribute:: UnsupportedMsgFilter.ANY

----------------

Callback Filters
~~~~~~~~~~~~~~~~

.. autoclass:: CallbackFilter
.. autoattribute:: CallbackFilter.ANY
.. automethod:: CallbackFilter.data_match
.. automethod:: CallbackFilter.data_contain
.. automethod:: CallbackFilter.data_startswith
.. automethod:: CallbackFilter.data_endswith
.. automethod:: CallbackFilter.data_regex

----------------

Message Status Filters
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: MessageStatusFilter
.. autoattribute:: MessageStatusFilter.SENT
.. autoattribute:: MessageStatusFilter.DELIVERED
.. autoattribute:: MessageStatusFilter.READ
.. autoattribute:: MessageStatusFilter.FAILED
.. automethod:: MessageStatusFilter.failed_with_error_code
.. automethod:: MessageStatusFilter.failed_with_exception

