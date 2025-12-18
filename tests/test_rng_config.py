"""Tests for RNG configuration and seed management.

Tests that:
1. set_global_seed correctly seeds the random module
2. get_current_seed returns the correct seed
3. generate_seed produces unique values
4. Seeded random produces deterministic sequences
"""

import random
import pytest

from engine.rng_config import (
    set_global_seed,
    get_current_seed,
    generate_seed,
    reset_rng_state,
    stable_scenario_seed,
)


class TestSetGlobalSeed:
    """Tests for set_global_seed function."""
    
    def setup_method(self):
        """Reset RNG state before each test."""
        reset_rng_state()
    
    def teardown_method(self):
        """Reset RNG state after each test."""
        reset_rng_state()
    
    def test_set_seed_updates_current_seed(self):
        """set_global_seed should update the stored seed."""
        set_global_seed(12345)
        assert get_current_seed() == 12345
    
    def test_set_seed_produces_deterministic_random(self):
        """Same seed should produce same random sequence."""
        set_global_seed(42)
        seq1 = [random.randint(0, 100) for _ in range(5)]
        
        set_global_seed(42)
        seq2 = [random.randint(0, 100) for _ in range(5)]
        
        assert seq1 == seq2
    
    def test_different_seeds_produce_different_sequences(self):
        """Different seeds should (almost certainly) produce different sequences."""
        set_global_seed(100)
        seq1 = [random.randint(0, 1000000) for _ in range(10)]
        
        set_global_seed(200)
        seq2 = [random.randint(0, 1000000) for _ in range(10)]
        
        assert seq1 != seq2


class TestGetCurrentSeed:
    """Tests for get_current_seed function."""
    
    def setup_method(self):
        """Reset RNG state before each test."""
        reset_rng_state()
    
    def teardown_method(self):
        """Reset RNG state after each test."""
        reset_rng_state()
    
    def test_returns_none_before_set(self):
        """get_current_seed should return None if seed not set."""
        assert get_current_seed() is None
    
    def test_returns_seed_after_set(self):
        """get_current_seed should return the seed after set_global_seed."""
        set_global_seed(99999)
        assert get_current_seed() == 99999


class TestGenerateSeed:
    """Tests for generate_seed function."""
    
    def test_generates_integer(self):
        """generate_seed should return an integer."""
        seed = generate_seed()
        assert isinstance(seed, int)
    
    def test_generates_positive_value(self):
        """generate_seed should return a positive value."""
        seed = generate_seed()
        assert seed >= 0
    
    def test_generates_different_values_over_time(self):
        """generate_seed should produce different values (time-based)."""
        import time
        seeds = set()
        for _ in range(3):
            seeds.add(generate_seed())
            time.sleep(0.001)  # Small delay to get different timestamps
        
        # Should have at least 2 unique seeds (could be 3)
        assert len(seeds) >= 2


class TestResetRngState:
    """Tests for reset_rng_state function."""
    
    def test_resets_current_seed(self):
        """reset_rng_state should clear the stored seed."""
        set_global_seed(12345)
        assert get_current_seed() == 12345
        
        reset_rng_state()
        assert get_current_seed() is None


class TestSoakHarnessIntegration:
    """Integration tests for RNG seeding in soak context."""
    
    def setup_method(self):
        """Reset RNG state before each test."""
        reset_rng_state()
    
    def teardown_method(self):
        """Reset RNG state after each test."""
        reset_rng_state()
    
    def test_sequential_seeds_from_base(self):
        """Soak harness pattern: base_seed + run_number should work correctly."""
        base_seed = 10000
        
        # Simulate what soak harness does
        for run_num in range(1, 4):
            run_seed = base_seed + (run_num - 1)
            set_global_seed(run_seed)
            
            assert get_current_seed() == base_seed + (run_num - 1)
    
    def test_reproducible_sequence_with_base_seed(self):
        """Two soak sessions with same base_seed should produce identical run sequences."""
        base_seed = 42
        
        # First "session"
        set_global_seed(base_seed)
        session1_values = [random.randint(0, 100) for _ in range(3)]
        
        # Second "session" with same seed
        set_global_seed(base_seed)
        session2_values = [random.randint(0, 100) for _ in range(3)]
        
        assert session1_values == session2_values


class TestStableScenarioSeed:
    """Tests for stable_scenario_seed function (balance suite determinism)."""
    
    def test_returns_integer(self):
        """stable_scenario_seed should return an integer."""
        seed = stable_scenario_seed("depth3_orc_brutal", 0, 1337)
        assert isinstance(seed, int)
    
    def test_returns_positive_value(self):
        """stable_scenario_seed should return a non-negative value."""
        seed = stable_scenario_seed("depth3_orc_brutal", 0, 1337)
        assert seed >= 0
    
    def test_same_inputs_produce_same_seed(self):
        """Same inputs should always produce the same seed (deterministic)."""
        seed1 = stable_scenario_seed("depth3_orc_brutal", 5, 1337)
        seed2 = stable_scenario_seed("depth3_orc_brutal", 5, 1337)
        assert seed1 == seed2
    
    def test_different_run_idx_produces_different_seed(self):
        """Different run indices should produce different seeds."""
        seeds = [stable_scenario_seed("depth3_orc_brutal", i, 1337) for i in range(10)]
        # All should be unique
        assert len(set(seeds)) == 10
    
    def test_different_scenario_produces_different_seed(self):
        """Different scenarios should produce different seeds."""
        seed1 = stable_scenario_seed("depth3_orc_brutal", 0, 1337)
        seed2 = stable_scenario_seed("depth5_zombie", 0, 1337)
        assert seed1 != seed2
    
    def test_different_seed_base_produces_different_seed(self):
        """Different seed_base should produce different seeds."""
        seed1 = stable_scenario_seed("depth3_orc_brutal", 0, 1337)
        seed2 = stable_scenario_seed("depth3_orc_brutal", 0, 42)
        assert seed1 != seed2
    
    def test_stable_across_invocations(self):
        """Seed should be stable across multiple invocations (hash-based)."""
        # This ensures we're not using time or any other varying input
        expected = stable_scenario_seed("test_scenario", 42, 12345)
        for _ in range(100):
            actual = stable_scenario_seed("test_scenario", 42, 12345)
            assert actual == expected
    
    def test_produces_reproducible_random_sequence(self):
        """Using stable_scenario_seed should produce reproducible random sequences."""
        seed = stable_scenario_seed("my_scenario", 0, 1337)
        
        set_global_seed(seed)
        seq1 = [random.randint(0, 1000) for _ in range(20)]
        
        set_global_seed(seed)
        seq2 = [random.randint(0, 1000) for _ in range(20)]
        
        assert seq1 == seq2
    
    def teardown_method(self):
        """Reset RNG state after each test."""
        reset_rng_state()

