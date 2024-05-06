"""This module contains the types related to WhatsApp Flows."""

from __future__ import annotations
from pywa.types.flows import *  # noqa MUST BE IMPORTED FIRST

import logging
import dataclasses
import datetime
import json
import pathlib
from typing import Iterable, TYPE_CHECKING, Any, BinaryIO

from .base_update import BaseUserUpdate  # noqa
from .others import (
    WhatsAppBusinessAccount,
    FacebookApplication,
    MessageType,
    Metadata,
    User,
    ReplyToMessage,
)

if TYPE_CHECKING:
    from pywa import WhatsApp

_logger = logging.getLogger(__name__)


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class FlowCompletion(BaseUserUpdate):
    """
    A flow completion message. This update arrives when a user completes a flow.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/gettingstarted/receiveflowresponse>`_.

    Attributes:
        id: The message ID (If you want to reply to the message, use ``message_id_to_reply`` instead).
        metadata: The metadata of the message (to which phone number it was sent).
        type: The message type (Always ``MessageType.INTERACTIVE``).
        from_user: The user who sent the message.
        timestamp: The timestamp when the message was sent.
        reply_to_message: The message to which this message is a reply to.
        body: The body of the message.
        token: The token of the flow. can be ``None`` in some cases :|
        response: The response from the flow.
    """

    id: str
    type: MessageType
    metadata: Metadata
    from_user: User
    timestamp: datetime.datetime
    reply_to_message: ReplyToMessage | None
    body: str
    token: str | None
    response: dict[str, Any]

    @classmethod
    def from_update(cls, client: WhatsApp, update: dict) -> FlowCompletion:
        msg = (value := update["entry"][0]["changes"][0]["value"])["messages"][0]
        response = json.loads(msg["interactive"]["nfm_reply"]["response_json"])
        if (flow_token := response.get("flow_token")) is None:
            _logger.warning(
                "A flow completion message without flow token is received, This is a known issue on iOS devices."
            )
        return cls(
            _client=client,
            raw=update,
            id=msg["id"],
            type=MessageType(msg["type"]),
            metadata=Metadata.from_dict(value["metadata"]),
            from_user=User.from_dict(value["contacts"][0]),
            timestamp=datetime.datetime.fromtimestamp(int(msg["timestamp"])),
            reply_to_message=ReplyToMessage.from_dict(msg["context"]),
            body=msg["interactive"]["nfm_reply"]["body"],
            token=flow_token,
            response=response,
        )


@dataclasses.dataclass(slots=True, kw_only=True)
class FlowDetails:
    """
    Represents the details of a flow.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowsapi#details>`_.

    Attributes:
        id: The ID of the flow.
        name: The name of the flow.
        status: The status of the flow.
        updated_at: The last time the flow was updated (name, categories, endpoint_uri, json, etc.).
        json_version: The version of the flow JSON.
        data_api_version: The version to use during communication with the WhatsApp Flows Data Endpoint.
        categories: The categories of the flow.
        validation_errors: The validation errors of the flow.
        endpoint_uri: The endpoint URI of the flow.
        preview: The preview of the flow.
        whatsapp_business_account: The WhatsApp Business Account that owns the flow.
        application: The application that owns the flow.
    """

    _client: WhatsApp = dataclasses.field(repr=False, hash=False, compare=False)
    id: str
    name: str
    status: FlowStatus
    json_version: str | None
    data_api_version: str | None
    categories: tuple[FlowCategory, ...]
    validation_errors: tuple[FlowValidationError, ...] | None
    endpoint_uri: str | None
    preview: FlowPreview | None
    whatsapp_business_account: WhatsAppBusinessAccount | None
    application: FacebookApplication | None
    updated_at: datetime.datetime | None = None

    @classmethod
    def from_dict(cls, data: dict, client: WhatsApp) -> FlowDetails:
        return cls(
            _client=client,
            id=data["id"],
            name=data["name"],
            status=FlowStatus(data["status"]),
            categories=tuple(FlowCategory(c) for c in data["categories"]),
            validation_errors=tuple(
                FlowValidationError.from_dict(e) for e in data["validation_errors"]
            )
            or None,
            json_version=data.get("json_version"),
            data_api_version=data.get("data_api_version"),
            endpoint_uri=data.get("endpoint_uri")
            or data.get("data_channel_uri"),  # data_channel_uri removed at v19.0
            preview=FlowPreview.from_dict(data["preview"])
            if data.get("preview")
            else None,
            whatsapp_business_account=WhatsAppBusinessAccount.from_dict(
                data["whatsapp_business_account"]
            )
            if data.get("whatsapp_business_account")
            else None,
            application=FacebookApplication.from_dict(data["application"])
            if data.get("application")
            else None,
            updated_at=datetime.datetime.strptime(
                data["updated_at"], "%Y-%m-%dT%H:%M:%S%z"
            ),
        )

    async def publish(self) -> bool:
        """
        Update the status of this flow to ``FlowStatus.PUBLISHED``.
            - A shortcut for :meth:`pywa.client.WhatsApp.publish_flow`.

        - This action is not reversible.
        - The Flow and its assets become immutable once published.
        - To update the Flow after that, you must create a new Flow. You specify the existing Flow ID as the clone_flow_id parameter while creating to copy the existing flow.

            You can publish your Flow once you have ensured that:

            - All validation errors and publishing checks have been resolved.
            - The Flow meets the design principles of WhatsApp Flows
            - The Flow complies with WhatsApp Terms of Service, the WhatsApp Business Messaging Policy and, if applicable, the WhatsApp Commerce Policy

        Returns:
            Whether the flow was published.

        Raises:
            FlowPublishingError: If this flow has validation errors or not all publishing checks have been resolved.
        """
        if await self._client.publish_flow(self.id):
            self.status = FlowStatus.PUBLISHED
            return True
        return False

    async def delete(self) -> bool:
        """
        When the flow is in ``FlowStatus.DRAFT`` status, you can delete it.
            - A shortcut for :meth:`pywa.client.WhatsApp.delete_flow`.

        Returns:
            Whether the flow was deleted.

        Raises:
            FlowDeletingError: If this flow is already published.
        """
        if await self._client.delete_flow(self.id):
            self.status = FlowStatus.DEPRECATED  # there is no `DELETED` status
            return True
        return False

    async def deprecate(self) -> bool:
        """
        When the flow is in ``FlowStatus.PUBLISHED`` status, you can only deprecate it.
            - A shortcut for :meth:`pywa.client.WhatsApp.deprecate_flow`.

        Returns:
            Whether the flow was deprecated.

        Raises:
            FlowDeprecatingError: If this flow is not published or already deprecated.
        """
        if await self._client.deprecate_flow(self.id):
            self.status = FlowStatus.DEPRECATED
            return True
        return False

    async def get_assets(self) -> tuple[FlowAsset, ...]:
        """
        Get all assets attached to this flow.
            - A shortcut for :meth:`pywa.client.WhatsApp.get_flow_assets`.

        Returns:
            The assets of the flow.
        """
        return await self._client.get_flow_assets(self.id)

    async def update_metadata(
        self,
        name: str | None = None,
        categories: Iterable[FlowCategory | str] | None = None,
        endpoint_uri: str | None = None,
    ) -> bool:
        """
        Update the metadata of this flow.
            - A shortcut for :meth:`pywa.client.WhatsApp.update_flow_metadata`.

        Args:
            name: The name of the flow (optional).
            categories: The new categories of the flow (optional).
            endpoint_uri: The URL of the FlowJSON Endpoint. Starting from FlowJSON 3.0 this property should be
             specified only gere. Do not provide this field if you are cloning a FlowJSON with version below 3.0.

        Example:

            >>> from pywa.types.flows import FlowCategory
            >>> wa = WhatsApp(business_account_id='1234567890', ...)
            >>> my_flows = wa.get_flows()
            >>> my_flows[0].update_metadata(
            ...     name='Feedback',
            ...     categories=[FlowCategory.SURVEY, FlowCategory.OTHER],
            ...     endpoint_uri='https://my-api-server/feedback_flow'
            ... )

        Returns:
            Whether the flow was updated.

        Raises:
            ValueError: If neither ``name``, ``categories`` or ``endpoint_uri`` is provided.
        """
        success = await self._client.update_flow_metadata(
            flow_id=self.id,
            name=name,
            categories=categories,
            endpoint_uri=endpoint_uri,
        )
        if success:
            if name:
                self.name = name
            if categories:
                self.categories = tuple(FlowCategory(c) for c in categories)
            if endpoint_uri:
                self.endpoint_uri = endpoint_uri
        return success

    async def update_json(
        self, flow_json: FlowJSON | dict | str | pathlib.Path | bytes | BinaryIO
    ) -> bool:
        """
        Update the json of this flow.
            - A shortcut for :meth:`pywa.client.WhatsApp.update_flow_json`.

        Args:
            flow_json: The new json of the flow. Can be a :class:`FlowJSON` object, :class:`dict`, json :class:`str`,
             json file path or json bytes.

        Returns:
            Whether the flow was updated.

        Raises:
            FlowUpdatingError: If the flow json is invalid or this flow is already published.
        """
        is_success, errors = await self._client.update_flow_json(
            flow_id=self.id,
            flow_json=flow_json,
        )
        self.validation_errors = errors or None
        return is_success
