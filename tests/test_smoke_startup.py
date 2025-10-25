"""
Smoke tests for critical import and startup paths.

These tests catch catastrophic failures like circular imports
that prevent the game from starting at all.
"""

import pytest


class TestImports:
    """Test that critical modules can be imported without errors."""
    
    def test_state_config_imports(self):
        """State config must import without circular import errors."""
        try:
            from state_management.state_config import StateManager, STATE_CONFIGURATIONS
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import state_config: {e}")
    
    def test_input_handlers_imports(self):
        """Input handlers must import successfully."""
        try:
            from input_handlers import handle_keys, handle_player_turn_keys
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import input_handlers: {e}")
    
    def test_turn_controller_imports(self):
        """Turn controller must import successfully."""
        try:
            from systems.turn_controller import TurnController, get_turn_controller
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import turn_controller: {e}")
    
    def test_game_actions_imports(self):
        """Game actions must import successfully."""
        try:
            from game_actions import ActionProcessor
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import game_actions: {e}")
    
    def test_engine_imports(self):
        """Engine module must import successfully."""
        try:
            import engine
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import engine: {e}")


class TestStateManagerInitialization:
    """Test that StateManager initializes correctly."""
    
    def test_state_configurations_populate_on_first_use(self):
        """STATE_CONFIGURATIONS should populate lazily."""
        from state_management.state_config import StateManager, STATE_CONFIGURATIONS
        from game_states import GameStates
        
        # Access a config - this should trigger initialization
        config = StateManager.get_config(GameStates.PLAYERS_TURN)
        
        # Now STATE_CONFIGURATIONS should be populated
        assert len(STATE_CONFIGURATIONS) > 0
        assert GameStates.PLAYERS_TURN in STATE_CONFIGURATIONS
    
    def test_all_game_states_have_configs(self):
        """All GameStates should have configurations after initialization."""
        from state_management.state_config import StateManager
        from game_states import GameStates
        
        # Trigger initialization
        StateManager.get_config(GameStates.PLAYERS_TURN)
        
        # Validate all states
        try:
            StateManager.validate_all_states()
        except ValueError as e:
            pytest.fail(f"Not all states have configurations: {e}")


class TestCircularImports:
    """Regression tests for circular import bugs."""
    
    def test_no_circular_import_state_config_input_handlers(self):
        """Prevent regression of circular import between state_config and input_handlers.
        
        Bug History:
        - Date: Oct 25, 2025
        - Error: ImportError: cannot import name 'handle_player_turn_keys' from partially initialized module
        - Cause: state_config imported handlers at module level
        - Fix: Lazy initialization in _initialize_state_configurations()
        """
        # This test passes if imports succeed
        try:
            # This order previously caused circular import
            from input_handlers import handle_keys
            from state_management.state_config import StateManager
            
            # If we got here, no circular import!
            assert True
        except ImportError as e:
            pytest.fail(f"Circular import detected: {e}")
    
    def test_engine_can_import_all_dependencies(self):
        """Engine must be able to import all its dependencies.
        
        This is the ultimate smoke test - if engine imports, game can start.
        """
        try:
            import engine
            # If this succeeds, all imports work
            assert True
        except Exception as e:
            pytest.fail(f"Engine failed to import (game won't start!): {e}")


class TestRegressionPreventionStartup:
    """Tests that prevent specific startup bugs from returning."""
    
    def test_game_actually_starts(self):
        """Game must be able to initialize without crashing.
        
        This is the most important test - does the game start?
        """
        try:
            # Import main engine components
            import engine
            from config.game_constants import get_constants
            
            # If we can get constants, core systems initialized
            constants = get_constants()
            assert constants is not None
            assert 'screen_width' in constants
            
        except Exception as e:
            pytest.fail(f"Game startup failed: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

