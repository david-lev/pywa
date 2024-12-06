import asyncio
import inspect

from pywa import WhatsApp as WhatsAppSync
from pywa.handlers import HandlerDecorators
from pywa.types.base_update import BaseUpdate
from pywa_async import WhatsApp as WhatsAppAsync
from pywa.api import WhatsAppCloudApi as WhatsAppCloudApiSync
from pywa_async.api import WhatsAppCloudApiAsync
from pywa.server import Server as ServerSync
from pywa_async.server import Server as ServerAsync
from pywa.listeners import Listeners as ListenersSync
from pywa_async.listeners import AsyncListeners as ListenersAsync
from pywa.types import (
    Message as MessageSync,
    CallbackButton as CallbackButtonSync,
    CallbackSelection as CallbackSelectionSync,
    MessageStatus as MessageStatusSync,
    ChatOpened as ChatOpenedSync,
    FlowCompletion as FlowCompletionSync,
    TemplateStatus as TemplateStatusSync,
    FlowRequest as FlowRequestSync,
    FlowResponse as FlowResponseSync,
    MediaUrlResponse as MediaUrlResponseSync,
)
from pywa_async.types import (
    Message as MessageAsync,
    CallbackButton as CallbackButtonAsync,
    CallbackSelection as CallbackSelectionAsync,
    MessageStatus as MessageStatusAsync,
    ChatOpened as ChatOpenedAsync,
    FlowCompletion as FlowCompletionAsync,
    TemplateStatus as TemplateStatusAsync,
    FlowRequest as FlowRequestAsync,
    MediaUrlResponse as MediaUrlResponseAsync,
)
from pywa.types.flows import FlowDetails as FlowDetailsSync
from pywa_async.types.flows import FlowDetails as FlowDetailsAsync
from pywa.types.media import BaseMedia as BaseMediaSync
from pywa_async.types.media import BaseMediaAsync
from pywa.types.sent_message import SentMessage as SentMessageSync
from pywa_async.types.sent_message import SentMessage as SentMessageAsync

OVERRIDES: list[tuple] = [
    (WhatsAppSync, WhatsAppAsync),
    (MessageSync, MessageAsync),
    (CallbackButtonSync, CallbackButtonAsync),
    (CallbackSelectionSync, CallbackSelectionAsync),
    (MessageStatusSync, MessageStatusAsync),
    (ChatOpenedSync, ChatOpenedAsync),
    (FlowCompletionSync, FlowCompletionAsync),
    (TemplateStatusSync, TemplateStatusAsync),
    (FlowRequestSync, FlowRequestAsync),
    (FlowDetailsSync, FlowDetailsAsync),
    (MediaUrlResponseSync, MediaUrlResponseAsync),
    (BaseMediaSync, BaseMediaAsync),
    (SentMessageSync, SentMessageAsync),
    (WhatsAppCloudApiSync, WhatsAppCloudApiAsync),
]


def get_all_methods_names(obj):
    return {m for m in dir(obj) if callable(getattr(obj, m)) and not m.startswith("__")}


def test_all_methods_are_overwritten_in_async():
    skip_methods = [
        m.__name__
        for m in {
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
            ServerSync._check_and_prepare_update,
            ServerSync._after_handling_update,
            ServerSync._delayed_register_callback_url,
            ServerSync._register_callback_url,
            ServerSync._get_handler,
            ServerSync._register_flow_endpoint_callback,
            HandlerDecorators.on_message,
            HandlerDecorators.on_callback_button,
            HandlerDecorators.on_callback_selection,
            HandlerDecorators.on_message_status,
            HandlerDecorators.on_chat_opened,
            HandlerDecorators.on_flow_completion,
            HandlerDecorators.on_flow_request,
            HandlerDecorators.on_template_status,
            HandlerDecorators.on_raw_update,
            ListenersSync._remove_listener,
            BaseUpdate.from_update,
            BaseUpdate.stop_handling,
            BaseUpdate.continue_handling,
            BaseMediaSync.from_flow_completion,
            SentMessageSync.from_sent_update,
            FlowRequestSync.decrypt_media,
            FlowRequestSync.respond,
            FlowRequestSync.from_dict,
            FlowCompletionSync.get_media,
            TemplateStatusSync.TemplateEvent,
            TemplateStatusSync.TemplateRejectionReason,
        }
    ]
    non_async = {
        "_register_routes",
        "_register_flow_endpoint_callback",
        "_register_flow_callback_wrapper",
        "_api_cls",
        "_httpx_client",
        "_flow_req_cls",
    }
    for sync_obj, async_obj in OVERRIDES:
        for method_name in filter(
            lambda m: m not in skip_methods, get_all_methods_names(sync_obj)
        ):
            sync_method, async_method = (
                getattr(sync_obj, method_name),
                getattr(async_obj, method_name),
            )
            if not asyncio.iscoroutinefunction(async_method):
                if method_name in non_async:
                    assert (
                        sync_method != async_method
                    ), f"Method/attr {method_name} is not overwritten in {async_obj.__name__}"
                    continue
                raise AssertionError(
                    f"Method {method_name} is not overwritten in {async_obj.__name__}"
                )


def test_same_signature():
    skip_methods = [
        m.__name__
        for m in {
            BaseMediaSync.from_dict,
        }
    ]
    skip_methods.extend(
        {
            "_api_cls",
            "_httpx_client",
            "_flow_req_cls",
        }
    )
    skip_signature_check = {
        m.__name__: skip_params
        for m, skip_params in (
            (WhatsAppSync.upload_media, ("dl_session",)),
            (FlowRequestSync.decrypt_media, ("dl_session",)),
            (WhatsAppSync.webhook_update_handler, ("self",)),
            (WhatsAppSync.webhook_challenge_handler, ("self",)),
        )
    }
    for sync_obj, async_obj in OVERRIDES:
        for method_name in get_all_methods_names(sync_obj):
            if method_name in skip_methods:
                continue
            sync_sig, async_sig = (
                inspect.signature(getattr(sync_obj, method_name)),
                inspect.signature(getattr(async_obj, method_name)),
            )
            if sync_sig.parameters != async_sig.parameters:
                if method_name not in skip_signature_check:
                    raise AssertionError(
                        f"Method {method_name} has different signature in {async_obj.__name__}"
                    )


def test_same_return_annotation():
    skip_methods = [
        m.__name__
        for m in {
            BaseMediaSync.from_dict,
            BaseMediaSync.from_flow_completion,
        }
    ]
    for sync_obj, async_obj in OVERRIDES:
        for method_name in get_all_methods_names(sync_obj):
            if method_name in skip_methods:
                continue
            sync_sig, async_sig = (
                inspect.signature(getattr(sync_obj, method_name)),
                inspect.signature(getattr(async_obj, method_name)),
            )
            if sync_sig.return_annotation != async_sig.return_annotation:
                raise AssertionError(
                    f"Method {method_name} has different return annotations in {async_obj.__name__}"
                )
