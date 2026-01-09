import asyncio
import inspect

import pytest

from pywa import WhatsApp as WhatsAppSync
from pywa.api import GraphAPI as GraphAPISync
from pywa.handlers import _HandlerDecorators
from pywa.listeners import _Listeners as ListenersSync
from pywa.server import Server as ServerSync
from pywa.types import (
    CallbackButton as CallbackButtonSync,
)
from pywa.types import (
    CallbackSelection as CallbackSelectionSync,
)
from pywa.types import (
    CallConnect as CallConnectSync,
)
from pywa.types import (
    CallPermissionUpdate as CallPermissionUpdateSync,
)
from pywa.types import (
    CallStatus as CallStatusSync,
)
from pywa.types import (
    CallTerminate as CallTerminateSync,
)
from pywa.types import (
    ChatOpened as ChatOpenedSync,
)
from pywa.types import (
    FlowCompletion as FlowCompletionSync,
)
from pywa.types import (
    FlowRequest as FlowRequestSync,
)
from pywa.types import (
    FlowResponse as FlowResponseSync,
)
from pywa.types import (
    IdentityChange as IdentityChangeSync,
)
from pywa.types import (
    MediaURL as MediaUrlResponseSync,
)
from pywa.types import (
    Message as MessageSync,
)
from pywa.types import (
    MessageStatus as MessageStatusSync,
)
from pywa.types import (
    PhoneNumberChange as PhoneNumberChangeSync,
)
from pywa.types import (
    QRCode as QRCodeSync,
)
from pywa.types import (
    Result as ResultSync,
)
from pywa.types import (
    TemplateCategoryUpdate as TemplateCategoryUpdateSync,
)
from pywa.types import (
    TemplateComponentsUpdate as TemplateComponentsUpdateSync,
)
from pywa.types import (
    TemplateQualityUpdate as TemplateQualityUpdateSync,
)
from pywa.types import (
    TemplateStatusUpdate as TemplateStatusUpdateSync,
)
from pywa.types import (
    User as UserSync,
)
from pywa.types import (
    UserMarketingPreferences as UserMarketingPreferencesSync,
)
from pywa.types.base_update import BaseUpdate
from pywa.types.flows import FlowDetails as FlowDetailsSync
from pywa.types.media import ArrivedMedia
from pywa.types.media import Media as MediaSync
from pywa.types.sent_update import (
    InitiatedCall as InitiatedCallSync,
)
from pywa.types.sent_update import (
    SentMessage as SentMessageSync,
)
from pywa.types.sent_update import (
    SentTemplate as SentTemplateSync,
)
from pywa.types.templates import (
    CreatedTemplate as CreatedTemplateSync,
)
from pywa.types.templates import (
    CreatedTemplates as CreatedTemplatesSync,
)
from pywa.types.templates import (
    TemplateDetails as TemplateDetailsSync,
)
from pywa.types.templates import (
    TemplatesResult as TemplatesResultSync,
)
from pywa.types.templates import (
    UpdatedTemplate as UpdatedTemplateSync,
)
from pywa_async import WhatsApp as WhatsAppAsync
from pywa_async.api import GraphAPIAsync
from pywa_async.types import (
    CallbackButton as CallbackButtonAsync,
)
from pywa_async.types import (
    CallbackSelection as CallbackSelectionAsync,
)
from pywa_async.types import (
    CallConnect as CallConnectAsync,
)
from pywa_async.types import (
    CallPermissionUpdate as CallPermissionUpdateAsync,
)
from pywa_async.types import (
    CallStatus as CallStatusAsync,
)
from pywa_async.types import (
    CallTerminate as CallTerminateAsync,
)
from pywa_async.types import (
    ChatOpened as ChatOpenedAsync,
)
from pywa_async.types import (
    FlowCompletion as FlowCompletionAsync,
)
from pywa_async.types import (
    FlowRequest as FlowRequestAsync,
)
from pywa_async.types import (
    FlowResponse as FlowResponseAsync,
)
from pywa_async.types import (
    IdentityChange as IdentityChangeAsync,
)
from pywa_async.types import (
    MediaURL as MediaUrlResponseAsync,
)
from pywa_async.types import (
    Message as MessageAsync,
)
from pywa_async.types import (
    MessageStatus as MessageStatusAsync,
)
from pywa_async.types import (
    PhoneNumberChange as PhoneNumberChangeAsync,
)
from pywa_async.types import (
    QRCode as QRCodeAsync,
)
from pywa_async.types import (
    Result as ResultAsync,
)
from pywa_async.types import (
    TemplateCategoryUpdate as TemplateCategoryUpdateAsync,
)
from pywa_async.types import (
    TemplateComponentsUpdate as TemplateComponentsUpdateAsync,
)
from pywa_async.types import (
    TemplateQualityUpdate as TemplateQualityUpdateAsync,
)
from pywa_async.types import (
    TemplateStatusUpdate as TemplateStatusUpdateAsync,
)
from pywa_async.types import (
    User as UserAsync,
)
from pywa_async.types import (
    UserMarketingPreferences as UserMarketingPreferencesAsync,
)
from pywa_async.types.flows import FlowDetails as FlowDetailsAsync
from pywa_async.types.media import Media as MediaAsync
from pywa_async.types.sent_update import (
    InitiatedCall as InitiatedCallAsync,
)
from pywa_async.types.sent_update import (
    SentMessage as SentMessageAsync,
)
from pywa_async.types.sent_update import (
    SentTemplate as SentTemplateAsync,
)
from pywa_async.types.templates import (
    CreatedTemplate as CreatedTemplateAsync,
)
from pywa_async.types.templates import (
    CreatedTemplates as CreatedTemplatesAsync,
)
from pywa_async.types.templates import (
    TemplateDetails as TemplateDetailsAsync,
)
from pywa_async.types.templates import (
    TemplatesResult as TemplatesResultAsync,
)
from pywa_async.types.templates import (
    UpdatedTemplate as UpdatedTemplateAsync,
)


@pytest.fixture(scope="session")
def overrides() -> list[tuple[type, type]]:
    return [
        (WhatsAppSync, WhatsAppAsync),
        (MessageSync, MessageAsync),
        (CallbackButtonSync, CallbackButtonAsync),
        (CallbackSelectionSync, CallbackSelectionAsync),
        (MessageStatusSync, MessageStatusAsync),
        (ChatOpenedSync, ChatOpenedAsync),
        (PhoneNumberChangeSync, PhoneNumberChangeAsync),
        (IdentityChangeSync, IdentityChangeAsync),
        (FlowCompletionSync, FlowCompletionAsync),
        (TemplateStatusUpdateSync, TemplateStatusUpdateAsync),
        (TemplateCategoryUpdateSync, TemplateCategoryUpdateAsync),
        (TemplateQualityUpdateSync, TemplateQualityUpdateAsync),
        (TemplateComponentsUpdateSync, TemplateComponentsUpdateAsync),
        (UserMarketingPreferencesSync, UserMarketingPreferencesAsync),
        (CallConnectSync, CallConnectAsync),
        (CallTerminateSync, CallTerminateAsync),
        (CallStatusSync, CallStatusAsync),
        (CallPermissionUpdateSync, CallPermissionUpdateAsync),
        (FlowRequestSync, FlowRequestAsync),
        (FlowResponseSync, FlowResponseAsync),
        (FlowDetailsSync, FlowDetailsAsync),
        (MediaUrlResponseSync, MediaUrlResponseAsync),
        (MediaSync, MediaAsync),
        (SentMessageSync, SentMessageAsync),
        (SentTemplateSync, SentTemplateAsync),
        (InitiatedCallSync, InitiatedCallAsync),
        (GraphAPISync, GraphAPIAsync),
        (UserSync, UserAsync),
        (ResultSync, ResultAsync),
        (TemplateDetailsSync, TemplateDetailsAsync),
        (TemplatesResultSync, TemplatesResultAsync),
        (CreatedTemplateSync, CreatedTemplateAsync),
        (CreatedTemplatesSync, CreatedTemplatesAsync),
        (UpdatedTemplateSync, UpdatedTemplateAsync),
        (QRCodeSync, QRCodeAsync),
    ]


def get_obj_methods_names(obj):
    return {m for m in dir(obj) if callable(getattr(obj, m)) and not m.startswith("__")}


def test_all_methods_are_overwritten_in_async(overrides):
    skip_methods = [
        m.__name__
        for m in {
            WhatsAppSync.stream_media,
            WhatsAppSync.add_handlers,
            WhatsAppSync.remove_handlers,
            WhatsAppSync.remove_callbacks,
            WhatsAppSync.add_flow_request_handler,
            WhatsAppSync.stop_listening,
            WhatsAppSync.get_flow_request_handler,
            WhatsAppSync.load_handlers_modules,
            WhatsAppSync._check_for_async_callback,
            WhatsAppSync._check_for_async_filters,
            WhatsAppSync._flow_req_cls,
            GraphAPISync.stream_media_bytes,
            ServerSync._check_and_prepare_update,
            ServerSync._after_handling_update,
            ServerSync._delayed_register_callback_url,
            ServerSync._register_callback_url,
            ServerSync._get_handler_type,
            ServerSync._register_flow_endpoint_callback,
            _HandlerDecorators.on_message,
            _HandlerDecorators.on_callback_button,
            _HandlerDecorators.on_callback_selection,
            _HandlerDecorators.on_message_status,
            _HandlerDecorators.on_chat_opened,
            _HandlerDecorators.on_phone_number_change,
            _HandlerDecorators.on_identity_change,
            _HandlerDecorators.on_flow_completion,
            _HandlerDecorators.on_flow_request,
            _HandlerDecorators.on_template_status_update,
            _HandlerDecorators.on_template_category_update,
            _HandlerDecorators.on_template_quality_update,
            _HandlerDecorators.on_template_components_update,
            _HandlerDecorators.on_call_connect,
            _HandlerDecorators.on_call_terminate,
            _HandlerDecorators.on_call_status,
            _HandlerDecorators.on_call_permission_update,
            _HandlerDecorators.on_user_marketing_preferences,
            _HandlerDecorators.on_raw_update,
            ListenersSync._remove_listener,
            BaseUpdate.from_update,
            BaseUpdate.stop_handling,
            BaseUpdate.continue_handling,
            BaseUpdate.handle_again,
            ArrivedMedia.from_flow_completion,
            SentMessageSync.from_sent_update,
            SentMessageSync._convert_to,
            FlowRequestSync.decrypt_media,
            FlowRequestSync.token_no_longer_valid,
            FlowRequestSync.respond,
            FlowRequestSync.from_dict,
            FlowResponseSync.to_dict,
            FlowCompletionSync.get_media,
            UserSync.as_vcard,
            TemplateDetailsSync.to_json,
            MessageSync._resolve_msg_content,
        }
    ]
    non_async = {
        "_register_routes",
        "_register_flow_endpoint_callback",
        "_register_flow_callback_wrapper",
        "_api_cls",
        "_usr_cls",
        "_httpx_client",
        "_flow_req_cls",
        "_api_fields",
        "is_quick_reply",
    }
    for sync_obj, async_obj in overrides:
        for method_name in filter(
            lambda m: m not in skip_methods, get_obj_methods_names(sync_obj)
        ):
            sync_method, async_method = (
                getattr(sync_obj, method_name),
                getattr(async_obj, method_name),
            )
            if not asyncio.iscoroutinefunction(async_method):
                if method_name in non_async:
                    assert sync_method != async_method, (
                        f"Method/attr {method_name} is not overwritten in {async_obj}"
                    )
                    continue
                raise AssertionError(
                    f"Method {method_name} is not overwritten in {async_obj}"
                ) from None


def test_same_signature(overrides):
    skip_methods = [
        "_api_cls",
        "_usr_cls",
        "_httpx_client",
        "_flow_req_cls",
    ]

    skip_signature_check = {
        m.__name__: skip_params
        for m, skip_params in (
            (WhatsAppSync.upload_media, ("dl_session",)),
            (FlowRequestSync.decrypt_media, ("dl_session",)),
            (WhatsAppSync.webhook_update_handler, ("self",)),
            (WhatsAppSync.webhook_challenge_handler, ("self",)),
            (WhatsAppSync.send_image, ("image",)),
            (MessageSync.reply_image, ("image",)),
            (WhatsAppSync.send_video, ("video",)),
            (MessageSync.reply_video, ("video",)),
            (WhatsAppSync.send_document, ("document",)),
            (MessageSync.reply_document, ("document",)),
            (WhatsAppSync.send_audio, ("audio",)),
            (WhatsAppSync.send_voice, ("voice",)),
            (MessageSync.reply_audio, ("audio",)),
            (MessageSync.reply_voice, ("voice",)),
            (WhatsAppSync.send_sticker, ("sticker",)),
            (MessageSync.reply_sticker, ("sticker",)),
            (WhatsAppSync.upload_media, ("media", "download_chunk_size", "dl_session")),
            (WhatsAppSync.update_business_profile, ("profile_picture",)),
            (GraphAPISync.upload_file, ("file",)),
        )
    }
    for sync_obj, async_obj in overrides:
        for method_name in get_obj_methods_names(sync_obj):
            if method_name in skip_methods:
                continue
            sync_sig, async_sig = (
                inspect.signature(getattr(sync_obj, method_name)),
                inspect.signature(getattr(async_obj, method_name)),
            )
            try:
                assert sync_sig.parameters == async_sig.parameters, (
                    f"Method {method_name} has different signature in {async_obj}"
                )
            except AssertionError:
                if method_name in skip_signature_check:
                    sync_sig, async_sig = (
                        dict(sync_sig.parameters),
                        dict(async_sig.parameters),
                    )
                    for param in skip_signature_check[method_name]:
                        sync_sig.pop(param, None)
                        async_sig.pop(param, None)
                    assert sync_sig == async_sig, (
                        f"Method {method_name} has different signature in {async_obj}"
                    )
                else:
                    raise


def test_same_return_annotation(overrides):
    skip_methods = [
        WhatsAppSync.stream_media.__name__,
        GraphAPISync.stream_media_bytes.__name__,
        MediaSync.stream.__name__,
    ]
    for sync_obj, async_obj in overrides:
        for method_name in get_obj_methods_names(sync_obj):
            if method_name in skip_methods:
                continue
            sync_sig, async_sig = (
                inspect.signature(getattr(sync_obj, method_name)),
                inspect.signature(getattr(async_obj, method_name)),
            )
            assert sync_sig.return_annotation == async_sig.return_annotation, (
                f"Method {method_name} has different return annotations in {async_obj}"
            )


def test_same_docstring(overrides):
    skip_methods = [
        "wait_for_completion",
        "upload_media",
        "_api_cls",
        "_usr_cls",
        "_httpx_client",
        "_flow_req_cls",
    ]
    for sync_obj, async_obj in overrides:
        _check_docs(
            sync_doc=sync_obj.__doc__,
            async_doc=async_obj.__doc__,
            async_obj=async_obj,
            method_name=None,
        )
        for method_name in get_obj_methods_names(sync_obj):
            if method_name in skip_methods:
                continue
            sync_doc, async_doc = (
                getattr(sync_obj, method_name).__doc__,
                getattr(async_obj, method_name).__doc__,
            )
            _check_docs(
                sync_doc=sync_doc,
                async_doc=async_doc,
                async_obj=async_obj,
                method_name=method_name,
            )


def _check_docs(
    *, sync_doc: str, async_doc: str, async_obj: type, method_name: str | None
):
    if (sync_doc and not async_doc) or (not sync_doc and async_doc):
        if method_name:
            raise AssertionError(
                f"Method {method_name} missing docstrings in {async_obj}"
            )
        raise AssertionError(f"Missing docstrings in {async_obj}")
    try:
        assert sync_doc == async_doc, (
            f"Method {method_name} has different docstrings in {async_obj}"
            if method_name
            else f"Docstrings are different in {async_obj}"
        )
    except AssertionError:
        try:
            for doc, adoc in zip(
                sync_doc.splitlines(), async_doc.splitlines(), strict=True
            ):
                if doc != adoc:
                    if (
                        "async" in adoc.lower() or "await" in adoc.lower()
                    ):  # async examples
                        continue
                    raise
        except ValueError:  # different number of lines
            raise AssertionError(
                f"Method {method_name} has different docstrings in {async_obj}"
            ) from None


def test_all_handlers_to_updates_are_overwritten_in_async(overrides):
    assert len(WhatsAppSync._handlers_to_updates) == len(
        WhatsAppAsync._handlers_to_updates
    ), (
        "WhatsAppSync._handlers_to_updates and WhatsAppAsync._handlers_to_updates have different lengths"
    )
    for handler, update in WhatsAppSync._handlers_to_updates.items():
        assert WhatsAppAsync._handlers_to_updates[handler] != update, (
            f"Handler {handler} has the same update class in WhatsAppAsync: {update}"
        )
