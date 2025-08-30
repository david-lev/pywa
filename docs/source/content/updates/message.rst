Message
=======

.. currentmodule:: pywa.types

The :class:`Message` type is used to represent incoming messages from WhatsApp user.


.. autoclass:: Message()
    :members: media, is_reply, has_media, download_media, copy

----------------

.. autoclass:: MessageType()

----------------

.. autoclass:: User()
    :members: block, unblock

----------------

.. autoclass:: Image()
    :show-inheritance:

.. autoclass:: Video()
    :show-inheritance:

.. autoclass:: Audio()
    :show-inheritance:

.. autoclass:: Document()
    :show-inheritance:

.. autoclass:: Sticker()
    :show-inheritance:

----------------

.. autoclass:: Reaction()
    :members: is_removed

.. autoclass:: Location()
    :members: current_location, in_radius

.. autoclass:: Contact()
    :members: as_vcard, Name, Phone, Email, Url, Address, Org

.. autoclass:: Product()
    :members: total_price

.. autoclass:: Order()
    :members: total_price

.. autoclass:: Referral()

----------------

.. autoclass:: Metadata()


.. autoclass:: ReplyToMessage()


.. autoclass:: ReferredProduct()
