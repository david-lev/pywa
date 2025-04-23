from pywa.types.flows import *  # noqa
import datetime


calendar_picker_single_mode = FlowJSON(
    version="6.1",
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
                    CalendarPicker(
                        name="calendar",
                        label="Single date",
                        helper_text="Select a date",
                        required=True,
                        mode=CalendarPickerMode.SINGLE,
                        min_date=datetime.date(2024, 10, 21),
                        max_date=datetime.date(2025, 12, 12),
                        unavailable_dates=[
                            datetime.date(2024, 11, 28),
                            datetime.date(2024, 11, 1),
                        ],
                        include_days=[
                            CalendarDay.MON,
                            CalendarDay.TUE,
                            CalendarDay.WED,
                            CalendarDay.THU,
                            CalendarDay.FRI,
                        ],
                        init_value=datetime.date(2024, 10, 23),
                        on_select_action=DataExchangeAction(
                            payload={"calendar": ComponentRef("calendar")},
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


calendar_picker_range_mode = FlowJSON(
    version="6.1",
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
                    CalendarPicker(
                        name="calendar_range",
                        title="Range calendar",
                        description="Use this to select a date range",
                        label=CalendarRangeValues(
                            start_date="Start date",
                            end_date="End date",
                        ),
                        helper_text=CalendarRangeValues(
                            start_date="Select from date",
                            end_date="Select to date",
                        ),
                        required=CalendarRangeValues(
                            start_date=True,
                            end_date=False,
                        ),
                        mode=CalendarPickerMode.RANGE,
                        min_date=datetime.date(2024, 10, 21),
                        max_date=datetime.date(2025, 12, 12),
                        unavailable_dates=[
                            datetime.date(2024, 11, 28),
                            datetime.date(2024, 11, 1),
                        ],
                        include_days=[
                            CalendarDay.MON,
                            CalendarDay.TUE,
                            CalendarDay.WED,
                            CalendarDay.THU,
                            CalendarDay.FRI,
                        ],
                        min_days=3,
                        max_days=10,
                        init_value=CalendarRangeValues(
                            start_date=datetime.date(2024, 10, 22),
                            end_date=datetime.date(2024, 10, 25),
                        ),
                        on_select_action=DataExchangeAction(
                            payload={"calendar_range": ComponentRef("calendar_range")},
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
