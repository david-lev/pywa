.. image:: https://i.imgur.com/hbGP0rW.png
  :width: 200
  :alt: PyWa Logo
.. end-logo

`PyWa <https://github.com/david-lev/pywa>`_ • Python wrapper for the WhatsApp Cloud API
######################################################################################

**THIS IS A WORK IN PROGRESS. DO NOT USE IN PRODUCTION.**


.. image:: https://img.shields.io/pypi/dm/pywa?style=flat-square
    :alt: PyPI Downloads
    :target: https://pypi.org/project/pywa/

.. image:: https://badge.fury.io/py/pywa.svg
    :alt: PyPI Version
    :target: https://badge.fury.io/py/pywa

.. image:: https://www.codefactor.io/repository/github/david-lev/pywa/badge/master
   :target: https://www.codefactor.io/repository/github/david-lev/pywa/overview/master
   :alt: CodeFactor

.. image:: https://readthedocs.org/projects/pywa/badge/?version=latest&style=flat-square
   :target: https://pywa.readthedocs.io
   :alt: Docs

.. image:: https://badges.aleen42.com/src/telegram.svg
   :target: https://t.me/py_wa
   :alt: Telegram

________________________


🎛 Installation
--------------
.. installation

- **Install using pip3:**

.. code-block:: bash

    pip3 install -U pywa

    # or if you want to use webhooks
    pip3 install -U pywa[flask]
    # or:
    pip3 install -U pywa[fastapi]

- **Install from source:**

.. code-block:: bash

    pip3 install -U git+https://github.com/david-lev/pywa.git

.. end-installation

----------------------------------------


👨‍💻 **Usage**
----------------

- Create a WhatsApp client and send a message


.. code-block:: python

    from pywa import WhatsApp

    wa = WhatsApp(phone_id='100458559237541', token='xxxxxxxxxxxxxxx')

    wa.send_message(
        to='9876543210',
        text='Hello from PyWa!'
    )

- Create a WhatsApp client, pass a Flask (or FastAPI) app and start handling incoming updates

.. code-block:: python

    from pywa import WhatsApp
    from flask import Flask
    from pywa.types import Message, CallbackButton, InlineButton
    from pywa.filters import TextFilter, CallbackFilter

    flask_app = Flask(__name__)
    wa = WhatsApp(
        phone_id='1234567890',
        token='xxxxxxxxxxxxxxx',
        server=flask_app,
        verify_token='XYZXYZ',
    )

    @wa.on_message(TextFilter.equals('Hello', 'Hi'))
    def hello(client: WhatsApp, message: Message):
        message.react('👋')
        message.reply_text(
            text='Hello from PyWa!',
            keyboard=[
                InlineButton(
                    title='Click me!',
                    callback_data='id:123'
                )
            ]
        )

    @wa.on_callback_button(CallbackFilter.data_startswith('id:'))
    def click_me(client: WhatsApp, clb: CallbackButton):
        clb.reply_text('You clicked me!')

    flask_app.run()  # Run the flask app to start the webhook


💾 **Requirements**
--------------------

- Python 3.10 or higher - https://www.python.org

📖 **Setup and Usage**
-----------------------

See the `Documentation <https://pywa.readthedocs.io/>`_ for detailed instructions

.. end-readme