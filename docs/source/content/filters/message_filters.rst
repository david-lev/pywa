Message Filters
===============

.. automodule:: pywa.filters

.. autoattribute:: pywa.filters.forwarded
.. autoattribute:: pywa.filters.forwarded_many_times
.. autoattribute:: pywa.filters.reply
.. autoattribute:: pywa.filters.has_referred_product

----------------

.. autoclass:: text
.. automethod:: text.matches
.. automethod:: text.contains
.. automethod:: text.startswith
.. automethod:: text.endswith
.. automethod:: text.regex
.. automethod:: text.length
.. automethod:: text.is_command
.. automethod:: text.command

----------------

.. autoclass:: media
.. automethod:: media.mimetypes
.. automethod:: media.extensions

.. autoclass:: image
.. autoattribute:: image.has_caption

.. autoclass:: video
.. autoattribute:: video.has_caption

.. autoclass:: audio
.. autoattribute:: audio.voice
.. autoattribute:: audio.audio

.. autoclass:: document
.. autoattribute:: document.has_caption

.. autoclass:: sticker
.. autoattribute:: sticker.animated
.. autoattribute:: sticker.static

----------------

.. autoclass:: reaction
.. autoattribute:: reaction.added
.. autoattribute:: reaction.removed
.. automethod:: reaction.emojis

----------------

.. autoclass:: location
.. autoattribute:: location.current_location
.. automethod:: location.in_radius

----------------

.. autoclass:: contacts
.. autoattribute:: contacts.has_wa
.. automethod:: contacts.count
.. automethod:: contacts.phones

----------------

.. autoclass:: order
.. automethod:: order.price
.. automethod:: order.count
.. automethod:: order.has_product

----------------

.. autoclass:: unsupported
