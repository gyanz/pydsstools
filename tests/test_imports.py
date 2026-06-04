import importlib
import pytest

MODULES = [
    "pydsstools",
    "pydsstools.core",
    "pydsstools.heclib",
    "pydsstools.heclib.dss",
    "pydsstools.heclib.utils",
]


@pytest.mark.parametrize("module_path", MODULES)
def test_import_star(module_path):
    try:
        mod = importlib.import_module(module_path)
    except ImportError as exc:
        pytest.skip(f"Skipping {module_path} — extension not built: {exc}")
    missing = [n for n in getattr(mod, "__all__", []) if not hasattr(mod, n)]
    assert not missing, f"{module_path}.__all__ lists names not on the module: {missing}"
