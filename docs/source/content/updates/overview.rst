💬 Updates
==========

.. currentmodule:: pywa.types

Updates are the **incoming events** from the WhatsApp Cloud API.
They are sent to your webhook URL and converted by PyWa into type-safe objects that are easy to handle.

In WhatsApp Cloud API, updates are called **fields**, and you need to subscribe to them in order to receive them at your webhook URL.

-----------------
Supported Fields
-----------------

The currently supported fields in PyWa are:

- ``messages`` → all user-related updates (messages, callbacks, message status updates)
- ``calls`` → call connect, terminate, and status updates
- ``message_template_status_update`` → template approved, rejected, etc.
- ``message_template_quality_update`` → template quality score changed
- ``message_template_components_update`` → template components changed (header, body, footer, buttons)
- ``template_category_update`` → template category changed
- ``user_preferences`` → user marketing preferences

.. tip::

   If you want to handle other types of updates, use :func:`~pywa.client.WhatsApp.on_raw_update` decorator or the :py:class:`~pywa.handlers.RawUpdateHandler` class.

   .. code-block:: python

      from pywa import WhatsApp, types

      wa = WhatsApp(...)

      @wa.on_raw_update
      def handle_raw_update(wa: WhatsApp, raw: types.RawUpdate):
          print("Received raw update:", raw)

-----------------
Update Types
-----------------

The supported fields are automatically handled by PyWa and converted into Python classes.

👉 To learn how to handle them, see: `Handlers <../handlers/overview.html>`_

**User-related updates:**

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Type
     - Description
   * - :py:class:`~pywa.types.message.Message`
     - A message sent by a user (text, media, order, location, etc.)
   * - :py:class:`~pywa.types.callback.CallbackButton`
     - A :py:class:`~pywa.types.callback.Button` | :py:class:`~pywa.types.templates.QuickReplyButton` pressed by a user
   * - :py:class:`~pywa.types.callback.CallbackSelection`
     - A :py:class:`~pywa.types.callback.SectionRow` chosen by a user
   * - :py:class:`~pywa.types.flows.FlowCompletion`
     - A flow completed by a user
   * - :py:class:`~pywa.types.message_status.MessageStatus`
     - A message status update (delivered, seen, etc.)
   * - :py:class:`~pywa.types.chat_opened.ChatOpened`
     - A chat opened by a user
   * - :py:class:`~pywa.types.system.PhoneNumberChange`
     - A user's phone number changed
   * - :py:class:`~pywa.types.system.IdentityChange`
     - A user's identity changed
   * - :py:class:`~pywa.types.calls.CallConnect`
     - A call connected by a user
   * - :py:class:`~pywa.types.calls.CallTerminate`
     - A call terminated by a user
   * - :py:class:`~pywa.types.calls.CallStatus`
     - A call status update (ringing, busy, etc.)
   * - :py:class:`~pywa.types.calls.CallPermissionUpdate`
     - A call permission update (permission granted or denied)
   * - :py:class:`~pywa.types.user_preferences.UserMarketingPreferences`
     - A user marketing preferences update (e.g. opted in, opted out)

**Account-related updates:**

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Type
     - Description
   * - :py:class:`~pywa.types.templates.TemplateStatusUpdate`
     - A template status update (approved, rejected, etc.)
   * - :py:class:`~pywa.types.templates.TemplateCategoryUpdate`
     - A template category update (category changed)
   * - :py:class:`~pywa.types.templates.TemplateQualityUpdate`
     - A template quality update (quality score changed)
   * - :py:class:`~pywa.types.templates.TemplateComponentsUpdate`
     - A template components update (header, body, footer, buttons changed)

-----------------
Common Properties
-----------------

.. currentmodule:: pywa.types.base_update

All updates share common methods and properties:

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
     - The update timestamp (UTC)
   * - :attr:`~BaseUpdate.shared_data`
     - A dictionary to share data between handlers
   * - :meth:`~BaseUpdate.stop_handling`
     - Prevent further handlers from processing the update
   * - :meth:`~BaseUpdate.continue_handling`
     - Force the update to continue to the next handler
   * - :meth:`~BaseUpdate.handle_again`
     - Re-handle the update from the first handler

**User-related updates** share additional properties:

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Method / Property
     - Description
   * - :attr:`~BaseUserUpdate.sender`
     - The phone ID of the sender
   * - :attr:`~BaseUserUpdate.recipient`
     - The phone ID of the recipient
   * - :attr:`~BaseUserUpdate.message_id_to_reply`
     - The message ID to reply to
   * - :meth:`~BaseUserUpdate.reply_text`
     - Reply with a text message
   * - :meth:`~BaseUserUpdate.reply_image`
     - Reply with an image message
   * - :meth:`~BaseUserUpdate.reply_video`
     - Reply with a video message
   * - :meth:`~BaseUserUpdate.reply_audio`
     - Reply with an audio message
   * - :meth:`~BaseUserUpdate.reply_voice`
     - Reply with a voice message
   * - :meth:`~BaseUserUpdate.reply_document`
     - Reply with a document message
   * - :meth:`~BaseUserUpdate.reply_location`
     - Reply with a location message
   * - :meth:`~BaseUserUpdate.reply_location_request`
     - Request the user’s location
   * - :meth:`~BaseUserUpdate.reply_contact`
     - Reply with a contact message
   * - :meth:`~BaseUserUpdate.reply_sticker`
     - Reply with a sticker message
   * - :meth:`~BaseUserUpdate.reply_template`
     - Reply with a template message
   * - :meth:`~BaseUserUpdate.reply_catalog`
     - Reply with a catalog message
   * - :meth:`~BaseUserUpdate.reply_product`
     - Reply with a product message
   * - :meth:`~BaseUserUpdate.reply_products`
     - Reply with a list of product messages
   * - :meth:`~BaseUserUpdate.react`
     - React to the update with an emoji
   * - :meth:`~BaseUserUpdate.unreact`
     - Remove a reaction
   * - :meth:`~BaseUserUpdate.mark_as_read`
     - Mark the update as read
   * - :meth:`~BaseUserUpdate.indicate_typing`
     - Indicate typing to the user
   * - :meth:`~BaseUserUpdate.block_sender`
     - Block the sender
   * - :meth:`~BaseUserUpdate.unblock_sender`
     - Unblock the sender
   * - :meth:`~BaseUserUpdate.call`
     - Start a call with the sender

.. toctree::
    message
    callback_button
    callback_selection
    flow_completion
    message_status
    chat_opened
    phone_number_change
    identity_change
    call_connect
    call_terminate
    call_status
    call_permission_update
    user_marketing_preferences
    template_status_update
    template_category_update
    template_quality_update
    template_components_update
    raw_update
    common_methods
