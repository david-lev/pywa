"""One-off converter: docs/source/**/*.rst (Sphinx) -> docs-mkdocs/docs/**/*.md (MkDocs)."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import griffe

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
SRC = ROOT / "docs" / "source"
OUT = HERE.parent / "docs"
sys.path.insert(0, str(HERE))
from refs import ROLE_RE, Resolver

pkg = griffe.load("pywa", search_paths=[ROOT])
resolver = Resolver(pkg)
documented: set[str] = set()
aliases: dict[str, str] = {}  # old Sphinx autodoc id -> id rendered by mkdocstrings
AUTODOC = re.compile(
    r"^(?P<ind>[ \t]*)\.\. (?P<kind>autoclass|automethod|autofunction|autoattribute|automodule)::[ \t]*(?P<name>[^\n]+)\n(?P<opts>(?:(?P=ind)[ \t]+:[\w-]+:.*\n(?:(?P=ind)[ \t]+[^\s:][^\n]*\n)*)*)",
    re.MULTILINE,
)
CODEBLOCK = re.compile(
    r"^(?P<ind>[ \t]*)\.\. (?P<kind>code-block|literalinclude)::[ \t]*(?P<arg>[^\n]*)\n(?P<opts>(?:(?P=ind)[ \t]+:[\w-]+:.*\n)*)(?:[ \t]*\n)*(?P<body>(?:(?P=ind)[ \t]+[^\n]*(?:\n|$)|[ \t]*\n)*)",
    re.MULTILINE,
)


def fence_attrs(opts: dict) -> str:
    a = ""
    if "caption" in opts:
        a += f' title="{opts["caption"].strip()}"'
    if "linenos" in opts:
        a += ' linenums="1"'
    if "emphasize-lines" in opts:
        a += ' hl_lines="%s"' % re.sub(r"\s*,\s*", " ", opts["emphasize-lines"].strip())
    return a


ADM = {
    "note": "note",
    "tip": "tip",
    "warning": "warning",
    "attention": "warning",
    "important": "warning",
    "seealso": "note",
}
FENCE = re.compile(r"^(:{3,})(?:\s*\{([^}]*)\}|\s+(\S+))?\s*$")


def convert_divs(md: str) -> str:
    lines = md.split("\n")

    def parse(i, closer=None):
        out = []
        while i < len(lines):
            line = lines[i]
            m = FENCE.match(line)
            if m and m[2] is None and m[3] is None:  # closing fence
                if closer is not None and len(m[1]) >= closer:
                    return out, i + 1
                i += 1
                continue
            if m and (m[2] or m[3]) and not (m[3] and m[3].startswith("pywa.")):
                classes = (m[2] or m[3]).replace(".", "").split()
                inner, i = parse(i + 1, len(m[1]))
                out.extend(render(classes, inner))
                continue
            out.append(line)
            i += 1
        return out, i

    def render(classes, inner):
        body = "\n".join(inner).strip("\n")
        if "pwa-toggle" in classes:
            return ["", '??? example "Show"', "", textwrap.indent(body, "    "), ""]
        for c in classes:
            if c in ADM:
                return ["", f"!!! {ADM[c]}", "", textwrap.indent(body, "    "), ""]
        return ["", body, ""]

    out, _ = parse(0)
    return "\n".join(out)


def convert(path: Path) -> tuple[str, str]:
    rel = path.relative_to(SRC)
    text = path.read_text()
    module = [None]
    stash: dict[str, str] = {}

    def put(val: str) -> str:
        k = f"PWASTASH{len(stash):04d}X"
        stash[k] = val
        return k

    # docutils accepts title underlines shorter than the title; pandoc doesn't: pad them
    def pad(m):
        title, under = m[1], m[2]
        return (
            f"{title}\n{under[0] * len(title.rstrip())}\n"
            if len(under) < len(title.rstrip())
            else m[0]
        )

    text = re.sub(
        r"^([^\s.:\-=~^\"'#*`|][^\n]*)\n([=\-~^\"'`#*+]{3,})\n",
        pad,
        text,
        flags=re.MULTILINE,
    )

    # includes of markdown files
    text = re.sub(
        r"^\.\. include:: (\S+\.md)\n((?:[ \t]+:[\w-]+:.*\n)*)",
        lambda m: (
            "\n"
            + put('--8<-- "%s"' % ((path.parent / m[1]).resolve().relative_to(ROOT)))
            + "\n"
        ),
        text,
        flags=re.MULTILINE,
    )

    def seg(text, mod):
        # autodoc
        def auto(m):
            ind, kind, name = m["ind"], m["kind"], m["name"].strip()
            name = re.sub(r"\(\)$", "", name)
            opts = dict(
                re.findall(
                    r":([\w-]+):[ \t]*(.*)",
                    re.sub(r"\n[ \t]+(?=[^\s:])", " ", m["opts"]),
                )
            )
            full = name if (name.startswith("pywa") or not mod) else f"{mod}.{name}"
            orig = full
            # canonicalise
            full = (
                resolver.canon.get(full) or next(iter(c))
                if len(c := resolver.by_name.get(full.split(".")[-1], ())) == 1
                and full not in resolver.canon
                else resolver.canon.get(full, full)
            )
            documented.add(full)
            if orig != full:
                aliases[orig] = full
            if kind == "autoclass":
                try:
                    obj = pkg[full.removeprefix("pywa.")]
                    names = [
                        x.strip()
                        for x in opts.get("members", "").split(",")
                        if x.strip()
                    ] or (
                        [k for k in obj.members if not k.startswith("_")]
                        if "members" in opts
                        else []
                    )
                    for nm in names:
                        if orig != full or True:
                            aliases[f"{orig}.{nm}"] = f"{full}.{nm}"
                except Exception:
                    pass
            lines = [f"::: {full}", "    options:"]
            if kind == "automodule":
                lines.append("      members: false")
            elif kind == "autoclass":
                if "members" in opts:
                    mem = [x.strip() for x in opts["members"].split(",") if x.strip()]
                    if mem:
                        documented.update(f"{full}.{x}" for x in mem)
                    else:
                        try:
                            documented.update(
                                m.path
                                for m in pkg[
                                    full.removeprefix("pywa.")
                                ].members.values()
                                if not m.name.startswith("_")
                            )
                        except Exception:
                            pass
                    lines.append(
                        "      members: %s" % (json.dumps(mem) if mem else "true")
                    )
                    if mem:
                        lines.append("      inherited_members: %s" % json.dumps(mem))
                else:
                    lines.append("      members: false")
                if "show-inheritance" in opts:
                    lines.append("      show_bases: true")
            else:
                lines.append("      members: false")
            return "\n" + put("\n".join(lines)) + "\n\n"

        text = AUTODOC.sub(auto, text)

        # code-block / literalinclude
        def code(m):
            ind, kind = m["ind"], m["kind"]
            opts = dict(re.findall(r":([\w-]+):[ \t]*(.*)", m["opts"]))
            attrs = fence_attrs(opts)
            if kind == "literalinclude":
                target = (path.parent / m["arg"].strip()).resolve().relative_to(ROOT)
                lang = opts.get("language", "text")
                body = f'--8<-- "{target}"'
                block = f"```{lang}{attrs}\n{body}\n```"
            else:
                lang = m["arg"].strip() or "text"
                body = textwrap.dedent(m["body"]).rstrip("\n")
                block = f"```{lang}{attrs}\n{body}\n```"
            # re-indent relative to directive indent (pandoc will re-indent via container)
            block = textwrap.indent(block, "")
            return "\n" + ind + put(block.replace("\n", "\n")) + "\n\n"

        text = CODEBLOCK.sub(code, text)

        # toggle -> container
        text = re.sub(
            r"^(\s*)\.\. toggle::[^\n]*\n",
            r"\1.. container:: pwa-toggle\n",
            text,
            flags=re.MULTILINE,
        )

        # roles
        def role(m):
            return put(resolver.render(m[1], m[2], m[3], mod))

        text = ROLE_RE.sub(role, text)
        text = re.sub(
            r":(?:py:)?(?:class|meth|func|attr|mod|data|exc|obj):`[^`]+`",
            lambda m: put("`%s`" % m[0].split("`")[1].lstrip("~")),
            text,
        )
        text = re.sub(
            r"^\.\. role:: .*\n(?:[ \t]+:.*\n)*", "", text, flags=re.MULTILINE
        )
        text = re.sub(r":python:`([^`]+)`", r"``\1``", text)
        return text

    parts = re.split(r"^\.\. (?:py:)?currentmodule:: (\S+)\n", text, flags=re.MULTILINE)
    text = seg(parts[0], None) + "".join(
        seg(parts[i + 1], parts[i].strip()) for i in range(1, len(parts), 2)
    )
    # toctree (collected separately)
    text = re.sub(
        r"^\.\. toctree::\n(?:[ \t]+:.*\n)*(?:[ \t]*\n)*(?:[ \t]+\S[^\n]*\n?|[ \t]*\n)*",
        "\n",
        text,
        flags=re.MULTILINE,
    )
    text = text.replace(":class:", "").replace("seealso::", "note::")

    # fix intra-doc html links `x <foo.html>`_ -> keep (still valid with use_directory_urls: false)
    # and `#idN` jumps -> drop (handled by hand)
    md = subprocess.run(
        [
            "pandoc",
            "-f",
            "rst",
            "-t",
            "gfm-raw_html-alerts+fenced_divs",
            "--wrap=none",
            "--columns=1000",
        ],
        input=text,
        text=True,
        capture_output=True,
        check=True,
    ).stdout

    md = convert_divs(md)

    # restore stash (indent-aware)
    def restore(m):
        ind = m[1]
        val = stash[m[2]]
        return "\n".join((ind + l) if i else l for i, l in enumerate(val.split("\n")))

    for _ in range(3):
        md = re.sub(
            r"^([ \t]*)((?:.*?)PWASTASH\d{4}X)", lambda m: m[0], md, flags=re.MULTILINE
        )

    def restore_all(s):
        def r(m):
            ind = (
                re.sub(r">[ ]?", "", m.group(1))
                if "```" in stash[m.group(2)]
                else m.group(1)
            )
            val = stash[m.group(2)]
            block = val.replace("\n", "\n" + ind) if val.startswith("```") else val
            return (
                ("\n" if val.startswith("```") else "")
                + ind
                + block
                + ("\n" if val.startswith("```") else "")
            )

        s = re.sub(r"(?m)^([ \t>]*)(PWASTASH\d{4}X)[ \t]*$", r, s)
        return re.sub(r"PWASTASH\d{4}X", lambda m: stash[m.group(0)], s)

    md = restore_all(md)
    return str(rel.with_suffix(".md")), md


def title_of(md: str, fallback: str) -> str:
    m = re.search(r"^# (.+)$", md, re.MULTILINE)
    return m[1].strip() if m else fallback


def toctree_entries(path: Path) -> list[str]:
    txt = path.read_text()
    out = []
    for m in re.finditer(
        r"^\.\. toctree::\n((?:[ \t]+:.*\n)*)((?:[ \t]*\n|[ \t]+\S[^\n]*\n?)*)",
        txt,
        re.MULTILINE,
    ):
        for line in m[2].splitlines():
            line = line.strip()
            if line and not line.startswith(":"):
                out.append(line)
    return out


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    results = {}
    for p in sorted(SRC.rglob("*.rst")):
        rel, md = convert(p)
        results[p] = (rel, md)
    # visible toctrees are rendered by Sphinx as a list of child pages: do the same
    for p, (rel, md) in list(results.items()):
        txt = p.read_text()
        if p.name == "index.rst" or ":hidden:" in txt:
            continue
        kids = []
        for e in toctree_entries(p):
            m = re.match(r"(.*?)<(.+)>$", e)
            ref = m[2] if m else e
            tp = (
                (SRC / ref.lstrip("/")) if ref.startswith("/") else (p.parent / ref)
            ).with_suffix(".rst")
            if tp in results:
                kids.append(
                    f"- [{m[1].strip() if m else title_of(results[tp][1], tp.stem)}]({os.path.relpath(OUT / results[tp][0], (OUT / rel).parent)})"
                )
        if kids:
            results[p] = (rel, md.rstrip("\n") + "\n\n" + "\n".join(kids) + "\n")
    for p, (rel, md) in results.items():
        dest = OUT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(md)
    shutil.copytree(ROOT / "docs" / "static", OUT / "_static")
    (HERE / "documented.json").write_text(json.dumps(sorted(documented)))
    (HERE / "autodoc_aliases.json").write_text(
        json.dumps({k: v for k, v in sorted(aliases.items()) if k != v}, indent=0)
    )

    # nav from toctrees
    def nav(p: Path, seen=()) -> list:
        items = []
        for e in toctree_entries(p):
            m = re.match(r"(.*?)<(.+)>$", e)
            title, ref = (m[1].strip(), m[2]) if m else (None, e)
            if ref == "self":
                continue
            tp = (SRC / ref.lstrip("/")) if ref.startswith("/") else (p.parent / ref)
            tp = tp.with_suffix(".rst")
            if tp not in results:
                print("WARN toctree target missing:", tp.relative_to(SRC))
                continue
            rel, md = results[tp]
            t = title or title_of(md, tp.stem)
            sub = nav(tp)
            items.append(
                {t: ([rel] + sub) if sub else rel} if not sub else {t: [rel] + sub}
            )
        return items

    nav_yaml = nav(SRC / "index.rst")
    (HERE / "nav.json").write_text(json.dumps(nav_yaml, ensure_ascii=False, indent=1))
    # index: README + changelog stub
    print(len(results), "files;", len(documented), "documented objects")


main()
