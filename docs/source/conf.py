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
from pywa.__version__ import __version__


sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, '../..')


# -- Project information -----------------------------------------------------

project = 'pywa'
copyright = f"{date.today().year}, David Lev"
author = 'David Lev'

version = __version__
release = __version__

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx_copybutton",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinxext.opengraph",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx.ext.autosectionlabel"
]

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

pygments_style = "friendly"

html_theme = "sphinx_book_theme"
copybutton_prompt_text = "$ "
suppress_warnings = ["image.not_readable"]
html_favicon = "favicon.ico"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['../static']

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
        }
    ],
    "use_download_button": True,
}

intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}

ogp_site_url = "https://pywa.readthedocs.io/"
ogp_site_name = "pywa documentation"
ogp_image = "https://pywa.readthedocs.io/en/latest/_static/pywa-ogp.png"
ogp_image_alt = "pywa logo"
ogp_description_length = 300
ogp_type = "website"
ogp_custom_meta_tags = [
    '<meta property="og:description" content="pywa • Python wrapper for the WhatsApp Cloud API" /> '
]

html_extra_path = ["google898e98a538257a96.html"]