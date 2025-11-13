# Golden-Path Tests: Quick Start

## TL;DR

6 new integration tests catch critical gameplay breaks. All pass in 0.4 seconds.

### Run Tests

```bash
# All tests
python3 run_golden_path_tests.py

# Specific test
python3 run_golden_path_tests.py explore   # Movement tests
python3 run_golden_path_tests.py combat    # Combat tests
python3 run_golden_path_tests.py wands     # Portal wand tests
python3 run_golden_path_tests.py lore      # Mural/signpost tests

# Via pytest
python3 -m pytest tests/test_golden_path_floor1.py -v
```

## What's New

### Tests Created
- `tests/test_golden_path_floor1.py` - 6 golden-path tests
- `run_golden_path_tests.py` - Convenience runner with filtering
- `tests/GOLDEN_PATH_TESTS.md` - Detailed documentation
- `GOLDEN_PATH_IMPLEMENTATION.md` - Full implementation summary

### Test Coverage
| Test | What It Tests |
|------|---------------|
| **explore** | Game init, movement, FOV, map structures |
| **combat** | Monster death, entity cleanup |
| **wands** | Wand component, portal creation |
| **lore** | Mural/signpost spawning and visibility |
| **moves** | 20+ sustained moves without crash |
| **overlap** | No entity overlap on same tile |

### Performance
- ⚡ 6 tests in 0.40 seconds
- 📦 Sub-second execution (CI/CD friendly)
- 🎯 Fast feedback on gameplay breaks

## Example: Running a Single Test

```bash
$ python3 run_golden_path_tests.py wands

████████████████████████████████████████████████████████████████████████████████
█                      GOLDEN-PATH INTEGRATION TESTS                          █
████████████████████████████████████████████████████████████████████████████████

🎯 Running: TestGoldenPathFloor1::test_use_wand_of_portals_on_floor1

======================== test session starts ========================
...
tests/test_golden_path_floor1.py::TestGoldenPathFloor1::test_use_wand_of_portals_on_floor1 PASSED [100%]

========================= 1 passed in 0.05s ==========================
```

## Interpreting Results

### ✅ All Tests Pass
Basic gameplay flows are working correctly.

### ❌ One Test Fails
Critical system is broken:
- **explore fails** → Game init or movement broken
- **combat fails** → Monster death or entity system broken
- **wands fails** → Wand component or portal creation broken
- **lore fails** → Mural/signpost spawning broken
- **moves fails** → Game loop has issues
- **overlap fails** → Entity spawning has collision bugs

Run failed test with `-v -s` for details:
```bash
python3 -m pytest tests/test_golden_path_floor1.py::TestGoldenPathFloor1::test_basic_explore_floor1 -v -s
```

## Using in CI/CD

### GitHub Actions

```yaml
- name: Run Golden-Path Tests
  run: python3 run_golden_path_tests.py
  timeout-minutes: 1
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit
python3 run_golden_path_tests.py || exit 1
```

## When to Run

✅ **Always run**:
- Before merging to main
- After changes to core systems (combat, movement, init)
- On every CI/CD build

⚡ **Quick feedback loop**:
- While developing (0.4s feedback)
- To catch regressions early
- To verify fixes work

## Documentation

- 📖 [Full Implementation Guide](GOLDEN_PATH_IMPLEMENTATION.md)
- 📚 [Detailed Test Documentation](tests/GOLDEN_PATH_TESTS.md)
- 🔧 [Test Configuration](config/testing_config.py)
- 🎮 [Game Initialization](loader_functions/initialize_new_game.py)

## Troubleshooting

### Tests don't run
```bash
cd /Users/rafehatfield/development/rlike
python3 run_golden_path_tests.py
```

### Single test fails
```bash
# Run with verbose output
python3 -m pytest tests/test_golden_path_floor1.py -v -s

# Run specific test
python3 run_golden_path_tests.py explore
```

### ImportError
```bash
# Ensure correct directory
pwd  # Should show: .../rlike
echo $PYTHONPATH  # Should be empty or include project root
```

### Timeout
```bash
# Run with longer timeout
timeout 60 python3 run_golden_path_tests.py
```

## Key Features

✨ **Real Game State**
- Uses actual game initialization
- Tests real gameplay flows
- Not mocked or simplified

🔍 **Fail Loudly**
- Exceptions stop tests immediately
- Clear assertion messages
- Identifies root cause fast

⚡ **Fast Execution**
- 0.4 seconds total
- CI/CD friendly
- Quick feedback loop

🎯 **Focused Tests**
- Each test covers one system
- Easy to understand failures
- Simple to extend

## Files Overview

```
tests/test_golden_path_floor1.py      # Tests (330 lines)
├── TestGoldenPathFloor1
│   ├── test_basic_explore_floor1
│   ├── test_kill_basic_monster_and_loot
│   ├── test_use_wand_of_portals_on_floor1
│   └── test_discover_mural_and_signpost
└── TestGoldenPathIntegration
    ├── test_multiple_moves_no_crash
    └── test_spawn_multiple_entities_no_overlap

run_golden_path_tests.py              # Convenience runner (145 lines)

tests/GOLDEN_PATH_TESTS.md            # Detailed docs (280+ lines)
GOLDEN_PATH_IMPLEMENTATION.md         # Full summary (350+ lines)
```

## Next Steps

1. **Run tests**: `python3 run_golden_path_tests.py`
2. **Read docs**: [GOLDEN_PATH_IMPLEMENTATION.md](GOLDEN_PATH_IMPLEMENTATION.md)
3. **Integrate to CI/CD**: Add to your pipeline
4. **Monitor**: Track results over time
5. **Extend**: Add tests for other systems

---

**Status**: ✅ All 6 tests passing  
**Runtime**: 0.40s  
**Ready for**: Production use, CI/CD integration

