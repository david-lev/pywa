⚙️ Get Started
===============


⬇️ Installation
---------------

- **Install using pip3:**

.. code-block:: bash

    pip3 install -U pywa

- **Install from source (the bleeding edge):**

.. code-block:: bash

    git clone https://github.com/david-lev/pywa.git
    cd pywa && pip3 install -U .

- **If you going to use the webhook features, here is shortcut to install the required dependencies:**

.. code-block:: bash

    pip3 install -U "pywa[fastapi]"
    pip3 install -U "pywa[flask]"

- **If you going to use the Flow features and want to use the default FlowRequestDecryptor and the default FlowResponseEncryptor, here is shortcut to install the required dependencies:**

.. code-block:: bash

    pip3 install -U "pywa[cryptography]"


================================


Create a WhatsApp Application
=============================

    You already have an app? skip to `Setup the App <#id1>`_.

In order to use the WhatsApp Cloud API, you need to create a Facebook App.
To do that you need a Facebook Developer account. If you don't have one, `you can register here <https://developers.facebook.com/>`_.

1. Go to `Meta for Developers > My Apps <https://developers.facebook.com/apps/>`_ and create a new app
    - Click `here <https://developers.facebook.com/apps/creation/>`_ to go directly to the app creation page

2. Select **Other** as the use case and hit **Next**

.. toggle::

    .. image:: ../../_static/guides/create-new-app.webp
       :width: 600
       :alt: Create a new app
       :align: center

--------------------

3. Select **Business** as the app type and click on **Next**

.. toggle::

    .. image:: ../../_static/guides/select-app-type.webp
        :width: 600
        :alt: Select app type
        :align: center

--------------------

4. Fill the app name and the email and hit **Create App**

.. toggle::

    .. image:: ../../_static/guides/fill-app-details.webp
        :width: 600
        :alt: Fill the app details
        :align: center

--------------------

5. In the **Add products to your app** screen, scroll down and search for **WhatsApp**. Click on **Set Up**

.. toggle::

    .. image:: ../../_static/guides/setup-whatsapp-product.webp
        :width: 600
        :alt: Setup WhatsApp product
        :align: center

--------------------

6. At this point you will be asked to select a **Meta Business Account**. If you have one - select it and hit **Next**. Accept the terms and conditions and hit **Submit**. If you don't have a Business Account, you will need to create one.

.. toggle::

    .. image:: ../../_static/guides/select-meta-business-account.webp
        :width: 600
        :alt: select meta business
        :align: center

--------------------

Setup the App
=============


    You already have **Phone ID** and **Token**? skip to `Send a Message <#id2>`_.


7. Now, in the left menu (under **Products**), expand **WhatsApp** and click on **API Setup**. The following screen will appear:

.. toggle::

    .. image:: ../../_static/guides/api-setup.webp
        :width: 600
        :alt: api setup
        :align: center

--------------------

In the top you will see a **Temporary access token**. This is the token you will use to interact with the WhatsApp Cloud API.
Right below it you will see the **Send and receive messages**. Below it you will see the **Phone number ID**. This is the ID
of the phone number you will use to send and receive messages. You will need to use both of them in the next step.

.. note::

    The **Temporary access token** is valid for 24 hours. After that you will need to generate a new one.
        - Learn `how to create a permanent token <https://developers.facebook.com/docs/whatsapp/business-management-api/get-started>`_.


.. attention::

    If you haven't connected a real phone number to your WhatsApp Business Account, you have the option to use a test phone number.
    This is a phone number that is provided by Meta and can be used for testing purposes only. You can send messages
    up to 5 different numbers and you must add them to the **Allowed Numbers** list. (Select the **Test number** in the ``From`` field
    and then in the **To** field, go to **Manage phone number list** and add the numbers you want to send messages to).

    .. toggle::

        .. image:: ../../_static/guides/verify-phone-number-for-testing.webp
            :width: 600
            :alt: test number
            :align: center

--------------------

Send a Message
==============


So now you have a ``phone id`` and a ``token``. You can use them to send messages:

.. code-block:: python

    from pywa import WhatsApp

    wa = WhatsApp(
        phone_id='YOUR_PHONE_ID',  # The phone id you got from the API Setup
        token='YOUR_TOKEN'  # The token you got from the API Setup
    )

And that's it! You are ready to send messages!

.. code-block:: python

    wa.send_message(
        to='PHONE_NUMBER_TO_SEND_TO',
        text='Hi! This message sent from pywa!'
    )

    wa.send_image(
        to='PHONE_NUMBER_TO_SEND_TO',
        image='https://www.rd.com/wp-content/uploads/2021/04/GettyImages-1053735888-scaled.jpg'
    )



.. note::

    - The ``to`` parameter must be a phone number with the country code. For example: ``+972123456789``, ``16315551234``. You can read more about the `phone number format here <https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-messages#phone-number-formats>`_.
    - If you using the **Test Number**, remember to add the recipient number to the allowed numbers list.

--------------------

Quick Start
===========

Now you can continue to the next section and learn how to use the ``pywa`` package. here is a quick overview of the package:

- The `WhatsApp <client/overview.html>`_ Client: is the core of the package. It is used to send and receive messages and media, register callbacks, manage profile and business settings and more.

- The `Handlers <handlers/overview.html>`_: Learn how to register callbacks and handle incoming updates (messages, callbacks and more).

- The `Filters <filters/overview.html>`_: Learn how to handle specific updates by applying filters and conditions (for example, handle only text messages that contains the word "Hello").

- The `Updates <updates/overview.html>`_: Learn about the different types of updates that the client can receive, their attributes and properties and how to use them.

- The `Flows <flows/overview.html>`_: Learn how to create, update and send flows.

- The `errors <errors/overview.html>`_: Learn about the different types of errors in the package and how to handle them.

- The `Examples <examples/overview.html>`_: See some examples of how to use the package.
