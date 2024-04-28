🔬 Filters
============

.. currentmodule:: pywa.filters

Filters are used by the handlers to determine if they should handle an update or not.

The library provides some built-in filters that you can use. The filters are located in the :mod:`pywa.filters` module.

Here is an example of how to use them:

.. code-block:: python
    :emphasize-lines: 3, 7, 12

    from pywa import WhatsApp
    from pywa.types import Message, CallbackButton, Button
    from pywa import filters as fil

    wa = WhatsApp(...)

    @wa.on_message(fil.startswith('Hello', 'Hi', ignore_case=True))
    def handle_hello(wa: WhatsApp, msg: Message):
        msg.react('👋')
        msg.reply(f'Hello {msg.from_user.name}!', buttons=[Button('Click me!', 'click')])

    @wa.on_callback(fil.matches('click'))
    def handle_click(wa: WhatsApp, clb: CallbackButton):
        clb.reply('You clicked me!')


----------------------------------------

Combining Filters
-----------------

As default, all filters are combined with ``&`` (and) operator. So if you provide multiple filters, all of them must
return ``True`` for the handler to handle the update.

If you need to combine (``&``, ``|``) or negate (``not``) filters, you can use the
:meth:`all_`, :meth:`any_` and :meth:`not_` functions.

Here is some examples:

.. code-block:: python

    from pywa import filters as fil  # short name for convenience

    # message text must start with "Hello" and (end with "World" or have a length between 1 and 10)
    fil.all_(fil.startswith("Hello"), fil.any_(fil.endswith("World"), fil.text.length((1, 10))))

    # message must be a photo or a (video of type "video/mp4" and have a caption)
    fil.any_(fil.image, fil.all_(fil.video.mimetypes("video/mp4"), fil.video.has_caption))

    # message must not contain "bad word"
    fil.not_(fil.contains("bad word"))


.. role:: python(code)
   :language: python

.. tip::
    :class: dropdown

    Keep in mind that all match-filters (:meth:`matches`, :meth:`contains`, etc) will return ``True`` if
    **ANY** of the given matches are found. so there is no need to do something like
    :python:`any_(matches('hello'), matches('hi'))`, you can just do :python:`matches('hello', 'hi')`.

----------------------------------------

Custom Filters
-----------------

You can create your own filters by providing a function that takes the client and the update and returns a boolean.
If the function returns True, the handler will handle the update, otherwise it will be ignored.

.. code-block:: python
    :emphasize-lines: 4, 9, 14

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

----------------------------------------


Built-in Filters
-----------------

.. toctree::

    ./common_filters
    ./message_filters
    ./callback_filters
    ./message_status_filters
    ./template_status_filters
