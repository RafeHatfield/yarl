# Necromancer Scenario Balance Tuning

**Date:** 2026-01-01  
**Issue:** Initial scenario configuration resulted in extreme outcomes  
**Resolution:** Iterative tuning to 5-20 deaths / 30 runs (moderate threat)

---

## Tuning Journey

### Initial Configuration (FAIL)

**Setup:**
- 1 Necromancer + 4 Skeletons + 4 Orcs (9 enemies)
- Player: dagger, no armor, 10 healing potions
- Result: **27/30 deaths** (90% death rate)
- Verdict: **Too hard** - overwhelming

### Over-Correction (TOO EASY)

**Setup:**
- 1 Necromancer + 2 Skeletons + 1 Orc (4 enemies)
- Player: shortsword, leather armor, 20 healing potions
- Result: **1/30 deaths** (3% death rate)
- Verdict: **Too easy** - necromancer is a pushover

### Final Balance (GOLDILOCKS)

**Setup:**
- 1 Necromancer + 3 Skeletons + 2 Orcs (6 enemies)
- Player: shortsword, leather armor, 13 healing potions
- Result: **10-11/30 deaths** (33-37% death rate)
- Verdict: **Just right** - moderate threat

---

## Balance Philosophy

**Death Rate Range: 5-20 deaths / 30 runs**

### Why This Range?

**Minimum (5 deaths):**
- Validates necromancer is a **real threat**
- Player can't ignore raised zombies
- Corpse economy creates tactical pressure
- **Below 5 = scenario doesn't test the mechanic**

**Maximum (20 deaths):**
- Ensures necromancer is **beatable with skill**
- Not an auto-loss scenario
- Tactical play should succeed ~60-80% of the time
- **Above 20 = scenario is frustrating, not fun**

**Sweet Spot (10 deaths):**
- 33% death rate = challenging but fair
- 67% win rate = player has agency
- Demonstrates necromancer power without overwhelming
- Room for variance (±5 deaths expected)

---

## Brittleness Considerations

**Question:** Is 5-20 range too narrow/brittle?

**Analysis:**

### Variance Sources

1. **Bot RNG (seed-based):**
   - 30 runs smooth out variance
   - Expected variance: ±3-5 deaths
   - **Impact: LOW**

2. **Combat Math Changes:**
   - If to-hit/damage formulas change, deaths shift
   - **This is intended** - scenario catches regressions
   - **Impact: MEDIUM (by design)**

3. **Equipment Changes:**
   - If shortsword/leather_armor stats change, deaths shift
   - Scenario uses specific items (not random loot)
   - **Impact: MEDIUM (detectable)**

4. **AI Behavior Changes:**
   - If necromancer raise/seek logic regresses, deaths shift
   - **This is what we're testing!**
   - **Impact: HIGH (desired)**

### Brittleness Assessment

**15-point range (5-20) provides:**
- ✅ Clear signal when something breaks
- ✅ Tolerance for minor variance (±5)
- ✅ Validates both "too easy" and "too hard"
- ⚠️ May require baseline updates if intentional changes made

**Alternatives Considered:**

| Range | Pros | Cons | Verdict |
|-------|------|------|---------|
| 5-20 (current) | Tight signal, validates threat level | May need tuning on combat changes | ✅ RECOMMENDED |
| 3-25 (wider) | More tolerant, less maintenance | Loses signal, allows drift | ⚠️ Too loose |
| 8-15 (narrower) | Very precise validation | Brittle, constant tuning | ❌ Too tight |
| No range (any deaths OK) | Never breaks | Useless for validation | ❌ Not a test |

**Recommendation:** **Keep 5-20 range**

**Rationale:**
- Scenario is a **regression anchor**, not a smoke test
- SHOULD fail when combat balance shifts
- Easy to update baseline when intentional changes made
- Provides valuable signal vs noise

---

## Tuning Knobs (For Future Adjustments)

**If deaths drift outside 5-20 range:**

### Too Hard (>20 deaths) - Player Needs Help

**Buff Options (choose smallest impact first):**
1. +2-3 healing potions
2. Upgrade weapon (shortsword → longsword)
3. Upgrade armor (leather → scale)
4. Remove 1-2 initial enemies
5. Reduce necromancer raise range (5 → 4)

### Too Easy (<5 deaths) - Necromancer Needs Threat

**Nerf Options (choose smallest impact first):**
1. -2-3 healing potions
2. Downgrade weapon (shortsword → dagger)
3. Remove player armor
4. Add 1-2 more initial enemies
5. Increase necromancer raise range (5 → 6)
6. Reduce raise cooldown (4 → 3 turns)

### Current Leverage Points

**Scenario Tuning (No Code):**
- Enemy count: 6 (can adjust 4-8 range)
- Potions: 13 (can adjust 8-18 range)
- Player weapon: shortsword (can swap dagger/longsword)
- Player armor: leather (can remove or upgrade)

**Necromancer Tuning (Config Change):**
- Raise cooldown: 4 turns (can adjust 3-6 range)
- Raise range: 5 tiles (can adjust 4-6 range)
- Danger radius: 2 tiles (can adjust 1-3 range)

**Both approaches are valid** - prefer scenario tuning for scenario-specific fixes, config tuning for global balance.

---

## Baseline Establishment

**New Baseline (2026-01-01):**

```json
"monster_necromancer_identity": {
  "deaths": 10,
  "death_rate": 0.33,
  "player_hit_rate": 0.7693,
  "monster_hit_rate": 0.2819,
  "pressure_index": -8.30,
  "bonus_attacks_per_run": 16.40
}
```

**Interpretation:**
- 10/30 deaths = 33% death rate (moderate threat)
- Player hit rate 77% = player has good accuracy
- Monster hit rate 28% = necromancer + zombies not overwhelming
- Pressure index -8.3 = slightly player-favored (good for regression test)

**When to Update Baseline:**
- Intentional necromancer tuning (cooldown, range changes)
- Intentional scenario rebalancing (enemy count, player kit)
- Global combat math changes (to-hit formulas, damage scaling)

**When NOT to Update:**
- Test failures due to bugs (fix the bug, not the baseline)
- Random variance (rerun to confirm)
- Single outlier run (30-run average should be stable)

---

## Comparison to Other Identity Scenarios

| Scenario | Deaths | Death Rate | Threat Level |
|----------|--------|------------|--------------|
| Slime | 0 | 0% | Trivial |
| Skeleton | 0 | 0% | Trivial |
| Troll | 0 | 0% | Trivial |
| Shaman | 8 | 27% | Moderate |
| Necromancer | 10 | 33% | **Moderate** |
| Chieftain | 13 | 43% | High |
| Wraith | 23 | 77% | Very High |

**Necromancer sits between Shaman and Chieftain - appropriate for summoner/controller archetype.**

---

## Recommendations

### For This Scenario

**ACCEPT 5-20 range as-is:**
- Validates moderate threat level
- Detects regressions effectively
- Not overly brittle (15-point range)
- Easy to interpret failures

**Document clearly:**
- Why range exists (not arbitrary)
- How to adjust if needed (tuning knobs above)
- When to update baseline vs fix bugs

### For Future Identity Scenarios

**Consider threat-appropriate ranges:**
- **Low threat** (Slime, Skeleton): 0-5 deaths
- **Moderate threat** (Shaman, Necromancer): 5-20 deaths
- **High threat** (Chieftain, Wraith): 15-30 deaths

**Don't use one-size-fits-all thresholds** - tailor to monster identity.

---

## Summary

**Problem:** Necromancer scenario had extreme variance (1 death → 27 deaths)

**Solution:** Iterative tuning to hit 5-20 range with clear baseline

**Final State:**
- ✅ 10 deaths / 30 runs (33% death rate)
- ✅ Moderate threat (between Shaman and Chieftain)
- ✅ Validates necromancer raises corpses (~85/run)
- ✅ Tests corpse seeking (~100 moves/run)
- ✅ Range prevents both over/under tuning

**Baseline Updated:** Old baseline (30 deaths) replaced with new (10 deaths)

**Balance Suite:** Now passes with minimal delta

---

**END OF DOCUMENT**

