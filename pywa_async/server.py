"""This module contains the Server class, which is used to set up a webhook for receiving incoming updates."""

from pywa.server import *  # noqa MUST BE IMPORTED FIRST
from pywa.server import Server, _VERIFY_TIMEOUT_SEC  # noqa MUST BE IMPORTED FIRST

import logging
import threading
from typing import TYPE_CHECKING

from . import utils
from .errors import WhatsAppError
from .handlers import Handler
from .utils import FastAPI, Flask

if TYPE_CHECKING:
    from .client import WhatsApp


_logger = logging.getLogger(__name__)


class Server(Server):
    """This class is used internally by the :class:`WhatsApp` client to set up a webhook for receiving incoming
    requests."""

    def __init__(
        self: "WhatsApp",
        server: Flask | FastAPI | None,
        webhook_endpoint: str,
        callback_url: str | None,
        fields: tuple[str, ...] | None,
        app_id: int | None,
        app_secret: str | None,
        verify_token: str | None,
        verify_timeout: int | None,
        business_private_key: str | None,
        business_private_key_password: str | None,
        flows_request_decryptor: utils.FlowRequestDecryptor | None,
        flows_response_encryptor: utils.FlowResponseEncryptor | None,
        max_workers: int,
    ):
        if server is None:
            self._server = None
            return

        super().__init__(
            server=server,
            webhook_endpoint=webhook_endpoint,
            callback_url=callback_url,
            fields=fields,
            app_id=app_id,
            app_secret=app_secret,
            verify_token=verify_token,
            verify_timeout=verify_timeout,
            business_private_key=business_private_key,
            business_private_key_password=business_private_key_password,
            flows_request_decryptor=flows_request_decryptor,
            flows_response_encryptor=flows_response_encryptor,
            max_workers=max_workers,
            auto_register_callback_url=False,
        )

        if callback_url is not None:
            threading.Timer(
                interval=(verify_timeout - _VERIFY_TIMEOUT_SEC)
                if verify_timeout is not None and verify_timeout > _VERIFY_TIMEOUT_SEC
                else 0,
                function=lambda: self._loop.create_task(
                    self._register_callback_url(
                        callback_url=callback_url,
                        app_id=app_id,
                        app_secret=app_secret,
                        verify_token=verify_token,
                        fields=fields,
                    )
                ),
            ).start()

    async def _register_callback_url(
        self: "WhatsApp",
        callback_url: str,
        app_id: int,
        app_secret: str,
        verify_token: str,
        fields: tuple[str, ...] | None,
    ) -> None:
        full_url = f"{callback_url.rstrip('/')}/{self._webhook_endpoint.lstrip('/')}"
        try:
            app_access_token = await self.api.get_app_access_token(
                app_id=app_id, app_secret=app_secret
            )
            # noinspection PyProtectedMember
            res = await self.api.set_app_callback_url(
                app_id=app_id,
                app_access_token=app_access_token["access_token"],
                callback_url=full_url,
                verify_token=verify_token,
                fields=tuple(fields or Handler._fields_to_subclasses().keys()),
            )
            if not res["success"]:
                raise RuntimeError("Failed to register callback URL.")
            _logger.info("Callback URL '%s' registered successfully", full_url)
        except WhatsAppError as e:
            raise RuntimeError(f"Failed to register callback URL '{full_url}'") from e
