from pywa.types.flows import *  # noqa


string_concatenation = FlowJSON(
    version="6.0",
    screens=[
        Screen(
            id="DEMO_SCREEN",
            terminal=True,
            title="Demo screen",
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    first_name := TextInput(
                        label="First name",
                        input_type=InputType.TEXT,
                        name="first_name",
                        required=True,
                    ),
                    age := TextInput(
                        label="Age",
                        input_type=InputType.NUMBER,
                        name="age",
                        required=True,
                    ),
                    TextBody(text=f"`'Hello ' {first_name.ref}`"),
                    TextBody(
                        text=f"`{first_name.ref} ' you are ' {age.ref} ' years old.'`"
                    ),
                    Footer(
                        label="Footer",
                        on_click_action=Action(
                            name=FlowActionType.COMPLETE,
                            payload={},
                        ),
                    ),
                ],
            ),
        )
    ],
)

open_url = FlowJSON(
    version="6.0",
    screens=[
        Screen(
            id="DEMO_SCREEN",
            terminal=True,
            title="Demo screen",
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    EmbeddedLink(
                        text="This is an external link.",
                        on_click_action=Action(
                            name=FlowActionType.OPEN_URL,
                            url="https://pywa.readthedocs.io/",
                        ),
                    ),
                    OptIn(
                        label="I agree to the terms.",
                        name="T&Cs",
                        on_click_action=Action(
                            name=FlowActionType.OPEN_URL,
                            url="https://pywa.readthedocs.io/",
                        ),
                    ),
                    Footer(
                        label="Footer",
                        on_click_action=Action(
                            name=FlowActionType.COMPLETE,
                            payload={},
                        ),
                    ),
                ],
            ),
        )
    ],
)
