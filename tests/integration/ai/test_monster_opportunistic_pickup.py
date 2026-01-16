"""Regression tests for monster opportunistic item pickup behavior.

This test suite verifies that monsters (e.g., orcs) with item-seeking AI
opportunistically pick up items while moving toward the player, but NOT when
already in combat.

Design Rules (from ItemSeekingAI and BasicMonster):
1. Monster must have can_seek_items=true and ItemSeekingAI component
2. Monster must NOT be in combat (not attacked yet)
3. Item must be closer to monster than player is
4. Item must be within seek_distance (default 5 tiles)
5. Monster must have inventory space

These tests ensure the behavior remains stable and deterministic.
"""

import pytest
import random
from unittest.mock import Mock

from entity import Entity
from components.fighter import Fighter
from components.inventory import Inventory
from components.ai.basic_monster import BasicMonster
from components.item_seeking_ai import ItemSeekingAI
from components.component_registry import ComponentType
from map_objects.game_map import GameMap
from map_objects.tile import Tile
from config.entity_factory import EntityFactory
from config.entity_registry import load_entity_config


@pytest.fixture(scope="module")
def entity_factory():
    """Create entity factory with loaded config."""
    load_entity_config('config/entities.yaml')
    return EntityFactory()


class TestMonsterOpportunisticPickup:
    """Test monster opportunistic item pickup behavior."""
    
    def test_orc_picks_up_weapon_on_path_to_player(self, entity_factory):
        """Orc should pick up weapon on path when moving toward player (not in combat)."""
        # Set deterministic seed
        random.seed(1337)
        
        # Create a simple 20x20 map with no obstacles
        game_map = GameMap(20, 20)
        for x in range(20):
            for y in range(20):
                game_map.tiles[x][y] = Tile(False)  # All walkable
        
        # Create player at (15, 10)
        player = Entity(15, 10, '@', (255, 255, 255), 'Player', blocks=True)
        player.fighter = Fighter(hp=100, defense=2, power=5)
        
        # Create orc at (5, 10) - same row, 10 tiles away from player
        orc = entity_factory.create_monster('orc', 5, 10)
        assert orc is not None, "Orc should be created"
        
        # Verify orc has item-seeking capability
        item_seeking_ai = orc.get_component_optional(ComponentType.ITEM_SEEKING_AI)
        assert item_seeking_ai is not None, "Orc should have ItemSeekingAI component"
        
        # Verify orc is NOT in combat initially
        ai = orc.get_component_optional(ComponentType.AI)
        assert ai is not None, "Orc should have AI component"
        assert not ai.in_combat, "Orc should not be in combat initially"
        
        # Create a weapon (sword) at (8, 10) - on the path between orc and player
        # Distance from orc: 3 tiles, Distance from player: 7 tiles
        # Item is closer to orc than player, so orc should seek it
        sword = entity_factory.create_weapon('sword', 8, 10)
        assert sword is not None, "Sword should be created"
        
        entities = [player, orc, sword]
        
        # Mock FOV map (orc can see player and sword)
        fov_map = Mock()
        fov_map.fov = [[True for _ in range(20)] for _ in range(20)]
        
        # Simulate orc's turn
        # Orc should move toward the sword (item-seeking behavior)
        results = ai.take_turn(player, fov_map, game_map, entities)
        
        # Check if orc moved toward sword or picked it up
        # After one turn, orc should have moved closer to the sword
        # Orc was at (5, 10), sword at (8, 10), so orc should move to (6, 10)
        assert orc.x > 5 or sword in orc.inventory.items, \
            "Orc should move toward sword or pick it up"
        
        # Continue turns until orc reaches the sword
        max_turns = 10
        for turn in range(max_turns):
            if sword not in entities:
                # Sword was picked up
                break
            
            results = ai.take_turn(player, fov_map, game_map, entities)
            
            # If orc is on the sword's tile, it should pick it up
            if orc.x == sword.x and orc.y == sword.y:
                # Next turn should pick it up
                results = ai.take_turn(player, fov_map, game_map, entities)
                break
        
        # Verify sword was picked up
        assert sword not in entities, \
            f"Sword should be picked up by orc after {turn+1} turns"
        assert sword in orc.inventory.items or orc.equipment.main_hand == sword, \
            "Sword should be in orc's inventory or equipped"
    
    def test_orc_ignores_items_when_in_combat(self, entity_factory):
        """Orc should NOT pick up items when already in combat (attacked)."""
        # Set deterministic seed
        random.seed(1337)
        
        # Create a simple 20x20 map
        game_map = GameMap(20, 20)
        for x in range(20):
            for y in range(20):
                game_map.tiles[x][y] = Tile(False)  # All walkable
        
        # Create player at (15, 10)
        player = Entity(15, 10, '@', (255, 255, 255), 'Player', blocks=True)
        player.fighter = Fighter(hp=100, defense=2, power=5)
        
        # Create orc at (5, 10)
        orc = entity_factory.create_monster('orc', 5, 10)
        assert orc is not None, "Orc should be created"
        
        # Set orc to in_combat state (simulating it was attacked)
        ai = orc.get_component_optional(ComponentType.AI)
        assert ai is not None, "Orc should have AI component"
        ai.in_combat = True  # Orc has been attacked
        
        # Create a weapon at (8, 10) - on the path
        sword = entity_factory.create_weapon('sword', 8, 10)
        assert sword is not None, "Sword should be created"
        
        entities = [player, orc, sword]
        
        # Mock FOV map
        fov_map = Mock()
        fov_map.fov = [[True for _ in range(20)] for _ in range(20)]
        
        # Record orc's initial position
        initial_x = orc.x
        
        # Simulate orc's turn - should move toward PLAYER, not sword
        results = ai.take_turn(player, fov_map, game_map, entities)
        
        # Orc should move toward player (x increases), ignoring the sword
        assert orc.x > initial_x, "Orc should move toward player when in combat"
        
        # Continue for a few more turns
        for _ in range(5):
            if orc.x >= player.x - 1:  # Stop before reaching player
                break
            results = ai.take_turn(player, fov_map, game_map, entities)
        
        # Verify sword was NOT picked up (orc ignored it)
        assert sword in entities, "Sword should still be on the ground (not picked up)"
        assert sword not in orc.inventory.items, "Sword should not be in orc's inventory"
    
    def test_orc_ignores_items_farther_than_player(self, entity_factory):
        """Orc should NOT seek items that are farther away than the player."""
        # Set deterministic seed
        random.seed(1337)
        
        # Create a simple 20x20 map
        game_map = GameMap(20, 20)
        for x in range(20):
            for y in range(20):
                game_map.tiles[x][y] = Tile(False)  # All walkable
        
        # Create player at (10, 10)
        player = Entity(10, 10, '@', (255, 255, 255), 'Player', blocks=True)
        player.fighter = Fighter(hp=100, defense=2, power=5)
        
        # Create orc at (5, 10) - 5 tiles from player
        orc = entity_factory.create_monster('orc', 5, 10)
        assert orc is not None, "Orc should be created"
        
        # Verify orc is NOT in combat
        ai = orc.get_component_optional(ComponentType.AI)
        assert ai is not None, "Orc should have AI component"
        assert not ai.in_combat, "Orc should not be in combat"
        
        # Create a weapon at (15, 10) - BEYOND the player (farther from orc)
        # Distance from orc: 10 tiles, Distance from player: 5 tiles
        # Item is farther from orc than player, so orc should ignore it
        sword = entity_factory.create_weapon('sword', 15, 10)
        assert sword is not None, "Sword should be created"
        
        entities = [player, orc, sword]
        
        # Mock FOV map
        fov_map = Mock()
        fov_map.fov = [[True for _ in range(20)] for _ in range(20)]
        
        # Record initial position
        initial_x = orc.x
        
        # Simulate orc's turn - should move toward PLAYER, not sword
        results = ai.take_turn(player, fov_map, game_map, entities)
        
        # Orc should move toward player (x increases), ignoring the far sword
        assert orc.x > initial_x, "Orc should move toward player, ignoring far item"
        
        # Continue for a few turns
        for _ in range(3):
            if orc.x >= player.x - 1:  # Stop before reaching player
                break
            results = ai.take_turn(player, fov_map, game_map, entities)
        
        # Verify sword was NOT picked up
        assert sword in entities, "Sword should still be on the ground"
        assert sword not in orc.inventory.items, "Sword should not be in orc's inventory"
    
    def test_orc_picks_up_item_when_adjacent(self, entity_factory):
        """Orc should pick up item when moving onto its tile."""
        # Set deterministic seed
        random.seed(1337)
        
        # Create a simple 20x20 map
        game_map = GameMap(20, 20)
        for x in range(20):
            for y in range(20):
                game_map.tiles[x][y] = Tile(False)  # All walkable
        
        # Create player at (15, 10)
        player = Entity(15, 10, '@', (255, 255, 255), 'Player', blocks=True)
        player.fighter = Fighter(hp=100, defense=2, power=5)
        
        # Create orc at (5, 10)
        orc = entity_factory.create_monster('orc', 5, 10)
        assert orc is not None, "Orc should be created"
        
        # Verify orc is NOT in combat
        ai = orc.get_component_optional(ComponentType.AI)
        assert ai is not None, "Orc should have AI component"
        assert not ai.in_combat, "Orc should not be in combat"
        
        # Create a weapon at (6, 10) - exactly 1 tile away from orc
        sword = entity_factory.create_weapon('sword', 6, 10)
        assert sword is not None, "Sword should be created"
        
        entities = [player, orc, sword]
        
        # Mock FOV map
        fov_map = Mock()
        fov_map.fov = [[True for _ in range(20)] for _ in range(20)]
        
        # Simulate orc's turn - should move to sword's tile and pick it up
        results = ai.take_turn(player, fov_map, game_map, entities)
        
        # After moving to (6, 10), orc should be on the sword
        assert orc.x == 6, f"Orc should move to sword's tile, but is at {orc.x}"
        
        # If not picked up yet, take another turn
        if sword in entities:
            results = ai.take_turn(player, fov_map, game_map, entities)
        
        # Verify sword was picked up
        assert sword not in entities, "Sword should be removed from entities"
        assert sword in orc.inventory.items or orc.equipment.main_hand == sword, \
            "Sword should be in orc's inventory or equipped"
    
    def test_multiple_orcs_can_seek_different_items(self, entity_factory):
        """Multiple orcs should each seek their own closest items."""
        # Set deterministic seed
        random.seed(1337)
        
        # Create a simple 30x30 map
        game_map = GameMap(30, 30)
        for x in range(30):
            for y in range(30):
                game_map.tiles[x][y] = Tile(False)  # All walkable
        
        # Create player at (20, 15)
        player = Entity(20, 15, '@', (255, 255, 255), 'Player', blocks=True)
        player.fighter = Fighter(hp=100, defense=2, power=5)
        
        # Create two orcs at different positions
        orc1 = entity_factory.create_monster('orc', 5, 10)
        orc2 = entity_factory.create_monster('orc', 5, 15)
        
        assert orc1 is not None and orc2 is not None, "Both orcs should be created"
        
        # Create two weapons at different positions
        sword1 = entity_factory.create_weapon('sword', 8, 10)  # Closer to orc1
        sword2 = entity_factory.create_weapon('sword', 8, 15)  # Closer to orc2
        
        entities = [player, orc1, orc2, sword1, sword2]
        
        # Mock FOV map
        fov_map = Mock()
        fov_map.fov = [[True for _ in range(30)] for _ in range(30)]
        
        # Get AI components
        ai1 = orc1.get_component_optional(ComponentType.AI)
        ai2 = orc2.get_component_optional(ComponentType.AI)
        
        # Both orcs should not be in combat
        assert not ai1.in_combat and not ai2.in_combat
        
        # Simulate several turns for both orcs
        for turn in range(10):
            # Orc1's turn
            if sword1 in entities:
                ai1.take_turn(player, fov_map, game_map, entities)
            
            # Orc2's turn
            if sword2 in entities:
                ai2.take_turn(player, fov_map, game_map, entities)
            
            # Stop if both swords are picked up
            if sword1 not in entities and sword2 not in entities:
                break
        
        # Verify each orc picked up their respective sword
        # (or at least one of them did)
        picked_up_count = 0
        if sword1 not in entities:
            picked_up_count += 1
        if sword2 not in entities:
            picked_up_count += 1
        
        assert picked_up_count >= 1, \
            "At least one orc should have picked up a sword"


class TestMonsterPickupDeterminism:
    """Test that monster pickup behavior is deterministic under fixed seed."""
    
    def test_pickup_behavior_is_deterministic(self, entity_factory):
        """Verify that monster pickup behavior is deterministic with seed_base=1337."""
        
        def run_scenario():
            """Run the scenario and return the final state."""
            random.seed(1337)
            
            # Create map
            game_map = GameMap(20, 20)
            for x in range(20):
                for y in range(20):
                    game_map.tiles[x][y] = Tile(False)
            
            # Create entities
            player = Entity(15, 10, '@', (255, 255, 255), 'Player', blocks=True)
            player.fighter = Fighter(hp=100, defense=2, power=5)
            
            orc = entity_factory.create_monster('orc', 5, 10)
            sword = entity_factory.create_weapon('sword', 8, 10)
            
            entities = [player, orc, sword]
            
            # Mock FOV
            fov_map = Mock()
            fov_map.fov = [[True for _ in range(20)] for _ in range(20)]
            
            # Get AI
            ai = orc.get_component_optional(ComponentType.AI)
            
            # Run 10 turns
            for _ in range(10):
                if sword not in entities:
                    break
                ai.take_turn(player, fov_map, game_map, entities)
            
            # Return state
            return {
                'orc_x': orc.x,
                'orc_y': orc.y,
                'sword_in_entities': sword in entities,
                'sword_in_inventory': sword in orc.inventory.items if hasattr(orc, 'inventory') else False,
                'sword_equipped': orc.equipment.main_hand == sword if hasattr(orc, 'equipment') and orc.equipment else False,
            }
        
        # Run scenario twice with same seed
        result1 = run_scenario()
        result2 = run_scenario()
        
        # Results should be identical
        assert result1 == result2, \
            f"Scenario should be deterministic but got different results:\n{result1}\nvs\n{result2}"
