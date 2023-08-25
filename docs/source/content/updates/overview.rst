💬 Updates
==========



.. currentmodule:: pywa.types

In WhatsApp Cloud API, updates are sent to your webhook URL. There are lots of different types of updates,
but currently, we only support the ``messages`` field. this field contains all the user-related updates (e.g. messages, callbacks, etc.).

.. tip::

        If you do want to handle other types of updates, you can use the :func:`~pywa.client.WhatsApp.on_raw_update`
        decorator. This decorator will be called for every update.


.. important::
    :class: dropdown

    The ``messages`` field must be enabled in your webhook settings. Otherwise, you will not receive any updates.
    To enable it, go to your app dashboard, click on the ``Webhooks`` tab. Then, subscribe to the ``messages`` field.


The supported types of updates are:

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Type
     - Description
   * - :py:class:`~pywa.types.message.Message`
     - A message sent by a user (text, media, order, location, etc.)
   * - :py:class:`~pywa.types.callback.CallbackButton`
     - A callback button pressed by a user
   * - :py:class:`~pywa.types.callback.CallbackSelection`
     - A callback selection chosen by a user
   * - :py:class:`~pywa.types.message_status.MessageStatus`
     - A message status update (e.g. delivered, seen, etc.)

All updates have common methods:

.. currentmodule:: pywa.types.base_update

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Method
     - Description
   * - :meth:`~BaseUpdate.reply_text`
     - Reply to the update with a text message
   * - :meth:`~BaseUpdate.reply_image`
     - Reply to the update with an image message
   * - :meth:`~BaseUpdate.reply_video`
     - Reply to the update with a video message
   * - :meth:`~BaseUpdate.reply_audio`
     - Reply to the update with an audio message
   * - :meth:`~BaseUpdate.reply_document`
     - Reply to the update with a document message
   * - :meth:`~BaseUpdate.reply_location`
     - Reply to the update with a location message
   * - :meth:`~BaseUpdate.reply_contact`
     - Reply to the update with a contact message
   * - :meth:`~BaseUpdate.reply_sticker`
     - Reply to the update with a sticker message
   * - :meth:`~BaseUpdate.reply_template`
     - Reply to the update with a template message
   * - :meth:`~BaseUpdate.reply_catalog`
     - Reply to the update with a catalog message
   * - :meth:`~BaseUpdate.reply_product`
     - Reply to the update with a product message
   * - :meth:`~BaseUpdate.reply_products`
     - Reply to the update with a list of product messages
   * - :meth:`~BaseUpdate.react`
     - React to the update with a emoji
   * - :meth:`~BaseUpdate.unreact`
     - Unreact to the update
   * - :meth:`~BaseUpdate.mark_as_read`
     - Mark the update as read

.. toctree::
    message
    callback_button
    callback_selection
    message_status
    common_methods
