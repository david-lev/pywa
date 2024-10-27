📥 Listeners
==================

When handling updates, most of the time you ask the user for input (e.g. a reply, text, button press, etc.). This is where listeners come in.
With listeners, you can create an `inline` handler that waits for a specific user input and returns the result.

Listen
______

Let's see an example of how to use a listener:

.. code-block:: python
    :linenos:
    :emphasize-lines: 8-11

    from pywa import WhatsApp, types, filters

    wa = WhatsApp(...)

    @wa.on_message(filters.command("start"))
    def start(client: WhatsApp, msg: types.Message):
        msg.reply("Hello! How old are you?")
        age: types.Message = client.listen( # Now we want to wait for the user to send their age
            to=msg.sender,
            filters=filters.text
        )
        msg.reply(f"Your age is {age.text}.")

In the example above, we are waiting for the user to send their age. The `client.listen` method will wait for the user to send a message that matches the filter :attr:`pywa.filters.text`.

Cancel
______

Now, listeners have a few options that you can use to customize the behavior. for example, you can set a timeout for the listener, or cancel the listener if the user sends a specific message. let's see an example:

.. code-block:: python
    :linenos:
    :emphasize-lines: 9, 16

    from pywa import WhatsApp, types, filters

    wa = WhatsApp(...)

    @wa.on_message(filters.command("start"))
    def start(client: WhatsApp, msg: types.Message):
        msg.reply(
            text="Hello! How old are you?",
            buttons=[types.Button("Cancel", callback_data="cancel")]
        )
        age = client.listen(
            to=msg.sender,
            filters=filters.text,
            timeout=20, # 20 seconds
            # If the user presses "cancel" the listener will be canceled
            cancelers=filters.callback_button & filters.matches("cancel")
        )
        msg.reply(f"Your age is {age.text}.")

In the example above, we added a button to the message that the user can press to cancel the listener. The listener will be canceled if the user sends a message that matches the filter ``filters.callback_button & filters.matches("cancel")``.

Now - we actually need to know what happend with the listener. The :meth:`~pywa.client.WhatsApp.listen` uses exceptions to notify you about the listener status. Let's see an example:

Try-Except
__________

.. code-block:: python
    :linenos:
    :emphasize-lines: 9, 17, 19

    from pywa import WhatsApp, types, filters, listeners

    wa = WhatsApp(...)

    @wa.on_message(filters.command("start"))
    def start(client: WhatsApp, msg: types.Message):
        msg.reply("Hello! Please send me your age.", buttons=[types.Button("Cancel", callback_data="cancel")])

        try:
            age = client.listen(
                to=msg.sender,
                filters=filters.text,
                cancelers=filters.callback_button & filters.matches("cancel"),
                timeout=20
            )
            msg.reply(f"Your age is {age.text}.")
        except ListenerTimeout:
            msg.reply("You took too long to send your age.")
        except ListenerCanceled:
            msg.reply("You canceled the operation.")

In the example above, we added a try-except block to handle the listener exceptions. If the listener times out, the :class:`~pywa.listeners.ListenerTimeout` exception will be raised. If the listener is canceled, the :class:`~pywa.listeners.ListenerCanceled` exception will be raised.

Shortcuts
_________

PyWa also provides a few shortcuts to create listeners when sending messages. Let's see an example:

.. code-block:: python
    :linenos:
    :emphasize-lines: 7

    from pywa import WhatsApp, types, filters

    wa = WhatsApp(...)

    @wa.on_message(filters.command("start"))
    def start(client: WhatsApp, msg: types.Message):
        age: types.Message = m.reply("Hello! How old are you?").wait_for_reply(filters.text)
        m.reply(f"You are {age.text} years old")

In the example above, we used the :meth:`~pywa.types.sent_message.SentMessage.wait_for_reply` method to create a listener that waits for a text reply from the user.

.. code-block:: python
    :linenos:
    :emphasize-lines: 7

    from pywa import WhatsApp, types, filters

    wa = WhatsApp(...)

    @wa.on_message(filters.command("start"))
    def start(client: WhatsApp, msg: types.Message):
        msg.reply(f"Hello {msg.from_user.name}!").wait_until_delivered()
        msg.reply("How can I help you?")

In the example above, we used the :meth:`~pywa.types.sent_message.SentMessage.wait_until_delivered` method to create a listener that waits until the message is delivered to the user.

Other shortcuts are available, such as :meth:`~pywa.types.sent_message.SentMessage.wait_for_click`, :meth:`~pywa.types.sent_message.SentMessage.wait_for_selection`, :meth:`~pywa.types.sent_message.SentMessage.wait_until_read`, and more.

.. currentmodule:: pywa.client

.. automethod:: WhatsApp.listen
    :noindex:
.. automethod:: WhatsApp.stop_listening
    :noindex:

.. currentmodule:: pywa.types.sent_message

.. automethod:: SentMessage.wait_for_reply
.. automethod:: SentMessage.wait_for_click
.. automethod:: SentMessage.wait_for_selection
.. automethod:: SentMessage.wait_until_read
.. automethod:: SentMessage.wait_until_delivered
