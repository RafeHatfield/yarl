# Difficulty Curve Dashboard
_Updated: 2025-12-11_

[Eco Balance Report](reports/eco_balance_report.md)

## Overview
- Scenarios: 13
- Metrics source: `/Users/rafehatfield/development/rlike/reports/metrics`
- Graphs: `/Users/rafehatfield/development/rlike/reports/graphs`

## Summary Table

| scenario | family | depth | runs | death% | player_hit% | monster_hit% | bonus/run | pressure_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| backstab_training | backstab_training | None | 100 | 1.0% | 69.3% | 47.2% | 5.20 | -7.60 |
| dueling_pit | dueling_pit | None | 50 | 0.0% | 70.3% | 34.9% | 2.38 | -3.50 |
| dueling_pit_slow_zombie_baseline | dueling_pit | None | 50 | 0.0% | 80.4% | 26.7% | 3.14 | 0.60 |
| dueling_pit_slow_zombie_speed_full | dueling_pit | None | 50 | 0.0% | 88.0% | 21.5% | 2.36 | -3.76 |
| dueling_pit_speed_full | dueling_pit | None | 50 | 0.0% | 72.7% | 27.9% | 3.38 | -4.54 |
| dueling_pit_speed_light | dueling_pit | None | 50 | 0.0% | 73.2% | 36.4% | 3.08 | -4.24 |
| orc_swarm_baseline | orc_swarm | None | 50 | 10.0% | 69.4% | 36.4% | 10.60 | -15.22 |
| orc_swarm_brutal_baseline | orc_swarm | None | 50 | 14.0% | 69.8% | 34.8% | 13.04 | -19.20 |
| orc_swarm_brutal_speed_full | orc_swarm | None | 50 | 0.0% | 74.2% | 33.8% | 15.88 | -21.74 |
| orc_swarm_speed_full | orc_swarm | None | 50 | 2.0% | 74.3% | 31.8% | 9.42 | -12.98 |
| orc_swarm_tight | orc_swarm | None | 50 | 24.0% | 70.3% | 46.3% | 4.04 | -7.54 |
| plague_arena | plague_arena | None | 100 | 38.0% | 83.6% | 24.3% | 11.93 | 3.93 |
| zombie_horde | zombie_horde | None | 50 | 14.0% | 85.0% | 20.8% | 11.50 | 1.90 |

## Graphs

![player_hit_rate_vs_depth.png](graphs/player_hit_rate_vs_depth.png)

![monster_hit_rate_vs_depth.png](graphs/monster_hit_rate_vs_depth.png)

![death_rate_vs_depth.png](graphs/death_rate_vs_depth.png)

![bonus_attacks_per_run_vs_depth.png](graphs/bonus_attacks_per_run_vs_depth.png)

![pressure_index_vs_depth.png](graphs/pressure_index_vs_depth.png)

![difficulty_curve_overview.png](graphs/difficulty_curve_overview.png)

## Family Insights
- **backstab_training** — deaths 1–1%, player hit ~69%, monster hit ~47%, bonus/run ~5, pressure index ~-7.6 (player drives tempo).
- **dueling_pit** — deaths 0–0%, player hit ~77%, monster hit ~29%, bonus/run ~3, pressure index ~-3.1 (balanced tempo).
- **orc_swarm** — deaths 0–24%, player hit ~72%, monster hit ~37%, bonus/run ~11, pressure index ~-15.3 (player drives tempo).
- **plague_arena** — deaths 38–38%, player hit ~84%, monster hit ~24%, bonus/run ~12, pressure index ~3.9 (balanced tempo).
- **zombie_horde** — deaths 14–14%, player hit ~85%, monster hit ~21%, bonus/run ~12, pressure index ~1.9 (balanced tempo).

## Scenario Breakdown
### backstab_training
- family: backstab_training
- depth: None
- runs: 100
- death_rate: 0.010
- player_hit_rate: 0.693
- monster_hit_rate: 0.472
- bonus_attacks_per_run: 5.200
- pressure_index: -7.600

### dueling_pit
- family: dueling_pit
- depth: None
- runs: 50
- death_rate: 0.000
- player_hit_rate: 0.703
- monster_hit_rate: 0.349
- bonus_attacks_per_run: 2.380
- pressure_index: -3.500

### dueling_pit_slow_zombie_baseline
- family: dueling_pit
- depth: None
- runs: 50
- death_rate: 0.000
- player_hit_rate: 0.804
- monster_hit_rate: 0.267
- bonus_attacks_per_run: 3.140
- pressure_index: 0.600

### dueling_pit_slow_zombie_speed_full
- family: dueling_pit
- depth: None
- runs: 50
- death_rate: 0.000
- player_hit_rate: 0.880
- monster_hit_rate: 0.215
- bonus_attacks_per_run: 2.360
- pressure_index: -3.760

### dueling_pit_speed_full
- family: dueling_pit
- depth: None
- runs: 50
- death_rate: 0.000
- player_hit_rate: 0.727
- monster_hit_rate: 0.279
- bonus_attacks_per_run: 3.380
- pressure_index: -4.540

### dueling_pit_speed_light
- family: dueling_pit
- depth: None
- runs: 50
- death_rate: 0.000
- player_hit_rate: 0.732
- monster_hit_rate: 0.364
- bonus_attacks_per_run: 3.080
- pressure_index: -4.240

### orc_swarm_baseline
- family: orc_swarm
- depth: None
- runs: 50
- death_rate: 0.100
- player_hit_rate: 0.694
- monster_hit_rate: 0.364
- bonus_attacks_per_run: 10.600
- pressure_index: -15.220

### orc_swarm_brutal_baseline
- family: orc_swarm
- depth: None
- runs: 50
- death_rate: 0.140
- player_hit_rate: 0.698
- monster_hit_rate: 0.348
- bonus_attacks_per_run: 13.040
- pressure_index: -19.200

### orc_swarm_brutal_speed_full
- family: orc_swarm
- depth: None
- runs: 50
- death_rate: 0.000
- player_hit_rate: 0.742
- monster_hit_rate: 0.338
- bonus_attacks_per_run: 15.880
- pressure_index: -21.740

### orc_swarm_speed_full
- family: orc_swarm
- depth: None
- runs: 50
- death_rate: 0.020
- player_hit_rate: 0.743
- monster_hit_rate: 0.318
- bonus_attacks_per_run: 9.420
- pressure_index: -12.980

### orc_swarm_tight
- family: orc_swarm
- depth: None
- runs: 50
- death_rate: 0.240
- player_hit_rate: 0.703
- monster_hit_rate: 0.463
- bonus_attacks_per_run: 4.040
- pressure_index: -7.540

### plague_arena
- family: plague_arena
- depth: None
- runs: 100
- death_rate: 0.380
- player_hit_rate: 0.836
- monster_hit_rate: 0.243
- bonus_attacks_per_run: 11.930
- pressure_index: 3.930

### zombie_horde
- family: zombie_horde
- depth: None
- runs: 50
- death_rate: 0.140
- player_hit_rate: 0.850
- monster_hit_rate: 0.208
- bonus_attacks_per_run: 11.500
- pressure_index: 1.900

## Raw Metrics (appendix)

<details><summary>backstab_training</summary>

```json
{
  "_source_path": "/Users/rafehatfield/development/rlike/reports/metrics/backstab_training_metrics.json",
  "bonus_attacks_per_run": 5.2,
  "death_rate": 0.01,
  "depth": null,
  "family": "backstab_training",
  "monster_attacks_per_run": 7.84,
  "monster_hit_rate": 0.4719387755102041,
  "player_attacks_per_run": 15.44,
  "player_hit_rate": 0.6930051813471503,
  "pressure_index": -7.6,
  "raw": {
    "metrics": {
      "average_turns": 24.96,
      "player_deaths": 1,
      "runs": 100,
      "total_bonus_attacks_triggered": 520,
      "total_kills_by_faction": {
        "Orc": 1,
        "Player": 199
      },
      "total_kills_by_source": {
        "MONSTERS": 1,
        "PLAYER": 199
      },
      "total_monster_attacks": 784,
      "total_monster_hits": 370,
      "total_plague_infections": 0,
      "total_player_attacks": 1544,
      "total_player_hits": 1070,
      "total_portals_used": 0,
      "total_reanimations": 0,
      "total_surprise_attacks": 200
    },
    "player_bot": "tactical_fighter",
    "runs": 100,
    "scenario_id": "backstab_training",
    "turn_limit": 50
  },
  "runs": 100,
  "scenario_id": "backstab_training"
}
```

</details>

<details><summary>dueling_pit</summary>

```json
{
  "_source_path": "/Users/rafehatfield/development/rlike/reports/metrics/dueling_pit_metrics.json",
  "bonus_attacks_per_run": 2.38,
  "death_rate": 0.0,
  "depth": null,
  "family": "dueling_pit",
  "monster_attacks_per_run": 3.9,
  "monster_hit_rate": 0.3487179487179487,
  "player_attacks_per_run": 7.4,
  "player_hit_rate": 0.7027027027027027,
  "pressure_index": -3.5000000000000004,
  "raw": {
    "metrics": {
      "average_turns": 50.0,
      "player_deaths": 0,
      "runs": 50,
      "total_bonus_attacks_triggered": 119,
      "total_kills_by_faction": {
        "Player": 50
      },
      "total_kills_by_source": {
        "PLAYER": 50
      },
      "total_monster_attacks": 195,
      "total_monster_hits": 68,
      "total_plague_infections": 0,
      "total_player_attacks": 370,
      "total_player_hits": 260,
      "total_portals_used": 0,
      "total_reanimations": 0,
      "total_surprise_attacks": 50
    },
    "player_bot": "tactical_fighter",
    "runs": 50,
    "scenario_id": "dueling_pit",
    "turn_limit": 100
  },
  "runs": 50,
  "scenario_id": "dueling_pit"
}
```

</details>

<details><summary>dueling_pit_slow_zombie_baseline</summary>

```json
{
  "_source_path": "/Users/rafehatfield/development/rlike/reports/metrics/dueling_pit_slow_zombie_baseline_metrics.json",
  "bonus_attacks_per_run": 3.14,
  "death_rate": 0.0,
  "depth": null,
  "family": "dueling_pit",
  "monster_attacks_per_run": 6.3,
  "monster_hit_rate": 0.26666666666666666,
  "player_attacks_per_run": 5.7,
  "player_hit_rate": 0.8035087719298246,
  "pressure_index": 0.5999999999999996,
  "raw": {
    "metrics": {
      "average_turns": 50.0,
      "player_deaths": 0,
      "runs": 50,
      "total_bonus_attacks_triggered": 157,
      "total_kills_by_faction": {
        "Player": 50
      },
      "total_kills_by_source": {
        "PLAYER": 50
      },
      "total_monster_attacks": 315,
      "total_monster_hits": 84,
      "total_plague_infections": 0,
      "total_player_attacks": 285,
      "total_player_hits": 229,
      "total_portals_used": 0,
      "total_reanimations": 0,
      "total_surprise_attacks": 50
    },
    "player_bot": "tactical_fighter",
    "runs": 50,
    "scenario_id": "dueling_pit_slow_zombie_baseline",
    "turn_limit": 100
  },
  "runs": 50,
  "scenario_id": "dueling_pit_slow_zombie_baseline"
}
```

</details>

<details><summary>dueling_pit_slow_zombie_speed_full</summary>

```json
{
  "_source_path": "/Users/rafehatfield/development/rlike/reports/metrics/dueling_pit_slow_zombie_speed_full_metrics.json",
  "bonus_attacks_per_run": 2.36,
  "death_rate": 0.0,
  "depth": null,
  "family": "dueling_pit",
  "monster_attacks_per_run": 1.58,
  "monster_hit_rate": 0.21518987341772153,
  "player_attacks_per_run": 5.34,
  "player_hit_rate": 0.8801498127340824,
  "pressure_index": -3.76,
  "raw": {
    "metrics": {
      "average_turns": 50.0,
      "player_deaths": 0,
      "runs": 50,
      "total_bonus_attacks_triggered": 118,
      "total_kills_by_faction": {
        "Player": 50
      },
      "total_kills_by_source": {
        "PLAYER": 50
      },
      "total_monster_attacks": 79,
      "total_monster_hits": 17,
      "total_plague_infections": 0,
      "total_player_attacks": 267,
      "total_player_hits": 235,
      "total_portals_used": 0,
      "total_reanimations": 0,
      "total_surprise_attacks": 50
    },
    "player_bot": "tactical_fighter",
    "runs": 50,
    "scenario_id": "dueling_pit_slow_zombie_speed_full",
    "turn_limit": 100
  },
  "runs": 50,
  "scenario_id": "dueling_pit_slow_zombie_speed_full"
}
```

</details>

<details><summary>dueling_pit_speed_full</summary>

```json
{
  "_source_path": "/Users/rafehatfield/development/rlike/reports/metrics/dueling_pit_speed_full_metrics.json",
  "bonus_attacks_per_run": 3.38,
  "death_rate": 0.0,
  "depth": null,
  "family": "dueling_pit",
  "monster_attacks_per_run": 2.94,
  "monster_hit_rate": 0.2789115646258503,
  "player_attacks_per_run": 7.48,
  "player_hit_rate": 0.7272727272727273,
  "pressure_index": -4.540000000000001,
  "raw": {
    "metrics": {
      "average_turns": 50.0,
      "player_deaths": 0,
      "runs": 50,
      "total_bonus_attacks_triggered": 169,
      "total_kills_by_faction": {
        "Player": 50
      },
      "total_kills_by_source": {
        "PLAYER": 50
      },
      "total_monster_attacks": 147,
      "total_monster_hits": 41,
      "total_plague_infections": 0,
      "total_player_attacks": 374,
      "total_player_hits": 272,
      "total_portals_used": 0,
      "total_reanimations": 0,
      "total_surprise_attacks": 50
    },
    "player_bot": "tactical_fighter",
    "runs": 50,
    "scenario_id": "dueling_pit_speed_full",
    "turn_limit": 100
  },
  "runs": 50,
  "scenario_id": "dueling_pit_speed_full"
}
```

</details>

<details><summary>dueling_pit_speed_light</summary>

```json
{
  "_source_path": "/Users/rafehatfield/development/rlike/reports/metrics/dueling_pit_speed_light_metrics.json",
  "bonus_attacks_per_run": 3.08,
  "death_rate": 0.0,
  "depth": null,
  "family": "dueling_pit",
  "monster_attacks_per_run": 3.3,
  "monster_hit_rate": 0.36363636363636365,
  "player_attacks_per_run": 7.54,
  "player_hit_rate": 0.7320954907161804,
  "pressure_index": -4.24,
  "raw": {
    "metrics": {
      "average_turns": 50.0,
      "player_deaths": 0,
      "runs": 50,
      "total_bonus_attacks_triggered": 154,
      "total_kills_by_faction": {
        "Player": 50
      },
      "total_kills_by_source": {
        "PLAYER": 50
      },
      "total_monster_attacks": 165,
      "total_monster_hits": 60,
      "total_plague_infections": 0,
      "total_player_attacks": 377,
      "total_player_hits": 276,
      "total_portals_used": 0,
      "total_reanimations": 0,
      "total_surprise_attacks": 50
    },
    "player_bot": "tactical_fighter",
    "runs": 50,
    "scenario_id": "dueling_pit_speed_light",
    "turn_limit": 100
  },
  "runs": 50,
  "scenario_id": "dueling_pit_speed_light"
}
```

</details>

<details><summary>orc_swarm_baseline</summary>

```json
{
  "_source_path": "/Users/rafehatfield/development/rlike/reports/metrics/orc_swarm_baseline_metrics.json",
  "bonus_attacks_per_run": 10.6,
  "death_rate": 0.1,
  "depth": null,
  "family": "orc_swarm",
  "monster_attacks_per_run": 15.4,
  "monster_hit_rate": 0.36363636363636365,
  "player_attacks_per_run": 30.62,
  "player_hit_rate": 0.6943174395819726,
  "pressure_index": -15.22,
  "raw": {
    "metrics": {
      "average_turns": 47.76,
      "player_deaths": 5,
      "runs": 50,
      "total_bonus_attacks_triggered": 530,
      "total_kills_by_faction": {
        "Orc": 5,
        "Player": 195
      },
      "total_kills_by_source": {
        "MONSTERS": 5,
        "PLAYER": 195
      },
      "total_monster_attacks": 770,
      "total_monster_hits": 280,
      "total_plague_infections": 0,
      "total_player_attacks": 1531,
      "total_player_hits": 1063,
      "total_portals_used": 0,
      "total_reanimations": 0,
      "total_surprise_attacks": 200
    },
    "player_bot": "tactical_fighter",
    "runs": 50,
    "scenario_id": "orc_swarm_baseline",
    "turn_limit": 100
  },
  "runs": 50,
  "scenario_id": "orc_swarm_baseline"
}
```

</details>

<details><summary>orc_swarm_brutal_baseline</summary>

```json
{
  "_source_path": "/Users/rafehatfield/development/rlike/reports/metrics/orc_swarm_brutal_baseline_metrics.json",
  "bonus_attacks_per_run": 13.04,
  "death_rate": 0.14,
  "depth": null,
  "family": "orc_swarm",
  "monster_attacks_per_run": 18.2,
  "monster_hit_rate": 0.34835164835164834,
  "player_attacks_per_run": 37.4,
  "player_hit_rate": 0.6983957219251337,
  "pressure_index": -19.2,
  "raw": {
    "metrics": {
      "average_turns": 46.84,
      "player_deaths": 7,
      "runs": 50,
      "total_bonus_attacks_triggered": 652,
      "total_kills_by_faction": {
        "Orc": 7,
        "Player": 237
      },
      "total_kills_by_source": {
        "MONSTERS": 7,
        "PLAYER": 237
      },
      "total_monster_attacks": 910,
      "total_monster_hits": 317,
      "total_plague_infections": 0,
      "total_player_attacks": 1870,
      "total_player_hits": 1306,
      "total_portals_used": 0,
      "total_reanimations": 0,
      "total_surprise_attacks": 244
    },
    "player_bot": "tactical_fighter",
    "runs": 50,
    "scenario_id": "orc_swarm_brutal_baseline",
    "turn_limit": 100
  },
  "runs": 50,
  "scenario_id": "orc_swarm_brutal_baseline"
}
```

</details>

<details><summary>orc_swarm_brutal_speed_full</summary>

```json
{
  "_source_path": "/Users/rafehatfield/development/rlike/reports/metrics/orc_swarm_brutal_speed_full_metrics.json",
  "bonus_attacks_per_run": 15.88,
  "death_rate": 0.0,
  "depth": null,
  "family": "orc_swarm",
  "monster_attacks_per_run": 14.28,
  "monster_hit_rate": 0.33753501400560226,
  "player_attacks_per_run": 36.02,
  "player_hit_rate": 0.742365352581899,
  "pressure_index": -21.740000000000002,
  "raw": {
    "metrics": {
      "average_turns": 50.0,
      "player_deaths": 0,
      "runs": 50,
      "total_bonus_attacks_triggered": 794,
      "total_kills_by_faction": {
        "Player": 250
      },
      "total_kills_by_source": {
        "PLAYER": 250
      },
      "total_monster_attacks": 714,
      "total_monster_hits": 241,
      "total_plague_infections": 0,
      "total_player_attacks": 1801,
      "total_player_hits": 1337,
      "total_portals_used": 0,
      "total_reanimations": 0,
      "total_surprise_attacks": 250
    },
    "player_bot": "tactical_fighter",
    "runs": 50,
    "scenario_id": "orc_swarm_brutal_speed_full",
    "turn_limit": 100
  },
  "runs": 50,
  "scenario_id": "orc_swarm_brutal_speed_full"
}
```

</details>

<details><summary>orc_swarm_speed_full</summary>

```json
{
  "_source_path": "/Users/rafehatfield/development/rlike/reports/metrics/orc_swarm_speed_full_metrics.json",
  "bonus_attacks_per_run": 9.42,
  "death_rate": 0.02,
  "depth": null,
  "family": "orc_swarm",
  "monster_attacks_per_run": 8.24,
  "monster_hit_rate": 0.3179611650485437,
  "player_attacks_per_run": 21.22,
  "player_hit_rate": 0.7426955702167767,
  "pressure_index": -12.979999999999999,
  "raw": {
    "metrics": {
      "average_turns": 49.3,
      "player_deaths": 1,
      "runs": 50,
      "total_bonus_attacks_triggered": 471,
      "total_kills_by_faction": {
        "Orc": 1,
        "Player": 148
      },
      "total_kills_by_source": {
        "MONSTERS": 1,
        "PLAYER": 148
      },
      "total_monster_attacks": 412,
      "total_monster_hits": 131,
      "total_plague_infections": 0,
      "total_player_attacks": 1061,
      "total_player_hits": 788,
      "total_portals_used": 0,
      "total_reanimations": 0,
      "total_surprise_attacks": 149
    },
    "player_bot": "tactical_fighter",
    "runs": 50,
    "scenario_id": "orc_swarm_speed_full",
    "turn_limit": 100
  },
  "runs": 50,
  "scenario_id": "orc_swarm_speed_full"
}
```

</details>

<details><summary>orc_swarm_tight</summary>

```json
{
  "_source_path": "/Users/rafehatfield/development/rlike/reports/metrics/orc_swarm_tight_metrics.json",
  "bonus_attacks_per_run": 4.04,
  "death_rate": 0.24,
  "depth": null,
  "family": "orc_swarm",
  "monster_attacks_per_run": 14.34,
  "monster_hit_rate": 0.4630404463040446,
  "player_attacks_per_run": 21.88,
  "player_hit_rate": 0.7029250457038391,
  "pressure_index": -7.539999999999999,
  "raw": {
    "metrics": {
      "average_turns": 49.98,
      "player_deaths": 12,
      "runs": 50,
      "total_bonus_attacks_triggered": 202,
      "total_kills_by_faction": {
        "Orc_Chieftain": 2,
        "Orc_Veteran": 10,
        "Player": 131
      },
      "total_kills_by_source": {
        "MONSTERS": 12,
        "PLAYER": 131
      },
      "total_monster_attacks": 717,
      "total_monster_hits": 332,
      "total_plague_infections": 0,
      "total_player_attacks": 1094,
      "total_player_hits": 769,
      "total_portals_used": 0,
      "total_reanimations": 0,
      "total_surprise_attacks": 143
    },
    "player_bot": "tactical_fighter",
    "runs": 50,
    "scenario_id": "orc_swarm_tight",
    "turn_limit": 120
  },
  "runs": 50,
  "scenario_id": "orc_swarm_tight"
}
```

</details>

<details><summary>plague_arena</summary>

```json
{
  "_source_path": "/Users/rafehatfield/development/rlike/reports/metrics/plague_arena_metrics.json",
  "bonus_attacks_per_run": 11.93,
  "death_rate": 0.38,
  "depth": null,
  "family": "plague_arena",
  "monster_attacks_per_run": 23.17,
  "monster_hit_rate": 0.24341821320673285,
  "player_attacks_per_run": 19.24,
  "player_hit_rate": 0.8357588357588358,
  "pressure_index": 3.9300000000000033,
  "raw": {
    "metrics": {
      "average_turns": 172.48,
      "player_deaths": 38,
      "runs": 100,
      "total_bonus_attacks_triggered": 1193,
      "total_kills_by_faction": {
        "Plague_Zombie": 38,
        "Player": 251
      },
      "total_kills_by_source": {
        "MONSTERS": 38,
        "PLAYER": 251
      },
      "total_monster_attacks": 2317,
      "total_monster_hits": 564,
      "total_plague_infections": 75,
      "total_player_attacks": 1924,
      "total_player_hits": 1608,
      "total_portals_used": 0,
      "total_reanimations": 0,
      "total_surprise_attacks": 289
    },
    "player_bot": "tactical_fighter",
    "runs": 100,
    "scenario_id": "plague_arena",
    "turn_limit": 500
  },
  "runs": 100,
  "scenario_id": "plague_arena"
}
```

</details>

<details><summary>zombie_horde</summary>

```json
{
  "_source_path": "/Users/rafehatfield/development/rlike/reports/metrics/zombie_horde_metrics.json",
  "bonus_attacks_per_run": 11.5,
  "death_rate": 0.14,
  "depth": null,
  "family": "zombie_horde",
  "monster_attacks_per_run": 22.84,
  "monster_hit_rate": 0.2084063047285464,
  "player_attacks_per_run": 20.94,
  "player_hit_rate": 0.8500477554918816,
  "pressure_index": 1.8999999999999986,
  "raw": {
    "metrics": {
      "average_turns": 55.72,
      "player_deaths": 7,
      "runs": 50,
      "total_bonus_attacks_triggered": 575,
      "total_kills_by_faction": {
        "Player": 239,
        "Zombie": 7
      },
      "total_kills_by_source": {
        "MONSTERS": 7,
        "PLAYER": 239
      },
      "total_monster_attacks": 1142,
      "total_monster_hits": 238,
      "total_plague_infections": 0,
      "total_player_attacks": 1047,
      "total_player_hits": 890,
      "total_portals_used": 0,
      "total_reanimations": 0,
      "total_surprise_attacks": 246
    },
    "player_bot": "tactical_fighter",
    "runs": 50,
    "scenario_id": "zombie_horde",
    "turn_limit": 120
  },
  "runs": 50,
  "scenario_id": "zombie_horde"
}
```

</details>
