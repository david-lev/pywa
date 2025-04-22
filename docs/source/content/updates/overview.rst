💬 Updates
==========


.. currentmodule:: pywa.types

Updates are the incoming events from WhatsApp Cloud API. They are sent to your webhook URL and constructed by the library
to be easily and type-safely to handle.

In WhatsApp Cloud API, the updates called ``fields`` and need to be subscribed to in order to receive them to your webhook URL.

The currently supported fields by PyWa are:

- ``messages`` (all user related updates: messages, callbacks and message status updates)
- ``message_template_status_update`` (template got approved, rejected, etc.)

.. important::

    If you register your callback URL manually (not using PyWa), you need to subscribe to the fields you want to receive.
    Go to your app dashboard, click on the ``Webhooks`` tab (Or the ``Configuration`` tab > ``Webhook fields``).
    Then, subscribe to the fields you want to receive.

    .. toggle::

        .. image:: ../../../../_static/guides/webhook-fields.webp
           :width: 600
           :alt: Subscribe to webhook fields
           :align: center

.. tip::

        If you do want to handle other types of updates (fields), you can use the :py:class:`~pywa.handlers.RawUpdateHandler`
        (or the :func:`~pywa.client.WhatsApp.on_raw_update` decorator) to handle them.


The supported fields are automatically handled by PyWa and converted to the following types:

- To handle updates see `Handlers <../handlers/overview.html>`_

User related updates:

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Type
     - Description
   * - :py:class:`~pywa.types.message.Message`
     - A message sent by a user (text, media, order, location, etc.)
   * - :py:class:`~pywa.types.callback.CallbackButton`
     - A :py:class:`~pywa.types.callback.Button` pressed by a user
   * - :py:class:`~pywa.types.callback.CallbackSelection`
     - A :py:class:`~pywa.types.callback.SectionRow` chosen by a user
   * - :py:class:`~pywa.types.flows.FlowCompletion`
     - A flow completed by a user
   * - :py:class:`~pywa.types.message_status.MessageStatus`
     - A message status update (e.g. delivered, seen, etc.)
   * - :py:class:`~pywa.types.chat_opened.ChatOpened`
     - A chat opened by a user

Account related updates:

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Type
     - Description
   * - :py:class:`~pywa.types.template.TemplateStatus`
     - A template status update (e.g. approved, rejected, etc.)


.. currentmodule:: pywa.types.base_update

All updates have common methods and properties:

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Property
     - Description
   * - :attr:`~BaseUpdate.id`
     - The update ID
   * - :attr:`~BaseUpdate.raw`
     - The raw update data
   * - :attr:`~BaseUpdate.timestamp`
     - The timestamp of the update
   * - :meth:`~BaseUpdate.stop_handling`
     - Stop next handlers from handling the update
   * - :meth:`~BaseUpdate.continue_handling`
     - Continue to the next handler

All user-related-updates have common methods and properties:

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Method / Property
     - Description
   * - :attr:`~BaseUserUpdate.sender`
     - The phone id who sent the update
   * - :attr:`~BaseUserUpdate.recipient`
     - The phone id who received the update
   * - :attr:`~BaseUserUpdate.message_id_to_reply`
     - The message id to reply to
   * - :meth:`~BaseUserUpdate.reply_text`
     - Reply to the update with a text message
   * - :meth:`~BaseUserUpdate.reply_image`
     - Reply to the update with an image message
   * - :meth:`~BaseUserUpdate.reply_video`
     - Reply to the update with a video message
   * - :meth:`~BaseUserUpdate.reply_audio`
     - Reply to the update with an audio message
   * - :meth:`~BaseUserUpdate.reply_document`
     - Reply to the update with a document message
   * - :meth:`~BaseUserUpdate.reply_location`
     - Reply to the update with a location message
   * - :meth:`~BaseUserUpdate.reply_location_request`
     - Request a location from the user
   * - :meth:`~BaseUserUpdate.reply_contact`
     - Reply to the update with a contact message
   * - :meth:`~BaseUserUpdate.reply_sticker`
     - Reply to the update with a sticker message
   * - :meth:`~BaseUserUpdate.reply_template`
     - Reply to the update with a template message
   * - :meth:`~BaseUserUpdate.reply_catalog`
     - Reply to the update with a catalog message
   * - :meth:`~BaseUserUpdate.reply_product`
     - Reply to the update with a product message
   * - :meth:`~BaseUserUpdate.reply_products`
     - Reply to the update with a list of product messages
   * - :meth:`~BaseUserUpdate.react`
     - React to the update with a emoji
   * - :meth:`~BaseUserUpdate.unreact`
     - Unreact to the update
   * - :meth:`~BaseUserUpdate.mark_as_read`
     - Mark the update as read
   * - :meth:`~BaseUserUpdate.indicate_typing`
     - Indicate that the user is typing

.. toctree::
    message
    callback_button
    callback_selection
    flow_completion
    message_status
    chat_opened
    template_status
    common_methods
