Media
======

.. currentmodule:: pywa.types

.. autoclass:: Image()

.. autoclass:: Video()

.. autoclass:: Audio()

.. autoclass:: Document()

.. autoclass:: Sticker()

--------------------------------

**Every media type has the following properties and methods:**

.. currentmodule:: pywa.types.media

.. automethod:: Media.get_media_url
.. automethod:: Media.download
.. autoproperty:: BaseUserMedia.extension
.. automethod:: BaseUserMedia.from_flow_completion

----------------

.. currentmodule:: pywa.types

.. autoclass:: MediaUrlResponse()
    :members: download
