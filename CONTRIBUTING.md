🤝 **Contributing**
--------------------

Thank you for considering contributing to pywa! We appreciate your time and effort in helping improve this project. This
guide will walk you through the steps and standards to follow for contributing.

## Prerequisites

- [Python](https://www.python.org/downloads/) 3.10 or higher
- [uv](https://docs.astral.sh/uv/) for dependency management and virtual environments
- A [GitHub account](https://github.com)
- Familiarity with [git](https://git-scm.com/) for version control

## Getting Started

1. **Fork** the repository and **clone** your fork locally:

   ```bash
   git clone https://github.com/<your-username>/pywa.git
   cd pywa
   ```


2. Sync the virtual environment and install the required dependencies:

   ```bash
   uv sync
   # for docs changes: uv sync --group docs
   ```

3. Activate [pre-commit](https://pre-commit.com/) to ensure code quality:

   ```bash
   uv run pre-commit install
   ```

4. Run the tests to make sure everything is working:

   ```bash
   uv run pytest
   ```

Now you are ready to start contributing!

## Code Standards

- Follow the [PEP 8](https://pep8.org/) style guide.
- Use [Google Style Python Docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html) for
  docstrings.
- Include type annotations for all function parameters and return types.
- The project uses [Ruff](https://astral.sh/ruff) for linting and code formatting. You can run checks manually:
  ```bash
  uv run ruff check .
  uv run ruff format .
  ```
- The project uses [ty](https://github.com/astral-sh/ty) for static type checking. You can run it manually:
  ```bash
  uv run ty check
  ```

## Making Changes

1. Create a new branch for your changes

   ```bash
   git checkout -b my-new-feature
   ```

> Use descriptive names like `feature-add-listeners` or `bugfix-handler-issue.`

2. Test your changes:

   ```bash
   pytest
   ```

   If you're making doc changes, you can build the docs locally:

   ```bash
   make -C docs html
   ```

   And run a local server to view the changes:

   ```bash
   python3 -m http.server 8000 -d docs/build/html
   ```

   Then launch your browser and navigate to `http://localhost:8000`.

3. Commit your changes:

   ```bash
   git add .
   git commit -m "[listeners] add `.ask(...)` shortcut"
   ```

4. Push your changes to your fork and submit a pull request:
   ```bash
   git push origin my-new-feature
   ```

> **Important:** Pull requests must target the `dev` branch, not `master`.

## Communication

If you have questions, need help, or want to discuss changes, feel free to reach out via:

- Our **Telegram Group**: [pywa Chat](https://t.me/pywachat)
- GitHub [Issues](https://github.com/david-lev/pywa/issues) for bug reports and feature requests.
- GitHub [Discussions](https://github.com/david-lev/pywa/discussions) for general questions, ideas, and showcase.

## License

By contributing to pywa, you agree that your contributions will be licensed under the MIT License. See
the [LICENSE](https://github.com/david-lev/pywa/blob/master/LICENSE) file for details.

## Project Structure

This project provides both synchronous (`pywa`) and asynchronous (`pywa_async`) implementations. The asynchronous
implementation structure mirrors the synchronous implementation structure.

### Synchronous Structure (`pywa`)

```bash
pywa/
├── __init__.py
├── __main__.py
├── _helpers.py
├── api.py
├── cli.py
├── client.py
├── errors.py
├── filters.py
├── handlers.py
├── listeners.py
├── server.py
├── types/
│   ├── __init__.py
│   ├── base_update.py
│   ├── account_update.py
│   ├── callback.py
│   ├── calls.py
│   ├── chat.py
│   ├── flows.py
│   ├── groups.py
│   ├── media.py
│   ├── message.py
│   ├── message_status.py
│   ├── others.py
│   ├── sent_update.py
│   ├── system.py
│   ├── templates.py
│   ├── user.py
│   └── user_preferences.py
└── utils.py
```

### Asynchronous Structure (`pywa_async`)

```bash
pywa_async/
├── __init__.py
├── _helpers.py
├── api.py
├── client.py
├── errors.py
├── filters.py
├── handlers.py
├── listeners.py
├── server.py
├── types/
│   ├── __init__.py
│   ├── base_update.py
│   ├── account_update.py
│   ├── callback.py
│   ├── calls.py
│   ├── chat.py
│   ├── flows.py
│   ├── groups.py
│   ├── media.py
│   ├── message.py
│   ├── message_status.py
│   ├── others.py
│   ├── sent_update.py
│   ├── system.py
│   ├── templates.py
│   ├── user.py
│   └── user_preferences.py
└── utils.py
```

### Project Components

Below is where to make changes for common kinds of contributions, and what each layer is and isn't responsible for.
**Every module below has a sync (`pywa/`) and async (`pywa_async/`) counterpart — a change to one almost always
requires the matching change to the other.**

#### API

`api.py` (`GraphAPI` sync / `GraphAPIAsync` async) is the thin, low-level HTTP layer over the WhatsApp Cloud API.

- Methods accept **only builtin types** (`str`, `int`, `bool`, `dict`, `pathlib.Path`, file-likes, etc.) — never
  `pywa.types` dataclasses or enums as arguments.
- Argument names must match the **real Cloud API parameter names** (e.g. `phone_id`, `message_id`), not renamed for
  readability — this file is a direct mirror of the API surface.
- Methods return the **raw, unparsed JSON response** (a `dict`). No parsing into `pywa.types` objects happens here.
- Every method added or changed in `pywa/api.py` must be mirrored **exactly** in `pywa_async/api.py` (same
  signature, `async def`, `await self._request(...)`).

Example (`pywa/api.py`):

```python
def mark_message_as_read(self, phone_id: str, message_id: str) -> dict[str, bool]:
    ...
    return self._request(
        method="POST",
        endpoint=f"/{phone_id}/messages",
        json={
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        },
    )
```

The async mirror in `pywa_async/api.py` is identical except `async def` + `await`.

#### Client

The `WhatsApp` class in `client.py` is the user-facing layer built on top of `api.py`.

- Methods accept nicer-to-use Python values (enums, dataclasses, `int | str` phone numbers, file paths/bytes, etc.)
  instead of raw API params.
- Each method calls the matching `self.api.*` method and parses the raw `dict` it gets back into a `pywa.types`
  object (or a small result type like `SuccessResult`), rather than returning the raw dict.
- Same mirroring rule as `api.py`: every method added or changed in `pywa/client.py` must be mirrored in
  `pywa_async/client.py` as `async def`.

Example (`pywa/client.py`), wrapping the `api.py` example above:

```python
def mark_message_as_read(self, message_id: str, *, sender: str | int | None = None) -> SuccessResult:
    return SuccessResult.from_dict(
        self.api.mark_message_as_read(
            phone_id=helpers.resolve_arg(wa=self, value=sender, method_arg="sender", ...),
            message_id=message_id,
        )
    )
```

#### Server

The `Server` mixin in `server.py` owns the incoming side of the pipeline: verifying the webhook signature, parsing
the raw payload into a `RawUpdate`, and **deciding which `Handler` class should handle it**.

- If you add support for a new webhook field, message type, or interactive/system sub-type, the *routing decision*
  belongs here — in the `_handle_*_field` functions and the `_MESSAGE_TYPES` / `_INTERACTIVE_TYPES` /
  `_SYSTEM_TYPES` / `_CALL_EVENTS` lookup dicts — not in `handlers.py` or `types/`.
- `server.py` is also responsible for registering the webhook routes (Flask/FastAPI/built-in server) and the
  callback URL.

Example — mapping a message type to the handler that should process it:

```python
_MESSAGE_TYPES: dict[MessageType, type[handlers.Handler]] = {
    MessageType.BUTTON: handlers.CallbackButtonHandler,
    MessageType.EDIT: handlers.EditedMessageHandler,
    MessageType.REVOKE: handlers.DeletedMessageHandler,
}
```

#### Handlers

`handlers.py` contains one `Handler` subclass per update type, plus the `@wa.on_*` decorator machinery that
registers callbacks against them. When you add a new update type, add a matching `Handler` subclass here (and its
`wa.on_x` decorator / entry in `add_handlers`), then point `server.py`'s dispatch dict at it.

```python
class MessageHandler(Handler[Message]):
    """Handler for `Message` updates. Registered via `@wa.on_message`."""
```

#### Filters

`filters.py` holds composable `Filter` objects used to narrow which updates a handler receives. Each update type
gets a base filter for "is this update of this type at all" (`filters.message`, `filters.callback_button`, ...),
plus finer-grained filters for its different kinds (`filters.text`, `filters.image`, `filters.mimetypes(...)`, etc.).

```python
message: Filter[types.Message] = new(
    lambda _, m: isinstance(m, types.Message), name="filters.message"
)
text: Filter[types.Message] = new(
    lambda _, m: m.type == MessageType.TEXT, name="filters.text"
)
```

#### Types

The `types` package contains the dataclasses for every update and API resource (`Message`, `CallbackButton`,
`Template`, `FlowDetails`, business profiles, calling settings, etc.).

- `types/base_update.py` defines the shared base classes: `BaseUpdate` (every incoming update), `BaseUserUpdate`
  (updates that originate from an end user — adds reply/typing-indicator machinery), and `_ClientShortcuts` (mixed
  into `BaseUserUpdate` to expose convenience methods like `.reply_text(...)`, bound to the update's own `WhatsApp`
  client instance).
- Most type files carry no sync/async-specific logic and don't need touching on the async side beyond a plain
  re-export. Files whose types expose client-shortcut methods (e.g. `.reply_text`, `.mark_as_read`) follow this
  pattern in `pywa_async/types/<file>.py`: star-import the sync module to re-export everything unchanged, import the
  specific class under a private alias, then subclass it together with the async base to override only the methods
  that need to become `async`:

```python
from pywa.types.message import *
from pywa.types.message import Message as _Message

class Message(BaseUserUpdateAsync, _Message):
    """Async override: same fields as the sync `Message`; shortcut methods are async."""

    async def reply_text(self, ...): ...
```

  So when adding a new field to a type, edit the `pywa/types/<file>.py` dataclass only (it's shared); when adding a
  new *client-shortcut method*, add the sync version to the sync class and the async version to the
  `pywa_async/types/<file>.py` override class.

#### Listeners

`listeners.py` implements inline "wait for the next matching update" mechanics (`msg.wait_for_reply(...)`,
`msg.wait_for_click(...)`). Unlike `api.py`/`client.py`, the async version (`pywa_async/listeners.py`) is **not** a thin override —
asyncio-based waiting requires different control flow, so it's independently implemented rather than subclassed.
Keep both in sync by behavior, not by inheritance.

#### Utils

Contains utility functions used across the library and by the users (unlike `_helpers.py` which is used internally).

#### Errors

Contains the custom exceptions used in the library.

#### CLI

The `cli.py` and `__main__.py` files implement the command line interface (run using the `pywa` command) to run the dev
server, send messages etc.

#### Docs

The documentation is written in [reStructuredText](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html) and is located in the `docs/source/content` directory. The
documentation is built using [Sphinx](https://www.sphinx-doc.org/en/master/index.html) and hosted on [ReadTheDocs](https://app.readthedocs.org/projects/pywa/).

#### Tests

The tests live in `tests/` and are written using [pytest](https://docs.pytest.org/en/stable/). The split mirrors
the modules above — put new tests next to the existing ones for the module you touched, not in a new file:

```bash
uv run pytest                                    # full suite
uv run pytest tests/test_client.py               # one file
uv run pytest tests/test_client.py -k test_name  # one test
```

- `test_api.py` / `test_api_async.py` — `api.py` request-building/params (sync and async are separate files here,
  since `GraphAPIAsync` methods must each be awaited).
- `test_client.py` / `test_async.py` — `client.py`; add tests for every new/changed client method or option to
  **both** files (`test_async.py` covers `pywa_async`-specific and async-only behavior).
- `test_server.py` — webhook verification, parsing, and handler-routing decisions in `server.py`.
- `test_handlers.py` — handler classes and the `@wa.on_*` decorator machinery.
- `test_listeners.py` — `.wait_for_reply(...)` / `.ask(...)` mechanics (sync and async).
- `test_filters.py` — add a case here for every new filter in `filters.py`.
- `test_types.py` / `test_updates.py` — new/changed dataclasses go in `test_types.py`; parsing of new update shapes
  (raw JSON → typed object) goes in `test_updates.py`.
- `test_templates.py`, `test_flows.py`, `test_callback_data.py`, `test_errors.py`, `test_cli.py`,
  `test_helpers.py` — one file per matching module (`templates.py`/`types/templates.py`, `types/flows.py`,
  `types/callback.py`, `errors.py`, `cli.py`/`__main__.py`, `_helpers.py`).
- `common.py` is a shared fixture, not a test file: it builds one sync `WhatsApp` and one async `WhatsApp` client
  from the same raw JSON fixtures in `tests/data/updates/`, so update-parsing/dispatch logic is exercised
  identically for both packages. Add new update fixtures there rather than hand-constructing typed objects.
