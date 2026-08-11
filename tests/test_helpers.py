"""Additional tests for pywa/_helpers.py targeting branches not exercised
via tests/test_client.py (which already covers the happy paths of several
of these helpers through the `helpers` alias)."""

import io
from unittest import mock

import httpx
import pytest

from pywa import _helpers as helpers
from pywa.errors import PywaUnknownEnumMemberWarning
from pywa.types.flows import FlowJSON
from pywa.types.media import Media
from pywa.types.sent_update import RecipientType

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
    info = helpers.get_media_from_path(p)
    try:
        assert info.filename == "a.txt"
        assert info.length == 5
        assert info.content.read() == b"hello"
    finally:
        info.content.close()


# --- get_media_from_file_like_obj -----------------------------------------


def test_get_media_from_file_like_obj_with_fileno(tmp_path):
    p = tmp_path / "b.txt"
    p.write_text("hello world")
    with open(p, "rb") as f:
        info = helpers.get_media_from_file_like_obj(f)
        assert info.length == 11
        assert info.filename == str(p)
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
    info = helpers.get_media_from_url(
        "https://example.com/file.txt", session, download_chunk_size=1024, stream=True
    )
    assert b"".join(info.content) == b"filedata"
    assert info.mime_type == "text/plain"
    assert info.length == 8
    info.cm.__exit__(None, None, None)


def test_get_media_from_url_http_error_raises():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, content=b"not found")

    session = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(ValueError):
        helpers.get_media_from_url(
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
    info = helpers.get_media_from_media_id_or_obj_or_url(
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
    info = helpers.get_media_from_media_id_or_obj_or_url(
        wa=wa,
        media="https://lookaside.fbsbx.com/whatsapp_business/attachments/?mid=1",
        media_source=helpers.MediaSource.MEDIA_URL,
        download_chunk_size=1024,
        stream=True,
    )
    assert b"".join(info.content) == b"data"


def test_get_media_from_media_id_or_obj_or_url_invalid_source_raises():
    wa = mock.Mock()
    with pytest.raises(ValueError):
        helpers.get_media_from_media_id_or_obj_or_url(
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
    with pytest.raises(ValueError):
        helpers.get_media_from_media_id_or_obj_or_url(
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
