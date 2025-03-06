Named Parameters
===============

.. currentmodule:: pywa.types.named_parameter

WhatsApp templates support named parameters, which allow you to reference template parameters by name rather than position. This makes templates more maintainable and less error-prone, especially for complex templates with many parameters.

Named parameters can be used in both header components (text type only) and body components of WhatsApp templates. For header components, you can use the ``parameter_name`` attribute of the ``Template.TextValue`` class. For body components, you can use either the dedicated named parameter classes below or the ``parameter_name`` attribute of the component classes.

.. autoclass:: NamedParameter()
    :members:

--------------------

.. autoclass:: NamedTextParameter()
    :members:

--------------------

.. autoclass:: NamedCurrencyParameter()
    :members:

--------------------

.. autoclass:: NamedDateTimeParameter()
    :members:
