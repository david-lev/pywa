from pywa.types.template import *  # noqa: F403

seasonal_promotion = Template(
    name="seasonal_promotion",
    language=TemplateLanguage.ENGLISH_US,
    category=TemplateCategory.MARKETING,
    components=[
        HeaderText(
            "Our {{1}} is on!",
            "Summer Sale",
        ),
        BodyText(
            "Shop now through {{1}} and use code {{2}} to get {{3}} off of all merchandise.",
            "the end of August",
            "25OFF",
            "25%",
        ),
        Footer(text="Use the buttons below to manage your MARKETING subscriptions"),
        Buttons(
            buttons=[
                QuickReplyButton(text="Unsubscribe from Promos"),
                QuickReplyButton(text="Unsubscribe from All"),
            ]
        ),
    ],
)

order_confirmation = Template(
    name="order_confirmation",
    language=TemplateLanguage.ENGLISH_US,
    category=TemplateCategory.UTILITY,
    components=[
        HeaderDocument(
            example=HeaderMediaExample(handle="4::YX..."),
        ),
        BodyText(
            "Thank you for your order, {{1}}! Your order number is {{2}}. Tap the PDF linked above to view your receipt. If you have any questions, please use the buttons below to contact support. Thank you for being a customer!",
            "Pablo",
            "860198-230332",
        ),
        Buttons(
            buttons=[
                PhoneNumberButton(text="Call", phone_number="15550051310"),
                URLButton(
                    text="Contact Support", url="https://www.luckyshrub.com/support"
                ),
            ]
        ),
    ],
)

order_delivery_update = Template(
    name="order_delivery_update",
    language=TemplateLanguage.ENGLISH_US,
    category=TemplateCategory.UTILITY,
    components=[
        HeaderLocation(),
        BodyText(
            "Good news {{1}}! Your order #{{2}} is on its way to the location above. Thank you for your order!",
            "Mark",
            "566701",
        ),
        Footer(text="To stop receiving delivery updates, tap the button below."),
        Buttons(
            buttons=[
                QuickReplyButton(text="Stop Delivery Updates"),
            ]
        ),
    ],
)

abandoned_cart_offer = Template(
    name="abandoned_cart_offer",
    language=TemplateLanguage.ENGLISH_US,
    category=TemplateCategory.MARKETING,
    components=[
        HeaderProduct(),
        BodyText(
            "Use code {{1}} to get {{2}} off our newest succulent!", "25OFF", "25%"
        ),
        Footer(text="Offer ends September 30, 2024"),
        Buttons(
            buttons=[
                SPMButton(text="View"),
            ]
        ),
    ],
)

intro_catalog_offer = Template(
    name="intro_catalog_offer",
    language=TemplateLanguage.ENGLISH_US,
    category=TemplateCategory.MARKETING,
    components=[
        BodyText(
            "Now shop for your favourite products right here on WhatsApp! Get Rs {{1}} off on all orders above {{2}}Rs! Valid for your first {{3}} orders placed on WhatsApp!",
            "100",
            "400",
            "3",
        ),
        Footer(text="Best grocery deals on WhatsApp!"),
        Buttons(
            buttons=[
                CatalogButton(text="View catalog"),
            ]
        ),
    ],
)

coupon_code_fall2023_25off = Template(
    name="coupon_code_fall2023_25off",
    language=TemplateLanguage.ENGLISH_US,
    category=TemplateCategory.MARKETING,
    components=[
        HeaderText(text="Our Fall Sale is on!"),
        BodyText(
            "Shop now through November and use code {{1}} to get {{2}} off of all merchandise!",
            "25OFF",
            "25%",
        ),
        Buttons(
            buttons=[
                QuickReplyButton(text="Unsubscribe"),
                CopyCodeButton(example="250FF"),
            ]
        ),
    ],
)

abandoned_cart = Template(
    name="abandoned_cart",
    language=TemplateLanguage.ENGLISH_US,
    category=TemplateCategory.MARKETING,
    components=[
        HeaderText(
            "Forget something, {{1}}?",
            "Pablo",
        ),
        BodyText(
            "Looks like you left these items in your cart, still interested? Use code {{1}} to get 10% off!",
            "10OFF",
        ),
        Buttons(buttons=[MPMButton(text="View items")]),
    ],
)
