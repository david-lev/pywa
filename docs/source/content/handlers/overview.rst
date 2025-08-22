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

- `ngrok <https://ngrok.com/>`_
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

Registering Callback Functions
------------------------------

To handle incoming updates, you must **register callback functions**.
These functions are called whenever WhatsApp sends an update.

A callback function must accept two arguments:

- The WhatsApp client object (:class:`~pywa.client.WhatsApp`)
- The update object (:class:`~pywa.types.Message`, :class:`~pywa.types.CallbackButton`, etc.)

**Example:**

.. code-block:: python
    :emphasize-lines: 3, 6

    from pywa import WhatsApp, types

    def echo_ok(client: WhatsApp, msg: types.Message):
        msg.reply("Ok")

    def react_to_button(client: WhatsApp, clb: types.CallbackButton):
        clb.react("❤️")

Once defined, you can register callbacks in two main ways:



Using decorators
^^^^^^^^^^^^^^^^

The simplest approach is with the ``on_...`` decorators such as :meth:`~pywa.client.WhatsApp.on_message`, :meth:`~pywa.client.WhatsApp.on_callback_button` etc.

.. code-block:: python
    :caption: main.py
    :linenos:
    :emphasize-lines: 7, 11

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

    If you don’t have access to the client instance (e.g., in a module where you define handlers), you can register handlers **directly on the WhatsApp class**.

    Example:

    .. code-block:: python
        :caption: my_handlers.py
        :linenos:

        from pywa import WhatsApp, types
        from fastapi import FastAPI

        fastapi_app = FastAPI()
        wa = WhatsApp(..., server=fastapi_app)

        @WhatsApp.on_message  # Register with the class itself
        def handle_message(client: WhatsApp, msg: types.Message):
            print(msg)

    Then load the handlers in your main file:

    .. code-block:: python
        :caption: main.py
        :linenos:
        :emphasize-lines: 4, 8

        from pywa import WhatsApp
        import my_handlers  # Import the module with your handlers

        wa = WhatsApp(..., handlers_modules=[my_handlers])

        # Or dynamically:
        wa = WhatsApp(...)
        wa.load_handlers_modules(my_handlers)


Using ``Handler`` objects
^^^^^^^^^^^^^^^^^^^^^^^^^^

For larger projects, or when you need to register handlers dynamically, you can wrap callback functions in ``Handler`` objects and add them via :meth:`~pywa.client.WhatsApp.add_handlers`.

**Example:**

.. code-block:: python
    :caption: my_handlers.py
    :linenos:

    from pywa import WhatsApp, types

    def handle_message(client: WhatsApp, msg: types.Message):
        print(msg.text)

    def handle_callback_button(client: WhatsApp, clb: types.CallbackButton):
        print(clb.data)

.. code-block:: python
    :caption: main.py
    :linenos:
    :emphasize-lines: 3, 9-10

    from pywa import WhatsApp, handlers
    from fastapi import FastAPI
    import my_handlers  # Import the module with your handlers

    fastapi_app = FastAPI()
    wa = WhatsApp(..., server=fastapi_app)

    wa.add_handlers(
        handlers.MessageHandler(callback=my_handlers.handle_message),
        handlers.CallbackButtonHandler(callback=my_handlers.handle_callback_button),
    )

.. code-block:: bash
    :caption: Terminal

    fastapi dev main.py


Available Handlers
-------------------

.. list-table::
   :widths: 20 20 60
   :header-rows: 1

   * - Decorator
     - Handler
     - Update type
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
-----------------

You can filter incoming updates by passing filters to your handlers.
This is useful when you only want to react to specific types of messages.

.. code-block:: python
    :caption: main.py
    :linenos:
    :emphasize-lines: 5

    from pywa import WhatsApp, types, filters

    wa = WhatsApp(...)

    @wa.on_message(filters.text)  # Only handle text messages
    def echo(client: WhatsApp, msg: types.Message):
        msg.reply(text=msg.text)  # msg.text is guaranteed to exist here

.. tip::

    Explore the :mod:`~pywa.filters` module for built-in filters,
    or create your own. See more in the `filters guide <../filters/overview.html>`_.


Using listeners instead of handlers
------------------------------------

Handlers are best for **entry points** in your app (e.g., commands or button clicks).
When you need to collect additional input from the user (like their age or address),
you can use **listeners** instead of registering a new handler at runtime.

.. code-block:: python
    :caption: main.py
    :linenos:
    :emphasize-lines: 7

    from pywa import WhatsApp, types, filters

    wa = WhatsApp(...)

    @wa.on_message(filters.command("start"))
    def start(_: WhatsApp, msg: types.Message):
        age = msg.reply("Hello! What's your age?").wait_for_reply(filters.text).text
        ...

.. note::

    Read more about listeners in the `listeners guide <../listeners/overview.html>`_.


Controlling handler flow
-------------------------

By default, once a handler processes an update, no other handlers are called.

.. code-block:: python
    :caption: main.py
    :linenos:
    :emphasize-lines: 8

    from pywa import WhatsApp, types

    wa = WhatsApp(...)

    @wa.on_message
    def handle_message(client: WhatsApp, msg: types.Message):
        print(msg)
        # No further handlers will run

    @wa.on_message
    def handle_message2(client: WhatsApp, msg: types.Message):
        print(msg)

.. tip::

    Handlers run in the order they’re registered, unless you set a ``priority``.
    A lower number means higher priority:

    .. code-block:: python
        :caption: main.py
        :linenos:

        from pywa import WhatsApp, types

        wa = WhatsApp(...)

        @wa.on_message(priority=1)
        def first(client: WhatsApp, msg: types.Message):
            print("First:", msg)

        @wa.on_message(priority=2)  # Will run before the previous handler
        def second(client: WhatsApp, msg: types.Message):
            print("Second:", msg)

You can change the default behavior by enabling ``continue_handling`` when creating the client:

.. code-block:: python
    :caption: main.py
    :linenos:
    :emphasize-lines: 1

    wa = WhatsApp(..., continue_handling=True)

    @wa.on_message
    def handler(client: WhatsApp, msg: types.Message):
        print(msg)
        # The next handler WILL also run

You can also decide per-message inside a handler by using
:meth:`~pywa.types.base_update.BaseUpdate.stop_handling` or
:meth:`~pywa.types.base_update.BaseUpdate.continue_handling`:

.. code-block:: python
    :caption: main.py
    :linenos:
    :emphasize-lines: 9, 11

    from pywa import WhatsApp, types, filters

    wa = WhatsApp(...)

    @wa.on_message(filters.text)
    def handle_message(client: WhatsApp, msg: types.Message):
        print(msg)
        if msg.text == "stop":
            msg.stop_handling()       # Stop further handlers
        else:
            msg.continue_handling()   # Allow further handlers


Validating updates
------------------

WhatsApp `recommends <https://developers.facebook.com/docs/graph-api/webhooks/getting-started#event-notifications>`_
validating updates using the ``X-Hub-Signature-256`` header.
This ensures the update was really sent by WhatsApp.

To enable validation, pass your ``app_secret`` when creating the client:

.. code-block:: python
    :caption: main.py
    :linenos:
    :emphasize-lines: 4

    from pywa import WhatsApp

    wa = WhatsApp(
        validate_updates=True,  # Enabled by default
        app_secret="xxxx",
        ...
    )

If the signature is invalid, pywa automatically responds with
``HTTP 401 Unauthorized``.

You can disable validation by setting ``validate_updates=False``.

.. toctree::
    handler_decorators
    handler_objects
