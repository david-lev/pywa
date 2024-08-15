"""The internal API for the WhatsApp client."""

import importlib
import logging
from typing import Any, TYPE_CHECKING

import httpx

import pywa
from . import utils
from .errors import WhatsAppError

if TYPE_CHECKING:
    from .client import WhatsApp


_logger = logging.getLogger(__name__)


class WhatsAppCloudApi:
    """Internal methods for the WhatsApp client. Do not use this class directly."""

    def __init__(
        self,
        token: str,
        session: httpx.Client,
        base_url: str,
        api_version: float,
    ):
        self._session = self._setup_session(session, token)
        self._base_url = f"{base_url}/v{api_version}"

        # backward compatibility with requests.Session
        self._is_requests_session, _ = utils.is_requests_and_err(session)
        if self._is_requests_session:
            _logger.warning(
                "Using `requests.Session` is deprecated and will be removed in future versions. "
                "Please use `httpx.Client` instead."
            )

    @staticmethod
    def _setup_session(session, token: str) -> httpx.Client:
        if session.headers.get("Authorization") is not None:
            raise ValueError(
                "You can't use the same httpx.Client for multiple WhatsApp instances!"
            )
        session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "User-Agent": f"PyWa/{pywa.__version__}",
            }
        )
        return session

    def __str__(self) -> str:
        return f"WhatsAppCloudApi(session={self._session})"

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

    def set_waba_callback_url(
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

    def set_phone_callback_url(
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
            **(
                dict(
                    files=[("file", (filename, media, mime_type))],
                    data={"messaging_product": "whatsapp"},
                )
                if self._is_requests_session
                else dict(
                    files={
                        "file": (filename, media, mime_type),
                        "messaging_product": (None, "whatsapp"),
                        "type": (None, mime_type),
                    }
                )
            ),
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
        **kwargs,
    ) -> tuple[bytes, str | None]:
        """
        Get the bytes of a media file from WhatsApp servers.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media#download-media>`_.

        Args:
            media_url: The URL of the media file (from ``get_media_url``).
            **kwargs: Additional arguments to pass to the request.

        Returns:
            The media file bytes and the MIME type (if available).
        """
        headers = self._session.headers.copy()
        res = self._session.get(media_url, headers=headers, **kwargs)
        res.raise_for_status()
        return res.content, res.headers.get("Content-Type")

    def delete_media(self, media_id: str) -> dict[str, bool]:
        """
        Delete a media file from WhatsApp servers.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media#delete-media>`_.

        Return example::

            {'success': True}

        Args:
            media_id: The ID of the media file.

        Returns:
            True if the media file was deleted successfully, False otherwise.
        """
        return self._make_request(method="DELETE", endpoint=f"/{media_id}")

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
            params={
                k: v
                for k, v in {
                    "enable_welcome_message": enable_welcome_message,
                    "prompts": prompts,
                    "commands": commands,
                }.items()
                if v is not None
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

    def get_commerce_settings(self, phone_id: str) -> dict[str, list[dict]]:
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

        Returns:
            The commerce settings of the business catalog.
        """
        return self._make_request(
            method="GET",
            endpoint=f"/{phone_id}/whatsapp_commerce_settings",
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
        template: dict[str, str | list[str]],
    ) -> dict[str, str]:
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

    def create_flow(
        self,
        waba_id: str,
        name: str,
        categories: tuple[str, ...],
        clone_flow_id: str | None = None,
        endpoint_uri: str | None = None,
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

        Return example::

            {
              "id": "<Flow-ID>"
            }
        """
        data = {
            "name": name,
            "categories": categories,
            **({"clone_flow_id": clone_flow_id} if clone_flow_id else {}),
            **({"endpoint_uri": endpoint_uri} if endpoint_uri else {}),
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
            **(
                dict(
                    files=[("file", ("flow.json", flow_json, "application/json"))],
                    data={
                        "name": "flow.json",
                        "asset_type": "FLOW_JSON",
                        "messaging_product": "whatsapp",
                    },
                )
                if self._is_requests_session
                else dict(
                    files={
                        "file": ("flow.json", flow_json, "application/json"),
                        "name": (None, "flow.json"),
                        "asset_type": (None, "FLOW_JSON"),
                        "messaging_product": (None, "whatsapp"),
                    }
                )
            ),
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
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Get all flows.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowsapi#list>`_.

        Args:
            waba_id: The ID of the WhatsApp Business Account.
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
        endpoint = f"/{waba_id}/flows"
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

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowsapi#asset-list>`_.

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
    ) -> dict:
        """
        Get a QR code.

        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/qr-codes/#get-qr-code>`_.

        Args:
            phone_id: The ID of the phone number to get the QR code from.
            code: The code of the QR code.

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
        )

    def get_qr_codes(self, phone_id: str) -> dict:
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
              ]
            }

        Args:
            phone_id: The ID of the phone number to get the QR codes from.
        """
        return self._make_request(
            method="GET",
            endpoint=f"/{phone_id}/message_qrdls",
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
