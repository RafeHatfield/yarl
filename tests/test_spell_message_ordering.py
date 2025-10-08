"""Tests for spell message ordering.

This module tests that spell cast messages appear BEFORE effect messages,
fixing a bug where dragon fart showed affected entities before the cast message.
"""

import unittest
from unittest.mock import Mock, patch
from entity import Entity
from components.fighter import Fighter
from components.ai import BasicMonster
from game_messages import Message
import item_functions


class TestSpellMessageOrdering(unittest.TestCase):
    """Test that spell messages appear in correct order."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create caster (player)
        self.player = Entity(x=10, y=10, char='@', color=(255, 255, 255), name='Player')
        
        # Create target monsters
        # Create orcs with AI and Fighter components
        fighter1 = Fighter(hp=20, defense=3, power=4)
        ai1 = BasicMonster()
        self.orc1 = Entity(x=12, y=10, char='o', color=(0, 127, 0), name='Orc 1', 
                          blocks=True, fighter=fighter1, ai=ai1)
        
        fighter2 = Fighter(hp=20, defense=3, power=4)
        ai2 = BasicMonster()
        self.orc2 = Entity(x=13, y=10, char='o', color=(0, 127, 0), name='Orc 2',
                          blocks=True, fighter=fighter2, ai=ai2)
        
        # Create entities list
        self.entities = [self.player, self.orc1, self.orc2]
        
        # Mock game_map
        self.game_map = Mock()
        
    def test_dragon_fart_cast_message_before_effects(self):
        """Test that dragon fart cast message appears BEFORE affected entity messages.
        
        Bug: "The monster is showing it's effect before the message about the spell being cast."
        Fix: Move cast message before the loop that generates effect messages.
        """
        # Mock visual effect to prevent actual rendering
        with patch('item_functions.show_dragon_fart'):
            # Cast dragon fart at orcs
            results = item_functions.cast_dragon_fart(
                self.player,
                entities=self.entities,
                game_map=self.game_map,
                target_x=15,  # Target to the right
                target_y=10,
                duration=20
            )
        
        # Extract all messages
        messages = [r.get("message") for r in results if r.get("message")]
        message_texts = [m.text for m in messages]
        
        # Should have at least 3 messages: cast + 2 affected orcs
        self.assertGreaterEqual(len(message_texts), 3,
                               "Should have cast message + affected entity messages")
        
        # First message should be the cast message
        self.assertIn("DRAGON FART", message_texts[0].upper(),
                     "First message should be the cast message")
        self.assertIn("unleashes", message_texts[0].lower(),
                     "Cast message should mention unleashing")
        
        # Subsequent messages should be about affected entities
        for i in range(1, len(message_texts)):
            self.assertIn("overwhelmed", message_texts[i].lower(),
                         f"Message {i} should be about affected entity")
    
    def test_dragon_fart_consumed_flag_with_cast_message(self):
        """Test that the consumed flag is set with the cast message."""
        with patch('item_functions.show_dragon_fart'):
            results = item_functions.cast_dragon_fart(
                self.player,
                entities=self.entities,
                game_map=self.game_map,
                target_x=15,
                target_y=10,
                duration=20
            )
        
        # Find the result with consumed=True
        consumed_results = [r for r in results if r.get("consumed")]
        self.assertEqual(len(consumed_results), 1,
                        "Should have exactly one consumed=True result")
        
        # The consumed result should have the cast message
        cast_result = consumed_results[0]
        self.assertIn("message", cast_result, "Consumed result should have message")
        self.assertIn("DRAGON FART", cast_result["message"].text.upper(),
                     "Consumed result message should be the cast message")
    
    def test_dragon_fart_no_targets_message(self):
        """Test message when dragon fart hits no targets."""
        # Create entities list with no monsters in cone
        entities_no_targets = [self.player]
        
        with patch('item_functions.show_dragon_fart'):
            results = item_functions.cast_dragon_fart(
                self.player,
                entities=entities_no_targets,
                game_map=self.game_map,
                target_x=15,
                target_y=10,
                duration=20
            )
        
        # Should have one message about dissipating
        messages = [r.get("message") for r in results if r.get("message")]
        self.assertEqual(len(messages), 1,
                        "Should have exactly one message when no targets hit")
        self.assertIn("dissipates", messages[0].text.lower(),
                     "Message should mention gas dissipating")
        
        # Should NOT be consumed if no targets
        consumed = [r for r in results if r.get("consumed")]
        self.assertEqual(len(consumed), 0,
                        "Should not consume scroll if no targets hit")
    
    def test_fireball_cast_message_ordering(self):
        """Test that fireball cast message appears before damage messages."""
        with patch('item_functions.show_fireball'):
            results = item_functions.cast_fireball(
                self.player,
                entities=self.entities,
                fov_map=Mock(),
                target_x=12,
                target_y=10,
                damage=25,
                radius=3
            )
        
        # Extract all messages
        messages = [r.get("message") for r in results if r.get("message")]
        message_texts = [m.text for m in messages]
        
        # Should have messages
        self.assertGreater(len(message_texts), 0,
                          "Should have at least one message")
        
        # First message should be about fireball explosion
        self.assertIn("fireball", message_texts[0].lower(),
                     "First message should mention fireball")
    
    def test_lightning_cast_message_ordering(self):
        """Test that lightning cast message appears before damage message."""
        # Mock FOV to show orc is visible
        mock_fov = Mock()
        
        with patch('item_functions.show_lightning'), \
             patch('item_functions.map_is_in_fov', return_value=True):
            results = item_functions.cast_lightning(
                self.player,
                entities=self.entities,
                fov_map=mock_fov,
                damage=40,
                maximum_range=5
            )
        
        # Extract all messages
        messages = [r.get("message") for r in results if r.get("message")]
        message_texts = [m.text for m in messages]
        
        # Should have 1 message combining cast + damage
        self.assertEqual(len(message_texts), 1,
                        "Should have one message combining cast and damage")
        
        # Message should mention both striking and damage
        self.assertIn("strike", message_texts[0].lower(),
                     "Message should mention lightning striking")
        self.assertIn("damage", message_texts[0].lower(),
                     "Message should mention damage")


if __name__ == '__main__':
    unittest.main()

