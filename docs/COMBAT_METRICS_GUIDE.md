# Combat Metrics Guide (Phase 13A)

## Overview

Phase 13A introduces **combat metrics** to the scenario harness, enabling data-driven analysis of hit rates, attack pacing, and combat balance.

## Quick Start

### Run a Dueling Scenario
```bash
python3 ecosystem_sanity.py \
  --scenario dueling_pit \
  --runs 50 \
  --export-json dueling_data.json
```

### View Combat Metrics
The CLI automatically displays combat metrics in the Results section:

```
Combat Metrics:
  Player Attacks: 287
  Player Hits: 191
  Player Hit Rate: 66.6%
  Monster Attacks: 187
  Monster Hits: 78
  Monster Hit Rate: 41.7%
```

### Export to JSON
Use `--export-json` to save metrics for analysis:

```json
{
  "scenario_id": "dueling_pit",
  "runs": 50,
  "metrics": {
    "total_player_attacks": 287,
    "total_player_hits": 191,
    "total_monster_attacks": 187,
    "total_monster_hits": 78,
    ...
  }
}
```

---

## Metrics Reference

### Player Combat Stats
- **`total_player_attacks`**: Total attack attempts by the player across all runs
- **`total_player_hits`**: Total successful hits by the player
- **Player Hit Rate**: `total_player_hits / total_player_attacks × 100%`

### Monster Combat Stats
- **`total_monster_attacks`**: Total attack attempts by all monsters across all runs
- **`total_monster_hits`**: Total successful hits by monsters
- **Monster Hit Rate**: `total_monster_hits / total_monster_attacks × 100%`

### What Counts as an Attack?
All d20-based melee attacks, including:
- Normal attacks (hit or miss)
- Critical hits (natural 20)
- Fumbles (natural 1)
- Surprise attacks (auto-hit)
- Bonus/momentum attacks

### What Counts as a Hit?
- Attack roll ≥ target AC
- Natural 20 (always hits)
- Surprise attacks (always hit)
- **Does NOT count**: Natural 1 (always misses)

---

## Available Scenarios

### dueling_pit (New in Phase 13A)
**Purpose**: Baseline 1v1 combat measurement

- **Depth**: 5
- **Opponent**: Single orc
- **Equipment**: Dagger + leather armor
- **Typical Hit Rates**: ~65-70% player, ~40-50% monster
- **Use For**: Baseline accuracy/evasion tuning

### backstab_training
**Purpose**: Surprise attack mechanics

- **Depth**: 5
- **Typical Hit Rates**: ~65-70% player, ~55-65% monster
- **Note**: Includes surprise attacks (100% hit rate)
- **Use For**: Stealth/backstab balance

### plague_arena
**Purpose**: Swarm combat and plague mechanics

- **Depth**: 8
- **Typical Hit Rates**: ~75-80% player, ~25-35% monster
- **Note**: Zombies have lower accuracy
- **Use For**: AOE/swarm balance

---

## Analysis Examples

### Calculate Hit Rates from JSON
```bash
cat dueling_data.json | jq '.metrics | {
  player_hit_rate: ((.total_player_hits / .total_player_attacks) * 100 | round),
  monster_hit_rate: ((.total_monster_hits / .total_monster_attacks) * 100 | round),
  combat_ratio: (.total_player_attacks / .total_monster_attacks)
}'
```

Output:
```json
{
  "player_hit_rate": 67,
  "monster_hit_rate": 42,
  "combat_ratio": 1.53
}
```

### Compare Scenarios
```bash
for scenario in backstab_training plague_arena dueling_pit; do
  echo "=== $scenario ==="
  python3 ecosystem_sanity.py --scenario $scenario --runs 20 2>&1 \
    | grep -A 2 "Player Hit Rate"
done
```

### Track Metrics Over Time
```bash
# Baseline measurement
python3 ecosystem_sanity.py --scenario dueling_pit --runs 100 \
  --export-json baseline_v1.json

# After balance changes
python3 ecosystem_sanity.py --scenario dueling_pit --runs 100 \
  --export-json baseline_v2.json

# Compare
jq -s '.[0].metrics.total_player_hits, .[1].metrics.total_player_hits' \
  baseline_v1.json baseline_v2.json
```

---

## Interpreting Results

### Hit Rate Expectations

**General Guidelines** (depth 5, baseline equipment):
- **Player vs Orc**: 60-70% hit rate (slight player advantage)
- **Player vs Zombie**: 70-80% hit rate (zombie disadvantage)
- **Monster vs Player**: 40-60% hit rate (depends on armor/stats)

### Red Flags
🚩 Player hit rate < 50% → Player too weak or monster AC too high
🚩 Player hit rate > 90% → Combat too easy, needs challenge
🚩 Monster hit rate > 80% → Player defense too low, unfair
🚩 Monster hit rate < 20% → Combat too one-sided

### Combat Ratio
`combat_ratio = total_player_attacks / total_monster_attacks`

- **Ratio > 1.5**: Player attacks much more (speed advantage or monsters dying quickly)
- **Ratio ≈ 1.0**: Balanced turn-taking
- **Ratio < 0.7**: Monsters attack more (player on defensive or outnumbered)

---

## Common Tasks

### Measure Impact of Equipment Change
```bash
# Before change
python3 ecosystem_sanity.py --scenario dueling_pit --runs 50 \
  --export-json before.json

# Make equipment change (e.g., adjust dagger damage)

# After change
python3 ecosystem_sanity.py --scenario dueling_pit --runs 50 \
  --export-json after.json

# Compare
echo "Before: $(jq '.metrics.total_player_hits' before.json) hits"
echo "After: $(jq '.metrics.total_player_hits' after.json) hits"
```

### Measure Impact of Stat Changes
```bash
# Test with different depths (affects monster stats)
for depth in 1 5 10 15 20; do
  # Note: Would need scenario YAML with configurable depth
  python3 ecosystem_sanity.py --scenario dueling_pit --runs 20 \
    --export-json depth_${depth}.json
done

# Analyze hit rate vs depth
for f in depth_*.json; do
  jq -r '[.scenario_id, .metrics.total_player_hits, .metrics.total_player_attacks] | @csv' $f
done
```

### Find Optimal Balance Point
```bash
# Run 100+ iterations for statistical significance
python3 ecosystem_sanity.py --scenario dueling_pit --runs 100 \
  --export-json dueling_100runs.json

# Calculate confidence intervals
jq '.metrics | {
  player_hit_rate: (.total_player_hits / .total_player_attacks),
  sample_size: .total_player_attacks,
  confidence_95: (1.96 * sqrt((.total_player_hits / .total_player_attacks) * (1 - (.total_player_hits / .total_player_attacks)) / .total_player_attacks))
}' dueling_100runs.json
```

---

## Troubleshooting

### Metrics show 0/0 attacks
**Cause**: Combat never happened (player/monsters died too quickly or turn limit too short)
**Fix**: Increase `--turn-limit` or check scenario spawn configuration

### Hit rates seem inconsistent
**Cause**: Low sample size (< 20 runs)
**Fix**: Run at least 50 iterations for stable statistics

### Monster hit rate = 0%
**Cause**: Player killed monster before it could attack (surprise attacks, high damage)
**Fix**: Expected in some scenarios (e.g., backstab_training)

---

## Future Enhancements (Phase 13B+)

Planned additions:
- [ ] **Critical hit rate** tracking
- [ ] **Fumble rate** tracking
- [ ] **Damage per hit** distribution
- [ ] **Turns per kill** metric
- [ ] **Speed bonus** effectiveness
- [ ] **Momentum chain** statistics
- [ ] **Attack type breakdown** (normal/surprise/bonus)

---

## See Also

- `PHASE_13A_SUMMARY.md` - Implementation details
- `config/levels/scenario_dueling_pit.yaml` - Example scenario
- `ecosystem_sanity.py --help` - CLI reference
