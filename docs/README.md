# Yarl Documentation Hub

Welcome to the Yarl documentation system. This folder contains detailed technical and development documentation.

## 📚 Quick Navigation

### For Game Designers & Reviewers

Start with these files in the root directory:
- **[README.md](../README.md)** ← Main overview (START HERE)
- **[STORY_LORE_CANONICAL.md](../STORY_LORE_CANONICAL.md)** - Complete narrative and themes
- **[VICTORY_CONDITION_PHASES.md](../VICTORY_CONDITION_PHASES.md)** - How victory works
- **[DESIGN_PRINCIPLES.md](../DESIGN_PRINCIPLES.md)** - Architectural philosophy
- **[PLAYER_PAIN_POINTS.md](../PLAYER_PAIN_POINTS.md)** - Design challenges & solutions
- **[TRADITIONAL_ROGUELIKE_FEATURES.md](../TRADITIONAL_ROGUELIKE_FEATURES.md)** - Feature roadmap

### For Developers

- **[architecture/](architecture/)** - System design and specifications
  - Portal System specification
  - Session handoff template
  
- **[development/](development/)** - Feature development history
  - Phase 4: Environmental Lore (complete)
  - Phase 5: Victory Condition (complete)
  - Portal System: Phase A & B (complete)
  - Session handoff notes

## 📁 Folder Structure

```
docs/
├── README.md (this file)
├── architecture/
│   ├── README.md
│   ├── portal_system.md
│   └── session_handoff_template.md
└── development/
    ├── README.md
    ├── phase4/
    │   ├── README.md
    │   ├── agent_answers.md
    │   ├── completion_summary.md
    │   ├── polish_roadmap.md
    │   └── signpost_draft_revised.md
    ├── phase5/
    │   ├── README.md
    │   ├── current_session.md
    │   ├── implementation_plan.md
    │   ├── session_complete.md
    │   └── testing_plan.md
    ├── portal/
    │   ├── README.md
    │   ├── phase_a_session_summary.md
    │   ├── phase_b_complete.md
    │   ├── phase_b_plan.md
    │   ├── phase_b_session_summary.md
    │   ├── playtest_checklist.md
    │   ├── playtest_ready_summary.md
    │   ├── playtest_setup_summary.md
    │   └── refactoring_plan.md
    ├── current_session_handoff.md
    ├── next_session_request.md
    ├── session_copy_paste.md
    └── session_handoff_next.md
```

## 🎯 Documentation by Purpose

### Architecture & Design
- [DESIGN_PRINCIPLES.md](../DESIGN_PRINCIPLES.md) - Why we design this way
- [architecture/portal_system.md](architecture/portal_system.md) - Portal system specification
- [architecture/session_handoff_template.md](architecture/session_handoff_template.md) - Development template

### Game Design & Story
- [STORY_LORE_CANONICAL.md](../STORY_LORE_CANONICAL.md) - Complete narrative
- [VICTORY_CONDITION_PHASES.md](../VICTORY_CONDITION_PHASES.md) - Victory condition design
- [PLAYER_PAIN_POINTS.md](../PLAYER_PAIN_POINTS.md) - Design challenges
- [TRADITIONAL_ROGUELIKE_FEATURES.md](../TRADITIONAL_ROGUELIKE_FEATURES.md) - Feature roadmap

### Project Information
- [README.md](../README.md) - Main project overview
- [PROJECT_STATS.md](../PROJECT_STATS.md) - Codebase metrics
- [ROADMAP.md](../ROADMAP.md) - Future development plans
- [CHANGELOG.md](../CHANGELOG.md) - Version history

### Feature Development
- **Phase 4 (Environmental Lore):** [development/phase4/](development/phase4/README.md)
- **Phase 5 (Victory Condition):** [development/phase5/](development/phase5/README.md)
- **Portal System:** [development/portal/](development/portal/README.md)

### Session Management
- [development/next_session_request.md](development/next_session_request.md) - Planned work
- [development/current_session_handoff.md](development/current_session_handoff.md) - Current session
- [development/session_handoff_next.md](development/session_handoff_next.md) - Next session prep

## 🚀 Getting Started

### If you're a...

**Game Designer:**
1. Read [README.md](../README.md) for overview
2. Review [STORY_LORE_CANONICAL.md](../STORY_LORE_CANONICAL.md) for narrative
3. Check [DESIGN_PRINCIPLES.md](../DESIGN_PRINCIPLES.md) for philosophy
4. See [TRADITIONAL_ROGUELIKE_FEATURES.md](../TRADITIONAL_ROGULELIKE_FEATURES.md) for roadmap

**Developer Joining the Project:**
1. Read [README.md](../README.md) for overview
2. Review [DESIGN_PRINCIPLES.md](../DESIGN_PRINCIPLES.md)
3. Check [architecture/](architecture/) for system design
4. Look at relevant phase docs in [development/](development/)

**Code Reviewer:**
1. Start with [README.md](../README.md)
2. Review [PROJECT_STATS.md](../PROJECT_STATS.md)
3. Check [DESIGN_PRINCIPLES.md](../DESIGN_PRINCIPLES.md)
4. Deep-dive specific systems in [architecture/](architecture/)

**Playtester:**
- Read [development/portal/playtest_checklist.md](development/portal/playtest_checklist.md)
- Check [README.md](../README.md#-how-to-play) for gameplay tips

## 📊 Current Status

- ✅ **Portal System** - Phase A & B complete (91/91 tests passing)
- ✅ **Story Arcs** - Phases 1-5 complete with 6 endings
- ✅ **Core Gameplay** - Combat, exploration, items fully implemented
- ✅ **Test Coverage** - 2500+ tests, 100% critical path
- 🔄 **Next** - Gameplay expansion and balance refinement

## 📝 Documentation Guidelines

When adding documentation:

1. **Strategic Docs** (keep in root):
   - Architecture philosophy
   - Game design principles
   - Narrative and lore
   - Feature roadmaps

2. **Development Docs** (put in `development/`):
   - Phase summaries
   - Implementation plans
   - Session notes
   - Playtest results

3. **Architecture Docs** (put in `architecture/`):
   - System specifications
   - Design patterns
   - Integration points
   - Technical decisions

4. **Each Folder Gets a README.md**:
   - Quick navigation
   - Purpose statement
   - Key files listed
   - Links to related docs

## 🔗 External References

- **Game Code:** See `../` for Python source files
- **Tests:** `../tests/` for test suite (2500+ tests)
- **Configuration:** `../config/` for YAML entity definitions
- **Components:** `../components/` for ECS components

## 💡 Tips

- Each section has a `README.md` - start there for navigation
- Strategic docs in root are easiest to find and reference
- Development history is organized by phase/feature
- Architecture docs explain "why," not "how"
- Code examples in main README.md

---

**Last Updated:** November 2025 | Documentation Reorganization Complete

**Questions?** Check the README in the relevant folder or see the main [README.md](../README.md)
