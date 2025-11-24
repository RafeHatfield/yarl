# Structured Project Plan (Deep Dive)

## 1) Progression Spine & Balance Scaffolding
- **Band definitions**: Maintain five 5-floor bands (B1:1–5, B2:6–10, B3:11–15, B4:16–20, B5:21–25). Attach per-band stat multipliers (HP/damage/drops) in one table to avoid divergent tuning. Document expected TTK/TTD targets and keep them visible in tests.
- **ETP enforcement**: Implement generator validation that sums encounter ETP per room and per floor; assert totals within band ranges (±10%). Add debug logging that surfaces over-budget groups with entity IDs and spawn sources for quick fixes.
- **Pacing metrics**: Track actions-per-floor, kills-per-floor, consumables-used-per-floor. Emit telemetry JSON per run to `telemetry/` with timestamps to support regression tracking.
- **Band transitions**: Bake micro-tutorial beats at L2/L6/L11 for portals/verbs; spike challenge at L5/L10/L15/L20/L25 with Guide/Entity beats and elite/vault guarantees. Add room-parameter overrides at those depths for puzzle density and faction collisions.
- **Regression harness**: Add a headless simulation that runs 50 seeded floors per band to ensure budgets and drop EVs stay within spec when tables change.

## 2) Faction Depth (Orc/Troll/Goblin vs. Undead, Slime Neutral)
- **Archetype registry**: Define canonical statlines per unit at B1 and derive band deltas mechanically (HP/dmg multipliers, perk unlocks at B3/B5). Keep one source of truth in `data/entities.yml` (or equivalent).
- **Behavior flags**: Add AI modifiers: orcs gain aggression when armed; trolls prioritize doors/obstacles; goblin sneaks seek flanks; undead variants carry resist tags (skeleton pierce/bleed resist, zombie poison resist, wraith dodge/phase weakness to magic/holy).
- **Faction collisions**: Author two scripted collision templates per band (e.g., orc barracks vs. undead breach; slime choke in an orc hall). Express via YAML hostility matrices so generator can auto-resolve target selection.
- **Elite cadence**: Guarantee one elite template per band (Chieftain B1+, Troll Ground-Slam B5, Necro lieutenant B4). Provide knobs for elite modifiers per difficulty.
- **Summoning rules**: Limit necromancer corpse-raise frequency per encounter; log corpse count to avoid runaway difficulty. Provide counter items (holy water, firebombs) earlier than resist gates.

## 3) Combat Verbs & Status Interplay
- **Weapon speed**: Annotate weapons with action time (light 0.9T, medium 1.0T, heavy 1.1–1.2T). Update UI/tooltips/logs to show actual time cost. Ensure dual-wield and shields respect speed scaling.
- **Positional advantage**: Implement flank/backstab/surprise bonuses (+hit/+crit). Add detection rules (enemy awareness cones) and integrate with stealth/pathfinding so AI reacts to lost sight and searches last-known positions.
- **Travel speed & terrain**: Tag tiles (mud/slime/web) with movement multipliers; display iconography and log entries when slowed. Gate slow clears via items (oil, fire, cleansing scrolls).
- **Status combos**: Codify a small matrix (bleed → +10% crit taken; shock → −10% block; chill → −10% move speed) and expose in tooltips/combat log. Ensure stacking rules are capped and cleansable.
- **Portal interplay**: Enforce portal usability flags (bosses false, rank-and-file true). Add AI behavior for chasing through portals with delay/hesitation per faction.

## 4) Rooms, Vaults, and Secrets Expansion
- **Template library**: Ship initial high-quality templates—Treasure Vault, Faction Border, Puzzle Gate, Secret Room, Portal Tutorials (L2/L6/L11). Store as JSON/YAML with parameters for size ranges, door rules, trap density, and encounter ETP bounds.
- **Locks/doors/secrets**: Add door rules (wood/iron), locked percentages, secret door chances with discovery DCs. Pair with key tagging so keys/locks resolve within 2 floors.
- **Puzzle gating**: Support mural/signpost hints that reference off-room switches/items; block ~30% of floor content behind a solvable puzzle in B3+.
- **Environmental hazards**: Incorporate trap tables (spike, web, gas, alarm). Allow per-room overrides for density. Log trap reveal/trigger for telemetry.
- **Secret rooms**: Guarantee ~1 per band; prefer dead-end conversions; add fair tells (misaligned wall tiles, rhyme hints). Telemetry includes discovery method (search vs. item vs. accidental).

## 5) Loot, Drop Pacing, and Pity Controller
- **EV targets**: Per band, set expected drops per floor (healing, escape, ID, upgrade). Use weighted tables plus pity to smooth RNG streaks.
- **Pity mechanics**: Track streaks per category over a 4–5 floor window; if zero, multiply weights (e.g., ×3). Optionally inject on floor 5+ for essentials. Reset counters on drop. Expose thresholds in config for difficulty modes.
- **Rarity gating**: Common only in B1; add uncommon in B2; rares in B4/B5 with low preview odds earlier. Ensure upgrades average every 2–3 floors.
- **Key/lock economy**: Spawn keys with soft guarantees to find a matching lock within 2 floors. If unused, spawn a consolation lock with modest reward to avoid dead inventory.
- **Vendor/shrine hooks**: Introduce “shrine of succor” in B4–B5 trading relic charges for heals; keep drop EV consistent with pity counts.

## 6) Difficulty Settings & Run Modifiers
- **Multipliers, not forks**: Apply HP/accuracy/drop EV/trap damage/elite chance/pity thresholds per difficulty. Avoid separate content tables.
- **Nightmare rules**: Remove pity for escape/ID, allow stacking elite modifiers, tighten corridor safety (fewer safe tiles/doors).
- **Accessibility toggles**: Optional assists (combat log verbosity, highlight traps/portals) without altering core balance numbers.
- **Config surface**: Expose difficulty block in one config file; ensure save files store difficulty to prevent mid-run switching exploits.

## 7) Narrative Cadence & Milestone Beats
- **Guide/Entity beats**: Reinforce at L5/10/15/20/25 with bespoke rooms and safe delivery spaces. Keep death=canon messaging light and recurring.
- **Undead arc**: Seed necromancer foreshadowing from B3 murals; introduce lieutenant boss in B4; climax near L20; tie Ruby Heart finale to soul-recycling stakes.
- **Environmental storytelling**: Use murals/signposts in vaults/secrets to teach counters (fire vs. trolls, blunt vs. skeletons) and foreshadow endings. Avoid front-loading exposition; drip via discoveries.
- **Portal tutorials**: Script three micro-rooms that reward performing the demonstrated trick (kite & cull, faction fuse, vault juke). Grant a “challenge coin” or consumable on success.

## 8) Testing & Validation
- **Design tests**: Automated checks that per-floor ETP totals stay within band targets; pity never exceeds thresholds; resist-gated foes co-occur with counters; portal usability flags respected (boss false, mobs true).
- **Schema validation**: On load, verify entity IDs, counts, room sizes, encounter budgets, key/lock pairs. Fail fast with actionable errors.
- **Simulation runs**: Headless runner to generate N floors per band, record telemetry for TTK/TTD, drops, traps, secrets, and faction collisions. Produce summary dashboards for tuning.
- **Performance guardrails**: Track entity counts per room/floor against `max_entities` to prevent perf regressions. Include tests for tooltip/log determinism when new statuses/verbs land.

