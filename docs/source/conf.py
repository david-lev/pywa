# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import os
import sys
from datetime import date

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, "../..")

import pywa  # noqa: E402

# -- Project information -----------------------------------------------------

project = "pywa"
copyright = f"{date.today().year}, David Lev"
author = "David Lev"

version = pywa.__version__
release = pywa.__version__

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx_copybutton",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinxext.opengraph",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx_togglebutton",
    "sphinx.ext.autosectionlabel",
    "myst_parser",
    "sphinxcontrib.googleanalytics",
]

# The suffix of source filenames.
source_suffix = [".rst", ".md"]

# The master toctree document.
master_doc = "index"

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []
pygments_style = "friendly"
html_theme = "sphinx_book_theme"
suppress_warnings = ["image.not_readable"]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["../static"]
html_favicon = "../static/favicon.ico"

# sphinx.ext.autodoc
autodoc_member_order = "bysource"
# autodoc_typehints = "none"  # show type hints in doc signature
# autodoc_typehints = "description"  # show type hints in doc body instead of signature

# sphinx.ext.napoleon
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_use_ivar = True

# sphinx-copybutton
copybutton_prompt_text = (
    r">>> |\.\.\. |> |\$ |\# | In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
)
copybutton_prompt_is_regexp = True
copybutton_remove_prompts = True

# sphinx_book_theme
html_theme_options = {
    "use_sidenotes": True,
    "repository_url": "https://github.com/david-lev/pywa",
    "repository_branch": "master",
    "path_to_docs": "docs/source",
    "use_edit_page_button": True,
    "use_repository_button": True,
    "use_issues_button": True,
    "use_source_button": True,
    "logo": {
        "text": "pywa",
        "link": "https://pywa.readthedocs.io/",
        "alt_text": "pywa logo",
        "image_light": "pywa-logo.png",
        "image_dark": "pywa-logo.png",
    },
    "icon_links_label": "Quick Links",
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/david-lev/pywa",
            "icon": "fab fa-github",
        },
        {
            "name": "PyPI",
            "url": "https://pypi.org/project/pywa/",
            "icon": "fab fa-python",
        },
        {
            "name": "Updates",
            "url": "https://t.me/py_wa",
            "icon": "fa-solid fa-bullhorn",
        },
        {
            "name": "Chat",
            "url": "https://t.me/pywachat",
            "icon": "fa-solid fa-comment-dots",
        },
        {
            "name": "Issues",
            "url": "https://github.com/david-lev/pywa/issues",
            "icon": "fas fa-bug",
        },
    ],
    "use_download_button": True,
}

# sphinx.ext.intersphinx
intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}

# sphinxext.opengraph
ogp_site_url = "https://pywa.readthedocs.io/"
ogp_site_name = "PyWa Documentation"
ogp_image = "https://pywa.readthedocs.io/en/latest/_static/pywa-ogp.png"
ogp_image_alt = "PyWa Logo"
ogp_description_length = 300
ogp_type = "website"
ogp_custom_meta_tags = [
    '<meta property="og:description" content="🚀 PyWa • Build WhatsApp Bots in Python • Fast, Effortless, Powerful" /> '
]

# html_extra_path = ["google898e98a538257a96.html"]

# sphinx.ext.todo
todo_include_todos = True

# sphinxcontrib.googleanalytics
googleanalytics_id = "G-N8G048V8GB"
