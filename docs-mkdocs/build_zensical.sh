#!/usr/bin/env bash
# usage: docs-mkdocs/build_zensical.sh [copy_to_dir]
# Builds `mkdocs.yml` with Zensical into `site/`, restores the legacy `.html` URLs and anchors, and fails if any old
# URL or #anchor of the Sphinx docs no longer resolves. Zensical ignores `hooks.py`, so `tools/postbuild.py` does its job.
set -e
cd "$(dirname "$0")/.."
export NO_PROXY='*' NO_MKDOCS_2_WARNING=1 DISABLE_MKDOCS_2_WARNING=true
zensical build -f mkdocs.yml --clean
python3 docs-mkdocs/tools/postbuild.py site
python3 docs-mkdocs/tools/verify.py site
if [ -n "${1:-}" ]; then
    rm -rf "$1" && mkdir -p "$1" && cp -R site/. "$1"/
fi
