# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'PyDAGMC'
copyright = '2025, The UW CNERG Team. All rights reserved.'
author = 'Patrick Shriwise, Paul Wilson, et al'

# Attempt to get version from package metadata
try:
    from importlib import metadata
    release = metadata.version('pydagmc')
except metadata.PackageNotFoundError:
    release = '0.0.0'

version = '.'.join(release.split('.')[:2])

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
    'myst_parser',
    'sphinx_book_theme',
    'sphinx_copybutton',
    'sphinx_design',
    'sphinx_tabs.tabs',
    'sphinx_togglebutton',
    'nbsphinx',
    'sphinx_autodoc_typehints',
]

templates_path = ['_templates']
exclude_patterns = []


# MyST Parser settings
myst_enable_extensions = [
    "colon_fence",  # Allows ```python ... ``` blocks
    "dollarmath",   # For $...$ and $$...$$ math
    "amsmath",      # For AMS math environments
    "linkify",      # Auto-detect links
    "smartquotes",
    "tasklist",
]
myst_heading_anchors = 3 # Auto-generate header anchors up to h3

# Autodoc settings
autodoc_member_order = 'bysource'
autodoc_typehints = "description" # Add typehints to description
sphinx_autodoc_typehints_fully_qualified = False # Keep typehints short

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    # 'pymoab': ('...pymoab_docs_url...', None), # TODO
}


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_book_theme'
html_static_path = ['_static']
# html_logo = "_static/logo.png"
# html_favicon = "_static/favicon.ico"

html_theme_options = {
    "repository_url": "https://github.com/svalinn/pydagmc",
    "use_repository_button": True,
    "use_issues_button": True,
    "use_edit_page_button": True,
    "path_to_docs": "docs/source",
    "home_page_in_toc": True,
}

# Nbsphinx settings
nbsphinx_execute = 'never' # 'auto' or 'always'
nbsphinx_allow_errors = True

# html_css_files = ["custom.css"]

# Autosummary generation
autosummary_generate = True
