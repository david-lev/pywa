from __future__ import annotations

__all__ = [
    "resolve_buttons_param",
    "resolve_media_param",
    "resolve_tracker_param",
    "resolve_phone_id_param",
    "resolve_waba_id_param",
    "resolve_flow_json_param",
    "get_interactive_msg",
    "get_media_msg",
    "get_flow_fields",
    "get_flow_metric_field",
    "resolve_callback_data",
]

import datetime
import json
import pathlib
from typing import Any, BinaryIO, Literal, Iterable, TYPE_CHECKING

from .types import (
    FlowMetricName,
    FlowMetricGranularity,
    FlowJSON,
    CallbackData,
    MessageType,
    ButtonUrl,
    SectionList,
    FlowButton,
    Button,
    NewTemplate, FlowActionType
)
from pywa.types.others import InteractiveType

if TYPE_CHECKING:
    from pywa import WhatsApp


def resolve_buttons_param(
    buttons: Iterable[Button] | ButtonUrl | FlowButton | SectionList,
) -> tuple[
    InteractiveType,
    dict,
    dict[str, set[str] | str],
]:
    """
    Internal method to resolve ``buttons`` parameter. Returns a tuple of (``type``, ``buttons``, ``callback_options``).
    """
    if isinstance(buttons, SectionList):
        data = buttons.to_dict()
        return (
            InteractiveType.LIST,
            data,
            {
                "_callback_options": {
                    row["id"] for section in data["sections"] for row in section["rows"]
                }
            },
        )
    elif isinstance(buttons, ButtonUrl):
        return InteractiveType.CTA_URL, buttons.to_dict(), {}
    elif isinstance(buttons, FlowButton):
        return (
            InteractiveType.FLOW,
            buttons.to_dict(),
            {"_flow_token": buttons.flow_token},
        )
    else:  # assume its list of buttons
        data = tuple(b.to_dict() for b in buttons)
        return (
            InteractiveType.BUTTON,
            {"buttons": data},
            {"_callback_options": {b["reply"]["id"] for b in data}},
        )


_media_types_default_filenames = {
    MessageType.IMAGE: "image.jpg",
    MessageType.VIDEO: "video.mp4",
    MessageType.AUDIO: "audio.mp3",
    MessageType.STICKER: "sticker.webp",
}


def resolve_media_param(
    wa: WhatsApp,
    media: str | pathlib.Path | bytes | BinaryIO,
    mime_type: str | None,
    filename: str | None,
    media_type: Literal[
        MessageType.IMAGE, MessageType.VIDEO, MessageType.AUDIO, MessageType.STICKER
    ]
    | None,
    phone_id: str,
) -> tuple[bool, str]:
    """
    Internal method to resolve the ``media`` parameter. Returns a tuple of (``is_url``, ``media_id_or_url``).
    """
    if isinstance(media, (str, pathlib.Path)):
        if str(media).startswith(("https://", "http://")):
            return True, media
        elif str(media).isdigit() and not pathlib.Path(media).is_file():
            return False, media  # assume it's a media ID
    # assume its bytes or a file path
    return False, wa.upload_media(
        phone_id=phone_id,
        media=media,
        mime_type=mime_type,
        filename=_media_types_default_filenames.get(media_type, filename),
    )


def resolve_tracker_param(tracker: str | CallbackData | None) -> str | None:
    """Internal method to resolve the `tracker` parameter."""
    return tracker.to_str() if isinstance(tracker, CallbackData) else tracker


def resolve_phone_id_param(
    wa: WhatsApp, phone_id: str | int | None, arg_name: str
) -> str:
    """Internal method to resolve the `phone_id` parameter."""
    if phone_id is not None:
        return str(phone_id)
    if wa.phone_id is not None:
        return wa.phone_id
    raise ValueError(
        f"When initializing WhatsApp without phone_id, {arg_name} must be provided."
    )


def resolve_waba_id_param(wa: WhatsApp, waba_id: str | int | None) -> str:
    """Internal method to resolve the `waba_id` parameter."""
    if waba_id is not None:
        return str(waba_id)
    if wa.business_account_id is not None:
        return wa.business_account_id
    raise ValueError(
        "When initializing WhatsApp without business_account_id, waba_id must be provided."
    )


def resolve_flow_json_param(
    flow_json: FlowJSON | dict | str | pathlib.Path | bytes | BinaryIO,
) -> str:
    """Internal method to solve the `flow_json` parameter"""
    json_str, to_dump = None, None
    if isinstance(flow_json, (str, pathlib.Path)):  # json str or path to json file
        as_path = pathlib.Path(flow_json)
        try:
            if as_path.is_file():
                with open(as_path, "r", encoding="utf-8") as f:
                    json_str = f.read()
            else:
                json_str = flow_json
        except OSError:
            json_str = flow_json
    elif isinstance(flow_json, bytes):
        json_str = flow_json.decode()
    elif isinstance(flow_json, FlowJSON):
        json_str = flow_json.to_json()
    elif isinstance(flow_json, dict):
        to_dump = flow_json
    else:
        raise TypeError(
            f"`flow_json` must be a FlowJSON object, dict, json string, json file path or json bytes. not {type(flow_json)}"
        )

    if to_dump is not None:
        json_str = json.dumps(to_dump, indent=4, ensure_ascii=False)

    return json_str


def get_interactive_msg(
    typ: InteractiveType,
    action: dict[str, Any],
    header: dict | None = None,
    body: str | None = None,
    footer: str | None = None,
):
    return {
        "type": typ,
        "action": action,
        **({"header": header} if header else {}),
        **({"body": {"text": body}} if body else {}),
        **({"footer": {"text": footer}} if footer else {}),
    }


def get_media_msg(
    media_id_or_url: str,
    is_url: bool,
    caption: str | None = None,
    filename: str | None = None,
):
    return {
        ("link" if is_url else "id"): media_id_or_url,
        **({"caption": caption} if caption else {}),
        **({"filename": filename} if filename else {}),
    }


def get_flow_fields(
    invalidate_preview: bool, phone_number_id: str | None
) -> tuple[str, ...]:
    """Internal method to get the fields of a flow."""
    return (
        "id",
        "name",
        "status",
        "updated_at",
        "categories",
        "validation_errors",
        "json_version",
        "data_api_version",
        "endpoint_uri",
        f"preview.invalidate({'true' if invalidate_preview else 'false'})",
        "whatsapp_business_account",
        "application",
        "health_status"
        if not phone_number_id
        else f"health_status.phone_number({phone_number_id})",
    )


def get_flow_metric_field(
    metric_name: FlowMetricName,
    granularity: FlowMetricGranularity,
    since: datetime.date | str | None,
    until: datetime.date | str | None,
) -> str:
    date_fmt = "%Y-%m-%d"
    return (
        f"metric.name({metric_name}).granularity({granularity})"
        + (
            f".since({since.strftime(date_fmt) if isinstance(since, datetime.date) else since})"
            if since
            else ""
        )
        + (
            f".until({until.strftime(date_fmt) if isinstance(until, datetime.date) else until})"
            if until
            else ""
        )
    )


def resolve_callback_data(data: str | CallbackData) -> str:
    """Internal function to convert callback data to a string."""
    if isinstance(data, CallbackData):
        return data.to_str()
    elif isinstance(data, str):
        return data
    raise TypeError(f"Invalid callback data type {type(data)}")


def parse_template_data(template_data: dict[str, Any]) -> dict[str, Any]:
    """Parse template data into a structured dictionary with typed components."""
    template = {
        "id": template_data.get("id", ""),
        "name": template_data.get("name", ""),
        "language": template_data.get("language", ""),
        "status": template_data.get("status", ""),
        "parameter_format": template_data.get("parameter_format", ""),
        "sub_category": template_data.get("sub_category"),
    }

    # Convert category to enum
    category_value = template_data.get("category", "")
    try:
        template["category"] = NewTemplate.Category(category_value)
    except ValueError:
        raise ValueError(f"Unknown template category: {category_value}")

    # Parse components
    components = []
    for component in template_data.get("components", []):
        comp_type = component.get("type")

        if comp_type == "HEADER":
            format_type = component.get("format")
            if format_type == "TEXT":
                components.append(NewTemplate.Text(text=component.get("text", "")))
            elif format_type == "IMAGE":
                example = component.get("example", {}).get("header_handle", [""])[0]
                components.append(NewTemplate.Image(example=example))
            elif format_type == "VIDEO":
                example = component.get("example", {}).get("header_handle", [""])[0]
                components.append(NewTemplate.Video(example=example))
            elif format_type == "DOCUMENT":
                example = component.get("example", {}).get("header_handle", [""])[0]
                components.append(NewTemplate.Document(example=example))
            elif format_type == "LOCATION":
                components.append(NewTemplate.Location())
            else:
                raise ValueError(f"Unknown header format: {format_type}")

        elif comp_type == "BODY":
            text = component.get("text", "")
            components.append(NewTemplate.Body(text=text))

        elif comp_type == "FOOTER":
            text = component.get("text", "")
            components.append(NewTemplate.Footer(text=text))

        elif comp_type == "BUTTONS":
            buttons = []
            for button in component.get("buttons", []):
                button_type = button.get("type")

                if button_type == "PHONE_NUMBER":
                    buttons.append(NewTemplate.PhoneNumberButton(
                        title=button.get("text", ""),
                        phone_number=button.get("phone_number", "")
                    ))

                elif button_type == "URL":
                    buttons.append(NewTemplate.UrlButton(
                        title=button.get("text", ""),
                        url=button.get("url", "")
                    ))

                elif button_type == "QUICK_REPLY":
                    buttons.append(NewTemplate.QuickReplyButton(
                        text=button.get("text", "")
                    ))

                elif button_type == "COPY_CODE":
                    buttons.append(NewTemplate.CopyCodeButton(
                        example=button.get("example", "")
                    ))

                elif button_type == "OTP":
                    otp_type_str = button.get("otp_type", "")
                    try:
                        otp_type = NewTemplate.OTPButton.OtpType(otp_type_str)
                        if otp_type in (NewTemplate.OTPButton.OtpType.ONE_TAP,
                                        NewTemplate.OTPButton.OtpType.ZERO_TAP):
                            buttons.append(NewTemplate.OTPButton(
                                otp_type=otp_type,
                                title=button.get("text"),
                                autofill_text=button.get("autofill_text"),
                                package_name=button.get("package_name"),
                                signature_hash=button.get("signature_hash"),
                                zero_tap_terms_accepted=button.get("zero_tap_terms_accepted", True)
                            ))
                        else:
                            buttons.append(NewTemplate.OTPButton(
                                otp_type=otp_type,
                                title=button.get("text")
                            ))
                    except ValueError:
                        raise ValueError(f"Unknown OTP button type: {otp_type_str}")

                elif button_type == "MPM":
                    buttons.append(NewTemplate.MPMButton())

                elif button_type == "CATALOG":
                    buttons.append(NewTemplate.CatalogButton())

                elif button_type == "FLOW":
                    flow_id = button.get("flow_id", "")
                    flow_action_str = button.get("flow_action", "")

                    try:
                        flow_action = FlowActionType(flow_action_str)
                        if flow_action == FlowActionType.NAVIGATE:
                            buttons.append(NewTemplate.FlowButton(
                                title=button.get("text", ""),
                                flow_id=flow_id,
                                flow_action=flow_action,
                                navigate_screen=button.get("navigate_screen", "")
                            ))
                        else:
                            buttons.append(NewTemplate.FlowButton(
                                title=button.get("text", ""),
                                flow_id=flow_id,
                                flow_action=flow_action
                            ))
                    except ValueError:
                        raise ValueError(f"Unknown flow action type: {flow_action_str}")

                else:
                    raise ValueError(f"Unknown button type: {button_type}")

            components.append({"type": "BUTTONS", "buttons": buttons})

        else:
            raise ValueError(f"Unknown component type: {comp_type}")

    template["components"] = components
    return template