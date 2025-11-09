# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))

import os
import subprocess
import sys

import django

sys.path.insert(0, os.path.abspath("../rewardsweb"))

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

# Set Django settings
os.environ["DJANGO_SETTINGS_MODULE"] = "rewardsweb.settings.development"


django.setup()


# -- Project information -----------------------------------------------------

project = "ASA Stats Rewards website"
copyright = "2025, ASA Stats"
author = "Eduard Ravnić"

# The full version, including alpha/beta/rc tags
from rewardsweb import __version__

release = __version__

# -- General configuration ---------------------------------------------------

master_doc = "index"

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
]

# Generate TypeDoc once at the start
frontend_path = os.path.abspath("../rewardsweb/frontend")
if os.path.exists(frontend_path):
    print("Generating TypeDoc documentation...")
    try:
        subprocess.run(["npm", "run", "build:docs"], cwd=frontend_path, check=True)
    except subprocess.CalledProcessError:
        print("TypeDoc generation failed - continuing without frontend docs")



# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

html_logo = "_static/logo.png"
html_favicon = "_static/favicon.ico"

latex_documents = [
    (
        "index",
        "asastats-rewards-site.tex",
        "ASA Stats Rewards website documentation",
        author,
        "howto",
    )
]
