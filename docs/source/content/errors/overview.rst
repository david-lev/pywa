⚠️ Errors
==========

.. currentmodule:: pywa.errors

Exceptions in ``pywa`` are a key mechanism for letting you know **what went wrong and why**.
They appear in two main ways:

1. **Raised exceptions** — when something fails immediately (e.g., invalid parameters).
2. **Returned errors** — when the API reports an error asynchronously via a message status update.

------------------------------

Basic Example
-------------

Most exceptions are raised directly when you attempt an invalid action:

.. code-block:: python
    :emphasize-lines: 8-9, 11

    import logging
    from pywa import WhatsApp, types, errors

    wa = WhatsApp(...)

    try:
        wa.send_message(..., buttons=[
            types.Button(title="click 1", callback_data="click"),
            types.Button(title="click 2", callback_data="click"),  # ⚠️duplicate callback_data
        ])
    except errors.InvalidParameter as e:
        logging.error(f"Duplicated `callback_data` in buttons: {e}")

------------------------------

Message Status Errors
----------------------

Some errors are **not raised immediately** but instead appear as part of a :class:`~pywa.types.message_status.MessageStatus` update.

For example:

- Sending a non-template message **outside the 24h conversation window** →
  :class:`~pywa.errors.ReEngagementMessage`
- Sending invalid media (wrong file type, too large, invalid URL, etc.) →
  :class:`~pywa.errors.MediaUploadError`

These errors surface in the **status update** rather than raising an exception directly.

That’s why it’s **important to always register a handler** for failed message statuses:

.. code-block:: python
    :emphasize-lines: 6

    import logging
    from pywa import WhatsApp, types, filters

    wa = WhatsApp(...)

    @wa.on_message_status(filters.failed)
    def handle_failed_message(client: WhatsApp, status: types.MessageStatus):
        logging.error("Message failed to send to %s: %s",
            status.sender, status.error
        )

------------------------------

Handling Specific Errors
-------------------------

You can also filter and handle specific error types:

.. code-block:: python
    :linenos:
    :emphasize-lines: 18, 24, 31

    import logging
    from pywa import WhatsApp, filters, errors

    wa = WhatsApp(...)

    wa.send_message(to="972501234567", text="Hello")  # 24h window closed
    wa.send_image(  # nonexistent image
        to="972501234567",
        image="https://example.com/this-image-does-not-exist.jpg",
        caption="Not found"
    )
    wa.send_document(  # file too large
        to="972501234567",
        document="https://example.com/document-size-is-too-big.pdf",
        filename="big.pdf"
    )

    @wa.on_message_status(filters.failed_with(errors.ReEngagementMessage))
    def handle_failed_reengagement(client: WhatsApp, status: types.MessageStatus):
        logging.error("Message failed to send to %s: %s",
            status.from_user.wa_id, status.error
        )

    @wa.on_status_message(filters.failed_with(errors.MediaUploadError))
    def handle_failed_sent_media(client: WhatsApp, status: types.MessageStatus):
        logging.error("Message failed to send to %s: %s",
            status.from_user.wa_id, status.error
        )
        status.reply_text("Sorry, I can't upload this file")

    @wa.on_status_message(filters.failed_with(errors.MediaDownloadError))
    def handle_failed_received_media(client: WhatsApp, status: types.MessageStatus):
        logging.error("Got a media download error from %s: %s",
            status.from_user.wa_id, status.error
        )
        status.reply_text("Sorry, I can't download this file")

------------------------------

Incoming Errors (Unsupported Messages)
---------------------------------------

If a user sends an unsupported message type (e.g., poll), you’ll receive a :class:`~pywa.types.Message` with type :class:`~pywa.types.MessageType.UNSUPPORTED` and an error of :class:`~UnsupportedMessageType`.

.. code-block:: python
    :emphasize-lines: 5

    from pywa import WhatsApp, types, filters

    wa = WhatsApp(...)

    @wa.on_message(filters.unsupported)
    def handle_unsupported_message(client: WhatsApp, msg: types.Message):
        msg.reply_text("Sorry, I don't support this message type yet")

------------------------------

Catching All Exceptions
------------------------

Since all exceptions inherit from :class:`~WhatsAppError`, you can catch everything with one block:

.. code-block:: python
    :linenos:
    :emphasize-lines: 7

    from pywa import WhatsApp, errors

    wa = WhatsApp(...)

    try:
        wa.send_message(...)
    except errors.WhatsAppError as e:
        print(f"Error: {e}")

------------------------------

Base Exception
--------------

.. autoclass:: WhatsAppError()
    :show-inheritance:

------------------------------

Categories of Exceptions
-------------------------

All exceptions fall into one of these categories:

.. toctree::

    ./sending_messages_errors
    ./flows_errors
    ./authorization_errors
    ./rate_limit_errors
    ./integrity_errors
    ./block_users_errors
    ./calling_errors
