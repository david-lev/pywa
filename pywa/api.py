"""The internal API for the WhatsApp client."""

import logging
from typing import Any, TYPE_CHECKING

import httpx

import pywa
from .errors import WhatsAppError

if TYPE_CHECKING:
    from .client import WhatsApp


_logger = logging.getLogger(__name__)


class GraphAPI:
    """Internal methods for the WhatsApp client. Do not use this class directly."""

    def __init__(
        self,
        token: str,
        session: httpx.Client,
        api_version: float,
    ):
        if session.headers.get("Authorization") is not None:
            raise ValueError(
                "You can't use the same httpx.Client for multiple WhatsApp instances!"
            )
        session.base_url = f"https://graph.facebook.com/v{api_version}"
        session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "User-Agent": f"PyWa/{pywa.__version__}",
            }
        )
        self._session = session

    def __str__(self) -> str:
        return f"GraphAPI(session={self._session})"

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
        try:
            res = self._session.request(method=method, url=endpoint, **kwargs)
        except httpx.RequestError as e:
            e.add_note(
                "You may want to provide your own `httpx.Client` instance. e.g. `WhatsApp(session=httpx.Client(timeout=..., proxies=...))`. See https://www.python-httpx.org/api/#client for more information."
            )
            raise
        if res.status_code >= 400:
            raise WhatsAppError.from_dict(error=res.json()["error"], response=res)
        return res.json()

    def get_app_access_token(self, app_id: int, app_secret: str) -> dict[str, str]:
        """
        Get an access token for an app.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/facebook-login/guides/access-tokens/#apptokens>`_.

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

    def set_app_callback_url(
        self,
        app_id: int,
        app_access_token: str,
        callback_url: str,
        verify_token: str,
        fields: tuple[str, ...],
    ) -> dict[str, bool]:
        """
        Set the callback URL for the webhook.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/graph-api/reference/app/subscriptions>`_.

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

    def set_waba_alternate_callback_url(
        self,
        waba_id: str,
        callback_url: str,
        verify_token: str,
    ) -> dict[str, bool]:
        """
        Set an alternate callback URL on a WABA.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/embedded-signup/webhooks/override#set-waba-alternate-callback>`_.

        Return example::

            {
                'success': True
            }

        Args:
            waba_id: The ID of the WhatsApp Business Account.
            callback_url: The URL to set.
            verify_token: The verify token to challenge the webhook with.

        Returns:
            The success of the operation.
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{waba_id}/subscribed_apps",
            json={
                "override_callback_uri": callback_url,
                "verify_token": verify_token,
            },
        )

    def get_waba_subscribed_apps(self, waba_id: str) -> dict[str, list[dict]]:
        """
        Get the subscribed apps of a WABA.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/embedded-signup/webhooks/override#get-waba-alternate-callback>`_.

        Args:
            waba_id: The ID of the WhatsApp Business Account.

        Return example::

            {
                "data": [
                    {
                        "whatsapp_business_api_data": {
                            "link": "https://www.facebook.com/games/?app_id=12345",
                            "name": "My App",
                            "id": "12345"
                        },
                        "override_callback_uri": "https://example.com/wa_webhook"
                    },
                    {
                        "whatsapp_business_api_data": {
                            "link": "https://www.facebook.com/games/?app_id=67890",
                            "name": "My second app",
                            "id": "67890"
                        }
                    }
                ]
            }

        Returns:
            The subscribed apps of the WABA.
        """
        return self._make_request(
            method="GET",
            endpoint=f"/{waba_id}/subscribed_apps",
        )

    def delete_waba_alternate_callback_url(self, waba_id: str) -> dict[str, bool]:
        """
        Delete the callback URL of a WABA.

        Example:

            {
                'success': True
            }

        Args:
            waba_id: The ID of the WhatsApp Business Account.

        Returns:
            The success of the operation.
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{waba_id}/subscribed_apps",
        )

    def set_phone_alternate_callback_url(
        self,
        callback_url: str,
        verify_token: str,
        phone_id: str,
    ) -> dict[str, bool]:
        """
        Set an alternate callback URL on the business phone number.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/embedded-signup/webhooks/override#set-phone-number-alternate-callback>`_.

        Args:
            phone_id: The ID of the phone number to set the callback URL on.
            callback_url: The URL to set.
            verify_token: The verify token to challenge the webhook with.

        Returns:
            The success of the operation.
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{phone_id}/",
            json={
                "webhook_configuration": {
                    "override_callback_uri": callback_url,
                    "verify_token": verify_token,
                }
            },
        )

    def delete_phone_alternate_callback_url(self, phone_id: str) -> dict[str, bool]:
        """
        Delete the alternate callback URL of a phone number.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/embedded-signup/webhooks/override#delete-phone-number-alternate-callback>`_.

        Return example::

            {
                'success': True
            }

        Args:
            phone_id: The ID of the phone number to delete the callback URL from.

        Returns:
            The success of the operation.
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{phone_id}/",
            json={
                "webhook_configuration": {
                    "override_callback_uri": "",
                }
            },
        )

    def set_business_public_key(
        self,
        phone_id: str,
        public_key: str,
    ) -> dict[str, bool]:
        """
        Set the public key of the business.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/whatsapp-business-encryption/#set-business-public-key>`_.

        Return example::

            {
                'success': True
            }

        Args:
            phone_id: The ID of the phone number to set the public key on.
            public_key: The public key to set.

        Returns:
            The success of the operation.
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{phone_id}/whatsapp_business_encryption",
            data={"business_public_key": public_key},
        )

    def upload_media(
        self,
        phone_id: str,
        media: bytes,
        mime_type: str,
        filename: str,
    ) -> dict[str, str]:
        """
        Upload a media file to WhatsApp.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media#upload-media>`_.

        Return example::

            {
              'id':'<MEDIA_ID>'
            }

        Args:
            phone_id: The ID of the phone number to upload the media to.
            media: media bytes or open(path, 'rb') object
            mime_type: The type of the media file
            filename: The name of the media file
        Returns:
            A dict with the ID of the uploaded media file.
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{phone_id}/media",
            files={
                "file": (filename, media, mime_type),
                "messaging_product": (None, "whatsapp"),
                "type": (None, mime_type),
            },
        )

    def get_media_url(self, media_id: str) -> dict:
        """
        Get the URL of a media file.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media#retrieve-media-url>`_.

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
        **httpx_kwargs,
    ) -> tuple[bytes, str | None]:
        """
        Get the bytes of a media file from WhatsApp servers.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media#download-media>`_.

        Args:
            media_url: The URL of the media file (from ``get_media_url``).
            **httpx_kwargs: Additional arguments to pass to the httpx get request.

        Returns:
            The media file bytes and the MIME type (if available).
        """
        headers = self._session.headers.copy()
        res = self._session.get(media_url, headers=headers, **httpx_kwargs)
        res.raise_for_status()
        return res.content, res.headers.get("Content-Type")

    def delete_media(
        self, media_id: str, phone_number_id: str | None = None
    ) -> dict[str, bool]:
        """
        Delete a media file from WhatsApp servers.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media#delete-media>`_.

        Return example::

            {'success': True}

        Args:
            media_id: The ID of the media file.
            phone_number_id: Business phone number ID. If included, the operation will only be processed if the ID matches the ID of the business phone number that the media was uploaded on.

        Returns:
            True if the media file was deleted successfully, False otherwise.
        """
        params = {"phone_number_id": phone_number_id} if phone_number_id else None
        return self._make_request(
            method="DELETE", endpoint=f"/{media_id}", params=params
        )

    def send_raw_request(self, method: str, endpoint: str, **kwargs) -> Any:
        """
        Send a raw request to WhatsApp Cloud API.

        - Use this method if you want to send a request that is not yet supported by pywa.
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
            endpoint=endpoint,
            **kwargs,
        )

    def send_message(
        self,
        sender: str,
        to: str,
        typ: str,
        msg: dict[str, str | list[str]] | tuple[dict],
        reply_to_message_id: str | None = None,
        biz_opaque_callback_data: str | None = None,
    ) -> dict[str, dict | list]:
        """
        Send a message to a WhatsApp user.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/messages>`_.

        Args:
            sender: The phone id to send the message from.
            to: The phone number to send the message to.
            typ: The type of the message (e.g. ``text``, ``image``, etc.).
            msg: The message object to send.
            reply_to_message_id: The ID of the message to reply to.
            biz_opaque_callback_data: The tracker to send with the message.

        Returns:
            The response from the WhatsApp Cloud API.
        """
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": typ,
            typ: msg,
        }
        if reply_to_message_id:
            data["context"] = {"message_id": reply_to_message_id}
        if biz_opaque_callback_data:
            data["biz_opaque_callback_data"] = biz_opaque_callback_data
        return self._make_request(
            method="POST",
            endpoint=f"/{sender}/messages",
            json=data,
        )

    def send_marketing_message(
        self,
        sender: str,
        to: str,
        template: dict[str, str | list[str]],
        reply_to_message_id: str | None = None,
        message_activity_sharing: bool | None = None,
        biz_opaque_callback_data: str | None = None,
    ) -> dict[str, dict | list]:
        """
        Send marketing template messages via MM Lite API.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/marketing-messages-lite-api/sending-messages#sending-messages>`_.


        Args:
            sender: The phone id to send the message from.
            to: The phone number to send the message to.
            template: The template object to send.
            reply_to_message_id: The ID of the message to reply to.
            message_activity_sharing: Toggles on / off sharing message activities (e.g. message read) for that specific marketing message to Meta to help optimize marketing messages.
            biz_opaque_callback_data: The tracker to send with the message.

        Returns:
            The response from the WhatsApp Cloud API.
        """
        body = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "template",
            "template": template,
        }
        if reply_to_message_id:
            body["context"] = {"message_id": reply_to_message_id}
        if message_activity_sharing is not None:
            body["message_activity_sharing"] = message_activity_sharing
        if biz_opaque_callback_data:
            body["biz_opaque_callback_data"] = biz_opaque_callback_data
        return self._make_request(
            method="POST",
            endpoint=f"/{sender}/marketing_messages",
            json=body,
        )

    def register_phone_number(
        self,
        phone_id: str,
        pin: str,
        data_localization_region: str = None,
    ) -> dict[str, bool]:
        """
        Register a phone number.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/registration#register>`_.

        Return example:
            {
                'success': True,
            }

        Args:
            phone_id: The ID of the phone number to register.
            pin: The pin to register the phone number with.
            data_localization_region: The region to localize the data (Value must be a 2-letter ISO 3166 country code (e.g. IN) indicating the country where you want data-at-rest to be stored).

        Returns:
            The success of the operation.
        """

        return self._make_request(
            method="POST",
            endpoint=f"/{phone_id}/register",
            json={
                "messaging_product": "whatsapp",
                "pin": pin,
                **(
                    {"data_localization_region": data_localization_region}
                    if data_localization_region
                    else {}
                ),
            },
        )

    def deregister_phone_number(
        self,
        phone_id: str,
    ) -> dict[str, bool]:
        """
        Deregister a phone number.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/registration/#deregister>`_.

        Return example::

            {
                'success': True
            }

        Args:
            phone_id: The ID of the phone number to deregister.

        Returns:
            The success of the operation.
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{phone_id}/deregister",
        )

    def mark_message_as_read(
        self,
        phone_id: str,
        message_id: str,
    ) -> dict[str, bool]:
        """
        Mark a message as read.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/guides/mark-message-as-read>`_.

        Return example::

            {
                'success': True
            }

        Args:
            phone_id: The ID of the phone number that message belongs to.
            message_id: The ID of the message to mark as read.

        Returns:
            The success of the operation.
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{phone_id}/messages",
            json={
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id,
            },
        )

    def get_waba_info(
        self,
        waba_id: str,
        fields: tuple[str, ...] | None = None,
    ) -> dict[str, Any]:
        """
        Get the WhatsApp Business Account information.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/graph-api/reference/whats-app-business-account>`_.

        Args:
            waba_id: The ID of the WhatsApp Business Account.
            fields: The fields to get. If None, all available fields will be returned.

        Returns:
            The WhatsApp Business Account information.
        """
        return self._make_request(
            method="GET",
            endpoint=f"/{waba_id}",
            params={"fields": ",".join(fields)} if fields else None,
        )

    def get_business_phone_number(
        self,
        phone_id: str,
        fields: tuple[str, ...] | None = None,
    ) -> dict[str, Any]:
        """
        Get the business phone number.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/graph-api/reference/whats-app-business-account-to-number-current-status/>`_.

        Return example::

            {
                'verified_name': 'Test Number',
                'code_verification_status': 'NOT_VERIFIED',
                'display_phone_number': '+1 555-096-7852',
                'quality_rating': 'GREEN',
                'platform_type': 'CLOUD_API',
                'throughput': {'level': 'STANDARD'},
                'id': '277321005464405'

            }
        Args:
            phone_id: The ID of the phone number to get.
            fields: The fields to get.

        Returns:
            The business phone number.
        """
        return self._make_request(
            method="GET",
            endpoint=f"/{phone_id}",
            params={"fields": ",".join(fields)} if fields else None,
        )

    def get_business_phone_numbers(
        self,
        waba_id: str,
        fields: tuple[str, ...] | None = None,
        pagination: dict[str, str] | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Get business phone numbers.

        Return example::

            {
                'data': [
                    {
                        'verified_name': 'Test Number',
                        'code_verification_status': 'NOT_VERIFIED',
                        'display_phone_number': '+1 555-096-7852',
                        'quality_rating': 'GREEN',
                        'platform_type': 'CLOUD_API',
                        'throughput': {'level': 'STANDARD'},
                        'id': '277321005464405'
                    },
                    ...
                ]
            }

        Args:
            waba_id: The ID of the WhatsApp Business Account.
            fields: The fields to get.
            pagination: The pagination of the API.

        Returns:
            The business phone numbers.
        """
        endpoint = f"/{waba_id}/phone_numbers"
        params = {
            k: v
            for k, v in {
                "fields": ",".join(fields) if fields else None,
            }.items()
            if v
        } | (pagination or {})
        return self._make_request(
            method="GET",
            endpoint=endpoint,
            params=params,
        )

    def get_business_phone_number_settings(
        self,
        phone_id: str,
        fields: tuple[str, ...] | None = None,
        include_sip_credentials: bool | None = None,
    ) -> dict[str, Any]:
        """
        Get the business phone number settings.

        Args:
            phone_id: The ID of the phone number to get.
            include_sip_credentials: Whether to include SIP credentials in the response.
            fields: The fields to get. If None, all available fields will be returned.

        Returns:
            The business phone number settings.
        """
        params = {
            "fields": ",".join(fields) if fields else None,
        }
        if include_sip_credentials is not None:
            params["include_sip_credentials"] = include_sip_credentials
        return self._make_request(
            method="GET",
            endpoint=f"/{phone_id}/settings",
            params=params,
        )

    def update_business_phone_number_settings(
        self,
        phone_id: str,
        settings: dict[str, Any],
    ) -> dict[str, bool]:
        """
        Update the business phone number settings.

        Args:
            phone_id: The ID of the phone number to update.
            settings: The settings to update.

        Returns:
            The success of the operation.
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{phone_id}/settings",
            json=settings,
        )

    def update_conversational_automation(
        self,
        phone_id: str,
        enable_welcome_message: bool | None = None,
        prompts: tuple[dict] | None = None,
        commands: str | None = None,
    ) -> dict[str, bool]:
        """
        Update the conversational automation settings.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/phone-numbers/conversational-components/#configuring-via-the-api>`_.

        Return example::

            {
                'success': True
            }

        Args:
            phone_id: The ID of the phone number to update.
            enable_welcome_message: Enable the welcome message.
            prompts: The prompts (ice breakers) to set.
            commands: The commands to set.

        Returns:
            The success of the operation.
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{phone_id}/conversational_automation",
            json={
                k: v
                for k, v in {
                    "enable_welcome_message": enable_welcome_message,
                    "prompts": prompts,
                    "commands": commands,
                }.items()
                if v is not None
            },
        )

    def update_display_name(
        self,
        phone_id: str,
        new_display_name: str,
    ) -> dict[str, bool]:
        """
        Update the display name of the business phone number.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/phone-numbers#updating-display-name-via-api>`_.

        Return example::

            {
                'success': True
            }

        Args:
            phone_id: The ID of the phone number to update.
            new_display_name: The new display name to set.
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{phone_id}",
            json={
                "new_display_name": new_display_name,
                "messaging_product": "whatsapp",
            },
        )

    def get_business_profile(
        self,
        phone_id: str,
        fields: tuple[str, ...] | None = None,
    ) -> dict[str, list[dict[str, str | list[str]]]]:
        """
        Get the business profile.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/business-profiles/#get-business-profile>`_.

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

        Args:
            phone_id: The ID of the phone number to get.
            fields: The fields to get.
        """
        return self._make_request(
            method="GET",
            endpoint=f"/{phone_id}/whatsapp_business_profile",
            params={"fields": ",".join(fields)} if fields else None,
        )

    def update_business_profile(
        self, phone_id: str, data: dict[str, str | list[str]]
    ) -> dict[str, bool]:
        """
        Update the business profile.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/business-profiles/#update-business-profile>`_.

        Args:
            phone_id: The ID of the phone number to update.
            data: The data to update the business profile with.

        Return example::

            {
                "success": True
            }
        """
        data.update(messaging_product="whatsapp")
        return self._make_request(
            method="POST",
            endpoint=f"/{phone_id}/whatsapp_business_profile",
            json=data,
        )

    def get_commerce_settings(
        self, phone_id: str, fields: tuple[str, ...] | None = None
    ) -> dict:
        """
        Get the commerce settings of the business catalog.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/guides/sell-products-and-services/set-commerce-settings/#get-commerce-settings>`_.

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

        Args:
            phone_id: The ID of the phone number to get.
            fields: The fields to get. If None, all fields will be returned.

        Returns:
            The commerce settings of the business catalog.
        """
        return self._make_request(
            method="GET",
            endpoint=f"/{phone_id}/whatsapp_commerce_settings",
            params={"fields": ",".join(fields)} if fields else None,
        )

    def update_commerce_settings(
        self,
        phone_id: str,
        data: dict,
    ) -> dict[str, bool]:
        """
        Change the commerce settings of the business catalog.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/guides/sell-products-and-services/set-commerce-settings>`_.

        Args:
            phone_id: The ID of the phone number to update.
            data: The data to update the commerce settings with.

        Return example::

            {
              "success": True
            }
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{phone_id}/whatsapp_commerce_settings",
            params=data,
        )

    def create_template(
        self,
        waba_id: str,
        template: dict,
    ) -> dict:
        """
        Create a message template.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates#creating-templates>`_.

        Args:
            waba_id: The ID of the WhatsApp Business Account.
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
            endpoint=f"/{waba_id}/message_templates",
            json=template,
        )

    def get_template(
        self,
        template_id: str,
        fields: tuple[str, ...] | None = None,
    ) -> dict[str, Any]:
        """
        Get a message template.

        Example::

            {
              "name": "seasonal_promotion_text_only",
              "status": "APPROVED",
              "id": "564750795574598"
            }

        Args:
            template_id: The ID of the template to get.
            fields: The fields to get. If None, all fields will be returned.

        Returns:
            The template data.
        """
        return self._make_request(
            method="GET",
            endpoint=f"/{template_id}",
            params={"fields": ",".join(fields)} if fields else None,
        )

    def get_templates(
        self,
        waba_id: str,
        fields: tuple[str, ...] | None = None,
        filters: dict[str, Any] | None = None,
        summary_fields: tuple[str, ...] | None = None,
        pagination: dict[str, str] | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Get a list of message templates.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates#retrieve-templates>`_.

        Args:
            waba_id: The ID of the WhatsApp Business Account.
            fields: The fields to get. If None, all fields will be returned.
            filters: Filters to apply to the templates. e.g. {"status": "APPROVED"}.
            summary_fields: Aggregated information a such as counts.
            pagination: Pagination parameters to apply to the templates.

        Returns:
            A dict with the templates data.
        """
        params = {
            "fields": ",".join(fields) if fields else None,
            **(filters if filters else {}),
            **(pagination if pagination else {}),
            **({"summary": ",".join(summary_fields)} if summary_fields else {}),
        }
        return self._make_request(
            method="GET",
            endpoint=f"/{waba_id}/message_templates",
            params={k: v for k, v in params.items() if v is not None},
        )

    def update_template(
        self,
        template_id: str,
        template: dict,
    ) -> dict[str, bool]:
        """
        Update a message template.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates#edit-a-message-template>`_.

        Args:
            template_id: The ID of the template to update.
            template: The template data to update.

        Returns:
            A dict with the success status of the operation.
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{template_id}",
            json=template,
        )

    def delete_template(
        self,
        waba_id: str,
        template_name: str,
        template_id: str | None = None,
    ) -> dict[str, bool]:
        """
        Delete a message template.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates#deleting-templates>`_.

        Args:
            waba_id: The ID of the WhatsApp Business Account.
            template_name: The name of the template to delete.
            template_id: The ID of the template to delete. If not provided, the template will be deleted by name.

        Returns:
            A dict with the success status of the operation.
        """
        return self._make_request(
            method="DELETE",
            endpoint=f"/{waba_id}/message_templates",
            params={
                "name": template_name,
                **({"hsm_id": template_id} if template_id else {}),
            },
        )

    def compare_templates(
        self,
        template_id: str,
        template_ids: tuple[str, ...],
        start: str,
        end: str,
    ) -> dict:
        """
        Compare a template with other templates.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/template-comparison>`_.

        Args:
            template_id: The ID of the template to compare.
            template_ids: The IDs of the templates to compare with.
            start: TUNIX timestamp indicating start of timeframe.
            end: UNIX timestamp indicating end of timeframe.

        Returns:
            A dict with the comparison results.
        """
        return self._make_request(
            method="GET",
            endpoint=f"/{template_id}/compare",
            params={
                "template_ids": ",".join(template_ids),
                "start": start,
                "end": end,
            },
        )

    def migrate_templates(
        self,
        dest_waba_id: str,
        source_waba_id: str,
        page_number: int | None = None,
    ) -> dict:
        """
        Migrate templates from one WABA to another.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/template-migration>`_.

        Args:
            dest_waba_id: The ID of the destination WhatsApp Business Account.
            source_waba_id: The ID of the source WhatsApp Business Account.
            page_number: Indicates amount of templates to migrate as sets of 500. Zero-indexed. For example, to migrate 1000 templates, send one request with this value set to 0 and another request with this value set to 1, in parallel.

        Returns:
            A dict with the migration results.
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{dest_waba_id}/migrate_message_templates",
            params={
                "source_waba_id": source_waba_id,
                **({"page_number": page_number} if page_number is not None else {}),
            },
        )

    def unpause_template(self, template_id: str) -> dict[str, bool | str]:
        """
        Unpause a message template.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/graph-api/reference/whats-app-business-hsm/unpause/>`_.

        Args:
            template_id: The ID of the template to unpause.

        Returns:
            A dict with the success status of the operation.
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{template_id}/unpause",
        )

    def upsert_message_templates(
        self,
        waba_id: str,
        template: dict,
    ) -> dict:
        """
        Bulk update or create authentication templates in multiple languages that include or exclude the optional security and expiration warnings.

        If a template already exists with a matching name and language, the template will be updated with the contents of the request, otherwise, a new template will be created.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/authentication-templates#bulk-management>`_.

        Return example::

            {
                "data": [
                    {
                        "id": "123456789012345",
                        "language": "en_US",
                        "status": "APPROVED"
                    },
                    ...
                ],

        Args:
            waba_id: The ID of the WhatsApp Business Account.
            template: A dict containing the template to create or update to all languages listed in the template.
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{waba_id}/upsert_message_templates",
            json=template,
        )

    def create_flow(
        self,
        waba_id: str,
        name: str,
        categories: tuple[str, ...],
        clone_flow_id: str | None = None,
        endpoint_uri: str | None = None,
        flow_json: str = None,
        publish: bool = None,
    ) -> dict[str, str]:
        """
        Create or clone a flow.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowsapi#create>`_.

        Args:
            waba_id: The ID of the WhatsApp Business Account.
            name: The name of the flow.
            categories: The categories of the flow.
            clone_flow_id: The ID of the flow to clone.
            endpoint_uri: The endpoint URI of the flow.
            flow_json: Flow's JSON encoded as string.
            publish: Whether to publish the flow. Only works if ``flow_json`` is also provided with valid Flow JSON.

        Return example::

            {
               "id": "<Flow-ID>"
               "success": True,
               "validation_errors": [
                {
                  "error": "INVALID_PROPERTY_VALUE" ,
                  "error_type": "FLOW_JSON_ERROR",
                  "message": "Invalid value found for property 'type'.",
                  "line_start": 10,
                  "line_end": 10,
                  "column_start": 21,
                  "column_end": 34,
                  "pointers": [
                   {
                     "line_start": 10,
                     "line_end": 10,
                     "column_start": 21,
                     "column_end": 34,
                     "path": "screens [0].layout.children[0].type"
                   }
                  ]
                }
              ]
            }
        """
        data = {
            "name": name,
            "categories": categories,
            **{
                k: v
                for k, v in {
                    "clone_flow_id": clone_flow_id,
                    "endpoint_uri": endpoint_uri,
                    "flow_json": flow_json,
                    "publish": publish,
                }.items()
                if v is not None
            },
        }
        return self._make_request(
            method="POST",
            endpoint=f"/{waba_id}/flows",
            json=data,
        )

    def update_flow_metadata(
        self,
        flow_id: str,
        name: str | None = None,
        categories: tuple[str, ...] | None = None,
        endpoint_uri: str | None = None,
        application_id: int | None = None,
    ) -> dict[str, bool]:
        """
        Update the metadata of a flow.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowsapi#update>`_.

        Args:
            flow_id: The ID of the flow.
            name: The name of the flow.
            categories: The categories of the flow.
            endpoint_uri: The endpoint URI of the flow.
            application_id: The ID of the application.

        Return example::

            {
              "success": True
            }
        """
        data = {
            **({"name": name} if name else {}),
            **({"endpoint_uri": endpoint_uri} if endpoint_uri else {}),
            **({"categories": categories} if categories else {}),
            **({"application_id": application_id} if application_id else {}),
        }
        return self._make_request(
            method="POST",
            endpoint=f"/{flow_id}",
            json=data,
        )

    def update_flow_json(self, flow_id: str, flow_json: str) -> dict:
        """
        Update the JSON of a flow.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowsapi#update-json>`_.

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
        return self._make_request(
            method="POST",
            endpoint=f"/{flow_id}/assets",
            files={
                "file": ("flow.json", flow_json, "application/json"),
                "name": (None, "flow.json"),
                "asset_type": (None, "FLOW_JSON"),
                "messaging_product": (None, "whatsapp"),
            },
        )

    def publish_flow(
        self,
        flow_id: str,
    ) -> dict[str, bool]:
        """
        Publish a flow.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowsapi#publish>`_.

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

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowsapi#delete>`_.

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

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowsapi#deprecate>`_.

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

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowsapi#details>`_.

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
        waba_id: str,
        fields: tuple[str, ...] | None = None,
        pagination: dict[str, str] | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Get all flows.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowsapi#list>`_.

        Args:
            waba_id: The ID of the WhatsApp Business Account.
            fields: The fields to get.
            pagination: The pagination of the API.

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
        endpoint = f"/{waba_id}/flows"
        params = {
            k: v
            for k, v in {
                "fields": ",".join(fields) if fields else None,
            }.items()
            if v
        } | (pagination or {})
        return self._make_request(
            method="GET",
            endpoint=endpoint,
            params=params,
        )

    def get_flow_assets(
        self,
        flow_id: str,
        pagination: dict[str, str] | None = None,
    ) -> dict[str, list | dict]:
        """
        Get all assets of a flow.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowsapi#asset-list>`_.

        Args:
            flow_id: The ID of the flow.
            pagination: The pagination of the API.

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
            endpoint=f"/{flow_id}/assets?fields=name,asset_type,download_url",
            params=pagination,
        )

    def migrate_flows(
        self,
        dest_waba_id: str,
        source_waba_id: str,
        source_flow_names: tuple[str, ...],
    ) -> dict[str, list[dict[str, str]]]:
        """
        Migrate Flows from one WhatsApp Business Account (WABA) to another.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowsapi/#migrate>`_.

        Migration doesn't move the source Flows, it creates copies of them with the same names in the destination WABA.

        - You can specify specific Flow names to migrate, or choose to migrate all Flows in source WABA.
        - Flows can only be migrated between WABAs owned by the same Meta business.
        - If a Flow exists with the same name in the destination WABA, it will be skipped and the API will return an error message for that Flow. Other Flows in the same request will be copied.
        - The migrated Flow will be published if the original Flow is published, otherwise it will be in draft state.
        - New Flows under destination WABA will have new Flow IDs.


        Return example::

            {
              "migrated_flows": [
                {
                  "source_name": "appointment-booking",
                  "source_id": "1234",
                  "migrated_id": "5678"
                }
              ],
              "failed_flows": [
                {
                  "source_name": "lead-gen",
                  "error_code": "4233041",
                  "error_message": "Flows Migration Error: Flow with the same name exists in destination WABA."
                }
              ]
            }

        Args:
            dest_waba_id: Destination WhatsApp Business Account ID.
            source_waba_id: Source WhatsApp Business Account ID.
            source_flow_names: Tuple of specific Flow names to migrate. If not specified, it will migrate all flows in source WABA. Only 100 Flows can be migrated in a request.

        Returns:
            Result of the migration request.
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{dest_waba_id}/migrate_flows?source_waba_id={source_waba_id}&source_flow_names={','.join(source_flow_names)}",
        )

    def create_qr_code(
        self, phone_id: str, prefilled_message: str, generate_qr_image: str
    ) -> dict:
        """
        Create a QR code.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/qr-codes/#create-qr-code>`_.

        Args:
            phone_id: The ID of the phone number to create the QR code on.
            prefilled_message: The prefilled message to set.
            generate_qr_image: PNG or SVG

        Return example::

            {
              "code": "4O4YGZEG3RIVE1",
              "prefilled_message": "Cyber Monday 1",
              "deep_link_url": "https://wa.me/message/4O4YGZEG3RIVE1",
              "qr_image_url": "https://scontent-iad3-2.xx.fbcdn.net/..."
            }
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{phone_id}/message_qrdls",
            json={
                "prefilled_message": prefilled_message,
                "generate_qr_image": generate_qr_image,
            },
        )

    def get_qr_code(
        self,
        phone_id: str,
        code: str,
        fields: tuple[str, ...] | None = None,
    ) -> dict:
        """
        Get a QR code.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/qr-codes/#get-qr-code>`_.

        Args:
            phone_id: The ID of the phone number to get the QR code from.
            code: The code of the QR code.
            fields: The fields to get. If None, default fields will be returned.

        Return example::

            {
              "data": [
                {
                  "code": "4O4YGZEG3RIVE1",
                  "prefilled_message": "Cyber Monday",
                  "deep_link_url": "https://wa.me/message/4O4YGZEG3RIVE1"
                }
              ]
            }
        """
        return self._make_request(
            method="GET",
            endpoint=f"/{phone_id}/message_qrdls/{code}",
            params={"fields": ",".join(fields)} if fields else None,
        )

    def get_qr_codes(
        self,
        phone_id: str,
        fields: tuple[str, ...] | None = None,
        pagination: dict[str, str] | None = None,
    ) -> dict:
        """
        Get all QR codes.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/qr-codes/#get-qr-codes>`_.

        Return example::

            {
              "data": [
                {
                  "code": "4O4YGZEG3RIVE1",
                  "prefilled_message": "Cyber Monday 1",
                  "deep_link_url": "https://wa.me/message/4O4YGZEG3RIVE1",
                  "qr_image_url": "https://scontent-iad3-2.xx.fbcdn.net/..."
                }
              ],
                "paging": {
                    "cursors": {
                    "before": "QVFIU...",
                    "after": "QVFIU..."
                    }
                }
            }

        Args:
            phone_id: The ID of the phone number to get the QR codes from.
            fields: The fields to get. If None, default fields will be returned.
            pagination: The pagination parameters.
        """
        return self._make_request(
            method="GET",
            endpoint=f"/{phone_id}/message_qrdls",
            params={
                k: v
                for k, v in {
                    "fields": ",".join(fields) if fields else None,
                    **(pagination or {}),
                }.items()
                if v is not None
            },
        )

    def update_qr_code(
        self,
        phone_id: str,
        code: str,
        prefilled_message: str,
    ) -> dict:
        """
        Update a QR code.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/qr-codes/#update-qr-code>`_.

        Return example::

            {
              "code": "4O4YGZEG3RIVE1",
              "prefilled_message": "Cyber Tuesday",
              "deep_link_url": "https://wa.me/message/4O4YGZEG3RIVE1"
            }

        Args:
            phone_id: The ID of the phone number to update the QR code on.
            code: The code of the QR code.
            prefilled_message: The prefilled message to set.
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{phone_id}/message_qrdls",
            json={"code": code, "prefilled_message": prefilled_message},
        )

    def delete_qr_code(self, phone_id: str, code: str):
        """
        Delete a QR code.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/qr-codes/#delete-qr-code>`_.

        Return example::

            {
              "success": True
            }

        Args:
            phone_id: The ID of the phone number to delete the QR code from.
            code: The code of the QR code.
        """
        return self._make_request(
            method="DELETE",
            endpoint=f"/{phone_id}/message_qrdls/{code}",
        )

    def set_indicator(
        self, phone_id: str, message_id: str, typ: str
    ) -> dict[str, bool]:
        """
        Set a typing indicator.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/typing-indicators>`_.

        Return example::

            {
                'success': True
            }

        Args:
            phone_id: The ID of the phone number to set the typing indicator on.
            message_id: The ID of the message in the conversation to set the typing indicator on.
            typ: The type of indicator to set (currently only "text" is supported).

        Returns:
            The success of the operation.
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{phone_id}/messages",
            json={
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id,
                "typing_indicator": {
                    "type": typ,
                },
            },
        )

    def block_users(
        self,
        phone_id: str,
        users: tuple[str, ...],
    ) -> dict:
        """
        Block users from sending messages to the business.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/block-users#block-users-2>`_.

        Return example::

            {
                'messaging_product': 'whatsapp',
                'block_users': {
                    'removed_users': [
                        {'input': '123456789', 'wa_id': '123456789'}
                    ]
                }
            }

        Args:
            phone_id: The ID of the phone number to block users on.
            users: The list of phone numbers/wa_ids to block.

        Returns:
            The response from the WhatsApp Cloud API.
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{phone_id}/block_users",
            json={
                "messaging_product": "whatsapp",
                "block_users": [{"user": user} for user in users],
            },
        )

    def unblock_users(
        self,
        phone_id: str,
        users: tuple[str, ...],
    ) -> dict:
        """
        Unblock users from sending messages to the business.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/block-users#unblock-users>`_.

        Return example::

            {
                'messaging_product': 'whatsapp',
                'block_users': {
                    'removed_users': [
                        {'input': '123456789', 'wa_id': '123456789'}
                    ]
                }

        Args:
            phone_id: The ID of the phone number to unblock users on.
            users: The list of phone numbers/wa_ids to unblock.

        Returns:
            The response from the WhatsApp Cloud API.
        """
        return self._make_request(
            method="DELETE",
            endpoint=f"/{phone_id}/block_users",
            json={
                "messaging_product": "whatsapp",
                "block_users": [{"user": user} for user in users],
            },
        )

    def get_blocked_users(self, phone_id: str, pagination: dict | None = None) -> dict:
        """
        Get the list of blocked users.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/block-users#get-list-of-blocked-numbers>`_.

        Args:
            phone_id: The ID of the phone number to get the blocked users from.
            pagination: The pagination parameters.

        Return example::

            {
                'data': [
                    {'messaging_product': 'whatsapp', 'wa_id': '1234567890'}
                ],
                'paging': {
                    'cursors': {
                        'before': 'eyJvZAmZAzZAXQiOjAsIn',
                        'after': 'I6IjE3Mzc1ODA5MjUwMTk0NTIifQZDZD',
                    }
                }
            }

        Returns:
            The response from the WhatsApp Cloud API.
        """
        return self._make_request(
            method="GET",
            endpoint=f"/{phone_id}/block_users",
            params=pagination,
        )

    def create_upload_session(
        self,
        app_id: str,
        file_name: str,
        file_length: int,
        file_type: str,
    ) -> dict[str, str]:
        """
        Create an upload session for a file.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/graph-api/guides/upload#step-1>`_.

        Args:
            app_id: The ID of the app to create the upload session for.
            file_name: The name of the file to upload.
            file_length: File size in bytes
            file_type: The file's MIME type. Valid values are: ``application/pdf``, ``image/jpeg``, ``image/jpg``, ``image/png``, and ``video/mp4``.

        Returns:
            The ID of the upload session
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{app_id}/uploads?file_name={file_name}&file_length={file_length}&file_type={file_type}",
        )

    def upload_file(
        self,
        upload_session_id: str,
        file: bytes,
        file_offset: int = 0,
    ) -> dict[str, str]:
        """
        Upload a file to an upload session.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/graph-api/guides/upload#step-2>`_.

        Args:
            upload_session_id: The ID of the upload session to upload the file to (This is the ID returned by the ``create_upload_session`` method).
            file: The file to upload (as bytes).
            file_offset: The offset in the file to start uploading from. you can use this to resume an interrupted upload (use `get_upload_session` to get the current offset).

        Returns:
            The file handle of the uploaded file.
        """
        return self._make_request(
            method="POST",
            endpoint=f"/{upload_session_id}",
            headers={
                "file_offset": str(file_offset),
            },
            data=file,
        )

    def get_upload_session(
        self,
        upload_session_id: str,
    ) -> dict[str, str | int]:
        """
        Get the status of an upload session (resuming an interrupted upload).

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/graph-api/guides/upload#resume-an-interrupted-upload>`_.

        Args:
            upload_session_id: The ID of the upload session.

        Returns:
            The status of the upload session (ID and current offset)
        """
        return self._make_request(
            method="GET",
            endpoint=f"/{upload_session_id}",
        )

    def get_call_permissions(self, phone_id: str, user_wa_id: str) -> dict:
        """
        Get call permissions for a user.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/user-call-permissions>`_.

        Return example::

            {
              "messaging_product": "whatsapp",
              "permission": {
                "status": "temporary",
                "expiration_time": 1745343479
              },
              "actions": [
                {
                  "action_name": "send_call_permission_request",
                  "can_perform_action": True,
                  "limits": [
                    {
                      "time_period": "PT24H",
                      "max_allowed": 1,
                      "current_usage": 0,
                    },
                    {
                      "time_period": "P7D",
                      "max_allowed": 2,
                      "current_usage": 1,
                    }
                  ]
                },
                {
                  "action_name": "start_call",
                  "can_perform_action": False,
                  "limits": [
                    {
                      "time_period": "PT24H",
                      "max_allowed": 5,
                      "current_usage": 5,
                      "limit_expiration_time": 1745622600,
                    }
                  ]
                }
              }
            }

        Args:
            phone_id: The ID of the phone number to get call permissions for.
            user_wa_id: The WhatsApp ID of the user to check permissions for.

        Returns:
            The response from the WhatsApp Cloud API.
        """
        return self._make_request(
            method="GET",
            endpoint=f"/{phone_id}/call_permissions",
            params={"user_wa_id": user_wa_id},
        )

    def initiate_call(
        self,
        phone_id: str,
        to: str,
        sdp: dict[str, str],
        biz_opaque_callback_data: str | None = None,
    ) -> dict[str, str | bool]:
        """
        Initiate a call.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/user-initiated-calls#initiate-call>`_.

        Return example::

            {
              "messaging_product": "whatsapp",
              "calls" : [{
                 "id" : "wacid.ABGGFjFVU2AfAgo6V",
               }]
            }

        Args:
            phone_id: The ID of the phone number to initiate the call on.
            to: The number being called (callee).
            sdp: The SDP info of the device on the other end of the call. The SDP must be compliant with RFC 8866.
            biz_opaque_callback_data: An arbitrary string you can pass in that is useful for tracking and logging purposes.

        Returns:
            The response from the WhatsApp Cloud API containing the call ID.
        """
        return self._make_request(
            method="POST",
            endpoint=f"{phone_id}/calls",
            json={
                "messaging_product": "whatsapp",
                "to": to,
                "action": "connect",
                "session": sdp,
                **(
                    {"biz_opaque_callback_data": biz_opaque_callback_data}
                    if biz_opaque_callback_data
                    else {}
                ),
            },
        )

    def pre_accept_call(
        self, phone_id: str, call_id: str, sdp: dict[str, str] | None = None
    ) -> dict[str, str | bool]:
        """
        Pre-accept a call.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/user-initiated-calls#pre-accept-call>`_.

        Return example::

            {
                "messaging_product": "whatsapp",
                "success": True
            }

        Args:
            phone_id: The ID of the phone number to pre-accept the call on.
            call_id: The ID of the call to pre-accept.
            sdp: The SDP info of the device on the other end of the call. The SDP must be compliant with RFC 8866.

        Returns:
            The response from the WhatsApp Cloud API.
        """
        return self._make_request(
            method="POST",
            endpoint=f"{phone_id}/calls",
            json={
                "messaging_product": "whatsapp",
                "call_id": call_id,
                "action": "pre_accept",
                **({"session": sdp} if sdp else {}),
            },
        )

    def accept_call(
        self,
        phone_id: str,
        call_id: str,
        sdp: dict[str, str] | None = None,
        biz_opaque_callback_data: str | None = None,
    ) -> dict[str, str | bool]:
        """
        Accept a call.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/user-initiated-calls#accept-call>`_.

        Return example::

            {
                "messaging_product": "whatsapp",
                "success": True
            }

        Args:
            phone_id: The ID of the phone number to accept the call on.
            call_id: The ID of the call to accept.
            sdp: The SDP info of the device on the other end of the call. The SDP must be compliant with RFC 8866.
            biz_opaque_callback_data: An arbitrary string you can pass in that is useful for tracking and logging purposes.

        Returns:
            The response from the WhatsApp Cloud API.
        """
        return self._make_request(
            method="POST",
            endpoint=f"{phone_id}/calls",
            json={
                "messaging_product": "whatsapp",
                "call_id": call_id,
                "action": "accept",
                **({"session": sdp} if sdp else {}),
                **(
                    {"biz_opaque_callback_data": biz_opaque_callback_data}
                    if biz_opaque_callback_data
                    else {}
                ),
            },
        )

    def reject_call(self, phone_id: str, call_id: str) -> dict[str, bool]:
        """
        Reject a call.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/user-initiated-calls#reject-call>`_.

        Return example::

            {
                "messaging_product": "whatsapp",
                "success": True
            }

        Args:
            phone_id: The ID of the phone number to reject the call on.
            call_id: The ID of the call to reject.

        Returns:
            The response from the WhatsApp Cloud API.
        """
        return self._make_request(
            method="POST",
            endpoint=f"{phone_id}/calls",
            json={
                "messaging_product": "whatsapp",
                "call_id": call_id,
                "action": "reject",
            },
        )

    def terminate_call(self, phone_id: str, call_id: str) -> dict[str, bool]:
        """
        Terminate a call.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/calling/user-initiated-calls#terminate-call>`_.

        Return example::

            {
                "messaging_product": "whatsapp",
                "success": True
            }

        Args:
            phone_id: The ID of the phone number to terminate the call on.
            call_id: The ID of the call to terminate.

        Returns:
            The response from the WhatsApp Cloud API.
        """
        return self._make_request(
            method="POST",
            endpoint=f"{phone_id}/calls",
            json={
                "messaging_product": "whatsapp",
                "call_id": call_id,
                "action": "terminate",
            },
        )
