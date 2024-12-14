import datetime

from pywa.types.flows import *  # noqa: F403


radio_buttons_with_pics = FlowJSON(
    version="5.0",
    screens=[
        Screen(
            id="TRAVEL_PACKAGES",
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    RadioButtonsGroup(
                        name="packages",
                        required=True,
                        data_source=[
                            DataSource(
                                id="1",
                                title="Tropical Beach Vacation",
                                description="Enjoy 7 nights and 8 days at a luxury beach resort in Bali. Including flights and stays",
                                alt_text="beach vacation",
                                image="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
                            ),
                            DataSource(
                                id="2",
                                title="Mountain Adventure",
                                description="Embark on a 5-day guided trek in the Swiss Alps. Package includes flights and stays",
                                image="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
                            ),
                            DataSource(
                                id="3",
                                title="City Break",
                                description="Explore the sights and sounds of New York City with our 4 nights and 5 days package",
                                image="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
                            ),
                            DataSource(
                                id="4",
                                title="Historical Tour",
                                description="Take a 7-day historical tour of Rome, Italy. Package includes flights and stays",
                                image="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
                            ),
                        ],
                        label="Explore our exciting packages",
                    ),
                    Footer(
                        label="Continue",
                        on_click_action=CompleteAction(),
                    ),
                ],
            ),
            title="Travel Packages",
            terminal=True,
        ),
    ],
)

date_picker_dates_obj = FlowJSON(
    version="5.0",
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
                    date := DatePicker(
                        name="date",
                        label="Date",
                        min_date=datetime.date(2024, 10, 21),
                        max_date=datetime.date(2024, 11, 12),
                        unavailable_dates=[
                            datetime.date(2024, 10, 28),
                            datetime.date(2024, 11, 1),
                        ],
                        on_select_action=DataExchangeAction(
                            payload={"date": ComponentRef("date")},
                        ),
                    ),
                    Footer(
                        label="Continue",
                        on_click_action=DataExchangeAction(),
                    ),
                ],
            ),
        )
    ],
)
