# **North Star (anchor this first)**

* **Core fantasy:** gritty, tactical, portable stories from runs where clever positioning, portals, and faction shenanigans let a melee-forward hero outplay stronger foes.

* **Story guardrails:** the 25-floor descent culminates at the Ruby Heart with choice-driven endings; cadence for Guide/Entity beats at L5/10/15/20/25 (already in your canon). Keep death \= canon (soul rotation) as the run loop; don’t front-load exposition.

---

# **The Systematic Build Plan**

## **1\) Lock the progression spine (25 floors)**

Treat the dungeon as five “bands” of 5 floors each. Each band establishes new baselines for: time-to-kill, time-to-die, resource burn, and puzzle/room complexity.

**Bands**

* **B1 (L1–5):** Teach systems; give at least one “aha” portal trick. First Guide beat at L5. Target 20–30 actions per floor.

* **B2 (L6–10):** Add counters to player habits; first “elite vault” template. Entity tone shifts; Guide beat at L10.

* **B3 (L11–15):** Introduce resistances as hard gates; first puzzle room that blocks 30% of floor content unless solved. Guide shares true name at L15.

* **B4 (L16–20):** Multi-faction set-pieces; hazards \+ speed control. Final Guide beat at L20.

* **B5 (L21–25):** Attrition pressure; boss preface rooms; final confrontation scaffolding at L25.

**Target experience per floor (baseline warrior run):**

* **Encounters:** 3–5 packs \+ 1 micro-setpiece (faction interaction OR mini-puzzle)

* **TTK:** common foes die in 2–4 player attacks in B1, increasing \~+1 attack per band

* **TTD:** the player survives \~3–5 average enemy attacks at full health in B1, drifting toward 2–3 by B5 unless properly geared

Opinion: consistency here matters more than raw numbers. If “how fast I kill / die” is predictable per band, you can mix surprises without feeling unfair.

---

## **2\) Challenge budgeting (encounters, not just monsters)**

Give each monster an **Effective Threat Points (ETP)** score to budget rooms and floors.

**Per-monster ETP**  
 ETP \= (DPS × 6\) × Durability × Behavior × Synergy

* **DPS:** average damage per enemy turn vs. baseline AC.

* **Durability:** expected player hits to kill / 3 (so 1.0 means \~3 hits to kill).

* **Behavior:** 0.8–1.2 (melee dummy 0.9; gap-closer 1.0; kiter/control 1.1; area denial 1.2).

* **Synergy:** \+0.1 per meaningful combo in that group (e.g., slime slow \+ orc heavy hits).

**Encounter budgets (by band):**

* B1: 3–5 ETP

* B2: 6–8

* B3: 9–12

* B4: 12–15

* B5: 16–20

Setpiece rooms can spike up to **\+50%** budget with compensations (line-of-sight blockers, one-use consumable on entry, etc.).

---

## **3\) Factions as a first-class lever**

You’ve already got inter-faction aggression; double down by giving factions **play patterns**:

* **Orcs (Martial/Greed):** pick up weapons; \+Behavior when armed; prefer flanks.

* **Trolls (Brute/Regeneration):** area denial \+ door smashing; counters: fire/bleed.

* **Slimes (Ooze/Divide):** slow, split, resist blunt—great portal bait.

Author **two scripted “collision patterns” per band** (e.g., slime nest spilling into orc barracks; trolls trying to breach a slime-sealed treasure door). Tie these into **vault templates** so they recur with variations.

---

## **4\) Item and drop pacing (math you can tune)**

Think in **expected value per floor**, not raw RNG. Use a simple controller:

**Per-floor expectations (baseline, Normal difficulty):**

* **Healing:** \~1.5 “minor heals” worth of recovery (potions or equivalent)

* **Oh-crap outs (teleport, smoke, confuse):** 0.2–0.3 per floor average (pity timer ensures 1 within any 5-floor band if none dropped)

* **Power spikes:** one equipment upgrade **every 2–3 floors** on average

* **Identification fuel:** 1 scroll of ID every 1–2 floors until midgame; taper to 1 per 3 floors after B3

**Implement with weighted tables \+ pity timers:**

* Maintain per-category counters. If the moving window (e.g., last 5 floors) \< target, bias the next roll into that category.

* Gate **rarity tiers** by band (Common in B1, Uncommon in B2, Rare in B3+, Legendary B5 only), with tiny preview chances earlier for excitement.

**Identification game:**

* Early bands: safe IDs or plentiful scrolls; midgame: add mimic/curse risk; late: introduce lore-based soft ID (murals/hints tie to specific uniques). Your docs already emphasize identification; keep it discoverable in play.

---

## **5\) Difficulty settings (hook points)**

Apply **multipliers**, not separate tables:

* **Easy:** Enemy HP ×0.90, Enemy Accuracy ×0.90, Drop EV \+20%, trap damage ×0.8, pity timers half as long.

* **Normal:** Baseline.

* **Hard:** Enemy HP ×1.10, Enemy Accuracy ×1.10, Resist gate checks \+10%, Drop EV −15%, elite spawn chance \+25%, fewer safe corridors.

* **Nightmare (unlock):** Add “scarcity mode” (no pity timers), elite modifiers stack.

Keep endings/lore identical across difficulties; only path harshness changes. (Your endings matrix and moral weight shouldn’t be gated by a menu choice.)

---

## **6\) Combat layer: close the missing verbs**

You called out missing pieces. Prioritize these **four** (they materially deepen melee play and scale into puzzles):

1. **Weapon speed** → Action cost modifier (light 0.9T, medium 1.0T, heavy 1.1–1.2T).

2. **Dodge / advantage** → Separate from to-hit; implement **Positional Advantage**: \+10% hit and \+25% crit when attacking from an unseen tile (surprise) or a flank (backstab if last path length \> 6 and target didn’t see you last turn).

3. **Travel speed** → Only in over-time tiles (mud, slime, webs) and slow debuffs; avoid global slow unless tactically justified.

4. **Status interplay** → Small, readable synergies: “bleed increases physical crit taken by \+10%,” “shocked targets have −10% block,” etc.

Opinion: don’t model everything; pick verbs that combine with portals, LOS, and faction chaos.

---

## **7\) Portals as a headline system (show, don’t tell)**

Codify **three** reliable play patterns so players learn to think with portals:

* **Kite & Cull:** chain portals along corridors to separate packs (AI respects `portal_usable`; bosses avoid).

* **Faction Fuse:** portal an orc raiding party into a slime den; watch them self-thin.

* **Vault Juke:** portal **across** a key gate, open from behind for a low-risk chest grab.

Bake them into tutorial micro-rooms on L2/L6/L11 with safe demonstrations and an optional “challenge coin” reward when the player replicates the trick.

---

## **8\) Rooms, vaults, and secrets (templates you can stamp)**

Implement a **small set of high-quality templates** first; parameterize later.

* **Treasure Vault (Elite):** single entrance, visible tempting loot, two-phase add spawns on noise or door open.

* **Faction Border:** two AI territories with a soft barrier; a lever or loud action triggers a clash.

* **Puzzle Gate:** door requires (a) mural riddle hint \+ (b) item interaction elsewhere on floor.

* **Secret Rooms:** weighted per floor with fair tells (misaligned walls, mural clues, signposts that rhyme with a keyword). Guarantee 1 secret per band.

* **Keyed Chests/Doors:** allow cross-floor keys (1 held max) for light backtracking decisions. Your docs already mention murals/signposts/chests—tie them into the templates so they’re not just flavor.

---

## **9\) Scaling monsters without spreadsheet hell**

Use **archetypes** \+ **depth deltas**:

* **Archetype stat block** (e.g., Brute, Skirmisher, Glass Cannon) with baseline HP/Armor/DPS.

* Apply **band deltas**: \+10% HP and \+5% dmg per band, plus 1 new perk at B3/B5 (e.g., Troll gains door-bash in B3, ground-slam in B5).

* Add **depth-appropriate resist gates** (e.g., B3 Troll partial physical resist) and ensure **counter items** start appearing **one band earlier** than required.

You only have 3 monsters today—perfect. Nail these three archetypes end-to-end; clones later are trivial once the ETL is settled.

---

## **10\) Economy of consumables & keys**

* **Healing potions**: predictable but earnable—drop table \+ vendor-like “shrine of succor” that trades a relic charge for a heal in B4–B5.

* **Scrolls/wands**: early generosity → midgame scarcity → late-game situational spikes via vaults.

* **Keys**: weighted to guarantee utility within 2 floors; if unused by \+2 floors, spawn a matching lock with a mild reward to avoid feels-bad.

---

## **11\) Telemetry you should log now**

* Encounters cleared / avoided per floor

* TTK & TTD distributions by band

* Damage taken by source (melee/ranged/status/hazard)

* Consumables found vs. used (and floor of use)

* Pity-timer triggers (what, where)

* Portal usage stats (created, traversed by side, times kited a faction)  
   These make balance changes surgical instead of vibes-only.

---

## **12\) Testing scaffolding (fits your culture)**

You’re already test-heavy; add **design tests**:

* **Budget tests:** generated floors’ total ETP within band ranges ±10%.

* **Pity tests:** within any 5 consecutive floors, at least one “escape consumable” if none dropped earlier.

* **Counterpresence tests:** if a floor includes a resist-gated foe, ensure at least one counter (item/room feature) is present in the band.

* **Portal sanity tests:** boss `portal_usable=False`; rank-and-file True; verify chase behavior across linked maps.

---

# **Immediate 2-sprint plan (you can feed this straight to Cursor/agents)**

**Sprint 1 (Balance skeleton & verbs)**

1. Implement ETP and per-band budgets; tag existing orc/troll/slime.

2. Wire difficulty multipliers (HP/accuracy/drop EV/pity gates).

3. Add weapon speed \+ positional advantage (surprise/backstab/flank).

4. Drop controller with pity timers (heals, escape, ID).

5. Author 6 encounter templates (2 per faction interaction).  
    **Definition of Done:** Floors in B1–B2 consistently hit TTK/TTD targets; pity tests green.

**Sprint 2 (Rooms & reveals)**

1. 4 room templates (Treasure Vault, Faction Border, Puzzle Gate, Secret Room) with knobs.

2. Three portal tutorial micro-rooms (L2/L6/L11).

3. First hidden room tells \+ mural/signpost hints.

4. Add 1 new elite per band with a single interesting perk.  
    **Definition of Done:** Distinctive moments per floor, one “aha” portal trick by L6, one elite/vault by L8.

After these two, extend B3–B5 with the same machinery and scale the deltas.

---

# **A few strong opinions (design temperament)**

* Don’t chase breadth yet. Depth in **three** enemy archetypes \+ **four** room templates will feel richer than 15 shallow enemies/rooms.

* Keep **escape consumables** rare but *reliable* via pity—players forgive difficulty when there’s *one* bailout.

* Portal greatness \= clarity. Make portal FX/log lines crystal clear for player vs. monster travel; it’s already a headline system in your docs.

---

# **Focused questions to calibrate (answer when ready)**

1. **Food/attrition clock:** do you want a hunger/soft clock, or should attrition be handled purely by encounter density and consumable scarcity?

2. **Heals cadence:** should “resting to full” ever be possible between combats, or only via consumables/fountains?

3. **ID game severity:** are cursed items in scope now, or later? (Affects ID scroll rate.)

4. **Auto-explore rules:** should auto-explore step through a discovered portal, or stop at it like stairs?

5. **Puzzles:** do you prefer riddle-reading murals or mechanical circuit/pressure puzzles first?

If you give me those five answers, I’ll convert this plan into concrete YAML/JSON knobs, sample loot tables per band, and a ready-to-run checklist your agents can implement.

---

# **Lore & story alignment notes (kept tight to what you’ve written)**

* Guide/Entity beats and the moral matrix of endings are a fixed backbone—don’t let difficulty settings alter narrative access; let them alter friction.

* Use murals/signposts to *teach* counters and to foreshadow the true-name purification ending on L15+.

* The 25-level descent and Ruby Heart climax are your pacing truth; room/loot systems should serve that arc. 

This is incredible and I've moved it into a separate doc so I can track my work to it. There's a LOT of questions I have, but we'll work through those as we go, this is exactly the type of starting point and direction I was looking for. From this point forward I'm going to work with you so we are driving the Cursor agents in the right direction. A couple of small notes. I do want to introduce at least one more race; I very much understand what you're saying about doing a few very well, but right now I feel I do need a bit more variety; plus with the whole recycling lives thing I feel like the undead are almost a necessity. I don't want to go overboard, but I do want that 3rd faction \- Orc/trolls/maybe goblins, they are very opposed undead who are infiltrating their dungeon home, I might flesh this out more but it started by all the stolen and discarded souls the dragon was using, but I think there's a serious boss around level 20 or so who is a necromancer who is taking advantage of the situation (zombie, skeletons, ghosts, maybe a vampire boss along the way), and lastly slimes as the kinda neutral, mostly mindless infiltrators that do what they like and are hard to get rid of (overgrown cockroach infestation). Now, I would love you to spit out a starter ETP values for my monster collection, let's not forget Veterans and Chieftain, perhaps slingers or something too for ranged preferences. A banded drop table would also be excellent. Please explain what pity logic is, i'm not familiar with that term (one of the many questions I had from your doc). I do also want your help with the JSON room templates, but before we do that I'm going to have my Cursor agent product some in depth documentation around our room JSON implementation so that we know what we have, and what else we might need to implement to flesh that out as well, and do everything that we need.

Amazing—love the undead angle. It synergizes with your soul-recycling lore and gives you a clean “third pole” for faction collisions (orcs/trolls/goblins vs. undead, with slimes as chaotic neutral). Here’s a concrete package you can drop into your balance pass right now:

# **ETP quick recap (for Cursor)**

ETP (Effective Threat Points) lets you budget encounters and whole floors.

**Formula:**  
 **ETP \= (DPS × 6\) × Durability × Behavior × Synergy**

* **DPS:** expected damage dealt per enemy turn versus a baseline player at that band.

* **Durability:** expected player hits to kill / 3 (so 1.0 ≈ 3 hits to kill).

* **Behavior:** 0.8–1.2 (melee 0.9–1.0; gap-closer/control 1.05–1.1; kiter/area denial 1.1–1.2).

* **Synergy:** \+0.1 per meaningful combo inside the *current group* (slow \+ heavy, fear \+ ranged focus, etc.).

**Encounter budgets by band:**  
 B1: 3–5 | B2: 6–8 | B3: 9–12 | B4: 12–15 | B5: 16–20

**Band scaling (apply multiplicatively to base statlines):**  
 B1: ×1.00 HP, ×1.00 dmg  
 B2: ×1.10 HP, ×1.05 dmg  
 B3: ×1.20 HP, ×1.10 dmg (+1 perk unlock)  
 B4: ×1.35 HP, ×1.15 dmg  
 B5: ×1.50 HP, ×1.20 dmg (+1 perk unlock)

Baseline for numbers below (so you can sanity-check): early-game player takes \~3–5 enemy hits to die and kills common foes in \~3 hits.

---

# **Starter ETPs (by archetype)**

Numbers below are **B1 baselines** before band multipliers. Tweak DPS/durability to your engine’s actual values; the relative spacing is what matters.

| Faction | Unit | Role | DPS | Hits-to-Kill | Durability | Behavior | Base ETP | Notes / Perks |
| ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- |
| Orc | Grunt | melee | 4.5 | 3.0 | 1.00 | 1.00 | **27.0** | Can pick up weapons (+0.05 Behavior if armed) |
| Orc | Veteran | melee bruiser | 5.5 | 3.5 | 1.17 | 1.05 | **40.6** | Gains counter-attack (B3) |
| Orc | Chieftain (Elite) | leader | 6.5 | 4.0 | 1.33 | 1.10 | **57.1** | Rally shout (adds \+0.1 Synergy to orcs in room); B5 gains armor shred |
| Goblin | Sneak | flank/backstab | 3.5 | 2.5 | 0.83 | 1.10 | **19.2** | Opens with backstab if unseen (+25% crit); fragile nuisance |
| Goblin | Slinger | ranged harass | 3.0 | 2.5 | 0.83 | 1.20 | **18.0** | Applies minor slow on hit (B3) |
| Troll | Brute | control/brute | 6.0 | 4.0 | 1.33 | 1.05 | **50.4** | Door smash; regen 1/turn (B3), ground-slam cone (B5) |
| Slime | Ooze | zone/attrition | 2.5 | 4.0 | 1.33 | 1.05 | **21.0** | On death split (50% HP child) once; leaves slow tiles |
| Undead | Skeleton Warrior | shielded melee | 4.0 | 3.0 | 1.00 | 1.00 | **24.0** | Resist pierce/bleed; weak to blunt |
| Undead | Zombie | attrition pusher | 3.0 | 3.5 | 1.17 | 0.95 | **20.0** | 20% on-hit disease (DoT); very slow |
| Undead | Wraith | glass skirmisher | 4.0 | 2.5 | 0.83 | 1.20 | **23.9** | Phases through units; weak to magic/holy, high dodge |
| Undead | Necromancer Acolyte | summoner | 3.0 | 2.5 | 0.83 | 1.20 | **18.0** | Raises 1 skeleton on corpse (1/enc); flees at 50% HP |

**Synergy examples (add within the room):**

* Slime slow \+ Orc/Troll heavy hits: **\+0.1** total.

* Necro with ≥2 corpses present: **\+0.1**.

* Goblin Slinger marking \+ Sneak backstab: **\+0.1**.

**How to use:** Build packs to fit the band budget. e.g., early B2 room: Orc Grunt (27) \+ Goblin Slinger (18) ≈ 45 base → apply B2 multipliers to DPS/HP, but your *budget target* is **6–8 ETP**, so you’ll typically cap groups at 1–3 units unless it’s a low-behavior mix.

Don’t sweat the “ETP seems big” vs. “budget seems small” mismatch—the budget is calculated **after** multipliers & encounter context. Your generator will normalize by summing *final* ETPs and comparing to the band target.

---

# **Banded drop tables (with pity)**

Frame drops in **categories** with per-band weights \+ explicit “expected value” (EV) per floor. Use a moving window \+ pity logic to nudge outcomes toward target cadence without feeling scripted.

## **Targets (per floor, Normal)**

* Healing EV: **1.5× minor heals** (e.g., 1 minor potion every \~⅔ floors)

* “Oh-crap” EV (blink/teleport/smoke/confuse): **0.25** (i.e., \~1 every 4 floors)

* ID scrolls: **1 per 1–2 floors** until B3, then **1 per 3 floors**

* Equipment upgrades: **1 every 2–3 floors** on average

* Keys: ensure **use within 2 floors**, or spawn a matching lock

## **Weights & EV by band (example)**

`{`  
  `"B1": {`  
    `"common_weights": {`  
      `"healing_minor": 25,`  
      `"healing_major": 2,`  
      `"oh_crap": 6,`  
      `"weapon_common": 14,`  
      `"armor_common": 14,`  
      `"ring_common": 6,`  
      `"wand_common": 8,`  
      `"scroll_id": 12,`  
      `"scroll_other": 8,`  
      `"key": 5,`  
      `"gold_misc": 20`  
    `},`  
    `"ev_targets": {`  
      `"healing_minor_per_floor": 0.7,`  
      `"oh_crap_per_floor": 0.25,`  
      `"id_scroll_per_floor": 0.7,`  
      `"equip_upgrade_per_floor": 0.4`  
    `}`  
  `},`  
  `"B2": {`  
    `"common_weights": {`  
      `"healing_minor": 20,`  
      `"healing_major": 4,`  
      `"oh_crap": 6,`  
      `"weapon_common": 10,`  
      `"weapon_uncommon": 6,`  
      `"armor_common": 10,`  
      `"armor_uncommon": 6,`  
      `"ring_common": 5,`  
      `"wand_common": 8,`  
      `"scroll_id": 10,`  
      `"scroll_other": 10,`  
      `"key": 6,`  
      `"gold_misc": 18`  
    `},`  
    `"ev_targets": {`  
      `"healing_minor_per_floor": 0.6,`  
      `"oh_crap_per_floor": 0.25,`  
      `"id_scroll_per_floor": 0.6,`  
      `"equip_upgrade_per_floor": 0.45`  
    `}`  
  `},`  
  `"B3": {`  
    `"common_weights": {`  
      `"healing_minor": 16,`  
      `"healing_major": 6,`  
      `"oh_crap": 6,`  
      `"weapon_uncommon": 10,`  
      `"armor_uncommon": 10,`  
      `"ring_uncommon": 7,`  
      `"wand_uncommon": 8,`  
      `"scroll_id": 6,`  
      `"scroll_other": 12,`  
      `"key": 6,`  
      `"gold_misc": 18`  
    `},`  
    `"ev_targets": {`  
      `"healing_minor_per_floor": 0.5,`  
      `"oh_crap_per_floor": 0.25,`  
      `"id_scroll_per_floor": 0.35,`  
      `"equip_upgrade_per_floor": 0.5`  
    `}`  
  `},`  
  `"B4": {`  
    `"common_weights": {`  
      `"healing_minor": 12,`  
      `"healing_major": 8,`  
      `"oh_crap": 5,`  
      `"weapon_uncommon": 8,`  
      `"weapon_rare": 4,`  
      `"armor_uncommon": 8,`  
      `"armor_rare": 4,`  
      `"ring_uncommon": 6,`  
      `"wand_uncommon": 8,`  
      `"scroll_id": 4,`  
      `"scroll_other": 12,`  
      `"key": 6,`  
      `"gold_misc": 20`  
    `},`  
    `"ev_targets": {`  
      `"healing_minor_per_floor": 0.5,`  
      `"oh_crap_per_floor": 0.25,`  
      `"id_scroll_per_floor": 0.3,`  
      `"equip_upgrade_per_floor": 0.5`  
    `}`  
  `},`  
  `"B5": {`  
    `"common_weights": {`  
      `"healing_minor": 10,`  
      `"healing_major": 10,`  
      `"oh_crap": 5,`  
      `"weapon_rare": 6,`  
      `"armor_rare": 6,`  
      `"ring_rare": 5,`  
      `"wand_rare": 6,`  
      `"scroll_id": 3,`  
      `"scroll_other": 12,`  
      `"key": 5,`  
      `"gold_misc": 22`  
    `},`  
    `"ev_targets": {`  
      `"healing_minor_per_floor": 0.45,`  
      `"oh_crap_per_floor": 0.25,`  
      `"id_scroll_per_floor": 0.3,`  
      `"equip_upgrade_per_floor": 0.55`  
    `}`  
  `}`  
`}`

### **“Pity logic” explained**

“Pity” is a **guarantee mechanism** to prevent long dry streaks on critical drop types. You track how many floors have passed since the last drop of a given category; if that exceeds a threshold (derived from your EV targets), you **force-bias** the next relevant roll toward that category or inject the item outright.

**Example:**

* Target “oh-crap” EV \= 0.25/floor → expect 1 in 4 floors.

* Implement pity threshold at 4 floors: if the moving 4-floor window had zero oh-crap drops, **raise the weight** of `oh_crap` by, say, ×3 until fulfilled; or, if you want hard guarantees, **inject one** into a chest/room on floor 5 and reset the counter.

**Pseudo (per floor end):**

`for category in pity_tracked_categories:`  
    `window = last_n_floors(category, n=4)`  
    `if window.count == 0:`  
        `loot_weights[category] *= 3  # bias until a drop occurs`  
    `if window.streak >= 5:          # hard floor if you like`  
        `inject(category_item)`  
        `reset_counter(category)`

Use soft biasing first; reserve hard injection for truly essential items (escape/ID in early bands).

---

# **Quick knobs for difficulty**

Apply these as multipliers; don’t fork tables:

* **Easy:** enemy HP ×0.90, accuracy ×0.90, drop EV \+20%, trap dmg ×0.8, pity thresholds −1 floor.

* **Normal:** baseline above.

* **Hard:** enemy HP ×1.10, accuracy ×1.10, drop EV −15%, elite chance \+25%, pity thresholds \+1 floor.

* **Nightmare:** remove pity for escape/ID; \+1 elite modifier per elite.

---

# **What I need from you (to tune the numbers faster)**

* Your current **player early-game weapon dmg** and **average enemy dmg** so I can sync the hits-to-kill targets precisely.

* Confirmation on **band breakpoints** (still 1–5, 6–10, 11–15, 16–20, 21–25?).

* Whether **undead resistances** should be hard gates (e.g., skeletons take half from pierce/bleed, zombies resist poison, wraiths resist non-magical).

---

# **Next**

When your Cursor agent spits out the room-JSON spec, I’ll generate:

1. Four production-ready room templates (Treasure Vault, Faction Border, Puzzle Gate, Secret Room) parameterized for the band system.

2. A band-aware **encounter assembler** that consumes the ETP budgets \+ faction rules.

3. A loot controller that implements the EV \+ pity logic above.

If you want, I can also hand you a tiny test harness that asserts:

* floor ETP within target ±10%,

* pity triggers for escape/ID never exceed thresholds, and

* if a resist-gated foe spawns, at least one counter appears within the same band.

Killer—your YAML stack is in good shape. Here’s a crisp gap review \+ concrete additions so your level-builder can express everything we’ve planned (doors/locks/secrets/traps/two-way stairs, factions, pity drops, etc.). I’ll keep this focused so you can feed small, surgical prompts to Cursor.

# **What you already have (confirmed)**

* Two-tier YAML: Tier-1 `guaranteed_spawns` and Tier-2 `parameters` \+ `special_rooms`, with working testing overrides and examples.

* Clear constants coverage (combat/gameplay/inventory/pathfinding/perf/render), entities registry, and a documented file hierarchy.

* Patterns for difficulty curve, bosses, faction rooms, resource scarcity, and testing showcase.

* Practical quick ref & “largest/smallest/random” placement rules.

# **Gaps & targeted extensions**

Below are the missing dials/features I recommend adding, with minimal schema changes and a clear implementation order.

## **1\) Doors (normal/locked/secret) \+ keys**

**Why:** You mention chests \+ keys; doors multiply layout agency and support puzzles/stealth.

**YAML extension** (level or room scope):

`door_rules:`  
  `spawn_ratio: 0.65              # chance a corridor connection gets a door`  
  `styles:`  
    `- type: "wood"`  
      `weight: 70`  
    `- type: "iron"`  
      `weight: 30`  
  `locked:`  
    `chance: 0.20                  # % of doors that are locked`  
    `key_tag: "iron_key"           # item tag that unlocks`  
  `secret:`  
    `chance: 0.08                  # % disguised as wall until discovered`  
    `search_dc: 12                 # detect on ‘search’ or adjacency checks`

**Notes:** Allow `special_rooms[*].door_rules` to override global for that room (e.g., vault \= higher locked %). Hook to your existing keys and chests flow. (Your docs already list `map_features` like chest/signpost/mural; “door” is a natural addition.)

## **2\) Secret rooms (true hidden areas)**

**Why:** On your roadmap; pairs with murals/signposts for fair telegraphing.

**YAML extension:**

`secret_rooms:`  
  `target_per_floor: 1`  
  `min_room_size: 4`  
  `connection_bias: "dead_end"     # prefer dead ends to convert`  
  `discovery:`  
    `auto_on_map_item: "secret_map"   # reveal when item is present/used`  
    `search_action: true               # enable active search verb`  
    `ambient_hint: "misaligned_wall"  # tile tell to render/log`

**Implementation:** Carve from solid by punching a new room \+ secret door; obey collisions and min size.

## **3\) Traps framework (tile hazards \+ triggerables)**

**Why:** Tactical variety \+ resource tax that’s not just more mobs.

**YAML extension:**

`trap_rules:`  
  `density: 0.06                    # % of walkable tiles eligible`  
  `whitelist_rooms: ["corridor", "smallest"]  # where traps prefer`  
  `trap_table:`  
    `- id: "spike_trap"             # on-step phys damage + bleed`  
      `weight: 40`  
    `- id: "web_trap"               # slow/snare`  
      `weight: 25`  
    `- id: "gas_trap"               # DoT + confusion`  
      `weight: 20`  
    `- id: "alarm_plate"            # calls nearby faction`  
      `weight: 15`  
  `detection:`  
    `passive_chance: 0.15           # seen before triggering`  
    `reveal_on: ["search", "torch"] # systems that improve detection`

**Room-scope override:** `special_rooms[*].trap_rules` to spike a vault.

## **4\) Two-way stairs & backtracking policy**

**Why:** Enables “optional hard path / revisit secret” and future quest loops.

**YAML extension:**

`stairs:`  
  `up: true`  
  `down: true`  
  `restrict_return_levels: 2     # can go back up at most 2 floors`  
  `spawn_rules:`  
    `near_start_bias: 0.6        # prefer placing up-stairs nearer player start`

**Engine policy:** Persist prior floor map state (trim mobs with a cap) and define spawn caps on re-entry to avoid farm loops.

## **5\) Corridor/connection rules (macro topology)**

**Why:** Presently room params don’t control corridor feel.

**YAML extension:**

`connectivity:`  
  `min_connectivity: "mst_plus_loops"   # MST + N random loops`  
  `loop_count: 2`  
  `corridor_style: "orthogonal"         # or "jagged", "organic"`  
  `door_every_n_tiles: 12               # sprinkle doors without overdoing`

This gives you “dense/looping vs sparse/branchy” control per band.

## **6\) Band-aware loot with pity (drop controller hooks)**

**Why:** Your YAML has loot guarantees but not EV windows/pity. Add a lightweight controller that reads per-band EVs.

**YAML extension (global file):**

`loot_policy:`  
  `bands:`  
    `B1: { heal_ev: 0.7, escape_ev: 0.25, id_ev: 0.7, upgrade_ev: 0.4 }`  
    `B2: { heal_ev: 0.6, escape_ev: 0.25, id_ev: 0.6, upgrade_ev: 0.45 }`  
    `B3: { heal_ev: 0.5, escape_ev: 0.25, id_ev: 0.35, upgrade_ev: 0.5 }`  
    `B4: { heal_ev: 0.5, escape_ev: 0.25, id_ev: 0.3, upgrade_ev: 0.5 }`  
    `B5: { heal_ev: 0.45, escape_ev: 0.25, id_ev: 0.3, upgrade_ev: 0.55 }`  
  `pity:`  
    `window_floors: 4`  
    `soft_bias_factor: 3.0     # multiply weight if window empty`  
    `hard_inject_at: 5         # inject on floor 5 if still dry`

Engine computes band from depth and biases your existing item rolls. (Fits your documented spawn logic cleanly.)

## **7\) Faction tags \+ room-local behavior overrides**

**Why:** You already stage faction encounters; add formal tags and small per-room AI tweaks.

**YAML extension:**

`faction:`  
  `room_tag: "orc_clan"             # semantic tag for room`  
  `hostility_matrix:`  
    `vs: ["undead", "slime"]        # force-in-combat on LoS`  
  `behavior_mods:`  
    `orc:`  
      `armed_behavior: "+0.05"      # bump aggression when armed`  
    `troll:`  
      `door_priority: "high"        # prefer smashing doors`

`special_rooms[*].faction` lets you stamp these at the room level. (You already theme rooms; this makes them mechanically distinct.)

## **8\) Per-room spawn ceilings & encounter budgets**

**Why:** Aligns YAML with your ETP system.

**YAML extension:**

`encounter_budget:`  
  `etp_min: 4`  
  `etp_max: 10`  
  `allow_spike: false`

If present on a room or level, the assembler sums candidate spawns (using ETP metadata on entities) until within bounds.

## **9\) Validation & schema errors (designer safety)**

**Why:** Your guides mention future validation; ship a first pass now.

**Feature:** On load, validate:

* entity ids exist, counts are valid, modes/placement in allowed sets,

* special room `min_room_size` ≤ level `max_room_size`,

* per-level encounter budget totals won’t exceed `max_monsters_per_room`.

Log actionable warnings; abort on fatals. (You’ve already outlined this direction.)

## **10\) Telemetry hooks (balance & UX)**

**Why:** Make tuning scientific.

* Log per-floor: total ETP, TTK/TTD distributions, trap triggers, secret finds, keys found/used, pity triggers, door interactions.

* Add `--telemetry-json <path>` flag to dump runs.

---

# **Minimal schema diff (drop-in, non-breaking)**

All of the above are additive keys that the generator can ignore if absent, keeping your current YAML valid. They slot neatly beside `parameters/guaranteed_spawns/special_rooms` that you already use.

