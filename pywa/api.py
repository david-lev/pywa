from typing import TYPE_CHECKING
from pywa.errors import WhatsAppApiError
from pywa.types import Button, SectionList

if TYPE_CHECKING:
    from pywa.client import WhatsApp


class WhatsAppCloudApi:
    """Internal methods for the WhatsApp client."""

    def _make_request(
            self: "WhatsApp",
            method: str,
            endpoint: str,
            **kwargs
    ) -> dict | list:
        res = self._session.request(method=method, url=f"{self._base_url}{endpoint}", **kwargs)
        if res.status_code != 200:
            raise WhatsAppApiError(status_code=res.status_code, error=res.json()["error"])
        return res.json()

    def _send_text_message(
            self: "WhatsApp",
            to: str,
            text: str,
            preview_url: bool = False,
            reply_to_message_id: str | None = None,
    ) -> str:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": text},
            "preview_url": preview_url
        }
        if reply_to_message_id:
            data["context"] = {"message_id": reply_to_message_id}

        return self._make_request(
            method="POST",
            endpoint=f"/{self.phone_id}/messages",
            json=data
        )['messages'][0]['id']

    def _send_interactive_message(
            self: "WhatsApp",
            to: str,
            keyboard: list[Button] | SectionList,
            text: str,
            reply_to_message_id: str | None = None,
    ) -> str:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "",
                "action": {},
                "body": {"text": text},
            }
        }
        if reply_to_message_id:
            data["context"] = {"message_id": reply_to_message_id}
        if isinstance(keyboard, SectionList):
            data["interactive"]["type"] = "list"
            data["interactive"]["action"] = keyboard.to_dict()
        else:
            data["interactive"]["type"] = "button"
            data["interactive"]["action"]["buttons"] = [button.to_dict() for button in keyboard]

        return self._make_request(
            method="POST",
            endpoint=f"/{self.phone_id}/messages",
            json=data
        )['messages'][0]['id']
