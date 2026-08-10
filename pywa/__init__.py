"""
🚀 Build WhatsApp Bots in Python • Fast, Effortless, Powerful

- 📚 `Documentation <https://pywa.readthedocs.io>`_
- 💻 `Source Code <https://github.com/david-lev/pywa>`_
- 📦 `PyPI <https://pypi.org/project/pywa>`_
"""

import importlib.metadata

from pywa.client import WhatsApp
from pywa.utils import Version

__version__ = importlib.metadata.version("pywa")
__author__ = "David Lev"
__license__ = "MIT"
