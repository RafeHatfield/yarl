.PHONY: clean test run quick-test bot bot-smoke soak help test-fast test-full ci-quick balance-ci-local \
        eco-swarm-baseline eco-swarm-baseline-json eco-swarm-speed-full eco-swarm-speed-full-json \
        eco-swarm-brutal-baseline eco-swarm-brutal-baseline-json eco-swarm-brutal-speed-full eco-swarm-brutal-speed-full-json \
        eco-swarm-tight eco-swarm-tight-json eco-zombie-horde eco-zombie-horde-json \
        eco-swarm-all eco-swarm-report worldgen-quick worldgen-ci worldgen-report \
        difficulty-collect difficulty-graphs difficulty-dashboard difficulty-all \
        balance-suite balance-suite-fast balance-suite-update-baseline balance-suite-update-baseline-fast \
        dist-build dist-clean dist-rebuild dist-run dist-check

# Use python3 (or whatever python is active if in virtualenv)
PYTHON := $(shell which python3 2>/dev/null || which python 2>/dev/null || echo python3)

help:
	@echo "Development Commands:"
	@echo ""
	@echo "  make clean       - Clear Python cache (fixes 'old code' issues)"
	@echo "  make run         - Start game with fresh code"
	@echo "  make clean-run   - Clear cache + start game"
	@echo "  make run-test    - Start test game with fresh code"
	@echo ""
	@echo "Testing:"
	@echo "  make test-fast   - Fast pytest (excludes slow tests)"
	@echo "  make test-full   - Full pytest (all tests, including slow)"
	@echo "  make test        - Run Phase 5 critical tests"
	@echo "  make quick-test  - Quick validation (no full game needed)"
	@echo "  make worldgen-quick  - Worldgen sanity smoke (depth 3, 10 runs)"
	@echo "  make worldgen-ci     - Worldgen sanity + JSON export (depth 3, 20 runs)"
	@echo "  make worldgen-report - Worldgen sanity report (depth 3, 50 runs)"
	@echo ""
	@echo "CI / Balance:"
	@echo "  make ci-quick              - Run quick CI checks (fast tests + ETP + loot)"
	@echo "  make balance-ci-local      - Run full Balance CI locally (with coverage)"
	@echo "  make balance-suite              - Run full balance suite (compare mode)"
	@echo "  make balance-suite-fast         - Run balance suite (fast compare mode)"
	@echo "  make balance-suite-update-baseline      - Update baseline (full)"
	@echo "  make balance-suite-update-baseline-fast - Update baseline (fast)"
	@echo "  make hazards-suite              - Run hazards suite (traps/environmental)"
	@echo "  make hazards-suite-fast         - Run hazards suite (fast mode)"
	@echo ""
	@echo "Bot Testing:"
	@echo "  make bot         - Single bot run (watch the bot play)"
	@echo "  make bot-smoke   - Quick smoke test (10 runs, 500 turns, 3 floors)"
	@echo "  make soak        - Extended soak test (200 runs, 5000 turns, 10 floors)"
	@echo ""
	@echo "Distribution:"
	@echo "  make dist-build   - Build distributable package (requires PyInstaller)"
	@echo "  make dist-clean   - Remove PyInstaller build artifacts"
	@echo "  make dist-rebuild - Clean + build from scratch"
	@echo "  make dist-run     - Run the built executable from dist/"
	@echo ""
	@echo "IMPORTANT: Always run 'make clean' if game behaves unexpectedly!"
	@echo "NOTE: Activate virtualenv first if using one: source ~/.virtualenvs/rlike/bin/activate"

clean:
	@echo "🧹 Clearing Python cache..."
	@find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	@find . -name '*.pyc' -delete 2>/dev/null || true
	@echo "✅ Cache cleared - code will reload fresh"

test:
	@echo "🧪 Running Phase 5 critical tests..."
	@$(PYTHON) -m pytest tests/test_phase5_critical_paths.py -v --tb=short || \
		echo "⚠️  Tests failed or pytest not available"

quick-test: clean
	@echo "⚡ Running quick validation..."
	@$(PYTHON) test_phase5_quick.py

# ─────────────────────────────────────────────────────────────────────
# Testing shortcuts
# ─────────────────────────────────────────────────────────────────────

test-fast:
	@echo "🧪 Running fast pytest (excludes slow tests)..."
	@$(PYTHON) -m pytest -q -m "not slow"

test-full:
	@echo "🧪 Running full pytest (all tests, including slow)..."
	@$(PYTHON) -m pytest -q

ci-quick:
	@echo "⚡ Running quick CI checks..."
	@./scripts/ci_quick.sh

balance-ci-local:
	@echo "🔬 Running full Balance CI locally (with coverage)..."
	@echo ""
	@echo "Step 1: Full pytest with coverage"
	@$(PYTHON) -m pytest -q \
		--cov=. \
		--cov-report=term-missing \
		--cov-report=html:htmlcov \
		--cov-fail-under=80
	@echo ""
	@echo "Step 2: Strict ETP sanity check"
	@./scripts/ci_run_etp.sh
	@echo ""
	@echo "Step 3: Full loot sanity check (5 runs per band)"
	@./scripts/ci_run_loot.sh
	@echo ""
	@echo "✅ Balance CI complete. Coverage report: htmlcov/index.html"

run: clean
	@echo "🎮 Starting game with fresh code..."
	@$(PYTHON) engine.py

clean-run: clean run

run-test: clean
	@echo "🎮 Starting test game with fresh code..."
	@$(PYTHON) engine.py --testing --wizard
# @$(PYTHON) engine.py --testing --start-level 20 --no-monsters --wizard --god-mode --reveal-map
# python engine.py --telemetry-json output.json
# python engine.py --bot
# python3 engine.py --bot-soak

# Run 10 bot games (default)
# python3 engine.py --bot-soak

# Run custom number of games
# python3 engine.py --bot-soak --runs 50

# With custom telemetry path
# python3 engine.py --bot-soak --runs 20 --telemetry-json telemetry/my_soak.json

bot: clean
	@echo "🤖 Single Bot Run (watch the bot play)"
	@$(PYTHON) engine.py --bot

bot-smoke: clean
	@echo "🤖 Bot Smoke Test: 10 runs, 500 turns max, 3 floors max"
	@mkdir -p logs
	@$(PYTHON) engine.py --bot-soak --runs 10 --max-turns 500 --max-floors 3 \
		--metrics-log logs/bot_smoke.jsonl --telemetry-json logs/bot_smoke_telemetry.json

soak: clean
	@echo "🧪 Bot Soak Test: 200 runs, 5000 turns max, 10 floors max (with window)"
	@mkdir -p logs
	@$(PYTHON) engine.py --bot-soak --runs 200 --max-turns 1000 --max-floors 10 \
		--metrics-log logs/bot_soak.jsonl --telemetry-json logs/bot_soak_telemetry.json

soak-headless: clean
	@echo "🧪 Bot Soak Test: 200 runs, 5000 turns max, 10 floors max (headless - no window)"
	@mkdir -p logs
	@$(PYTHON) engine.py --bot-soak --headless --runs 200 --max-turns 1000 --max-floors 10 \
		--metrics-log logs/bot_soak.jsonl --telemetry-json logs/bot_soak_telemetry.json

.DEFAULT_GOAL := help

# Default knobs (override on the command line if you like)
RUNS       ?= 50
MAX_TURNS  ?= 2000
MAX_FLOORS ?= 3

LOG_DIR    ?= logs
PYTHON     ?= python3

# Generic persona soak:
# Usage:
#   make bot-soak PERSONA=balanced
#   make bot-soak PERSONA=cautious RUNS=100 MAX_TURNS=5000
PERSONA ?= balanced

bot-soak:
	mkdir -p reports/soak
	$(PYTHON) engine.py \
	  --bot-soak \
	  --bot-persona $(PERSONA) \
	  --runs $(RUNS) \
	  --max-turns $(MAX_TURNS) \
	  --max-floors $(MAX_FLOORS) \
	  --metrics-log reports/soak/soak_$(PERSONA).csv \
	  --telemetry-json reports/soak/soak_$(PERSONA)_telemetry.json

# Convenience shortcuts for common personas
bot-soak-balanced:
	$(MAKE) bot-soak PERSONA=balanced

bot-soak-cautious:
	$(MAKE) bot-soak PERSONA=cautious

bot-soak-aggressive:
	$(MAKE) bot-soak PERSONA=aggressive

bot-soak-greedy:
	$(MAKE) bot-soak PERSONA=greedy

bot-soak-speedrunner:
	$(MAKE) bot-soak PERSONA=speedrunner

# Scenario-based soak testing
# Usage:
#   make bot-soak-scenario SCENARIO=orc_swarm_tight RUNS=50 MAX_TURNS=150 MAX_FLOORS=1
#   make bot-soak-scenario SCENARIO=orc_swarm_baseline PERSONA=cautious RUNS=100
SCENARIO ?= orc_swarm_tight

bot-soak-scenario:
	mkdir -p reports/soak
	$(PYTHON) engine.py \
	  --bot-soak \
	  --bot-persona $(PERSONA) \
	  --runs $(RUNS) \
	  --max-turns $(MAX_TURNS) \
	  --max-floors $(MAX_FLOORS) \
	  --scenario $(SCENARIO) \
	  --metrics-log reports/soak/soak_$(PERSONA)_$(SCENARIO).csv \
	  --telemetry-json reports/soak/soak_$(PERSONA)_$(SCENARIO)_telemetry.json

bot-survivability-report:
	python3 tools/bot_survivability_report.py



# --------------------------------------------------------------------
# Ecosystem / Scenario Harness Shortcuts
# --------------------------------------------------------------------

.PHONY: worldgen-quick worldgen-ci worldgen-report eco-balance-report

worldgen-quick:
	python3 worldgen_sanity.py --runs 10 --depth 3

worldgen-ci:
	python3 worldgen_sanity.py --runs 20 --depth 3 --export-json worldgen_depth3_20runs.json

worldgen-report:
	python3 worldgen_sanity.py --runs 50 --depth 3 --export-json worldgen_depth3_50runs.json

.PHONY: eco-quick eco-all eco-ci eco-report \
        eco-plague eco-plague-json \
        eco-backstab eco-backstab-json \
        eco-duel-baseline eco-duel-baseline-json \
        eco-duel-speed-light eco-duel-speed-light-json \
        eco-duel-speed-full eco-duel-speed-full-json \
        eco-duel-slow-zombie-baseline eco-duel-slow-zombie-baseline-json \
        eco-duel-slow-zombie-full eco-duel-slow-zombie-full-json \
        eco-depth1-orc-json eco-depth2-orc-json eco-depth3-orc-json \
        eco-depth4-plague-json eco-depth5-zombie-json

# A fast sampler of the main scenarios we care about (no JSON export)
eco-quick: eco-plague eco-backstab eco-duel-baseline

# Run *all* the dueling-related scenarios (no JSON export)
eco-all: eco-plague eco-backstab \
         eco-duel-baseline eco-duel-speed-light eco-duel-speed-full \
         eco-duel-slow-zombie-baseline eco-duel-slow-zombie-full

# Mirror what GitHub Actions does for ecosystem sanity on PRs
eco-ci:
	# Quick CI-style plague arena sanity
	python3 ecosystem_sanity.py \
	  --scenario plague_arena \
	  --runs 20 \
	  --turn-limit 500 \
	  --player-bot tactical_fighter \
	  --fail-on-expected
	# Quick CI-style backstab training sanity
	python3 ecosystem_sanity.py \
	  --scenario backstab_training \
	  --runs 50 \
	  --turn-limit 50 \
	  --player-bot tactical_fighter \
	  --fail-on-expected

# Run all key scenarios with JSON export, for tuning/analysis sessions
eco-report: \
	eco-plague-json \
	eco-backstab-json \
	eco-duel-baseline-json \
	eco-duel-speed-light-json \
	eco-duel-speed-full-json \
	eco-duel-slow-zombie-baseline-json \
	eco-duel-slow-zombie-full-json \
	eco-depth1-orc-json eco-depth2-orc-json eco-depth3-orc-json \
	eco-depth4-plague-json eco-depth5-zombie-json \
	eco-fire-beetle-json \
	eco-orc-gauntlet-json eco-orc-wave3-json eco-tight-funnel-json eco-plague-gauntlet-json

# --------------------
# Plague Arena
# --------------------

eco-plague:
	python3 ecosystem_sanity.py \
	  --scenario plague_arena \
	  --runs 20 \
	  --turn-limit 500 \
	  --player-bot tactical_fighter \
	  --fail-on-expected

eco-plague-json:
	python3 ecosystem_sanity.py \
	  --scenario plague_arena \
	  --runs 100 \
	  --turn-limit 500 \
	  --player-bot tactical_fighter \
	  --fail-on-expected \
	  --export-json plague_arena_100runs.json

# --------------------
# Backstab Training
# --------------------

eco-backstab:
	python3 ecosystem_sanity.py \
	  --scenario backstab_training \
	  --runs 50 \
	  --turn-limit 50 \
	  --player-bot tactical_fighter \
	  --fail-on-expected

eco-backstab-json:
	python3 ecosystem_sanity.py \
	  --scenario backstab_training \
	  --runs 100 \
	  --turn-limit 50 \
	  --player-bot tactical_fighter \
	  --fail-on-expected \
	  --export-json backstab_training_100runs.json

# --------------------
# Orc Dueling Pits (baseline / light / full speed)
# --------------------

eco-duel-baseline:
	python3 ecosystem_sanity.py \
	  --scenario dueling_pit \
	  --runs 50 \
	  --turn-limit 100 \
	  --player-bot tactical_fighter \
	  --fail-on-expected

eco-duel-baseline-json:
	python3 ecosystem_sanity.py \
	  --scenario dueling_pit \
	  --runs 50 \
	  --turn-limit 100 \
	  --player-bot tactical_fighter \
	  --fail-on-expected \
	  --export-json dueling_pit_50runs.json

eco-duel-speed-light:
	python3 ecosystem_sanity.py \
	  --scenario dueling_pit_speed_light \
	  --runs 50 \
	  --turn-limit 100 \
	  --player-bot tactical_fighter \
	  --fail-on-expected

eco-duel-speed-light-json:
	python3 ecosystem_sanity.py \
	  --scenario dueling_pit_speed_light \
	  --runs 50 \
	  --turn-limit 100 \
	  --player-bot tactical_fighter \
	  --fail-on-expected \
	  --export-json dueling_pit_speed_light_50runs.json

eco-duel-speed-full:
	python3 ecosystem_sanity.py \
	  --scenario dueling_pit_speed_full \
	  --runs 50 \
	  --turn-limit 100 \
	  --player-bot tactical_fighter \
	  --fail-on-expected

eco-duel-speed-full-json:
	python3 ecosystem_sanity.py \
	  --scenario dueling_pit_speed_full \
	  --runs 50 \
	  --turn-limit 100 \
	  --player-bot tactical_fighter \
	  --fail-on-expected \
	  --export-json dueling_pit_speed_full_50runs.json

# --------------------
# Slow Zombie Dueling (momentum lab)
# --------------------

eco-duel-slow-zombie-baseline:
	python3 ecosystem_sanity.py \
	  --scenario dueling_pit_slow_zombie_baseline \
	  --runs 50 \
	  --turn-limit 100 \
	  --player-bot tactical_fighter \
	  --fail-on-expected

eco-duel-slow-zombie-baseline-json:
	python3 ecosystem_sanity.py \
	  --scenario dueling_pit_slow_zombie_baseline \
	  --runs 50 \
	  --turn-limit 100 \
	  --player-bot tactical_fighter \
	  --fail-on-expected \
	  --export-json dueling_pit_slow_zombie_baseline_50runs.json

eco-duel-slow-zombie-full:
	python3 ecosystem_sanity.py \
	  --scenario dueling_pit_slow_zombie_speed_full \
	  --runs 50 \
	  --turn-limit 100 \
	  --player-bot tactical_fighter \
	  --fail-on-expected

eco-duel-slow-zombie-full-json:
	python3 ecosystem_sanity.py \
	  --scenario dueling_pit_slow_zombie_speed_full \
	  --runs 50 \
	  --turn-limit 100 \
	  --player-bot tactical_fighter \
	  --fail-on-expected \
	  --export-json dueling_pit_slow_zombie_speed_full_50runs.json

# --------------------
# Depth Probe Scenarios (Phase 17.0)
# --------------------

eco-depth1-orc-json:
	python3 ecosystem_sanity.py \
	  --scenario depth1_orc_easy \
	  --runs 30 \
	  --turn-limit 80 \
	  --player-bot tactical_fighter \
	  --fail-on-expected \
	  --export-json depth1_orc_easy_30runs.json

eco-depth2-orc-json:
	python3 ecosystem_sanity.py \
	  --scenario depth2_orc_baseline \
	  --runs 40 \
	  --turn-limit 100 \
	  --player-bot tactical_fighter \
	  --fail-on-expected \
	  --export-json depth2_orc_baseline_40runs.json

eco-depth3-orc-json:
	python3 ecosystem_sanity.py \
	  --scenario depth3_orc_brutal \
	  --runs 50 \
	  --turn-limit 110 \
	  --player-bot tactical_fighter \
	  --fail-on-expected \
	  --export-json depth3_orc_brutal_50runs.json

eco-depth4-plague-json:
	python3 ecosystem_sanity.py \
	  --scenario depth4_plague \
	  --runs 50 \
	  --turn-limit 140 \
	  --player-bot tactical_fighter \
	  --fail-on-expected \
	  --export-json depth4_plague_50runs.json

eco-depth5-zombie-json:
	python3 ecosystem_sanity.py \
	  --scenario depth5_zombie \
	  --runs 50 \
	  --turn-limit 150 \
	  --player-bot tactical_fighter \
	  --fail-on-expected \
	  --export-json depth5_zombie_50runs.json

# --------------------
# Fire Beetle Identity
# --------------------

eco-fire-beetle:
	python3 ecosystem_sanity.py \
	  --scenario monster_fire_beetle_identity \
	  --runs 30 \
	  --turn-limit 150 \
	  --player-bot tactical_fighter \
	  --fail-on-expected

eco-fire-beetle-json:
	python3 ecosystem_sanity.py \
	  --scenario monster_fire_beetle_identity \
	  --runs 30 \
	  --turn-limit 150 \
	  --player-bot tactical_fighter \
	  --fail-on-expected \
	  --export-json monster_fire_beetle_identity_30runs.json

# --------------------
# Orc Swarm Scenarios
# --------------------

eco-swarm-baseline:
	python3 ecosystem_sanity.py \
	  --scenario orc_swarm_baseline \
	  --runs 50 \
	  --turn-limit 100 \
	  --player-bot tactical_fighter \
	  --fail-on-expected

eco-swarm-baseline-json:
	python3 ecosystem_sanity.py \
	  --scenario orc_swarm_baseline \
	  --runs 50 \
	  --turn-limit 100 \
	  --player-bot tactical_fighter \
	  --fail-on-expected \
	  --export-json orc_swarm_baseline_50runs.json

eco-swarm-speed-full:
	python3 ecosystem_sanity.py \
	  --scenario orc_swarm_speed_full \
	  --runs 50 \
	  --turn-limit 100 \
	  --player-bot tactical_fighter \
	  --fail-on-expected

eco-swarm-speed-full-json:
	python3 ecosystem_sanity.py \
	  --scenario orc_swarm_speed_full \
	  --runs 50 \
	  --turn-limit 100 \
	  --player-bot tactical_fighter \
	  --fail-on-expected \
	  --export-json orc_swarm_speed_full_50runs.json

# --------------------
# Orc Swarm – Brutal
# --------------------

eco-swarm-brutal-baseline:
	python3 ecosystem_sanity.py \
	  --scenario orc_swarm_brutal_baseline \
	  --runs 50 \
	  --turn-limit 100 \
	  --player-bot tactical_fighter \
	  --fail-on-expected

eco-swarm-brutal-baseline-json:
	python3 ecosystem_sanity.py \
	  --scenario orc_swarm_brutal_baseline \
	  --runs 50 \
	  --turn-limit 100 \
	  --player-bot tactical_fighter \
	  --fail-on-expected \
	  --export-json orc_swarm_brutal_baseline_50runs.json

eco-swarm-brutal-speed-full:
	python3 ecosystem_sanity.py \
	  --scenario orc_swarm_brutal_speed_full \
	  --runs 50 \
	  --turn-limit 100 \
	  --player-bot tactical_fighter \
	  --fail-on-expected

eco-swarm-brutal-speed-full-json:
	python3 ecosystem_sanity.py \
	  --scenario orc_swarm_brutal_speed_full \
	  --runs 50 \
	  --turn-limit 100 \
	  --player-bot tactical_fighter \
	  --fail-on-expected \
	  --export-json orc_swarm_brutal_speed_full_50runs.json

eco-swarm-tight:
	python3 ecosystem_sanity.py \
	  --scenario orc_swarm_tight \
	  --runs 50 \
	  --turn-limit 120 \
	  --player-bot tactical_fighter \
	  --fail-on-expected

eco-swarm-tight-json:
	python3 ecosystem_sanity.py \
	  --scenario orc_swarm_tight \
	  --runs 50 \
	  --turn-limit 120 \
	  --player-bot tactical_fighter \
	  --fail-on-expected \
	  --export-json orc_swarm_tight_50runs.json

eco-zombie-horde:
	python3 ecosystem_sanity.py \
	  --scenario zombie_horde \
	  --runs 50 \
	  --turn-limit 120 \
	  --player-bot tactical_fighter \
	  --fail-on-expected

eco-zombie-horde-json:
	python3 ecosystem_sanity.py \
	  --scenario zombie_horde \
	  --runs 50 \
	  --turn-limit 120 \
	  --player-bot tactical_fighter \
	  --fail-on-expected \
	  --export-json zombie_horde_50runs.json

# --------------------
# Phase 17B.1: Lethal Scenarios for Survivability Testing
# --------------------

eco-orc-gauntlet:
	python3 ecosystem_sanity.py \
	  --scenario orc_gauntlet_5rooms \
	  --runs 50 \
	  --turn-limit 250 \
	  --player-bot tactical_fighter \
	  --fail-on-expected

eco-orc-gauntlet-json:
	python3 ecosystem_sanity.py \
	  --scenario orc_gauntlet_5rooms \
	  --runs 50 \
	  --turn-limit 250 \
	  --player-bot tactical_fighter \
	  --fail-on-expected \
	  --export-json reports/orc_gauntlet_5rooms_50runs.json

eco-orc-wave3:
	python3 ecosystem_sanity.py \
	  --scenario orc_swarm_wave3 \
	  --runs 50 \
	  --turn-limit 250 \
	  --player-bot tactical_fighter \
	  --fail-on-expected

eco-orc-wave3-json:
	python3 ecosystem_sanity.py \
	  --scenario orc_swarm_wave3 \
	  --runs 50 \
	  --turn-limit 250 \
	  --player-bot tactical_fighter \
	  --fail-on-expected \
	  --export-json reports/orc_swarm_wave3_50runs.json

eco-tight-funnel:
	python3 ecosystem_sanity.py \
	  --scenario tight_brutal_funnel \
	  --runs 50 \
	  --turn-limit 200 \
	  --player-bot tactical_fighter \
	  --fail-on-expected

eco-tight-funnel-json:
	python3 ecosystem_sanity.py \
	  --scenario tight_brutal_funnel \
	  --runs 50 \
	  --turn-limit 200 \
	  --player-bot tactical_fighter \
	  --fail-on-expected \
	  --export-json reports/tight_brutal_funnel_50runs.json

eco-plague-gauntlet:
	python3 ecosystem_sanity.py \
	  --scenario plague_gauntlet \
	  --runs 50 \
	  --turn-limit 300 \
	  --player-bot tactical_fighter \
	  --fail-on-expected

eco-plague-gauntlet-json:
	python3 ecosystem_sanity.py \
	  --scenario plague_gauntlet \
	  --runs 50 \
	  --turn-limit 300 \
	  --player-bot tactical_fighter \
	  --fail-on-expected \
	  --export-json reports/plague_gauntlet_50runs.json

eco-swarm-all: eco-swarm-baseline eco-swarm-speed-full eco-swarm-brutal-baseline eco-swarm-brutal-speed-full

eco-swarm-report: \
	eco-swarm-baseline-json \
	eco-swarm-speed-full-json \
	eco-swarm-brutal-baseline-json \
	eco-swarm-brutal-speed-full-json

# --------------------------------------------------------------------
# Ecosystem & bot balance reporting
# --------------------------------------------------------------------

eco-balance-report:
	python3 tools/eco_balance_report.py \
	  --ecosystem-json dueling_pit_50runs.json dueling_pit_speed_light_50runs.json dueling_pit_speed_full_50runs.json \
	    orc_swarm_baseline_50runs.json orc_swarm_speed_full_50runs.json orc_swarm_brutal_baseline_50runs.json orc_swarm_brutal_speed_full_50runs.json \
	    orc_swarm_tight_50runs.json zombie_horde_50runs.json \
	    plague_arena_100runs.json backstab_training_100runs.json \
	    monster_fire_beetle_identity_30runs.json \
	  --worldgen-json worldgen_depth3_20runs.json \
	  --output-markdown reports/eco_balance_report.md

# --------------------------------------------------------------------
# Difficulty Curve Tooling (Phase 16D)
# --------------------------------------------------------------------

difficulty-collect:
	python3 tools/collect_metrics_for_visualizer.py

difficulty-graphs:
	python3 tools/difficulty_curve_visualizer.py

difficulty-dashboard:
	python3 tools/generate_difficulty_dashboard.py

difficulty-all: eco-all difficulty-collect difficulty-graphs difficulty-dashboard


bot-soak-and-report:
	make bot-soak
	python3 tools/bot_survivability_report.py > reports/bot_survivability_report.md


bot-survivability:
	python3 tools/bot_survivability_report.py > reports/bot_survivability_report.md

# --------------------------------------------------------------------
# Balance Suite (Phase 18 QOL)
# --------------------------------------------------------------------

balance-suite:
	python3 tools/balance_suite.py

balance-suite-fast:
	python3 tools/balance_suite.py --fast

# Baseline update targets - write new baseline and exit 0
balance-suite-update-baseline:
	python3 tools/balance_suite.py --update-baseline

balance-suite-update-baseline-fast:
	python3 tools/balance_suite.py --update-baseline --fast

# Hazards suite targets - environmental hazards and trap scenarios
hazards-suite:
	python3 tools/hazards_suite.py

hazards-suite-fast:
	python3 tools/hazards_suite.py --fast

# --------------------------------------------------------------------
# Distribution / Packaging (PyInstaller)
# --------------------------------------------------------------------

# Configuration
PYINSTALLER   ?= pyinstaller
SPEC_FILE     := build/pyinstaller/CatacombsOfYARL.spec
DIST_DIR      := dist/CatacombsOfYARL
BUILD_DIR     := build/CatacombsOfYARL

# Check that PyInstaller is available
dist-check:
	@command -v $(PYINSTALLER) >/dev/null 2>&1 || { \
		echo ""; \
		echo "❌ PyInstaller not found in PATH."; \
		echo ""; \
		echo "   Install with:  pip install pyinstaller"; \
		echo ""; \
		exit 1; \
	}
	@echo "✅ PyInstaller found: $$(command -v $(PYINSTALLER))"

# Build the distributable package
dist-build: dist-check
	@echo ""
	@echo "📦 Building distributable package..."
	@echo "   Spec file: $(SPEC_FILE)"
	@echo "   Output:    $(DIST_DIR)/"
	@echo ""
	@$(PYINSTALLER) --clean -y $(SPEC_FILE)
	@echo ""
	@echo "✅ Build complete!"
	@echo "   Output: $(DIST_DIR)/"
	@echo ""
	@echo "   To test: make dist-run"
	@echo "   To package: zip -r CatacombsOfYARL.zip $(DIST_DIR)"

# Clean PyInstaller build artifacts (careful not to remove other build/ contents)
dist-clean:
	@echo "🧹 Removing PyInstaller build artifacts..."
	@rm -rf $(BUILD_DIR) 2>/dev/null || true
	@rm -rf $(DIST_DIR) 2>/dev/null || true
	@rm -f *.spec 2>/dev/null || true
	@echo "✅ Distribution artifacts cleaned"

# Full rebuild from scratch
dist-rebuild: dist-clean dist-build

# Run the built executable (best-effort cross-platform)
dist-run:
	@if [ ! -d "$(DIST_DIR)" ]; then \
		echo "❌ Distribution not found at $(DIST_DIR)"; \
		echo "   Run 'make dist-build' first."; \
		exit 1; \
	fi
	@echo "🎮 Running built executable..."
	@if [ -f "$(DIST_DIR)/CatacombsOfYARL" ]; then \
		./$(DIST_DIR)/CatacombsOfYARL; \
	elif [ -f "$(DIST_DIR)/CatacombsOfYARL.exe" ]; then \
		echo "   (Windows: run dist\\CatacombsOfYARL\\CatacombsOfYARL.exe manually)"; \
	else \
		echo "❌ Executable not found in $(DIST_DIR)"; \
		exit 1; \
	fi
