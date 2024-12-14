import re

from pywa.types.flows import *  # noqa

regex = FlowJSON(
    version="6.2",
    screens=[
        Screen(
            id="DEMO_SCREEN",
            title="Demo Screen",
            terminal=True,
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    TextInput(
                        required=True,
                        label="Regex Input",
                        input_type=InputType.TEXT,
                        pattern=re.compile(
                            "^(19|20)\\d\\d-(0[1-9]|1[012])-(0[1-9]|[12][0-9]|3[01])$"
                        ),
                        helper_text="E.g. 1993-08-04",
                        name="regex input",
                    ),
                    TextInput(
                        required=True,
                        label="Regex Passcode",
                        pattern="007",
                        input_type=InputType.PASSCODE,
                        name="passcode_oo7",
                        helper_text="Contains: 007",
                    ),
                    Footer(
                        label="Continue",
                        on_click_action=CompleteAction(),
                    ),
                ],
            ),
        )
    ],
)

navigation_list = FlowJSON(
    version="6.2",
    routing_model={
        "FIRST_SCREEN": ["SECOND_SCREEN", "THIRD_SCREEN", "FIFTH_SCREEN"],
        "SECOND_SCREEN": ["CONTACT"],
        "THIRD_SCREEN": ["CONTACT"],
        "FIFTH_SCREEN": ["CONTACT"],
        "CONTACT": [],
    },
    screens=[
        Screen(
            id="FIRST_SCREEN",
            title="Our offers",
            data={},
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    NavigationList(
                        name="insurances",
                        list_items=[
                            NavigationItem(
                                id="home",
                                main_content=NavigationItemMainContent(
                                    title="Home Insurance",
                                    metadata="Safeguard your home against natural disasters, theft, and accidents",
                                ),
                                end=NavigationItemEnd(
                                    title="$100", description="/ month"
                                ),
                                on_click_action=NavigateAction(
                                    next=Next(name="SECOND_SCREEN"),
                                ),
                            ),
                            NavigationItem(
                                id="health",
                                main_content=NavigationItemMainContent(
                                    title="Health Insurance",
                                    metadata="Get essential coverage for doctor visits, prescriptions, and hospital stays",
                                ),
                                end=NavigationItemEnd(
                                    title="$80", description="/ month"
                                ),
                                on_click_action=NavigateAction(
                                    next=Next(name="SECOND_SCREEN"),
                                ),
                            ),
                            NavigationItem(
                                id="intergalactic",
                                main_content=NavigationItemMainContent(
                                    title="Intergalactic Insurance",
                                    metadata="Enjoy coverage for asteroid collisions, alien encounters, and other risks",
                                ),
                                end=NavigationItemEnd(
                                    title="$1.000", description="/ month"
                                ),
                                on_click_action=NavigateAction(
                                    next=Next(name="FOURTH_SCREEN"),
                                ),
                            ),
                            NavigationItem(
                                id="timetravel",
                                main_content=NavigationItemMainContent(
                                    title="Time Travel Insurance",
                                    metadata="Ready for paradox-related damages or unforeseen consequences of altering history",
                                ),
                                end=NavigationItemEnd(
                                    title="$980", description="/ month"
                                ),
                                on_click_action=NavigateAction(
                                    next=Next(name="FIFTH_SCREEN"),
                                ),
                            ),
                            NavigationItem(
                                id="dream",
                                main_content=NavigationItemMainContent(
                                    title="Dream Loss Insurance",
                                    metadata="Protection from recurring nightmares or lost opportunities due to poor sleep",
                                ),
                                end=NavigationItemEnd(
                                    title="$540", description="/ month"
                                ),
                                on_click_action=NavigateAction(
                                    next=Next(name="FIFTH_SCREEN"),
                                    payload={"first_name": True},
                                ),
                            ),
                        ],
                    )
                ],
            ),
        ),
        Screen(
            id="SECOND_SCREEN",
            title="Home Insurance",
            data={},
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    TextSubheading(text="Tell us about your property"),
                    Form(
                        name="property_details_form",
                        children=[
                            Dropdown(
                                name="property_type",
                                required=True,
                                label="Property Type",
                                data_source=[
                                    DataSource(id="House", title="House"),
                                    DataSource(id="Apartment", title="Apartment"),
                                    DataSource(id="Condo", title="Condo"),
                                ],
                            ),
                            TextInput(
                                name="surface",
                                label="Total surface (sqm)",
                                input_type=InputType.NUMBER,
                                required=True,
                            ),
                            TextInput(
                                name="rooms",
                                input_type=InputType.NUMBER,
                                label="Number or rooms",
                                required=True,
                            ),
                            TextInput(name="floors", label="Number of floors"),
                            Footer(
                                label="Continue",
                                on_click_action=NavigateAction(
                                    next=Next(name="CONTACT"),
                                ),
                            ),
                        ],
                    ),
                ],
            ),
        ),
        Screen(
            id="THIRD_SCREEN",
            title="Health Insurance",
            data={},
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    TextSubheading(
                        text="Tell us about the type of insurance you are looking for"
                    ),
                    Form(
                        name="health_insurance_form",
                        children=[
                            Dropdown(
                                label="Insurance type",
                                name="insurance_type",
                                required=True,
                                data_source=[
                                    DataSource(id="individual", title="Individual"),
                                    DataSource(id="family", title="Family"),
                                ],
                            ),
                            TextInput(
                                label="Count",
                                required=True,
                                helper_text="How may people will be covered by this insurance",
                                name="number_of_people",
                            ),
                            Dropdown(
                                label="Age range",
                                name="age_range",
                                required=True,
                                data_source=[
                                    DataSource(id="18-24", title="18-24"),
                                    DataSource(id="25-34", title="25-34"),
                                ],
                            ),
                            Footer(
                                label="Next",
                                on_click_action=NavigateAction(
                                    next=Next(name="CONTACT"),
                                ),
                            ),
                        ],
                    ),
                ],
            ),
        ),
        Screen(
            id="FIFTH_SCREEN",
            title="Time Travel Insurance",
            data=[first_name := ScreenData(key="first_name", example="Bob")],
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    TextBody(
                        text=f"`{first_name.ref} ', we are excited you are joining our community of time travellers!'`"
                    ),
                    TextBody(
                        text="We require a few more details to make sure you have the best cover possible for your needs."
                    ),
                    Form(
                        name="health_insurance_form",
                        children=[
                            Dropdown(
                                label="Insurance type",
                                name="insurance_type",
                                required=True,
                                data_source=[
                                    DataSource(id="individual", title="Individual"),
                                    DataSource(id="family", title="Family"),
                                ],
                            ),
                            TextInput(
                                label="Count",
                                required=True,
                                helper_text="How may people will be covered by this insurance",
                                name="number_of_people",
                            ),
                            Dropdown(
                                label="Age range",
                                name="age_range",
                                required=True,
                                data_source=[
                                    DataSource(id="18-24", title="18-24"),
                                    DataSource(id="25-34", title="25-34"),
                                ],
                            ),
                            Footer(
                                label="Next",
                                on_click_action=NavigateAction(
                                    next=Next(name="CONTACT"),
                                ),
                            ),
                        ],
                    ),
                ],
            ),
        ),
        Screen(
            id="CONTACT",
            title="Contact details",
            terminal=True,
            data={},
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    TextHeading(text="How can we get in contact with you?"),
                    Form(
                        name="form",
                        children=[
                            name := TextInput(
                                name="name",
                                label="Full name",
                                required=True,
                            ),
                            phone := TextInput(
                                name="phone",
                                required=True,
                                label="Phone number",
                            ),
                            Footer(
                                label="Complete",
                                on_click_action=CompleteAction(
                                    payload={
                                        "phone": phone.ref,
                                        "name": name.ref,
                                    },
                                ),
                            ),
                        ],
                    ),
                ],
            ),
        ),
    ],
)


navigation_list_dynamic = FlowJSON(
    version="6.2",
    data_api_version="3.0",
    routing_model={
        "FIRST_SCREEN": ["SECOND_SCREEN", "THIRD_SCREEN"],
        "SECOND_SCREEN": ["CONTACT"],
        "THIRD_SCREEN": ["CONTACT"],
        "CONTACT": [],
    },
    screens=[
        Screen(
            id="FIRST_SCREEN",
            title="Our offers",
            data=[
                insurances := ScreenData(
                    key="insurances",
                    example=[
                        NavigationItem(
                            id="home",
                            main_content=NavigationItemMainContent(
                                title="Home Insurance",
                                metadata="Safeguard your home against natural disasters, theft, and accidents.",
                            ),
                            on_click_action=DataExchangeAction(
                                payload={"selection": "home"},
                            ),
                        ),
                        NavigationItem(
                            id="health",
                            main_content=NavigationItemMainContent(
                                title="Health Insurance",
                                metadata="Get essential coverage for doctor visits, prescriptions, and hospital stays.",
                            ),
                            on_click_action=DataExchangeAction(
                                payload={"selection": "health"},
                            ),
                        ),
                    ],
                ),
            ],
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    NavigationList(
                        name="insurances",
                        list_items=insurances.ref,
                    )
                ],
            ),
        ),
        Screen(
            id="SECOND_SCREEN",
            title="Home Insurance",
            data={},
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    TextSubheading(text="Tell us about your property"),
                    Form(
                        name="property_details_form",
                        children=[
                            Dropdown(
                                name="property_type",
                                required=True,
                                label="Property Type",
                                data_source=[
                                    DataSource(id="House", title="House"),
                                    DataSource(id="Apartment", title="Apartment"),
                                    DataSource(id="Condo", title="Condo"),
                                ],
                            ),
                            TextInput(
                                name="surface",
                                label="Total surface (sqm)",
                                input_type=InputType.NUMBER,
                                required=True,
                            ),
                            TextInput(
                                name="rooms",
                                input_type=InputType.NUMBER,
                                label="Number or rooms",
                                required=True,
                            ),
                            TextInput(
                                name="floors",
                                label="Number of floors",
                            ),
                            Footer(
                                label="Continue",
                                on_click_action=NavigateAction(
                                    next=Next(name="CONTACT"),
                                ),
                            ),
                        ],
                    ),
                ],
            ),
        ),
        Screen(
            id="THIRD_SCREEN",
            title="Health Insurance",
            data={},
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    TextSubheading(
                        text="Tell us about the type of insurance you are looking for"
                    ),
                    Form(
                        name="health_insurance_form",
                        children=[
                            Dropdown(
                                label="Insurance type",
                                name="insurance_type",
                                required=True,
                                data_source=[
                                    DataSource(id="individual", title="Individual"),
                                    DataSource(id="family", title="Family"),
                                ],
                            ),
                            TextInput(
                                label="Count",
                                required=True,
                                helper_text="How may people will be covered by this insurance",
                                name="number_of_people",
                            ),
                            Dropdown(
                                label="Age range",
                                name="age_range",
                                required=True,
                                data_source=[
                                    DataSource(id="18-24", title="18-24"),
                                    DataSource(id="25-34", title="25-34"),
                                ],
                            ),
                            Footer(
                                label="Next",
                                on_click_action=NavigateAction(
                                    next=Next(name="CONTACT"),
                                ),
                            ),
                        ],
                    ),
                ],
            ),
        ),
        Screen(
            id="CONTACT",
            title="Contact details",
            terminal=True,
            data={},
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    TextHeading(text="How can we get in contact with you?"),
                    Form(
                        name="form",
                        children=[
                            name := TextInput(
                                name="name",
                                label="Full name",
                                required=True,
                            ),
                            phone := TextInput(
                                name="phone",
                                required=True,
                                label="Phone number",
                            ),
                            Footer(
                                label="Complete",
                                on_click_action=CompleteAction(
                                    payload={
                                        "phone": phone.ref,
                                        "name": name.ref,
                                    }
                                ),
                            ),
                        ],
                    ),
                ],
            ),
        ),
    ],
)
