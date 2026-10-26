"""Shared Sphinx-role -> mkdocs-autorefs resolution (used by the converter and the griffe extension)."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROLE_RE = re.compile(r":(?:py:)?(class|meth|func|attr|mod|data|exc|obj):`(~?)([^`]+)`")
DOCUMENTED = Path(__file__).with_name("documented.json")


class Resolver:
    def __init__(self, package) -> None:
        self.canon: dict[str, str] = {}  # any public path -> canonical path
        self.by_name: dict[str, set[str]] = {}
        self._walk(package)
        self.documented: set[str] = (
            set(json.loads(DOCUMENTED.read_text())) if DOCUMENTED.exists() else set()
        )

    def _walk(self, obj) -> None:
        for m in list(obj.members.values()):
            try:
                target = m.final_target if m.is_alias else m
            except Exception:  # unresolvable alias (external)
                continue
            self.canon[m.path] = target.path
            self.by_name.setdefault(m.name, set()).add(target.path)
            if not m.is_alias and (m.is_module or m.is_class):
                self._walk(m)

    def resolve(self, text: str, module: str | None) -> str | None:
        text = text.lstrip(".")
        cands = [text]
        if module:
            parts = module.split(".")
            for i in range(len(parts), 0, -1):
                cands.insert(0, ".".join(parts[:i]) + "." + text)
        for c in cands:  # ids that are actually rendered in the docs win (inherited members live under the subclass id)
            if c in self.documented:
                return c
        for c in cands:
            if c in self.canon:
                return self.canon[c]
        if "." in text:
            hits = [d for d in self.documented if d.endswith("." + text)]
            if len(hits) == 1:
                return hits[0]
            last = text.rsplit(".", 1)[
                -1
            ]  # inherited/mixin members are rendered under the defining class
            hits = [
                d
                for d in self.documented
                if d.rsplit(".", 1)[-1] == last and d.count(".") >= 3
            ]
            if len(hits) == 1:
                return hits[0]
        head = text.split(".")[0]
        hits = self.by_name.get(head, set())
        if "." not in text and len(hits) == 1:
            return next(iter(hits))
        if "." in text:
            for p in self.by_name.get(text.split(".")[-1], ()):
                if p.endswith("." + text):
                    return p
            # Class.member where class is a unique name
            if len(hits) == 1:
                cand = next(iter(hits)) + text[len(head) :]
                if cand in self.canon:
                    return self.canon[cand]
        return None

    def render(self, role: str, tilde: str, text: str, module: str | None) -> str:
        text = text.strip()
        if "<" in text and text.endswith(">"):
            title, _, tgt = text[:-1].rpartition("<")
            title, text = title.strip(), tgt.strip()
        else:
            title = None
        target = self.resolve(text, module)
        shown = title or (
            text.lstrip(".").split(".")[-1]
            if tilde or text.startswith(".")
            else text.lstrip(".")
        )
        if role in ("meth", "func") and not shown.endswith("()"):
            shown += "()"
        if target and self.documented and target not in self.documented:
            parent = target.rsplit(".", 1)[
                0
            ]  # member not rendered on its own -> link to its documented class
            target = parent if parent in self.documented else None
        if target:
            return f"[`{shown}`][{target}]"
        return f"`{shown}`"

    def sub_roles(self, s: str, module: str | None) -> str:
        return ROLE_RE.sub(lambda m: self.render(m[1], m[2], m[3], module), s)
