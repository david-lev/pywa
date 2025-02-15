import datetime
import json
from pywa.types.template import NewTemplate, MediaCardComponent, Carousel, Template


def test_carousel_template_creation_json():
    template_body = NewTemplate.Body(
        text="Rare succulents for sale! {Pablo}, add these unique plants to your collection. Each of these rare succulents are {30%} if you checkout using code {30OFF}. Shop now and add some unique and beautiful plants to your collection!"
    )
    # Create media cards
    cards = [
        MediaCardComponent(
            header=NewTemplate.Image(example="4::an..."),
            body="Add a touch of elegance to your collection with the beautiful Aloe 'Blue Elf' succulent. Its deep blue-green leaves have a hint of pink around the edges.",
            buttons=[
                NewTemplate.QuickReplyButton(text="Send me more like this!"),
                NewTemplate.UrlButton(
                    title="Shop",
                    url="https://www.luckyshrub.com/rare-succulents/{BLUE_ELF}",
                ),
            ],
        ),
        MediaCardComponent(
            header=NewTemplate.Image(example="4::an..."),
            body="The Crassula Buddha's Temple is sure to be a conversation starter with its tiny temple shaped leaves, intricate details, and lacy texture.",
            buttons=[
                NewTemplate.QuickReplyButton(text="Send me more like this!"),
                NewTemplate.UrlButton(
                    title="Shop",
                    url="https://www.luckyshrub.com/rare-succulents{BUDDHA}",
                ),
            ],
        ),
        MediaCardComponent(
            header=NewTemplate.Image(example="4::an..."),
            body="The Echeveria 'Black Prince' is a stunning succulent, with near-black leaves, adorned with a hint of green around the edges, giving it its striking appearance.",
            buttons=[
                NewTemplate.QuickReplyButton(text="Send me more like this!"),
                NewTemplate.UrlButton(
                    title="Shop",
                    url="https://www.luckyshrub.com/rare-succulents{BLACK_PRINCE}",
                ),
            ],
        ),
    ]

    carousel = Carousel(cards=cards)

    template = NewTemplate(
        name="carousel_template_media_cards_v1",
        category=NewTemplate.Category.MARKETING,
        language=NewTemplate.Language.ENGLISH_US,
        body=template_body,
        carousel=carousel,
    )

    # Json payload from documentation:
    # https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/media-card-carousel-templates/

    actual = {
        "name": "carousel_template_media_cards_v1",
        "language": "en_US",
        "category": "marketing",
        "components": [
            {
                "type": "body",
                "text": "Rare succulents for sale! {{1}}, add these unique plants to your collection. Each of these rare succulents are {{2}} if you checkout using code {{3}}. Shop now and add some unique and beautiful plants to your collection!",
                "example": {"body_text": [["Pablo", "30%", "30OFF"]]},
            },
            {
                "type": "carousel",
                "cards": [
                    {
                        "components": [
                            {
                                "type": "header",
                                "format": "image",
                                "example": {"header_handle": ["4::an..."]},
                            },
                            {
                                "type": "body",
                                "text": "Add a touch of elegance to your collection with the beautiful Aloe 'Blue Elf' succulent. Its deep blue-green leaves have a hint of pink around the edges.",
                            },
                            {
                                "type": "buttons",
                                "buttons": [
                                    {
                                        "type": "quick_reply",
                                        "text": "Send me more like this!",
                                    },
                                    {
                                        "type": "url",
                                        "text": "Shop",
                                        "url": "https://www.luckyshrub.com/rare-succulents/{{1}}",
                                        "example": ["BLUE_ELF"],
                                    },
                                ],
                            },
                        ]
                    },
                    {
                        "components": [
                            {
                                "type": "header",
                                "format": "image",
                                "example": {"header_handle": ["4::an..."]},
                            },
                            {
                                "type": "body",
                                "text": "The Crassula Buddha's Temple is sure to be a conversation starter with its tiny temple shaped leaves, intricate details, and lacy texture.",
                            },
                            {
                                "type": "buttons",
                                "buttons": [
                                    {
                                        "type": "quick_reply",
                                        "text": "Send me more like this!",
                                    },
                                    {
                                        "type": "url",
                                        "text": "Shop",
                                        "url": "https://www.luckyshrub.com/rare-succulents{{1}}",
                                        "example": ["BUDDHA"],
                                    },
                                ],
                            },
                        ]
                    },
                    {
                        "components": [
                            {
                                "type": "header",
                                "format": "image",
                                "example": {"header_handle": ["4::an..."]},
                            },
                            {
                                "type": "body",
                                "text": "The Echeveria 'Black Prince' is a stunning succulent, with near-black leaves, adorned with a hint of green around the edges, giving it its striking appearance.",
                            },
                            {
                                "type": "buttons",
                                "buttons": [
                                    {
                                        "type": "quick_reply",
                                        "text": "Send me more like this!",
                                    },
                                    {
                                        "type": "url",
                                        "text": "Shop",
                                        "url": "https://www.luckyshrub.com/rare-succulents{{1}}",
                                        "example": ["BLACK_PRINCE"],
                                    },
                                ],
                            },
                        ]
                    },
                ],
            },
        ],
    }

    assert (
        json.dumps(template.to_dict(), sort_keys=True).lower()
        == json.dumps(actual, sort_keys=True).lower()
    )


def test_carousel_template_send_json():
    ...
    body_params = [
        Template.TextValue(value="Pablo"),
        Template.TextValue(value="20%"),
        Template.TextValue(value="20OFF"),
    ]

    cards = [
        Template.MediaCard(
            card_index=0,
            header_asset_id="1558081531584829",
            header_format="image",
            quick_reply_payload="more-aloes",
            url_button_text="blue-elf",
        ),
        Template.MediaCard(
            card_index=1,
            header_asset_id="861236878885705",
            header_format="image",
            quick_reply_payload="more-crassulas",
            url_button_text="buddhas-temple",
        ),
        Template.MediaCard(
            card_index=2,
            header_asset_id="1587064918516321",
            header_format="image",
            quick_reply_payload="more-echeverias",
            url_button_text="black-prince",
        ),
    ]

    template = Template(
        name="carousel_template_media_cards_v1",
        language=Template.Language.ENGLISH_US,
        body=body_params,
        cards=cards,
    )

    # Valid JSON payload from documentation:
    # https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-message-templates/media-card-carousel-templates
    actual = {
        "name": "carousel_template_media_cards_v1",
        "language": {"code": "en_US"},
        "components": [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": "Pablo"},
                    {"type": "text", "text": "20%"},
                    {"type": "text", "text": "20OFF"},
                ],
            },
            {
                "type": "carousel",
                "cards": [
                    {
                        "card_index": "0",
                        "components": [
                            {
                                "type": "header",
                                "parameters": [
                                    {
                                        "type": "image",
                                        "image": {"id": "1558081531584829"},
                                    }
                                ],
                            },
                            {
                                "type": "button",
                                "sub_type": "quick_reply",
                                "index": "0",
                                "parameters": [
                                    {"type": "payload", "payload": "more-aloes"}
                                ],
                            },
                            {
                                "type": "button",
                                "sub_type": "url",
                                "index": "1",
                                "parameters": [{"type": "text", "text": "blue-elf"}],
                            },
                        ],
                    },
                    {
                        "card_index": "1",
                        "components": [
                            {
                                "type": "header",
                                "parameters": [
                                    {
                                        "type": "image",
                                        "image": {"id": "861236878885705"},
                                    }
                                ],
                            },
                            {
                                "type": "button",
                                "sub_type": "quick_reply",
                                "index": "0",
                                "parameters": [
                                    {"type": "payload", "payload": "more-crassulas"}
                                ],
                            },
                            {
                                "type": "button",
                                "sub_type": "url",
                                "index": "1",
                                "parameters": [
                                    {"type": "text", "text": "buddhas-temple"}
                                ],
                            },
                        ],
                    },
                    {
                        "card_index": "2",
                        "components": [
                            {
                                "type": "header",
                                "parameters": [
                                    {
                                        "type": "image",
                                        "image": {"id": "1587064918516321"},
                                    }
                                ],
                            },
                            {
                                "type": "button",
                                "sub_type": "quick_reply",
                                "index": "0",
                                "parameters": [
                                    {"type": "payload", "payload": "more-echeverias"}
                                ],
                            },
                            {
                                "type": "button",
                                "sub_type": "url",
                                "index": "1",
                                "parameters": [
                                    {"type": "text", "text": "black-prince"}
                                ],
                            },
                        ],
                    },
                ],
            },
        ],
    }

    with open("./pred.json", "w") as f:
        json.dump(template.to_dict(), f, sort_keys=True)

    with open("./actual.json", "w") as f:
        json.dump(actual, f, sort_keys=True)

    assert (
        json.dumps(template.to_dict(), sort_keys=True).lower()
        == json.dumps(actual, sort_keys=True).lower()
    )
