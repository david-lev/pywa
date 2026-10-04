import base64
import io
import json
import logging
import pathlib
import re
import warnings

import httpx
import pytest
from starlette.applications import Starlette

from pywa import WhatsApp
from pywa import utils as pywa_utils
from pywa._logging import (
    ColorFormatter,
    _color_enabled,
    bind_update_logger,
    emit_banner,
    get_update_hash,
    resolve_log_level,
    setup_console_logging,
)
from pywa.api import GraphAPI
from pywa.errors import PywaWarning, WhatsAppError
from pywa.types import MessageType
from pywa.types.base_update import RawUpdate
from pywa_async import WhatsApp as WhatsAppAsync


def test_webhook_updates_validator():
    assert pywa_utils.webhook_updates_validator(
        app_secret="1222e786b144d0e85b9f365372d93676",  # This secret key is already reset
        request_body=b'{"object":"whatsapp_business_account","entry":[{"id":"264937493375603","changes":[{"value":{"messaging_product":"whatsapp","metadata":{"display_phone_number":"15550953877","phone_number_id":"277321005464405"},"contacts":[{"profile":{"name":"PyWa Tests"},"wa_id":"972544401243"}],"messages":[{"from":"972544401243","id":"wamid.HBgMOTcyNTQ0NDAxMjQzFQIAEhggM0RFQTNCMEEwRTY3QzUwODYzMDc4NjQ4QzM4ODAxM0YA","timestamp":"1730231903","text":{"body":"Hey there! I am using PyWa."},"type":"text"}]},"field":"messages"}]}]}',
        x_hub_signature="sha256=54edfa1d7259e0eb13c677cc7d73d1b5c86cfa12433d19156e058ab9251bc441",
    )


# This private key is already reset
private_key = """
-----BEGIN ENCRYPTED PRIVATE KEY-----
MIIFJDBWBgkqhkiG9w0BBQ0wSTAxBgkqhkiG9w0BBQwwJAQQkgClH0obPRRd3cmr
s0LvRAICCAAwDAYIKoZIhvcNAgkFADAUBggqhkiG9w0DBwQIWxsUnYjosHEEggTI
tIwws0TcJNJ+IoMfNfalxb8FpV8JzIXNPKoS2vBNhni3F6tk6tYSsBW7p5Wl/1jv
0fmf6iZhGgidFT5KvxRI7Z9FyD4FAKKxMsIsrxdqblupaB/2L1dHM2foBmKZTKVP
pMkiGYCRM+uPQWao/etBvTf1IKQw5phFJ6J/NVhlU6hSh3SjMp9CN4Xy6rA7wcfu
yYfrSUBHoCZZMvdWkCxo9sQ0N/nvU1FpBO0ZZQ+WDRKKg3g8BD8jWKRVM+uzZdVx
oWLoqkIWlNuCbObYsWvK07q9qryG0WeeZtPRti6Tp/TW2NMSqIN5Zx1jHLAYPU0V
3fgt3TmHPphy8etyXEg7PBJToCgTw6snnDqQDJm4nfJPg9UxxUvkkN8Tk+5P3o/0
E2Hf3RhYIqraKhuZAToA5Isniez/L/O5Fyjye0ShOFF9auhsmLDKbdG6wL+2CX1+
cQAash4HE2Xlj9v2iVC5mlnU9e7F1EyhJNAkmbr+i2z+93Wp/XytAx9xGV6lt7J8
gv454dCSQ5brByM/D12yyB5mcKX73MkaECa2iu/qH30H10S91IgiLUOQsS9A8ABi
S32U9SlYGfwlyV7izOXiS5vnk2XiihYFKPIdoNgcq3FPDXZoJr9u/ipZl/viTzWP
2V9DTODpTWuERIUCi8Lrg82HA62yNLO6Z5ib7+oHgpsTrhxWbqvxa8T4EL7V2Hx+
AqD2/M9easd2Atl6mI8uekjndL8sKNJ2kNlG54PMddgZzoIMYPnYp0ZPCtds+KIj
pwHK0nGL+kih0R9FLHLm0YKIYgD/i13N0vD+qSd0/PC66Bcnm5CqDlOYMyweBzvv
TrnUgTCUyMVGbKJ4mpBMHQOSoVfGuE18zkfvoUmqXNEUiOj3v61ODs50zrz9GzeL
r8mehVuSY82CDqPM7vbJS+UIgrPi9cqhxv1APcV+FW+nDux3hyvyG6mHxSOoaTz/
tmAXqxZ7IJKRJW+p2Qw9FjSrQOjjfCDWRKNd3m7WhHlceKWuh6fargYbs3A7jIf7
+BaGTOfx/EcbgWrrvQ6FgdNqiijUfxmk0nTtFAaAACs/V9wOiqZLCBP+Uqv5GL7T
X2+yrJtpe2A/Jc/0VC7utOK7HPHO9y+mqkFm2SzCUnN4PDCIm6L4yDdzdjsAxj6n
YcG2AYnZhPGstAXYeQThbbgnOa76hpr4FDFb7y5OMQvbb7uDAs6goHd8yrlGdMub
KqalC3IWh9RbnDbXQLFkTG9ijaswbKu0Q4DRIjVtN/RRlYrLqKE/P/uy99GQ+zxC
vUSUci1YVbkGaTC7OMeLWf2gPptcEOXRqZhluEFIxIeMD2ykv50nfZWl6wBQRyas
+MsEoHCZYtb8ZgA8adAh0bFo/zsh9nu/HeXN6Rk0DIzBv31t6bIubsZ8VAybVetG
vkivZ9yrc5R/lNYCmIIk0YqYr4IU8GMru7l11Ojui08RTESwZ5KcsH1s9CFWuUG4
D8SsbEVopM4IbnZi0X5WWyHreEjfBrcP6+/o+3vzi+sq76v17PXlalypi4kuUjAD
78w/o5vWmS+DWkrr0DqmQZ3nFX3fcrBbP1blr1Nlb5iv3Rwy7tVMF87tpgrnk/4Y
337xpCvNLXW0EwL6KdWqJ7Y6KLjLDmeT
-----END ENCRYPTED PRIVATE KEY-----
"""


def test_flow_private_key_is_parsed_once_per_key():
    """The private key does not change per request, so it is not re-parsed per request."""
    pywa_utils._load_flow_private_key.cache_clear()

    first = pywa_utils._load_flow_private_key(private_key, "pywa")
    second = pywa_utils._load_flow_private_key(private_key, "pywa")
    assert first is second
    assert pywa_utils._load_flow_private_key.cache_info().hits == 1

    # The password is part of the cache key, so a wrong one is not served
    # the key a correct one loaded.
    try:
        pywa_utils._load_flow_private_key(private_key, "not-the-password")
    except ValueError:
        pass
    else:
        raise AssertionError("a wrong password must not be served the cached key")


def test_default_flow_request_decryptor_encryptor():
    payload = {
        "encrypted_flow_data": "sCTmBCqjs0GkkX6n/nyZDuyjpaijuelY3I/8rlr1ZIEymEzCMnDGQdxQ9OGaKw0CEaWSgc/GLhuixa8NTQNYXAyVfTaU9H2FWEabWUb8nbZYRdYy81XHUkDCodl4SvBhhufEag==",
        "encrypted_aes_key": "gSTeWDqfKqo1eL73VstmrMm5k5lymwUwXCfuxauPFPoW7Ji9dgcG74Y6YRtoYOAch6Z/AgrR7EAlsRi/s8xT/Gx2WWz6zfcXPUQVpoIlp7EgC+HmmA2ZK64g/107yL+vKoUdL0mWJHQf1ml12HszBxOtNlW+7GAMPESNDqGpgy1R3Zgz/luStp2INtigps9w2j9+Ktp0smqxHqpUkBWp8xxoWVvzPK4H0jcFm7sjFMpiJ1e1EjApo7iDqldys0tMRC+KoOjJVD6aq1gY5s2yYL7iCXXgEAKJItTk/4/mbWWNkRtd9NoEGnMHilcjYOzlUCHehAO9fos+WCLE87JAXw==",
        "initial_vector": "5eCmDjs+VAJwdo5caZtgbw==",
    }
    decrypted_data, aes_key, iv = pywa_utils.default_flow_request_decryptor(
        encrypted_flow_data_b64=payload["encrypted_flow_data"],
        encrypted_aes_key_b64=payload["encrypted_aes_key"],
        initial_vector_b64=payload["initial_vector"],
        private_key=private_key,
        password="pywa",
    )
    assert decrypted_data == {
        "data": {},
        "flow_token": "my_flow_token",
        "screen": "",
        "action": "INIT",
        "version": "3.0",
    }

    assert (
        pywa_utils.default_flow_response_encryptor(
            response={"version": "3.0", "screen": "SUCCESS", "data": {"key": "value"}},
            aes_key=aes_key,
            iv=iv,
        )
        == "FBEoV73B8mnSt+nzfurVK704zkwHsr1uu/m953h5vNdri5G4Pe/BoDTh6SgzgjrrZ4iP12GO3kti8YW7Tn1KibKaRf8LE/gps2ATJq3nWSCI"
    )


def test_flow_request_media_decryptor():
    assert (
        pywa_utils._flow_request_media_decryptor(
            cdn_file=b"\x84a\xd2~\xd7\xe5f\xf0T$Yv\xa3\xa3\xb0\xc3\xa9>+\xca7\xd5\x81\x0cw\xe7/a\x92Q\xce\xfe\xa8>\xeaP\x915\x0b[/\x83\xd23gB\xd4\xf0\xd4c\x95w\xc6\xa2>\xb38\x7f[\xef\x87\x8d,Y\xce\xe9\xe3\xaf\x88\x04\x91e\xfc\xf9dK\\\xd0\x8e^\xa4\x88\xd7\x101JI2T\x13\xe1\xf5BR\r\x1et\xdeO@K\xbd\x95DQ\xb1(\x00\x84\xe5\xed\xe90\xf0\xd3k\xb0\xf2\x01\x88(7%\xd0\xc63<\x91\x96\x9c\xd4*\xbb.\xed\xa1D\x01D\xdd\xfa\x96eK\xd9\xe44H\x16\x0e\xb8eC\xfe\x1a\xfb\x14/\x1b\x81\x93\xef\xc5\xc2}\xe1\xd2\x9d\xca\xdf\x96\xb0V\xe96\xfcL9\x82KE\xfe\x11\xea\x8a\x9e\x13{\x19\xaba\x05\xcaW\x11\xa3#B\xa2\x93\x95&\x925~\xec\xc5Qt\x16\xed\x88\r\x16\xeb\x06$\xd8\x1c\x9d\xcc\xbec\x9f\x9e\x0bkz/\xffK\x18\x8ag(wO9t\xd7\xcc\xd7za\x94\xe3\x85a<\x8f<\xb6\x19]\xfev\x92\xa7T\xb6\x0cE\x86\x04\xfb\xdb\xb8\xb2\x93\x1d\x12\xa3>\xb1\x01vR\xde\xcb\xdf\xb2\xb3E\xdaHv\xcbg\x1bZ\xd0\x82)\xda\x14\xadL\x9b\x99\x03\n\xa9p\xda8\x11`\xc8\xfe\xeaAe\x85\xd7\x9c\r\x7f\x88\xd9 \xaf\xc8\x93\x98\xe7\xe1 Y\xc2\xc6\xc8\x9b9\x9bf\xa2\x84DL\xb7\xfc\xab\x1c\xd3yH\xb5\xedE\xc9\xddi\xd1f\xff\x18\x84\xcd\xbc\x80\x91\xa4\x04gZ\x85\x9ae\xd8\xc1Pf+\xaa=\x08\x9b~0\x16\x96\x9b\xd3\x13]\xb1Z\xca\xd4\xf8(\xf4\x14\x02\xb5\x13R\x06wY\xc4\xf3\xe6;\x10T\xca\t\xf5C\xe6)5\xf7\xef\xd1DW+\xf5\x94\xc0y\x9d\xdd\x90\x81\x1c)r}NE\x981m@\xed\x9fq\xfb^\xe0\xfaR;\xdf\x16\xce\x081\x95i={\xfeK]",
            encryption_metadata={
                "encryption_key": "202pQMDtZoAMwJwZJFVPqQOgdJRBahBmGywwSXz5tAY=",
                "hmac_key": "A/72TYylRAHTg/CdXpBtC6T6qcJ2C7Cf2qzZ/hqVASM=",
                "iv": "t1MOy02KXLbsH+NYkqkRXQ==",
                "plaintext_hash": "ZvSgxwXg5fWL7v7ggGHXtMCZYTf/nVFasOdX0p6kiP4=",
                "encrypted_hash": "pDhRHkyevzgkdg5ObY+MfzW5J6/ObZj/OrmAvyUeYA8=",
            },
        )
        == b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00\x84\x00\x06\x06\x06\x06\x07\x06\x07\x08\x08\x07\n\x0b\n\x0b\n\x0f\x0e\x0c\x0c\x0e\x0f\x16\x10\x11\x10\x11\x10\x16"\x15\x19\x15\x15\x19\x15"\x1e$\x1e\x1c\x1e$\x1e6*&&*6>424>LDDL_Z_||\xa7\x01\x06\x06\x06\x06\x07\x06\x07\x08\x08\x07\n\x0b\n\x0b\n\x0f\x0e\x0c\x0c\x0e\x0f\x16\x10\x11\x10\x11\x10\x16"\x15\x19\x15\x15\x19\x15"\x1e$\x1e\x1c\x1e$\x1e6*&&*6>424>LDDL_Z_||\xa7\xff\xc2\x00\x11\x08\x00\x01\x00\x01\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\'\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x06\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x10\x03\x10\x00\x00\x02\xaa\x07\xff\xc4\x00\x02\xff\xda\x00\x0c\x03\x01\x00\x02\x00\x03\x00\x00\x00!\x03\xff\xc4\x00\x02\xff\xda\x00\x0c\x03\x01\x00\x02\x00\x03\x00\x00\x00\x10\xf3\xff\xc4\x00\x14\x11\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x02\x01\x01?\x00\x7f\xff\xc4\x00\x14\x11\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x03\x01\x01?\x00\x7f\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x01?\x02\x7f\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x01?!\x7f\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x01?\x10\x7f\xff\xd9'
    )


class _FakeTTYStream(io.StringIO):
    def isatty(self):
        return True


class _FakeNonTTYStream(io.StringIO):
    def isatty(self):
        return False


def test_color_enabled_respects_no_color(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    assert _color_enabled(_FakeTTYStream()) is False


def test_color_enabled_respects_force_color(monkeypatch):
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.delenv("NO_COLOR", raising=False)
    assert _color_enabled(_FakeNonTTYStream()) is True


def test_color_enabled_auto_detects_tty(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    assert _color_enabled(_FakeTTYStream()) is True
    assert _color_enabled(_FakeNonTTYStream()) is False


def _make_record(msg: str, level: int = logging.INFO) -> logging.LogRecord:
    return logging.LogRecord("pywa.server", level, __file__, 1, msg, None, None)


def test_color_formatter_emits_ansi_when_enabled():
    formatter = ColorFormatter(use_color=True)
    output = formatter.format(_make_record("hello"))
    assert "\x1b[" in output


def test_color_formatter_plain_when_disabled():
    formatter = ColorFormatter(use_color=False)
    output = formatter.format(_make_record("hello"))
    assert "\x1b[" not in output


def test_bind_update_logger_includes_hash_and_endpoint(caplog):
    caplog.set_level(logging.INFO, logger="pywa.test_bind")
    logger = logging.getLogger("pywa.test_bind")
    log = bind_update_logger(logger, "abcdef0123456789", "/webhook")
    log.info("hello")
    assert "[abcdef01] [/webhook] hello" in caplog.records[-1].getMessage()


def test_plain_logger_omits_context(caplog):
    caplog.set_level(logging.INFO, logger="pywa.test_plain")
    logger = logging.getLogger("pywa.test_plain")
    logger.info("hello")
    assert caplog.records[-1].getMessage() == "hello"


def test_resolve_log_level_trace():
    assert resolve_log_level("trace") == 5
    assert logging.getLevelName(5) == "TRACE"


def test_resolve_log_level_int_passthrough():
    assert resolve_log_level(logging.DEBUG) == logging.DEBUG


def test_resolve_log_level_invalid():
    with pytest.raises(ValueError):
        resolve_log_level("nonsense")


@pytest.fixture
def clean_logging():
    root = logging.getLogger()
    affected_loggers = [
        "pywa",
        "pywa.cli",
        "uvicorn.error",
        "uvicorn.access",
    ]
    original_handlers = root.handlers[:]
    original_levels = {name: logging.getLogger(name).level for name in affected_loggers}
    # pytest's own capture handlers live on root; start from a root nobody configured
    root.handlers[:] = []
    if hasattr(logging.getLogger("pywa"), "_pywa_configured_level"):
        del logging.getLogger("pywa")._pywa_configured_level
    yield
    root.handlers[:] = original_handlers
    if hasattr(logging.getLogger("pywa"), "_pywa_configured_level"):
        del logging.getLogger("pywa")._pywa_configured_level
    for name, level in original_levels.items():
        logging.getLogger(name).setLevel(level)


def _drop_pytest_root_handlers():
    # pytest re-attaches its capture handler to root for the `call` phase, after fixtures ran
    logging.getLogger().handlers.clear()


def test_setup_console_logging_idempotent(clean_logging):
    _drop_pytest_root_handlers()
    setup_console_logging("info", stream=io.StringIO())
    setup_console_logging("info", stream=io.StringIO())
    root = logging.getLogger()
    sentinel_handlers = [
        h for h in root.handlers if getattr(h, "_pywa_console_handler", False)
    ]
    assert len(sentinel_handlers) == 1


def test_setup_console_logging_sets_pywa_level_not_root(clean_logging):
    root_level_before = logging.getLogger().level
    setup_console_logging("debug", stream=io.StringIO())
    assert logging.getLogger("pywa").getEffectiveLevel() == logging.DEBUG
    assert logging.getLogger().level == root_level_before


def test_setup_console_logging_warns_on_debug(clean_logging):
    _drop_pytest_root_handlers()
    stream = io.StringIO()
    setup_console_logging("debug", stream=stream)
    out = stream.getvalue()
    assert "personal data" in out
    assert "py.warnings" not in out  # a plain log line, not a captured `warnings.warn`


def test_setup_console_logging_no_warning_on_info(clean_logging):
    stream = io.StringIO()
    setup_console_logging("info", stream=stream)
    assert "personal data" not in stream.getvalue()


def test_setup_console_logging_no_duplicate_warning_for_same_level(clean_logging):
    _drop_pytest_root_handlers()
    stream = io.StringIO()
    setup_console_logging("debug", stream=stream)
    setup_console_logging("debug", stream=stream)
    assert stream.getvalue().count("personal data") == 1


def test_setup_console_logging_respects_host_configured_root(clean_logging):
    host_stream = io.StringIO()
    host_handler = logging.StreamHandler(host_stream)
    logging.getLogger().addHandler(host_handler)
    ours = io.StringIO()
    setup_console_logging("info", stream=ours)
    logging.getLogger("pywa.test_host").info("hello")
    assert host_stream.getvalue().count("hello") == 1
    assert ours.getvalue() == ""  # no second handler, so no duplicate output
    assert logging.getLogger("pywa").getEffectiveLevel() == logging.INFO


def test_emit_banner_is_plain_stderr_text():
    stream = io.StringIO()
    emit_banner(["Title", "a: 1"], stream=stream)
    out = stream.getvalue()
    assert "Title" in out and "a: 1" in out
    assert "INFO" not in out and "pywa." not in out


def test_setup_console_logging_keeps_uvicorn_chatter_quiet_regardless_of_level(
    clean_logging,
):
    setup_console_logging("debug", stream=io.StringIO())
    assert logging.getLogger("uvicorn.error").getEffectiveLevel() == logging.WARNING
    assert logging.getLogger("uvicorn.asgi").getEffectiveLevel() == logging.WARNING


def test_setup_console_logging_keeps_uvicorn_access_at_info(clean_logging):
    setup_console_logging("warning", stream=io.StringIO())
    assert logging.getLogger("uvicorn.access").getEffectiveLevel() == logging.INFO


_MESSAGE_UPDATE = json.loads(
    pathlib.Path("tests/data/updates/message.json").read_text()
)["text"]
_PHONE_NUMBER = "972987654321"
_MESSAGE_TEXT = "Body Text"
_CONTACT_NAME = "Test Name"


def _make_client() -> WhatsApp:
    return WhatsApp(phone_id="1122334455667", token="xyz", filter_updates=False)


def test_pii_absent_at_info(caplog):
    wa = _make_client()
    caplog.set_level(logging.INFO, logger="pywa")
    wa.webhook_update_handler(json.dumps(_MESSAGE_UPDATE).encode())
    combined = "\n".join(r.getMessage() for r in caplog.records)
    assert _PHONE_NUMBER not in combined
    assert _MESSAGE_TEXT not in combined


def test_pii_present_at_debug(caplog):
    wa = _make_client()
    caplog.set_level(logging.DEBUG, logger="pywa")
    wa.webhook_update_handler(json.dumps(_MESSAGE_UPDATE).encode())
    combined = "\n".join(r.getMessage() for r in caplog.records)
    assert _PHONE_NUMBER in combined
    assert _MESSAGE_TEXT in combined


_UNKNOWN_SHAPE_UPDATE = {
    "object": "whatsapp_business_account",
    "entry": [
        {
            "id": "1234567890987654321",
            "changes": [
                {
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "972123456789",
                            "phone_number_id": "1122334455667",
                        },
                        "contacts": [
                            {
                                "profile": {"name": _CONTACT_NAME},
                                "wa_id": _PHONE_NUMBER,
                            }
                        ],
                    },
                    "field": "messages",
                }
            ],
        }
    ],
}


def test_unknown_update_shape_does_not_leak_payload_at_warning(caplog):
    wa = _make_client()
    caplog.set_level(logging.WARNING, logger="pywa")
    encoded = json.dumps(_UNKNOWN_SHAPE_UPDATE).encode()
    raw = RawUpdate(encoded, hmac_header=None, update_hash=get_update_hash(encoded))
    wa._get_handler_type(raw)
    warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert warning_records
    combined = " ".join(r.getMessage() for r in warning_records)
    assert _CONTACT_NAME not in combined
    assert _PHONE_NUMBER not in combined


def test_call_handlers_summary_line(caplog):
    wa = _make_client()
    caplog.set_level(logging.INFO, logger="pywa")
    wa.webhook_update_handler(json.dumps(_MESSAGE_UPDATE).encode())
    assert any(
        re.search(r"\[.{8}] Message\(text\) wamid\.\S+ -> ", r.getMessage())
        for r in caplog.records
    )


def test_info_summary_names_update_and_callback_without_pii(caplog):
    wa = _make_client()
    caplog.set_level(logging.INFO, logger="pywa")

    @wa.on_message
    def my_callback(_, __): ...

    wa.webhook_update_handler(json.dumps(_MESSAGE_UPDATE).encode())
    summary = [r.getMessage() for r in caplog.records if "->" in r.getMessage()]
    assert len(summary) == 1
    assert "Message(text) wamid." in summary[0]
    assert "my_callback" in summary[0]
    assert _PHONE_NUMBER not in summary[0]


def test_info_summary_when_no_handler_matched(caplog):
    wa = _make_client()
    caplog.set_level(logging.INFO, logger="pywa")
    wa.webhook_update_handler(json.dumps(_MESSAGE_UPDATE).encode())
    assert any("no handler matched" in r.getMessage() for r in caplog.records)


def test_debug_does_not_dump_raw_payload_but_trace_does(caplog):
    wa = _make_client()
    caplog.set_level(logging.DEBUG, logger="pywa")
    wa.webhook_update_handler(json.dumps(_MESSAGE_UPDATE).encode())
    assert "Raw payload" not in caplog.text
    assert "=None" not in caplog.text
    caplog.clear()
    caplog.set_level(5, logger="pywa")
    wa.webhook_update_handler(json.dumps(_MESSAGE_UPDATE).encode() + b" ")
    assert "Raw payload" in caplog.text


def test_unexpected_update_error_path_survives_missing_entry(caplog):
    wa = _make_client()
    caplog.set_level(logging.DEBUG, logger="pywa")
    wa.webhook_update_handler(b"{}")  # must not raise from the logging itself


def _api_client(handler):
    return GraphAPI(
        token="SECRET-TOKEN",
        session=httpx.Client(transport=httpx.MockTransport(handler)),
        api_version=26.0,
    )


def test_api_request_success_never_logs_token(caplog):
    api = _api_client(lambda _: httpx.Response(200, json={"ok": 1}))
    caplog.set_level(logging.DEBUG, logger="pywa")
    api._request("POST", "/123/messages", json={"to": _PHONE_NUMBER})
    assert "POST /123/messages -> 200" in caplog.text
    assert "SECRET-TOKEN" not in caplog.text


def test_api_request_logs_error_code_and_trace_id(caplog):
    err = {"error": {"code": 131009, "message": "bad param", "fbtrace_id": "AbC"}}
    api = _api_client(lambda _: httpx.Response(400, json=err))
    caplog.set_level(logging.INFO, logger="pywa")
    with pytest.raises(WhatsAppError):
        api._request("GET", "/x?access_token=LEAK")
    rec = next(r for r in caplog.records if r.levelno == logging.WARNING)
    assert "code=131009" in rec.getMessage()
    assert "fbtrace_id=AbC" in rec.getMessage()
    assert "LEAK" not in caplog.text


def test_api_request_debug_shows_payload_and_truncated_response(caplog):
    api = _api_client(lambda _: httpx.Response(200, json={"data": "x" * 2000}))
    caplog.set_level(logging.DEBUG, logger="pywa")
    api._request("POST", "/1/messages", json={"to": _PHONE_NUMBER})
    assert _PHONE_NUMBER in caplog.text
    assert "chars)" in caplog.text


def test_signature_mismatch_does_not_log_the_signature(caplog):
    wa = WhatsApp(
        phone_id="1",
        token="x",
        server=None,
        verify_token="v",
        app_secret="s",
        validate_updates=True,
    )
    caplog.set_level(logging.WARNING, logger="pywa")
    res = wa.webhook_update_validator(b"{}", "sha256=deadbeef")
    assert res == ("Forbidden", 403)
    assert "mismatching signature" in caplog.text
    assert "deadbeef" not in caplog.text


def test_successful_challenge_logs_at_info(caplog):
    wa = WhatsApp(phone_id="1", token="x", server=None, verify_token="v")
    caplog.set_level(logging.INFO, logger="pywa")
    assert wa.webhook_challenge_handler("v", "c") == ("c", 200)
    assert "Webhook verified by WhatsApp" in caplog.text


def test_api_rate_limit_error_has_hint(caplog):
    err = {"error": {"code": 130429, "message": "Rate limit hit"}}
    api = _api_client(lambda _: httpx.Response(400, json=err))
    caplog.set_level(logging.INFO, logger="pywa")
    with pytest.raises(WhatsAppError):
        api._request("POST", "/1/messages")
    assert "rate limit hit" in caplog.text


def test_api_success_is_silent_at_info(caplog):
    api = _api_client(lambda _: httpx.Response(200, json={}))
    caplog.set_level(logging.INFO, logger="pywa")
    api._request("POST", "/123/messages")
    assert not caplog.records


def test_malformed_body_is_rejected_with_hash_context(caplog):
    wa = _make_client()
    caplog.set_level(logging.DEBUG, logger="pywa")
    assert wa.webhook_update_handler(b"not json") == ("Bad Request", 400)
    assert "Rejected a malformed (non-JSON) update body (8 bytes)" in caplog.text
    assert "preview" in caplog.text


def test_unrecognized_shape_warns_with_keys_not_values(caplog):
    wa = _make_client()
    caplog.set_level(logging.DEBUG, logger="pywa")
    encoded = json.dumps(_UNKNOWN_SHAPE_UPDATE).encode()
    raw = RawUpdate(encoded, hmac_header=None, update_hash=get_update_hash(encoded))
    wa._get_handler_type(raw)
    assert "unrecognized shape" in caplog.text
    assert _CONTACT_NAME not in caplog.text


def test_warnings_are_logged_as_one_clean_line(clean_logging):
    _drop_pytest_root_handlers()
    stream = io.StringIO()
    original = warnings.showwarning
    try:
        setup_console_logging("info", stream=stream)
        with warnings.catch_warnings():
            warnings.simplefilter("always")
            warnings.showwarning = warnings.showwarning  # keep our hook installed
            warnings.warn("be careful", PywaWarning, stacklevel=1)
        out = stream.getvalue()
    finally:
        warnings.showwarning = original
    assert "PywaWarning: be careful (test_server.py:" in out
    assert "warnings.warn(" not in out  # the source line is not echoed


def test_missing_app_secret_warning_points_at_user_code():
    with pytest.warns(PywaWarning, match="No `app_secret`") as record:
        _make_client_with_server()
    assert record[0].filename == __file__


def _make_client_with_server():
    return WhatsApp(
        phone_id="1",
        token="x",
        server=Starlette(),
        verify_token="v",
        validate_updates=True,
    )


def test_unknown_enum_warning_message_is_well_formed():
    with pytest.warns(Warning) as record:
        MessageType("brand_new_type")
    msg = str(record[0].message)
    assert "'brand_new_type'. Defaulting to MessageType.UNKNOWN." in msg


def test_async_warnings_point_at_user_code():
    with pytest.warns(PywaWarning) as record:
        WhatsAppAsync(phone_id="1", token="x", api_version="16.0")
    assert record[0].filename == __file__
    with pytest.warns(PywaWarning, match="No `app_secret`") as record:
        WhatsAppAsync(phone_id="1", token="x", server=Starlette(), verify_token="v")
    assert record[0].filename == __file__


def test_info_summary_does_not_leak_phone_number_embedded_in_wamid(caplog):

    wa = _make_client()
    caplog.set_level(logging.INFO, logger="pywa")
    # real `wamid`s start with base64 of the user's phone number (or BSUID)
    embedded = base64.b64encode(b"\x1c\x18\x0b" + _PHONE_NUMBER.encode()).decode()
    update = json.loads(json.dumps(_MESSAGE_UPDATE))
    update["entry"][0]["changes"][0]["value"]["messages"][0]["id"] = (
        f"wamid.{embedded}FQIAEhgUM0FBREY4NDQxMzQ3RTg1NzFDMTAA"
    )
    wa.webhook_update_handler(json.dumps(update).encode())
    assert embedded not in caplog.text
    assert _PHONE_NUMBER not in caplog.text
    assert "Message(text) wamid.…" in caplog.text


_ALL_UPDATES = [
    pytest.param(payload, id=f"{f.stem}:{name}")
    for f in sorted(pathlib.Path("tests/data/updates").glob("*.json"))
    for name, payload in json.loads(f.read_text()).items()
]


def _summary_for(payload: dict, caplog) -> str:
    wa = _make_client()
    caplog.set_level(logging.INFO, logger="pywa")
    wa.webhook_update_handler(json.dumps(payload).encode())
    (record,) = [r for r in caplog.records if "->" in r.getMessage()]
    return record.getMessage()


@pytest.mark.parametrize("payload", _ALL_UPDATES)
def test_every_fixture_update_gets_one_clean_summary(payload, caplog):
    summary = _summary_for(payload, caplog)
    assert re.match(r"\[\w{8}] [A-Z]\w+(\([a-z_]+\))?( wamid\.\S+)? -> ", summary)
    assert _PHONE_NUMBER not in summary
    assert not any(r.levelno >= logging.WARNING for r in caplog.records)


@pytest.mark.parametrize(
    ("fixture", "name", "label"),
    [
        ("account_update", "account_deleted", "AccountUpdate(account_deleted)"),
        ("message_status", "failed", "MessageStatus(failed)"),
        ("call_permission_update", "accept", "CallPermissionUpdate(accept)"),
        ("call_permission_update", "reject", "CallPermissionUpdate(reject)"),
        ("call_status", "call_status", "CallStatus(ringing)"),
        ("template_status_update", "approved", "TemplateStatusUpdate(approved)"),
        ("template_category_update", "marketing", "TemplateCategoryUpdate(marketing)"),
        ("template_quality_update", "yellow", "TemplateQualityUpdate(yellow)"),
        ("user_marketing_preferences", "resume", "UserMarketingPreferences(resume)"),
        ("message", "image", "Message(image)"),
        ("callback_button", "button", "CallbackButton(button)"),
        ("callback_button", "quick_reply", "CallbackButton(quick_reply)"),
        ("flow_completion", "completion", "FlowCompletion"),
        ("system", "phone_number_change", "PhoneNumberChange"),
    ],
)
def test_update_summary_labels(fixture, name, label, caplog):
    payload = json.loads(
        pathlib.Path(f"tests/data/updates/{fixture}.json").read_text()
    )[name]
    assert _summary_for(payload, caplog).split("] ", 1)[1].startswith(f"{label} ")


def test_debug_parsed_update_keeps_false_but_drops_none(caplog):
    wa = _make_client()
    caplog.set_level(logging.DEBUG, logger="pywa")
    wa.webhook_update_handler(json.dumps(_MESSAGE_UPDATE).encode())
    parsed = next(
        r.getMessage() for r in caplog.records if "Parsed update" in r.getMessage()
    )
    assert "forwarded=False" in parsed
    assert "=None" not in parsed
