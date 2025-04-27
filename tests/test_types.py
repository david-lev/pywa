import datetime
from pywa import types, WhatsApp
from pywa.types.flows import FlowDetails
from pywa.types.sent_message import SentMessage, SentTemplate, SentTemplateStatus

wa = WhatsApp(token="token")


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
        whatsapp_business_account=types.flows.WhatsAppBusinessAccount(
            id="124578",
            name="Test WhatsApp Business Account",
            timezone_id="1",
            message_template_namespace="1acaxyzfec",
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
    assert SentMessage.from_sent_update(
        client=wa,
        update={
            "messaging_product": "whatsapp",
            "contacts": [{"input": "16505555555", "wa_id": "16505555555"}],
            "messages": [
                {"id": "wamid.HBgLMTY1MDUwNzY1MjAVAgARGBI5QTNDQTVCM0Q0Q0Q2RTY3RTcA"}
            ],
        },
        from_phone_id=wa.phone_id,
    ) == SentMessage(
        _client=wa,
        _callback_options=None,
        _flow_token=None,
        id="wamid.HBgLMTY1MDUwNzY1MjAVAgARGBI5QTNDQTVCM0Q0Q0Q2RTY3RTcA",
        to_user=types.User(wa_id="16505555555", name=None, _client=wa),
        from_phone_id=wa.phone_id,
    )

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
