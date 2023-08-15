🔌 Client
===========

.. currentmodule:: pywa.client


The :class:`~WhatsApp` client has two responsibilities. Sending messages & handling updates. You can use both or only one of them.

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
   * - Business profile
     - :meth:`~WhatsApp.get_business_profile`,
       :meth:`~WhatsApp.update_business_profile`
   * - Commerce
     - :meth:`~WhatsApp.get_commerce_settings`,
       :meth:`~WhatsApp.update_commerce_settings`

.. toctree::
    client_reference
    api_reference
