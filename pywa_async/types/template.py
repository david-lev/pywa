from pywa.types.template import *  # noqa MUST BE IMPORTED FIRST
from pywa.types.template_v2 import *  # noqa MUST BE IMPORTED FIRST
from pywa.types.template_v2 import (
    TemplateDetails as _TemplateDetails,
    TemplatesResult as _TemplatesResult,
)  # noqa MUST BE IMPORTED FIRST

if TYPE_CHECKING:
    from ..client import WhatsApp
    from .sent_message import SentTemplate


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
        parameter_format: The type of parameter formatting the Header and Body components of the template will use.
        message_send_ttl_seconds: The time-to-live (TTL) for the template message in seconds (See `Time-to-live (TTL) <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates#time-to-live--ttl---customization--defaults--min-max-values--and-compatibility>`_).
        correct_category: The correct category of the template, if applicable.
        previous_category: The previous category of the template, if applicable.
        rejected_reason: The reason the message template was rejected, if applicable (See `Template Rejected Status <https://developers.facebook.com/docs/whatsapp/updates-to-pricing/new-template-guidelines#rejected-status>`_).
        library_template_name: Template Library name that this template is cloned from, if applicable.
        quality_score: The quality score of the template, if applicable (See `Template Quality Score <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates#template-quality-score>`_).
        cta_url_link_tracking_opted_out: Optional boolean field for opting out/in of link tracking at template level.
        sub_category: The sub-category of the template, if applicable.
    """

    _client: WhatsApp = dataclasses.field(repr=False, hash=False, compare=False)

    async def delete(self) -> bool:
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
        new_components: list[BaseComponent] | None = None,
        new_message_send_ttl_seconds: int | None = None,
        new_parameter_format: ParamFormat | None = None,
    ) -> bool:
        """
        Update this template with new values.

        - The template object will be updated in memory after a successful update.
        - Only templates with an ``APPROVED``, ``REJECTED``, or ``PAUSED`` status can be edited.
        - Approved templates can be edited up to 10 times in a 30 day window, or 1 time in a 24 hour window. Rejected or paused templates can be edited an unlimited number of times.
        - After editing an approved or paused template, it will automatically be approved unless it fails template review.

        Args:
            new_category: The new category for the template (See `Template Categorization <https://developers.facebook.com/docs/whatsapp/updates-to-pricing/new-template-guidelines#template-categorization>`_).
            new_components: The new components for the template.
            new_message_send_ttl_seconds: The new time-to-live (TTL) for the template message in seconds (See `Time-to-live (TTL) <https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates#time-to-live--ttl---customization--defaults--min-max-values--and-compatibility>`_).
            new_parameter_format: The new type of parameter formatting the Header and Body components of the template will use.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        if await self._client.update_template(
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
            return True
        return False

    async def compare(
        self,
        others: Iterable[int | str],
        start: datetime.datetime,
        end: datetime.datetime,
    ):
        return await self._client.compare_templates(
            template_ids=[self.id, *others], start=start, end=end
        )

    async def migrate(self): ...

    async def send(self) -> SentTemplate: ...


class TemplatesResult(_TemplatesResult):
    _wa: WhatsApp

    async def compare(self, start: datetime.datetime, end: datetime.datetime):
        return await self._wa.compare_templates(
            template_ids=[t.id for t in self], start=start, end=end
        )
