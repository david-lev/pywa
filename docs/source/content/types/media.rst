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

.. autoclass:: Media()
    :members: get_media_url, download, delete

.. autoproperty:: BaseUserMedia.extension
.. automethod:: BaseUserMedia.from_flow_completion

----------------

.. currentmodule:: pywa.types

.. autoclass:: MediaUrlResponse()
    :members: download
