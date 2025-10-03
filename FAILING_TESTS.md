# TODO: Fix remaining 2 test failures

## Status: 99.88% Pass Rate (1637/1639 passing)

### Remaining Failures (tcod state isolation):

1. `tests/test_entity_sorting_cache.py::TestEntitySortingIntegration::test_render_functions_integration`
2. `tests/test_map_rendering_regression.py::TestMapRenderingRegression::test_render_all_with_optimization_flag`

### Issue:
- Both tests **pass individually** ✅
- Both tests **fail when run together** ❌
- Cause: tcod console state pollution between tests

### Solution (Next Push):
- Add proper tcod console cleanup in tearDown
- Or: Use pytest fixtures with proper isolation
- Or: Mock tcod console state more carefully

### Priority: Low
- Regression tests only
- Code coverage is fine (same paths tested elsewhere)
- No impact on actual gameplay
