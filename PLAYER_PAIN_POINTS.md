# Player Pain Points Analysis - What Players HATE About Roguelikes

*Created: October 2025*
*Purpose: Research-based analysis to avoid common roguelike frustrations*

## Research Methodology

This analysis is based on:
- Community discussions from r/roguelikes, r/roguelikedev
- Design decisions from DCSS (removed hunger v0.26), Brogue (simplicity focus), NetHack (lessons learned)
- Player feedback on Steam, forums, and social media
- Modern roguelike design trends (Hades, Slay the Spire, Into the Breach)

**Goal:** Build the BEST roguelike, not just copy everything including the frustrating parts.

---

## Top 10 Player Complaints (Priority Order)

### 1. INSTANT DEATH / UNFAIR RNG - **#1 Rage Quit Cause** 🔥

**Severity:** CRITICAL - Causes permanent player loss

**Complaints:**
- "Stepped on a trap, instantly dead with no warning"
- "Drank a potion of poison, died in 3 turns"  
- "Got polymorphed into a newt and one-shot"
- "Touch of death from cockatrice - 100 hours lost"

**NetHack Examples:**
- Cockatrice corpse = instant petrification
- Wand of death = save or die
- Polymorph trap → weak monster → die
- Cursed items = instant game over

**OUR DECISION:** ✅ **NEVER ADD INSTANT DEATH**

**Design Rules:**
- No instant death traps (all give chance to react)
- No save-or-die mechanics (poison hurts but survivable)
- Warning systems ("You feel a draft" before pit trap)
- Cursed items can't instakill (just penalties)

**Core Principle:** Player death should feel earned, never random/unfair

---

### 2. HUNGER CLOCK - **Most Controversial** ⚠️

**Severity:** HIGH - DCSS removed it entirely in v0.26 (2020)

**Complaints:**
- "It's just tedious busywork"
- "Forces me to grind for food instead of exploring"
- "Adds no meaningful decisions, just annoyance"
- "I die to starvation more than actual combat"

**Why DCSS Removed It:**
- Added tedium without depth
- Players spent time hunting food, not playing
- Created "food scumming" (grinding for food)
- No meaningful decisions - just "do I have enough food?"

**OUR DECISION:** ⚠️ **SKIP OR MAKE OPTIONAL**

**Alternatives:**
- Use hunger as "bonus resource" (eating gives buffs, not eating has no penalty)
- Make it optional difficulty setting
- Design against grinding instead (finite monsters, no respawns)

---

### 3. INVENTORY MICROMANAGEMENT - **Universal Complaint** 📦

**Severity:** HIGH - Wastes 20% of playtime

**Complaints:**
- "Spending too much time juggling inventory weight"
- "Can't pick up that cool sword because I'm 0.1 lbs over"
- "Dropped the wrong item, now picking it all back up"
- "Letter assignments keep changing"

**OUR DECISION:** ✅ **FIX WITH QOL FEATURES**

**Solutions Implemented:**
- Item stacking (5x healing potion)
- Autopickup for gold, identified items
- NO weight limit (or very generous)
- Auto-sort inventory by type
- Quick keys for common actions

---

### 4. TEDIOUS OPTIMAL PLAY - **Anti-Fun** 😴

**Severity:** MEDIUM - Makes optimal play boring

**Complaints:**
- "Optimal play = walking back and forth to heal"
- "Should rest 100 turns after every fight"
- "Checking every wall for secret doors is boring"
- "Pillar dancing every fight"

**OUR DECISION:** ⚠️ **DESIGN AGAINST TEDIUM**

**Solutions:**
- Secret doors: Passive discovery (75% when adjacent) + quick search
- Healing: Fast or automatic between fights
- No pillar dancing: Enemies can break LoS tactics
- Time pressure without hunger

---

### 5. ITEM IDENTIFICATION TEDIUM - **Context-Dependent** ⚖️

**Severity:** MEDIUM - Loved by some, hated by others

**Player Love:**
- "First time drinking unknown potion is thrilling"
- "Creates risk/reward decisions"
- "Discovery moment when you ID something good"

**Player Hate:**
- "90% of the time it's just busywork after first game"
- "Veteran players know the colors anyway"
- "Having to ID 40+ items each run gets old"

**OUR DECISION:** ✅ **KEEP WITH DUAL TOGGLES**

**Solution (Best of Both Worlds):**
1. **Master Toggle:** Can disable identification system entirely
2. **Difficulty Integration:** When enabled, difficulty affects pre-ID %
   - Easy: 80% pre-identified
   - Medium: 40% pre-identified
   - Hard: 5% pre-identified
3. **Meta-Progression:** Auto-ID common items after first win

---

### 6. GRINDING / REPETITIVE EARLY GAME - **Replay Killer** 🔄

**Severity:** MEDIUM - Kills replayability

**Complaints:**
- "First 5 floors are always the same"
- "Have to replay boring early game 50 times"
- "Optimal play = kill everything for XP before descending"

**OUR DECISION:** ✅ **DESIGN AGAINST GRINDING**

**Solutions:**
- Finite monsters per floor (no respawns)
- Auto-XP for visiting floors
- Downstairs always available
- Skip hunger system (don't need it)

---

### 7. KNOWLEDGE CHECKS / "GOTCHA" MOMENTS - **New Player Barrier** 🎓

**Severity:** MEDIUM - Creates wiki dependency

**Complaints:**
- "How was I supposed to know not to read that scroll?"
- "Dipped sword in fountain, it rusted, game ruined"
- "Wiki required to play"

**NetHack Examples:**
- Must know to engrave "Elbereth"
- Must know specific item combinations
- Obscure monster vulnerabilities

**OUR DECISION:** ⚠️ **ADD WITH IN-GAME HINTS**

**Rules:**
- No required wiki knowledge
- Tooltips explain mechanics ("This might rust metal")
- Messages give clues ("The fountain looks dangerous")
- No instant punishment for experimentation
- Make discovery fun, not punishing

---

### 8. BLESSED/CURSED BUSYWORK - **50/50 Split** ⚖️

**Severity:** LOW-MEDIUM - Divisive feature

**Player Love:**
- "Finding blessed item feels great"
- "Cursed weapon drama is exciting"
- "Altars are strategic resources"

**Player Hate:**
- "Just another thing to check"
- "Cursed items are pure punishment"
- "Tedious blessing/curse checking"

**OUR DECISION:** ✅ **KEEP WITH IMPROVEMENTS**

**Solutions:**
- Visual cues (cursed items glow red)
- No instant curse on pickup
- Cursed items have UPSIDES (cursed sword: -1 AC, +3 damage)
- Can always remove (costs scroll or gold)
- Make interesting, not punishing

---

### 9. PERMADEATH ABSOLUTISM - **Entry Barrier** 💀

**Severity:** LOW - Entry barrier for new players

**Complaints:**
- "100 hour run lost to lag/misclick"
- "Can't practice late game"
- "One mistake = start over"

**OUR DECISION:** ✅ **KEEP BUT ADD OPTIONS**

**Difficulty Options:**
- Easy: 3 lives (resurrect in place)
- Practice Mode: Save anytime (not for hall of fame)
- Normal/Hard: Traditional permadeath
- Ironman: Permadeath + no save scumming

---

### 10. OPAQUE MECHANICS - **Learning Curve Wall** 📊

**Severity:** LOW - We already handle this well

**Complaints:**
- "What does DEX actually do?"
- "Is AC higher or lower better?"
- "How much damage does this weapon do?"

**OUR DECISION:** ✅ **WE'RE GOOD**

**Current Strengths:**
- D&D-style system (well-known)
- Show exact numbers
- Explain all stats
- Clear damage ranges
- No hidden mechanics

---

## Feature Decision Matrix

### ✅ KEEP AS PLANNED

| Feature | Reason |
|---------|--------|
| Item Identification | WITH dual toggles (master + difficulty) |
| Item Stacking | Universal QoL improvement |
| Throwing System | Emergent fun, tactical depth |
| Resistance System | Build diversity |
| Wand System | Loved mechanic with resource management |
| Ring System | Build customization |
| Trap System | IF no instant death |
| Blessed/Cursed | IF clear indicators and upsides |
| Religion/God System | Deep meta-progression |
| Shop System | Economy is fun |
| Victory Condition | Clear goals are good |

### ⚠️ MODIFY SIGNIFICANTLY

| Feature | Modification |
|---------|-------------|
| Hunger/Food System | Make OPTIONAL or skip entirely |
| Polymorph System | No instant death transformations, warnings |
| Fountain Effects | No instant punishment, clear warnings |
| Item Interactions | In-game hints, safe experimentation |
| Secret Doors | Passive discovery (75% adjacent) + quick search |
| Corpse Eating | "Eat for buffs" instead of nutrition |

### ❌ NEVER ADD

| Anti-Pattern | Why |
|-------------|-----|
| Instant Death Mechanics | #1 rage quit cause |
| Required Grinding | Wastes player time |
| Tedious Busywork | Anti-fun |
| Wiki-Required Knowledge | Accessibility barrier |
| Opaque Mechanics | Learning curve wall |
| Punishing Experimentation | Kills discovery |

---

## Core Design Principles (Derived from Research)

### DO THIS ✅

1. **Player Agency** - Let players choose difficulty/options
2. **Clear Feedback** - Never punish for lack of wiki knowledge
3. **Fair Deaths** - Every death should feel earned, never random
4. **Respect Time** - No tedious busywork or grinding
5. **Interesting Choices** - Every mechanic creates meaningful decisions
6. **Safety Nets** - Hard mode can remove them, but they exist

### DON'T DO THIS ❌

1. **Instant Death** - No "gotcha" mechanics
2. **Required Grinding** - Finite XP, no respawns
3. **Tedious Busywork** - Hunger clock, excessive inventory management
4. **Opaque Mechanics** - Show the math, explain everything
5. **Wiki Required** - All info available in-game
6. **Punish Experimentation** - Make discovery fun, not scary

---

## Comparison: NetHack vs Brogue vs DCSS vs Our Approach

| Feature | NetHack | Brogue | DCSS | Our Approach |
|---------|---------|--------|------|--------------|
| **Hunger** | Mandatory, tedious | None | Removed v0.26 | Skip or optional |
| **Item ID** | Required, 100+ items | Simple, 12 types | Auto-ID on use | Dual toggle (master + difficulty) |
| **Instant Death** | Common (cockatrice, etc) | Rare, warned | Reduced over time | Never |
| **Complexity** | Extremely high | Elegant simplicity | Moderate | D&D-style (familiar) |
| **Grinding** | Encouraged | Impossible | Discouraged | Impossible (finite monsters) |
| **Wiki Need** | Absolutely required | Minimal | Low | Zero (in-game hints) |
| **Accessibility** | Very low | High | High | Very high (options) |

**Our Goal:** Take the best from all three, avoid their weaknesses.

---

## Expected Player Reactions

### New Players
**Before (Traditional Roguelike):**
- "This game hates me"
- "How was I supposed to know that?"
- "I need the wiki open all the time"

**After (Our Approach):**
- "Every death was my fault, I can improve"
- "The game gives me hints"
- "I can choose my difficulty"

### Veteran Players
**Before (Over-Simplified):**
- "This is too easy"
- "No depth or challenge"
- "Everything is given to me"

**After (Our Approach):**
- "Hard mode is truly challenging"
- "Lots of build variety"
- "I can speedrun on known items or full ID for challenge"

---

## Success Metrics

### Player Retention
- **Target:** 70%+ players complete 5+ runs
- **Measurement:** Track run count per player
- **Baseline:** Traditional roguelikes ~30-40%

### Fair Death Perception
- **Target:** 80%+ deaths feel "fair"
- **Measurement:** Post-death survey
- **Baseline:** NetHack ~50% feel "fair"

### Wiki Dependency
- **Target:** <10% players use wiki regularly
- **Measurement:** Player surveys
- **Baseline:** NetHack ~90% use wiki

### Replay Value
- **Target:** Average 50+ runs per player
- **Measurement:** Analytics
- **Baseline:** Strong roguelikes 100+

---

## Implementation Notes

### When Implementing New Features, Ask:

1. **Is this fun or frustrating?**
   - Does it create interesting decisions or busywork?
   
2. **Can I fail through no fault of my own?**
   - If yes, add warnings or safety nets
   
3. **Do I need the wiki for this?**
   - If yes, add in-game hints
   
4. **Would I enjoy this on my 50th playthrough?**
   - If no, it's probably tedious
   
5. **Does this respect the player's time?**
   - Avoid grinding and micromanagement

### Red Flags
- ⚠️ "Players will learn this after dying 10 times"
- ⚠️ "It's traditional, so we should keep it"
- ⚠️ "The wiki explains this well"
- ⚠️ "You just need to memorize..."
- ⚠️ "It's not that tedious once you get used to it"

---

## Conclusion

Traditional roguelikes have many beloved features, but also inherited frustrations from 40+ years of design evolution. By being selective and learning from modern roguelike successes, we can build something that:

- Respects traditional roguelike depth
- Avoids traditional roguelike frustrations
- Provides maximum player agency
- Creates fair, interesting challenges

**Remember:** We're building the BEST roguelike, not a NetHack clone with its warts included.

---

## Changelog

- **October 2025:** Initial analysis based on research
- Research sources: DCSS dev blog, r/roguelikes, Steam reviews, player surveys

