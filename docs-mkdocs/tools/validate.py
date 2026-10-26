"""Validate a built MkDocs site against the old Sphinx site: python validate.py <sphinx_out> <mkdocs_out>"""

import html
import os
import re
import sys
from urllib.parse import unquote, urlparse

OLD, NEW = map(os.path.abspath, sys.argv[1:3])
problems = []


def pages(root, skip=("_static", "_sources", "assets", "search", ".doctrees")):
    out = {}
    for d, _, fs in os.walk(root):
        if any(x in d.split(os.sep) for x in skip):
            continue
        for f in fs:
            if f.endswith(".html"):
                h = open(os.path.join(d, f), encoding="utf8").read()
                out[os.path.relpath(os.path.join(d, f), root)] = h
    return out


old_all, new_all = pages(OLD), pages(NEW)
redirects = {p for p, h in new_all.items() if "Redirecting" in h[:400]}
new = {p: h for p, h in new_all.items() if p not in redirects and p != "404.html"}
old = {
    p: h
    for p, h in old_all.items()
    if p not in ("genindex.html", "py-modindex.html", "search.html")
}

# 1. every old URL resolves (page or redirect stub)
for p in old_all:
    if p not in new_all:
        problems.append(("old URL has no page/redirect", p))

# 2. redirect stubs point to existing pages
for p in redirects:
    url = re.search(r'url=([^"]+)"', new_all[p])
    t = os.path.normpath(os.path.join(os.path.dirname(os.path.join(NEW, p)), url[1]))
    if os.path.isdir(t):
        t = os.path.join(t, "index.html")
    if not os.path.exists(t):
        problems.append(("redirect target missing", f"{p} -> {url[1]}"))


# 3. internal links / anchors / images
class _P:
    pass


ids = {p: set(re.findall(r'\b(?:id|name)="([^"]+)"', h)) for p, h in new.items()}
for p, h in new.items():
    base = os.path.dirname(os.path.join(NEW, p))
    for attr, val in re.findall(r'\b(href|src)="([^"]*)"', h):
        u = urlparse(html.unescape(val))
        if (
            u.scheme
            or val.startswith(("//", "mailto:", "javascript:", "data:"))
            or val.startswith("{{")
        ):
            continue
        tgt = os.path.join(base, unquote(u.path)) if u.path else os.path.join(NEW, p)
        tgt = os.path.normpath(tgt)
        if os.path.isdir(tgt):
            tgt = os.path.join(tgt, "index.html")
        if not os.path.exists(tgt):
            problems.append(("missing file", f"{p}: {val}"))
        elif u.fragment and tgt.endswith(".html"):
            rel = os.path.relpath(tgt, NEW)
            if rel in ids and unquote(u.fragment) not in ids[rel]:
                problems.append(("missing anchor", f"{p}: {val}"))


# 4. content parity: autodoc objects + headings
def old_name(p):
    if p.endswith("/index.html"):
        c = p[: -len("index.html")] + "overview.html"
        return c if c in old else p[: -len("/index.html")] + ".html"
    return p


new_ids = set().union(
    *[set(re.findall(r'\bid="(pywa[\w.]+)"', h)) for h in new.values()]
)
tails = {}
for i in new_ids:
    tails.setdefault(i.split(".")[-1], set()).add(i)
n_old = 0
for p, h in old.items():
    for i in re.findall(r'<dt[^>]*\bid="(pywa[\w.]+)"', h):
        n_old += 1
        last, parent = i.split(".")[-1], (i.split(".")[-2] if "." in i else "")
        c = tails.get(last, set())
        if not (
            c
            and (
                last[:1].isupper()
                or any(x.split(".")[-2] == parent for x in c)
                or len(c) >= 1
                and parent.startswith(("WhatsApp", "Base", "Created"))
            )
        ):
            problems.append(("autodoc object missing", f"{p}: {i}"))


def heads(h):
    body = re.search(
        r"<article.*?</article>|<div class=\"bd-article\".*?</article>|<main.*?</main>",
        h,
        re.DOTALL,
    )
    body = body[0] if body else h
    return [
        re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", x)))
        .replace("¶", "")
        .replace("#", "")
        .strip()
        for x in re.findall(r"<h[1-6][^>]*>(.*?)</h[1-6]>", body, re.DOTALL)
    ]


def norm(t):
    return re.sub(r"[^\w]+", " ", t.replace("PyWa", "Pywa")).strip().lower()


for p, h in new.items():
    o = old_name(p)
    if o in old:
        oh = {norm(x) for x in heads(old[o]) if not x.startswith("pywa.")}
        nh = {norm(x) for x in heads(h)}
        miss = [
            x for x in oh if x and x not in nh and not any(x in y or y in x for y in nh)
        ]
        for m in miss:
            problems.append(("heading missing", f"{p}: {m}"))

# 5. rendering artifacts
pats = {
    "unresolved ref": r"\]\[[\w.]+\]",
    "rst role": r":(?:py:)?(?:class|meth|func|attr|mod):`",
    "stash": r"PWASTASH",
    "fence": r"```",
    "directive": r"^\s*\.\. [a-z-]+::",
    "pyWa": r"PyWa",
    "blockquote-doctest": r"<blockquote>\s*<blockquote>",
}
for p, h in new.items():
    b = re.sub(r"<script.*?</script>", "", h, flags=re.DOTALL)
    txt = html.unescape(re.sub(r"<[^>]+>", "", b)) if True else b
    for k, pat in pats.items():
        if re.search(pat, b if k == "blockquote-doctest" else txt, re.MULTILINE):
            problems.append(("artifact:" + k, p))
    if len(txt.strip()) < 200 and p != "404.html":
        problems.append(("page nearly empty", p))
    if not re.search(r"<h1", h):
        problems.append(("no h1", p))

print(
    f"pages: old={len(old_all)} new={len(new_all)} (content={len(new)}, redirect stubs={len(redirects)}); old autodoc objects checked={n_old}"
)
by = {}
for k, v in problems:
    by.setdefault(k, []).append(v)
for k, v in by.items():
    print(f"== {k}: {len(v)}")
    for x in v[: int(os.environ.get("N", 12))]:
        print("   ", x)
print("TOTAL PROBLEMS:", len(problems))
