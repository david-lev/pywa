import datetime

from pywa import types, WhatsApp
from pywa.types import Result
from pywa.types.flows import FlowDetails
from pywa.types.sent_update import (
    SentMessage,
    SentTemplate,
    SentTemplateStatus,
    InitiatedCall,
)
import pytest
from unittest.mock import MagicMock, call

wa = WhatsApp(phone_id="123456789", token="token")


def test_flow_details():
    assert FlowDetails.from_dict(
        client=wa,
        data={
            "id": "12345",
            "name": "my_flow",
            "status": "DRAFT",
            "updated_at": "2024-10-29T21:09:19+0000",
            "categories": ["OTHER"],
            "validation_errors": [],
            "json_version": "5.1",
            "data_api_version": "3.0",
            "endpoint_uri": "https://example.com/flow",
            "preview": {
                "preview_url": "https://business.facebook.com/wa/manage/flows/12345/preview/?token=xyz",
                "expires_at": "2024-12-31T18:45:52+0000",
            },
            "whatsapp_business_account": {
                "id": "124578",
                "name": "Test WhatsApp Business Account",
                "timezone_id": "1",
                "message_template_namespace": "1acaxyzfec",
            },
            "application": {
                "link": "https://www.facebook.com/games/?app_id=12345",
                "name": "My App",
                "id": "12345",
            },
        },
    ) == FlowDetails(
        _client=wa,
        id="12345",
        name="my_flow",
        status=types.flows.FlowStatus.DRAFT,
        updated_at=datetime.datetime(
            2024, 10, 29, 21, 9, 19, tzinfo=datetime.timezone.utc
        ),
        categories=(types.flows.FlowCategory.OTHER,),
        validation_errors=None,
        json_version="5.1",
        data_api_version="3.0",
        endpoint_uri="https://example.com/flow",
        preview=types.flows.FlowPreview(
            url="https://business.facebook.com/wa/manage/flows/12345/preview/?token=xyz",
            expires_at=datetime.datetime(
                2024, 12, 31, 18, 45, 52, tzinfo=datetime.timezone.utc
            ),
        ),
        whatsapp_business_account=types.others.WhatsAppBusinessAccount(
            id="124578",
            name="Test WhatsApp Business Account",
            timezone_id="1",
            message_template_namespace="1acaxyzfec",
            status=None,
            business_verification_status=None,
            is_enabled_for_insights=None,
            marketing_messages_onboarding_status=None,
            marketing_messages_lite_api_status=None,
            on_behalf_of_business_info=None,
            ownership_type=None,
            health_status=None,
            country=None,
            currency=None,
            subscribed_apps=None,
        ),
        application=types.flows.FacebookApplication(
            link="https://www.facebook.com/games/?app_id=12345",
            name="My App",
            id="12345",
        ),
    )


def test_business_profile():
    assert types.BusinessProfile.from_dict(
        data={
            "about": "Hey there! I am using PyWa.",
            "email": "user@server.com",
            "websites": ["https://pywa.readthedocs.io/"],
            "vertical": "PROF_SERVICES",
            "messaging_product": "whatsapp",
            "address": "123 Main St, San Francisco, CA 94107",
            "description": "Business Description",
        }
    ) == types.BusinessProfile(
        about="Hey there! I am using PyWa.",
        email="user@server.com",
        websites=("https://pywa.readthedocs.io/",),
        industry=types.others.Industry.PROF_SERVICES,
        profile_picture_url=None,
        description="Business Description",
        address="123 Main St, San Francisco, CA 94107",
    )


def test_business_phone_number():
    assert types.BusinessPhoneNumber.from_dict(
        data={
            "id": "123456789",
            "verified_name": "Test Number",
            "display_phone_number": "+1 123-456-7890",
            "conversational_automation": {
                "prompts": ["Hi man"],
                "commands": [
                    {"command_name": "start", "command_description": "Start"},
                    {"command_name": "help", "command_description": "Help"},
                ],
                "enable_welcome_message": False,
                "id": "47328947638",
            },
            "status": "CONNECTED",
            "quality_rating": "GREEN",
            "quality_score": {"score": "GREEN"},
            "webhook_configuration": {"application": "https://example.com/wa_webhook"},
            "name_status": "APPROVED",
            "new_name_status": "NONE",
            "code_verification_status": "NOT_VERIFIED",
            "account_mode": "LIVE",
            "is_on_biz_app": True,
            "is_official_business_account": False,
            "is_pin_enabled": True,
            "is_preverified_number": False,
            "messaging_limit_tier": "TIER_1K",
            "search_visibility": "NON_VISIBLE",
            "platform_type": "CLOUD_API",
            "throughput": {"level": "STANDARD"},
            "eligibility_for_api_business_global_search": "NON_ELIGIBLE_UNDEFINED_COUNTRY",
            "health_status": {
                "can_send_message": "BLOCKED",
                "entities": [
                    {
                        "entity_type": "PHONE_NUMBER",
                        "id": "123456789",
                        "can_send_message": "AVAILABLE",
                    },
                    {
                        "entity_type": "WABA",
                        "id": "8976r843r3r3",
                        "can_send_message": "BLOCKED",
                        "errors": [
                            {
                                "error_code": 141006,
                                "error_description": "There is an error with the payment method. This will block business initiated conversations.",
                                "possible_solution": "There was an error with your payment method. Please add a new payment method to the account.",
                            }
                        ],
                    },
                    {
                        "entity_type": "BUSINESS",
                        "id": "473958473543",
                        "can_send_message": "AVAILABLE",
                    },
                    {
                        "entity_type": "APP",
                        "id": "4759843753",
                        "can_send_message": "AVAILABLE",
                    },
                ],
            },
        }
    ) == types.BusinessPhoneNumber(
        id="123456789",
        verified_name="Test Number",
        display_phone_number="+1 123-456-7890",
        conversational_automation=types.others.ConversationalAutomation(
            id="47328947638",
            chat_opened_enabled=False,
            ice_breakers=("Hi man",),
            commands=(
                types.others.Command(name="start", description="Start"),
                types.others.Command(name="help", description="Help"),
            ),
        ),
        status="CONNECTED",
        quality_rating="GREEN",
        quality_score={"score": "GREEN"},
        webhook_configuration={"application": "https://example.com/wa_webhook"},
        name_status="APPROVED",
        new_name_status="NONE",
        code_verification_status="NOT_VERIFIED",
        account_mode="LIVE",
        is_on_biz_app=True,
        is_official_business_account=False,
        is_pin_enabled=True,
        is_preverified_number=False,
        messaging_limit_tier="TIER_1K",
        search_visibility="NON_VISIBLE",
        platform_type="CLOUD_API",
        throughput={"level": "STANDARD"},
        eligibility_for_api_business_global_search="NON_ELIGIBLE_UNDEFINED_COUNTRY",
        health_status={
            "can_send_message": "BLOCKED",
            "entities": [
                {
                    "entity_type": "PHONE_NUMBER",
                    "id": "123456789",
                    "can_send_message": "AVAILABLE",
                },
                {
                    "entity_type": "WABA",
                    "id": "8976r843r3r3",
                    "can_send_message": "BLOCKED",
                    "errors": [
                        {
                            "error_code": 141006,
                            "error_description": "There is an error with the payment method. This will block business initiated conversations.",
                            "possible_solution": "There was an error with your payment method. Please add a new payment method to the account.",
                        }
                    ],
                },
                {
                    "entity_type": "BUSINESS",
                    "id": "473958473543",
                    "can_send_message": "AVAILABLE",
                },
                {
                    "entity_type": "APP",
                    "id": "4759843753",
                    "can_send_message": "AVAILABLE",
                },
            ],
        },
        certificate=None,
        new_certificate=None,
        last_onboarded_time=None,
    )


def test_sent_message():
    sm = SentMessage.from_sent_update(
        client=wa,
        update={
            "messaging_product": "whatsapp",
            "contacts": [{"input": "16505555555", "wa_id": "16505555555"}],
            "messages": [
                {"id": "wamid.HBgLMTY1MDUwNzY1MjAVAgARGBI5QTNDQTVCM0Q0Q0Q2RTY3RTcA"}
            ],
        },
        from_phone_id=wa.phone_id,
    )
    assert sm == SentMessage(
        _client=wa,
        _callback_options=None,
        _flow_token=None,
        id="wamid.HBgLMTY1MDUwNzY1MjAVAgARGBI5QTNDQTVCM0Q0Q0Q2RTY3RTcA",
        to_user=types.User(wa_id="16505555555", name=None, _client=wa),
        from_phone_id=wa.phone_id,
    )
    assert sm.sender == wa.phone_id
    assert sm.recipient == sm.to_user.wa_id

    assert SentTemplate.from_sent_update(
        client=wa,
        update={
            "messaging_product": "whatsapp",
            "contacts": [{"input": "16505555555", "wa_id": "16505555555"}],
            "messages": [
                {
                    "id": "wamid.HBgLMTY1MDUwNzY1MjAVAgARGBI5QTNDQTVCM0Q0Q0Q2RTY3RTcA",
                    "message_status": "accepted",
                }
            ],
        },
        from_phone_id=wa.phone_id,
    ) == SentTemplate(
        _client=wa,
        _callback_options=None,
        _flow_token=None,
        id="wamid.HBgLMTY1MDUwNzY1MjAVAgARGBI5QTNDQTVCM0Q0Q0Q2RTY3RTcA",
        to_user=types.User(wa_id="16505555555", name=None, _client=wa),
        from_phone_id=wa.phone_id,
        status=SentTemplateStatus.ACCEPTED,
    )


def test_initiated_call():
    c = InitiatedCall.from_sent_update(
        client=wa,
        update={
            "messaging_product": "whatsapp",
            "calls": [{"id": "wacid.fiurefh8e="}],
            "success": True,
        },
        from_phone_id=wa.phone_id,
        to_wa_id="16506666666",
    )
    assert c.caller == wa.phone_id
    assert c.callee == "16506666666"
    assert c == InitiatedCall(
        _client=wa,
        id="wacid.fiurefh8e=",
        to_user=types.User(wa_id="16506666666", name=None, _client=wa),
        from_phone_id=wa.phone_id,
        success=True,
    )


@pytest.fixture
def fake_item_factory():
    return lambda data: {"name": data["name"]}


@pytest.fixture
def wa_result():
    _wa = MagicMock()
    _wa.api._make_request = MagicMock()
    return _wa


@pytest.fixture
def response_data():
    return {
        "data": [{"name": "Alice"}, {"name": "Bob"}],
        "paging": {
            "next": "/next-url",
            "previous": "/prev-url",
            "cursors": {"before": "abc", "after": "xyz"},
        },
    }


@pytest.fixture
def pages():
    return (
        {
            "data": [{"name": "Zed"}],
            "paging": {"next": "/page2", "previous": None, "cursors": {}},
        },
        {
            "data": [{"name": "Yara"}],
            "paging": {"next": "/page3", "previous": "/page1", "cursors": {}},
        },
        {
            "data": [{"name": "Xander"}],
            "paging": {"next": None, "previous": "/page2", "cursors": {}},
        },
    )


def test_result_behavior(wa_result, fake_item_factory, response_data):
    result = Result(wa_result, response_data, fake_item_factory)
    assert len(result) == 2
    assert list(result) == [{"name": "Alice"}, {"name": "Bob"}]
    assert result[0]["name"] == "Alice"
    assert bool(result)


def test_result_properties(wa_result, fake_item_factory, response_data):
    result = Result(wa_result, response_data, fake_item_factory)
    assert result.has_next is True
    assert result.has_previous is True
    assert result.before == "abc"
    assert result.after == "xyz"


def test_result_empty(wa_result, fake_item_factory, response_data):
    result = Result(wa_result, response_data, fake_item_factory)
    empty = result.empty
    assert isinstance(empty, Result)
    assert list(empty) == []
    assert empty.has_next is True  # next_url is preserved
    assert empty.has_previous is False
    assert empty.before == "abc"


def test_result_next(wa_result, fake_item_factory, response_data):
    wa_result.api._make_request.return_value = {
        "data": [{"name": "Charlie"}],
        "paging": {},
    }

    result = Result(wa_result, response_data, fake_item_factory)
    next_result = result.next()
    wa_result.api._make_request.assert_called_once_with(
        method="GET", endpoint="/next-url"
    )
    assert list(next_result) == [{"name": "Charlie"}]


def test_next_result_when_no_next(wa_result, fake_item_factory, response_data):
    response_data["paging"]["next"] = None
    result = Result(wa_result, response_data, fake_item_factory)
    next_result = result.next()
    assert not next_result.has_next
    assert next_result._data == []


def test_previous_result(wa_result, fake_item_factory, response_data):
    wa_result.api._make_request.return_value = {
        "data": [{"name": "Dave"}],
        "paging": {},
    }

    result = Result(wa_result, response_data, fake_item_factory)
    prev_result = result.previous()
    wa_result.api._make_request.assert_called_once_with(
        method="GET", endpoint="/prev-url"
    )
    assert list(prev_result) == [{"name": "Dave"}]


def test_previous_result_when_no_previous(wa_result, fake_item_factory, response_data):
    response_data["paging"]["previous"] = None
    result = Result(wa_result, response_data, fake_item_factory)
    prev_result = result.previous()
    assert not prev_result.has_previous
    assert prev_result._data == []


def test_all_on_first_page(wa_result, fake_item_factory, pages):
    first_page, second_page, third_page = pages
    wa_result.api._make_request.side_effect = [second_page, third_page]
    first_result = Result(wa_result, first_page, fake_item_factory)
    all_results = first_result.all()
    wa_result.api._make_request.assert_has_calls(
        [call(method="GET", endpoint="/page2"), call(method="GET", endpoint="/page3")],
        any_order=False,
    )
    assert all_results == [{"name": "Zed"}, {"name": "Yara"}, {"name": "Xander"}]


def test_all_on_middle_page(wa_result, fake_item_factory, pages):
    first_page, second_page, third_page = pages
    wa_result.api._make_request.side_effect = [first_page, third_page]
    second_result = Result(wa_result, second_page, fake_item_factory)
    all_results = second_result.all()
    wa_result.api._make_request.assert_has_calls(
        [
            call(method="GET", endpoint="/page1"),
            call(method="GET", endpoint="/page3"),
        ],
        any_order=False,
    )
    assert all_results == [{"name": "Zed"}, {"name": "Yara"}, {"name": "Xander"}]


def test_all_on_last_page(wa_result, fake_item_factory, pages):
    first_page, second_page, third_page = pages
    wa_result.api._make_request.side_effect = [second_page, first_page]
    third_result = Result(wa_result, third_page, fake_item_factory)
    all_results = third_result.all()
    wa_result.api._make_request.assert_has_calls(
        [
            call(method="GET", endpoint="/page2"),
            call(method="GET", endpoint="/page1"),
        ],
        any_order=False,
    )
    assert all_results == [{"name": "Zed"}, {"name": "Yara"}, {"name": "Xander"}]


def test_repr(wa_result, fake_item_factory, response_data):
    result = Result(wa_result, response_data, fake_item_factory)
    r = repr(result)
    assert "Result" in r
    assert "has_next=True" in r
    assert "has_previous=True" in r
