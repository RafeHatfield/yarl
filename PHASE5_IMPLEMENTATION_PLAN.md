# 🐉 Phase 5: The Five Endings - Implementation Plan

**Status:** In Progress  
**Start Date:** October 27, 2025  
**Goal:** Implement all six ending paths with boss fights and story resolution

---

## 📖 Story Context

See `STORY_LORE_CANONICAL.md` for full backstory.

**TL;DR:**
- Zhyraxion & Aurelyn (partner dragons) caught in Crimson Order ritual
- Aurelyn destroyed, Ruby Heart extracted
- Zhyraxion partially bound (can't leave, can't shapeshift)
- Player must retrieve Aurelyn's Ruby Heart from Level 25
- Final confrontation offers 6 different endings

---

## 🎯 The Six Endings

### 1a. ⚔️ Escape Through Battle (Neutral-Good)
- Keep Heart → Refuse Transform → Fight
- **Boss: Human Zhyraxion** (Medium-Hard)
- Style: Fast, technical, pattern-based (Dark Souls)
- Victory: Escape with heart, Zhyraxion stays trapped

### 1b. 💀 Crimson Collector (Secret Dark)
- Keep Heart → Use Ritual Knowledge
- **Requires:** `crimson_ritual_knowledge` from secret room
- No fight: ritual sequence
- Victory: Extract both hearts, dark power ending

### 2. 🐉 Dragon's Bargain (Bad - Trapped)
- Keep Heart → Accept Transformation
- No fight: cutscene of curse transfer
- Defeat: You become trapped, Zhyraxion freed with Rickman wit

### 3. ☠️ Fool's Freedom (Bad - Unwinnable)
- Give Heart Immediately
- **Boss: Full Dragon Zhyraxion** (EXTREME)
- Style: Overwhelming, massive damage, area attacks
- Expected: Death (0.1% win for "Dragonslayer" achievement)

### 4. 🔥 Mercy & Corruption (Tragic)
- Destroy Heart (no true name)
- **Boss: Grief-Corrupted Dragon** (Hard)
- Style: Erratic, unpredictable, berserker rage
- Victory: Escape but at horrific cost (destroyed his connection to partner)

### 5. ✨ Sacrifice & Redemption (Best)
- Destroy Heart (WITH true name "ZHYRAXION")
- **Requires:** `entity_true_name_zhyraxion` from Guide (Level 15)
- No fight: golden light cutscene
- Victory: Everyone freed, dragons reunited

---

## 🏗️ Architecture Overview

```
Level 25 Vault
    ↓
[Pick up Ruby Heart]
    ↓
[Portal Appears]
    ↓
[OPTIONAL: Explore for Secret Room]
    ↓ (if found)
[Fight Corrupted Ritualists]
    ↓
[Get Crimson Ritual Codex]
    ↓
[Enter Portal]
    ↓
Confrontation Chamber
    ↓
[Zhyraxion Dialogue]
    ↓
[CHOICE MENU]
    ↓
┌─────────┬─────────┬─────────┐
│  KEEP   │  GIVE   │ DESTROY │
└─────────┴─────────┴─────────┘
    ↓         ↓         ↓
[Sub-Menu] [Ending 3] [Check Name]
    ↓                   ↓
┌───┬───┬───┐      ┌──────┬──────┐
│ 1a│ 2 │1b │      │ Has  │ No   │
└───┴───┴───┘      └──────┴──────┘
  ↓   ↓   ↓          ↓       ↓
Fight Cut. Ritual  End.5   End.4
```

---

## 📋 Implementation Tasks

### **Phase 5.1: Ruby Heart & Portal System**

#### Task 1.1: Create Ruby Heart Entity
**File:** `config/entity_factory.py` or new items config

```python
# Ruby Heart - Aurelyn's extracted dragon heart
"ruby_heart": {
    "name": "Aurelyn's Ruby Heart",
    "description": "A dragon's heart, crystallized into ruby. It pulses with inner fire, warm to the touch, beating with a rhythm that isn't quite alive but isn't quite dead either. You can feel immense power thrumming through it.",
    "char": "*",
    "color": (255, 0, 0),  # Bright red
    "item": {
        "use_function": None,  # Cannot be used like normal items
        "targeting": False
    },
    "triggers_victory": True,  # Triggers portal spawn
    "blocks": False
}
```

**Features:**
- Glowing animation (pulse effect?)
- Special pickup message
- Cannot be dropped once picked up
- Triggers portal spawn on pickup

#### Task 1.2: Portal System
**File:** `victory_manager.py` or new `ending_manager.py`

**Functionality:**
1. When Ruby Heart picked up → Spawn portal entity
2. Portal entity on same level (near stairs?)
3. Entering portal → Transition to confrontation chamber
4. Optional: Message about secret room if player hasn't found it

**Portal Entity:**
- Glowing, animated portal sprite
- Interact with 'G' or click to enter
- "Step through portal?" confirmation

---

### **Phase 5.2: Secret Room (Ending 1b Unlock)**

#### Task 2.1: Hidden Passage
**File:** `map_objects/game_map.py` Level 25 template

**Trigger:**
- After Ruby Heart pickup, secret wall becomes passable
- Or: Secret door appears/unlocks
- Visual cue: Faint glow, different tile color

**Location:**
- Hidden in vault level
- Requires exploration (not directly on path to portal)

#### Task 2.2: Corrupted Ritualists
**File:** `config/entity_factory.py`

```python
"corrupted_ritualist": {
    "name": "Corrupted Ritualist",
    "description": "A mad remnant of the Crimson Order, corrupted by Aurelyn's absorbed power. Flesh rotting, eyes glowing, mumbling about 'the completion'.",
    "char": "R",
    "color": (150, 0, 150),  # Purple
    "ai": "basic_monster",
    "fighter": {
        "hp": 120,  # Tough!
        "defense": 12,
        "power": 18
    },
    "xp": 500,
    "dialogue": {
        "on_spot": ["Two... need two...", "Complete... the ritual...", "Hearts... both hearts..."]
    }
}
```

**Fight:**
- 2-3 ritualists
- Difficult but fair
- Maybe some special abilities (drain? curse?)

#### Task 2.3: Crimson Ritual Codex
**File:** `config/entity_factory.py`

```python
"crimson_ritual_codex": {
    "name": "Crimson Ritual Codex",
    "description": "An ancient journal detailing the dragon-binding ritual. The final entry reads: 'The ritual succeeded beyond measure. One heart extracted, one dragon bound. If only there were two...'",
    "char": "?",
    "color": (139, 0, 0),  # Dark red
    "item": {
        "use_function": "unlock_ritual_knowledge"
    }
}
```

**Effect:**
- Unlocks `crimson_ritual_knowledge` flag in player's knowledge
- Enables Ending 1b option in confrontation menu
- Cannot be dropped

---

### **Phase 5.3: Confrontation Chamber**

#### Task 3.1: Chamber Map
**File:** New map template or special room

**Description:**
- Circular room
- Ritual circles still glowing on floor (ominous)
- Aurelyn's remains/ashes in center (pile of golden scales?)
- Zhyraxion standing in human form, waiting
- No exits (no escape until choice made)

**Atmosphere:**
- Dim lighting except for ritual circles
- Heavy, oppressive feeling
- Zhyraxion's dialogue establishes mood

#### Task 3.2: Zhyraxion Entity (Human Form)
**File:** `config/entity_factory.py`

```python
"zhyraxion_human": {
    "name": "Zhyraxion",
    "description": "The Entity, revealed in his true form: a dragon bound into a rotting human shell. His eyes betray centuries of grief and rage.",
    "char": "Z",
    "color": (200, 50, 50),
    "ai": "boss_ai",  # If we have one
    "fighter": {
        "hp": 200,
        "defense": 15,
        "power": 25
    },
    "boss": {
        "boss_name": "Zhyraxion, the Bound",
        "boss_type": "dragon_human",
        "enrage_threshold": 0.5,
        "dialogue": {
            "spawn": ["So... you have it. After all these centuries."],
            "hit": ["You dare strike me?!", "Impressive. But futile."],
            "enrage": ["ENOUGH! I've waited TOO LONG!"],
            "low_hp": ["This... this cannot... not after everything..."],
            "death": ["Aurelyn... I tried... I'm sorry..."]
        }
    },
    "blocks": True
}
```

**Combat Style (Ending 1a):**
- Fast attacks
- Pattern-based (telegraph, then strike)
- Dodge windows (player can learn patterns)
- Technical, requires skill
- Medium-Hard difficulty

---

### **Phase 5.4: Choice Menu System**

#### Task 4.1: Confrontation Dialogue
**File:** New `screens/confrontation_screen.py` or extend `screens/`

**Dialogue Flow:**
```
Zhyraxion: "You have it. Aurelyn's heart. Give it to me. Please."

Player sees Ruby Heart pulsing in hands.

Zhyraxion: "I've waited centuries. Do you have any idea what it's like? To be so close to what you need, but unable to reach it?"

[Pause for effect]

Zhyraxion: "Give me the heart. I'll free us both. We can escape together."

[Choice Menu Appears]
```

#### Task 4.2: Choice Menu
**File:** `screens/confrontation_screen.py`

**Main Menu:**
```
╔═══════════════════════════════════════╗
║   What will you do with the heart?    ║
╠═══════════════════════════════════════╣
║ (K) Keep the heart                    ║
║ (G) Give it to Zhyraxion              ║
║ (D) Destroy the heart                 ║
╚═══════════════════════════════════════╝
```

**Keep Sub-Menu:**
```
╔═══════════════════════════════════════╗
║      You grip the heart tightly.      ║
║     Zhyraxion's eyes narrow...        ║
╠═══════════════════════════════════════╣
║ (F) Fight him for your freedom        ║
║ (A) Accept his transformation offer   ║
║ (R) Use the ritual (if unlocked)      ║
║ (B) Back                              ║
╚═══════════════════════════════════════╝
```

**Destroy Sub-Menu:**
```
╔═══════════════════════════════════════╗
║   You raise the heart to destroy it   ║
╠═══════════════════════════════════════╣
║ (Y) Speak his true name (if known)    ║
║ (N) Just destroy it                   ║
║ (B) Back                              ║
╚═══════════════════════════════════════╝
```

**Conditional Options:**
- "Use the ritual" only shown if `crimson_ritual_knowledge` flag set
- "Speak his true name" only shown if `entity_true_name_zhyraxion` flag set
- Otherwise greyed out or hidden

---

### **Phase 5.5: Boss Fights**

#### Task 5.1: Human Zhyraxion Boss (Ending 1a)
**Fight Style:** Dark Souls inspired
- Fast, deliberate attacks
- Telegraphed moves (visual cue before strike)
- Patterns player can learn
- Windows for counterattack
- Enrages at 50% HP (faster attacks)

**Attacks:**
- Claw Swipe (quick, short range)
- Lunge (telegraphed, longer range)
- Fury Combo (3-hit when enraged)
- Desperate Strike (low HP, high damage)

**Difficulty:** Medium-Hard
- Beatable with skill and good gear
- Fair but punishing

#### Task 5.2: Full Dragon Zhyraxion (Ending 3)
**Fight Style:** Overwhelming spectacle
- MASSIVE HP pool (500+)
- High defense
- Devastating attacks
- Area-of-effect damage
- Fire breath (multi-tile)
- Tail swipe (knockback)
- Wing buffet (pushes player back)

**Difficulty:** EXTREME (Nearly Impossible)
- Designed to kill player
- 0.1% chance to win with perfect play + god-tier RNG
- Victory grants "Dragonslayer" achievement

**Special:** If player somehow wins:
- Special victory text
- Collect both hearts (like Ending 1b)
- Hall of Fame marker

#### Task 5.3: Grief-Corrupted Dragon (Ending 4)
**Fight Style:** Berserker
- Partial dragon transformation (incomplete)
- Erratic, unpredictable attacks
- No clear patterns (madness)
- Fast but vulnerable (damaged form)
- Self-damaging rage attacks

**Attacks:**
- Wild Slash (random direction)
- Grief Roar (AOE fear/damage)
- Reckless Charge (telegraphed but fast)
- Death Throes (when low HP, berserker mode)

**Difficulty:** Hard
- Very difficult but beatable
- Requires good gear and skill
- More forgiving than Full Dragon
- Unpredictability is the challenge

**Balance Note:** Needs careful tuning between Human (Medium-Hard) and Full Dragon (Impossible)

---

### **Phase 5.6: Ending Cutscenes & Screens**

#### Ending 1a: Escape Through Battle
**Cutscene:**
```
Zhyraxion falls, defeated.

"You... you would condemn me... to stay here... forever?"

He collapses, still breathing but broken.

You grip the Ruby Heart and turn away.

The portal shimmers, offering escape.

Behind you, Zhyraxion's voice, barely a whisper:
"Aurelyn... I tried... I'm sorry..."

You step through the portal.

The last thing you hear is his anguished cry,
fading as the portal closes behind you.

You're free.

But at what cost?
```

**Victory Screen:**
- Title: "ESCAPE - Freedom Through Strength"
- Stats shown
- Hall of Fame entry
- Moral weight: Grey (you condemned him)

#### Ending 1b: Crimson Collector
**Cutscene:**
```
You place Aurelyn's heart on the ritual circle.

The ancient symbols flare to life.

Zhyraxion: "What... what are you doing?"

You begin the ritual chant from the codex.

"No. NO! You can't—"

The ritual binds him, just as it bound Aurelyn.

His screams echo through the chamber as you
complete what the Crimson Order started.

Minutes later, you hold TWO ruby hearts,
both pulsing in your hands.

Immense power flows through you.

The portal opens—but it's different now.
Darker. Red-tinted.

You step through, leaving behind the ashes
of two ancient dragons.

You've become what the ritualists wanted to be.
```

**Victory Screen:**
- Title: "ASCENSION - The Crimson Collector"
- Dark red theme
- Special achievement: "Following in Their Footsteps"
- Unsettling victory music
- Stats with "Dragon Hearts Collected: 2"

#### Ending 2: Dragon's Bargain
**Cutscene:**
```
Zhyraxion smiles.

"You're smarter than the others. Why be a puppet
when you could be a DRAGON?"

He gestures to the heart.

"Touch it. Take the power. We'll BOTH escape."

You reach out... the heart pulses... power floods
through your veins...

Your form shifts. Scales emerge. Wings unfurl.

For one glorious moment, you ARE a dragon.

Then you feel it.

The binding curse. Transferring. Snapping shut
around YOUR soul instead of his.

Zhyraxion transforms before your eyes, his true
dragon form restored.

"Oh, don't look so betrayed. I offered you EXACTLY
what I promised: dragon transformation. Not MY fault
you didn't read the fine print about the binding curse."

He stretches his wings.

"Marvelous view from up here, isn't it? The sky,
the freedom... I'll visit when I'm bored. Might be
a few centuries. You understand, I'm sure."

He flies away, leaving you trapped in the chamber
that held him for so long.

Forever.
```

**Defeat Screen:**
- Title: "BOUND - The Dragon's Bargain"
- Dark ending theme
- Player trapped
- Final line: "Ta-ta!"

#### Ending 3: Fool's Freedom (Expected: Death)
**Cutscene:**
```
You hand the Ruby Heart to Zhyraxion.

"YES! FINALLY! After all these centuries..."

He absorbs the heart, and power erupts from him.

His human shell SHATTERS.

What emerges is an ANCIENT DRAGON.

Massive. Terrible. Glorious.

He spreads his wings and roars.

You realize your mistake.

[BOSS FIGHT: Full Dragon]

[Expected Outcome: Death]

You are crushed beneath dragon claws.

As your vision fades, you see him fly away,
not even acknowledging your existence.

"...Finally. Aurelyn, I'm coming."

Your soul joins the Guide's.

Just another failure in the collection.
```

**Death Screen:**
- Standard death but with special text
- "You trusted the dragon. The dragon did not care."
- Achievement: "Fool's Bargain"

**IF PLAYER SOMEHOW WINS:**
- Special text: "You did the impossible."
- Achievement: "DRAGONSLAYER" (gold)
- Both hearts collected
- Hall of Fame special marker: "⚔️ DRAGONSLAYER"

#### Ending 4: Mercy & Corruption
**Cutscene:**
```
You raise the Ruby Heart and SHATTER it.

Golden essence explodes outward.

Zhyraxion: "NO! WHAT HAVE YOU—AURELYN!"

His scream of anguish is inhuman.

The binding breaks from the sheer force of his grief.

His form twists, shifts, transforms.

But it's WRONG. Corrupted. Incomplete.

What emerges is a GRIEF-MAD dragon,
twisted by centuries of suffering and rage.

[BOSS FIGHT: Grief-Corrupted Dragon]

[Difficult but Winnable]

You defeat him.

As he falls, his eyes clear for just a moment.

"You... destroyed... her heart..."

"The only... thing I had left... of her..."

He dies, broken twice over.

You escape.

But the cost...

The cost was too high.
```

**Victory Screen:**
- Title: "FREEDOM - The Cruelest Mercy"
- Somber tone
- Stats shown
- Achievement: "Tragic Hero"
- Heavy moral weight text

#### Ending 5: Sacrifice & Redemption
**Cutscene:**
```
You raise the Ruby Heart.

Zhyraxion tenses: "Don't you DARE—"

You speak: "ZHYRAXION."

His eyes widen.

"You... you know my name?"

The heart shatters—but DIFFERENTLY.

Golden light, not red.

The curse doesn't just BREAK—it PURIFIES.

The binding dissolves.

Zhyraxion transforms, but the corruption is GONE.

He's whole again.

From the shattered heart, a second form emerges:
Aurelyn's spirit, freed at last.

Zhyraxion: "Aurelyn? Is it... is it really you?"

They circle each other, two dragons reunited.

Zhyraxion looks at you.

"You... you knew what I was. What I'd done.
And you still... spoke my name..."

Your soul contract SHATTERS.

The Guide appears beside you, corporeal again.

Guide: "Huh. You actually did it. Freed us all."

The portal opens—but this time it's GOLDEN.

Zhyraxion and Aurelyn fade into light,
together at last.

Where they go, you don't know.

But it's right.

Guide: "Come on, kid. Let's get out of here."

You step through the portal.

Side by side with the ghost who warned you.

Both of you finally, truly free.
```

**Victory Screen:**
- Title: "REDEMPTION - Sacrifice & Compassion"
- Bright, hopeful theme
- Stats shown
- Achievement: "True Freedom"
- Special text: "Everyone wins."
- Hall of Fame: "✨ TRUE HERO"

---

## 🧪 Testing Plan

### Unit Tests
- [ ] Ruby Heart pickup triggers portal
- [ ] Secret room unlocks after heart pickup
- [ ] Ritual knowledge unlocks menu option
- [ ] True name knowledge unlocks menu option
- [ ] Each choice leads to correct ending

### Integration Tests
- [ ] Full playthrough: Ending 1a
- [ ] Full playthrough: Ending 1b (with secret)
- [ ] Full playthrough: Ending 2
- [ ] Full playthrough: Ending 3 (death)
- [ ] Full playthrough: Ending 4
- [ ] Full playthrough: Ending 5 (with true name)

### Balance Tests
- [ ] Human Zhyraxion beatable with mid-tier gear
- [ ] Full Dragon nearly impossible (99%+ death rate)
- [ ] Grief Dragon difficult but fair
- [ ] Boss HP/damage scaling appropriate

### Edge Cases
- [ ] Try to drop Ruby Heart (should fail)
- [ ] Try to leave chamber without choosing (should fail)
- [ ] Kill Zhyraxion before dialogue (prevent?)
- [ ] What if player dies in boss fight? (respawn? game over?)

---

## 📊 Success Metrics

- [ ] All 6 endings implemented and tested
- [ ] Boss fights balanced correctly
- [ ] Secret room discoverable but not obvious
- [ ] Ending cutscenes emotionally impactful
- [ ] Player choices feel meaningful
- [ ] Hall of Fame tracks which ending achieved

---

## 🚀 Implementation Order

**Sprint 1: Foundation**
1. Ruby Heart entity
2. Portal system
3. Confrontation chamber map
4. Basic choice menu

**Sprint 2: Secret Path**
5. Hidden room
6. Corrupted Ritualists
7. Crimson Ritual Codex
8. Ritual knowledge tracking

**Sprint 3: Boss Fights**
9. Human Zhyraxion (Ending 1a)
10. Full Dragon (Ending 3)
11. Grief Dragon (Ending 4)

**Sprint 4: Endings**
12. Cutscene system
13. All 6 ending screens
14. Victory/defeat handling

**Sprint 5: Polish & Balance**
15. Boss difficulty tuning
16. Cutscene timing
17. Integration testing
18. Bug fixes

---

## 📝 Notes

- Keep boss fights using existing combat system (Option A)
- Boss component already has enrage, dialogue, phases
- Each dragon form should FEEL different (fast/overwhelming/erratic)
- Ending 1b is secret, Ending 5 is best
- Portal appears after heart pickup but player can explore first
- Confrontation chamber is separate map (cinematic)
- Choice menu is key moment—needs good UI/UX

---

**Next Step:** Start with Ruby Heart + Portal (Phase 5.1)

