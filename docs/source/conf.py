import sys
import warnings

# -- Project information -----------------------------------------------------
project = "pydsstools"
copyright = "2025, Gyan Basyal"
author = "Gyan Basyal"

# Get version from the installed package (PyPI wheel on RTD)
try:
    from pydsstools import __version__
    release = __version__
    # Extract major.minor for short version (e.g., "3.0" from "3.0.0b3")
    version = ".".join(release.split(".")[:2]).split("+")[0]
except ImportError:
    release = "dev"
    version = "dev"

print(f"SPHINX version: {version}, release: {release}")

# Suppress sphinx_autodoc_typehints deprecation warnings (Sphinx 9/10 compatibility)
warnings.filterwarnings(
    "ignore",
    message=".*sphinx_autodoc_typehints.*",
    category=DeprecationWarning,
)

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
    "sphinxcontrib.autodoc_pydantic",
    "sphinx.ext.todo",
]

todo_include_todos = True

source_suffix = {
    ".md": "markdown",
    ".rst": "restructuredtext",
}

myst_enable_extensions = [
    "colon_fence",
    "deflist",
]

autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "show-inheritance": True,
    "inherited-members": False,  # Disabled to avoid duplication; document inherited attrs in docstrings
    "undoc-members": True,
    # Exclude Pydantic model internals from documentation
    "exclude-members": ", ".join([
        # Pydantic model methods
        "model_config",
        "model_fields",
        "model_computed_fields",
        "model_extra",
        "model_fields_set",
        "model_post_init",
        "model_construct",
        "model_copy",
        "model_dump",
        "model_dump_json",
        "model_json_schema",
        "model_parametrized_name",
        "model_rebuild",
        "model_validate",
        "model_validate_json",
        "model_validate_strings",
        # Pydantic internal attributes (from extra="allow" config)
        "extra_data",
        "__pydantic_extra__",
        "__pydantic_fields_set__",
        "__pydantic_private__",
        # GridInfoBase internal attributes (hide from inherited class docs)
        #"extra",
        #"extra_info",
        #"all_info",
    ]),
}

autodoc_typehints = "none"
typehints_fully_qualified = False
typehints_document_rtype = False
simplify_optional_unions = True

napoleon_numpy_docstring = True
napoleon_google_docstring = False

# Napoleon settings for attribute handling
napoleon_use_ivar = True  # Use :ivar: for instance variables (shows Field descriptions)
napoleon_attr_annotations = True  # Include type annotations in attribute docs

autosummary_generate = True

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# =============================================================================
# autodoc_pydantic configuration (Option A)
# =============================================================================

# Ensure pydantic model members are shown via the pydantic-aware documenter
autodoc_pydantic_model_members = True  # models: show fields + members (plugin-aware)

# ✅ The key setting: use Pydantic Field(description=...) for field docs
autodoc_pydantic_field_doc_policy = "docstring"  # choices: docstring|description|both :contentReference[oaicite:2]{index=2}

# Optional: nice summaries near the top of each model page
autodoc_pydantic_model_show_field_summary = True     # show "Fields:" summary :contentReference[oaicite:3]{index=3}
autodoc_pydantic_model_show_validator_summary = False
autodoc_pydantic_model_show_validator_members = False
autodoc_pydantic_model_erdantic_figure = False
autodoc_pydantic_model_signature_prefix = "class"

# Optional: include/omit schema JSON blocks
autodoc_pydantic_model_show_json = True
autodoc_pydantic_model_show_config_summary = False

# =============================================================================
# Fix for "more than one target found for cross-reference" warnings
# =============================================================================
# When symbols are re-exported from __init__.py, Sphinx finds them in multiple
# locations. This tells Sphinx which module is the canonical source.

# Option A: Suppress the warnings (quick fix)
suppress_warnings = [
    "ref.python",  # Suppress all Python cross-reference warnings
]

# Option B: Use nitpicky mode with exceptions (stricter, comment out Option A)
# nitpicky = True
# nitpick_ignore = [
#     ("py:class", "GridType"),
#     ("py:class", "DataType"),
#     ("py:class", "Datum"),
#     ("py:class", "CompressionMethod"),
#     ("py:class", "GridInfo"),
#     ("py:class", "GridInfo6"),
# ]

# Option C: Define canonical locations for re-exported symbols
# This requires autodoc_type_aliases or intersphinx mappings
# autodoc_type_aliases = {
#     "GridType": "pydsstools.core.enums.GridType",
#     "DataType": "pydsstools.core.enums.DataType",
#     "Datum": "pydsstools.core.enums.Datum",
#     "CompressionMethod": "pydsstools.core.enums.CompressionMethod",
#     "GridInfo": "pydsstools.core.gridinfo.GridInfo",
#     "GridInfo6": "pydsstools.core.gridinfo.v6.GridInfo6",
# }
