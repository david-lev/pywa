⚠️ Errors
==========

.. currentmodule:: pywa.errors

Exceptions are important part of the ``pywa`` library. They are used to tell you what went wrong and why.
For example, if you try to :meth:`~pywa.WhatsApp.send_message` to a user that the last time you sent a message to him was less than 24 hours ago,
if this message is not a template message, you will get a :class:`~ReEngagementMessage` exception.

Most of the exceptions are raised when you try to do something like sending a message, but some of them not raised by
the library, but come from the webhook as part of new :class:`~pywa.types.Message` or :class:`~pywa.types.MessageStatus`.
For example, you can sometimes send a message to a user, and you won't get any exception, but you will get a message status
with status of :class:`~pywa.types.MessageStatus.FAILED` and with error of :class:`~MessageUndeliverable`.
That's why it's important to always register a handler for failed delivery messages, here is an example:

.. code-block:: python

    import logging
    from pywa import WhatsApp
    from pywa.types import MessageStatus
    from pywa import filters as fil

    wa = WhatsApp(...)

    @wa.on_message_status(fil.message_status.failed)  # filter for failed message statuses
    def handle_failed_message(client: WhatsApp, msg: MessageStatus):
        logging.error("Message %s failed to send to %s: %s", status.id, status.from_user.wa_id, status.error.message)

Another example is for unsupported messages: if the user sends unsupported message type (like pool), you will get the
message with type of :class:`~pywa.types.MessageType.UNSUPPORTED` and with error of :class:`~UnsupportedMessageType`.

.. code-block:: python

    from pywa import WhatsApp
    from pywa.types import Message
    from pywa import filters as fil

    wa = WhatsApp(...)

    @wa.on_message(fil.unsupported)
    def handle_unsupported_message(client: WhatsApp, msg: Message):
        msg.reply_text("Sorry, I don't support this message type yet")

All the exceptions are inherited from :class:`~WhatsAppError`, so you can catch all of them with one exception:

.. code-block:: python

    from pywa import WhatsApp
    from pywa.errors import WhatsAppError

    wa = WhatsApp(...)

    try:
        wa.send_message(...)
    except WhatsAppError as e:
        print(f"Error: {e}")


Base Exception
--------------

.. autoclass:: WhatsAppError()
    :show-inheritance:

-----------------

**The exceptions are divided into 4 categories:**

.. toctree::

    ./sending_messages_errors
    ./authorization_errors
    ./rate_limit_errors
    ./integrity_errors
