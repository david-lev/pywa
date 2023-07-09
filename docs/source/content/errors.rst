⚠️ Errors
==========

.. currentmodule:: pywa.errors

All the exceptions in this library are subclasses of :class:`WhatsAppError`.

.. autoclass:: WhatsAppError()
    :show-inheritance:

-----------------

**The exceptions are divided into 4 categories:**

Sending Messages Errors
-----------------------

.. autoclass:: SendMessageError()
    :show-inheritance:
.. autoclass:: MessageUndeliverable()
    :show-inheritance:
.. autoclass:: ReEngagementMessage()
    :show-inheritance:
.. autoclass:: UnsupportedMessageType()
    :show-inheritance:
.. autoclass:: RecipientNotInAllowedList()
    :show-inheritance:
.. autoclass:: InvalidParameter()
    :show-inheritance:
.. autoclass:: MissingRequiredParameter()

Authorization Errors
--------------------

.. autoclass:: AuthorizationError()
    :show-inheritance:
.. autoclass:: AuthException()
    :show-inheritance:
.. autoclass:: APIMethod()
    :show-inheritance:
.. autoclass:: PermissionDenied()
    :show-inheritance:
.. autoclass:: ExpiredAccessToken()
    :show-inheritance:
.. autoclass:: APIPermission()
    :show-inheritance:

Rate Limit Errors
-----------------

.. autoclass:: ThrottlingError()
    :show-inheritance:
.. autoclass:: ToManyAPICalls()
    :show-inheritance:
.. autoclass:: RateLimitIssues()
    :show-inheritance:
.. autoclass:: RateLimitHit()
    :show-inheritance:
.. autoclass:: SpamRateLimitHit()
    :show-inheritance:
.. autoclass:: ToManyMessages()
    :show-inheritance:

Integrity Errors
----------------

.. autoclass:: IntegrityError()
    :show-inheritance:
.. autoclass:: TemporarilyBlocked()
    :show-inheritance:
.. autoclass:: AccountLocked()
    :show-inheritance:
