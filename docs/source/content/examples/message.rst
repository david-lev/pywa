Sending Messages
================


Sending a text message
----------------------

.. code-block:: python
    :caption: Text message
    :linenos:

    from pywa import WhatsApp

    wa = WhatsApp(phone_id='972123456789', token='xxxxx')

    recipient = '972987654321'
    wa.send_message(to=recipient, text='Hello world!')

    # Message with link preview
    wa.send_message(
        to=recipient,
        text='PyWa Documentation: https://pywa.readthedocs.io',
        preview_url=True
    )
