🔢 Calculator WhatsApp Bot
==========================

This is a simple calculator bot for WhatsApp. It can perform basic arithmetic operations on integers.

Usage:

>>> 1 + 2
>>> 1 - 2
>>> 1 * 2
>>> 1 / 2


1. Initialize the client:

.. code-block:: python

    from pywa import WhatsApp
    from flask import Flask

    flask_app = Flask(__name__)

    wa = WhatsApp(
        phone_number='your_phone_number',
        token='your_token',
        server=flask_app,
        verify_token='xyzxyz',
    )


2. Register a handler for incoming text messages:

.. code-block:: python
    :linenos:

    import re
    from pywa.types import Message
    from pywa.filters import text

    pattern = re.compile(r'^(\d+)\s*([+*/-])\s*(\d+)$')

    @wa.on_message(text.regex(pattern))
    def calculator(_: WhatsApp, msg: Message):
        a, op, b = re.match(pattern, msg.text).groups()
        a, b = int(a), int(b)
        match op:
            case '+':
                result = a + b
            case '-':
                result = a - b
            case '*':
                result = a * b
            case '/':
                try:
                    result = a / b
                except ZeroDivisionError:
                    msg.react('❌')
                    msg.reply('Division by zero is not allowed')
                    return
            case _:
                msg.react('❌')
                msg.reply('Unknown operator')
                return
        msg.reply(f'{a} {op} {b} = *{result}*')

3. Run the server:

.. code-block:: python

    flask_app.run()
