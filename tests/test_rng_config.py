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

