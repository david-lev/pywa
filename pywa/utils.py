from __future__ import annotations

import asyncio
import functools
import json
import base64
import hashlib
import hmac
import dataclasses
import enum
import importlib
import warnings
import logging
from typing import Any, Callable, Protocol, TypeAlias, ClassVar

import httpx

try:
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.padding import PKCS7
    from cryptography.hazmat.primitives.asymmetric.padding import OAEP, MGF1, hashes
    from cryptography.hazmat.primitives.ciphers import algorithms, Cipher, modes
    from cryptography.hazmat.primitives.serialization import load_pem_private_key

    is_cryptography_installed = True
except ImportError:
    is_cryptography_installed = False

_logger = logging.getLogger(__name__)


HUB_VT = "hub.verify_token"
"""The key for the verify token in the query parameters of the webhook get request."""
HUB_CH = "hub.challenge"
"""The key for the challenge in the query parameters of the webhook get request."""
HUB_SIG = "X-Hub-Signature-256"
"""The header key for the signature in the webhook post request."""
MISSING: object | None = object()
"""A sentinel value to indicate a missing value to distinguish from ``None``."""


class FastAPI(Protocol):
    """Protocol for the `FastAPI <https://fastapi.tiangolo.com/>`_ app."""

    def get(self, path: str) -> Callable: ...

    def post(self, path: str) -> Callable: ...


class Flask(Protocol):
    """Protocol for the `Flask <https://flask.palletsprojects.com/>`_ app."""

    def route(self, rule: str, **options: Any) -> Callable: ...


class ServerType(enum.Enum):
    """Enum for the supported server types."""

    FASTAPI = ("FASTAPI", FastAPI, lambda: importlib.import_module("fastapi").FastAPI)
    FLASK = ("FLASK", Flask, lambda: importlib.import_module("flask").Flask)

    def __new__(cls, name: str, protocol: Protocol, server: Callable):
        obj = object.__new__(cls)
        obj._value_ = name
        obj.protocol = protocol
        obj.server = server
        return obj

    @classmethod
    def from_app(cls, app) -> ServerType | None:
        """Get the server type from the app."""
        for server_type in cls:
            try:
                if isinstance(app, server_type.server()):
                    return server_type
            except ImportError:
                pass

    @classmethod
    def protocols_names(cls) -> tuple[str, ...]:
        """Get the names of the protocols."""
        return tuple(server_type.protocol.__name__ for server_type in cls)


def is_installed(lib: str) -> bool:
    """Check if the cryptography library is installed."""
    try:
        importlib.import_module(lib)
        return True
    except ImportError:
        return False


class Version(enum.Enum):
    """
    Enum for the latest and minimum versions of the `Graph API <https://developers.facebook.com/docs/graph-api>`_ and
    `WhatsApp Flows <https://developers.facebook.com/docs/whatsapp/flows/changelogs>`_.

    - Use the constant to get the latest version. Example: ``WhatsApp(..., api_version=Version.GRAPH_API)``
    - Using the latest version can break your code if the API changes. Use constants for stability.
    - Use the ``min`` attribute to get the minimum version. Example: Version.GRAPH_API.min

    Attributes:
        GRAPH_API: (MIN_VERSION: str, LATEST_VERSION: str)
        FLOW_JSON: (MIN_VERSION: str, LATEST_VERSION: str)
        FLOW_DATA_API: (MIN_VERSION: str, LATEST_VERSION: str)
        FLOW_MSG: (MIN_VERSION: str, LATEST_VERSION: str)
    """

    # KEY = (MIN_VERSION: str, LATEST_VERSION: str)
    GRAPH_API = ("17.0", "23.0")
    FLOW_JSON = ("2.1", "7.2")
    FLOW_DATA_API = ("3.0", "3.0")
    FLOW_MSG = ("3", "3")

    def __new__(cls, min_version: str, latest_version: str):
        obj = object.__new__(cls)
        obj._value_ = latest_version
        obj.min = min_version
        return obj

    def __str__(self):
        """Required for the ``Version`` enum to be used as a string."""
        return self.value

    def validate_min_version(self, version: str):
        """Check if the given version is supported."""
        if float(version) < float(self.min):
            raise ValueError(
                f"{self.name}: version {version} is not supported. Minimum version is {self.min}."
            )


class CallbackURLScope(enum.Enum):
    """
    Enum for the callback URL scopes.

    Attributes:
        APP: https://developers.facebook.com/docs/graph-api/reference/app/subscriptions
        WABA: https://developers.facebook.com/docs/whatsapp/embedded-signup/webhooks/override#set-waba-alternate-callback
        PHONE: https://developers.facebook.com/docs/whatsapp/embedded-signup/webhooks/override#set-phone-number-alternate-callback
    """

    APP = enum.auto()
    WABA = enum.auto()
    PHONE = enum.auto()


class StrEnum(str, enum.Enum):
    """A string-based enum that allows for custom handling of missing values."""

    _check_value: Callable[[str], bool] | None = str.isupper
    """Check if the value needs to be modified or not."""
    _modify_value: Callable[[str], str] | None = str.upper
    """Modify the value if needed."""

    def __str__(self):
        """Return the string representation of the enum member."""
        return self.value

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.name}"

    def __init_subclass__(cls, *args, **kwargs):
        """Ensure that the enum has an 'UNKNOWN' member to handle missing values."""
        if list(cls) and not hasattr(
            cls, "UNKNOWN"
        ):  # in python3.10 __init_subclass__ does not have access to enum members
            raise TypeError(
                f"Enum {cls.__name__} must have an 'UNKNOWN' member to handle missing values."
            )
        return super().__init_subclass__(*args, **kwargs)

    @classmethod
    def _missing_(cls, value: str):
        """Handle missing values in the enum."""
        if callable(cls._check_value) and not cls._check_value(value):
            return cls(cls._modify_value(value))

        _logger.warning(
            "Unknown value '%s' for enum '%s'. Defaulting to `%s.UNKNOWN`.",
            value,
            cls.__name__,
            cls.__name__,
        )
        # noinspection PyUnresolvedReferences
        return cls.UNKNOWN


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class FromDict:
    """Allows to ignore extra fields when creating a dataclass from a dict."""

    # noinspection PyArgumentList
    @classmethod
    def from_dict(cls, data: dict, **kwargs):
        return cls(
            **{
                k: v
                for k, v in (data | kwargs).items()
                if k in (f.name for f in dataclasses.fields(cls))
            }
        )


class APIObject:
    """Base class for API objects that allows overriding field names."""

    _override_api_fields: ClassVar[dict[str, str]] = {}
    """Override API field names for this object."""

    @classmethod
    @functools.cache
    def _api_fields(cls, *args, **kwargs) -> tuple[str, ...]:
        return tuple(
            cls._override_api_fields.get(f.name, f.name)
            for f in dataclasses.fields(cls)
            if not f.name.startswith("_")
        )


FlowRequestDecryptor: TypeAlias = Callable[
    [str, str, str, str, str | None], tuple[dict, bytes, bytes]
]
"""
Type hint for the function that decrypts the request from WhatsApp Flow.

- All parameters need to be positional.
- See :py:func:`default_flow_request_decryptor` source code for an example.

Args:
    encrypted_flow_data_b64 (str): encrypted flow data
    encrypted_aes_key_b64 (str): encrypted AES key
    initial_vector_b64 (str): initial vector
    private_key (str): private key
    password (str): password for the private key. Optional.

Returns:
    tuple[dict, bytes, bytes]
    - decrypted_data (dict): decrypted data from the request
    - aes_key (bytes): AES key you should use to encrypt the response
    - iv (bytes): initial vector you should use to encrypt the response
"""


def default_flow_request_decryptor(
    encrypted_flow_data_b64: str,
    encrypted_aes_key_b64: str,
    initial_vector_b64: str,
    private_key: str,
    password: str = None,
) -> tuple[dict, bytes, bytes]:
    """
    The default global decryption function for decrypting data exchange requests from WhatsApp Flow.

    - This implementation follows the :class:`FlowRequestDecryptor` type hint.
    - This implementation requires ``cryptography`` to be installed. To install it, run ``pip3 install 'pywa[cryptography]'`` or ``pip3 install cryptography``.
    - This implementation was taken from the official documentation at
      `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/guides/implementingyourflowendpoint#python-django-example>`_.

    Example:

        Set the default global decryptor (This is indeed the default):

        >>> from pywa.utils import default_flow_request_decryptor
        >>> from pywa import WhatsApp
        >>> wa = WhatsApp(flows_request_decryptor=default_flow_request_decryptor, ...)

        Set the decryptor for a specific flow:

        >>> from pywa import WhatsApp
        >>> from pywa.types.flows import FlowRequest, FlowResponse
        >>> from pywa.utils import default_flow_request_decryptor
        >>> wa = WhatsApp(...)
        >>> @wa.on_flow_request("/sign-up-flow", request_decryptor=default_flow_request_decryptor)
        ... def on_sign_up_request(_: WhatsApp, flow: FlowRequest) -> FlowResponse | None: ...
    """

    flow_data = base64.b64decode(encrypted_flow_data_b64)
    iv = base64.b64decode(initial_vector_b64)
    encrypted_aes_key = base64.b64decode(encrypted_aes_key_b64)
    private_key = load_pem_private_key(
        data=private_key.encode("utf-8"),
        password=password.encode("utf-8") if password else None,
    )
    aes_key = private_key.decrypt(
        encrypted_aes_key,
        OAEP(
            mgf=MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None
        ),
    )
    encrypted_flow_data_body = flow_data[:-16]
    encrypted_flow_data_tag = flow_data[-16:]
    decryptor = Cipher(
        algorithms.AES(aes_key), modes.GCM(iv, encrypted_flow_data_tag)
    ).decryptor()
    decrypted_data_bytes = (
        decryptor.update(encrypted_flow_data_body) + decryptor.finalize()
    )
    decrypted_data = json.loads(decrypted_data_bytes.decode("utf-8"))
    return decrypted_data, aes_key, iv


FlowResponseEncryptor: TypeAlias = Callable[[dict, bytes, bytes], str]
"""
Type hint for the function that encrypts the response to WhatsApp Flow.

- All parameters need to be positional.
- See :py:func:`default_flow_response_encryptor` source code for an example.

Args:
    response (dict): response to encrypt
    aes_key (bytes): AES key
    iv (bytes): initial vector

Returns:
    encrypted_response (str): encrypted response to send back to WhatsApp Flow
"""


def default_flow_response_encryptor(response: dict, aes_key: bytes, iv: bytes) -> str:
    """
    The default global encryption function for encrypting data exchange responses to WhatsApp Flow.

    - This implementation follows the :class:`FlowResponseEncryptor` type hint.
    - This implementation requires ``cryptography`` to be installed. To install it, run ``pip3 install 'pywa[cryptography]'`` or ``pip3 install cryptography``.
    - This implementation was taken from the official documentation at
      `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/guides/implementingyourflowendpoint#python-django-example>`_.

    Example:

        Set the default global encryptor (This is indeed the default):

        >>> from pywa.utils import default_flow_response_encryptor
        >>> from pywa import WhatsApp
        >>> wa = WhatsApp(flows_response_encryptor=default_flow_response_encryptor, ...)

        Set the encryptor for a specific flow:

        >>> from pywa import WhatsApp
        >>> from pywa.types.flows import FlowRequest, FlowResponse
        >>> from pywa.utils import default_flow_response_encryptor
        >>> wa = WhatsApp(...)
        >>> @wa.on_flow_request("/sign-up-flow", response_encryptor=default_flow_response_encryptor)
        ... def on_sign_up_request(_: WhatsApp, flow: FlowRequest) -> FlowResponse | None: ...
    """

    flipped_iv = bytearray()
    for byte in iv:
        flipped_iv.append(byte ^ 0xFF)

    encryptor = Cipher(algorithms.AES(aes_key), modes.GCM(flipped_iv)).encryptor()
    return base64.b64encode(
        encryptor.update(json.dumps(response).encode("utf-8"))
        + encryptor.finalize()
        + encryptor.tag
    ).decode("utf-8")


def webhook_updates_validator(
    app_secret: str, request_body: bytes, x_hub_signature: str
) -> bool:
    """The webhook update validator for validating updates from WhatsApp."""
    signature = hmac.new(
        app_secret.encode("utf-8"), request_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, x_hub_signature.removeprefix("sha256="))


@dataclasses.dataclass(frozen=True, slots=True)
class FlowRequestDecryptedMedia:
    """
    Represents the decrypted media from a flow request.

    Attributes:
        media_id (str): The media ID.
        filename (str): The filename of the media.
        data (bytes): The decrypted media data.
    """

    media_id: str
    filename: str
    data: bytes

    def __iter__(self):
        """Allow iteration over the attributes."""
        warnings.warn(
            "flow_request_media_decryptor() is no longer return (media_id, filename, data) tuple, but FlowRequestDecryptedMedia object.",
            DeprecationWarning,
            stacklevel=2,
        )
        return iter((self.media_id, self.filename, self.data))


def flow_request_media_decryptor(
    encrypted_media: dict[str, str | dict[str, str]],
    dl_session: httpx.Client | None = None,
) -> FlowRequestDecryptedMedia:
    """
    Decrypt the encrypted media file from the flow request.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components/media_upload#endpoint>`_.
    - Use the .decrypt_media() shorthand method of the :class:`FlowRequest` class instead.
    - This implementation requires ``cryptography`` to be installed. To install it, run ``pip3 install 'pywa[cryptography]'`` or ``pip3 install cryptography``.

    Example:

        >>> from pywa import WhatsApp, types
        >>> wa = WhatsApp(...)
        >>> @wa.on_flow_request("/media-upload")
        ... def on_media_upload_request(_: WhatsApp, req: types.FlowRequest) -> types.FlowResponse | None:
        ...     dec = req.decrypt_media(key="driver_license", index=0)
        ...     with open(dec.filename, "wb") as file:
        ...         file.write(dec.data)
        ...     return req.respond(...)

    Args:
        encrypted_media (dict): encrypted media data from the flow request (see example above).
        dl_session (httpx.Client): download session. Optional.

    Returns:
        An object containing the media ID, filename, and decrypted data.

    Raises:
        HTTPStatusError: If the request to the CDN URL fails.
        ValueError: If any of the hash verifications fail.
    """
    res = (dl_session or httpx.Client()).get(encrypted_media["cdn_url"])
    res.raise_for_status()
    return FlowRequestDecryptedMedia(
        media_id=encrypted_media["media_id"],
        filename=encrypted_media["file_name"],
        data=_flow_request_media_decryptor(
            res.content, encrypted_media["encryption_metadata"]
        ),
    )


def _flow_request_media_decryptor(
    cdn_file: bytes, encryption_metadata: dict[str, str]
) -> bytes:
    """The actual implementation of the media decryption."""

    ciphertext = cdn_file[:-10]
    sha256 = hashlib.sha256(cdn_file)
    calculated_hash = base64.b64encode(sha256.digest()).decode()
    if calculated_hash != encryption_metadata["encrypted_hash"]:
        raise ValueError("CDN file hash verification failed")
    if (
        hmac.new(
            base64.b64decode(encryption_metadata["hmac_key"]),
            base64.b64decode(encryption_metadata["iv"]) + ciphertext,
            hashlib.sha256,
        ).digest()[:10]
        != cdn_file[-10:]
    ):
        raise ValueError("HMAC verification failed")
    decryptor = Cipher(
        algorithms.AES(base64.b64decode(encryption_metadata["encryption_key"])),
        modes.CBC(base64.b64decode(encryption_metadata["iv"])),
        backend=default_backend(),
    ).decryptor()
    decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = PKCS7(128).unpadder()
    decrypted_data = unpadder.update(decrypted_data) + unpadder.finalize()
    sha256 = hashlib.sha256(decrypted_data)
    if (
        base64.b64encode(sha256.digest()).decode()
        != encryption_metadata["plaintext_hash"]
    ):
        raise ValueError("Decrypted data hash verification failed")
    return decrypted_data


def rename_func(extended_with: str) -> Callable:
    """Rename function to avoid conflicts when registering the same function multiple times."""

    def inner(func: Callable):
        func.__name__ = f"{func.__name__}{extended_with}"
        return func

    return inner


def is_async_callable(obj: Any) -> bool:
    """Check if an object is an async callable."""
    while isinstance(obj, functools.partial):
        obj = obj.func

    return asyncio.iscoroutinefunction(obj) or (
        callable(obj) and asyncio.iscoroutinefunction(obj.__call__)
    )
