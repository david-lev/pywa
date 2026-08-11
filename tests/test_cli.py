import pathlib
import runpy
import shutil
import sys

import httpx
import pytest

from pywa import cli

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
