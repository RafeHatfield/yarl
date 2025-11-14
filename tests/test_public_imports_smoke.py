"""Smoke tests for critical public module imports.

This test suite catches catastrophic failures like:
- NameError and circular imports that prevent game startup
- Missing critical modules or components
- Broken module hierarchy

Tests iterate through core public modules and verify they can be imported
without raising exceptions. Failures here indicate the game cannot start.
"""

import pytest
import importlib
from typing import List


# List of critical public modules that MUST import successfully
CRITICAL_MODULES = [
    # Engine and integration
    'engine_integration',
    'engine',
    'engine.game_state_manager',
    'engine.game_engine',
    
    # Game flow
    'game_actions',
    'game_states',
    'game_messages',
    'death_functions',
    'input_handlers',
    
    # Core entities and components
    'entity',
    'components',
    'components.fighter',
    'components.inventory',
    'components.equipment',
    'components.item',
    'components.wand',
    'components.portal',
    'components.boss',
    'components.component_registry',
    
    # Services
    'services.portal_manager',
    'services.mural_manager',
    
    # Configuration
    'config',
    'config.game_constants',
    'config.testing_config',
    'config.entity_factory',
    'config.factories',
    
    # Map and world generation
    'map_objects.game_map',
    'map_objects.room_generators',
    
    # Rendering
    'render_functions',
    'fov_functions',
    
    # Game initialization
    'loader_functions.initialize_new_game',
    'loader_functions.data_loaders',
    
    # State management
    'state_management.state_config',
    
    # Turn management
    'systems.turn_controller',
]


class TestPublicImports:
    """Test that all critical public modules can be imported."""
    
    @pytest.mark.parametrize('module_name', CRITICAL_MODULES)
    def test_critical_module_imports(self, module_name: str):
        """Test that a critical module can be imported without exception.
        
        Args:
            module_name: Name of the module to import
            
        Raises:
            ImportError: If module cannot be imported
            ModuleNotFoundError: If module is not found
        """
        try:
            module = importlib.import_module(module_name)
            assert module is not None, f"Module {module_name} imported but is None"
        except (ImportError, ModuleNotFoundError, AttributeError) as e:
            pytest.fail(f"Failed to import critical module '{module_name}': {e}")
        except Exception as e:
            pytest.fail(f"Unexpected exception importing '{module_name}': {type(e).__name__}: {e}")


class TestEntrypeointModuleIntegration:
    """Test that entrypoint modules work together without circular imports."""
    
    def test_engine_integration_imports_cleanly(self):
        """engine_integration must import without circular import errors."""
        import engine_integration
        assert hasattr(engine_integration, '_manual_input_system_update'), \
            "engine_integration missing expected function"
    
    def test_game_actions_imports_cleanly(self):
        """game_actions must import successfully."""
        import game_actions
        assert hasattr(game_actions, 'ActionProcessor'), \
            "game_actions missing ActionProcessor"
    
    def test_death_functions_imports_cleanly(self):
        """death_functions must import without issues."""
        import death_functions
        assert hasattr(death_functions, 'kill_monster'), \
            "death_functions missing kill_monster function"
        assert hasattr(death_functions, 'kill_player'), \
            "death_functions missing kill_player function"
    
    def test_portal_manager_imports_cleanly(self):
        """PortalManager service must import successfully."""
        from services.portal_manager import PortalManager
        assert PortalManager is not None
        assert hasattr(PortalManager, 'create_portal_entity'), \
            "PortalManager missing create_portal_entity method"
    
    def test_entity_imports_cleanly(self):
        """Entity class must import successfully."""
        from entity import Entity
        assert Entity is not None
        assert hasattr(Entity, 'create_player'), \
            "Entity missing create_player class method"


class TestCoreComponentsAvailable:
    """Test that core game components are available."""
    
    def test_fighter_component_available(self):
        """Fighter component must be available."""
        from components.fighter import Fighter
        assert Fighter is not None
    
    def test_inventory_component_available(self):
        """Inventory component must be available."""
        from components.inventory import Inventory
        assert Inventory is not None
    
    def test_equipment_component_available(self):
        """Equipment component must be available."""
        from components.equipment import Equipment
        assert Equipment is not None
    
    def test_item_component_available(self):
        """Item component must be available."""
        from components.item import Item
        assert Item is not None
    
    def test_wand_component_available(self):
        """Wand component must be available."""
        from components.wand import Wand
        assert Wand is not None
    
    def test_portal_component_available(self):
        """Portal component must be available."""
        from components.portal import Portal
        assert Portal is not None


class TestConfigurationAvailable:
    """Test that configuration systems are available."""
    
    def test_game_constants_available(self):
        """Game constants must be retrievable."""
        from config.game_constants import get_constants
        constants = get_constants()
        assert constants is not None
        assert 'screen_width' in constants
    
    def test_testing_config_available(self):
        """Testing configuration must be available."""
        from config.testing_config import get_testing_config, set_testing_mode
        assert callable(get_testing_config)
        assert callable(set_testing_mode)
    
    def test_entity_factory_available(self):
        """Entity factory must be available."""
        from config.factories import EntityFactory
        assert EntityFactory is not None


class TestGameStateManagement:
    """Test that game state management is available."""
    
    def test_game_states_enum_available(self):
        """GameStates enum must be available."""
        from game_states import GameStates
        assert GameStates is not None
        # Check for common states
        assert hasattr(GameStates, 'PLAYERS_TURN')
    
    def test_game_state_manager_available(self):
        """GameStateManager must be available."""
        from engine.game_state_manager import GameStateManager, GameState
        assert GameStateManager is not None
        assert GameState is not None
    
    def test_state_config_available(self):
        """State configuration must be available."""
        from state_management.state_config import StateManager
        assert StateManager is not None


class TestNoCircularImports:
    """Regression tests to prevent circular import bugs."""
    
    def test_no_circular_import_state_config_input_handlers(self):
        """Prevent circular import between state_config and input_handlers.
        
        This is a known issue that was fixed. This test ensures it doesn't regress.
        """
        try:
            # This order previously caused circular import
            from input_handlers import handle_keys
            from state_management.state_config import StateManager
            assert True  # If we get here, no circular import
        except ImportError as e:
            pytest.fail(f"Circular import detected: {e}")
    
    def test_no_circular_import_engine_integration_game_actions(self):
        """Prevent circular import between engine_integration and game_actions."""
        try:
            import engine_integration
            import game_actions
            assert True
        except ImportError as e:
            pytest.fail(f"Circular import detected: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


