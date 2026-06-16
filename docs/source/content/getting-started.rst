⚙️ Get Started
===============

This page walks you through installing pywa, creating a WhatsApp app on Meta,
and sending your first message. If you already have your **Phone ID** and **Token**,
jump straight to `Send a Message <#id2>`_.

⬇️ Installation
---------------

- **Install using pip:**

.. code-block:: bash

    pip3 install -U pywa

- **Install from source (bleeding edge):**

.. code-block:: bash

    git clone https://github.com/david-lev/pywa.git
    cd pywa && pip3 install -U .

- **For webhook features:**

.. code-block:: bash

    pip3 install -U "pywa[server]"

- **For Flow features with default encryption/decryption:**

.. code-block:: bash

    pip3 install -U "pywa[cryptography]"

================================

Create a WhatsApp Application
------------------------------

Already have a Facebook App? `Jump to Setup the App → <#id1>`_

To use the WhatsApp Cloud API, you need a Facebook App.
If you don't have a Facebook Developer account, `register here <https://developers.facebook.com/>`_.

1. Go to `Meta for Developers > My Apps <https://developers.facebook.com/apps/>`_ and create a new app.
   - Or click `here <https://developers.facebook.com/apps/create/?show_additional_prod_app_info=false>`_ to go directly to the app creation page.

2. Select **Business** as the app type and click **Next**.

.. toggle::

    .. image:: ../../_static/guides/select-app-type.webp
       :width: 600
       :alt: Select app type
       :align: center

3. Fill in the app name and email, then click **Create App**.

.. toggle::

    .. image:: ../../_static/guides/fill-app-details.webp
       :width: 600
       :alt: Fill app details
       :align: center

4. In **Add products to your app**, search for **WhatsApp** and click **Set Up**.

.. toggle::

    .. image:: ../../_static/guides/setup-whatsapp-product.webp
       :width: 600
       :alt: Setup WhatsApp product
       :align: center

5. Select a **Meta Business Account**, accept the terms, and click **Submit**.
   If you don't have a Business Account, you will need to create one.

.. toggle::

    .. image:: ../../_static/guides/select-meta-business-account.webp
       :width: 600
       :alt: Select meta business
       :align: center

--------------------

Setup the App
-------------

Already have your **Phone ID** and **Token**? `Jump to Send a Message → <#id2>`_

6. In the left menu (under **Products**), expand **WhatsApp** and click **API Setup**.

.. toggle::

    .. image:: ../../_static/guides/api-setup.webp
       :width: 600
       :alt: API setup
       :align: center

- Copy the **Temporary access token** (valid for 24h) and the **Phone number ID**.

.. note::

    Learn `how to create a permanent token <https://developers.facebook.com/docs/whatsapp/business-management-api/get-started>`_.

.. attention::

    If you haven't connected a real phone number, you can use a test number provided by Meta.
    You can send messages to up to 5 allowed numbers. Add them in the **Manage phone number list**.

    .. toggle::

        .. image:: ../../_static/guides/verify-phone-number-for-testing.webp
           :width: 600
           :alt: Test number setup
           :align: center

--------------------

Send a Message
--------------

Now that you have your ``phone_id`` and ``token``, you're ready to send messages:

.. code-block:: python

    from pywa import WhatsApp

    wa = WhatsApp(
        phone_id='YOUR_PHONE_ID',  # from API Setup
        token='YOUR_TOKEN'         # from API Setup
    )

    # Send a text message
    wa.send_message(
        to='PHONE_NUMBER_TO_SEND_TO',
        text='Hi! This message was sent from pywa!'
    )

    # Send an image
    wa.send_image(
        to='PHONE_NUMBER_TO_SEND_TO',
        image='https://www.rd.com/wp-content/uploads/2021/04/GettyImages-1053735888-scaled.jpg'
    )

.. note::

    - For **Test Numbers**, add recipients to the allowed numbers list.
    - Free-form messages can only be received if the recipient messaged your number in the last 24h.
      See `WhatsApp policy <https://business.whatsapp.com/policy>`_.

--------------------

Quick Start
-----------

Here's a brief overview of the main pywa concepts — click any link to dive deeper:

- `WhatsApp <client/overview.html>`_: The core client. Use it to send messages, manage your business
  profile, and register handlers. Everything starts here.
- `Handlers <handlers/overview.html>`_: Register callbacks that fire when a user sends a message,
  presses a button, or triggers any other update. The backbone of every bot.
- `Listeners <listeners/overview.html>`_: Wait for a user's *next* reply inline, without registering
  a separate handler. Perfect for step-by-step conversations.
- `Filters <filters/overview.html>`_: Composable conditions that decide which updates a handler
  processes. Combine them with ``&``, ``|``, and ``~`` like Python expressions.
- `Updates <updates/overview.html>`_: All the types of incoming events — messages, button clicks,
  delivery statuses, flow completions, and more.
- `Flows <flows/overview.html>`_: Build rich, multi-screen interactive WhatsApp experiences entirely
  in Python.
- `Errors <errors/overview.html>`_: How pywa surfaces API errors and how to handle them gracefully.
- `Examples <examples/overview.html>`_: Complete, runnable bots and code snippets to get inspired.
