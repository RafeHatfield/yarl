# Phase 22.3 Cleanup — Faction & Warning Hygiene

**Status**: ✅ Complete  
**Date**: 2026-01-25

---

## Summary

Two small cleanup tasks to improve skirmisher ecology and reduce log noise:
1. **Orc Faction Assignment**: Skirmisher now belongs to orc faction (ecology fit)
2. **Healing Potion Warning Deduplication**: Warning logged once per session, not per item

---

## Task A: Orc Faction Assignment ✅

### Change

**File**: `config/entities.yaml`

```yaml
# Before:
faction: "independent"

# After:
faction: "orc"  # Orc faction (agile raider, early-mid game ecology)
```

### Rationale

**Ecology Fit**:
- Skirmisher is an agile raider (fits orc warband composition)
- Complements orc roster: Orc (basic), Orc Veteran, Orc Scout, Orc Chieftain, Orc Shaman, **Skirmisher**
- Early-mid game threat level (ETP 28, similar to basic orc at 27)

**No Gameplay Impact**:
- Stats unchanged
- AI unchanged
- Spawn rates unchanged
- Only affects faction relationships (orcs assist skirmishers, vice versa)

### Verification

```bash
$ python3 -c "from config.factories import get_entity_factory; skirm = get_entity_factory().create_monster('skirmisher', 0, 0); print(skirm.faction)"
Faction.ORC_FACTION
```

✅ Skirmisher is now orc faction

---

## Task B: Healing Potion Warning Cleanup ✅

### Problem

Scenario runs emitted repeated warnings:
```
WARNING: No appearance found for healing_potion (potion), defaulting to identified
WARNING: No appearance found for healing_potion (potion), defaulting to identified
WARNING: No appearance found for healing_potion (potion), defaulting to identified
... (7-12 times per scenario run)
```

**Root Cause**: Scenario mode doesn't initialize appearance generator, but identification logic still runs. Each healing potion item triggers the warning.

### Solution

**Approach**: Option 2 (Deduplicate warning)

**File**: `config/factories/_factory_base.py`

**Implementation**:
- Added class-level set `_appearance_warnings_logged` to track warnings
- Check before logging: `if warning_key not in FactoryBase._appearance_warnings_logged:`
- Log once per `item_type:category` key per session

**Code**:
```python
# Class-level deduplication
_appearance_warnings_logged = set()

# In _apply_identification_logic():
warning_key = f"{item_type}:{item_category}"
if warning_key not in FactoryBase._appearance_warnings_logged:
    logger.warning(f"No appearance found for {item_type} ({item_category}), defaulting to identified")
    FactoryBase._appearance_warnings_logged.add(warning_key)
```

### Before/After

**Before** (5-run scenario):
```
WARNING: No appearance found for healing_potion (potion), defaulting to identified
WARNING: No appearance found for healing_potion (potion), defaulting to identified
WARNING: No appearance found for healing_potion (potion), defaulting to identified
... (12 warnings total)
```

**After** (5-run scenario):
```
WARNING: No appearance found for healing_potion (potion), defaulting to identified
... (1 warning total)
```

✅ **Noise reduced by ~90%** (1 warning instead of 10+)

### Verification

```bash
$ python3 ecosystem_sanity.py --scenario skirmisher_identity --runs 5 2>&1 | grep -c "WARNING.*healing_potion"
1

$ python3 ecosystem_sanity.py --scenario skirmisher_vs_ranged_net_identity --runs 5 2>&1 | grep -c "WARNING.*healing_potion"
1
```

**Only 1 warning per scenario run** ✅

---

## Testing

### Fast Test Suite

```bash
$ pytest -m "not slow"
3639 passed, 15 skipped ✅
```

**No regressions** ✅

### Scenario Sanity Check

```bash
$ python3 ecosystem_sanity.py --scenario skirmisher_vs_ranged_net_identity --runs 10
Player: 10/10 wins, 0/10 deaths
All Expectations: PASS ✅
```

**Behavior unchanged** ✅  
**Warning noise eliminated** ✅

---

## Impact

**Task A (Orc Faction)**:
- Semantic/ecology improvement only
- No stat, AI, or spawn changes
- Skirmishers now assist/cooperate with orc warband

**Task B (Warning Deduplication)**:
- Log hygiene only
- No behavior changes
- Reduces noise by ~90% in scenario runs
- Other warnings NOT suppressed (only this specific warning deduplicated)

---

## Files Modified

1. `config/entities.yaml` — Changed skirmisher faction: `independent` → `orc`
2. `config/factories/_factory_base.py` — Deduplicated appearance warnings
3. `PHASE_22_3_CLEANUP.md` — This document

---

**Both tasks complete with minimal, focused changes** ✅
