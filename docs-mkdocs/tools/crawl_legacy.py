"""Snapshot every page and #anchor of the live Sphinx docs (`tools/legacy_anchors.json`), the baseline `verify.py` checks.

usage: crawl_legacy.py [base_url]   (default https://pywa.readthedocs.io/en/latest/)
"""

import http.client
import json
import sys
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

TOOLS = Path(__file__).parent
BASE = (
    sys.argv[1] if len(sys.argv) > 1 else "https://pywa.readthedocs.io/en/latest/"
).rstrip("/") + "/"
# anchors of the theme chrome, not of the content
_CHROME = (
    "bd-",
    "pst-",
    "site-navigation",
    "searchbox",
    "main-content",
    "__",
    "navbar",
    "bd-sidebar",
)


class _Ids(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids: list[str] = []

    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k == "id" and v and not v.startswith(_CHROME):
                self.ids.append(v)


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "pywa-docs-migration/1.0"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except (http.client.IncompleteRead, urllib.error.URLError, TimeoutError):
            time.sleep(1 + attempt)
    raise RuntimeError(f"could not fetch {url}")


def main() -> None:
    redirects = json.loads((TOOLS / "redirects.json").read_text())
    pages = sorted({"index.html", *redirects})
    out: dict[str, list[str]] = {}
    for page in pages:
        if page in ("genindex.html", "search.html", "py-modindex.html"):
            continue  # Sphinx-generated indexes: only the page URL matters
        parser = _Ids()
        parser.feed(_get(BASE + page).decode("utf-8", "replace"))
        out[page] = sorted(set(parser.ids))
        print(f"{page}: {len(out[page])} ids")
    (TOOLS / "legacy_anchors.json").write_text(
        json.dumps(out, indent=1, sort_keys=True)
    )
    print(f"{len(out)} pages, {sum(map(len, out.values()))} anchors")


if __name__ == "__main__":
    main()
