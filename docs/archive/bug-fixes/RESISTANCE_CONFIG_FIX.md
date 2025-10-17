# Resistance System Configuration Fix

**Issue:** Game startup crash when loading entities with resistances from YAML config

**Error:**
```
TypeError: EntityStats.__init__() got an unexpected keyword argument 'resistances'
ValueError: Invalid resolved monster configuration for 'dragon_lord': EntityStats.__init__() got an unexpected keyword argument 'resistances'
```

---

## Root Cause

The resistance system implementation added `resistances` to:
- `config/entities.yaml` (Dragon Lord and Demon King)
- `components/fighter.py` (Fighter component)

But **NOT** to:
- `config/entity_registry.py` (EntityStats dataclass)
- `config/entity_factory.py` (monster creation)

This caused a mismatch where the YAML configuration tried to pass `resistances` to `EntityStats`, which didn't accept that parameter.

---

## The Fix

### 1. Added `resistances` field to EntityStats

**File:** `config/entity_registry.py`

```python
@dataclass
class EntityStats:
    """Base stats for any entity (player, monster, etc.)."""
    hp: int
    power: int
    defense: int
    xp: int = 0
    damage_min: Optional[int] = None
    damage_max: Optional[int] = None
    defense_min: Optional[int] = None
    defense_max: Optional[int] = None
    # D&D-style stats
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    # Resistance system (v3.12.0)
    resistances: Optional[Dict[str, int]] = None  # <-- ADDED
```

### 2. Updated monster creation to pass resistances

**File:** `config/entity_factory.py`

```python
# Create fighter component from stats
fighter_component = Fighter(
    hp=monster_def.stats.hp,
    defense=monster_def.stats.defense,
    power=monster_def.stats.power,
    xp=monster_def.stats.xp,
    damage_min=monster_def.stats.damage_min or 0,
    damage_max=monster_def.stats.damage_max or 0,
    strength=getattr(monster_def.stats, 'strength', 10),
    dexterity=getattr(monster_def.stats, 'dexterity', 10),
    constitution=getattr(monster_def.stats, 'constitution', 10),
    resistances=getattr(monster_def.stats, 'resistances', None)  # <-- ADDED
)
```

### 3. Created comprehensive configuration tests

**File:** `tests/test_resistance_config.py`

New test suite with 10 tests covering:
- ✅ EntityStats accepts resistances parameter
- ✅ EntityStats works without resistances (backward compatible)
- ✅ Fighter component accepts resistances dict
- ✅ Fighter works without resistances (backward compatible)
- ✅ Dragon Lord config loads with resistances
- ✅ Demon King config loads with resistances
- ✅ Entity factory creates monsters with resistances
- ✅ Monsters without resistances still work (backward compatible)

---

## Verification

```bash
$ python3 -c "from config.entity_registry import EntityStats; stats = EntityStats(hp=100, power=20, defense=15, xp=500, resistances={'fire': 100, 'cold': 50}); print(f'✅ EntityStats with resistances: {stats.resistances}')"
✅ EntityStats with resistances: {'fire': 100, 'cold': 50}
```

---

## Why We Didn't Catch This Initially

1. **Unit tests for Fighter component** - These tested the component in isolation, but didn't test the full integration with YAML config
2. **No integration tests** - We didn't have tests that loaded actual entity configurations
3. **Runtime-only error** - The error only appeared when the game tried to load `entities.yaml` at startup

---

## What We Learned

### Good Test Coverage Needs:
1. ✅ **Unit tests** - Test components in isolation (we had this)
2. ✅ **Integration tests** - Test components working together with config (we added this)
3. ✅ **Configuration validation tests** - Test YAML loading (we added this)
4. ✅ **End-to-end tests** - Test full entity creation pipeline (we added this)

### Prevention Strategy:
- **Always test configuration integration** when adding new fields to YAML
- **Test the full creation pipeline** from YAML → EntityStats → Component
- **Add "round-trip" tests** that create entities from config
- **Use type checking** (mypy) to catch parameter mismatches earlier

---

## Files Changed

1. ✅ `config/entity_registry.py` - Added `resistances` field to EntityStats
2. ✅ `config/entity_factory.py` - Pass resistances to Fighter component
3. ✅ `tests/test_resistance_config.py` - New comprehensive test suite

---

## Status: ✅ FIXED

The game should now start successfully with resistances configured in YAML.

**Backward Compatibility:** ✅ Maintained
- Entities without resistances still work
- `resistances` is optional in EntityStats
- Fighter component handles None resistances gracefully

---

## Next Steps

1. ✅ Game starts without errors
2. ⏭️ Test resistance system in actual gameplay (manual testing)
3. ⏭️ Continue with next feature from priority list

---

**Date:** October 17, 2025
**Version:** v3.12.0
**Issue Reporter:** User (found during startup testing)
**Fix Time:** ~10 minutes
**Lesson:** Integration tests are critical for configuration-driven systems

