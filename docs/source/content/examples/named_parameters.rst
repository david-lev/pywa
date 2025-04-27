Using Named Parameters with Templates
===================================

This example demonstrates how to use named parameters with WhatsApp templates. According to the WhatsApp Business Management API documentation, named parameters can be implemented in both the header component (with type text) and the body component.

Named Parameters in Body Components
--------------------------------

.. code-block:: python
    :caption: Using named parameters in body components
    :linenos:

    from pywa import WhatsApp
    from pywa.types import Template

    wa = WhatsApp(...)

    # Send a template message with named parameters in body
    wa.send_template(
        to="1234567890",
        template=Template(
            name="order_confirmation",
            language=Template.Language.ENGLISH_US,
            body=[
                # Using named parameters directly in Template components
                Template.TextValue(value="John Doe", parameter_name="customer_name"),
                Template.TextValue(value="123456789", parameter_name="order_id"),
                Template.TextValue(value="March 15, 2025", parameter_name="delivery_date"),
            ],
        ),
    )


Named Parameters in Header Components
---------------------------------

.. code-block:: python
    :caption: Using named parameters in header components
    :linenos:

    from pywa import WhatsApp
    from pywa.types import Template

    wa = WhatsApp(...)

    # Send a template message with named parameters in header
    wa.send_template(
        to="1234567890",
        template=Template(
            name="greeting_template",
            language=Template.Language.ENGLISH_US,
            # Named parameter in header (only works with TextValue)
            header=Template.TextValue(value="John Doe", parameter_name="customer_name"),
            body=[
                Template.TextValue(value="Welcome to our service!"),
            ],
        ),
    )

Using the Named Parameter Classes
--------------------------------

.. code-block:: python
    :caption: Using dedicated named parameter classes
    :linenos:

    from pywa import WhatsApp
    from pywa.types import Template
    from pywa.types.named_parameter import (
        NamedTextParameter,
        NamedCurrencyParameter,
        NamedDateTimeParameter
    )

    wa = WhatsApp(...)

    # Send a template message with named parameters using dedicated classes
    wa.send_template(
        to="1234567890",
        template=Template(
            name="payment_confirmation",
            language=Template.Language.ENGLISH_US,
            body=[
                # Text parameter
                NamedTextParameter(
                    parameter_name="customer_name",
                    value="John Doe"
                ),
                # Currency parameter
                NamedCurrencyParameter(
                    parameter_name="payment_amount",
                    fallback_value="$100.00",
                    code="USD",
                    amount_1000=100000
                ),
                # Date parameter
                NamedDateTimeParameter(
                    parameter_name="payment_date",
                    fallback_value="March 15, 2025"
                ),
            ],
        ),
    )

Mixed Parameters Example
-----------------------

.. code-block:: python
    :caption: Using both named and positional parameters
    :linenos:

    from pywa import WhatsApp
    from pywa.types import Template

    wa = WhatsApp(...)

    # Send a template message with both named and positional parameters
    wa.send_template(
        to="1234567890",
        template=Template(
            name="mixed_template",
            language=Template.Language.ENGLISH_US,
            body=[
                # Named parameter
                Template.TextValue(value="John Doe", parameter_name="customer_name"),
                # Positional parameter (no parameter_name specified)
                Template.TextValue(value="123456789"),
            ],
        ),
    )

    # Note: When using both named and positional parameters, named parameters
    # take precedence and are processed first, followed by positional parameters.
