"""Post-build step for the Zensical site (Zensical does not run MkDocs hooks, and its `redirects` plugin cannot write
literal `.html` files). Replaces what `hooks.py` did at `on_post_build`:

* writes a redirect stub for every legacy Sphinx URL (`content/client/overview.html` -> `content/client/`),
* writes `javascripts/anchor-aliases.js`: old Sphinx/docutils heading ids -> the ids of the new pages,
* renames `PyWa` to `Pywa` in the text of the pages.

usage: postbuild.py <site_dir>
"""

import html
import json
import os
import re
import sys
import unicodedata
from html.parser import HTMLParser
from pathlib import Path

TOOLS = Path(__file__).parent

STUB = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>Redirecting…</title>
<link rel="canonical" href="{url}"><meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url={url}">
<script>location.replace({url!r} + location.hash)</script></head>
<body>Redirecting to <a href="{url}">{url}</a>…</body></html>
"""


def target_dir(new_md: str) -> str:
    """``content/client/index.md`` -> ``content/client/``; ``content/cli.md`` -> ``content/cli/``."""
    return (
        new_md[: -len("index.md")] if new_md.endswith("index.md") else new_md[:-3] + "/"
    )


def write_redirects(site: Path) -> int:
    redirects = json.loads((TOOLS / "redirects.json").read_text())
    written = 0
    for old, new_md in redirects.items():
        dest = site / old
        if dest.exists() and "Redirecting" not in dest.read_text(errors="ignore")[:300]:
            continue  # never shadow a real page
        url = os.path.relpath(target_dir(new_md) or ".", os.path.dirname(old) or ".")
        url = "./" if url == "." else url + ("/" if not url.endswith("/") else "")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(STUB.format(url=url))
        written += 1
    return written


def docutils_id(text: str) -> str:
    """Mimic ``docutils.nodes.make_id`` so the old ``#heading-anchors`` keep working."""
    t = (
        unicodedata.normalize(
            "NFKD", html.unescape(re.sub(r"<[^>]+>", "", text)).lower()
        )
        .encode("ascii", "ignore")
        .decode()
    )
    t = re.sub(r"[^a-z0-9]+", "-", t)
    t = re.sub(r"^[^a-z]+", "", t)
    return t.rstrip("-")


class Headings(HTMLParser):
    """``(id, text)`` of the prose headings of a page (not the API object headings, whose ids are kept as they are)."""

    def __init__(self):
        super().__init__()
        self.found: list[tuple[str, str]] = []
        self._open: list | None = None
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if (
            re.fullmatch(r"h[1-6]", tag)
            and a.get("id")
            and "doc-heading" not in (a.get("class") or "")
        ):
            self._open = [a["id"], ""]
        elif (
            self._open is not None
            and tag == "a"
            and "headerlink" in (a.get("class") or "")
        ):
            self._skip += 1

    def handle_endtag(self, tag):
        if self._open is not None and tag == "a" and self._skip:
            self._skip -= 1
        elif self._open is not None and re.fullmatch(r"h[1-6]", tag):
            self.found.append((self._open[0], self._open[1].strip()))
            self._open = None

    def handle_data(self, data):
        if self._open is not None and not self._skip:
            self._open[1] += data


def page_files(site: Path):
    for path in sorted(site.rglob("index.html")):
        if "Redirecting" in path.read_text(errors="ignore")[:300]:
            continue
        rel = path.relative_to(site).as_posix()
        yield "/" + rel[: -len("index.html")], path


def write_anchor_aliases(site: Path) -> int:
    pages: dict[str, dict[str, str]] = {}
    for key, path in page_files(site):
        parser = Headings()
        parser.feed(path.read_text(errors="ignore"))
        aliases: dict[str, str] = {}
        for new_id, text in parser.found:
            old = docutils_id(text)
            if old and old != new_id:
                aliases.setdefault(old, new_id)
        if aliases:
            pages[key] = aliases
    data = {
        "global": json.loads((TOOLS / "autodoc_aliases.json").read_text()),
        "pages": pages,
    }
    out = site / "javascripts"
    out.mkdir(parents=True, exist_ok=True)
    (out / "anchor-aliases.js").write_text(
        "window.PWA_ANCHOR_ALIASES = " + json.dumps(data, separators=(",", ":")) + ";"
    )
    return sum(map(len, pages.values()))


_TEXT = re.compile(r">([^<]*)<")
_PROTECTED = re.compile(r"(<script.*?</script>|<style.*?</style>)", re.DOTALL)


def rename_brand(site: Path) -> None:
    for path in site.rglob("*.html"):
        text = path.read_text(errors="ignore")
        if "PyWa" not in text:
            continue
        parts = _PROTECTED.split(text)
        for i in range(0, len(parts), 2):  # odd parts are scripts/styles
            parts[i] = _TEXT.sub(
                lambda m: ">" + m.group(1).replace("PyWa", "Pywa") + "<", parts[i]
            )
        path.write_text("".join(parts))


def main(site_dir: str) -> None:
    site = Path(site_dir)
    print(f"redirect stubs: {write_redirects(site)}")
    print(f"anchor aliases: {write_anchor_aliases(site)}")
    rename_brand(site)


if __name__ == "__main__":
    main(sys.argv[1])
