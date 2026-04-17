import datetime
import importlib
import json
import pathlib

import pytest

from pywa import _helpers as helpers
from pywa import types
from pywa.types import flows
from pywa.types.templates import *  # noqa: F403


def _resolve_example_handles(template: Template):
    not_uploaded = helpers.filter_not_uploaded_comps(template.components)
    for comp in not_uploaded:
        comp._handle = comp._example
    return template


def test_templates_to_json(caplog):
    for templates_dir in pathlib.Path("tests/data/templates").iterdir():
        with open(
            pathlib.Path(templates_dir, "examples.json"), "r", encoding="utf-8"
        ) as f:
            json_examples = json.load(f)
            obj_examples = importlib.import_module(
                f"tests.data.templates.{templates_dir.name}.examples"
            )
            for template_name, template_json in json_examples.items():
                example_obj: Template = getattr(obj_examples, template_name)
                # example_dict: dict = json_examples[template_name]

                assert (
                    json.loads(
                        _resolve_example_handles(
                            Template.from_dict(
                                json.loads(
                                    _resolve_example_handles(example_obj).to_json()
                                )
                            )
                        ).to_json()
                    )
                    == template_json
                ), (
                    f"Template {templates_dir.name=} {template_name=} does not match example JSON."
                )
                assert not caplog.records, (
                    f"Template {templates_dir.name=} {template_name=} has warnings: {' '.join(record.message for record in caplog.records)}"
                )


def test_template_text_params_both_pos_and_named_examples():
    with pytest.raises(ValueError):
        HeaderText.params("pos", named="named")


def test_template_text_examples_positionals():
    with pytest.raises(
        ValueError,
        match="Text contains placeholders {'1'} but no examples were provided.",
    ):
        HeaderText("example {{1}}")

    with pytest.raises(
        ValueError,
        match="Mismatched positional placeholders. Expected {'1|2', '1|2'} based on 2 provided examples, but found {'1'} in text.",
    ):
        HeaderText("example {{1}} {{2}}", "one")

    with pytest.raises(
        ValueError,
        match="Found named placeholders {'named_param'} in text, but positional examples were provided.",
    ):
        HeaderText("example {{named_param}}", "example")

    h = HeaderText(
        "Hi {{1}}, this is a text template number {{2}}",
        "David",
        1,
    )
    assert h.to_dict() == {
        "type": "HEADER",
        "format": "TEXT",
        "text": "Hi {{1}}, this is a text template number {{2}}",
        "example": {
            "header_text": ["David", "1"],
        },
    }
    assert h.text == "Hi {{1}}, this is a text template number {{2}}"
    assert h.example == ("David", 1)
    assert h.preview() == "Hi David, this is a text template number 1"
    assert h.preview("David2") == "Hi David2, this is a text template number 1"
    assert h.params("John", 100).to_dict() == {
        "type": "HEADER",
        "parameters": [
            {"type": "text", "text": "John"},
            {"type": "text", "text": "100"},
        ],
    }
    assert h.param_format == ParamFormat.POSITIONAL
    with pytest.raises(
        ValueError,
        match="HeaderText does not accept named parameters when using positional format.",
    ):
        h.params(named="John")
    with pytest.raises(
        ValueError,
        match="HeaderText requires 2 positional parameters, got 3.",
    ):
        h.params("John", 100, "unexpected")

    with pytest.raises(
        ValueError,
        match="HeaderText does not accept parameters as it was initialized without examples.",
    ):
        HeaderText("Hi").params("John")


def test_template_text_examples_named():
    with pytest.raises(
        ValueError,
        match="Text contains placeholders {'name'} but no examples were provided.",
    ):
        BodyText("Hi {{name}}")

    with pytest.raises(
        ValueError, match="Named parameters mismatch: missing examples for {'number'}"
    ):
        BodyText("Hi {{name}}, this is a text template number {{number}}", name="David")

    with pytest.raises(
        ValueError,
        match="Found positional placeholders {'1|2', '1|2'} in text, but named examples were provided.",
    ):
        BodyText(
            "Hi {{1}}, this is a text template number {{2}}", name="David", number=1
        )

    b = BodyText(
        "Hi {{name}}, this is a text template number {{number}}",
        name="David",
        number=1,
    )
    assert b.to_dict() == {
        "type": "BODY",
        "text": "Hi {{name}}, this is a text template number {{number}}",
        "example": {
            "body_text_named_params": [
                {"param_name": "name", "example": "David"},
                {"param_name": "number", "example": "1"},
            ]
        },
    }
    assert b.text == "Hi {{name}}, this is a text template number {{number}}"
    assert b.example == {"name": "David", "number": 1}
    assert b.preview() == "Hi David, this is a text template number 1"
    assert b.preview(number=2) == "Hi David, this is a text template number 2"
    assert b.params(name="John", number=100).to_dict() == {
        "type": "BODY",
        "parameters": [
            {"type": "text", "text": "John", "parameter_name": "name"},
            {"type": "text", "text": "100", "parameter_name": "number"},
        ],
    }
    assert b.param_format == ParamFormat.NAMED
    with pytest.raises(
        ValueError,
        match="BodyText does not accept positional parameters when using named format.",
    ):
        b.params("John")
    with pytest.raises(
        ValueError,
        match="BodyText received unexpected parameters: unexpected",
    ):
        b.params(name="John", number=100, unexpected="unexpected")

    with pytest.raises(ValueError, match="BodyText is missing parameters: number"):
        b.params(name="John")

    with pytest.raises(
        ValueError,
        match="BodyText does not accept parameters as it was initialized without examples.",
    ):
        BodyText("Hi").params(name="John")


def test_media_header_handle_reset():
    media_header = HeaderImage(example="https://example.com/image.jpg")
    media_header._handle = "1:handle"
    media_header.example = "https://example2.com/image.jpg"
    assert media_header._handle is None, (
        "Handle should be reset to None after example change"
    )


def test_comp_and_params_to_dict():
    ht = HeaderText("Hello {{1}}", "World")
    assert ht.to_dict() == {
        "type": "HEADER",
        "format": "TEXT",
        "text": "Hello {{1}}",
        "example": {"header_text": ["World"]},
    }
    assert ht.params("John").to_dict() == {
        "type": "HEADER",
        "parameters": [{"type": "text", "text": "John"}],
    }
    hi = HeaderImage(example="1:imagehandle")
    hi._handle = "1:imagehandle"
    assert hi.to_dict() == {
        "type": "HEADER",
        "format": "IMAGE",
        "example": {"header_handle": ["1:imagehandle"]},
    }
    hip = hi.params(image="123456")
    hip._resolved_media = "123456"
    assert hip.to_dict() == {
        "type": "HEADER",
        "parameters": [{"type": "image", "image": {"id": "123456"}}],
    }

    hv = HeaderVideo(example="1:videohandle")
    hv._handle = "1:videohandle"
    assert hv.to_dict() == {
        "type": "HEADER",
        "format": "VIDEO",
        "example": {"header_handle": ["1:videohandle"]},
    }
    hvp = hv.params(video="123456")
    hvp._resolved_media = "123456"
    assert hvp.to_dict() == {
        "type": "HEADER",
        "parameters": [{"type": "video", "video": {"id": "123456"}}],
    }

    hv = HeaderGIF(example="1:gifhandle")
    hv._handle = "1:gifhandle"
    assert hv.to_dict() == {
        "type": "HEADER",
        "format": "GIF",
        "example": {"header_handle": ["1:gifhandle"]},
    }
    hvp = hv.params(gif="123456")
    hvp._resolved_media = "123456"
    assert hvp.to_dict() == {
        "type": "HEADER",
        "parameters": [{"type": "gif", "gif": {"id": "123456"}}],
    }

    hd = HeaderDocument(example="1:documenthandle")
    hd._handle = "1:documenthandle"
    assert hd.to_dict() == {
        "type": "HEADER",
        "format": "DOCUMENT",
        "example": {"header_handle": ["1:documenthandle"]},
    }
    hdp = hd.params(document="123456")
    hdp._resolved_media = "123456"
    assert hdp.to_dict() == {
        "type": "HEADER",
        "parameters": [{"type": "document", "document": {"id": "123456"}}],
    }

    hl = HeaderLocation()
    assert hl.to_dict() == {
        "type": "HEADER",
        "format": "LOCATION",
    }
    assert hl.params(
        lat=123.456, lon=78.910, name="Test", address="123 Test St"
    ).to_dict() == {
        "type": "HEADER",
        "parameters": [
            {
                "type": "location",
                "location": {
                    "latitude": 123.456,
                    "longitude": 78.910,
                    "name": "Test",
                    "address": "123 Test St",
                },
            }
        ],
    }

    hp = HeaderProduct()
    assert hp.to_dict() == {
        "type": "HEADER",
        "format": "PRODUCT",
    }
    assert hp.params(catalog_id="1234", sku="ITEM123").to_dict() == {
        "type": "HEADER",
        "parameters": [
            {
                "type": "product",
                "product": {"catalog_id": "1234", "product_retailer_id": "ITEM123"},
            }
        ],
    }

    bt = BodyText("Hello {{1}}", "World")
    assert bt.to_dict() == {
        "type": "BODY",
        "text": "Hello {{1}}",
        "example": {"body_text": [["World"]]},
    }
    assert bt.params("John").to_dict() == {
        "type": "BODY",
        "parameters": [{"type": "text", "text": "John"}],
    }

    assert FooterText(text="Powered by PyWa").to_dict() == {
        "type": "FOOTER",
        "text": "Powered by PyWa",
    }

    assert Buttons(buttons=[]).to_dict() == {
        "type": "BUTTONS",
        "buttons": [],
    }

    ccb = CopyCodeButton(example="SUMMER2023_20OFF")
    assert ccb.to_dict() == {
        "type": "COPY_CODE",
        "example": "SUMMER2023_20OFF",
    }
    assert ccb.params(coupon_code="FALL2023_25OFF", index=0).to_dict() == {
        "type": "button",
        "sub_type": "COPY_CODE",
        "index": 0,
        "parameters": [{"type": "coupon_code", "coupon_code": "FALL2023_25OFF"}],
    }

    assert FlowButton(text="Start Flow", flow_id="123456").to_dict() == {
        "type": "FLOW",
        "text": "Start Flow",
        "flow_id": "123456",
    }
    assert json.loads(
        FlowButton(
            text="Start Flow",
            flow_json=flows.FlowJSON(
                version="7.0",
                screens=[
                    flows.Screen(
                        id="START",
                        title="Newsletter Subscription",
                        terminal=True,
                        layout=flows.Layout(
                            children=[
                                flows.TextHeading(text="Subscribe to our Newsletter"),
                                email := flows.TextInput(
                                    name="email",
                                    label="Enter your email",
                                    input_type=flows.InputType.EMAIL,
                                    required=True,
                                ),
                                flows.OptIn(
                                    name="opt_in",
                                    label="By subscribing, you agree to receive our newsletter.",
                                    required=True,
                                ),
                                flows.Footer(
                                    label="Subscribe!",
                                    on_click_action=flows.CompleteAction(
                                        payload={
                                            "email": email.ref,
                                        }
                                    ),
                                ),
                            ]
                        ),
                    )
                ],
            ),
        ).to_dict()["flow_json"]
    ) == {
        "screens": [
            {
                "id": "START",
                "layout": {
                    "children": [
                        {"text": "Subscribe to our Newsletter", "type": "TextHeading"},
                        {
                            "input-type": "email",
                            "label": "Enter your email",
                            "name": "email",
                            "required": True,
                            "type": "TextInput",
                        },
                        {
                            "label": "By subscribing, you agree to "
                            "receive our newsletter.",
                            "name": "opt_in",
                            "required": True,
                            "type": "OptIn",
                        },
                        {
                            "label": "Subscribe!",
                            "on-click-action": {
                                "name": "complete",
                                "payload": {"email": "${form.email}"},
                            },
                            "type": "Footer",
                        },
                    ],
                    "type": "SingleColumnLayout",
                },
                "terminal": True,
                "title": "Newsletter Subscription",
            }
        ],
        "version": "7.0",
    }

    assert FlowButton(
        text="Start Flow",
        flow_name="newsletter_flow",
    ).params(
        index=0,
        flow_token="abc123",
        flow_action_data={
            "is_email_required": True,
            "is_name_input_visible": False,
        },
    ).to_dict() == {
        "type": "button",
        "sub_type": "FLOW",
        "index": 0,
        "parameters": [
            {
                "type": "action",
                "action": {
                    "flow_token": "abc123",
                    "flow_action_data": {
                        "is_email_required": True,
                        "is_name_input_visible": False,
                    },
                },
            },
        ],
    }

    pnb = PhoneNumberButton(text="Call Us", phone_number="+1234567890")
    assert pnb.to_dict() == {
        "type": "PHONE_NUMBER",
        "text": "Call Us",
        "phone_number": "+1234567890",
    }
    assert PhoneNumberButton.library_input(phone_number="+1234567890").to_dict() == {
        "type": "PHONE_NUMBER",
        "phone_number": "+1234567890",
    }

    assert VoiceCallButton(text="Call Us").to_dict() == {
        "type": "VOICE_CALL",
        "text": "Call Us",
    }

    qrb = QuickReplyButton(text="Unsubscribe")
    assert qrb.to_dict() == {
        "type": "QUICK_REPLY",
        "text": "Unsubscribe",
    }
    assert qrb.params(callback_data="unsubscribe", index=0).to_dict() == {
        "type": "button",
        "sub_type": "QUICK_REPLY",
        "index": 0,
        "parameters": [{"type": "payload", "payload": "unsubscribe"}],
    }

    ub = URLButton(text="Visit Website", url="https://example.com")
    assert ub.to_dict() == {
        "type": "URL",
        "text": "Visit Website",
        "url": "https://example.com",
    }
    assert URLButton(
        text="Visit Website",
        url="https://example.com?ref={{1}}",
        example="wa_android",
        app_deep_link=AppDeepLink(
            meta_app_id=12345678,
            android_deep_link="myapp://menu",
            android_fallback_playstore_url="https://play.google.com/store/apps/details?id=com.example.myapp",
        ),
    ).to_dict() == {
        "type": "URL",
        "text": "Visit Website",
        "url": "https://example.com?ref={{1}}",
        "example": ["wa_android"],
        "app_deep_link": {
            "meta_app_id": 12345678,
            "android_deep_link": "myapp://menu",
            "android_fallback_playstore_url": "https://play.google.com/store/apps/details?id=com.example.myapp",
        },
    }
    assert ub.params(url_variable="wa_ios", index=0).to_dict() == {
        "type": "button",
        "sub_type": "URL",
        "index": 0,
        "parameters": [
            {
                "type": "text",
                "text": "wa_ios",
            }
        ],
    }
    assert URLButton.library_input(
        base_url="https://example.com?ref={{1}}",
        url_suffix_example="https://example.com?ref=wa_android",
    ).to_dict() == {
        "type": "URL",
        "url": {
            "base_url": "https://example.com?ref={{1}}",
            "url_suffix_example": "https://example.com?ref=wa_android",
        },
    }

    cb = CatalogButton(text="View Catalog")
    assert cb.to_dict() == {
        "type": "CATALOG",
        "text": "View Catalog",
    }
    assert cb.params(thumbnail_product_sku="ITEM123", index=0).to_dict() == {
        "type": "button",
        "sub_type": "CATALOG",
        "index": 0,
        "parameters": [
            {
                "type": "action",
                "action": {"thumbnail_product_retailer_id": "ITEM123"},
            }
        ],
    }

    mpmb = MPMButton(text="View Products")
    assert mpmb.to_dict() == {
        "type": "MPM",
        "text": "View Products",
    }
    assert mpmb.params(
        thumbnail_product_sku="SKU12345",
        index=0,
        product_sections=[
            types.ProductsSection(
                title="Section 1",
                skus=["SKU12345", "SKU12346"],
            ),
            types.ProductsSection(
                title="Section 2",
                skus=["SKU12347", "SKU12348"],
            ),
        ],
    ).to_dict() == {
        "type": "button",
        "sub_type": "MPM",
        "index": 0,
        "parameters": [
            {
                "type": "action",
                "action": {
                    "thumbnail_product_retailer_id": "SKU12345",
                    "sections": [
                        {
                            "title": "Section 1",
                            "product_items": (
                                {"product_retailer_id": "SKU12345"},
                                {"product_retailer_id": "SKU12346"},
                            ),
                        },
                        {
                            "title": "Section 2",
                            "product_items": (
                                {"product_retailer_id": "SKU12347"},
                                {"product_retailer_id": "SKU12348"},
                            ),
                        },
                    ],
                },
            }
        ],
    }

    assert SPMButton(text="View Product").to_dict() == {
        "type": "SPM",
        "text": "View Product",
    }

    assert CallPermissionRequestButton().to_dict() == {
        "type": "CALL_PERMISSION_REQUEST",
    }

    otb = OneTapOTPButton(
        text="Autofill Code",
        autofill_text="Autofill",
        supported_apps=[
            OTPSupportedApp(
                package_name="com.example.app", signature_hash="K8a/AINcGX7"
            ),
        ],
    )
    assert otb.to_dict() == {
        "type": "OTP",
        "otp_type": "ONE_TAP",
        "text": "Autofill Code",
        "autofill_text": "Autofill",
        "supported_apps": [
            {
                "package_name": "com.example.app",
                "signature_hash": "K8a/AINcGX7",
            },
        ],
    }

    assert otb.params(otp="123456").to_dict() == {
        "type": "button",
        "sub_type": "URL",
        "index": 0,
        "parameters": [
            {
                "type": "text",
                "text": "123456",
            }
        ],
    }
    assert OneTapOTPButton.library_input(
        supported_apps=[
            OTPSupportedApp(
                package_name="com.example.app", signature_hash="K8a/AINcGX7"
            ),
        ]
    ).to_dict() == {
        "type": "OTP",
        "otp_type": "ONE_TAP",
        "supported_apps": [
            {
                "package_name": "com.example.app",
                "signature_hash": "K8a/AINcGX7",
            },
        ],
    }

    ztb = ZeroTapOTPButton(
        text="Copy Code",
        autofill_text="Copy",
        zero_tap_terms_accepted=True,
        supported_apps=[
            OTPSupportedApp(
                package_name="com.example.app", signature_hash="K8a/AINcGX7"
            ),
        ],
    )
    assert ztb.to_dict() == {
        "type": "OTP",
        "otp_type": "ZERO_TAP",
        "text": "Copy Code",
        "autofill_text": "Copy",
        "zero_tap_terms_accepted": True,
        "supported_apps": [
            {
                "package_name": "com.example.app",
                "signature_hash": "K8a/AINcGX7",
            },
        ],
    }
    assert ztb.params(otp="123456").to_dict() == {
        "type": "button",
        "sub_type": "URL",
        "index": 0,
        "parameters": [
            {
                "type": "text",
                "text": "123456",
            }
        ],
    }
    assert ZeroTapOTPButton.library_input(
        zero_tap_terms_accepted=True,
        supported_apps=[
            OTPSupportedApp(
                package_name="com.example.app", signature_hash="K8a/AINcGX7"
            ),
        ],
    ).to_dict() == {
        "type": "OTP",
        "otp_type": "ZERO_TAP",
        "zero_tap_terms_accepted": True,
        "supported_apps": [
            {
                "package_name": "com.example.app",
                "signature_hash": "K8a/AINcGX7",
            },
        ],
    }

    assert CopyCodeOTPButton().to_dict() == {
        "type": "OTP",
        "otp_type": "COPY_CODE",
    }
    assert CopyCodeOTPButton.library_input().to_dict() == {
        "type": "OTP",
        "otp_type": "COPY_CODE",
    }

    lto = LimitedTimeOffer(text="Limited Time", has_expiration=True)
    assert lto.to_dict() == {
        "type": "LIMITED_TIME_OFFER",
        "limited_time_offer": {
            "text": "Limited Time",
            "has_expiration": True,
        },
    }
    now = datetime.datetime.now()
    assert lto.params(expiration_time=now).to_dict() == {
        "type": "LIMITED_TIME_OFFER",
        "parameters": [
            {
                "type": "limited_time_offer",
                "limited_time_offer": {
                    "expiration_time_ms": int(now.timestamp()),
                },
            }
        ],
    }
    ttc = TapTargetConfiguration(
        title="Offer Details", url="https://www.luckyshrubs.com/"
    )
    assert ttc.to_dict() == {
        "type": "tap_target_configuration",
        "parameters": [
            {
                "type": "tap_target_configuration",
                "tap_target_configuration": [
                    {"url": "https://www.luckyshrubs.com/", "title": "Offer Details"}
                ],
            }
        ],
    }


def test_validate_template_params():
    Template(
        name="test_template_no_params",
        language=TemplateLanguage.ENGLISH_US,
        category=TemplateCategory.MARKETING,
        components=[
            BodyText(text="Hello World!"),
        ],
    ).validate_params(params=None)

    Template(
        name="test_template_without_real_params",
        language=TemplateLanguage.ENGLISH_US,
        category=TemplateCategory.MARKETING,
        components=[
            {"type": "new_component"},
        ],
    ).validate_params(
        params=[
            TapTargetConfiguration(
                title="PyWa Docs", url="https://pywa.readthedocs.io/"
            ),
            {"type": "new_type", "parameters": []},
        ]
    )

    with pytest.raises(
        ValueError,
        match="Template does not expect any parameters, but some were provided.",
    ):
        t = Template(
            name="test_template_no_params",
            language=TemplateLanguage.ENGLISH_US,
            category=TemplateCategory.MARKETING,
            components=[
                BodyText(text="Hello World!"),
            ],
        )
        t.validate_params(
            [
                BodyText.params("Extra Param"),
            ]
        )

    with pytest.raises(
        ValueError,
        match=r"Missing parameter for button #0 \(QuickReplyButton\)",
    ):
        t = Template(
            name="test_template_with_button_not_in_index",
            language=TemplateLanguage.ENGLISH_US,
            category=TemplateCategory.MARKETING,
            components=[
                Buttons(buttons=[QuickReplyButton(text="Click Me")]),
            ],
        )
        t.validate_params(params=None)

    with pytest.raises(
        ValueError,
        match="Missing parameters for: BodyText$",
    ):
        t = Template(
            name="test_template_with_body_param",
            language=TemplateLanguage.ENGLISH_US,
            category=TemplateCategory.MARKETING,
            components=[
                BodyText(
                    "Hello {{name}}, welcome to our service!",
                    name="User",
                ),
            ],
        )
        t.validate_params(params=None)

    with pytest.raises(
        ValueError,
        match="Missing parameters for Carousel component.",
    ):
        t = Template(
            name="test_template_with_carousel",
            language=TemplateLanguage.ENGLISH_US,
            category=TemplateCategory.MARKETING,
            components=[
                Carousel(
                    cards=[
                        CarouselCard(
                            components=[
                                BodyText(
                                    "Hello {{name}}",
                                    name="User",
                                )
                            ]
                        )
                    ]
                )
            ],
        )
        t.validate_params(params=None)

    with pytest.raises(
        ValueError, match="Expected 2 cards in Carousel parameters, but got 1."
    ):
        t = Template(
            name="test_template_with_carousel_card_param",
            language=TemplateLanguage.ENGLISH_US,
            category=TemplateCategory.MARKETING,
            components=[
                Carousel(
                    cards=[
                        CarouselCard(
                            components=[
                                BodyText(
                                    "Hello {{name}}",
                                    name="User",
                                )
                            ]
                        )
                        for _ in range(2)
                    ]
                )
            ],
        )
        t.validate_params(
            params=[
                Carousel.params(
                    cards=[
                        CarouselCard.params(
                            index=0,
                            params=[
                                BodyText.params(name="Alice"),
                            ],
                        )
                    ]
                )
            ]
        )

    with pytest.raises(
        ValueError, match="In Carousel card #0: Missing parameters for: BodyText"
    ):
        t = Template(
            name="test_template_with_carousel_card_param_missing",
            language=TemplateLanguage.ENGLISH_US,
            category=TemplateCategory.MARKETING,
            components=[
                Carousel(
                    cards=[
                        CarouselCard(
                            components=[
                                BodyText(
                                    "Hello {{name}}",
                                    name="User",
                                )
                            ]
                        )
                        for _ in range(2)
                    ]
                )
            ],
        )
        t.validate_params(
            params=[
                Carousel.params(
                    cards=[
                        CarouselCard.params(
                            index=0,
                            params=[
                                # Missing BodyText params
                            ],
                        ),
                        CarouselCard.params(
                            index=1,
                            params=[
                                BodyText.params(name="Bob"),
                            ],
                        ),
                    ]
                )
            ]
        )

    with pytest.raises(
        ValueError,
        match="Missing parameters for: HeaderText, BodyText$",
    ):
        t = Template(
            name="test_template_with_header_and_body_params",
            language=TemplateLanguage.ENGLISH_US,
            category=TemplateCategory.MARKETING,
            components=[
                HeaderText(
                    "Welcome {{user}}",
                    user="Customer",
                ),
                BodyText(
                    "Your order {{order_id}} is confirmed.",
                    order_id="12345",
                ),
            ],
        )
        t.validate_params(params=None)

    with pytest.raises(
        ValueError,
        match="Extra parameters provided: BodyText, QuickReplyButton$",
    ):
        t = Template(
            name="test_template_no_params_but_extra_provided",
            language=TemplateLanguage.ENGLISH_US,
            category=TemplateCategory.MARKETING,
            components=[
                HeaderText(text="Welcome {{user}}", user="Customer"),
            ],
        )
        t.validate_params(
            params=[
                BodyText.params("Extra Body"),
                QuickReplyButton.params(callback_data="extra", index=0),
            ]
        )


def test_template_get_header():
    t = Template(
        name="test_template_get_header",
        language=TemplateLanguage.ENGLISH_US,
        category=TemplateCategory.MARKETING,
        components=[
            HeaderText(text="Welcome {{user}}", user="Customer"),
        ],
    )
    assert isinstance(t.get_component(HeaderText), HeaderText)


def test_template_get_body():
    t = Template(
        name="test_template_get_body",
        language=TemplateLanguage.ENGLISH_US,
        category=TemplateCategory.MARKETING,
        components=[
            BodyText(
                text="Your order {{order_id}} is confirmed.",
                order_id="12345",
            ),
        ],
    )
    assert isinstance(t.get_component(BodyText), BodyText)


def test_template_get_component_from_buttons():
    t = Template(
        name="test_template_get_component",
        language=TemplateLanguage.ENGLISH_US,
        category=TemplateCategory.MARKETING,
        components=[
            Buttons(
                buttons=[
                    QuickReplyButton(text="Support"),
                ]
            ),
        ],
    )
    assert isinstance(t.get_component(QuickReplyButton), QuickReplyButton)


def test_template_get_component_from_carousel():
    t = Template(
        name="test_template_get_component",
        language=TemplateLanguage.ENGLISH_US,
        category=TemplateCategory.MARKETING,
        components=[
            Carousel(
                cards=[
                    CarouselCard(
                        components=[
                            HeaderText(text="Welcome {{user}}", user="Customer"),
                        ]
                    )
                ]
            )
        ],
    )
    assert isinstance(t.get_component(HeaderText), HeaderText)


def test_template_get_components():
    t = Template(
        name="test_template_get_component",
        language=TemplateLanguage.ENGLISH_US,
        category=TemplateCategory.MARKETING,
        components=[
            Buttons(
                buttons=[
                    QuickReplyButton(text="1"),
                    QuickReplyButton(text="2"),
                ]
            ),
        ],
    )
    comps = t.get_components(QuickReplyButton)
    assert len(comps) == 2
    for component in comps:
        assert isinstance(component, QuickReplyButton)


def test_template_get_components_from_carousel():
    t = Template(
        name="test_template_get_components",
        language=TemplateLanguage.ENGLISH_US,
        category=TemplateCategory.MARKETING,
        components=[
            Carousel(
                cards=[
                    CarouselCard(
                        components=[
                            HeaderText(text="1"),
                        ]
                    ),
                    CarouselCard(
                        components=[
                            HeaderText(text="2"),
                        ]
                    ),
                ]
            )
        ],
    )
    comps = t.get_components(HeaderText)
    assert len(comps) == 2
    for component in comps:
        assert isinstance(component, HeaderText)
