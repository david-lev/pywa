Sign Up Flow
============

.. currentmodule:: pywa.types.flows

**In this example, we will create a sign up flow that allows users to sign up and login to their account.**

Think of a Flow as a collection of related screens. The screens can exchange data with each other and with your server.

A screen can be static: it can display static content that configured when the flow is created. For example, a screen can
display a generic welcome message without any dynamic content, or it can display a message that will be different for each user
by providing the message text when the flow is sent to the user or when it requested from the server.

Almost every aspect of a screen component can be dynamic. For example, let's take the :class:`TextInput` component which is used to
collect user input (e.g name, email, password, etc.). The label, the input type, the helper text, the minimum and maximum number of characters,
and whether the input is required or not, if the field is pre-filled with a value, and if the field is disabled or not, can all be dynamic.

Each :class:`Screen` has

- A ``id``: The unique ID of the screen, which is used for navigation
- A ``title``: The title of the screen, which is rendered at the top of the screen
- A ``layout``: The layout of the screen, which contains the elements that are displayed on the screen.
- A ``data``: The data that the screen expects to receive. This data is used to insert content and configure the screen
  in order to make it dynamic.

Important thing to understand is that it doesn't matter in which order the screens are defined, every screen is independent
and has its own data.

I think it's easier to understand this with an examples, so let's get started.

Start Screen
--------------

Let's start from the ``START`` screen. This screen welcomes the user and allows them to choose if they want to sign up
(create an account) or login to their existing account.

.. code-block:: python
    :linenos:
    :emphasize-lines: 6, 9, 26


    START = Screen(
        id="START",
        title="Home",
        layout=Layout(
            children=[
                TextHeading(
                    text="Welcome to our app",
                ),
                EmbeddedLink(
                    text="Click here to sign up",
                    on_click_action=Action(
                        name=FlowActionType.NAVIGATE,
                        next=ActionNext(
                            type=ActionNextType.SCREEN,
                            name="SIGN_UP",
                        ),
                        payload={
                            "first_name_initial_value": "",
                            "last_name_initial_value": "",
                            "email_initial_value": "",
                            "password_initial_value": "",
                            "confirm_password_initial_value": "",
                        },
                    ),
                ),
                EmbeddedLink(
                    text="Click here to login",
                    on_click_action=Action(
                        name=FlowActionType.NAVIGATE,
                        next=ActionNext(
                            type=ActionNextType.SCREEN,
                            name="LOGIN",
                        ),
                        payload={
                            "email_initial_value": "",
                            "password_initial_value": "",
                        },
                    ),
                ),
            ]
        ),
    )

This is an example of static screen. The screen doesn't expect to receive any data and all its components are pre-configured.

The ``START`` screen has three components:

- A :class:`TextHeading`, which welcomes the user
- A :class:`EmbeddedLink` with an :class:`Action` that navigates to the ``SIGN_UP`` screen
- A :class:`EmbeddedLink` with an :class:`Action` that navigates to the ``LOGIN`` screen

Each EmbeddedLink has an ``.on_click_action`` with Action value, so when the user clicks on the link, the action is triggered. In this case,
the action is to :class:`FlowActionType.NAVIGATE` to another screen. The payload contains the data that will be passed to the navigated screen, in
this case, we are passing the expected data of the ``SIGN_UP`` and ``LOGIN`` screens.

We will see how this works later on.


Sign Up Screen
--------------

The ``SIGN_UP`` screen allows the user to sign up (create an account). Let's take a look at the layout:


.. code-block:: python
    :linenos:
    :emphasize-lines: 4, 5, 6, 7, 8, 9, 10, 25, 26, 33, 38, 40, 45, 47, 52, 54, 62, 64, 71, 77, 78, 79, 80, 81, 82, 83

    SIGN_UP = Screen(
        id="SIGN_UP",
        title="Sign Up",
        data=[
            first_name_initial_value := ScreenData(key="first_name_initial_value", example="John"),
            last_name_initial_value := ScreenData(key="last_name_initial_value", example="Doe"),
            email_initial_value := ScreenData(key="email_initial_value", example="john.doe@gmail.com"),
            password_initial_value := ScreenData(key="password_initial_value", example="abc123"),
            confirm_password_initial_value := ScreenData(key="confirm_password_initial_value", example="abc123"),
        ],
        layout=Layout(
            children=[
                TextHeading(
                    text="Please enter your details",
                ),
                EmbeddedLink(
                    text="Already have an account?",
                    on_click_action=Action(
                        name=FlowActionType.NAVIGATE,
                        next=ActionNext(
                            type=ActionNextType.SCREEN,
                            name="LOGIN",
                        ),
                        payload={
                            "email_initial_value": FormRef("email"),
                            "password_initial_value": FormRef("password"),
                        },
                    ),
                ),
                Form(
                    name="form",
                    children=[
                        first_name := TextInput(
                            name="first_name",
                            label="First Name",
                            input_type=InputType.TEXT,
                            required=True,
                            init_value=first_name_initial_value.data_key,
                        ),
                        last_name := TextInput(
                            name="last_name",
                            label="Last Name",
                            input_type=InputType.TEXT,
                            required=True,
                            init_value=last_name_initial_value.data_key,
                        ),
                        email := TextInput(
                            name="email",
                            label="Email Address",
                            input_type=InputType.EMAIL,
                            required=True,
                            init_value=email_initial_value.data_key,
                        ),
                        password := TextInput(
                            name="password",
                            label="Password",
                            input_type=InputType.PASSWORD,
                            min_chars=8,
                            max_chars=16,
                            helper_text="Password must contain at least one number",
                            required=True,
                            init_value=password_initial_value.data_key,
                        ),
                        confirm_password := TextInput(
                            name="confirm_password",
                            label="Confirm Password",
                            input_type=InputType.PASSWORD,
                            min_chars=8,
                            max_chars=16,
                            required=True,
                            init_value=confirm_password_initial_value.data_key,
                        ),
                        Footer(
                            label="Done",
                            on_click_action=Action(
                                name=FlowActionType.DATA_EXCHANGE,
                                payload={
                                    "first_name": first_name.form_ref,
                                    "last_name": last_name.form_ref,
                                    "email": email.form_ref,
                                    "password": password.form_ref,
                                    "confirm_password": confirm_password.form_ref,
                                },
                            ),
                        ),
                    ]
                )
            ]
        )
    )


Ok, that's a lot of code. Let's break it down.

    In this examples we are using the walrus operator (:=) to assign values to variables. This allows us to use the
    variables later on in the code without having to declare them outside of the layout and then assign them values later

The ``SIGN_UP`` screen expects to receive some data. In this case, we are expecting to receive some values to pre-fill the form fields.

The data of the screen is represented by the ``.data`` property. The data is a list of :class:`ScreenData` objects.

Every :class:`ScreenData` need to have a unique ``key`` and an ``example`` value. The example value is used to generate the appropriate
JSON schema for the data. Also, we are assigning every :class:`ScreenData` to a variable (inlined with the walrus operator) so
that we can use them later on in the code to reference the data and "use" it in the screen (e.g. ``first_name_initial_value.data_key``).

The layout of the ``SIGN_UP`` screen contains the following elements:

- A :class:`TextHeading`, which asks the user to enter their details
- A :class:`EmbeddedLink` to the ``LOGIN`` screen, which allows the user to login if they already have an account (the user just remembered
  that they already have an account)
- A :class:`Form`, which contains the form fields that the user needs to fill in to sign up
- A :class:`Footer`, which contains a button that the user can click to submit the form

The :class:`Form` fields are:

- A :class:`TextInput` field for the first name, which is required
- A :class:`TextInput` field for the last name, which is required
- A :class:`TextInput` field for the email address (the input type is set to :class:`InputType.EMAIL`, so that the keyboard on the user's phone
  will show the ``@`` symbol and validate the email address. Also, the input is required)
- A :class:`TextInput` field for the password (the input type is set to :class:`InputType.PASSWORD`, so that the user's password is hidden when they type it)
  We are also providing a helper text to tell the user that the password must contain at least one number. Also, the minimum number of characters is 8 and the maximum is 16, and the input is required)
- A :class:`TextInput` field for the confirm password (the input type is set to :class:`InputType.PASSWORD`, so that the user's password is hidden when they re-type it)

Now, every form child get assigned to a variable (inlined with the walrus operator) so that we can use them later on in
the code to reference the form fields and send their "values" to the server or to another screen (e.g. ``first_name.form_ref``).

The :class:`Footer` contains a button that the user can click to submit the form. When the user clicks on the button, the :class:`Action`
:class:`FlowActionType.DATA_EXCHANGE` is triggered. This action type allows us to send data to the server and then decide what to do next (for example,
if the user is already registered, we can navigate to the ``LOGIN`` screen, or if the password and confirm password do not match,
we can show an error message and ask the user to try again).

The payload of the :class:`Action` of the :class:`Footer` contains the data that we want to send to the server. In this case, we are sending
the values of the form fields. The values can be either a :class:`DataKey` or a :class:`FormRef`. A :class:`DataKey` is used to reference
a screen's ``.data`` items and a :class:`FormRef` is used to reference :class:`Form` children.
Because we are using the walrus operator to assign the form fields to variables, we can use the variables to reference the form fields
by using the the ``.form_ref`` property of the form field (which is more type-safe than using the :class:`FormRef` with the form field's name).


The ``.form_ref`` and ``.data_key`` properties are equivalent to the :class:`FormRef` with the form field's name and the :class:`DataKey` with the
screen's data key, respectively. Infact, the ``.form_ref`` and ``.data_key`` properties are just shortcuts for the :class:`FormRef` and :class:`DataKey` classes.

    We are not using the ``.form_ref`` property to reference the ``email`` and ``password`` fields in the :class:`EmbeddedLink` because
    the ``.form_ref`` property is only available after the :class:`Form` has been added to the layout. So, we are using the :class:`FormRef` class


Sign In Screen
--------------

Ok, now to the ``LOGIN`` screen. This screen allows the user to login to their existing account.


.. code-block:: python
    :linenos:
    :emphasize-lines: 5, 6, 7, 8, 22, 23, 24, 25, 26, 27, 28, 34, 39, 41, 46, 52, 53, 54, 55

    LOGIN = Screen(
        id="LOGIN",
        title="Login",
        terminal=True,
        data=[
            email_initial_value := ScreenData(key="email_initial_value", example="john.doe@gmail.com"),
            password_initial_value := ScreenData(key="password_initial_value", example="abc123"),
        ],
        layout=Layout(
            children=[
                TextHeading(
                    text="Please enter your details"
                ),
                EmbeddedLink(
                    text="Don't have an account?",
                    on_click_action=Action(
                        name=FlowActionType.NAVIGATE,
                        next=ActionNext(
                            type=ActionNextType.SCREEN,
                            name="SIGN_UP",
                        ),
                        payload={
                            "email_initial_value": FormRef("email"),
                            "password_initial_value": FormRef("password"),
                            "confirm_password_initial_value": "",
                            "first_name_initial_value": "",
                            "last_name_initial_value": "",
                        },
                    ),
                ),
                Form(
                    name="form",
                    children=[
                        email := TextInput(
                            name="email",
                            label="Email Address",
                            input_type=InputType.EMAIL,
                            required=True,
                            init_value=email_initial_value.data_key,
                        ),
                        password := TextInput(
                            name="password",
                            label="Password",
                            input_type=InputType.PASSWORD,
                            required=True,
                            init_value=password_initial_value.data_key,
                        ),
                        Footer(
                            label="Done",
                            on_click_action=Action(
                                name=FlowActionType.DATA_EXCHANGE,
                                payload={
                                    "email": email.form_ref,
                                    "password": password.form_ref,
                                },
                            ),
                        ),
                    ]
                )
            ]
        )
    )


This screen is very straightforward. It has two elements:

- A :class:`TextInput` field for the email address (the input type is set to :class:`InputType.EMAIL`, so that the keyboard on the user's phone
  will show the ``@`` symbol and validate the email address)
- A :class:`TextInput` field for the password (the input type is set to :class:`InputType.PASSWORD`, so that the user's password is hidden when they type it)

The :class:`Footer` contains a button that the user can click to submit the form. When the user clicks on the button, We are using the
:class:`FlowActionType.DATA_EXCHANGE` action type to send the email and password that the user entered, to the server and then decide what to do next (for example,
if the user is not registered, we can navigate to the ``SIGN_UP`` screen, or if the password is incorrect, we can show an error message and ask
the user to try again).

Login Success Screen
--------------------

Now, to the last screen, the ``LOGIN_SUCCESS`` screen. This screen is displayed when the user successfully logs in:

.. code-block:: python
    :linenos:
    :emphasize-lines: 16, 24, 25, 26

    LOGIN_SUCCESS = Screen(
        id="LOGIN_SUCCESS",
        title="Success",
        terminal=True,
        layout=Layout(
            children=[
                TextHeading(
                    text="Welcome to our store",
                ),
                TextSubheading(
                    text="You are now logged in",
                ),
                Form(
                    name="form",
                    children=[
                        stay_logged_in := OptIn(
                            name="stay_logged_in",
                            label="Stay logged in",
                        ),
                        Footer(
                            label="Done",
                            on_click_action=Action(
                                name=FlowActionType.COMPLETE,
                                payload={
                                    "stay_logged_in": stay_logged_in.form_ref,
                                },
                            ),
                        ),
                    ]
                )
            ]
        ),
    )

This screen has two elements:

- A :class:`TextHeading`, which welcomes the user to the store
- A :class:`TextSubheading`, which tells the user that they are now logged in
- A :class:`Form`, which contains an :class:`OptIn` field that asks the user if they want to stay logged in

The :class:`Footer` contains a button that the user can click to submit the form. The ``COMPLETE`` action is used to complete the flow.
When the user clicks on the button, we are using the :class:`FlowActionType.COMPLETE` action to send the value of the :class:`OptIn` field to the server and
then complete the flow.

This screen is the only scrren that can complete the flow, that's why we are setting the ``terminal`` property to ``True``.


Creating the Flow
-----------------

Now, we need to wrap everything in a :class:`FlowJSON` object and create the flow:

.. code-block:: python
    :linenos:

    from pywa import utils
    from pywa.types.flows import FlowJSON

    SIGN_UP_FLOW_JSON = FlowJSON(
        data_api_version=utils.Version.FLOW_DATA_API,
        routing_model={
            "START": ["SIGN_UP", "LOGIN"],
            "SIGN_UP": ["LOGIN"],
            "LOGIN": ["LOGIN_SUCCESS"],
            "LOGIN_SUCCESS": [],
        },
        screens=[
            START,
            SIGN_UP,
            LOGIN,
            LOGIN_SUCCESS,
        ]
    )


The :class:`FlowJSON` object contains the following properties:

- ``data_api_version``: The version of the data API that we are using. We are using the latest version, which is ``Version.FLOW_DATA_API``
- ``routing_model``: The routing model of the flow. This is used to define the flow's navigation. In this case, we are using a simple routing model
  that allows us to navigate from the ``START`` screen to the ``SIGN_UP`` and ``LOGIN`` screens, from the ``SIGN_UP`` screen to the ``LOGIN`` screen (and the other way around),
  and from the ``LOGIN`` screen to the ``LOGIN_SUCCESS`` screen. The ``LOGIN_SUCCESS`` can't navigate to any other screen.
- ``screens``: The screens of the flow. In this case, we are using the screens that we created earlier.

Here is all the flow code in one place:

.. toggle::

    .. code-block:: python
        :linenos:

        from pywa import utils
        from pywa.types.flows import (
            FlowJSON,
            Screen,
            ScreenData,
            Form,
            Footer,
            Layout,
            Action,
            ActionNext,
            ActionNextType,
            FlowActionType,
            FormRef,
            InputType,
            TextHeading,
            TextSubheading,
            TextInput,
            OptIn,
            EmbeddedLink,
        )

        SIGN_UP_FLOW_JSON = FlowJSON(
            data_api_version=utils.Version.FLOW_DATA_API,
            routing_model={
                "START": ["SIGN_UP", "LOGIN"],
                "SIGN_UP": ["LOGIN"],
                "LOGIN": ["LOGIN_SUCCESS"],
                "LOGIN_SUCCESS": [],
            },
            screens=[
                Screen(
                    id="START",
                    title="Home",
                    layout=Layout(
                        children=[
                            TextHeading(
                                text="Welcome to our app",
                            ),
                            EmbeddedLink(
                                text="Click here to sign up",
                                on_click_action=Action(
                                    name=FlowActionType.NAVIGATE,
                                    next=ActionNext(
                                        type=ActionNextType.SCREEN,
                                        name="SIGN_UP",
                                    ),
                                    payload={
                                        "first_name_initial_value": "",
                                        "last_name_initial_value": "",
                                        "email_initial_value": "",
                                        "password_initial_value": "",
                                        "confirm_password_initial_value": "",
                                    },
                                ),
                            ),
                            EmbeddedLink(
                                text="Click here to login",
                                on_click_action=Action(
                                    name=FlowActionType.NAVIGATE,
                                    next=ActionNext(
                                        type=ActionNextType.SCREEN,
                                        name="LOGIN",
                                    ),
                                    payload={
                                        "email_initial_value": "",
                                        "password_initial_value": "",
                                    },
                                ),
                            ),
                        ]
                    ),
                ),
                Screen(
                    id="SIGN_UP",
                    title="Sign Up",
                    data=[
                        first_name_initial_value := ScreenData(key="first_name_initial_value", example="John"),
                        last_name_initial_value := ScreenData(key="last_name_initial_value", example="Doe"),
                        email_initial_value := ScreenData(key="email_initial_value", example="john.doe@gmail.com"),
                        password_initial_value := ScreenData(key="password_initial_value", example="abc123"),
                        confirm_password_initial_value := ScreenData(key="confirm_password_initial_value", example="abc123"),
                    ],
                    layout=Layout(
                        children=[
                            TextHeading(
                                text="Please enter your details",
                            ),
                            EmbeddedLink(
                                text="Already have an account?",
                                on_click_action=Action(
                                    name=FlowActionType.NAVIGATE,
                                    next=ActionNext(
                                        type=ActionNextType.SCREEN,
                                        name="LOGIN",
                                    ),
                                    payload={
                                        "email_initial_value": FormRef("email"),
                                        "password_initial_value": FormRef("password"),
                                    },
                                ),
                            ),
                            Form(
                                name="form",
                                children=[
                                    first_name := TextInput(
                                        name="first_name",
                                        label="First Name",
                                        input_type=InputType.TEXT,
                                        required=True,
                                        init_value=first_name_initial_value.data_key,
                                    ),
                                    last_name := TextInput(
                                        name="last_name",
                                        label="Last Name",
                                        input_type=InputType.TEXT,
                                        required=True,
                                        init_value=last_name_initial_value.data_key,
                                    ),
                                    email := TextInput(
                                        name="email",
                                        label="Email Address",
                                        input_type=InputType.EMAIL,
                                        required=True,
                                        init_value=email_initial_value.data_key,
                                    ),
                                    password := TextInput(
                                        name="password",
                                        label="Password",
                                        input_type=InputType.PASSWORD,
                                        min_chars=8,
                                        max_chars=16,
                                        helper_text="Password must contain at least one number",
                                        required=True,
                                        init_value=password_initial_value.data_key,
                                    ),
                                    confirm_password := TextInput(
                                        name="confirm_password",
                                        label="Confirm Password",
                                        input_type=InputType.PASSWORD,
                                        min_chars=8,
                                        max_chars=16,
                                        required=True,
                                        init_value=confirm_password_initial_value.data_key,
                                    ),
                                    Footer(
                                        label="Done",
                                        on_click_action=Action(
                                            name=FlowActionType.DATA_EXCHANGE,
                                            payload={
                                                "first_name": first_name.form_ref,
                                                "last_name": last_name.form_ref,
                                                "email": email.form_ref,
                                                "password": password.form_ref,
                                                "confirm_password": confirm_password.form_ref,
                                            },
                                        ),
                                    ),
                                ]
                            )
                        ]
                    )
                ),
                Screen(
                    id="LOGIN",
                    title="Login",
                    terminal=True,
                    data=[
                        email_initial_value := ScreenData(key="email_initial_value", example="john.doe@gmail.com"),
                        password_initial_value := ScreenData(key="password_initial_value", example="abc123"),
                    ],
                    layout=Layout(
                        children=[
                            TextHeading(
                                text="Please enter your details"
                            ),
                            EmbeddedLink(
                                text="Don't have an account?",
                                on_click_action=Action(
                                    name=FlowActionType.NAVIGATE,
                                    next=ActionNext(
                                        type=ActionNextType.SCREEN,
                                        name="SIGN_UP",
                                    ),
                                    payload={
                                        "email_initial_value": FormRef("email"),
                                        "password_initial_value": FormRef("password"),
                                        "confirm_password_initial_value": "",
                                        "first_name_initial_value": "",
                                        "last_name_initial_value": "",
                                    },
                                ),
                            ),
                            Form(
                                name="form",
                                children=[
                                    email := TextInput(
                                        name="email",
                                        label="Email Address",
                                        input_type=InputType.EMAIL,
                                        required=True,
                                        init_value=email_initial_value.data_key,
                                    ),
                                    password := TextInput(
                                        name="password",
                                        label="Password",
                                        input_type=InputType.PASSWORD,
                                        required=True,
                                        init_value=password_initial_value.data_key,
                                    ),
                                    Footer(
                                        label="Done",
                                        on_click_action=Action(
                                            name=FlowActionType.DATA_EXCHANGE,
                                            payload={
                                                "email": email.form_ref,
                                                "password": password.form_ref,
                                            },
                                        ),
                                    ),
                                ]
                            )
                        ]
                    ),
                ),
                Screen(
                    id="LOGIN_SUCCESS",
                    title="Success",
                    terminal=True,
                    layout=Layout(
                        children=[
                            TextHeading(
                                text="Welcome to our store",
                            ),
                            TextSubheading(
                                text="You are now logged in",
                            ),
                            Form(
                                name="form",
                                children=[
                                    stay_logged_in := OptIn(
                                        name="stay_logged_in",
                                        label="Stay logged in",
                                    ),
                                    Footer(
                                        label="Done",
                                        on_click_action=Action(
                                            name=FlowActionType.COMPLETE,
                                            payload={
                                                "stay_logged_in": stay_logged_in.form_ref,
                                            },
                                        ),
                                    ),
                                ]
                            )
                        ]
                    ),
                )
            ]
        )

And if you want to go to the `WhatsApp Flows Playground <https://business.facebook.com/wa/manage/flows>`_ and see the flow in action, copy the equivalent JSON to the playground:

.. toggle::

    .. code-block:: json
        :linenos:

        {
            "version": "3.0",
            "data_api_version": "3.0",
            "routing_model": {
                "START": [
                    "SIGN_UP",
                    "LOGIN"
                ],
                "SIGN_UP": [
                    "LOGIN"
                ],
                "LOGIN": [
                    "LOGIN_SUCCESS"
                ],
                "LOGIN_SUCCESS": []
            },
            "screens": [
                {
                    "id": "START",
                    "title": "Home",
                    "layout": {
                        "type": "SingleColumnLayout",
                        "children": [
                            {
                                "type": "TextHeading",
                                "text": "Welcome to our app"
                            },
                            {
                                "type": "EmbeddedLink",
                                "text": "Click here to sign up",
                                "on-click-action": {
                                    "name": "navigate",
                                    "next": {
                                        "type": "screen",
                                        "name": "SIGN_UP"
                                    },
                                    "payload": {
                                        "first_name_initial_value": "",
                                        "last_name_initial_value": "",
                                        "email_initial_value": "",
                                        "password_initial_value": "",
                                        "confirm_password_initial_value": ""
                                    }
                                }
                            },
                            {
                                "type": "EmbeddedLink",
                                "text": "Click here to login",
                                "on-click-action": {
                                    "name": "navigate",
                                    "next": {
                                        "type": "screen",
                                        "name": "LOGIN"
                                    },
                                    "payload": {
                                        "email_initial_value": "",
                                        "password_initial_value": ""
                                    }
                                }
                            }
                        ]
                    }
                },
                {
                    "id": "SIGN_UP",
                    "title": "Sign Up",
                    "data": {
                        "first_name_initial_value": {
                            "type": "string",
                            "__example__": "John"
                        },
                        "last_name_initial_value": {
                            "type": "string",
                            "__example__": "Doe"
                        },
                        "email_initial_value": {
                            "type": "string",
                            "__example__": "john.doe@gmail.com"
                        },
                        "password_initial_value": {
                            "type": "string",
                            "__example__": "abc123"
                        },
                        "confirm_password_initial_value": {
                            "type": "string",
                            "__example__": "abc123"
                        }
                    },
                    "layout": {
                        "type": "SingleColumnLayout",
                        "children": [
                            {
                                "type": "TextHeading",
                                "text": "Please enter your details"
                            },
                            {
                                "type": "EmbeddedLink",
                                "text": "Already have an account?",
                                "on-click-action": {
                                    "name": "navigate",
                                    "next": {
                                        "type": "screen",
                                        "name": "LOGIN"
                                    },
                                    "payload": {
                                        "email_initial_value": "${form.email}",
                                        "password_initial_value": "${form.password}"
                                    }
                                }
                            },
                            {
                                "type": "Form",
                                "name": "form",
                                "init-values": {
                                    "first_name": "${data.first_name_initial_value}",
                                    "last_name": "${data.last_name_initial_value}",
                                    "email": "${data.email_initial_value}",
                                    "password": "${data.password_initial_value}",
                                    "confirm_password": "${data.confirm_password_initial_value}"
                                },
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
                                        "type": "TextInput",
                                        "name": "password",
                                        "label": "Password",
                                        "input-type": "password",
                                        "required": true,
                                        "min-chars": 8,
                                        "max-chars": 16,
                                        "helper-text": "Password must contain at least one number"
                                    },
                                    {
                                        "type": "TextInput",
                                        "name": "confirm_password",
                                        "label": "Confirm Password",
                                        "input-type": "password",
                                        "required": true,
                                        "min-chars": 8,
                                        "max-chars": 16
                                    },
                                    {
                                        "type": "Footer",
                                        "label": "Done",
                                        "on-click-action": {
                                            "name": "data_exchange",
                                            "payload": {
                                                "first_name": "${form.first_name}",
                                                "last_name": "${form.last_name}",
                                                "email": "${form.email}",
                                                "password": "${form.password}",
                                                "confirm_password": "${form.confirm_password}"
                                            }
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                },
                {
                    "id": "LOGIN",
                    "title": "Login",
                    "data": {
                        "email_initial_value": {
                            "type": "string",
                            "__example__": "john.doe@gmail.com"
                        },
                        "password_initial_value": {
                            "type": "string",
                            "__example__": "abc123"
                        }
                    },
                    "terminal": true,
                    "layout": {
                        "type": "SingleColumnLayout",
                        "children": [
                            {
                                "type": "TextHeading",
                                "text": "Please enter your details"
                            },
                            {
                                "type": "EmbeddedLink",
                                "text": "Don't have an account?",
                                "on-click-action": {
                                    "name": "navigate",
                                    "next": {
                                        "type": "screen",
                                        "name": "SIGN_UP"
                                    },
                                    "payload": {
                                        "email_initial_value": "${form.email}",
                                        "password_initial_value": "${form.password}",
                                        "confirm_password_initial_value": "",
                                        "first_name_initial_value": "",
                                        "last_name_initial_value": ""
                                    }
                                }
                            },
                            {
                                "type": "Form",
                                "name": "form",
                                "init-values": {
                                    "email": "${data.email_initial_value}",
                                    "password": "${data.password_initial_value}"
                                },
                                "children": [
                                    {
                                        "type": "TextInput",
                                        "name": "email",
                                        "label": "Email Address",
                                        "input-type": "email",
                                        "required": true
                                    },
                                    {
                                        "type": "TextInput",
                                        "name": "password",
                                        "label": "Password",
                                        "input-type": "password",
                                        "required": true
                                    },
                                    {
                                        "type": "Footer",
                                        "label": "Done",
                                        "on-click-action": {
                                            "name": "data_exchange",
                                            "payload": {
                                                "email": "${form.email}",
                                                "password": "${form.password}"
                                            }
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                },
                {
                    "id": "LOGIN_SUCCESS",
                    "title": "Success",
                    "terminal": true,
                    "layout": {
                        "type": "SingleColumnLayout",
                        "children": [
                            {
                                "type": "TextHeading",
                                "text": "Welcome to our store"
                            },
                            {
                                "type": "TextSubheading",
                                "text": "You are now logged in"
                            },
                            {
                                "type": "Form",
                                "name": "form",
                                "children": [
                                    {
                                        "type": "OptIn",
                                        "name": "stay_logged_in",
                                        "label": "Stay logged in"
                                    },
                                    {
                                        "type": "Footer",
                                        "label": "Done",
                                        "on-click-action": {
                                            "name": "complete",
                                            "payload": {
                                                "stay_logged_in": "${form.stay_logged_in}"
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




Creating the flow is very simple using the :meth:`~pywa.client.WhatsApp.create_flow` method:

.. code-block:: python
    :linenos:

    from pywa import WhatsApp
    from pywa.types.flows import FlowCategory

    wa = WhatsApp(
        phone_id="1234567890",
        token="abcdefg",
        business_account_id="1234567890",  # the ID of the WhatsApp Business Account
    )

    flow_id = wa.create_flow(
        name="Sign Up Flow",
        categories=[FlowCategory.SIGN_IN, FlowCategory.SIGN_UP],
    )

Because we are going to exchange data with our server, we need to provide endpoint URI for the flow. This is the URI that
WhatsApp will use to send data to our server. We can do this by using the :meth:`~pywa.client.WhatsApp.update_flow_metadata` method:

.. code-block:: python
    :linenos:

    wa.update_flow_metadata(
        flow_id=flow_id,
        endpoint_uri="https://my-server.com/sign-up-flow",
    )

This endpoint must, of course, be pointing to our server. We can use ngrok or a similar tool to expose our server to the internet.

Finally, let's update the flow's JSON with :meth:`~pywa.client.WhatsApp.update_flow_json`:

.. code-block:: python
    :linenos:

    from pywa.errors import FlowUpdatingError

    try:
        wa.update_flow_json(
            flow_id=flow_id,
            flow_json=SIGN_UP_FLOW_JSON,
        )
        print("Flow updated successfully")
    except FlowUpdatingError as e:
        print(wa.get_flow_json(flow_id=flow_id).validation_errors)

Storing Users
------------

After the flow updates successfully, we can start with our server logic. First we need a simple user repository to store the users:

.. code-block:: python
    :linenos:

    import typing

    class UserRepository:
        def __init__(self):
            self._users = {}

        def create(self, email: str, details: dict[str, typing.Any]):
            self._users[email] = details

        def get(self, email: str) -> dict[str, typing.Any] | None:
            return self._users.get(email)

        def update(self, email: str, details: dict[str, typing.Any]):
            self._users[email] = details

        def delete(self, email: str):
            del self._users[email]

        def exists(self, email: str) -> bool:
            return email in self._users

        def is_password_valid(self, email: str, password: str) -> bool:
            return self._users[email]["password"] == password

    user_repository = UserRepository()  # create an instance of the user repository


Of course, in a real application, we would use a real database to store the users (and we never store the passwords in plain text...).

Sending the Flow
----------------

To send the flow we need to initialize the :class:`~pywa.client.WhatsApp` client with some specific parameters:

.. code-block:: python
    :linenos:

    import flask
    from pywa import WhatsApp

    flask_app = flask.Flask(__name__)

    wa = WhatsApp(
        phone_id="1234567890",
        token="abcdefg",
        server=flask_app,
        callback_url="https://my-server.com",
        webhook_endpoint="/webhook",
        verify_token="xyz123",
        app_id=123,
        app_secret="zzz",
        business_private_key=open("private.pem").read(),
        business_private_key_password="abc123",
    )


The :class:`~pywa.client.WhatsApp` class takes a few parameters:

- ``phone_id``: The phone ID of the WhatsApp account that we are using to send and receive messages
- ``token``: The token of the WhatsApp account that we are using to send and receive messages
- ``server``: The Flask app that we created earlier, which will be used to register the routes
- ``callback_url``: The URL that WhatsApp will use to send us updates
- ``webhook_endpoint``: The endpoint that WhatsApp will use to send us updates
- ``verify_token``: Used by WhatsApp to challenge the server when we register the webhook
- ``app_id``: The ID of the WhatsApp App, needed to register the callback URL
- ``app_secret``: The secret of the WhatsApp App, needed to register the callback URL
- ``business_private_key``: The private key of the WhatsApp Business Account, needed to decrypt the flow requests (see `here <../flows/overview.html#handling-flow-requests-and-responding-to-them>`_ for more info)
- ``business_private_key_password``: The passphrase of the private_key, if it has one


First let's send the flow!

.. code-block:: python
    :linenos:

    from pywa.types import FlowButton
    from pywa.types.flows import FlowStatus, FlowActionType

    wa.send_message(
        to="1234567890",
        text="Welcome to our app! Click the button below to login or sign up",
        buttons=[
            FlowButton(
                title="Sign Up",
                flow_id=flow_id,
                flow_token="5749d4f8-4b74-464a-8405-c26b7770cc8c",
                mode=FlowStatus.DRAFT,
                flow_action_type=FlowActionType.NAVIGATE,
                flow_action_screen="START",
            ),
        ],
    )

Ok, let's break this down:

Sending a flow is very simple. We sending text (or image, video etc.) message with a :class:`~pywa.types.callback.FlowButton`. The FlowButton contains the following properties:

- ``title``: The title of the button (the text that the user will see on the button)
- ``flow_id``: The ID of the flow that we want to send
- ``mode``: The mode of the flow. We are using ``FlowStatus.DRAFT`` because we are still testing the flow. When we are ready to publish the flow, we can change the mode to ``FlowStatus.PUBLISHED``
- ``flow_action_type``: The action that will be triggered when the user clicks on the button. In this case, we are using ``FlowActionType.NAVIGATE`` to navigate to the ``START`` screen
- ``flow_action_screen``: The name of the screen that we want to navigate to. In this case, we are using ``START``

- ``flow_token``: The unique token for this specific flow.

When the flow request is sent to our server, we don't know which flow and which user the request is for. We only know the flow token.
So, the flow token is used to give us some context about the flow request. We can use the flow token to identify the user and the flow.
The flow token can be saved in a database or in-memory cache, and be mapped to the user ID and the flow ID (in cases you have multiple flows running at your application).
And when requests are coming, you can use the flow token to identify the user and the flow and make the appropriate actions for the request.

    The flow token can be also used to invalidate the flow, by raising FlowTokenNoLongerValid exception with appropriate error_message.

A good practice is to generate a unique token for each flow request. This way, we can be sure that the token is unique and that we can identify the user and the flow.
You can use the :mod:`uuid` module to generate a unique token:

.. code-block:: python
    :linenos:

    import uuid

    flow_token = str(uuid.uuid4())


After we create the WhatsApp instance and we send the flow, we can start listening to flow requests:

.. code-block:: python
    :linenos:

    from pywa.types.flows import FlowRequest, FlowResponse

    @wa.on_flow_request("/sign-up-flow")
    def on_sign_up_request(_: WhatsApp, flow: FlowRequest) -> FlowResponse | None:
        if flow.has_error:
            logging.error("Flow request has error: %s", flow.data)
            return

        ...


The :meth:`~pywa.client.WhatsApp.on_flow_request` decorator takes the endpoint URI as a parameter. This is the endpoint that we provided when we updated the flow's metadata.
So if the endpoint URI is ``https://my-server.com/sign-up-flow``, then the endpoint URI that we are listening to is ``/sign-up-flow``.

    Yes, you can point multiple flows to the same endpoint URI. But then you need to find a way to identify the flow by the flow token.
    I recommend creating a unique endpoint URI for each flow.


Our ``on_sign_up_request`` calback function takes two parameters:

- ``wa``: The :class:`~pywa.client.WhatsApp` class instance
- ``flow``: A :class:`FlowRequest` object, which contains the flow request data

The flow request contains the following properties:

- ``version``: The version of the flow data API that the flow request is using (you should use thisn version in the response)
- ``flow_token``: The token of the flow (the same token that we provided when we sent the flow)
- ``action``: The action type that was triggered the request. ``FlowActionType.DATA_EXCHANGE`` in our case.
- ``screen``: The name of the screen that the user is currently on (We have two screens with data exchange actions, so we need to know which screen the user is currently on)
- ``data``: The data that the action sent to the server (the ``payload`` property of the action)


In the top of the function, we are checking if the flow request has an error. If it does, we are logging the error and returning.

    By default, if the flow has error, ``pywa`` will ignore the callback return value and will acknowledge the error.
    This behavior can be changed by setting ``acknowledge_errors`` parameter to ``False`` in ``on_flow_request`` decorator.

Handling Sign Up Flow Requests
------------------------------

Now, let's handle the flow request. we can handle all the screens in one code block but for the sake of simplicity, we will handle each screen separately:

.. code-block:: python
    :linenos:

    def handle_signup_screen(request: FlowRequest) -> FlowResponse:

        if user_repository.exists(request.data["email"]):
            return FlowResponse(
                version=request.version,
                screen="LOGIN",
                error_message="You are already registered. Please login",
                data={
                    "email_initial_value": request.data["email"],
                    "password_initial_value": request.data["password"],
                },
            )
        elif request.data["password"] != request.data["confirm_password"]:
            return FlowResponse(
                version=request.version,
                screen=request.screen,
                error_message="Passwords do not match",
                data={
                    "first_name_initial_value": request.data["first_name"],
                    "last_name_initial_value": request.data["last_name"],
                    "email_initial_value": request.data["email"],
                    "password_initial_value": "",
                    "confirm_password_initial_value": "",
                },
            )
        elif not any(char.isdigit() for char in request.data["password"]):
            return FlowResponse(
                version=request.version,
                screen=request.screen,
                error_message="Password must contain at least one number",
                data={
                    "first_name_initial_value": request.data["first_name"],
                    "last_name_initial_value": request.data["last_name"],
                    "email_initial_value": request.data["email"],
                    "password_initial_value": "",
                    "confirm_password_initial_value": "",
                },
            )
        else:
            user_repository.create(request.data["email"], request.data)
            return FlowResponse(
                version=request.version,
                screen="LOGIN",
                data={
                    "email_initial_value": request.data["email"],
                    "password_initial_value": "",
                },
            )

So, what's going on here?

This function handles the ``SIGN_UP`` screen.
We need to check a few things:

- Check if the user is already registered. If they are, we need to navigate to the ``LOGIN`` screen and show an error message
- Check if the password and confirm password match. If they don't, we navigate again to ``SIGN_UP`` screen and show an error message
- Check if the password contains at least one number. If it doesn't, we navigate again to ``SIGN_UP`` screen and show an error message
- If everything is ok, we create the user and navigate to the ``LOGIN`` screen (with the email address already filled in 😋)

    Now you understand why ``SIGN_UP`` screen get's initial values? because we don't want the user to re-enter the data again if there is an error.
    From the same reason, ``LOGIN`` screen get's initial values too, so when the sign up succeeds, the user will be navigated to the ``LOGIN`` screen with the email address already filled in.

Handling Login Flow Requests
----------------------------

Now, let's handle the ``LOGIN`` screen:

.. code-block:: python
    :linenos:

    def handle_login_screen(request: FlowRequest) -> FlowResponse:

        if not user_repository.exists(request.flow_token):
            return FlowResponse(
                version=request.version,
                screen="SIGN_UP",
                error_message="You are not registered. Please sign up",
                data={
                    "first_name_initial_value": "",
                    "last_name_initial_value": "",
                    "email_initial_value": request.data["email"],
                    "password_initial_value": "",
                    "confirm_password_initial_value": "",
                },
            )
        elif not user_repository.is_password_valid(request.data["email"], request.data["password"]):
            return FlowResponse(
                version=request.version,
                screen=request.screen,
                error_message="Incorrect password",
                data={
                    "email_initial_value": request.data["email"],
                    "password_initial_value": "",
                },
            )
        else:
            return FlowResponse(
                version=request.version,
                screen="LOGIN_SUCCESS",
                data={},
            )

The ``LOGIN`` screen is very similar to the ``SIGN_UP`` screen. We need to check a few things:

- Check if the user is registered. If they are not, we need to navigate to the ``SIGN_UP`` screen and show an error message
- Check if the password is correct. If it's not, we need to navigate again to ``LOGIN`` screen and show an error message
- If everything is ok, we navigate to the ``LOGIN_SUCCESS`` screen

Handling the Flow Requests
--------------------------

Let's modify out ``on_sign_up_request`` callback function to handle the ``SIGN_UP`` and ``LOGIN`` screens:

.. code-block:: python
    :linenos:

    @wa.on_flow_request("/sign-up-flow")
    def on_sign_up_request(_: WhatsApp, flow: FlowRequest) -> FlowResponse | None:
        if flow.has_error:
            logging.error("Flow request has error: %s", flow.data)
            return

        if flow.screen == "SIGN_UP":
            return handle_signup_screen(flow)
        elif flow.screen == "LOGIN":
            return handle_login_screen(flow)


Handling Flow Completion
------------------------

The ``LOGIN_SUCCESS`` scrren completes the flow, so we don't need to do anything here. instead we need to handle the flow completion:

.. code-block:: python
    :linenos:

    @wa.on_flow_completion()
    def handle_flow_completion(_: WhatsApp, flow: FlowCompletion):
        print("Flow completed successfully")
        print(flow.token)
        print(flow.payload)

Now, in a real application, this is the time to mark the user as logged in and allow them to perform actions in their account.
You can also implement some kind of session management, so that the user will stay logged in for a certain amount of time and then require them to login again.

Running the Server
------------------

The last thing that we need to do is run the server:

.. code-block:: python
    :linenos:

    if __name__ == "__main__":
        flask_app.run()

What's Next?
------------

Now that you know how to create and send a flow, you can try to add the following features to the flow:

- A ``FORGOT_PASSWORD`` screen, which allows the user to reset their password if they forgot it
- A more detailed ``LOGIN_SUCCESS`` screen, which shows the user's name, email address and other details
- Try to adding a nice image to the ``START`` screen, to make it more appealing
- A ``LOGOUT`` screen, which allows the user to logout from their account
- Allow the user to change their email & password
- Allow the user to close the flow at any screen
