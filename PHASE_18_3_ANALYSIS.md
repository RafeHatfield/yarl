# Phase 18.3: Item & Combat Curve Tuning

**Date**: 2025-12-13  
**Branch**: `feature/phase18-3-item-tuning`  
**Status**: Analysis Phase

## Baseline Metrics (Pre-Phase 18.3)

### Difficulty Dashboard (from reports/difficulty_dashboard.md)

**Key Scenarios:**
| Scenario | Depth | Death Rate | Player Hit % | Monster Hit % | Pressure Index |
|----------|-------|------------|--------------|---------------|----------------|
| depth1_orc_easy | 1 | 0.0% | 66.7% | 36.6% | -8.2 (player advantage) |
| depth2_orc_baseline | 2 | 5.0% | 68.0% | 37.5% | -11.9 (player advantage) |
| depth3_orc_brutal | 3 | 12.0% | 70.9% | 38.8% | -14.6 (player advantage) |
| depth5_zombie | 5 | 46.0% | 83.9% | 36.7% | +14.7 (monster advantage) |
| zombie_horde | 5 | 10.0% | 84.8% | 20.2% | +1.6 (balanced) |

**Observations:**
- Player hit rates: 67-85% (reasonable spread)
- Monster hit rates: 20-47% (zombies miss more due to low DEX)
- Death rates: 0-46% (good difficulty curve)
- Pressure index: -14.6 to +14.7 (balanced range)

### Phase 18.1-18.2 Implementation Status

**Affixed Weapons Created:**
- Keen (2 weapons): crit 19-20 (10% vs 5% base)
- Fine (2 weapons): +1 to-hit
- Vicious (2 weapons): +1 damage (1d10+1)
- Masterwork (1 weapon): +1 hit, +1 damage

**Damage Types:**
- Base weapons: slashing/piercing/bludgeoning
- Zombie: resistant piercing, vulnerable bludgeoning

**Test Coverage:**
- ✅ 17 Phase 18 tests (all passing)
- ✅ 3109 total tests passing

---

## Analysis Questions (Step 1)

### Q1: Are Keen weapons increasing crit frequency measurably?

**Expected Impact:**
- Base crit rate: 5% (1 in 20 rolls)
- Keen crit rate: 10% (2 in 20 rolls)
- **Doubling of crit frequency**

**Current Status:**
- ❓ No ecosystem runs with Phase 18 items yet
- Tests confirm keen weapons crit on 19-20
- Need validation run to measure actual frequency

**Action Required:**
- Run ecosystem scenario with Keen weapons enabled
- Measure crit frequency in combat logs

### Q2: Are Vicious weapons increasing average damage?

**Expected Impact:**
- Vicious battleaxe: 1d10+1 → avg 6.5 damage (vs 1d10 = 5.5)
- **+1 average damage (~18% increase)**

**Current Status:**
- ❓ No damage distribution data with Phase 18 items
- Configuration correct (1d10+1 in YAML)
- Need validation run to confirm

**Action Required:**
- Run ecosystem scenario comparing vicious vs base weapons
- Measure average damage dealt

### Q3: Do damage types shift outcomes in zombie scenarios?

**Expected Impact:**
- Bludgeoning vs zombie: +1 damage
- Piercing vs zombie: -1 damage
- **~15-20% damage swing** on zombie encounters

**Current Status:**
- ❓ No zombie scenario runs with Phase 18 damage types
- Configuration correct (zombie has resist/vuln)
- Need validation run to confirm

**Zombie Scenarios to Test:**
- `zombie_horde` (depth 5, 10% death rate baseline)
- `depth5_zombie` (depth 5, 46% death rate baseline)

**Action Required:**
- Run zombie scenarios with bludgeoning weapons (club, mace)
- Run zombie scenarios with piercing weapons (dagger, rapier)
- Compare death rates and combat duration

---

## Preliminary Assessment (Before Validation Runs)

### Affix Balance (Theoretical)

**Keen vs Vicious vs Fine:**
```
Keen: 10% crit (2× damage) = 0.10 × 2× = +10% avg damage (spiky)
Fine: +1 to-hit = +5% hit chance = ~+5-7% DPS (reliable)
Vicious: +1 damage = +18-20% avg damage (brute force)
```

**Concern**: Vicious appears strongest on paper (+18% vs +10% for Keen).

**Mitigation Options:**
1. Keep as-is (Vicious is simple, Keen is exciting)
2. Reduce Vicious to fractional bonus (complex, avoid)
3. Increase Keen crit threshold to 18-20 (15% crit - too strong)
4. Accept that Vicious is slightly stronger (acceptable for Phase 18)

**Recommendation**: Keep current balance, validate with runs first.

### Damage Type Impact (Theoretical)

**Bludgeoning vs Zombie:**
```
Base: 1d6 club = 3.5 avg
vs Zombie: 3.5 + 1 = 4.5 avg (+28% damage)
```

**Piercing vs Zombie:**
```
Base: 1d4 dagger = 2.5 avg  
vs Zombie: 2.5 - 1 = 1.5 → floor(1) often = ~1.5 avg (-40% damage)
```

**Concern**: Piercing penalty might be too harsh for daggers.

**Mitigation**: Zombies are slow (low evasion), so higher hit rate compensates.

**Recommendation**: Validate with runs, consider softening if zombie fights become trivial with bludgeoning.

---

## Tuning Plan (Step 2-4)

### No Changes Recommended Yet

**Rationale:**
- Phase 18.1-18.2 just implemented
- No validation data available
- Numbers are theoretically reasonable
- Tests all pass

**Next Steps:**
1. Run validation scenarios (Step 5)
2. Collect metrics
3. Compare to baseline
4. Apply tuning ONLY if needed

---

## Validation Plan (Step 5)

### Required Test Runs

#### Ecosystem Validation (Quick)
```bash
# Orc scenarios (test Fine/Vicious)
python3 engine.py --scenario depth2_orc_baseline --runs 30

# Zombie scenarios (test damage types)
python3 engine.py --scenario zombie_horde --runs 30
python3 engine.py --scenario depth5_zombie --runs 30
```

#### Full Difficulty Suite
```bash
make difficulty-all
```

### Metrics to Compare

**Before vs After Phase 18:**
| Metric | Baseline | Target (Phase 18) | Acceptable Range |
|--------|----------|-------------------|------------------|
| depth2_orc death % | 5.0% | 3-7% | ±2% (stable) |
| depth5_zombie death % | 46.0% | 40-52% | ±6% (stable) |
| zombie_horde death % | 10.0% | 8-15% | ±5% (stable) |
| Player hit % | 68-85% | 68-85% | No change |
| Crit frequency | ~5% | 5-10% | Keen weapons present |

---

## Acceptance Criteria

### Phase 18.3 Success Metrics

✅ **Affix Viability:**
- Keen weapons show measurable crit increase (~10%)
- Fine weapons show hit rate improvement (~+5%)
- Vicious weapons show damage increase (~+1 avg)
- No single affix dominates (all have use cases)

✅ **Damage Type Impact:**
- Bludgeoning vs zombie: noticeable but not game-breaking
- Piercing vs zombie: penalty exists but not crippling
- Other matchups remain neutral

✅ **Difficulty Stability:**
- Death rates within ±5% of baseline
- Pressure index within ±3 points
- No scenario collapses or spikes

✅ **Test Coverage:**
- All tests passing (3109+)
- No regressions in combat mechanics

---

## Status

**Current**: Analysis complete, no validation runs yet  
**Next**: Run ecosystem scenarios to collect Phase 18 metrics  
**Then**: Apply tuning ONLY if metrics show imbalance

**Recommendation**: Phase 18.1-18.2 implementation appears sound. Validation runs required before any tuning.
