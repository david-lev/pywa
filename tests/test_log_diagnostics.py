import json
import logging
import pathlib

import httpx
import pytest

from pywa import WhatsApp, _logging
from pywa._logging import log_api_response, log_once, url_host
from pywa_async import WhatsApp as WhatsAppAsync

_MESSAGE_UPDATE = json.loads(
    pathlib.Path("tests/data/updates/message.json").read_text()
)["text"]


@pytest.fixture(autouse=True)
def _reset_log_once():
    _logging._logged_once.clear()


def _api_error(code: int, status: int = 400) -> httpx.Response:
    return httpx.Response(status, json={"error": {"code": code, "message": "boom"}})


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        (190, "access token is invalid or expired"),
        (131030, "not in the allowed list"),
        (131047, "24-hour customer service window"),
    ],
)
def test_api_error_hints(caplog, code, expected):
    caplog.set_level(logging.WARNING, logger="pywa")
    log_api_response(
        logging.getLogger("pywa.api"), "POST", "/1/messages", _api_error(code), 0.0
    )
    assert expected in caplog.text
    assert f"code={code}" in caplog.text


def test_api_error_without_hint(caplog):
    caplog.set_level(logging.WARNING, logger="pywa")
    log_api_response(
        logging.getLogger("pywa.api"), "POST", "/1/messages", _api_error(999), 0.0
    )
    assert "code=999" in caplog.text
    assert "[" not in caplog.text.split("code=999")[1]


def test_log_once_dedupes_per_key(caplog):
    logger = logging.getLogger("pywa.test_once")
    caplog.set_level(logging.WARNING, logger="pywa")
    for _ in range(3):
        log_once(logger, logging.WARNING, "k1", "first")
    log_once(logger, logging.WARNING, "k2", "second")
    assert caplog.text.count("first") == 1
    assert caplog.text.count("second") == 1


def test_url_host_hides_signed_path():
    assert (
        url_host(
            "https://lookaside.fbsbx.com/whatsapp_business/attachments/?mid=1&hash=SECRET"
        )
        == "lookaside.fbsbx.com"
    )


def test_duplicate_update_not_logged_at_info(caplog):
    wa = WhatsApp(
        phone_id="1122334455667",
        token="xyz",
        filter_updates=False,
        skip_duplicate_updates=True,
    )
    caplog.set_level(logging.INFO, logger="pywa")
    body = json.dumps(_MESSAGE_UPDATE).encode()
    wa.webhook_update_handler(body)
    caplog.clear()
    wa.webhook_update_handler(body)
    assert "duplicate" not in caplog.text
