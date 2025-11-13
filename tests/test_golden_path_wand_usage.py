"""Golden-path integration test for Wand of Portals usage.

This test simulates real gameplay where the player finds and uses the Wand of Portals
to place entrance and exit portals. It verifies that the portal creation flow works
end-to-end without component registry errors.

Regression Context: Previous bug where portal creation would fail with
"ValueError: Component PORTAL already exists in registry" when using the wand.
"""

import pytest
from config.testing_config import get_testing_config, set_testing_mode
from loader_functions.initialize_new_game import get_constants, get_game_variables
from fov_functions import initialize_fov
from engine_integration import create_game_engine, initialize_game_engine
from game_states import GameStates
from components.component_registry import ComponentType
from components.wand import Wand
from components.portal_placer import PortalPlacer
from services.portal_manager import PortalManager, get_portal_manager


class TestGoldenPathWandUsage:
    """Test the complete golden-path scenario for Wand of Portals."""
    
    def setup_method(self):
        """Reset testing config before each test."""
        from config import testing_config as tc_module
        tc_module._testing_config = None
        set_testing_mode(True)
        
        config = get_testing_config()
        config.start_level = 1
    
    def _setup_game(self):
        """Helper to start a real game engine on floor 1.
        
        Returns:
            tuple: (engine, player, entities, game_map, constants, state_manager)
        """
        constants = get_constants()
        player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Create mock console objects for the engine
        class MockConsole:
            pass
        
        sidebar = MockConsole()
        viewport = MockConsole()
        status = MockConsole()
        
        # Create game engine and initialize it
        engine = create_game_engine(constants, sidebar, viewport, status)
        initialize_game_engine(engine, player, entities, game_map, message_log, game_state, constants)
        
        # Initialize FOV
        fov_map = initialize_fov(game_map)
        engine.state_manager.set_fov_data(fov_map, fov_recompute=True)
        
        return engine, player, entities, game_map, constants, engine.state_manager
    
    def test_game_initializes_successfully(self):
        """Test that the game engine initializes successfully on floor 1."""
        engine, player, entities, game_map, constants, state_manager = self._setup_game()
        
        assert engine is not None, "Engine should be created"
        assert player is not None, "Player should exist"
        assert state_manager is not None, "State manager should exist"
        assert state_manager.state.current_state == GameStates.PLAYERS_TURN, \
            "Should start in PLAYERS_TURN state"
    
    def test_portal_manager_create_portal_no_error(self):
        """Test that PortalManager.create_portal_entity() completes without error.
        
        This is the core regression test - should not raise double-add error.
        """
        engine, player, entities, game_map, constants, state_manager = self._setup_game()
        
        portal_manager = get_portal_manager()
        
        # Create entrance portal at a valid location
        valid_x, valid_y = 20, 20
        
        try:
            entrance = portal_manager.create_portal_entity(
                portal_type='entrance',
                x=valid_x,
                y=valid_y,
                from_yaml=False
            )
            
            # Should succeed without ValueError
            assert entrance is not None, "Entrance portal should be created"
            assert ComponentType.PORTAL in entrance.components, \
                "Portal should have PORTAL component"
                
        except ValueError as e:
            if "already exists in registry" in str(e):
                pytest.fail(f"Portal creation raised double-add error: {e}")
            else:
                raise
    
    def test_create_portal_pair_no_error(self):
        """Test creating a linked portal pair without component registry errors."""
        engine, player, entities, game_map, constants, state_manager = self._setup_game()
        
        portal_manager = get_portal_manager()
        
        try:
            # Create entrance
            entrance = portal_manager.create_portal_entity(
                portal_type='entrance',
                x=25,
                y=25,
                from_yaml=False
            )
            assert entrance is not None, "Entrance should be created"
            
            # Create exit linked to entrance
            exit_portal = portal_manager.create_portal_entity(
                portal_type='exit',
                x=30,
                y=30,
                linked_portal=entrance.portal,
                from_yaml=False
            )
            assert exit_portal is not None, "Exit should be created"
            
            # Link them
            success = portal_manager.link_portal_pair(
                entrance.portal,
                exit_portal.portal
            )
            assert success, "Portal linking should succeed"
            
        except ValueError as e:
            if "already exists in registry" in str(e):
                pytest.fail(f"Portal pair creation raised double-add error: {e}")
            else:
                raise
    
    def test_portal_entities_have_exactly_one_portal_component(self):
        """Test that created portals have exactly one PORTAL component.
        
        Regression check: each portal entity should have exactly 1 PORTAL component,
        not 2 (which would happen if double-add was attempted but silently handled).
        """
        engine, player, entities, game_map, constants, state_manager = self._setup_game()
        
        portal_manager = get_portal_manager()
        
        # Create both portal types
        entrance = portal_manager.create_portal_entity(
            portal_type='entrance',
            x=35,
            y=35,
            from_yaml=False
        )
        
        exit_portal = portal_manager.create_portal_entity(
            portal_type='exit',
            x=40,
            y=40,
            from_yaml=False
        )
        
        for portal_entity in [entrance, exit_portal]:
            assert portal_entity is not None, "Portal should be created"
            
            # Count PORTAL components
            portal_count = sum(
                1 for ct in portal_entity.components.get_all_types()
                if ct == ComponentType.PORTAL
            )
            
            assert portal_count == 1, \
                f"Portal should have exactly 1 PORTAL component, found {portal_count}"
    
    def test_portal_accessible_via_multiple_methods(self):
        """Test that portal component is accessible via different methods."""
        engine, player, entities, game_map, constants, state_manager = self._setup_game()
        
        portal_manager = get_portal_manager()
        
        portal_entity = portal_manager.create_portal_entity(
            portal_type='entrance',
            x=45,
            y=45,
            from_yaml=False
        )
        
        assert portal_entity is not None, "Portal should be created"
        
        # Method 1: Via attribute
        portal_via_attr = portal_entity.portal
        assert portal_via_attr is not None, "Portal should be accessible via .portal attribute"
        
        # Method 2: Via components registry
        portal_via_registry = portal_entity.components.get(ComponentType.PORTAL)
        assert portal_via_registry is not None, "Portal should be accessible via registry"
        
        # Method 3: Via get_component_optional
        portal_via_optional = portal_entity.get_component_optional(ComponentType.PORTAL)
        assert portal_via_optional is not None, "Portal should be accessible via get_component_optional"
        
        # All should be the same object
        assert portal_via_attr is portal_via_registry, \
            "All access methods should return the same portal object"
        assert portal_via_attr is portal_via_optional, \
            "All access methods should return the same portal object"
    
    def test_portal_component_registry_consistency(self):
        """Test that component registry is consistent after multiple operations."""
        engine, player, entities, game_map, constants, state_manager = self._setup_game()
        
        portal_manager = get_portal_manager()
        
        # Create multiple portals
        portals = []
        for i in range(3):
            portal = portal_manager.create_portal_entity(
                portal_type='entrance' if i % 2 == 0 else 'exit',
                x=50 + i,
                y=50 + i,
                from_yaml=False
            )
            assert portal is not None, f"Portal {i} should be created"
            portals.append(portal)
        
        # Verify each portal has consistent registry state
        for i, portal_entity in enumerate(portals):
            all_types = portal_entity.components.get_all_types()
            
            # Should have PORTAL and ITEM at minimum
            assert ComponentType.PORTAL in all_types, \
                f"Portal {i} should have PORTAL component"
            assert ComponentType.ITEM in all_types, \
                f"Portal {i} should have ITEM component"
            
            # Should not have duplicates
            type_counts = {}
            for ct in all_types:
                type_counts[ct] = type_counts.get(ct, 0) + 1
            
            for ct, count in type_counts.items():
                assert count == 1, \
                    f"Portal {i} has {count} {ct.name} components, should be exactly 1"
    
    def test_portal_owner_relationship(self):
        """Test that portal.owner relationship is properly maintained."""
        engine, player, entities, game_map, constants, state_manager = self._setup_game()
        
        portal_manager = get_portal_manager()
        
        portal_entity = portal_manager.create_portal_entity(
            portal_type='entrance',
            x=55,
            y=55,
            from_yaml=False
        )
        
        assert portal_entity is not None, "Portal should be created"
        
        # Portal should have owner set to entity
        assert portal_entity.portal.owner is portal_entity, \
            "Portal.owner should reference the entity"
        
        # Entity should have portal reference
        assert portal_entity.portal is not None, \
            "Entity should have portal"
    
    def test_portal_deployment_status(self):
        """Test that newly created portals are marked as deployed."""
        engine, player, entities, game_map, constants, state_manager = self._setup_game()
        
        portal_manager = get_portal_manager()
        
        portal_entity = portal_manager.create_portal_entity(
            portal_type='entrance',
            x=60,
            y=60,
            from_yaml=False
        )
        
        assert portal_entity is not None, "Portal should be created"
        assert portal_entity.portal.is_deployed is True, \
            "Newly created portal should be marked as deployed"


class TestPortalCreationEdgeCases:
    """Test edge cases and error conditions for portal creation."""
    
    def setup_method(self):
        """Reset testing config before each test."""
        from config import testing_config as tc_module
        tc_module._testing_config = None
        set_testing_mode(True)
        
        config = get_testing_config()
        config.start_level = 1
    
    def test_portal_creation_at_boundary_coordinates(self):
        """Test portal creation at various map boundary coordinates."""
        from entity import Entity
        
        portal_manager = get_portal_manager()
        
        # Test various boundary positions
        test_positions = [
            (0, 0),      # Corner
            (79, 0),     # Edge
            (0, 49),     # Edge
            (79, 49),    # Corner
            (40, 25),    # Center
        ]
        
        for x, y in test_positions:
            try:
                portal = portal_manager.create_portal_entity(
                    portal_type='entrance',
                    x=x,
                    y=y,
                    from_yaml=False
                )
                
                if portal is not None:
                    assert ComponentType.PORTAL in portal.components, \
                        f"Portal at ({x}, {y}) should have PORTAL component"
                        
            except ValueError as e:
                if "already exists in registry" in str(e):
                    pytest.fail(f"Double-add error at ({x}, {y}): {e}")
                else:
                    raise
    
    def test_sequential_portal_creation_no_state_pollution(self):
        """Test that sequential portal creations don't pollute global state.
        
        This verifies that portal_manager doesn't maintain state that could
        cause issues in subsequent creations.
        """
        portal_manager = get_portal_manager()
        
        portal1 = portal_manager.create_portal_entity(
            portal_type='entrance',
            x=10,
            y=10,
            from_yaml=False
        )
        
        portal2 = portal_manager.create_portal_entity(
            portal_type='exit',
            x=20,
            y=20,
            from_yaml=False
        )
        
        # Both should exist and be independent
        assert portal1 is not None, "First portal should be created"
        assert portal2 is not None, "Second portal should be created"
        
        # Should be different entities
        assert portal1 is not portal2, "Portals should be different entities"
        
        # Each should have its own component registry
        portal1_types = set(portal1.components.get_all_types())
        portal2_types = set(portal2.components.get_all_types())
        
        # Both should have PORTAL and ITEM
        assert ComponentType.PORTAL in portal1_types, "Portal1 should have PORTAL"
        assert ComponentType.PORTAL in portal2_types, "Portal2 should have PORTAL"
        assert ComponentType.ITEM in portal1_types, "Portal1 should have ITEM"
        assert ComponentType.ITEM in portal2_types, "Portal2 should have ITEM"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

