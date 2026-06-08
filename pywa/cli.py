# ruff: noqa: T201
"""
Pywa CLI

A command-line interface to easily serve and develop WhatsApp applications built with Pywa.
Provides `run` (production) and `dev` (development) commands with hot-reloading support.
"""

from __future__ import annotations

import argparse
import importlib
import itertools
import os
import pathlib
import sys
import time

from . import __version__ as pywa_version
from .client import WhatsApp

try:
    import uvicorn
except ImportError:
    uvicorn = None


class PywaCLIException(Exception):
    """Base exception for all Pywa CLI related errors."""


def get_default_path() -> pathlib.Path:
    """
    Attempt to auto-discover the application file if none is provided.

    Returns:
        A pathlib.Path object pointing to the discovered entry point.

    Raises:
        PywaCLIException: If no standard application file could be found.
    """
    directories = ["", "app/", "bot/", "wa/", "src/"]
    filenames = ["main.py", "app.py", "wa.py", "bot.py"]

    for full_path in (f"{d}{f}" for d, f in itertools.product(directories, filenames)):
        path = pathlib.Path(full_path)
        if path.is_file():
            return path

    raise PywaCLIException(
        "Could not auto-discover a default app file (e.g., main.py, app.py). "
        "Please provide an explicit path."
    )


def resolve_module_path(path: pathlib.Path) -> tuple[str, pathlib.Path]:
    """
    Determine the Python module import string and the required sys.path addition.

    Args:
        path: The file path to the application script.

    Returns:
        A tuple containing:
        - The import string (e.g., 'src.app.main')
        - The absolute path to add to sys.path so the import works.
    """
    use_path = path.resolve()
    module_path = use_path.parent if use_path.stem == "__init__" else use_path

    module_parts = [module_path.stem]
    extra_sys_path = module_path.parent

    for parent in module_path.parents:
        if (parent / "__init__.py").is_file():
            module_parts.insert(0, parent.stem)
            extra_sys_path = parent.parent
        else:
            break

    module_str = ".".join(module_parts)
    return module_str, extra_sys_path.resolve()


def discover_app_instance(
    module_str: str, explicit_app_name: str | None = None
) -> tuple[str, WhatsApp]:
    """
    Discover the WhatsApp application instance name inside the loaded module.

    Args:
        module_str: The resolved module import string.
        explicit_app_name: An optional explicit variable name to look for.

    Returns:
        The string name of the variable holding the WhatsApp application instance.

    Raises:
        PywaCLIException: If the module cannot be imported or the app instance isn't found.
    """
    try:
        mod = importlib.import_module(module_str)
    except (ImportError, ValueError) as e:
        raise PywaCLIException(
            f"Import error: {e}\nEnsure all package directories have an __init__.py file."
        ) from e

    object_names_set = set(dir(mod))

    if explicit_app_name:
        if explicit_app_name not in object_names_set:
            raise PywaCLIException(
                f"Could not find app name '{explicit_app_name}' in '{module_str}'"
            )

        app = getattr(mod, explicit_app_name)
        if not isinstance(app, WhatsApp):
            raise PywaCLIException(
                f"The variable '{explicit_app_name}' in '{module_str}' is not a `pywa.WhatsApp` instance."
            )
        return explicit_app_name, app

    for preferred_name in ["wa", "bot", "client", "app", "main"]:
        if preferred_name in object_names_set:
            obj = getattr(mod, preferred_name)
            if isinstance(obj, WhatsApp):
                return preferred_name, obj

    for name in object_names_set:
        obj = getattr(mod, name)
        if isinstance(obj, WhatsApp):
            return name, obj

    raise PywaCLIException(
        f"Could not auto-discover a WhatsApp app instance in '{module_str}'. "
        "Use --app to specify the variable name manually."
    )


def serve_application(
    command: str,
    path: pathlib.Path | None = None,
    app: str | None = None,
    entrypoint: str | None = None,
    **uvicorn_kwargs,
) -> None:
    """
    Core function that resolves dependencies and starts the Uvicorn server.
    """
    if not uvicorn:
        print(
            "❌ Error: Could not import Uvicorn. Please install it using 'pip install \"pywa[server]\"'."
        )
        sys.exit(1)

    if entrypoint and (path or app):
        print(
            "❌ Error: Cannot use --entrypoint together with a path or --app arguments."
        )
        sys.exit(1)

    workers = uvicorn_kwargs.get("workers")

    try:
        if entrypoint:
            module_str, _, app_name = entrypoint.partition(":")
            if not module_str or not app_name:
                raise PywaCLIException("Entrypoint must be in the format 'module:app'")

            sys_path = pathlib.Path.cwd().resolve()
            sys.path.insert(0, str(sys_path))

        else:
            target_path = path or get_default_path()
            if not target_path.exists():
                raise PywaCLIException(f"Target path does not exist: {target_path}")

            module_str, sys_path = resolve_module_path(target_path)
            sys.path.insert(0, str(sys_path))
            app_name, client = discover_app_instance(module_str, app)
            client._uvicorn_workers = workers or 1

    except PywaCLIException as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    base_import_string = f"{module_str}:{app_name}"
    uvicorn_app_string = (
        f"{base_import_string}.{WhatsApp._setup_and_get_starlette_app.__name__}"
    )

    host = uvicorn_kwargs.get("host", "127.0.0.1")
    port = uvicorn_kwargs.get("port", 8000)

    mode = "development" if command == "dev" else "production"
    print(f"\n🚀  Starting Pywa in {mode} mode")
    print("-" * 40)
    print(f"📦  Module Path:  {sys_path}")
    print(f"🔍  App Instance: {base_import_string}")
    print(f"🌐  Server URL:   http://{host}:{port}")
    if command == "dev":
        print("⚠️  Auto-reload:  Enabled (Use 'pywa run' for production)")
    print("-" * 40 + "\n")

    clean_kwargs = {k: v for k, v in uvicorn_kwargs.items() if v is not None}

    clean_kwargs["app"] = uvicorn_app_string
    clean_kwargs["factory"] = True
    clean_kwargs["log_config"] = None

    uvicorn.run(**clean_kwargs)


def send_messages(
    send_type: str,
    to: list[str],
    delay: float,
    reply_to_message_id: str | None,
    token: str,
    phone_id: str,
    **kwargs,
):
    if not token or not phone_id:
        raise PywaCLIException(
            "WhatsApp API token and phone ID are required. Provide them via --token, --phone-id or set PYWA_TOKEN and PYWA_PHONE_ID environment variables."
        )

    wa = WhatsApp(phone_id=phone_id, token=token)
    uploaded_media = None

    for index, recipient in enumerate(to):
        if index > 0 and delay > 0:
            time.sleep(delay)

        try:
            if send_type == "text":
                sent = wa.send_message(
                    to=recipient,
                    text=kwargs["text"],
                    preview_url=kwargs.get("preview_url", False),
                    reply_to_message_id=reply_to_message_id,
                )
            elif send_type == "location":
                sent = wa.send_location(
                    to=recipient,
                    latitude=kwargs["latitude"],
                    longitude=kwargs["longitude"],
                    name=kwargs.get("name"),
                    address=kwargs.get("address"),
                    reply_to_message_id=reply_to_message_id,
                )
            else:
                send_method = getattr(wa, f"send_{send_type}")

                payload = {
                    send_type: uploaded_media or kwargs.get("media"),
                    "reply_to_message_id": reply_to_message_id,
                }

                for arg in ["caption", "mime_type", "filename", "is_voice"]:
                    if arg in kwargs and kwargs[arg] is not None:
                        payload[arg] = kwargs[arg]

                sent = send_method(to=recipient, **payload)

                if sent.uploaded_media:
                    uploaded_media = sent.uploaded_media

            print(
                f"✅ [{index + 1}/{len(to)}] Sent {send_type} to {recipient} (Msg ID: {sent.id})"
            )

        except Exception as e:
            print(
                f"❌ [{index + 1}/{len(to)}] Failed to send {send_type} to {recipient}: {e}"
            )


DEFAULT_PROJECT = """from pywa_async import WhatsApp, filters, types, utils

ngrok_url = utils.start_ngrok_tunnel(auth_token="NGROK_AUTH_TOKEN")

wa = WhatsApp(
    token="YOUR_TOKEN",
    phone_id="YOUR_PHONE_ID",
    app_id="YOUR_APP_ID",
    app_secret="YOUR_APP_SECRET",
    callback_url=ngrok_url,
    verify_token="xyzxyz",
)

@wa.on_message(filters.text)
async def echo_handler(message: types.Message):
    await message.reply(f"You said: {message.text}")

# Run in your terminal: pywa dev
"""


def async_code_to_sync(code: str) -> str:
    return (
        code.replace("pywa_async", "pywa")
        .replace("async def", "def")
        .replace("await ", "")
    )


def generate_code(target: str | None, is_async: bool, out_path: pathlib.Path) -> None:
    if target in [None, "project"]:
        code = DEFAULT_PROJECT if is_async else async_code_to_sync(DEFAULT_PROJECT)
        out_file = out_path / "main.py"
        if out_file.exists():
            print(
                f"❌ Error: File '{out_file}' already exists. Aborting to prevent overwrite. Use --out to specify a different output directory or remove the existing file."
            )
            return
        out_file.write_text(code)
        print(f"✅ Created new Pywa project at {out_file.resolve()}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pywa",
        description="Pywa CLI - A command-line toolkit to run, test, and manage Pywa WhatsApp applications.",
        epilog=(
            "Examples:\n"
            "  pywa dev                          # Run the app in development mode with auto-reload\n"
            "  pywa run                          # Run the app in production mode\n"
            "  pywa new --async -o ./my_bot      # Create a new async Pywa project\n"
            '  pywa send text --to 123 "Hello"   # Send a text message to a user'
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version="%(prog)s " + pywa_version,
    )

    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Available commands"
    )

    # ==========================================
    # SERVE PARSER (Shared logic for run/dev)
    # ==========================================
    serve_parser = argparse.ArgumentParser(add_help=False)
    serve_parser.add_argument(
        "path",
        nargs="?",
        type=str,
        help="Path to the python file containing the WhatsApp instance (e.g., 'main.py').",
    )
    serve_parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Bind socket to this host. Default: 127.0.0.1",
    )
    serve_parser.add_argument(
        "--port", type=int, default=8000, help="Bind socket to this port. Default: 8000"
    )
    serve_parser.add_argument(
        "--app",
        type=str,
        help="The explicit variable name of the WhatsApp instance (e.g., 'wa').",
    )
    serve_parser.add_argument(
        "--entrypoint",
        type=str,
        help="Explicit entrypoint string (e.g., 'main:wa'). Overrides `path` and `--app`.",
    )

    serve_parser.add_argument(
        "--log-level",
        type=str,
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="Log level.",
    )
    serve_parser.add_argument("--ssl-keyfile", type=str, help="SSL key file.")
    serve_parser.add_argument(
        "--ssl-certfile",
        type=str,
        help="SSL certificate file.",
    )

    # --- RUN PARSER ---
    run_parser = subparsers.add_parser(
        "run",
        parents=[serve_parser],
        help="Run the client in production mode.",
        description="Run the Pywa WhatsApp client in production mode using a high-performance ASGI server.",
        epilog=(
            "Examples:\n"
            "  pywa run\n"
            "  pywa run my_bot.py\n"
            "  pywa run my_bot:wa\n"
            "  pywa run --port 8080 --host mydomain.com\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    run_parser.add_argument(
        "--workers",
        type=int,
        help="Number of worker processes.",
    )
    run_parser.add_argument(
        "--proxy-headers",
        action=argparse.BooleanOptionalAction,
        help="Enable/Disable X-Forwarded-Proto, X-Forwarded-For to populate url scheme and remote address info.",
    )
    run_parser.add_argument(
        "--forwarded-allow-ips",
        type=str,
        help="Comma separated list of IPs to trust with proxy headers. The literal '*' means trust everything.",
    )
    run_parser.add_argument(
        "--timeout-keep-alive",
        type=int,
        help="Close Keep-Alive connections if no new data is received within this timeout (in seconds).",
    )

    # --- DEV PARSER ---
    dev_parser = subparsers.add_parser(
        "dev",
        parents=[serve_parser],
        help="Run the client in development mode with auto-reload enabled.",
        description="Run the Pywa WhatsApp client in development mode. Automatically reloads the server when code changes are detected.",
        epilog=(
            "Examples:\n"
            "  pywa dev\n"
            "  pywa dev my_bot.py\n"
            "  pywa dev my_bot.py --reload-dir ./src"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    dev_parser.add_argument(
        "--reload",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable auto-reload. Default: True",
    )
    dev_parser.add_argument(
        "--reload-dir",
        action="append",
        dest="reload_dirs",
        type=str,
        help="Set reload directories explicitly, instead of using the current working directory.",
    )
    dev_parser.add_argument(
        "--reload-delay",
        type=float,
        help="Delay between previous and next check if application needs to be reloaded.",
    )

    # ==========================================
    # SEND PARSER
    # ==========================================
    send_common_parser = argparse.ArgumentParser(add_help=False)
    send_common_parser.add_argument(
        "--to",
        nargs="+",
        required=True,
        help="One or multiple recipient phone numbers/IDs (space separated)",
    )
    send_common_parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Delay in seconds between sending messages (default: 0)",
    )
    send_common_parser.add_argument(
        "--reply-to", dest="reply_to_message_id", help="Message ID to reply to"
    )
    send_common_parser.add_argument(
        "--token", default=os.environ.get("PYWA_TOKEN"), help="WhatsApp Cloud API Token"
    )
    send_common_parser.add_argument(
        "--phone-id", default=os.environ.get("PYWA_PHONE_ID"), help="WhatsApp Phone ID"
    )

    send_parser = subparsers.add_parser(
        "send",
        help="Send messages to users",
        description="Send messages directly from the command line. Useful for testing, notifications, or basic scripting.",
        epilog=(
            "Authentication Note:\n"
            "  You must provide credentials using --token and --phone-id,\n"
            "  or by setting the `PYWA_TOKEN` and `PYWA_PHONE_ID` environment variables.\n\n"
            "Examples:\n"
            '  pywa send text --to 1234567890 "Hello there"\n'
            '  pywa send image --to 1234567890 ./cat.jpg --caption "Cute cat"\n'
            "  pywa send video --to 1234567890 https://example.com/video.mp4\n"
            '  pywa send document --to 1234567890 ~/Documents/passport.pdf --filename "My Passport"\n'
            '  pywa send location --to 1234567890 37.7749 -122.4194 --name "San Francisco"'
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    send_subparsers = send_parser.add_subparsers(
        dest="send_type", required=True, help="Type of message to send"
    )

    # Text
    send_text = send_subparsers.add_parser(
        "text", parents=[send_common_parser], help="Send a text message"
    )
    send_text.add_argument("text", help="The text message body")
    send_text.add_argument(
        "--preview-url",
        action="store_true",
        help="Enable URL preview if text contains links",
    )

    # Location
    send_loc = send_subparsers.add_parser(
        "location", parents=[send_common_parser], help="Send a location"
    )
    send_loc.add_argument("latitude", type=float, help="Latitude coordinate")
    send_loc.add_argument("longitude", type=float, help="Longitude coordinate")
    send_loc.add_argument("--name", help="Name of the location")
    send_loc.add_argument("--address", help="Address of the location")

    media_configs = {
        "image": {"caption": True, "aliases": ["img", "pic"]},
        "video": {"caption": True, "aliases": ["vid"]},
        "document": {
            "caption": True,
            "aliases": ["doc"],
            "extra": [("--filename", {"help": "Optional filename to display"})],
        },
        "audio": {
            "caption": False,
            "aliases": ["aud"],
            "extra": [
                ("--is-voice", {"action": "store_true", "help": "Send as a voice note"})
            ],
        },
        "voice": {
            "caption": False,
            "aliases": [],
        },
        "sticker": {"caption": False, "aliases": []},
    }

    media_common_parser = argparse.ArgumentParser(
        add_help=False, parents=[send_common_parser]
    )
    media_common_parser.add_argument("media", help="Path/URL/ID of the media to send")
    media_common_parser.add_argument("--mime-type", help="Optional MIME type")

    for m_type, config in media_configs.items():
        p = send_subparsers.add_parser(
            m_type,
            parents=[media_common_parser],
            help=f"Send a {m_type}",
            aliases=config.get("aliases", list[str]),
        )

        if config.get("caption"):
            p.add_argument("--caption", help=f"{m_type.capitalize()} caption")

        for arg_name, arg_kwargs in config.get("extra", []):
            p.add_argument(arg_name, **arg_kwargs)

    # ==========================================
    # NEW PARSER
    # ==========================================
    new_common_parser = argparse.ArgumentParser(add_help=False)
    new_common_parser.add_argument(
        "--async",
        action="store_true",
        dest="is_async",
        help="Generate an asynchronous code",
    )

    new_common_parser.add_argument(
        "--out",
        "-o",
        type=pathlib.Path,
        default=pathlib.Path.cwd(),
        help="Output directory path (default: current directory '.')",
    )
    new_parser = subparsers.add_parser(
        "new",
        help="Create a new Pywa project",
        parents=[new_common_parser],
        description="Initialize a new Pywa project with ready-to-use boilerplate code.",
        epilog=(
            "Examples:\n"
            "  pywa new                            # Create a sync project in the current directory\n"
            "  pywa new --async                    # Create an async project in the current directory\n"
            "  pywa new project -o ./my_bot        # Create a sync project in a specific directory\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    new_subparsers = new_parser.add_subparsers(dest="target", required=False)
    new_subparsers.add_parser(
        "project",
        parents=[new_common_parser],
        help="Create a new Pywa project (default)",
    )
    # --- EXECUTION ---
    args = parser.parse_args()

    if args.command in ["run", "dev"]:
        target_path = pathlib.Path(args.path) if getattr(args, "path", None) else None
        app_args = {
            "command": args.command,
            "path": target_path,
            "app": getattr(args, "app", None),
            "entrypoint": getattr(args, "entrypoint", None),
        }

        exclude_keys = app_args.keys()
        uvicorn_kwargs = {k: v for k, v in vars(args).items() if k not in exclude_keys}

        if uvicorn_kwargs.get("reload_dirs"):
            uvicorn_kwargs["reload_dirs"] = [
                str(pathlib.Path(d).resolve()) for d in uvicorn_kwargs["reload_dirs"]
            ]

        serve_application(**app_args, **uvicorn_kwargs)

    elif args.command == "send":
        send_messages(**vars(args))

    elif args.command == "new":
        generate_code(target=args.target, is_async=args.is_async, out_path=args.out)


if __name__ == "__main__":
    main()
