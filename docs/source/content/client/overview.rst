🔌 Client
===========

.. currentmodule:: pywa.client


The :class:`~WhatsApp` client has 3 main responsibilities:

1. Sending messages (text, media, location, contact, etc.)
2. Listening for incoming messages and events
3. Creating and managing templates, flows, profile and other business-related resources


.. tip::
    :class: note

    Pywa provides two clients, synchronous and asynchronous, you can choose the one that fits your needs.

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

.. autoclass:: WhatsApp()
    :members: __init__


Sending messages
----------------

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
     - Send an audio
   * - :meth:`~WhatsApp.send_document`
     - Send a document
   * - :meth:`~WhatsApp.send_location`
     - Send a location
   * - :meth:`~WhatsApp.request_location`
     - Request location
   * - :meth:`~WhatsApp.send_contact`
     - Send a contact/s
   * - :meth:`~WhatsApp.send_sticker`
     - Send a sticker
   * - :meth:`~WhatsApp.send_template`
     - Send a template
   * - :meth:`~WhatsApp.send_catalog`
     - Send a catalog
   * - :meth:`~WhatsApp.send_product`
     - Send a product
   * - :meth:`~WhatsApp.send_products`
     - Send multiple products
   * - :meth:`~WhatsApp.send_reaction`
     - React to a message
   * - :meth:`~WhatsApp.remove_reaction`
     - Remove a reaction
   * - :meth:`~WhatsApp.mark_message_as_read`
     - Mark a message as read
   * - :meth:`~WhatsApp.indicate_typing`
     - Indicate typing

Handling updates
----------------

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Method
     - Description
   * - :meth:`~WhatsApp.on_message`
     - Handle messages
   * - :meth:`~WhatsApp.on_callback_button`
     - Handle callback button clicks
   * - :meth:`~WhatsApp.on_callback_selection`
     - Handle callback selections
   * - :meth:`~WhatsApp.on_message_status`
     - Handle message status (delivered, read etc.)
   * - :meth:`~WhatsApp.on_chat_opened`
     - Handle when new chat is opened
   * - :meth:`~WhatsApp.on_flow_request`
     - Handle incoming flow requests
   * - :meth:`~WhatsApp.on_flow_completion`
     - Handle flow completions
   * - :meth:`~WhatsApp.on_template_status`
     - Handle template status changes
   * - :meth:`~WhatsApp.add_handlers`
     - Add handlers programmatically
   * - :meth:`~WhatsApp.remove_handlers`
     - Remove handlers programmatically
   * - :meth:`~WhatsApp.remove_callbacks`
     - Remove handlers by callbacks
   * - :meth:`~WhatsApp.add_flow_request_handler`
     - Add a flow request handler programmatically
   * - :meth:`~WhatsApp.load_handlers_modules`
     - Load handlers from modules

Listening
---------

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Method
     - Description
   * - :meth:`~WhatsApp.listen`
     - Listen to specific user update
   * - :meth:`~WhatsApp.stop_listening`
     - Stop listening

Media
-----

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Method
     - Description
   * - :meth:`~WhatsApp.upload_media`
     - Upload media to WhatsApp servers
   * - :meth:`~WhatsApp.download_media`
     - Download media
   * - :meth:`~WhatsApp.get_media_url`
     - Get media URL
   * - :meth:`~WhatsApp.delete_media`
     - Delete media from WhatsApp servers

Templates
---------

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Method
     - Description
   * - :meth:`~WhatsApp.create_template`
     - Create a template
   * - :meth:`~WhatsApp.upsert_authentication_template`
     - Bulk create or update authentication templates
   * - :meth:`~WhatsApp.get_templates`
     - List all templates
   * - :meth:`~WhatsApp.get_template`
     - Get a template details
   * - :meth:`~WhatsApp.update_template`
     - Update a template
   * - :meth:`~WhatsApp.delete_template`
     - Delete a template
   * - :meth:`~WhatsApp.unpause_template`
     - Unpause a template
   * - :meth:`~WhatsApp.compare_templates`
     - Compare two templates
   * - :meth:`~WhatsApp.migrate_templates`
     - Migrate templates from one WABA to another

Flows
-----

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Method
     - Description
   * - :meth:`~WhatsApp.create_flow`
     - Create a flow
   * - :meth:`~WhatsApp.update_flow_metadata`
     - Update flow metadata (name, categories, endpoint etc.)
   * - :meth:`~WhatsApp.update_flow_json`
     - Update flow JSON
   * - :meth:`~WhatsApp.publish_flow`
     - Publish a flow
   * - :meth:`~WhatsApp.delete_flow`
     - Delete a flow
   * - :meth:`~WhatsApp.deprecate_flow`
     - Deprecate a flow
   * - :meth:`~WhatsApp.get_flow`
     - Get a flow details
   * - :meth:`~WhatsApp.get_flows`
     - List all flows
   * - :meth:`~WhatsApp.get_flow_metrics`
     - Get flow metrics
   * - :meth:`~WhatsApp.get_flow_assets`
     - Get flow assets
   * - :meth:`~WhatsApp.migrate_flows`
     - Migrate flows from one WABA to another

Business
--------

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
     - Get business phone numbers
   * - :meth:`~WhatsApp.get_business_phone_number`
     - Get business phone number
   * - :meth:`~WhatsApp.update_business_profile`
     - Update business profile details (name, description, picture etc.)
   * - :meth:`~WhatsApp.update_conversational_automation`
     - Update commands and ice breakers
   * - :meth:`~WhatsApp.set_business_public_key`
     - Upload business public key
   * - :meth:`~WhatsApp.get_business_phone_number_settings`
     - Get business phone number settings
   * - :meth:`~WhatsApp.update_business_phone_number_settings`
     - Update business phone number settings
   * - :meth:`~WhatsApp.register_phone_number`
     - Register new phone number
   * - :meth:`~WhatsApp.update_display_name`
     - Update display name of the phone number

Managing users
----------------

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
     - Get blocked users

QR Codes
--------

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Method
     - Description
   * - :meth:`~WhatsApp.create_qr_code`
     - Create a QR code for a phone number
   * - :meth:`~WhatsApp.get_qr_code`
     - Get a QR code
   * - :meth:`~WhatsApp.get_qr_codes`
     - Get all QR codes
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
------

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
     - Get flow request handler to handle manually

Others
------

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Method
     - Description
   * - :meth:`~WhatsApp.get_app_access_token`
     - Get app access token
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
