"""Check that every legacy Sphinx URL still works on a built site: the page resolves (directly, or through its
redirect stub) and every old ``#anchor`` is either still a real id there or mapped by `anchor-aliases.js`.

The baseline is `legacy_anchors.json` (a snapshot of the live Sphinx docs, `crawl_legacy.py`) and `redirects.json`.

usage: verify.py <site_dir> [--show N]      (exit code 1 if anything is broken)
"""

import json
import posixpath
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

TOOLS = Path(__file__).parent
# ids Sphinx generates for its own machinery, never linked to
_SPHINX_ONLY = re.compile(
    r"^(module-.*|index-\d+|id\d+|searchbox|search-.*|sidebar-.*|jb-.*|ethical-ad-placement|print-main-content|contents)$"
)


class _Ids(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids: set[str] = set()

    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k in ("id", "name") and v:
                self.ids.add(v)


def stub_target(path: Path) -> str | None:
    m = re.search(
        r'http-equiv="refresh" content="0; url=([^"]+)"',
        path.read_text(errors="ignore")[:600],
    )
    return m.group(1) if m else None


def resolve_page(site: Path, old: str) -> str | None:
    """The built page (relative file path) a legacy ``old`` URL ends up on, following a redirect stub."""
    path = site / old
    if not path.is_file():
        return None
    url = stub_target(path)
    if url is None:
        return old
    dest = posixpath.normpath(posixpath.join(posixpath.dirname(old), url.split("#")[0]))
    dest = (dest + "/index.html") if not dest.endswith(".html") else dest
    return dest if (site / dest).is_file() else None


def main(site_dir: str, show: int) -> int:
    site = Path(site_dir)
    legacy: dict[str, list[str]] = json.loads(
        (TOOLS / "legacy_anchors.json").read_text()
    )
    redirects: dict[str, str] = json.loads((TOOLS / "redirects.json").read_text())
    js = (site / "javascripts" / "anchor-aliases.js").read_text()
    aliases = json.loads(js[js.index("=") + 1 :].strip().rstrip(";"))

    bad_pages = [
        p
        for p in sorted({"index.html", *redirects, *legacy})
        if resolve_page(site, p) is None
    ]
    ids_cache: dict[str, set[str]] = {}
    unresolved: dict[str, list[str]] = {}
    total = 0
    for old, anchors in legacy.items():
        new = resolve_page(site, old)
        if new is None:
            continue
        if new not in ids_cache:
            parser = _Ids()
            parser.feed((site / new).read_text(errors="ignore"))
            ids_cache[new] = parser.ids
        ids = ids_cache[new]
        key = "/" + new[: -len("index.html")]
        for anchor in anchors:
            if _SPHINX_ONLY.match(anchor):
                continue
            total += 1
            target = aliases["global"].get(anchor) or aliases["pages"].get(key, {}).get(
                anchor
            )
            if anchor not in ids and (target is None or target not in ids):
                unresolved.setdefault(old, []).append(anchor)

    n_bad = sum(map(len, unresolved.values()))
    print(f"pages: {len(legacy) + 3} legacy URLs checked, {len(bad_pages)} broken")
    for p in bad_pages:
        print(f"  BROKEN PAGE {p}")
    print(f"anchors: {total} checked, {n_bad} unresolved")
    for old, anchors in sorted(unresolved.items(), key=lambda kv: -len(kv[1])):
        print(
            f"  {old}: {len(anchors)} -> {', '.join(anchors[:show])}{' ...' if len(anchors) > show else ''}"
        )
    return 1 if bad_pages or n_bad else 0


if __name__ == "__main__":
    show = int(sys.argv[sys.argv.index("--show") + 1]) if "--show" in sys.argv else 4
    sys.exit(main(sys.argv[1], show))
