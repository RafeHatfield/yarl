.PHONY: clean test run quick-test bot bot-smoke soak help test-fast test-full ci-quick balance-ci-local eco-swarm-baseline eco-swarm-baseline-json eco-swarm-speed-full eco-swarm-speed-full-json eco-swarm-brutal-baseline eco-swarm-brutal-baseline-json eco-swarm-brutal-speed-full eco-swarm-brutal-speed-full-json eco-swarm-all eco-swarm-report

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
	@echo ""
	@echo "CI / Balance:"
	@echo "  make ci-quick         - Run quick CI checks (fast tests + ETP + loot)"
	@echo "  make balance-ci-local - Run full Balance CI locally (with coverage)"
	@echo ""
	@echo "Bot Testing:"
	@echo "  make bot         - Single bot run (watch the bot play)"
	@echo "  make bot-smoke   - Quick smoke test (10 runs, 500 turns, 3 floors)"
	@echo "  make soak        - Extended soak test (200 runs, 5000 turns, 10 floors)"
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
	@$(PYTHON) engine.py --testing --start-level 91 --wizard
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
	mkdir -p $(LOG_DIR)
	$(PYTHON) engine.py \
	  --bot-soak \
	  --bot-persona $(PERSONA) \
	  --runs $(RUNS) \
	  --max-turns $(MAX_TURNS) \
	  --max-floors $(MAX_FLOORS) \
	  --metrics-log $(LOG_DIR)/soak_$(PERSONA).csv

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

# A tiny "smoke" run for quick sanity checks
bot-smoke:
	mkdir -p $(LOG_DIR)
	$(PYTHON) engine.py \
	  --bot-soak \
	  --bot-persona balanced \
	  --runs 10 \
	  --max-turns 500 \
	  --max-floors 2 \
	  --metrics-log $(LOG_DIR)/bot_smoke.csv



# --------------------------------------------------------------------
# Ecosystem / Scenario Harness Shortcuts
# --------------------------------------------------------------------

.PHONY: eco-quick eco-all eco-ci eco-report \
        eco-plague eco-plague-json \
        eco-backstab eco-backstab-json \
        eco-duel-baseline eco-duel-baseline-json \
        eco-duel-speed-light eco-duel-speed-light-json \
        eco-duel-speed-full eco-duel-speed-full-json \
        eco-duel-slow-zombie-baseline eco-duel-slow-zombie-baseline-json \
        eco-duel-slow-zombie-full eco-duel-slow-zombie-full-json

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
	eco-duel-slow-zombie-full-json

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

eco-swarm-all: eco-swarm-baseline eco-swarm-speed-full eco-swarm-brutal-baseline eco-swarm-brutal-speed-full

eco-swarm-report: \
	eco-swarm-baseline-json \
	eco-swarm-speed-full-json \
	eco-swarm-brutal-baseline-json \
	eco-swarm-brutal-speed-full-json
