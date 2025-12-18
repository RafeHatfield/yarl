"""Tests for balance suite determinism.

Verifies that running scenarios with the same seed_base produces
identical metrics across multiple invocations.

Phase 19: Fix balance-suite flakiness by ensuring deterministic seeding.
"""

import pytest
import random

from engine.rng_config import reset_rng_state, stable_scenario_seed, set_global_seed


class TestBalanceSuiteDeterminism:
    """Tests for deterministic scenario execution."""
    
    def setup_method(self):
        """Reset RNG state before each test."""
        reset_rng_state()
    
    def teardown_method(self):
        """Reset RNG state after each test."""
        reset_rng_state()
    
    def test_stable_scenario_seed_determinism(self):
        """stable_scenario_seed produces identical seeds for identical inputs."""
        scenario_id = "depth2_orc_baseline_fine"
        seed_base = 1337
        
        # Run twice
        seeds_run1 = [stable_scenario_seed(scenario_id, i, seed_base) for i in range(10)]
        seeds_run2 = [stable_scenario_seed(scenario_id, i, seed_base) for i in range(10)]
        
        assert seeds_run1 == seeds_run2
    
    def test_seeded_random_sequence_determinism(self):
        """Same seed produces identical random sequence (simulates combat rolls)."""
        seed = stable_scenario_seed("depth2_orc_baseline_fine", 0, 1337)
        
        # First run
        set_global_seed(seed)
        rolls_run1 = [random.randint(1, 20) for _ in range(100)]
        
        # Second run with same seed
        set_global_seed(seed)
        rolls_run2 = [random.randint(1, 20) for _ in range(100)]
        
        assert rolls_run1 == rolls_run2
    
    def test_different_runs_get_different_seeds(self):
        """Each run index should get a unique seed."""
        scenario_id = "depth3_orc_brutal"
        seed_base = 1337
        
        seeds = [stable_scenario_seed(scenario_id, i, seed_base) for i in range(50)]
        
        # All seeds should be unique
        assert len(set(seeds)) == 50
    
    def test_different_scenarios_get_different_seeds(self):
        """Different scenarios should get different seed sequences."""
        seed_base = 1337
        
        seeds_scenario1 = [stable_scenario_seed("depth2_orc_baseline", i, seed_base) for i in range(10)]
        seeds_scenario2 = [stable_scenario_seed("depth2_orc_baseline_fine", i, seed_base) for i in range(10)]
        
        # No overlap between the two scenarios' seeds
        assert set(seeds_scenario1).isdisjoint(set(seeds_scenario2))


@pytest.mark.slow
class TestScenarioHarnessDeterminism:
    """Integration tests for scenario harness determinism.
    
    These tests run actual scenarios and verify metrics match.
    Marked slow because they execute game logic.
    """
    
    def setup_method(self):
        """Reset RNG state before each test."""
        reset_rng_state()
    
    def teardown_method(self):
        """Reset RNG state after each test."""
        reset_rng_state()
    
    def test_run_scenario_many_determinism(self):
        """run_scenario_many with seed_base produces identical metrics."""
        from config.level_template_registry import get_scenario_registry
        from services.scenario_harness import run_scenario_many, make_bot_policy
        
        # Use a small, fast scenario
        registry = get_scenario_registry()
        
        # Find a simple scenario (skeleton identity is fast)
        scenario = registry.get_scenario_definition("monster_skeleton_identity")
        if scenario is None:
            # Fall back to any available scenario
            scenario_ids = registry.list_scenarios()
            if not scenario_ids:
                pytest.skip("No scenarios available")
            scenario = registry.get_scenario_definition(scenario_ids[0])
        
        policy = make_bot_policy("tactical_fighter")
        seed_base = 1337
        runs = 3  # Small number for speed
        turn_limit = 20  # Short runs
        
        # First execution
        metrics1 = run_scenario_many(scenario, policy, runs, turn_limit, seed_base=seed_base)
        
        # Second execution with same seed_base
        metrics2 = run_scenario_many(scenario, policy, runs, turn_limit, seed_base=seed_base)
        
        # Key metrics must match exactly
        assert metrics1.runs == metrics2.runs
        assert metrics1.player_deaths == metrics2.player_deaths
        assert metrics1.total_player_attacks == metrics2.total_player_attacks
        assert metrics1.total_player_hits == metrics2.total_player_hits
        assert metrics1.total_monster_attacks == metrics2.total_monster_attacks
        assert metrics1.total_monster_hits == metrics2.total_monster_hits
        assert metrics1.total_bonus_attacks_triggered == metrics2.total_bonus_attacks_triggered
        assert metrics1.average_turns == metrics2.average_turns
    
    def test_different_seed_base_produces_different_results(self):
        """Different seed_base should produce different metrics (with high probability)."""
        from config.level_template_registry import get_scenario_registry
        from services.scenario_harness import run_scenario_many, make_bot_policy
        
        registry = get_scenario_registry()
        scenario = registry.get_scenario_definition("monster_skeleton_identity")
        if scenario is None:
            scenario_ids = registry.list_scenarios()
            if not scenario_ids:
                pytest.skip("No scenarios available")
            scenario = registry.get_scenario_definition(scenario_ids[0])
        
        policy = make_bot_policy("tactical_fighter")
        runs = 5
        turn_limit = 30
        
        # Run with two different seed bases
        metrics1 = run_scenario_many(scenario, policy, runs, turn_limit, seed_base=1337)
        metrics2 = run_scenario_many(scenario, policy, runs, turn_limit, seed_base=9999)
        
        # At least one metric should differ (with very high probability)
        # We check multiple metrics to reduce false positive rate
        all_same = (
            metrics1.player_deaths == metrics2.player_deaths
            and metrics1.total_player_hits == metrics2.total_player_hits
            and metrics1.total_monster_hits == metrics2.total_monster_hits
            and metrics1.average_turns == metrics2.average_turns
        )
        
        # It's technically possible but extremely unlikely for all to match
        # If this fails, it suggests the seeding isn't being applied
        assert not all_same, "Different seed bases should produce different results"
