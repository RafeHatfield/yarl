# Depth Boons — Implementation Guide (Phase 23)

## What exists now

### Core module: `balance/depth_boons.py`

| Symbol | Purpose |
|---|---|
| `BOON_REGISTRY` | Dict mapping `boon_id → BoonDefinition` (metadata: display name, description) |
| `DEPTH_BOON_MAP` | Fixed mapping of `depth → boon_id` for depths 1–5 |
| `apply_boon(player, boon_id)` | Mutates Fighter base fields in-place; raises `ValueError` on unknown ID, returns `False` if Fighter missing |
| `apply_depth_boon_if_eligible(player, depth)` | Main entry point; checks visited_depths gate + disable flag; records to Statistics; returns boon_id or None |
| `get_boon_for_depth(depth)` | Pure lookup into `DEPTH_BOON_MAP` |

### Starter boons (proof-of-pipeline set)

| `boon_id` | Effect | Fighter field mutated |
|---|---|---|
| `fortitude_10` | +10 `base_max_hp`; heals 10 HP immediately | `base_max_hp`, `hp` |
| `accuracy_1` | +1 to-hit | `accuracy` |
| `defense_1` | +1 AC | `base_defense` |
| `damage_1` | +1 minimum damage | `damage_min` |
| `resilience_5` | +5 `base_max_hp`; heals 5 HP immediately | `base_max_hp`, `hp` |

### Default depth mapping

```
depth 1 → fortitude_10
depth 2 → accuracy_1
depth 3 → defense_1
depth 4 → damage_1
depth 5 → resilience_5
depth 6+ → (none; visitied_depths still updated)
```

### Player state: `components/statistics.py`

Three new fields on `Statistics`:

```python
visited_depths: Set[int]      # depths already visited (non-farmable gate)
boons_applied: List[str]      # ordered log of boon IDs received this run
disable_depth_boons: bool     # set True to prevent automatic depth boons
```

All three are serialised in `to_dict()` / `from_dict()` — fully save/load safe.
Old saves without these keys are handled by `from_dict` defaults (empty set / empty
list / False).

### Save/load: `loader_functions/data_loaders.py`

* `Statistics` component is now serialised as part of the player entity
  (`_serialize_entity`, `_deserialize_entity`).
* `Fighter.accuracy` and `Fighter.evasion` are now serialised so boon stat
  mutations survive save/load.

### Campaign hook: `map_objects/game_map.py`

`next_floor()` calls `apply_depth_boon_if_eligible(player, self.dungeon_level)`
immediately after incrementing `dungeon_level`.  A `try/except` guard prevents
boon bugs from aborting floor generation; in testing mode (`is_testing_mode()`)
exceptions are re-raised so tests fail loudly.

### Scenario harness: `services/scenario_harness.py`

`RunMetrics` has a new field:

```python
boons_applied: List[str] = field(default_factory=list)
```

It is populated at the end of `run_scenario_once()` from
`player.statistics.boons_applied` and is always present in `RunMetrics.to_dict()`
(empty list if no boons were applied).

---

## How to test

```bash
# All Phase 23 unit tests (fast, no harness)
pytest tests/test_depth_boons.py -m fast -q

# Full non-slow suite (includes depth boon tests)
pytest -m "not slow" -q

# Single scenario proving pipeline
pytest tests/test_depth_boons.py::test_run_metrics_boon_export -v
```

---

## How to add a new boon

1. Add an entry to `BOON_REGISTRY` in `balance/depth_boons.py`:
   ```python
   "toughness_2": BoonDefinition(
       boon_id="toughness_2",
       display_name="Toughness",
       description="+2 base defense",
   ),
   ```

2. Add the application logic in `apply_boon()`:
   ```python
   elif boon_id == "toughness_2":
       fighter.base_defense += 2
   ```

3. Optionally map it to a depth in `DEPTH_BOON_MAP`:
   ```python
   6: "toughness_2",
   ```

4. Add a unit test in `tests/test_depth_boons.py` (follow the existing pattern).

---

## Scenario YAML wiring

Under the `player:` block in any scenario YAML:

```yaml
player:
  position: [2, 2]
  equipment:
    weapon: "dagger"
    armor: "leather_armor"

  # Phase 23 extensions:
  boons: ["fortitude_10", "accuracy_1"]  # applied explicitly at scenario start
  disable_depth_boons: true              # prevents automatic depth boons
```

`boons` is processed by `_apply_player_boons()` in `scenario_level_loader.py`,
following the same pattern as the existing `oath` field.  Unknown boon IDs log a
warning and are skipped rather than crashing the scenario build.

**Tip for isolated testing:** always set `disable_depth_boons: true` in identity
scenarios so automatic boons don't interfere with explicit boon state being tested.

---

## Pressure model / analysis

Boon state is exported as `boons_applied` in every `RunMetrics.to_dict()` result:

```json
{
  "turns_taken": 12,
  "player_died": false,
  "player_damage_dealt": 45,
  "monster_damage_dealt": 18,
  "boons_applied": ["fortitude_10"]
}
```

To compare **with boons** vs **without boons** in the depth pressure pipeline:

1. **Without boons:** add `disable_depth_boons: true` to the scenario YAML.
2. **With boons (manual):** add `boons: ["fortitude_10"]` to the scenario YAML.
3. **With auto depth boons:** omit both keys (the campaign hook fires automatically).

Run the depth pressure data collection and compare `total_player_damage_dealt` /
`total_monster_damage_dealt` ratios between the variant runs.

---

## How to verify locally (3-step checklist)

### Step A — Confirm boons appear in scenario JSON export

```bash
python ecosystem_sanity.py --scenario boon_identity --export-json /tmp/boon_identity.json --runs 1 --seed-base 1337
python -m json.tool /tmp/boon_identity.json | grep -A 3 "boons_applied"
```

Expected output:
```
"boons_applied": [
    "fortitude_10"
]
```

**Where to look:** `boons_applied` lives inside `metrics.run_details[0]`, **not** at the
top level of the JSON.  The top-level `metrics` key holds `AggregatedMetrics`; per-run
details are under `metrics.run_details` (a list, one entry per run).

### Step B — Confirm the in-game message when descending

Run the game normally (`make run` or `python main.py`), create a new character, and
descend to depth 2 via the stairs.  The message log should show (in purple):

> **The Heart pulses… You gain: Keen Eye**

If you descend to depth 1 for the first time the message reads:

> **The Heart pulses… You gain: Fortitude**

### Step C — If neither appears, run these 3 checks

```bash
# 1. Confirm Statistics is attached to the campaign player
grep -n "Statistics\|statistics_component" loader_functions/initialize_new_game.py | head -10

# 2. Confirm next_floor() has the boon hook
grep -n "apply_depth_boon_if_eligible\|Heart pulses" map_objects/game_map.py

# 3. Run the fast boon unit tests and the aggregated export test
python -m pytest tests/test_depth_boons.py -q
```

If test #3 fails, the boon module itself has a regression.  If the grep in #2 shows no
results, the hook was accidentally removed from `next_floor()`.  If #1 shows no
`Statistics` attachment, `apply_depth_boon_if_eligible` returns `None` silently.

---

## How to run A/B depth pressure reports

### When to use

Use the A/B pipeline to measure how depth boons shift the pressure curve.
Run it any time you tune boon effects, add new boons, or change depth scaling.
This is tooling only — no balance changes are made here.

### Commands

```bash
# Full A/B run (both variants, ~7 scenarios × 2 × N runs — takes a few minutes)
python tools/collect_depth_pressure_data.py --ab --runs 50 --seed-base 1337

# Control variant only (boons disabled, flat layout)
python tools/collect_depth_pressure_data.py --disable-depth-boons --runs 50 --seed-base 1337

# Normal variant only (existing behavior, boons enabled)
python tools/collect_depth_pressure_data.py --runs 50 --seed-base 1337

# Dry run — print all commands without executing (fast; useful for CI checks)
python tools/collect_depth_pressure_data.py --dry-run --ab --runs 5 --seed-base 1337
```

### Output layout (`--ab`)

```
reports/depth_pressure/<timestamp>/
  manifest.json               ← written FIRST (top-level; boons_mode: "ab")
  on/
    depth1_orc_easy.json      ← boons enabled
    depth2_orc_baseline.json
    ...
    manifest.json             ← boons_mode: "on"
    depth_pressure_report.md
    depth_pressure_table.csv
  off/
    depth1_orc_easy.json      ← boons disabled (control)
    depth2_orc_baseline.json
    ...
    manifest.json             ← boons_mode: "off"
    depth_pressure_report.md
    depth_pressure_table.csv
  depth_pressure_compare.md   ← delta table; open this first
```

### What to open first

**`depth_pressure_compare.md`** — side-by-side delta table showing how H_PM,
H_MP, DPR_P, DPR_M, and Death% change at each depth when boons are removed.

Delta convention: Δ = OFF − ON.  A positive ΔH_MP means monsters need more
rounds to kill the player without boons (boons made the player squishier).

### Where boon mode is recorded

- Each subdir `manifest.json` has `"boons_mode": "on"` or `"off"`.
- The top-level `manifest.json` has `"boons_mode": "ab"`.
- Per-run JSON exports do **not** have a `boons_mode` key — the truth is
  visible in `metrics.run_details[i].boons_applied` (empty list = boons off).

### How the flag works internally

`--disable-depth-boons` in `ecosystem_sanity.py` passes
`disable_depth_boons=True` to `run_scenario_many()` → `run_scenario_once()`.
After `build_scenario_map()` constructs the player, the harness sets
`player.statistics.disable_depth_boons = True` before the game loop starts.
The scenario YAML is **never mutated**; no duplicate YAML files are needed.

---

---

## Difficulty Curve Visualization

After a data collection run the pipeline automatically generates two additional
artifacts in the output directory:

| File | Contents |
|------|---------|
| `depth_pressure_curve.md` | Compact table + ASCII sparklines |
| `depth_pressure_curve.png` | Line chart: H_PM and Death% vs depth |

### How to read the curve

**Table columns**

| Column | Meaning |
|--------|---------|
| `H_PM(on/off)` | Rounds for player to kill one monster. **Higher = harder encounter.** |
| `H_MP(on/off)` | Rounds for monsters to kill player. **Lower = more dangerous depth.** |
| `DPR_P(on/off)` | Player expected damage per round. Higher = player hits harder. |
| `DPR_M(on/off)` | Monster expected damage per round. Higher = monsters hit harder. |
| `Death%(on/off)` | Fraction of runs the player died. **Higher = deadlier depth.** |

**ON** = boons enabled (normal campaign).
**OFF** = boons disabled (control variant).

In single-variant mode only the `(on)` columns are present.

**`[gear probe]`** rows use upgraded starting equipment and are not part of the
main depth curve. Do not compare them directly to different-depth rows.

### Sparklines

ASCII sparklines show the trend across depths 1–6 (left = shallow, right = deep).
Block height represents relative magnitude — `▁` = low, `█` = high.
Gear probe rows are excluded so they do not distort the scale.

### PNG chart

Two subplots: **H_PM** (top) and **Death%** (bottom) vs dungeon depth.

- Solid line = ON variant.
- Dashed line = OFF variant (A/B mode only).
- `×` markers = gear probe data points (not connected to main lines).

### Commands

```bash
# Produce curve from an existing single-variant directory
python analysis/depth_pressure_curve.py reports/depth_pressure/<timestamp>/on/

# Produce curve from an existing A/B run
python analysis/depth_pressure_curve.py --ab \
    reports/depth_pressure/<timestamp>/on/depth_pressure_table.csv \
    reports/depth_pressure/<timestamp>/off/depth_pressure_table.csv \
    reports/depth_pressure/<timestamp>/

# Full A/B run (curve generated automatically)
python tools/collect_depth_pressure_data.py --ab --runs 50
```

---

## Gear Pressure Probes

Gear probes isolate the effect of a single equipment upgrade while holding all
other scenario variables constant (same enemies, same arena, same seed).

### Available probes

| Scenario ID | Change from base |
|-------------|----------------|
| `depth3_orc_brutal_gear_weapon_plus1` | `fine_longsword` instead of `dagger` (+1 to-hit) |
| `depth3_orc_brutal_gear_armor_plus1` | `chain_mail` instead of `leather_armor` (+1 defense) |

Both probe scenarios are identical to `depth3_orc_brutal` in monsters, layout,
items, and turn limit. They carry `suites: ["gear_probe"]` and are **not**
included in the main balance suite by default.

### What the probes measure

- **Weapon probe** quantifies how much a +1 accuracy upgrade reduces H_PM and
  Death% at depth 3. Compares how faster killing translates to survival.
- **Armor probe** quantifies how much a +1 defense upgrade increases H_MP and
  reduces Death% at depth 3. Shows defensive value of one armor tier.

Compare probe rows against the base `depth3_orc_brutal` row at the same depth
in the curve table to read the delta.

### How to run

```bash
# Include gear probes in a standard A/B run (50 simulations each)
python tools/collect_depth_pressure_data.py --ab --include-gear-probes --runs 50

# Gear probes with default run count only (no A/B)
python tools/collect_depth_pressure_data.py --include-gear-probes --runs 50

# Dry-run to verify probe scenario IDs appear in the suite
python tools/collect_depth_pressure_data.py --dry-run --include-gear-probes
```

Gear probe rows appear in `depth_pressure_report.md`, `depth_pressure_table.csv`,
`depth_pressure_curve.md`, and `depth_pressure_curve.png` alongside normal suite
rows. They are always marked `[gear probe]` in the curve markdown.

---

## Intentionally deferred (not in Phase 23)

* **3-choose-1 selection UI** — player will eventually choose from a pool at each depth
* **Large boon pool** — currently only 5 starter boons
* **Boon synergies / compound effects** — e.g. "if you have fortitude_10 + defense_1"
* **Boon display in sidebar** — showing active boons during gameplay
* ~~**AggregatedMetrics boon field**~~ — shipped: `AggregatedMetrics.run_details` carries per-run `boons_applied` lists
* **XP / level-up triggered boons** — explicitly out of scope; use depth-arrival only
