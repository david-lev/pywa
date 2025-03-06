#!/usr/bin/env python3
"""
Example of using named parameters with WhatsApp templates in PyWa.

This example demonstrates how to use named parameters when sending WhatsApp templates.
Named parameters allow you to reference template variables by name rather than position,
which can be more maintainable for complex templates.
"""

from pywa import WhatsApp
from pywa.types import Template


def main():
    # Initialize WhatsApp client
    # Replace with your actual credentials
    wa = WhatsApp(
        phone_id="YOUR_PHONE_ID",
        token="YOUR_TOKEN"
    )
    
    # Example 1: Using named parameters directly with TextValue
    print("Example 1: Using named parameters with TextValue")
    template1 = Template(
        name="order_confirmation",
        language=Template.Language.ENGLISH_US,
        body=[
            # Using named parameters by setting the parameter_name attribute
            Template.TextValue(value="John Doe", parameter_name="customer_name"),
            Template.TextValue(value="123456789", parameter_name="order_id"),
            Template.TextValue(value="March 15, 2025", parameter_name="delivery_date"),
        ]
    )
    
    # Print the template dictionary to see how named parameters are structured
    print(f"Template with named parameters: {template1.to_dict()}\n")
    
    # Example 2: Using named parameters with currency
    print("Example 2: Using named parameters with currency")
    template2 = Template(
        name="payment_confirmation",
        language=Template.Language.ENGLISH_US,
        body=[
            Template.TextValue(value="John Doe", parameter_name="customer_name"),
            # Currency with named parameter
            Template.Currency(
                fallback_value="$100.00",
                code="USD",
                amount_1000=100000,
                parameter_name="payment_amount"
            ),
            Template.DateTime(
                fallback_value="March 15, 2025",
                parameter_name="payment_date"
            ),
        ]
    )
    
    # Print the template dictionary
    print(f"Template with named currency parameter: {template2.to_dict()}\n")
    
    # Example 3: Mixing named and positional parameters (not recommended)
    # Note: WhatsApp API doesn't support mixing named and positional parameters
    # in the same component, this is just to demonstrate how PyWa handles it
    print("Example 3: Mixing named and positional parameters (not recommended)")
    template3 = Template(
        name="mixed_parameters",
        language=Template.Language.ENGLISH_US,
        body=[
            # Named parameter
            Template.TextValue(value="John Doe", parameter_name="customer_name"),
            # Positional parameter (no parameter_name)
            Template.TextValue(value="123456789"),
        ]
    )
    
    # Print the template dictionary
    # Note: PyWa will prioritize named parameters over positional ones
    print(f"Template with mixed parameters: {template3.to_dict()}\n")
    
    # Uncomment to actually send the template
    # recipient = "RECIPIENT_PHONE_NUMBER"  # Format: country code + phone number
    # wa.send_template(to=recipient, template=template1)


if __name__ == "__main__":
    main()
