# 🔌 Client

The [`WhatsApp`][pywa.client.WhatsApp] client is the heart of the **pywa** library. It is responsible for managing communication with the WhatsApp Business API.

Its **three main responsibilities** are:

1.  **Sending messages** — text, media, location, contacts, etc.
2.  **Listening** — handling incoming messages, events, and statuses.
3.  **Managing resources** — templates, flows, profiles, and other business-related settings.


!!! tip

    Tip


    tip

    Pywa provides **two types of clients**:

    - **Synchronous** (pywa)
    - **Asynchronous** (pywa_async)

    Choose the one that best fits your application’s needs.


    ```python hl_lines="1"
    from pywa import WhatsApp, types

    wa = WhatsApp(...)


    @wa.on_message
    def on_message(_: WhatsApp, msg: types.Message):
        msg.reply("Hello!")
    ```



    ```python hl_lines="1"
    from pywa_async import WhatsApp, types

    wa = WhatsApp(...)


    @wa.on_message
    async def on_message(_: WhatsApp, msg: types.Message):
        await msg.reply("Hello!")
    ```


    For optimal type checking, ensure that **all** your imports come from the same package—either `pywa` or `pywa_async`.


To help you navigate the API, the client's methods are grouped below by functionality. Most of these methods return type-safe objects representing API responses, which you can then manipulate or reply to directly.

::: pywa.client.WhatsApp
    options:
      members: ["__init__"]
      inherited_members: ["__init__"]

## Sending Messages

The client allows you to send a wide variety of messages:

| Method        | Description                             |
|---------------|-----------------------------------------|
| [`send_message()`][pywa.client.WhatsApp.send_message] | Send a text message                     |
| [`send_image()`][pywa.client.WhatsApp.send_image] | Send an image                           |
| [`send_video()`][pywa.client.WhatsApp.send_video] | Send a video                            |
| [`send_audio()`][pywa.client.WhatsApp.send_audio] | Send an audio file                      |
| [`send_voice()`][pywa.client.WhatsApp.send_voice] | Send a voice message                    |
| [`send_document()`][pywa.client.WhatsApp.send_document] | Send a document                         |
| [`send_location()`][pywa.client.WhatsApp.send_location] | Share a location                        |
| [`request_location()`][pywa.client.WhatsApp.request_location] | Request location from a user            |
| [`request_contact_info()`][pywa.client.WhatsApp.request_contact_info] | Request contact information from a user |
| [`send_contact()`][pywa.client.WhatsApp.send_contact] | Send one or multiple contacts           |
| [`send_sticker()`][pywa.client.WhatsApp.send_sticker] | Send a sticker                          |
| [`send_template()`][pywa.client.WhatsApp.send_template] | Send a template message                 |
| [`send_catalog()`][pywa.client.WhatsApp.send_catalog] | Send a product catalog                  |
| [`send_product()`][pywa.client.WhatsApp.send_product] | Send a single product                   |
| [`send_products()`][pywa.client.WhatsApp.send_products] | Send multiple products                  |
| [`send_carousel()`][pywa.client.WhatsApp.send_carousel] | Send a carousel message                 |
| [`send_reaction()`][pywa.client.WhatsApp.send_reaction] | React to a message                      |
| [`remove_reaction()`][pywa.client.WhatsApp.remove_reaction] | Remove a reaction                       |
| [`mark_message_as_read()`][pywa.client.WhatsApp.mark_message_as_read] | Mark a message as read                  |
| [`indicate_typing()`][pywa.client.WhatsApp.indicate_typing] | Indicate typing status to the user      |

## Handling Updates

Register event handlers to listen for updates:

| Method        | Description                                        |
|---------------|----------------------------------------------------|
| [`on_message()`][pywa.handlers._HandlerDecorators.on_message] | Handle incoming messages                           |
| [`on_callback_button()`][pywa.handlers._HandlerDecorators.on_callback_button] | Handle callback button clicks                      |
| [`on_callback_selection()`][pywa.handlers._HandlerDecorators.on_callback_selection] | Handle list or menu selections                     |
| [`on_message_status()`][pywa.handlers._HandlerDecorators.on_message_status] | Track message delivery, read, and failure statuses |
| [`on_flow_request()`][pywa.handlers._HandlerDecorators.on_flow_request] | Handle incoming flow requests                      |
| [`on_flow_completion()`][pywa.handlers._HandlerDecorators.on_flow_completion] | Handle flow completions                            |
| [`on_phone_number_change()`][pywa.handlers._HandlerDecorators.on_phone_number_change] | Handle phone number changes                        |
| [`on_identity_change()`][pywa.handlers._HandlerDecorators.on_identity_change] | Handle identity changes                            |
| [`on_call_connect()`][pywa.handlers._HandlerDecorators.on_call_connect] | Handle incoming/outgoing call connections          |
| [`on_call_terminate()`][pywa.handlers._HandlerDecorators.on_call_terminate] | Handle call terminations                           |
| [`on_call_status()`][pywa.handlers._HandlerDecorators.on_call_status] | Handle call status updates                         |
| [`on_call_permission_update()`][pywa.handlers._HandlerDecorators.on_call_permission_update] | Handle call permission updates                     |
| [`on_user_marketing_preferences()`][pywa.handlers._HandlerDecorators.on_user_marketing_preferences] | Handle user marketing preferences updates          |
| [`on_template_status_update()`][pywa.handlers._HandlerDecorators.on_template_status_update] | Handle template status updates                     |
| [`on_template_category_update()`][pywa.handlers._HandlerDecorators.on_template_category_update] | Handle template category changes                   |
| [`on_template_quality_update()`][pywa.handlers._HandlerDecorators.on_template_quality_update] | Handle template quality changes                    |
| [`on_template_components_update()`][pywa.handlers._HandlerDecorators.on_template_components_update] | Handle template components updates                 |
| [`on_edited_message()`][pywa.handlers._HandlerDecorators.on_edited_message] | Handle edited messages                             |
| [`on_deleted_message()`][pywa.handlers._HandlerDecorators.on_deleted_message] | Handle deleted messages                            |
| [`on_outgoing_message()`][pywa.handlers._HandlerDecorators.on_outgoing_message] | Handle outgoing messages                           |
| [`on_outgoing_edited_message()`][pywa.handlers._HandlerDecorators.on_outgoing_edited_message] | Handle outgoing edited messages                    |
| [`on_outgoing_deleted_message()`][pywa.handlers._HandlerDecorators.on_outgoing_deleted_message] | Handle outgoing deleted messages                   |
| [`on_account_update()`][pywa.handlers._HandlerDecorators.on_account_update] | Handle business account updates                    |
| [`on_raw_update()`][pywa.handlers._HandlerDecorators.on_raw_update] | Handle raw updates from WhatsApp                   |
| [`add_handlers()`][pywa.client.WhatsApp.add_handlers] | Dynamically add handlers programmatically          |
| [`remove_handlers()`][pywa.client.WhatsApp.remove_handlers] | Remove handlers programmatically                   |
| [`remove_callbacks()`][pywa.client.WhatsApp.remove_callbacks] | Remove handlers by callbacks                       |
| [`add_flow_request_handler()`][pywa.client.WhatsApp.add_flow_request_handler] | Add flow request handlers programmatically         |
| [`load_handlers_modules()`][pywa.client.WhatsApp.load_handlers_modules] | Load handlers from external modules                |

## Listening

You can listen for updates from specific users:

| Method        | Description                      |
|---------------|----------------------------------|
| [`listen()`][pywa.listeners._Listeners.listen] | Listen to a specific user update |
| [`stop_listening()`][pywa.listeners._Listeners.stop_listening] | Stop listening                   |

## Media

Manage media with ease:

| Method        | Description                        |
|---------------|------------------------------------|
| [`upload_media()`][pywa.client.WhatsApp.upload_media] | Upload media to WhatsApp servers   |
| [`download_media()`][pywa.client.WhatsApp.download_media] | Download media                     |
| [`stream_media()`][pywa.client.WhatsApp.stream_media] | Stream media                       |
| [`get_media_bytes()`][pywa.client.WhatsApp.get_media_bytes] | Get media as bytes                 |
| [`get_media_url()`][pywa.client.WhatsApp.get_media_url] | Get direct media URL               |
| [`delete_media()`][pywa.client.WhatsApp.delete_media] | Delete media from WhatsApp servers |

## Templates

Create, update, and manage message templates:

| Method        | Description                                                            |
|---------------|------------------------------------------------------------------------|
| [`create_template()`][pywa.client.WhatsApp.create_template] | Create a new template                                                  |
| [`upsert_authentication_template()`][pywa.client.WhatsApp.upsert_authentication_template] | Create or update multiple authentication templates in a single request |
| [`get_templates()`][pywa.client.WhatsApp.get_templates] | Retrieve all templates                                                 |
| [`get_template()`][pywa.client.WhatsApp.get_template] | Get details of a specific template                                     |
| [`update_template()`][pywa.client.WhatsApp.update_template] | Update an existing template                                            |
| [`delete_template()`][pywa.client.WhatsApp.delete_template] | Delete a template                                                      |
| [`unpause_template()`][pywa.client.WhatsApp.unpause_template] | Unpause a previously paused template                                   |
| [`archive_templates()`][pywa.client.WhatsApp.archive_templates] | Archive one or multiple templates                                      |
| [`unarchive_templates()`][pywa.client.WhatsApp.unarchive_templates] | Unarchive one or multiple templates                                    |
| [`compare_templates()`][pywa.client.WhatsApp.compare_templates] | Compare two templates                                                  |
| [`migrate_templates()`][pywa.client.WhatsApp.migrate_templates] | Migrate templates between WABAs                                        |

## Flows

Programmatically manage flows:

| Method        | Description                                             |
|---------------|---------------------------------------------------------|
| [`create_flow()`][pywa.client.WhatsApp.create_flow] | Create a flow                                           |
| [`update_flow_metadata()`][pywa.client.WhatsApp.update_flow_metadata] | Update flow metadata (name, categories, endpoint, etc.) |
| [`update_flow_json()`][pywa.client.WhatsApp.update_flow_json] | Update flow JSON definition                             |
| [`publish_flow()`][pywa.client.WhatsApp.publish_flow] | Publish a flow                                          |
| [`delete_flow()`][pywa.client.WhatsApp.delete_flow] | Delete a flow                                           |
| [`deprecate_flow()`][pywa.client.WhatsApp.deprecate_flow] | Deprecate a flow                                        |
| [`get_flow()`][pywa.client.WhatsApp.get_flow] | Get details of a flow                                   |
| [`get_flows()`][pywa.client.WhatsApp.get_flows] | List all flows                                          |
| [`get_flow_metrics()`][pywa.client.WhatsApp.get_flow_metrics] | Get flow performance metrics                            |
| [`get_flow_assets()`][pywa.client.WhatsApp.get_flow_assets] | Get flow assets                                         |
| [`migrate_flows()`][pywa.client.WhatsApp.migrate_flows] | Migrate flows between WABAs                             |

## Business

Manage business account and profile:

| Method        | Description                                               |
|---------------|-----------------------------------------------------------|
| [`get_business_account()`][pywa.client.WhatsApp.get_business_account] | Get business account details                              |
| [`update_business_account_settings()`][pywa.client.WhatsApp.update_business_account_settings] | Update business account settings                          |
| [`get_business_profile()`][pywa.client.WhatsApp.get_business_profile] | Get business profile                                      |
| [`get_business_phone_numbers()`][pywa.client.WhatsApp.get_business_phone_numbers] | Get all business phone numbers                            |
| [`get_business_phone_number()`][pywa.client.WhatsApp.get_business_phone_number] | Get a specific business phone number                      |
| [`update_business_profile()`][pywa.client.WhatsApp.update_business_profile] | Update profile details (name, description, picture, etc.) |
| [`update_display_name()`][pywa.client.WhatsApp.update_display_name] | Update phone number display name                          |
| [`update_conversational_automation()`][pywa.client.WhatsApp.update_conversational_automation] | Update commands and ice breakers                          |
| [`set_business_public_key()`][pywa.client.WhatsApp.set_business_public_key] | Upload business public key                                |
| [`get_business_phone_number_settings()`][pywa.client.WhatsApp.get_business_phone_number_settings] | Get phone number settings                                 |
| [`update_business_phone_number_settings()`][pywa.client.WhatsApp.update_business_phone_number_settings] | Update phone number settings                              |
| [`set_username()`][pywa.client.WhatsApp.set_username] | Set a username for the business account                   |
| [`get_current_username()`][pywa.client.WhatsApp.get_current_username] | Get the current username of the business account          |
| [`get_reserved_usernames()`][pywa.client.WhatsApp.get_reserved_usernames] | Get a list of reserved usernames for the business account |
| [`delete_username()`][pywa.client.WhatsApp.delete_username] | Delete the current username of the business account       |

## Managing Users

| Method        | Description            |
|---------------|------------------------|
| [`block_users()`][pywa.client.WhatsApp.block_users] | Block users            |
| [`unblock_users()`][pywa.client.WhatsApp.unblock_users] | Unblock users          |
| [`get_blocked_users()`][pywa.client.WhatsApp.get_blocked_users] | Retrieve blocked users |

## QR Codes

| Method        | Description              |
|---------------|--------------------------|
| [`create_qr_code()`][pywa.client.WhatsApp.create_qr_code] | Create a QR code         |
| [`get_qr_code()`][pywa.client.WhatsApp.get_qr_code] | Get details of a QR code |
| [`get_qr_codes()`][pywa.client.WhatsApp.get_qr_codes] | List all QR codes        |
| [`update_qr_code()`][pywa.client.WhatsApp.update_qr_code] | Update a QR code         |
| [`delete_qr_code()`][pywa.client.WhatsApp.delete_qr_code] | Delete a QR code         |

## Signups

| Method        | Description             |
|---------------|-------------------------|
| [`create_signup()`][pywa.client.WhatsApp.create_signup] | Create a signup         |
| [`get_signup()`][pywa.client.WhatsApp.get_signup] | Get details of a signup |
| [`get_signups()`][pywa.client.WhatsApp.get_signups] | List all signups        |
| [`update_signup()`][pywa.client.WhatsApp.update_signup] | Update a signup         |

## Commerce

| Method        | Description              |
|---------------|--------------------------|
| [`get_commerce_settings()`][pywa.client.WhatsApp.get_commerce_settings] | Get commerce settings    |
| [`update_commerce_settings()`][pywa.client.WhatsApp.update_commerce_settings] | Update commerce settings |

## Calls

| Method        | Description          |
|---------------|----------------------|
| [`get_call_permissions()`][pywa.client.WhatsApp.get_call_permissions] | Get call permissions |
| [`pre_accept_call()`][pywa.client.WhatsApp.pre_accept_call] | Pre-accept a call    |
| [`accept_call()`][pywa.client.WhatsApp.accept_call] | Accept a call        |
| [`reject_call()`][pywa.client.WhatsApp.reject_call] | Reject a call        |
| [`terminate_call()`][pywa.client.WhatsApp.terminate_call] | Terminate a call     |

## Groups

| Method        | Description                                             |
|---------------|---------------------------------------------------------|
| [`create_group()`][pywa.client.WhatsApp.create_group] | Create a group                                          |
| [`get_group()`][pywa.client.WhatsApp.get_group] | Get details of a group                                  |
| [`get_groups()`][pywa.client.WhatsApp.get_groups] | List all groups                                         |
| [`delete_group()`][pywa.client.WhatsApp.delete_group] | Delete a group                                          |
| [`get_group_join_requests()`][pywa.client.WhatsApp] | Get pending group join requests                         |
| `approve_group_join_request()` | Approve a group join request                            |
| [`reject_group_join_requests()`][pywa.client.WhatsApp.reject_group_join_requests] | Reject a group join request                             |
| [`update_group_settings()`][pywa.client.WhatsApp.update_group_settings] | Update group details (name, description, picture, etc.) |
| [`remove_group_participants()`][pywa.client.WhatsApp.remove_group_participants] | Remove participants from a group                        |
| [`get_group_invite_link()`][pywa.client.WhatsApp.get_group_invite_link] | Get group invite link                                   |
| [`reset_group_invite_link()`][pywa.client.WhatsApp.reset_group_invite_link] | Reset group invite link                                 |
| [`pin_message()`][pywa.client.WhatsApp.pin_message] | Pin a message in a group                                |
| [`unpin_message()`][pywa.client.WhatsApp.unpin_message] | Unpin a message in a group                              |

## Server

Integrate with webhook events manually:

| Method        | Description                               |
|---------------|-------------------------------------------|
| [`run()`][pywa.server.Server.run] | Start a webhook server to receive updates |
| [`webhook_challenge_handler()`][pywa.server.Server.webhook_challenge_handler] | Handle webhook challenge manually         |
| [`webhook_update_validator()`][pywa.server.Server.webhook_update_validator] | Validate incoming webhook updates         |
| [`webhook_update_handler()`][pywa.server.Server.webhook_update_handler] | Handle webhook updates manually           |
| [`get_flow_request_handler()`][pywa.server.Server.get_flow_request_handler] | Retrieve flow request handler             |

## Partner tools

| Method        | Description                                           |
|---------------|-------------------------------------------------------|
| [`create_phone_number()`][pywa.client.WhatsApp.create_phone_number] | Create a phone number on a WhatsApp Business Account. |
| [`request_verification_code()`][pywa.client.WhatsApp.request_verification_code] | Request a verification code for a phone number.       |
| [`verify_phone_number()`][pywa.client.WhatsApp.verify_phone_number] | Verify a phone number with a verification code.       |
| [`register_phone_number()`][pywa.client.WhatsApp.register_phone_number] | Register a new phone number                           |
| [`deregister_phone_number()`][pywa.client.WhatsApp.deregister_phone_number] | Deregister a phone number                             |
| [`get_shared_business_accounts()`][pywa.client.WhatsApp.get_shared_business_accounts] | Get shared business accounts                          |
| [`get_owned_business_accounts()`][pywa.client.WhatsApp.get_owned_business_accounts] | Get owned business account                            |
| [`override_waba_callback_url()`][pywa.client.WhatsApp.override_waba_callback_url] | Override WABA callback URL                            |
| [`delete_waba_callback_url()`][pywa.client.WhatsApp.delete_waba_callback_url] | Delete WABA callback URL                              |
| [`override_phone_callback_url()`][pywa.client.WhatsApp.override_phone_callback_url] | Override phone callback URL                           |
| [`delete_phone_callback_url()`][pywa.client.WhatsApp.delete_phone_callback_url] | Delete phone callback URL                             |

## Others

| Method        | Description               |
|---------------|---------------------------|
| [`get_app_access_token()`][pywa.client.WhatsApp.get_app_access_token] | Retrieve app access token |
| [`set_app_callback_url()`][pywa.client.WhatsApp.set_app_callback_url] | Set app callback URL      |

- [Client Reference](client_reference.md)
- [API Reference](api_reference.md)
