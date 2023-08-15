💬 Updates
==========



.. currentmodule:: pywa.types

In WhatsApp Cloud API, updates are sent to your webhook URL. There are lots of different types of updates,
but currently, we only support the ``messages`` field. this field contains all the user-related updates (e.g. messages, callbacks, etc.).

.. note::
    :class: dropdown

    The ``messages`` field must be enabled in your webhook settings. Otherwise, you will not receive any updates.
    To enable it, go to your app dashboard, click on the ``Webhooks`` tab. Then, subscribe to the ``messages`` field.


The supported types of updates are:

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Type
     - Description
   * - :class:`~Message`
     - A message sent by a user (text, media, order, location, etc.)
   * - :class:`~CallbackButton`
     - A callback button pressed by a user
   * - :class:`~CallbackSelection`
     - A callback selection chosen by a user
   * - :class:`~MessageStatus`
     - A message status update (e.g. delivered, seen, etc.)


.. toctree::

    message
    callback_button
    callback_selection
    message_status
