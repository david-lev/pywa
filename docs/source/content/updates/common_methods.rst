Common methods
================

.. currentmodule:: pywa.types.base_update

.. autoclass:: BaseUpdate()
    :members: id, raw, timestamp, shared_data, stop_handling, continue_handling, handle_again

.. autoclass:: BaseUserUpdate()
    :members: sender, recipient, message_id_to_reply,
        reply_text, reply_image, reply_video, reply_audio, reply_document, reply_location, reply_location_request,
        reply_contact, reply_sticker, reply_template, reply_catalog, reply_product, reply_products, react, unreact,
        mark_as_read, indicate_typing, block_sender, unblock_sender, call
