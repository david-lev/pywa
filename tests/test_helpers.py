"""Additional tests for pywa/_helpers.py targeting branches not exercised
via tests/test_client.py (which already covers the happy paths of several
of these helpers through the `helpers` alias)."""

import base64
import contextlib
import io
from unittest import mock

import httpx
import pytest

from pywa import _helpers as helpers
from pywa.errors import PywaUnknownEnumMemberWarning, WhatsAppError
from pywa.types.flows import FlowJSON
from pywa.types.media import Media
from pywa.types.sent_update import RecipientType
from pywa.types.templates import HeaderImage

# --- StrEnum -----------------------------------------------------------


class _Color(helpers.StrEnum):
    RED = "RED"
    BLUE = "BLUE"
    UNKNOWN = "UNKNOWN"


def test_str_enum_unknown_string_value_warns_and_falls_back():
    with pytest.warns(PywaUnknownEnumMemberWarning):
        assert _Color("green") == _Color.UNKNOWN


def test_str_enum_lookup_is_case_insensitive():
    assert _Color("red") == _Color.RED


def test_str_enum_non_str_value_raises():
    with pytest.raises(ValueError):
        _Color(123)


class _NoUnknown(helpers.StrEnum):
    RED = "RED"


def test_str_enum_without_unknown_member_raises_type_error():
    with pytest.warns(PywaUnknownEnumMemberWarning), pytest.raises(TypeError):
        _NoUnknown("green")


# --- resolve_buttons_param error branches -----------------------------


def test_resolve_buttons_param_not_iterable_raises():
    with pytest.raises(ValueError):
        helpers.resolve_buttons_param(123)


def test_resolve_buttons_param_non_button_item_raises():
    with pytest.raises(TypeError):
        helpers.resolve_buttons_param([object()])


# --- detect_media_source ------------------------------------------------


def test_detect_media_source_invalid_type_raises():
    with pytest.raises(TypeError):
        helpers.detect_media_source(object())


# --- GeneratorStreamer ---------------------------------------------------


def test_generator_streamer_read_and_tell():
    def gen():
        yield b"abc"
        yield b"def"

    streamer = helpers.GeneratorStreamer(gen())
    assert streamer.__iter__() is streamer
    assert streamer.read(999) == b"abc"
    assert streamer.read(999) == b"def"
    assert streamer.tell() == 6
    assert streamer.read(999) == b""  # exhausted -> sentinel b""
    assert streamer.read(999) == b""  # StopIteration -> b""


def test_generator_streamer_seek_to_end_with_known_length():
    streamer = helpers.GeneratorStreamer(iter([b"abc"]), length=10)
    assert streamer.seek(0, io.SEEK_END) == 10


def test_generator_streamer_seek_to_end_without_known_length_raises():
    streamer = helpers.GeneratorStreamer(iter([b"abc"]))
    with pytest.raises(OSError):
        streamer.seek(0, io.SEEK_END)


def test_generator_streamer_seek_to_current_position():
    streamer = helpers.GeneratorStreamer(iter([b"abc"]))
    streamer.read(999)
    assert streamer.seek(0, io.SEEK_SET) == 3


def test_generator_streamer_seek_unsupported_raises():
    streamer = helpers.GeneratorStreamer(iter([b"abc"]))
    with pytest.raises(OSError):
        streamer.seek(5, io.SEEK_CUR)


# --- get_media_from_base64 -----------------------------------------------


def test_get_media_from_base64_data_uri():
    info = helpers.get_media_from_base64("data:image/png;base64,aGVsbG8=")
    assert info.content == b"hello"
    assert info.mime_type == "image/png"
    assert info.length == 5


def test_get_media_from_base64_plain():
    info = helpers.get_media_from_base64("aGVsbG8=")
    assert info.content == b"hello"
    assert info.mime_type is None


def test_get_media_from_base64_invalid_raises():
    with pytest.raises(ValueError):
        helpers.get_media_from_base64("not base64!!")


# --- get_media_from_path --------------------------------------------------


def test_get_media_from_path(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("hello")
    with contextlib.ExitStack() as stack:
        info = helpers.get_media_from_path(stack, p)
        assert info.filename == "a.txt"
        assert info.length == 5
        assert info.content.read() == b"hello"
    assert info.content.closed


# --- get_media_from_file_like_obj -----------------------------------------


def test_get_media_from_file_like_obj_with_fileno(tmp_path):
    p = tmp_path / "b.txt"
    p.write_text("hello world")
    with open(p, "rb") as f:
        info = helpers.get_media_from_file_like_obj(f)
        assert info.length == 11
        assert info.filename == "b.txt"  # basename, not the local path
        assert info.mime_type == "text/plain"


def test_get_media_from_file_like_obj_without_fileno():
    buf = io.BytesIO(b"hello")
    info = helpers.get_media_from_file_like_obj(buf)
    assert info.length == 5
    assert info.filename is None
    assert info.mime_type is None
    assert buf.tell() == 0  # seek position restored


# --- get_filename_from_httpx_response_headers ------------------------------


def test_get_filename_from_headers_present():
    headers = httpx.Headers({"Content-Disposition": 'attachment; filename="a.pdf"'})
    assert helpers.get_filename_from_httpx_response_headers(headers) == "a.pdf"


def test_get_filename_from_headers_absent():
    assert helpers.get_filename_from_httpx_response_headers(httpx.Headers({})) is None


# --- get_media_from_url ---------------------------------------------------


def test_get_media_from_url_success():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=b"filedata",
            headers={"Content-Type": "text/plain", "Content-Length": "8"},
        )

    session = httpx.Client(transport=httpx.MockTransport(handler))
    with contextlib.ExitStack() as stack:
        info = helpers.get_media_from_url(
            stack,
            "https://example.com/file.txt",
            session,
            download_chunk_size=1024,
            stream=True,
        )
        assert b"".join(info.content) == b"filedata"
        assert info.mime_type == "text/plain"
        assert info.length == 8


def test_get_media_from_url_http_error_raises():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, content=b"not found")

    session = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(ValueError), contextlib.ExitStack() as stack:
        helpers.get_media_from_url(
            stack,
            "https://example.com/missing.txt",
            session,
            download_chunk_size=1024,
            stream=True,
        )


# --- resolve_recipient / resolve_callee / resolve_users -------------------


def test_resolve_recipient_empty_raises():
    with pytest.raises(ValueError):
        helpers.resolve_recipient("")


def test_resolve_recipient_unmatched_type_raises(mocker):
    mocker.patch("pywa._helpers.RecipientType.from_recipient", return_value=None)
    with pytest.raises(ValueError):
        helpers.resolve_recipient("123")


def test_clean_phone_number():
    assert helpers.clean_phone_number("+1 (631) 555-1234") == "16315551234"


def test_resolve_callee_wa_id():
    callee, recipient_type = helpers.resolve_callee("123456789")
    assert callee == {"to": "123456789", "recipient": None}
    assert recipient_type == RecipientType.WA_ID


def test_resolve_callee_bsuid():
    callee, recipient_type = helpers.resolve_callee("US.13491208655302741918")
    assert callee == {"to": None, "recipient": "US.13491208655302741918"}
    assert recipient_type == RecipientType.BSUID


def test_resolve_call_permission_request_user_wa_id():
    assert helpers.resolve_call_permission_request_user("+1 (631) 555-1234") == {
        "user_wa_id": "16315551234"
    }


def test_resolve_call_permission_request_user_bsuid():
    assert helpers.resolve_call_permission_request_user("US.13491208655302741918") == {
        "recipient": "US.13491208655302741918"
    }


def test_resolve_call_permission_request_user_invalid_raises():
    with pytest.raises(ValueError):
        helpers.resolve_call_permission_request_user("some-group-id")


def test_resolve_users_mixed():
    result = helpers.resolve_users(["123456789", "US.13491208655302741918"])
    assert result == {
        "users": ("123456789",),
        "user_ids": ("US.13491208655302741918",),
    }


def test_resolve_users_invalid_raises():
    with pytest.raises(ValueError):
        helpers.resolve_users(["some-group-id"])


# --- resolve_flow_json_param -----------------------------------------------


def test_resolve_flow_json_param_path_to_file(tmp_path):
    p = tmp_path / "flow.json"
    p.write_text('{"key": "value"}')
    assert helpers.resolve_flow_json_param(p) == '{"key": "value"}'


def test_resolve_flow_json_param_flow_json_obj():
    fj = FlowJSON(version="7.3", screens=[])
    result = helpers.resolve_flow_json_param(fj)
    assert '"version"' in result


def test_resolve_flow_json_param_file_obj():
    buf = io.BytesIO(b'{"key": "value"}')
    assert helpers.resolve_flow_json_param(buf) == '{"key": "value"}'


def test_resolve_flow_json_param_invalid_type_raises():
    with pytest.raises(TypeError):
        helpers.resolve_flow_json_param(123)


# --- resolve_callback_data --------------------------------------------------


def test_resolve_callback_data_invalid_type_raises():
    with pytest.raises(TypeError):
        helpers.resolve_callback_data(123)


# --- is_installed / rename_func --------------------------------------------


def test_is_installed_true():
    assert helpers.is_installed("os") is True


def test_is_installed_false():
    assert helpers.is_installed("this_module_does_not_exist_pywa") is False


def test_rename_func():
    @helpers.rename_func("_extended")
    def my_func():
        pass

    assert my_func.__name__ == "my_func_extended"


# --- filter_not_uploaded_comps / filter_not_uploaded_params ----------------


def test_filter_not_uploaded_comps_empty():
    assert helpers.filter_not_uploaded_comps([]) == []


def test_filter_not_uploaded_params_empty():
    assert helpers.filter_not_uploaded_params([]) == []


# --- get_media_from_media_id_or_obj_or_url ----------------------------------


def _stream_cm(status_code=200, headers=None, chunks=(b"data",)):
    response = mock.Mock()
    response.status_code = status_code
    response.headers = headers or {}
    response.raise_for_status = mock.Mock()
    if status_code >= 400:
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "err", request=mock.Mock(), response=mock.Mock(status_code=status_code)
        )
    response.iter_bytes = mock.Mock(return_value=iter(chunks))
    cm = mock.MagicMock()
    cm.__enter__ = mock.Mock(return_value=response)
    cm.__exit__ = mock.Mock(return_value=False)
    return cm


def test_get_media_from_media_id_or_obj_or_url_media_id():
    wa = mock.Mock()
    wa.get_media_url.return_value = mock.Mock(
        url="https://media.example/1", mime_type="image/png"
    )
    wa.api.stream_media_bytes.return_value = _stream_cm(headers={"Content-Length": "4"})
    with contextlib.ExitStack() as stack:
        info = helpers.get_media_from_media_id_or_obj_or_url(
            stack,
            wa=wa,
            media="m1",
            media_source=helpers.MediaSource.MEDIA_ID,
            download_chunk_size=1024,
            stream=True,
        )
        assert b"".join(info.content) == b"data"
    assert info.mime_type == "image/png"
    assert info.length == 4
    wa.get_media_url.assert_called_once_with(media_id="m1")


def test_get_media_from_media_id_or_obj_or_url_media_url():
    wa = mock.Mock()
    wa.api.stream_media_bytes.return_value = _stream_cm()
    with contextlib.ExitStack() as stack:
        info = helpers.get_media_from_media_id_or_obj_or_url(
            stack,
            wa=wa,
            media="https://lookaside.fbsbx.com/whatsapp_business/attachments/?mid=1",
            media_source=helpers.MediaSource.MEDIA_URL,
            download_chunk_size=1024,
            stream=True,
        )
        assert b"".join(info.content) == b"data"


def test_get_media_from_media_id_or_obj_or_url_invalid_source_raises():
    wa = mock.Mock()
    with pytest.raises(ValueError), contextlib.ExitStack() as stack:
        helpers.get_media_from_media_id_or_obj_or_url(
            stack,
            wa=wa,
            media="x",
            media_source=helpers.MediaSource.BYTES,
            download_chunk_size=1024,
            stream=True,
        )


def test_get_media_from_media_id_or_obj_or_url_http_error_raises():
    wa = mock.Mock()
    wa.get_media_url.return_value = mock.Mock(
        url="https://media.example/1", mime_type=None
    )
    wa.api.stream_media_bytes.return_value = _stream_cm(status_code=404)
    with pytest.raises(ValueError), contextlib.ExitStack() as stack:
        helpers.get_media_from_media_id_or_obj_or_url(
            stack,
            wa=wa,
            media="m1",
            media_source=helpers.MediaSource.MEDIA_ID,
            download_chunk_size=1024,
            stream=True,
        )


# --- internal_upload_media ---------------------------------------------------


def test_internal_upload_media_bytes():
    wa = mock.Mock()
    wa.api.upload_media.return_value = {"id": "media-id-1"}
    media = helpers.internal_upload_media(
        media=b"filebytes",
        media_source=helpers.MediaSource.BYTES,
        media_type="image",
        mime_type=None,
        filename=None,
        download_chunk_size=None,
        wa=wa,
        phone_id="p1",
    )
    assert isinstance(media, Media)
    assert media.id == "media-id-1"
    wa.api.upload_media.assert_called_once()
    _, kwargs = wa.api.upload_media.call_args
    assert kwargs["mime_type"] == "image/jpeg"
    assert kwargs["filename"] == "image.jpg"


def test_internal_upload_media_unsupported_source_raises():
    wa = mock.Mock()
    with pytest.raises(ValueError):
        helpers.internal_upload_media(
            media="x",
            media_source=helpers.MediaSource.FILE_HANDLE,
            media_type=None,
            mime_type=None,
            filename=None,
            download_chunk_size=None,
            wa=wa,
            phone_id="p1",
        )


# --- internal_upload_file -----------------------------------------------


def test_internal_upload_file_file_handle_shortcircuits():
    wa = mock.Mock()
    handle, source = helpers.internal_upload_file(
        wa=wa,
        file="2:c2FtcGxl...",
        app_id=None,
        mime_type=None,
        fallback_mime_type="application/octet-stream",
        fallback_filename=None,
    )
    assert handle == "2:c2FtcGxl..."
    assert source == helpers.MediaSource.FILE_HANDLE
    wa.api.upload_file.assert_not_called()


def test_internal_upload_file_bytes():
    wa = mock.Mock()
    wa.api.create_upload_session.return_value = {"id": "session-1"}
    wa.api.upload_file.return_value = {"h": "handle-1"}
    wa.app_id = "app-1"
    handle, source = helpers.internal_upload_file(
        wa=wa,
        file=b"filebytes",
        app_id=None,
        mime_type="text/plain",
        fallback_mime_type="application/octet-stream",
        fallback_filename="fallback.bin",
    )
    assert handle == "handle-1"
    assert source == helpers.MediaSource.BYTES
    wa.api.create_upload_session.assert_called_once_with(
        app_id="app-1",
        file_name="fallback.bin",
        file_length=len(b"filebytes"),
        file_type="text/plain",
    )


def test_internal_upload_file_wraps_errors():
    wa = mock.Mock()
    wa.api.create_upload_session.side_effect = RuntimeError("boom")
    wa.app_id = "app-1"
    with pytest.raises(ValueError):
        helpers.internal_upload_file(
            wa=wa,
            file=b"filebytes",
            app_id=None,
            mime_type="text/plain",
            fallback_mime_type="application/octet-stream",
            fallback_filename="fallback.bin",
        )


# --- internal_upload_media: remaining media sources -------------------------


def test_internal_upload_media_external_url(mocker):
    wa = mock.Mock()
    wa.api.upload_media.return_value = {"id": "media-id-1"}
    mocker.patch(
        "pywa._helpers.get_media_from_url",
        return_value=helpers.MediaInfo(
            content=b"data", filename="f.jpg", mime_type="image/jpeg", length=4
        ),
    )
    media = helpers.internal_upload_media(
        media="https://example.com/f.jpg",
        media_source=helpers.MediaSource.EXTERNAL_URL,
        media_type="image",
        mime_type=None,
        filename=None,
        download_chunk_size=None,
        wa=wa,
        phone_id="p1",
    )
    assert media.id == "media-id-1"


def test_internal_upload_media_path(tmp_path):
    wa = mock.Mock()
    wa.api.upload_media.return_value = {"id": "media-id-1"}
    p = tmp_path / "a.jpg"
    p.write_bytes(b"data")
    media = helpers.internal_upload_media(
        media=p,
        media_source=helpers.MediaSource.PATH,
        media_type="image",
        mime_type=None,
        filename=None,
        download_chunk_size=None,
        wa=wa,
        phone_id="p1",
    )
    assert media.id == "media-id-1"
    assert media.filename == "a.jpg"


def test_internal_upload_media_file_obj():
    wa = mock.Mock()
    wa.api.upload_media.return_value = {"id": "media-id-1"}
    media = helpers.internal_upload_media(
        media=io.BytesIO(b"data"),
        media_source=helpers.MediaSource.FILE_OBJ,
        media_type="image",
        mime_type=None,
        filename=None,
        download_chunk_size=None,
        wa=wa,
        phone_id="p1",
    )
    assert media.id == "media-id-1"


def test_internal_upload_media_bytes_gen():
    wa = mock.Mock()
    wa.api.upload_media.return_value = {"id": "media-id-1"}
    media = helpers.internal_upload_media(
        media=iter([b"a", b"b"]),
        media_source=helpers.MediaSource.BYTES_GEN,
        media_type="image",
        mime_type=None,
        filename="custom.jpg",
        download_chunk_size=None,
        wa=wa,
        phone_id="p1",
    )
    assert media.filename == "custom.jpg"


def test_internal_upload_media_base64():
    wa = mock.Mock()
    wa.api.upload_media.return_value = {"id": "media-id-1"}
    media = helpers.internal_upload_media(
        media="aGVsbG8=",
        media_source=helpers.MediaSource.BASE64,
        media_type="image",
        mime_type=None,
        filename=None,
        download_chunk_size=None,
        wa=wa,
        phone_id="p1",
    )
    assert media.id == "media-id-1"


def test_internal_upload_media_media_obj():
    wa = mock.Mock()
    wa.get_media_url.return_value = mock.Mock(
        url="https://media.example/1", mime_type=None
    )
    wa.api.stream_media_bytes.return_value = _stream_cm()
    wa.api.upload_media.return_value = {"id": "media-id-2"}
    src_media = Media(_client=wa, _id="orig-id", filename=None, uploaded_to="p1")
    media = helpers.internal_upload_media(
        media=src_media,
        media_source=helpers.MediaSource.MEDIA_OBJ,
        media_type="image",
        mime_type=None,
        filename=None,
        download_chunk_size=None,
        wa=wa,
        phone_id="p1",
    )
    assert media.id == "media-id-2"


# --- internal_upload_file: remaining media sources ---------------------------


def test_internal_upload_file_external_url(mocker):
    wa = mock.Mock()
    wa.api.create_upload_session.return_value = {"id": "session-1"}
    wa.api.upload_file.return_value = {"h": "handle-1"}
    wa.app_id = "app-1"
    mocker.patch(
        "pywa._helpers.get_media_from_url",
        return_value=helpers.MediaInfo(
            content=b"data", filename="f.jpg", mime_type="image/jpeg", length=4
        ),
    )
    handle, source = helpers.internal_upload_file(
        wa=wa,
        file="https://example.com/f.jpg",
        app_id=None,
        mime_type=None,
        fallback_mime_type="application/octet-stream",
        fallback_filename=None,
    )
    assert handle == "handle-1"
    assert source == helpers.MediaSource.EXTERNAL_URL


def test_internal_upload_file_path(tmp_path):
    wa = mock.Mock()
    wa.api.create_upload_session.return_value = {"id": "session-1"}
    wa.api.upload_file.return_value = {"h": "handle-1"}
    wa.app_id = "app-1"
    p = tmp_path / "a.pdf"
    p.write_bytes(b"data")
    handle, source = helpers.internal_upload_file(
        wa=wa,
        file=p,
        app_id=None,
        mime_type=None,
        fallback_mime_type="application/octet-stream",
        fallback_filename=None,
    )
    assert handle == "handle-1"
    assert source == helpers.MediaSource.PATH


def test_internal_upload_file_media_obj():
    wa = mock.Mock()
    wa.get_media_url.return_value = mock.Mock(
        url="https://media.example/1", mime_type=None
    )
    wa.api.stream_media_bytes.return_value = _stream_cm(headers={"Content-Length": "4"})
    wa.api.create_upload_session.return_value = {"id": "session-1"}
    wa.api.upload_file.return_value = {"h": "handle-1"}
    wa.app_id = "app-1"
    src_media = Media(_client=wa, _id="orig-id", filename=None, uploaded_to="p1")
    handle, source = helpers.internal_upload_file(
        wa=wa,
        file=src_media,
        app_id=None,
        mime_type=None,
        fallback_mime_type="application/octet-stream",
        fallback_filename="fallback.bin",
    )
    assert handle == "handle-1"
    assert source == helpers.MediaSource.MEDIA_OBJ


def test_internal_upload_file_bytes_gen():
    wa = mock.Mock()
    wa.api.create_upload_session.return_value = {"id": "session-1"}
    wa.api.upload_file.return_value = {"h": "handle-1"}
    wa.app_id = "app-1"
    handle, source = helpers.internal_upload_file(
        wa=wa,
        file=iter([b"a", b"b"]),
        app_id=None,
        mime_type="text/plain",
        fallback_mime_type="application/octet-stream",
        fallback_filename="fallback.bin",
    )
    assert handle == "handle-1"
    assert source == helpers.MediaSource.BYTES_GEN


def test_internal_upload_file_base64():
    wa = mock.Mock()
    wa.api.create_upload_session.return_value = {"id": "session-1"}
    wa.api.upload_file.return_value = {"h": "handle-1"}
    wa.app_id = "app-1"
    handle, source = helpers.internal_upload_file(
        wa=wa,
        file="aGVsbG8=",
        app_id=None,
        mime_type="text/plain",
        fallback_mime_type="application/octet-stream",
        fallback_filename="fallback.bin",
    )
    assert handle == "handle-1"
    assert source == helpers.MediaSource.BASE64


def test_internal_upload_file_unknown_filename_raises():
    wa = mock.Mock()
    with pytest.raises(ValueError):
        helpers.internal_upload_file(
            wa=wa,
            file=iter([b"a"]),
            app_id=None,
            mime_type="text/plain",
            fallback_mime_type="application/octet-stream",
            fallback_filename=None,
        )


# --- resolve_flow_json_param: OSError fallback -------------------------------


def test_resolve_flow_json_param_oserror_falls_back_to_str(mocker):
    mocker.patch("pathlib.Path.is_file", side_effect=OSError("boom"))
    assert helpers.resolve_flow_json_param("not-a-real-path") == "not-a-real-path"


# --- filter_not_uploaded_params: Carousel branch ------------------------------


def test_filter_not_uploaded_params_ignores_non_media_params():
    class _NotMedia:
        pass

    assert helpers.filter_not_uploaded_params([_NotMedia()]) == []


# --- internal_upload_file: extra edge cases ----------------------------------


async def _async_gen():
    yield b"a"


def test_internal_upload_file_async_bytes_gen_unsupported_raises():
    wa = mock.Mock()
    with pytest.raises(ValueError):
        helpers.internal_upload_file(
            wa=wa,
            file=_async_gen(),
            app_id=None,
            mime_type="text/plain",
            fallback_mime_type="application/octet-stream",
            fallback_filename="fallback.bin",
        )


def test_internal_upload_file_file_obj():
    wa = mock.Mock()
    wa.api.create_upload_session.return_value = {"id": "session-1"}
    wa.api.upload_file.return_value = {"h": "handle-1"}
    wa.app_id = "app-1"
    handle, source = helpers.internal_upload_file(
        wa=wa,
        file=io.BytesIO(b"data"),
        app_id=None,
        mime_type="text/plain",
        fallback_mime_type="application/octet-stream",
        fallback_filename="fallback.bin",
    )
    assert handle == "handle-1"
    assert source == helpers.MediaSource.FILE_OBJ


def test_internal_upload_file_unknown_length_raises():
    wa = mock.Mock()
    wa.get_media_url.return_value = mock.Mock(
        url="https://media.example/1", mime_type=None
    )
    wa.api.stream_media_bytes.return_value = _stream_cm()  # no Content-Length header
    with pytest.raises(ValueError):
        helpers.internal_upload_file(
            wa=wa,
            file="123456",
            app_id=None,
            mime_type="text/plain",
            fallback_mime_type="application/octet-stream",
            fallback_filename="fallback.bin",
        )


# --- media source detection / metadata edge cases ---------------------------


def test_detect_media_source_long_string_is_not_a_filename_error():
    # a name too long for the OS made `Path.is_file` raise instead of returning False
    b64 = base64.b64encode(b"x" * 3000).decode()
    assert helpers.detect_media_source(b64) == helpers.MediaSource.BASE64


@pytest.mark.parametrize("media", [bytearray(b"abc"), memoryview(b"abc")])
def test_detect_media_source_buffers_are_bytes(media):
    assert helpers.detect_media_source(media) == helpers.MediaSource.BYTES


def test_get_media_from_file_like_obj_rewinds_and_measures_whole_file():
    buf = io.BytesIO()
    buf.write(b"hello world")  # position left at the end, like after `img.save(buf)`
    info = helpers.get_media_from_file_like_obj(buf)
    assert info.length == 11
    assert buf.read() == b"hello world"


def test_get_media_from_file_like_obj_ignores_non_path_name():
    f = io.BytesIO(b"x")
    f.name = 3  # e.g. `os.fdopen`
    assert helpers.get_media_from_file_like_obj(f).filename is None


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        ('attachment; filename="a.pdf"; size=12', "a.pdf"),
        ("attachment; filename=a.pdf", "a.pdf"),
        ("attachment; filename*=UTF-8''%D7%A9.pdf", "ש.pdf"),
        ('attachment; filename="../../etc/passwd"', "passwd"),
        ("inline", None),
    ],
)
def test_get_filename_from_headers_parsing(header, expected):
    headers = httpx.Headers({"Content-Disposition": header})
    assert helpers.get_filename_from_httpx_response_headers(headers) == expected


def test_get_filename_and_mime_from_url_ignore_query_string():
    url = "https://cdn.example.com/a/img%201.jpg?w=1&h=2#frag"
    assert helpers.get_filename_from_url(url) == "img 1.jpg"
    assert helpers.get_mime_type_from_url(url) == "image/jpeg"
    assert helpers.get_filename_from_url("https://example.com/") is None


@pytest.mark.parametrize(
    ("content_type", "expected"),
    [
        ("image/PNG; charset=binary", "image/png"),
        ("application/octet-stream", None),
        ("binary/octet-stream", None),
        (None, None),
    ],
)
def test_get_mime_type_from_headers(content_type, expected):
    headers = httpx.Headers({"Content-Type": content_type} if content_type else {})
    assert helpers.get_mime_type_from_httpx_response_headers(headers) == expected


def test_get_content_length_ignored_when_content_encoded():
    assert (
        helpers.get_content_length_from_httpx_response_headers(
            httpx.Headers({"Content-Length": "10"})
        )
        == 10
    )
    assert (
        helpers.get_content_length_from_httpx_response_headers(
            httpx.Headers({"Content-Length": "10", "Content-Encoding": "gzip"})
        )
        is None
    )


def test_get_media_from_url_falls_back_to_url_extension_for_generic_content_type():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Accept-Encoding"] == "identity"
        return httpx.Response(
            200, content=b"x", headers={"Content-Type": "application/octet-stream"}
        )

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as session,
        contextlib.ExitStack() as stack,
    ):
        info = helpers.get_media_from_url(
            stack,
            "https://example.com/dir/pic.png?sig=a&b=c",
            session,
            download_chunk_size=1024,
            stream=True,
        )
    assert info.filename == "pic.png"
    assert info.mime_type == "image/png"


def test_describe_media_never_exposes_content_or_url_query():
    assert (
        helpers.describe_media("https://example.com/a.png?token=secret")
        == "https://example.com/a.png"
    )
    assert helpers.describe_media(b"secret") == "<bytes>"
    assert helpers.describe_media(base64.b64encode(b"secret!!").decode()) == "<base64>"
    assert helpers.describe_media("12345") == "12345"
    assert helpers.describe_media(object()) == "<object>"


# --- upload lifecycle -------------------------------------------------------


def test_internal_upload_media_closes_download_client_when_download_fails(mocker):
    client = mock.MagicMock()
    mocker.patch("pywa._helpers.httpx.Client", return_value=client)
    mocker.patch("pywa._helpers.get_media_from_url", side_effect=ValueError("404"))
    with pytest.raises(ValueError, match="404"):
        helpers.internal_upload_media(
            media="https://example.com/a.png",
            media_source=helpers.MediaSource.EXTERNAL_URL,
            media_type="image",
            mime_type=None,
            filename=None,
            download_chunk_size=None,
            wa=mock.Mock(),
            phone_id="p1",
        )
    client.__exit__.assert_called_once()


def test_internal_upload_media_keeps_callers_download_session_open(mocker):
    session = mock.MagicMock()
    mocker.patch("pywa._helpers.get_media_from_url", side_effect=ValueError("404"))
    with pytest.raises(ValueError):
        helpers.internal_upload_media(
            media="https://example.com/a.png",
            media_source=helpers.MediaSource.EXTERNAL_URL,
            media_type="image",
            mime_type=None,
            filename=None,
            download_chunk_size=None,
            wa=mock.Mock(),
            phone_id="p1",
            dl_session=session,
        )
    session.__exit__.assert_not_called()
    session.close.assert_not_called()


def test_internal_upload_media_exits_streaming_response_when_upload_fails():
    cm = _stream_cm(headers={"Content-Length": "4"})
    wa = mock.Mock()
    wa.get_media_url.return_value = mock.Mock(
        url="https://media.example/1", mime_type=None
    )
    wa.api.stream_media_bytes.return_value = cm
    wa.api.upload_media.side_effect = RuntimeError("boom")
    with pytest.raises(RuntimeError):
        helpers.internal_upload_media(
            media="123",
            media_source=helpers.MediaSource.MEDIA_ID,
            media_type="image",
            mime_type=None,
            filename=None,
            download_chunk_size=None,
            wa=wa,
            phone_id="p1",
        )
    cm.__exit__.assert_called_once()


def test_internal_upload_file_closes_download_client_when_download_fails(mocker):
    client = mock.MagicMock()
    mocker.patch("pywa._helpers.httpx.Client", return_value=client)
    mocker.patch("pywa._helpers.get_media_from_url", side_effect=ValueError("404"))
    with pytest.raises(ValueError, match="404"):
        helpers.internal_upload_file(
            wa=mock.Mock(),
            file="https://example.com/a.png?token=secret",
            app_id="a",
            mime_type=None,
            fallback_mime_type="image/png",
            fallback_filename="a.png",
        )
    client.__exit__.assert_called_once()


def test_internal_upload_file_closes_opened_path_when_upload_fails(tmp_path):
    p = tmp_path / "a.png"
    p.write_bytes(b"data")
    wa = mock.Mock()
    wa.api.create_upload_session.side_effect = RuntimeError("boom")
    opened = []
    real_open = helpers.get_media_from_path

    def spy(stack, path):
        info = real_open(stack, path)
        opened.append(info.content)
        return info

    with (
        mock.patch("pywa._helpers.get_media_from_path", spy),
        pytest.raises(ValueError),
    ):
        helpers.internal_upload_file(
            wa=wa,
            file=p,
            app_id="a",
            mime_type=None,
            fallback_mime_type="image/png",
            fallback_filename="a.png",
        )
    assert opened[0].closed


def test_internal_upload_file_error_message_has_no_payload():
    secret = base64.b64encode(b"private document").decode()
    wa = mock.Mock()
    wa.api.create_upload_session.side_effect = RuntimeError("boom")
    with pytest.raises(ValueError) as exc:
        helpers.internal_upload_file(
            wa=wa,
            file=secret,
            app_id="a",
            mime_type="image/png",
            fallback_mime_type="image/png",
            fallback_filename="a.png",
        )
    assert secret not in str(exc.value)


def test_upload_helpers_do_not_wrap_whatsapp_errors():
    err = WhatsAppError.from_dict({"code": 190, "message": "bad token"})
    wa = mock.Mock()
    wa.api.create_upload_session.side_effect = err
    with pytest.raises(WhatsAppError) as exc:
        helpers.internal_upload_file(
            wa=wa,
            file=b"x",
            app_id="a",
            mime_type="image/png",
            fallback_mime_type="image/png",
            fallback_filename="a.png",
        )
    assert exc.value is err


def test_run_in_threads_raises_first_error_and_skips_unstarted_tasks():
    started = []

    def ok():
        started.append(1)

    def fail():
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        helpers.run_in_threads("t", [fail, ok, ok])


# --- group_by_media -----------------------------------------------------------


def test_group_by_media_groups_equal_values_even_when_not_adjacent():
    items = [("a", 1), ("b", 2), ("a", 3)]
    assert helpers.group_by_media(items, lambda i: i[0]) == [
        ("a", [("a", 1), ("a", 3)]),
        ("b", [("b", 2)]),
    ]


def test_group_by_media_compares_streams_by_identity():
    f1, f2 = io.BytesIO(b"x"), io.BytesIO(b"x")  # equal content, different streams
    items = [(f1, 1), (f2, 2), (f1, 3)]
    groups = helpers.group_by_media(items, lambda i: i[0])
    assert [(m is f1, [n for _, n in g]) for m, g in groups] == [
        (True, [1, 3]),
        (False, [2]),
    ]


def test_upload_template_media_components_reads_a_shared_stream_once():
    buf = io.BytesIO(b"image")
    comps = [
        HeaderImage(buf, mime_type="image/png"),
        HeaderImage(b"other", mime_type="image/png"),
        HeaderImage(buf, mime_type="image/png"),  # not adjacent to the first one
    ]
    uploaded = []

    def upload(*, file, **_):
        uploaded.append(file)
        return f"handle-{len(uploaded)}", helpers.MediaSource.BYTES

    with mock.patch("pywa._helpers.internal_upload_file", side_effect=upload):
        helpers.upload_template_media_components(
            wa=mock.Mock(), app_id="a", components=comps
        )
    assert len(uploaded) == 2
    assert sum(f is buf for f in uploaded) == 1
    assert comps[0]._handle == comps[2]._handle != comps[1]._handle


# --- GeneratorStreamer <-> httpx contract --------------------------------------
# GeneratorStreamer fakes a file to get httpx to stream a generator in a multipart body.
# These pin the httpx behaviour it relies on, so an httpx upgrade that breaks it fails here.


def _multipart_request(streamer, handler_calls):
    def handler(request: httpx.Request) -> httpx.Response:
        handler_calls.append((request.headers, request.read()))
        return httpx.Response(200, json={"id": "1"})

    return httpx.Client(transport=httpx.MockTransport(handler)).post(
        "https://x.test/media", files={"file": ("a.bin", streamer, "image/png")}
    )


def test_generator_streamer_known_length_is_sent_with_content_length():
    calls = []
    _multipart_request(
        helpers.GeneratorStreamer(iter([b"abc", b"defg"]), length=7), calls
    )
    headers, body = calls[0]
    assert b"abcdefg" in body
    assert "content-length" in headers
    assert int(headers["content-length"]) == len(body)
    assert "transfer-encoding" not in headers


def test_generator_streamer_unknown_length_is_sent_chunked():
    calls = []
    _multipart_request(helpers.GeneratorStreamer(iter([b"abc", b"defg"])), calls)
    headers, body = calls[0]
    assert b"abcdefg" in body
    assert headers["transfer-encoding"] == "chunked"


def test_generator_streamer_skips_empty_chunks_instead_of_ending_early():
    calls = []
    _multipart_request(helpers.GeneratorStreamer(iter([b"abc", b"", b"def"])), calls)
    assert b"abcdef" in calls[0][1]


class _StreamingTransport(httpx.BaseTransport):
    """Unlike ``httpx.MockTransport`` (which buffers the body first) this iterates the body like a real transport."""

    def __init__(self, handler):
        self.handler = handler

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        return self.handler(request, b"".join(request.stream))


def test_generator_streamer_raises_when_the_body_is_sent_twice():
    # a redirect re-sends the same body; an exhausted generator must not be silently sent as empty
    sent = []

    def handler(request: httpx.Request, body: bytes) -> httpx.Response:
        sent.append(body)
        if len(sent) == 1:
            return httpx.Response(307, headers={"Location": "https://y.test/media"})
        return httpx.Response(200, json={"id": "1"})

    client = httpx.Client(transport=_StreamingTransport(handler), follow_redirects=True)
    with pytest.raises(RuntimeError, match="already consumed"):
        client.post(
            "https://x.test/media",
            files={"file": ("a.bin", helpers.GeneratorStreamer(iter([b"abc"])), "t")},
        )
    assert b"abc" in sent[0]


# --- sniffing the media type ---------------------------------------------------

_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8
_MP4_ISOM = b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00"


@pytest.mark.parametrize(
    ("head", "expected"),
    [
        (_PNG, ("image/png", ".png")),
        (b"\xff\xd8\xff\xe0" + b"\x00" * 12, ("image/jpeg", ".jpg")),
        (b"GIF89a" + b"\x00" * 10, ("image/gif", ".gif")),
        (b"GIF87a" + b"\x00" * 10, ("image/gif", ".gif")),
        (b"RIFF\x24\x00\x00\x00WEBPVP8 ", ("image/webp", ".webp")),
        (b"%PDF-1.7\n" + b"\x00" * 7, ("application/pdf", ".pdf")),
        (b"OggS\x00\x02" + b"\x00" * 10, ("audio/ogg", ".ogg")),
        (b"ID3\x04\x00" + b"\x00" * 11, ("audio/mpeg", ".mp3")),
        (b"#!AMR\n" + b"\x00" * 10, ("audio/amr", ".amr")),
        (_MP4_ISOM, ("video/mp4", ".mp4")),
        (b"\x00\x00\x00\x18ftypM4A \x00\x00\x00\x00", ("audio/mp4", ".m4a")),
        (b"\x00\x00\x00\x18ftyp3gp4\x00\x00\x00\x00", ("video/3gpp", ".3gp")),
    ],
)
def test_sniff_media_type(head, expected):
    assert helpers.sniff_media_type(head) == expected


@pytest.mark.parametrize(
    "head",
    [
        b"",
        b"hello world, plain text",
        b"RIFF\x24\x00\x00\x00WAVEfmt ",  # RIFF, but not WebP
        b"\x00\x00\x00\x18ftypheic\x00\x00\x00\x00",  # a brand we don't map is not guessed as mp4
        b"PK\x03\x04" + b"\x00" * 12,  # zip: docx, xlsx, apk...: ambiguous
    ],
)
def test_sniff_media_type_unknown_is_none(head):
    assert helpers.sniff_media_type(head) is None


def test_peek_media_head_does_not_consume_a_file():
    f = io.BytesIO(b"0123456789abcdefXYZ")
    f.seek(3)
    assert helpers.peek_media_head(f) == b"3456789abcdefXYZ"[:16]
    assert f.tell() == 3
    assert f.read() == b"3456789abcdefXYZ"


def test_peek_media_head_leaves_generators_and_unseekable_streams_alone():
    consumed = []

    def gen():
        consumed.append(1)
        yield _PNG

    assert helpers.peek_media_head(gen()) == b""
    assert helpers.peek_media_head(helpers.GeneratorStreamer(gen())) == b""
    assert not consumed

    class Pipe(io.BytesIO):
        def seekable(self):
            return False

    pipe = Pipe(_PNG)
    assert helpers.peek_media_head(pipe) == b""
    assert pipe.tell() == 0


def _upload_media(media, **kwargs):
    """Upload ``media`` to a fake API. Returns the ``(mime_type, filename, body)`` that the API got."""
    sent = {}

    def upload_media(*, media, mime_type, filename, **_):
        body = (
            media
            if isinstance(media, bytes)
            else b"".join(iter(lambda: media.read(1024), b""))
        )
        sent.update(mime_type=mime_type, filename=filename, body=body)
        return {"id": "m"}

    wa = mock.Mock()
    wa.api.upload_media = upload_media
    helpers.internal_upload_media(
        media=media,
        media_source=helpers.detect_media_source(media),
        media_type=kwargs.get("media_type"),
        mime_type=kwargs.get("mime_type"),
        filename=kwargs.get("filename"),
        download_chunk_size=None,
        wa=wa,
        phone_id="p1",
    )
    return sent["mime_type"], sent["filename"], sent["body"]


def test_upload_media_sniffs_when_nothing_else_is_known():
    assert _upload_media(_PNG)[:2] == ("image/png", "file.png")


def test_upload_media_sniffs_a_file_without_extension(tmp_path):
    p = tmp_path / "blob"
    p.write_bytes(_MP4_ISOM + b"payload")
    mime, name, body = _upload_media(p)
    assert (mime, name) == ("video/mp4", "blob")
    assert body == _MP4_ISOM + b"payload"  # sniffing didn't move the file


def test_upload_media_sniffs_a_file_object_without_moving_it():
    _, _, body = _upload_media(io.BytesIO(_PNG + b"rest"))
    assert body == _PNG + b"rest"


def test_upload_media_explicit_values_win_over_sniffing():
    mime, name, _ = _upload_media(_PNG, mime_type="image/x-custom", filename="a.dat")
    assert (mime, name) == ("image/x-custom", "a.dat")


def test_upload_media_partial_values_are_completed_by_sniffing():
    assert _upload_media(_PNG, filename="photo")[:2] == ("image/png", "photo")
    assert _upload_media(_PNG, mime_type="image/png")[:2] == ("image/png", "file.png")


@pytest.mark.parametrize(
    ("media_type", "mime", "name"),
    [
        ("image", "image/jpeg", "image.jpg"),
        ("sticker", "image/webp", "sticker.webp"),
        ("document", "application/pdf", "document.pdf"),
    ],
)
def test_upload_media_media_type_defaults_win_over_sniffing(media_type, mime, name):
    assert _upload_media(_PNG, media_type=media_type)[:2] == (mime, name)


def test_upload_media_unrecognized_content_keeps_the_old_fallback():
    assert _upload_media(b"just some text")[:2] == ("text/plain", "file.txt")


def test_upload_media_generator_is_not_consumed_by_sniffing():
    mime, _, body = _upload_media(iter([_PNG, b"rest"]))
    assert mime == "text/plain"
    assert body == _PNG + b"rest"


@pytest.mark.parametrize(
    ("filename", "mime"),
    [
        ("photo.png", "image/png"),
        (
            "report.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
    ],
)
def test_upload_media_guesses_the_type_from_a_given_filename(filename, mime):
    assert _upload_media(b"opaque", filename=filename)[:2] == (mime, filename)


def test_upload_media_filename_guess_comes_before_sniffing():
    assert _upload_media(_PNG, filename="photo.jpg")[0] == "image/jpeg"


def test_upload_media_unknown_extension_falls_through_to_sniffing_then_default():
    assert _upload_media(_PNG, filename="photo.zzz")[:2] == ("image/png", "photo.zzz")
    assert _upload_media(b"text", filename="photo.zzz")[0] == "text/plain"


def test_upload_media_filename_does_not_override_media_type_defaults():
    mime, name, _ = _upload_media(
        b"opaque", media_type="document", filename="report.xlsx"
    )
    assert (mime, name) == ("application/pdf", "report.xlsx")


def test_whatsapp_error_propagates_while_a_download_is_open():
    # the download is an httpx (generator based) context manager that the error passes through on its way out
    err = WhatsAppError.from_dict({"code": 190, "message": "bad token"})
    transport = httpx.MockTransport(lambda request: httpx.Response(200, content=b"x"))
    with (
        httpx.Client(transport=transport) as session,
        pytest.raises(WhatsAppError) as exc,
        contextlib.ExitStack() as stack,
    ):
        helpers.get_media_from_url(
            stack, "https://example.com/a.png", session, 1024, stream=True
        )
        raise err
    assert exc.value is err
