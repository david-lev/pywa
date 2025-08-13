🎛️ Handlers
==================

.. currentmodule:: pywa.handlers

To process updates from WhatsApp, your application needs to receive **incoming webhooks**.
This is done by running a web server that listens for requests from WhatsApp and passes them to your handlers.

**Why pywa Doesn’t Start the Server?**

``pywa`` is designed for **maximum flexibility** — it does not run the server for you.
Instead, it only registers the route that will handle incoming updates.

This means you can:

- Use any web framework you like.
- Configure your server however you want.
- Serve other parts of your app alongside ``pywa`` without restrictions.

.. note::

    Pywa has built-in support for FastAPI and Flask, but you can use any framework that supports handling HTTP requests.

Setting Up a Callback URL
-------------------------
For WhatsApp to send updates to your server, you must provide a **callback URL** — a public, secure (``HTTPS``) endpoint that points to your running server.

If you’re developing locally, you can use tunneling services like:

- `grok <https://ngrok.com/>`_
- `Cloudflare Tunnel <https://developers.cloudflare.com/pages/how-to/preview-with-cloudflare-tunnel/>`_
- `localtunnel <https://localtunnel.github.io/www/>`_

These create a secure, public URL that forwards traffic to your local machine.

Example using ngrok:

.. code-block:: bash
    :caption: Terminal

    ngrok http 8080

Once you have a public URL, you must **register it** with WhatsApp — either automatically (via pywa) or manually (via the WhatsApp App Dashboard).

Option 1: Automatic Callback URL Registration
---------------------------------------------
This is the simplest method — ``pywa`` will:

- Register your callback URL with WhatsApp.
- Handle the verification request for you.

**Requirements:**

- Your WhatsApp App **ID** and **Secret** (unless you’re setting callback_url_scope to ``PHONE`` or ``WABA``).
  See `Facebook docs <https://developers.facebook.com/docs/development/create-an-app/app-dashboard/basic-settings/>`_ for how to get them.

Example using FastAPI:

.. code-block:: python
    :caption: main.py
    :linenos:
    :emphasize-lines: 4, 9, 10, 11, 12, 13

    import fastapi
    from pywa import WhatsApp

    fastapi_app = fastapi.FastAPI()

    wa = WhatsApp(
        phone_id='1234567890',
        token='xxxxxx',
        server=fastapi_app,
        callback_url='https://subdomain.ngrok.io',  # Your public URL
        verify_token='XYZ123',
        app_id=123456,
        app_secret='xxxxxx'
    )

    # Register your handlers here

Run the server:

.. code-block:: bash
    :caption: Terminal

    fastapi dev main.py --port 8080

.. note::

    The port must match the one you expose via your tunnel.
    Example: ``ngrok http 8080`` means your server should run on port 8080.

Option 2: Manual Callback URL Registration
------------------------------------------
If you prefer to register the callback URL yourself:

1. Start your server so ``pywa`` can handle WhatsApp’s verification request.
2. Go to **App Dashboard > WhatsApp > Configuration**.

.. image:: ../../../../_static/guides/register-callback-url.webp
    :alt: Register Callback URL

3. Enter:

   - Your server’s public URL (e.g., ``https://subdomain.ngrok.io``).
   - The ``verify_token`` you used in your ``WhatsApp`` client initialization.

Example using FastAPI:

.. code-block:: python
    :caption: main.py
    :linenos:
    :emphasize-lines: 4, 9, 10

    import fastapi
    from pywa import WhatsApp

    fastapi_app = fastapi.FastAPI()

    wa = WhatsApp(
        phone_id='1234567890',
        token='xxxxxx',
        server=fastapi_app,
        verify_token='XYZ123',
    )

    # Register your handlers here

Run the server:

.. code-block:: bash
    :caption: Terminal

    fastapi dev main.py --port 8080

Subscribing to Webhook Fields
-----------------------------
When registering manually, you must also subscribe to webhook fields in your app settings.

Go to **App Dashboard > WhatsApp > Configuration** and scroll down to the **Webhook Fields** section.

.. image:: ../../../../_static/guides/subscribe-webhook-fields.webp
    :alt: Subscribe to Webhook Fields

Supported by pywa:

- ``messages`` – all user-related updates (messages, callbacks, message statuses)
- ``calls`` – call connect, terminate, and status updates
- ``message_template_status_update`` – template approval/rejection changes
- ``message_template_quality_update`` – template quality score changes
- ``message_template_components_update`` – template component changes (header, body, footer, buttons)
- ``template_category_update`` – template category changes
- ``user_preferences`` – user marketing preferences

You can also subscribe to other fields, but they won’t be processed automatically — use :meth:`~pywa.client.WhatsApp.on_raw_update` to handle them.

Once everything is set up correctly, WhatsApp will start sending updates to your webhook URL.

--------------------------

Registering a callback function
-------------------------------

To handle the incoming updates, you need to register a callback function. This function will be called whenever an update
is received from WhatsApp.


A callback function is a function that takes two (positional) arguments:
    - The WhatsApp client object (:class:`~pywa.client.WhatsApp`)
    - The update object (:class:`~pywa.types.Message`, :class:`~pywa.types.CallbackButton`, etc.)

Here is an example of a callback functions

.. code-block:: python
    :emphasize-lines: 3, 6

    from pywa import WhatsApp, types

    def echo_ok(client: WhatsApp, msg: types.Message):
        msg.reply('Ok')

    def react_to_button(client: WhatsApp, clb: types.CallbackButton):
        clb.react('❤️')

Once you define the callback function, you have two ways to register it:

Using decorators
^^^^^^^^^^^^^^^^

The easiest way to register a callback function is to use the ``on_message`` and the other ``on_...`` decorators:

.. code-block:: python
    :caption: main.py
    :linenos:
    :emphasize-lines: 7, 12

    from pywa import WhatsApp, types
    from fastapi import FastAPI

    fastapi_app = FastAPI()
    wa = WhatsApp(..., server=fastapi_app)

    @wa.on_message
    def handle_message(client: WhatsApp, msg: types.Message):
        print(msg)


    @wa.on_callback_button
    def handle_callback_button(client: WhatsApp, clb: types.CallbackButton):
        print(clb.data)


.. code-block:: bash
    :caption: Terminal

    fastapi dev main.py

.. tip::

    If you don't have accees to the client instance, you can register the callback functions with the WhatsApp class:

    Create module for the handlers:

    .. code-block:: python
        :caption: my_handlers.py
        :linenos:
        :emphasize-lines: 7, 12

        from pywa import WhatsApp, types
        from fastapi import FastAPI

        fastapi_app = FastAPI()
        wa = WhatsApp(..., server=fastapi_app)

        @WhatsApp.on_message  # Register the handler with the WhatsApp class
        def handle_message(client: WhatsApp, msg: types.Message):
            print(msg)


    And then load it in the main file:

    .. code-block:: python
        :caption: main.py
        :linenos:
        :emphasize-lines: 4, 9

        from pywa import WhatsApp
        from . import my_handlers  # Import the module that contains the handlers

        wa = WhatsApp(..., handlers_modules=[my_handlers])

        # Or:

        wa = WhatsApp(...)
        wa.load_handlers_modules(my_handlers)


Using ``Handler`` objects
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The other way to register a callback function is to use the :meth:`~pywa.client.WhatsApp.add_handlers` method and pass the function wrapped in
a ``Handler`` object. This is useful when your application is large and you want to separate the handlers from the
main code, or when you want to dynamically register handlers programmatically.

.. code-block:: python
    :caption: my_handlers.py
    :linenos:

    from pywa import WhatsApp, types

    def handle_message(wa: WhatsApp, msg: types.Message):
        print(message)

    def handle_callback_button(wa: WhatsApp, clb: types.CallbackButton):
        print(clb.data)


.. code-block:: python
    :caption: main.py
    :linenos:
    :emphasize-lines: 2, 9-10

    from pywa import WhatsApp, handlers
    from . import my_handlers
    from fastapi import FastAPI

    fastapi_app = FastAPI()
    wa = WhatsApp(..., server=fastapi_app)

    wa.add_handlers(
        handlers.MessageHandler(callback=my_handlers.handle_message),
        handlers.CallbackButtonHandler(callback=my_handlers.handle_callback_button),
    )


.. code-block:: bash
    :caption: Terminal

    fastapi dev main.py


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
   * - :meth:`~pywa.client.WhatsApp.on_template_status_update`
     - :class:`TemplateStatusUpdateHandler`
     - :class:`~pywa.types.templates.TemplateStatusUpdate`
   * - :meth:`~pywa.client.WhatsApp.on_template_category_update`
     - :class:`TemplateCategoryUpdateHandler`
     - :class:`~pywa.types.templates.TemplateCategoryUpdate`
   * - :meth:`~pywa.client.WhatsApp.on_template_quality_update`
     - :class:`TemplateQualityUpdateHandler`
     - :class:`~pywa.types.templates.TemplateQualityUpdate`
   * - :meth:`~pywa.client.WhatsApp.on_template_components_update`
     - :class:`TemplateComponentsUpdateHandler`
     - :class:`~pywa.types.templates.TemplateComponentsUpdate`
   * - :meth:`~pywa.client.WhatsApp.on_chat_opened`
     - :class:`ChatOpenedHandler`
     - :class:`~pywa.types.chat_opened.ChatOpened`
   * - :meth:`~pywa.client.WhatsApp.on_phone_number_change`
     - :class:`PhoneNumberChangeHandler`
     - :class:`~pywa.types.system.PhoneNumberChange`
   * - :meth:`~pywa.client.WhatsApp.on_identity_change`
     - :class:`IdentityChangeHandler`
     - :class:`~pywa.types.system.IdentityChange`
   * - :meth:`~pywa.client.WhatsApp.on_call_connect`
     - :class:`CallConnectHandler`
     - :class:`~pywa.types.calls.CallConnect`
   * - :meth:`~pywa.client.WhatsApp.on_call_terminate`
     - :class:`CallTerminateHandler`
     - :class:`~pywa.types.calls.CallTerminate`
   * - :meth:`~pywa.client.WhatsApp.on_call_status`
     - :class:`CallStatusHandler`
     - :class:`~pywa.types.calls.CallStatus`
   * - :meth:`~pywa.client.WhatsApp.on_call_permission_update`
     - :class:`CallPermissionUpdateHandler`
     - :class:`~pywa.types.calls.CallPermissionUpdate`
   * - :meth:`~pywa.client.WhatsApp.on_user_marketing_preferences`
     - :class:`UserMarketingPreferencesHandler`
     - :class:`~pywa.types.user_preferences.UserMarketingPreferences`
   * - :meth:`~pywa.client.WhatsApp.on_raw_update`
     - :class:`RawUpdateHandler`
     - :class:`dict`


Filtering updates
__________________

You can filter the updates by passing filters to the decorators. This is useful when you want to handle only specific updates.

.. code-block:: python
    :caption: main.py
    :linenos:
    :emphasize-lines: 5

    from pywa import WhatsApp, types, filters

    wa = WhatsApp(...)

    @wa.on_message(filters.text)  # Handle only text messages
    def echo(client: WhatsApp, msg: types.Message):
        # we know this handler will get only text messages, so:
        msg.reply(text=msg.text)

.. tip::

    You can find useful filters in the :mod:`~pywa.filters` module or create your own filters. read more about filters `here <../filters/overview.html>`_.


Listen instead of registering
______________________________

The handlers can be registered and removed dynamicly when the server is running. but most of the time you can use listeners instead of registering new handler.
This is because handler should be a start point of the application, like handling command, or menu click, but when you want to collect data from the user
(e.g. ask for his age or address) you can use listeners:

.. code-block:: python
    :caption: main.py
    :linenos:
    :emphasize-lines: 7, 12

    from pywa import WhatsApp, types, filters

    wa = WhatsApp(...)

    @wa.on_message(filters.command("start")
    def start(_: WhatsApp, msg: types.Message):
        age = msg.reply("Hello! What's your age?").wait_for_reply(filters.text).text
        ...

.. note::

    Read more about listeners `here <../listeners/overview.html>`_.


Stop or continue handling updates
_________________________________

When a handler is called, when it finishes, in default, the next handler will not be called.

.. code-block:: python
    :caption: main.py
    :linenos:
    :emphasize-lines: 8

    from pywa import WhatsApp, types

    wa = WhatsApp(...)

    @wa.on_message
    def handle_message(client: WhatsApp, msg: types.Message):
        print(msg)
        # The next handler will not be called

    @wa.on_message
    def handle_message2(client: WhatsApp, msg: types.Message):
        print(msg)


.. tip::
    :class: dropdown

    The order of the handlers is the order they are registered. You can override this by providing ``priority`` argument to the handler.

    .. code-block:: python
        :caption: main.py
        :linenos:

        from pywa import WhatsApp, types

        wa = WhatsApp(...)

        @wa.on_message(priority=1)
        def handle_message(client: WhatsApp, msg: types.Message):
            print(msg)

        @wa.on_message(priority=2) # this handler will be called before the previous one
        def handle_message2(client: WhatsApp, msg: types.Message):
            print(msg)


You can change this behavior by setting the ``continue_handling`` to ``True`` when initializing :class:`~pywa.client.WhatsApp`.

.. code-block:: python
    :caption: main.py
    :linenos:
    :emphasize-lines: 1

    wa = WhatsApp(..., continue_handling=True)

    @wa.on_message
    def handle_message(client: WhatsApp, msg: types.Message):
        print(msg)
        # The next handler WILL be called
    ...

You can also change this behavior inside the callback function by calling the :meth:`~pywa.types.base_update.BaseUpdate.stop_handling`
or :meth:`~pywa.types.base_update.BaseUpdate.continue_handling` methods on the update object.

.. code-block:: python
    :caption: main.py
    :linenos:
    :emphasize-lines: 9, 11

    from pywa import WhatsApp, types, filters

    wa = WhatsApp(...)

    @wa.on_message(filters.text)
    def handle_message(client: WhatsApp, msg: types.Message):
        print(msg)
        if msg.text == 'stop':
            msg.stop_handling() # The next handler will not be called
        else:
            msg.continue_handling() # The next handler will be called

    ...

Validating the updates
______________________

WhatsApp `recommends <https://developers.facebook.com/docs/graph-api/webhooks/getting-started#event-notifications>`_
validating the updates by checking the signature of the update. This is done by comparing the
signature of the update with the signature that WhatsApp sends in the ``X-Hub-Signature-256`` header of the request.

To enable this feature, you need to pass the ``app_secret`` when initializing the WhatsApp client.

.. code-block:: python
    :caption: main.py
    :linenos:
    :emphasize-lines: 4

    from pywa import WhatsApp

    wa = WhatsApp(
        validate_updates=True, # Default is True
        app_secret='xxxx',
        ...
    )

If the signature is invalid, pywa will return an ``HTTP 401 Unauthorized`` response.

The validation is done by default. You can disable this feature by setting the ``validate_updates`` to ``False`` when initializing :class:`~pywa.client.WhatsApp`.


.. toctree::
    handler_decorators
    handler_objects
