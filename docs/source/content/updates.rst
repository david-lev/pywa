💬 Updates
==========

.. currentmodule:: pywa.types

In WhatsApp there are lots of types of updates, the most important one is ``messages`` because it contains all the messages, status updates and callbacks from the users.
In PyWa, this update split into 4 different types:

- :class:`Message`: represents a message from a user (text, image, video, etc).
- :class:`CallbackButton`: represents a callback from a user (when the user clicks on a button).
- :class:`CallbackSelection`: represents a callback from a user (when the user selects an option from selection list).
- :class:`MessageStatus`: represents a status change of message that was sent by the bot (read, delivered, etc).

------------------------------------------------------------------------------------------------------------------------

.. autoclass:: Message()
    :members:

------------------------------------------------------------------------------------------------------------------------

.. autoclass:: CallbackButton()
    :members:

------------------------------------------------------------------------------------------------------------------------

.. autoclass:: CallbackSelection()
    :members:

------------------------------------------------------------------------------------------------------------------------

.. autoclass:: MessageStatus()
    :members:

------------------------------------------------------------------------------------------------------------------------

.. currentmodule:: pywa.types.base_update

.. autoclass:: BaseUpdate()
    :members:

