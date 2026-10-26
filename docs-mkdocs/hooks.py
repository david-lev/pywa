"""Write legacy ``.html`` redirect stubs (old Sphinx URLs -> new clean URLs), preserving #anchors."""

import html
import json
import os
import re
import unicodedata
from pathlib import Path

STUB = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>Redirecting…</title>
<link rel="canonical" href="{url}"><meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url={url}">
<script>location.replace({url!r} + location.hash)</script></head>
<body>Redirecting to <a href="{url}">{url}</a>…</body></html>
"""


def _write_redirects(config):
    redirects = json.loads(
        (Path(__file__).parent / "tools" / "redirects.json").read_text()
    )
    site = Path(config.site_dir)
    for old, new_md in redirects.items():
        dest = site / old
        target = (
            new_md[: -len("index.md")]
            if new_md.endswith("index.md")
            else new_md[:-3] + "/"
        )
        url = os.path.relpath(target or ".", os.path.dirname(old) or ".")
        url = "./" if url == "." else url + ("/" if not url.endswith("/") else "")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(STUB.format(url=url))


def _rename(text: str) -> str:
    return text.replace("PyWa", "Pywa")


def on_page_markdown(markdown, **kwargs):
    return _rename(markdown)


def on_page_content(html, **kwargs):
    return _rename(html)


# --- legacy anchors: Sphinx/docutils ids -> MkDocs ids --------------------------------------------------------------
_PAGE_ALIASES: dict[str, dict[str, str]] = {}


def _docutils_id(text: str) -> str:
    """Mimic docutils.nodes.make_id so old `#heading-anchors` keep working."""
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


def _collect(items, page_aliases):
    for item in items:
        old = _docutils_id(item.title)
        if old and old != item.id:
            page_aliases.setdefault(old, item.id)
        _collect(item.children, page_aliases)


def on_page_context(context, page, **kwargs):
    def walk(items):
        for item in items:
            item.title = _rename(item.title)
            walk(item.children)

    walk(page.toc)
    page.title = _rename(page.title) if page.title else page.title
    aliases: dict[str, str] = {}
    _collect(page.toc, aliases)
    if aliases:
        _PAGE_ALIASES["/" + page.url] = aliases
    return context


def on_post_build(config, **kwargs):
    _write_redirects(config)
    tools = Path(__file__).parent / "tools"
    data = {
        "global": json.loads((tools / "autodoc_aliases.json").read_text()),
        "pages": _PAGE_ALIASES,
    }
    out = Path(config.site_dir) / "javascripts"
    out.mkdir(parents=True, exist_ok=True)
    (out / "anchor-aliases.js").write_text(
        "window.PWA_ANCHOR_ALIASES = " + json.dumps(data, separators=(",", ":")) + ";"
    )
