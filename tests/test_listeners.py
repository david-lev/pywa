import asyncio
import logging
import threading
import time

import pytest

from pywa import WhatsApp as WhatsAppSync
from pywa import filters, server, utils
from pywa.listeners import (
    Listener,
    ListenerCanceled,
    ListenerStopped,
    ListenerTimeout,
    UserUpdateListenerIdentifier,
    _warn_anyio_thread_limit,
)
from pywa_async import WhatsApp as WhatsAppAsync


class DummyUpdate:
    @property
    def listener_identifiers(self):
        yield UserUpdateListenerIdentifier(sender="123456789", recipient="987654321")


@pytest.fixture
def wa_sync():
    return WhatsAppSync(server=None, verify_token="xyz")


@pytest.fixture
def wa_async():
    return WhatsAppAsync(server=None, verify_token="xyz")


def test_listener_success_sync(wa_sync: WhatsAppSync):
    identifiers = DummyUpdate().listener_identifiers
    first_id = next(identifiers)

    def emit_update():
        time.sleep(0.1)
        update = DummyUpdate()
        wa_sync._process_listener(update)

    threading.Thread(target=emit_update).start()
    result = wa_sync.listen(
        to=first_id, filters=filters.true, cancelers=filters.false, timeout=1
    )
    assert isinstance(result, DummyUpdate)


@pytest.mark.asyncio
async def test_listener_success_async(wa_async: WhatsAppAsync):
    identifiers = DummyUpdate().listener_identifiers
    first_id = next(identifiers)

    async def emit_update():
        await asyncio.sleep(0.1)
        update = DummyUpdate()
        await wa_async._process_listener(update)

    asyncio.create_task(emit_update())
    result = await wa_async.listen(
        to=first_id, filters=filters.true, cancelers=filters.false, timeout=1
    )
    assert isinstance(result, DummyUpdate)


def test_listener_timeout_sync(wa_sync: WhatsAppSync):
    identifiers = DummyUpdate().listener_identifiers
    first_id = next(identifiers)

    with pytest.raises(ListenerTimeout):
        wa_sync.listen(
            to=first_id,
            filters=filters.true,
            cancelers=filters.false,
            timeout=0.000001,
        )


@pytest.mark.asyncio
async def test_listener_timeout_async(wa_async: WhatsAppAsync):
    identifiers = DummyUpdate().listener_identifiers
    first_id = next(identifiers)
    with pytest.raises(ListenerTimeout):
        await wa_async.listen(
            to=first_id,
            filters=filters.true,
            cancelers=filters.false,
            timeout=0.000001,
        )


def test_listener_canceled_sync(wa_sync: WhatsAppSync):
    identifiers = DummyUpdate().listener_identifiers
    first_id = next(identifiers)

    def emit_update():
        time.sleep(0.1)
        update = DummyUpdate()
        wa_sync._process_listener(update)

    threading.Thread(target=emit_update).start()
    with pytest.raises(ListenerCanceled):
        wa_sync.listen(
            to=first_id, filters=filters.false, cancelers=filters.true, timeout=0.3
        )


@pytest.mark.asyncio
async def test_listener_canceled_async(wa_async: WhatsAppAsync):
    identifiers = DummyUpdate().listener_identifiers
    first_id = next(identifiers)

    async def emit_update():
        await asyncio.sleep(0.1)
        update = DummyUpdate()
        await wa_async._process_listener(update)

    asyncio.create_task(emit_update())
    with pytest.raises(ListenerCanceled):
        await wa_async.listen(
            to=first_id, filters=filters.false, cancelers=filters.true, timeout=0.3
        )


def test_listener_stopped_sync(wa_sync: WhatsAppSync):
    identifiers = DummyUpdate().listener_identifiers
    first_id = next(identifiers)

    def stop_listener():
        time.sleep(0.1)
        wa_sync.stop_listening(to=first_id, reason="manual")

    threading.Thread(target=stop_listener).start()
    with pytest.raises(ListenerStopped) as exc_info:
        wa_sync.listen(
            to=first_id, filters=filters.true, cancelers=filters.false, timeout=0.3
        )
    assert exc_info.value.reason == "manual"


@pytest.mark.asyncio
async def test_listener_stopped_async(wa_async: WhatsAppAsync):
    identifiers = DummyUpdate().listener_identifiers
    first_id = next(identifiers)

    async def stop_listener():
        await asyncio.sleep(0.1)
        wa_async.stop_listening(to=first_id, reason="manual")

    asyncio.create_task(stop_listener())
    with pytest.raises(ListenerStopped) as exc_info:
        await wa_async.listen(
            to=first_id, filters=filters.true, cancelers=filters.false, timeout=0.3
        )
    assert exc_info.value.reason == "manual"


def test_listener_timeout_is_logged_at_info(wa_sync: WhatsAppSync, caplog):
    caplog.set_level(logging.INFO, logger="pywa")
    first_id = next(DummyUpdate().listener_identifiers)
    with pytest.raises(ListenerTimeout):
        wa_sync.listen(to=first_id, filters=filters.true, timeout=0.000001)
    assert "Listener timed out after" in caplog.text


def test_anyio_thread_limit_warns_once_per_spike(wa_sync: WhatsAppSync, caplog):
    wa_sync._server_type = utils.CustomServerType.STARLETTE
    caplog.set_level(logging.WARNING, logger="pywa")
    old = server.ANYIO_THREADS_LIMIT
    server.ANYIO_THREADS_LIMIT = 10
    try:
        for i in range(9):
            wa_sync._listeners[i] = Listener(filters=None, cancelers=None)
        _warn_anyio_thread_limit(wa_sync)
        _warn_anyio_thread_limit(wa_sync)  # same spike: no second warning
        assert caplog.text.count("close to the AnyIO thread limit") == 1
        wa_sync._listeners.clear()
        _warn_anyio_thread_limit(wa_sync)  # back under the threshold: re-arms
        for i in range(9):
            wa_sync._listeners[i] = Listener(filters=None, cancelers=None)
        _warn_anyio_thread_limit(wa_sync)
        assert caplog.text.count("close to the AnyIO thread limit") == 2
    finally:
        server.ANYIO_THREADS_LIMIT = old
        wa_sync._listeners.clear()
