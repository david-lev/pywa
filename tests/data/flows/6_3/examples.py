from pywa.types.flows import *

chips_selector = FlowJSON(
    version="6.3",
    screens=[
        Screen(
            id="DEMO_SCREEN",
            terminal=True,
            title="Demo screen",
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    ChipsSelector(
                        name="chips",
                        label="Personalize your experience",
                        description="Choose your interests to get personalized design ideas and solution",
                        max_selected_items=2,
                        data_source=[
                            DataSource(id="room_layout", title="🏡 Room layouts"),
                            DataSource(id="lighting", title="💡 Lighting"),
                            DataSource(id="renovation", title="🛠️ Renovation"),
                            DataSource(id="furnitures", title="📐 Room layouts"),
                        ],
                    ),
                    Footer(
                        label="Continue",
                        on_click_action=CompleteAction(),
                    ),
                ],
            ),
        ),
    ],
)
