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
import pathlib
import sys

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

    # Climb up the tree as long as we find __init__.py files
    for parent in module_path.parents:
        if (parent / "__init__.py").is_file():
            module_parts.insert(0, parent.stem)
            extra_sys_path = parent.parent
        else:
            break

    module_str = ".".join(module_parts)
    return module_str, extra_sys_path.resolve()


def discover_app_instance(module_str: str, explicit_app_name: str | None = None) -> str:
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
        return explicit_app_name

    # Heuristic discovery
    for preferred_name in ["wa", "bot", "client", "app", "main"]:
        if preferred_name in object_names_set:
            obj = getattr(mod, preferred_name)
            if isinstance(obj, WhatsApp):
                return preferred_name

    # Fallback to exhaustive search
    for name in object_names_set:
        obj = getattr(mod, name)
        if isinstance(obj, WhatsApp):
            return name

    raise PywaCLIException(
        f"Could not auto-discover a WhatsApp app instance in '{module_str}'. "
        "Use --app to specify the variable name manually."
    )


def serve_application(
    command: str,
    path: pathlib.Path | None = None,
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
    reload: bool = False,
    reload_dirs: list[pathlib.Path] | None = None,
    workers: int | None = None,
    app: str | None = None,
    entrypoint: str | None = None,
) -> None:
    """
    Core function that resolves dependencies and starts the Uvicorn server.
    """
    if not uvicorn:
        print(
            "❌ Error: Could not import Uvicorn. Please install it using 'pip install uvicorn'."
        )
        sys.exit(1)

    if entrypoint and (path or app):
        print(
            "❌ Error: Cannot use --entrypoint together with a path or --app arguments."
        )
        sys.exit(1)

    try:
        if entrypoint:
            # Handle explicit entrypoint (e.g. 'main:app')
            module_str, _, app_name = entrypoint.partition(":")
            if not module_str or not app_name:
                raise PywaCLIException("Entrypoint must be in the format 'module:app'")

            sys_path = pathlib.Path.cwd().resolve()
            sys.path.insert(0, str(sys_path))

        else:
            # Handle auto-discovery or path-based execution
            target_path = path or get_default_path()
            if not target_path.exists():
                raise PywaCLIException(f"Target path does not exist: {target_path}")

            module_str, sys_path = resolve_module_path(target_path)
            sys.path.insert(0, str(sys_path))
            app_name = discover_app_instance(module_str, app)

    except PywaCLIException as e:
        print(f"❌ Configuration Error: {e}")
        sys.exit(1)

    # Final import string resolution
    base_import_string = f"{module_str}:{app_name}"
    # Target the Starlette factory method on the WhatsApp instance
    uvicorn_app_string = (
        f"{base_import_string}.{WhatsApp._setup_and_get_starlette_app.__name__}"
    )

    # Print startup summary
    mode = "development" if command == "dev" else "production"
    print(f"\n🚀 Starting Pywa in {mode} mode")
    print("-" * 40)
    print(f"📦 Module Path:  {sys_path}")
    print(f"🔍 App Instance: {base_import_string}")
    print(f"🌐 Server URL:   http://{host}:{port}")
    if command == "dev":
        print("⚠️  Auto-reload:  Enabled (Use 'pywa run' for production)")
    print("-" * 40 + "\n")

    uvicorn.run(
        app=uvicorn_app_string,
        factory=True,
        host=host,
        port=port,
        reload=reload,
        reload_dirs=[str(d.resolve()) for d in reload_dirs] if reload_dirs else None,
        workers=workers,
        log_config=None,  # Relying on imperative logging configuration as requested
    )


def main() -> None:
    """
    CLI entry point. Parses arguments and routes to the correct command server.
    """
    parser = argparse.ArgumentParser(
        prog="pywa",
        description=(
            "Pywa CLI - The official command-line interface to serve and develop "
            "WhatsApp applications effortlessly."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Available commands"
    )

    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "path",
        nargs="?",
        type=str,
        help="Path to the python file containing the Pywa app (e.g., 'src/main.py').",
    )
    parent_parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Bind socket to this host. Default: 127.0.0.1",
    )
    parent_parser.add_argument(
        "--port", type=int, default=8000, help="Bind socket to this port. Default: 8000"
    )
    parent_parser.add_argument(
        "--app", type=str, help="The explicit variable name of the WhatsApp instance."
    )
    parent_parser.add_argument(
        "--entrypoint",
        type=str,
        help="Explicit entrypoint string (e.g., 'main:app'). Overrides path and --app.",
    )

    run_parser = subparsers.add_parser(
        "run", parents=[parent_parser], help="Run the application in production mode."
    )
    run_parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of worker processes. Defaults to 1.",
    )

    dev_parser = subparsers.add_parser(
        "dev",
        parents=[parent_parser],
        help="Run the application in development mode with auto-reload enabled.",
    )
    dev_parser.add_argument(
        "--reload-dir",
        action="append",
        dest="reload_dirs",
        type=str,
        help="Directories to watch for changes (can be used multiple times).",
    )

    args = parser.parse_args()

    target_path = pathlib.Path(args.path) if args.path else None
    reload_dirs = (
        [pathlib.Path(d) for d in args.reload_dirs]
        if getattr(args, "reload_dirs", None)
        else None
    )

    if args.command == "run":
        serve_application(
            command="run",
            path=target_path,
            host=args.host,
            port=args.port,
            reload=False,
            workers=args.workers,
            app=args.app,
            entrypoint=args.entrypoint,
        )
    elif args.command == "dev":
        serve_application(
            command="dev",
            path=target_path,
            host=args.host,
            port=args.port,
            reload=True,
            reload_dirs=reload_dirs,
            workers=None,  # Uvicorn doesn't support multiple workers with reload enabled
            app=args.app,
            entrypoint=args.entrypoint,
        )


if __name__ == "__main__":
    main()
