"""Unit test for Necromancer entity creation.

Verifies that the necromancer entity can be created with all config attributes.
"""

import pytest


def test_necromancer_entity_creation():
    """Necromancer should be created with all ability config attributes."""
    from config.factories import get_entity_factory
    
    # Create necromancer
    factory = get_entity_factory()
    necro = factory.create_monster('necromancer', 10, 10)
    
    assert necro is not None, "Necromancer should be created"
    assert necro.name == "Necromancer"
    
    # Check AI type
    from components.ai.necromancer_ai import NecromancerAI
    assert isinstance(necro.ai, NecromancerAI), f"AI should be NecromancerAI, got {type(necro.ai)}"
    
    # Check faction
    from components.faction import Faction
    assert necro.faction == Faction.CULTIST, f"Faction should be CULTIST, got {necro.faction}"
    
    # Check raise dead config attributes
    assert hasattr(necro, 'raise_dead_enabled'), "Should have raise_dead_enabled"
    assert necro.raise_dead_enabled is True
    
    assert hasattr(necro, 'raise_dead_range'), "Should have raise_dead_range"
    assert necro.raise_dead_range == 5
    
    assert hasattr(necro, 'raise_dead_cooldown_turns'), "Should have raise_dead_cooldown_turns"
    assert necro.raise_dead_cooldown_turns == 4
    
    # Check hang-back config attributes
    assert hasattr(necro, 'danger_radius_from_player'), "Should have danger_radius_from_player"
    assert necro.danger_radius_from_player == 2
    
    assert hasattr(necro, 'preferred_distance_min'), "Should have preferred_distance_min"
    assert necro.preferred_distance_min == 4
    
    assert hasattr(necro, 'preferred_distance_max'), "Should have preferred_distance_max"
    assert necro.preferred_distance_max == 7


def test_necromancer_ai_has_cooldown_tracking():
    """NecromancerAI should initialize with cooldown tracking."""
    from components.ai.necromancer_ai import NecromancerAI
    
    ai = NecromancerAI()
    
    assert hasattr(ai, 'raise_cooldown_remaining')
    assert ai.raise_cooldown_remaining == 0  # Starts ready

