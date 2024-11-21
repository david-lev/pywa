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

update_data = FlowJSON(
    version="6.0",
    screens=[
        Screen(
            id="ADDRESS_SELECTION",
            title="Address selection",
            terminal=True,
            success=True,
            data=[
                state_visibility := ScreenData(
                    key="state_visibility",
                    example=False,
                ),
                pincode_visibility := ScreenData(
                    key="pincode_visibility",
                    example=False,
                ),
                states := ScreenData(
                    key="states",
                    example=[DataSource(id="1", title="USA")],
                ),
                pincode := ScreenData(
                    key="pincode",
                    example=[DataSource(id="M6B2A9", title="M6B2A9")],
                ),
                countries := ScreenData(
                    key="countries",
                    example=[
                        DataSource(
                            id="1",
                            title="USA",
                            on_select_action=Action(
                                name=FlowActionType.UPDATE_DATA,
                                payload={
                                    states.key: [
                                        DataSource(
                                            id="new_york",
                                            title="New York",
                                            on_unselect_action=Action(
                                                name=FlowActionType.UPDATE_DATA,
                                                payload={pincode_visibility.key: False},
                                            ),
                                            on_select_action=Action(
                                                name=FlowActionType.UPDATE_DATA,
                                                payload={
                                                    pincode.key: [
                                                        DataSource(
                                                            id="10001", title="10001"
                                                        ),
                                                        DataSource(
                                                            id="10005", title="10005"
                                                        ),
                                                    ],
                                                    pincode_visibility.key: True,
                                                },
                                            ),
                                        ),
                                        DataSource(
                                            id="california",
                                            title="California",
                                            on_unselect_action=Action(
                                                name=FlowActionType.UPDATE_DATA,
                                                payload={pincode_visibility.key: False},
                                            ),
                                            on_select_action=Action(
                                                name=FlowActionType.UPDATE_DATA,
                                                payload={
                                                    pincode.key: [
                                                        DataSource(
                                                            id="90019", title="90019"
                                                        ),
                                                        DataSource(
                                                            id="93504", title="93504"
                                                        ),
                                                    ],
                                                    pincode_visibility.key: True,
                                                },
                                            ),
                                        ),
                                    ],
                                    state_visibility.key: True,
                                },
                            ),
                            on_unselect_action=Action(
                                name=FlowActionType.UPDATE_DATA,
                                payload={
                                    state_visibility.key: False,
                                    pincode_visibility.key: False,
                                },
                            ),
                        ),
                        DataSource(
                            id="2",
                            title="Canada",
                            on_select_action=Action(
                                name=FlowActionType.UPDATE_DATA,
                                payload={
                                    states.key: [
                                        DataSource(
                                            id="ontario",
                                            title="Ontario",
                                            on_unselect_action=Action(
                                                name=FlowActionType.UPDATE_DATA,
                                                payload={pincode_visibility.key: False},
                                            ),
                                            on_select_action=Action(
                                                name=FlowActionType.UPDATE_DATA,
                                                payload={
                                                    pincode.key: [
                                                        DataSource(
                                                            id="L4K", title="L4K"
                                                        ),
                                                        DataSource(
                                                            id="M3C", title="M3C"
                                                        ),
                                                    ],
                                                    pincode_visibility.key: True,
                                                },
                                            ),
                                        ),
                                        DataSource(
                                            id="quebec",
                                            title="Quebec",
                                            on_unselect_action=Action(
                                                name=FlowActionType.UPDATE_DATA,
                                                payload={pincode_visibility.key: False},
                                            ),
                                            on_select_action=Action(
                                                name=FlowActionType.UPDATE_DATA,
                                                payload={
                                                    pincode.key: [
                                                        DataSource(
                                                            id="M6B2A9", title="M6B2A9"
                                                        ),
                                                        DataSource(
                                                            id="M5V", title="M5V"
                                                        ),
                                                    ],
                                                    pincode_visibility.key: True,
                                                },
                                            ),
                                        ),
                                    ],
                                    state_visibility.key: True,
                                },
                            ),
                            on_unselect_action=Action(
                                name=FlowActionType.UPDATE_DATA,
                                payload={
                                    state_visibility.key: False,
                                    pincode_visibility.key: False,
                                },
                            ),
                        ),
                    ],
                ),
            ],
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    RadioButtonsGroup(
                        name="select_country",
                        label="Select country:",
                        data_source=countries.ref,
                    ),
                    RadioButtonsGroup(
                        name="select_states",
                        label="Select state:",
                        visible=state_visibility.ref,
                        data_source=states.ref,
                    ),
                    RadioButtonsGroup(
                        name="pincode",
                        label="Select pincode:",
                        visible=pincode_visibility.ref,
                        data_source=pincode.ref,
                    ),
                    Footer(
                        label="Complete",
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


math_operators = FlowJSON(
    version="6.0",
    screens=[
        Screen(
            id="DEMO_SCREEN",
            title="Demo Screen",
            terminal=True,
            success=True,
            data=[
                number_1 := ScreenData(
                    key="number_1",
                    example=10,
                ),
                number_2 := ScreenData(
                    key="number_2",
                    example=20,
                ),
            ],
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    TextBody(
                        text=[
                            f"`'The sum of ' {number_1.ref} ' and ' {number_2.ref} ' is ' {number_1.ref + number_2.ref}`",
                            f"`'The difference of ' {number_1.ref} ' and ' {number_2.ref} ' is ' {number_1.ref - number_2.ref}`",
                            f"`'The product of ' {number_1.ref} ' and ' {number_2.ref} ' is ' {number_1.ref * number_2.ref}`",
                            f"`'The division of ' {number_1.ref} ' by ' {number_2.ref} ' is ' {number_1.ref / number_2.ref}`",
                        ],
                    ),
                    Footer(
                        label="Static footer label",
                        on_click_action=Action(
                            name=FlowActionType.COMPLETE,
                            payload={},
                        ),
                    ),
                ],
            ),
        ),
    ],
)

visible_condition = FlowJSON(
    version="6.0",
    screens=[
        Screen(
            id="DEMO_SCREEN",
            title="Demo Screen",
            terminal=True,
            success=True,
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    number := TextInput(
                        label="Enter a number",
                        input_type=InputType.NUMBER,
                        name="number",
                    ),
                    TextBody(
                        text="You choose the right number!",
                        visible=number.ref == 42,
                    ),
                    Footer(
                        label="Static footer label",
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
