import asyncio
import inspect
from pywa import WhatsApp as WhatsAppSync
from pywa_async import WhatsApp as WhatsAppAsync
from pywa.api import WhatsAppCloudApi as WhatsAppCloudApiSync
from pywa_async.api import WhatsAppCloudApiAsync
from pywa.types import (
    Message as MessageSync,
    CallbackButton as CallbackButtonSync,
    CallbackSelection as CallbackSelectionSync,
    MessageStatus as MessageStatusSync,
    ChatOpened as ChatOpenedSync,
    FlowCompletion as FlowCompletionSync,
    TemplateStatus as TemplateStatusSync,
    FlowRequest as FlowRequestSync,
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


def test_all_methods_are_overwritten_in_async():
    objs: list[tuple] = [
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
    skip_methods = {
        "add_handlers",
        "remove_handlers",
        "remove_callbacks",
        "add_flow_request_handler",
        "on_message",
        "on_callback_button",
        "on_callback_selection",
        "on_message_status",
        "on_chat_opened",
        "on_flow_completion",
        "on_template_status",
        "on_raw_update",
        "on_flow_request",
        "stop_listening",
        "_check_for_async_callback",
        "_after_handling_update",
        "_check_for_async_filters",
        "_check_and_prepare_update",
        "_check_for_async_func",
        "_get_handler",
        "_api_cls",
        "_flow_req_cls",
        "_httpx_client",
        "_delayed_register_callback_url",
        "_register_callback_url",
        "_get_handler_from_update",
        "_register_flow_callback_wrapper",
        "_register_flow_endpoint_callback",
        "_register_routes",
        "_remove_listener",
        "get_flow_request_handler",
        "load_handlers_modules",
        "continue_handling",
        "stop_handling",
        "from_update",
        "from_dict",
        "from_flow_completion",
        "from_sent_update",
        "get_media",
        "respond",
        "TemplateEvent",
        "TemplateRejectionReason",
    }
    skip_signature_check = {
        "upload_media",
        "webhook_challenge_handler",
        "webhook_update_handler",
        "decrypt_media",
    }
    for sync_obj, async_obj in objs:
        for method_name in filter(
            lambda a: callable(getattr(sync_obj, a))
            and not a.startswith("__")
            and a not in skip_methods,
            dir(sync_obj),
        ):
            sync_method, async_method = (
                getattr(sync_obj, method_name),
                getattr(async_obj, method_name),
            )
            if not asyncio.iscoroutinefunction(async_method):
                raise AssertionError(
                    f"Method {method_name} is not overwritten in {async_obj.__name__}"
                )
            if method_name not in skip_signature_check:
                sync_sig, async_sig = (
                    inspect.signature(sync_method),
                    inspect.signature(async_method),
                )
                if sync_sig.parameters != async_sig.parameters:
                    raise AssertionError(
                        f"Method {method_name} has different signatures in {async_obj.__name__}\n"
                        f"S: {sync_sig.parameters}\n"
                        f"A: {async_sig.parameters}"
                    )
                if sync_sig.return_annotation != async_sig.return_annotation:
                    raise AssertionError(
                        f"Method {method_name} has different return annotations in {async_obj.__name__}\n"
                        f"S: {sync_sig.return_annotation}\n"
                        f"A: {async_sig.return_annotation}"
                    )
