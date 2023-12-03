⚠️ Errors
==========

.. currentmodule:: pywa.errors

Exceptions are important part of the ``pywa`` library. They are used to tell you what went wrong and why.
For example, if you try to :meth:`~pywa.client.WhatsApp.send_message` to a user that the last time you sent a message to him was less than 24 hours ago,
if this message is not a template message, you will get a :class:`~ReEngagementMessage` exception.

Most of the exceptions are raised when you try to do something like sending a message:

.. code-block:: python
    :emphasize-lines: 4, 10, 18

    import logging
    from pywa import WhatsApp
    from pywa.types import Button
    from pywa.errors import ReEngagementMessage, InvalidParameter

    wa = WhatsApp(...)

    try:
        wa.send_message(...)
    except ReEngagementMessage as e: # last message to this user was less than 24 hours ago
        logging.error(f"Can't send message after 24 hours: {e}")

    try:
        wa.send_message(..., buttons=[
            Button(title="click 1", callback_data="click"),
            Button(title="click 2", callback_data="click"),
        ])
    except InvalidParameter as e:  # duplicate callback_data in buttons (`click`)
        logging.error(f"Duplicated callback_data in buttons: {e}")


But there are also errors that are not raised, but can be returned in a message status.

For example, you can sometimes send a invalid media (unsupported file type, too big file, invalid url, etc.),
you won't get an exception, but you will get :class:`~pywa.types.message_status.MessageStatus` on :class:`~pywa.types.message_status.MessageStatusType.FAILED`
status with .error attribute with value of :class:`~pywa.errors.MediaUploadError`.

That's why it's important to always register a handler for failed status messages, so you can know when a message failed to send:

.. code-block:: python
    :emphasize-lines: 8

    import logging
    from pywa import WhatsApp
    from pywa.types import MessageStatus
    from pywa import filters as fil

    wa = WhatsApp(...)

    @wa.on_message_status(fil.message_status.failed)  # filter for failed message statuses
    def handle_failed_message(client: WhatsApp, msg: MessageStatus):
        logging.error("Message failed to sent to %s: %s. details: %s",
            status.from_user.wa_id, status.error.message, status.error.details
        )


You can also handle specific errors, for example, if you want to handle only media errors:

.. code-block:: python
    :emphasize-lines: 20

    from pywa import WhatsApp
    from pywa.errors import MediaUploadError, MediaDownloadError
    from pywa.types import MessageStatus
    from pywa import filters as fil

    wa = WhatsApp(...)

    wa.send_image(  # this image does not exist
        to="972501234567",
        image="https://example.com/this-image-does-not-exist.jpg",
        caption="Not found"
    )

    wa.send_document(  # this document is too big
        to="972501234567",
        document="https://example.com/document-size-is-too-big.pdf",
        filename="big.pdf"
    )

    @wa.on_message_status(fil.message_status.failed_with(MediaUploadError, MediaDownloadError))
    def handle_failed_sent_media(client: WhatsApp, msg: MessageStatus):
        if isinstance(msg.error, MediaUploadError):
            msg.reply_text(f"Sorry, I can't upload this file: {msg.error.details}")
        elif isinstance(msg.error, MediaDownloadError):
            msg.reply_text(f"Sorry, I can't download this file: {msg.error.details}")


Another example for "incoming" errors is for unsupported messages: if the user sends unsupported message type (like pool), you will get the
message with type of :class:`~pywa.types.MessageType.UNSUPPORTED` and with error of :class:`~UnsupportedMessageType`.

.. code-block:: python

    from pywa import WhatsApp
    from pywa.types import Message
    from pywa import filters as fil

    wa = WhatsApp(...)

    @wa.on_message(fil.unsupported)
    def handle_unsupported_message(client: WhatsApp, msg: Message):
        msg.reply_text("Sorry, I don't support this message type yet")


-----------------

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
