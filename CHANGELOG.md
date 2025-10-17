# Changelog

All notable changes to Catacombs of Yarl are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [v3.12.0] - 2025-10-18

### Added
- **Clickable Main Menu** - Mouse support for menu options
- **Wider Sidebar** - Increased from 20 to 24 tiles (20% wider)
- **Documentation Organization** - 50+ docs organized into structured folders

### Fixed
- **Ring of Regeneration** - Now properly heals +1 HP every 5 turns
- **Auto-Identification Crash** - Fixed MessageBuilder method error
- **Ring Unequipping** - Correctly targets the actual equipped slot
- **Sidebar Coordinate Bug** - Fixed off-by-one error in click detection

### Documentation
- Organized 50+ markdown files into `docs/` structure
- Created `docs/README.md` as documentation index
- Archived completed features, bug fixes, and session summaries
- Kept 7 active docs in root directory

---

## [v3.11.1] - 2025-10-16

### Added
- **Ring System** - 15 unique ring types across 2 equipment slots
  - Defensive rings (Protection, Regeneration, Resistance)
  - Offensive rings (Strength, Dexterity, Might)
  - Utility rings (Teleportation, Invisibility, Searching, Free Action)
  - Magic rings (Wizardry, Clarity, Speed)
  - Special rings (Constitution, Luck)
- **Auto-Identify on Equip** - Items automatically identify when equipped
- **Ring Passive Effects** - Always active while worn
- **Ring Combat Triggers** - Effects that activate on damage/new level

### Technical
- New `Ring` component with 15 effect types
- Ring slots in equipment system (left and right hand)
- Integration with Fighter, AI, and combat systems
- Comprehensive ring test coverage

---

## [v3.11.0] - 2025-10-16

### Added
- **Resistance System** - Elemental damage types and resistances
  - 6 damage types: Fire, Cold, Poison, Lightning, Acid, Physical
  - Equipment can provide resistances (0-100%)
  - Boss monsters have thematic immunities
  - Damage reduction calculations

### Technical
- Fighter component now handles resistances
- Spell system integrated with damage types
- Comprehensive resistance logging
- Resistance configuration in YAML

---

## [v3.11.0] - 2025-10-15

### Added
- **Turn Economy System** - All actions now cost turns
  - Picking up items costs 1 turn
  - Using items costs 1 turn
  - Equipping/unequipping costs 1 turn
  - Dropping items costs 1 turn
  - Completing targeting costs 1 turn
- **Identify Scroll** - Temporary identification powers
  - 10-turn identification buff
  - Can identify 1 item per turn
  - Status effect with visual feedback

### Changed
- Menu navigation remains free (no turn cost)
- Failed actions don't consume turns

### Technical
- Integrated turn consumption throughout action system
- New `IdentifyModeEffect` status effect
- Turn-based processing for identification

---

## [v3.10.0] - 2025-10-14

### Added
- **Fear Scroll** - AoE fear effect causing enemies to flee
- **Detect Monster Scroll** - Reveals all monsters for 20 turns
- Completed scroll expansion (8 → 22 scroll types)

### Technical
- New `FearEffect` status effect
- New `DetectMonsterEffect` status effect
- AI modification for fleeing behavior

---

## [v3.9.0] - 2025-10-10

### Added
- **Boss Fight System** - Two unique boss encounters
  - Dragon Lord (100 HP, fire immune, enrage mechanic)
  - Demon King (80 HP, poison immune, high enrage)
- **Guaranteed Legendary Loot** - Bosses drop 1-2 legendary items
- **Boss AI** - Enrage mechanics and combat behaviors

---

## [Earlier Versions]

See individual release notes in `docs/archive/releases/` for:
- v3.8.0 and earlier releases

---

## Version Numbering

- **Major** (x.0.0): Major gameplay overhauls
- **Minor** (0.x.0): New systems and features
- **Patch** (0.0.x): Bug fixes and tweaks

---

*For detailed release notes, see `RELEASE_NOTES_v*.md` files*

