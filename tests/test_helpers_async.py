"""Async counterparts of the media upload helpers tests (see ``test_helpers.py``)."""

import asyncio
import base64
import contextlib
import io
import time
from unittest import mock

import httpx
import pytest

from pywa.errors import WhatsAppError
from pywa.types.templates import HeaderImage
from pywa_async import _helpers as helpers

pytestmark = pytest.mark.asyncio


def _wa() -> mock.Mock:
    wa = mock.Mock()
    wa.api.create_upload_session = mock.AsyncMock(return_value={"id": "session-1"})
    wa.api.upload_file = mock.AsyncMock(return_value={"h": "handle-1"})
    wa.api.upload_media = mock.AsyncMock(return_value={"id": "media-1"})
    return wa


def _transport(status=200, content=b"filedata", headers=None):
    return httpx.MockTransport(
        lambda request: httpx.Response(status, content=content, headers=headers)
    )


async def test_get_media_from_url_not_streamed_reads_body():
    async with (
        httpx.AsyncClient(
            transport=_transport(headers={"Content-Type": "image/png"})
        ) as session,
        contextlib.AsyncExitStack() as stack,
    ):
        info = await helpers.get_media_from_url(
            stack,
            "https://example.com/a.png?sig=1",
            session,
            download_chunk_size=None,
            stream=False,
        )
    assert info.content == b"filedata"
    assert info.length == 8
    assert (info.filename, info.mime_type) == ("a.png", "image/png")


async def test_get_media_from_url_streamed_is_readable_until_stack_closes():
    async with (
        httpx.AsyncClient(transport=_transport()) as session,
        contextlib.AsyncExitStack() as stack,
    ):
        info = await helpers.get_media_from_url(
            stack,
            "https://example.com/a.txt",
            session,
            download_chunk_size=3,
            stream=True,
        )
        assert b"".join([c async for c in info.content]) == b"filedata"


async def test_get_media_from_url_http_error_raises_value_error():
    async with httpx.AsyncClient(transport=_transport(404)) as session:
        with pytest.raises(ValueError, match="404"):
            async with contextlib.AsyncExitStack() as stack:
                await helpers.get_media_from_url(
                    stack, "https://example.com/x", session, None, True
                )


async def test_get_media_from_media_url_http_error_raises_value_error_not_runtime_error():
    # `res.close()` on an async response raised `RuntimeError` and hid the real error
    url = "https://lookaside.fbsbx.com/whatsapp_business/attachments/?mid=1"
    wa = mock.Mock()
    wa.api.stream_media_bytes.return_value = httpx.AsyncClient(
        transport=_transport(404)
    ).stream("GET", url)
    with pytest.raises(ValueError, match="404"):
        async with contextlib.AsyncExitStack() as stack:
            await helpers.get_media_from_media_id_or_obj_or_url(
                stack,
                wa,
                url,
                helpers.MediaSource.MEDIA_URL,
                download_chunk_size=None,
                stream=False,
            )


async def test_internal_upload_media_closes_download_client_when_download_fails(mocker):
    client = mock.MagicMock()
    client.__aenter__ = mock.AsyncMock(return_value=client)
    client.__aexit__ = mock.AsyncMock(return_value=None)
    mocker.patch("pywa_async._helpers.httpx.AsyncClient", return_value=client)
    mocker.patch(
        "pywa_async._helpers.get_media_from_url", side_effect=ValueError("404")
    )
    with pytest.raises(ValueError, match="404"):
        await helpers.internal_upload_media(
            media="https://example.com/a.png",
            media_source=helpers.MediaSource.EXTERNAL_URL,
            media_type="image",
            mime_type=None,
            filename=None,
            wa=_wa(),
            phone_id="p1",
        )
    client.__aexit__.assert_awaited_once()


async def test_internal_upload_file_closes_download_client_when_download_fails(mocker):
    client = mock.MagicMock()
    client.__aenter__ = mock.AsyncMock(return_value=client)
    client.__aexit__ = mock.AsyncMock(return_value=None)
    mocker.patch("pywa_async._helpers.httpx.AsyncClient", return_value=client)
    mocker.patch(
        "pywa_async._helpers.get_media_from_url", side_effect=ValueError("404")
    )
    with pytest.raises(ValueError, match="404"):
        await helpers.internal_upload_file(
            wa=_wa(),
            file="https://example.com/a.png",
            app_id="a",
            mime_type=None,
            fallback_mime_type="image/png",
            fallback_filename="a.png",
        )
    client.__aexit__.assert_awaited_once()


async def test_internal_upload_file_streams_path_and_closes_it(tmp_path):
    p = tmp_path / "a.png"
    p.write_bytes(b"abcdefgh")
    wa = _wa()
    received = []

    async def upload_file(**kwargs):
        received.append(b"".join([c async for c in kwargs["file"]]))
        return {"h": "handle-1"}

    wa.api.upload_file = upload_file
    handle, source = await helpers.internal_upload_file(
        wa=wa,
        file=p,
        app_id="a",
        mime_type=None,
        fallback_mime_type="image/png",
        fallback_filename="a.png",
    )
    assert (handle, source) == ("handle-1", helpers.MediaSource.PATH)
    assert received == [b"abcdefgh"]


async def test_internal_upload_file_file_obj_is_sendable_by_async_client():
    buf = io.BytesIO(b"abcdefgh")
    buf.name = "/tmp/some/dir/a.png"
    wa = _wa()
    await helpers.internal_upload_file(
        wa=wa,
        file=buf,
        app_id="a",
        mime_type=None,
        fallback_mime_type="image/png",
        fallback_filename="fallback.png",
    )
    assert wa.api.create_upload_session.call_args.kwargs["file_name"] == "a.png"
    sent = wa.api.upload_file.call_args.kwargs
    assert sent["content_length"] == 8
    assert b"".join([c async for c in sent["file"]]) == b"abcdefgh"


async def test_internal_upload_file_does_not_wrap_whatsapp_errors():
    err = WhatsAppError.from_dict({"code": 190, "message": "bad token"})
    wa = _wa()
    wa.api.create_upload_session.side_effect = err
    with pytest.raises(WhatsAppError) as exc:
        await helpers.internal_upload_file(
            wa=wa,
            file=b"x",
            app_id="a",
            mime_type="image/png",
            fallback_mime_type="image/png",
            fallback_filename="a.png",
        )
    assert exc.value is err


async def test_internal_upload_file_error_message_has_no_payload():
    secret = base64.b64encode(b"private document").decode()
    wa = _wa()
    wa.api.create_upload_session.side_effect = RuntimeError("boom")
    with pytest.raises(ValueError) as exc:
        await helpers.internal_upload_file(
            wa=wa,
            file=secret,
            app_id="a",
            mime_type="image/png",
            fallback_mime_type="image/png",
            fallback_filename="a.png",
        )
    assert secret not in str(exc.value)


async def test_sync_generator_does_not_block_the_event_loop():
    ticks = 0

    def slow_chunks():
        for _ in range(4):
            time.sleep(0.05)  # a blocking source
            yield b"chunk"

    async def ticker():
        nonlocal ticks
        while True:
            await asyncio.sleep(0.005)
            ticks += 1

    task = asyncio.create_task(ticker())
    try:
        async with contextlib.AsyncExitStack() as stack:
            info = await helpers.open_media(
                stack,
                wa=_wa(),
                media=slow_chunks(),
                source=helpers.MediaSource.BYTES_GEN,
                stream=False,
            )
    finally:
        task.cancel()
    assert info.content == b"chunk" * 4
    assert info.length == 20
    assert ticks > 10  # the loop kept running while the generator was blocking


async def test_upload_template_media_components_reads_a_shared_stream_once():
    buf = io.BytesIO(b"image")
    comps = [
        HeaderImage(buf, mime_type="image/png"),
        HeaderImage(b"other", mime_type="image/png"),
        HeaderImage(buf, mime_type="image/png"),  # not adjacent to the first one
    ]
    uploaded = []

    async def upload(*, file, **_):
        uploaded.append(file)
        return f"handle-{len(uploaded)}", helpers.MediaSource.BYTES

    with mock.patch("pywa_async._helpers.internal_upload_file", side_effect=upload):
        await helpers.upload_template_media_components(
            wa=_wa(), app_id="a", components=comps
        )
    assert len(uploaded) == 2
    assert sum(f is buf for f in uploaded) == 1
    assert comps[0]._handle == comps[2]._handle != comps[1]._handle


async def test_generator_streamer_is_uploaded_as_multipart_by_the_async_client():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["headers"], seen["body"] = request.headers, request.content
        return httpx.Response(200, json={"id": "1"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        await client.post(
            "https://x.test/media",
            files={
                "file": (
                    "a.bin",
                    helpers.GeneratorStreamer(iter([b"abc", b"defg"]), length=7),
                    "image/png",
                )
            },
        )
    assert b"abcdefg" in seen["body"]
    assert int(seen["headers"]["content-length"]) == len(seen["body"])


async def test_async_upload_media_sniffs_when_nothing_else_is_known():
    wa = _wa()
    await helpers.internal_upload_media(
        media=b"\x89PNG\r\n\x1a\n" + b"\x00" * 8,
        media_source=helpers.MediaSource.BYTES,
        media_type=None,
        mime_type=None,
        filename=None,
        wa=wa,
        phone_id="p1",
    )
    sent = wa.api.upload_media.call_args.kwargs
    assert (sent["mime_type"], sent["filename"]) == ("image/png", "file.png")


async def test_async_upload_media_media_type_defaults_win_over_sniffing():
    wa = _wa()
    await helpers.internal_upload_media(
        media=b"\x89PNG\r\n\x1a\n" + b"\x00" * 8,
        media_source=helpers.MediaSource.BYTES,
        media_type="image",
        mime_type=None,
        filename=None,
        wa=wa,
        phone_id="p1",
    )
    sent = wa.api.upload_media.call_args.kwargs
    assert (sent["mime_type"], sent["filename"]) == ("image/jpeg", "image.jpg")


async def test_whatsapp_error_propagates_while_a_download_is_open():
    err = WhatsAppError.from_dict({"code": 190, "message": "bad token"})
    async with httpx.AsyncClient(transport=_transport()) as session:
        with pytest.raises(WhatsAppError) as exc:
            async with contextlib.AsyncExitStack() as stack:
                await helpers.get_media_from_url(
                    stack, "https://example.com/a.png", session, 1024, stream=True
                )
                raise err
    assert exc.value is err
