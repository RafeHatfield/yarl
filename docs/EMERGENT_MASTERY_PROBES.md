# Emergent Mastery Probes

## What This Is

Emergent mastery probes are diagnostic identity scenarios designed to
validate that the game supports **clever system use** rather than pure
stat-checking. They are intentionally difficult encounters where the
bot (tactical_fighter) is expected to have a high death rate, but a
human player exploiting game systems should perform significantly better.

These scenarios are not balance baselines. They do not define "fair."
They define "solvable with cleverness."

## Manual Puzzle Scenario Index

These scenarios are for **human manual playtesting only.** They have no suite
tags, no bot expectations, and no CI impact. They are intentionally allowed to
be overtuned and are not required to be bot-solvable — that is by design.

| Scenario ID | File | What This Room Teaches |
|-------------|------|------------------------|
| `orc_stronghold_puzzle` | `config/levels/scenario_orc_stronghold_puzzle.yaml` | Portal bypass, choke luring, and consumable sequencing against a depth-5 fortified orc group that cannot be brute-forced |

---

## What "Emergent Mastery" Means in YARL

Emergent mastery is when the player combines existing game systems in
ways that aren't explicitly scripted to overcome challenges that appear
overwhelming on paper.

**Examples of emergent mastery:**

- **Choke exploitation.** Using a narrow doorway or corridor to force
  a group of enemies into single-file, negating their numerical
  advantage.
- **LOS manipulation.** Positioning behind pillars or around corners
  to break a shaman's line of sight, preventing hex casts while
  engaging melee targets.
- **Consumable combos.** Throwing a root potion to entangle a brute,
  then blinking past it with a blink scroll to reach the shaman.
- **Terrain awareness.** Retreating through the choke when
  overwhelmed, forcing enemies to bottleneck.
- **Skirmisher prediction.** Recognizing the skirmisher's leap range
  and staying outside it until ready to engage.

These are all built from existing systems (movement, LOS, status
effects, scrolls, potions, monster AI). No special "mastery mechanic"
is needed. The game just needs to support enough system interactions
that creative combinations emerge.

## Current Probes

### Orc Stronghold Probe

**File:** `config/levels/scenario_orc_stronghold_probe.yaml`
**Suite:** identity
**Depth:** 4

**Layout:** 20x14 arena with a dividing wall creating a 2-tile choke
point. Left half is the approach zone; right half is the fortified
stronghold with cover pillars.

**Composition:** 5 enemies — 2 orc grunts (choke guards), 1 orc brute
(center tank), 1 orc shaman (back-corner caster), 1 orc skirmisher
(flanking leaper).

**Emergent tools available:**
- Blink scroll (ground pickup) — repositioning past the wall
- Root potion (ground pickup) — throwable entangle for crowd control
- Choke point geometry — natural 1-on-1 engagement
- Pillar cover — LOS break against shaman

**Player gear:** Longsword + chain_mail (midgame-appropriate kit), 4
healing potions. Chain_mail (+4 AC) was required to bring death rate
below 100%; leather_armor (+2 AC) resulted in 100% bot deaths.

**Expected bot outcome:** ~70% death rate (observed: 14/20 deaths, 47
kills across 20 runs). The bot fights head-on with basic tactics. It
does not exploit the choke, use scrolls strategically, or manipulate
LOS. This high death rate is intentional and expected.

**What the probe catches:**
- If death rate exceeds 90% (18/20): scaling or composition has made
  the encounter nearly hopeless. Emergent play becomes irrelevant.
- If total kills across 20 runs drops below 20: the encounter is
  so lethal that the player dies before meaningfully engaging.

## When to Revisit These Scenarios

Revisit emergent mastery probes when:

1. **Monster scaling curve changes.** Any modification to
   `balance/depth_scaling.py` multipliers, especially HP or damage
   at the depth 3–5 band.

2. **Orc composition changes.** New orc variants, stat changes to
   existing orcs (grunt, brute, shaman, skirmisher), or changes to
   orc AI behavior.

3. **New tactical items.** Adding new scrolls, potions, or usable
   items that could change the player's tactical options in these
   encounters.

4. **Depth Boons implementation.** When boons are added (see
   `PLAYER_PROGRESSION_DOCTRINE.md`), these probes need re-evaluation
   to confirm that boons make the encounter more solvable through
   cleverness, not just through stat inflation.

5. **Bot policy upgrades.** If the tactical_fighter bot becomes
   smarter (uses consumables, exploits chokes), the expected death
   rate will change and thresholds may need adjustment.

## Puzzle Scenarios (Emergent Mastery Cultivation)

Puzzle scenarios are a distinct category from probes. They are designed
for **human manual playtesting only** and are never part of CI, identity
suite, or regression tooling.

**Puzzle scenarios are explicitly allowed to be overtuned and are not
required to be bot-solvable. A bot dying 100% of the time in a puzzle
scenario is expected and correct behavior, not a regression.**

### Probe vs Puzzle

| Aspect | Probe | Puzzle |
|--------|-------|--------|
| **Purpose** | Drift detection (canary) | Emergent mastery cultivation |
| **Runner** | Bot (tactical_fighter) | Human player only |
| **Suite** | identity | None |
| **Expectations** | Loose guardrails (kills, deaths) | None |
| **CI impact** | Yes (fails if thresholds violated) | None |
| **Deterministic** | Yes (seed_base=1337) | Not required |
| **Balance baseline** | No, but detects regression | No |

Probes answer: "Does the game still support emergent play?"
Puzzles answer: "Can a clever human actually exploit these systems?"

### Orc Stronghold Puzzle

**File:** `config/levels/scenario_orc_stronghold_puzzle.yaml`
**Suite:** None (manual playtest only)
**Depth:** 5

**Why this exists:**

The Orc Stronghold Probe (depth 4, 5 enemies) validates that emergent
play is *possible* — the bot dies ~70% of the time, but the systems
exist for a human to do better. The Puzzle (depth 5, 6 enemies) goes
further: it creates a room that is *impossible* to brute-force and can
only be solved through creative system exploitation. It is the
practical test of YARL's "skill = system mastery" pillar.

**Layout:** 22x18 arena with layered fort geometry:

- Two horizontal dividing walls (y=7 and y=12), each with a single
  1-tile gap at x=11. The y=12 wall is the **entry choke** from the
  approach zone into the main hall. The y=7 wall separates the main
  hall from the **back chamber**.
- A vertical partition in the back chamber (x=11, y=3–5) splits it
  into NW and NE sub-areas. The NE sub-area is the shaman's hideout.
  Gap at y=6 allows east-west movement between sub-areas.
- Pillars at (5,4) and (17,10) provide partial LOS cover.

**Composition:** 6 enemies — 3 orc grunts, 1 orc brute, 1 orc
skirmisher, 1 orc shaman. At depth 5 (HP ~1.47x, ToHit ~1.34x),
head-on combat through the 1-tile choke against this force is
near-guaranteed death.

**Player kit:** Longsword + chain_mail, 3 healing potions, plus ground
pickups: Wand of Portals (3 charges), root potion, blink scroll.

**Systemic interactions this scenario highlights:**

1. **Portal bypass.** The Wand of Portals is the keystone tool. The
   player can portal from the approach zone directly into the NE back
   chamber, skipping both walls and all main-hall enemies to reach the
   shaman. Or portal behind the main-hall group for a flanking attack.

2. **Portal traps.** Place a portal entrance at the choke gap and the
   exit in the far approach zone. Enemies walking through the choke
   teleport away from the fight, buying time.

3. **Geometry-driven luring.** Step into the choke, pull 1–2 enemies
   south, retreat. The 1-tile gap forces single-file engagement.
   Repeat to thin the pack before committing.

4. **Root + isolation.** Root potion the brute at the choke to block
   it, then fight grunts that squeeze past. Or root the skirmisher
   to prevent its leap.

5. **LOS manipulation.** Use the y=7 divider wall and pillars to break
   shaman LOS. The shaman cannot hex through solid walls — only
   through the 1-tile gap, which can be blocked by a rooted enemy.

6. **Blink repositioning.** Blink scroll for emergency escape if the
   skirmisher leaps past the choke or if surrounded in the main hall.

**Example solution patterns (conceptual):**

- *Portal assassination:* Pick up wand → place entrance in approach →
  place exit in NE back (16,2) → step through → kill shaman 1-on-1 →
  portal back → deal with remaining 5 via choke abuse.

- *Divide and conquer:* Lure grunts through choke → fight them in
  approach zone → root brute at choke → portal past divider wall →
  clear grunt guarding back passage → reach shaman.

- *Portal trap + attrition:* Place portal entrance at (11,12) choke
  gap, exit at (3,16). Enemies teleport south. Fight them piecemeal
  as they walk back north.

**This scenario is NOT a balance baseline.** It does not define "fair."
It defines "solvable with system mastery." If a human cannot solve it
using available tools, that indicates a system gap — not a balance
problem.

## How to Manually Playtest a Puzzle Scenario

### Running the scenario (bot observer, single pass)

Use the **ecosystem harness** (`ecosystem_sanity.py`) to load the scenario
and run the bot headlessly.  With `--runs 1` you get a single execution and
can confirm the scenario loads cleanly and the composition is present:

```
python3 ecosystem_sanity.py --scenario orc_stronghold_puzzle --runs 1 --turn-limit 200 --player-bot tactical_fighter
```

To observe the raw death rate across multiple bot attempts (expect near 100%
for puzzle scenarios — that is expected and correct):

```
python3 ecosystem_sanity.py --scenario orc_stronghold_puzzle --runs 10 --turn-limit 200 --player-bot tactical_fighter
```

Alternatively, via the Makefile bot-soak-scenario target:

```
make bot-soak-scenario SCENARIO=orc_stronghold_puzzle RUNS=1 MAX_TURNS=250 MAX_FLOORS=1 PERSONA=balanced
```

> **Note:** `engine.py --bot-soak --headless --scenario <id>` is **not a valid
> command** in this repository.  `engine.py` does not accept a `--scenario`
> flag.  Use `ecosystem_sanity.py --scenario` for all headless scenario runs.

### Interactive play (not yet supported)

Interactive scenario loading via CLI is **not yet implemented**.  There is no
`engine.py --scenario` flag.  To playtest a puzzle scenario as a human player,
use one of these workarounds:

- **Debug-start:** Launch normally (`python3 engine.py`) with available debug
  flags (`--god-mode`, `--start-level`, etc.) to reach a comparable depth,
  treating the YAML layout description as your reference map.
- **Watch a bot run:** `ecosystem_sanity.py` is headless-only; there is
  currently no windowed observation mode.

When interactive scenario loading is implemented, this section will be updated
with the real command.  Until then, `ecosystem_sanity.py --scenario` is the
only supported path for loading and running a named scenario.

### What to look for

Evaluate these dimensions during a playtest session:

- **Solution paths exist.** Can you identify at least 2–3 distinct routes to
  win using the available tools? If only one path works, the room is a
  scripted puzzle, not an emergent one.
- **Tool usefulness.** Does every ground pickup (scroll, potion, wand charge)
  have at least one clear use case? Items with no purpose are noise.
- **Fairness ceiling.** A clever player should be able to win consistently. If
  even optimal play results in death (insta-kill, no escape route), the
  scenario needs tuning.
- **Brute-force futility.** A player who ignores all tools and charges
  straight in should die. If a head-on approach routinely wins, the puzzle is
  undertuned.
- **System legibility.** Does the room telegraph its intended tools? A player
  who picks up the wand of portals and reads the geometry should infer
  "portal bypass" as a strategy without a hint.

### Recording playtest notes (suggested template)

```
## Playtest: <scenario_id>  —  <date>
### Run summary
- Attempts:        N
- Wins:            N
- Primary strategy used: (e.g. portal assassination, choke luring)
- Tools used: (e.g. wand of portals ✓, root potion ✗, blink scroll ✓)

### What worked
-

### What didn't work / felt unfair
-

### Untested solution paths
-

### Suggested changes (if any)
-
```

---

## When to Revisit These Scenarios

Revisit emergent mastery probes when:

1. **Monster scaling curve changes.** Any modification to
   `balance/depth_scaling.py` multipliers, especially HP or damage
   at the depth 3–5 band.

2. **Orc composition changes.** New orc variants, stat changes to
   existing orcs (grunt, brute, shaman, skirmisher), or changes to
   orc AI behavior.

3. **New tactical items.** Adding new scrolls, potions, or usable
   items that could change the player's tactical options in these
   encounters.

4. **Depth Boons implementation.** When boons are added (see
   `PLAYER_PROGRESSION_DOCTRINE.md`), these probes need re-evaluation
   to confirm that boons make the encounter more solvable through
   cleverness, not just through stat inflation.

5. **Bot policy upgrades.** If the tactical_fighter bot becomes
   smarter (uses consumables, exploits chokes), the expected death
   rate will change and thresholds may need adjustment.

Revisit puzzle scenarios when:

6. **Portal system changes.** Any modification to wand_of_portals,
   portal placement, or portal teleportation behavior.

7. **New systemic tools.** Items or abilities that create new
   emergent interaction possibilities.

## Design Constraints

- Probes use only existing game systems. No special mechanics.
- All enemy types use explicit IDs (never generic "orc").
- Probe scenarios are deterministic under `seed_base=1337`.
- Probe expectations use only supported harness keys.
- Probes are tagged `suites: ["identity"]` and listed in
  `tools/identity_suite.py`.
- Puzzle scenarios have NO suite tags, NO expectations, and NO CI
  impact. They are for manual playtesting only.

## Puzzle Scenario Creation Checklist

Use this when adding a new puzzle scenario to keep the pattern consistent:

- [ ] No `suites:` tag in the YAML (or `suites: []`).
- [ ] No `expectations:` block in the YAML.
- [ ] Scenario loads and completes without error: `python3 ecosystem_sanity.py --scenario <id> --runs 1 --turn-limit 200 --player-bot tactical_fighter`
- [ ] At least 2 distinct ground-pickup tools that enable meaningfully different
      solution paths (e.g. portal vs. root vs. blink — not two potions of the
      same type).
- [ ] The YAML file (or the entry in this doc) contains one paragraph describing
      the intended "clever win": what systems the player must combine, and why a
      head-on approach fails.
