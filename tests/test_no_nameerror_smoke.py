# tests/test_no_nameerror_smoke.py
import ast, pathlib, pytest

@pytest.mark.parametrize("path", [
    p for p in pathlib.Path(".").rglob("*.py")
    if "tests" not in str(p) 
    and p.name not in ("conftest.py",)
    and "site-packages" not in str(p)
])
def test_parse_only(path):
    # Catches obvious typos before runtime
    with open(path, "r", encoding="utf-8") as f:
        ast.parse(f.read(), filename=str(path))
