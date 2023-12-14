"""The internal API for the WhatsApp client."""

from typing import Any, TYPE_CHECKING

import requests
import requests_toolbelt

import pywa
from pywa.errors import WhatsAppError

if TYPE_CHECKING:
    from pywa import WhatsApp


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
        if session.headers.get("Authorization") is not None:
            raise ValueError(
                "You can't use the same requests.Session for multiple WhatsApp instances!"
            )
        self._session = session
        self._base_url = f"{base_url}/v{api_version}"
        self._session.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "User-Agent": f"PyWa/{pywa.__version__}",
        }
        self._common_keys = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
        }

    def __str__(self) -> str:
        return f"WhatsAppCloudApi(phone_id={self.phone_id!r})"

    def __repr__(self) -> str:
        return self.__str__()

    def _make_request(self, method: str, endpoint: str, **kwargs) -> dict | list:
        """
        Internal method to make a request to the WhatsApp Cloud API.

        Args:
            method: The HTTP method to use.
            endpoint: The endpoint to request.
            **kwargs: Additional arguments to pass to the request.

        Returns:
            The response JSON.

        Raises:
            WhatsAppError: If the request failed.
        """
        res = self._session.request(
            method=method, url=f"{self._base_url}{endpoint}", **kwargs
        )
        if res.status_code >= 400:
            raise WhatsAppError.from_dict(error=res.json()["error"], response=res)
        return res.json()

    def get_app_access_token(self, app_id: int, app_secret: str) -> dict[str, str]:
        """
        Get an access token for an app.

        Return example::

            {
                'access_token': 'xyzxyzxyz',
                'token_type': 'bearer'
            }


        Args:
            app_id: The ID of the app.
            app_secret: The secret of the app.

        Returns:
            The access token and its type.

        """
        return self._make_request(
            method="GET",
            endpoint="/oauth/access_token",
            params={
                "grant_type": "client_credentials",
                "client_id": app_id,
                "client_secret": app_secret,
            },
        )

    def set_callback_url(
        self,
        app_id: int,
        app_access_token: str,
        callback_url: str,
        verify_token: str,
        fields: tuple[str, ...],
    ) -> dict[str, bool]:
        """
        Set the callback URL for the webhook.

        Return example::

            {
                'success': True
            }

        Args:
            app_id: The ID of the app.
            app_access_token: The access token of the app (from ``get_app_access_token``).
            callback_url: The URL to set.
            verify_token: The verify token to challenge the webhook with.
            fields: The fields to subscribe to.

        Returns:
            The success of the operation.
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{app_id}/subscriptions",
            params={
                "object": "whatsapp_business_account",
                "callback_url": callback_url,
                "verify_token": verify_token,
                "fields": ",".join(fields),
                "access_token": app_access_token,
            },
        )

    def set_business_public_key(
        self,
        public_key: str,
    ) -> dict[str, bool]:
        """
        Set the public key of the business.

        Return example::

            {
                'success': True
            }

        Args:
            public_key: The public key to set.

        Returns:
            The success of the operation.
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{self.phone_id}/whatsapp_business_encryption",
            data={"business_public_key": public_key},
        )

    def send_text_message(
        self,
        to: str,
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
            "to": to,
            "type": "text",
            "text": {"body": text, "preview_url": preview_url},
        }
        if reply_to_message_id:
            data["context"] = {"message_id": reply_to_message_id}

        return self._make_request(
            method="POST",
            endpoint=f"/{self.phone_id}/messages",
            json=data,
        )

    def upload_media(
        self,
        media: bytes,
        mime_type: str,
        filename: str,
    ) -> dict[str, str]:
        """
        Upload a media file to WhatsApp.

        Return example::

            {
              'id':'<MEDIA_ID>'
            }

        Args:
            media: media bytes or open(path, 'rb') object
            mime_type: The type of the media file
            filename: The name of the media file
        Returns:
            A dict with the ID of the uploaded media file.
        """
        headers = self._session.headers.copy()
        form_data = requests_toolbelt.MultipartEncoder(
            {
                "file": (filename, media, mime_type),
                "messaging_product": "whatsapp",
                "type": mime_type,
            }
        )
        headers["Content-Type"] = form_data.content_type
        return self._make_request(
            method="POST",
            endpoint=f"/{self.phone_id}/media",
            headers=headers,
            data=form_data,
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
        return self._make_request(method="GET", endpoint=f"/{media_id}")

    def get_media_bytes(
        self,
        media_url: str,
        **kwargs,
    ) -> tuple[bytes, str | None]:
        """
        Get the bytes of a media file from WhatsApp servers.

        Args:
            media_url: The URL of the media file (from ``get_media_url``).
            **kwargs: Additional arguments to pass to the request.

        Returns:
            The media file bytes and the MIME type (if available).
        """
        headers = self._session.headers.copy()
        del headers["Content-Type"]
        res = self._session.get(media_url, headers=headers, **kwargs)
        res.raise_for_status()
        return res.content, res.headers.get("Content-Type")

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
        return self._make_request(method="DELETE", endpoint=f"/{media_id}")

    def send_media(
        self,
        to: str,
        media_id_or_url: str,
        media_type: str,
        is_url: bool,
        caption: str | None = None,
        filename: str | None = None,
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
            is_url: Whether the media_id_or_url is a URL or an ID.
            media_type: The type of the media file (e.g. 'image', 'video', 'document').
            caption: The caption to send with the media file (only for images, videos and documents).
            filename: The filename to send with the media file (only for documents).

        Returns:
            The sent message.
        """
        data = {
            **self._common_keys,
            "to": to,
            "type": media_type,
            media_type: {
                ("link" if is_url else "id"): media_id_or_url,
                **({"caption": caption} if caption else {}),
                **({"filename": filename} if filename else {}),
            },
        }
        return self._make_request(
            method="POST",
            endpoint=f"/{self.phone_id}/messages",
            json=data,
        )

    def send_reaction(
        self,
        to: str,
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
                "to": to,
                "type": "reaction",
                "reaction": {"emoji": emoji, "message_id": message_id},
            },
        )

    def send_location(
        self,
        to: str,
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
            "to": to,
            "type": "location",
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "name": name,
                "address": address,
            },
        }

        return self._make_request(
            method="POST",
            endpoint=f"/{self.phone_id}/messages",
            json=data,
        )

    def send_raw_request(self, method: str, endpoint: str, **kwargs) -> Any:
        """
        Send a raw request to WhatsApp Cloud API.

        - Use this method if you want to send a request that is not yet supported by pywa.
        - The endpoint can contain path parameters (e.g. ``/{phone_id}/messages/``). only ``phone_id`` is supported.
        - Every request will automatically include the ``Authorization`` and ``Content-Type`` headers. you can override them by passing them in ``kwargs`` (headers={...}).

        Args:
            method: The HTTP method to use (e.g. ``POST``, ``GET``, etc.).
            endpoint: The endpoint to send the message to (e.g. ``/{phone_id}/messages/``).
            **kwargs: Additional arguments to send with the request (e.g. ``json={...}, headers={...}``).

        Example:

            >>> wa = WhatsApp(...)
            >>> wa.api.send_raw_request(
            ..   method="POST",
            ..   endpoint="/{phone_id}/messages",
            ..   json={"to": "1234567890", "type": "text", "text": {"body": "Hello, World!"}}
            .. )
            {
                'messaging_product': 'whatsapp',
                'contacts': [{'input': '1234567890', 'wa_id': '1234567890'}],
                'messages': [{'id': 'wamid.XXXXXXXXXXXXXXXX=='}]
            }

        Returns:
            The response from the WhatsApp Cloud API.
        """
        return self._make_request(
            method=method,
            endpoint=endpoint.format(phone_id=self.phone_id),
            **kwargs,
        )

    def send_interactive_message(
        self,
        to: str,
        type_: str,
        action: dict[str, Any],
        header: dict | None = None,
        body: str | None = None,
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
            type_: The type of the message (e.g. ``list``, ``button``, ``product``, etc.).
            action: The action of the message.
            header: The header of the message.
            body: The body of the message.
            footer: The footer of the message.
            reply_to_message_id: The ID of the message to reply to.

        Returns:
            The sent message.
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{self.phone_id}/messages",
            json={
                **self._common_keys,
                "to": to,
                "type": "interactive",
                "interactive": {
                    "type": type_,
                    "action": action,
                    **({"header": header} if header else {}),
                    **({"body": {"text": body}} if body else {}),
                    **({"footer": {"text": footer}} if footer else {}),
                },
                **(
                    {"context": {"message_id": reply_to_message_id}}
                    if reply_to_message_id
                    else {}
                ),
            },
        )

    def send_contacts(
        self,
        to: str,
        contacts: tuple[dict[str, Any]],
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
            "to": to,
            "type": "contacts",
            "contacts": tuple(contacts),
        }
        if reply_to_message_id:
            data["context"] = {"message_id": reply_to_message_id}
        return self._make_request(
            method="POST",
            endpoint=f"/{self.phone_id}/messages",
            json=data,
        )

    def mark_message_as_read(self, message_id: str) -> dict[str, bool]:
        """
        Mark a message as read.

        Return example::

            {
                'success': True
            }

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
                "message_id": message_id,
            },
        )

    def get_business_profile(
        self,
    ) -> dict[str, list[dict[str, str | list[str]]]]:
        """
        Get the business profile.

        Return example::

            {
              "data": [{
                "about": "ABOUT",
                "address": "ADDRESS",
                "description": "DESCRIPTION",
                "email": "EMAIL",
                "messaging_product": "whatsapp",
                "profile_picture_url": "https://URL",
                "websites": [
                   "https://WEBSITE-1",
                   "https://WEBSITE-2"
                 ],
                "vertical": "INDUSTRY",
              }]
            }
        """
        fields = (
            "about",
            "address",
            "description",
            "email",
            "profile_picture_url",
            "websites",
            "vertical",
        )
        return self._make_request(
            method="GET",
            endpoint=f"/{self.phone_id}/whatsapp_business_profile?fields={','.join(fields)}",
        )

    def update_business_profile(
        self, data: dict[str, str | list[str]]
    ) -> dict[str, bool]:
        """
        Update the business profile.

        Args:
            data: The data to update the business profile with.

        Return example::

            {
                "success": True
            }
        """
        data.update(messaging_product="whatsapp")
        return self._make_request(
            method="POST",
            endpoint=f"/{self.phone_id}/whatsapp_business_profile",
            json=data,
        )

    def get_commerce_settings(self) -> dict[str, list[dict]]:
        """
        Get the commerce settings of the business catalog.

        Return example::

            {
              "data": [
                {
                  "is_cart_enabled": True,
                  "is_catalog_visible": True,
                  "id": "727705352028726"
                }
              ]
            }
        """
        return self._make_request(
            method="GET",
            endpoint=f"/{self.phone_id}/whatsapp_commerce_settings",
        )

    def update_commerce_settings(self, data: dict) -> dict[str, bool]:
        """
        Change the commerce settings of the business catalog.

        Args:
            data: The data to update the commerce settings with.

        Return example::

            {
              "success": True
            }
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{self.phone_id}/whatsapp_commerce_settings",
            params=data,
        )

    def create_template(
        self,
        business_account_id: str,
        template: dict[str, str | list[str]],
    ) -> dict[str, str]:
        """
        Create a message template.

        Args:
            business_account_id: The ID of the business account.
            template: The template to create.

        Return example::

            {
                "id": "594425479261596",
                "status": "PENDING",
                "category": "MARKETING"
            }
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{business_account_id}/message_templates",
            json=template,
        )

    def send_template(
        self,
        to: str,
        template: dict,
        reply_to_message_id: str | None = None,
    ) -> dict[str, dict | list]:
        """
        Send a template to a WhatsApp user.

        Args:
            to: The WhatsApp ID of the recipient.
            template: The template to send.
            reply_to_message_id: The ID of the message to reply to.

        Returns example::

            {
                'messaging_product': 'whatsapp',
                'contacts': [{'input': '1234567890', 'wa_id': '1234567890'}],
                'messages': [{'id': 'wamid.XXXXXXXXXXXXXXXX=='}]
            }

        """
        data = {
            **self._common_keys,
            "to": to,
            "type": "template",
            "template": template,
        }
        if reply_to_message_id:
            data["context"] = {"message_id": reply_to_message_id}
        return self._make_request(
            method="POST",
            endpoint=f"/{self.phone_id}/messages",
            json=data,
        )

    def create_flow(
        self,
        business_account_id: str,
        name: str,
        categories: tuple[str, ...],
        clone_flow_id: str | None = None,
    ) -> dict[str, str]:
        """
        Create or clone a flow.

        Args:
            business_account_id: The ID of the business account.
            name: The name of the flow.
            categories: The categories of the flow.
            clone_flow_id: The ID of the flow to clone.

        Return example::

            {
              "id": "<Flow-ID>"
            }
        """
        data = {
            "name": name,
            "categories": categories,
            **({"clone_flow_id": clone_flow_id} if clone_flow_id else {}),
        }
        return self._make_request(
            method="POST",
            endpoint=f"/{business_account_id}/flows",
            json=data,
        )

    def update_flow_metadata(
        self,
        flow_id: str,
        name: str | None = None,
        categories: tuple[str, ...] | None = None,
        endpoint_uri: str | None = None,
    ) -> dict[str, bool]:
        """
        Update the metadata of a flow.

        Args:
            flow_id: The ID of the flow.
            name: The name of the flow.
            categories: The categories of the flow.
            endpoint_uri: The endpoint URI of the flow.

        Return example::

            {
              "success": True
            }
        """
        data = {
            **({"name": name} if name else {}),
            **({"endpoint_uri": endpoint_uri} if endpoint_uri else {}),
            **({"categories": categories} if categories else {}),
        }
        return self._make_request(
            method="POST",
            endpoint=f"/{flow_id}",
            json=data,
        )

    def update_flow_json(self, flow_id: str, flow_json: str) -> dict:
        """
        Update the JSON of a flow.

        Args:
            flow_id: The ID of the flow.
            flow_json: The JSON of the flow.

        Return example::

            {
              "success": true,
              "validation_errors": [
                {
                  "error": "INVALID_PROPERTY",
                  "error_type": "JSON_SCHEMA_ERROR",
                  "message": "The property \"initial-text\" cannot be specified at \"$root/screens/0/layout/children/2/children/0\".",
                  "line_start": 46,
                  "line_end": 46,
                  "column_start": 17,
                  "column_end": 30
                }
              ]
            }
        """
        form_data = requests_toolbelt.MultipartEncoder(
            {
                "file": ("flow.json", flow_json, "application/json"),
                "name": "flow.json",
                "asset_type": "FLOW_JSON",
                "messaging_product": "whatsapp",
            }
        )
        headers = self._session.headers.copy()
        headers["Content-Type"] = form_data.content_type
        return self._make_request(
            method="POST",
            endpoint=f"/{flow_id}/assets",
            headers=headers,
            data=form_data,
        )

    def publish_flow(
        self,
        flow_id: str,
    ) -> dict[str, bool]:
        """
        Publish a flow.

        Args:
            flow_id: The ID of the flow.

        Return example::

            {
              "success": true
            }
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{flow_id}/publish",
        )

    def delete_flow(
        self,
        flow_id: str,
    ) -> dict[str, bool]:
        """
        Delete a flow.

        Args:
            flow_id: The ID of the flow.

        Return example::

            {
              "success": true
            }
        """

        return self._make_request(
            method="DELETE",
            endpoint=f"/{flow_id}",
        )

    def deprecate_flow(
        self,
        flow_id: str,
    ) -> dict[str, bool]:
        """
        Deprecate a flow.

        Args:
            flow_id: The ID of the flow.

        Return example::

            {
              "success": true
            }
        """

        return self._make_request(
            method="POST",
            endpoint=f"/{flow_id}/deprecate",
        )

    def get_flow(
        self,
        flow_id: str,
        fields: tuple[str, ...] | None = None,
    ) -> dict[str, Any]:
        """
        Get a flow.

        Args:
            flow_id: The ID of the flow.
            fields: The fields to get.

        Return example::

            {
              "id": "<Flow-ID>",
              "name": "<Flow-Name>",
              "status": "DRAFT",
              "categories": [ "LEAD_GENERATION" ],
              "validation_errors": [],
              "json_version": "3.0",
              "data_api_version": "3.0",
              "endpoint_uri": "https://example.com",
              "preview": {
                "preview_url": "https://business.facebook.com/wa/manage/flows/55000..../preview/?token=b9d6.....",
                "expires_at": "2023-05-21T11:18:09+0000"
              },
              "whatsapp_business_account": {
                ...
              },
              "application": {
                ...
              }
            }
        """
        endpoint = f"/{flow_id}"
        if fields:
            endpoint += f"?fields={','.join(fields)}"
        return self._make_request(
            method="GET",
            endpoint=endpoint,
        )

    def get_flows(
        self,
        business_account_id: str,
        fields: tuple[str, ...] | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Get all flows.

        Args:
            business_account_id: The ID of the business account.
            fields: The fields to get.

        Return example::

            {
              "data": [
                {
                  "id": "<Flow-ID>",
                  "name": "<Flow-Name>",
                  "status": "DRAFT",
                  "categories": [ "LEAD_GENERATION" ]
                },
                {
                    "id": "<Flow-ID>",
                    "name": "<Flow-Name>",
                    "status": "DRAFT",
                    "categories": [ "LEAD_GENERATION" ]
                }
              ]
            }
        """
        endpoint = f"/{business_account_id}/flows"
        if fields:
            endpoint += f"?fields={','.join(fields)}"
        return self._make_request(
            method="GET",
            endpoint=endpoint,
        )

    def get_flow_assets(
        self,
        flow_id: str,
    ) -> dict[str, list | dict]:
        """
        Get all assets of a flow.

        Args:
            flow_id: The ID of the flow.

        Return example::

            {
              "data": [
                {
                  "name": "flow.json",
                  "asset_type": "FLOW_JSON",
                  "download_url": "https://scontent.xx.fbcdn.net/m1/v/t0.57323-24/An_Hq0jnfJ..."
                }
              ],
              "paging": {
                "cursors": {
                  "before": "QVFIU...",
                  "after": "QVFIU..."
                }
              }
            }
        """
        return self._make_request(
            method="GET",
            endpoint=f"/{flow_id}/assets",
        )
