"""Tests for monster corpse behavior.

This module contains tests to verify that dead monsters are properly
transformed into corpses that remain visible in the game world.
"""


# QUARANTINED: Corpse mechanics may have changed
# See QUARANTINED_TESTS.md for details.

import pytest

# Quarantine entire file - REMOVED for Session 2 testing
# pytestmark = pytest.mark.skip(reason="Quarantined - Corpse mechanics may have changed. See QUARANTINED_TESTS.md")

import unittest
from unittest.mock import Mock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from loader_functions.initialize_new_game import get_game_variables, get_constants
from components.fighter import Fighter
from components.ai import BasicMonster
from entity import Entity
from game_actions import ActionProcessor
from engine.game_state_manager import GameStateManager
from game_states import GameStates


class TestCorpseBehavior(unittest.TestCase):
    """Test that dead monsters become visible corpses."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create game state
        constants = get_constants()
        self.player, entities, game_map, message_log, game_state = get_game_variables(constants)
        
        # Create a weak monster that will die in one hit (place it away from player)
        self.monster = Entity(
            x=self.player.x + 5, y=self.player.y + 5, 
            char='o', color=(63, 127, 63), name='Test Orc',
            fighter=Fighter(hp=1, defense=0, power=1),
            ai=BasicMonster(),
            blocks=True
        )
        entities.append(self.monster)
        
        # Set up game state manager
        self.state_manager = GameStateManager()
        self.state_manager.initialize_game(
            self.player, entities, game_map, message_log, 
            GameStates.PLAYERS_TURN, constants
        )
        
        # Create action processor
        self.action_processor = ActionProcessor(self.state_manager)
    
    def test_combat_death_creates_corpse(self):
        """Test that combat deaths create visible corpses."""
        # Record initial state
        initial_entity_count = len(self.state_manager.state.entities)
        
        # Verify monster is alive
        self.assertTrue(self.monster.fighter.hp > 0, "Monster should be alive")
        self.assertTrue(self.monster.blocks, "Living monster should block")
        self.assertEqual(self.monster.char, 'o', "Living monster should have orc char")
        self.assertIn(self.monster, self.state_manager.state.entities, "Monster should be in entities")
        
        # Attack monster (should kill it)
        attack_results = self.player.fighter.attack(self.monster)
        
        # Process death
        for result in attack_results:
            dead_entity = result.get('dead')
            if dead_entity:
                self.action_processor._handle_entity_death(dead_entity, remove_from_entities=False)
        
        # Verify corpse state
        self.assertEqual(self.monster.fighter, None, "Corpse should have no fighter")
        self.assertFalse(self.monster.blocks, "Corpse should not block movement")
        self.assertEqual(self.monster.char, '%', "Corpse should have % character")
        self.assertTrue(self.monster.name.startswith("remains of"), "Corpse should have 'remains of' name")
        
        # Verify corpse remains in entities (visible in game world)
        self.assertIn(self.monster, self.state_manager.state.entities, 
                     "Corpse should remain in entities list")
        # Note: Entity count may increase due to loot drops (equipment, items)
        # This is expected behavior - corpse replaces monster, but loot adds new entities
        self.assertGreaterEqual(len(self.state_manager.state.entities), initial_entity_count,
                               "Corpse should remain (may have loot drops)")
    
    def test_multiple_corpses_accumulate(self):
        """Test that multiple corpses can accumulate in the game world."""
        # Create second monster (place it away from other entities)
        monster2 = Entity(
            x=self.player.x + 10, y=self.player.y + 10,
            char='g', color=(0, 127, 0), name='Test Goblin',
            fighter=Fighter(hp=1, defense=0, power=1),
            ai=BasicMonster(),
            blocks=True
        )
        self.state_manager.state.entities.append(monster2)
        
        initial_entity_count = len(self.state_manager.state.entities)
        
        # Kill both monsters
        for monster in [self.monster, monster2]:
            attack_results = self.player.fighter.attack(monster)
            for result in attack_results:
                dead_entity = result.get('dead')
                if dead_entity:
                    self.action_processor._handle_entity_death(dead_entity, remove_from_entities=False)
        
        # Verify both corpses remain
        self.assertIn(self.monster, self.state_manager.state.entities, "First corpse should remain")
        self.assertIn(monster2, self.state_manager.state.entities, "Second corpse should remain")
        
        # Verify both are proper corpses
        for corpse in [self.monster, monster2]:
            self.assertIsNone(corpse.fighter, "Corpse should have no fighter")
            self.assertFalse(corpse.blocks, "Corpse should not block")
            self.assertEqual(corpse.char, '%', "Corpse should have % character")
        
        # Note: Entity count may increase due to loot drops from both monsters
        self.assertGreaterEqual(len(self.state_manager.state.entities), initial_entity_count,
                               "Corpses should remain (may have loot drops)")
    
    def test_corpse_does_not_block_movement(self):
        """Test that corpses do not block player movement."""
        # Kill monster
        attack_results = self.player.fighter.attack(self.monster)
        for result in attack_results:
            dead_entity = result.get('dead')
            if dead_entity:
                self.action_processor._handle_entity_death(dead_entity, remove_from_entities=False)
        
        # Verify corpse doesn't block
        self.assertFalse(self.monster.blocks, "Corpse should not block movement")
        
        # Player should be able to move through corpse position
        # (This would be tested in movement logic, but we verify the blocks property)
        corpse_position = (self.monster.x, self.monster.y)
        
        # Check that no entity at corpse position blocks movement
        blocking_entities = [
            entity for entity in self.state_manager.state.entities
            if entity.x == corpse_position[0] and entity.y == corpse_position[1] and entity.blocks
        ]
        self.assertEqual(len(blocking_entities), 0, 
                        "No entities at corpse position should block movement")
    
    def test_corpse_visual_properties(self):
        """Test that corpses have the correct visual appearance."""
        original_name = self.monster.name
        
        # Kill monster
        attack_results = self.player.fighter.attack(self.monster)
        for result in attack_results:
            dead_entity = result.get('dead')
            if dead_entity:
                self.action_processor._handle_entity_death(dead_entity, remove_from_entities=False)
        
        # Verify visual properties
        self.assertEqual(self.monster.char, '%', "Corpse should display as %")
        self.assertEqual(self.monster.color, (127, 0, 0), "Corpse should be dark red")
        self.assertEqual(self.monster.name, f"remains of {original_name}", 
                        "Corpse should have 'remains of' prefix")
        
        # Verify render order (corpses should render behind other entities)
        from render_functions import RenderOrder
        self.assertEqual(self.monster.render_order, RenderOrder.CORPSE,
                        "Corpse should have CORPSE render order")


if __name__ == '__main__':
    unittest.main()
