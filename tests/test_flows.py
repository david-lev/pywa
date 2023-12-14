import json

from pywa.types.flows import (
    FlowJSON,
    Screen,
    Layout,
    LayoutType,
    Form,
    TextInput,
    InputType,
    Footer,
    Action,
    FlowActionType,
    ActionNext,
    ActionNextType,
    TextHeading,
    TextSubheading,
    RadioButtonsGroup,
    DataSource,
    TextArea,
    Dropdown,
    CheckboxGroup,
    TextBody,
    OptIn,
    EmbeddedLink,
)

FLOWS_VERSION = "2.1"

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

load_re_engagement = FlowJSON(
    version="2.1",
    screens=[
        Screen(
            id="SIGN_UP",
            title="Finish Sign Up",
            terminal=True,
            data={},
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    Form(
                        name="form",
                        children=[
                            TextInput(
                                name="firstName",
                                label="First Name",
                                input_type=InputType.TEXT,
                                required=True,
                                visible=True,
                            ),
                            TextInput(
                                name="lastName",
                                label="Last Name",
                                input_type=InputType.TEXT,
                                required=True,
                                visible=True,
                            ),
                            TextInput(
                                name="email",
                                label="Email Address",
                                input_type=InputType.EMAIL,
                                required=True,
                                visible=True,
                            ),
                            Footer(
                                label="Done",
                                enabled=True,
                                on_click_action=Action(
                                    name=FlowActionType.COMPLETE,
                                    payload={
                                        "firstName": "${form.firstName}",
                                        "lastName": "${form.lastName}",
                                        "email": "${form.email}",
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

costumer_engagement = FlowJSON(
    version="2.1",
    screens=[
        Screen(
            id="QUESTION_ONE",
            title="Question 1 of 3",
            data={},
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    Form(
                        name="form",
                        children=[
                            TextHeading(
                                text="You've found the perfect deal, what do you do next?"
                            ),
                            CheckboxGroup(
                                name="question1Checkbox",
                                label="Choose all that apply:",
                                required=True,
                                data_source=[
                                    DataSource(id="0", title="Buy it right away"),
                                    DataSource(
                                        id="1", title="Check reviews before buying"
                                    ),
                                    DataSource(
                                        id="2", title="Share it with friends + family"
                                    ),
                                    DataSource(
                                        id="3", title="Buy multiple, while its cheap"
                                    ),
                                    DataSource(id="4", title="None of the above"),
                                ],
                            ),
                            Footer(
                                label="Continue",
                                on_click_action=Action(
                                    name=FlowActionType.NAVIGATE,
                                    next=ActionNext(
                                        type=ActionNextType.SCREEN, name="QUESTION_TWO"
                                    ),
                                    payload={
                                        "question1Checkbox": "${form.question1Checkbox}"
                                    },
                                ),
                            ),
                        ],
                    )
                ],
            ),
        ),
        Screen(
            id="QUESTION_TWO",
            title="Question 2 of 3",
            data={
                "question1Checkbox": {
                    "type": "array",
                    "items": {"type": "string"},
                    "__example__": [],
                }
            },
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    Form(
                        name="form",
                        children=[
                            TextHeading(
                                text="Its your birthday in two weeks, how might you prepare?"
                            ),
                            RadioButtonsGroup(
                                name="question2RadioButtons",
                                label="Choose all that apply:",
                                required=True,
                                data_source=[
                                    DataSource(id="0", title="Buy something new"),
                                    DataSource(id="1", title="Wear the same, as usual"),
                                    DataSource(id="2", title="Look for a deal online"),
                                ],
                            ),
                            Footer(
                                label="Continue",
                                on_click_action=Action(
                                    name=FlowActionType.NAVIGATE,
                                    next=ActionNext(
                                        type=ActionNextType.SCREEN,
                                        name="QUESTION_THREE",
                                    ),
                                    payload={
                                        "question2RadioButtons": "${form.question2RadioButtons}",
                                        "question1Checkbox": "${data.question1Checkbox}",
                                    },
                                ),
                            ),
                        ],
                    )
                ],
            ),
        ),
        Screen(
            id="QUESTION_THREE",
            title="Question 3 of 3",
            data={
                "question2RadioButtons": {"type": "string", "__example__": "Example"},
                "question1Checkbox": {
                    "type": "array",
                    "items": {"type": "string"},
                    "__example__": [],
                },
            },
            terminal=True,
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    Form(
                        name="form",
                        children=[
                            TextHeading(text="What's the best gift for a friend?"),
                            CheckboxGroup(
                                name="question3Checkbox",
                                label="Choose all that apply:",
                                required=True,
                                data_source=[
                                    DataSource(id="0", title="A gift voucher"),
                                    DataSource(id="1", title="A new outfit "),
                                    DataSource(id="2", title="A bouquet of flowers"),
                                    DataSource(id="3", title="A meal out together"),
                                ],
                            ),
                            Footer(
                                label="Done",
                                on_click_action=Action(
                                    name=FlowActionType.COMPLETE,
                                    payload={
                                        "question1Checkbox": "${data.question1Checkbox}",
                                        "question2RadioButtons": "${data.question2RadioButtons}",
                                        "question3Checkbox": "${form.question3Checkbox}",
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

support_request = FlowJSON(
    version="2.1",
    screens=[
        Screen(
            id="DETAILS",
            title="Get help",
            data={},
            terminal=True,
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
                            ),
                            TextInput(
                                label="Order number",
                                name="orderNumber",
                                input_type=InputType.NUMBER,
                                required=True,
                                helper_text="",
                            ),
                            RadioButtonsGroup(
                                label="Choose a topic",
                                name="topicRadio",
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
                                label="Description of issue",
                                required=False,
                                name="description",
                            ),
                            Footer(
                                label="Done",
                                on_click_action=Action(
                                    name=FlowActionType.COMPLETE,
                                    payload={
                                        "name": "${form.name}",
                                        "orderNumber": "${form.orderNumber}",
                                        "topicRadio": "${form.topicRadio}",
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

communication_preferences = FlowJSON(
    version="2.1",
    screens=[
        Screen(
            id="PREFERENCES",
            title="Update Preferences",
            data={},
            terminal=True,
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    Form(
                        name="form",
                        children=[
                            CheckboxGroup(
                                label="Communication types",
                                required=True,
                                name="communicationTypes",
                                data_source=[
                                    DataSource(
                                        id="0", title="Special offers and promotions"
                                    ),
                                    DataSource(
                                        id="1", title="Changes to my subscription"
                                    ),
                                    DataSource(id="2", title="News and events"),
                                    DataSource(id="3", title="New products"),
                                ],
                            ),
                            CheckboxGroup(
                                label="Contact Preferences",
                                required=False,
                                name="contactPrefs",
                                data_source=[
                                    DataSource(id="0", title="Whatsapp"),
                                    DataSource(id="1", title="Email"),
                                    DataSource(id="2", title="SMS"),
                                ],
                            ),
                            Footer(
                                label="Done",
                                on_click_action=Action(
                                    name=FlowActionType.COMPLETE,
                                    payload={
                                        "communicationTypes": "${form.communicationTypes}",
                                        "contactPrefs": "${form.contactPrefs}",
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

register_for_an_event = FlowJSON(
    version="2.1",
    screens=[
        Screen(
            id="SIGN_UP",
            title="Sign Up",
            data={},
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    Form(
                        name="form",
                        children=[
                            TextHeading(text="Join our next webinar!"),
                            TextBody(text="First, we'll need a few details from you."),
                            TextInput(
                                name="firstName",
                                label="First Name",
                                input_type=InputType.TEXT,
                                required=True,
                            ),
                            TextInput(
                                label="Last Name",
                                name="lastName",
                                input_type=InputType.TEXT,
                                required=True,
                            ),
                            TextInput(
                                label="Email Address",
                                name="email",
                                input_type=InputType.EMAIL,
                                required=True,
                            ),
                            Footer(
                                label="Continue",
                                on_click_action=Action(
                                    name=FlowActionType.NAVIGATE,
                                    next=ActionNext(
                                        type=ActionNextType.SCREEN, name="SURVEY"
                                    ),
                                    payload={
                                        "firstName": "${form.firstName}",
                                        "lastName": "${form.lastName}",
                                        "email": "${form.email}",
                                    },
                                ),
                            ),
                        ],
                    )
                ],
            ),
        ),
        Screen(
            id="SURVEY",
            title="Thank you",
            data={
                "firstName": {"type": "string", "__example__": "Example"},
                "lastName": {"type": "string", "__example__": "Example"},
                "email": {"type": "string", "__example__": "Example"},
            },
            terminal=True,
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    Form(
                        name="form",
                        children=[
                            TextHeading(text="Before you go"),
                            TextBody(text="How did you hear about us?"),
                            RadioButtonsGroup(
                                name="source",
                                label="Choose one",
                                required=False,
                                data_source=[
                                    DataSource(id="0", title="Friend's recommendation"),
                                    DataSource(id="1", title="TV advertisement"),
                                    DataSource(id="2", title="Search engine"),
                                    DataSource(id="3", title="Social media"),
                                ],
                            ),
                            Footer(
                                label="Done",
                                on_click_action=Action(
                                    name=FlowActionType.COMPLETE,
                                    payload={
                                        "source": "${form.source}",
                                        "firstName": "${data.firstName}",
                                        "lastName": "${data.lastName}",
                                        "email": "${data.email}",
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

sign_in = FlowJSON(
    version="2.1",
    data_api_version="3.0",
    data_channel_uri="https://example.com",
    routing_model={
        "SIGN_IN": ["SIGN_UP", "FORGOT_PASSWORD"],
        "SIGN_UP": ["TERMS_AND_CONDITIONS"],
        "FORGOT_PASSWORD": [],
        "TERMS_AND_CONDITIONS": [],
    },
    screens=[
        Screen(
            id="SIGN_IN",
            title="Sign in",
            terminal=True,
            data={},
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    Form(
                        name="sign_in_form",
                        children=[
                            TextInput(
                                name="email",
                                label="Email address",
                                input_type=InputType.EMAIL,
                                required=True,
                            ),
                            TextInput(
                                name="password",
                                label="Password",
                                input_type=InputType.PASSWORD,
                                required=True,
                            ),
                            EmbeddedLink(
                                text="Don't have an account? Sign up",
                                on_click_action=Action(
                                    name=FlowActionType.NAVIGATE,
                                    next=ActionNext(
                                        type=ActionNextType.SCREEN, name="SIGN_UP"
                                    ),
                                    payload={},
                                ),
                            ),
                            EmbeddedLink(
                                text="Forgot password",
                                on_click_action=Action(
                                    name=FlowActionType.NAVIGATE,
                                    next=ActionNext(
                                        type=ActionNextType.SCREEN,
                                        name="FORGOT_PASSWORD",
                                    ),
                                    payload={"body": "Example"},
                                ),
                            ),
                            Footer(
                                label="Sign in",
                                on_click_action=Action(
                                    name=FlowActionType.DATA_EXCHANGE,
                                    payload={
                                        "email": "${form.email}",
                                        "password": "${form.password}",
                                    },
                                ),
                            ),
                        ],
                    )
                ],
            ),
        ),
        Screen(
            id="SIGN_UP",
            title="Sign up",
            data={},
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    Form(
                        name="sign_up_form",
                        children=[
                            TextInput(
                                name="first_name",
                                label="First Name",
                                input_type=InputType.TEXT,
                                required=True,
                            ),
                            TextInput(
                                name="last_name",
                                label="Last Name",
                                input_type=InputType.TEXT,
                                required=True,
                            ),
                            TextInput(
                                name="email",
                                label="Email address",
                                input_type=InputType.EMAIL,
                                required=True,
                            ),
                            TextInput(
                                name="password",
                                label="Set password",
                                input_type=InputType.PASSWORD,
                                required=True,
                            ),
                            TextInput(
                                name="confirm_password",
                                label="Confirm password",
                                input_type=InputType.PASSWORD,
                                required=True,
                            ),
                            OptIn(
                                name="terms_agreement",
                                label="I agree with the terms.",
                                required=True,
                                on_click_action=Action(
                                    name=FlowActionType.NAVIGATE,
                                    next=ActionNext(
                                        type=ActionNextType.SCREEN,
                                        name="TERMS_AND_CONDITIONS",
                                    ),
                                    payload={},
                                ),
                            ),
                            OptIn(
                                name="offers_acceptance",
                                label="I would like to receive news and offers.",
                            ),
                            Footer(
                                label="Continue",
                                on_click_action=Action(
                                    name=FlowActionType.DATA_EXCHANGE,
                                    payload={
                                        "first_name": "${form.first_name}",
                                        "last_name": "${form.last_name}",
                                        "email": "${form.email}",
                                        "password": "${form.password}",
                                        "confirm_password": "${form.confirm_password}",
                                        "terms_agreement": "${form.terms_agreement}",
                                        "offers_acceptance": "${form.offers_acceptance}",
                                    },
                                ),
                            ),
                        ],
                    )
                ],
            ),
        ),
        Screen(
            id="FORGOT_PASSWORD",
            title="Forgot password",
            terminal=True,
            data={
                "body": {
                    "type": "string",
                    "__example__": "Enter your email address for your account and we'll send a reset link. The single-use link will expire after 24 hours.",
                }
            },
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    Form(
                        name="forgot_password_form",
                        children=[
                            TextBody(text="${data.body}"),
                            TextInput(
                                name="email",
                                label="Email address",
                                input_type=InputType.EMAIL,
                                required=True,
                            ),
                            Footer(
                                label="Sign in",
                                on_click_action=Action(
                                    name=FlowActionType.DATA_EXCHANGE,
                                    payload={"email": "${form.email}"},
                                ),
                            ),
                        ],
                    )
                ],
            ),
        ),
        Screen(
            id="TERMS_AND_CONDITIONS",
            title="Terms and conditions",
            data={},
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    TextHeading(text="Our Terms"),
                    TextSubheading(text="Data usage"),
                    TextBody(
                        text="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed vitae odio dui. Praesent ut nulla tincidunt, scelerisque augue malesuada, volutpat lorem. Aliquam iaculis ex at diam posuere mollis. Suspendisse eget purus ac tellus interdum pharetra. In quis dolor turpis. Fusce in porttitor enim, vitae efficitur nunc. Fusce dapibus finibus volutpat. Fusce velit mi, ullamcorper ac gravida vitae, blandit quis ex. Fusce ultrices diam et justo blandit, quis consequat nisl euismod. Vestibulum pretium est sem, vitae convallis justo sollicitudin non. Morbi bibendum purus mattis quam condimentum, a scelerisque erat bibendum. Nullam sit amet bibendum lectus."
                    ),
                    TextSubheading(text="Privacy policy"),
                    TextBody(
                        text="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed vitae odio dui. Praesent ut nulla tincidunt, scelerisque augue malesuada, volutpat lorem. Aliquam iaculis ex at diam posuere mollis. Suspendisse eget purus ac tellus interdum pharetra. In quis dolor turpis. Fusce in porttitor enim, vitae efficitur nunc. Fusce dapibus finibus volutpat. Fusce velit mi, ullamcorper ac gravida vitae, blandit quis ex. Fusce ultrices diam et justo blandit, quis consequat nisl euismod. Vestibulum pretium est sem, vitae convallis justo sollicitudin non. Morbi bibendum purus mattis quam condimentum, a scelerisque erat bibendum. Nullam sit amet bibendum lectus."
                    ),
                ],
            ),
        ),
    ],
)

register = FlowJSON(
    version="2.1",
    data_api_version="3.0",
    data_channel_uri="https://example.com",
    routing_model={"REGISTER": ["TERMS_AND_CONDITIONS"], "TERMS_AND_CONDITIONS": []},
    screens=[
        Screen(
            id="REGISTER",
            title="Register for an account",
            terminal=True,
            data={
                "error_messages": {
                    "type": "object",
                    "__example__": {"confirm_password": "Passwords don't match."},
                }
            },
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    Form(
                        name="register_form",
                        error_messages="${data.error_messages}",
                        children=[
                            TextInput(
                                name="first_name",
                                required=True,
                                label="First name",
                                input_type="text",
                            ),
                            TextInput(
                                name="last_name",
                                required=True,
                                label="Last name",
                                input_type="text",
                            ),
                            TextInput(
                                name="email",
                                required=True,
                                label="Email address",
                                input_type="email",
                            ),
                            TextInput(
                                name="password",
                                required=True,
                                label="Set password",
                                input_type="password",
                            ),
                            TextInput(
                                name="confirm_password",
                                required=True,
                                label="Confirm password",
                                input_type="password",
                            ),
                            OptIn(
                                name="terms_agreement",
                                label="I agree with the terms.",
                                required=True,
                                on_click_action=Action(
                                    name=FlowActionType.NAVIGATE,
                                    next=ActionNext(
                                        type=ActionNextType.SCREEN,
                                        name="TERMS_AND_CONDITIONS",
                                    ),
                                    payload={},
                                ),
                            ),
                            OptIn(
                                name="offers_acceptance",
                                label="I would like to receive news and offers.",
                            ),
                            Footer(
                                label="Continue",
                                on_click_action=Action(
                                    name=FlowActionType.DATA_EXCHANGE,
                                    payload={
                                        "first_name": "${form.first_name}",
                                        "last_name": "${form.last_name}",
                                        "email": "${form.email}",
                                        "password": "${form.password}",
                                        "confirm_password": "${form.confirm_password}",
                                        "terms_agreement": "${form.terms_agreement}",
                                        "offers_acceptance": "${form.offers_acceptance}",
                                    },
                                ),
                            ),
                        ],
                    )
                ],
            ),
        ),
        Screen(
            id="TERMS_AND_CONDITIONS",
            title="Terms and conditions",
            data={},
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    TextHeading(text="Our Terms"),
                    TextSubheading(text="Data usage"),
                    TextBody(
                        text="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed vitae odio dui. Praesent ut nulla tincidunt, scelerisque augue malesuada, volutpat lorem. Aliquam iaculis ex at diam posuere mollis. Suspendisse eget purus ac tellus interdum pharetra. In quis dolor turpis. Fusce in porttitor enim, vitae efficitur nunc. Fusce dapibus finibus volutpat. Fusce velit mi, ullamcorper ac gravida vitae, blandit quis ex. Fusce ultrices diam et justo blandit, quis consequat nisl euismod. Vestibulum pretium est sem, vitae convallis justo sollicitudin non. Morbi bibendum purus mattis quam condimentum, a scelerisque erat bibendum. Nullam sit amet bibendum lectus."
                    ),
                    TextSubheading(text="Privacy policy"),
                    TextBody(
                        text="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed vitae odio dui. Praesent ut nulla tincidunt, scelerisque augue malesuada, volutpat lorem. Aliquam iaculis ex at diam posuere mollis. Suspendisse eget purus ac tellus interdum pharetra. In quis dolor turpis. Fusce in porttitor enim, vitae efficitur nunc. Fusce dapibus finibus volutpat. Fusce velit mi, ullamcorper ac gravida vitae, blandit quis ex. Fusce ultrices diam et justo blandit, quis consequat nisl euismod. Vestibulum pretium est sem, vitae convallis justo sollicitudin non. Morbi bibendum purus mattis quam condimentum, a scelerisque erat bibendum. Nullam sit amet bibendum lectus."
                    ),
                ],
            ),
        ),
    ],
)


get_a_quote = FlowJSON(
    version="2.1",
    data_api_version="3.0",
    data_channel_uri="https://example.com",
    routing_model={
        "DETAILS": ["COVER"],
        "COVER": ["QUOTE"],
        "QUOTE": ["TERMS_AND_CONDITIONS"],
        "TERMS_AND_CONDITIONS": [],
    },
    screens=[
        Screen(
            id="DETAILS",
            title="Your details",
            data={
                "city": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "title": {"type": "string"},
                        },
                    },
                    "__example__": [{"id": "1", "title": "Light City, SO"}],
                }
            },
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    Form(
                        name="details_form",
                        children=[
                            TextInput(
                                label="Your name",
                                input_type=InputType.TEXT,
                                name="name",
                                required=True,
                            ),
                            TextInput(
                                label="Street address",
                                input_type=InputType.TEXT,
                                name="address",
                                required=True,
                            ),
                            Dropdown(
                                label="City, State",
                                name="city",
                                data_source="${data.city}",
                                required=True,
                            ),
                            TextInput(
                                label="Zip code",
                                input_type=InputType.TEXT,
                                name="zip_code",
                                required=True,
                            ),
                            TextInput(
                                label="Country/Region",
                                input_type=InputType.TEXT,
                                name="country_region",
                                required=True,
                            ),
                            Footer(
                                label="Continue",
                                on_click_action=Action(
                                    name=FlowActionType.DATA_EXCHANGE,
                                    payload={
                                        "name": "${form.name}",
                                        "address": "${form.address}",
                                        "city": "${form.city}",
                                        "zip_code": "${form.zip_code}",
                                        "country_region": "${form.country_region}",
                                    },
                                ),
                            ),
                        ],
                    )
                ],
            ),
        ),
        Screen(
            id="COVER",
            title="Your cover",
            data={
                "options": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                        },
                    },
                    "__example__": [
                        {
                            "id": "1",
                            "title": "Fire and theft",
                            "description": "Cover your home against incidents of theft or accidental fires",
                        },
                        {
                            "id": "2",
                            "title": "Natural disaster",
                            "description": "Protect your home against disasters including earthquakes, floods and storms",
                        },
                        {
                            "id": "3",
                            "title": "Liability",
                            "description": "Protect yourself from legal liabilities that occur from accidents on your property",
                        },
                    ],
                }
            },
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    Form(
                        name="cover_form",
                        children=[
                            CheckboxGroup(
                                name="options",
                                data_source="${data.options}",
                                label="Options",
                                required=True,
                            ),
                            Footer(
                                label="Continue",
                                on_click_action=Action(
                                    name=FlowActionType.DATA_EXCHANGE,
                                    payload={"options": "${form.options}"},
                                ),
                            ),
                        ],
                    )
                ],
            ),
        ),
        Screen(
            id="QUOTE",
            title="Your quote",
            terminal=True,
            data={
                "excess": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "title": {"type": "string"},
                        },
                    },
                    "__example__": [{"id": "1", "title": "$250"}],
                },
                "total": {"type": "string", "__example__": "$47.98 per month"},
            },
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    Form(
                        name="quote_form",
                        init_values={"payment_options": "1"},
                        children=[
                            Dropdown(
                                label="Excess",
                                name="excess",
                                data_source="${data.excess}",
                                on_select_action=Action(
                                    name=FlowActionType.DATA_EXCHANGE,
                                    payload={"excess": "${form.excess}"},
                                ),
                                required=True,
                            ),
                            RadioButtonsGroup(
                                name="payment_options",
                                label="Payment options",
                                data_source=[
                                    DataSource(id="1", title="Monthly"),
                                    DataSource(id="2", title="Annually (Save $115)"),
                                ],
                                on_select_action=Action(
                                    name=FlowActionType.DATA_EXCHANGE,
                                    payload={
                                        "payment_options": "${form.payment_options}"
                                    },
                                ),
                                required=True,
                            ),
                            TextHeading(text="${data.total}"),
                            OptIn(
                                name="privacy_policy",
                                label="Accept our Privacy Policy",
                                required=True,
                                on_click_action=Action(
                                    name=FlowActionType.NAVIGATE,
                                    next=ActionNext(
                                        type=ActionNextType.SCREEN,
                                        name="TERMS_AND_CONDITIONS",
                                    ),
                                    payload={},
                                ),
                            ),
                            Footer(
                                label="Choose quote",
                                on_click_action=Action(
                                    name=FlowActionType.DATA_EXCHANGE,
                                    payload={
                                        "privacy_policy": "${form.privacy_policy}"
                                    },
                                ),
                            ),
                        ],
                    )
                ],
            ),
        ),
        Screen(
            id="TERMS_AND_CONDITIONS",
            title="Terms and conditions",
            data={},
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    TextHeading(text="Our Terms"),
                    TextSubheading(text="Data usage"),
                    TextBody(
                        text="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed vitae odio dui. Praesent ut nulla tincidunt, scelerisque augue malesuada, volutpat lorem. Aliquam iaculis ex at diam posuere mollis. Suspendisse eget purus ac tellus interdum pharetra. In quis dolor turpis. Fusce in porttitor enim, vitae efficitur nunc. Fusce dapibus finibus volutpat. Fusce velit mi, ullamcorper ac gravida vitae, blandit quis ex. Fusce ultrices diam et justo blandit, quis consequat nisl euismod. Vestibulum pretium est sem, vitae convallis justo sollicitudin non. Morbi bibendum purus mattis quam condimentum, a scelerisque erat bibendum. Nullam sit amet bibendum lectus."
                    ),
                    TextSubheading(text="Privacy policy"),
                    TextBody(
                        text="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed vitae odio dui. Praesent ut nulla tincidunt, scelerisque augue malesuada, volutpat lorem. Aliquam iaculis ex at diam posuere mollis. Suspendisse eget purus ac tellus interdum pharetra. In quis dolor turpis. Fusce in porttitor enim, vitae efficitur nunc. Fusce dapibus finibus volutpat. Fusce velit mi, ullamcorper ac gravida vitae, blandit quis ex. Fusce ultrices diam et justo blandit, quis consequat nisl euismod. Vestibulum pretium est sem, vitae convallis justo sollicitudin non. Morbi bibendum purus mattis quam condimentum, a scelerisque erat bibendum. Nullam sit amet bibendum lectus."
                    ),
                ],
            ),
        ),
    ],
)

FLOWS = {
    "customer_satisfaction_survey": customer_satisfaction_survey,
    "load_re_engagement": load_re_engagement,
    "costumer_engagement": costumer_engagement,
    "support_request": support_request,
    "communication_preferences": communication_preferences,
    "register_for_an_event": register_for_an_event,
    "sign_in": sign_in,
    "register": register,
    "get_a_quote": get_a_quote,
}


def test_flows_to_json():
    with open(f"tests/data/flows/{FLOWS_VERSION}/examples.json", "r") as f:
        examples = json.load(f)
    for flow_name, flow in FLOWS.items():
        assert flow.to_dict() == examples[flow_name]
