"""This module contains classes and functions related to WhatsApp message templates."""

from __future__ import annotations

import dataclasses
import datetime
from typing import TYPE_CHECKING, cast

from pywa.listeners import TemplateUpdateListenerIdentifier
from pywa.types import CallbackData
from pywa.types.others import _ItemFactory
from pywa.types.templates import *  # noqa MUST BE IMPORTED FIRST
from pywa.types.templates import (
    TemplateDetails as _TemplateDetails,
    CreatedTemplate as _CreatedTemplate,
    CreatedTemplates as _CreatedTemplates,
    UpdatedTemplate as _UpdatedTemplate,
    TemplateStatusUpdate as _TemplateStatusUpdate,
    TemplateQualityUpdate as _TemplateQualityUpdate,
    TemplateCategoryUpdate as _TemplateCategoryUpdate,
    TemplateComponentsUpdate as _TemplateComponentsUpdate,
)  # noqa MUST BE IMPORTED FIRST
from .others import Result, SuccessResult
from .. import filters as pywa_filters

if TYPE_CHECKING:
    from ..client import WhatsApp as WhatsAppAsync, WhatsApp
    from .sent_update import SentTemplate


@dataclasses.dataclass(frozen=True, kw_only=True)
class BaseTemplateUpdateAsync:
    """Base class for template updates."""

    _client: WhatsAppAsync = dataclasses.field(repr=False, hash=False, compare=False)
    template_id: str

    async def get_template(self) -> TemplateDetails:
        """
        Fetches the template details from WhatsApp.

        Returns:
            TemplateDetails: The details of the template.
        """
        return await self._client.get_template(
            template_id=self.template_id,
        )


@dataclasses.dataclass(slots=True, frozen=True, kw_only=True)
class TemplateStatusUpdate(BaseTemplateUpdateAsync, _TemplateStatusUpdate):
    """
    Represents status change of a template.

    Triggers::

        - A template is approved.
        - A template is rejected.
        - A template is disabled.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/reference/message_template_status_update>`_.

    Attributes:
        id: ID of Whatsapp Business Accounts this update belongs to.
        timestamp: Timestamp of the update (in UTC).
        new_status: The new status of the template.
        template_id: The ID of the template.
        template_name: The name of the template.
        template_language: The language of the template.
        reason: The reason the template was rejected (if status is ``REJECTED``).
        disable_date: The date the template was disabled (if status is ``DISABLED``).
        title: Title of template pause or unpause event.
        description: String describing why the template was locked or unlocked.
        shared_data: Shared data between handlers.
    """

    async def unpause(self) -> TemplateUnpauseResult:
        """
        Unpause the template that has been paused due to pacing.

        - You must wait 5 minutes after a template has been paused as a result of pacing before calling this method.
        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/message-templates/guidelines#unpausing>`_.

        Returns:
            A TemplateUnpauseResult object containing the result of the unpause operation.
        """
        return await self._client.unpause_template(template_id=self.template_id)


@dataclasses.dataclass(slots=True, frozen=True, kw_only=True)
class TemplateCategoryUpdate(BaseTemplateUpdateAsync, _TemplateCategoryUpdate):
    """
    Represents a template category update.

    Triggers::

        - The existing category of a WhatsApp template is going to be changed by an automated process.
        - The existing category of a WhatsApp template is changed manually or by an automated process.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/reference/template_category_update>`_.

    Attributes:
        id: ID of Whatsapp Business Accounts this update belongs to.
        timestamp: Timestamp of the update (in UTC).
        template_id: The ID of the template.
        template_name: The name of the template.
        template_language: The language of the template.
        correct_category: The category that the template will be `recategorized <https://developers.facebook.com/docs/whatsapp/updates-to-pricing/new-template-guidelines/#how-we-update-a-template-s-category-after-initial-approval>`_ as in 24 hours.
        previous_category: The template's previous category.
        new_category: If ``correct_category`` is set - the ``new_category`` is the current category of the template. If ``previous_category`` is set - the ``new_category`` is the category that the template was recategorized to.
    """


@dataclasses.dataclass(slots=True, frozen=True, kw_only=True)
class TemplateComponentsUpdate(BaseTemplateUpdateAsync, _TemplateComponentsUpdate):
    """
    Represents a template components update.

    Triggers::

        - A template is edited.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/reference/message_template_components_update>`_.

    Attributes:
        id: ID of Whatsapp Business Accounts this update belongs to.
        timestamp: Timestamp of the update (in UTC).
        template_id: The ID of the template.
        template_name: The name of the template.
        template_language: The language of the template.
        template_element: The body text of the template.
        template_title: The header text of the template.
        template_footer: The footer text of the template.
        template_buttons: A list of buttons in the template.
    """


@dataclasses.dataclass(slots=True, frozen=True, kw_only=True)
class TemplateQualityUpdate(BaseTemplateUpdateAsync, _TemplateQualityUpdate):
    """
    Represents a template quality update.

    Triggers::

        - A template's quality score changes.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/reference/message_template_quality_update>`_.

    Attributes:
        id: ID of Whatsapp Business Accounts this update belongs to.
        timestamp: Timestamp of the update (in UTC).
        template_id: The ID of the template.
        template_name: The name of the template.
        template_language: The language of the template.
        new_quality_score: The new quality score of the template.
        previous_quality_score: The previous quality score of the template.
    """


@dataclasses.dataclass(kw_only=True, slots=True)
class TemplateDetails(_TemplateDetails):
    """
    Represents the details of an existing WhatsApp Template.

    Attributes:
        id: The unique identifier of the template.
        name: The name of the template.
        status: The status of the template (See `Template Status <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates#template-status>`_).
        category: The category of the template (See `Template Categorization <https://developers.facebook.com/docs/whatsapp/updates-to-pricing/new-template-guidelines#template-categorization>`_).
        language: The language of the template (See `Supported Languages <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/supported-languages>`_).
        components: Components that make up the template. Header, Body, Footer, Buttons, Cards, etc. (See `Template Components <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components>`_).
        parameter_format: The type of parameter formatting the Header and BodyText components of the template will use.
        message_send_ttl_seconds: The time-to-live (TTL) for the template message in seconds (See `Time-to-live (TTL) <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates#time-to-live--ttl---customization--defaults--min-max-values--and-compatibility>`_).
        correct_category: The correct category of the template, if applicable.
        previous_category: The previous category of the template, if applicable.
        rejected_reason: The reason the message template was rejected, if applicable (See `Template Rejected Status <https://developers.facebook.com/docs/whatsapp/updates-to-pricing/new-template-guidelines#rejected-status>`_).
        library_template_name: Template Library name that this template is cloned from, if applicable.
        quality_score: The quality score of the template, if applicable (See `Template Quality Score <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates#template-quality-score>`_).
        cta_url_link_tracking_opted_out: Optional boolean field for opting out/in of link tracking at template level.
        sub_category: The sub-category of the template, if applicable.
    """

    _client: WhatsAppAsync = dataclasses.field(repr=False, hash=False, compare=False)

    async def delete(self) -> SuccessResult:
        """
        Delete this template

        - If you delete a template that has been sent in a template message but has yet to be delivered (e.g. because the customer's phone is turned off), the template's status will be set to ``PENDING_DELETION`` and we will attempt to deliver the message for 30 days. After this time you will receive a "Structure Unavailable" error and the customer will not receive the message.
        - Names of an approved template that has been deleted cannot be used again for 30 days.
        """
        return await self._client.delete_template(
            template_name=self.name, template_id=self.id
        )

    async def update(
        self,
        *,
        new_category: TemplateCategory | None = None,
        new_components: list[TemplateBaseComponent] | None = None,
        new_message_send_ttl_seconds: int | None = None,
        new_parameter_format: ParamFormat | None = None,
    ) -> UpdatedTemplate:
        """
        Update this template.

        - The template object will be updated in memory after a successful update.
        - Only templates with an ``APPROVED``, ``REJECTED``, or ``PAUSED`` status can be edited.
        - You cannot edit the category of an approved template.
        - Approved templates can be edited up to 10 times in a 30 day window, or 1 time in a 24 hour window. Rejected or paused templates can be edited an unlimited number of times.
        - After editing an approved or paused template, it will automatically be approved unless it fails template review.
        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates#edit-a-message-template>`_.

        Args:
            new_category: The new category of the template (optional, cannot be changed for approved templates).
            new_components: The new components of the template (optional, if not provided, the existing components will be used).
            new_message_send_ttl_seconds: The new message send TTL in seconds (optional, if not provided, the existing TTL will be used).
            new_parameter_format: The new parameter format (optional, if not provided, the existing format will be used).

        Returns:
            Whether the template was updated successfully.
        """
        if res := await self._client.update_template(
            template_id=self.id,
            new_category=new_category,
            new_components=new_components,
            new_message_send_ttl_seconds=new_message_send_ttl_seconds,
            new_parameter_format=new_parameter_format,
        ):
            if new_category:
                self.category = new_category
            if new_components:
                self.components = new_components
            if new_message_send_ttl_seconds is not None:
                self.message_send_ttl_seconds = new_message_send_ttl_seconds
            if new_parameter_format is not None:
                self.parameter_format = new_parameter_format
        return res

    async def duplicate(self, **overrides) -> CreatedTemplate:
        """
        Duplicate this template.

        - WhatsApp Cloud API does not support duplicating templates, this method creates a new template with the same components and properties as this one. It is useful for creating variations of existing templates with minor changes.

        Example:
            >>> wa = WhatsApp(...)
            >>> template = wa.get_template("my_template_id")
            >>> new_template = template.duplicate(language=TemplateLanguage.ENGLISH)

        Args:
            overrides: Optional overrides for the template properties.
        """
        return await self._client.create_template(
            Template(
                name=overrides.get("name", self.name),
                language=overrides.get("language", self.language),
                category=overrides.get("category", self.category),
                components=overrides.get("components", self.components),
                parameter_format=overrides.get(
                    "parameter_format", self.parameter_format
                ),
                message_send_ttl_seconds=overrides.get(
                    "message_send_ttl_seconds", self.message_send_ttl_seconds
                ),
            )
        )

    async def compare(
        self,
        *to: int | str,
        start: datetime.datetime | int,
        end: datetime.datetime | int,
    ) -> TemplatesCompareResult:
        """
        You can compare two templates by examining how often each one is sent, which one has the lower ratio of blocks to sends, and each template's top reason for being blocked.

        - Only two templates can be compared at a time.
        - Both templates must be in the same WhatsApp Business Account.
        - Templates must have been sent at least 1,000 times in the queries specified timeframe.
        - Timeframes are limited to ``7``, ``30``, ``60`` and ``90`` day lookbacks from the time of the request.
        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/template-comparison>`_.

        Args:
            to: The IDs of the templates to compare with the given template.
            start: The start date of the comparison period.
            end: The end date of the comparison period.

        Returns:
            A TemplatesCompareResult object containing the comparison results.
        """
        return await self._client.compare_templates(
            template_id=self.id, *to, start=start, end=end
        )

    async def unpause(self) -> TemplateUnpauseResult:
        """
        Unpause a template that has been paused due to pacing.

        - This method can only be called if the template is currently paused due to pacing.
        - You must wait 5 minutes after a template has been paused as a result of pacing before calling this method.
        - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/message-templates/guidelines#unpausing>`_.

        Returns:
            A TemplateUnpauseResult object containing the result of the unpause operation.
        """
        res = await self._client.unpause_template(template_id=self.id)
        if res:
            self.status = TemplateStatus.APPROVED
        return res

    async def send(
        self,
        to: str | int,
        params: list[TemplateBaseComponent.Params],
        *,
        reply_to_message_id: str | None = None,
        tracker: str | CallbackData | None = None,
        sender: str | int | None = None,
    ) -> SentTemplate:
        """
        A shortcut to send a template message to WhatsApp users.

        Args:
            to: The phone ID of the WhatsApp user.
            params: The parameters to fill in the template.
            reply_to_message_id: The ID of the message to reply to (optional).
            tracker: A callback data to track the message (optional, can be a string or a :class:`CallbackData` object).
            sender: The phone ID to send the template from (optional, if not provided, the client's phone ID will be used).
        """
        return await self._client.send_template(
            to=to,
            name=self.name,
            language=self.language,
            params=params,
            reply_to_message_id=reply_to_message_id,
            tracker=tracker,
            sender=sender,
        )


class TemplatesResult(Result[TemplateDetails]):
    """
    Represents the result of a templates query.

    Attributes:
        total_count: The total number of message templates that belong to a WhatsApp Business Account.
        message_template_count: The current number of message templates that belong to the WhatsApp Business Account.
        message_template_limit: The maximum number of message templates that can belong to a WhatsApp Business Account.
        are_translations_complete: The status for template translations.
    """

    total_count: int
    message_template_count: int
    message_template_limit: int
    are_translations_complete: bool

    def __init__(
        self,
        wa: WhatsApp,
        response: dict,
        item_factory: _ItemFactory,
    ):
        super().__init__(
            wa=wa,
            response=response,
            item_factory=item_factory,
        )
        self.total_count = response["summary"]["total_count"]
        self.message_template_count = response["summary"]["message_template_count"]
        self.message_template_limit = response["summary"]["message_template_limit"]
        self.are_translations_complete = response["summary"][
            "are_translations_complete"
        ]

    def __repr__(self) -> str:
        return (
            f"TemplatesResult({self._data!r}, has_next={self.has_next!r}, has_previous={self.has_previous!r}, "
            f"total_count={self.total_count!r}, "
            f"message_template_count={self.message_template_count!r}, "
            f"message_template_limit={self.message_template_limit!r}, "
            f"are_translations_complete={self.are_translations_complete!r})"
        )


class _CreatedAndUpdatedTemplateActionsAsync:
    async def get(self) -> TemplateDetails:
        """
        Retrieve the details of the created or updated template.

        Returns:
            TemplateDetails: The details of the created or updated template.
        """
        return await self._client.get_template(template_id=self.id)

    async def wait_until_approved(
        self,
        *,
        cancelers: pywa_filters.Filter | None = None,
        timeout: float | None = None,
    ) -> TemplateStatusUpdate:
        """
        Wait until the template is approved.

        Example usage:

            >>> from pywa import WhatsApp, filters
            >>> wa = WhatsApp(...)
            >>> created_template = wa.create_template(...)
            >>> status = created_template.wait_until_approved(cancelers=filters.template_status & filters.template_status_rejected)
            >>> print(f"Template {created_template.id} is approved with status: {status.new_status}")


        Args:
            cancelers: A filter to cancel the waiting process.
            timeout: The maximum time to wait for the template to be approved.

        Returns:
            TemplateStatusUpdate: An update containing the status of the template once it is approved.
        """
        return cast(
            TemplateStatusUpdate,
            await self._client.listen(
                to=TemplateUpdateListenerIdentifier(
                    waba_id=self._client.business_account_id, template_id=self.id
                ),
                filters=pywa_filters.template_status
                & pywa_filters.template_status_approved,
                cancelers=cancelers,
                timeout=timeout,
            ),
        )


@dataclasses.dataclass(frozen=True, slots=True)
class CreatedTemplate(_CreatedAndUpdatedTemplateActionsAsync, _CreatedTemplate):
    """
    Represents a created WhatsApp Template.

    Attributes:
        id: the template ID.
        status: the template status.
        category: the template category.
    """

    _client: WhatsAppAsync = dataclasses.field(repr=False, hash=False, compare=False)


@dataclasses.dataclass(frozen=True, slots=True)
class UpdatedTemplate(_CreatedAndUpdatedTemplateActionsAsync, _UpdatedTemplate):
    """
    Represents the result of a template update operation.

    Attributes:
        id: The unique identifier of the updated template.
        name: The name of the updated template.
        category: The category of the updated template.
        success: Indicates whether the template update was successful.
    """

    _client: WhatsAppAsync = dataclasses.field(repr=False, hash=False, compare=False)


@dataclasses.dataclass(frozen=True, slots=True)
class CreatedTemplates(_CreatedTemplates):
    """
    Represents a collection of created WhatsApp Templates.

    Attributes:
        templates: A list of CreatedTemplate instances.
    """

    templates: tuple[CreatedTemplate, ...]
