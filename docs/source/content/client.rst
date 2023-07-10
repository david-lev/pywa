🔌 Client
===========

The client has two responsibilities. Sending messages & handling updates.

Sending messages
----------------

If you only need to send messages to users, you can initialize the client like this:

.. code-block:: python

    from pywa import WhatsApp

    wa = WhatsApp(token='YOUR_TOKEN', phone_id='YOUR_PHONE_ID')
    wa.send_message(to='123456789', text='Hello from pywa!')
    wa.send_image(to='123456789', image='path/to/image.jpg')

Handling updates
----------------

To handle updates, you first need to listen for them. WhatsApp will send updates to your webhook URL that you can configure
in the app dashboard.
In order to keep it simple and flexible, PyWa does not start a web server for you. Instead, you need to provide running
web server and PyWa register a route to listen for updates and pass them to your handlers.
This approach allows you to use PyWa along with your existing web server or framework without any conflicts or multiple threads.

        - Currently, only Flask and FastAPI are supported. If you need support for other frameworks, please open an issue or, even better, a PR.
        - You don't need to know how to work with Flask or FastAPI to use PyWa. The only thing you need to do is to provide a running web server. (See examples below)

Here is an example of how to use PyWa with Flask:

.. code-block:: python

    from flask import Flask
    from pywa import WhatsApp

    flask_app = Flask(__name__)

    wa = WhatsApp(
        token='YOUR_TOKEN',
        phone_id='YOUR_PHONE_ID',
        server=flask_app,
        webhook_endpoint='/pywa',
        verify_token='YOUR_VERIFY_TOKEN'
    )

    # Register your handlers

    if __name__ == '__main__':
        flask_app.run()

- flask_app: Your Flask app instance
- webhook_endpoint: The endpoint that PyWa will register to listen for updates, defaults to '/'
- verify_token: The verify token that you set in the app dashboard
