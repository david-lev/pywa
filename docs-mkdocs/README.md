# Markdown docs (Zensical)

`docs/source/**/*.rst` (Sphinx) is converted to Markdown by `tools/convert.py` + `tools/finish.py` (a one-off, until the
Sphinx sources are removed) and built with [Zensical](https://zensical.org) + mkdocstrings. Zensical reads the
`mkdocs.yml` at the repo root (it is **generated** by `tools/finish.py`), so the same config also builds with MkDocs Material.

## Build

```bash
pip install -r docs-mkdocs/requirements.txt .
docs-mkdocs/build_zensical.sh [copy_to_dir]   # build -> site/, restore the legacy URLs, verify them
python3 -m http.server -d site 8000            # look at it
```

`docs-mkdocs/build.sh <out_dir>` regenerates the Markdown from the Sphinx sources and builds with MkDocs Material (the fallback).

## Keeping the old Sphinx URLs working

The pages live at clean URLs (`/content/client/`), but every old `.html` URL and `#anchor` still has to work.

* `hooks.py` is the MkDocs hook that did it; **Zensical ignores hooks**, so `tools/postbuild.py` does the same after the
  build: it writes a redirect stub per old page (`tools/redirects.json`), `javascripts/anchor-aliases.js` (old heading ids
  and `tools/autodoc_aliases.json`, resolved by `anchor-redirect.js`) and renames `PyWa` to `Pywa`.
* `tools/verify.py` checks it: every page and `#anchor` of the Sphinx docs (`tools/legacy_anchors.json`, a snapshot made
  by `tools/crawl_legacy.py`) must still resolve on the built site. `build_zensical.sh` fails if one does not.
* Read the Docs' own redirects (`/en/<version>/*` -> `/en/latest/:splat`) only rewrite the prefix, so they keep working.

## Read the Docs

`readthedocs.yaml.example` is the config for the cutover (replace `docs/.readthedocs.yaml` with it). It uses
`build.commands`, which replaces Read the Docs' own build step: try it on the `dev` version first.

* `tools/pywa_griffe_ext.py` rewrites Sphinx roles / `code-block` / `list-table` in docstrings to Markdown at load time.
