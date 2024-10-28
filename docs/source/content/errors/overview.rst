⚠️ Errors
==========

.. currentmodule:: pywa.errors

Exceptions are important part of the ``pywa`` library. They are used to tell you what went wrong and why.

Most of the exceptions are raised when you try to do something like sending a message:

.. code-block:: python
    :emphasize-lines: 8-9, 11

    import logging
    from pywa import WhatsApp, types, errors

    wa = WhatsApp(...)

    try:
        wa.send_message(..., buttons=[
            types.Button(title="click 1", callback_data="click"),
            types.Button(title="click 2", callback_data="click"),
        ])
    except errors.InvalidParameter as e:  # duplicate callback_data in buttons (`click`)
        logging.error(f"Duplicated callback_data in buttons: {e}")


But there are also errors that are not raised, but can be returned in a message status.

For example, you can sometimes try to :meth:`~pywa.client.WhatsApp.send_message` to a user that the last time you sent a message to him was less than 24 hours ago,
if this message is not a :class:`~pywa.types.template.Template` message, you will not get an exception,
but you will get :class:`~pywa.types.message_status.MessageStatus` on :class:`~pywa.types.message_status.MessageStatusType.FAILED`
status with .error attribute with value of :class:`~pywa.errors.ReEngagementMessage`.

The same goes for media messages: if you try to send a invalid media (unsupported file type, too big file, invalid url, etc.),
You will not get the exception, when you try to send the message, but in the message status error attribute (:class:`~pywa.errors.MediaUploadError`).


That's why it's important to always register a handler for failed status messages, so you can know when a message failed to send:

.. code-block:: python
    :emphasize-lines: 6

    import logging
    from pywa import WhatsApp, types, filters

    wa = WhatsApp(...)

    @wa.on_message_status(filters.failed)  # filter for failed message statuses
    def handle_failed_message(client: WhatsApp, status: types.MessageStatus):
        logging.error("Message failed to sent to %s: %s. details: %s",
            status.from_user.wa_id, status.error.message, status.error.details
        )


You can also handle specific errors, for example, if you want to handle only media errors:

.. code-block:: python
    :emphasize-lines: 20, 26, 33

    import logging
    from pywa import WhatsApp, filters, errors

    wa = WhatsApp(...)

    wa.send_message(to="972501234567", text="Hello")  # this conversation window is closed (24 hours passed)

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

    @wa.on_message_status(filters.failed_with(errors.ReEngagementMessage))
    def handle_failed_reengagement(client: WhatsApp, status: types.MessageStatus):
        logging.error("Message failed to sent to %s: %s. details: %s",
            status.from_user.wa_id, status.error.message, status.error.details
        )

    @wa.on_status_message(filters.failed_with(errors.MediaUploadError))
    def handle_failed_sent_media(client: WhatsApp, status: types.MessageStatus):
        logging.error("Message failed to sent to %s: %s. details: %s",
            status.from_user.wa_id, status.error.message, status.error.details
        )
        status.reply_text("Sorry, I can't upload this file")

    @wa.on_status_message(filters.failed_with(errors.MediaDownloadError))
    def handle_failed_received_media(client: WhatsApp, status: types.MessageStatus):
        logging.error("Got a media download error from %s: %s. details: %s",
            status.from_user.wa_id, status.error.message, status.error.details
        )
        status.reply_text("Sorry, I can't download this file")


Another example for "incoming" errors is for unsupported messages: if the user sends unsupported message type (like pool), you will get the
message with type of :class:`~pywa.types.MessageType.UNSUPPORTED` and with error of :class:`~UnsupportedMessageType`.

.. code-block:: python
    :emphasize-lines: 5

    from pywa import WhatsApp, types, filters

    wa = WhatsApp(...)

    @wa.on_message(filters.unsupported)
    def handle_unsupported_message(client: WhatsApp, msg: types.Message):
        msg.reply_text("Sorry, I don't support this message type yet")


-----------------

All the exceptions are inherited from :class:`~WhatsAppError`, so you can catch all of them with one exception:

.. code-block:: python
    :linenos:
    :emphasize-lines: 7

    from pywa import WhatsApp, errors

    wa = WhatsApp(...)

    try:
        wa.send_message(...)
    except errors.WhatsAppError as e:
        print(f"Error: {e}")


Base Exception
--------------

.. autoclass:: WhatsAppError()
    :show-inheritance:

-----------------

**The exceptions are divided into 5 categories:**

.. toctree::

    ./sending_messages_errors
    ./flows_errors
    ./authorization_errors
    ./rate_limit_errors
    ./integrity_errors
