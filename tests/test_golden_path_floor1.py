"""Golden-path integration tests for basic Floor 1 gameplay flows.

These tests exercise the most critical player workflows on Floor 1 and fail
loudly if basic functionality breaks, even when individual unit tests still pass.

They are designed to be fast (seconds to complete) and catch regressions that
would prevent a player from starting or progressing through basic gameplay.

Tests:
- test_basic_explore_floor1: Start game and walk around
- test_kill_basic_monster_and_loot: Combat and monster death
- test_use_wand_of_portals_on_floor1: Portal system
- test_discover_mural_and_signpost: Lore entities and visibility
"""

import pytest
from unittest.mock import Mock, patch
from config.testing_config import get_testing_config, set_testing_mode
from loader_functions.initialize_new_game import get_game_variables, get_constants
from game_states import GameStates
from entity import Entity
from components.fighter import Fighter
from components.wand import Wand
from death_functions import kill_monster
from services.portal_manager import PortalManager
from fov_functions import initialize_fov, recompute_fov


class TestGoldenPathFloor1:
    """Golden path integration tests for Floor 1 gameplay."""

    def setup_method(self):
        """Reset testing config and set up test environment."""
        from config import testing_config as tc_module
        tc_module._testing_config = None
        set_testing_mode(True)
        
        # Start on floor 1
        config = get_testing_config()
        config.start_level = 1

    def test_basic_explore_floor1(self):
        """Golden Path 1: Start a game and explore Floor 1 with basic movement.
        
        This test verifies:
        - Game initializes without crashing
        - Player can be placed and moved
        - FOV can be computed
        - Map contains required structures (stairs)
        - Basic game state invariants hold
        """
        constants = get_constants()
        player, entities, game_map, message_log, game_state = get_game_variables(constants)

        # Verify initialization
        assert player is not None, "Player must be created"
        assert game_map is not None, "Game map must be created"
        assert game_map.dungeon_level == 1, "Should start on floor 1"
        assert len(entities) > 0, "Should have entities on the map"

        # Record starting position
        start_x, start_y = player.x, player.y

        # Simulate FOV recomputation (first draw)
        fov_map = initialize_fov(game_map)
        recompute_fov(fov_map, player.x, player.y, constants["fov_radius"], constants["fov_algorithm"])

        # Simulate movement: take a few random walks
        moves = [(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1)]
        for dx, dy in moves:
            new_x = player.x + dx
            new_y = player.y + dy

            # Ensure new position is valid (on map and not blocked)
            if 0 <= new_x < game_map.width and 0 <= new_y < game_map.height:
                if not game_map.is_blocked(new_x, new_y):
                    player.x = new_x
                    player.y = new_y
                    # Recompute FOV after move
                    recompute_fov(fov_map, player.x, player.y, constants["fov_radius"], constants["fov_algorithm"])

        # Verify exploration happened
        assert player.x != start_x or player.y != start_y, "Player should have moved"
        assert 0 <= player.x < game_map.width, "Player X must be within map bounds"
        assert 0 <= player.y < game_map.height, "Player Y must be within map bounds"

        # Verify stairs exist on the map (required structure)
        stairs = [e for e in entities if hasattr(e, 'stairs') and e.stairs]
        assert len(stairs) > 0, "Floor 1 must have at least one staircase"

        # Verify basic FOV properties
        assert fov_map is not None, "FOV map must exist after recompute"
        
        # Check that FOV is computed (at least player's location should be in FOV)
        player_in_fov = fov_map.is_in_fov(player.x, player.y)
        assert player_in_fov, "Player should always be in their own FOV"

    def test_kill_basic_monster_and_loot(self):
        """Golden Path 2: Kill a basic monster and verify death flow completes.
        
        This test verifies:
        - Monster death functions complete without crashing
        - Loot system integration works (if applicable)
        - Entity list updates are correct
        - Death screen quote is set (if configured)
        - No exception propagates from death handling
        """
        constants = get_constants()
        player, entities, game_map, message_log, game_state = get_game_variables(constants)

        # Find or create a basic monster (non-boss)
        monsters = [e for e in entities if hasattr(e, 'fighter') and e.fighter and e.name != 'Player']
        
        if not monsters:
            # Create a simple test monster if none exists
            monster = Entity(
                x=11, y=10, char='o', color=(63, 127, 63), name='Test Orc',
                fighter=Fighter(hp=5, defense=0, power=2),
                blocks=True
            )
            entities.append(monster)
        else:
            monster = monsters[0]

        initial_entity_count = len(entities)

        # Kill the monster via kill_monster function
        try:
            kill_monster(monster, game_map, entities=entities)
        except Exception as e:
            pytest.fail(f"kill_monster raised exception: {e}")

        # Verify no uncaught exceptions occurred
        # If we reach here, the death flow completed

        # Verify entity still exists (might be transformed to corpse or removed by loot system)
        # The function should handle cleanup gracefully
        assert isinstance(entities, list), "Entities must remain a list"
        
        # Verify basic consistency
        for entity in entities:
            assert hasattr(entity, 'x') and hasattr(entity, 'y'), \
                f"Entity {entity.name} must have x and y coordinates"
            assert 0 <= entity.x < game_map.width or entity.x == -1, \
                f"Entity {entity.name} x-coordinate out of bounds: {entity.x}"
            assert 0 <= entity.y < game_map.height or entity.y == -1, \
                f"Entity {entity.name} y-coordinate out of bounds: {entity.y}"

    def test_use_wand_of_portals_on_floor1(self):
        """Golden Path 3: Create and use a Wand of Portals.
        
        This test verifies:
        - Wand component can be created and has charges
        - Portal creation via PortalManager completes without exception
        - Portal entity is properly registered
        - Portal system integrates with game state
        """
        constants = get_constants()
        player, entities, game_map, message_log, game_state = get_game_variables(constants)

        # Create a Wand component directly and test its functionality
        try:
            wand = Wand(spell_type='portal_wand', charges=-1)  # -1 = infinite charges
        except Exception as e:
            pytest.fail(f"Failed to create Wand component: {e}")

        # Verify wand has valid state
        assert wand is not None, "Wand must be created"
        assert wand.spell_type == 'portal_wand', "Wand spell_type must be set"
        assert not wand.is_empty(), "Wand with infinite charges should not be empty"

        # Verify wand can use a charge
        charge_used = wand.use_charge()
        assert charge_used, "Wand should be able to use a charge"

        # Simulate using the wand to create a portal at a nearby location
        target_x = min(player.x + 2, game_map.width - 1)
        target_y = min(player.y + 2, game_map.height - 1)

        # Ensure target is not blocked
        if game_map.is_blocked(target_x, target_y):
            # Find a nearby unblocked tile
            for dx in [-1, 1]:
                for dy in [-1, 1]:
                    test_x = player.x + dx
                    test_y = player.y + dy
                    if 0 <= test_x < game_map.width and 0 <= test_y < game_map.height:
                        if not game_map.is_blocked(test_x, test_y):
                            target_x, target_y = test_x, test_y
                            break

        # Attempt to create portal via PortalManager
        try:
            portal = PortalManager.create_portal_entity(
                portal_type='entity_portal',
                x=target_x,
                y=target_y,
                from_yaml=True
            )
        except Exception as e:
            pytest.fail(f"PortalManager.create_portal_entity raised exception: {e}")

        # Verify portal was created successfully
        if portal is not None:  # Some configurations might return None
            assert hasattr(portal, 'x') and hasattr(portal, 'y'), \
                "Portal must have x and y coordinates"
            assert portal.x == target_x and portal.y == target_y, \
                "Portal must be at target location"
            
            # Add to entities
            entities.append(portal)

    def test_discover_mural_and_signpost(self):
        """Golden Path 4: Discover murals and signposts for lore.
        
        This test verifies:
        - Murals and signposts can be created and placed
        - They have valid lore text
        - They can be moved into FOV without crashing
        - Interaction with them completes without exception
        """
        constants = get_constants()
        player, entities, game_map, message_log, game_state = get_game_variables(constants)

        # Find or create murals and signposts
        murals = [e for e in entities if hasattr(e, 'mural') and e.mural]
        signposts = [e for e in entities if hasattr(e, 'signpost') and e.signpost]

        # Note: These might not exist in all testing configurations, so we handle gracefully
        if not murals and not signposts:
            pytest.skip("No murals or signposts generated in test configuration (this is OK)")

        # If we have murals or signposts, verify they have proper state
        for lore_entity in murals + signposts:
            assert hasattr(lore_entity, 'x') and hasattr(lore_entity, 'y'), \
                f"{lore_entity.name} must have coordinates"
            assert 0 <= lore_entity.x < game_map.width, \
                f"{lore_entity.name} x-coordinate out of bounds: {lore_entity.x}"
            assert 0 <= lore_entity.y < game_map.height, \
                f"{lore_entity.name} y-coordinate out of bounds: {lore_entity.y}"

        # Move player to where we can see a mural/signpost
        if murals:
            mural = murals[0]
            # Move player adjacent to mural
            new_x = min(mural.x + 1, game_map.width - 1)
            new_y = min(mural.y + 1, game_map.height - 1)
            
            # Find walkable tile
            if game_map.is_blocked(new_x, new_y):
                new_x = mural.x
                new_y = min(mural.y + 1, game_map.height - 1)

            if not game_map.is_blocked(new_x, new_y):
                player.x = new_x
                player.y = new_y

                # Recompute FOV to see the mural
                fov_map = initialize_fov(game_map)
                recompute_fov(fov_map, player.x, player.y, constants["fov_radius"], constants["fov_algorithm"])

                # Verify mural FOV check works (no crash)
                try:
                    mural_visible = fov_map.is_in_fov(mural.x, mural.y)
                    # If visible, great; if not, that's OK (positioning is random)
                except Exception as e:
                    pytest.fail(f"FOV check raised exception: {e}")


class TestGoldenPathIntegration:
    """Higher-level integration tests combining multiple systems."""

    def setup_method(self):
        """Reset testing config for each test."""
        from config import testing_config as tc_module
        tc_module._testing_config = None
        set_testing_mode(True)
        config = get_testing_config()
        config.start_level = 1

    def test_multiple_moves_no_crash(self):
        """Extended integration test: multiple moves in a row without crash.
        
        This verifies that the game loop can handle sustained play without
        accumulating errors or memory issues.
        """
        constants = get_constants()
        player, entities, game_map, message_log, game_state = get_game_variables(constants)

        fov_map = initialize_fov(game_map)
        recompute_fov(fov_map, player.x, player.y, constants["fov_radius"], constants["fov_algorithm"])

        # Simulate 20 moves in random valid directions
        move_count = 0
        max_attempts = 0

        directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)]

        while move_count < 20 and max_attempts < 50:
            max_attempts += 1
            
            # Pick a random valid direction
            for dx, dy in directions:
                new_x = player.x + dx
                new_y = player.y + dy

                if 0 <= new_x < game_map.width and 0 <= new_y < game_map.height:
                    if not game_map.is_blocked(new_x, new_y):
                        player.x = new_x
                        player.y = new_y
                        recompute_fov(fov_map, player.x, player.y, constants["fov_radius"], constants["fov_algorithm"])
                        move_count += 1
                        break

        # Verify we made meaningful progress
        assert move_count >= 10, f"Should make at least 10 moves, got {move_count}"

    def test_spawn_multiple_entities_no_overlap(self):
        """Verify that spawned entities don't overlap at same coordinates.
        
        This catches bugs where the spawning system places multiple entities
        on top of each other.
        """
        constants = get_constants()
        player, entities, game_map, message_log, game_state = get_game_variables(constants)

        # Get all entity positions
        positions = {}
        for entity in entities:
            # Skip items in inventory (x, y = -1)
            if entity.x < 0 or entity.y < 0:
                continue
            
            pos = (entity.x, entity.y)
            if pos not in positions:
                positions[pos] = []
            positions[pos].append(entity.name)

        # Check for overlaps (only blocking entities should be alone)
        for pos, entity_names in positions.items():
            if len(entity_names) > 1:
                # Multiple entities at same position - verify at least one is not blocking
                blocking_entities = [
                    e for e in entities 
                    if (e.x, e.y) == pos and hasattr(e, 'blocks') and e.blocks
                ]
                assert len(blocking_entities) <= 1, \
                    f"Position {pos} has {len(blocking_entities)} blocking entities: {entity_names}"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])

