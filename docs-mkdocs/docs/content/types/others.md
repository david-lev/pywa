# Others

::: pywa.types.sent_update.SentMessage
    options:
      members: false

::: pywa.types.sent_update.SentTemplate
    options:
      members: false
      show_bases: true

::: pywa.types.sent_update.SentMediaMessage
    options:
      members: false
      show_bases: true

::: pywa.types.sent_update.SentVoiceMessage
    options:
      members: false
      show_bases: true

::: pywa.types.sent_update.SentLocationRequest
    options:
      members: false
      show_bases: true

::: pywa.types.sent_update.SentContactInfoRequest
    options:
      members: false
      show_bases: true

::: pywa.types.sent_update.SentReaction
    options:
      members: false
      show_bases: true

::: pywa.types.sent_update.SentTemplateStatus
    options:
      members: false

::: pywa.types.others.SuccessResult
    options:
      members: false

::: pywa.types.others.Result
    options:
      members: ["has_next", "next", "has_previous", "previous", "all", "before", "after", "empty"]
      inherited_members: ["has_next", "next", "has_previous", "previous", "all", "before", "after", "empty"]

::: pywa.types.others.Pagination
    options:
      members: false

::: pywa.types.others.BusinessVerificationStatus
    options:
      members: false

::: pywa.types.others.MarketingMessagesLiteAPIStatus
    options:
      members: false

::: pywa.types.others.MarketingMessagesOnboardingStatus
    options:
      members: false

::: pywa.types.others.BusinessProfile
    options:
      members: false

::: pywa.types.others.BusinessPhoneNumber
    options:
      members: false

::: pywa.types.calls.BusinessPhoneNumberSettings
    options:
      members: false

::: pywa.types.others.StorageConfiguration
    options:
      members: false

::: pywa.types.others.ConversationalAutomation
    options:
      members: false

::: pywa.types.others.QRCode
    options:
      members: ["fetch_image", "update", "delete"]
      inherited_members: ["fetch_image", "update", "delete"]

::: pywa.types.others.QRCodeImageType
    options:
      members: false

::: pywa.types.others.CreatedSignup
    options:
      members: true

::: pywa.types.others.SignupDetails
    options:
      members: true

::: pywa.types.others.SignupStatus
    options:
      members: false

::: pywa.types.others.Command
    options:
      members: false

::: pywa.types.others.CommerceSettings
    options:
      members: false

::: pywa.types.others.Industry
    options:
      members: false

::: pywa.types.others.WhatsAppBusinessAccount
    options:
      members: false

::: pywa.types.others.FacebookApplication
    options:
      members: false

::: pywa.types.others.UsersBlockedResult
    options:
      members: false

::: pywa.types.others.UsersUnblockedResult
    options:
      members: false

::: pywa.types.others.BlockUserFailure
    options:
      members: false

::: pywa.utils.Version
    options:
      members: false

::: pywa.types.base_update.StopHandling
    options:
      members: false

::: pywa.types.base_update.ContinueHandling
    options:
      members: false

::: pywa.utils.CallbackURLScope
    options:
      members: false

::: pywa.utils.WebhookFields
    options:
      members: false

::: pywa.utils.start_ngrok_tunnel
    options:
      members: false
