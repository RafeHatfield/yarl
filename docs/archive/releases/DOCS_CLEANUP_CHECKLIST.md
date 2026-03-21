# Docs Cleanup Checklist

Status owner: branch `docs/deep-doc-cleanup`
Scope: documentation and repo hygiene only (no game logic changes).

## Master Steps
- [x] Create this checklist file
- [x] Inventory all docs (root, docs/, config/, archive/, etc.)
- [x] Classify docs (canonical, historical, scratch)
- [x] Remove obsolete fix/summary/scratch files
- [x] Update phase/roadmap docs (mark done vs todo)
- [x] Consolidate or remove redundant docs
- [x] Update root README
- [x] Sanity-check doc/code consistency for:
  - Turn/phase system
  - Scenario harness + ecosystem_sanity
  - ETP + loot/pity
  - Combat metrics + dueling scenarios
- [x] Final pass for dead/contradictory docs

## Classification Buckets (to be filled during inventory)

### Canonical (keep/maintain)
- README.md (root)
- DOCS_CLEANUP_CHECKLIST.md
- ROADMAP.md
- docs/README.md
- docs/architecture/README.md
- docs/architecture/RENDERER_INPUT_ABSTRACTION.md
- docs/architecture/portal_system.md
- docs/TURN_AND_STATE_ARCHITECTURE.md
- docs/AI_SYSTEM.md
- docs/COMBAT_METRICS_GUIDE.md
- docs/BOT_SOAK_HARNESS.md
- docs/BOT_PERSONAS.md
- docs/LOGGING.md
- docs/MESSAGE_BUILDER_GUIDE.md
- docs/COMPONENT_TYPE_BEST_PRACTICES.md
- docs/balance/balance_system_overview.md
- docs/balance/loot_baseline.md
- docs/balance/tuning_cheat_sheet.md
- docs/testing/GOLDEN_PATH_IMPLEMENTATION.md
- docs/testing/GOLDEN_PATH_QUICKSTART.md
- HEADLESS_MODE.md
- STORY_LORE_CANONICAL.md
- TRADITIONAL_ROGUELIKE_FEATURES.md

### Historical but useful (archive or clearly label)
- ARCHITECTURE_OVERVIEW.md (locked; reference only)
- docs/ARCHIVE_COMPONENT_ACCESS_REFACTORING_GUIDE.md
- docs/ARCHIVE_LOGGING_CONSOLIDATION_PLAN.md
- docs/ARCHIVE_MONOLITHIC_REFACTORING_PLAN.md
- docs/ARCHIVE_PHASE_2_3_REFACTORING.md
- docs/ARCHIVE_TECH_DEBT_ANALYSIS_2025.md
- docs/structured_project_plan.md
- docs/development/phase4/* (agent_answers, polish_roadmap, etc.)
- docs/development/phase5/* (implementation_plan, session_complete, etc.)
- docs/development/portal/* (phase summaries, playtest summaries)
- docs/planning/* (BALANCE_NOTES, DUNGEON_LEVELS_PLAN, VAULT_SYSTEM_PLAN, VICTORY_CONDITION_PHASES)
- archive/obsolete-docs/* (component access migration, spell registry history, etc.)
- archive/old-releases/* (release notes, changelogs)
- archive/session-docs/* (PR/summary drops, tech debt notes)
- tests/GOLDEN_PATH_TESTS.md
- ENGINE_ENTRYPOINTS_NOTES.md
- PLAYER_PAIN_POINTS.md
- WAND_PORTAL_CANCELLATION_IMPLEMENTATION.md

### Proposed removals (scratch/obsolete)
- Removed in this pass: PHASE_13B_SUMMARY.md, PHASE_13C_SUMMARY.md, PHASE_13D_SUMMARY.md, SESSION_COMPLETE_SUMMARY.md, phase13b_analysis.txt, phase13c_analysis.txt, phase13d_fix_results.txt, YAML_DOCUMENTATION_COMPLETE.txt, docs/cursor_agent_presets.md, docs/model_selection_guide.md, docs/structured_project_plan_thinking_dump.md, archive/session-docs/pr_description.md, archive/session-docs/TEST_SUITE_FIX_SUMMARY.md, archive/session-docs/GIT_WORKFLOW_SUMMARY.md, archive/session-docs/DEBUG_EXIT_ISSUE.md

## Notes / Decisions Log
- Use this section to record any judgment calls or moves of content between docs.
- Removed PHASE_13B/C/D summaries and related analysis/scratch files; archived session one-offs culled.
- ROADMAP.md rewritten to match current scenario/ETP/metrics reality and mark historical docs.
- Phase READMEs (development/phase4, phase5, portal) and victory phases doc marked as historical snapshots.
- docs/README.md updated to point to canonical references and clarify archives.
- AI_SYSTEM code locations corrected; duplicate balance_system_overview_chatgpt removed.
- Archive folders now have READMEs clarifying historical status; planning folder labeled historical.
- CONTRIBUTING_AUTOGEN marked as historical guidance; prefer canonical docs for current entrypoints.
