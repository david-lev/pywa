♻️ Flows
========

.. currentmodule:: pywa.types.flows

.. note::

    WORK IN PROGRESS

    The ``Flows`` in pywa are still in beta and not fully tested.
    Install the RC version of pywa to use it:

    >>> pip3 install "pywa[cryptography]==1.13.0rc3"

    The ``cryptography`` extra is required for the default implementation of the decryption and encryption of the flow requests and responses.

    If you find any bugs or have any suggestions, please open an issue on `GitHub <https://github.com/david-lev/pywa/issues>`_.

The WhatsApp Flows are now the most exciting part of the WhatsApp Cloud API.

From `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows>`_:

    .. image:: ../../../../_static/guides/flows.webp
        :alt: WhatsApp Flows
        :width: 100%

    WhatsApp Flows is a way to build structured interactions for business messaging. With Flows, businesses can define, configure, and customize messages with rich interactions that give customers more structure in the way they communicate.

    You can use Flows to book appointments, browse products, collect customer feedback, get new sales leads, or anything else where structured communication is more natural or comfortable for your customers.


When you reading the official docs it's looks very intimidating, but in fact it's quite simple (by PyWa ;) ).

The Flows are seperated to 4 parts:

- Creating Flow
- Sending Flow
- Handling Flow requests and responding to them
- Getting Flow Completion message

Creating Flow
-------------

First you need to create the flow, name it and assign categories to it.
You can create the flows using the `WhatsApp Flow Builder <https://business.facebook.com/wa/manage/flows/>`_ or by PyWa:

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

.. note::

    WORK IN PROGRESS

A flow is collection of screens containing components. screens can exchange data with each other and with your server.

Flow can be static; all the components settings are predefined and no interaction is required from your server.
Or it can be dynamic; your server can respond to screen actions and determine the next screen to display (or close the flow) and the data to provide to it.

.. note::

    WORK IN PROGRESS

    I really recommend you to read the `Flow JSON Docs <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson>`_ before you continue.
    A full guide will be added soon.

Every component on the flowJSON has a corresponding class in :mod:`pywa.types.flows`.

here is an example of static flow:

.. toggle::

    .. code-block:: python
        :caption: customer_satisfaction_survey_flow.py
        :linenos:

        from pywa.types.flows import (
            FlowJSON,
            Screen,
            Layout,
            LayoutType,
            Form,
            TextSubheading,
            RadioButtonsGroup,
            DataSource,
            TextArea,
            Footer,
            Action,
            FlowActionType,
            ActionNext,
            ActionNextType,
            Dropdown,
        )
        customer_satisfaction_survey = FlowJSON(
            version="2.1",
            screens=[
                Screen(
                    id="RECOMMEND",
                    title="Feedback 1 of 2",
                    data={},
                    layout=Layout(
                        type=LayoutType.SINGLE_COLUMN,
                        children=[
                            Form(
                                name="form",
                                children=[
                                    TextSubheading(text="Would you recommend us to a friend?"),
                                    RadioButtonsGroup(
                                        name="recommend_radio",
                                        label="Choose one",
                                        data_source=[
                                            DataSource(id="0", title="Yes"),
                                            DataSource(id="1", title="No"),
                                        ],
                                        required=True,
                                    ),
                                    TextSubheading(text="How could we do better?"),
                                    TextArea(
                                        name="comment_text",
                                        label="Leave a comment",
                                        required=False,
                                    ),
                                    Footer(
                                        label="Continue",
                                        on_click_action=Action(
                                            name=FlowActionType.NAVIGATE,
                                            next=ActionNext(
                                                type=ActionNextType.SCREEN, name="RATE"
                                            ),
                                            payload={
                                                "recommend_radio": "${form.recommend_radio}",
                                                "comment_text": "${form.comment_text}",
                                            },
                                        ),
                                    ),
                                ],
                            )
                        ],
                    ),
                ),
                Screen(
                    id="RATE",
                    title="Feedback 2 of 2",
                    data={
                        "recommend_radio": {"type": "string", "__example__": "Example"},
                        "comment_text": {"type": "string", "__example__": "Example"},
                    },
                    terminal=True,
                    layout=Layout(
                        type=LayoutType.SINGLE_COLUMN,
                        children=[
                            Form(
                                name="form",
                                children=[
                                    TextSubheading(text="Rate the following: "),
                                    Dropdown(
                                        name="purchase_rating",
                                        label="Purchase experience",
                                        required=True,
                                        data_source=[
                                            DataSource(id="0", title="★★★★★ • Excellent (5/5)"),
                                            DataSource(id="1", title="★★★★☆ • Good (4/5)"),
                                            DataSource(id="2", title="★★★☆☆ • Average (3/5)"),
                                            DataSource(id="3", title="★★☆☆☆ • Poor (2/5)"),
                                            DataSource(id="4", title="★☆☆☆☆ • Very Poor (1/5)"),
                                        ],
                                    ),
                                    Dropdown(
                                        name="delivery_rating",
                                        label="Delivery and setup",
                                        required=True,
                                        data_source=[
                                            DataSource(id="0", title="★★★★★ • Excellent (5/5)"),
                                            DataSource(id="1", title="★★★★☆ • Good (4/5)"),
                                            DataSource(id="2", title="★★★☆☆ • Average (3/5)"),
                                            DataSource(id="3", title="★★☆☆☆ • Poor (2/5)"),
                                            DataSource(id="4", title="★☆☆☆☆ • Very Poor (1/5)"),
                                        ],
                                    ),
                                    Dropdown(
                                        name="cs_rating",
                                        label="Customer service",
                                        required=True,
                                        data_source=[
                                            DataSource(id="0", title="★★★★★ • Excellent (5/5)"),
                                            DataSource(id="1", title="★★★★☆ • Good (4/5)"),
                                            DataSource(id="2", title="★★★☆☆ • Average (3/5)"),
                                            DataSource(id="3", title="★★☆☆☆ • Poor (2/5)"),
                                            DataSource(id="4", title="★☆☆☆☆ • Very Poor (1/5)"),
                                        ],
                                    ),
                                    Footer(
                                        label="Done",
                                        on_click_action=Action(
                                            name=FlowActionType.COMPLETE,
                                            payload={
                                                "purchase_rating": "${form.purchase_rating}",
                                                "delivery_rating": "${form.delivery_rating}",
                                                "cs_rating": "${form.cs_rating}",
                                                "recommend_radio": "${data.recommend_radio}",
                                                "comment_text": "${data.comment_text}",
                                            },
                                        ),
                                    ),
                                ],
                            )
                        ],
                    ),
                ),
            ],
        )

Which is the equivalent of the following flow json:

.. toggle::

    .. code-block:: json
        :caption: customer_satisfaction_survey_flow.json
        :linenos:

        {
            "version": "2.1",
            "screens": [
              {
                "id": "RECOMMEND",
                "title": "Feedback 1 of 2",
                "data": {},
                "layout": {
                  "type": "SingleColumnLayout",
                  "children": [
                    {
                      "type": "Form",
                      "name": "form",
                      "children": [
                        {
                          "type": "TextSubheading",
                          "text": "Would you recommend us to a friend?"
                        },
                        {
                          "type": "RadioButtonsGroup",
                          "label": "Choose one",
                          "name": "recommend_radio",
                          "data-source": [
                            {
                              "id": "0",
                              "title": "Yes"
                            },
                            {
                              "id": "1",
                              "title": "No"
                            }
                          ],
                          "required": true
                        },
                        {
                          "type": "TextSubheading",
                          "text": "How could we do better?"
                        },
                        {
                          "type": "TextArea",
                          "label": "Leave a comment",
                          "required": false,
                          "name": "comment_text"
                        },
                        {
                          "type": "Footer",
                          "label": "Continue",
                          "on-click-action": {
                            "name": "navigate",
                            "next": {
                              "type": "screen",
                              "name": "RATE"
                            },
                            "payload": {
                              "recommend_radio": "${form.recommend_radio}",
                              "comment_text": "${form.comment_text}"
                            }
                          }
                        }
                      ]
                    }
                  ]
                }
              },
              {
                "id": "RATE",
                "title": "Feedback 2 of 2",
                "data": {
                  "recommend_radio": {
                    "type": "string",
                    "__example__": "Example"
                  },
                  "comment_text": {
                    "type": "string",
                    "__example__": "Example"
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
                          "type": "TextSubheading",
                          "text": "Rate the following: "
                        },
                        {
                          "type": "Dropdown",
                          "label": "Purchase experience",
                          "required": true,
                          "name": "purchase_rating",
                          "data-source": [
                            {
                              "id": "0",
                              "title": "★★★★★ • Excellent (5/5)"
                            },
                            {
                              "id": "1",
                              "title": "★★★★☆ • Good (4/5)"
                            },
                            {
                              "id": "2",
                              "title": "★★★☆☆ • Average (3/5)"
                            },
                            {
                              "id": "3",
                              "title": "★★☆☆☆ • Poor (2/5)"
                            },
                            {
                              "id": "4",
                              "title": "★☆☆☆☆ • Very Poor (1/5)"
                            }
                          ]
                        },
                        {
                          "type": "Dropdown",
                          "label": "Delivery and setup",
                          "required": true,
                          "name": "delivery_rating",
                          "data-source": [
                            {
                              "id": "0",
                              "title": "★★★★★ • Excellent (5/5)"
                            },
                            {
                              "id": "1",
                              "title": "★★★★☆ • Good (4/5)"
                            },
                            {
                              "id": "2",
                              "title": "★★★☆☆ • Average (3/5)"
                            },
                            {
                              "id": "3",
                              "title": "★★☆☆☆ • Poor (2/5)"
                            },
                            {
                              "id": "4",
                              "title": "★☆☆☆☆ • Very Poor (1/5)"
                            }
                          ]
                        },
                        {
                          "type": "Dropdown",
                          "label": "Customer service",
                          "required": true,
                          "name": "cs_rating",
                          "data-source": [
                            {
                              "id": "0",
                              "title": "★★★★★ • Excellent (5/5)"
                            },
                            {
                              "id": "1",
                              "title": "★★★★☆ • Good (4/5)"
                            },
                            {
                              "id": "2",
                              "title": "★★★☆☆ • Average (3/5)"
                            },
                            {
                              "id": "3",
                              "title": "★★☆☆☆ • Poor (2/5)"
                            },
                            {
                              "id": "4",
                              "title": "★☆☆☆☆ • Very Poor (1/5)"
                            }
                          ]
                        },
                        {
                          "type": "Footer",
                          "label": "Done",
                          "on-click-action": {
                            "name": "complete",
                            "payload": {
                              "purchase_rating": "${form.purchase_rating}",
                              "delivery_rating": "${form.delivery_rating}",
                              "cs_rating": "${form.cs_rating}",
                              "recommend_radio": "${data.recommend_radio}",
                              "comment_text": "${data.comment_text}"
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

Here is example of dynamic flow:

.. toggle::

    .. code-block:: python
        :caption: support_request.json
        :linenos:

        support_request = FlowJSON(
            version="2.1",
            data_api_version="3.0",
            data_channel_uri="https://your-server-api.com/support_request_flow",
            routing_model={},
            screens=[
                Screen(
                    id="DETAILS",
                    terminal=True,
                    title="Get help",
                    data={
                        "name_help": {
                            "type": "string",
                            "__example__": "request for full name",
                        },
                        "is_order_num_required": {
                            "type": "boolean",
                            "__example__": True,
                        },
                        "is_desc_enabled": {
                            "type": "boolean",
                            "__example__": False,
                        },
                    },
                    layout=Layout(
                        type=LayoutType.SINGLE_COLUMN,
                        children=[
                            Form(
                                name="form",
                                children=[
                                    TextInput(
                                        name="name",
                                        label="Name",
                                        input_type=InputType.TEXT,
                                        required=True,
                                        helper_text="${data.name_help}",
                                    ),
                                    TextInput(
                                        name="order_number",
                                        label="Order number",
                                        input_type=InputType.NUMBER,
                                        required="${data.is_order_num_required}",
                                        helper_text="",
                                    ),
                                    RadioButtonsGroup(
                                        name="topic_radio",
                                        label="Choose a topic",
                                        data_source=[
                                            DataSource(id="0", title="Orders and payments"),
                                            DataSource(id="1", title="Maintenance"),
                                            DataSource(id="2", title="Delivery"),
                                            DataSource(id="3", title="Returns"),
                                            DataSource(id="4", title="Other"),
                                        ],
                                        required=True,
                                    ),
                                    TextArea(
                                        name="description",
                                        label="Description of issue",
                                        required=False,
                                        enabled="${data.is_desc_enabled}",
                                    ),
                                    Footer(
                                        label="Done",
                                        on_click_action=Action(
                                            name=FlowActionType.COMPLETE,
                                            payload={
                                                "name": "${form.name}",
                                                "order_number": "${form.order_number}",
                                                "topic": "${form.topic_radio}",
                                                "description": "${form.description}",
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
        :caption: support_request.json
        :linenos:

        {
          "version": "2.1",
          "data_api_version": "3.0",
          "data_channel_uri": "https://example.com/support_request_flow",
          "routing_model": {},
          "screens": [
            {
              "id": "DETAILS",
              "title": "Get help",
              "data": {
                "name_help": {
                  "type": "string",
                  "__example__": "request for full name"
                },
                "is_order_num_required": {
                  "type": "boolean",
                  "__example__": true
                },
                "is_desc_enabled": {
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
                        "name": "name",
                        "label": "Name",
                        "input-type": "text",
                        "required": true,
                        "helper-text": "${data.name_help}"
                      },
                      {
                        "type": "TextInput",
                        "name": "order_number",
                        "label": "Order number",
                        "input-type": "number",
                        "required": "${data.is_order_num_required}",
                        "helper-text": ""
                      },
                      {
                        "type": "RadioButtonsGroup",
                        "name": "topic_radio",
                        "data-source": [
                          {
                            "id": "0",
                            "title": "Orders and payments"
                          },
                          {
                            "id": "1",
                            "title": "Maintenance"
                          },
                          {
                            "id": "2",
                            "title": "Delivery"
                          },
                          {
                            "id": "3",
                            "title": "Returns"
                          },
                          {
                            "id": "4",
                            "title": "Other"
                          }
                        ],
                        "label": "Choose a topic",
                        "required": true
                      },
                      {
                        "type": "TextArea",
                        "name": "description",
                        "label": "Description of issue",
                        "required": false,
                        "enabled": "${data.is_desc_enabled}"
                      },
                      {
                        "type": "Footer",
                        "label": "Done",
                        "on-click-action": {
                          "name": "complete",
                          "payload": {
                            "name": "${form.name}",
                            "order_number": "${form.order_number}",
                            "topic": "${form.topic_radio}",
                            "description": "${form.description}"
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

After you have the flow json, you can update the flow:

.. code-block:: python
    :linenos:

    from pywa import WhatsApp

    wa = WhatsApp(...)

    wa.update_flow(flow_id, flow_json=customer_satisfaction_survey)

The ``flow_json`` argument can be :class:`FlowJSON`, a dict, json string, json file path or open(json_file) obj.

You can get the :class:`FlowDetails` of the flow with :meth:`pywa.client.WhatsApp.get_flow` to see if there is validation errors needed to be fixed:

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
        wa.update_flow(flow_id, flow_json=your_flow_json)
    except FlowUpdatingError:
        print("Error updating flow")
        print(wa.get_flow(flow_id).validation_errors)

This way you always know if there is validation errors that needed to be fixed.

To test your flow you need to sent it:

Sending Flow
------------

.. note::

    WORK IN PROGRESS


Flow is just a button attached to a message.
Let's see how to send text message with flow:

.. code-block:: python
    :linenos:
    :emphasize-lines: 9, 10, 11, 12, 13, 14, 15, 16, 17

    from pywa import WhatsApp
    from pywa.types import FlowButton

    wa = WhatsApp(...)

    wa.send_message(
        phone_number="1234567890",
        text="Hi, We love to get your feedback on our service!",
        buttons=FlowButton(
            title="Leave Feedback",
            flow_id="1234567890123456",  # The `customer_satisfaction_survey_flow` id from above
            flow_token="AQAAAAACS5FpgQ_cAAAAAD0QI3s.",
            flow_message_version="3",
            mode=FlowStatus.DRAFT,
            flow_action_type=FlowActionType.NAVIGATE,
            flow_action_screen="RECOMMEND", # The first screen id
        )
    )

Let's walk through the arguments:

- ``title`` - The button title that will appear on the bottom of the message.

- ``flow_id`` - The flow id that you want to send.

- ``flow_token`` - A unique token you generate for each flow message. The token is used to identify the flow message when you receive a response from the user.

- ``flow_message_version`` - The version of the flow message. The version is used to identify the flow message when you receive a response from the user.

- ``mode`` - If the flow is in draft mode, you must specify the mode as ``FlowStatus.DRAFT``.

- ``flow_action_type`` - The action to take when the user clicks the button. The action can be ``FlowActionType.NAVIGATE`` or ``FlowActionType.DATA_EXCHANGE``. since this example is static flow, we will use ``FlowActionType.NAVIGATE``.

- ``flow_action_screen`` - The first screen id to display when the user clicks the button.


Handling Flow requests and responding to them
---------------------------------------------

.. note::

    WORK IN PROGRESS

In dynamic flow, when the user perform an action with type of ``FlowActionType.DATA_EXCHANGE`` you will receive a request to your server with the payload
and you need to determine if you want to continue to the next screen or complete the flow.

So in our dynamic example (``support_request``) we have just one screen: ``DETAILS``

.. code-block:: python
        :linenos:
        :emphasize-lines: 3, 6, 10, 14

        Screen(
            id="DETAILS",
            terminal=True,
            title="Get help",
            data={
                "name_help": {
                    "type": "string",
                    "__example__": "request for full name",
                },
                "is_order_num_required": {
                    "type": "boolean",
                    "__example__": True,
                },
                "is_desc_enabled": {
                    "type": "boolean",
                    "__example__": False,
                },
            },
            ...
        )

The ``terminal`` argument is set to ``True`` which means that this screen can ends the flow.

As you can see, this screen gets data that help it to be dynamic.

For example, we have :class:`TextInput` that gets the user's name. We want to be dynamic about what we want the user
typing in. So we don't hard-code the ``helper_text`` with value like "Enter you first and last name:", instead, we use
the ``"${data.name_help}"`` which is a reference to the ``name_help`` key in the ``data`` dict we are going to provide dynamically.

So when the user clicks the button, we will receive a request to our server with the ation, flow_token and the screen which requested the data.

We first sending this flow. this time with an image:

.. code-block:: python
    :linenos:
    :emphasize-lines: 16

    from pywa import WhatsApp
    from pywa.types import FlowButton, FlowActionType, FlowStatus

    wa = WhatsApp(...)

    wa.send_image(
        to="1234567890",
        image="https://wpforms.com/wp-content/uploads/2017/11/designing-support-ticket-request-form-best-practices.jpg",
        caption="Hi, Please fill the form below to get support.",
        buttons=FlowButton(
            title="Get Support",
            flow_id="1234567890123456",  # The `support_request` flow id from above
            flow_token="AQAAAAACS5FpgQ_cAAAAAD0QI3s.",
            flow_message_version="3",
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
        business_private_key="PRIVATE_KEY",
    )

    @wa.on_flow_request(endpoint="/support_request_flow")
    def on_support_request(_: WhatsApp, req: FlowRequest) -> FlowResponse:
        print(req.flow_token)  # use this to indentify the user who you sent the flow to
        return FlowResponse(
            version=req.version,
            screen="DETAILS",
            data={
                 "name_help": "Just your first name",
                 "is_order_num_required": True,
                 "is_desc_enabled": False,
             },
        )

We need to provide our business private key to decrypt the request and encrypt the response.

        We need to setup WhatsApp Business Encryption in order to decrypt the request and encrypt the response.
        You can read more about it in `WhatsApp Business Encryption <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/whatsapp-business-encryption>`_.
        The public key can be uploaded using the :meth:`pywa.api.WhatsAppCloudApi.set_business_public_key` method.

After that. we are registering a callback function to handle the request.
The callback function will receive the :class:`FlowRequest` object and should return :class:`FlowResponse` object.

        A callback function can be return or raise :class:`FlowTokenNoLongerValid` or :class:`FlowRequestSignatureAuthenticationFailed`
        to indicate that the flow token is no longer valid or the request signature authentication failed.

In our example, we returning our dynamic data to the ``DETAILS`` screen.

Of course, it can be more complex, if you have multiple screens, you can return data from them and then decide
what screen to open next or complete the flow.

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
