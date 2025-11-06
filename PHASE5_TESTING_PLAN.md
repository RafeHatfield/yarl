# Phase 5: The Six Endings - Comprehensive Testing Plan

This document provides a systematic approach to testing all 6 endings in Phase 5.

## Quick Start Commands

```bash
# Start at level 25 with god mode and revealed map for fast testing
python engine.py --testing --start-level 25 --god-mode --reveal-map

# Start at level 20 to unlock true name knowledge from Guide first
python engine.py --testing --start-level 20 --god-mode --reveal-map
```

## Pre-Test Setup

### Required Knowledge Flags

| Ending | True Name | Ritual | Needed For |
|--------|-----------|--------|-----------|
| 1 | ❌ | ❌ | Fight Zhyraxion, escape with heart |
| 2 | ✅ | ✅ | Unlock ritual sequence (BOTH required!) |
| 3 | ❌ | ❌ | Accept transformation cutscene |
| 4 | ❌ | ❌ | Give heart to Zhyraxion |
| 5 | ❌ | ❌ | Destroy heart, grief dragon fight |
| 6 | ✅ | ❌ | Destroy heart + speak name for redemption |

### How to Unlock Knowledge
1. **True Name (Zhyraxion)**: Talk to Ghost Guide on Level 20 → `entity_true_name_zhyraxion`
2. **Crimson Ritual**: Find secret room on Level 25 → Defeat Corrupted Ritualists → Read Crimson Ritual Codex → `crimson_ritual_knowledge`

⚠️ **IMPORTANT FOR ENDING 2:** Both flags are required! If only ritual knowledge or only true name, the option won't appear.

## Test Matrix

| # | Name | Choice Path | Boss Fight? | Knowledge Needed | Expected Theme | Status |
|---|------|-------------|-------------|------------------|-----------------|--------|
| 1 | Escape Through Battle | Keep → Refuse → Fight | YES (Human, 70 HP) | None | Amber | 🔲 TODO |
| 2 | Crimson Collector | Keep → Use Ritual | NO (Ritual cutscene) | Name + Ritual | Gold | 🔲 TODO |
| 3 | Dragon's Bargain | Keep → Accept Transform | NO (Transform cutscene) | None | Purple | 🔲 TODO |
| 4 | Fool's Freedom | Give Heart | YES (Dragon, 200 HP) ⚠️ EXTREME | None | Dark Red | 🔲 TODO |
| 5 | Mercy & Corruption | Destroy (no name) | YES (Grief, 100 HP) | None | Crimson | 🔲 TODO |
| 6 | Sacrifice & Redemption | Destroy (WITH name) | NO (Redemption cutscene) | True Name | Gold | 🔲 TODO |

---

## Detailed Testing Procedures

### Test 1: Ending 1 - "Escape Through Battle" (Neutral-Good)

**Setup:**
1. Start game with `--testing --start-level 25 --god-mode --reveal-map`
2. Pick up Ruby Heart (triggers portal)

**Test Steps:**
1. Enter the portal (step on it)
2. Verify confrontation menu appears with choices
3. Select "Keep the heart"
4. Verify submenu shows "Refuse Transform" option
5. Select "Refuse Transform" or "Fight him"
6. Verify Zhyraxion (Human Form) boss spawns: 70 HP, ~50% enrage
7. Defeat the boss
8. Verify Ending 1 screen appears with amber theme
9. Check story: "You defeat Zhyraxion and absorb his power. You become the new Entity."

**Expected Boss Stats:**
- Name: Zhyraxion the Betrayed (Human Form)
- HP: 70
- Damage: 15-22
- Enrage at 50% HP

**Knowledge Required:** None
**Pass Criteria:** Boss spawns and fight concludes properly

---

### Test 2: Ending 2 - "Crimson Collector" (Secret Dark)

**Setup:**
1. Start game with `--testing --start-level 20 --god-mode --reveal-map`
2. Find Ghost Guide and learn Zhyraxion's true name (`entity_true_name_zhyraxion`)
3. Descend to Level 25
4. Find secret room (look for hidden passage)
5. Defeat 2-3 Corrupted Ritualists in secret room
6. Pick up Crimson Ritual Codex and use it (read it) → `crimson_ritual_knowledge`
7. Verify message: "New knowledge unlocked: The Crimson Ritual!"
8. Pick up Ruby Heart (triggers portal)

**Test Steps:**
1. Enter the portal
2. Verify confrontation menu appears
3. Select "Keep the heart"
4. Verify submenu shows "Use the Crimson Ritual" option (new!)
5. Select "Use the Crimson Ritual"
6. Verify **NO boss fight** occurs
7. Verify ritual sequence plays
8. Verify Ending 2 screen appears with gold theme
9. Check story: "You perform the Crimson Ritual. Both dragons are destroyed, and their power flows through you."

**Secret Room Notes:**
- 7x7 room attached to a random room on Level 25
- Connected by a tunnel (visible after Ruby Heart pickup)
- Contains 2-3 Corrupted Ritualists (60 HP each)
- Crimson Ritual Codex in center

**Knowledge Required:** 
- ✅ `entity_true_name_zhyraxion` 
- ✅ `crimson_ritual_knowledge`
- **BOTH are required!** If only one is present, the menu option will NOT appear

**Pass Criteria:** Both knowledge flags present → ritual option appears and triggers cutscene

---

### Test 3: Ending 3 - "Dragon's Bargain" (Bad - Trapped)

**Setup:**
1. Start game with `--testing --start-level 25 --god-mode --reveal-map`
2. Pick up Ruby Heart (triggers portal)
3. **Do NOT** gather any knowledge flags

**Test Steps:**
1. Enter the portal
2. Verify confrontation menu appears
3. Select "Keep the heart"
4. Verify submenu shows "Accept Transformation" option (or similar)
5. Select "Accept Transformation"
6. Verify **NO boss fight** occurs
7. Verify cutscene plays showing curse transfer
8. Verify Ending 3 screen appears with purple/corruption theme
9. Check story: "You accept Zhyraxion's offer. The curse transfers to you, and Zhyraxion escapes free, amused."

**Expected:**
- Cutscene, no combat
- Tragic bad ending
- Setup for potential future encounters with free Zhyraxion

**Knowledge Required:** None
**Pass Criteria:** Cutscene plays and transitions to bad ending screen

---

### Test 4: Ending 4 - "Fool's Freedom" (Bad - Unwinnable)

**Setup:**
1. Start game with `--testing --start-level 25 --god-mode --reveal-map`
2. Pick up Ruby Heart (triggers portal)
3. **IMPORTANT:** Use god mode or prepare to die - this fight is EXTREME difficulty

**Test Steps:**
1. Enter the portal
2. Verify confrontation menu appears
3. Select "Give the heart to Zhyraxion"
4. Verify Zhyraxion (Full Dragon) boss spawns: 200 HP, EXTREME difficulty
5. Attempt to fight (or use god mode to verify fight mechanics)
6. Defeat the boss (with god mode)
7. Verify Ending 4 screen appears with dark red theme
8. Check story: "You gave the heart to Zhyraxion. He is fully restored and shows no mercy."

**Expected Boss Stats:**
- Name: Zhyraxion the Betrayed (Full Dragon Form)
- HP: 200
- Damage: 25-40
- Defense: 15
- Area attacks (AOE)
- Designed to be nearly impossible (0.1% win rate)

**Knowledge Required:** None
**Pass Criteria:** Full Dragon boss spawns, has expected stats, fight is brutally difficult

---

### Test 5: Ending 5 - "Mercy & Corruption" (Tragic)

**Setup:**
1. Start game with `--testing --start-level 25 --god-mode --reveal-map`
2. Pick up Ruby Heart (triggers portal)
3. **DO NOT** gather true name knowledge

**Test Steps:**
1. Enter the portal
2. Verify confrontation menu appears
3. Select "Keep the heart"
4. Verify submenu appears
5. Select "Destroy the heart" (at the bottom)
6. Verify Zhyraxion (Grief-Corrupted Dragon) boss spawns: 100 HP, erratic behavior
7. Defeat the boss (or allow grief-driven attacks)
8. Verify Ending 5 screen appears with crimson theme
9. Check story: "You destroy the heart out of mercy, but it destroys him. Aurelyn is gone forever."

**Expected Boss Stats:**
- Name: Zhyraxion the Betrayed (Grief-Mad Dragon)
- HP: 100
- Damage: 20-30
- Erratic, grief-driven attacks (unpredictable pattern)

**Knowledge Required:** None (but must NOT have true name)
**Pass Criteria:** Boss spawns with grief mechanics and fight concludes

---

### Test 6: Ending 6 - "Sacrifice & Redemption" (Best - Secret)

**Setup:**
1. Start game with `--testing --start-level 20 --god-mode --reveal-map`
2. Find Ghost Guide and learn Zhyraxion's true name (`entity_true_name_zhyraxion`)
3. Descend to Level 25
4. Pick up Ruby Heart (triggers portal)
5. **Do NOT** find secret room or read Crimson Ritual Codex

**Test Steps:**
1. Enter the portal
2. Verify confrontation menu appears
3. Select "Keep the heart"
4. Verify submenu appears
5. Select "Destroy the heart"
6. Verify menu shows "Speak his true name: ZHYRAXION" option (because you know the name)
7. Select "Speak his true name"
8. Verify **NO boss fight** occurs
9. Verify golden light cutscene plays
10. Verify Ending 6 screen appears with gold theme
11. Check story: "You speak Zhyraxion's true name as the heart breaks. The curse shatters. Zhyraxion is freed and Aurelyn returns. All is made whole."

**Expected:**
- Peaceful resolution (best ending)
- True name power theme
- Hope and redemption
- Most satisfying for thorough players

**Knowledge Required:** 
- ✅ `entity_true_name_zhyraxion`
- ❌ `crimson_ritual_knowledge` (should NOT be present)

**Pass Criteria:** True name triggers redemption ending, no ritual option available

---

## Testing Checklist

### Phase 1: Basic Functionality
- [ ] Ruby Heart spawns on Level 25
- [ ] Portal spawns after Ruby Heart pickup
- [ ] Portal transports to Confrontation Chamber
- [ ] Confrontation menu appears correctly
- [ ] All 6 ending paths are accessible

### Phase 2: Knowledge System
- [ ] Ghost Guide spawns on Level 20
- [ ] Ghost Guide dialogue reveals true name (`entity_true_name_zhyraxion`)
- [ ] True name unlocks appropriate menu options (Endings 1, 6)
- [ ] Secret room spawns on Level 25
- [ ] Corrupted Ritualists spawn in secret room
- [ ] Crimson Ritual Codex spawns in secret room
- [ ] Reading Codex unlocks `crimson_ritual_knowledge`
- [ ] Ending 2 REQUIRES both name AND ritual (verify it doesn't appear with just one)

### Phase 3: Boss Fights
- [ ] Zhyraxion (Human) spawns for Ending 1
- [ ] Zhyraxion (Full Dragon) spawns if Ending 4 triggers boss fight (if implemented)
- [ ] Zhyraxion (Grief Dragon) spawns for Ending 5
- [ ] Boss death triggers correct ending screen
- [ ] Boss stats are correct (HP, damage, mechanics)

### Phase 4: Cutscenes (Non-Combat Endings)
- [ ] Ending 2 ritual sequence plays correctly
- [ ] Ending 3 transformation cutscene plays correctly
- [ ] Ending 6 golden light cutscene plays correctly

### Phase 5: Ending Screens
- [ ] Ending 1 displays correctly (amber theme)
- [ ] Ending 2 displays correctly (gold theme, ritual variant)
- [ ] Ending 3 displays correctly (purple theme)
- [ ] Ending 4 displays correctly (dark red theme)
- [ ] Ending 5 displays correctly (crimson theme)
- [ ] Ending 6 displays correctly (gold theme, redemption variant)
- [ ] Each ending shows correct story text
- [ ] Player stats display on ending screen

### Phase 6: Integration
- [ ] Hall of Fame records correct ending code
- [ ] Victory screen shows after boss defeat or cutscene
- [ ] No crashes or errors during transitions
- [ ] All dialogue text displays correctly
- [ ] Choice logic works as expected
- [ ] Menu options appear/disappear based on knowledge flags

### Phase 7: Edge Cases
- [ ] Ending 2: Test with only true name (should NOT show ritual option)
- [ ] Ending 2: Test with only ritual knowledge (should NOT show ritual option)
- [ ] Ending 2: Test with BOTH (should show ritual option)
- [ ] Ending 6: Test without true name (should NOT show name option)
- [ ] All endings accessible without prior knowledge (except those requiring it)

---

## Quick Test Scenarios

### Fastest Tests (No Combat)
- **Ending 4**: Simple choice (~1 minute)
- **Ending 3**: One choice + cutscene (~2 minutes)
- **Ending 6**: True name only, no ritual (~3 minutes)
- **Ending 2**: Both knowledge flags + no combat (~5 minutes)

### Combat Tests
- **Ending 1**: Medium-Hard boss (~5-10 minutes)
- **Ending 5**: Hard boss with grief mechanics (~5-10 minutes)

---

## Known Issues to Watch For

1. **Menu Conditional Logic**: Verify Ending 2 requires BOTH knowledge flags, not just one
2. **Right-click pickup**: Ensure Ruby Heart pickup works with both 'g' key and right-click
3. **Portal detection**: Verify portal entry works reliably
4. **Boss spawning**: Check that correct boss variant spawns
5. **Menu options**: Confirm conditional options appear/hide correctly based on knowledge
6. **State transitions**: Watch for any state transition bugs (CONFRONTATION → PLAYERS_TURN → VICTORY)

---

## Reporting Test Results

When testing, note:
1. Which ending you tested
2. Knowledge flags you had (name, ritual, or both)
3. Expected vs actual behavior
4. Any errors or crashes
5. Any dialogue/text issues
6. Boss fight difficulty (if applicable)
7. Timing of transitions and cutscenes

---

## Developer Notes

### Easy Testing Commands
```bash
# Full game playthrough
python engine.py

# Start at Level 20 (get true name from Guide)
python engine.py --testing --start-level 20 --god-mode --reveal-map

# Start at Level 25 (quick ending tests)
python engine.py --testing --start-level 25 --god-mode --reveal-map

# God mode for impossible fights
python engine.py --god-mode
```

### Debug Logging
Check `debug.log` for:
- Ruby Heart spawn confirmation
- Secret room creation
- Portal spawn
- Knowledge flag unlocking (`entity_true_name_zhyraxion`, `crimson_ritual_knowledge`)
- Boss creation
- Ending triggers
- Menu option availability based on flags

---

## Success Criteria

All 6 endings should:
1. ✅ Be accessible through clear choice paths
2. ✅ Display unique story text and themes
3. ✅ Work with appropriate knowledge flags (especially Ending 2's dual requirement)
4. ✅ Spawn correct boss (if applicable)
5. ✅ Play correct cutscene (if applicable)
6. ✅ Trigger correct ending screen
7. ✅ Record in Hall of Fame
8. ✅ Be bug-free and stable
9. ✅ Menu options correctly show/hide based on knowledge state

---

**Happy Testing! The fate of Aurelyn and Zhyraxion is in your hands!**
