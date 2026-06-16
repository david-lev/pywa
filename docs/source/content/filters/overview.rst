🔬 Filters
==========

.. currentmodule:: pywa.filters

Filters are conditions that decide whether an incoming update should be handled or ignored.
Pass them to any handler and pywa will only call your callback when the filter matches.

The library ships with a wide range of built-in filters in the :mod:`pywa.filters` module,
and you can write your own in a single function.

Basic Usage
-----------

.. code-block:: python
    :emphasize-lines: 5, 13

    from pywa import WhatsApp, types, filters

    wa = WhatsApp(...)

    @wa.on_message(filters.startswith("Hello", "Hi", ignore_case=True))
    def handle_hello(wa: WhatsApp, msg: types.Message):
        msg.react("👋")
        msg.reply(
            f"Hello {msg.from_user.name}!",
            buttons=[types.Button("Click me!", "click")]
        )

    @wa.on_callback_button(filters.matches("click"))
    def handle_click(wa: WhatsApp, clb: types.CallbackButton):
        clb.reply("You clicked me!")

Combining Filters
-----------------

Filters can be combined with logical operators:

- ``&`` → **and**
- ``|`` → **or**
- ``~`` → **not**

.. code-block:: python

    from pywa import filters

    # image with caption
    filters.image & filters.has_caption

    # text or image
    filters.text | filters.image

    # message must not contain "bad word"
    ~filters.contains("bad word")

.. tip::

   All match-filters (:meth:`matches`, :meth:`contains` etc.) return ``True`` if **any** of the given options match.
   So instead of writing:

   .. code-block:: python

        filters.matches("hello") | filters.matches("hi")

   You can simply write:

   .. code-block:: python

        filters.matches("hello", "hi")

Custom Filters
--------------

Write a function that accepts the client and the update, and returns a boolean.
``True`` means the handler runs; ``False`` means the update is skipped.

.. note::

   - Custom filters must be wrapped with :func:`pywa.filters.new`.
   - You can combine custom and built-in filters using logical operators.
   - Async functions can be used as filters **only** with the async client.

.. code-block:: python
    :emphasize-lines: 3-4, 8, 13

    from pywa import WhatsApp, types, filters

    def without_xyz_filter(_: WhatsApp, msg: types.Message) -> bool:
        return msg.text and "xyz" not in msg.text

    wa = WhatsApp(...)

    @wa.on_message(filters.new(without_xyz_filter))
    def messages_without_xyz(wa: WhatsApp, msg: types.Message):
        msg.reply("You said something without xyz!")

    # Or inline with a lambda — combine with built-in filters:
    @wa.on_message(filters.text & filters.new(lambda _, msg: "xyz" not in msg.text))
    def messages_without_xyz(wa: WhatsApp, msg: types.Message):
        msg.reply("You said something without xyz!")

Built-in Filters
----------------

.. toctree::

    ./common_filters
    ./message_filters
    ./message_status_filters
    ./account_update_filters
    ./calls_filters
