import httpx
import pytest

from pywa.api import GraphAPI, _UnpauseTemplateResult
from pywa.errors import WhatsAppError

TOKEN = "xyz-token"
API_VERSION = 21.0


@pytest.fixture
def session():
    return httpx.Client()


@pytest.fixture
def api(session):
    return GraphAPI(token=TOKEN, session=session, api_version=API_VERSION)


@pytest.fixture
def req(api, mocker):
    """Patches GraphAPI._request on the instance and returns the mock."""
    return mocker.patch.object(api, "_request", return_value={"stub": True})


# --- __init__ / dunder / static helpers ---------------------------------


def test_init_sets_auth_header_and_base_url(session):
    GraphAPI(token=TOKEN, session=session, api_version=API_VERSION)
    assert session.headers["Authorization"] == f"Bearer {TOKEN}"
    assert "PyWa/" in session.headers["User-Agent"]
    assert str(session.base_url) == f"https://graph.facebook.com/v{API_VERSION}/"


def test_init_raises_on_reused_session():
    session = httpx.Client(headers={"Authorization": "Bearer already-set"})
    with pytest.raises(ValueError):
        GraphAPI(token=TOKEN, session=session, api_version=API_VERSION)


def test_str_and_repr(api):
    assert str(api) == f"GraphAPI(session={api._session})"
    assert repr(api) == str(api)


def test_filter_none():
    assert GraphAPI._filter_none({"a": 1, "b": None}, c=2, d=None) == {"a": 1, "c": 2}
    assert GraphAPI._filter_none() == {}
    assert GraphAPI._filter_none(None, a=1) == {"a": 1}


def test_join_fields():
    assert GraphAPI._join_fields(("a", "b")) == "a,b"
    assert GraphAPI._join_fields(()) is None
    assert GraphAPI._join_fields(None) is None


# --- _request -------------------------------------------------------------


def _response(status_code: int, json_body: dict) -> httpx.Response:
    return httpx.Response(
        status_code, json=json_body, request=httpx.Request("GET", "https://x.test")
    )


def test_request_success(api, mocker):
    mocker.patch.object(
        api._session, "request", return_value=_response(200, {"ok": True})
    )
    assert api._request(method="GET", endpoint="/foo") == {"ok": True}


def test_request_pops_legacy_log_kwargs(api, mocker):
    request_mock = mocker.patch.object(
        api._session, "request", return_value=_response(200, {"ok": True})
    )
    api._request(method="GET", endpoint="/foo", log_kwargs={"x": 1})
    assert "log_kwargs" not in request_mock.call_args.kwargs


def test_request_error_raises_whatsapp_error(api, mocker):
    mocker.patch.object(
        api._session,
        "request",
        return_value=_response(
            400, {"error": {"message": "bad", "type": "OAuthException", "code": 1}}
        ),
    )
    with pytest.raises(WhatsAppError):
        api._request(method="GET", endpoint="/foo")


@pytest.mark.parametrize(
    "exc",
    [httpx.TimeoutException("t"), httpx.ConnectError("c"), httpx.ProxyError("p")],
)
def test_request_network_errors_reraise(api, mocker, exc):
    mocker.patch.object(api._session, "request", side_effect=exc)
    with pytest.raises(type(exc)):
        api._request(method="GET", endpoint="/foo")


def test_request_generic_request_error_reraises(api, mocker):
    mocker.patch.object(api._session, "request", side_effect=httpx.RequestError("boom"))
    with pytest.raises(httpx.RequestError):
        api._request(method="GET", endpoint="/foo")


# --- OAuth / app subscriptions ---------------------------------------------


def test_get_app_access_token(api, req):
    api.get_app_access_token(client_id=123, client_secret="secret")
    req.assert_called_once_with(
        method="GET",
        endpoint="/oauth/access_token",
        params={
            "grant_type": "client_credentials",
            "client_id": 123,
            "client_secret": "secret",
        },
    )


def test_get_business_access_token(api, req):
    api.get_business_access_token(client_id=123, client_secret="secret", code="c0de")
    req.assert_called_once_with(
        method="GET",
        endpoint="/oauth/access_token",
        params={"client_id": 123, "client_secret": "secret", "code": "c0de"},
    )


def test_set_app_callback_url(api, req):
    api.set_app_callback_url(
        app_id=123,
        access_token="at",
        callback_url="https://cb",
        verify_token="vt",
        fields=("messages", "message_status"),
    )
    req.assert_called_once_with(
        method="POST",
        endpoint="/123/subscriptions",
        params={
            "object": "whatsapp_business_account",
            "callback_url": "https://cb",
            "verify_token": "vt",
            "fields": "messages,message_status",
            "access_token": "at",
        },
    )


def test_set_waba_alternate_callback_url(api, req):
    api.set_waba_alternate_callback_url(
        waba_id="waba1", override_callback_uri="https://cb", verify_token="vt"
    )
    req.assert_called_once_with(
        method="POST",
        endpoint="/waba1/subscribed_apps",
        json={"override_callback_uri": "https://cb", "verify_token": "vt"},
    )


def test_get_waba_subscribed_apps(api, req):
    api.get_waba_subscribed_apps(waba_id="waba1")
    req.assert_called_once_with(method="GET", endpoint="/waba1/subscribed_apps")


def test_delete_waba_alternate_callback_url(api, req):
    api.delete_waba_alternate_callback_url(waba_id="waba1")
    req.assert_called_once_with(method="POST", endpoint="/waba1/subscribed_apps")


def test_set_phone_alternate_callback_url(api, req):
    api.set_phone_alternate_callback_url(
        phone_id="p1", override_callback_uri="https://cb", verify_token="vt"
    )
    req.assert_called_once_with(
        method="POST",
        endpoint="/p1/",
        json={
            "webhook_configuration": {
                "override_callback_uri": "https://cb",
                "verify_token": "vt",
            }
        },
    )


def test_delete_phone_alternate_callback_url(api, req):
    api.delete_phone_alternate_callback_url(phone_id="p1")
    req.assert_called_once_with(
        method="POST",
        endpoint="/p1/",
        json={"webhook_configuration": {"override_callback_uri": ""}},
    )


def test_set_business_public_key(api, req):
    api.set_business_public_key(phone_id="p1", business_public_key="pubkey")
    req.assert_called_once_with(
        method="POST",
        endpoint="/p1/whatsapp_business_encryption",
        json={"business_public_key": "pubkey"},
    )


# --- Media -------------------------------------------------------------


def test_upload_media_without_ttl(api, req):
    api.upload_media(
        phone_id="p1", media=b"bytes", mime_type="image/png", filename="a.png"
    )
    req.assert_called_once_with(
        method="POST",
        endpoint="/p1/media",
        files={
            "file": ("a.png", b"bytes", "image/png"),
            "messaging_product": (None, "whatsapp"),
            "type": (None, "image/png"),
        },
    )


def test_upload_media_with_ttl(api, req):
    api.upload_media(
        phone_id="p1",
        media=b"bytes",
        mime_type="image/png",
        filename="a.png",
        ttl_minutes=30,
    )
    _, kwargs = req.call_args
    assert kwargs["files"]["ttl_minutes"] == (None, "30")


def test_get_media_url(api, req):
    api.get_media_url(media_id="m1")
    req.assert_called_once_with(method="GET", endpoint="/m1")


def test_stream_media_bytes(api, mocker):
    stream_mock = mocker.patch.object(api._session, "stream")
    api.stream_media_bytes(media_url="https://media/1", timeout=5)
    stream_mock.assert_called_once_with(
        method="GET",
        url="https://media/1",
        headers=api._session.headers.copy(),
        follow_redirects=True,
        timeout=5,
    )


def test_delete_media(api, req):
    api.delete_media(media_id="m1", phone_number_id="p1")
    req.assert_called_once_with(
        method="DELETE", endpoint="/m1", params={"phone_number_id": "p1"}
    )


def test_delete_media_without_phone_number_id(api, req):
    api.delete_media(media_id="m1")
    req.assert_called_once_with(method="DELETE", endpoint="/m1", params={})


def test_send_raw_request(api, req):
    api.send_raw_request("PUT", "/custom", json={"a": 1})
    req.assert_called_once_with(method="PUT", endpoint="/custom", json={"a": 1})


# --- Messages ------------------------------------------------------------


def test_send_message_requires_to_or_recipient(api, req):
    with pytest.raises(ValueError):
        api.send_message(
            sender="p1",
            to=None,
            recipient=None,
            recipient_type="individual",
            typ="text",
            msg={"body": "hi"},
        )
    req.assert_not_called()


def test_send_message(api, req):
    api.send_message(
        sender="p1",
        to="123",
        recipient=None,
        recipient_type="individual",
        typ="text",
        msg={"body": "hi"},
        reply_to_message_id="wamid.1",
        biz_opaque_callback_data="tracker",
        recipient_identity_key_hash="hash",
    )
    req.assert_called_once_with(
        method="POST",
        endpoint="/p1/messages",
        json={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "type": "text",
            "to": "123",
            "context": {"message_id": "wamid.1"},
            "biz_opaque_callback_data": "tracker",
            "recipient_identity_key_hash": "hash",
            "text": {"body": "hi"},
        },
    )


def test_send_marketing_message_requires_to_or_recipient(api, req):
    with pytest.raises(ValueError):
        api.send_marketing_message(
            sender="p1",
            to=None,
            recipient=None,
            recipient_type="individual",
            template={"name": "t"},
        )
    req.assert_not_called()


def test_send_marketing_message(api, req):
    api.send_marketing_message(
        sender="p1",
        to="123",
        recipient=None,
        recipient_type="individual",
        template={"name": "t"},
        reply_to_message_id="wamid.1",
        message_activity_sharing=True,
        biz_opaque_callback_data="tracker",
        recipient_identity_key_hash="hash",
    )
    req.assert_called_once_with(
        method="POST",
        endpoint="/p1/marketing_messages",
        json={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": "123",
            "type": "template",
            "template": {"name": "t"},
            "context": {"message_id": "wamid.1"},
            "message_activity_sharing": True,
            "biz_opaque_callback_data": "tracker",
            "recipient_identity_key_hash": "hash",
        },
    )


def test_mark_message_as_read(api, req):
    api.mark_message_as_read(phone_id="p1", message_id="wamid.1")
    req.assert_called_once_with(
        method="POST",
        endpoint="/p1/messages",
        json={
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": "wamid.1",
        },
    )


def test_set_indicator(api, req):
    api.set_indicator(phone_id="p1", message_id="wamid.1", typ="text")
    req.assert_called_once_with(
        method="POST",
        endpoint="/p1/messages",
        json={
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": "wamid.1",
            "typing_indicator": {"type": "text"},
        },
    )


# --- Phone numbers ---------------------------------------------------------


def test_create_phone_number(api, req):
    api.create_phone_number(
        waba_id="w1", country_code="1", phone_number="5551234", verified_name="Biz"
    )
    req.assert_called_once_with(
        method="POST",
        endpoint="w1/phone_numbers",
        json={
            "country_code": "1",
            "phone_number": "5551234",
            "verified_name": "Biz",
        },
    )


def test_request_verification_code(api, req):
    api.request_verification_code(phone_id="p1", code_method="SMS", language="en")
    req.assert_called_once_with(
        method="POST",
        endpoint="/p1/request_code",
        params={"code_method": "SMS", "language": "en"},
    )


def test_verify_phone_number(api, req):
    api.verify_phone_number(phone_id="p1", code="123456")
    req.assert_called_once_with(
        method="POST", endpoint="/p1/verify_code", params={"code": "123456"}
    )


def test_register_phone_number(api, req):
    api.register_phone_number(
        phone_id="p1", pin="123456", data_localization_region="US"
    )
    req.assert_called_once_with(
        method="POST",
        endpoint="/p1/register",
        json={
            "messaging_product": "whatsapp",
            "pin": "123456",
            "data_localization_region": "US",
        },
    )


def test_deregister_phone_number(api, req):
    api.deregister_phone_number(phone_id="p1")
    req.assert_called_once_with(method="POST", endpoint="/p1/deregister")


def test_get_shared_wabas(api, req):
    api.get_shared_wabas(
        business_portfolio_id="b1", fields=("id", "name"), pagination={"limit": 5}
    )
    req.assert_called_once_with(
        method="GET",
        endpoint="/b1/client_whatsapp_business_accounts",
        params={"limit": 5, "fields": "id,name"},
    )


def test_get_owned_wabas(api, req):
    api.get_owned_wabas(
        business_portfolio_id="b1", fields=None, pagination={"limit": 5}
    )
    req.assert_called_once_with(
        method="GET",
        endpoint="/b1/owned_whatsapp_business_accounts",
        params={"limit": 5},
    )


def test_get_waba_info(api, req):
    api.get_waba_info(waba_id="w1", fields=("id",))
    req.assert_called_once_with(method="GET", endpoint="/w1", params={"fields": "id"})


def test_update_waba_settings(api, req):
    api.update_waba_settings(waba_id="w1", settings={"a": 1})
    req.assert_called_once_with(method="POST", endpoint="/w1", json={"a": 1})


def test_get_business_phone_number(api, req):
    api.get_business_phone_number(phone_id="p1", fields=("id",))
    req.assert_called_once_with(method="GET", endpoint="/p1", params={"fields": "id"})


def test_get_business_phone_numbers(api, req):
    api.get_business_phone_numbers(waba_id="w1", fields=("id",), pagination={})
    req.assert_called_once_with(
        method="GET", endpoint="/w1/phone_numbers", params={"fields": "id"}
    )


def test_get_business_phone_number_settings(api, req):
    api.get_business_phone_number_settings(
        phone_id="p1", fields=("sip",), include_sip_credentials=True
    )
    req.assert_called_once_with(
        method="GET",
        endpoint="/p1/settings",
        params={"fields": "sip", "include_sip_credentials": True},
    )


def test_update_business_phone_number_settings(api, req):
    api.update_business_phone_number_settings(phone_id="p1", settings={"a": 1})
    req.assert_called_once_with(method="POST", endpoint="/p1/settings", json={"a": 1})


def test_update_conversational_automation(api, req):
    api.update_conversational_automation(
        phone_id="p1", prompts=["hi"], commands=[{"command_name": "help"}]
    )
    req.assert_called_once_with(
        method="POST",
        endpoint="/p1/conversational_automation",
        json={"prompts": ["hi"], "commands": [{"command_name": "help"}]},
    )


def test_update_display_name(api, req):
    api.update_display_name(phone_id="p1", new_display_name="New Biz")
    req.assert_called_once_with(
        method="POST",
        endpoint="/p1",
        json={"new_display_name": "New Biz", "messaging_product": "whatsapp"},
    )


def test_get_business_profile(api, req):
    api.get_business_profile(phone_id="p1", fields=("about",))
    req.assert_called_once_with(
        method="GET",
        endpoint="/p1/whatsapp_business_profile",
        params={"fields": "about"},
    )


def test_update_business_profile(api, req):
    api.update_business_profile(phone_id="p1", data={"about": "hi"})
    req.assert_called_once_with(
        method="POST",
        endpoint="/p1/whatsapp_business_profile",
        json={"about": "hi", "messaging_product": "whatsapp"},
    )


def test_get_commerce_settings(api, req):
    api.get_commerce_settings(phone_id="p1", fields=("is_cart_enabled",))
    req.assert_called_once_with(
        method="GET",
        endpoint="/p1/whatsapp_commerce_settings",
        params={"fields": "is_cart_enabled"},
    )


def test_update_commerce_settings(api, req):
    api.update_commerce_settings(phone_id="p1", data={"is_cart_enabled": True})
    req.assert_called_once_with(
        method="POST",
        endpoint="/p1/whatsapp_commerce_settings",
        params={"is_cart_enabled": True},
    )


# --- Templates -------------------------------------------------------------


def test_create_template(api, req):
    api.create_template(waba_id="w1", template={"name": "t"})
    req.assert_called_once_with(
        method="POST",
        endpoint="/w1/message_templates",
        json={"name": "t"},
        headers={"Content-Type": "application/json"},
    )


def test_get_template(api, req):
    api.get_template(template_id="t1", fields=("status",))
    req.assert_called_once_with(
        method="GET", endpoint="/t1", params={"fields": "status"}
    )


def test_get_templates(api, req):
    api.get_templates(
        waba_id="w1",
        fields=("id",),
        filters={"status": "APPROVED"},
        summary_fields=("total_count",),
        pagination={"limit": 5},
    )
    req.assert_called_once_with(
        method="GET",
        endpoint="/w1/message_templates",
        params={
            "limit": 5,
            "fields": "id",
            "summary": "total_count",
            "status": "APPROVED",
        },
    )


def test_update_template(api, req):
    api.update_template(template_id="t1", template={"components": []})
    req.assert_called_once_with(
        method="POST",
        endpoint="/t1",
        json={"components": []},
        headers={"Content-Type": "application/json"},
    )


def test_delete_template(api, req):
    api.delete_template(waba_id="w1", template_name="t_name", template_id="t1")
    req.assert_called_once_with(
        method="DELETE",
        endpoint="/w1/message_templates",
        params={"name": "t_name", "hsm_id": "t1"},
    )


def test_archive_templates(api, req):
    api.archive_templates(waba_id="w1", template_ids=["t1", "t2"])
    req.assert_called_once_with(
        method="POST",
        endpoint="https://api.facebook.com/w1/message_templates/archive",
        json={"hsm_ids": "t1,t2"},
    )


def test_unarchive_templates(api, req):
    api.unarchive_templates(waba_id="w1", template_ids=["t1", "t2"])
    req.assert_called_once_with(
        method="POST",
        endpoint="https://api.facebook.com/w1/message_templates/unarchive",
        json={"hsm_ids": "t1,t2"},
    )


def test_compare_templates(api, req):
    api.compare_templates(
        template_id="t1",
        template_ids=["t2", "t3"],
        start="2024-01-01",
        end="2024-02-01",
    )
    req.assert_called_once_with(
        method="GET",
        endpoint="/t1/compare",
        params={"template_ids": "t2,t3", "start": "2024-01-01", "end": "2024-02-01"},
    )


def test_migrate_templates(api, req):
    api.migrate_templates(dest_waba_id="w2", source_waba_id="w1", page_number=2)
    req.assert_called_once_with(
        method="POST",
        endpoint="/w2/migrate_message_templates",
        params={"source_waba_id": "w1", "page_number": 2},
    )


def test_unpause_template(api, req):
    result = api.unpause_template(template_id="t1")
    req.assert_called_once_with(method="POST", endpoint="/t1/unpause")
    assert result == {"stub": True}


def test_unpause_template_return_type_cast():
    assert _UnpauseTemplateResult.__annotations__.keys() == {"success", "reason"}


def test_upsert_message_templates(api, req):
    api.upsert_message_templates(waba_id="w1", template={"name": "t"})
    req.assert_called_once_with(
        method="POST", endpoint="/w1/upsert_message_templates", json={"name": "t"}
    )


# --- Flows -------------------------------------------------------------


def test_create_flow(api, req):
    api.create_flow(
        waba_id="w1",
        name="Flow1",
        categories=["OTHER"],
        clone_flow_id=None,
        endpoint_uri="https://ep",
        flow_json=None,
        publish=False,
    )
    req.assert_called_once_with(
        method="POST",
        endpoint="/w1/flows",
        json={
            "name": "Flow1",
            "categories": ["OTHER"],
            "endpoint_uri": "https://ep",
            "publish": False,
        },
    )


def test_update_flow_metadata(api, req):
    api.update_flow_metadata(
        flow_id="f1",
        name="New",
        categories=["OTHER"],
        endpoint_uri=None,
        application_id=None,
    )
    req.assert_called_once_with(
        method="POST",
        endpoint="/f1",
        json={"name": "New", "categories": ["OTHER"]},
    )


def test_update_flow_json(api, req):
    api.update_flow_json(flow_id="f1", flow_json=b"{}")
    req.assert_called_once_with(
        method="POST",
        endpoint="/f1/assets",
        files={
            "file": ("flow.json", b"{}", "application/json"),
            "name": (None, "flow.json"),
            "asset_type": (None, "FLOW_JSON"),
            "messaging_product": (None, "whatsapp"),
        },
    )


def test_publish_flow(api, req):
    api.publish_flow(flow_id="f1")
    req.assert_called_once_with(method="POST", endpoint="/f1/publish")


def test_delete_flow(api, req):
    api.delete_flow(flow_id="f1")
    req.assert_called_once_with(method="DELETE", endpoint="/f1")


def test_deprecate_flow(api, req):
    api.deprecate_flow(flow_id="f1")
    req.assert_called_once_with(method="POST", endpoint="/f1/deprecate")


def test_get_flow(api, req):
    api.get_flow(flow_id="f1", fields=("status",))
    req.assert_called_once_with(
        method="GET", endpoint="/f1", params={"fields": "status"}
    )


def test_get_flows(api, req):
    api.get_flows(waba_id="w1", fields=("status",), pagination={})
    req.assert_called_once_with(
        method="GET", endpoint="/w1/flows", params={"fields": "status"}
    )


def test_get_flow_assets(api, req):
    api.get_flow_assets(flow_id="f1", pagination={"limit": 5})
    req.assert_called_once_with(
        method="GET",
        endpoint="/f1/assets?fields=name,asset_type,download_url",
        params={"limit": 5},
    )


def test_migrate_flows(api, req):
    api.migrate_flows(
        dest_waba_id="w2", source_waba_id="w1", source_flow_names=["a", "b"]
    )
    req.assert_called_once_with(
        method="POST",
        endpoint="/w2/migrate_flows",
        params={"source_waba_id": "w1", "source_flow_names": "a,b"},
    )


# --- QR codes -------------------------------------------------------------


def test_create_qr_code(api, req):
    api.create_qr_code(phone_id="p1", prefilled_message="hi", generate_qr_image="PNG")
    req.assert_called_once_with(
        method="POST",
        endpoint="/p1/message_qrdls",
        json={"prefilled_message": "hi", "generate_qr_image": "PNG"},
    )


def test_get_qr_code(api, req):
    api.get_qr_code(phone_id="p1", code="c1", fields=("code",))
    req.assert_called_once_with(
        method="GET",
        endpoint="/p1/message_qrdls/c1",
        params={"fields": "code"},
    )


def test_get_qr_codes(api, req):
    api.get_qr_codes(phone_id="p1", fields=("code",), pagination={})
    req.assert_called_once_with(
        method="GET", endpoint="/p1/message_qrdls", params={"fields": "code"}
    )


def test_update_qr_code(api, req):
    api.update_qr_code(phone_id="p1", code="c1", prefilled_message="hi")
    req.assert_called_once_with(
        method="POST",
        endpoint="/p1/message_qrdls",
        json={"code": "c1", "prefilled_message": "hi"},
    )


def test_delete_qr_code(api, req):
    api.delete_qr_code(phone_id="p1", code="c1")
    req.assert_called_once_with(method="DELETE", endpoint="/p1/message_qrdls/c1")


# --- Block users -------------------------------------------------------------


def test_block_users(api, req):
    api.block_users(phone_id="p1", users=["1", "2"], user_ids=["u1"])
    req.assert_called_once_with(
        method="POST",
        endpoint="/p1/block_users",
        json={
            "messaging_product": "whatsapp",
            "block_users": [{"user": "1"}, {"user": "2"}, {"user_id": "u1"}],
        },
    )


def test_unblock_users(api, req):
    api.unblock_users(phone_id="p1", users=["1"], user_ids=["u1", "u2"])
    req.assert_called_once_with(
        method="DELETE",
        endpoint="/p1/block_users",
        json={
            "messaging_product": "whatsapp",
            "block_users": [{"user": "1"}, {"user_id": "u1"}, {"user_id": "u2"}],
        },
    )


def test_get_blocked_users(api, req):
    api.get_blocked_users(phone_id="p1", pagination={"limit": 5})
    req.assert_called_once_with(
        method="GET", endpoint="/p1/block_users", params={"limit": 5}
    )


# --- Resumable uploads -------------------------------------------------------------


def test_create_upload_session(api, req):
    api.create_upload_session(
        app_id="a1", file_name="f.png", file_length=10, file_type="image/png"
    )
    req.assert_called_once_with(
        method="POST",
        endpoint="/a1/uploads?file_name=f.png&file_length=10&file_type=image/png",
    )


def test_upload_file_with_content_length(api, req):
    api.upload_file(
        upload_session_id="s1", file=b"data", file_offset=0, content_length=4
    )
    req.assert_called_once_with(
        method="POST",
        endpoint="/s1",
        headers={"file_offset": "0", "Content-Length": "4"},
        content=b"data",
    )


def test_upload_file_without_content_length(api, req):
    api.upload_file(
        upload_session_id="s1", file=b"data", file_offset=4, content_length=None
    )
    req.assert_called_once_with(
        method="POST",
        endpoint="/s1",
        headers={"file_offset": "4"},
        content=b"data",
    )


def test_get_upload_session(api, req):
    api.get_upload_session(upload_session_id="s1")
    req.assert_called_once_with(method="GET", endpoint="/s1")


# --- Calls -------------------------------------------------------------


def test_get_call_permissions_requires_user_wa_id_or_recipient(api, req):
    with pytest.raises(ValueError):
        api.get_call_permissions(phone_id="p1", user_wa_id=None, recipient=None)
    req.assert_not_called()


def test_get_call_permissions(api, req):
    api.get_call_permissions(phone_id="p1", user_wa_id="123", recipient=None)
    req.assert_called_once_with(
        method="GET",
        endpoint="/p1/call_permissions",
        params={"user_wa_id": "123"},
    )


def test_initiate_call_requires_to_or_recipient(api, req):
    with pytest.raises(ValueError):
        api.initiate_call(
            phone_id="p1",
            to=None,
            recipient=None,
            session={"sdp": "x"},
            biz_opaque_callback_data=None,
        )
    req.assert_not_called()


def test_initiate_call(api, req):
    api.initiate_call(
        phone_id="p1",
        to="123",
        recipient=None,
        session={"sdp": "x"},
        biz_opaque_callback_data="tracker",
    )
    req.assert_called_once_with(
        method="POST",
        endpoint="p1/calls",
        json={
            "messaging_product": "whatsapp",
            "to": "123",
            "action": "connect",
            "session": {"sdp": "x"},
            "biz_opaque_callback_data": "tracker",
        },
    )


def test_pre_accept_call(api, req):
    api.pre_accept_call(phone_id="p1", call_id="c1", session={"sdp": "x"})
    req.assert_called_once_with(
        method="POST",
        endpoint="p1/calls",
        json={
            "messaging_product": "whatsapp",
            "call_id": "c1",
            "action": "pre_accept",
            "session": {"sdp": "x"},
        },
    )


def test_accept_call(api, req):
    api.accept_call(
        phone_id="p1",
        call_id="c1",
        session={"sdp": "x"},
        biz_opaque_callback_data="tracker",
    )
    req.assert_called_once_with(
        method="POST",
        endpoint="p1/calls",
        json={
            "messaging_product": "whatsapp",
            "call_id": "c1",
            "action": "accept",
            "session": {"sdp": "x"},
            "biz_opaque_callback_data": "tracker",
        },
    )


def test_reject_call(api, req):
    api.reject_call(phone_id="p1", call_id="c1")
    req.assert_called_once_with(
        method="POST",
        endpoint="p1/calls",
        json={
            "messaging_product": "whatsapp",
            "call_id": "c1",
            "action": "reject",
        },
    )


def test_terminate_call(api, req):
    api.terminate_call(phone_id="p1", call_id="c1")
    req.assert_called_once_with(
        method="POST",
        endpoint="p1/calls",
        json={
            "messaging_product": "whatsapp",
            "call_id": "c1",
            "action": "terminate",
        },
    )


# --- Groups -------------------------------------------------------------


def test_create_group(api, req):
    api.create_group(
        phone_id="p1",
        subject="Subj",
        description="Desc",
        join_approval_mode="admin_approval",
    )
    req.assert_called_once_with(
        method="POST",
        endpoint="/p1/groups",
        json={
            "messaging_product": "whatsapp",
            "subject": "Subj",
            "description": "Desc",
            "join_approval_mode": "admin_approval",
        },
    )


def test_update_group_info_with_picture(api, req):
    api.update_group_info(
        group_id="g1",
        subject="Subj",
        description="Desc",
        profile_picture_file=b"imgbytes",
    )
    req.assert_called_once_with(
        method="POST",
        endpoint="/g1",
        files={
            "messaging_product": (None, "whatsapp"),
            "subject": (None, "Subj"),
            "description": (None, "Desc"),
            "profile_picture_file": ("profile.jpg", b"imgbytes", "image/jpeg"),
        },
    )


def test_update_group_info_without_optional_fields(api, req):
    api.update_group_info(
        group_id="g1", subject=None, description=None, profile_picture_file=None
    )
    req.assert_called_once_with(
        method="POST",
        endpoint="/g1",
        files={"messaging_product": (None, "whatsapp")},
    )


def test_get_group_join_requests(api, req):
    api.get_group_join_requests(group_id="g1", pagination={"limit": 5})
    req.assert_called_once_with(
        method="GET", endpoint="/g1/join_requests", params={"limit": 5}
    )


def test_approve_group_join_requests(api, req):
    api.approve_group_join_requests(group_id="g1", request_ids=["r1", "r2"])
    req.assert_called_once_with(
        method="POST",
        endpoint="/g1/join_requests",
        json={"messaging_product": "whatsapp", "join_requests": ["r1", "r2"]},
    )


def test_reject_group_join_requests(api, req):
    api.reject_group_join_requests(group_id="g1", request_ids=["r1"])
    req.assert_called_once_with(
        method="DELETE",
        endpoint="/g1/join_requests",
        json={"messaging_product": "whatsapp", "join_requests": ["r1"]},
    )


def test_get_group_invite_link(api, req):
    api.get_group_invite_link(group_id="g1")
    req.assert_called_once_with(method="GET", endpoint="/g1/invite_link")


def test_reset_group_invite_link(api, req):
    api.reset_group_invite_link(group_id="g1")
    req.assert_called_once_with(
        method="POST",
        endpoint="/g1/invite_link",
        json={"messaging_product": "whatsapp"},
    )


def test_delete_group(api, req):
    api.delete_group(group_id="g1")
    req.assert_called_once_with(method="DELETE", endpoint="/g1")


def test_remove_group_participants(api, req):
    api.remove_group_participants(group_id="g1", users=["1"], user_ids=["u1"])
    req.assert_called_once_with(
        method="DELETE",
        endpoint="/g1/participants",
        json={
            "messaging_product": "whatsapp",
            "participants": [{"user": "1"}, {"user_id": "u1"}],
        },
    )


def test_get_group_info(api, req):
    api.get_group_info(group_id="g1", fields=("subject",))
    req.assert_called_once_with(
        method="GET", endpoint="/g1", params={"fields": "subject"}
    )


def test_get_active_groups(api, req):
    api.get_active_groups(phone_id="p1", fields=("subject",), pagination={})
    req.assert_called_once_with(
        method="GET", endpoint="/p1/groups", params={"fields": "subject"}
    )


# --- Usernames -------------------------------------------------------------


def test_set_username(api, req):
    api.set_username(phone_id="p1", username="biz_user", transfer_action="MOVE")
    req.assert_called_once_with(
        method="POST",
        endpoint="/p1/username",
        json={"username": "biz_user", "transfer_action": "MOVE"},
    )


def test_get_current_username(api, req):
    api.get_current_username(phone_id="p1")
    req.assert_called_once_with(method="GET", endpoint="/p1/username")


def test_get_reserved_usernames(api, req):
    api.get_reserved_usernames(phone_id="p1")
    req.assert_called_once_with(method="GET", endpoint="/p1/username_suggestions")


def test_delete_username(api, req):
    api.delete_username(phone_id="p1")
    req.assert_called_once_with(method="DELETE", endpoint="/p1/username")


# --- Signups -------------------------------------------------------------


def test_create_signup(api, req):
    api.create_signup(
        waba_id="w1",
        signup_message="hi",
        confirmation_message=None,
        privacy_policy_url="https://pp",
        website_url=None,
        promo_code=None,
        display_name="Biz",
        policy=None,
    )
    req.assert_called_once_with(
        method="POST",
        endpoint="/w1/signups",
        json={
            "signup_message": "hi",
            "privacy_policy_url": "https://pp",
            "display_name": "Biz",
        },
    )


def test_get_signups(api, req):
    api.get_signups(waba_id="w1", fields=("status",), pagination={})
    req.assert_called_once_with(
        method="GET", endpoint="/w1/signups", params={"fields": "status"}
    )


def test_get_signup(api, req):
    api.get_signup(signup_id="s1")
    req.assert_called_once_with(method="GET", endpoint="/signups/s1")


def test_update_signup(api, req):
    api.update_signup(
        signup_id="s1",
        status="APPROVED",
        signup_message=None,
        confirmation_message=None,
        website_url=None,
        promo_code=None,
        display_name=None,
    )
    req.assert_called_once_with(
        method="POST",
        endpoint="/signups/s1",
        json={"status": "APPROVED"},
    )
