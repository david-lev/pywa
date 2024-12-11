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
                        on_click_action=CompleteAction(payload={}),
                    ),
                ],
            ),
        )
    ],
)
