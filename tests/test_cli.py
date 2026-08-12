import pathlib
import runpy
import shutil
import sys

import httpx
import pytest

from pywa import WhatsApp, cli
from pywa.errors import SendMessageError

MANIFEST = [
    {
        "slug": "01-message-router",
        "title": "Smart Support Router Bot",
        "emoji": "🧭",
        "feature": "filters",
        "description": "Route messages with composable filters.",
    },
    {
        "slug": "02-order-bot",
        "title": "Quick-Serve Restaurant Ordering Bot",
        "emoji": "🍕",
        "feature": "types",
        "description": "Browse a categorized menu.",
    },
]

MAIN_PY_SRC = """from pywa_async import WhatsApp, filters, types

wa = WhatsApp(token="x", phone_id="y")


@wa.on_message(filters.text)
async def echo(_: WhatsApp, msg: types.Message):
    await msg.reply("hi")
"""

TREE = {
    "tree": [
        {"path": "examples/examples.json", "type": "blob"},
        {"path": "examples/01-message-router/main.py", "type": "blob"},
        {"path": "examples/01-message-router/requirements.txt", "type": "blob"},
        {"path": "examples/02-order-bot/main.py", "type": "blob"},
    ],
    "truncated": False,
}

RAW_FILES = {
    "examples/01-message-router/main.py": MAIN_PY_SRC,
    "examples/01-message-router/requirements.txt": "pywa[server]\n",
}


def _response(url: str, **kwargs) -> httpx.Response:
    request = httpx.Request("GET", url)
    return httpx.Response(request=request, **kwargs)


def _manifest_url(ref: str) -> str:
    return f"{cli.GITHUB_RAW_BASE}/{cli.GITHUB_REPO}/{ref}/examples/examples.json"


def _tree_url(ref: str) -> str:
    return f"{cli.GITHUB_API_BASE}/{cli.GITHUB_REPO}/git/trees/{ref}?recursive=1"


def _raw_url(ref: str, path: str) -> str:
    return f"{cli.GITHUB_RAW_BASE}/{cli.GITHUB_REPO}/{ref}/{path}"


def _install_router(mocker, routes: dict[str, httpx.Response]):
    """Monkeypatch `httpx.get` (the only network call the examples feature makes) to
    serve canned responses by exact URL, instead of hitting GitHub."""

    def fake_get(url, *args, **kwargs):
        try:
            return routes[url]
        except KeyError:
            raise AssertionError(f"Unexpected URL requested: {url}") from None

    return mocker.patch("pywa.cli.httpx.get", side_effect=fake_get)


def _default_routes(ref: str = "master") -> dict[str, httpx.Response]:
    routes = {
        _manifest_url(ref): _response(
            _manifest_url(ref), status_code=200, json=MANIFEST
        ),
        _tree_url(ref): _response(_tree_url(ref), status_code=200, json=TREE),
    }
    for path, content in RAW_FILES.items():
        routes[_raw_url(ref, path)] = _response(
            _raw_url(ref, path), status_code=200, text=content
        )
    return routes


# ==========================================
# _fetch_examples_manifest
# ==========================================


def test_fetch_examples_manifest_success(mocker):
    _install_router(mocker, _default_routes("master"))
    assert cli._fetch_examples_manifest("master") == MANIFEST


def test_fetch_examples_manifest_uses_given_ref(mocker):
    _install_router(mocker, _default_routes("v1.2.3"))
    assert cli._fetch_examples_manifest("v1.2.3") == MANIFEST


def test_fetch_examples_manifest_http_status_error(mocker):
    url = _manifest_url("master")
    _install_router(mocker, {url: _response(url, status_code=404, text="not found")})
    with pytest.raises(cli.PywaCLIException, match="Failed to fetch"):
        cli._fetch_examples_manifest("master")


def test_fetch_examples_manifest_connection_error(mocker):
    mocker.patch("pywa.cli.httpx.get", side_effect=httpx.ConnectError("no network"))
    with pytest.raises(cli.PywaCLIException, match="Failed to fetch"):
        cli._fetch_examples_manifest("master")


# ==========================================
# list_examples
# ==========================================


def test_list_examples_prints_all_slugs(mocker, capsys):
    _install_router(mocker, _default_routes("master"))
    cli.list_examples(ref="master")
    out = capsys.readouterr().out
    for example in MANIFEST:
        assert example["slug"] in out
        assert example["title"] in out
        assert example["description"] in out
    assert "pywa new examples <slug>" in out


def test_list_examples_propagates_fetch_errors(mocker):
    url = _manifest_url("master")
    _install_router(mocker, {url: _response(url, status_code=500, text="oops")})
    with pytest.raises(cli.PywaCLIException):
        cli.list_examples(ref="master")


# ==========================================
# generate_code
# ==========================================


def test_generate_code_writes_async_project(tmp_path, capsys):
    cli.generate_code(target=None, is_async=True, out_path=tmp_path)
    main_py = (tmp_path / "main.py").read_text(encoding="utf-8")
    assert main_py == cli.DEFAULT_PROJECT
    assert "✅ Created new Pywa project" in capsys.readouterr().out


def test_generate_code_writes_sync_project(tmp_path):
    cli.generate_code(target="project", is_async=False, out_path=tmp_path)
    main_py = (tmp_path / "main.py").read_text(encoding="utf-8")
    assert main_py == cli.async_code_to_sync(cli.DEFAULT_PROJECT)
    assert "pywa_async" not in main_py
    assert "async def" not in main_py


def test_generate_code_existing_file_is_not_overwritten(tmp_path, capsys):
    main_py = tmp_path / "main.py"
    main_py.write_text("existing content", encoding="utf-8")
    cli.generate_code(target=None, is_async=True, out_path=tmp_path)
    assert main_py.read_text(encoding="utf-8") == "existing content"
    assert "already exists" in capsys.readouterr().out


# ==========================================
# get_default_path
# ==========================================


def test_get_default_path_finds_main_py_in_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "main.py").write_text("wa = None")
    assert cli.get_default_path() == pathlib.Path("main.py")


def test_get_default_path_falls_back_to_other_filenames(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "app.py").write_text("wa = None")
    assert cli.get_default_path() == pathlib.Path("app.py")


def test_get_default_path_searches_known_subdirectories(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "bot.py").write_text("wa = None")
    assert cli.get_default_path() == pathlib.Path("src/bot.py")


def test_get_default_path_raises_when_nothing_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(cli.PywaCLIException, match="Could not auto-discover"):
        cli.get_default_path()


# ==========================================
# resolve_module_path
# ==========================================


def test_resolve_module_path_plain_file(tmp_path):
    file = tmp_path / "main.py"
    file.write_text("")
    module_str, sys_path = cli.resolve_module_path(file)
    assert module_str == "main"
    assert sys_path == tmp_path.resolve()


def test_resolve_module_path_package_member(tmp_path):
    pkg = tmp_path / "app"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    module_str, sys_path = cli.resolve_module_path(pkg / "main.py")
    assert module_str == "app.main"
    assert sys_path == tmp_path.resolve()


def test_resolve_module_path_init_file_resolves_to_package(tmp_path):
    pkg = tmp_path / "app"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    module_str, sys_path = cli.resolve_module_path(pkg / "__init__.py")
    assert module_str == "app"
    assert sys_path == tmp_path.resolve()


def test_resolve_module_path_nested_packages(tmp_path):
    outer = tmp_path / "src"
    outer.mkdir()
    (outer / "__init__.py").write_text("")
    inner = outer / "app"
    inner.mkdir()
    (inner / "__init__.py").write_text("")
    module_str, sys_path = cli.resolve_module_path(inner / "main.py")
    assert module_str == "src.app.main"
    assert sys_path == tmp_path.resolve()


# ==========================================
# discover_app_instance
# ==========================================


def _write_and_import_cleanup(monkeypatch, tmp_path, module_name, source):
    monkeypatch.syspath_prepend(str(tmp_path))
    (tmp_path / f"{module_name}.py").write_text(source)
    sys.modules.pop(module_name, None)


def test_discover_app_instance_prefers_conventional_names(tmp_path, monkeypatch):
    _write_and_import_cleanup(
        monkeypatch,
        tmp_path,
        "cli_app_preferred",
        "from pywa import WhatsApp\nwa = WhatsApp(token='t', phone_id='p')\n",
    )
    name, app = cli.discover_app_instance("cli_app_preferred")
    assert name == "wa"
    assert isinstance(app, WhatsApp)


def test_discover_app_instance_falls_back_to_any_whatsapp_instance(
    tmp_path, monkeypatch
):
    _write_and_import_cleanup(
        monkeypatch,
        tmp_path,
        "cli_app_fallback",
        "from pywa import WhatsApp\nmy_custom_var = WhatsApp(token='t', phone_id='p')\n",
    )
    name, app = cli.discover_app_instance("cli_app_fallback")
    assert name == "my_custom_var"
    assert isinstance(app, WhatsApp)


def test_discover_app_instance_explicit_name(tmp_path, monkeypatch):
    _write_and_import_cleanup(
        monkeypatch,
        tmp_path,
        "cli_app_explicit",
        "from pywa import WhatsApp\nbot_client = WhatsApp(token='t', phone_id='p')\n",
    )
    name, _app = cli.discover_app_instance(
        "cli_app_explicit", explicit_app_name="bot_client"
    )
    assert name == "bot_client"


def test_discover_app_instance_explicit_name_not_found(tmp_path, monkeypatch):
    _write_and_import_cleanup(monkeypatch, tmp_path, "cli_app_missing_name", "x = 1\n")
    with pytest.raises(cli.PywaCLIException, match="Could not find app name"):
        cli.discover_app_instance("cli_app_missing_name", explicit_app_name="wa")


def test_discover_app_instance_explicit_name_wrong_type(tmp_path, monkeypatch):
    _write_and_import_cleanup(
        monkeypatch, tmp_path, "cli_app_wrong_type", "wa = 'not a client'\n"
    )
    with pytest.raises(cli.PywaCLIException, match="is not a `pywa.WhatsApp` instance"):
        cli.discover_app_instance("cli_app_wrong_type", explicit_app_name="wa")


def test_discover_app_instance_no_app_found(tmp_path, monkeypatch):
    _write_and_import_cleanup(monkeypatch, tmp_path, "cli_app_none_found", "x = 1\n")
    with pytest.raises(
        cli.PywaCLIException, match="Could not auto-discover a WhatsApp"
    ):
        cli.discover_app_instance("cli_app_none_found")


def test_discover_app_instance_import_error(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(tmp_path))
    with pytest.raises(cli.PywaCLIException, match="Import error"):
        cli.discover_app_instance("cli_module_does_not_exist_xyz")


# ==========================================
# serve_application
# ==========================================


def test_serve_application_uvicorn_not_installed(mocker):
    mocker.patch.dict(sys.modules, {"uvicorn": None})
    with pytest.raises(cli.PywaCLIException, match="Could not import uvicorn"):
        cli.serve_application(command="run")


def test_serve_application_entrypoint_with_path_conflicts(tmp_path):
    with pytest.raises(cli.PywaCLIException, match="Cannot use --entrypoint"):
        cli.serve_application(command="run", path=tmp_path, entrypoint="mod:app")


def test_serve_application_invalid_entrypoint_format():
    with pytest.raises(cli.PywaCLIException, match="Entrypoint must be in the format"):
        cli.serve_application(command="run", entrypoint="no-colon-here")


def test_serve_application_missing_target_path(tmp_path):
    missing = tmp_path / "does-not-exist.py"
    with pytest.raises(cli.PywaCLIException, match="Target path does not exist"):
        cli.serve_application(command="run", path=missing)


def test_serve_application_rejects_already_configured_client(mocker, tmp_path):
    target = tmp_path / "main.py"
    target.write_text("")
    fake_server_type = mocker.Mock(name="FASTAPI")
    fake_server_type.name = "FASTAPI"
    fake_client = mocker.Mock(_server=object(), _server_type=fake_server_type)
    mocker.patch("pywa.cli.discover_app_instance", return_value=("wa", fake_client))
    with pytest.raises(cli.PywaCLIException, match="already configured with a"):
        cli.serve_application(command="run", path=target)


def test_serve_application_starts_uvicorn_with_resolved_app(mocker, tmp_path):
    target = tmp_path / "main.py"
    target.write_text("")
    fake_client = mocker.Mock(_server=None, _server_type=None, _uvicorn_workers=0)
    mocker.patch("pywa.cli.discover_app_instance", return_value=("wa", fake_client))
    mocker.patch("pywa.cli.setup_console_logging")
    run_mock = mocker.patch("uvicorn.run")
    cli.serve_application(command="dev", path=target)
    assert run_mock.call_count == 1
    kwargs = run_mock.call_args.kwargs
    assert kwargs["app"].endswith(
        f"main:wa.{WhatsApp._setup_and_get_starlette_app.__name__}"
    )
    assert kwargs["factory"] is True
    assert fake_client._uvicorn_workers == 1


def test_serve_application_uses_entrypoint_directly(mocker):
    mocker.patch("pywa.cli.setup_console_logging")
    run_mock = mocker.patch("uvicorn.run")
    cli.serve_application(command="run", entrypoint="mypkg.mod:app")
    kwargs = run_mock.call_args.kwargs
    assert kwargs["app"].endswith(
        f"mypkg.mod:app.{WhatsApp._setup_and_get_starlette_app.__name__}"
    )


# ==========================================
# send_messages
# ==========================================


def test_send_messages_requires_token_and_phone_id():
    with pytest.raises(cli.PywaCLIException, match="API token and phone ID"):
        cli.send_messages(
            send_type="text",
            to=["123"],
            delay=0,
            reply_to_message_id=None,
            token="",
            phone_id="p",
            text="hi",
        )


def test_send_messages_sends_text_to_each_recipient(mocker, capsys):
    send_mock = mocker.patch.object(
        WhatsApp,
        "send_message",
        return_value=mocker.Mock(id="wamid.1", uploaded_media=None),
    )
    cli.send_messages(
        send_type="text",
        to=["111", "222"],
        delay=0,
        reply_to_message_id=None,
        token="t",
        phone_id="p",
        text="hello",
    )
    assert send_mock.call_count == 2
    out = capsys.readouterr().out
    assert "✅ [1/2] Sent text to 111" in out
    assert "✅ [2/2] Sent text to 222" in out


def test_send_messages_continues_after_recipient_send_error(mocker, capsys):
    error = SendMessageError(raw={}, code=131026, message="boom")
    mocker.patch.object(WhatsApp, "send_message", side_effect=error)
    cli.send_messages(
        send_type="text",
        to=["111", "222"],
        delay=0,
        reply_to_message_id=None,
        token="t",
        phone_id="p",
        text="hi",
    )
    out = capsys.readouterr().out
    assert "❌ [1/2] Failed to send text to 111:" in out
    assert "❌ [2/2] Failed to send text to 222:" in out
    assert out.count("boom") == 2


def test_send_messages_unexpected_error_aborts_batch(mocker):
    send_mock = mocker.patch.object(
        WhatsApp, "send_message", side_effect=RuntimeError("boom")
    )
    with pytest.raises(
        cli.PywaCLIException, match="Unexpected error while sending text to 111: boom"
    ):
        cli.send_messages(
            send_type="text",
            to=["111", "222"],
            delay=0,
            reply_to_message_id=None,
            token="t",
            phone_id="p",
            text="hi",
        )
    # the batch is aborted on the first unexpected error, the second recipient is never attempted
    send_mock.assert_called_once()


def test_send_messages_location_uses_lat_lon(mocker):
    send_mock = mocker.patch.object(
        WhatsApp,
        "send_location",
        return_value=mocker.Mock(id="wamid.1", uploaded_media=None),
    )
    cli.send_messages(
        send_type="location",
        to=["111"],
        delay=0,
        reply_to_message_id=None,
        token="t",
        phone_id="p",
        latitude=1.23,
        longitude=4.56,
        name="HQ",
    )
    send_mock.assert_called_once()
    assert send_mock.call_args.kwargs["latitude"] == 1.23
    assert send_mock.call_args.kwargs["longitude"] == 4.56


def test_send_messages_media_reuses_uploaded_media(mocker):
    send_mock = mocker.patch.object(
        WhatsApp,
        "send_image",
        side_effect=[
            mocker.Mock(id="wamid.1", uploaded_media="media-id-123"),
            mocker.Mock(id="wamid.2", uploaded_media=None),
        ],
    )
    cli.send_messages(
        send_type="image",
        to=["111", "222"],
        delay=0,
        reply_to_message_id=None,
        token="t",
        phone_id="p",
        media="./photo.jpg",
    )
    assert send_mock.call_args_list[0].kwargs["image"] == "./photo.jpg"
    assert send_mock.call_args_list[1].kwargs["image"] == "media-id-123"


def test_send_messages_verbose_enables_debug_logging(mocker):
    mocker.patch.object(
        WhatsApp,
        "send_message",
        return_value=mocker.Mock(id="wamid.1", uploaded_media=None),
    )
    log_mock = mocker.patch("pywa.cli.setup_console_logging")
    cli.send_messages(
        send_type="text",
        to=["111"],
        delay=0,
        reply_to_message_id=None,
        token="t",
        phone_id="p",
        verbose=True,
        text="hi",
    )
    log_mock.assert_called_once_with("debug")


def test_send_messages_sleeps_between_recipients(mocker):
    mocker.patch.object(
        WhatsApp,
        "send_message",
        return_value=mocker.Mock(id="wamid.1", uploaded_media=None),
    )
    sleep_mock = mocker.patch("pywa.cli.time.sleep")
    cli.send_messages(
        send_type="text",
        to=["111", "222", "333"],
        delay=2.5,
        reply_to_message_id=None,
        token="t",
        phone_id="p",
        text="hi",
    )
    assert sleep_mock.call_count == 2
    sleep_mock.assert_called_with(2.5)


# ==========================================
# download_example
# ==========================================


def test_download_example_unknown_name(mocker, tmp_path):
    _install_router(mocker, _default_routes("master"))
    with pytest.raises(cli.PywaCLIException, match="Unknown example"):
        cli.download_example(
            name="does-not-exist", is_async=True, out_path=tmp_path, ref="master"
        )


def test_download_example_async_writes_files_unmodified(mocker, tmp_path):
    _install_router(mocker, _default_routes("master"))
    cli.download_example(
        name="01-message-router", is_async=True, out_path=tmp_path, ref="master"
    )
    dest = tmp_path / "01-message-router"
    assert (dest / "main.py").read_text() == MAIN_PY_SRC
    assert (dest / "requirements.txt").read_text() == "pywa[server]\n"


def test_download_example_sync_converts_python_files(mocker, tmp_path):
    _install_router(mocker, _default_routes("master"))
    cli.download_example(
        name="01-message-router", is_async=False, out_path=tmp_path, ref="master"
    )
    dest = tmp_path / "01-message-router"
    converted = (dest / "main.py").read_text()
    assert converted == cli.async_code_to_sync(MAIN_PY_SRC)
    assert "pywa_async" not in converted
    assert "async def" not in converted
    assert "await " not in converted
    # non-python files are copied byte-for-byte, never converted
    assert (dest / "requirements.txt").read_text() == "pywa[server]\n"


def test_download_example_only_fetches_files_under_example_prefix(mocker, tmp_path):
    _install_router(mocker, _default_routes("master"))
    cli.download_example(
        name="01-message-router", is_async=True, out_path=tmp_path, ref="master"
    )
    dest = tmp_path / "01-message-router"
    assert sorted(p.name for p in dest.iterdir()) == ["main.py", "requirements.txt"]


def test_download_example_respects_custom_out_path(mocker, tmp_path):
    _install_router(mocker, _default_routes("master"))
    out_dir = tmp_path / "somewhere" / "nested"
    out_dir.mkdir(parents=True)
    cli.download_example(
        name="01-message-router", is_async=True, out_path=out_dir, ref="master"
    )
    assert (out_dir / "01-message-router" / "main.py").exists()


def test_download_example_respects_ref(mocker, tmp_path):
    _install_router(mocker, _default_routes("v2.0.0"))
    cli.download_example(
        name="01-message-router", is_async=True, out_path=tmp_path, ref="v2.0.0"
    )
    assert (tmp_path / "01-message-router" / "main.py").read_text() == MAIN_PY_SRC


def test_download_example_existing_nonempty_dir_raises(mocker, tmp_path):
    _install_router(mocker, _default_routes("master"))
    dest = tmp_path / "01-message-router"
    dest.mkdir()
    (dest / "keep.txt").write_text("already here")
    with pytest.raises(cli.PywaCLIException, match="already exists and is not empty"):
        cli.download_example(
            name="01-message-router", is_async=True, out_path=tmp_path, ref="master"
        )


def test_download_example_existing_empty_dir_is_fine(mocker, tmp_path):
    _install_router(mocker, _default_routes("master"))
    dest = tmp_path / "01-message-router"
    dest.mkdir()
    cli.download_example(
        name="01-message-router", is_async=True, out_path=tmp_path, ref="master"
    )
    assert (dest / "main.py").exists()


def test_download_example_no_files_found_for_prefix(mocker, tmp_path):
    routes = _default_routes("master")
    empty_tree_url = _tree_url("master")
    routes[empty_tree_url] = _response(
        empty_tree_url,
        status_code=200,
        json={"tree": [{"path": "examples/examples.json", "type": "blob"}]},
    )
    _install_router(mocker, routes)
    with pytest.raises(cli.PywaCLIException, match="No files found"):
        cli.download_example(
            name="01-message-router", is_async=True, out_path=tmp_path, ref="master"
        )


def test_download_example_tree_fetch_error(mocker, tmp_path):
    routes = _default_routes("master")
    routes[_tree_url("master")] = _response(
        _tree_url("master"), status_code=503, text="unavailable"
    )
    _install_router(mocker, routes)
    with pytest.raises(
        cli.PywaCLIException, match="Failed to fetch the repository file tree"
    ):
        cli.download_example(
            name="01-message-router", is_async=True, out_path=tmp_path, ref="master"
        )


def test_download_example_file_fetch_error(mocker, tmp_path):
    routes = _default_routes("master")
    bad_url = _raw_url("master", "examples/01-message-router/main.py")
    routes[bad_url] = _response(bad_url, status_code=404, text="gone")
    _install_router(mocker, routes)
    with pytest.raises(cli.PywaCLIException, match="Failed to download"):
        cli.download_example(
            name="01-message-router", is_async=True, out_path=tmp_path, ref="master"
        )


# ==========================================
# `pywa new examples ...` CLI dispatch (argparse -> main())
# ==========================================


def test_main_new_examples_lists_when_no_name_given(mocker, capsys, monkeypatch):
    _install_router(mocker, _default_routes("master"))
    monkeypatch.setattr(sys, "argv", ["pywa", "new", "examples"])
    cli.main()
    out = capsys.readouterr().out
    assert "01-message-router" in out
    assert "02-order-bot" in out


def test_main_new_examples_downloads_given_slug(mocker, tmp_path, monkeypatch):
    _install_router(mocker, _default_routes("master"))
    monkeypatch.setattr(
        sys,
        "argv",
        ["pywa", "new", "examples", "01-message-router", "-o", str(tmp_path)],
    )
    cli.main()
    dest = tmp_path / "01-message-router"
    assert (dest / "main.py").read_text() == cli.async_code_to_sync(MAIN_PY_SRC)


def test_main_new_examples_downloads_async_variant(mocker, tmp_path, monkeypatch):
    _install_router(mocker, _default_routes("master"))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pywa",
            "new",
            "examples",
            "01-message-router",
            "--async",
            "-o",
            str(tmp_path),
        ],
    )
    cli.main()
    dest = tmp_path / "01-message-router"
    assert (dest / "main.py").read_text() == MAIN_PY_SRC


def test_main_new_examples_respects_ref_flag(mocker, tmp_path, monkeypatch):
    _install_router(mocker, _default_routes("v9.9.9"))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pywa",
            "new",
            "examples",
            "01-message-router",
            "--ref",
            "v9.9.9",
            "-o",
            str(tmp_path),
        ],
    )
    cli.main()
    assert (tmp_path / "01-message-router" / "main.py").exists()


def test_main_new_examples_unknown_slug_exits_with_error(mocker, capsys, monkeypatch):
    _install_router(mocker, _default_routes("master"))
    monkeypatch.setattr(sys, "argv", ["pywa", "new", "examples", "does-not-exist"])
    with pytest.raises(SystemExit) as exc_info:
        cli.main()
    assert exc_info.value.code == 1
    assert "Unknown example" in capsys.readouterr().out


def test_main_new_no_subcommand_generates_project(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["pywa", "new", "-o", str(tmp_path)])
    cli.main()
    assert (tmp_path / "main.py").exists()


# ==========================================
# `pywa run` / `pywa dev` CLI dispatch (argparse -> main())
# ==========================================


def test_main_run_dispatches_to_serve_application(mocker, tmp_path, monkeypatch):
    serve_mock = mocker.patch("pywa.cli.serve_application")
    target = tmp_path / "main.py"
    target.write_text("")
    monkeypatch.setattr(
        sys, "argv", ["pywa", "run", str(target), "--host", "0.0.0.0", "--port", "9000"]
    )
    cli.main()
    serve_mock.assert_called_once()
    kwargs = serve_mock.call_args.kwargs
    assert kwargs["command"] == "run"
    assert kwargs["path"] == pathlib.Path(str(target))
    assert kwargs["host"] == "0.0.0.0"
    assert kwargs["port"] == 9000


def test_main_dev_resolves_reload_dirs_to_absolute_paths(mocker, tmp_path, monkeypatch):
    serve_mock = mocker.patch("pywa.cli.serve_application")
    reload_dir = tmp_path / "src"
    reload_dir.mkdir()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["pywa", "dev", "--reload-dir", "src"])
    cli.main()
    kwargs = serve_mock.call_args.kwargs
    assert kwargs["reload_dirs"] == [str(reload_dir.resolve())]


def test_main_top_level_exception_prints_and_exits(mocker, capsys, monkeypatch):
    mocker.patch("pywa.cli.serve_application", side_effect=RuntimeError("kaboom"))
    monkeypatch.setattr(sys, "argv", ["pywa", "run"])
    with pytest.raises(SystemExit) as exc_info:
        cli.main()
    assert exc_info.value.code == 1
    assert "❌ Error: kaboom" in capsys.readouterr().out


# ==========================================
# `pywa send` CLI dispatch (argparse -> main())
# ==========================================


def test_main_send_dispatches_to_send_messages(mocker, monkeypatch):
    send_mock = mocker.patch("pywa.cli.send_messages")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pywa",
            "send",
            "text",
            "--to",
            "111",
            "--token",
            "t",
            "--phone-id",
            "p",
            "hi there",
        ],
    )
    cli.main()
    send_mock.assert_called_once()
    kwargs = send_mock.call_args.kwargs
    assert kwargs["send_type"] == "text"
    assert kwargs["to"] == ["111"]
    assert kwargs["token"] == "t"
    assert kwargs["phone_id"] == "p"


# ==========================================
# Local `examples/*/main.py` are actually importable
#
# These don't go through download_example at all — they exercise the example source
# checked into the repo directly, to catch import errors, typos (e.g. an attribute that
# got renamed, like `.wa_id` -> `.bsuid`) and other issues that only surface once the
# module actually runs, on top of `ruff check`/`py_compile`'s purely-syntactic checks.
# ==========================================

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
EXAMPLES_DIR = REPO_ROOT / "examples"
EXAMPLE_MAIN_FILES = sorted(EXAMPLES_DIR.glob("*/main.py"))


class _NoOpTimer:
    """Stand-in for `threading.Timer`, so importing an example that attaches to its own
    `server=...` (see 12-existing-app-integration) never schedules the real background
    callback-URL registration, which would otherwise hit the real Graph API a few seconds
    into the test run."""

    def __init__(self, *args, **kwargs):
        pass

    def start(self):
        pass


def _example_env() -> dict[str, str]:
    """Fake credentials/ids so `WhatsApp(...)` construction succeeds without ever making
    a real network call, plus values for the handful of extra `os.environ[...]` reads
    some examples do at import time (`WHATSAPP_BUSINESS_ACCOUNT_ID`, `LOAN_FLOW_ID`)."""
    return {
        "WHATSAPP_PHONE_ID": "100000000000000",
        "WHATSAPP_TOKEN": "test-token",
        "WHATSAPP_APP_ID": "100000000000000",
        "WHATSAPP_APP_SECRET": "test-app-secret",
        "WHATSAPP_BUSINESS_ACCOUNT_ID": "100000000000000",
        "LOAN_FLOW_ID": "test-flow-id",
        # Truthy, so examples skip their `if not callback_url: start_ngrok_tunnel(...)`
        # branch entirely instead of trying to open a real ngrok tunnel.
        "CALLBACK_URL": "https://example.com/callback",
    }


@pytest.mark.parametrize(
    "example_main", EXAMPLE_MAIN_FILES, ids=lambda p: p.parent.name
)
def test_example_main_is_importable(example_main, tmp_path, monkeypatch):
    # Copy to an isolated tmp dir before executing: a couple of examples write to disk at
    # import time (e.g. 11-media-inbox-bot creates a `downloads/` dir next to `main.py`),
    # and we don't want that touching the real examples/ tree.
    example_dir = tmp_path / example_main.parent.name
    shutil.copytree(
        example_main.parent, example_dir, ignore=shutil.ignore_patterns("__pycache__")
    )

    monkeypatch.setattr("pywa.server.threading.Timer", _NoOpTimer)
    monkeypatch.chdir(example_dir)
    # So sibling-module imports resolve (e.g. 05-loan-application-flow's `import flow_json`),
    # the same way `pywa`'s own module resolution adds a bot's directory to sys.path.
    monkeypatch.syspath_prepend(str(example_dir))
    for key, value in _example_env().items():
        monkeypatch.setenv(key, value)

    # Only 05-loan-application-flow reads this, but it's harmless to set unconditionally.
    private_key_path = example_dir / "business_private_key.pem"
    private_key_path.write_text("dummy-private-key-for-import-smoke-test")
    monkeypatch.setenv("BUSINESS_PRIVATE_KEY_PATH", str(private_key_path))

    try:
        runpy.run_path(str(example_dir / "main.py"), run_name="pywa_example_under_test")
    finally:
        # Avoid leaking a stale `flow_json` module into other parametrizations/tests.
        sys.modules.pop("flow_json", None)
