🤝 **Contributing**
--------------------

Thank you for considering contributing to pywa! We appreciate your time and effort in helping improve this project. This
guide will walk you through the steps and standards to follow for contributing.

## Prerequisites

- [Python](https://www.python.org/downloads/) 3.10 or higher
- A [GitHub account](https://github.com)
- Familiarity with [git](https://git-scm.com/) for version control

## Getting Started

1. **Fork** the repository and **clone** your fork locally:

   ```bash
   git clone https://github.com/<your-username>/pywa.git
   cd pywa
   ```


2. Set up a [virtual environment](https://docs.python.org/3/library/venv.html) and install the required dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   # for docs changes: pip install -e ".[dev,docs]"
   ```

3. Activate [pre-commit](https://pre-commit.com/) to ensure code quality:

   ```bash
   pre-commit install
   ```

4. Run the tests to make sure everything is working:

   ```bash
   pytest
   ```

Now you are ready to start contributing!

## Code Standards

- Follow the [PEP 8](https://pep8.org/) style guide.
- Use [Google Style Python Docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html) for
  docstrings.
- Include type annotations for all function parameters and return types.
- The project uses [Ruff](https://astral.sh/ruff) for linting and code formatting. You can run checks manually:
  ```bash
  ruff check .
  ruff format .
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

4. Push your changes to your fork and submit a pull request targeting the `dev` branch:
   ```bash
   git push origin my-new-feature
   ```

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

#### API

The `api.py` file contains all the api calls to the WhatsApp Cloud API. It is responsible for sending requests to the
WhatsApp Cloud API and returning their raw responses.

#### Client

The `WhatsApp` class in the `client.py` file is a wrapper around the api calls. It is responsible for sending requests
to the WhatsApp Cloud API and returning the parsed responses. It allows to send messages, upload media, manage profiles,
flows, templates, and more.

#### Server

The `Server` class in the `server.py` file is responsible for handling, verifying and parsing the incoming updates from
the webhook. It is also responsible for registering the webhook routes and the callback url.

#### Handlers

The `handlers.py` file contains the handler decorators and their respective handler objects. The handlers are used to
handle incoming updates from the webhook.

#### Listeners

The `listeners.py` file contains the listener functions and the logic to wait and listen to specific updates.

#### Filters

The `filters.py` file contains the filters to use in the handlers to filter incoming updates.

#### Types

The `types` package contains the data classes representing the different types of updates, messages, templates, flows,
business profiles, calling settings, etc.

#### Utils

Contains utility functions used across the library and by the users (unlike `_helpers.py` which is used internally).

#### Errors

Contains the custom exceptions used in the library.

#### CLI

The `cli.py` and `__main__.py` files implement the command line interface (run using the `pywa` command) to run the dev
server, send messages etc.

#### Async

The async version of pywa (`pywa_async`) preserves the same structure as the sync version (`pywa`). Most of the code in
the async version is inherited from the sync version, while overriding every api-related method to be async. So when you
make changes to the sync version, make sure to apply the same changes to the async version.

#### Docs

The documentation is written in reStructuredText and is located in the `docs/source/content` directory. The
documentation is built using Sphinx and hosted on ReadTheDocs.

#### Tests

The tests are located in the `tests` directory and are written using `pytest`.

- Run all tests:
  ```bash
  pytest
  ```
- When adding new features or fixing bugs, please write corresponding tests:
    - Add tests for client methods/options in `test_client.py` and `test_async.py`.
    - Add tests for new filters in `test_filters.py`.
    - Add tests for new types/updates in `test_types.py` or `test_updates.py`.
