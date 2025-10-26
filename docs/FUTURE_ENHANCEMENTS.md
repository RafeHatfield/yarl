# Future Enhancements

## 🏆 MacGuffin of Power - Replace "Amulet of Yendor"

**Status:** Placeholder  
**Priority:** HIGH - Phase 3+  
**Date Noted:** October 26, 2025

### Current State
The "Amulet of Yendor" is currently used as the MacGuffin that binds the Entity and triggers the victory condition. This is a **placeholder** name borrowed from Nethack tradition.

### The Vision
We want something **far more unique** and thematically appropriate to our story. The artifact should:
- **Feel original** - Not a generic roguelike reference
- **Tie to the Entity's backstory** - Ancient dragon bound in human form
- **Evoke the game's themes** - Cursed artifacts, binding magic, moral choices
- **Sound epic** - This is THE endgame MacGuffin

### Naming Ideas (Brainstorm)
Consider themes like:
- **Binding/Chains**: The Shackle of Eternity, The Binding Sigil
- **Dragon/Ancient**: The Dragonheart Seal, The Wyrm's Prison
- **Curse/Corruption**: The Cursed Crown, The Corruption Stone
- **Time/Forever**: The Eternal Chain, The Timeless Cage
- **Human Form**: The Flesh-Binding Amulet, The Mortality Seal

### Implementation Notes
- Currently referenced as `amulet_of_yendor` in code
- Will require:
  - Rename in `config/entities.yaml`
  - Update all dialogue references
  - Update victory screens
  - Update documentation
  - Consider new visual description (if we add ASCII art)

### Timeline
- **Phase 1-2**: Keep "Amulet of Yendor" placeholder
- **Phase 3**: Brainstorm and decide on final name
- **Phase 4**: Implement rename and update all references
- **Phase 5**: Polish and ensure thematic consistency

### Rationale for Waiting
- Let the story development inform the name
- Guide system (Phase 3) will add more backstory
- Environmental lore (Phase 4) will establish world-building
- Better to name it once with full context than rename multiple times

---

## 🔤 Font Replacement

**Status:** Current font hard to read  
**Priority:** MEDIUM - Quality of Life  
**Date Noted:** October 26, 2025

### Current State
Using `arial10x10.png` font which is somewhat hard to read during extended play sessions.

### Goal
Find a more readable font for better player experience during long roguelike sessions.

### Research Needed
- What fonts does tcod/libtcod support?
- Where are font files located? (`arial10x10.png` reference in code)
- What format do they need to be in?
- Are there pre-made roguelike fonts available?
- Can we test fonts easily without breaking the game?

### Popular Roguelike Fonts to Consider
- **Terminus** - Clean, highly readable
- **Inconsolata** - Programmer favorite
- **Hack** - Modern, clean
- **DejaVu Sans Mono** - Wide compatibility
- **Source Code Pro** - Adobe's readable font
- **Fira Code** - Modern with good readability

### Implementation Notes
- Currently set in `engine.py`: `libtcod.console_set_custom_font("arial10x10.png", ...)`
- May need to:
  - Find or create `.png` font files
  - Test different sizes (10x10, 12x12, etc.)
  - Ensure UI still fits properly
  - Update constants if font size changes

### Testing Plan
1. Research tcod font requirements
2. Find 3-5 candidate fonts
3. Create testing branch
4. Easy font swap mechanism (config file?)
5. Playtest each font for readability
6. Get user feedback
7. Commit the winner

### Timeline
- **Research**: 1-2 hours
- **Implementation**: 2-4 hours  
- **Testing**: 1-2 hours
- **Total**: Half day to full day

**Not blocking current development** - can be done anytime between phases.

---

## Other Future Enhancements
(Add more ideas here as they emerge)
