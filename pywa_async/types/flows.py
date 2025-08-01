"""This module contains the types related to WhatsApp Flows."""

from __future__ import annotations

__all__ = [
    "FlowCompletion",
    "FlowRequest",
    "FlowResponse",
    "FlowResponseError",
    "FlowRequestCannotBeDecrypted",
    "FlowRequestSignatureAuthenticationFailed",
    "FlowTokenNoLongerValid",
    "FlowCategory",
    "FlowDetails",
    "FlowMetricName",
    "FlowMetricGranularity",
    "FlowStatus",
    "FlowPreview",
    "FlowJSONUpdateResult",
    "FlowValidationError",
    "FlowAsset",
    "CreatedFlow",
    "MigratedFlow",
    "MigratedFlowError",
    "MigrateFlowsResponse",
    "FlowJSON",
    "Screen",
    "ScreenData",
    "ScreenDataUpdate",
    "Layout",
    "LayoutType",
    "Form",
    "ScreenDataRef",
    "ComponentRef",
    "FlowStr",
    "TextHeading",
    "TextSubheading",
    "TextBody",
    "TextCaption",
    "RichText",
    "FontWeight",
    "TextInput",
    "InputType",
    "LabelVariant",
    "TextArea",
    "CheckboxGroup",
    "ChipsSelector",
    "RadioButtonsGroup",
    "Footer",
    "OptIn",
    "Dropdown",
    "EmbeddedLink",
    "NavigationList",
    "NavigationItem",
    "NavigationItemStart",
    "NavigationItemMainContent",
    "NavigationItemEnd",
    "DatePicker",
    "CalendarPicker",
    "CalendarPickerMode",
    "CalendarRangeValues",
    "CalendarDay",
    "Image",
    "ImageCarouselItem",
    "ImageCarousel",
    "PhotoPicker",
    "PhotoSource",
    "DocumentPicker",
    "ScaleType",
    "If",
    "Switch",
    "DataSource",
    "DataExchangeAction",
    "NavigateAction",
    "CompleteAction",
    "UpdateDataAction",
    "OpenUrlAction",
    "FlowActionType",
    "FlowRequestActionType",
    "Next",
    "NextType",
]

import httpx

from pywa.types.flows import *  # noqa MUST BE IMPORTED FIRST
from pywa.types.flows import (
    FlowDetails as _FlowDetails,
    FlowCompletion as _FlowCompletion,
    FlowRequest as _FlowRequest,
)  # noqa MUST BE IMPORTED FIRST
from pywa.types.others import SuccessResult
from .others import Result
from .base_update import BaseUserUpdateAsync

import dataclasses
import pathlib
from typing import Iterable, TYPE_CHECKING, BinaryIO

from .. import utils

if TYPE_CHECKING:
    from ..client import WhatsApp


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class FlowRequest(_FlowRequest):
    """
    Represents a flow request. This request is sent to the flow endpoint when a user interacts with a flow.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/guides/implementingyourflowendpoint#data_exchange_request>`_.

    Attributes:
        version: The version of the ``data_api_version`` specified on the flow json.
        flow_token: The flow token used to create the flow
        action: The action that triggered the request.
        screen: The screen that triggered the request. If action is ``FlowRequestActionType.INIT`` or ``FlowRequestActionType.BACK``, this field may be ``None``.
        data: The data sent from the screen. If action is ``FlowRequestActionType.BACK`` or ``FlowRequestActionType.INIT``, this field may be ``None``.
        raw: The raw data of the request.
        raw_encrypted: The raw-encrypted data of the request.
    """

    async def decrypt_media(
        self, key: str, index: int = 0, dl_session: httpx.AsyncClient | None = None
    ) -> utils.FlowRequestDecryptedMedia:
        """
        Decrypt the encrypted media file from the flow request.

        Example:

            >>> from pywa_async import WhatsApp, types
            >>> wa = WhatsApp(...)
            >>> @wa.on_flow_request("/my-flow-endpoint")
            ... async def my_flow_endpoint(_: WhatsApp, req: types.FlowRequest):
            ...     media_id, filename, decrypted_data = await req.decrypt_media(key="driver_license", index=0)
            ...     with open(filename, "wb") as file:
            ...         file.write(decrypted_data)
            ...     return req.respond(...)

        Args:
            key: The key of the media in the data (e.g. ``"driver_license"``).
            index: The index of the media in the data (default to ``0``).
            dl_session: The HTTPX async session to download the media (optional, new session will be created if not provided).

        Returns:
            A tuple of (media_id, filename, decrypted_data) where:
                - media_id: The media ID of the decrypted media.
                - filename: The filename of the decrypted media.
                - decrypted_data: The decrypted data of the media.
        Raises:
            ValueError: If the request has no data.
            KeyError: If the key is not found in the data.
            IndexError: If the index is out of range.
        """
        return await utils.flow_request_media_decryptor(
            encrypted_media=self.data[key][index],
            dl_session=dl_session,
        )


@dataclasses.dataclass(slots=True, kw_only=True, frozen=True)
class FlowCompletion(BaseUserUpdateAsync, _FlowCompletion):
    """
    A flow completion message. This update arrives when a user completes a flow.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/gettingstarted/receiveflowresponse>`_.

    Attributes:
        id: The message ID (If you want to reply to the message, use ``message_id_to_reply`` instead).
        metadata: The metadata of the message (to which phone number it was sent).
        type: The message type (Always ``MessageType.INTERACTIVE``).
        from_user: The user who sent the message.
        timestamp: The timestamp when the message was sent (in UTC).
        reply_to_message: The message to which this message is a reply to.
        body: The body of the message.
        token: The token of the flow. can be ``None`` in some cases :|
        response: The response from the flow.
        shared_data: Shared data between handlers.
    """


@dataclasses.dataclass(slots=True, kw_only=True)
class FlowDetails(_FlowDetails):
    """
    Represents the details of a flow.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowsapi#details>`_.

    Attributes:
        id: The unique ID of the Flow.
        name: The user-defined name of the Flow which is not visible to users.
        status: The status of the flow.
        updated_at: The last time the flow was updated (name, categories, endpoint_uri, json, etc.).
        json_version: The version specified by the developer in the Flow JSON asset uploaded.
        data_api_version: The version of the Data API specified by the developer in the Flow JSON asset uploaded. Only for Flows with an Endpoint.
        categories: The categories of the flow.
        validation_errors: The validation errors of the flow (All errors must be fixed before the Flow can be published).
        endpoint_uri: The URL of the WA Flow Endpoint specified by the developer via API or in the Builder UI (Was ``data_channel_uri`` before v19.0).
        preview: The URL to the web preview page to visualize the flow and its expiry time.
        whatsapp_business_account: The WhatsApp Business Account which owns the Flow.
        application: The Facebook developer application used to create the Flow initially.
        health_status: A summary of the Flows health status.
    """

    _client: WhatsApp = dataclasses.field(repr=False, hash=False, compare=False)

    async def publish(self) -> SuccessResult:
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
        if res := await self._client.publish_flow(self.id):
            self.status = FlowStatus.PUBLISHED
        return res

    async def delete(self) -> SuccessResult:
        """
        When the flow is in ``FlowStatus.DRAFT`` status, you can delete it.
            - A shortcut for :meth:`pywa.client.WhatsApp.delete_flow`.

        Returns:
            Whether the flow was deleted.

        Raises:
            FlowDeletingError: If this flow is already published.
        """
        if res := await self._client.delete_flow(self.id):
            self.status = FlowStatus.DEPRECATED  # there is no `DELETED` status
        return res

    async def deprecate(self) -> SuccessResult:
        """
        When the flow is in ``FlowStatus.PUBLISHED`` status, you can only deprecate it.
            - A shortcut for :meth:`pywa.client.WhatsApp.deprecate_flow`.

        Returns:
            Whether the flow was deprecated.

        Raises:
            FlowDeprecatingError: If this flow is not published or already deprecated.
        """
        if res := await self._client.deprecate_flow(self.id):
            self.status = FlowStatus.DEPRECATED
        return res

    async def get_assets(self) -> Result[FlowAsset]:
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
        application_id: int | None = None,
    ) -> SuccessResult:
        """
        Update the metadata of this flow.
            - A shortcut for :meth:`pywa.client.WhatsApp.update_flow_metadata`.

        Args:
            name: The name of the flow (optional).
            categories: The new categories of the flow (optional).
            endpoint_uri: The URL of the FlowJSON Endpoint. Starting from FlowJSON 3.0 this property should be
             specified only gere. Do not provide this field if you are cloning a FlowJSON with version below 3.0.
            application_id: The ID of the Meta application which will be connected to the Flow. All the flows with endpoints need to have an Application connected to them.

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
            application_id=application_id,
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
    ) -> FlowJSONUpdateResult:
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
        res = await self._client.update_flow_json(
            flow_id=self.id,
            flow_json=flow_json,
        )
        self.validation_errors = res.validation_errors or None
        return res
