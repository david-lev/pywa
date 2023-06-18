from importlib import import_module


def is_fastapi_app(app):
    try:
        return isinstance(app, import_module("fastapi").FastAPI)
    except ImportError:
        return False


def is_flask_app(app):
    try:
        return isinstance(app, import_module("flask").Flask)
    except ImportError:
        return False
