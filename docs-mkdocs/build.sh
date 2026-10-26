#!/usr/bin/env bash
# usage: docs-mkdocs/build.sh <site_dir>   (regenerates md from docs/source, then builds)
set -e
cd "$(dirname "$0")/.."
export NO_PROXY='*' DISABLE_MKDOCS_2_WARNING=true
uv run --with griffe python docs-mkdocs/tools/convert.py
python3 docs-mkdocs/tools/finish.py
uv run --with mkdocs --with mkdocs-material --with 'mkdocstrings[python]' --with pyyaml --with griffe mkdocs build -f mkdocs.yml -d "$1"
