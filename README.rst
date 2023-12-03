.. image:: https://i.imgur.com/hbGP0rW.png
  :width: 200
  :alt: PyWa Logo
.. end-logo

`PyWa <https://github.com/david-lev/pywa>`_ • Python wrapper for the WhatsApp Cloud API
########################################################################################

.. image:: https://img.shields.io/pypi/dm/pywa
    :alt: PyPI Downloads
    :target: https://pypi.org/project/pywa/

.. image:: https://badge.fury.io/py/pywa.svg
    :alt: PyPI Version
    :target: https://badge.fury.io/py/pywa

.. image:: https://img.shields.io/github/actions/workflow/status/david-lev/pywa/python-app.yml?label=Tests
    :alt: Tests
    :target: https://github.com/david-lev/pywa/actions/workflows/python-app.yml


.. image:: https://readthedocs.org/projects/pywa/badge/?version=latest&
   :target: https://pywa.readthedocs.io
   :alt: Docs

.. image:: https://img.shields.io/github/license/david-lev/pywa
    :alt: License
    :target: https://github.com/david-lev/pywa/blob/master/LICENSE

.. image:: https://www.codefactor.io/repository/github/david-lev/pywa/badge/master
   :target: https://www.codefactor.io/repository/github/david-lev/pywa/overview/master
   :alt: CodeFactor

.. image:: https://badges.aleen42.com/src/telegram.svg
   :target: https://t.me/py_wa
   :alt: Telegram

________________________

**PyWa is a Fast, Simple, Modern and easy-to-use Python framework for building WhatsApp bots using the WhatsApp Cloud API.**


📄 **Quick Documentation Index**
--------------------------------

>> `Get Started <https://pywa.readthedocs.io/en/latest/content/getting-started.html>`_
• `WhatsApp Client <https://pywa.readthedocs.io/en/latest/content/client/overview.html>`_
• `Handlers <https://pywa.readthedocs.io/en/latest/content/handlers/overview.html>`_
• `Filters <https://pywa.readthedocs.io/en/latest/content/filters/overview.html>`_
• `Updates <https://pywa.readthedocs.io/en/latest/content/updates/overview.html>`_
• `Examples <https://pywa.readthedocs.io/en/latest/content/examples/overview.html>`_

------------------------

⚡ **Features**
---------------
- 🚀 Fast and simple to use. No need to worry about the low-level details.
- 💬 Send text messages with interactive keyboards, images, videos, documents, audio, locations, contacts, etc.
- 📩 Receive messages, callbacks, message status updates, etc.
- 🔄 Built-in support for webhooks (Flask, FastAPI, etc.)
- 🔬 Filters for handling incoming updates
- 📄 Send and create templates
- ✅ Fully typed, documented and tested

------------------------

👨‍💻 **Usage**
----------------

- Create a WhatsApp client and send a message


.. code-block:: python

    from pywa import WhatsApp

    wa = WhatsApp(
        phone_id='100458559237541',
        token='xxxxxxxxxxxxxxx'
    )

    wa.send_message(
        to='9876543210',
        text='Hello from PyWa!'
    )

- Create a WhatsApp client, pass a web server app (Flask in this example) and start the webhook:

    > See `Handlers <https://pywa.readthedocs.io/en/latest/content/handlers/overview.html>`_ for more information.

.. code-block:: python

    from pywa import WhatsApp
    from flask import Flask
    from pywa.types import Message, CallbackButton, Button
    from pywa.filters import text, callback

    flask_app = Flask(__name__)
    wa = WhatsApp(
        phone_id='1234567890',
        token='xxxxxxx',
        server=flask_app,
        callback_url='https://xyz.ngrok-free.app',
        verify_token='xyz123',
        app_id=123456,
        app_secret='yyyyyy'
    )

    @wa.on_message(text.matches('Hello', 'Hi'))
    def hello(client: WhatsApp, msg: Message):
        msg.react('👋')
        msg.reply_text(
            text=f'Hello {msg.from_user.name}!',
            buttons=[
                Button(
                    title='Click me!',
                    callback_data='id:123'
                )
            ]
        )

    @wa.on_callback_button(callback.data_startswith('id'))
    def click_me(client: WhatsApp, clb: CallbackButton):
        clb.reply_text('You clicked me!')

    flask_app.run()  # Run the flask app to start the server

🎛 Installation
--------------
.. installation

- **Install using pip3:**

.. code-block:: bash

    pip3 install -U pywa

- **Install from source (the bleeding edge):**

.. code-block:: bash

    git clone https://github.com/david-lev/pywa.git
    cd pywa && pip3 install -U .

- **If you going to use the webhook features, here is shortcut to install the required dependencies:**

.. code-block:: bash

    pip3 install -U pywa[flask]
    pip3 install -U pywa[fastapi]

.. end-installation


💾 **Requirements**
--------------------

- Python 3.10 or higher - https://www.python.org

📖 **Setup and Usage**
-----------------------

See the `Documentation <https://pywa.readthedocs.io/>`_ for detailed instructions

☑️ **TODO**
------------

- Add support for Flows
- Add support for async
- Add support for more web frameworks (``Django``, ``Starlette``, etc.)
- Add support for more types of updates (``account_alerts``, ``phone_number_quality_updates``, ``template_category_updates``, etc.)
- Add more examples and guides

Feel free to open an issue if you have any suggestions. or even better - submit a PR!

📝 **License**
---------------

This project is licensed under the MIT License - see the
`LICENSE <https://github.com/david-lev/pywa/blob/master/LICENSE>`_ file for details

🔱 **Contributing**
--------------------

Contributions are welcome! Please feel free to submit a Pull Request.

🙏 **Acknowledgments**
-----------------------

- `Pyrogram <https://pyrogram.org/>`_ - For the design inspiration


.. end-readme
