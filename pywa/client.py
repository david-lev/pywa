import requests
from pywa.api import WhatsAppCloudApi
from pywa.types import Button, SectionList


class WhatsApp(WhatsAppCloudApi):
    def __init__(
        self,
        phone_id: str,
        token: str,
        verify_token: str | None = None,
        base_url: str = "https://graph.facebook.com",
        api_version: float = 17.0,
        session: requests.Session | None = None,
    ):
        """
        Initialize the WhatsApp client.

        >>> from pywa import WhatsApp
        >>> wa = WhatsApp(phone_id="100944", token="EAADKQl9oJxx")

        Args:
            phone_id: The phone ID of the WhatsApp account.
            token: The token of the WhatsApp account.
            verify_token: The verify token if you want to receive messages from WhatsApp.
            base_url: The base URL of the WhatsApp API. Default: `https://graph.facebook.com`
            api_version: The API version of the WhatsApp API. Default: 17.0
            session: The session to use for requests. Default: New session.
        """
        self.phone_id = phone_id
        self.token = token
        self.verify_token = verify_token
        self._session = session or requests.Session()
        self._base_url = f"{base_url}/v{api_version}"
        self._session.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

    def send_message(
        self,
        to: str,
        text: str,
        preview_url: bool = False,
        reply_to_message_id: str | None = None,
        keyboard: list[Button] | SectionList | None = None,
    ):
        if not keyboard:
            return self._send_text_message(
                to=to,
                text=text,
                preview_url=preview_url,
                reply_to_message_id=reply_to_message_id,
            )

    def send_image(
        self,
        to: str,
        image: str | bytes,
        caption: str | None = None,
        preview_url: bool = False,
        reply_to_message_id: str | None = None,
        keyboard: list[list] | None = None,
    ):
        raise NotImplementedError

    def send_video(
        self,
        to: str,
        video: str | bytes,
        caption: str | None = None,
        preview_url: bool = False,
        reply_to_message_id: str | None = None,
        keyboard: list[list] | None = None,
    ):
        raise NotImplementedError

    def send_document(
        self,
        to: str,
        document: str | bytes,
        filename: str | None = None,
        caption: str | None = None,
        preview_url: bool = False,
        reply_to_message_id: str | None = None,
        keyboard: list[list] | None = None,
    ):
        raise NotImplementedError

    def send_audio(
        self,
        to: str,
        audio: str | bytes,
        caption: str | None = None,
        preview_url: bool = False,
        reply_to_message_id: str | None = None,
        keyboard: list[list] | None = None,
    ):
        raise NotImplementedError

    def send_reaction(
        self,
        to: str,
        emoji: str,
        message_id: str,
    ):
        raise NotImplementedError

    def send_location(
        self,
        to: str,
        latitude: float,
        longitude: float,
        name: str | None = None,
        address: str | None = None,
    ):
        raise NotImplementedError
