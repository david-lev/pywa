⚙️ Get Started
===============


⬇️ Installation
---------------
.. include:: ../../../README.rst
  :start-after: installation
  :end-before: end-installation

================================


Setup
=======

.. note::

    This guide will explain how to setup the WhatsApp Business API and how to use the ``pywa`` package.


Create a WhatsApp Application
=============================

    You already have an app? skip to `Setup the WhatsApp Business API <#id1>`_.

In order to use the WhatsApp Business API, you need to create a Facebook App. For that you need to have a Facebook developer account.
If you don't have one, `you can register here <https://developers.facebook.com/>`_.

After that you need to create a new app. Follow the steps below:

1. Go to `Meta for Developers > My Apps <https://developers.facebook.com/apps/>`_ and create a new app
    - Click `here <https://developers.facebook.com/apps/creation/>`_ to go directly to the app creation page

2. Select **Other** as the use case and hit next

.. toggle::

    .. image:: ../../_static/guides/create-new-app.webp
       :width: 600
       :alt: Create a new app
       :align: center

--------------------

3. Select **Business** as the app type and hit next

.. toggle::

    .. image:: ../../_static/guides/select-app-type.webp
        :width: 600
        :alt: Select app type
        :align: center

--------------------

4. Fill the app name and the email and hit create app

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

6. At this point you will be asked to select a **Meta Business Account**. If you have one - select it and hit **Next**.
Accept the terms and conditions and hit **Submit**.

.. toggle::

    .. image:: ../../_static/guides/select-meta-business-account.webp
        :width: 600
        :alt: select meta business
        :align: center

--------------------

Setup the WhatsApp Business API
===============================


    You already have **Phone ID** and **Token**? skip to `Send a Message <#id2>`_.


7. Now, in the left menu (under **Products**), expand **WhatsApp** and click on **API Setup**. The following screen will appear:

.. toggle::

    .. image:: ../../_static/guides/api-setup.webp
        :width: 600
        :alt: api setup
        :align: center

--------------------

In the top you will see a **Temporary access token**. This is the token you will use to connect to the WhatsApp Business API.
Right below it you will see the **Send and receive messages**. Below it you will see the **Phone number ID**. This is the ID
of the phone number you will use to send and receive messages. You will need to use them in the next step.

.. note::

    The **Temporary access token** is valid for 24 hours. After that you will need to generate a new one.
        - Learn `how to create a permanent token <https://developers.facebook.com/docs/whatsapp/business-management-api/get-started>`_.


.. attention::

    If you haven't connected a real phone number to your app, you have the option to use a test phone number.
    This is a phone number that is provided by Meta and can be used for testing purposes only. You can send messages
    up to 5 different numbers and you must authenticate every one of them (Select the **Test number** in the ``From`` field
    and add the number you want to send the message to in the ``To`` field. Then click on **Send**. You will receive a
    6 digit code to the WhatsApp account of the number you added. Copy the code and paste it in the **Verification code** field and hit **Next**).

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
        phone_id='YOUR_PHONE_ID',
        token='YOUR_TOKEN'
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

- The `WhatsApp <client/overview.html>`_ Client: is the core of the package. It is used to send and receive messages and media, handle orders, manage the business profile and settings and more.

- The `Handlers <handlers/overview.html>`_ are used to handle incoming messages and events. This way you can register a handler to a specific event and handle it.

- The `Filters <filters/overview.html>`_ section will explain how to provide filters to the handlers. Filters are used to filter the incoming messages and events. For example, you can register a handler to handle all the text message that starts with ``Hello`` or ``Hi``.

- The `Updates <updates/overview.html>`_ are the incoming messages and events that the client receives. It contains the available data for each message and event. For example, the :class:`~pywa.types.message.Message` update is arrived user send a text, media, location contact and other types of messages. Every update has it's own methods and properties.

- The `errors <errors/overview.html>`_ that the client can raise. For example, if you try to send message from your test number to a number that is not in the recipients list, the client will raise a :class:`~pywa.errors.RecipientNotInAllowedList`.

- The `Examples <examples/overview.html>`_ section contains examples of how to use the package.
