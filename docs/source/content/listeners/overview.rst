📥 Listeners
==================

.. currentmodule:: pywa.types.sent_update

When handling updates, most of the time you ask the user for input (e.g. a reply, text, button press, etc.). This is where listeners come in.
With listeners, you can create an `inline` handler that waits for a specific user input and returns the result.


Listening
_________

In this example, we will create a listener that waits for the user to send their age. The listener will wait for a text-digit message from the user and then reply with a message based on the age provided.

.. code-block:: python
    :linenos:
    :emphasize-lines: 8-10

    from pywa import WhatsApp, types, filters

    wa = WhatsApp(...)

    @wa.on_message(filters.command("start"))
    def start(client: WhatsApp, msg: types.Message):
        sent = msg.reply("Hello! How old are you?")
        age_reply: Message = sent.wait_for_reply(
            filters=filters.text & filters.new(lambda _, m: m.text.isdigit())
        )
        age = int(age_reply.text)
        if age < 18:
            age_reply.reply("You are too young to use this service.")
            # Handle the case when the user is too young
        else:
            age_reply.reply("Welcome! You can now use the service.")
            # Handle the case when the user is old enough

.. role:: python(code)
   :language: python

In the example above, we storing the sent message in the variable ``sent``. Then, we used the :meth:`~SentMessage.wait_for_reply` method to create a listener that waits for a reply from the user. The listener will wait for a message that matches the filter :python:`filters.text & filters.new(lambda _, m: m.text.isdigit())`, which means it will wait for a text message that contains only digits.
When the user sends a message that matches the filter, the listener will return the message as a :class:`~pywa.types.Message` object, which we store in the variable ``age_reply``. We then convert the text of the message to an integer and check if the user is old enough to use the service.


Canceling
_________

Now, listeners are blocking. This means that the code execution will stop until the listener returns a result. However, you can cancel the listener if you want to stop waiting for a reply. For example, you can add a button to the message that the user can press to cancel the listener or you can set a timeout for the listener to stop waiting after a certain period of time.

.. code-block:: python
    :linenos:
    :emphasize-lines: 10-11

    from pywa import WhatsApp, types, filters

    wa = WhatsApp(...)

    @wa.on_message(filters.command("start"))
    def start(_: WhatsApp, msg: types.Message):
        sent = msg.reply("Hello! How old are you?", buttons=[types.Button(title="Cancel", callback_data="cancel")])
        age_reply = sent.wait_for_reply(
            filters=filters.text & filters.new(lambda _, m: m.text.isdigit()),
            cancelers=filters.callback_button & filters.matches("cancel"),
            timeout=60,
        )
        ...

In the example above, we added a button to the message that the user can press to cancel the listener. We also set a timeout of 60 seconds for the listener. If the user presses the cancel button or if the listener times out, the listener will stop waiting for a reply and raise an exception.

Handling cancel and timeout
____________________________

When a listener is canceled or times out, it raises an exception. Most of the time, you will want to handle these exceptions to provide a better user experience. PyWa provides two exceptions for this purpose: :class:`~pywa.listeners.ListenerCanceled` and :class:`~pywa.listeners.ListenerTimeout`.
You can use these exceptions to handle the cancel and timeout cases in your code. Let's see an example:

.. code-block:: python
    :linenos:
    :emphasize-lines: 14-15, 17, 20

    from pywa import WhatsApp, types, filters

    wa = WhatsApp(...)


    @wa.on_message(filters.command("start"))
    def start(_: WhatsApp, msg: types.Message):
        try:
            age_reply = msg.reply(
                text="Hello! How old are you?",
                buttons=[types.Button(title="Cancel", callback_data="cancel")],
            ).wait_for_reply(
                filters=filters.text & filters.new(lambda _, m: m.text.isdigit()),
                cancelers=filters.callback_button & filters.matches("cancel"),
                timeout=60,
            )
        except types.ListenerCanceled:
            msg.reply("You canceled the operation by clicking the cancel button.")
            return
        except types.ListenerTimeout:
            msg.reply("You took too long to respond. Please try again later.")
            return
        ...


In the example above, we used a try-except block to handle the :class:`~pywa.listeners.ListenerCanceled` and :class:`~pywa.listeners.ListenerTimeout` exceptions. If the user cancels the listener by clicking the cancel button, we send a message to inform them that they canceled the operation. If the listener times out, we send a message to inform the user that they took too long to respond.
If the listener returns a result, we can continue processing the user's input as usual.


Custom listeners
_________________

.. currentmodule:: pywa.client

You can create custom listeners by using the raw :meth:`WhatsApp.listen` method. This method allows you to create a listener that waits for a specific update and returns the result when the update is received.

For example, let's create a listener that waits for another user to enter the bot and become an admin. We will create a simple database to store the users and admins, and then we will create a listener that waits for a user to enter the bot and adds them as an admin if they are not already registered.

.. code-block:: python
    :linenos:
    :emphasize-lines: 33-38

    from pywa import WhatsApp, types, filters, listeners

    wa = WhatsApp(...)

    class Database:
        def __init__(self):
            self._users = []
            self._admins = set()

        def add_user(self, user: str):
            if user not in self._users:
                self._users.append(user)

        def is_user_exists(self, user: str) -> bool:
            return user in self._users

        def add_admin(self, admin: str):
            if admin not in self._admins:
                self._admins.add(admin)
                self.add_user(admin)

        def is_admin(self, user: str) -> bool:
            return user in self._admins

    db = Database()
    db.add_admin("my_phone_number")  # Add your phone number as an default admin

    @wa.on_message(filters.command("add_admin") & filters.new(lambda _, msg: db.is_admin(msg.sender)))
    def add_admin(client: WhatsApp, msg: types.Message):
        _, new_admin_phone = msg.text.split(maxsplit=1)  # command is /add_admin <phone_number>
        if not db.is_user_exists(new_admin_phone):
            msg.reply("This user is not registered with the bot. Please ask them to enter the bot first.")
            new_chat: types.ChatOpened = client.listen(
                to=listeners.UserUpdateListenerIdentifier(
                    sender=new_admin_phone, recipient=client.phone_id
                ),
                filters=filters.chat_opened,
            )
            new_chat.reply(f"Hi {new_chat.from_user.name}, you have been added as an admin.")
            msg.reply(f"{new_chat.from_user.name} entered the bot, you are now an admin.")
        else:
            db.add_admin(new_admin_phone)
            msg.reply(f"{new_admin_phone} is now an admin.")

.. attention::

    If the listener did not **use** the update (the update not matched the filters or the cancelers), the update **will be passed to the handlers**.
    This means that the update can be processed by other handlers that are registered to handle the same update type.
    This behavior changed since version ``3.0.0``, before that - when update was not used by the listener - it was ignored and not passed to the handlers.

    If you must prevent the update from being passed to the handlers, call the :meth:`~pywa.types.base_update.BaseUpdate.stop_handling` method on the update inside the filters or the cancelers (it will not affect the listener behavior, just prevent the update from being passed to the handlers).


Shortcuts
_________

PyWa provides a few shortcuts to create listeners when sending messages. Let's see an example:

.. code-block:: python
    :linenos:
    :emphasize-lines: 7

    from pywa import WhatsApp, types, filters

    wa = WhatsApp(...)

    @wa.on_message(filters.command("start"))
    def start(client: WhatsApp, msg: types.Message):
        age: types.Message = m.reply("Hello! How old are you?").wait_for_reply(filters.text)
        m.reply(f"You are {age.text} years old")

In the example above, we used the :meth:`~pywa.types.sent_update.SentMessage.wait_for_reply` method to create a listener that waits for a text reply from the user.

.. code-block:: python
    :linenos:
    :emphasize-lines: 7

    from pywa import WhatsApp, types, filters

    wa = WhatsApp(...)

    @wa.on_message(filters.command("start"))
    def start(client: WhatsApp, msg: types.Message):
        msg.reply(f"Hello {msg.from_user.name}!").wait_until_delivered()
        msg.reply("How can I help you?")

In the example above, we used the :meth:`~pywa.types.sent_update.SentMessage.wait_until_delivered` method to create a listener that waits until the message is delivered to the user.

Other shortcuts are available, such as :meth:`~pywa.types.sent_update.SentMessage.wait_for_click`, :meth:`~pywa.types.sent_update.SentMessage.wait_for_selection`, :meth:`~pywa.types.sent_update.SentMessage.wait_until_read`, and more.

.. toctree::

    ./reference
