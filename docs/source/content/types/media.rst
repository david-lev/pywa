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

.. autoproperty:: BaseMedia.extension
.. automethod:: BaseMedia.get_media_url
.. automethod:: BaseMedia.download
.. automethod:: BaseMedia.from_flow_completion

----------------

.. currentmodule:: pywa.types

.. autoclass:: MediaUrlResponse()
    :members: download
