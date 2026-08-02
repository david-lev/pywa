# ruff: noqa: T201

"""
Standalone sanity check run against a built wheel/sdist in an isolated environment
(no dev dependencies, no local source tree) to catch packaging mistakes such as
missing modules, missing `py.typed` markers, or broken imports before publishing.

Run via:
    uv run --isolated --no-project --with dist/*.whl tests/smoke_test.py
    uv run --isolated --no-project --with dist/*.tar.gz tests/smoke_test.py
"""

import importlib.resources

import pywa
import pywa_async

assert pywa.__version__ == pywa_async.__version__, (
    f"version mismatch: pywa={pywa.__version__!r} pywa_async={pywa_async.__version__!r}"
)

wa = pywa.WhatsApp(phone_id="1234567890", token="xyzxyz")
assert wa.phone_id == "1234567890"

wa_async = pywa_async.WhatsApp(phone_id="1234567890", token="xyzxyz")
assert wa_async.phone_id == "1234567890"

for package in (pywa, pywa_async):
    marker = importlib.resources.files(package) / "py.typed"
    assert marker.is_file(), f"{package.__name__} is missing its py.typed marker"

print(f"pywa {pywa.__version__} smoke test passed")
