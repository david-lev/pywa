from pywa.types.template_v2 import *  # noqa: F403
from pywa.types.template_v2 import TemplateText

carousel_template_media_cards_v1 = TemplateV2(
    name="carousel_template_media_cards_v1",
    language=TemplateLanguage.ENGLISH_US,
    category=TemplateCategory.MARKETING,
    components=[
        Body(
            text=TemplateText(
                "Rare succulents for sale! {{1}}, add these unique plants to your collection. Each of these rare succulents are {{2}} if you checkout using code {{3}}. Shop now and add some unique and beautiful plants to your collection!",
                "Pablo",
                "30%",
                "30OFF",
            )
        ),
        Carousel(
            cards=[
                CarouselMediaCard(
                    components=[
                        HeaderImage(example=HeaderMediaExample(handle="4::an...")),
                        Body(
                            text="Add a touch of elegance to your collection with the beautiful Aloe 'Blue Elf' succulent. Its deep blue-green leaves have a hint of pink around the edges."
                        ),
                        Buttons(
                            buttons=[
                                QuickReplyButton(text="Send me more like this!"),
                                URLButton(
                                    text="Shop",
                                    url="https://www.luckyshrub.com/rare-succulents/{{1}}",
                                    example="BLUE_ELF",
                                ),
                            ]
                        ),
                    ]
                ),
                CarouselMediaCard(
                    components=[
                        HeaderImage(example=HeaderMediaExample(handle="4::an...")),
                        Body(
                            text="The Crassula Buddha's Temple is sure to be a conversation starter with its tiny temple shaped leaves, intricate details, and lacy texture."
                        ),
                        Buttons(
                            buttons=[
                                QuickReplyButton(text="Send me more like this!"),
                                URLButton(
                                    text="Shop",
                                    url="https://www.luckyshrub.com/rare-succulents/{{1}}",
                                    example="BUDDHA",
                                ),
                            ]
                        ),
                    ]
                ),
                CarouselMediaCard(
                    components=[
                        HeaderImage(example=HeaderMediaExample(handle="4::an...")),
                        Body(
                            text="The Echeveria 'Black Prince' is a stunning succulent, with near-black leaves, adorned with a hint of green around the edges, giving it its striking appearance."
                        ),
                        Buttons(
                            buttons=[
                                QuickReplyButton(text="Send me more like this!"),
                                URLButton(
                                    text="Shop",
                                    url="https://www.luckyshrub.com/rare-succulents/{{1}}",
                                    example="BLACK_PRINCE",
                                ),
                            ]
                        ),
                    ]
                ),
            ]
        ),
    ],
)


carousel_template_product_cards_v1 = TemplateV2(
    name="carousel_template_product_cards_v1",
    language=TemplateLanguage.ENGLISH_US,
    category=TemplateCategory.MARKETING,
    components=[
        Body(
            text=TemplateText(
                "Rare succulents for sale! {{1}}, add these unique plants to your collection. All three of these rare succulents are available for purchase on our website, and they come with a 100% satisfaction guarantee. Whether you're a seasoned succulent enthusiast or just starting your plant collection, these rare succulents are sure to impress. Shop now and add some unique and beautiful plants to your collection!",
                "Pablo",
            )
        ),
        Carousel(
            cards=[
                CarouselMediaCard(
                    components=[
                        HeaderProduct(),
                        Buttons(buttons=[SPMButton(text="View")]),
                    ]
                ),
                CarouselMediaCard(
                    components=[
                        HeaderProduct(),
                        Buttons(buttons=[SPMButton(text="View")]),
                    ]
                ),
            ]
        ),
    ],
)
