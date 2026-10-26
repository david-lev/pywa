# Flow Types

::: pywa.types.flows.FlowRequest
    options:
      members: ["respond", "decrypt_media", "has_error", "token_no_longer_valid"]
      inherited_members: ["respond", "decrypt_media", "has_error", "token_no_longer_valid"]

::: pywa.types.flows.FlowRequestActionType
    options:
      members: false

::: pywa.types.flows.FlowResponse
    options:
      members: false

::: pywa.types.flows.FlowCategory
    options:
      members: false

::: pywa.types.flows.FlowDetails
    options:
      members: ["publish", "delete", "deprecate", "get_assets", "update_metadata", "update_json"]
      inherited_members: ["publish", "delete", "deprecate", "get_assets", "update_metadata", "update_json"]

::: pywa.types.flows.FlowStatus
    options:
      members: false

::: pywa.types.flows.FlowPreview
    options:
      members: ["with_params"]
      inherited_members: ["with_params"]

::: pywa.types.flows.FlowJSONUpdateResult
    options:
      members: false

::: pywa.types.flows.FlowValidationError
    options:
      members: false

::: pywa.types.flows.FlowAsset
    options:
      members: false

::: pywa.types.flows.FlowMetricName
    options:
      members: false

::: pywa.types.flows.FlowMetricGranularity
    options:
      members: false

::: pywa.types.flows.CreatedFlow
    options:
      members: false

::: pywa.types.flows.MigrateFlowsResponse
    options:
      members: false

::: pywa.types.flows.MigratedFlow
    options:
      members: false

::: pywa.types.flows.MigratedFlowError
    options:
      members: false

::: pywa.types.flows.FlowResponseError
    options:
      members: false
      show_bases: true

::: pywa.types.flows.FlowTokenNoLongerValid
    options:
      members: false
      show_bases: true

::: pywa.types.flows.FlowRequestSignatureAuthenticationFailed
    options:
      members: false
      show_bases: true

::: pywa.utils.FlowRequestDecryptedMedia
    options:
      members: false

::: pywa.utils.FlowRequestDecryptor
    options:
      members: false

::: pywa.utils.FlowResponseEncryptor
    options:
      members: false

::: pywa.utils.default_flow_request_decryptor
    options:
      members: false

::: pywa.utils.default_flow_response_encryptor
    options:
      members: false

::: pywa.utils.flow_request_media_decryptor
    options:
      members: false

::: pywa.handlers.FlowRequestCallbackWrapper
    options:
      members: ["on_init", "on_data_exchange", "on_back", "on_completion", "on"]
      inherited_members: ["on_init", "on_data_exchange", "on_back", "on_completion", "on"]
