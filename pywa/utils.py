from __future__ import annotations

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
from typing import Any, Callable, Protocol, TypeAlias

import httpx

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


def is_requests_and_err(session) -> tuple[bool, type[Exception]]:
    """Check if the given object is a requests/httpx session and return the error type."""
    try:
        if isinstance(session, importlib.import_module("requests").Session):
            return True, importlib.import_module("requests").HTTPError
        raise ImportError
    except ImportError:
        return False, importlib.import_module("httpx").HTTPStatusError


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
    GRAPH_API = ("17.0", "19.0")
    FLOW_JSON = ("2.1", "5.1")
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


class StrEnum(str, enum.Enum):
    """Enum where the values are also (and must be) strings."""

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.name}"


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
    from cryptography.hazmat.primitives.asymmetric.padding import OAEP, MGF1, hashes
    from cryptography.hazmat.primitives.ciphers import algorithms, Cipher, modes
    from cryptography.hazmat.primitives.serialization import load_pem_private_key

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
    from cryptography.hazmat.primitives.ciphers import algorithms, Cipher, modes

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


def _download_cdn_file_sync(session: httpx.Client, url: str) -> bytes:
    response = session.get(url)
    response.raise_for_status()
    return response.content


async def _download_cdn_file_async(session: httpx.AsyncClient, url: str) -> bytes:
    response = await session.get(url)
    response.raise_for_status()
    return response.content


def flow_request_media_decryptor_sync(
    encrypted_media: dict[str, str | dict[str, str]],
    dl_session: httpx.Client | None = None,
) -> tuple[str, str, bytes]:
    """
    Decrypt the encrypted media file from the flow request.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components/media_upload#endpoint>`_.
    - This implementation requires ``cryptography`` to be installed. To install it, run ``pip3 install 'pywa[cryptography]'`` or ``pip3 install cryptography``.
    - This implementation is synchronous. Use this if your flow request callback is synchronous, otherwise use :func:`flow_request_media_decryptor_async`.

    Example:

        >>> from pywa import WhatsApp, utils, types
        >>> wa = WhatsApp(...)
        >>> @wa.on_flow_request("/media-upload")
        ... def on_media_upload_request(_: WhatsApp, flow: types.FlowRequest) -> types.FlowResponse | None:
        ...     encrypted_media = flow.data["driver_license"][0]
        ...     media_id, filename, decrypted_data = utils.flow_request_media_decryptor_sync(encrypted_media)
        ...     with open(filename, "wb") as file:
        ...         file.write(decrypted_data)
        ...     return types.FlowResponse(...)

    Args:
        encrypted_media (dict): encrypted media data from the flow request (see example above).
        dl_session (httpx.Client): download session. Optional.

    Returns:
        tuple[str, str, bytes]
        - media_id (str): media ID
        - filename (str): media filename
        - decrypted_data (bytes): decrypted media file

    Raises:
        ValueError: If any of the hash verifications fail.
    """
    is_requests, _ = is_requests_and_err(dl_session)
    if is_requests:
        _logger.warning(
            "Using `requests.Session` is deprecated and will be removed in future versions. "
            "Please use `httpx.Client` instead."
        )
    cdn_file = _download_cdn_file_sync(
        dl_session or httpx.Client(), encrypted_media["cdn_url"]
    )
    return (
        encrypted_media["media_id"],
        encrypted_media["file_name"],
        _flow_request_media_decryptor(cdn_file, encrypted_media["encryption_metadata"]),
    )


async def flow_request_media_decryptor_async(
    encrypted_media: dict[str, str | dict[str, str]],
    dl_session: httpx.AsyncClient | None = None,
) -> tuple[str, str, bytes]:
    """
    Decrypt the encrypted media file from the flow request.

    - Read more at `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/reference/flowjson/components/media_upload#endpoint>`_.
    - This implementation requires ``cryptography`` to be installed. To install it, run ``pip3 install 'pywa[cryptography]'`` or ``pip3 install cryptography``.
    - This implementation is asynchronous. Use this if your flow request callback is asynchronous, otherwise use :func:`flow_request_media_decryptor_sync`.

    Example:

        >>> from pywa import WhatsApp, utils, types
        >>> wa = WhatsApp(...)
        >>> @wa.on_flow_request("/media-upload")
        ... async def on_media_upload_request(_: WhatsApp, flow: types.FlowRequest) -> types.FlowResponse | None:
        ...     encrypted_media = flow.data["driver_license"][0]
        ...     media_id, filename, decrypted_data = await utils.flow_request_media_decryptor_async(encrypted_media)
        ...     with open(filename, "wb") as file:
        ...         file.write(decrypted_data)
        ...     return types.FlowResponse(...)

    Args:
        encrypted_media (dict): encrypted media data from the flow request (see example above).
        dl_session (httpx.AsyncClient): download session. Optional.

    Returns:
        tuple[str, str, bytes]
        - media_id (str): media ID
        - filename (str): media filename
        - decrypted_data (bytes): decrypted media file

    Raises:
        ValueError: If any of the hash verifications fail.
    """
    cdn_file = await _download_cdn_file_async(
        dl_session or httpx.AsyncClient(), encrypted_media["cdn_url"]
    )
    return (
        encrypted_media["media_id"],
        encrypted_media["file_name"],
        _flow_request_media_decryptor(cdn_file, encrypted_media["encryption_metadata"]),
    )


def _flow_request_media_decryptor(
    cdn_file: bytes, encryption_metadata: dict[str, str]
) -> bytes:
    """The actual implementation of the media decryption."""
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.padding import PKCS7
    from cryptography.hazmat.backends import default_backend

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


def deprecated_func(use_instead: str | None) -> Callable:
    """Mark a function as deprecated."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            msg = (
                f"Function `{func.__name__}` is deprecated and will be removed in a future version"
                + (f". Use `{use_instead}` instead." if use_instead else ".")
            )
            warnings.simplefilter("always", DeprecationWarning)
            warnings.warn(message=msg, category=DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        return wrapper

    return decorator
