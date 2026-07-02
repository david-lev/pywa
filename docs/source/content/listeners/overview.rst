📥 Listeners
============

.. currentmodule:: pywa.types.sent_update

When your bot needs more than a single reply — for example, asking a follow-up question or
collecting a sequence of inputs — listeners let you pause execution and wait for the user's
next message, right inside the same handler function. No extra handler needed.

.. warning::

    **Limitations and Resource Safety Warnings:**

    * **Multi-worker environments**: Listening is **not supported** when running the server with multiple workers (e.g., ``pywa run --workers > 1``), as workers do not share in-memory listener states.
    * **Memory Leak Risk**: Listening without a ``timeout`` is highly discouraged. If the user never responds, the listener remains in memory indefinitely. Always specify a reasonable ``timeout``.
    * **Thread Pool Exhaustion (Synchronous Clients)**: In synchronous pywa (not ``pywa_async``, each active listener blocks a worker thread. If you run pywa synchronously with ASGI frameworks like FastAPI or Starlette, active listeners can quickly exhaust the AnyIO thread pool (default is 40). **If the limit is reached, your server will freeze and drop incoming webhooks.**

      *Actionable mitigations:*

      1. **(Recommended)** Migrate to the asynchronous client (``pywa_async``) for fully non-blocking listeners.
      2. Enforce strict, shorter ``timeout`` durations on all listeners to free up threads faster.
      3. Increase the AnyIO thread limit by adjusting ``pywa.server.ANYIO_THREADS_LIMIT`` to a higher value.

Listening
---------

In this example, we wait for the user to send their age. The listener checks that the reply
is a text message containing only digits, then branches based on the value.

.. code-block:: python
    :linenos:
    :emphasize-lines: 8-10

    from pywa import WhatsApp, types, filters

    wa = WhatsApp(...)

    @wa.on_message(filters.command("start"))
    def start(client: WhatsApp, msg: types.Message):
        sent = msg.reply("Hello! How old are you?")
        age_reply: types.Message = sent.wait_for_reply(
            filters=filters.text & filters.new(lambda _, m: m.text.isdigit())
        )
        age = int(age_reply.text)
        if age < 18:
            age_reply.reply("You are too young to use this service.")
        else:
            age_reply.reply("Welcome! You can now use the service.")

.. role:: python(code)
   :language: python

:meth:`~SentMessage.wait_for_reply` blocks execution until the user sends a message that
matches the filter — :python:`filters.text & filters.new(lambda _, m: m.text.isdigit())` here.
The matching update is returned as a :class:`~pywa.types.Message` object, so you can read
``age_reply.text``, reply to it, or pass it along to other logic.

Canceling
---------

Listeners block until a matching message arrives. You can also give the user a way out by
providing ``cancelers`` (e.g., a cancel button) or a ``timeout`` in seconds.
If either triggers, a exception is raised — see *Handling cancel and timeout* below.

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

Handling cancel and timeout
---------------------------

When a listener is canceled or times out, pywa raises :class:`~pywa.listeners.ListenerCanceled`
or :class:`~pywa.listeners.ListenerTimeout` respectively. Catch them to send a helpful response.

.. code-block:: python
    :linenos:
    :emphasize-lines: 12-14, 16, 19

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

Custom listeners
----------------

.. currentmodule:: pywa.client

For advanced use cases, you can use the lower-level :meth:`WhatsApp.listen` method directly.
It lets you specify which sender and update type to wait for, and is what all the shortcuts
(``wait_for_reply``, ``wait_for_click``, etc.) are built on top of.

.. attention::

    If the listener did not **use** the update (the update did not match the filters or the
    cancelers), the update **will be passed to the handlers**.
    This means that the update can be processed by other handlers registered for the same update type.

    If you must prevent the update from being passed to the handlers, call
    :meth:`~pywa.types.base_update.BaseUpdate.stop_handling` on the update inside the filters
    or cancelers (this only affects handler dispatch, not the listener itself).

.. code-block:: python
    :linenos:
    :emphasize-lines: 8-13

    from pywa import WhatsApp, types, filters, listeners

    wa = WhatsApp(...)

    @wa.on_message(filters.command("confirm"))
    def confirm_action(_: WhatsApp, msg: types.Message):
        try:
            confirmation: types.Message = wa.listen(
                to=listeners.UserUpdateListenerIdentifier(sender="97212345678", recipient=wa.phone_id),
                filters=filters.message & filters.matches("yes", "no"),
                cancelers=filters.message & filters.matches("cancel"),
                timeout=30,
            )
            if confirmation.text == "yes":
                confirmation.reply("✅ Confirmed!")
            else:
                confirmation.reply("❌ Didn't confirm")
        except types.ListenerCanceled:
            msg.reply("You canceled the operation by clicking the cancel button.")
            return
        except types.ListenerTimeout:
            msg.reply("You took too long to respond. Please try again later.")
            return

Shortcuts
---------

PyWa provides several shortcuts to create listeners directly from sent messages:

.. code-block:: python
    :linenos:
    :emphasize-lines: 7

    from pywa import WhatsApp, types, filters

    wa = WhatsApp(...)

    @wa.on_message(filters.command("start"))
    def start(client: WhatsApp, msg: types.Message):
        age = msg.reply("Hello! How old are you?").wait_for_reply(filters.text)
        msg.reply(f"You are {age.text} years old")

.. code-block:: python
    :linenos:
    :emphasize-lines: 7

    from pywa import WhatsApp, types, filters

    wa = WhatsApp(...)

    @wa.on_message(filters.command("start"))
    def start(client: WhatsApp, msg: types.Message):
        msg.reply(f"Hello {msg.from_user.name}!").wait_until_delivered()
        msg.reply("How can I help you?")

Other shortcuts include :meth:`~pywa.types.sent_update.SentMessage.wait_for_click`,
:meth:`~pywa.types.sent_update.SentMessage.wait_for_selection`,
:meth:`~pywa.types.sent_update.SentMessage.wait_until_read`,
:meth:`~pywa.types.sent_update.SentVoiceMessage.wait_until_played`,
:meth:`~pywa.types.sent_update.SentLocationRequest.wait_for_location`,
:meth:`~pywa.types.sent_update.SentContactInfoRequest.wait_for_contact_info` and more.

.. toctree::

    ./reference
