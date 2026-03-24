import asyncio
import threading
import time

import pytest

from pywa import WhatsApp as WhatsAppSync
from pywa import filters
from pywa.listeners import (
    ListenerCanceled,
    ListenerStopped,
    ListenerTimeout,
    UserUpdateListenerIdentifier,
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
