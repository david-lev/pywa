from pywa.types.flows import *  # noqa: F403

rich_text = FlowJSON(
    version="5.1",
    screens=[
        Screen(
            id="FIRST_SCREEN",
            title="Welcome",
            terminal=True,
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    TextCaption(
                        markdown=True,
                        text=[
                            "This is a markdown example inside **TextCaption**. You can combine **different** *formatting* ~~***styles***~~",
                            "You can also add [links](https://whatsapp.com) to external web-sites",
                        ],
                    ),
                    TextBody(
                        markdown=True,
                        text=[
                            "This is a markdown example inside **TextCaption**. You can combine **different** *formatting* ~~***styles***~~.",
                            "You can also add [links](https://whatsapp.com) to external web-sites",
                            "And use **Ordered** and **Unordered** lists:",
                            "1. List item",
                            "2. List item",
                        ],
                    ),
                    OptIn(
                        name="toc",
                        required=True,
                        label="RichText can be used to render large static or dynamic texts.",
                        on_click_action=Action(
                            name=FlowActionType.NAVIGATE,
                            next=ActionNext(type=ActionNextType.SCREEN, name="TOC"),
                            payload={},
                        ),
                    ),
                    Footer(
                        label="Proceed",
                        on_click_action=Action(
                            name=FlowActionType.COMPLETE, payload={}
                        ),
                    ),
                ],
            ),
        ),
        Screen(
            id="TOC",
            title="Terms of Service",
            layout=Layout(
                type=LayoutType.SINGLE_COLUMN,
                children=[
                    RichText(
                        text=[
                            "This is a mock-up of ToC demonstrating the supported syntax of RichText components",
                            "# Terms of Service",
                            "## 1. Acceptance of Terms",
                            'By using our services, you *agree* to a these lol **Terms of Service** (*"Terms"*). If you do not *agree*, please do not use our services.',
                            "**Here is image example:**",
                            '"![Whatsapp-logo](data:image/png;base64,meQAyMDIzLTA0LTA4VDE3OjMyOjA1KzAwOjAw8ZGfFgAAAABJRU5ErkJggg==)"',
                            "We are not **liable** for:",
                            "1. *indirect* including the ones that happens all the time in normal life, I just need to make this text slightly longer",
                            "2. *incidental*,",
                            "3. *special*,",
                            "4. *punitive* damages",
                            "including loss of:",
                            "+ *profits*,",
                            "+ *data*",
                            "+ *use*.",
                            "## 2. Modifications to Terms",
                            'We *reserve* the right to **modify** these *Terms* at any time. Changes will be indicated by the **"Last Updated"** date. Continued use after changes constitutes acceptance.',
                            "## 3. Use of Services",
                            "**Eligibility:** You must be at least *18 years old*. By using our services, you *confirm* you meet this requirement.",
                            "**Account Responsibilities:** You are **responsible** for your account confidentiality and activities.",
                            "## 4. User Conduct",
                            "You *agree* not to **violate** laws, **infringe** rights, or transmit *objectionable* content.",
                            "## 5. Termination",
                            "We may **terminate** or *suspend* your access immediately, without notice, for any reason, including **breach** of *Terms*.",
                            "## 6. Disclaimer of Warranties",
                            'Services are provided ***"AS IS"*** and ***"AS AVAILABLE"***. We disclaim all **warranties**, express or implied, including *merchantability* and *fitness for a particular purpose*.',
                            "## 7. Limitation of Liability",
                            "We are not **liable** for:",
                            "1. *indirect* including the ones that happens all the time in normal life, I just need to make this text slightly longer",
                            "2. *incidental*,",
                            "3. *special*,",
                            "4. *punitive* damages",
                            "including loss of:",
                            "+ *profits*,",
                            "+ *data*",
                            "+ *use*.",
                            "## 8. Governing Law",
                            "| Column  with extended width   | Column  with extended width   | Column  with extended width   |",
                            "| --------   | --------   |",
                            "| It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum. | Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.|  Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum |",
                            "| It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum. | Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.|  Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum |",
                            "## 9. Contact Information",
                            "For questions, contact us at **[your email address]**.",
                            "Alternatively please go to our [Fancy web-site](https://www.whatsapp.com) to learn more about our services.",
                            "**Last Updated:** ***[Date]***",
                        ]
                    )
                ],
            ),
        ),
    ],
)
