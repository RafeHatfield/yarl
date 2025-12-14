# Difficulty Curve Dashboard
_Updated: 2025-12-14_

[Eco Balance Report](reports/eco_balance_report.md)

## Overview
- Scenarios: 18
- Metrics source: `/Users/rafehatfield/development/rlike/reports/metrics`
- Graphs: `/Users/rafehatfield/development/rlike/reports/graphs`

## Summary Table

| scenario | family | depth | runs | death% | player_hit% | monster_hit% | bonus/run | pressure_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| backstab_training | backstab_training | 5 | 100 | 1.0% | 67.5% | 46.5% | 5.25 | -7.53 |
| depth1_orc_easy | depth1_orc | 1 | 30 | 0.0% | 73.3% | 40.1% | 4.90 | -7.30 |
| depth2_orc_baseline | depth2_orc | 2 | 40 | 2.5% | 68.4% | 36.9% | 8.25 | -11.75 |
| depth3_orc_brutal | depth3_orc | 3 | 50 | 16.0% | 69.6% | 37.7% | 10.54 | -15.36 |
| depth4_plague | depth4_plague | 4 | 50 | 12.0% | 84.3% | 33.2% | 10.16 | 3.34 |
| depth5_zombie | depth5_zombie | 5 | 50 | 50.0% | 85.0% | 35.4% | 13.66 | 15.96 |
| dueling_pit | dueling_pit | 5 | 50 | 0.0% | 71.0% | 35.8% | 2.44 | -3.64 |
| dueling_pit_slow_zombie_baseline | dueling_pit | 5 | 50 | 0.0% | 84.2% | 25.3% | 3.10 | 0.48 |
| dueling_pit_slow_zombie_speed_full | dueling_pit | 5 | 50 | 0.0% | 86.2% | 21.0% | 2.38 | -3.88 |
| dueling_pit_speed_full | dueling_pit | 5 | 50 | 0.0% | 74.4% | 31.9% | 3.14 | -4.28 |
| dueling_pit_speed_light | dueling_pit | 5 | 50 | 0.0% | 66.4% | 37.4% | 3.14 | -4.30 |
| orc_swarm_baseline | orc_swarm | 5 | 50 | 16.0% | 69.6% | 36.3% | 10.58 | -15.18 |
| orc_swarm_brutal_baseline | orc_swarm | 5 | 50 | 26.0% | 69.0% | 36.4% | 13.08 | -18.64 |
| orc_swarm_brutal_speed_full | orc_swarm | 5 | 50 | 2.0% | 71.2% | 33.7% | 17.30 | -23.06 |
| orc_swarm_speed_full | orc_swarm | 5 | 50 | 0.0% | 74.8% | 30.2% | 9.90 | -13.52 |
| orc_swarm_tight | orc_swarm | 5 | 50 | 30.0% | 68.8% | 47.0% | 3.98 | -7.34 |
| plague_arena | plague_arena | 8 | 100 | 35.0% | 84.1% | 26.0% | 11.96 | 3.47 |
| zombie_horde | zombie_horde | 5 | 50 | 10.0% | 83.0% | 21.6% | 12.40 | 1.82 |

## Graphs

![player_hit_rate_vs_depth.png](graphs/player_hit_rate_vs_depth.png)

![monster_hit_rate_vs_depth.png](graphs/monster_hit_rate_vs_depth.png)

![death_rate_vs_depth.png](graphs/death_rate_vs_depth.png)

![bonus_attacks_per_run_vs_depth.png](graphs/bonus_attacks_per_run_vs_depth.png)

![pressure_index_vs_depth.png](graphs/pressure_index_vs_depth.png)

![difficulty_curve_overview.png](graphs/difficulty_curve_overview.png)

## Family Insights
- **backstab_training** — deaths 1–1%, player hit ~67%, monster hit ~46%, bonus/run ~5, pressure index ~-7.5 (player drives tempo).
- **depth1_orc** — deaths 0–0%, player hit ~73%, monster hit ~40%, bonus/run ~5, pressure index ~-7.3 (player drives tempo).
- **depth2_orc** — deaths 2–2%, player hit ~68%, monster hit ~37%, bonus/run ~8, pressure index ~-11.8 (player drives tempo).
- **depth3_orc** — deaths 16–16%, player hit ~70%, monster hit ~38%, bonus/run ~11, pressure index ~-15.4 (player drives tempo).
- **depth4_plague** — deaths 12–12%, player hit ~84%, monster hit ~33%, bonus/run ~10, pressure index ~3.3 (balanced tempo).
- **depth5_zombie** — deaths 50–50%, player hit ~85%, monster hit ~35%, bonus/run ~14, pressure index ~16.0 (monsters drive tempo).
- **dueling_pit** — deaths 0–0%, player hit ~76%, monster hit ~30%, bonus/run ~3, pressure index ~-3.1 (balanced tempo).
- **orc_swarm** — deaths 0–30%, player hit ~71%, monster hit ~37%, bonus/run ~11, pressure index ~-15.5 (player drives tempo).
- **plague_arena** — deaths 35–35%, player hit ~84%, monster hit ~26%, bonus/run ~12, pressure index ~3.5 (balanced tempo).
- **zombie_horde** — deaths 10–10%, player hit ~83%, monster hit ~22%, bonus/run ~12, pressure index ~1.8 (balanced tempo).

## Scenario Breakdown
### backstab_training
- family: backstab_training
- depth: 5
- runs: 100
- death_rate: 0.010
- player_hit_rate: 0.675
- monster_hit_rate: 0.465
- bonus_attacks_per_run: 5.250
- pressure_index: -7.530

### depth1_orc_easy
- family: depth1_orc
- depth: 1
- runs: 30
- death_rate: 0.000
- player_hit_rate: 0.733
- monster_hit_rate: 0.401
- bonus_attacks_per_run: 4.900
- pressure_index: -7.300

### depth2_orc_baseline
- family: depth2_orc
- depth: 2
- runs: 40
- death_rate: 0.025
- player_hit_rate: 0.684
- monster_hit_rate: 0.369
- bonus_attacks_per_run: 8.250
- pressure_index: -11.750

### depth3_orc_brutal
- family: depth3_orc
- depth: 3
- runs: 50
- death_rate: 0.160
- player_hit_rate: 0.696
- monster_hit_rate: 0.377
- bonus_attacks_per_run: 10.540
- pressure_index: -15.360

### depth4_plague
- family: depth4_plague
- depth: 4
- runs: 50
- death_rate: 0.120
- player_hit_rate: 0.843
- monster_hit_rate: 0.332
- bonus_attacks_per_run: 10.160
- pressure_index: 3.340

### depth5_zombie
- family: depth5_zombie
- depth: 5
- runs: 50
- death_rate: 0.500
- player_hit_rate: 0.850
- monster_hit_rate: 0.354
- bonus_attacks_per_run: 13.660
- pressure_index: 15.960

### dueling_pit
- family: dueling_pit
- depth: 5
- runs: 50
- death_rate: 0.000
- player_hit_rate: 0.710
- monster_hit_rate: 0.358
- bonus_attacks_per_run: 2.440
- pressure_index: -3.640

### dueling_pit_slow_zombie_baseline
- family: dueling_pit
- depth: 5
- runs: 50
- death_rate: 0.000
- player_hit_rate: 0.842
- monster_hit_rate: 0.253
- bonus_attacks_per_run: 3.100
- pressure_index: 0.480

### dueling_pit_slow_zombie_speed_full
- family: dueling_pit
- depth: 5
- runs: 50
- death_rate: 0.000
- player_hit_rate: 0.862
- monster_hit_rate: 0.210
- bonus_attacks_per_run: 2.380
- pressure_index: -3.880

### dueling_pit_speed_full
- family: dueling_pit
- depth: 5
- runs: 50
- death_rate: 0.000
- player_hit_rate: 0.744
- monster_hit_rate: 0.319
- bonus_attacks_per_run: 3.140
- pressure_index: -4.280

### dueling_pit_speed_light
- family: dueling_pit
- depth: 5
- runs: 50
- death_rate: 0.000
- player_hit_rate: 0.664
- monster_hit_rate: 0.374
- bonus_attacks_per_run: 3.140
- pressure_index: -4.300

### orc_swarm_baseline
- family: orc_swarm
- depth: 5
- runs: 50
- death_rate: 0.160
- player_hit_rate: 0.696
- monster_hit_rate: 0.363
- bonus_attacks_per_run: 10.580
- pressure_index: -15.180

### orc_swarm_brutal_baseline
- family: orc_swarm
- depth: 5
- runs: 50
- death_rate: 0.260
- player_hit_rate: 0.690
- monster_hit_rate: 0.364
- bonus_attacks_per_run: 13.080
- pressure_index: -18.640

### orc_swarm_brutal_speed_full
- family: orc_swarm
- depth: 5
- runs: 50
- death_rate: 0.020
- player_hit_rate: 0.712
- monster_hit_rate: 0.337
- bonus_attacks_per_run: 17.300
- pressure_index: -23.060

### orc_swarm_speed_full
- family: orc_swarm
- depth: 5
- runs: 50
- death_rate: 0.000
- player_hit_rate: 0.748
- monster_hit_rate: 0.302
- bonus_attacks_per_run: 9.900
- pressure_index: -13.520

### orc_swarm_tight
- family: orc_swarm
- depth: 5
- runs: 50
- death_rate: 0.300
- player_hit_rate: 0.688
- monster_hit_rate: 0.470
- bonus_attacks_per_run: 3.980
- pressure_index: -7.340

### plague_arena
- family: plague_arena
- depth: 8
- runs: 100
- death_rate: 0.350
- player_hit_rate: 0.841
- monster_hit_rate: 0.260
- bonus_attacks_per_run: 11.960
- pressure_index: 3.470

### zombie_horde
- family: zombie_horde
- depth: 5
- runs: 50
- death_rate: 0.100
- player_hit_rate: 0.830
- monster_hit_rate: 0.216
- bonus_attacks_per_run: 12.400
- pressure_index: 1.820

## Raw Metrics (appendix)

<details><summary>backstab_training</summary>

```json
{
  "_source_path": "/Users/rafehatfield/development/rlike/reports/metrics/backstab_training_metrics.json",
  "bonus_attacks_per_run": 5.25,
  "death_rate": 0.01,
  "depth": 5,
  "family": "backstab_training",
  "monster_attacks_per_run": 8.09,
  "monster_hit_rate": 0.4647713226205192,
  "player_attacks_per_run": 15.62,
  "player_hit_rate": 0.674775928297055,
  "pressure_index": -7.529999999999999,
  "raw": {
    "depth": 5,
    "metrics": {
      "average_turns": 24.96,
      "depth": 5,
      "player_deaths": 1,
      "runs": 100,
      "total_bonus_attacks_triggered": 525,
      "total_kills_by_faction": {
        "Orc": 1,
        "Player": 199
      },
      "total_kills_by_source": {
        "MONSTERS": 1,
        "PLAYER": 199
      },
      "total_monster_attacks": 809,
      "total_monster_hits": 376,
      "total_plague_infections": 0,
      "total_player_attacks": 1562,
      "total_player_hits": 1054,
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
  "bonus_attacks_per_run": 4.9,
  "death_rate": 0.0,
  "depth": 1,
  "family": "depth1_orc",
  "monster_attacks_per_run": 7.066666666666666,
  "monster_hit_rate": 0.4009433962264151,
  "player_attacks_per_run": 14.366666666666667,
  "player_hit_rate": 0.7331786542923434,
  "pressure_index": -7.300000000000001,
  "raw": {
    "depth": 1,
    "metrics": {
      "average_turns": 40.0,
      "depth": 1,
      "player_deaths": 0,
      "runs": 30,
      "total_bonus_attacks_triggered": 147,
      "total_kills_by_faction": {
        "Player": 60
      },
      "total_kills_by_source": {
        "PLAYER": 60
      },
      "total_monster_attacks": 212,
      "total_monster_hits": 85,
      "total_plague_infections": 0,
      "total_player_attacks": 431,
      "total_player_hits": 316,
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
  "bonus_attacks_per_run": 8.25,
  "death_rate": 0.025,
  "depth": 2,
  "family": "depth2_orc",
  "monster_attacks_per_run": 11.725,
  "monster_hit_rate": 0.36886993603411516,
  "player_attacks_per_run": 23.475,
  "player_hit_rate": 0.6837060702875399,
  "pressure_index": -11.750000000000002,
  "raw": {
    "depth": 2,
    "metrics": {
      "average_turns": 49.23,
      "depth": 2,
      "player_deaths": 1,
      "runs": 40,
      "total_bonus_attacks_triggered": 330,
      "total_kills_by_faction": {
        "Orc": 1,
        "Player": 119
      },
      "total_kills_by_source": {
        "MONSTERS": 1,
        "PLAYER": 119
      },
      "total_monster_attacks": 469,
      "total_monster_hits": 173,
      "total_plague_infections": 0,
      "total_player_attacks": 939,
      "total_player_hits": 642,
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
  "bonus_attacks_per_run": 10.54,
  "death_rate": 0.16,
  "depth": 3,
  "family": "depth3_orc",
  "monster_attacks_per_run": 14.58,
  "monster_hit_rate": 0.3772290809327846,
  "player_attacks_per_run": 29.94,
  "player_hit_rate": 0.6960587842351369,
  "pressure_index": -15.360000000000001,
  "raw": {
    "depth": 3,
    "metrics": {
      "average_turns": 50.0,
      "depth": 3,
      "player_deaths": 8,
      "runs": 50,
      "total_bonus_attacks_triggered": 527,
      "total_kills_by_faction": {
        "Orc": 8,
        "Player": 190
      },
      "total_kills_by_source": {
        "MONSTERS": 8,
        "PLAYER": 190
      },
      "total_monster_attacks": 729,
      "total_monster_hits": 275,
      "total_plague_infections": 0,
      "total_player_attacks": 1497,
      "total_player_hits": 1042,
      "total_portals_used": 0,
      "total_reanimations": 0,
      "total_surprise_attacks": 198
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
  "bonus_attacks_per_run": 10.16,
  "death_rate": 0.12,
  "depth": 4,
  "family": "depth4_plague",
  "monster_attacks_per_run": 25.22,
  "monster_hit_rate": 0.33227597145122917,
  "player_attacks_per_run": 21.88,
  "player_hit_rate": 0.8427787934186471,
  "pressure_index": 3.34,
  "raw": {
    "depth": 4,
    "metrics": {
      "average_turns": 64.84,
      "depth": 4,
      "player_deaths": 6,
      "runs": 50,
      "total_bonus_attacks_triggered": 508,
      "total_kills_by_faction": {
        "Plague_Zombie": 8,
        "Player": 180,
        "Revenant Plague_Zombie": 1,
        "Revenant Zombie": 3,
        "Zombie": 17
      },
      "total_kills_by_source": {
        "MONSTERS": 29,
        "PLAYER": 180
      },
      "total_monster_attacks": 1261,
      "total_monster_hits": 419,
      "total_plague_infections": 38,
      "total_player_attacks": 1094,
      "total_player_hits": 922,
      "total_portals_used": 0,
      "total_reanimations": 17,
      "total_surprise_attacks": 187
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
  "bonus_attacks_per_run": 13.66,
  "death_rate": 0.5,
  "depth": 5,
  "family": "depth5_zombie",
  "monster_attacks_per_run": 40.84,
  "monster_hit_rate": 0.3535749265426053,
  "player_attacks_per_run": 24.88,
  "player_hit_rate": 0.8496784565916399,
  "pressure_index": 15.960000000000004,
  "raw": {
    "depth": 5,
    "metrics": {
      "average_turns": 53.98,
      "depth": 5,
      "player_deaths": 25,
      "runs": 50,
      "total_bonus_attacks_triggered": 683,
      "total_kills_by_faction": {
        "Player": 264,
        "Zombie": 69
      },
      "total_kills_by_source": {
        "MONSTERS": 69,
        "PLAYER": 264
      },
      "total_monster_attacks": 2042,
      "total_monster_hits": 722,
      "total_plague_infections": 0,
      "total_player_attacks": 1244,
      "total_player_hits": 1057,
      "total_portals_used": 0,
      "total_reanimations": 0,
      "total_surprise_attacks": 328
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
  "bonus_attacks_per_run": 2.44,
  "death_rate": 0.0,
  "depth": 5,
  "family": "dueling_pit",
  "monster_attacks_per_run": 3.8,
  "monster_hit_rate": 0.35789473684210527,
  "player_attacks_per_run": 7.44,
  "player_hit_rate": 0.7096774193548387,
  "pressure_index": -3.6400000000000006,
  "raw": {
    "depth": 5,
    "metrics": {
      "average_turns": 50.0,
      "depth": 5,
      "player_deaths": 0,
      "runs": 50,
      "total_bonus_attacks_triggered": 122,
      "total_kills_by_faction": {
        "Player": 50
      },
      "total_kills_by_source": {
        "PLAYER": 50
      },
      "total_monster_attacks": 190,
      "total_monster_hits": 68,
      "total_plague_infections": 0,
      "total_player_attacks": 372,
      "total_player_hits": 264,
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
  "bonus_attacks_per_run": 3.1,
  "death_rate": 0.0,
  "depth": 5,
  "family": "dueling_pit",
  "monster_attacks_per_run": 5.78,
  "monster_hit_rate": 0.25259515570934254,
  "player_attacks_per_run": 5.3,
  "player_hit_rate": 0.8415094339622642,
  "pressure_index": 0.4800000000000004,
  "raw": {
    "depth": 5,
    "metrics": {
      "average_turns": 50.0,
      "depth": 5,
      "player_deaths": 0,
      "runs": 50,
      "total_bonus_attacks_triggered": 155,
      "total_kills_by_faction": {
        "Player": 50
      },
      "total_kills_by_source": {
        "PLAYER": 50
      },
      "total_monster_attacks": 289,
      "total_monster_hits": 73,
      "total_plague_infections": 0,
      "total_player_attacks": 265,
      "total_player_hits": 223,
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
  "bonus_attacks_per_run": 2.38,
  "death_rate": 0.0,
  "depth": 5,
  "family": "dueling_pit",
  "monster_attacks_per_run": 1.62,
  "monster_hit_rate": 0.20987654320987653,
  "player_attacks_per_run": 5.5,
  "player_hit_rate": 0.8618181818181818,
  "pressure_index": -3.88,
  "raw": {
    "depth": 5,
    "metrics": {
      "average_turns": 50.0,
      "depth": 5,
      "player_deaths": 0,
      "runs": 50,
      "total_bonus_attacks_triggered": 119,
      "total_kills_by_faction": {
        "Player": 50
      },
      "total_kills_by_source": {
        "PLAYER": 50
      },
      "total_monster_attacks": 81,
      "total_monster_hits": 17,
      "total_plague_infections": 0,
      "total_player_attacks": 275,
      "total_player_hits": 237,
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
  "bonus_attacks_per_run": 3.14,
  "death_rate": 0.0,
  "depth": 5,
  "family": "dueling_pit",
  "monster_attacks_per_run": 2.82,
  "monster_hit_rate": 0.3191489361702128,
  "player_attacks_per_run": 7.1,
  "player_hit_rate": 0.7436619718309859,
  "pressure_index": -4.279999999999999,
  "raw": {
    "depth": 5,
    "metrics": {
      "average_turns": 50.0,
      "depth": 5,
      "player_deaths": 0,
      "runs": 50,
      "total_bonus_attacks_triggered": 157,
      "total_kills_by_faction": {
        "Player": 50
      },
      "total_kills_by_source": {
        "PLAYER": 50
      },
      "total_monster_attacks": 141,
      "total_monster_hits": 45,
      "total_plague_infections": 0,
      "total_player_attacks": 355,
      "total_player_hits": 264,
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
  "bonus_attacks_per_run": 3.14,
  "death_rate": 0.0,
  "depth": 5,
  "family": "dueling_pit",
  "monster_attacks_per_run": 3.74,
  "monster_hit_rate": 0.37433155080213903,
  "player_attacks_per_run": 8.04,
  "player_hit_rate": 0.664179104477612,
  "pressure_index": -4.299999999999999,
  "raw": {
    "depth": 5,
    "metrics": {
      "average_turns": 50.0,
      "depth": 5,
      "player_deaths": 0,
      "runs": 50,
      "total_bonus_attacks_triggered": 157,
      "total_kills_by_faction": {
        "Player": 50
      },
      "total_kills_by_source": {
        "PLAYER": 50
      },
      "total_monster_attacks": 187,
      "total_monster_hits": 70,
      "total_plague_infections": 0,
      "total_player_attacks": 402,
      "total_player_hits": 267,
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
  "bonus_attacks_per_run": 10.58,
  "death_rate": 0.16,
  "depth": 5,
  "family": "orc_swarm",
  "monster_attacks_per_run": 15.22,
  "monster_hit_rate": 0.36268068331143233,
  "player_attacks_per_run": 30.4,
  "player_hit_rate": 0.6960526315789474,
  "pressure_index": -15.179999999999998,
  "raw": {
    "depth": 5,
    "metrics": {
      "average_turns": 46.14,
      "depth": 5,
      "player_deaths": 8,
      "runs": 50,
      "total_bonus_attacks_triggered": 529,
      "total_kills_by_faction": {
        "Orc": 8,
        "Player": 191
      },
      "total_kills_by_source": {
        "MONSTERS": 8,
        "PLAYER": 191
      },
      "total_monster_attacks": 761,
      "total_monster_hits": 276,
      "total_plague_infections": 0,
      "total_player_attacks": 1520,
      "total_player_hits": 1058,
      "total_portals_used": 0,
      "total_reanimations": 0,
      "total_surprise_attacks": 199
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
  "bonus_attacks_per_run": 13.08,
  "death_rate": 0.26,
  "depth": 5,
  "family": "orc_swarm",
  "monster_attacks_per_run": 18.12,
  "monster_hit_rate": 0.36423841059602646,
  "player_attacks_per_run": 36.76,
  "player_hit_rate": 0.690424374319913,
  "pressure_index": -18.639999999999997,
  "raw": {
    "depth": 5,
    "metrics": {
      "average_turns": 44.78,
      "depth": 5,
      "player_deaths": 13,
      "runs": 50,
      "total_bonus_attacks_triggered": 654,
      "total_kills_by_faction": {
        "Orc": 13,
        "Player": 231
      },
      "total_kills_by_source": {
        "MONSTERS": 13,
        "PLAYER": 231
      },
      "total_monster_attacks": 906,
      "total_monster_hits": 330,
      "total_plague_infections": 0,
      "total_player_attacks": 1838,
      "total_player_hits": 1269,
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
  "bonus_attacks_per_run": 17.3,
  "death_rate": 0.02,
  "depth": 5,
  "family": "orc_swarm",
  "monster_attacks_per_run": 15.2,
  "monster_hit_rate": 0.3368421052631579,
  "player_attacks_per_run": 38.26,
  "player_hit_rate": 0.7119707266074229,
  "pressure_index": -23.06,
  "raw": {
    "depth": 5,
    "metrics": {
      "average_turns": 49.44,
      "depth": 5,
      "player_deaths": 1,
      "runs": 50,
      "total_bonus_attacks_triggered": 865,
      "total_kills_by_faction": {
        "Orc": 1,
        "Player": 248
      },
      "total_kills_by_source": {
        "MONSTERS": 1,
        "PLAYER": 248
      },
      "total_monster_attacks": 760,
      "total_monster_hits": 256,
      "total_plague_infections": 0,
      "total_player_attacks": 1913,
      "total_player_hits": 1362,
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
  "bonus_attacks_per_run": 9.9,
  "death_rate": 0.0,
  "depth": 5,
  "family": "orc_swarm",
  "monster_attacks_per_run": 8.54,
  "monster_hit_rate": 0.30210772833723654,
  "player_attacks_per_run": 22.06,
  "player_hit_rate": 0.7479601087941976,
  "pressure_index": -13.52,
  "raw": {
    "depth": 5,
    "metrics": {
      "average_turns": 50.0,
      "depth": 5,
      "player_deaths": 0,
      "runs": 50,
      "total_bonus_attacks_triggered": 495,
      "total_kills_by_faction": {
        "Player": 150
      },
      "total_kills_by_source": {
        "PLAYER": 150
      },
      "total_monster_attacks": 427,
      "total_monster_hits": 129,
      "total_plague_infections": 0,
      "total_player_attacks": 1103,
      "total_player_hits": 825,
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
  "bonus_attacks_per_run": 3.98,
  "death_rate": 0.3,
  "depth": 5,
  "family": "orc_swarm",
  "monster_attacks_per_run": 14.6,
  "monster_hit_rate": 0.46986301369863015,
  "player_attacks_per_run": 21.94,
  "player_hit_rate": 0.6882406563354604,
  "pressure_index": -7.340000000000002,
  "raw": {
    "depth": 5,
    "metrics": {
      "average_turns": 47.06,
      "depth": 5,
      "player_deaths": 15,
      "runs": 50,
      "total_bonus_attacks_triggered": 199,
      "total_kills_by_faction": {
        "Orc_Chieftain": 1,
        "Orc_Veteran": 14,
        "Player": 127
      },
      "total_kills_by_source": {
        "MONSTERS": 15,
        "PLAYER": 127
      },
      "total_monster_attacks": 730,
      "total_monster_hits": 343,
      "total_plague_infections": 0,
      "total_player_attacks": 1097,
      "total_player_hits": 755,
      "total_portals_used": 0,
      "total_reanimations": 0,
      "total_surprise_attacks": 142
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
  "bonus_attacks_per_run": 11.96,
  "death_rate": 0.35,
  "depth": 8,
  "family": "plague_arena",
  "monster_attacks_per_run": 22.68,
  "monster_hit_rate": 0.2601410934744268,
  "player_attacks_per_run": 19.21,
  "player_hit_rate": 0.8407079646017699,
  "pressure_index": 3.469999999999999,
  "raw": {
    "depth": 8,
    "metrics": {
      "average_turns": 178.5,
      "depth": 8,
      "player_deaths": 35,
      "runs": 100,
      "total_bonus_attacks_triggered": 1196,
      "total_kills_by_faction": {
        "Plague_Zombie": 36,
        "Player": 253
      },
      "total_kills_by_source": {
        "MONSTERS": 36,
        "PLAYER": 253
      },
      "total_monster_attacks": 2268,
      "total_monster_hits": 590,
      "total_plague_infections": 79,
      "total_player_attacks": 1921,
      "total_player_hits": 1615,
      "total_portals_used": 0,
      "total_reanimations": 1,
      "total_surprise_attacks": 288
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
  "bonus_attacks_per_run": 12.4,
  "death_rate": 0.1,
  "depth": 5,
  "family": "zombie_horde",
  "monster_attacks_per_run": 24.22,
  "monster_hit_rate": 0.21635012386457472,
  "player_attacks_per_run": 22.4,
  "player_hit_rate": 0.8303571428571429,
  "pressure_index": 1.8200000000000003,
  "raw": {
    "depth": 5,
    "metrics": {
      "average_turns": 57.14,
      "depth": 5,
      "player_deaths": 5,
      "runs": 50,
      "total_bonus_attacks_triggered": 620,
      "total_kills_by_faction": {
        "Player": 242,
        "Zombie": 5
      },
      "total_kills_by_source": {
        "MONSTERS": 5,
        "PLAYER": 242
      },
      "total_monster_attacks": 1211,
      "total_monster_hits": 262,
      "total_plague_infections": 0,
      "total_player_attacks": 1120,
      "total_player_hits": 930,
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
