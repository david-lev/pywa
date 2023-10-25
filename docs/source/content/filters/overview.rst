🔬 Filters
============

.. currentmodule:: pywa.filters

Filters are used by the handlers to determine if they should handle an update or not.
You can create your own filters by providing a function that takes the client and the update and returns a boolean.
If the function returns True, the handler will handle the update, otherwise it will be ignored.

.. code-block:: python

    from pywa import WhatsApp
    from pywa.types import Message

    def without_xyz_filter(_: WhatsApp, msg: Message) -> bool:
        return msg.text and 'xyz' not in msg.text

    wa = WhatsApp(...)

    @wa.on_message(without_xyz_filter)
    def messages_without_xyz(wa: WhatsApp, msg: Message):
        msg.reply('You said something without xyz!')

    # Or with lambda:
    @wa.on_message(lambda _, msg: msg.text and 'xyz' not in msg.text)
    def messages_without_xyz(wa: WhatsApp, msg: Message):
        msg.reply('You said something without xyz!')


The library provides some built-in filters that you can use. The filters are located in the :mod:`pywa.filters` module.

Here is an example of how to use them:

.. code-block:: python

    from pywa import WhatsApp
    from pywa.types import Message, CallbackButton, Button
    from pywa.filters import text, callback

    wa = WhatsApp(...)

    @wa.on_message(text.matches('hello', 'hi', ignore_case=True))
    def handle_hello(wa: WhatsApp, msg: Message):
        msg.reply(f'Hello {msg.from_user.name}!', buttons=[Button('Click me!', 'click')])

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
    fil.any_(fil.image, fil.all_(fil.video.mimetypes("video/mp4"), fil.video.has_caption))
    fil.not_(fil.text.contains("bad word"))


.. role:: python(code)
   :language: python

.. tip::
    :class: dropdown

    Keep in mind that all match-filters (:meth:`text.matches`, :meth:`text.contains`, etc) will return ``True`` if
    **ANY** of the given matches are found. so there is no need to do something like
    :python:`any_(text.matches('hello'), text.matches('hi'))`, you can just do :python:`text.matches('hello', 'hi')`.

----------------------------------------


Built-in Filters
-----------------

.. toctree::

    ./common_filters
    ./message_filters
    ./callback_filters
    ./message_status_filters
    ./template_status_filters
