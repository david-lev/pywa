Flow Types
==========

.. currentmodule:: pywa.types.flows

.. autoclass:: FlowRequest()
    :members: respond, decrypt_media, has_error, token_no_longer_valid

.. autoclass:: FlowRequestActionType()

.. autoclass:: FlowResponse()

.. autoclass:: FlowCategory()

.. autoclass:: FlowDetails()
    :members: publish, delete, deprecate, get_assets, update_metadata, update_json

.. autoclass:: FlowStatus()

.. autoclass:: FlowPreview()
    :members: with_params

.. autoclass:: FlowValidationError()

.. autoclass:: FlowAsset()

.. autoclass:: FlowMetricName()

.. autoclass:: FlowMetricGranularity()

.. autoclass:: CreatedFlow()

.. autoclass:: MigrateFlowsResponse()

.. autoclass:: MigratedFlow()

.. autoclass:: MigratedFlowError()

.. autoclass:: FlowResponseError()
    :show-inheritance:

.. autoclass:: FlowTokenNoLongerValid()
    :show-inheritance:

.. autoclass:: FlowRequestSignatureAuthenticationFailed()
    :show-inheritance:

.. currentmodule:: pywa.utils

.. autoclass:: FlowRequestDecryptor()

.. autoclass:: FlowResponseEncryptor()

.. autofunction:: default_flow_request_decryptor

.. autofunction:: default_flow_response_encryptor

.. autofunction:: flow_request_media_decryptor

.. currentmodule:: pywa.handlers

.. autoclass:: FlowRequestCallbackWrapper()
    :members: on_init, on_data_exchange, on_back, on
