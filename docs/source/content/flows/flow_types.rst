Flow Types
==========

.. currentmodule:: pywa.types.flows

.. autoclass:: FlowRequest()
    :members: has_error, is_health_check

.. autoclass:: FlowRequestActionType()

.. autoclass:: FlowResponse()

.. autoclass:: FlowCategory()

.. autoclass:: FlowDetails()
    :members: publish, delete, deprecate, get_assets, update_metadata, update_json

.. autoclass:: FlowStatus()

.. autoclass:: FlowPreview()

.. autoclass:: FlowValidationError()

.. autoclass:: FlowAsset()

.. autoclass:: FlowTokenNoLongerValid()

.. autoclass:: FlowRequestSignatureAuthenticationFailed()

.. currentmodule:: pywa.utils

.. autoclass:: FlowRequestDecryptor()

.. autoclass:: FlowResponseEncryptor()

.. autofunction:: default_flow_request_decryptor

.. autofunction:: default_flow_response_encryptor

.. autofunction:: flow_request_media_decryptor_sync

.. autofunction:: flow_request_media_decryptor_async
