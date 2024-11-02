import asyncio

from pywa import WhatsApp as WhatsAppSync
from pywa_async import WhatsApp as WhatsAppAsync


def test_all_methods_overwritten_in_async():
    skip_methods = {
        "api",
        "token",
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
        "_async_allowed",
        "_check_for_async_callback",
        "_after_calling_update",
        "_check_for_async_filters",
        "_check_and_prepare_update",
        "_check_for_async_func",
        "_get_handler",
        "_handlers_to_update_constractor",
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
    }
    for method in dir(WhatsAppSync):
        if method.startswith("__") or method in skip_methods:
            continue
        if not asyncio.iscoroutinefunction(getattr(WhatsAppAsync, method)):
            raise AssertionError(f"Method {method} is not overwritten in WhatsAppAsync")
