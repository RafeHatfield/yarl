# Phase 13D: Bug Fix - Player Bonus Attacks in Scenarios

## Summary

Phase 13D fixes the critical bug discovered in Phase 13C where player bonus attacks were not triggering in scenario runs despite having speed advantage over opponents.

**Status**: ✅ Complete - Bug Fixed!

---

## The Bug

**Symptom**: Player with full speed stack (1.0) vs slow zombie (0.5) showed **0 bonus attacks** over 50 duels.

**Root Cause**: The scenario harness (`services/scenario_harness.py`) was calling `attack_d20()` directly without implementing the bonus attack check logic. The bonus attack system only existed in `game_actions.py` which scenarios bypass.

**Code Location**: `_process_player_action()` in `scenario_harness.py` (line 332-363)

### Why Monster Bonus Attacks Worked

Monster attacks go through `basic_monster.py` AI which has its own `_try_bonus_attack()` method. This worked correctly in scenarios, which is why we saw 191 zombie bonus attacks in the baseline scenario.

### Why Player Bonus Attacks Didn't Work

Player attacks in scenarios:
1. Go through `_process_player_action()` in scenario_harness.py
2. Call `player_fighter.attack_d20(target)` directly
3. **Never check for bonus attacks** ❌

Player attacks in normal gameplay:
1. Go through `_handle_combat()` in game_actions.py
2. Call `_can_build_momentum()` to check speed gating
3. Roll for bonus attack if player is faster ✓
4. Execute bonus attack recursively

---

## The Fix

Added bonus attack logic to `_process_player_action()` in `scenario_harness.py`:

```python
# Phase 13D: Check for player bonus attack (speed momentum system)
# Only roll if target is still alive and player is faster than target
if not target_died and target_fighter and target_fighter.hp > 0:
    speed_tracker = player.get_component_optional(ComponentType.SPEED_BONUS_TRACKER)
    if speed_tracker:
        # Gate: Only roll if player is faster than target
        player_speed = speed_tracker.speed_bonus_ratio
        target_speed_tracker = target.get_component_optional(ComponentType.SPEED_BONUS_TRACKER)
        target_speed = target_speed_tracker.speed_bonus_ratio if target_speed_tracker else 0.0
        
        if player_speed > target_speed:
            # Roll for bonus attack
            if speed_tracker.roll_for_bonus_attack():
                if collector:
                    collector.record_bonus_attack(player, target)
                # Execute bonus attack immediately
                bonus_attack_results = player_fighter.attack_d20(target, is_surprise=False)
                # Process results...
```

**Key Points**:
1. Check if target is still alive (don't bonus attack corpses)
2. Get speed_bonus_ratio from both player and target
3. Only roll if `player_speed > target_speed` (speed gating)
4. Use `SpeedBonusTracker.roll_for_bonus_attack()` (same as monsters)
5. Record metrics via `collector.record_bonus_attack()`
6. Execute bonus attack immediately (no recursion needed)

---

## Verification Results (50 runs each)

### Before Fix

**Baseline (Player 0.25 vs Zombie 0.5)**:
- Bonus Attacks: 191 (zombie attacks - working ✓)

**Full Speed (Player 1.0 vs Zombie 0.5)**:
- Bonus Attacks: 0 (BROKEN - player should get attacks ✗)

### After Fix

**Baseline (Player 0.25 vs Zombie 0.5)**:
```
Bonus Attacks: 194 (zombie attacks - still working ✓)
Player Attacks: 323
Player Hits: 244 (75.5%)
Monster Attacks: 337
Monster Hits: 96 (28.5%)
Player Wins: 50/50
```

**Full Speed (Player 1.0 vs Zombie 0.5)**:
```
Bonus Attacks: 132 (PLAYER attacks - NOW WORKING! ✓)
Player Attacks: 287
Player Hits: 246 (85.7%)
Monster Attacks: 79 (76% reduction!)
Monster Hits: 21 (26.6%)
Player Wins: 50/50
```

---

## Impact Analysis

### Baseline → Full Speed Comparison

| Metric | Baseline | Full Speed | Change |
|--------|----------|------------|--------|
| Bonus Attacks | 0 (player) | 132 (player) | +132 ✓ |
| Player Attacks | 323 | 287 | -36 (-11%) |
| Monster Attacks | 337 | 79 | -258 (-76%) |
| Player Hit Rate | 75.5% | 85.7% | +10.2% |
| Monster Hit Rate | 28.5% | 26.6% | -1.9% |

### Key Insights

1. **Bonus Attack Frequency**: Player gets ~2.6 bonus attacks per duel with full speed stack
2. **Combat Dominance**: Monster attacks reduced by 76% (337 → 79)
3. **Momentum Impact**: Player needs fewer total attacks (323 → 287) to win
4. **Hit Rate Boost**: 10% improvement in player accuracy (75.5% → 85.7%)
5. **Speed Advantage**: Clear evidence that speed stacking works as designed

### Zombie Bonus Attacks (Baseline)

In baseline scenario where zombie (0.5) > player (0.25):
- Zombie gets **194 bonus attacks** over 50 duels
- Average ~3.9 bonus attacks per duel
- Monster attacks (337) exceed player attacks (323)
- Proves speed gating works for monsters

---

## What We Learned

### Equipment Bonuses Work Correctly

The equipment system was **never broken**! Items properly add speed bonuses:
- Quickfang Dagger: +0.25
- Boots of Swiftness: +0.25
- Ring of Hummingbird: +0.25
- **Total**: 0.25 (base) + 0.75 (equipment) = **1.0 speed_bonus_ratio** ✓

### Speed Gating Confirmed

The condition `attacker_speed > defender_speed` works perfectly:
- Player (1.0) > Zombie (0.5) → Player gets bonus attacks ✓
- Zombie (0.5) > Player (0.25) → Zombie gets bonus attacks ✓
- Player (0.25) < Zombie (0.5) → Player does NOT get bonus attacks ✓

### Scenario Harness Gap

The scenario harness was missing game mechanics that exist in normal gameplay:
- **Fixed**: Player bonus attacks
- **Working**: Monster bonus attacks (via AI system)
- **Working**: Surprise attacks
- **Working**: Kill tracking
- **Potential gaps**: Other game_actions.py mechanics?

---

## Files Modified

1. `services/scenario_harness.py` - Added player bonus attack logic to `_process_player_action()`
2. `game_actions.py` - Removed temporary debug code

---

## Testing

### New JSON Exports
- ✅ `dueling_pit_slow_zombie_baseline_50runs.json` - 194 bonus attacks (zombie)
- ✅ `dueling_pit_slow_zombie_speed_full_50runs.json` - 132 bonus attacks (player)

### Existing Scenarios
All existing scenarios continue to work:
- ✅ dueling_pit (baseline)
- ✅ plague_arena
- ✅ backstab_training
- ✅ dueling_pit_speed_light
- ✅ dueling_pit_speed_full

---

## Next Steps (Future Phases)

### Phase 13E: Speed Tuning
Now that measurements work correctly, we can:
1. Compare different speed builds (baseline vs light vs full)
2. Test against various opponent speeds (0.5, 0.75, 1.0, 1.5, 2.0)
3. Measure optimal speed bonus values
4. Analyze speed vs accuracy trade-offs

### Phase 13F: CI Integration
Consider adding slow zombie scenarios to CI:
- `dueling_pit_slow_zombie_baseline` as a stability check
- `dueling_pit_slow_zombie_speed_full` to ensure player momentum works

### Future Improvements
1. **Consolidate bonus attack logic**: Extract to shared helper used by both game_actions.py and scenario_harness.py
2. **Audit other mechanics**: Check if scenario harness is missing other gameplay systems
3. **Unit tests**: Add tests specifically for scenario bonus attacks

---

## Conclusion

Phase 13D successfully fixed the player bonus attack bug! The issue was **not** with equipment, speed calculation, or the momentum system itself - it was simply that the scenario harness bypassed the bonus attack check.

**The fix is minimal, focused, and effective:**
- ~30 lines of code added to scenario_harness.py
- Uses existing SpeedBonusTracker infrastructure
- Mirrors the logic from game_actions.py
- Properly records metrics for analysis

**The momentum system now works correctly in scenarios:**
- Monster bonus attacks: ✓ (always worked)
- Player bonus attacks: ✓ (now fixed!)
- Speed gating: ✓ (confirmed working)
- Equipment bonuses: ✓ (confirmed applying)
- Metrics tracking: ✓ (all bonus attacks counted)

**The data is ready for tuning!** 🎯
