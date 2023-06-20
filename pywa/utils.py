import math
from importlib import import_module
from typing import Callable, TYPE_CHECKING
if TYPE_CHECKING:
    from pywa import WhatsApp
    from pywa.types import MessageType, Message


def is_fastapi_app(app):
    """Check if the app is a FastAPI app."""
    try:
        return isinstance(app, import_module("fastapi").FastAPI)
    except ImportError:
        return False


def is_flask_app(app):
    """Check if the app is a Flask app."""
    try:
        return isinstance(app, import_module("flask").Flask)
    except ImportError:
        return False


def get_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the distance between two points on Earth using the Haversine formula.
    """
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    return (2 * math.asin(
        math.sqrt(
            math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    )) * 6371

