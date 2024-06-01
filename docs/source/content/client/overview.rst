🔌 Client
===========

.. currentmodule:: pywa.client

.. note::

    WORK IN PROGRESS


The :class:`~WhatsApp` client has 3 main responsibilities:

1. Sending messages (text, media, location, contact, etc.)
2. Creating and managing templates, flows, profile and other business-related resources
3. Listening for incoming messages and events

for sending messages and the other API calls, you will need to provide an phone number id that connects to the WhatsApp Cloud API.
for listening to incoming messages and events, you will need to tell WhatsApp to send the events to a webhook that you provide.

.. tip::
    :class: note

    Pywa provides two clients, synchronous and asynchronous, you can choose the one that fits your needs.

    .. important::

        At the moment it seems that there are problems running with flask or with fastapi when running uvicorn from the code (and not from the command line).

    .. code-block:: python
        :emphasize-lines: 1

        from pywa import WhatsApp, types
        wa = WhatsApp(...)

        @wa.on_message()
        def on_message(_: WhatsApp, msg: types.Message):
            msg.reply("Hello!")

    .. code-block:: python
        :emphasize-lines: 1

        from pywa_async import WhatsApp, types
        wa = WhatsApp(...)

        @wa.on_message()
        async def on_message(_: WhatsApp, msg: types.Message):
            await msg.reply("Hello!")

.. autoclass:: WhatsApp()
    :members: __init__

The available methods are:

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Category
     - Methods
   * - Sending messages
     - :meth:`~WhatsApp.send_message`,
       :meth:`~WhatsApp.send_image`,
       :meth:`~WhatsApp.send_video`,
       :meth:`~WhatsApp.send_audio`,
       :meth:`~WhatsApp.send_document`,
       :meth:`~WhatsApp.send_location`,
       :meth:`~WhatsApp.send_contact`,
       :meth:`~WhatsApp.send_sticker`,
       :meth:`~WhatsApp.send_template`,
       :meth:`~WhatsApp.send_catalog`,
       :meth:`~WhatsApp.send_product`,
       :meth:`~WhatsApp.send_products`,
       :meth:`~WhatsApp.send_reaction`,
       :meth:`~WhatsApp.remove_reaction`,
       :meth:`~WhatsApp.mark_message_as_read`
   * - Media
     - :meth:`~WhatsApp.upload_media`,
       :meth:`~WhatsApp.download_media`,
       :meth:`~WhatsApp.get_media_url`
   * - Templates
     - :meth:`~WhatsApp.create_template`
   * - Flows
     - :meth:`~WhatsApp.create_flow`,
       :meth:`~WhatsApp.update_flow_metadata`,
       :meth:`~WhatsApp.update_flow_json`,
       :meth:`~WhatsApp.publish_flow`,
       :meth:`~WhatsApp.delete_flow`,
       :meth:`~WhatsApp.deprecate_flow`,
       :meth:`~WhatsApp.get_flow`,
       :meth:`~WhatsApp.get_flows`,
       :meth:`~WhatsApp.get_flow_assets`
   * - Business profile
     - :meth:`~WhatsApp.get_business_profile`,
       :meth:`~WhatsApp.get_business_phone_number`,
       :meth:`~WhatsApp.update_business_profile`
       :meth:`~WhatsApp.update_conversational_automation`
       :meth:`~WhatsApp.set_business_public_key`
   * - Commerce
     - :meth:`~WhatsApp.get_commerce_settings`,
       :meth:`~WhatsApp.update_commerce_settings`
   * - Server
     - :meth:`~WhatsApp.webhook_update_handler`,
       :meth:`~WhatsApp.webhook_challenge_handler`,
       :meth:`~WhatsApp.get_flow_request_handler`

.. toctree::
    client_reference
    api_reference
