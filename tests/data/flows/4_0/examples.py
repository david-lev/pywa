from pywa.types.flows import *  # noqa: F403

switch = FlowJSON(
    version="4.0",
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
    version="4.0",
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

photo_picker = FlowJSON(
    version="4.0",
    routing_model={"FIRST": []},
    data_api_version="3.0",
    screens=[
        Screen(
            id="FIRST",
            title="Photo Picker Example",
            terminal=True,
            data={},
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    Form(
                        name="flow_path",
                        children=[
                            photo_picker := PhotoPicker(
                                name="photo_picker",
                                label="Upload photos",
                                description="Please attach images about the received items",
                                photo_source="camera_gallery",
                                min_uploaded_photos=1,
                                max_uploaded_photos=10,
                                max_file_size_kb=10240,
                            ),
                            Footer(
                                label="Submit",
                                on_click_action=Action(
                                    name=FlowActionType.DATA_EXCHANGE,
                                    payload={"images": photo_picker.ref},
                                ),
                            ),
                        ],
                    )
                ],
            ),
        )
    ],
)

doc_picker = FlowJSON(
    version="4.0",
    routing_model={"SECOND": []},
    data_api_version="3.0",
    screens=[
        Screen(
            id="SECOND",
            terminal=True,
            title="Document Picker Example",
            data={},
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    Form(
                        name="flow_path",
                        children=[
                            document_picker := DocumentPicker(
                                name="document_picker",
                                label="Contract",
                                description="Attach the signed copy of the contract",
                                min_uploaded_documents=1,
                                max_uploaded_documents=1,
                                max_file_size_kb=1024,
                                allowed_mime_types=[
                                    "image/jpeg",
                                    "application/pdf",
                                ],
                            ),
                            Footer(
                                label="Submit",
                                on_click_action=Action(
                                    name="complete",
                                    payload={"documents": document_picker.ref},
                                ),
                            ),
                        ],
                    )
                ],
            ),
        )
    ],
)


date_picker_dates_str = FlowJSON(
    version="4.0",
    data_api_version="3.0",
    routing_model={},
    screens=[
        Screen(
            id="DEMO_SCREEN",
            terminal=True,
            title="Demo screen",
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    Form(
                        name="form_name",
                        children=[
                            DatePicker(
                                name="date",
                                label="Date",
                                min_date="1693569600000",
                                max_date="1767182400000",
                                unavailable_dates=[
                                    "1694779200000",
                                    "1697371200000",
                                ],
                                on_select_action=Action(
                                    name=FlowActionType.DATA_EXCHANGE,
                                    payload={"date": ComponentRef("date")},
                                ),
                            ),
                            Footer(
                                label="Continue",
                                on_click_action=Action(
                                    name=FlowActionType.DATA_EXCHANGE,
                                    payload={},
                                ),
                            ),
                        ],
                    )
                ],
            ),
        )
    ],
)

global_fields = FlowJSON(
    version="4.0",
    screens=[
        screen_one := Screen(
            data=[
                field2 := ScreenData(key="field2", example="data"),
            ],
            id="SCREEN_ONE",
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    field1 := TextInput(name="field1", label="Enter your name"),
                    Footer(
                        label="CTA",
                        on_click_action=Action(
                            name=FlowActionType.NAVIGATE,
                            next=ActionNext(
                                type=ActionNextType.SCREEN, name="SCREEN_TWO"
                            ),
                            payload={},
                        ),
                    ),
                ],
            ),
            title="Screen 1",
        ),
        Screen(
            id="SCREEN_TWO",
            terminal=True,
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    Footer(
                        label="Complete",
                        on_click_action=Action(
                            name=FlowActionType.COMPLETE,
                            payload={
                                "field1": screen_one / field1.ref,
                                "field2": screen_one / field2.ref,
                            },
                        ),
                    ),
                ],
            ),
            title="Screen 2",
            data={},
        ),
    ],
)


forward_refs = FlowJSON(
    version="4.0",
    routing_model={"SELECT_SERVICES": ["SELECT_INSURANCE"]},
    screens=[
        select_insurance_screen := Screen(
            id="SELECT_INSURANCE",
            title="Select insurance",
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    insurance := RadioButtonsGroup(
                        name="insurance",
                        label="Please select your coverage",
                        data_source=[
                            basic := DataSource(id="basic", title="Basic"),
                            standard := DataSource(id="standard", title="Standard"),
                            full := DataSource(id="full", title="Premium"),
                        ],
                    )
                ],
            ),
        ),
        Screen(
            terminal=True,
            id="SELECT_SERVICES",
            title="Select services",
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    TextSubheading(text="Select insurance type"),
                    If(
                        condition=select_insurance_screen / insurance.ref != "",
                        then=[
                            Switch(
                                value=select_insurance_screen / insurance.ref,
                                cases={
                                    basic.id: [
                                        TextBody(
                                            text="You've selected a basic insurance"
                                        )
                                    ],
                                    standard.id: [
                                        TextBody(
                                            text="You've selected a standard insurance"
                                        )
                                    ],
                                    full.id: [
                                        TextBody(
                                            text="You've selected a comprehensive insurance"
                                        )
                                    ],
                                },
                            )
                        ],
                        else_=[
                            TextBody(text="You haven't selected any insurance type")
                        ],
                    ),
                    EmbeddedLink(
                        text="Choose insurance type",
                        on_click_action=Action(
                            name=FlowActionType.NAVIGATE,
                            next=ActionNext(
                                type=ActionNextType.SCREEN, name="SELECT_INSURANCE"
                            ),
                            payload={},
                        ),
                    ),
                    Footer(
                        label="Complete",
                        on_click_action=Action(
                            name=FlowActionType.COMPLETE,
                            payload={
                                "selected_insurance_type": select_insurance_screen
                                / insurance.ref
                            },
                        ),
                    ),
                ],
            ),
        ),
    ],
)
