♻️ Flows
========

.. currentmodule:: pywa.types.flows

The WhatsApp Flows are now the most exciting part of the WhatsApp Cloud API.

From `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows>`_:

    .. image:: ../../../../_static/guides/flows.webp
        :alt: WhatsApp Flows
        :width: 100%

    WhatsApp Flows is a way to build structured interactions for business messaging. With Flows, businesses can define, configure, and customize messages with rich interactions that give customers more structure in the way they communicate.

    You can use Flows to book appointments, browse products, collect customer feedback, get new sales leads, or anything else where structured communication is more natural or comfortable for your customers.


When you reading the official docs it's looks very intimidating, but in fact it's quite simple (by PyWa 😉).

    For a real world example, you can check out the `Sign up Flow Example <../examples/sign_up_flow.html>`_.

The Flows are seperated to 4 parts:

- Creating Flow
- Sending Flow
- Handling Flow requests and responding to them (Only for dynamic flow)
- Getting Flow Completion message

Creating Flow
-------------

First you need to create the flow, give it a name and set the categories by calling :meth:`~pywa.client.WhatsApp.create_flow`:
    You can also create the flows using the `WhatsApp Flow Builder <https://business.facebook.com/wa/manage/flows/>`_.

.. code-block:: python
    :linenos:

    from pywa import WhatsApp
    from pywa.types import FlowCategory

    # WhatsApp Business Account ID (WABA) is required
    wa = WhatsApp(..., business_account_id="1234567890123456")

    flow_id = wa.create_flow(
        name="My New Flow",
        categories=[FlowCategory.CUSTOMER_SUPPORT, FlowCategory.SURVEY]
    )
    print(wa.get_flow(flow_id))

    # FlowDetails(id='1234567890123456', name='My New Flow', status=FlowStatus.DRAFT, ...)

Now you can start building the flow structure.

A flow is collection of screens containing components. screens can exchange data with each other and with your server.

Flow can be static; all the components settings are predefined and no interaction is required from your server.
Or it can be dynamic; your server can respond to screen actions and determine the next screen to display (or close the flow) and the data to provide to it.

.. note::

    WORK IN PROGRESS

    I really recommend you to read the `Flow JSON Docs <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson>`_ before you continue.
    A full guide will be added soon.

Every component on the FlowJSON, has a corresponding class in :mod:`pywa.types.flows`:

.. list-table::
   :widths: 10 60
   :header-rows: 1

   * - Category
     - Types
   * - Static elements
     - :class:`TextHeading`,
       :class:`TextSubheading`,
       :class:`TextBody`,
       :class:`TextCaption`,
       :class:`Image`
   * - Collect data
     - :class:`Form`,
       :class:`TextInput`,
       :class:`TextArea`,
       :class:`RadioButtonsGroup`,
       :class:`CheckboxGroup`,
       :class:`Dropdown`,
       :class:`OptIn`,
       :class:`PhotoPicker`,
       :class:`DocumentPicker`
   * - Navigation
     - :class:`EmbeddedLink`,
       :class:`Footer`
   * - Conditional Component Rendering
     - :class:`If`,
       :class:`Switch`

here is an example of static flow:

.. toggle::

    .. code-block:: python
        :caption: simple_sign_up_flow.py
        :linenos:
        :emphasize-lines: 6, 13, 19, 25, 31, 36, 37, 38, 39, 40

        static_flow = FlowJSON(
            screens=[
                Screen(
                    id="SIGN_UP",
                    title="Finish Sign Up",
                    terminal=True,
                    layout=Layout(
                        type=LayoutType.SINGLE_COLUMN,
                        children=[
                            Form(
                                name="form",
                                children=[
                                    first_name := TextInput(
                                        name="first_name",
                                        label="First Name",
                                        input_type=InputType.TEXT,
                                        required=True,
                                    ),
                                    last_name := TextInput(
                                        name="last_name",
                                        label="Last Name",
                                        input_type=InputType.TEXT,
                                        required=True,
                                    ),
                                    email := TextInput(
                                        name="email",
                                        label="Email Address",
                                        input_type=InputType.EMAIL,
                                        required=True,
                                    ),
                                    Footer(
                                        label="Done",
                                        enabled=True,
                                        on_click_action=Action(
                                            name=FlowActionType.COMPLETE,
                                            payload={
                                                "first_name": first_name.form_ref,
                                                "last_name": last_name.form_ref,
                                                "email": email.form_ref,
                                            },
                                        ),
                                    ),
                                ],
                            )
                        ],
                    ),
                )
            ],
        )


Which is the equivalent of the following flow json:

.. toggle::

    .. code-block:: json
        :caption: simple_sign_up_flow.json
        :linenos:

        {
          "version": "3.0",
          "screens": [
            {
              "id": "SIGN_UP",
              "title": "Finish Sign Up",
              "terminal": true,
              "layout": {
                "type": "SingleColumnLayout",
                "children": [
                  {
                    "type": "Form",
                    "name": "form",
                    "children": [
                      {
                        "type": "TextInput",
                        "name": "first_name",
                        "label": "First Name",
                        "input-type": "text",
                        "required": true
                      },
                      {
                        "type": "TextInput",
                        "name": "last_name",
                        "label": "Last Name",
                        "input-type": "text",
                        "required": true
                      },
                      {
                        "type": "TextInput",
                        "name": "email",
                        "label": "Email Address",
                        "input-type": "email",
                        "required": true
                      },
                      {
                        "type": "Footer",
                        "label": "Done",
                        "on-click-action": {
                          "name": "complete",
                          "payload": {
                            "first_name": "${form.first_name}",
                            "last_name": "${form.last_name}",
                            "email": "${form.email}"
                          }
                        },
                        "enabled": true
                      }
                    ]
                  }
                ]
              }
            }
          ]
        }

And this is how it looks like on WhatsApp:

.. toggle::

    .. image:: ../../../../_static/guides/static-sign-up-screen.webp
        :alt: Static Sign Up Screen
        :width: 50%

==================


Here is example of dynamic flow:

.. toggle::

    .. code-block:: python
        :caption: dynamic_sign_up_flow.py
        :linenos:
        :emphasize-lines: 2, 3, 9, 10, 11, 12, 13, 20, 25, 27, 31, 33, 37, 43, 44, 45, 46, 47


        dynamic_flow = FlowJSON(
            data_api_version=utils.Version.FLOW_DATA_API,
            routing_model={},
            screens=[
                Screen(
                    id="SIGN_UP",
                    title="Finish Sign Up",
                    terminal=True,
                    data=[
                        first_name_helper_text := ScreenData(key="first_name_helper_text", example="Enter your first name"),
                        is_last_name_required := ScreenData(key="is_last_name_required", example=True),
                        is_email_enabled := ScreenData(key="is_email_enabled", example=False),
                    ],
                    layout=Layout(
                        type=LayoutType.SINGLE_COLUMN,
                        children=[
                            Form(
                                name="form",
                                children=[
                                    first_name := TextInput(
                                        name="first_name",
                                        label="First Name",
                                        input_type=InputType.TEXT,
                                        required=True,
                                        helper_text=first_name_helper_text.data_key,
                                    ),
                                    last_name := TextInput(
                                        name="last_name",
                                        label="Last Name",
                                        input_type=InputType.TEXT,
                                        required=is_last_name_required.data_key,
                                    ),
                                    email := TextInput(
                                        name="email",
                                        label="Email Address",
                                        input_type=InputType.EMAIL,
                                        enabled=is_email_enabled.data_key,
                                    ),
                                    Footer(
                                        label="Done",
                                        on_click_action=Action(
                                            name=FlowActionType.COMPLETE,
                                            payload={
                                                "first_name": last_name.form_ref,
                                                "last_name": last_name.form_ref,
                                                "email": email.form_ref,
                                            },
                                        ),
                                    ),
                                ],
                            )
                        ],
                    ),
                )
            ],
        )


Which is the equivalent of the following flow json:

.. toggle::

    .. code-block:: json
        :caption: dynamic_sign_up_flow.json
        :linenos:

        {
            "version": "3.0",
            "data_api_version": "3.0",
            "routing_model": {},
            "screens": [
                {
                    "id": "SIGN_UP",
                    "title": "Finish Sign Up",
                    "data": {
                        "first_name_helper_text": {
                            "type": "string",
                            "__example__": "Enter your first name"
                        },
                        "is_last_name_required": {
                            "type": "boolean",
                            "__example__": true
                        },
                        "is_email_enabled": {
                            "type": "boolean",
                            "__example__": false
                        }
                    },
                    "terminal": true,
                    "layout": {
                        "type": "SingleColumnLayout",
                        "children": [
                            {
                                "type": "Form",
                                "name": "form",
                                "children": [
                                    {
                                        "type": "TextInput",
                                        "name": "first_name",
                                        "label": "First Name",
                                        "input-type": "text",
                                        "required": true,
                                        "helper-text": "${data.first_name_helper_text}"
                                    },
                                    {
                                        "type": "TextInput",
                                        "name": "last_name",
                                        "label": "Last Name",
                                        "input-type": "text",
                                        "required": "${data.is_last_name_required}"
                                    },
                                    {
                                        "type": "TextInput",
                                        "name": "email",
                                        "label": "Email Address",
                                        "input-type": "email",
                                        "enabled": "${data.is_email_enabled}"
                                    },
                                    {
                                        "type": "Footer",
                                        "label": "Done",
                                        "on-click-action": {
                                            "name": "complete",
                                            "payload": {
                                                "first_name": "${form.first_name}",
                                                "last_name": "${form.last_name}",
                                                "email": "${form.email}"
                                            }
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                }
            ]
        }

And this is how it looks like on WhatsApp:

.. toggle::

    .. image:: ../../../../_static/guides/dynamic-sign-up-screen.webp
        :alt: Dynamic Sign Up Screen
        :width: 50%

After you have the flow json, you can update the flow with :meth:`~pywa.client.WhatsApp.update_flow_json`:

.. code-block:: python
    :linenos:

    from pywa import WhatsApp

    wa = WhatsApp(...)

    wa.update_flow_json(flow_id, flow_json=flow_json)

The ``flow_json`` argument can be :class:`FlowJSON`, a :class:`dict`, json :class:`str`, json file path or open(json_file) obj.

You can get the :class:`FlowDetails` of the flow with :meth:`~pywa.client.WhatsApp.get_flow` to see if there is validation errors needed to be fixed:

.. code-block:: python
    :linenos:

    from pywa import WhatsApp

    wa = WhatsApp(...)

    print(wa.get_flow(flow_id))

    # FlowDetails(id='1234567890123456', name='My New Flow', validation_errors=(...))

If you are working back and forth on the FlowJSON, you can do something like this:

.. code-block:: python
    :linenos:
    :emphasize-lines: 7, 9, 11, 12, 13, 14, 15

    from pywa import WhatsApp
    from pywa.errors import FlowUpdatingError
    from pywa.types.flows import *

    wa = WhatsApp(..., business_account_id="1234567890123456")

    flow_id = "123456789" # wa.create_flow(name="My New Flow") # run this only once

    your_flow_json = FlowJSON(...)  # keep edit your flow

    try:
        wa.update_flow_json(flow_id, flow_json=your_flow_json)
        print("Flow updated successfully!")
    except FlowUpdatingError:
        print("Error updating flow")
        print(wa.get_flow(flow_id).validation_errors)

This way you always know if there is validation errors that needed to be fixed.

To test your flow you need to sent it:

Sending Flow
------------

.. note::

    WORK IN PROGRESS

.. currentmodule:: pywa.types.callback

Flow is just a :class:`FlowButton` attached to a message.
Let's see how to send text message with flow:

.. currentmodule:: pywa.types.flows

.. code-block:: python
    :linenos:
    :emphasize-lines: 9, 10, 11, 12, 13, 14, 15, 16

    from pywa import WhatsApp
    from pywa.types import FlowButton

    wa = WhatsApp(...)

    wa.send_message(
        to="1234567890",
        text="Hi, You need to finish your sign up!",
        buttons=FlowButton(
            title="Finish Sign Up",
            flow_id="1234567890123456",  # The `static_flow` flow id from above
            flow_token="AQAAAAACS5FpgQ_cAAAAAD0QI3s.",
            mode=FlowStatus.DRAFT,
            flow_action_type=FlowActionType.NAVIGATE,
            flow_action_screen="SIGN_UP", # The screen id to open when the user clicks the button
        )
    )

Let's walk through the arguments:

- ``title`` - The button title that will appear on the bottom of the message.

- ``flow_id`` - The flow id that you want to send.

- ``flow_token`` - A unique token you generate for each flow message. The token is used to identify the flow message when you receive a response from the user.

- ``mode`` - If the flow is in draft mode, you must specify the mode as ``FlowStatus.DRAFT``.

- ``flow_action_type`` - The action to take when the user clicks the button. The action can be ``FlowActionType.NAVIGATE`` or ``FlowActionType.DATA_EXCHANGE``. since this example is static flow, we will use ``FlowActionType.NAVIGATE``.

- ``flow_action_screen`` - The first screen id to display when the user clicks the button.

    If you don't care about the dynamic example, you can skip to `Getting Flow Completion message <#getting-flow-completion-message>`_.

Handling Flow requests and responding to them
---------------------------------------------

This part is only for dynamic flow. here we will demonstrate how to handle the DATA_EXCHANGE requests and respond to them.

.. note::

    Since the requests and responses can contain sensitive data, such as passwords and other personal information,
    all the requests and responses are encrypted using the `WhatsApp Business Encryption <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/whatsapp-business-encryption>`_.

    Before you continue, you need to sign and upload the business public key.
    First you need to generate a private key and a public key:

    Generate a public and private RSA key pair by typing in the following command:

    >>> openssl genrsa -des3 -out private.pem 2048


    This generates 2048-bit RSA key pair encrypted with a password you provided and is written to a file.

    Next, you need to export the RSA Public Key to a file.

    >>> openssl rsa -in private.pem -outform PEM -pubout -out public.pem


    This exports the RSA Public Key to a file.

    Once you have the public key, you can upload it using the :meth:`~pywa.client.WhatsApp.set_business_public_key` method.

    .. code-block:: python
        :linenos:

        from pywa import WhatsApp

        wa = WhatsApp(...)

        wa.set_business_public_key(open("public.pem").read())

    Every request need to be decrypted using the private key. so you need to provide it when you create the :class:`WhatsApp` object:

    .. code-block:: python
        :linenos:

        from pywa import WhatsApp

        wa = WhatsApp(..., business_private_key=open("private.pem").read())

    Now you are ready to handle the requests.

    Just one more thing, the default decryption & encryption implementation is using the `cryptography <https://cryptography.io/en/latest/>`_ library,
    So you need to install it:

    >>> pip3 install cryptography

    Or when installing PyWa:

    >>> pip3 install "pywa[cryptography]"


In dynamic flow, when the user perform an action with type of ``FlowActionType.DATA_EXCHANGE`` you will receive a request to your server with the payload
and you need to determine if you want to continue to the next screen or complete the flow.

So in our dynamic example (``dynamic_sign_up_flow.py``), we have just one screen: ``SIGN_UP``.

.. code-block:: python
        :linenos:
        :emphasize-lines: 6,7,8

        Screen(
            id="SIGN_UP",
            title="Finish Sign Up",
            terminal=True,
            data=[
                first_name_helper_text := ScreenData(key="first_name_helper_text", example="Enter your first name"),
                is_last_name_required := ScreenData(key="is_last_name_required", example=True),
                is_email_enabled := ScreenData(key="is_email_enabled", example=False),
            ],
            ...
        )


The ``terminal`` argument is set to ``True`` which means that this screen can end the flow.

As you can see, this screen gets data that help it to be dynamic.

For example, we have :class:`TextInput` that gets the user's last name. We want to be able to decide if it's required or not,
so if we already have the user's last name in our database, we don't require it.
This can be done by setting the ``required`` argument to a dynamic value taken from the ``data`` map. this data can be provided by the previous screen, by our server or when sending the flow.

We want to demonstrate how to handle dynamic flow with our server, so we will send the flow with action type of ``FlowActionType.DATA_EXCHANGE``,
So when the user clicks the button, we will receive a request to our server with the ation, flow_token and the screen which requested the data.

We need to tell WhatsApp to send the requests to our serve. :meth:`~pywa.client.WhatsApp.update_flow_metadata`:

.. code-block:: python
    :linenos:
    :emphasize-lines: 7

    from pywa import WhatsApp

    wa = WhatsApp(...)

    wa.update_flow_metadata(
        flow_id="1234567890123456",  # The `dynamic_flow` flow id from above
        endpoint_uri="https://your-server.com/flow"
    )

Let's send the flow. this time with an image:

.. code-block:: python
    :linenos:
    :emphasize-lines: 15

    from pywa import WhatsApp
    from pywa.types import FlowButton, FlowActionType, FlowStatus

    wa = WhatsApp(...)

    wa.send_image(
        to="1234567890",
        image="https://t3.ftcdn.net/jpg/03/82/73/76/360_F_382737626_Th2TUrj9PbvWZKcN9Kdjxu2yN35rA9nU.jpg",
        caption="Hi, You need to finish your sign up!",
        buttons=FlowButton(
            title="Finish Sign Up",
            flow_id="1234567890123456",  # The `dynamic_flow` flow id from above
            flow_token="AQAAAAACS5FpgQ_cAAAAAD0QI3s.",
            mode=FlowStatus.DRAFT,
            flow_action_type=FlowActionType.DATA_EXCHANGE,  # This time we want to exchange data
        )
    )

Here we set the ``flow_action_type`` to ``FlowActionType.DATA_EXCHANGE`` since we want to exchange data with the server.
So, when the user opens the flow, we will receive a request to our server to provide the screen to open and the data to provide to it.

Let's register a callback function to handle this request:

.. code-block:: python
    :linenos:
    :emphasize-lines: 6, 9, 10, 14, 15, 16, 17, 18, 19

    from pywa import WhatsApp
    from pywa.types import FlowRequest, FlowResponse

    wa = WhatsApp(
        ...,
        business_private_key=open("private.pem").read(),  # provide your business private key
    )

    @wa.on_flow_request(endpoint="/flow")  # The endpoint we set above
    def on_support_request(_: WhatsApp, req: FlowRequest) -> FlowResponse:
        print(req.flow_token)  # use this to indentify the user who you sent the flow to
        return FlowResponse(
            version=req.version,
            screen="SIGN_UP",  # The screen id to open
            data={
                "first_name_helper_text": "Please enter your first name",
                "is_last_name_required": True,
                "is_email_enabled": False,
            },
        )

We need to provide our business private key to decrypt the request and encrypt the response.

After that. we are registering a callback function to handle the request.
The callback function will receive the :class:`FlowRequest` object and should return :class:`FlowResponse` object.

        A callback function can be return or raise :class:`FlowTokenNoLongerValid` or :class:`FlowRequestSignatureAuthenticationFailed`
        to indicate that the flow token is no longer valid or the request signature authentication failed.

In our example, we returning our dynamic data to the ``SIGN_UP`` screen.

Of course, it can be more complex, if you have multiple screens, you can return data from them and then decide
what screen to open next or complete the flow.

    If you want example of more complex flow, you can check out the `Sign up Flow Example <../examples/sign_up_flow.html>`_.

Getting Flow Completion message
-------------------------------

.. note::

    WORK IN PROGRESS

When the user completes the flow, you will receive a request to your webhook with the payload you sent when you completed the flow.

        WhatApp recommends to send the user a summary of the flow response.

Here is how to listen to flow completion request:

.. code-block:: python
    :linenos:

    from pywa import WhatsApp
    from pywa.types import FlowCompletion

    wa = WhatsApp(...)

    @wa.on_flow_completion()
    def on_flow_completion(_: WhatsApp, flow: FlowCompletion):
        print(f"The user {flow.from_user.name} just completed the {flow.token} flow!")
        print(flow.response)

The .response attribute is the payload you sent when you completed the flow.


.. toctree::
    flow_json
    flow_types
