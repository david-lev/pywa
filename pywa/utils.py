from __future__ import annotations

import base64
import json
import dataclasses
import enum
import importlib
from typing import Any, Callable, Protocol, TypeAlias


def is_fastapi_app(app):
    """Check if the app is a FastAPI app."""
    try:
        return isinstance(app, importlib.import_module("fastapi").FastAPI)
    except ImportError:
        return False


def is_flask_app(app):
    """Check if the app is a Flask app."""
    try:
        return isinstance(app, importlib.import_module("flask").Flask)
    except ImportError:
        return False


def is_cryptography_installed():
    """Check if the cryptography library is installed."""
    try:
        importlib.import_module("cryptography")
        return True
    except ImportError:
        return False


class Version(enum.Enum):
    """
    Enum for the latest and minimum versions of the WhatsApp API.

    - Use the constant to get the latest version. Example: ``WhatsApp(..., api_version=Version.GRAPH_API)``
    - Use the ``min`` attribute to get the minimum version. Example: Version.GRAPH_API.min

    Attributes:
        GRAPH_API: (MIN_VERSION: str, LATEST_VERSION: str)
        FLOW_JSON: (MIN_VERSION: str, LATEST_VERSION: str)
        FLOW_DATA_API: (MIN_VERSION: str, LATEST_VERSION: str)
        FLOW_MSG: (MIN_VERSION: str, LATEST_VERSION: str)
    """

    # KEY = (MIN_VERSION: str, LATEST_VERSION: str)
    GRAPH_API = ("17.0", "18.0")
    FLOW_JSON = ("2.1", "3.1")
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


class FastAPI(Protocol):
    def get(self, path: str) -> Callable:
        ...

    def post(self, path: str) -> Callable:
        ...


class Flask(Protocol):
    def route(self, rule: str, **options: Any) -> Callable:
        ...


FlowRequestDecryptor: TypeAlias = (
    Callable[[str, str, str, str, str | None], tuple[dict, bytes, bytes]],
)
"""
Type hint for the function that decrypts the request from WhatsApp Flow.

- All parameters need to be positional.

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
    The default decryption function for WhatsApp Flow.

    - This implementation requires ``cryptography`` to be installed.
    - To install it, run ``pip3 install 'pywa[cryptography]'`` or ``pip3 install cryptography``.
    - This implementation was taken from the official documentation at
      `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/guides/implementingyourflowendpoint#python-django-example>`_.


    Returns:
        decrypted_data: decrypted data from the request
        aes_key: AES key you should use to encrypt the response
        iv: initial vector you should use to encrypt the response
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

Args:
    response (dict): response to encrypt
    aes_key (bytes): AES key
    iv (bytes): initial vector

Returns:
    encrypted_response (str): encrypted response to send back to WhatsApp Flow
"""


def default_flow_response_encryptor(response: dict, aes_key: bytes, iv: bytes) -> str:
    """
    The default encryption function for WhatsApp Flow.

    - This implementation requires ``cryptography`` to be installed.
    - To install it, run ``pip3 install 'pywa[cryptography]'`` or ``pip3 install cryptography``.
    - This implementation was taken from the official documentation at
      `developers.facebook.com <https://developers.facebook.com/docs/whatsapp/flows/guides/implementingyourflowendpoint#python-django-example>`_.

    Returns:
        encrypted_response: encrypted response to send back to WhatsApp Flow
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


def rename_func(extended_with: str) -> Callable:
    """Rename function to avoid conflicts when registering the same function multiple times."""

    def inner(func: Callable):
        func.__name__ = f"{func.__name__}{extended_with}"
        return func

    return inner
