"""
The WhatsApp Flow definition for the loan application: three screens (personal info → loan
details → review), each exchanging data with the server (`main.py`) so we can validate input and
compute an estimated monthly payment before the applicant submits.
"""

from pywa_async.types.flows import *

personal_info_screen = Screen(
    id="PERSONAL_INFO",
    title="Personal Information",
    layout=Layout(
        children=[
            full_name := TextInput(
                name="full_name",
                label="Full name",
                input_type=InputType.TEXT,
                required=True,
            ),
            email := TextInput(
                name="email",
                label="Email address",
                input_type=InputType.EMAIL,
                required=True,
            ),
            employment_status := RadioButtonsGroup(
                name="employment_status",
                label="Employment status",
                required=True,
                data_source=[
                    DataSource(id="employed", title="Employed"),
                    DataSource(id="self_employed", title="Self-employed"),
                    DataSource(id="unemployed", title="Unemployed"),
                ],
            ),
            Footer(
                label="Continue",
                on_click_action=DataExchangeAction(
                    payload={
                        "full_name": full_name.ref,
                        "email": email.ref,
                        "employment_status": employment_status.ref,
                    },
                ),
            ),
        ]
    ),
)

loan_details_screen = Screen(
    id="LOAN_DETAILS",
    title="Loan Details",
    layout=Layout(
        children=[
            loan_amount := TextInput(
                name="loan_amount",
                label="Loan amount ($)",
                input_type=InputType.NUMBER,
                required=True,
            ),
            loan_purpose := Dropdown(
                name="loan_purpose",
                label="Purpose",
                required=True,
                data_source=[
                    DataSource(id="home", title="Home"),
                    DataSource(id="car", title="Car"),
                    DataSource(id="education", title="Education"),
                    DataSource(id="business", title="Business"),
                    DataSource(id="other", title="Other"),
                ],
            ),
            Footer(
                label="Continue",
                on_click_action=DataExchangeAction(
                    payload={
                        "loan_amount": loan_amount.ref,
                        "loan_purpose": loan_purpose.ref,
                    },
                ),
            ),
        ]
    ),
)

review_screen = Screen(
    id="REVIEW",
    title="Review",
    terminal=True,
    success=True,
    data=[
        summary := ScreenData(
            key="summary",
            example="Applicant: Jane Doe\nLoan amount: $10,000.00\nPurpose: home\n"
            "Estimated monthly payment (24 mo): $416.67",
        ),
    ],
    layout=Layout(
        children=[
            TextHeading(text="Review your application"),
            TextBody(text=summary.ref),
            Footer(
                label="Submit Application",
                on_click_action=CompleteAction(payload={"summary": summary.ref}),
            ),
        ]
    ),
)

loan_application_flow = FlowJSON(
    version="7.2",
    data_api_version="3.0",
    routing_model={
        "PERSONAL_INFO": ["LOAN_DETAILS"],
        "LOAN_DETAILS": ["REVIEW"],
        "REVIEW": [],
    },
    screens=[personal_info_screen, loan_details_screen, review_screen],
)
