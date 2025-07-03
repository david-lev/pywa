from pywa.types.template_v2 import *  # noqa: F403
from pywa.types.template_v2 import TemplateText

seasonal_promotion = TemplateV2(
    name="seasonal_promotion",
    language=TemplateLanguage.ENGLISH_US,
    category=TemplateCategory.MARKETING,
    components=[
        HeaderText(
            text=TemplateText("Our {{1}} is on!", "Summer Sale"),
        ),
        Body(
            text=TemplateText(
                "Shop now through {{1}} and use code {{2}} to get {{3}} off of all merchandise.",
                "the end of August",
                "25OFF",
                "25%",
            ),
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

order_confirmation = TemplateV2(
    name="order_confirmation",
    language=TemplateLanguage.ENGLISH_US,
    category=TemplateCategory.UTILITY,
    components=[
        HeaderDocument(
            example=HeaderMediaExample(handle="4::YX..."),
        ),
        Body(
            text=TemplateText(
                "Thank you for your order, {{1}}! Your order number is {{2}}. Tap the PDF linked above to view your receipt. If you have any questions, please use the buttons below to contact support. Thank you for being a customer!",
                "Pablo",
                "860198-230332",
            )
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

order_delivery_update = TemplateV2(
    name="order_delivery_update",
    language=TemplateLanguage.ENGLISH_US,
    category=TemplateCategory.UTILITY,
    components=[
        HeaderLocation(),
        Body(
            text=TemplateText(
                "Good news {{1}}! Your order #{{2}} is on its way to the location above. Thank you for your order!",
                "Mark",
                "566701",
            )
        ),
        Footer(text="To stop receiving delivery updates, tap the button below."),
        Buttons(
            buttons=[
                QuickReplyButton(text="Stop Delivery Updates"),
            ]
        ),
    ],
)

abandoned_cart_offer = TemplateV2(
    name="abandoned_cart_offer",
    language=TemplateLanguage.ENGLISH_US,
    category=TemplateCategory.MARKETING,
    components=[
        HeaderProduct(),
        Body(
            text=TemplateText(
                "Use code {{1}} to get {{2}} off our newest succulent!", "25OFF", "25%"
            )
        ),
        Footer(text="Offer ends September 30, 2024"),
        Buttons(
            buttons=[
                SPMButton(text="View"),
            ]
        ),
    ],
)

intro_catalog_offer = TemplateV2(
    name="intro_catalog_offer",
    language=TemplateLanguage.ENGLISH_US,
    category=TemplateCategory.MARKETING,
    components=[
        Body(
            text=TemplateText(
                "Now shop for your favourite products right here on WhatsApp! Get Rs {{1}} off on all orders above {{2}}Rs! Valid for your first {{3}} orders placed on WhatsApp!",
                "100",
                "400",
                "3",
            )
        ),
        Footer(text="Best grocery deals on WhatsApp!"),
        Buttons(
            buttons=[
                CatalogButton(text="View catalog"),
            ]
        ),
    ],
)

coupon_code_fall2023_25off = TemplateV2(
    name="coupon_code_fall2023_25off",
    language=TemplateLanguage.ENGLISH_US,
    category=TemplateCategory.MARKETING,
    components=[
        HeaderText(text=TemplateText("Our Fall Sale is on!")),
        Body(
            text=TemplateText(
                "Shop now through November and use code {{1}} to get {{2}} off of all merchandise!",
                "25OFF",
                "25%",
            )
        ),
        Buttons(
            buttons=[
                QuickReplyButton(text="Unsubscribe"),
                CopyCodeButton(example="250FF"),
            ]
        ),
    ],
)

abandoned_cart = TemplateV2(
    name="abandoned_cart",
    language=TemplateLanguage.ENGLISH_US,
    category=TemplateCategory.MARKETING,
    components=[
        HeaderText(
            text=TemplateText("Forget something, {{1}}?", "Pablo"),
        ),
        Body(
            text=TemplateText(
                "Looks like you left these items in your cart, still interested? Use code {{1}} to get 10% off!",
                "10OFF",
            )
        ),
        Buttons(buttons=[MPMButton(text="View items")]),
    ],
)
