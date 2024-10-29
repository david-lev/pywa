import dataclasses
import json

import pytest

from pywa import WhatsApp, handlers, utils, filters
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
    ScreenDataRef,
    ComponentRef,
    ScreenData,
    FlowResponse,
    FlowRequest,
    FlowRequestActionType,
    FlowJSONEncoder,
    Switch,
    If,
    Ref,
)
from pywa.utils import Version

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
                            recommend_radio := RadioButtonsGroup(
                                name="recommend_radio",
                                label="Choose one",
                                data_source=[
                                    DataSource(id="0", title="Yes"),
                                    DataSource(id="1", title="No"),
                                ],
                                required=True,
                            ),
                            TextSubheading(text="How could we do better?"),
                            comment_text := TextArea(
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
                                        "recommend_radio": recommend_radio.ref,
                                        "comment_text": comment_text.ref,
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
            data=[
                recommend_radio := ScreenData(key="recommend_radio", example="Example"),
                comment_text := ScreenData(key="comment_text", example="Example"),
            ],
            terminal=True,
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    Form(
                        name="form",
                        children=[
                            TextSubheading(text="Rate the following: "),
                            purchase_rating := Dropdown(
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
                            delivery_rating := Dropdown(
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
                            cs_rating := Dropdown(
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
                                        "purchase_rating": purchase_rating.ref,
                                        "delivery_rating": delivery_rating.ref,
                                        "cs_rating": cs_rating.ref,
                                        "recommend_radio": recommend_radio.ref,
                                        "comment_text": comment_text.ref,
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
                            first_name := TextInput(
                                name="firstName",
                                label="First Name",
                                input_type=InputType.TEXT,
                                required=True,
                                visible=True,
                            ),
                            last_name := TextInput(
                                name="lastName",
                                label="Last Name",
                                input_type=InputType.TEXT,
                                required=True,
                                visible=True,
                            ),
                            email := TextInput(
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
                                        "firstName": first_name.ref,
                                        "lastName": last_name.ref,
                                        "email": email.ref,
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
                            question1_checkbox := CheckboxGroup(
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
                                        "question1Checkbox": question1_checkbox.ref
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
            data=[
                question1_checkbox := ScreenData(
                    key="question1Checkbox", example=["Example", "Example2"]
                ),
            ],
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    Form(
                        name="form",
                        children=[
                            TextHeading(
                                text="Its your birthday in two weeks, how might you prepare?"
                            ),
                            question2_radio_buttons := RadioButtonsGroup(
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
                                        "question2RadioButtons": question2_radio_buttons.ref,
                                        "question1Checkbox": question1_checkbox.ref,
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
            data=[
                question2_radio_buttons := ScreenData(
                    key="question2RadioButtons", example="Example"
                ),
                question1_checkbox := ScreenData(
                    key="question1Checkbox", example=["Example", "Example2"]
                ),
            ],
            terminal=True,
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    Form(
                        name="form",
                        children=[
                            TextHeading(text="What's the best gift for a friend?"),
                            question3_checkbox := CheckboxGroup(
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
                                        "question1Checkbox": question1_checkbox.ref,
                                        "question2RadioButtons": question2_radio_buttons.ref,
                                        "question3Checkbox": question3_checkbox.ref,
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
                            name := TextInput(
                                name="name",
                                label="Name",
                                input_type=InputType.TEXT,
                                required=True,
                            ),
                            order_number := TextInput(
                                label="Order number",
                                name="orderNumber",
                                input_type=InputType.NUMBER,
                                required=True,
                                helper_text="",
                            ),
                            topic_radio := RadioButtonsGroup(
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
                            desc := TextArea(
                                label="Description of issue",
                                required=False,
                                name="description",
                            ),
                            Footer(
                                label="Done",
                                on_click_action=Action(
                                    name=FlowActionType.COMPLETE,
                                    payload={
                                        "name": name.ref,
                                        "orderNumber": order_number.ref,
                                        "topicRadio": topic_radio.ref,
                                        "description": desc.ref,
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
                            communication_types := CheckboxGroup(
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
                            contact_prefs := CheckboxGroup(
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
                                        "communicationTypes": communication_types.ref,
                                        "contactPrefs": contact_prefs.ref,
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
                            first_name := TextInput(
                                name="firstName",
                                label="First Name",
                                input_type=InputType.TEXT,
                                required=True,
                            ),
                            last_name := TextInput(
                                label="Last Name",
                                name="lastName",
                                input_type=InputType.TEXT,
                                required=True,
                            ),
                            email := TextInput(
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
                                        "firstName": first_name.ref,
                                        "lastName": last_name.ref,
                                        "email": email.ref,
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
            data=[
                first_name := ScreenData(key="firstName", example="Example"),
                last_name := ScreenData(key="lastName", example="Example"),
                email := ScreenData(key="email", example="Example"),
            ],
            terminal=True,
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    Form(
                        name="form",
                        children=[
                            TextHeading(text="Before you go"),
                            TextBody(text="How did you hear about us?"),
                            source := RadioButtonsGroup(
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
                                        "source": source.ref,
                                        "firstName": first_name.ref,
                                        "lastName": last_name.ref,
                                        "email": email.ref,
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
                            email := TextInput(
                                name="email",
                                label="Email address",
                                input_type=InputType.EMAIL,
                                required=True,
                            ),
                            password := TextInput(
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
                                        "email": email.ref,
                                        "password": password.ref,
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
                                label="Email address",
                                input_type=InputType.EMAIL,
                                required=True,
                            ),
                            password := TextInput(
                                name="password",
                                label="Set password",
                                input_type=InputType.PASSWORD,
                                required=True,
                            ),
                            confirm_password := TextInput(
                                name="confirm_password",
                                label="Confirm password",
                                input_type=InputType.PASSWORD,
                                required=True,
                            ),
                            terms_agreement := OptIn(
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
                            offers_acceptance := OptIn(
                                name="offers_acceptance",
                                label="I would like to receive news and offers.",
                            ),
                            Footer(
                                label="Continue",
                                on_click_action=Action(
                                    name=FlowActionType.DATA_EXCHANGE,
                                    payload={
                                        "first_name": first_name.ref,
                                        "last_name": last_name.ref,
                                        "email": email.ref,
                                        "password": password.ref,
                                        "confirm_password": confirm_password.ref,
                                        "terms_agreement": terms_agreement.ref,
                                        "offers_acceptance": offers_acceptance.ref,
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
            data=[
                body := ScreenData(
                    key="body",
                    example=(
                        "Enter your email address for your account and we'll send a reset link. "
                        "The single-use link will expire after 24 hours."
                    ),
                ),
            ],
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    Form(
                        name="forgot_password_form",
                        children=[
                            TextBody(text=body.ref),
                            email := TextInput(
                                name="email",
                                label="Email address",
                                input_type=InputType.EMAIL,
                                required=True,
                            ),
                            Footer(
                                label="Sign in",
                                on_click_action=Action(
                                    name=FlowActionType.DATA_EXCHANGE,
                                    payload={"email": email.ref},
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
            data=[
                error_messages := ScreenData(
                    key="error_messages",
                    example={"confirm_password": "Passwords don't match."},
                ),
            ],
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    Form(
                        name="register_form",
                        error_messages=error_messages.ref,
                        children=[
                            first_name := TextInput(
                                name="first_name",
                                required=True,
                                label="First name",
                                input_type="text",
                            ),
                            last_name := TextInput(
                                name="last_name",
                                required=True,
                                label="Last name",
                                input_type="text",
                            ),
                            email := TextInput(
                                name="email",
                                required=True,
                                label="Email address",
                                input_type="email",
                            ),
                            password := TextInput(
                                name="password",
                                required=True,
                                label="Set password",
                                input_type="password",
                            ),
                            confirm_password := TextInput(
                                name="confirm_password",
                                required=True,
                                label="Confirm password",
                                input_type="password",
                            ),
                            terms_agreement := OptIn(
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
                            offers_acceptance := OptIn(
                                name="offers_acceptance",
                                label="I would like to receive news and offers.",
                            ),
                            Footer(
                                label="Continue",
                                on_click_action=Action(
                                    name=FlowActionType.DATA_EXCHANGE,
                                    payload={
                                        "first_name": first_name.ref,
                                        "last_name": last_name.ref,
                                        "email": email.ref,
                                        "password": password.ref,
                                        "confirm_password": confirm_password.ref,
                                        "terms_agreement": terms_agreement.ref,
                                        "offers_acceptance": offers_acceptance.ref,
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
            data=[
                city := ScreenData(
                    key="city", example=[DataSource(id="1", title="Light City, SO")]
                ),
            ],
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    Form(
                        name="details_form",
                        children=[
                            name := TextInput(
                                label="Your name",
                                input_type=InputType.TEXT,
                                name="name",
                                required=True,
                            ),
                            address := TextInput(
                                label="Street address",
                                input_type=InputType.TEXT,
                                name="address",
                                required=True,
                            ),
                            city := Dropdown(
                                label="City, State",
                                name="city",
                                data_source=city.ref,
                                required=True,
                            ),
                            zip_code := TextInput(
                                label="Zip code",
                                input_type=InputType.TEXT,
                                name="zip_code",
                                required=True,
                            ),
                            country_region := TextInput(
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
                                        "name": name.ref,
                                        "address": address.ref,
                                        "city": city.ref,
                                        "zip_code": zip_code.ref,
                                        "country_region": country_region.ref,
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
            data=[
                options := ScreenData(
                    key="options",
                    example=[
                        DataSource(
                            id="1",
                            title="Fire and theft",
                            description="Cover your home against incidents of theft or accidental fires",
                        ),
                        DataSource(
                            id="2",
                            title="Natural disaster",
                            description="Protect your home against disasters including earthquakes, floods and storms",
                        ),
                        DataSource(
                            id="3",
                            title="Liability",
                            description="Protect yourself from legal liabilities that occur from accidents on your property",
                        ),
                    ],
                ),
            ],
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    Form(
                        name="cover_form",
                        children=[
                            options_form := CheckboxGroup(
                                name="options",
                                data_source=options.ref,
                                label="Options",
                                required=True,
                            ),
                            Footer(
                                label="Continue",
                                on_click_action=Action(
                                    name=FlowActionType.DATA_EXCHANGE,
                                    payload={"options": options_form.ref},
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
            data=[
                excess := ScreenData(
                    key="excess", example=[DataSource(id="1", title="$250")]
                ),
                total := ScreenData(key="total", example="$47.98 per month"),
            ],
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    Form(
                        name="quote_form",
                        children=[
                            Dropdown(
                                label="Excess",
                                name="excess",
                                data_source=excess.ref,
                                on_select_action=Action(
                                    name=FlowActionType.DATA_EXCHANGE,
                                    payload={"excess": ComponentRef("excess")},
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
                                        "payment_options": ComponentRef(
                                            "payment_options"
                                        )
                                    },
                                ),
                                required=True,
                                init_value="1",
                            ),
                            TextHeading(text=total.ref),
                            privacy_policy := OptIn(
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
                                        "privacy_policy": privacy_policy.ref,
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

switch = FlowJSON(
    version="5.0",
    screens=[
        Screen(
            id="SCREEN",
            title="Welcome",
            terminal=True,
            success=True,
            data=[ScreenData(key="value", example="cat")],
            layout=Layout(
                children=[
                    animal := TextInput(
                        name="animal",
                        label="Animal",
                        helper_text="Type: cat, dog or anything else",
                    ),
                    Switch(
                        value=animal.ref,
                        cases={
                            "cat": [TextHeading(text="It is a cat")],
                            "dog": [TextHeading(text="It is a dog")],
                            "default": [
                                TextHeading(text="It is neither a cat nor a dog")
                            ],
                        },
                    ),
                    Footer(
                        label="Complete",
                        on_click_action=Action(name="complete", payload={}),
                    ),
                ]
            ),
        )
    ],
)

if_ = FlowJSON(
    version="5.0",
    screens=[
        Screen(
            id="SCREEN",
            title="Welcome",
            terminal=True,
            success=True,
            data=[value := ScreenData(key="value", example=True)],
            layout=Layout(
                children=[
                    animal := TextInput(
                        name="animal",
                        label="Animal",
                        helper_text="Type: cat",
                    ),
                    If(
                        condition=value.ref & (animal.ref == "cat"),
                        then=[TextHeading(text="It is a cat")],
                        else_=[TextHeading(text="It is not a cat")],
                    ),
                    Footer(
                        label="Complete",
                        on_click_action=Action(name="complete", payload={}),
                    ),
                ]
            ),
        )
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
    "switch": switch,
    "if": if_,
}


def test_flows_to_json():
    with open(
        f"tests/data/flows/{FLOWS_VERSION}/examples.json", "r", encoding="utf-8"
    ) as f:
        examples = json.load(f)
    for flow_name, flow in FLOWS.items():
        obj_dict = json.loads(flow.to_json())
        example_dict = examples[flow_name]
        try:
            assert obj_dict == example_dict
        except AssertionError:
            raise AssertionError(
                f"Flow {flow_name} does not match example\nFlow: {obj_dict}\nJSON: {example_dict}"
            )


def test_min_version():
    with pytest.raises(ValueError):
        FlowJSON(version="1.0", screens=[])


def test_empty_form():
    with pytest.raises(ValueError):
        Form(name="form", children=[])


def test_action():
    with pytest.raises(ValueError):
        Action(name=FlowActionType.NAVIGATE)

    with pytest.raises(ValueError):
        Action(name=FlowActionType.COMPLETE)


def test_component_ref():
    assert ComponentRef("test").to_str() == "${form.test}"
    assert ComponentRef("test", screen="START").to_str() == "${screen.START.form.test}"
    assert TextInput(name="test", label="Test").ref.to_str() == "${form.test}"
    assert (
        TextInput(name="test", label="Test").ref_in(screen="START").to_str()
        == "${screen.START.form.test}"
    )


def test_screen_data_key():
    assert ScreenDataRef("test").to_str() == "${data.test}"
    assert ScreenDataRef("test", screen="START").to_str() == "${screen.START.data.test}"
    assert ScreenData(key="test", example="Example").ref.to_str() == "${data.test}"
    assert (
        ScreenData(key="test", example="Example").ref_in(screen="START").to_str()
        == "${screen.START.data.test}"
    )


def test_ref_to_str_without_screen():
    ref = Ref(prefix="data", field="age")
    assert ref.to_str() == "${data.age}"


def test_ref_to_str_with_screen_id():
    ref = Ref(prefix="data", field="age", screen="START")
    assert ref.to_str() == "${screen.START.data.age}"


def test_ref_to_str_with_screen():
    screen = Screen(id="START", layout=Layout(children=[]))
    ref = Ref(prefix="data", field="age", screen=screen)
    assert ref.to_str() == "${screen.START.data.age}"


def test_ref_equality():
    ref = Ref(prefix="data", field="age")
    condition = ref == 21
    assert condition.to_str() == "(${data.age} == 21)"


def test_ref_inequality():
    ref = Ref(prefix="data", field="age")
    condition = ref != 18
    assert condition.to_str() == "(${data.age} != 18)"


def test_ref_greater_than():
    ref = Ref(prefix="data", field="age")
    condition = ref > 21
    assert condition.to_str() == "(${data.age} > 21)"


def test_ref_greater_than_or_equal():
    ref = Ref(prefix="data", field="age")
    condition = ref >= 21
    assert condition.to_str() == "(${data.age} >= 21)"


def test_ref_less_than():
    ref = Ref(prefix="data", field="age")
    condition = ref < 21
    assert condition.to_str() == "(${data.age} < 21)"


def test_ref_less_than_or_equal():
    ref = Ref(prefix="data", field="age")
    condition = ref <= 21
    assert condition.to_str() == "(${data.age} <= 21)"


def test_logical_and_with_ref():
    ref1 = Ref(prefix="data", field="age")
    ref2 = Ref(prefix="form", field="is_verified")
    condition = ref1 & ref2
    assert condition.to_str() == "(${data.age} && ${form.is_verified})"


def test_logical_or_with_ref():
    ref1 = Ref(prefix="data", field="age")
    ref2 = Ref(prefix="form", field="is_verified")
    condition = ref1 | ref2
    assert condition.to_str() == "(${data.age} || ${form.is_verified})"


def test_logical_and_with_condition():
    ref1 = Ref(prefix="data", field="age")
    ref2 = Ref(prefix="form", field="is_verified")
    condition1 = ref1 > 21
    condition2 = ref2 == True  # noqa: E712
    combined_condition = condition1 & condition2
    assert (
        combined_condition.to_str()
        == "((${data.age} > 21) && (${form.is_verified} == true))"
    )


def test_logical_or_with_condition():
    ref1 = Ref(prefix="data", field="age")
    ref2 = Ref(prefix="form", field="is_verified")
    condition1 = ref1 < 18
    condition2 = ref2 == False  # noqa:  E712
    combined_condition = condition1 | condition2
    assert (
        combined_condition.to_str()
        == "((${data.age} < 18) || (${form.is_verified} == false))"
    )


def test_invert_condition():
    ref = Ref(prefix="data", field="age")
    condition = ~ref
    assert condition.to_str() == "!${data.age}"


def test_combined_conditions_with_invert():
    ref1 = Ref(prefix="data", field="age")
    ref2 = Ref(prefix="form", field="is_verified")
    condition = ~(ref1 > 18) & (ref2 == True)  # noqa: E712
    assert (
        condition.to_str() == "(!(${data.age} > 18) && (${form.is_verified} == true))"
    )


def test_combined_conditions_with_literal_before():
    ref1 = Ref(prefix="data", field="age")
    ref2 = Ref(prefix="form", field="is_verified")
    condition = ref2 & (ref1 > 18)
    assert condition.to_str() == "(${form.is_verified} && (${data.age} > 18))"


def test_combined_conditions_with_literal_after():
    ref1 = Ref(prefix="form", field="is_verified")
    ref2 = Ref(prefix="data", field="age")
    condition = (ref2 > 18) & ref1
    assert condition.to_str() == "((${data.age} > 18) && ${form.is_verified})"


def test_init_values():
    text_entry = TextInput(name="test", label="Test", init_value="Example")
    form = Form(name="form", children=[text_entry])
    assert form.init_values == {"test": "Example"}

    # check for duplicate init_values (in the form level and in the children level)
    with pytest.raises(ValueError):
        TextInput(
            name="test", label="Test", init_value="Example", input_type=InputType.NUMBER
        )
        Form(name="form", init_values={"test": "Example"}, children=[text_entry])

    # test that if form has init_values referred to a ref,
    # the init_values does not fill up from the .children init_value's
    form_with_init_values_as_data_key = Screen(
        id="test",
        title="Test",
        data=[
            init_vals := ScreenData(key="init_vals", example={"test": "Example"}),
        ],
        layout=Layout(
            children=[
                Form(name="form", init_values=init_vals.ref, children=[text_entry])
            ]
        ),
    )
    assert isinstance(
        form_with_init_values_as_data_key.layout.children[0].init_values, Ref
    )


#
#
def test_error_messages():
    text_entry = TextInput(name="test", label="Test", error_message="Example")
    form = Form(name="form", children=[text_entry])
    assert form.error_messages == {"test": "Example"}

    # check for duplicate error_messages (in the form level and in the children level)
    with pytest.raises(ValueError):
        TextInput(name="test", label="Test", error_message="Example")
        Form(name="form", error_messages={"test": "Example"}, children=[text_entry])

    # test that if form has error_messages referred to a ref,
    # the error_messages does not fill up from the .children error_message's
    form_with_error_messages_as_data_key = Screen(
        id="test",
        title="Test",
        data=[
            error_msgs := ScreenData(key="error_msgs", example={"test": "Example"}),
        ],
        layout=Layout(
            children=[
                Form(
                    name="form",
                    error_messages=error_msgs.ref,
                    children=[text_entry],
                )
            ]
        ),
    )

    assert isinstance(
        form_with_error_messages_as_data_key.layout.children[0].error_messages, Ref
    )


def test_screen_data():
    encoder = FlowJSONEncoder()
    assert encoder._get_json_type("Example") == {"type": "string"}
    assert encoder._get_json_type(example=1) == {"type": "number"}
    assert encoder._get_json_type(1.0) == {"type": "number"}
    assert encoder._get_json_type(True) == {"type": "boolean"}
    # ---

    assert encoder._get_json_type(DataSource(id="1", title="Example")) == {
        "type": "object",
        "properties": {"id": {"type": "string"}, "title": {"type": "string"}},
    }

    # ---

    assert encoder._get_json_type(
        [
            DataSource(id="1", title="Example"),
            DataSource(id="2", title="Example2"),
        ]
    ) == {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "title": {"type": "string"},
            },
        },
    }

    # ---

    with pytest.raises(ValueError):
        FlowJSON(
            screens=[
                Screen(
                    id="test",
                    title="Test",
                    data=[ScreenData(key="test", example=[])],
                    layout=Layout(children=[]),
                )
            ],
            version="2.1",
        ).to_json()

    with pytest.raises(ValueError):
        FlowJSON(
            screens=[
                Screen(
                    id="test",
                    title="Test",
                    data=[ScreenData(key="test", example=ValueError)],
                    layout=Layout(children=[]),
                )
            ],
            version="2.1",
        ).to_json()


def test_flow_response_with_error_msg():
    assert (
        "error_message"
        in FlowResponse(
            version=Version.FLOW_MSG.value,
            data={"test": "test"},
            screen="TEST",
            error_message="Example",
        ).to_dict()["data"]
    )


def test_flow_response_with_close_flow():
    assert (
        FlowResponse(  # closing flow make screen `SUCCESS`
            version=Version.FLOW_MSG.value,
            data={"test": "test"},
            close_flow=True,
            flow_token="test",
        ).to_dict()["screen"]
        == "SUCCESS"
    )

    with pytest.raises(ValueError):  # not closing flow without screen
        FlowResponse(
            version=Version.FLOW_MSG.value,
            data={"test": "test"},
            flow_token="test",
            close_flow=False,
        )

    with pytest.raises(ValueError):  # closing flow without flow_token
        FlowResponse(
            version=Version.FLOW_MSG.value,
            data={"test": "test"},
            close_flow=True,
        )

    with pytest.raises(ValueError):  # closing flow with error_message
        FlowResponse(
            version=Version.FLOW_MSG.value,
            data={"test": "test"},
            close_flow=True,
            flow_token="fdf",
            error_message="Example",
        )


def test_flow_response_with_data_sources():
    assert FlowResponse(
        version=Version.FLOW_MSG.value,
        data={"data_source": DataSource(id="1", title="Example")},
        screen="TEST",
    ).to_dict()["data"]["data_source"] == {"id": "1", "title": "Example"}

    assert FlowResponse(
        version=Version.FLOW_MSG.value,
        data={"data_source": [DataSource(id="1", title="Example")]},
        screen="TEST",
    ).to_dict()["data"]["data_source"] == [{"id": "1", "title": "Example"}]


def test_flow_callback_wrapper():
    wa = WhatsApp(
        token="xxx", server=None, business_private_key="xxx", verify_token="fdfd"
    )

    def main_handler(_, __): ...

    req = FlowRequest(
        version=...,
        action=FlowRequestActionType.DATA_EXCHANGE,
        flow_token="xyz",
        screen="START",
        data={},
        raw=...,
        raw_encrypted=...,
    )
    wrapper = wa.get_flow_request_handler(
        endpoint="/flow",
        callback=main_handler,
        request_decryptor=...,
        response_encryptor=...,
    )
    assert wrapper._get_callback(req) is main_handler

    def data_exchange_start_screen_callback(_, __): ...

    wrapper.add_handler(
        callback=data_exchange_start_screen_callback,
        action=FlowRequestActionType.DATA_EXCHANGE,
        screen="START",
    )
    req = dataclasses.replace(req, screen="START")
    assert wrapper._get_callback(req) is data_exchange_start_screen_callback

    def data_exchange_callback_without_screen(_, __): ...

    wrapper.add_handler(
        callback=data_exchange_callback_without_screen,
        action=FlowRequestActionType.DATA_EXCHANGE,
        screen=None,
    )
    assert wrapper._get_callback(req) is data_exchange_callback_without_screen

    def init_with_data_filter(_, __): ...

    wrapper._on_callbacks.clear()
    wrapper.add_handler(
        callback=init_with_data_filter,
        action=FlowRequestActionType.INIT,
        screen=None,
        filters=filters.new(lambda _, r: r.data.get("age") >= 20),
    )
    req = dataclasses.replace(req, action=FlowRequestActionType.INIT, data={"age": 20})
    assert wrapper._get_callback(req) is init_with_data_filter


def test_flows_server():
    with pytest.raises(ValueError, match="^When using a custom server.*"):
        wa = WhatsApp(token=..., server=None, verify_token=...)
        wa.add_flow_request_handler(
            handlers.FlowRequestHandler(
                callback=...,
                endpoint=...,
            )
        )

    with pytest.raises(ValueError, match="^You must initialize the WhatsApp client.*"):
        wa = WhatsApp(token=..., server=utils.MISSING)
        wa.add_flow_request_handler(
            handlers.FlowRequestHandler(
                callback=...,
                endpoint=...,
            )
        )
