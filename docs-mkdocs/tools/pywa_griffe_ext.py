"""Griffe extension: translate Sphinx/reST leftovers in docstrings into Markdown on load."""

import re
import sys
import textwrap
from pathlib import Path

import griffe

sys.path.insert(0, str(Path(__file__).parent))
from refs import Resolver

CODE_BLOCK = re.compile(
    r"^(?P<ind>[ \t]*)\.\. code-block::[ \t]*(?P<lang>\w*)[ \t]*\n(?P<opts>(?:(?P=ind)[ \t]+:[\w-]+:.*\n)*)(?P<blank>[ \t]*\n)*(?P<body>(?:(?P=ind)[ \t]+.*(?:\n|$)|[ \t]*\n)*)",
    re.MULTILINE,
)
LINK = re.compile(r"`([^`<]+?)\s*<([^>`]+)>`_{1,2}")


def _code(m: re.Match) -> str:
    ind, lang = m["ind"], m["lang"] or "text"
    opts = dict(re.findall(r":([\w-]+):\s*(.*)", m["opts"]))
    attrs = ""
    if "caption" in opts:
        attrs += f' title="{opts["caption"].strip()}"'
    if "linenos" in opts:
        attrs += ' linenums="1"'
    if "emphasize-lines" in opts:
        nums = re.sub(r"\s*,\s*", " ", opts["emphasize-lines"].strip())
        nums = nums.replace("-", "-")
        attrs += f' hl_lines="{nums}"'
    body = textwrap.dedent(m["body"]).rstrip("\n")
    body = textwrap.indent(body, ind)
    return f"{ind}```{lang}{attrs}\n{body}\n{ind}```\n\n"


SECTION = re.compile(
    r"^(Args|Arguments|Parameters|Returns|Raises|Yields|Example|Examples|Attributes|Note|Notes|Warning|Tip|See Also|Todo):\s*$",
    re.MULTILINE,
)


def _dedent_prose(v: str) -> str:
    """rst block quotes (indented paragraphs) are code blocks in Markdown: dedent them in the prose before the first section."""
    m = SECTION.search(v)
    head, tail = (v[: m.start()], v[m.start() :]) if m else (v, "")
    out = []
    for para in head.split("\n\n"):
        lines = para.split("\n")
        body = [l for l in lines if l.strip()]
        if (
            body
            and all(l.startswith("    ") for l in body)
            and not body[0].lstrip().startswith(">>>")
        ):
            para = textwrap.dedent(para)
        out.append(para)
    return "\n\n".join(out) + tail


KNOWN_SECTIONS = (
    "Args:",
    "Arguments:",
    "Parameters:",
    "Returns:",
    "Raises:",
    "Yields:",
    "Attributes:",
    "Note:",
    "Notes:",
    "Warning:",
    "Tip:",
    "See Also:",
    "Todo:",
)


def _fence_doctests(text: str) -> str:
    """`>>>` runs are blockquotes in Markdown: wrap consecutive doctest paragraphs (same indent) in one ```pycon fence.

    Inside `Examples:` griffe handles doctests itself; inside other sections the indent is kept; in plain prose the
    block is dedented (an indented block would otherwise be an indented code block holding a literal fence).
    """
    paras, mode = [], "prose"  # prose | examples | section
    for para in text.split("\n\n"):  # "intro:\n>>> code" -> two paragraphs
        para = para.lstrip("\n")
        lines = para.split("\n")
        first = lines[0]
        if re.match(r"^[A-Z][\w ]*:\s*$", first):
            mode = (
                "examples"
                if first.strip() in ("Examples:", "Example:")
                else "section"
                if first.strip() in KNOWN_SECTIONS
                else "prose"
            )
        if (
            mode == "examples"
            and len(lines) > 1
            and re.match(r"^[A-Z][\w ]*:\s*$", first)
            and lines[1].startswith(">>>")
        ):
            paras += [
                (first, "examples"),
                ("\n".join(lines[1:]), "prose"),
            ]  # header + unindented doctest
            mode = "prose"
            continue
        if (
            mode == "examples"
            and not (len(lines) > 1 and lines[1].startswith(" "))
            and para.lstrip().startswith(">>>")
        ):
            mode = "prose"  # doctest not indented under its header: griffe can't see it as an Examples section
        if mode == "examples":
            paras.append((para, mode))
            continue
        k = next((i for i, l in enumerate(lines) if l.lstrip().startswith(">>>")), 0)
        if k and not any(l.lstrip().startswith("```") for l in lines):
            paras += [("\n".join(lines[:k]), mode), ("\n".join(lines[k:]), mode)]
        else:
            paras.append((para, mode))

    out, run, run_ind, run_mode, in_fence = [], [], "", "prose", False

    def flush():
        if run:
            if run_mode == "prose":  # dedent the whole run
                block = [textwrap.dedent(r) for r in run]
                out.append("```pycon\n" + "\n\n".join(block) + "\n```")
            else:
                out.append(
                    f"{run_ind}```pycon\n" + "\n\n".join(run) + f"\n{run_ind}```"
                )
            run.clear()

    for para, mode in paras:
        ind = para[: len(para) - len(para.lstrip(" "))]
        is_doc = (
            not in_fence
            and mode != "examples"
            and not para.startswith("Examples:")
            and (
                para.lstrip().startswith(">>>")
                or (run and para.lstrip().startswith("..."))
            )
        )
        if is_doc and (not run or ind == run_ind):
            run_ind, run_mode = ind, mode
            run.append(para)
        else:
            flush()
            out.append(para)
        if para.count("```") % 2:
            in_fence = not in_fence
    flush()
    return "\n\n".join(out)


LITERAL = re.compile(
    r"^(?P<lead>[ \t]*)(?!\.\. )(?P<head>\S[^\n]*?)::[ \t]*\n(?:[ \t]*\n)+(?P<body>(?:(?P=lead)[ \t]+[^\n]*(?:\n|$)|[ \t]*\n)+)",
    re.MULTILINE,
)


def _literal(m: re.Match) -> str:
    body = m["body"].rstrip("\n")
    first = next(l for l in body.split("\n") if l.strip())
    ind = first[: len(first) - len(first.lstrip(" "))]
    code = textwrap.dedent(body)
    lang = "pycon" if ">>>" in code else "text"
    return (
        f"{m['lead']}{m['head']}:\n\n{ind}```{lang}\n"
        + textwrap.indent(code, ind)
        + f"\n{ind}```\n\n"
    )


ROLE_DECL = re.compile(r"^[ \t]*\.\. role:: .*\n(?:[ \t]+:.*\n)*\n?", re.MULTILINE)
NOTE = re.compile(
    r"^(?P<ind>[ \t]*)\.\. (?P<kind>note|warning|tip|important|attention)::[ \t]*(?P<first>[^\n]*)\n(?P<body>(?:(?P=ind)[ \t]+[^\n]*(?:\n|$)|[ \t]*\n)*)",
    re.MULTILINE,
)
LIST_TABLE = re.compile(
    r"^(?P<ind>[ \t]*)\.\. list-table::[ \t]*\n(?P<opts>(?:(?P=ind)[ \t]+:[\w-]+:.*\n)*)(?P<body>(?:(?P=ind)[ \t]+[^\n]*(?:\n|$)|[ \t]*\n)*)",
    re.MULTILINE,
)


def _cell(txt: str) -> str:
    txt = re.sub(r":python:`([^`]+)`", r"`\1`", " ".join(txt.split()))
    return txt.replace("|", "\\|")


def _list_table(m: re.Match) -> str:
    ind = m["ind"]
    header_rows = int(
        dict(re.findall(r":([\w-]+):\s*(.*)", m["opts"])).get("header-rows", 0)
    )
    rows, cur = [], None
    for line in textwrap.dedent(m["body"]).split("\n"):
        if line.startswith("* - "):
            cur = [line[4:]]
            rows.append(cur)
        elif line.startswith("  - "):
            cur.append(line[4:])
        elif cur and line.strip():
            cur[-1] += " " + line.strip()
    if not rows:
        return m[0]
    width = max(len(r) for r in rows)
    rows = [[_cell(c) for c in r] + [""] * (width - len(r)) for r in rows]
    head, body = (rows[0], rows[1:]) if header_rows else ([""] * width, rows)
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * width] + [
        "| " + " | ".join(r) + " |" for r in body
    ]
    return "\n".join(ind + l for l in lines) + "\n\n"


def _note(m: re.Match) -> str:
    ind = m["ind"]
    body = textwrap.dedent(
        (m["first"] + "\n" if m["first"].strip() else "") + textwrap.dedent(m["body"])
    ).strip("\n")
    return f"{ind}!!! {m['kind']}\n\n" + textwrap.indent(body, ind + "    ") + "\n\n"


class PywaDocstrings(griffe.Extension):
    def on_package(self, *, pkg, loader=None, **kw) -> None:
        self.resolver = Resolver(pkg)
        self._visit(pkg)

    def _visit(self, obj) -> None:
        if obj.docstring is not None and not obj.is_alias:
            module = obj.module.path if obj.module else None
            v = obj.docstring.value
            v = ROLE_DECL.sub("", v)
            v = LIST_TABLE.sub(_list_table, v)
            v = NOTE.sub(_note, v)
            v = CODE_BLOCK.sub(_code, v)
            v = LITERAL.sub(_literal, v)
            v = _dedent_prose(v)
            v = re.sub(
                r"^Examples?:[ \t]*\n(?:[ \t]*\n)+",
                "Examples:\n",
                v,
                flags=re.MULTILINE,
            )
            v = re.sub(r"^Example:[ \t]*$", "Examples:", v, flags=re.MULTILINE)
            v = re.sub(r"(?<=\w)::[ \t]*$", ":", v, flags=re.MULTILINE)
            v = _fence_doctests(v)
            v = re.sub(r":python:`([^`]+)`", r"`\\1`", v)
            v = LINK.sub(lambda m: f"[{m[1].strip()}]({m[2]})", v)
            v = self.resolver.sub_roles(v, module)
            obj.docstring.value = v
        for m in list(obj.members.values()):
            if not m.is_alias:
                self._visit(m)
