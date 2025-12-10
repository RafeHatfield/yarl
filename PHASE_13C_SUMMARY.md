# Phase 13C: Speed Gating Investigation & Slow Opponent Scenarios

## Summary

Phase 13C investigates the speed/momentum gating system by testing against slow opponents (zombies with 0.5 speed_bonus). This reveals how the bonus attack system works and uncovers a critical bug.

**Status**: ✅ Complete (with bug discovered)

---

## What Was Delivered

### 1. Speed Gating Investigation

**Code Inspection Results:**

**Monster Bonus Attack Gating** (`components/ai/basic_monster.py`, line 696):
```python
if speed_tracker.speed_bonus_ratio <= target_speed:
    # Monster is not faster than target - no momentum building
    return results
```

**Player Bonus Attack Gating** (`game_actions.py`, line 1037):
```python
def _can_build_momentum(self, attacker, defender) -> bool:
    attacker_speed = self._get_speed_bonus_ratio(attacker)
    defender_speed = self._get_speed_bonus_ratio(defender)
    return attacker_speed > defender_speed
```

**Key Finding**: Both use the same logic - attacker must have **speed > defender speed** to build momentum.

### 2. Monster Speed Bonuses

From `config/entities.yaml`:
- **Zombie**: `speed_bonus: 0.5` (slow - player can counter)
- **Orc_brute**: `speed_bonus: 0.5` (slow, tanky)
- **Orc**: No explicit speed_bonus (defaults to ~0.0 or 1.0)

### 3. Player Speed Configuration

From `loader_functions/initialize_new_game.py` and `services/scenario_level_loader.py`:
- **Player base speed**: `0.25` (25% bonus attack chance)
- **Equipment bonuses** (additive):
  - Quickfang Dagger: `+0.25`
  - Boots of Swiftness: `+0.25`
  - Ring of Hummingbird: `+0.25`
- **Expected total with full speed**: `1.0` (0.25 base + 0.75 equipment)

### 4. New Slow Zombie Scenarios

**Created:**
1. `scenario_dueling_pit_slow_zombie_baseline.yaml`
2. `scenario_dueling_pit_slow_zombie_speed_full.yaml`

Both scenarios:
- Depth 5 (same as baseline dueling_pit)
- 12×12 enclosed arena
- Single zombie opponent (speed_bonus: 0.5)
- Conservative expectations (min 25-30 kills, max 25 deaths)

---

## Verification Results (50 runs each)

### Baseline vs Slow Zombie
**Player**: 0.25 speed | **Zombie**: 0.5 speed
**Expected**: Zombie should get bonus attacks (0.5 > 0.25)

```
Player Attacks: 318
Player Hits: 244 (76.7%)
Monster Attacks: 347
Monster Hits: 95 (27.4%)
Bonus Attacks: 191 ← ZOMBIE bonus attacks!
Player Wins: 50/50
```

**Analysis**: ✅ **Speed gating works correctly for MONSTERS**
- Zombie (0.5) > Player (0.25) → Zombie gets 191 bonus attacks
- Confirms the gating logic: faster entity builds momentum

### Full Speed vs Slow Zombie
**Player**: 1.0 speed (expected) | **Zombie**: 0.5 speed
**Expected**: Player should get bonus attacks (1.0 > 0.5)

```
Player Attacks: 291
Player Hits: 251 (86.3%)
Monster Attacks: 171
Monster Hits: 44 (25.7%)
Bonus Attacks: 0 ← NO bonus attacks!
Player Wins: 50/50
```

**Analysis**: ❌ **BUG DISCOVERED - Player bonus attacks not triggering**
- Player (expected 1.0) should be faster than Zombie (0.5)
- But we see **0 bonus attacks**
- Player still dominates (86.3% hit rate, 50/50 wins)
- Suggests either:
  1. Equipment bonuses not applying correctly in scenarios
  2. Player speed calculation bug
  3. Player bonus attack logic has additional gate not present in monster logic

---

## Key Findings

### 1. Speed Gating Confirmed (for Monsters)
✅ Monster bonus attacks work as designed:
- Faster monster (0.5) vs slower player (0.25) = 191 bonus attacks in 50 duels
- Average ~3.8 bonus attacks per duel
- Significantly more monster attacks (347 vs 318 player attacks)

### 2. Critical Bug Discovered
❌ Player bonus attacks NOT triggering even when faster:
- Player with full speed stack (expected 1.0) vs zombie (0.5)
- Should trigger bonus attacks but shows 0
- Player still wins all duels but without momentum mechanic

### 3. Combat Metrics Working
✅ All metrics tracking correctly:
- `total_player_attacks`
- `total_player_hits`
- `total_monster_attacks`
- `total_monster_hits`
- `total_bonus_attacks_triggered`

### 4. Player Dominance vs Zombies
Regardless of bonus attacks:
- Player wins 50/50 duels in both scenarios
- Hit rates: 76.7% (baseline) to 86.3% (full speed)
- Zombies are weak opponents (low accuracy, no evasion)

---

## Investigation Results

### Speed Gating Condition
**Confirmed working** (at least for monsters):
```python
if attacker_speed > defender_speed:
    # Can build momentum and get bonus attacks
```

### Bonus Attack Tracking
**Confirmed working**:
- Monster bonus attacks increment `total_bonus_attacks_triggered`
- Recorded via `ScenarioMetricsCollector.record_bonus_attack()`

### Equipment Speed Bonus System
**Suspected bug location**:
- Equipment loading code looks correct (`_apply_player_loadout`)
- Speed bonus tracker has `add_equipment_bonus()` method
- But player bonus attacks not triggering in scenarios

**Possible causes**:
1. Equipment not being applied during scenario initialization
2. Speed bonus not accumulating from multiple items
3. Player speed calculation differs from `_get_speed_bonus_ratio()`
4. Scenario harness may not properly initialize equipment bonuses

---

## Next Steps (Phase 13D or Bug Fix)

### Immediate Investigation Required
1. **Add debug logging** to verify player's actual speed_bonus_ratio during scenario runs
2. **Check equipment loading** in scenario_level_loader - are speed items actually equipped?
3. **Verify speed stacking** - does 0.25 + 0.25 + 0.25 = 0.75 equipment bonus?
4. **Test manually** - equip full speed stack in normal game and attack zombie

### Potential Fixes
1. **If equipment not loading**: Fix `_apply_player_loadout` to properly equip items
2. **If speed not stacking**: Fix `Equipment._update_speed_bonus_from_equipment`
3. **If player logic differs**: Align player bonus attack logic with monster logic

### Additional Testing
Once bug is fixed:
1. Re-run `dueling_pit_slow_zombie_speed_full` with 50 runs
2. **Expected**: ~100-200 player bonus attacks (similar to zombie baseline)
3. Verify player momentum builds as designed

---

## Files Created

1. `config/levels/scenario_dueling_pit_slow_zombie_baseline.yaml` - Baseline vs slow zombie
2. `config/levels/scenario_dueling_pit_slow_zombie_speed_full.yaml` - Full speed vs slow zombie
3. `PHASE_13C_SUMMARY.md` - This document
4. `phase13c_analysis.txt` - Detailed comparison

---

## JSON Exports

1. `dueling_pit_slow_zombie_baseline_50runs.json`
2. `dueling_pit_slow_zombie_speed_full_50runs.json`

Both contain complete metrics including:
- Attack counts (player/monster)
- Hit rates
- Bonus attack counts
- Kill/death statistics

---

## Testing

All scenarios passed expectations:
- ✅ dueling_pit_slow_zombie_baseline: 50 kills, 0 deaths
- ✅ dueling_pit_slow_zombie_speed_full: 50 kills, 0 deaths

No regressions in existing scenarios.

---

## Conclusion

Phase 13C successfully:
1. ✅ Verified speed gating logic (attacker_speed > defender_speed)
2. ✅ Confirmed monster bonus attacks work correctly
3. ✅ Created slow opponent scenarios for testing
4. ✅ Measured baseline combat metrics vs slow enemies

**Critical Discovery**: Player bonus attacks are not triggering even when player should be faster. This is a **high-priority bug** that prevents the momentum system from working for players.

**Recommendation**: Fix the player bonus attack bug before proceeding with further speed tuning. The infrastructure is in place and working for monsters - we just need to enable it for players.

---

## Speed Gating Reference

### Working (Monster → Player)
```
Zombie (0.5 speed) vs Player (0.25 speed)
→ 0.5 > 0.25
→ Zombie gets 191 bonus attacks ✓
```

### Broken (Player → Monster)
```
Player (1.0 speed expected) vs Zombie (0.5 speed)
→ 1.0 > 0.5 (should work)
→ Player gets 0 bonus attacks ✗
```

### Next Test (After Bug Fix)
```
Player (1.0 speed) vs Zombie (0.5 speed)
→ 1.0 > 0.5
→ Player should get ~100-200 bonus attacks
```
