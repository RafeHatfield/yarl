# Difficulty Curve Dashboard
_Updated: 2025-12-13_

[Eco Balance Report](reports/eco_balance_report.md)

## Overview
- Scenarios: 18
- Metrics source: `/Users/rafehatfield/development/rlike/reports/metrics`
- Graphs: `/Users/rafehatfield/development/rlike/reports/graphs`

## Summary Table

| scenario | family | depth | runs | death% | player_hit% | monster_hit% | bonus/run | pressure_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| backstab_training | backstab_training | 5 | 100 | 1.0% | 68.0% | 47.0% | 5.62 | -8.08 |
| depth1_orc_easy | depth1_orc | 1 | 30 | 0.0% | 66.7% | 36.6% | 5.70 | -8.20 |
| depth2_orc_baseline | depth2_orc | 2 | 40 | 5.0% | 68.0% | 37.5% | 8.18 | -11.85 |
| depth3_orc_brutal | depth3_orc | 3 | 50 | 12.0% | 70.9% | 38.8% | 10.08 | -14.56 |
| depth4_plague | depth4_plague | 4 | 50 | 20.0% | 83.0% | 35.4% | 11.04 | 3.36 |
| depth5_zombie | depth5_zombie | 5 | 50 | 46.0% | 83.9% | 36.7% | 13.14 | 14.72 |
| dueling_pit | dueling_pit | 5 | 50 | 0.0% | 69.2% | 38.4% | 2.70 | -3.92 |
| dueling_pit_slow_zombie_baseline | dueling_pit | 5 | 50 | 0.0% | 83.5% | 24.7% | 3.50 | 1.16 |
| dueling_pit_slow_zombie_speed_full | dueling_pit | 5 | 50 | 0.0% | 87.7% | 22.1% | 2.20 | -3.66 |
| dueling_pit_speed_full | dueling_pit | 5 | 50 | 0.0% | 72.3% | 34.7% | 3.38 | -4.66 |
| dueling_pit_speed_light | dueling_pit | 5 | 50 | 0.0% | 77.0% | 36.2% | 2.76 | -3.92 |
| orc_swarm_baseline | orc_swarm | 5 | 50 | 12.0% | 71.5% | 40.4% | 10.30 | -14.78 |
| orc_swarm_brutal_baseline | orc_swarm | 5 | 50 | 34.0% | 70.4% | 38.3% | 11.98 | -17.14 |
| orc_swarm_brutal_speed_full | orc_swarm | 5 | 50 | 8.0% | 74.5% | 36.9% | 16.24 | -21.82 |
| orc_swarm_speed_full | orc_swarm | 5 | 50 | 0.0% | 72.5% | 31.8% | 10.20 | -13.68 |
| orc_swarm_tight | orc_swarm | 5 | 50 | 28.0% | 67.3% | 47.7% | 4.04 | -7.22 |
| plague_arena | plague_arena | 8 | 100 | 32.0% | 83.5% | 25.6% | 11.93 | 3.35 |
| zombie_horde | zombie_horde | 5 | 50 | 10.0% | 84.8% | 20.2% | 11.96 | 1.60 |

## Graphs

![player_hit_rate_vs_depth.png](graphs/player_hit_rate_vs_depth.png)

![monster_hit_rate_vs_depth.png](graphs/monster_hit_rate_vs_depth.png)

![death_rate_vs_depth.png](graphs/death_rate_vs_depth.png)

![bonus_attacks_per_run_vs_depth.png](graphs/bonus_attacks_per_run_vs_depth.png)

![pressure_index_vs_depth.png](graphs/pressure_index_vs_depth.png)

![difficulty_curve_overview.png](graphs/difficulty_curve_overview.png)

## Family Insights
- **backstab_training** — deaths 1–1%, player hit ~68%, monster hit ~47%, bonus/run ~6, pressure index ~-8.1 (player drives tempo).
- **depth1_orc** — deaths 0–0%, player hit ~67%, monster hit ~37%, bonus/run ~6, pressure index ~-8.2 (player drives tempo).
- **depth2_orc** — deaths 5–5%, player hit ~68%, monster hit ~38%, bonus/run ~8, pressure index ~-11.8 (player drives tempo).
- **depth3_orc** — deaths 12–12%, player hit ~71%, monster hit ~39%, bonus/run ~10, pressure index ~-14.6 (player drives tempo).
- **depth4_plague** — deaths 20–20%, player hit ~83%, monster hit ~35%, bonus/run ~11, pressure index ~3.4 (balanced tempo).
- **depth5_zombie** — deaths 46–46%, player hit ~84%, monster hit ~37%, bonus/run ~13, pressure index ~14.7 (monsters drive tempo).
- **dueling_pit** — deaths 0–0%, player hit ~78%, monster hit ~31%, bonus/run ~3, pressure index ~-3.0 (balanced tempo).
- **orc_swarm** — deaths 0–34%, player hit ~71%, monster hit ~39%, bonus/run ~11, pressure index ~-14.9 (player drives tempo).
- **plague_arena** — deaths 32–32%, player hit ~83%, monster hit ~26%, bonus/run ~12, pressure index ~3.4 (balanced tempo).
- **zombie_horde** — deaths 10–10%, player hit ~85%, monster hit ~20%, bonus/run ~12, pressure index ~1.6 (balanced tempo).

## Scenario Breakdown
### backstab_training
- family: backstab_training
- depth: 5
- runs: 100
- death_rate: 0.010
- player_hit_rate: 0.680
- monster_hit_rate: 0.470
- bonus_attacks_per_run: 5.620
- pressure_index: -8.080

### depth1_orc_easy
- family: depth1_orc
- depth: 1
- runs: 30
- death_rate: 0.000
- player_hit_rate: 0.667
- monster_hit_rate: 0.366
- bonus_attacks_per_run: 5.700
- pressure_index: -8.200

### depth2_orc_baseline
- family: depth2_orc
- depth: 2
- runs: 40
- death_rate: 0.050
- player_hit_rate: 0.680
- monster_hit_rate: 0.375
- bonus_attacks_per_run: 8.175
- pressure_index: -11.850

### depth3_orc_brutal
- family: depth3_orc
- depth: 3
- runs: 50
- death_rate: 0.120
- player_hit_rate: 0.709
- monster_hit_rate: 0.388
- bonus_attacks_per_run: 10.080
- pressure_index: -14.560

### depth4_plague
- family: depth4_plague
- depth: 4
- runs: 50
- death_rate: 0.200
- player_hit_rate: 0.830
- monster_hit_rate: 0.354
- bonus_attacks_per_run: 11.040
- pressure_index: 3.360

### depth5_zombie
- family: depth5_zombie
- depth: 5
- runs: 50
- death_rate: 0.460
- player_hit_rate: 0.839
- monster_hit_rate: 0.367
- bonus_attacks_per_run: 13.140
- pressure_index: 14.720

### dueling_pit
- family: dueling_pit
- depth: 5
- runs: 50
- death_rate: 0.000
- player_hit_rate: 0.692
- monster_hit_rate: 0.384
- bonus_attacks_per_run: 2.700
- pressure_index: -3.920

### dueling_pit_slow_zombie_baseline
- family: dueling_pit
- depth: 5
- runs: 50
- death_rate: 0.000
- player_hit_rate: 0.835
- monster_hit_rate: 0.247
- bonus_attacks_per_run: 3.500
- pressure_index: 1.160

### dueling_pit_slow_zombie_speed_full
- family: dueling_pit
- depth: 5
- runs: 50
- death_rate: 0.000
- player_hit_rate: 0.877
- monster_hit_rate: 0.221
- bonus_attacks_per_run: 2.200
- pressure_index: -3.660

### dueling_pit_speed_full
- family: dueling_pit
- depth: 5
- runs: 50
- death_rate: 0.000
- player_hit_rate: 0.723
- monster_hit_rate: 0.347
- bonus_attacks_per_run: 3.380
- pressure_index: -4.660

### dueling_pit_speed_light
- family: dueling_pit
- depth: 5
- runs: 50
- death_rate: 0.000
- player_hit_rate: 0.770
- monster_hit_rate: 0.362
- bonus_attacks_per_run: 2.760
- pressure_index: -3.920

### orc_swarm_baseline
- family: orc_swarm
- depth: 5
- runs: 50
- death_rate: 0.120
- player_hit_rate: 0.715
- monster_hit_rate: 0.404
- bonus_attacks_per_run: 10.300
- pressure_index: -14.780

### orc_swarm_brutal_baseline
- family: orc_swarm
- depth: 5
- runs: 50
- death_rate: 0.340
- player_hit_rate: 0.704
- monster_hit_rate: 0.383
- bonus_attacks_per_run: 11.980
- pressure_index: -17.140

### orc_swarm_brutal_speed_full
- family: orc_swarm
- depth: 5
- runs: 50
- death_rate: 0.080
- player_hit_rate: 0.745
- monster_hit_rate: 0.369
- bonus_attacks_per_run: 16.240
- pressure_index: -21.820

### orc_swarm_speed_full
- family: orc_swarm
- depth: 5
- runs: 50
- death_rate: 0.000
- player_hit_rate: 0.725
- monster_hit_rate: 0.318
- bonus_attacks_per_run: 10.200
- pressure_index: -13.680

### orc_swarm_tight
- family: orc_swarm
- depth: 5
- runs: 50
- death_rate: 0.280
- player_hit_rate: 0.673
- monster_hit_rate: 0.477
- bonus_attacks_per_run: 4.040
- pressure_index: -7.220

### plague_arena
- family: plague_arena
- depth: 8
- runs: 100
- death_rate: 0.320
- player_hit_rate: 0.835
- monster_hit_rate: 0.256
- bonus_attacks_per_run: 11.930
- pressure_index: 3.350

### zombie_horde
- family: zombie_horde
- depth: 5
- runs: 50
- death_rate: 0.100
- player_hit_rate: 0.848
- monster_hit_rate: 0.202
- bonus_attacks_per_run: 11.960
- pressure_index: 1.600

## Raw Metrics (appendix)

<details><summary>backstab_training</summary>

```json
{
  "_source_path": "/Users/rafehatfield/development/rlike/reports/metrics/backstab_training_metrics.json",
  "bonus_attacks_per_run": 5.62,
  "death_rate": 0.01,
  "depth": 5,
  "family": "backstab_training",
  "monster_attacks_per_run": 7.87,
  "monster_hit_rate": 0.4701397712833545,
  "player_attacks_per_run": 15.95,
  "player_hit_rate": 0.6796238244514107,
  "pressure_index": -8.079999999999998,
  "raw": {
    "depth": 5,
    "metrics": {
      "average_turns": 24.93,
      "depth": 5,
      "player_deaths": 1,
      "runs": 100,
      "total_bonus_attacks_triggered": 562,
      "total_kills_by_faction": {
        "Orc": 1,
        "Player": 199
      },
      "total_kills_by_source": {
        "MONSTERS": 1,
        "PLAYER": 199
      },
      "total_monster_attacks": 787,
      "total_monster_hits": 370,
      "total_plague_infections": 0,
      "total_player_attacks": 1595,
      "total_player_hits": 1084,
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

<details><summary>depth1_orc_easy</summary>

```json
{
  "_source_path": "/Users/rafehatfield/development/rlike/reports/metrics/depth1_orc_easy_metrics.json",
  "bonus_attacks_per_run": 5.7,
  "death_rate": 0.0,
  "depth": 1,
  "family": "depth1_orc",
  "monster_attacks_per_run": 7.833333333333333,
  "monster_hit_rate": 0.3659574468085106,
  "player_attacks_per_run": 16.033333333333335,
  "player_hit_rate": 0.6673596673596673,
  "pressure_index": -8.200000000000003,
  "raw": {
    "depth": 1,
    "metrics": {
      "average_turns": 40.0,
      "depth": 1,
      "player_deaths": 0,
      "runs": 30,
      "total_bonus_attacks_triggered": 171,
      "total_kills_by_faction": {
        "Player": 60
      },
      "total_kills_by_source": {
        "PLAYER": 60
      },
      "total_monster_attacks": 235,
      "total_monster_hits": 86,
      "total_plague_infections": 0,
      "total_player_attacks": 481,
      "total_player_hits": 321,
      "total_portals_used": 0,
      "total_reanimations": 0,
      "total_surprise_attacks": 60
    },
    "player_bot": "tactical_fighter",
    "runs": 30,
    "scenario_id": "depth1_orc_easy",
    "turn_limit": 80
  },
  "runs": 30,
  "scenario_id": "depth1_orc_easy"
}
```

</details>

<details><summary>depth2_orc_baseline</summary>

```json
{
  "_source_path": "/Users/rafehatfield/development/rlike/reports/metrics/depth2_orc_baseline_metrics.json",
  "bonus_attacks_per_run": 8.175,
  "death_rate": 0.05,
  "depth": 2,
  "family": "depth2_orc",
  "monster_attacks_per_run": 11.725,
  "monster_hit_rate": 0.3752665245202559,
  "player_attacks_per_run": 23.575,
  "player_hit_rate": 0.679745493107105,
  "pressure_index": -11.85,
  "raw": {
    "depth": 2,
    "metrics": {
      "average_turns": 48.7,
      "depth": 2,
      "player_deaths": 2,
      "runs": 40,
      "total_bonus_attacks_triggered": 327,
      "total_kills_by_faction": {
        "Orc": 2,
        "Player": 118
      },
      "total_kills_by_source": {
        "MONSTERS": 2,
        "PLAYER": 118
      },
      "total_monster_attacks": 469,
      "total_monster_hits": 176,
      "total_plague_infections": 0,
      "total_player_attacks": 943,
      "total_player_hits": 641,
      "total_portals_used": 0,
      "total_reanimations": 0,
      "total_surprise_attacks": 120
    },
    "player_bot": "tactical_fighter",
    "runs": 40,
    "scenario_id": "depth2_orc_baseline",
    "turn_limit": 100
  },
  "runs": 40,
  "scenario_id": "depth2_orc_baseline"
}
```

</details>

<details><summary>depth3_orc_brutal</summary>

```json
{
  "_source_path": "/Users/rafehatfield/development/rlike/reports/metrics/depth3_orc_brutal_metrics.json",
  "bonus_attacks_per_run": 10.08,
  "death_rate": 0.12,
  "depth": 3,
  "family": "depth3_orc",
  "monster_attacks_per_run": 14.6,
  "monster_hit_rate": 0.38767123287671235,
  "player_attacks_per_run": 29.16,
  "player_hit_rate": 0.7091906721536351,
  "pressure_index": -14.56,
  "raw": {
    "depth": 3,
    "metrics": {
      "average_turns": 51.06,
      "depth": 3,
      "player_deaths": 6,
      "runs": 50,
      "total_bonus_attacks_triggered": 504,
      "total_kills_by_faction": {
        "Orc": 6,
        "Player": 190
      },
      "total_kills_by_source": {
        "MONSTERS": 6,
        "PLAYER": 190
      },
      "total_monster_attacks": 730,
      "total_monster_hits": 283,
      "total_plague_infections": 0,
      "total_player_attacks": 1458,
      "total_player_hits": 1034,
      "total_portals_used": 0,
      "total_reanimations": 0,
      "total_surprise_attacks": 196
    },
    "player_bot": "tactical_fighter",
    "runs": 50,
    "scenario_id": "depth3_orc_brutal",
    "turn_limit": 110
  },
  "runs": 50,
  "scenario_id": "depth3_orc_brutal"
}
```

</details>

<details><summary>depth4_plague</summary>

```json
{
  "_source_path": "/Users/rafehatfield/development/rlike/reports/metrics/depth4_plague_metrics.json",
  "bonus_attacks_per_run": 11.04,
  "death_rate": 0.2,
  "depth": 4,
  "family": "depth4_plague",
  "monster_attacks_per_run": 26.7,
  "monster_hit_rate": 0.3543071161048689,
  "player_attacks_per_run": 23.34,
  "player_hit_rate": 0.8303341902313625,
  "pressure_index": 3.3599999999999994,
  "raw": {
    "depth": 4,
    "metrics": {
      "average_turns": 61.48,
      "depth": 4,
      "player_deaths": 10,
      "runs": 50,
      "total_bonus_attacks_triggered": 552,
      "total_kills_by_faction": {
        "Plague_Zombie": 12,
        "Player": 173,
        "Revenant Plague_Zombie": 1,
        "Revenant Revenant Zombie": 1,
        "Revenant Zombie": 6,
        "Zombie": 14
      },
      "total_kills_by_source": {
        "MONSTERS": 34,
        "PLAYER": 173
      },
      "total_monster_attacks": 1335,
      "total_monster_hits": 473,
      "total_plague_infections": 50,
      "total_player_attacks": 1167,
      "total_player_hits": 969,
      "total_portals_used": 0,
      "total_reanimations": 23,
      "total_surprise_attacks": 181
    },
    "player_bot": "tactical_fighter",
    "runs": 50,
    "scenario_id": "depth4_plague",
    "turn_limit": 140
  },
  "runs": 50,
  "scenario_id": "depth4_plague"
}
```

</details>

<details><summary>depth5_zombie</summary>

```json
{
  "_source_path": "/Users/rafehatfield/development/rlike/reports/metrics/depth5_zombie_metrics.json",
  "bonus_attacks_per_run": 13.14,
  "death_rate": 0.46,
  "depth": 5,
  "family": "depth5_zombie",
  "monster_attacks_per_run": 39.32,
  "monster_hit_rate": 0.3672431332655137,
  "player_attacks_per_run": 24.6,
  "player_hit_rate": 0.8390243902439024,
  "pressure_index": 14.719999999999999,
  "raw": {
    "depth": 5,
    "metrics": {
      "average_turns": 55.92,
      "depth": 5,
      "player_deaths": 23,
      "runs": 50,
      "total_bonus_attacks_triggered": 657,
      "total_kills_by_faction": {
        "Player": 248,
        "Zombie": 81
      },
      "total_kills_by_source": {
        "MONSTERS": 81,
        "PLAYER": 248
      },
      "total_monster_attacks": 1966,
      "total_monster_hits": 722,
      "total_plague_infections": 0,
      "total_player_attacks": 1230,
      "total_player_hits": 1032,
      "total_portals_used": 0,
      "total_reanimations": 0,
      "total_surprise_attacks": 314
    },
    "player_bot": "tactical_fighter",
    "runs": 50,
    "scenario_id": "depth5_zombie",
    "turn_limit": 150
  },
  "runs": 50,
  "scenario_id": "depth5_zombie"
}
```

</details>

<details><summary>dueling_pit</summary>

```json
{
  "_source_path": "/Users/rafehatfield/development/rlike/reports/metrics/dueling_pit_metrics.json",
  "bonus_attacks_per_run": 2.7,
  "death_rate": 0.0,
  "depth": 5,
  "family": "dueling_pit",
  "monster_attacks_per_run": 4.06,
  "monster_hit_rate": 0.3842364532019704,
  "player_attacks_per_run": 7.98,
  "player_hit_rate": 0.6917293233082706,
  "pressure_index": -3.920000000000001,
  "raw": {
    "depth": 5,
    "metrics": {
      "average_turns": 50.0,
      "depth": 5,
      "player_deaths": 0,
      "runs": 50,
      "total_bonus_attacks_triggered": 135,
      "total_kills_by_faction": {
        "Player": 50
      },
      "total_kills_by_source": {
        "PLAYER": 50
      },
      "total_monster_attacks": 203,
      "total_monster_hits": 78,
      "total_plague_infections": 0,
      "total_player_attacks": 399,
      "total_player_hits": 276,
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
  "bonus_attacks_per_run": 3.5,
  "death_rate": 0.0,
  "depth": 5,
  "family": "dueling_pit",
  "monster_attacks_per_run": 6.72,
  "monster_hit_rate": 0.24702380952380953,
  "player_attacks_per_run": 5.56,
  "player_hit_rate": 0.8345323741007195,
  "pressure_index": 1.1600000000000001,
  "raw": {
    "depth": 5,
    "metrics": {
      "average_turns": 50.0,
      "depth": 5,
      "player_deaths": 0,
      "runs": 50,
      "total_bonus_attacks_triggered": 175,
      "total_kills_by_faction": {
        "Player": 50
      },
      "total_kills_by_source": {
        "PLAYER": 50
      },
      "total_monster_attacks": 336,
      "total_monster_hits": 83,
      "total_plague_infections": 0,
      "total_player_attacks": 278,
      "total_player_hits": 232,
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
  "bonus_attacks_per_run": 2.2,
  "death_rate": 0.0,
  "depth": 5,
  "family": "dueling_pit",
  "monster_attacks_per_run": 1.54,
  "monster_hit_rate": 0.22077922077922077,
  "player_attacks_per_run": 5.2,
  "player_hit_rate": 0.8769230769230769,
  "pressure_index": -3.66,
  "raw": {
    "depth": 5,
    "metrics": {
      "average_turns": 50.0,
      "depth": 5,
      "player_deaths": 0,
      "runs": 50,
      "total_bonus_attacks_triggered": 110,
      "total_kills_by_faction": {
        "Player": 50
      },
      "total_kills_by_source": {
        "PLAYER": 50
      },
      "total_monster_attacks": 77,
      "total_monster_hits": 17,
      "total_plague_infections": 0,
      "total_player_attacks": 260,
      "total_player_hits": 228,
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
  "depth": 5,
  "family": "dueling_pit",
  "monster_attacks_per_run": 3.0,
  "monster_hit_rate": 0.3466666666666667,
  "player_attacks_per_run": 7.66,
  "player_hit_rate": 0.7232375979112271,
  "pressure_index": -4.66,
  "raw": {
    "depth": 5,
    "metrics": {
      "average_turns": 50.0,
      "depth": 5,
      "player_deaths": 0,
      "runs": 50,
      "total_bonus_attacks_triggered": 169,
      "total_kills_by_faction": {
        "Player": 50
      },
      "total_kills_by_source": {
        "PLAYER": 50
      },
      "total_monster_attacks": 150,
      "total_monster_hits": 52,
      "total_plague_infections": 0,
      "total_player_attacks": 383,
      "total_player_hits": 277,
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
  "bonus_attacks_per_run": 2.76,
  "death_rate": 0.0,
  "depth": 5,
  "family": "dueling_pit",
  "monster_attacks_per_run": 3.2,
  "monster_hit_rate": 0.3625,
  "player_attacks_per_run": 7.12,
  "player_hit_rate": 0.7696629213483146,
  "pressure_index": -3.92,
  "raw": {
    "depth": 5,
    "metrics": {
      "average_turns": 50.0,
      "depth": 5,
      "player_deaths": 0,
      "runs": 50,
      "total_bonus_attacks_triggered": 138,
      "total_kills_by_faction": {
        "Player": 50
      },
      "total_kills_by_source": {
        "PLAYER": 50
      },
      "total_monster_attacks": 160,
      "total_monster_hits": 58,
      "total_plague_infections": 0,
      "total_player_attacks": 356,
      "total_player_hits": 274,
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
  "bonus_attacks_per_run": 10.3,
  "death_rate": 0.12,
  "depth": 5,
  "family": "orc_swarm",
  "monster_attacks_per_run": 14.5,
  "monster_hit_rate": 0.40413793103448276,
  "player_attacks_per_run": 29.28,
  "player_hit_rate": 0.7151639344262295,
  "pressure_index": -14.780000000000001,
  "raw": {
    "depth": 5,
    "metrics": {
      "average_turns": 46.82,
      "depth": 5,
      "player_deaths": 6,
      "runs": 50,
      "total_bonus_attacks_triggered": 515,
      "total_kills_by_faction": {
        "Orc": 6,
        "Player": 192
      },
      "total_kills_by_source": {
        "MONSTERS": 6,
        "PLAYER": 192
      },
      "total_monster_attacks": 725,
      "total_monster_hits": 293,
      "total_plague_infections": 0,
      "total_player_attacks": 1464,
      "total_player_hits": 1047,
      "total_portals_used": 0,
      "total_reanimations": 0,
      "total_surprise_attacks": 198
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
  "bonus_attacks_per_run": 11.98,
  "death_rate": 0.34,
  "depth": 5,
  "family": "orc_swarm",
  "monster_attacks_per_run": 17.64,
  "monster_hit_rate": 0.3832199546485261,
  "player_attacks_per_run": 34.78,
  "player_hit_rate": 0.7038527889591719,
  "pressure_index": -17.14,
  "raw": {
    "depth": 5,
    "metrics": {
      "average_turns": 42.26,
      "depth": 5,
      "player_deaths": 17,
      "runs": 50,
      "total_bonus_attacks_triggered": 599,
      "total_kills_by_faction": {
        "Orc": 17,
        "Player": 219
      },
      "total_kills_by_source": {
        "MONSTERS": 17,
        "PLAYER": 219
      },
      "total_monster_attacks": 882,
      "total_monster_hits": 338,
      "total_plague_infections": 0,
      "total_player_attacks": 1739,
      "total_player_hits": 1224,
      "total_portals_used": 0,
      "total_reanimations": 0,
      "total_surprise_attacks": 236
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
  "bonus_attacks_per_run": 16.24,
  "death_rate": 0.08,
  "depth": 5,
  "family": "orc_swarm",
  "monster_attacks_per_run": 14.32,
  "monster_hit_rate": 0.3687150837988827,
  "player_attacks_per_run": 36.14,
  "player_hit_rate": 0.7448810182623132,
  "pressure_index": -21.82,
  "raw": {
    "depth": 5,
    "metrics": {
      "average_turns": 48.24,
      "depth": 5,
      "player_deaths": 4,
      "runs": 50,
      "total_bonus_attacks_triggered": 812,
      "total_kills_by_faction": {
        "Orc": 4,
        "Player": 245
      },
      "total_kills_by_source": {
        "MONSTERS": 4,
        "PLAYER": 245
      },
      "total_monster_attacks": 716,
      "total_monster_hits": 264,
      "total_plague_infections": 0,
      "total_player_attacks": 1807,
      "total_player_hits": 1346,
      "total_portals_used": 0,
      "total_reanimations": 0,
      "total_surprise_attacks": 249
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
  "bonus_attacks_per_run": 10.2,
  "death_rate": 0.0,
  "depth": 5,
  "family": "orc_swarm",
  "monster_attacks_per_run": 8.94,
  "monster_hit_rate": 0.31767337807606266,
  "player_attacks_per_run": 22.62,
  "player_hit_rate": 0.7250221043324492,
  "pressure_index": -13.680000000000001,
  "raw": {
    "depth": 5,
    "metrics": {
      "average_turns": 50.0,
      "depth": 5,
      "player_deaths": 0,
      "runs": 50,
      "total_bonus_attacks_triggered": 510,
      "total_kills_by_faction": {
        "Player": 150
      },
      "total_kills_by_source": {
        "PLAYER": 150
      },
      "total_monster_attacks": 447,
      "total_monster_hits": 142,
      "total_plague_infections": 0,
      "total_player_attacks": 1131,
      "total_player_hits": 820,
      "total_portals_used": 0,
      "total_reanimations": 0,
      "total_surprise_attacks": 150
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
  "death_rate": 0.28,
  "depth": 5,
  "family": "orc_swarm",
  "monster_attacks_per_run": 14.64,
  "monster_hit_rate": 0.476775956284153,
  "player_attacks_per_run": 21.86,
  "player_hit_rate": 0.6733760292772186,
  "pressure_index": -7.219999999999999,
  "raw": {
    "depth": 5,
    "metrics": {
      "average_turns": 47.92,
      "depth": 5,
      "player_deaths": 14,
      "runs": 50,
      "total_bonus_attacks_triggered": 202,
      "total_kills_by_faction": {
        "Orc_Chieftain": 2,
        "Orc_Veteran": 12,
        "Player": 127
      },
      "total_kills_by_source": {
        "MONSTERS": 14,
        "PLAYER": 127
      },
      "total_monster_attacks": 732,
      "total_monster_hits": 349,
      "total_plague_infections": 0,
      "total_player_attacks": 1093,
      "total_player_hits": 736,
      "total_portals_used": 0,
      "total_reanimations": 0,
      "total_surprise_attacks": 141
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
  "death_rate": 0.32,
  "depth": 8,
  "family": "plague_arena",
  "monster_attacks_per_run": 22.55,
  "monster_hit_rate": 0.25587583148558757,
  "player_attacks_per_run": 19.2,
  "player_hit_rate": 0.8348958333333333,
  "pressure_index": 3.3500000000000014,
  "raw": {
    "depth": 8,
    "metrics": {
      "average_turns": 184.51,
      "depth": 8,
      "player_deaths": 32,
      "runs": 100,
      "total_bonus_attacks_triggered": 1193,
      "total_kills_by_faction": {
        "Plague_Zombie": 33,
        "Player": 258
      },
      "total_kills_by_source": {
        "MONSTERS": 33,
        "PLAYER": 258
      },
      "total_monster_attacks": 2255,
      "total_monster_hits": 577,
      "total_plague_infections": 76,
      "total_player_attacks": 1920,
      "total_player_hits": 1603,
      "total_portals_used": 0,
      "total_reanimations": 2,
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
  "bonus_attacks_per_run": 11.96,
  "death_rate": 0.1,
  "depth": 5,
  "family": "zombie_horde",
  "monster_attacks_per_run": 23.08,
  "monster_hit_rate": 0.2019064124783362,
  "player_attacks_per_run": 21.48,
  "player_hit_rate": 0.8482309124767226,
  "pressure_index": 1.5999999999999979,
  "raw": {
    "depth": 5,
    "metrics": {
      "average_turns": 57.0,
      "depth": 5,
      "player_deaths": 5,
      "runs": 50,
      "total_bonus_attacks_triggered": 598,
      "total_kills_by_faction": {
        "Player": 242,
        "Zombie": 5
      },
      "total_kills_by_source": {
        "MONSTERS": 5,
        "PLAYER": 242
      },
      "total_monster_attacks": 1154,
      "total_monster_hits": 233,
      "total_plague_infections": 0,
      "total_player_attacks": 1074,
      "total_player_hits": 911,
      "total_portals_used": 0,
      "total_reanimations": 0,
      "total_surprise_attacks": 247
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
