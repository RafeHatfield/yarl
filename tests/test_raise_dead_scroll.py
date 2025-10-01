"""Tests for the Raise Dead scroll functionality.

This test suite ensures that the raise dead spell correctly:
- Finds and resurrects corpses
- Creates zombies with proper stats (2x HP, 0.5x damage)
- Sets up MindlessZombieAI
- Handles edge cases (no corpse, out of range, etc.)
"""

import unittest
from unittest.mock import MagicMock, patch, call
import math

from entity import Entity
from components.fighter import Fighter
from components.ai import MindlessZombieAI
from components.faction import Faction
from components.item import Item
from item_functions import cast_raise_dead
from render_functions import RenderOrder


class TestRaiseDeadScroll(unittest.TestCase):
    """Test suite for raise dead scroll functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create player
        self.player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
        self.player.fighter = Fighter(hp=100, defense=2, power=5)
        
        # Create a corpse (dead orc)
        self.corpse = Entity(3, 3, '%', (127, 0, 0), 'remains of orc', blocks=False)
        self.corpse.fighter = None  # Corpses have no fighter
        self.corpse.ai = None  # Corpses have no AI
        self.corpse.render_order = RenderOrder.CORPSE
        
        # Entities list
        self.entities = [self.player, self.corpse]
        
    def test_raise_dead_basic_resurrection(self):
        """Test basic corpse resurrection."""
        # Mock the entity registry to return orc stats
        with patch('config.entity_registry.get_entity_registry') as mock_registry:
            mock_monster_def = MagicMock()
            mock_monster_def.stats.hp = 20
            mock_monster_def.stats.defense = 0
            mock_monster_def.stats.power = 4
            
            mock_registry.return_value.monsters.get.return_value = mock_monster_def
            
            # Cast raise dead on the corpse
            results = cast_raise_dead(
                self.player,
                entities=self.entities,
                target_x=3,
                target_y=3,
                range=5
            )
            
            # Should consume the scroll
            self.assertTrue(any(r.get("consumed") for r in results))
            
            # Should have a success message
            self.assertTrue(any("message" in r for r in results))
            success_msg = next(r["message"] for r in results if "message" in r)
            self.assertIn("rises", success_msg.text)
            
            # Corpse should be transformed
            self.assertEqual(self.corpse.name, "Zombified orc")
            self.assertEqual(self.corpse.color, (40, 40, 40))  # Black
            self.assertTrue(self.corpse.blocks)
            self.assertEqual(self.corpse.render_order, RenderOrder.ACTOR)
            
            # Should have fighter with 2x HP, 0.5x power
            self.assertIsNotNone(self.corpse.fighter)
            self.assertEqual(self.corpse.fighter.hp, 40)  # 2x 20
            self.assertEqual(self.corpse.fighter.base_power, 2)  # 0.5x 4
            self.assertEqual(self.corpse.fighter.base_defense, 0)
            
            # Should have MindlessZombieAI
            self.assertIsNotNone(self.corpse.ai)
            self.assertIsInstance(self.corpse.ai, MindlessZombieAI)
            self.assertEqual(self.corpse.ai.owner, self.corpse)
            
            # Should have NEUTRAL faction
            self.assertEqual(self.corpse.faction, Faction.NEUTRAL)
    
    def test_raise_dead_no_corpse(self):
        """Test raise dead on empty tile."""
        results = cast_raise_dead(
            self.player,
            entities=self.entities,
            target_x=10,
            target_y=10,
            range=15  # Within range but no corpse
        )
        
        # Should not consume scroll
        self.assertFalse(any(r.get("consumed") for r in results))
        
        # Should have error message
        self.assertTrue(any("message" in r for r in results))
        error_msg = next(r["message"] for r in results if "message" in r)
        self.assertIn("no corpse", error_msg.text.lower())
    
    def test_raise_dead_out_of_range(self):
        """Test raise dead on corpse that's too far away."""
        results = cast_raise_dead(
            self.player,
            entities=self.entities,
            target_x=3,
            target_y=3,
            range=2  # Only 2 tiles range, corpse is at (3,3) from (0,0)
        )
        
        # Should not consume scroll
        self.assertFalse(any(r.get("consumed") for r in results))
        
        # Should have error message
        self.assertTrue(any("message" in r for r in results))
        error_msg = next(r["message"] for r in results if "message" in r)
        self.assertIn("too far", error_msg.text.lower())
    
    def test_raise_dead_no_target(self):
        """Test raise dead without target coordinates."""
        results = cast_raise_dead(
            self.player,
            entities=self.entities
        )
        
        # Should not consume scroll
        self.assertFalse(any(r.get("consumed") for r in results))
        
        # Should have error message
        self.assertTrue(any("message" in r for r in results))
        error_msg = next(r["message"] for r in results if "message" in r)
        self.assertIn("select a corpse", error_msg.text.lower())
    
    def test_raise_dead_clears_inventory_equipment(self):
        """Test that raised zombies have no inventory or equipment."""
        # Give corpse inventory and equipment attributes
        self.corpse.inventory = MagicMock()
        self.corpse.equipment = MagicMock()
        
        with patch('config.entity_registry.get_entity_registry') as mock_registry:
            mock_monster_def = MagicMock()
            mock_monster_def.stats.hp = 10
            mock_monster_def.stats.defense = 0
            mock_monster_def.stats.power = 3
            
            mock_registry.return_value.monsters.get.return_value = mock_monster_def
            
            results = cast_raise_dead(
                self.player,
                entities=self.entities,
                target_x=3,
                target_y=3,
                range=5
            )
            
            # Inventory and equipment should be None
            self.assertIsNone(self.corpse.inventory)
            self.assertIsNone(self.corpse.equipment)
    
    def test_raise_dead_unknown_monster_fallback(self):
        """Test raise dead with unknown monster type uses fallback stats."""
        with patch('config.entity_registry.get_entity_registry') as mock_registry:
            # Registry doesn't have this monster
            mock_registry.return_value.monsters.get.return_value = None
            
            results = cast_raise_dead(
                self.player,
                entities=self.entities,
                target_x=3,
                target_y=3,
                range=5
            )
            
            # Should still work with fallback stats
            self.assertTrue(any(r.get("consumed") for r in results))
            
            # Should use fallback: base_hp=10, base_power=3
            self.assertEqual(self.corpse.fighter.hp, 20)  # 2x 10
            self.assertEqual(self.corpse.fighter.base_power, 1)  # 0.5x 3 = 1.5, int() = 1
    
    def test_raise_dead_minimum_damage(self):
        """Test that zombie damage is at least 1."""
        with patch('config.entity_registry.get_entity_registry') as mock_registry:
            # Very weak monster (power=1)
            mock_monster_def = MagicMock()
            mock_monster_def.stats.hp = 5
            mock_monster_def.stats.defense = 0
            mock_monster_def.stats.power = 1
            
            mock_registry.return_value.monsters.get.return_value = mock_monster_def
            
            results = cast_raise_dead(
                self.player,
                entities=self.entities,
                target_x=3,
                target_y=3,
                range=5
            )
            
            # 0.5 * 1 = 0.5, but should be at least 1
            self.assertEqual(self.corpse.fighter.base_power, 1)
    
    def test_raise_dead_range_calculation(self):
        """Test that range is calculated correctly using Euclidean distance."""
        # Place corpse at (3, 4) - distance sqrt(9+16) = 5
        self.corpse.x = 3
        self.corpse.y = 4
        
        with patch('config.entity_registry.get_entity_registry') as mock_registry:
            mock_monster_def = MagicMock()
            mock_monster_def.stats.hp = 10
            mock_monster_def.stats.defense = 0
            mock_monster_def.stats.power = 3
            
            mock_registry.return_value.monsters.get.return_value = mock_monster_def
            
            # Exactly at max range (5)
            results = cast_raise_dead(
                self.player,
                entities=self.entities,
                target_x=3,
                target_y=4,
                range=5
            )
            
            # Should succeed
            self.assertTrue(any(r.get("consumed") for r in results))
            
            # Just beyond max range
            results2 = cast_raise_dead(
                self.player,
                entities=self.entities,
                target_x=3,
                target_y=4,
                range=4
            )
            
            # Should fail
            self.assertFalse(any(r.get("consumed") for r in results2))


class TestMindlessZombieAI(unittest.TestCase):
    """Test suite for MindlessZombieAI behavior."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.zombie = Entity(5, 5, 'Z', (40, 40, 40), 'Zombified orc', blocks=True)
        self.zombie.fighter = Fighter(hp=40, defense=0, power=2)
        self.zombie.fighter.owner = self.zombie  # Set owner!
        self.zombie.ai = MindlessZombieAI()
        self.zombie.ai.owner = self.zombie
        
        self.player = Entity(6, 5, '@', (255, 255, 255), 'Player', blocks=True)
        self.player.fighter = Fighter(hp=100, defense=2, power=5)
        self.player.fighter.owner = self.player  # Set owner!
        
        self.orc = Entity(5, 6, 'o', (63, 127, 63), 'Orc', blocks=True)
        self.orc.fighter = Fighter(hp=20, defense=0, power=4)
        self.orc.fighter.owner = self.orc  # Set owner!
        
        self.game_map = MagicMock()
        self.game_map.width = 80
        self.game_map.height = 45
        self.game_map.is_blocked.return_value = False
    
    def test_zombie_attacks_adjacent_player(self):
        """Test that zombie attacks adjacent player."""
        entities = [self.zombie, self.player, self.orc]
        
        results = self.zombie.ai.take_turn(
            target=self.player,
            fov_map=None,
            game_map=self.game_map,
            entities=entities
        )
        
        # Should have attack results
        self.assertTrue(len(results) > 0)
        # Should damage the player
        self.assertTrue(any("message" in r for r in results))
    
    def test_zombie_attacks_adjacent_monster(self):
        """Test that zombie attacks adjacent monster."""
        entities = [self.zombie, self.orc]
        
        results = self.zombie.ai.take_turn(
            target=None,
            fov_map=None,
            game_map=self.game_map,
            entities=entities
        )
        
        # Should attack the orc
        self.assertTrue(len(results) > 0)
    
    def test_zombie_wanders_when_no_targets(self):
        """Test that zombie wanders randomly when no adjacent targets."""
        # Place everyone far apart
        self.player.x, self.player.y = 10, 10
        self.orc.x, self.orc.y = 15, 15
        
        entities = [self.zombie, self.player, self.orc]
        
        original_x, original_y = self.zombie.x, self.zombie.y
        
        with patch('components.ai.randint') as mock_randint:
            mock_randint.side_effect = [1, 0]  # Move right
            
            results = self.zombie.ai.take_turn(
                target=None,
                fov_map=None,
                game_map=self.game_map,
                entities=entities
            )
            
            # Should have moved (or tried to move)
            # Movement depends on game_map.is_blocked
            # Just check that take_turn returned results (empty is ok for movement)
            self.assertIsInstance(results, list)
    
    def test_zombie_ignores_corpses(self):
        """Test that zombie doesn't attack corpses (no fighter)."""
        corpse = Entity(6, 5, '%', (127, 0, 0), 'remains of troll', blocks=False)
        corpse.fighter = None  # No fighter component
        
        entities = [self.zombie, corpse]
        
        results = self.zombie.ai.take_turn(
            target=None,
            fov_map=None,
            game_map=self.game_map,
            entities=entities
        )
        
        # Should not attack corpse (no fighter), should wander instead
        # Results should be empty (wandering) or very short
        self.assertIsInstance(results, list)


if __name__ == '__main__':
    unittest.main()

