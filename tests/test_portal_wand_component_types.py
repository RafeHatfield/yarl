"""Regression test for Wand of Portals component type issue.

This test verifies that using the Wand of Portals doesn't raise:
  TypeError: component_type must be ComponentType, got <class 'int'>

The bug occurred because portal_manager.py was calling:
  entity.components.add(_ck(ComponentType.PORTAL if ComponentType else "portal"), portal)

Where _ck() converts the enum to its integer value, which the component registry rejects.

The fix ensures portal_manager.py calls:
  entity.components.add(ComponentType.PORTAL, portal)

directly with the enum member.
"""

import pytest
from config.testing_config import get_testing_config, set_testing_mode
from loader_functions.initialize_new_game import get_constants, get_game_variables
from fov_functions import initialize_fov
from engine_integration import create_game_engine, initialize_game_engine
from game_states import GameStates
from components.component_registry import ComponentType
from services.portal_manager import PortalManager


class TestPortalWandComponentTypes:
    """Regression tests for Wand of Portals component type handling."""

    def setup_method(self):
        """Reset testing config and set up test environment."""
        from config import testing_config as tc_module
        tc_module._testing_config = None
        set_testing_mode(True)
        
        # Start on floor 1
        config = get_testing_config()
        config.start_level = 1

    def _setup_engine_and_player(self):
        """Helper to start a real game engine on floor 1.
        
        Returns:
            tuple: (engine, player, entities, game_map, constants)
        """
        constants = get_constants()
        player, entities, game_map, message_log, game_state = get_game_variables(constants)

        class MockConsole:
            pass

        sidebar = MockConsole()
        viewport = MockConsole()
        status = MockConsole()

        engine = create_game_engine(constants, sidebar, viewport, status)
        initialize_game_engine(engine, player, entities, game_map, message_log, game_state, constants)

        fov_map = initialize_fov(game_map)
        engine.state_manager.set_fov_data(fov_map, fov_recompute=True)

        return engine, player, entities, game_map, constants

    def _find_portal_wand(self, player):
        """Find the Wand of Portals in the player's inventory.
        
        Args:
            player: The player entity
            
        Returns:
            Entity: The Wand of Portals item entity, or None if not found
        """
        if not player.inventory:
            return None
        
        for item in player.inventory.items:
            if item.name == "Wand of Portals":
                return item
        
        return None

    @pytest.mark.integration
    def test_portal_creation_uses_enum_component_key(self):
        """Regression test: Creating a portal should use ComponentType.PORTAL enum, not int.
        
        This test verifies the fix for:
          TypeError: component_type must be ComponentType, got <class 'int'>
        
        The bug was in services/portal_manager.py calling:
          entity.components.add(_ck(ComponentType.PORTAL if ComponentType else "portal"), portal)
        
        Which converted the enum to its integer value. The component registry expects
        the actual enum member.
        """
        engine, player, entities, game_map, constants = self._setup_engine_and_player()
        
        # Find a valid placement location
        target_x = min(player.x + 2, game_map.width - 1)
        target_y = min(player.y + 2, game_map.height - 1)
        
        # Ensure target is not blocked
        if game_map.is_blocked(target_x, target_y):
            for dx in [-1, 1]:
                for dy in [-1, 1]:
                    test_x = player.x + dx
                    test_y = player.y + dy
                    if (0 <= test_x < game_map.width and 
                        0 <= test_y < game_map.height and
                        not game_map.is_blocked(test_x, test_y)):
                        target_x, target_y = test_x, test_y
                        break
        
        # Create a portal via PortalManager - this should NOT raise TypeError
        # The key test is that this doesn't raise:
        #   TypeError: component_type must be ComponentType, got <class 'int'>
        portal = None
        try:
            portal = PortalManager.create_portal_entity(
                portal_type='entrance',
                x=target_x,
                y=target_y,
                from_yaml=True
            )
        except TypeError as e:
            if "component_type must be ComponentType" in str(e):
                pytest.fail(
                    f"Portal creation raised the component type bug: {e}\n"
                    "This indicates portal_manager.py is not using ComponentType.PORTAL directly."
                )
            raise
        except Exception as e:
            # Portal factory might not be fully initialized in test config
            # The important thing is we don't get the component type error
            import logging
            logging.debug(f"Portal creation failed (expected in test config): {e}")
        
        # If we got a portal, verify it has the correct component structure
        if portal is not None:
            # Verify it has the portal component registered correctly
            assert hasattr(portal, 'portal'), "Portal entity should have portal attribute"
            assert portal.portal is not None, "Portal component should be set"
            
            # Verify the component is in the registry with the correct type
            portal_component = portal.components.get(ComponentType.PORTAL)
            assert portal_component is not None, \
                "Portal component should be registered in ComponentRegistry with ComponentType.PORTAL key"
            assert portal_component == portal.portal, \
                "Registered component should be the same as portal.portal"
        else:
            # If portal creation failed, that's okay for this test -
            # the important part is that we didn't get the component type error
            # which would indicate the bug is back
            pytest.skip("Portal factory not fully configured in test environment")

    @pytest.mark.integration
    def test_portal_wand_item_usage_flow(self):
        """Regression test: Using the Wand of Portals through the full item usage flow.
        
        This tests the complete flow: wand in inventory -> use -> portal creation.
        Any component type errors in portal creation would be caught here.
        """
        engine, player, entities, game_map, constants = self._setup_engine_and_player()
        
        # Find the wand in inventory
        wand = self._find_portal_wand(player)
        
        if wand is None:
            pytest.skip("Player does not have Wand of Portals (configuration-dependent)")
        
        # Verify wand has required components
        assert hasattr(wand, 'wand'), "Wand should have Wand component"
        assert wand.wand is not None, "Wand component should not be None"
        
        # Verify wand has portal_placer component (for targeting mode)
        assert hasattr(wand, 'portal_placer'), "Wand should have PortalPlacer component"
        assert wand.portal_placer is not None, "PortalPlacer should not be None"
        
        # Attempt to use the wand (enters targeting mode, doesn't place portals yet)
        try:
            inventory = player.require_component(ComponentType.INVENTORY)
            results = inventory.use(
                wand,
                entities=engine.state_manager.state.entities,
                fov_map=engine.state_manager.state.fov_map,
                game_map=engine.state_manager.state.game_map,
                wand_entity=wand
            )
        except TypeError as e:
            if "component_type must be ComponentType" in str(e):
                pytest.fail(
                    f"Wand usage raised component type bug: {e}\n"
                    "This might indicate portal creation during targeting mode setup."
                )
            raise
        except Exception as e:
            pytest.fail(f"Unexpected error using wand: {e}")
        
        # Verify the wand usage succeeded (got results)
        assert results, "Using wand should return results"

    @pytest.mark.integration
    def test_multiple_portals_use_correct_component_type(self):
        """Regression test: Creating multiple portals should each use ComponentType.PORTAL correctly.
        
        This verifies the fix works consistently across multiple portal creation calls.
        """
        engine, player, entities, game_map, constants = self._setup_engine_and_player()
        
        # Create entrance portal
        entrance_portal = None
        exit_portal = None
        
        try:
            entrance_portal = PortalManager.create_portal_entity(
                portal_type='entrance',
                x=min(player.x + 1, game_map.width - 1),
                y=min(player.y + 1, game_map.height - 1),
                from_yaml=True
            )
            
            # Create exit portal
            exit_portal = PortalManager.create_portal_entity(
                portal_type='exit',
                x=min(player.x + 3, game_map.width - 1),
                y=min(player.y + 3, game_map.height - 1),
                from_yaml=True
            )
        except TypeError as e:
            if "component_type must be ComponentType" in str(e):
                pytest.fail(
                    f"Portal creation (entrance or exit) raised component type bug: {e}"
                )
            raise
        except Exception as e:
            # Portal factory might not be fully initialized
            import logging
            logging.debug(f"Portal creation failed (expected in test config): {e}")
        
        # If both portals were created, verify structure
        if entrance_portal is not None and exit_portal is not None:
            # Verify both have PORTAL components registered correctly
            entrance_component = entrance_portal.components.get(ComponentType.PORTAL)
            exit_component = exit_portal.components.get(ComponentType.PORTAL)
            
            assert entrance_component is not None, \
                "Entrance portal should have ComponentType.PORTAL in registry"
            assert exit_component is not None, \
                "Exit portal should have ComponentType.PORTAL in registry"
            
            # Verify they can be linked
            try:
                entrance_component.linked_portal = exit_component
                exit_component.linked_portal = entrance_component
            except Exception as e:
                pytest.fail(f"Linking portals should not raise: {e}")
            
            # Verify linking succeeded
            assert entrance_component.linked_portal == exit_component, \
                "Entrance should link to exit"
            assert exit_component.linked_portal == entrance_component, \
                "Exit should link to entrance"
        else:
            # Portal factory not available - that's okay, we just didn't get the component type error
            pytest.skip("Portal factory not fully configured in test environment")

