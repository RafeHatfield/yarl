# tests/test_imports_public.py
import importlib

def test_imports_public_surfaces():
    # These should import without side effects / NameErrors
    for mod in [
        "engine_integration",
        "death_functions",
        "components",  # package init
        "config",      # package init
    ]:
        assert importlib.import_module(mod)
