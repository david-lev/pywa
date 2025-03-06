"""This module contains the types related to named parameters for WhatsApp templates.

Named parameters can be used in both header components (text type only) and body components
of WhatsApp templates. They allow referencing template parameters by name instead of position,
making template usage more explicit and maintainable."""

from __future__ import annotations

import dataclasses
from typing import Any, Dict, List, Optional, Union

from .. import utils
from .template import ParamType, ComponentABC, ComponentType


__all__ = [
    "NamedParameter",
    "NamedTextParameter",
    "NamedCurrencyParameter",
    "NamedDateTimeParameter",
]


@dataclasses.dataclass(slots=True)
class NamedParameter:
    """
    Base class for named parameters in WhatsApp templates.
    
    This class is used to specify named parameters when sending templates.
    Named parameters can be used in both header components (text type only) and body components.
    
    Example using named parameters in body:
        >>> from pywa.types import Template
        >>> from pywa.types.named_parameter import NamedTextParameter
        >>> Template(
        ...     name='template_with_named_params',
        ...     language=Template.Language.ENGLISH_US,
        ...     body=[
        ...         NamedTextParameter(parameter_name='customer_name', value='John Doe'),
        ...         NamedTextParameter(parameter_name='order_id', value='9128312831'),
        ...     ]
        ... )
    
    Example using named parameters in header:
        >>> from pywa.types import Template
        >>> Template(
        ...     name='template_with_header_param',
        ...     language=Template.Language.ENGLISH_US,
        ...     header=Template.TextValue(value='John Doe', parameter_name='customer_name'),
        ...     body=[
        ...         Template.TextValue(value='Welcome to our service!'),
        ...     ]
        ... )
    
    Attributes:
        parameter_name: The name of the parameter as defined in the template.
    """
    parameter_name: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the named parameter to a dictionary."""
        raise NotImplementedError("Subclasses must implement this method")


@dataclasses.dataclass(slots=True)
class NamedTextParameter(NamedParameter, ComponentABC):
    """
    Represents a named text parameter in a template.
    
    Example:
        >>> from pywa.types.named_parameter import NamedTextParameter
        >>> NamedTextParameter(parameter_name='customer_name', value='John Doe')
    
    Attributes:
        parameter_name: The name of the parameter as defined in the template.
        value: The value to assign to the named parameter.
    """
    value: str
    type: ParamType = dataclasses.field(
        default=ParamType.TEXT, init=False, repr=False
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the named text parameter to a dictionary."""
        return {
            "type": self.type.value,
            "parameter_name": self.parameter_name,
            "text": self.value
        }


@dataclasses.dataclass(slots=True)
class NamedCurrencyParameter(NamedParameter, ComponentABC):
    """
    Represents a named currency parameter in a template.
    
    Example:
        >>> from pywa.types.named_parameter import NamedCurrencyParameter
        >>> NamedCurrencyParameter(
        ...     parameter_name='price',
        ...     fallback_value='$100.00',
        ...     code='USD',
        ...     amount_1000=100000
        ... )
    
    Attributes:
        parameter_name: The name of the parameter as defined in the template.
        fallback_value: Default text if localization fails.
        code: ISO 4217 currency code (e.g. USD, EUR, etc.).
        amount_1000: Amount multiplied by 1000.
    """
    fallback_value: str
    code: str
    amount_1000: int
    type: ParamType = dataclasses.field(
        default=ParamType.CURRENCY, init=False, repr=False
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the named currency parameter to a dictionary."""
        return {
            "type": self.type.value,
            "parameter_name": self.parameter_name,
            "currency": {
                "fallback_value": self.fallback_value,
                "code": self.code,
                "amount_1000": self.amount_1000
            }
        }


@dataclasses.dataclass(slots=True)
class NamedDateTimeParameter(NamedParameter, ComponentABC):
    """
    Represents a named date time parameter in a template.
    
    Example:
        >>> from pywa.types.named_parameter import NamedDateTimeParameter
        >>> NamedDateTimeParameter(
        ...     parameter_name='delivery_date',
        ...     fallback_value='January 1, 2025'
        ... )
    
    Attributes:
        parameter_name: The name of the parameter as defined in the template.
        fallback_value: Default text if localization fails.
    """
    fallback_value: str
    type: ParamType = dataclasses.field(
        default=ParamType.DATE_TIME, init=False, repr=False
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the named date time parameter to a dictionary."""
        return {
            "type": self.type.value,
            "parameter_name": self.parameter_name,
            "date_time": {
                "fallback_value": self.fallback_value
            }
        }
