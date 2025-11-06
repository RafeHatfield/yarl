# Phase 5: The Six Endings - Comprehensive Testing Plan

This document provides a systematic approach to testing all 6 endings in Phase 5.

## Quick Start Commands

```bash
# Start at level 25 with god mode and revealed map for fast testing
python engine.py --testing --start-level 25 --god-mode --reveal-map
```

## Pre-Test Setup

### Required Knowledge Flags
- **Ending 1a**: Requires knowing Entity's true name (Zhyraxion)
- **Ending 1b**: Requires Crimson Ritual knowledge (from Codex)
- **Ending 2**: No knowledge required
- **Ending 3**: No knowledge required
- **Ending 4**: No knowledge required
- **Ending 5**: Requires knowing Entity's true name

### How to Unlock Knowledge
1. **True Name (Zhyraxion)**: Talk to Ghost Guide on Level 20
2. **Crimson Ritual**: Find and read the Crimson Ritual Codex in the secret room on Level 25

## Test Matrix

| Ending | Choice Path | Boss Fight? | Knowledge Needed | Expected Outcome |
|--------|-------------|-------------|------------------|------------------|
| 1a | Keep → Fight him | YES (human form) | True Name | Become new deity |
| 1b | Keep → Ritual | NO | Ritual | Restore both dragons |
| 2 | Give | NO | None | Zhyraxion restored |
| 3 | Destroy | YES (full dragon) | None | Nearly impossible fight |
| 4 | Keep → Destroy it | YES (grief dragon) | None | Corrupted Zhyraxion |
| 5 | Keep → Speak true name | NO | True Name | Break the curse |

---

## Detailed Testing Procedures

### Test 1: Ending 1a - "The Ascension"
**Setup:**
1. Start game with `--testing --start-level 20`
2. Find Ghost Guide and learn Zhyraxion's true name
3. Descend to Level 25
4. Pick up Ruby Heart (triggers portal)

**Test Steps:**
1. Enter the portal (step on it)
2. Verify confrontation menu appears
3. Select "Keep the heart"
4. Verify submenu shows "Fight him" option (because you know true name)
5. Select "Fight him"
6. Verify Zhyraxion (human form) boss spawns: 70 HP, ~50% enrage
7. Defeat the boss
8. Verify Ending 1a screen appears with amber theme
9. Check story: "You defeat Zhyraxion and absorb his power. You become the new Entity."

**Expected Boss Stats:**
- Name: Zhyraxion the Betrayed (Human Form)
- HP: 70
- Damage: 15-22
- Enrage at 50% HP

---

### Test 2: Ending 1b - "The Crimson Ritual"
**Setup:**
1. Start game with `--testing --start-level 25`
4. **Find secret room** (look for hidden passage near one of the rooms)
5. **Defeat 2-3 Corrupted Ritualists** in secret room
6. **Pick up Crimson Ritual Codex** and use it (read it)
7. Verify message: "New knowledge unlocked: The Crimson Ritual!"
8. Pick up Ruby Heart (triggers portal)

**Test Steps:**
1. Enter the portal
2. Verify confrontation menu appears
3. Select "Keep the heart"
4. Verify submenu NOW shows "Use the ritual" option (new!)
5. Select "Use the ritual"
6. Verify **NO boss fight** occurs
7. Verify Ending 1b screen appears with gold theme
8. Check story: "You perform the Crimson Ritual. Both dragons are restored."

**Secret Room Notes:**
- 7x7 room attached to a random room on Level 25
- Connected by a tunnel (visible after Ruby Heart pickup)
- Contains 2-3 Corrupted Ritualists (60 HP each)
- Crimson Ritual Codex in center

---

### Test 3: Ending 2 - "The Dragon's Freedom"
**Setup:**
1. Start game with `--testing --start-level 25`
2. Pick up Ruby Heart (triggers portal)
3. **DO NOT** get true name from Ghost Guide

**Test Steps:**
1. Enter the portal
2. Verify confrontation menu appears
3. Select "Give the heart to the Entity"
4. Verify **NO boss fight** occurs
5. Verify Ending 2 screen appears with cyan theme
6. Check story: "You give the heart to Zhyraxion. He is restored but Aurelyn is gone."

**Expected:**
- Simple, direct ending
- No combat required
- Bittersweet tone

---

### Test 4: Ending 3 - "The Dragon's Wrath"
**Setup:**
1. Start game with `--testing --start-level 25 --god-mode`
2. Pick up Ruby Heart (triggers portal)
3. **USE GOD MODE** - this fight is designed to be nearly impossible

**Test Steps:**
1. Enter the portal
2. Verify confrontation menu appears
3. Select "Destroy the heart"
4. Verify Zhyraxion (Full Dragon) boss spawns: 200 HP, EXTREME difficulty
5. Attempt to fight (or just verify boss appears)
6. Defeat with god mode
7. Verify Ending 3 screen appears with dark red theme
8. Check story: "You destroyed the heart. Zhyraxion goes fully mad."

**Expected Boss Stats:**
- Name: Zhyraxion the Betrayed (Full Dragon Form)
- HP: 200 (!!!)
- Damage: 25-40
- Defense: 15
- Designed to be 0.1% win rate

---

### Test 5: Ending 4 - "The Shattered Heart"
**Setup:**
1. Start game with `--testing --start-level 25`
2. Pick up Ruby Heart (triggers portal)

**Test Steps:**
1. Enter the portal
2. Verify confrontation menu appears
3. Select "Keep the heart"
4. Verify submenu appears
5. Select "Destroy it" (at the bottom)
6. Verify Zhyraxion (Grief Dragon) boss spawns: 100 HP, erratic
7. Defeat the boss
8. Verify Ending 4 screen appears with crimson theme
9. Check story: "You destroyed the heart. Zhyraxion becomes corrupted by grief."

**Expected Boss Stats:**
- Name: Zhyraxion the Betrayed (Grief-Mad Dragon)
- HP: 100
- Damage: 20-30
- Erratic, grief-driven attacks

---

### Test 6: Ending 5 - "The Curse Broken"
**Setup:**
1. Start game with `--testing --start-level 20`
2. Find Ghost Guide and learn Zhyraxion's true name
3. Descend to Level 25
4. Pick up Ruby Heart (triggers portal)

**Test Steps:**
1. Enter the portal
2. Verify confrontation menu appears
3. Select "Keep the heart"
4. Verify submenu shows "Speak his true name" option (because you know it)
5. Select "Speak his true name"
6. Verify **NO boss fight** occurs
7. Verify Ending 5 screen appears with gold theme
8. Check story: "You speak Zhyraxion's true name. The curse is broken."

**Expected:**
- Peaceful resolution
- True name power theme
- Hope for the future

---

## Testing Checklist

### Phase 1: Basic Functionality
- [ ] Ruby Heart spawns on Level 25
- [ ] Portal spawns after Ruby Heart pickup
- [ ] Portal transports to Confrontation Chamber
- [ ] Confrontation menu appears correctly
- [ ] Menu options change based on knowledge flags

### Phase 2: Knowledge System
- [ ] Ghost Guide spawns on Level 20
- [ ] Ghost Guide dialogue reveals true name
- [ ] True name unlocks "Fight him" and "Speak name" options
- [ ] Secret room spawns on Level 25
- [ ] Corrupted Ritualists spawn in secret room
- [ ] Crimson Ritual Codex spawns in secret room
- [ ] Reading Codex unlocks "Use the ritual" option

### Phase 3: Boss Fights
- [ ] Zhyraxion (Human) spawns for Ending 1a
- [ ] Zhyraxion (Full Dragon) spawns for Ending 3
- [ ] Zhyraxion (Grief Dragon) spawns for Ending 4
- [ ] Boss death triggers correct ending screen
- [ ] Boss stats are correct (HP, damage, enrage)

### Phase 4: Ending Screens
- [ ] Ending 1a displays correctly (amber theme)
- [ ] Ending 1b displays correctly (gold theme)
- [ ] Ending 2 displays correctly (cyan theme)
- [ ] Ending 3 displays correctly (dark red theme)
- [ ] Ending 4 displays correctly (crimson theme)
- [ ] Ending 5 displays correctly (gold theme)
- [ ] Each ending shows correct story text
- [ ] Player stats display on ending screen

### Phase 5: Integration
- [ ] Hall of Fame records correct ending code
- [ ] Victory screen shows after boss defeat
- [ ] No crashes or errors during transitions
- [ ] All dialogue text displays correctly
- [ ] Choice logic works as expected

---

## Quick Test Scenarios

### Fastest Tests (No Combat)
- **Ending 2**: No knowledge needed, no boss fight (~2 minutes)
- **Ending 5**: Only need true name, no boss fight (~3 minutes)
- **Ending 1b**: Need both knowledge flags, no boss fight (~5 minutes)

### Combat Tests
- **Ending 1a**: Medium-Hard boss (~5-10 minutes)
- **Ending 4**: Hard boss (~5-10 minutes)
- **Ending 3**: Extreme boss (use god mode) (~2 minutes with god mode)

---

## Known Issues to Watch For

1. **Right-click pickup**: Ensure Ruby Heart pickup works with both 'g' key and right-click
2. **Portal detection**: Verify portal entry works reliably
3. **Boss spawning**: Check that correct boss variant spawns
4. **Menu options**: Confirm conditional options appear/hide correctly
5. **State transitions**: Watch for any state transition bugs (CONFRONTATION → PLAYERS_TURN → VICTORY)

---

## Reporting Test Results

When testing, note:
1. Which ending you tested
2. Knowledge flags you had
3. Expected vs actual behavior
4. Any errors or crashes
5. Any dialogue/text issues
6. Boss fight difficulty (if applicable)

---

## Developer Notes

### Easy Testing Commands
```bash
# Full game playthrough
python engine.py

# Start at Level 20 (get true name from Guide)
python engine.py --testing --start-level 20 --god-mode

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
- Boss creation
- Ending triggers

---

## Success Criteria

All 6 endings should:
1. ✅ Be accessible through clear choice paths
2. ✅ Display unique story text and themes
3. ✅ Work with appropriate knowledge flags
4. ✅ Spawn correct boss (if applicable)
5. ✅ Trigger correct ending screen
6. ✅ Record in Hall of Fame
7. ✅ Be bug-free and stable

---

**Happy Testing! The fate of Aurelyn and Zhyraxion is in your hands!**

