"""Post-process converted docs: overview.md -> index.md, rewrite .html links, write mkdocs.yml."""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
DOCS = HERE.parent / "docs"
redirects = {
    "genindex.html": "index.md",
    "search.html": "index.md",
    "py-modindex.html": "index.md",
}
rename = {}
for p in sorted(DOCS.rglob("overview.md")):
    new = p.with_name("index.md")
    p.rename(new)
    rename[str(p.relative_to(DOCS))] = str(new.relative_to(DOCS))
for old, new in rename.items():
    redirects[old.replace(".md", ".html")] = new
for p in DOCS.rglob("*.md"):
    r = str(p.relative_to(DOCS))
    if r not in rename.values() and r != "index.md":
        redirects[r.replace(".md", ".html")] = r


def fix_static(p, md):
    depth = len(p.relative_to(DOCS).parts) - 1
    return re.sub(r"(?:\.\./)+_?static/", "../" * depth + "_static/", md)


def unwrap_code_quotes(md: str) -> str:
    """pandoc turned rst block-quoted code into `> ```...` quotes: unwrap them (indent under a preceding list item)."""
    lines, out, i = md.split("\n"), [], 0
    while i < len(lines):
        if lines[i].startswith(">") and not lines[i].startswith("> ["):
            j = i
            while j < len(lines) and (lines[j].startswith(">")):
                j += 1
            block = lines[i:j]
            if any(l.lstrip("> ").startswith("```") for l in block):
                prev = next((l for l in reversed(out) if l.strip()), "")
                pad = "    " if re.match(r"\s*(\d+\.|[-*])\s", prev) else ""
                out += [""] if out and out[-1].strip() else []
                out += [pad + re.sub(r"^> ?", "", l) for l in block]
                i = j
                continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


def fix_rst_quirks(md: str) -> str:
    md = unwrap_code_quotes(md)
    out = []
    for line in md.split("\n"):
        if re.match(
            r"^\*\*[^*]+:\*\* (\\\* .+)$", line
        ):  # "**Label:** \* a \* b" -> bullet list
            head, _, rest = line.partition(":** ")
            items = [i.strip() for i in re.split(r"\s*\\\*\s+", rest) if i.strip()]
            out += [head + ":**", ""] + [f"- {i}" for i in items] + [""]
        elif line.startswith("\\>\\>\\> "):  # doctest block collapsed to one line
            body = line.replace("\\>", ">").replace("\\*", "*")
            parts = re.split(r"\s(?=>>> )", body)
            out += ["", "```pycon"] + parts + ["```", ""]
        else:
            out.append(line)
    return "\n".join(out)


def fix_links(md: str) -> str:
    def f(m):
        path, frag = m[1], m[2] or ""
        if re.match(r"[a-z]+:|//", path):
            return m[0]
        path = re.sub(r"overview\.(html|md)$", "index.md", path)
        path = re.sub(r"\.html$", ".md", path)
        return f"]({path}{frag})"

    return re.sub(r"\]\(([^)#\s]*\.(?:html|md))(#[^)\s]*)?\)", f, md)


import shutil

shutil.copy(HERE / "index.md", DOCS / "index.md")
(DOCS / "stylesheets").mkdir(exist_ok=True)
shutil.copy(HERE / "extra.css", DOCS / "stylesheets" / "extra.css")
(DOCS / "javascripts").mkdir(exist_ok=True)
shutil.copy(HERE / "copy-clean.js", DOCS / "javascripts" / "copy-clean.js")
shutil.copy(HERE / "anchor-redirect.js", DOCS / "javascripts" / "anchor-redirect.js")
for p in DOCS.rglob("*.md"):
    s = p.read_text()
    n = (
        fix_static(p, fix_links(fix_rst_quirks(s)))
        .replace("(#id1)", "(#setup-the-app)")
        .replace("(#id2)", "(#send-a-message)")
    )
    if n != s:
        p.write_text(n)


def nav_fix(items):
    out = []
    for it in items:
        if isinstance(it, str):
            out.append(rename.get(it, it))
            continue
        ((k, v),) = it.items()
        out.append({k: nav_fix(v) if isinstance(v, list) else rename.get(v, v)})
    return out


nav = nav_fix(json.loads((HERE / "nav.json").read_text()))


# title-less first entries: give them readable titles
def retitle(items):
    out = []
    for it in items:
        if isinstance(it, str):
            first = (DOCS / it).read_text().split("\n", 1)[0].lstrip("# ").strip()
            out.append({first or it: it})
        else:
            ((k, v),) = it.items()
            out.append({k: retitle(v) if isinstance(v, list) else v})
    return out


nav = [{"Home": "index.md"}] + retitle(nav)
import yaml

cfg = {
    "site_name": "Pywa",
    "site_description": "Build WhatsApp Bots in Python • Fast, Effortless, Powerful",
    "site_url": "https://pywa.readthedocs.io/en/latest/",
    "repo_url": "https://github.com/david-lev/pywa",
    "repo_name": "david-lev/pywa",
    "edit_uri": "edit/master/docs-mkdocs/docs/",
    "docs_dir": "docs-mkdocs/docs",
    "use_directory_urls": True,
    "copyright": "Copyright © David Lev",
    "theme": {
        "name": "material",
        "logo": "_static/pywa-logo.png",
        "favicon": "_static/favicon.ico",
        "palette": [
            {
                "media": "(prefers-color-scheme: light)",
                "scheme": "default",
                "primary": "green",
                "accent": "teal",
                "toggle": {
                    "icon": "material/brightness-7",
                    "name": "Switch to dark mode",
                },
            },
            {
                "media": "(prefers-color-scheme: dark)",
                "scheme": "slate",
                "primary": "green",
                "accent": "teal",
                "toggle": {
                    "icon": "material/brightness-4",
                    "name": "Switch to light mode",
                },
            },
        ],
        "features": [
            "navigation.instant",
            "navigation.tracking",
            "navigation.sections",
            "navigation.top",
            "navigation.indexes",
            "toc.follow",
            "search.suggest",
            "search.highlight",
            "content.code.copy",
            "content.code.annotate",
            "content.action.edit",
        ],
    },
    "plugins": [
        "search",
        {
            "mkdocstrings": {
                "handlers": {
                    "python": {
                        "paths": ["."],
                        "options": {
                            "docstring_style": "google",
                            "show_source": False,
                            "show_root_heading": True,
                            "show_root_full_path": False,
                            "show_symbol_type_heading": True,
                            "show_symbol_type_toc": True,
                            "members_order": "source",
                            "separate_signature": True,
                            "show_signature_annotations": True,
                            "signature_crossrefs": True,
                            "merge_init_into_class": False,
                            "docstring_section_style": "table",
                            "heading_level": 3,
                            "inherited_members": False,
                            "show_if_no_docstring": False,
                            "extensions": ["docs-mkdocs/tools/pywa_griffe_ext.py"],
                        },
                        "inventories": ["https://docs.python.org/3/objects.inv"],
                    }
                }
            }
        },
    ],
    "markdown_extensions": [
        "admonition",
        "attr_list",
        "md_in_html",
        "tables",
        "toc",
        {"toc": {"permalink": True}},
        "pymdownx.details",
        "pymdownx.superfences",
        "pymdownx.highlight",
        "pymdownx.inlinehilite",
        {"pymdownx.snippets": {"base_path": ["."], "check_paths": True}},
        "pymdownx.tabbed",
        "pymdownx.emoji",
    ],
    "extra": {
        "analytics": {"provider": "google", "property": "G-N8G048V8GB"},
        "social": [
            {
                "icon": "fontawesome/brands/github",
                "link": "https://github.com/david-lev/pywa",
            },
            {
                "icon": "fontawesome/brands/python",
                "link": "https://pypi.org/project/pywa/",
            },
            {"icon": "fontawesome/brands/telegram", "link": "https://t.me/py_wa"},
        ],
    },
    "hooks": ["docs-mkdocs/hooks.py"],
    "extra_css": ["stylesheets/extra.css"],
    "extra_javascript": [
        "javascripts/copy-clean.js",
        "javascripts/anchor-aliases.js",
        "javascripts/anchor-redirect.js",
    ],
    "nav": nav,
}
(HERE.parents[1] / "mkdocs.yml").write_text(
    yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True).replace("PyWa", "Pywa")
)
(HERE / "redirects.json").write_text(json.dumps(redirects, indent=1))
print(len(redirects), "redirects;", len(rename), "overview->index")
