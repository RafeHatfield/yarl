.PHONY: clean test run quick-test bot bot-smoke soak help

# Use python3 (or whatever python is active if in virtualenv)
PYTHON := $(shell which python3 2>/dev/null || which python 2>/dev/null || echo python3)

help:
	@echo "Phase 5 Development Commands:"
	@echo ""
	@echo "  make clean       - Clear Python cache (fixes 'old code' issues)"
	@echo "  make test        - Run Phase 5 critical tests"
	@echo "  make quick-test  - Quick validation (no full game needed)"
	@echo "  make run         - Start game with fresh code"
	@echo "  make clean-run   - Clear cache + start game"
	@echo "  make run-test    - Start test game with fresh code"
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
	@echo "🧪 Bot Soak Test: 200 runs, 5000 turns max, 10 floors max"
	@mkdir -p logs
	@$(PYTHON) engine.py --bot-soak --runs 200 --max-turns 1000 --max-floors 10 \
		--metrics-log logs/bot_soak.jsonl --telemetry-json logs/bot_soak_telemetry.json

.DEFAULT_GOAL := help

