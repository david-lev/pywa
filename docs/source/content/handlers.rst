⚙️ Handlers
==================
.. currentmodule:: pywa.handlers

To handle incoming updates, you need to register handler functions.
Every type of update has its own handler type:

.. autoclass:: MessageHandler()
.. autoclass:: ButtonCallbackHandler()
.. autoclass:: SelectionCallbackHandler()
.. autoclass:: MessageStatusHandler()
.. autoclass:: RawUpdateHandler()
