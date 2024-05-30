🎛️ Handlers
==================
.. currentmodule:: pywa.handlers

To handle the updates from WhatsApp, you need a way to receive them. This is done by starting a web server that
will receive the updates from WhatsApp and then call your callback function to handle them.


To allow maximum flexibility, ``pywa`` does not start the server. This allows the server to be
started independently with the desired configurations without any need for pywa to know them.
All pywa does is register a route that will handle the incoming updates from WhatsApp.
This means that you can use the same server to handle other parts of your application without any limitation from pywa.

In order for WhatsApp to send the updates to your server, you need a callback url.

The callback url must be a public, secure (HTTPS) url that points to your server (or your local machine if you are
testing locally). You can use a service like `ngrok <https://ngrok.com/>`_ , `localtunnel <https://localtunnel.github.io/www/>`_
or `serveo <https://serveo.net/>`_ to create a secure tunnel to which WhatsApp can send the updates. These services
will give you a public url that points to your machine (where you run the code).

Here is an example using ngrok (https://ngrok.com/download)

- You will get screen with the public url that points to your machine (The "Forwarding" line)

.. code-block:: bash

    ngrok http 8000


Once you have a public url, You need to register it. This can be done two ways:

* Automatically by pywa
* Manually in the WhatsApp App Dashboard

Automatically registering the callback url
__________________________________________

This is the easiest way to register the callback url. All you need to do is to pass the url to the ``callback_url`` argument
when initializing the WhatsApp client and ``pywa`` will automatically register the url, and handle the verification request
for you.

This method requires the ID and the secret of the WhatsApp app.
See `Here <https://developers.facebook.com/docs/development/create-an-app/app-dashboard/basic-settings/>`_ how to get them.

- Example using Flask

.. toggle::

    - Install `Flask <https://flask.palletsprojects.com/>`_ (``pip3 install -U "pywa[flask]"``):

    .. code-block:: python
        :caption: main.py
        :emphasize-lines: 9, 10, 11, 12, 13

        from flask import Flask
        from pywa import WhatsApp

        flask_app = Flask(__name__)

        wa = WhatsApp(
            phone_id='1234567890',
            token='xxxxxx',
            server=flask_app,
            callback_url='https://12345678.ngrok.io',
            verify_token='XYZ123',
            app_id=123456,
            app_secret='xxxxxx'
        )

        ... # register the handlers

        if __name__ == '__main__':
            # start the server with flask or gunicorn, waitress, etc.
            flask_app.run(port=8000)

    The port that flask is running on (``8000`` in the example above) must be the same port that the callback url is listening on (e.g. ``ngrok http 8000``).

- Example using FastAPI

.. toggle::

    - Install `FastAPI <https://fastapi.tiangolo.com/>`_ (``pip3 install -U "pywa[fastapi]"``):

    .. code-block:: python
        :caption: main.py
        :emphasize-lines: 10, 11, 12, 13, 14

        import uvicorn
        from fastapi import FastAPI
        from pywa import WhatsApp

        fastapi_app = FastAPI()

        wa = WhatsApp(
            phone_id='1234567890',
            token='xxxxxx',
            server=fastapi_app,
            callback_url='https://12345678.ngrok.io',
            verify_token='XYZ123',
            app_id=123456,
            app_secret='xxxxxx'
        )

        ... # register the handlers

        if __name__ == '__main__':
            # start the server with
            uvicorn.run(fastapi_app, port=8000)

    The port that fastapi is running on (``8000`` in the example above) must be the same port that the callback url is listening on (e.g. ``ngrok http 8000``).


--------------------------

Registering the callback url manually in the WhatsApp App Dashboard
___________________________________________________________________

In this method, pywa will not register the callback url for you. Instead, pywa will assume that you have already registered
an callback url, or that you will register one AFTER you start the server.

If you already have callback url that points to your server, you just need to start the server (on the same port that
the callback url is listening on).

If not, you will need to register a callback url manually in the WhatsApp App Dashboard, And this need to be done
AFTER you start the server, so pywa can handle the verification request from WhatsApp.

So, start the server:

- Example using Flask

.. toggle::

    - Install `Flask <https://flask.palletsprojects.com/>`_ (``pip3 install -U "pywa[flask]"``):

    .. code-block:: python
        :caption: main.py
        :emphasize-lines: 9, 10

        from flask import Flask
        from pywa import WhatsApp

        flask_app = Flask(__name__)

        wa = WhatsApp(
            phone_id='1234567890',
            token='xxxxxx',
            server=flask_app,
            verify_token='XYZ123',
        )

        ... # register the handlers

        if __name__ == '__main__':
            # start the server with flask or gunicorn, waitress, etc.
            flask_app.run(port=8000)

    The port that flask is running on (``8000`` in the example above) must be the same port that the callback url is listening on (e.g. ``ngrok http 8000``).

- Example using FastAPI

.. toggle::

    - Install `FastAPI <https://fastapi.tiangolo.com/>`_ (``pip3 install -U "pywa[fastapi]"``):

    .. code-block:: python
        :caption: main.py
        :emphasize-lines: 10, 11

        import uvicorn
        from fastapi import FastAPI
        from pywa import WhatsApp

        fastapi_app = FastAPI()

        wa = WhatsApp(
            phone_id='1234567890',
            token='xxxxxx',
            server=fastapi_app,
            verify_token='XYZ123',
        )

        ... # register the handlers

        if __name__ == '__main__':
            # start the server with
            uvicorn.run(fastapi_app, port=8000)

    The port that fastapi is running on (``8000`` in the example above) must be the same port that the callback url is listening on (e.g. ``ngrok http 8000``).

Then, register the callback url in the WhatsApp App Dashboard.

The registration can be done in the ``App Dashboard > WhatsApp > Configuration > Callback URL``. You need to enter the webhook url
and the verify token that you used when initializing the WhatsApp client.

.. toggle::

    .. image:: https://user-images.githubusercontent.com/42866208/260836608-aae9f5c2-0088-4332-9f92-78ce8917be56.png
        :width: 100%
        :alt: WhatsApp webhook configuration

.. important::

    When registering the callback url manually, you must subscribe to webhook fields in your webhook settings. Otherwise, you will not receive any updates.
    To enable it, go to your app dashboard, click on the ``Webhooks`` tab (Or the ``Configuration`` tab > ``Webhook fields``).
    Then, subscribe to the fields you want to receive.

    The current supported fields are:
        - ``messages`` (all user related updates)
        - ``message_template_status_update`` (template got approved, rejected, etc.)

    You can subscribe to all the other fields, but they will not be handled by pywa, they can still be handled manually by
    registering a callback for the :meth:`~pywa.client.WhatsApp.on_raw_update` decorator (or the :class:`RawUpdateHandler` handler).

    .. toggle::

        .. image:: ../../../../_static/guides/webhook-fields.webp
           :width: 600
           :alt: Subscribe to webhook fields
           :align: center

If everything is correct, WhatsApp will start sending the updates to the webhook url.

--------------------------

Registering a callback function
-------------------------------

To handle the incoming updates, you need to register a callback function. This function will be called whenever an update
is received from WhatsApp.

.. tip::
    :class: note

    A callback function can be both a synchronous or an asynchronous function.

    .. code-block:: python
        :emphasize-lines: 1

        from pywa import WhatsApp

        wa = WhatsApp(...)

        @wa.on_message()
        async def handle_message(client: WhatsApp, message: Message):
            print(message)



A callback function is a function that takes two (positional) arguments:
    - The WhatsApp client object (:class:`~pywa.client.WhatsApp`)
    - The update object (:class:`~pywa.types.Message`, :class:`~pywa.types.CallbackButton`, etc.)

Here is an example of a callback function that prints messages

.. code-block:: python
    :emphasize-lines: 1, 4

    def print_message(client: WhatsApp, msg: Message):
        print(msg)

    def react_to_button(client: WhatsApp, clb: CallbackButton):
        clb.react('❤️')

Once you define the callback function, you have two ways to register it:

Using decorators
^^^^^^^^^^^^^^^^

The easiest way to register a callback function is to use the ``on_message`` and the other ``on_...`` decorators:

.. code-block:: python

    from pywa import WhatsApp
    from pywa.types import Message, CallbackButton
    from flask import Flask

    flask_app = Flask(__name__)
    wa = WhatsApp(..., server=flask_app)

    @wa.on_message()
    def handle_message(client: WhatsApp, message: Message):
        print(message)


    @wa.on_callback_button()
    def handle_callback_button(client: WhatsApp, clb: CallbackButton):
        print(clb.data)

    if __name__ == '__main__':
        flask_app.run(port=8000)  # start the server


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
    from flask import Flask

    flask_app = Flask(__name__)
    wa = WhatsApp(..., server=flask_app)

    wa.add_handlers(
        MessageHandler(handle_message),
        CallbackButtonHandler(handle_callback_button)
    )

    if __name__ == '__main__':
        flask_app.run(port=8000)  # start the server

.. seealso::

    See how to filter updates in `Filters <filters/overview.html>`_.


Available handlers
__________________

.. list-table::
   :widths: 20 20 60
   :header-rows: 1

   * - Decorator
     - Handler
     - The type of the update
   * - :meth:`~pywa.client.WhatsApp.on_message`
     - :class:`MessageHandler`
     - :class:`~pywa.types.message.Message`
   * - :meth:`~pywa.client.WhatsApp.on_callback_button`
     - :class:`CallbackButtonHandler`
     - :class:`~pywa.types.callback.CallbackButton`
   * - :meth:`~pywa.client.WhatsApp.on_callback_selection`
     - :class:`CallbackSelectionHandler`
     - :class:`~pywa.types.callback.CallbackSelection`
   * - :meth:`~pywa.client.WhatsApp.on_flow_completion`
     - :class:`FlowCompletionHandler`
     - :class:`~pywa.types.flows.FlowCompletion`
   * - :meth:`~pywa.client.WhatsApp.on_flow_request`
     - :class:`FlowRequestHandler`
     - :class:`~pywa.types.flows.FlowRequest`
   * - :meth:`~pywa.client.WhatsApp.on_message_status`
     - :class:`MessageStatusHandler`
     - :class:`~pywa.types.message_status.MessageStatus`
   * - :meth:`~pywa.client.WhatsApp.on_template_status`
     - :class:`TemplateStatusHandler`
     - :class:`~pywa.types.template.TemplateStatus`
   * - :meth:`~pywa.client.WhatsApp.on_chat_opened`
     - :class:`ChatOpenedHandler`
     - :class:`~pywa.types.chat_opened.ChatOpened`
   * - :meth:`~pywa.client.WhatsApp.on_raw_update`
     - :class:`RawUpdateHandler`
     - :class:`dict`

.. toctree::
    handler_decorators
    handler_objects
