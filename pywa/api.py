import mimetypes
import requests
from typing import Iterable
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
        """
        Internal method to make a request to the WhatsApp API.

        Args:
            method: The HTTP method to use.
            endpoint: The endpoint to request.
            **kwargs: Additional arguments to pass to the request.

        Returns:
            The response JSON.

        Raises:
            WhatsAppApiError: If the request failed.
        """
        res = self._session.request(method=method, url=f"{self._base_url}{endpoint}", **kwargs)
        if res.status_code != 200:
            raise WhatsAppApiError(status_code=res.status_code, error=res.json()["error"])
        return res.json()

    def send_text_message(
            self,
            to: str | int,
            text: str,
            preview_url: bool = False,
            reply_to_message_id: str | None = None,
    ) -> dict[str, dict | list]:
        """
        Send a text message to a WhatsApp user.

        Return example::

            {
                'messaging_product': 'whatsapp',
                'contacts': [{'input': '1234567890', 'wa_id': '1234567890'}],
                'messages': [{'id': 'wamid.XXXXXXXXXXXXXXXX=='}]
            }

        Args:
            to: The WhatsApp ID of the recipient.
            text: The text to send.
            preview_url: Whether to show a preview of the URL in the message.
            reply_to_message_id: The ID of the message to reply to.

        Returns:
            The sent message.
        """
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
            endpoint=f"/{self.phone_id}/messages",
            json=data
        )

    def upload_media(
            self,
            media: str | bytes,
            mime_type: str | None
    ) -> dict[str, str]:
        """
        Upload a media file to WhatsApp.

        Return example::

            {
              'id':'<MEDIA_ID>'
            }

        Args:
            media: media bytes / path / URL to upload.
            mime_type: The type of the media file (if not provided, it will be guessed with the `mimetypes` library).

        Returns:
            A dict with the ID of the uploaded media file.

        Raises:
            ValueError: If ``mime_type`` is not provided and cannot be guessed (e.g. for bytes or URLs without
             ``Content-Type`` header).
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
            endpoint=f"/{self.phone_id}/media",
            headers=headers,
            files=files
        )

    def get_media_url(self, media_id: str) -> dict:
        """
        Get the URL of a media file.
            - The url is valid for 5 minutes and can be downloaded only with access token.
            - For more info: https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media#retrieve-media-url

        Return example::

            {
                'url': 'https://lookaside.fbsbx.com/whatsapp_business/attachments/?mid=645645&ext=54353&hash=xxx-xx',
                'mime_type': 'image/jpeg',
                'sha256': '73298ec14751fhfonf4wfxxxf52f4fb031db3892ff5',
                'file_size': 61901,
                'id': '137524587935346',
                'messaging_product': 'whatsapp'
            }

        Args:
            media_id: The ID of the media file.

        Returns:
            A dict with the URL and other info about the media file.
        """
        return self._make_request(
            method="GET",
            endpoint=f"/{media_id}"
        )

    def download_media(
            self,
            media_url: str,
    ) -> tuple[bytes, str]:
        """
        Download a media file from WhatsApp servers.

        Args:
            media_url: The URL of the media file (from ``get_media_url``).

        Returns:
            The media file bytes and the MIME type.
        """
        headers = self._session.headers.copy()
        del headers["Content-Type"]
        res = self._session.get(media_url, headers=headers)
        res.raise_for_status()
        return res.content, res.headers.get("Content-Type", default=res.headers.get("content-type")) \
                            or 'application/octet-stream'

    def delete_media(self, media_id: str) -> dict[str, bool]:
        """
        Delete a media file from WhatsApp servers.

        Return example::

            {'success': True}

        Args:
            media_id: The ID of the media file.

        Returns:
            True if the media file was deleted successfully, False otherwise.
        """
        return self._make_request(
            method="DELETE",
            endpoint=f"/{media_id}"
        )

    def send_media(
            self,
            to: str | int,
            media_id_or_url: str,
            media_type: str,
            reply_to_message_id: str | None = None,
            **kwargs
    ) -> dict[str, dict | list]:
        """
        Send a media file to a WhatsApp user.

        Return example::

            {
                'messaging_product': 'whatsapp',
                'contacts': [{'input': '1234567890', 'wa_id': '1234567890'}],
                'messages': [{'id': 'wamid.XXXXXXXXXXXXXXXX=='}]
            }

        Args:
            to: The WhatsApp ID of the recipient.
            media_id_or_url: The ID or URL of the media file to send.
            media_type: The type of the media file.
            reply_to_message_id: The ID of the message to reply to.
            **kwargs: Additional arguments to send with the message.

        Returns:
            The sent message.
        """
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
            endpoint=f"/{self.phone_id}/messages",
            json=data
        )

    def send_reaction(
            self,
            to: str | int,
            emoji: str,
            message_id: str,
    ) -> dict[str, dict | list]:
        """
        Send a reaction to a message.

        Return example::

            {
                'messaging_product': 'whatsapp',
                'contacts': [{'input': '1234567890', 'wa_id': '1234567890'}],
                'messages': [{'id': 'wamid.XXXXXXXXXXXXXXXX=='}]
            }

        Args:
            to: The WhatsApp ID of the recipient.
            emoji: The emoji to react with (empty to remove reaction).
            message_id: The ID of the message to react to.

        Returns:
            The sent message.
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{self.phone_id}/messages/",
            json={
                **self._common_keys,
                "to": str(to),
                "type": "reaction",
                "reaction": {
                    "emoji": emoji,
                    "message_id": message_id
                }
            }
        )

    def send_location(
            self,
            to: str | int,
            latitude: float,
            longitude: float,
            name: str | None = None,
            address: str | None = None,
    ) -> dict[str, dict | list]:
        """
        Send a location to a WhatsApp user.

        Return example::

            {
                'messaging_product': 'whatsapp',
                'contacts': [{'input': '1234567890', 'wa_id': '1234567890'}],
                'messages': [{'id': 'wamid.XXXXXXXXXXXXXXXX=='}]
            }

        Args:
            to: The WhatsApp ID of the recipient.
            latitude: The latitude of the location.
            longitude: The longitude of the location.
            name: The name of the location.
            address: The address of the location.

        Returns:
            The sent message.
        """
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
            endpoint=f"/{self.phone_id}/messages",
            json=data
        )['messages'][0]['id']

    def send_raw_json(
            self,
            data: dict
    ) -> dict:
        """
        Send a raw JSON message to a WhatsApp Cloud API.

        Args:
            data: The raw JSON data to send.

        Returns:
            The sent message.
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{self.phone_id}/messages",
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
    ) -> dict[str, dict | list]:
        """
        Send an interactive message to a WhatsApp user.

        Return example::

            {
                'messaging_product': 'whatsapp',
                'contacts': [{'input': '1234567890', 'wa_id': '1234567890'}],
                'messages': [{'id': 'wamid.XXXXXXXXXXXXXXXX=='}]
            }

        Args:
            to: The WhatsApp ID of the recipient.
            keyboard: The keyboard to send.
            body: The body of the message.
            header: The header of the message.
            footer: The footer of the message.
            reply_to_message_id: The ID of the message to reply to.

        Returns:
            The sent message.
        """
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
            endpoint=f"/{self.phone_id}/messages",
            json=data
        )

    def send_contacts(
            self,
            to: str | int,
            contacts: Iterable[Contact],
            reply_to_message_id: str | None = None,
    ) -> dict[str, dict | list]:
        """
        Send a list of contacts to a WhatsApp user.

        Return example::

            {
                'messaging_product': 'whatsapp',
                'contacts': [{'input': '1234567890', 'wa_id': '1234567890'}],
                'messages': [{'id': 'wamid.XXXXXXXXXXXXXXXX=='}]
            }

        Args:
            to: The WhatsApp ID of the recipient.
            contacts: The contacts to send.
            reply_to_message_id: The ID of the message to reply to.

        Returns:
            The sent message.
        """
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
            endpoint=f"/{self.phone_id}/messages",
            json=data
        )

    def mark_message_as_read(
            self,
            message_id: str
    ) -> dict[str, bool]:
        """
        Mark a message as read.

        Return example::

            {'success': True}

        Args:
            message_id: The ID of the message to mark as read.

        Returns:
            The success of the operation.
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{self.phone_id}/messages",
            json={
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id
            }
        )
