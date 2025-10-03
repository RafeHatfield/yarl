# Phase 1: Entity Personality Expansion (v3.3.0)

**Status:** Ready to implement
**Estimated Time:** 1 week  
**Voice Inspiration:** Alan Rickman - dry, withering, magnificently condescending

---

## 🎭 **Goals**

Make the Entity's presence felt throughout the entire game experience, not just on death. The Entity should feel like an ever-present observer, commenting on your journey with sardonic wit.

**The player should:**
- Hear the Entity's voice at key moments
- Feel watched and judged constantly
- Want to prove the Entity wrong
- Experience personality that makes Yarl unique

---

## 📋 **Features to Implement**

### 1. Level Transition Dialogue
**When:** Player descends stairs to new level  
**Frequency:** Every level transition  
**Location:** Brief message on descending

**Quote Categories:**

*Early Levels (1-3):*
- "Level 2. Try not to embarrass yourself immediately."
- "Deeper you go. How... ambitious."
- "Level 3 already? Don't let it go to your head."

*Mid Levels (4-7):*
- "Level 5? I'm almost impressed. *Almost*."
- "You're getting deeper. The monsters are getting... less forgiving."
- "Level 6. This is where most of your predecessors failed."

*Deep Levels (8-9):*
- "Level 8. Careful down here."
- "You're... actually making progress. Fascinating."
- "Level 9. I'd say you're close to something, but that would be premature."

*Very Deep (10+):*
- "Level 10. You shouldn't be this deep." *(subtle worry creeping in)*
- "This... this is unexpected." *(losing arrogance)*
- "Perhaps I underestimated you. Slightly." *(defensive)*

**Implementation:**
- Add to level transition in `game_map.py` or stairs logic
- Use dungeon level to select quote pool
- Display as temporary message
- Maybe subtle visual effect (text color, position)

**Estimated Time:** 2-3 hours

---

### 2. Main Menu Presence
**When:** Player sees title screen  
**Frequency:** Every menu visit, rotating quotes  
**Location:** Bottom of menu or subtitle area

**Quote Pool (10-15 rotating):**
- "Back again? How... persistent."
- "Ready to fail once more?"
- "Another attempt. How delightfully futile."
- "Your soul is mine. Let's not forget that."
- "Impatient to die again, are we?"
- "Yes, yes, off you go. Try to last more than five minutes this time."
- "Another body awaits. Try not to waste it."
- "Eager for more punishment? Very well."
- "I do admire your determination. If not your competence."
- "Let's see if you've learned anything. (Unlikely.)"

**Implementation:**
- Add to main menu rendering in `menus.py`
- Random selection on menu load
- Subtle color/positioning (not intrusive)
- Sets tone immediately

**Estimated Time:** 1-2 hours

---

### 3. First Kill Commentary
**When:** Player kills their first monster  
**Frequency:** Once per run  
**Location:** Message log

**Quote Pool:**
- "Your first kill. How... violent. Continue."
- "Well, at least you can swing a sword. Barely."
- "One down. Only several hundred more to go."
- "Congratulations. You've discovered basic combat. Thrilling."
- "A kill. Don't celebrate too early."

**Implementation:**
- Check in `game_actions.py` when recording kills
- If `stats.total_kills == 1`, trigger Entity quote
- Add to message log with special color

**Estimated Time:** 30 minutes

---

### 4. Milestone Kill Commentary
**When:** Player reaches kill milestones (10, 25, 50, 100)  
**Frequency:** Once per milestone per run  
**Location:** Message log or level transition

**10 Kills:**
- "Ten kills. Are you expecting applause?"
- "Double digits. How... pedestrian."
- "Ten corpses. The dungeon barely notices."

**25 Kills:**
- "Twenty-five kills. You're actually keeping count, aren't you?"
- "Quarter century of death. Still not impressive."
- "Your enthusiasm for violence is noted."

**50 Kills:**
- "Fifty kills. I suppose that's... adequate."
- "Half a hundred. If you're looking for praise, you won't find it here."
- "Your body count grows. As does my collection."

**100 Kills:**
- "One hundred. Yes, I'm counting too."
- "A century of kills. Still think you're the hero?"
- "One hundred souls. All mine. Including yours."

**Implementation:**
- Check in `game_actions.py` when recording kills
- Track which milestones already triggered
- Display on kill or next level transition

**Estimated Time:** 1 hour

---

### 5. Rare Item Discovery Commentary
**When:** Player finds legendary/rare items  
**Frequency:** Per item type  
**Location:** Message log when picked up

**Items to Comment On:**
- **Fireball Scroll**: "Ah, fire. Try not to burn yourself."
- **Lightning Scroll**: "Lightning. How... shocking."
- **Raise Dead Scroll**: "Necromancy. How delightfully dark."
- **Dragon Fart Scroll**: "That one's... special. You'll see."
- **Greatsword/Legendary Weapon**: "A fine blade. Try not to drop it."
- **Heavy Armor**: "Oh good, protection. You'll need it."
- **Enhancement Scrolls**: "Making improvements? How optimistic."

**Implementation:**
- Add to item pickup in `game_actions.py`
- Check item type and trigger quote
- Only first time per item type per run
- Special color in message log

**Estimated Time:** 2 hours

---

### 6. Close Call Commentary
**When:** Player survives with very low HP (< 10% max HP)  
**Frequency:** Once or twice per run (not spammy)  
**Location:** Message log

**Quote Pool:**
- "That was close. Too close, even for you."
- "Your heart's still beating. Barely."
- "Lucky. Very, very lucky."
- "I was preparing the next vessel. You've bought yourself a moment."
- "Survival instinct kicking in? About time."

**Implementation:**
- Check after taking damage if HP < 10% of max
- Cooldown to prevent spam
- Maybe only trigger once per level

**Estimated Time:** 1 hour

---

### 7. Long Survival Commentary
**When:** Player survives many turns (100, 250, 500)  
**Frequency:** Once per milestone  
**Location:** Level transition or message log

**100 Turns:**
- "Still alive at 100 turns. Marginally impressive."
- "You're lasting longer than usual. Don't get cocky."

**250 Turns:**
- "250 turns. Perhaps this body is more resilient."
- "You're... persistent. I'll give you that."

**500 Turns:**
- "500 turns. I'm starting to think you might actually be competent."
- "Half a thousand turns. Are you trying to prove something?"

**Implementation:**
- Check `stats.turns_taken` on level transition
- Track which milestones already triggered

**Estimated Time:** 30 minutes

---

## 🎨 **Visual/Audio Polish**

### Text Styling
- **Entity quotes** should be visually distinct:
  - Different color (dark gold? purple?)
  - Maybe italics or special formatting
  - Prefix with "⟨Entity⟩" or similar
  - Slightly longer display time

### Tone Consistency
- **Early game**: Maximum condescension, superiority
- **Mid game**: Grudging acknowledgment, less dismissive
- **Late game**: Subtle worry, defensiveness creeping in
- **Boss level**: Full personality shift (future)

---

## 🧪 **Testing Requirements**

### Unit Tests
- Test quote selection based on context
- Test trigger conditions (first kill, milestones)
- Test cooldowns and spam prevention
- Test quote pool accessibility

### Manual Testing
- Play through and verify quotes appear
- Check timing feels right (not intrusive)
- Verify tone progression (condescending → worried)
- Test with Alan Rickman voice in head!

### Integration Tests
- Quotes don't break game flow
- Message log handles Entity messages
- Save/load preserves milestone tracking

---

## 📊 **Success Metrics**

**This feature succeeds if:**
- ✅ Players comment on the Entity's personality
- ✅ Deaths feel less frustrating due to humor
- ✅ Players quote the Entity to friends
- ✅ Yarl feels unique compared to other roguelikes
- ✅ Entity voice is consistent (Alan Rickman!)

---

## 🚀 **Implementation Order**

**Day 1-2: Core Systems**
1. Main menu presence (easiest, sets tone)
2. Level transition dialogue
3. First kill commentary

**Day 3-4: Milestones**
4. Kill milestone commentary
5. Survival milestone commentary
6. Close call commentary

**Day 5: Polish**
7. Rare item commentary
8. Visual styling and formatting
9. Cooldown/spam prevention
10. Testing and refinement

**Day 6-7: Testing & Iteration**
11. Comprehensive testing
12. Adjust quote selection weights
13. Fine-tune timing and display
14. Polish message formatting

---

## 💡 **Future Expansion Ideas**

*Save these for later phases:*

- **Entity reacts to player choices** (using potions, fleeing)
- **Entity comments on death causes** (specific to monster type)
- **Entity mood system** (gets more worried as you progress)
- **Hidden dialogue** for rare achievements
- **Entity lore revelations** (hints at backstory)
- **Fourth-wall breaks** (very subtle)

---

## 🎭 **The Alan Rickman Test**

When writing any Entity dialogue, read it in Alan Rickman's voice:
- Would he deliver this with dry wit? ✅
- Does it sound bored yet menacing? ✅
- Is there a subtle put-down? ✅
- Could this be from Die Hard, Dogma, or Galaxy Quest? ✅

If yes to all four, it's perfect Entity dialogue.

---

**"One week to make the Entity unforgettable. Let's begin."** 

— *(Rickman voice)* ✨

