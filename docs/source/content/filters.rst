Filters
=======

.. currentmodule:: pywa.filters

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

Built-in Filters
----------------

.. autoclass:: TextFilter
    :members:

.. autoclass:: ImageFilter
    :members:

.. autoclass:: VideoFilter
    :members:

.. autoclass:: AudioFilter
    :members:

.. autoclass:: DocumentFilter
    :members:

.. autoclass:: StickerFilter
    :members:

.. autoclass:: ReactionFilter
    :members:

.. autoclass:: UnsupportedMsgFilter
    :members:

.. autoclass:: LocationFilter
    :members:

.. autoclass:: ContactsFilter
    :members:

.. autoclass:: CallbackFilter
    :members:

.. autoclass:: MessageStatusFilter
    :members:

