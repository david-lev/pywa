💻 Command-Line Interface
==========================

Pywa includes a powerful command-line interface (CLI) that simplifies generating, serving, developing, and testing your WhatsApp applications.

The CLI is available as the ``pywa`` executable after installing the package.

⬇️ Installation
---------------

To use the web server features (the `run` and `dev` commands) of the CLI, install Pywa with the ``server`` extras:

.. code-block:: bash

    pip install "pywa[server]"

If you are using flows with automatic encryption, install the ``cryptography`` extras as well:

.. code-block:: bash

    pip install "pywa[cryptography]"

--------------------

🚀 Development and Production Servers
-------------------------------------

Pywa provides simple commands to spin up a local ASGI web server using `Uvicorn <https://www.uvicorn.org/>`_. This registers your webhook endpoints automatically and starts listening for incoming updates.

Running in Development Mode (dev)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use ``pywa dev`` to run the application with auto-reload enabled. The server will restart automatically when changes are made to your source code.

.. code-block:: bash

    pywa dev [path] [options]

By default, if you don't specify a ``path``, ``pywa dev`` will attempt to auto-discover standard application entry files in the current directory (such as ``main.py``, ``app.py``, ``wa.py``, or ``bot.py`` under the root, ``app/``, ``bot/``, ``wa/``, or ``src/`` directories).

**Examples:**

.. code-block:: bash

    # Auto-detect application entrypoint and run
    pywa dev

    # Explicitly run a specific file
    pywa dev src/main.py

    # Monitor specific directories for changes
    pywa dev --reload-dir ./src --reload-dir ./utils

Running in Production Mode (run)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use ``pywa run`` to deploy the application in production mode. In this mode, auto-reload is disabled and options for scaling worker processes are available.

.. code-block:: bash

    pywa run [path] [options]

**Examples:**

.. code-block:: bash

    # Run application in production with 4 worker processes
    pywa run main.py --workers 4

    # Run on a custom host and port
    pywa run main.py --host 0.0.0.0 --port 8080

Global Server Options
^^^^^^^^^^^^^^^^^^^^^

Both ``pywa dev`` and ``pywa run`` share the following options:

* ``path``: Optional positional argument pointing to the Python file containing the ``WhatsApp`` instance.
* ``--host <str>``: The host to bind the socket to. Default: ``127.0.0.1``.
* ``--port <int>``: The port to bind the socket to. Default: ``8000``.
* ``--app <str>``: Specify the variable name of the ``WhatsApp`` client instance within the script (e.g., if you set ``my_wa_client = WhatsApp(...)``, pass ``--app my_wa_client``). By default, Pywa auto-detects ``WhatsApp`` instances in the script. If multiple instances exist, you must specify which one to use with this option - otherwise, the first instance found will be used.
* ``--entrypoint <str>``: Explicit entrypoint string (e.g., ``main:wa``). This overrides ``path`` and ``--app``.
* ``--log-level <level>``: Set the logging level (choices: ``critical``, ``error``, ``warning``, ``info``, ``debug``, ``trace``).
* ``--ssl-keyfile <path>``: Path to an SSL key file.
* ``--ssl-certfile <path>``: Path to an SSL certificate file.

Production-only Options (``pywa run``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* ``--workers <int>``: Number of worker processes to run (this will disable the listeners feature! e.g. ``msg.wait_for_reply(...)``). Default: ``1``.
* ``--proxy-headers`` / ``--no-proxy-headers``: Enable/Disable proxy headers (``X-Forwarded-Proto``, ``X-Forwarded-For``) to populate the request's URL scheme and client IP address.
* ``--forwarded-allow-ips <str>``: Comma-separated list of IPs to trust with proxy headers. Use ``*`` to trust all IPs.
* ``--timeout-keep-alive <int>``: Close keep-alive connections if no new data is received within this timeout (in seconds).

Development-only Options (``pywa dev``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* ``--no-reload``: Disable auto-reload.
* ``--reload-dir <path>``: Directory to watch for changes (can be specified multiple times).
* ``--reload-delay <float>``: Delay between checks for code modifications.

--------------------

📁 Creating a New Project
-------------------------

You can bootstrap a new Pywa project with a basic working echo bot using the ``pywa new`` command.

.. code-block:: bash

    pywa new [options] [project]

Options
^^^^^^^

* ``--async``: Generate an asynchronous application template (using ``pywa_async``). By default, it generates a synchronous template.
* ``--out <dir>`` / ``-o <dir>``: Directory path where the ``main.py`` boilerplate file will be created. Defaults to the current directory (``.``).

**Example:**

.. code-block:: bash

    # Generate an asynchronous bot in a new folder
    pywa new --async -o ./my_new_bot

Browsing and Downloading Example Bots
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Beyond the minimal echo-bot template, Pywa ships a gallery of complete, ready-to-run example bots (order taking,
OTP verification, WhatsApp Flows, calls, groups, and more) in the
`examples <https://github.com/david-lev/pywa/tree/master/examples>`_ directory of the repository. Use
``pywa new examples`` to browse and download them without cloning the repo yourself.

.. code-block:: bash

    pywa new examples [name] [options]

Run it with no arguments to list every available example:

.. code-block:: bash

    pywa new examples

Pass a slug to download that example (as a synchronous ``pywa`` bot by default) into ``./<name>``:

.. code-block:: bash

    pywa new examples 02-order-bot

Example Options
"""""""""""""""

* ``name``: Optional positional argument — the example slug to download (from the list printed by
  ``pywa new examples``). Omit it to just list the available examples.
* ``--async``: Download the ``pywa_async`` version instead of converting it to synchronous ``pywa`` code.
* ``--out <dir>`` / ``-o <dir>``: Directory to download the example into. The example's files are placed in
  ``<dir>/<name>``. Defaults to the current directory (``.``).
* ``--ref <str>``: Git branch or tag to fetch the example from. Defaults to ``master``.

**Example:**

.. code-block:: bash

    # Download the async version of the OTP-verification bot into ./bots
    pywa new examples 04-otp-verification --async -o ./bots

--------------------

💬 Sending Messages from the Terminal
-------------------------------------

The CLI has a built-in message-sending helper which is highly useful for scripting, testing, sending notifications, or quick verification.

.. code-block:: bash

    pywa send <message_type> [options]

Authentication
^^^^^^^^^^^^^^

To send messages, you must authenticate with your WhatsApp Cloud API credentials. You can do this in two ways:

1. **Environment Variables (Recommended)**: Set ``PYWA_TOKEN`` and ``PYWA_PHONE_ID`` in your shell environment.
2. **CLI Flags**: Pass ``--token <your_token>`` and ``--phone-id <your_phone_id>`` with the commands.

Common Options
^^^^^^^^^^^^^^

Every ``pywa send`` command supports:

* ``--to <recipient...>``: One or more space-separated recipient phone numbers or IDs. (e.g. ``--to 1234567890 9876543210``).
* ``--delay <float>``: Seconds to wait between sending messages to multiple recipients (default: ``0.0``).
* ``--reply-to <message_id>``: ID of a message to reply to.
* ``--token <str>``: WhatsApp Cloud API Access Token.
* ``--phone-id <str>``: WhatsApp Phone ID.

Available Message Types
^^^^^^^^^^^^^^^^^^^^^^^

Text Message (``text``)
"""""""""""""""""""""""

Send standard text messages.

.. code-block:: bash

    pywa send text "Hello from Pywa CLI!" --to 1234567890

**Options:**
* ``--preview-url``: Enable link previews if the text contains URLs.

Location (``location``)
"""""""""""""""""""""""

Send a geographic location.

.. code-block:: bash

    pywa send location <latitude> <longitude> [options] --to 1234567890

**Example:**

.. code-block:: bash

    pywa send location 37.7749 -122.4194 --name "San Francisco" --address "CA, USA" --to 1234567890

**Options:**
* ``--name <str>``: Name of the location.
* ``--address <str>``: Address of the location.

Media Messages (Image, Video, Document, Audio, Voice, Sticker)
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Send media using a local file path, a public URL, or a Meta media ID.

.. code-block:: bash

    pywa send <media_type> <media_source> [options] --to 1234567890

**Available types & aliases:**
* ``image`` (aliases: ``img``, ``pic``)
* ``video`` (aliases: ``vid``)
* ``document`` (aliases: ``doc``)
* ``audio`` (aliases: ``aud``)
* ``voice``
* ``sticker``

**Media options:**
* ``--mime-type <str>``: Optional MIME type to specify manually.
* ``--caption <str>``: Caption to include (supported by ``image``, ``video``, and ``document``).
* ``--filename <str>``: Custom filename to display (supported by ``document``).
* ``--is-voice``: Send the audio file formatted as a voice note (supported by ``audio``).

**Examples:**

.. code-block:: bash

    # Send a document with a caption and filename
    pywa send document ./receipt.pdf --caption "Your Receipt" --filename "Receipt-1002.pdf" --to 1234567890

    # Send a video from a URL
    pywa send video https://example.com/movie.mp4 --caption "Watch this!" --to 1234567890

    # Send an image using its Meta Media ID
    pywa send image 987654321012345 --caption "ID image" --to 1234567890
