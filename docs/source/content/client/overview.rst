🔌 Client
===========

.. currentmodule:: pywa.client

.. note::

    WORK IN PROGRESS


The :class:`~WhatsApp` client has two responsibilities. Sending messages & handling updates.



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
       :meth:`~WhatsApp.update_business_profile`
       :meth:`~WhatsApp.set_business_public_key`
   * - Commerce
     - :meth:`~WhatsApp.get_commerce_settings`,
       :meth:`~WhatsApp.update_commerce_settings`

.. toctree::
    client_reference
    api_reference
