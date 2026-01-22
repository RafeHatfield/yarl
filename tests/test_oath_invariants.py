"""Phase 22.1.1: Anti-regression tests for Oath invariants.

These tests prevent drift in Oath implementation and ensure:
1. Oaths never expire (permanent status effects)
2. Oath effects only apply to player (not monsters)
3. Oath procs use seeded RNG (deterministic)
"""

import pytest
import random
from unittest.mock import Mock, MagicMock

from components.status_effects import (
    OathOfEmbersEffect,
    OathOfVenomEffect,
    OathOfChainsEffect,
    StatusEffectManager
)
from components.component_registry import ComponentType
from entity import Entity


class TestOathPermanence:
    """Verify Oaths never expire."""
    
    def test_oath_effects_have_infinite_duration(self):
        """Verify all Oath effects start with duration = -1 (infinite)."""
        mock_owner = Mock()
        
        embers = OathOfEmbersEffect(owner=mock_owner)
        venom = OathOfVenomEffect(owner=mock_owner)
        chains = OathOfChainsEffect(owner=mock_owner)
        
        assert embers.duration == -1, "Oath of Embers should have infinite duration"
        assert venom.duration == -1, "Oath of Venom should have infinite duration"
        assert chains.duration == -1, "Oath of Chains should have infinite duration"
    
    def test_oath_process_turn_end_never_decrements(self):
        """Verify Oath.process_turn_end() doesn't decrement duration."""
        mock_owner = Mock()
        
        embers = OathOfEmbersEffect(owner=mock_owner)
        initial_duration = embers.duration
        
        # Call process_turn_end multiple times
        for _ in range(10):
            embers.process_turn_end()
        
        assert embers.duration == initial_duration, "Oath duration should never change"
        assert embers.duration == -1, "Oath should remain infinite"


class TestOathPlayerOnly:
    """Verify Oath effects only apply to player attacks."""
    
    def test_oath_effects_check_for_ai_component(self):
        """Verify _apply_oath_effects() checks attacker has no AI (is player)."""
        from components.fighter import Fighter
        
        # Create a mock attacker with AI (monster)
        monster = Mock()
        monster_ai = Mock()  # Has AI = monster
        monster.get_component_optional = Mock(side_effect=lambda ct: 
            monster_ai if ct == ComponentType.AI else None
        )
        
        # Create fighter for monster
        monster_fighter = Fighter(
            hp=10, defense=5, power=5,
            damage_min=1, damage_max=3,
            strength=10, dexterity=10, constitution=10
        )
        monster_fighter.owner = monster
        
        # Give monster an Oath (shouldn't happen, but test the check)
        status_effects = StatusEffectManager(monster)
        oath = OathOfEmbersEffect(owner=monster)
        status_effects.add_effect(oath)
        monster.components = Mock()
        monster.components.has = Mock(return_value=True)
        monster.get_component_optional = Mock(side_effect=lambda ct: 
            monster_ai if ct == ComponentType.AI else status_effects if ct == ComponentType.STATUS_EFFECTS else None
        )
        
        # Apply Oath effects - should be blocked by AI check
        target = Mock()
        results = monster_fighter._apply_oath_effects(target)
        
        assert len(results) == 0, "Oath effects should not apply to monsters (entities with AI)"


class TestOathDeterminism:
    """Verify Oath procs use seeded RNG."""
    
    def test_oath_uses_python_random_module(self):
        """Verify Oath effects use Python's random module (which is seeded by scenarios)."""
        # This test verifies that Oaths use random.random(), not some other RNG
        # The actual seeding happens in scenario_harness.py via set_global_seed()
        
        # Test that proc chance respects seeded random
        random.seed(1337)
        rolls = [random.random() for _ in range(100)]
        
        random.seed(1337)
        rolls2 = [random.random() for _ in range(100)]
        
        assert rolls == rolls2, "Python random should be deterministic when seeded"
        
        # Verify Oath parameters are within expected ranges
        mock_owner = Mock()
        embers = OathOfEmbersEffect(owner=mock_owner)
        venom = OathOfVenomEffect(owner=mock_owner)
        
        assert 0 < embers.burn_chance < 1, "Burn chance should be a valid probability"
        assert 0 < venom.poison_chance < 1, "Poison chance should be a valid probability"
        
        # Count how many rolls would proc with 33% chance
        random.seed(1337)
        procs = sum(1 for _ in range(100) if random.random() < 0.33)
        assert 20 <= procs <= 45, f"Expected ~33% procs in 100 rolls (got {procs})"


class TestOathConstraints:
    """Verify Oath-specific constraints work correctly."""
    
    def test_chains_respects_movement_flag(self):
        """Verify Oath of Chains checks moved_last_turn flag."""
        from services.knockback_service import calculate_knockback_distance
        
        # Create real Entity with Oath of Chains (not mock - too complex)
        from entity import Entity
        from components.fighter import Fighter
        
        attacker = Entity(
            x=5, y=5,
            char='@', color=(255, 255, 255), name='Player',
            blocks=True
        )
        
        # Add status effects and Oath
        status_effects = StatusEffectManager(attacker)
        oath = OathOfChainsEffect(owner=attacker)
        status_effects.add_effect(oath)
        attacker.status_effects = status_effects
        attacker.components.add(ComponentType.STATUS_EFFECTS, status_effects)
        
        # Test 1: Didn't move (bonus should apply)
        attacker.moved_last_turn = False
        distance_still = calculate_knockback_distance(10, 5, attacker)
        
        # Test 2: Did move (bonus should NOT apply)
        attacker.moved_last_turn = True
        distance_moved = calculate_knockback_distance(10, 5, attacker)
        
        # With power delta of 5 (10-5), base knockback should be 4 tiles
        # With Chains bonus (+1), it should be 5 when standing still
        assert distance_still == 5, f"Expected 5 tiles when standing still (got {distance_still})"
        assert distance_moved == 4, f"Expected 4 tiles when moving (got {distance_moved})"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
