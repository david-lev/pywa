# 💬 Updates

Updates are the **incoming events** from the WhatsApp Cloud API. They are sent to your webhook URL and converted by PyWa into type-safe objects that are easy to handle.

In the WhatsApp Cloud API, incoming events are grouped into webhook **fields** (such as `messages` or `calls`). To receive these updates, you must configure your webhook URL in the Meta Developer Portal and subscribe to the specific fields your bot needs.

## Supported Fields

The currently supported fields in PyWa are:

- `messages` → all user-related updates (messages, callbacks, message status updates)
- `calls` → call connect, terminate, and status updates
- `message_template_status_update` → template approved, rejected, etc.
- `message_template_quality_update` → template quality score changed
- `message_template_components_update` → template components changed (header, body, footer, buttons)
- `template_category_update` → template category changed
- `user_preferences` → user marketing preferences


!!! tip

    Tip


    If you want to handle other types of updates, use [`on_raw_update()`][pywa.handlers._HandlerDecorators.on_raw_update] decorator or the [`RawUpdateHandler`][pywa.handlers.RawUpdateHandler] class.


    ```python
    from pywa import WhatsApp, types

    wa = WhatsApp(...)


    @wa.on_raw_update
    def handle_raw_update(wa: WhatsApp, raw: types.RawUpdate):
        print("Received raw update:", raw)
    ```



## Update Types

The supported fields are automatically handled by PyWa and converted into Python classes.

👉 To learn how to handle them, see: [Handlers](../handlers/index.md)

**User-related updates:**

| Type          | Description                                                             |
|---------------|-------------------------------------------------------------------------|
| [`Message`][pywa.types.message.Message] | A message sent by a user (text, media, order, location, etc.)           |
| [`CallbackButton`][pywa.types.callback.CallbackButton] | A [`Button`][pywa.types.callback.Button] \| [`QuickReplyButton`][pywa.types.templates.QuickReplyButton] pressed by a user                      |
| [`CallbackSelection`][pywa.types.callback.CallbackSelection] | A [`SectionRow`][pywa.types.callback.SectionRow] chosen by a user                                        |
| [`FlowCompletion`][pywa.types.flows.FlowCompletion] | A flow completed by a user                                              |
| [`MessageStatus`][pywa.types.message_status.MessageStatus] | A message status update (delivered, seen, etc.)                         |
| [`PhoneNumberChange`][pywa.types.system.PhoneNumberChange] | A user's phone number changed                                           |
| [`IdentityChange`][pywa.types.system.IdentityChange] | A user's identity changed                                               |
| [`CallConnect`][pywa.types.calls.CallConnect] | A call connected by a user                                              |
| [`CallTerminate`][pywa.types.calls.CallTerminate] | A call terminated by a user                                             |
| [`CallStatus`][pywa.types.calls.CallStatus] | A call status update (ringing, busy, etc.)                              |
| [`CallPermissionUpdate`][pywa.types.calls.CallPermissionUpdate] | A call permission update (permission granted or denied)                 |
| [`UserMarketingPreferences`][pywa.types.user_preferences.UserMarketingPreferences] | A user marketing preferences update (e.g. opted in, opted out)          |
| [`EditedMessage`][pywa.types.message.EditedMessage] | A user edited a message                                                 |
| [`DeletedMessage`][pywa.types.message.DeletedMessage] | A user deleted (revoked) a message                                      |
| [`OutgoingMessage`][pywa.types.message.OutgoingMessage] | A message sent from the business app (only available in Coexistence)    |
| [`OutgoingEditedMessage`][pywa.types.message.OutgoingEditedMessage] | A message edited from the business app (only available in Coexistence)  |
| [`OutgoingDeletedMessage`][pywa.types.message.OutgoingDeletedMessage] | A message deleted from the business app (only available in Coexistence) |
| [`AccountUpdate`][pywa.types.account_update.AccountUpdate] | An account update (e.g. account banned, restricted, etc.)               |

**Account-related updates:**

| Type          | Description                                                          |
|---------------|----------------------------------------------------------------------|
| [`TemplateStatusUpdate`][pywa.types.templates.TemplateStatusUpdate] | A template status update (approved, rejected, etc.)                  |
| [`TemplateCategoryUpdate`][pywa.types.templates.TemplateCategoryUpdate] | A template category update (category changed)                        |
| [`TemplateQualityUpdate`][pywa.types.templates.TemplateQualityUpdate] | A template quality update (quality score changed)                    |
| [`TemplateComponentsUpdate`][pywa.types.templates.TemplateComponentsUpdate] | A template components update (header, body, footer, buttons changed) |

## Common Properties

All updates share common methods and properties:

| Property      | Description                                         |
|---------------|-----------------------------------------------------|
| [`id`][pywa.types.base_update.BaseUpdate.id] | The update ID                                       |
| [`raw`][pywa.types.base_update.BaseUpdate.raw] | The raw update data                                 |
| [`timestamp`][pywa.types.base_update.BaseUpdate.timestamp] | The update timestamp (UTC)                          |
| [`shared_data`][pywa.types.base_update.BaseUpdate.shared_data] | A dictionary to share data between handlers         |
| [`stop_handling()`][pywa.types.base_update.BaseUpdate.stop_handling] | Prevent further handlers from processing the update |
| [`continue_handling()`][pywa.types.base_update.BaseUpdate.continue_handling] | Force the update to continue to the next handler    |
| [`handle_again()`][pywa.types.base_update.BaseUpdate.handle_again] | Re-handle the update from the first handler         |

**User-related updates** share additional properties:

| Method / Property | Description                           |
|-------------------|---------------------------------------|
| [`reply_text()`][pywa.types.base_update.BaseUserUpdate.reply_text]     | Reply with a text message             |
| [`reply_image()`][pywa.types.base_update.BaseUserUpdate.reply_image]     | Reply with an image message           |
| [`reply_video()`][pywa.types.base_update.BaseUserUpdate.reply_video]     | Reply with a video message            |
| [`reply_audio()`][pywa.types.base_update.BaseUserUpdate.reply_audio]     | Reply with an audio message           |
| [`reply_voice()`][pywa.types.base_update.BaseUserUpdate.reply_voice]     | Reply with a voice message            |
| [`reply_document()`][pywa.types.base_update.BaseUserUpdate.reply_document]     | Reply with a document message         |
| [`reply_location()`][pywa.types.base_update.BaseUserUpdate.reply_location]     | Reply with a location message         |
| [`reply_location_request()`][pywa.types.base_update.BaseUserUpdate.reply_location_request]     | Request the user’s location           |
| [`reply_contact_info_request()`][pywa.types.base_update.BaseUserUpdate.reply_contact_info_request]     | Request the user’s contact info       |
| [`reply_contact()`][pywa.types.base_update.BaseUserUpdate.reply_contact]     | Reply with a contact message          |
| [`reply_sticker()`][pywa.types.base_update.BaseUserUpdate.reply_sticker]     | Reply with a sticker message          |
| [`reply_template()`][pywa.types.base_update.BaseUserUpdate.reply_template]     | Reply with a template message         |
| [`reply_catalog()`][pywa.types.base_update.BaseUserUpdate.reply_catalog]     | Reply with a catalog message          |
| [`reply_product()`][pywa.types.base_update.BaseUserUpdate.reply_product]     | Reply with a product message          |
| [`reply_products()`][pywa.types.base_update.BaseUserUpdate.reply_products]     | Reply with a list of product messages |
| [`reply_carousel()`][pywa.types.base_update.BaseUserUpdate.reply_carousel]     | Reply with a carousel message         |
| [`react()`][pywa.types.base_update.BaseUserUpdate.react]     | React to the update with an emoji     |
| [`unreact()`][pywa.types.base_update.BaseUserUpdate.unreact]     | Remove a reaction                     |
| [`mark_as_read()`][pywa.types.base_update.BaseUserUpdate.mark_as_read]     | Mark the update as read               |
| [`indicate_typing()`][pywa.types.base_update.BaseUserUpdate.indicate_typing]     | Indicate typing to the user           |
| [`block_sender()`][pywa.types.base_update.BaseUserUpdate.block_sender]     | Block the sender                      |
| [`unblock_sender()`][pywa.types.base_update.BaseUserUpdate.unblock_sender]     | Unblock the sender                    |
| [`call()`][pywa.types.base_update.BaseUserUpdate.call]     | Start a call with the sender          |
| [`message_id_to_reply`][pywa.types.base_update.BaseUserUpdate.message_id_to_reply]     | The message ID to reply to            |

- [Message](message.md)
- [Callback Button](callback_button.md)
- [Callback Selection](callback_selection.md)
- [Flow Completion](flow_completion.md)
- [Message Status](message_status.md)
- [Phone Number Change](phone_number_change.md)
- [Identity Change](identity_change.md)
- [Call Connect](call_connect.md)
- [Call Terminate](call_terminate.md)
- [Call Status](call_status.md)
- [Call Permission Update](call_permission_update.md)
- [User Marketing Preferences](user_marketing_preferences.md)
- [Template Status Update](template_status_update.md)
- [Template Category Update](template_category_update.md)
- [Template Quality Update](template_quality_update.md)
- [Template Components Update](template_components_update.md)
- [Edited Message](edited_message.md)
- [Deleted Message](deleted_message.md)
- [Outgoing Message](outgoing_message.md)
- [Outgoing Edited Message](outgoing_edited_message.md)
- [Outgoing Deleted Message](outgoing_deleted_message.md)
- [Account Update](account_update.md)
- [Raw Update](raw_update.md)
- [Common methods](common_methods.md)
