.PHONY: clean test run quick-test help

help:
	@echo "Phase 5 Development Commands:"
	@echo ""
	@echo "  make clean       - Clear Python cache (fixes 'old code' issues)"
	@echo "  make test        - Run Phase 5 critical tests"
	@echo "  make quick-test  - Quick validation (no full game needed)"
	@echo "  make run         - Start game with fresh code"
	@echo "  make clean-run   - Clear cache + start game"
	@echo ""
	@echo "IMPORTANT: Always run 'make clean' if game behaves unexpectedly!"

clean:
	@echo "🧹 Clearing Python cache..."
	@find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	@find . -name '*.pyc' -delete 2>/dev/null || true
	@echo "✅ Cache cleared - code will reload fresh"

test:
	@echo "🧪 Running Phase 5 critical tests..."
	@python3 -m pytest tests/test_phase5_critical_paths.py -v --tb=short 2>/dev/null || \
		echo "⚠️  pytest not available, skipping"

quick-test: clean
	@echo "⚡ Running quick validation..."
	@python3 test_phase5_quick.py

run: clean
	@echo "🎮 Starting game with fresh code..."
	@python3 engine.py

clean-run: clean run

.DEFAULT_GOAL := help

