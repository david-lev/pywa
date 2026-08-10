"""`pywa.__version__` is derived from installed package metadata (`importlib.metadata`),
which uv_build populates from pyproject.toml's `version` at build/install time. This test
guards that the derivation actually resolves to the right value, and that `pywa_async`
(which re-exports `pywa.__version__`) stays in sync."""

import pathlib
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import pywa
import pywa_async

PYPROJECT_PATH = pathlib.Path(__file__).parent.parent / "pyproject.toml"


def test_version_matches_pyproject():
    pyproject_version = tomllib.loads(PYPROJECT_PATH.read_text())["project"]["version"]
    assert pywa.__version__ == pyproject_version
    assert pywa_async.__version__ == pyproject_version
