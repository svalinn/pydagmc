# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import datetime

project = 'PyDAGMC'
copyright = '2023 - {}, The UW CNERG Team. All rights reserved.'.format(datetime.date.today().year)
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
    'sphinxcontrib.mermaid',
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
myst_fence_as_directive = ["mermaid"]

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
html_css_files = ["custom.css"]
html_title = project
html_logo = "_static/logo.png"
html_favicon = "_static/logo.png"

html_sidebars = {
    "**": [
        "navbar-logo",
        "icon-links",
        "sbt-sidebar-nav",
    ]
}

html_theme_options = {
    "repository_url": "https://github.com/svalinn/pydagmc",
    "path_to_docs": "docs/source",
    "use_edit_page_button": True,
    "use_source_button": True,
    "use_issues_button": True,
    "use_repository_button": True,
    "use_download_button": True,
    "use_fullscreen_button": True,
    "use_sidenotes": True,
    "home_page_in_toc": True,
    "show_toc_level": 2,
    "logo": {
        "text": html_title,
    },
    "icon_links": [
        {
            "name": "Build and Test",
            "url": "https://github.com/svalinn/pydagmc/actions/workflows/ci.yml",
            "icon": "https://github.com/svalinn/pydagmc/actions/workflows/ci.yml/badge.svg",
            "type": "url",
        },
        {
            "name": "Code Coverage",
            "url": "https://codecov.io/github/svalinn/pydagmc",
            "icon": "https://codecov.io/github/svalinn/pydagmc/branch/main/graph/badge.svg?token=TONI94VBED",
            "type": "url",
        },
    ],
}

# Nbsphinx settings
nbsphinx_execute = 'always'
nbsphinx_allow_errors = True

# Autosummary generation
autosummary_generate = True
