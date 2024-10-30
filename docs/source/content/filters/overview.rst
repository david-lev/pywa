🔬 Filters
============

.. currentmodule:: pywa.filters

Filters are used by the handlers to determine if they should handle an update or not.

The library provides some built-in filters that you can use. The filters are located in the :mod:`pywa.filters` module.

Here is an example of how to use them:

.. code-block:: python
    :emphasize-lines: 5, 10

    from pywa import WhatsApp, types, filters

    wa = WhatsApp(...)

    @wa.on_message(filters.startswith('Hello', 'Hi', ignore_case=True))
    def handle_hello(wa: WhatsApp, msg: types.Message):
        msg.react('👋')
        msg.reply(f'Hello {msg.from_user.name}!', buttons=[types.Button('Click me!', 'click')])

    @wa.on_callback(filters.matches('click'))
    def handle_click(wa: WhatsApp, clb: types.CallbackButton):
        clb.reply('You clicked me!')


----------------------------------------

Combining Filters
-----------------

You can combine filters with logical operators:

- ``&``: and
- ``|``: or
- ``~``: not


Here is some examples:

.. code-block:: python

    from pywa import filters

    # image with caption
    filters.image & filters.has_caption

    # text or image
    filters.text | filters.image

    # message must not contain "bad word"
    ~filters.contains("bad word")


.. role:: python(code)
   :language: python

.. tip::

    Keep in mind that all match-filters (:meth:`matches`, :meth:`contains`, etc) will return ``True`` if
    **ANY** of the given matches are found. so there is no need to do something like
    :python:`filters.matches('hello') | filters.matches('hi')`, you can just do :python:`filters.matches('hello', 'hi')`.

----------------------------------------

Custom Filters
-----------------

You can create your own filters by providing a function that takes the client and the update and returns a boolean.
If the function returns True, the handler will handle the update, otherwise it will be ignored.

.. note::
    - The custom filter function should be wrapped with :func:`pywa.filters.new` to be used as a filter.
    - You can combine built-in filters with custom filters using logical operators.
    - You can use async functions as filters only if you using the async client.

.. code-block:: python
    :emphasize-lines: 3-4, 8, 13

    from pywa import WhatsApp, types, filters

    def without_xyz_filter(_: WhatsApp, msg: types.Message) -> bool:
        return msg.text and 'xyz' not in msg.text

    wa = WhatsApp(...)

    @wa.on_message(filters.new(without_xyz_filter))
    def messages_without_xyz(wa: WhatsApp, msg: Message):
        msg.reply('You said something without xyz!')

    # Or with lambda:
    @wa.on_message(filters.new(lambda _, msg: msg.text and 'xyz' not in msg.text))
    def messages_without_xyz(wa: WhatsApp, msg: Message):
        msg.reply('You said something without xyz!')

----------------------------------------


Built-in Filters
-----------------

.. toctree::

    ./common_filters
    ./message_filters
    ./message_status_filters
