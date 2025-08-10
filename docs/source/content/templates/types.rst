Template Types
==============

.. currentmodule:: pywa.types.templates

.. autoclass:: Template()

.. autoclass:: TemplateDetails()
    :members: update, duplicate, delete, compare, migrate, send, unpause

.. autoclass:: TemplateStatus()

.. autoclass:: TemplateRejectionReason()

.. autoclass:: QualityScore()

.. autoclass:: QualityScoreType()

.. autoclass:: LibraryTemplate()

.. autoclass:: TemplateCategory()

.. autoclass:: TemplateSubCategory()

.. autoclass:: TemplateLanguage()

.. autoclass:: ParamFormat()

.. autoclass:: HeaderText()
    :members: preview, params
.. autoclass:: HeaderImage()
    :members: params
.. autoclass:: HeaderVideo()
    :members: params
.. autoclass:: HeaderDocument()
    :members: params
.. autoclass:: HeaderLocation()
    :members: params
.. autoclass:: HeaderProduct()
    :members: params

.. autoclass:: BodyText()
    :members: preview, params, library_input

.. autoclass:: DateTime()
.. autoclass:: Currency()

.. autoclass:: FooterText()

.. autoclass:: Buttons()
.. autoclass:: CopyCodeButton()
    :members: params
.. autoclass:: FlowButton()
    :members: params
.. autoclass:: FlowButtonIcon()
.. autoclass:: PhoneNumberButton()
    :members: params, library_input
.. autoclass:: VoiceCallButton()
.. autoclass:: CallPermissionRequestButton()
.. autoclass:: QuickReplyButton()
    :members: params
.. autoclass:: URLButton()
    :members: params, library_input
.. autoclass:: AppDeepLink()
.. autoclass:: CatalogButton()
    :members: params
.. autoclass:: MPMButton()
    :members: params
.. autoclass:: SPMButton()
    :members: params
.. autoclass:: OneTapOTPButton()
    :members: params, library_input
.. autoclass:: ZeroTapOTPButton()
    :members: params, library_input
.. autoclass:: CopyCodeOTPButton()
    :members: params, library_input
.. autoclass:: OTPSupportedApp()

.. autoclass:: LimitedTimeOffer()
    :members: params

.. autoclass:: Carousel()
    :members: params

.. autoclass:: CarouselCard()
    :members: params

.. autoclass:: AuthenticationBody()
    :members: params, library_input

.. autoclass:: AuthenticationFooter()

.. autoclass:: TemplatesResult()
    :show-inheritance:

.. autoclass:: CreatedTemplate()
.. autoclass:: CreatedTemplates()

.. autoclass:: UpdatedTemplate()

.. autoclass:: TemplateUnpauseResult()

.. autoclass:: TemplatesCompareResult()
.. autoclass:: TopBlockReasonType()

.. autoclass:: MigrateTemplatesResult()
.. autoclass:: MigratedTemplate()
.. autoclass:: MigratedTemplateError()

.. autoclass:: DegreesOfFreedomSpec()
.. autoclass:: CreativeFeaturesSpec()
