# Contributing to pywa

Thank you for considering contributing to pywa! We appreciate your time and effort in helping improve this project. This guide will walk you through the steps and standards to follow for contributing.

## Prerequisites
- Python 3.10 or higher
- A GitHub account
- Familiarity with `git` for version control

## Getting Started
1. **Fork** the repository and **clone** your fork locally:
   ```bash
   git clone https://github.com/david-lev/pywa.git
   cd pywa


2. Set up a virtual environment and install the required dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt
   ```

3. Activate the pre-commit hooks:
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

1. Create a new branch for your changes:
   ```bash
   git checkout -b my-new-feature
   ```
> Use descriptive names like feature-add-listeners or bugfix-handler-issue.

2. Make your changes, test and commit them:
   ```bash
   pytest
   git add .
   git commit -m "[listeners] add `.ask(...)` shortcut"
   ```

3. Push your changes to your fork and submit a pull request:
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
│   └── template.py
└── utils.py
```

The async version of pywa preserves the same structure as the sync version.
Most of the code in the async version is inherited from the sync version, while overriding every api-related method to be async.
So when you make changes to the sync version, make sure to apply the same changes to the async version.
