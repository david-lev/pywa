import mimetypes
from typing import Iterable
import requests
from pywa.errors import WhatsAppApiError
from pywa.types import InlineButton, SectionList, Contact


class WhatsAppCloudApi:
    """Internal methods for the WhatsApp client."""

    def __init__(
            self,
            phone_id: str,
            token: str,
            session: requests.Session,
            base_url: str,
            api_version: float,
    ):
        self.phone_id = phone_id
        self._session = session
        self._base_url = f"{base_url}/v{api_version}"
        self._session.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        self._common_keys = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
        }

    def _make_request(
            self,
            method: str,
            endpoint: str,
            **kwargs
    ) -> dict | list:
        res = self._session.request(method=method, url=f"{self._base_url}/{self.phone_id}{endpoint}", **kwargs)
        if res.status_code != 200:
            raise WhatsAppApiError(status_code=res.status_code, error=res.json()["error"])
        return res.json()

    def send_text_message(
            self,
            to: str | int,
            text: str,
            preview_url: bool = False,
            reply_to_message_id: str | None = None,
    ) -> str:
        data = {
            **self._common_keys,
            "to": str(to),
            "type": "text",
            "text": {
                "body": text,
                "preview_url": preview_url
            },
        }
        if reply_to_message_id:
            data["context"] = {"message_id": reply_to_message_id}

        return self._make_request(
            method="POST",
            endpoint=f"/messages",
            json=data
        )['messages'][0]['id']

    def upload_media(
            self,
            media: str | bytes,
            mime_type: str | None
    ) -> str:
        """
        Upload a media file to WhatsApp.

        Args:
            media: media bytes / path / URL to upload.
            mime_type: The type of the media file (if not provided, it will be guessed with the `mimetypes` library).

        Returns:
            The ID of the uploaded media file.

        Raises:
            ValueError: If ``mime_type`` is not provided and cannot be guessed (e.g. for bytes or URLs without ``Content-Type`` header).
        """
        if isinstance(media, str):
            if media.startswith(("https://", "http://")):
                res = requests.get(media)
                res.raise_for_status()
                file = res.content
                mime_type = mime_type or res.headers.get('Content-Type', default=res.headers.get('content-type'))
            else:
                mime_type = mime_type or mimetypes.guess_type(media)[0]
                with open(media, "rb") as f:
                    file = f.read()
        else:
            file = media
        if mime_type is None:
            raise ValueError("mime_type is required")
        headers = self._session.headers.copy()
        headers["Content-Type"] = mime_type
        files = {
            'file': (None, file),
            'type': (None, mime_type),
            'messaging_product': (None, '"whatsapp"'),
        }
        return self._make_request(
            method="POST",
            endpoint=f"/media",
            headers=headers,
            files=files
        )["id"]

    def send_media(
            self,
            to: str | int,
            media_id_or_url: str,
            media_type: str,
            reply_to_message_id: str | None = None,
            **kwargs
    ):
        if reply_to_message_id:
            kwargs["context"] = {"message_id": reply_to_message_id}
        data = {
            **self._common_keys,
            "to": str(to),
            "type": media_type,
            media_type: {
                "link" if media_id_or_url.startswith(('https:', 'http:')) else "id": media_id_or_url,
                **{k: v for k, v in kwargs.items() if v is not None}
            }
        }
        return self._make_request(
            method="POST",
            endpoint=f"/messages",
            json=data
        )['messages'][0]['id']

    def send_reaction(
            self,
            to: str | int,
            emoji: str,
            message_id: str,
    ):
        return self._make_request(
            method="POST",
            endpoint="/messages/",
            json={
                **self._common_keys,
                "to": str(to),
                "type": "reaction",
                "reaction": {
                    "emoji": emoji,
                    "message_id": message_id
                }
            }
        )['messages'][0]['id']

    def send_location(
            self,
            to: str | int,
            latitude: float,
            longitude: float,
            name: str | None = None,
            address: str | None = None,
    ):
        data = {
            **self._common_keys,
            "to": str(to),
            "type": "location",
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "name": name,
                "address": address
            }
        }

        return self._make_request(
            method="POST",
            endpoint=f"/messages",
            json=data
        )['messages'][0]['id']

    def send_raw_json(
            self,
            data: dict
    ) -> dict:
        return self._make_request(
            method="POST",
            endpoint=f"/messages",
            json=data
        )

    def send_interactive_message(
            self,
            to: str | int,
            keyboard: list[InlineButton] | SectionList,
            body: str,
            header: dict | None = None,
            footer: str | None = None,
            reply_to_message_id: str | None = None,
    ) -> str:
        data = {
            **self._common_keys,
            "to": str(to),
            "type": "interactive",
            "interactive": {
                "type": "",
                "action": {},
                "body": {"text": body},
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
        if header:
            data["interactive"]["header"] = header
        if footer:
            data["interactive"]["footer"] = {"text": footer}

        return self._make_request(
            method="POST",
            endpoint=f"/messages",
            json=data
        )['messages'][0]['id']

    def send_contacts(
            self,
            to: str | int,
            contacts: Iterable[Contact],
            reply_to_message_id: str | None = None,
    ) -> str:
        data = {
            **self._common_keys,
            "to": str(to),
            "type": "contacts",
            "contacts": [contact.to_dict() for contact in contacts]
        }
        if reply_to_message_id:
            data["context"] = {"message_id": reply_to_message_id}
        return self._make_request(
            method="POST",
            endpoint=f"/messages",
            json=data
        )['messages'][0]['id']
