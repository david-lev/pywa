🤝 **Contributing**
--------------------

Thank you for considering contributing to pywa! We appreciate your time and effort in helping improve this project. This guide will walk you through the steps and standards to follow for contributing.

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
   pip install -r requirements-dev.txt -r docs/requirements.txt
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
- Use [Google Style Python Docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html) for docstrings.
- Include type annotations for all function parameters and return types.

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

## Communication

If you have questions, feel free to reach out via our issue tracker or other communication channels listed in the repository.


## License

By contributing to pywa, you agree that your contributions will be licensed under the MIT License. See the [LICENSE](https://github.com/david-lev/pywa/blob/master/LICENSE) file for details.

## Project Structure

```bash
pywa/
├── __init__.py
├── _helpers.py
├── api.py
├── client.py
├── errors.py
├── filters.py
├── handlers.py
├── listeners.py
├── server.py
├── types
│   ├── __init__.py
│   ├── base_update.py
│   ├── callback.py
│   ├── chat_opened.py
│   ├── flows.py
│   ├── media.py
│   ├── message.py
│   ├── message_status.py
│   ├── others.py
│   ├── sent_message.py
│   └── templates.py
└── utils.py
```

**Let me explain how the library is structured:**

### API
The `api.py` file contains all the api calls to the WhatsApp Cloud API. It responsible for sending requests to the WhatsApp Cloud API and returning their raw responses.

### Client
The `WhatsApp` class in the `client.py` file is a wrapper around the api calls. It responsible for sending requests to the WhatsApp Cloud API and returning the parsed responses.
It allows to send messages, upload media, manage profiles, flows, templates, and more.

### Server
The `Server` class in the `server.py` file is responsible for handling, verifying and parsing the incoming updates from the webhook.
It also responsible for registering the webhook routes and the callback url.

### Handlers
The `handlers.py` file contains the handler decorators and their respective handler objects. The handlers are used to handle incoming updates from the webhook.

### Listeners
The `listeners.py` file contains the listener functions and the logic to wait and listen to specific user updates.

### Filters
The `filters.py` file contains the filters to use in the handlers to filter incoming updates.

### Types
The `types` package contains the data classes representing the different types of updates and messages.

### Utils
Contains utility functions used across the library and by the users (not like `_helpers.py` which is used internally).

### Errors
Contains the custom exceptions used in the library.

### Async
The async version of pywa preserves the same structure as the sync version.
Most of the code in the async version is inherited from the sync version, while overriding every api-related method to be async.
So when you make changes to the sync version, make sure to apply the same changes to the async version.

### Docs
The documentation is written in reStructuredText and is located in the `docs/source/content` directory. The documentation is built using Sphinx and hosted on ReadTheDocs.

### Tests
The tests are located in the `tests` directory. The tests are written using `pytest`.
