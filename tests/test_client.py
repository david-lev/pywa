import dataclasses
import json
import datetime
import tempfile
from platform import system

import pytest

from pywa import WhatsApp, types, utils, _helpers as helpers, filters
from pywa.types import Contact
from pywa.types.media import Media

PHONE_ID = "123456789"
TOKEN = "xyz"
WABA_ID = "987654321"
MSG_ID = "wamid.xx=="
MEDIA_ID = "mediaid.xx=="
TO = "135792468"
SENT_MESSAGE = {
    "messaging_product": "whatsapp",
    "contacts": [{"input": TO, "wa_id": TO}],
    "messages": [{"id": MSG_ID}],
}


@pytest.fixture
def api(mocker):
    return mocker.patch("pywa.client.WhatsApp.api")


@pytest.fixture
def wa():
    return WhatsApp(phone_id=PHONE_ID, token=TOKEN)


def test_api_usage_without_token():
    with pytest.raises(ValueError):
        _ = WhatsApp(phone_id="123", token="").api

    with pytest.raises(ValueError):
        _ = WhatsApp(token=None).api


def test_warning_when_version_lower_than_min():
    with pytest.warns(RuntimeWarning):
        WhatsApp(phone_id="123", token="123", api_version="16.0")


def test_wa_callback_scopes():
    with pytest.raises(ValueError):
        WhatsApp(
            callback_url_scope=utils.CallbackURLScope.APP,
            app_id=None,
            app_secret=None,
            server=None,
            callback_url="https://exmaple.com",
            verify_token="xyzxyz",
        )

    with pytest.raises(ValueError):
        WhatsApp(
            callback_url_scope=utils.CallbackURLScope.WABA,
            business_account_id=None,
            server=None,
            callback_url="https://exmaple.com",
            verify_token="xyzxyz",
        )

    with pytest.raises(ValueError):
        WhatsApp(
            callback_url_scope=utils.CallbackURLScope.PHONE,
            phone_id=None,
            server=None,
            callback_url="https://exmaple.com",
            verify_token="xyzxyz",
        )


def test_resolve_buttons_param():
    assert helpers.resolve_buttons_param(
        [
            types.Button(title="Button 1", callback_data="button1"),
            types.Button(title="Button 2", callback_data="button2"),
        ]
    ) == (
        types.others.InteractiveType.BUTTON,
        {
            "buttons": (
                {"type": "reply", "reply": {"id": "button1", "title": "Button 1"}},
                {"type": "reply", "reply": {"id": "button2", "title": "Button 2"}},
            )
        },
        {"_callback_options": {"button2", "button1"}},
    )

    assert helpers.resolve_buttons_param(
        types.URLButton(title="PyWa Docs", url="https://pywa.readthedocs.io")
    ) == (
        types.others.InteractiveType.CTA_URL,
        {
            "name": "cta_url",
            "parameters": {
                "display_text": "PyWa Docs",
                "url": "https://pywa.readthedocs.io",
            },
        },
        {},
    )

    assert helpers.resolve_buttons_param(
        types.VoiceCallButton(
            title="Call me",
            ttl_minutes=50,
        )
    ) == (
        types.others.InteractiveType.VOICE_CALL,
        {
            "name": "voice_call",
            "parameters": {
                "display_text": "Call me",
                "ttl_minutes": 50,
            },
        },
        {},
    )

    assert helpers.resolve_buttons_param(
        types.FlowButton(
            title="Next",
            flow_id="flow_id",
            flow_token="flow_token",
            flow_action_type=types.FlowActionType.NAVIGATE,
            flow_action_screen="START",
            flow_action_payload={"key": "value"},
            flow_message_version="3",
        )
    ) == (
        types.others.InteractiveType.FLOW,
        {
            "name": "flow",
            "parameters": {
                "mode": "published",
                "flow_message_version": "3",
                "flow_token": "flow_token",
                "flow_id": "flow_id",
                "flow_cta": "Next",
                "flow_action": "navigate",
                "flow_action_payload": {
                    "screen": "START",
                    "data": {"key": "value"},
                },
            },
        },
        {"_flow_token": "flow_token"},
    )

    assert helpers.resolve_buttons_param(
        types.SectionList(
            button_title="Menu",
            sections=[
                types.Section(
                    title="Section 1",
                    rows=[
                        types.SectionRow(
                            title="Row 1",
                            description="Description 1",
                            callback_data="row1",
                        )
                    ],
                )
            ],
        )
    ) == (
        types.others.InteractiveType.LIST,
        {
            "button": "Menu",
            "sections": (
                {
                    "title": "Section 1",
                    "rows": (
                        {
                            "id": "row1",
                            "title": "Row 1",
                            "description": "Description 1",
                        },
                    ),
                },
            ),
        },
        {"_callback_options": {"row1"}},
    )


def test_get_interactive_msg():
    assert helpers.get_interactive_msg(
        typ=types.others.InteractiveType.BUTTON,
        action={
            "buttons": (
                {"type": "reply", "reply": {"id": "button1", "title": "Button 1"}},
                {"type": "reply", "reply": {"id": "button2", "title": "Button 2"}},
            )
        },
        header={
            "type": types.MessageType.TEXT,
            "text": "header text",
        },
        body="body text",
        footer="footer text",
    ) == {
        "type": types.MessageType.BUTTON,
        "action": {
            "buttons": (
                {"type": "reply", "reply": {"id": "button1", "title": "Button 1"}},
                {"type": "reply", "reply": {"id": "button2", "title": "Button 2"}},
            )
        },
        "header": {
            "type": types.MessageType.TEXT,
            "text": "header text",
        },
        "body": {"text": "body text"},
        "footer": {"text": "footer text"},
    }


def test_get_media_msg():
    assert helpers.get_media_msg(
        media_id_or_url="1234",
        is_url=False,
        caption="caption",
        filename="filename",
    ) == {
        "id": "1234",
        "caption": "caption",
        "filename": "filename",
    }


def test_get_flow_metric_field():
    assert (
        helpers.get_flow_metric_field(
            metric_name=types.FlowMetricName.ENDPOINT_AVAILABILITY,
            granularity=types.FlowMetricGranularity.HOUR,
            since=datetime.date(2021, 1, 1),
            until=datetime.date(2021, 1, 2),
        )
        == "metric.name(ENDPOINT_AVAILABILITY).granularity(HOUR).since(2021-01-01).until(2021-01-02)"
    )

    assert (
        helpers.get_flow_metric_field(
            metric_name=types.FlowMetricName.ENDPOINT_AVAILABILITY,
            granularity=types.FlowMetricGranularity.HOUR,
            since=datetime.date(2021, 1, 1),
            until=None,
        )
        == "metric.name(ENDPOINT_AVAILABILITY).granularity(HOUR).since(2021-01-01)"
    )

    assert (
        helpers.get_flow_metric_field(
            metric_name=types.FlowMetricName.ENDPOINT_AVAILABILITY,
            granularity=types.FlowMetricGranularity.HOUR,
            since=None,
            until=datetime.date(2021, 1, 2),
        )
        == "metric.name(ENDPOINT_AVAILABILITY).granularity(HOUR).until(2021-01-02)"
    )


def test_resolve_callback_data():
    @dataclasses.dataclass
    class User(types.CallbackData):
        __callback_id__ = "user"
        __callback_data_sep__ = ":"
        id: str
        name: str

    assert helpers.resolve_callback_data(User(id="123", name="John")) == "user:123:John"

    assert helpers.resolve_callback_data("user:123:John") == "user:123:John"


def test_resolve_tracker_param():
    @dataclasses.dataclass
    class User(types.CallbackData):
        __callback_id__ = "user"
        __callback_data_sep__ = ":"
        id: str
        name: str

    assert helpers.resolve_tracker_param(User(id="123", name="John")) == "user:123:John"
    assert helpers.resolve_tracker_param("user:123:John") == "user:123:John"


def test_resolve_flow_json_param():
    assert json.loads(helpers.resolve_flow_json_param("""{"key": "value"}""")) == {
        "key": "value"
    }

    assert json.loads(helpers.resolve_flow_json_param({"key": "value"})) == {
        "key": "value"
    }

    assert json.loads(helpers.resolve_flow_json_param(b'{"key": "value"}')) == {
        "key": "value"
    }

    assert json.loads(
        helpers.resolve_flow_json_param(
            types.flows.FlowJSON(
                version="6.0",
                screens=[
                    types.flows.Screen(
                        id="START",
                        layout=types.flows.Layout(
                            children=[
                                types.flows.TextHeading(
                                    text="Hello World",
                                )
                            ],
                        ),
                    )
                ],
            )
        )
    ) == {
        "version": "6.0",
        "screens": [
            {
                "id": "START",
                "layout": {
                    "type": "SingleColumnLayout",
                    "children": [
                        {
                            "type": "TextHeading",
                            "text": "Hello World",
                        }
                    ],
                },
            }
        ],
    }


def test_resolve_waba_id_param():
    client = WhatsApp(business_account_id=WABA_ID)

    assert (
        helpers.resolve_arg(
            wa=client,
            value=None,
            method_arg="waba_id",
            client_arg="business_account_id",
        )
        == WABA_ID
    )
    assert (
        helpers.resolve_arg(
            wa=client,
            value=987654321,
            method_arg="waba_id",
            client_arg="business_account_id",
        )
        == "987654321"
    )

    with pytest.raises(ValueError):
        helpers.resolve_arg(
            wa=WhatsApp(),
            value=None,
            method_arg="waba_id",
            client_arg="business_account_id",
        )


def test_resolve_phone_id_param():
    client = WhatsApp(phone_id=PHONE_ID)

    assert (
        helpers.resolve_arg(
            wa=client, value=None, method_arg="phone_id", client_arg="phone_id"
        )
        == PHONE_ID
    )
    assert (
        helpers.resolve_arg(
            wa=client, value="1234567890", method_arg="phone_id", client_arg="phone_id"
        )
        == "1234567890"
    )

    with pytest.raises(ValueError):
        helpers.resolve_arg(
            wa=WhatsApp(), value=None, method_arg="phone_id", client_arg="phone_id"
        )


def test_resolve_media_param_with_url():
    assert helpers.resolve_media_param(
        wa=wa,
        media="https://example.com/image.jpg",
        mime_type=None,
        filename=None,
        media_type=types.MessageType.IMAGE,
        phone_id=PHONE_ID,
    ) == (True, "https://example.com/image.jpg")


def test_resolve_media_param_with_media_id():
    assert helpers.resolve_media_param(
        wa=wa,
        media="1234567890",
        mime_type=None,
        filename=None,
        media_type=types.MessageType.IMAGE,
        phone_id=PHONE_ID,
    ) == (False, "1234567890")


def test_resolve_media_param_with_media():
    assert helpers.resolve_media_param(
        wa=wa,
        media=Media(_client=wa, id="1234567890"),
        mime_type=None,
        filename=None,
        media_type=types.MessageType.IMAGE,
        phone_id=PHONE_ID,
    ) == (False, "1234567890")


def test_check_for_async_callback():
    client = WhatsApp(server=None, verify_token="xyz")

    async def callback(): ...

    with pytest.raises(ValueError):
        client._check_for_async_callback(callback)


def test_check_for_async_filters():
    client = WhatsApp(server=None, verify_token="xyz")

    async def callback(_, __) -> bool: ...

    with pytest.raises(ValueError):
        client._check_for_async_filters(filters.new(callback))


def test_token(wa):
    assert wa.token == TOKEN
    wa.token = "abc"
    assert wa.token == "abc"
    assert wa.api._session.headers["Authorization"] == "Bearer abc"


def test_send_message(api, wa):
    api.return_value.send_message.return_value = SENT_MESSAGE
    wa.send_text(
        to=TO,
        text="Hello",
        reply_to_message_id=MSG_ID,
    )
    api.send_message.assert_called_once_with(
        sender=PHONE_ID,
        to=TO,
        typ=types.MessageType.TEXT,
        msg={"body": "Hello", "preview_url": False},
        reply_to_message_id=MSG_ID,
        biz_opaque_callback_data=None,
    )


def test_send_image(api, wa):
    api.return_value.send_message.return_value = SENT_MESSAGE
    wa.send_image(
        to=TO,
        image="https://example.com/image.jpg",
        caption="caption",
        reply_to_message_id=MSG_ID,
    )
    api.send_message.assert_called_once_with(
        sender=PHONE_ID,
        to=TO,
        typ=types.MessageType.IMAGE,
        msg={
            "link": "https://example.com/image.jpg",
            "caption": "caption",
        },
        reply_to_message_id=MSG_ID,
        biz_opaque_callback_data=None,
    )


def test_send_video(api, wa):
    api.return_value.send_message.return_value = SENT_MESSAGE
    wa.send_video(
        to=TO,
        video="1234567890",
        caption="caption",
    )
    api.send_message.assert_called_once_with(
        sender=PHONE_ID,
        to=TO,
        typ=types.MessageType.VIDEO,
        msg={
            "id": "1234567890",
            "caption": "caption",
        },
        reply_to_message_id=None,
        biz_opaque_callback_data=None,
    )


def test_send_audio(api, wa):
    api.return_value.send_message.return_value = SENT_MESSAGE
    wa.send_audio(
        to=TO,
        audio="1234567890",
    )
    api.send_message.assert_called_once_with(
        sender=PHONE_ID,
        to=TO,
        typ=types.MessageType.AUDIO,
        msg={
            "id": "1234567890",
        },
        reply_to_message_id=None,
        biz_opaque_callback_data=None,
    )


def test_send_document(api, wa):
    api.return_value.send_message.return_value = SENT_MESSAGE
    wa.send_document(
        to=TO,
        document="1234567890",
        filename="filename",
    )
    api.send_message.assert_called_once_with(
        sender=PHONE_ID,
        to=TO,
        typ=types.MessageType.DOCUMENT,
        msg={
            "id": "1234567890",
            "filename": "filename",
        },
        reply_to_message_id=None,
        biz_opaque_callback_data=None,
    )


def test_send_location(api, wa):
    api.return_value.send_message.return_value = SENT_MESSAGE
    wa.send_location(
        to=TO,
        latitude=12.34,
        longitude=56.78,
        address="Address",
    )
    api.send_message.assert_called_once_with(
        sender=PHONE_ID,
        to=TO,
        typ=types.MessageType.LOCATION,
        msg={
            "latitude": 12.34,
            "longitude": 56.78,
            "name": None,
            "address": "Address",
        },
        reply_to_message_id=None,
        biz_opaque_callback_data=None,
    )


def test_send_contact(api, wa):
    api.return_value.send_message.return_value = SENT_MESSAGE
    wa.send_contact(
        to=TO,
        contact=types.Contact(
            name=Contact.Name(
                formatted_name="John Doe", first_name="John", last_name="Doe"
            ),
            phones=[Contact.Phone(phone=TO, type="WORK")],
            birthday="2000-01-01",
            emails=[Contact.Email(email="john@doe.com", type="WORK")],
            addresses=[
                Contact.Address(street="123 Main St", city="Anytown", country="USA")
            ],
            urls=[Contact.Url(url="https://example.com", type="WORK")],
            org=Contact.Org(company="Example Inc", department="Engineering"),
        ),
    )
    api.send_message.assert_called_once_with(
        sender=PHONE_ID,
        to=TO,
        typ=types.MessageType.CONTACTS,
        msg=(
            {
                "name": {
                    "formatted_name": "John Doe",
                    "first_name": "John",
                    "last_name": "Doe",
                    "middle_name": None,
                    "suffix": None,
                    "prefix": None,
                },
                "birthday": "2000-01-01",
                "phones": ({"phone": "135792468", "type": "WORK", "wa_id": None},),
                "emails": ({"email": "john@doe.com", "type": "WORK"},),
                "urls": ({"url": "https://example.com", "type": "WORK"},),
                "addresses": (
                    {
                        "street": "123 Main St",
                        "city": "Anytown",
                        "state": None,
                        "zip": None,
                        "country": "USA",
                        "country_code": None,
                        "type": None,
                    },
                ),
                "org": {
                    "company": "Example Inc",
                    "department": "Engineering",
                    "title": None,
                },
            },
        ),
        reply_to_message_id=None,
        biz_opaque_callback_data=None,
    )


def test_send_sticker(api, wa):
    api.return_value.send_message.return_value = SENT_MESSAGE
    wa.send_sticker(
        to=TO,
        sticker="1234567890",
    )
    api.send_message.assert_called_once_with(
        sender=PHONE_ID,
        to=TO,
        typ=types.MessageType.STICKER,
        msg={
            "id": "1234567890",
        },
        reply_to_message_id=None,
        biz_opaque_callback_data=None,
    )


def test_send_reaction(api, wa):
    api.return_value.send_message.return_value = SENT_MESSAGE
    wa.send_reaction(
        to=TO,
        emoji="😍",
        message_id=MSG_ID,
    )
    api.send_message.assert_called_once_with(
        sender=PHONE_ID,
        to=TO,
        typ=types.MessageType.REACTION,
        msg={
            "emoji": "😍",
            "message_id": MSG_ID,
        },
        biz_opaque_callback_data=None,
    )


def test_remove_reaction(api, wa):
    api.return_value.send_message.return_value = SENT_MESSAGE
    wa.remove_reaction(
        to=TO,
        message_id=MSG_ID,
    )
    api.send_message.assert_called_once_with(
        sender=PHONE_ID,
        to=TO,
        typ=types.MessageType.REACTION,
        msg={
            "emoji": "",
            "message_id": MSG_ID,
        },
        biz_opaque_callback_data=None,
    )


def test_request_location(api, wa):
    api.return_value.send_message.return_value = SENT_MESSAGE
    wa.request_location(
        to=TO,
        text="Send your location",
        reply_to_message_id=MSG_ID,
    )
    api.send_message.assert_called_once_with(
        sender=PHONE_ID,
        to=TO,
        typ=types.MessageType.INTERACTIVE,
        msg={
            "action": {
                "name": "send_location",
            },
            "body": {"text": "Send your location"},
            "type": types.others.InteractiveType.LOCATION_REQUEST_MESSAGE,
        },
        reply_to_message_id=MSG_ID,
        biz_opaque_callback_data=None,
    )


def test_send_catalog(api, wa):
    api.return_value.send_message.return_value = SENT_MESSAGE
    wa.send_catalog(
        to=TO,
        body="Hello",
        thumbnail_product_sku="IPHONE_8",
    )
    api.send_message.assert_called_once_with(
        sender=PHONE_ID,
        to=TO,
        typ=types.MessageType.INTERACTIVE,
        msg={
            "action": {
                "name": "catalog_message",
                "parameters": {
                    "thumbnail_product_retailer_id": "IPHONE_8",
                },
            },
            "body": {"text": "Hello"},
            "type": types.others.InteractiveType.CATALOG_MESSAGE,
        },
        reply_to_message_id=None,
        biz_opaque_callback_data=None,
    )


def test_send_product(api, wa):
    api.return_value.send_message.return_value = SENT_MESSAGE
    wa.send_product(
        to=TO,
        catalog_id="1234567890",
        sku="IPHONE_8",
    )
    api.send_message.assert_called_once_with(
        sender=PHONE_ID,
        to=TO,
        typ=types.MessageType.INTERACTIVE,
        msg={
            "action": {
                "catalog_id": "1234567890",
                "product_retailer_id": "IPHONE_8",
            },
            "type": types.others.InteractiveType.PRODUCT,
        },
        reply_to_message_id=None,
        biz_opaque_callback_data=None,
    )


def test_send_products(api, wa):
    api.return_value.send_message.return_value = SENT_MESSAGE
    wa.send_products(
        to=TO,
        title="Products",
        body="Hello",
        catalog_id="1234567890",
        product_sections=[
            types.ProductsSection(
                title="Section 1",
                skus=["IPHONE_8", "IPHONE_X"],
            )
        ],
    )
    api.send_message.assert_called_once_with(
        sender=PHONE_ID,
        to=TO,
        typ=types.MessageType.INTERACTIVE,
        msg={
            "action": {
                "catalog_id": "1234567890",
                "sections": (
                    {
                        "product_items": (
                            {
                                "product_retailer_id": "IPHONE_8",
                            },
                            {
                                "product_retailer_id": "IPHONE_X",
                            },
                        ),
                        "title": "Section 1",
                    },
                ),
            },
            "body": {"text": "Hello"},
            "header": {"text": "Products", "type": types.MessageType.TEXT},
            "type": types.others.InteractiveType.PRODUCT_LIST,
        },
        reply_to_message_id=None,
        biz_opaque_callback_data=None,
    )
