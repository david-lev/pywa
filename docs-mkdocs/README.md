# Markdown docs (Zensical)

The documentation is Markdown in `docs-mkdocs/docs/`, built with [Zensical](https://zensical.org) + mkdocstrings. Zensical reads the
`mkdocs.yml` at the repo root (nav, theme, mkdocstrings options). It replaced the Sphinx docs (reStructuredText).

## Build

```bash
pip install -r docs-mkdocs/requirements.txt .
docs-mkdocs/build_zensical.sh [copy_to_dir]   # build -> site/, restore the legacy URLs, verify them
python3 -m http.server -d site 8000            # look at it
```

## Keeping the old Sphinx URLs working

The pages live at clean URLs (`/content/client/`), but every old `.html` URL and `#anchor` still has to work.

* **Zensical ignores MkDocs hooks and its `redirects` plugin cannot write `.html` files**, so `tools/postbuild.py` does it
  after the build: it writes a redirect stub per old page (`tools/redirects.json`), `javascripts/anchor-aliases.js` (old heading ids
  and `tools/autodoc_aliases.json`, resolved by `docs/javascripts/anchor-redirect.js`) and renames `PyWa` to `Pywa`.
* `tools/verify.py` checks it: every page and `#anchor` of the Sphinx docs (`tools/legacy_anchors.json`, a snapshot made
  of the old live site) must still resolve on the built site. `build_zensical.sh` fails if one does not.
* Read the Docs' own redirects (`/en/<version>/*` -> `/en/latest/:splat`) only rewrite the prefix, so they keep working.

## Read the Docs

`docs/.readthedocs.yaml` uses `build.commands` (Read the Docs' own build step is replaced by `build_zensical.sh`).

* `tools/pywa_griffe_ext.py` rewrites Sphinx roles / `code-block` / `list-table` in docstrings to Markdown at load time.
