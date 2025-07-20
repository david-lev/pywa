from pywa.types.template import *  # noqa: F403

limited_time_offer_caribbean_pkg_2023 = Template(
    name="limited_time_offer_caribbean_pkg_2023",
    language=TemplateLanguage.ENGLISH_US,
    category=TemplateCategory.MARKETING,
    components=[
        HeaderImage(example=HeaderMediaExample(handle="4::aW...")),
        LimitedTimeOffer(
            limited_time_offer=LimitedTimeOfferConfig(
                text="Expiring offer!", has_expiration=True
            )
        ),
        BodyText(
            "Good news, {{1}}! Use code {{2}} to get 25% off all Caribbean Destination packages!",
            "Pablo",
            "CARIBE25",
        ),
        Buttons(
            buttons=[
                CopyCodeButton(example="CARIBE25"),
                URLButton(
                    text="Book now!",
                    url="https://awesomedestinations.com/offers?code={{1}}",
                    example="https://awesomedestinations.com/offers?ref=n3mtql",
                ),
            ]
        ),
    ],
)
