# Traditional Roguelike Features - Design Document

*Last Updated: October 2025 - Post Boss Fights v3.9.0*

## Executive Summary

This document outlines 35+ beloved features from classic roguelikes (NetHack, DCSS, Brogue, Caves of Qud, ADOM) that would elevate Catacombs of Yarl from a solid roguelike to one of the best traditional roguelikes ever made.

**Current Strengths:**
- Excellent D&D-style combat system (d20, AC, dice notation)
- Strong equipment foundation (12 weapons, armor, 5 slots)
- Good spell variety (8 scrolls) with tactical depth
- Boss fights with dialogue and phases
- Loot quality system (4 rarity tiers)

**Critical Gaps:**
- **Discovery:** No item identification system (THE defining roguelike mechanic)
- **Resource Management:** No hunger/food system, limited charge-based items
- **Build Diversity:** Missing rings, amulets, resistances, blessed/cursed
- **Emergent Gameplay:** No item interactions, throwing, polymorphing
- **Meta-Progression:** No religion/god system, achievements

---

## TIER 1: Essential Roguelike Features (Quick Wins)

### 1. Item Identification System ⭐⭐⭐⭐⭐

**Impact:** CRITICAL - This is THE defining roguelike mechanic
**Effort:** 1-2 weeks
**Priority:** #1

#### Why This Matters
Every legendary roguelike has unidentified items. It creates:
- Exciting risk/reward decisions ("Should I drink this unknown potion?")
- Discovery moments that create player stories
- Replay value (potion colors randomize each game)
- Strategic resource management (identify scrolls are valuable)

#### Design
- **Scrolls:** Appear as "scroll labeled XYZZY" or "scroll labeled PRATYAVAYAH"
  - Random labels per game (20+ possible labels)
  - Once used/identified, all scrolls of that type are known
  - Identify scroll reveals one item type
  
- **Potions:** Appear as "blue potion" or "bubbling yellow potion"
  - 10+ colors/descriptions
  - Drinking identifies the potion type
  - Risky but necessary
  
- **Rings/Wands (future):** Similar system

#### Configuration Options
**IMPORTANT: Implement with configurable toggle for accessibility**

Add to `config/game_constants.yaml`:
```yaml
identification_system:
  enabled: true  # Master toggle for entire identification system
  auto_identify_scrolls: false  # If true, all scrolls start identified
  auto_identify_potions: false  # If true, all potions start identified
  auto_identify_rings: false    # If true, all rings start identified (future)
  auto_identify_wands: false    # If true, all wands start identified (future)
```

**Use Cases:**
- `enabled: false` - Traditional gameplay (all items identified by default)
- `enabled: true, auto_identify_scrolls: true` - Only scrolls need identification
- `enabled: true` (all auto_identify: false) - Full roguelike experience

**Why This Matters:**
- Accessibility for players who don't want uncertainty
- Difficulty mode foundation (Easy = auto-identify ON, Hard = OFF)
- Matches modern roguelikes (DCSS has similar option)
- Allows gradual feature rollout (enable for scrolls first, then expand)

#### Implementation
**Core System:**
- Add `identified` boolean to Item component
- Add `appearance` field (random per game, saved with run)
- Add `item_type` field ("scroll", "potion", "ring", "wand")
- Modify rendering to show appearance vs real name based on `identified` flag

**Identification Configuration:**
- Load settings from `game_constants.yaml`
- Store in `GameState` for runtime access
- Check `identification_system.enabled` before applying unidentified state
- Check item-specific auto-identify flags when creating items

**Item Creation Flow:**
```python
def create_scroll(scroll_type, x, y):
    scroll = Item(...)
    
    # Check if identification system is enabled
    if game_constants.identification_system.enabled:
        # Check if this item type should auto-identify
        if not game_constants.identification_system.auto_identify_scrolls:
            scroll.identified = False
            scroll.appearance = get_random_scroll_appearance()
        else:
            scroll.identified = True
    else:
        # Identification system disabled, all items start identified
        scroll.identified = True
    
    return scroll
```

**Identification Methods:**
- Use item (auto-identifies)
- Read scroll of identify
- Visit shop (shopkeeper IDs for fee)
- **Configuration can bypass all of this if enabled**

#### Technical Notes
- Appearance mapping stored in game state
- Persists across save/load
- New game = new randomization (if enabled)
- Configuration file allows runtime toggle without code changes
- Easy to extend with difficulty modes later

---

### 2. Item Stacking ⭐⭐⭐⭐

**Impact:** HIGH - Quality of life, standard in all roguelikes
**Effort:** 1 week
**Priority:** #2

#### Why This Matters
Without stacking:
- Inventory fills with 10x healing potions taking 10 slots
- Frustrating management
- Players avoid picking up duplicates

With stacking:
- "5x healing potion" takes 1 slot
- Clean inventory
- Standard expectations met

#### Design
- Stackable: Potions, scrolls, food, ammunition (future)
- Non-stackable: Equipment, unique items
- Show count: "healing potion (x5)"
- Use one from stack
- Drop quantity selector

#### Implementation
- Add `quantity` field to Item
- Add `stackable` boolean
- Modify inventory add logic to merge stacks
- Update UI to show counts
- Add quantity selection for drop/use

---

### 3. Throwing System ⭐⭐⭐⭐

**Impact:** HIGH - Tactical depth, emergent gameplay
**Effort:** 1 week
**Priority:** #5

#### Why This Matters
Enables creative tactics:
- Throw healing potion at enemy (heals them, wastes potion BUT might pacify)
- Throw confusion potion to shatter on impact
- Throw daggers for ranged damage
- Throw items into lava/pits

#### Design
- Press 't' to enter throw mode
- Target with mouse or arrow keys
- Potions shatter on impact (apply effect to target tile)
- Weapons deal reduced damage
- Heavy items stun
- Items land on ground if missed

#### Implementation
- New throw mode in input handler
- Projectile trajectory calculation (straight line)
- Impact effects based on item type
- Animation (optional): flying item graphic

---

### 4. Resistance System ⭐⭐⭐⭐

**Impact:** HIGH - Build diversity, equipment strategy
**Effort:** 1-2 weeks
**Priority:** #4

#### Why This Matters
Creates meaningful equipment choices:
- Fire resistance for dragon fights
- Poison resistance for swamps
- Cold resistance for ice levels
- Electric resistance for shocking enemies

Makes loot more interesting:
- "Flaming Sword of Fire Resistance +2"
- "Cloak of Poison Immunity"

#### Design
- Resistance types: Fire, Cold, Poison, Electric, Acid
- Levels: None (100% damage), Resistant (50%), Immune (0%)
- Sources: Equipment, rings, potions (temporary)
- Monster resistances too

#### Implementation
- Add Resistance component with dict of types
- Modify damage calculation to check resistances
- Add resistance fields to equipment definitions
- Visual indicator on character screen

---

### 5. Scroll/Potion Variety ⭐⭐⭐⭐

**Impact:** HIGH - Replay value, discovery
**Effort:** 1-2 weeks  
**Priority:** #3

#### Current State
8 scrolls: Healing, Lightning, Fireball, Confusion, Teleport, Shield, Raise Dead, Dragon Fart

#### Expansion Plan
**New Scrolls (12 total, 20 target):**
- Identify (reveals item type)
- Remove Curse (frees cursed equipment)
- Magic Mapping (reveals level layout)
- Create Monster (spawns random creature)
- Enchant Weapon (permanent +1 damage)
- Enchant Armor (permanent +1 AC)
- Summon Demon (powerful ally, might turn)
- Genocide (eliminate one monster type)
- Charging (recharge wand)
- Light (illuminates area)
- Darkness (blinds nearby)
- Amnesia (forget mapped areas)

**New Potions (15 target):**
- Healing (current)
- Speed (double movement)
- Poison (take damage)
- Confusion (become confused)
- Levitation (fly over hazards)
- Strength (temporary +STR)
- Detect Objects (see items)
- Detect Monsters (see all monsters)
- ESP (see through walls)
- Blindness (lose vision)
- Paralysis (can't move)
- Gain Level (instant XP)
- Holy Water (bless items)
- Unholy Water (curse items)
- Restore Ability (cure stat drain)

---

### 6. Vault System ⭐⭐⭐⭐

**Impact:** HIGH - Memorable moments, risk/reward
**Effort:** 1-2 weeks
**Priority:** #9

#### Why This Matters
Special rooms that create stories:
- "I found the treasure vault with 3 trolls and 5 legendary items!"
- Risk/reward decisions
- Excitement of discovery
- Breaks up procedural monotony

#### Design
- 10-15 vault templates
- 5-10% chance per level
- Types:
  - **Treasure Vault:** Lots of items, tough guards
  - **Monster Zoo:** Packed with enemies
  - **Trap Maze:** Loot behind trap gauntlet
  - **Shrine:** Altar with divine rewards
  - **Armory:** All weapons/armor
  - **Library:** All scrolls
  - **Potion Shop:** All potions

#### Implementation
- Pre-designed room templates (YAML)
- Special vault generation logic
- Locked doors (require keys or break down)
- Vault-specific monster spawns
- Guaranteed high-quality loot

---

### 7. Secret Doors ⭐⭐⭐

**Impact:** MEDIUM-HIGH - Exploration rewards
**Effort:** 1 week
**Priority:** #10

#### Design
- Appear as walls until discovered
- 10% chance to find when adjacent
- Press 's' to actively search (100% in radius)
- Lead to bonus rooms, shortcuts, vaults
- Visual hint when found (highlight/different tile)

#### Implementation
- SecretDoor tile type
- Search command reveals in radius
- Passive discovery when walking past
- Becomes normal door when found

---

### 8. Corpse System ⭐⭐⭐

**Impact:** MEDIUM - Resource management, flavor
**Effort:** 1-2 weeks
**Priority:** #15

#### Design
- Dead monsters leave corpses
- Press 'e' to eat corpse
- Effects:
  - Nutrition (if hungry)
  - Gain temporary ability (eat dragon = fire resistance)
  - Get sick (old corpse, poison)
  - Trigger events (eating human = god anger)
- Corpses decay over 100-500 turns
- Visual: % symbol

#### Implementation
- Corpse entity on death
- Timer component for decay
- Eat action with effect table
- Integration with hunger system (future)

---

## TIER 2: Major Systems (Core Depth)

### 9. Hunger/Food System ⭐⭐⭐⭐⭐

**Impact:** CRITICAL - Tension, prevents grinding
**Effort:** 2-3 weeks
**Priority:** #6

#### Why This Matters
Creates time pressure:
- Can't rest forever
- Can't grind same level repeatedly
- Must balance exploration vs hunger
- Food becomes a resource to manage

#### Design
- Hunger states: Satiated > Normal > Hungry > Weak > Fainting > Starving
- Lose 1 nutrition per turn (adjustable)
- Hungry: Warning messages
- Weak: -2 to-hit, -2 damage
- Fainting: Random paralysis
- Starving: 1 HP damage per turn
- Food sources:
  - Rations (500 nutrition)
  - Corpses (100-300 nutrition, risks)
  - Fruit (50 nutrition)
  - Bread (150 nutrition)

#### Implementation
- Hunger component on player
- Tick every turn
- Status effects at thresholds
- Food items restore nutrition
- UI hunger indicator
- Balance: ~500 turns between meals

---

### 10. Blessed/Cursed Items ⭐⭐⭐⭐⭐

**Impact:** CRITICAL - Equipment puzzle, depth
**Effort:** 2-3 weeks
**Priority:** #11

#### Why This Matters
Adds equipment risk:
- Find awesome sword... it's cursed! (-1, can't remove)
- Bless your gear for extra power
- Curse removal is valuable
- Altars become strategic resources

#### Design
- States: Blessed (+1 bonus), Uncursed (normal), Cursed (-1, can't unequip)
- Visual indicator: blessed (glowing), cursed (dark)
- Effects:
  - **Blessed weapon:** +1 to-hit, +1 damage
  - **Blessed armor:** +1 AC
  - **Cursed:** Negative bonuses, CANNOT REMOVE
- Sources:
  - Random on generation (5% blessed, 10% cursed, 85% normal)
  - Altars (bless/curse items)
  - Holy water (bless)
  - Scroll of remove curse (uncurse)

#### Implementation
- BUC (Blessed/Uncursed/Cursed) state on items
- Modify stat calculations
- Block unequip if cursed
- Altar interactions
- Scroll of remove curse

---

### 11. Religion/God System ⭐⭐⭐⭐⭐

**Impact:** CRITICAL - Meta-progression, replay value
**Effort:** 3-4 weeks
**Priority:** #12

#### Why This Matters
Adds strategic layer:
- Choose god at start or first altar
- Build favor through play
- Pray for help in emergencies
- Divine gifts reward faithful play
- Different gods = different builds

#### Design
**Gods (3-5 initial):**

1. **Tyr (Law)** - God of Justice
   - Likes: Killing evil, protecting innocents
   - Dislikes: Stealing, harming neutrals
   - Gifts: Blessed weapons, holy protection
   - Power: Smite evil (damage undead/demons)

2. **Loki (Chaos)** - Trickster God
   - Likes: Chaos, random actions, risks
   - Dislikes: Boring safe play
   - Gifts: Random polymorphs, wild magic
   - Power: Chaos bolt (random effect)

3. **Gaia (Nature)** - Earth Mother
   - Likes: Preserving nature, eating natural food
   - Dislikes: Killing animals unnecessarily
   - Gifts: Natural resistances, regeneration
   - Power: Summon animals

#### Mechanics
- **Favor:** 0-100 scale
- **Gain favor:**
  - Sacrifice items at altar (+5-20)
  - Act according to god's values
  - Convert enemy altars
- **Lose favor:**
  - Act against god's values
  - Ignore altar when passing
- **Prayer:** (once per 1000 turns)
  - High favor: Divine intervention (heal, teleport to safety, gift)
  - Low favor: Punishment (curse items, spawn monsters)

#### Implementation
- Religion component on player
- God definitions (YAML)
- Altar entities on levels (10% spawn rate)
- Favor tracking
- Prayer cooldown
- Divine effects

---

### 12. Shop System ⭐⭐⭐⭐

**Impact:** HIGH - Economy, resource conversion
**Effort:** 2-3 weeks
**Priority:** #13

#### Why This Matters
- Convert items to gold, gold to items
- Identify items (shopkeeper knows all)
- Strategic: What to buy/sell?
- Risk: Shopkeepers are TOUGH if attacked

#### Design
- Shops spawn on ~20% of levels
- Types: General, Weapon, Armor, Scroll, Potion, Magic
- Shopkeeper NPC (HP: 100, Damage: 20-30, won't leave shop)
- Inventory: 10-15 random items
- Prices:
  - Buy from shop: 2x base value
  - Sell to shop: 0.5x base value
  - Identify: 100 gold

#### Implementation
- Shopkeeper entity (special AI: won't leave room)
- Shop room template
- Buy/sell UI
- Gold system (already exists?)
- Item valuation
- Theft = shopkeeper turns hostile

---

### 13. Wand System ⭐⭐⭐⭐

**Impact:** HIGH - Reusable magic, resource management
**Effort:** 2 weeks
**Priority:** #7

**Note:** Wand component already exists in codebase!

#### Design
**15 Wand Types:**
- Fire (fireball)
- Cold (ice bolt)
- Lightning (chain lightning)
- Death (instant kill, rare)
- Polymorph (change target)
- Teleportation (blink target)
- Slow (reduce speed)
- Speed (increase speed)
- Digging (create tunnels)
- Striking (force bolt damage)
- Wishing (1-2 charges, ultra rare)
- Sleep (put to sleep)
- Cancellation (remove magic)
- Create Monster (spawn creature)
- Charging (recharge other wands)

#### Mechanics
- Start with 3-10 charges
- Zap with 'z' key
- Recharging risky (might explode: 1d6 damage)
- Some wands affect user if misused
- Can zap self for beneficial effects

#### Implementation
- Already have wand.py component!
- Need to:
  - Create wand items in entities.yaml
  - Add zap action to input handler
  - Implement each wand effect
  - Add recharge scroll
  - Balance charges

---

### 14. Ring System ⭐⭐⭐⭐

**Impact:** HIGH - Build customization
**Effort:** 2-3 weeks
**Priority:** #8

#### Design
**Ring Types (15 total):**

Beneficial:
- Regeneration (restore 1 HP per turn)
- Protection (+2 AC)
- Strength (+2 STR)
- Dexterity (+2 DEX)
- See Invisible (detect invisible monsters)
- Teleport Control (choose teleport destination)
- Free Action (immune to paralysis)
- Fire Resistance
- Cold Resistance
- Poison Resistance
- Searching (auto-find secret doors)

Mixed/Cursed:
- Hunger (2x nutrition loss, but +1 speed)
- Aggravate Monster (monsters spawn faster)
- Teleportation (random teleport every 50-100 turns)

#### Mechanics
- 2 ring slots (left/right hand)
- Passive effects always active
- Cursed rings can't be removed
- Some have drawbacks

#### Implementation
- Add RING_LEFT and RING_RIGHT equipment slots
- Ring item definitions
- Passive effect system
- Auto-trigger effects each turn

---

### 15. Amulet System ⭐⭐⭐

**Impact:** MEDIUM-HIGH - Power spikes
**Effort:** 2 weeks
**Priority:** #14

#### Design
**Amulet Types (10 total):**
- Life Saving (auto-resurrect once, then crumbles)
- Reflection (reflect ranged attacks)
- ESP (see all monsters through walls)
- Strangulation (cursed: lose HP every turn)
- Unchanging (immune to polymorph)
- Magical Breathing (no need for air)
- Flying (levitation permanent)
- Versus Poison (poison immunity)
- Guarding (monsters less likely to attack)
- Restful Sleep (regenerate 2x when resting)

#### Implementation
- AMULET equipment slot
- Similar to rings (passive effects)
- Life saving is special case (trigger on death)

---

### 16. Trap System ⭐⭐⭐⭐

**Impact:** HIGH - Danger, rewards caution
**Effort:** 2-3 weeks
**Priority:** #10

#### Design
**Trap Types (10 total):**
- Dart Trap (1d4 damage)
- Pit Trap (1d6 damage, fall to lower level)
- Teleport Trap (random teleport)
- Polymorph Trap (transform temporarily)
- Fire Trap (2d6 fire damage, burns items)
- Sleeping Gas (paralysis 5-10 turns)
- Arrow Trap (1d8 damage)
- Bear Trap (stuck for 1d4 turns)
- Rust Trap (damages equipment)
- Magic Trap (random effect)

#### Mechanics
- Hidden until triggered or searched
- Press 's' to search (reveal traps in radius)
- 10% passive detection when adjacent
- Can trigger intentionally (useful for teleport trap)
- Rogues better at detecting

#### Implementation
- Trap entities (invisible until detected)
- Trigger on movement
- Search action
- Disarm action (skill check)
- Each trap effect

---

### 17. More Status Effects ⭐⭐⭐

**Impact:** MEDIUM-HIGH - Tactical depth
**Effort:** 2-3 weeks
**Priority:** #16

#### Current Effects
Invisibility, Confusion, Shield, Disorientation

#### New Effects
- **Poison:** 1 HP damage per turn, 10-20 turns
- **Disease:** -2 all stats, lasts until cured
- **Paralysis:** Can't move, vulnerable to attacks
- **Blindness:** No FOV, can only see adjacent
- **Levitation:** Fly over hazards/water, can't pick up items
- **Haste:** 2 actions per turn
- **Slow:** 1 action per 2 turns
- **Regeneration:** +1 HP per turn
- **Detect Monsters:** See all monsters through walls
- **Berserk:** +4 STR/DEX, -4 INT, attack everything

#### Implementation
- Extend StatusEffect system
- Add duration timers
- Visual indicators
- Cure methods (potions, scrolls, rest)

---

### 18. Polymorph System ⭐⭐⭐⭐

**Impact:** HIGH - Unique mechanic, power fantasy
**Effort:** 3-4 weeks
**Priority:** #17

#### Why This Matters
Legendary roguelike moments:
- Turn into dragon, breathe fire
- Become troll, regenerate like crazy
- Transform enemy into newt
- Polymorph trap chaos

#### Design
- Duration: 50-200 turns
- Gain monster's abilities
- Keep items (drop if incompatible)
- Return to normal after duration or death
- Sources: Wand, potion, trap, scroll

#### Implementation
- Store original form
- Replace Fighter stats with monster stats
- Replace AI with monster AI (player still controls)
- Special abilities available
- Complex: Monster → Player controller

---

## TIER 3: Depth Systems (Advanced)

### 19. Wish/Genie System ⭐⭐⭐⭐⭐

**Impact:** LEGENDARY - Memorable moments
**Effort:** 1-2 weeks
**Priority:** #18

#### Why This Matters
Players remember their wishes FOREVER:
- "I wished for Excalibur!"
- "I wasted my wish on food..."
- Creates legendary moments
- Shows trust in players

#### Design
- Wand of Wishing (1-2 charges, ultra rare)
- Magic Lamp (releases genie, 3 wishes)
- Player types what they want
- Interpretation system:
  - Exact match: Grant item/effect
  - Close match: Grant similar
  - Greedy: Curse or punish
  - Vague: Random

#### Implementation
- Text input dialog
- Item/effect database for matching
- Generation system
- Wish parser with fuzzy matching
- Limited per game (find 1-2 sources max)

---

### 20. Item Interaction System ⭐⭐⭐⭐

**Impact:** HIGH - Emergent gameplay
**Effort:** 3-4 weeks
**Priority:** #19

#### Design
**Dipping:**
- Dip weapon in potion → Apply effect
  - Health potion = heal on hit (3 charges)
  - Poison = poison damage
  - Fire = flaming weapon
- Dip item in fountain → Random effect
- Dip cursed item in holy water → Remove curse

**Mixing:**
- Mix 2 potions → New potion or explosion
- Experimentation encouraged

**Applying:**
- Apply poison to food → Poisoned food
- Apply oil to weapon → Lights on fire

#### Implementation
- Dip command ('D')
- Apply command ('A')
- Effect system for combinations
- Save mixed potions

---

### 21. Unique Artifacts ⭐⭐⭐⭐

**Impact:** MEDIUM-HIGH - Chase items
**Effort:** 2-3 weeks
**Priority:** #20

#### Design
**Artifacts (10 legendary items):**
- **Excalibur:** +5 longsword, lawful only, silver, +5 vs undead
- **Mjolnir:** +5 warhammer, returns when thrown, lightning damage
- **Stormbringer:** +7 greatsword, life drain, evil alignment
- **Grimtooth:** +3 dagger, poison on hit, backstab damage
- **Dragonbane:** +5 spear, +10 vs dragons, fire resistance
- **Sunsword:** +4 longsword, light radius, undead bane
- **Frostbrand:** +3 longsword, cold damage, cold immunity
- **Grayswandir:** +5 shortsword, silver, accurate
- **Staff of the Magi:** +7 quarterstaff, spell power, mana regen
- **Vorpal Blade:** +5 longsword, 5% instant death

#### Mechanics
- Can't spawn randomly
- Found in specific vaults, boss drops, quest rewards
- One per game (unique)
- Special abilities

---

### 22. Digging/Tunneling ⭐⭐⭐

**Impact:** MEDIUM - Player agency
**Effort:** 2-3 weeks
**Priority:** #21

#### Design
- Pickaxe item or Dig spell/wand
- Press 'd' + direction to dig
- Takes 3-5 turns
- Creates passage through rock
- Can't dig through special walls
- Uses:
  - Escape when trapped
  - Shortcut to vault
  - Bypass monsters
  - Reach inaccessible areas

#### Implementation
- Dig action
- Wall replacement with floor
- Time delay (multiple turns)
- Noise (attracts monsters)

---

### 23. Fountain Effects ⭐⭐⭐

**Impact:** MEDIUM - Risk/reward, flavor
**Effort:** 1-2 weeks
**Priority:** #22

#### Design
- Fountains spawn on ~15% of levels
- Press 'D' to drink
- Effects (random):
  - Restore HP
  - Gain level
  - Detect treasure
  - Wish (1% chance!)
  - Water demon (hostile)
  - Dry up (no more uses)
  - Poison
  - Curse items
- Can dip items for effects
- Fountains can be used 1-5 times

#### Implementation
- Fountain tile/entity
- Drink action
- Effect table with probabilities
- Use counter

---

### 24. Monster Special Abilities ⭐⭐⭐⭐

**Impact:** HIGH - Monster variety
**Effort:** 2-4 weeks
**Priority:** #23

#### New Monster Types
- **Nymphs:** Steal items and teleport away
- **Leprechauns:** Steal gold
- **Rust Monsters:** Corrode equipment on hit
- **Wraiths:** Drain max HP (permanent until restore)
- **Liches:** Summon undead
- **Mind Flayers:** Int drain, confusion attack
- **Kobolds:** Poison darts from range
- **Jellies:** Split when hit
- **Mimics:** Appear as items

#### Implementation
- New AI behaviors
- Special attack effects
- Stat drain mechanics
- Equipment damage system (extend existing corrosion)

---

### 25. Victory Condition/Ascension ⭐⭐⭐⭐

**Impact:** HIGH - Sense of completion
**Effort:** 2-3 weeks
**Priority:** #24

#### Design
- Goal: Retrieve Amulet of Yendor from level 25+
- Return to surface
- Escape with amulet = WIN
- Victory screen:
  - Final stats
  - Play time
  - Kills
  - Level reached
  - Score calculation
- Hall of Fame (persistent)
- Difficulty multipliers

#### Implementation
- Amulet item (quest item, can't drop)
- Win condition check (have amulet, reach level 1, use stairs up)
- Victory screen UI
- Score system
- Save to hall of fame file

---

### 26. Morgue Files ⭐⭐⭐

**Impact:** MEDIUM - Community, learning
**Effort:** 1-2 weeks
**Priority:** #25

#### Design
- On death, dump character info to text file
- Contents:
  - Final stats
  - Equipment
  - Inventory
  - Kill count
  - Deepest level
  - Cause of death
  - Turn count
  - Timeline of major events
- Saved to `morgue/` folder
- Filename: `charactername_YYYYMMDD_HHMMSS.txt`
- Can share with others

#### Implementation
- Character dump function
- Trigger on death
- Text file generation
- Event log system

---

### 27. Swarm Mechanics ⭐⭐⭐

**Impact:** MEDIUM - Tactical variety
**Effort:** 1-2 weeks
**Priority:** #26

#### Design
- Swarm monsters: Rats, Bats, Insects
- Spawn in groups of 5-15
- Individually weak (1-3 HP, 1-2 damage)
- Dangerous in numbers
- Fast movement
- Run away at low HP

#### Implementation
- New monster types
- Swarm spawn logic (create group)
- Flee AI when damaged
- Balance: Many weak vs few strong

---

## Implementation Priority Matrix

### Phase 1: Core Identification & QoL (Weeks 1-6)
**Goal:** Add THE essential roguelike mechanic and basic improvements

1. Item Identification System (2 weeks) - THE defining feature
2. Item Stacking (1 week) - Quality of life
3. Scroll/Potion Variety (2 weeks) - Content for identification
4. Resistance System (1 week) - Build diversity foundation

### Phase 2: Resource Management (Weeks 7-13)
**Goal:** Add strategic depth and tension

5. Throwing System (1 week) - Tactical options
6. Hunger/Food System (3 weeks) - Time pressure
7. Wand System (2 weeks) - Reusable magic
8. Corpse System (1 week) - Food integration

### Phase 3: Build Diversity (Weeks 14-20)
**Goal:** Make character builds matter

9. Ring System (3 weeks) - Passive builds
10. Amulet System (2 weeks) - Power spikes
11. Blessed/Cursed Items (2 weeks) - Equipment puzzle

### Phase 4: World Depth (Weeks 21-30)
**Goal:** Make the world feel alive

12. Trap System (3 weeks) - Danger
13. Vaults & Secret Doors (2 weeks) - Discovery
14. Shop System (3 weeks) - Economy
15. Religion/God System (4 weeks) - Meta-progression

### Phase 5: Advanced Mechanics (Weeks 31-45)
**Goal:** Add legendary features

16. More Status Effects (3 weeks)
17. Polymorph System (4 weeks)
18. Item Interaction System (4 weeks)
19. Unique Artifacts (3 weeks)
20. Monster Special Abilities (3 weeks)

### Phase 6: Completion Systems (Weeks 46-52)
**Goal:** Polish and victory

21. Victory Condition/Ascension (3 weeks)
22. Fountain Effects (1 week)
23. Digging/Tunneling (2 weeks)
24. Wish/Genie System (2 weeks)
25. Morgue Files (1 week)

---

## Integration with Existing Roadmap

### Already Planned Features (Keep These)
- Difficulty Selection (1-2 weeks) - Complements all systems
- Player Profiles/Achievements (2-3 weeks) - Works with morgue files
- Player Classes (4-6 weeks) - Enhances replayability with new systems
- Ranged Weapons (2-3 weeks) - Complements throwing system
- Player Naming (1 week) - Quality of life

### Synergies
- **Item ID + Blessed/Cursed:** Unknown if blessed/cursed until identified
- **Hunger + Corpses:** Food source with risks
- **Throwing + Potions:** Tactical potion use
- **Rings + Resistances:** Build customization
- **Vaults + Traps:** Dangerous treasure hunting
- **Gods + Altars:** Strategic resource points
- **Wands + Shops:** Economic resource management

---

## Success Metrics

### Depth Score Target
| System | Current | Target | Impact |
|--------|---------|--------|--------|
| Discovery | 2/10 | 10/10 | +Item ID, unknown effects, secret areas |
| Resource Management | 3/10 | 9/10 | +Hunger, wand charges, identify scrolls |
| Build Diversity | 5/10 | 9/10 | +Rings, resistances, blessed/cursed, gods |
| Emergent Gameplay | 4/10 | 9/10 | +Throwing, item interactions, polymorph |
| Memorable Moments | 6/10 | 10/10 | +Wishes, polymorph, vaults, divine intervention |

### Player Experience Goals
1. **"I wonder what this potion does?"** - Identification system
2. **"I need food NOW"** - Hunger tension
3. **"Should I pray or save it?"** - God system decisions
4. **"I got a wish!"** - Legendary moments
5. **"This ring changed my build"** - Equipment synergies
6. **"That vault was worth the risk"** - Exploration rewards

---

## Conclusion

These 35+ features represent what makes traditional roguelikes beloved by players worldwide. Implementing them in order of Impact vs Effort will transform Catacombs of Yarl from a solid roguelike into one of the best traditional roguelikes ever made.

**Next Immediate Action:** Start with Item Identification System (Week 1-2)

The journey to becoming a legendary roguelike begins with the question: "I wonder what this blue potion does?"

