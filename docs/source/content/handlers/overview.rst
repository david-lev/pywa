🎛️ Handlers
==================
.. currentmodule:: pywa.handlers

In order to handle the incoming updates from WhatsApp, you need to do two things:
-  Start a web server that will receive the updates from the webhook
-  Register a callback functions that will be called when an update is received

Let's see how to do that.

Starting a web server
---------------------

.. role:: python(code)
   :language: bash

The first thing you need to do is to start a web server that will receive the updates from WhatsApp.

.. note::
    :class: dropdown

    To allow maximum flexibility, ``pywa`` does not initialize the server itself. This allows the server to be
    initialized independently with the desired configurations without any need for pywa to know them.
    All pywa does is register a route that will handle the incoming updates from WhatsApp.
    This means that you can use the same server to handle other parts of your software without any limitation from pywa.

You first need to register webhook url to your WhatsApp app.

.. note::
    :class: dropdown

    The webhook url must be a public, secure (HTTPS) url that points to your server (or your local machine if you are
    testing locally). You can use a service like `ngrok <https://ngrok.com/>`_ , `localtunnel <https://localtunnel.github.io/www/>`_
    or `serveo <https://serveo.net/>`_ to create a secure tunnel to which WhatsApp can send the updates. These services
    will give you a public url that points to your machine (where you run the code).


Once you have a public url, You need to start a web server that will receive the updates from WhatsApp.

Here is an example using `Flask <https://flask.palletsprojects.com/>`_ (``pip3 install flask``):

.. code-block:: python

    from flask import Flask
    from pywa import WhatsApp

    flask_app = Flask(__name__)

    wa = WhatsApp(
        phone_id='1234567890',
        token='xxxxxxxxxxxxxxxxxxxx',
        server=flask_app,
        verify_token='XYZ123
    )

    if __name__ == '__main__':
        flask_app.run(host='localhost', port=8000)  # or any other way to start a flask server (e.g. gunicorn, waitress, etc.)


And here is an example using `FastAPI <https://fastapi.tiangolo.com/>`_ (``pip3 install fastapi[uvicorn]``):

.. code-block:: python

    import uvicorn
    from fastapi import FastAPI
    from pywa import WhatsApp

    fastapi_app = FastAPI()

    wa = WhatsApp(
        phone_id='1234567890',
        token='xxxxxxxxxxxxxxxxxxxx',
        server=fastapi_app,
        verify_token='XYZ123
    )

    if __name__ == '__main__':
        uvicorn.run(fastapi_app, host='localhost', port=8000)  # or any other way to start a fastapi server

After you start the server, you can go to your WhatsApp app settings and register the webhook url.
This can be done in the ``App Dashboard > WhatsApp > Configuration > Callback URL``. You need to enter the webhook url
and the verify token that you used when initializing the WhatsApp client. When you click on ``Save``, WhatsApp will send
a ``GET`` request to the webhook url to verify that it is valid and that the verify token is correct (``pywa`` will
automatically handle this request and send the correct response to WhatsApp). If everything is correct, WhatsApp
will start sending the updates to the webhook url. In the next section we will see how to handle these updates.

.. image:: https://user-images.githubusercontent.com/42866208/260836608-aae9f5c2-0088-4332-9f92-78ce8917be56.png
    :width: 100%
    :alt: WhatsApp webhook configuration

--------------------------

Registering a callback function
-------------------------------


After you start the server and register the webhook url, you need to register a callback function that will be called
when an update is received from WhatsApp.

.. attention::
    :class: dropdown

    All callback functions must be registered before starting the server. Otherwise, the updates will not be handled!

There are two ways to register a callback function:

Using decorators
^^^^^^^^^^^^^^^^

The easiest way to register a callback function is to use the ``on_message`` and the other ``on_...`` decorators:

.. code-block:: python

    from pywa import WhatsApp
    from pywa.types import Message, CallbackButton

    wa = WhatsApp(...)  # initialize the WhatsApp client and provide web server (e.g. flask, fastapi, etc.)

    @wa.on_message()
    def handle_message(client: WhatsApp, message: Message):
        print(message)


    @wa.on_callback_button()
    def handle_callback_button(client: WhatsApp, clb: CallbackButton):
        print(clb.data)

    if __name__ == '__main__':
        # start the server


Using ``Handler`` objects
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The other way to register a callback function is to use the :meth:`~pywa.client.WhatsApp.add_handlers` method and pass the function wrapped in
a ``Handler`` object. This is useful when your application is large and you want to separate the handlers from the
main code, or when you want to dynamically register handlers programmatically.

.. code-block:: python
    :caption: my_handlers.py

    from pywa import WhatsApp
    from pywa.types import Message, CallbackButton

    def handle_message(client: WhatsApp, message: Message):
        print(message)

    def handle_callback_button(client: WhatsApp, clb: CallbackButton):
        print(clb.data)


.. code-block:: python
    :caption: main.py

    from pywa import WhatsApp
    from pywa.handlers import MessageHandler, CallbackButtonHandler
    from my_handlers import handle_message, handle_callback_button

    wa = WhatsApp(...)  # initialize the WhatsApp client and provide web server (e.g. flask, fastapi, etc.)

    wa.add_handlers(
        MessageHandler(handle_message),
        CallbackButtonHandler(handle_callback_button)
    )

    if __name__ == '__main__':
        # start the server

.. seealso::
    :class: dropdown

    See how to filter updates in `Filters <filters/overview.html>`_.


Available handlers
^^^^^^^^^^^^^^^^^^

.. list-table::
   :widths: 20 20 60
   :header-rows: 1

   * - Decorator
     - Handler
     - The type of the update
   * - :meth:`~pywa.client.WhatsApp.on_message`
     - :class:`MessageHandler`
     - :class:`~pywa.types.Message`
   * - :meth:`~pywa.client.WhatsApp.on_callback_button`
     - :class:`CallbackButtonHandler`
     - :class:`~pywa.types.CallbackButton`
   * - :meth:`~pywa.client.WhatsApp.on_callback_selection`
     - :class:`CallbackSelectionHandler`
     - :class:`~pywa.types.CallbackSelection`
   * - :meth:`~pywa.client.WhatsApp.on_message_status`
     - :class:`MessageStatusHandler`
     - :class:`~pywa.types.MessageStatus`
   * - :meth:`~pywa.client.WhatsApp.on_raw_update`
     - :class:`RawUpdateHandler`
     - :class:`dict`

.. toctree::
    handler_decorators
    handler_objects
