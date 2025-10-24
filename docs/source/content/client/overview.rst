🔌 Client
=========

.. currentmodule:: pywa.client

The :class:`~WhatsApp` client is the heart of the **pywa** library.
It is responsible for managing communication with the WhatsApp Business API.

Its **three main responsibilities** are:

1. **Sending messages** — text, media, location, contacts, etc.
2. **Listening** — handling incoming messages, events, and statuses.
3. **Managing resources** — templates, flows, profiles, and other business-related settings.

.. tip::
   :class: note

   Pywa provides **two types of clients**:

   - **Synchronous** (`pywa`)
   - **Asynchronous** (`pywa_async`)

   Choose the one that best fits your application’s needs.

   .. code-block:: python
      :emphasize-lines: 1

      from pywa import WhatsApp, types
      wa = WhatsApp(...)

      @wa.on_message
      def on_message(_: WhatsApp, msg: types.Message):
          msg.reply("Hello!")

   .. code-block:: python
      :emphasize-lines: 1

      from pywa_async import WhatsApp, types
      wa = WhatsApp(...)

      @wa.on_message
      async def on_message(_: WhatsApp, msg: types.Message):
          await msg.reply("Hello!")

   For optimal type checking, ensure that **all** your imports come from the same package—either ``pywa`` or ``pywa_async``.
.. autoclass:: WhatsApp()
   :members: __init__


Sending Messages
----------------

The client allows you to send a wide variety of messages:

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Method
     - Description
   * - :meth:`~WhatsApp.send_message`
     - Send a text message
   * - :meth:`~WhatsApp.send_image`
     - Send an image
   * - :meth:`~WhatsApp.send_video`
     - Send a video
   * - :meth:`~WhatsApp.send_audio`
     - Send an audio file
   * - :meth:`~WhatsApp.send_document`
     - Send a document
   * - :meth:`~WhatsApp.send_location`
     - Share a location
   * - :meth:`~WhatsApp.request_location`
     - Request location from a user
   * - :meth:`~WhatsApp.send_contact`
     - Send one or multiple contacts
   * - :meth:`~WhatsApp.send_sticker`
     - Send a sticker
   * - :meth:`~WhatsApp.send_template`
     - Send a template message
   * - :meth:`~WhatsApp.send_catalog`
     - Send a product catalog
   * - :meth:`~WhatsApp.send_product`
     - Send a single product
   * - :meth:`~WhatsApp.send_products`
     - Send multiple products
   * - :meth:`~WhatsApp.send_reaction`
     - React to a message
   * - :meth:`~WhatsApp.remove_reaction`
     - Remove a reaction
   * - :meth:`~WhatsApp.mark_message_as_read`
     - Mark a message as read
   * - :meth:`~WhatsApp.indicate_typing`
     - Indicate typing status to the user


Handling Updates
----------------

Register event handlers to listen for updates:

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Method
     - Description
   * - :meth:`~WhatsApp.on_message`
     - Handle incoming messages
   * - :meth:`~WhatsApp.on_callback_button`
     - Handle callback button clicks
   * - :meth:`~WhatsApp.on_callback_selection`
     - Handle list or menu selections
   * - :meth:`~WhatsApp.on_message_status`
     - Track message delivery, read, and failure statuses
   * - :meth:`~WhatsApp.on_chat_opened`
     - Detect when a user opens a chat
   * - :meth:`~WhatsApp.on_flow_request`
     - Handle incoming flow requests
   * - :meth:`~WhatsApp.on_flow_completion`
     - Handle flow completions
   * - :meth:`~WhatsApp.on_phone_number_change`
     - Handle phone number changes
   * - :meth:`~WhatsApp.on_identity_change`
     - Handle identity changes
   * - :meth:`~WhatsApp.on_call_connect`
     - Handle incoming/outgoing call connections
   * - :meth:`~WhatsApp.on_call_terminate`
     - Handle call terminations
   * - :meth:`~WhatsApp.on_call_status`
     - Handle call status updates
   * - :meth:`~WhatsApp.on_call_permission_update`
     - Handle call permission updates
   * - :meth:`~WhatsApp.on_user_marketing_preferences`
     - Handle user marketing preferences updates
   * - :meth:`~WhatsApp.on_template_status_update`
     - Handle template status updates
   * - :meth:`~WhatsApp.on_template_category_update`
     - Handle template category changes
   * - :meth:`~WhatsApp.on_template_quality_update`
     - Handle template quality changes
   * - :meth:`~WhatsApp.on_template_components_update`
     - Handle template components updates
   * - :meth:`~WhatsApp.on_raw_update`
     - Handle raw updates from WhatsApp
   * - :meth:`~WhatsApp.add_handlers`
     - Dynamically add handlers programmatically
   * - :meth:`~WhatsApp.remove_handlers`
     - Remove handlers programmatically
   * - :meth:`~WhatsApp.remove_callbacks`
     - Remove handlers by callbacks
   * - :meth:`~WhatsApp.add_flow_request_handler`
     - Add flow request handlers programmatically
   * - :meth:`~WhatsApp.load_handlers_modules`
     - Load handlers from external modules


Listening
---------

You can listen for updates from specific users:

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Method
     - Description
   * - :meth:`~WhatsApp.listen`
     - Listen to a specific user update
   * - :meth:`~WhatsApp.stop_listening`
     - Stop listening


Media
-----

Manage media with ease:

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Method
     - Description
   * - :meth:`~WhatsApp.upload_media`
     - Upload media to WhatsApp servers
   * - :meth:`~WhatsApp.download_media`
     - Download media
   * - :meth:`~WhatsApp.stream_media`
     - Stream media
   * - :meth:`~WhatsApp.get_media_bytes`
     - Get media as bytes
   * - :meth:`~WhatsApp.get_media_url`
     - Get direct media URL
   * - :meth:`~WhatsApp.delete_media`
     - Delete media from WhatsApp servers


Templates
---------

Create, update, and manage message templates:

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Method
     - Description
   * - :meth:`~WhatsApp.create_template`
     - Create a new template
   * - :meth:`~WhatsApp.upsert_authentication_template`
     - Bulk create or update authentication templates
   * - :meth:`~WhatsApp.get_templates`
     - Retrieve all templates
   * - :meth:`~WhatsApp.get_template`
     - Get details of a specific template
   * - :meth:`~WhatsApp.update_template`
     - Update an existing template
   * - :meth:`~WhatsApp.delete_template`
     - Delete a template
   * - :meth:`~WhatsApp.unpause_template`
     - Unpause a previously paused template
   * - :meth:`~WhatsApp.compare_templates`
     - Compare two templates
   * - :meth:`~WhatsApp.migrate_templates`
     - Migrate templates between WABAs


Flows
-----

Programmatically manage flows:

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Method
     - Description
   * - :meth:`~WhatsApp.create_flow`
     - Create a flow
   * - :meth:`~WhatsApp.update_flow_metadata`
     - Update flow metadata (name, categories, endpoint, etc.)
   * - :meth:`~WhatsApp.update_flow_json`
     - Update flow JSON definition
   * - :meth:`~WhatsApp.publish_flow`
     - Publish a flow
   * - :meth:`~WhatsApp.delete_flow`
     - Delete a flow
   * - :meth:`~WhatsApp.deprecate_flow`
     - Deprecate a flow
   * - :meth:`~WhatsApp.get_flow`
     - Get details of a flow
   * - :meth:`~WhatsApp.get_flows`
     - List all flows
   * - :meth:`~WhatsApp.get_flow_metrics`
     - Get flow performance metrics
   * - :meth:`~WhatsApp.get_flow_assets`
     - Get flow assets
   * - :meth:`~WhatsApp.migrate_flows`
     - Migrate flows between WABAs


Business
--------

Manage business account and profile:

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Method
     - Description
   * - :meth:`~WhatsApp.get_business_account`
     - Get business account details
   * - :meth:`~WhatsApp.get_business_profile`
     - Get business profile
   * - :meth:`~WhatsApp.get_business_phone_numbers`
     - Get all business phone numbers
   * - :meth:`~WhatsApp.get_business_phone_number`
     - Get a specific business phone number
   * - :meth:`~WhatsApp.update_business_profile`
     - Update profile details (name, description, picture, etc.)
   * - :meth:`~WhatsApp.update_display_name`
     - Update phone number display name
   * - :meth:`~WhatsApp.update_conversational_automation`
     - Update commands and ice breakers
   * - :meth:`~WhatsApp.set_business_public_key`
     - Upload business public key
   * - :meth:`~WhatsApp.get_business_phone_number_settings`
     - Get phone number settings
   * - :meth:`~WhatsApp.update_business_phone_number_settings`
     - Update phone number settings
   * - :meth:`~WhatsApp.register_phone_number`
     - Register a new phone number
   * - :meth:`~WhatsApp.deregister_phone_number`
     - Deregister a phone number


Managing Users
--------------

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Method
     - Description
   * - :meth:`~WhatsApp.block_users`
     - Block users
   * - :meth:`~WhatsApp.unblock_users`
     - Unblock users
   * - :meth:`~WhatsApp.get_blocked_users`
     - Retrieve blocked users


QR Codes
--------

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Method
     - Description
   * - :meth:`~WhatsApp.create_qr_code`
     - Create a QR code
   * - :meth:`~WhatsApp.get_qr_code`
     - Get details of a QR code
   * - :meth:`~WhatsApp.get_qr_codes`
     - List all QR codes
   * - :meth:`~WhatsApp.update_qr_code`
     - Update a QR code
   * - :meth:`~WhatsApp.delete_qr_code`
     - Delete a QR code


Commerce
--------

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Method
     - Description
   * - :meth:`~WhatsApp.get_commerce_settings`
     - Get commerce settings
   * - :meth:`~WhatsApp.update_commerce_settings`
     - Update commerce settings


Calls
-----

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Method
     - Description
   * - :meth:`~WhatsApp.get_call_permissions`
     - Get call permissions
   * - :meth:`~WhatsApp.pre_accept_call`
     - Pre-accept a call
   * - :meth:`~WhatsApp.accept_call`
     - Accept a call
   * - :meth:`~WhatsApp.reject_call`
     - Reject a call
   * - :meth:`~WhatsApp.terminate_call`
     - Terminate a call


Server
------

Integrate with webhook events manually:

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Method
     - Description
   * - :meth:`~WhatsApp.webhook_update_handler`
     - Handle webhook updates manually
   * - :meth:`~WhatsApp.webhook_challenge_handler`
     - Handle webhook challenge manually
   * - :meth:`~WhatsApp.get_flow_request_handler`
     - Retrieve flow request handler


Others
------

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Method
     - Description
   * - :meth:`~WhatsApp.get_app_access_token`
     - Retrieve app access token
   * - :meth:`~WhatsApp.set_app_callback_url`
     - Set app callback URL
   * - :meth:`~WhatsApp.override_waba_callback_url`
     - Override WABA callback URL
   * - :meth:`~WhatsApp.delete_waba_callback_url`
     - Delete WABA callback URL
   * - :meth:`~WhatsApp.override_phone_callback_url`
     - Override phone callback URL
   * - :meth:`~WhatsApp.delete_phone_callback_url`
     - Delete phone callback URL


.. toctree::
   client_reference
   api_reference
