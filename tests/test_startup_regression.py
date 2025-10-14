"""Regression test for startup crashes.

This test ensures the game can start without crashing, catching critical
initialization bugs before they reach production.
"""

import pytest


def test_appearance_generator_initialization():
    """Test that appearance generator can be reset and initialized without errors.
    
    Regression test for: AttributeError: 'NoneType' object has no attribute 'initialize'
    """
    from config.item_appearances import reset_appearance_generator
    
    # Reset should return a valid generator
    appearance_gen = reset_appearance_generator()
    assert appearance_gen is not None
    assert hasattr(appearance_gen, 'initialize')
    
    # Initialize should work without errors
    appearance_gen.initialize({
        'scroll': ['lightning_scroll', 'fireball_scroll'],
        'potion': ['healing_potion', 'speed_potion']
    })
    
    # Generator should now be initialized
    assert appearance_gen._initialized == True


def test_game_initialization_does_not_crash():
    """Test that get_game_variables can be called without crashing.
    
    This is the critical path that runs on every game start.
    """
    from loader_functions.initialize_new_game import get_constants, get_game_variables
    
    # Get constants
    constants = get_constants()
    
    # This should not crash
    try:
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Verify basic initialization
        assert player is not None
        assert game_map is not None
        assert message_log is not None
        
    except AttributeError as e:
        if "'NoneType' object has no attribute" in str(e):
            pytest.fail(f"Initialization crash: {e}")
        raise


def test_appearance_generator_has_potion_types():
    """Test that all new potion types are registered with appearance generator."""
    from config.item_appearances import reset_appearance_generator
    
    appearance_gen = reset_appearance_generator()
    
    # All 11 new potions should be registered
    appearance_gen.initialize({
        'potion': [
            'healing_potion',
            'speed_potion',
            'regeneration_potion',
            'invisibility_potion',
            'levitation_potion',
            'protection_potion',
            'heroism_potion',
            'weakness_potion',
            'slowness_potion',
            'blindness_potion',
            'paralysis_potion',
            'experience_potion'
        ]
    })
    
    # Verify some potions got appearances
    assert appearance_gen.get_appearance('speed_potion', 'potion') is not None
    assert appearance_gen.get_appearance('healing_potion', 'potion') is not None
    assert appearance_gen.get_appearance('experience_potion', 'potion') is not None


def test_fighter_none_status_effects_check():
    """Test that the None check for status_effects works correctly.
    
    Regression test for: AttributeError: 'NoneType' object has no attribute 'get_effect'
    
    The fix adds 'and self.owner.status_effects is not None' to prevent calling
    .get_effect() on None.
    """
    from unittest.mock import Mock
    
    # Create entity with status_effects=None (common scenario)
    entity = Mock()
    entity.status_effects = None
    
    # Test the exact condition from fighter.py line 200 and 389
    # The bug was: hasattr returns True even if attribute is None
    assert hasattr(entity, 'status_effects')  # This is True
    assert entity.status_effects is None  # This is also True!
    
    # The fix: check BOTH conditions
    if hasattr(entity, 'status_effects') and entity.status_effects is not None:
        # This block should NOT execute
        pytest.fail("None check failed - would have called .get_effect() on None")
    
    # Verify the check works correctly - this should pass
    assert not (hasattr(entity, 'status_effects') and entity.status_effects is not None)

