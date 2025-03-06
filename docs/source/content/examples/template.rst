Creating and Sending Template Messages
======================================

Create Template
----------------


.. code-block:: python
    :caption: Creating a template
    :linenos:

    from pywa.types import NewTemplate as NewTemp
    wa = WhatsApp(...)

    wa.create_template(
        template=NewTemp(
            name='buy_new_iphone_x',
            category=NewTemp.Category.MARKETING,
            language=NewTemp.Language.ENGLISH_US,
            header=NewTemp.Text('The New iPhone {15} is here!'),
            body=NewTemp.Body('Buy now and use the code {WA_IPHONE_15} to get {15%} off!'),
            footer=NewTemp.Footer('Powered by PyWa'),
            buttons=[
                NewTemp.UrlButton(title='Buy Now', url='https://example.com/shop/{iphone15}'),
                NewTemp.PhoneNumberButton(title='Call Us', phone_number='1234567890'),
                NewTemp.QuickReplyButton('Unsubscribe from marketing messages'),
                NewTemp.QuickReplyButton('Unsubscribe from all messages'),
            ],
        ),
    )


Create Authentication Template
------------------------------

.. code-block:: python
    :caption: Creating an authentication template
    :linenos:

    from pywa.types import NewTemplate as NewTemp
    wa = WhatsApp(...)

    wa.create_template(
        template=NewTemp(
            name='auth_with_otp',
            category=NewTemp.Category.AUTHENTICATION,
            language=NewTemp.Language.ENGLISH_US,
            body=NewTemp.AuthBody(
                code_expiration_minutes=5,
                add_security_recommendation=True,
            ),
            buttons=NewTemp.OTPButton(
                otp_type=NewTemp.OTPButton.OtpType.ZERO_TAP,
                title='Copy Code',
                autofill_text='Autofill',
                package_name='com.example.app',
                signature_hash='1234567890ABCDEF1234567890ABCDEF12345678'
            )
        ),
    )


Sending Template Messages
-------------------------

.. code-block:: python
    :caption: Sending a template message
    :linenos:

    from pywa.types import Template as Temp
    wa = WhatsApp(...)
    wa.send_template(
        to='1234567890',
        template=Temp(
            name='buy_new_iphone_x',
            language=Temp.Language.ENGLISH_US,
            header=Temp.TextValue(value='15'),
            body=[
                Temp.TextValue(value='John Doe'),
                Temp.TextValue(value='WA_IPHONE_15'),
                Temp.TextValue(value='15%'),
            ],
            buttons=[
                Temp.UrlButtonValue(value='iphone15'),
                Temp.QuickReplyButtonData(data='unsubscribe_from_marketing_messages'),
                Temp.QuickReplyButtonData(data='unsubscribe_from_all_messages'),
            ],
        ),
    )


Sending Template Messages with Named Parameters
------------------------------------------

.. code-block:: python
    :caption: Sending a template message with named parameters
    :linenos:

    from pywa.types import Template as Temp
    wa = WhatsApp(...)
    wa.send_template(
        to='1234567890',
        template=Temp(
            name='order_confirmation',
            language=Temp.Language.ENGLISH_US,
            body=[
                # Using named parameters by setting the parameter_name attribute
                Temp.TextValue(value='John Doe', parameter_name='customer_name'),
                Temp.TextValue(value='123456789', parameter_name='order_id'),
                Temp.TextValue(value='March 15, 2025', parameter_name='delivery_date'),
            ],
        ),
    )


Sending Template Messages with Named Currency and DateTime Parameters
------------------------------------------------------------------

.. code-block:: python
    :caption: Sending a template message with named currency and date parameters
    :linenos:

    from pywa.types import Template as Temp
    wa = WhatsApp(...)
    wa.send_template(
        to='1234567890',
        template=Temp(
            name='payment_confirmation',
            language=Temp.Language.ENGLISH_US,
            body=[
                Temp.TextValue(value='John Doe', parameter_name='customer_name'),
                # Currency with named parameter
                Temp.Currency(
                    fallback_value='$100.00',
                    code='USD',
                    amount_1000=100000,
                    parameter_name='payment_amount'
                ),
                Temp.DateTime(
                    fallback_value='March 15, 2025',
                    parameter_name='payment_date'
                ),
            ],
        ),
    )


Sending Authentication Template Messages
----------------------------------------

.. code-block:: python
    :caption: Sending an authentication template message
    :linenos:

    from pywa.types import Template as Temp
    wa = WhatsApp(...)
    wa.send_template(
        to='1234567890',
            template=Temp(
            name='auth_with_otp',
            language=Temp.Language.ENGLISH_US,
            buttons=Temp.OTPButtonCode(code='123456'),
        ),
    )
