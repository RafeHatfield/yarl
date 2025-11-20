# Contributing: AI/Automated Agent Guidelines

This guide is for AI assistants, autonomous agents, and developers making broad changes to Catacombs of Yarl. It clarifies module responsibilities and testing requirements to keep the codebase robust and maintainable.

---

## 🎯 Core Principle

**When you change behavior in a module, you must add or update tests that cover that behavior.**

This prevents regressions and makes the codebase resilient to automated refactoring.

---

## 📦 Module Ownership & Responsibilities

### Rendering & Visibility System

**Owns:** Screen rendering, field of view (FOV), visual display of entities/map

**Key Files:**
- `render_functions.py` - Main rendering orchestration
- `fov_functions.py` - FOV computation and visibility checks
- `rendering/` - Modular rendering subsystems (camera, effects, etc.)
- `rendering/camera.py` - Viewport management

**Contract:**
- FOV is computed via `fov_functions.recompute_fov()`
- Visibility checks use `fov_map.is_in_fov(x, y)`
- Do NOT reimplement FOV logic elsewhere
- Death screen quotes are managed here; see `render_functions.py` line 300

**When Changing:**
- Update `tests/test_golden_path_floor1.py` for FOV functionality
- Update rendering-specific tests in `tests/integration/`
- Ensure `fov_functions.py` tests still pass

**Tests to Update:**
- `tests/test_golden_path_floor1.py::test_basic_explore_floor1` - FOV verification
- `tests/integration/portals/test_portal_visual_effects.py` - Portal rendering

---

### World Generation & Map Objects

**Owns:** Dungeon generation, room layouts, stairs, doors, map structure

**Key Files:**
- `map_objects/game_map.py` - Map data structure and tile properties
- `map_objects/room_generators.py` - Room generation algorithms
- `map_objects/tile.py` - Individual tile properties
- `map_objects/secret_door.py` - Secret door logic

**Contract:**
- All floor data flows through `GameMap` class
- Rooms are generated via room generators in configurable templates
- Stairs are placed via `room_generators.py` placement logic
- Do NOT hardcode world generation in other modules

**When Changing:**
- Ensure each floor has at least one staircase (test will catch this)
- Verify spawning doesn't place entities out of bounds
- Check that walkable percentage stays >5% (configurable in tests)
- Update level template YAML if changing generation rules

**Tests to Update:**
- `tests/test_world_invariants.py` - World structure checks
- `tests/comprehensive/test_stairs_functionality.py` - Stair-specific behavior
- Map generation tests in `tests/integration/`

---

### Portal System

**Owns:** Portal creation, detection, teleportation, AI interaction

**Key Files:**
- `services/portal_manager.py` - Centralized portal operations
- `components/portal.py` - Portal component definition
- `engine/portal_system.py` - Portal engine system
- `engine_integration.py` - Portal integration with main engine
- `components/victory.py` - Victory state tied to portals

**Contract:**
- ALL portal creation goes through `PortalManager.create_portal_entity()`
- Portal pairs are linked via Portal component
- Collision detection via `portal_manager.check_portal_collision()`
- Do NOT create portals directly; use the manager
- Extend portal behavior only through Portal component

**When Changing:**
- Verify portals are placed on valid tiles (test catches invalid coordinates)
- Ensure portal system integrates with victory condition
- Check monster AI still respects portals
- Update portal service method signatures in tests

**Tests to Update:**
- `tests/test_golden_path_floor1.py::test_use_wand_of_portals_on_floor1` - Portal creation
- `tests/integration/portals/test_portal_entity_integration.py` - Portal mechanics
- `tests/integration/portals/test_victory_portal_entry.py` - Victory portal behavior

---

### Death & Combat System

**Owns:** Entity death, monster dying, loot dropping, combat messages

**Key Files:**
- `death_functions.py` - Death handlers for player and monsters
- `components/fighter.py` - Combat stats and health
- `game_actions.py` - Combat action processing
- `combat_debug.log` - Combat event logging

**Contract:**
- Entity death flows through `kill_monster()` or `kill_player()`
- Loot generation is separate; see `components/loot.py`
- Death screen quotes stored on game state
- Do NOT duplicate death logic elsewhere
- Extend via monster components (boss, slime, etc.), not new functions

**When Changing:**
- Ensure `kill_monster()` doesn't crash on edge cases
- Verify entity list remains consistent after death
- Check that loot appears or messages are generated
- Update death screen quote handling if modified

**Tests to Update:**
- `tests/test_golden_path_floor1.py::test_kill_basic_monster_and_loot` - Death flow
- `tests/test_death_nonboss.py` - Monster death handling
- `tests/integration/combat/` - Combat system tests

---

### Component System (ECS)

**Owns:** Entity-component-system architecture, component definitions, access patterns

**Key Files:**
- `entity.py` - Entity class and component access
- `components/component_registry.py` - ComponentType enum and registry
- `components/` - All component definitions
- `components/interfaces.py` - Component interface contracts

**Contract:**
- Components are accessed via `entity.get_component_optional(ComponentType.X)`
- Do NOT access component dicts directly; use getter methods
- New components must be registered in ComponentType enum
- Component keys use Enum (not strings) in production code
- Do NOT duplicate component logic across modules

**When Changing:**
- New component? Add to ComponentType enum first
- Changing component interface? Update all consumers
- Ensure Enum and string key access work (backwards compatibility)
- Verify `get_component_optional()` handles missing components

**Tests to Update:**
- `tests/test_component_contracts.py` - Component key handling
- `tests/test_public_imports_smoke.py` - Component availability
- Component-specific tests in `tests/unit/components/`

---

### Configuration & Constants

**Owns:** Game configuration, player stats, difficulty settings, item/monster templates

**Key Files:**
- `config/game_constants.py` - Game-wide constants
- `config/factories/` - Entity factory definitions
- `config/level_template_registry.py` - Level generation templates
- `config/testing_config.py` - Testing configuration
- `config/*.yaml` - Configuration files for YAML loading

**Contract:**
- All constants load via `config/game_constants.py`
- Entity templates are in `config/` (not hardcoded elsewhere)
- Level templates come from YAML registry
- Testing config is separate; don't modify normal config for tests
- Do NOT hardcode values; use constants

**When Changing:**
- Update all callers if changing constant names
- Verify testing still works with new defaults
- Add to `CRITICAL_MODULES` if module affects startup
- Document breaking changes in comments

**Tests to Update:**
- `tests/test_game_constants_integration.py` - Constants loading
- `tests/test_config_file_loading.py` - Config file parsing
- `tests/test_public_imports_smoke.py::TestConfigurationAvailable`

---

### Lore & Environment

**Owns:** Murals, signposts, lore text, environmental storytelling

**Key Files:**
- `services/mural_manager.py` - Mural text management
- `components/mural.py` - Mural component
- `components/signpost.py` - Signpost component
- `config/lore_catalog.yaml` - Lore definitions

**Contract:**
- All lore text flows through managers/components
- Murals and signposts are immutable once placed
- Uniqueness enforced by `mural_manager` (per-floor)
- Do NOT hardcode lore text in game logic
- Extend via component properties, not new systems

**When Changing:**
- Verify lore entities spawn in reasonable quantities
- Check visibility and player interaction work
- Ensure unique message selection per floor
- Update lore tests if changing behavior

**Tests to Update:**
- `tests/test_golden_path_floor1.py::test_discover_mural_and_signpost` - Discovery
- `tests/test_mural_messages_unique.py` - Uniqueness guarantee
- `tests/test_mural_visibility.py` - Visibility behavior

---

### Input & State Management

**Owns:** Player input handling, game state transitions, input modes

**Key Files:**
- `input_handlers.py` - Input mode handlers
- `state_management/state_config.py` - State machine configuration
- `game_states.py` - GameStates enum
- `input/` - Input system modules

**Contract:**
- Input modes are defined in `input_handlers.py`
- State transitions are explicit in `state_config.py`
- Do NOT create new input modes without updating state config
- Input handlers must not contain game logic (separation of concerns)

**When Changing:**
- Verify no circular imports (known issue: state_config ↔ input_handlers)
- Test with `tests/test_public_imports_smoke.py::TestNoCircularImports`
- Update state configuration if adding new states
- Add tests for new input modes

**Tests to Update:**
- `tests/test_public_imports_smoke.py` - Import verification
- `tests/state_machine/` - State machine tests
- Input handler tests in `tests/input/`

---

## ✅ Testing Requirements for Changes

### When You Change Behavior

1. **Identify the module**: Which responsibility does it own? (See above)
2. **Identify affected systems**: What depends on this module?
3. **Update/add tests**: Cover the new behavior
4. **Run test suite**: 
   ```bash
   pytest tests/test_golden_path_floor1.py          # Golden path
   pytest tests/test_public_imports_smoke.py         # Imports
   pytest tests/test_component_contracts.py          # Components
   pytest tests/test_world_invariants.py             # World generation
   pytest tests/                                      # All tests
   ```
5. **Check coverage**: Aim for >80% coverage on changed modules

### Minimal Test Requirements

**For any behavioral change:**
- ✅ At least one test covering the new behavior
- ✅ All existing tests still pass
- ✅ No NameError or ImportError introduced
- ✅ Component contracts still respected (Enum vs string keys)
- ✅ World invariants still hold (stairs exist, valid coordinates, etc.)

**For critical modules** (portals, death, visibility):
- ✅ Integration test covering the system end-to-end
- ✅ Golden path test (if affects basic gameplay)
- ✅ Regression test (if fixing a bug)

---

## 🚫 Anti-Patterns (Don't Do This)

### ❌ Duplicating Mechanisms

```python
# BAD: Reimplementing FOV check in your module
if x in visible_x_coords:  # Why not use fov_map.is_in_fov()?

# GOOD: Use existing mechanism
if fov_map.is_in_fov(x, y):
```

### ❌ Hardcoding Values

```python
# BAD: Magic numbers scattered around
if entity.hp < 10:  # What does 10 mean?

# GOOD: Use constants
if entity.fighter.hp < constants['critical_hp']:
```

### ❌ Creating Portals Outside PortalManager

```python
# BAD: Creating portal entity directly
portal = Entity(x=10, y=10, char='O', name='Portal')
portal.is_portal = True

# GOOD: Use the manager
portal = PortalManager.create_portal_entity('entity_portal', x=10, y=10)
```

### ❌ Accessing Components Directly

```python
# BAD: Direct dict access
fighter = entity.components['fighter']  # Or: entity.fighter in new code

# GOOD: Use getter
fighter = entity.get_component_optional(ComponentType.FIGHTER)
```

### ❌ Skipping Tests for "Small" Changes

```python
# BAD: "This change is too small to need a test"
# Result: Bug found in production

# GOOD: Always add a test
# Even 1-line changes get a test proving they work
```

---

## 🔍 Code Review Checklist for AI Agents

Before committing changes, verify:

- [ ] **Module Ownership**: Am I changing the right module?
- [ ] **No Duplication**: Am I using existing mechanisms, not reimplementing?
- [ ] **Tests Added**: Do I have at least one test for my changes?
- [ ] **Tests Pass**: Do all tests still pass? (`pytest tests/`)
- [ ] **Imports Clean**: No new NameError or circular import? (`tests/test_public_imports_smoke.py`)
- [ ] **Contracts Respected**: Component access patterns correct? (`tests/test_component_contracts.py`)
- [ ] **Invariants Hold**: World generation still valid? (`tests/test_world_invariants.py`)
- [ ] **Comments Added**: Does module contract note still make sense?
- [ ] **Backwards Compatible**: Do existing callers still work?

---

## 🧪 Running Tests

### Quick Tests (Fast Feedback)

```bash
# Smoke tests (imports + contracts + world generation)
pytest tests/test_public_imports_smoke.py \
        tests/test_component_contracts.py \
        tests/test_world_invariants.py -v

# Or run our convenience runners
python3 run_golden_path_tests.py        # Golden-path gameplay tests
```

### Full Test Suite

```bash
# All tests with coverage
pytest tests/ -v --cov=. --cov-report=term-missing

# Specific test suite
pytest tests/integration/ -v

# Watch for issues during development
pytest tests/ --tb=short -x  # Stop on first failure
```

### Critical Path (Pre-Merge)

```bash
# Run before pushing/merging
pytest tests/test_golden_path_floor1.py \
        tests/test_public_imports_smoke.py \
        tests/test_component_contracts.py \
        tests/test_world_invariants.py -v

# Should see: 92 passed in ~2 seconds
```

---

## 📝 Module Contract Notes

Each critical module has a contract note at its top explaining:
- What it owns
- When behavior changes, which tests to update
- Where to look for expected behavior

Example:

```python
"""Portal System - Centralized portal management.

OWNERSHIP: All portal creation, collision detection, teleportation
CONTRACTS: 
  - Use PortalManager.create_portal_entity() for all portal creation
  - Portal pairs linked via Portal component
  - See tests/test_golden_path_floor1.py::test_use_wand_of_portals_on_floor1
  - See tests/integration/portals/test_portal_entity_integration.py

When changing behavior:
  - Update tests in tests/integration/portals/
  - Verify portal placement is on valid tiles
  - Ensure AI still respects portals
"""
```

Look for these at the top of:
- `services/portal_manager.py`
- `death_functions.py`
- `render_functions.py`
- `fov_functions.py`

---

## 🎓 Learning Path for New Contributors

1. **Start Here**: Read this document
2. **Review Module Ownership**: Understand which module you're changing
3. **Find Relevant Tests**: Look at existing tests for that module
4. **Follow the Pattern**: Copy test structure from similar tests
5. **Run Tests**: Verify your changes work
6. **Get Feedback**: AI agents should get explicit approval for contract changes

---

## ❓ Questions?

- **Where is module X's responsibility?** → Check the "Module Ownership" section above
- **How do I add a test?** → Look at existing tests in `tests/` for patterns
- **What if I need to change a contract?** → Document in module comment + update tests
- **Did I break something?** → Run `pytest tests/test_public_imports_smoke.py -v` to diagnose

---

## Summary

| Principle | Guideline |
|-----------|-----------|
| **Own your module** | Know what responsibility you own |
| **Reuse, don't duplicate** | Use existing mechanisms |
| **Test-first changes** | Add tests before code when possible |
| **Respect contracts** | Follow ECS patterns, access methods, etc. |
| **Keep tests passing** | Green tests = confidence in changes |
| **Document changes** | Update module comments and tests |

**The goal:** Enable fast, safe, automated changes while maintaining code quality and preventing regressions.




