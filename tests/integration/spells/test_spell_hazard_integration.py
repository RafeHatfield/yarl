"""Integration tests for spell hazard creation.

This module tests that area-of-effect spells properly create ground hazards
when cast, including:
- Fireball creates fire hazards
- Dragon Fart creates poison gas hazards
- Hazards have correct properties (damage, duration, position)
- Hazards are added to game map's hazard manager
"""

import unittest
from unittest.mock import Mock, patch

from item_functions import cast_fireball, cast_dragon_fart
from map_objects.game_map import GameMap
from components.ground_hazard import HazardType
from entity import Entity


class TestFireballHazardCreation(unittest.TestCase):
    """Test that casting Fireball creates fire hazards."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.game_map = GameMap(width=40, height=40, dungeon_level=1)
        self.entities = []
        
        # Mock FOV map
        self.fov_map = Mock()
        
    @patch('item_functions.map_is_in_fov')
    @patch('item_functions.show_fireball')
    def test_fireball_creates_fire_hazards(self, mock_show, mock_fov):
        """Test that casting fireball creates fire hazards on all explosion tiles."""
        mock_fov.return_value = True
        
        # Cast fireball at center with radius 1
        results = cast_fireball(
            entities=self.entities,
            fov_map=self.fov_map,
            damage=25,
            radius=1,
            target_x=20,
            target_y=20,
            game_map=self.game_map
        )
        
        # Should have created hazards
        self.assertGreater(len(self.game_map.hazard_manager.hazards), 0)
        
        # Check center tile has hazard
        center_hazard = self.game_map.hazard_manager.get_hazard_at(20, 20)
        self.assertIsNotNone(center_hazard)
        self.assertEqual(center_hazard.hazard_type, HazardType.FIRE)
    
    @patch('item_functions.map_is_in_fov')
    @patch('item_functions.show_fireball')
    def test_fire_hazard_properties(self, mock_show, mock_fov):
        """Test that fire hazards have correct properties."""
        mock_fov.return_value = True
        
        cast_fireball(
            entities=self.entities,
            fov_map=self.fov_map,
            damage=25,
            radius=0,  # Just one tile
            target_x=15,
            target_y=15,
            game_map=self.game_map
        )
        
        hazard = self.game_map.hazard_manager.get_hazard_at(15, 15)
        
        # New spell system values from spell_catalog.py
        self.assertEqual(hazard.base_damage, 3)  # FIREBALL.hazard_damage
        self.assertEqual(hazard.remaining_turns, 3)  # FIREBALL.hazard_duration
        self.assertEqual(hazard.max_duration, 3)
        self.assertEqual(hazard.source_name, "Fireball")
    
    @patch('item_functions.map_is_in_fov')
    @patch('item_functions.show_fireball')
    def test_fireball_multiple_tiles(self, mock_show, mock_fov):
        """Test that fireball creates hazards on all tiles in radius."""
        mock_fov.return_value = True
        
        cast_fireball(
            entities=self.entities,
            fov_map=self.fov_map,
            damage=25,
            radius=2,
            target_x=20,
            target_y=20,
            game_map=self.game_map
        )
        
        # Should have multiple hazards in a circular pattern
        hazard_count = len(self.game_map.hazard_manager.hazards)
        self.assertGreater(hazard_count, 5)  # At least 5 tiles in radius 2
        
        # Check adjacent tiles
        self.assertTrue(self.game_map.hazard_manager.has_hazard_at(20, 20))  # Center
        self.assertTrue(self.game_map.hazard_manager.has_hazard_at(21, 20))  # Right
        self.assertTrue(self.game_map.hazard_manager.has_hazard_at(20, 21))  # Down
    
    @patch('item_functions.map_is_in_fov')
    @patch('item_functions.show_fireball')
    def test_fireball_without_game_map(self, mock_show, mock_fov):
        """Test that fireball works even if game_map is not provided."""
        mock_fov.return_value = True
        
        # Should not crash when game_map is None
        results = cast_fireball(
            entities=self.entities,
            fov_map=self.fov_map,
            damage=25,
            radius=1,
            target_x=20,
            target_y=20,
            game_map=None  # No map provided
        )
        
        # Should still return results (just no hazards created)
        self.assertIsNotNone(results)
        self.assertGreater(len(results), 0)
    
    @patch('item_functions.map_is_in_fov')
    @patch('item_functions.show_fireball')
    def test_fireball_replaces_existing_hazard(self, mock_show, mock_fov):
        """Test that new fireball replaces existing hazard (no stacking)."""
        mock_fov.return_value = True
        
        # Cast first fireball
        cast_fireball(
            entities=self.entities,
            fov_map=self.fov_map,
            damage=25,
            radius=0,
            target_x=15,
            target_y=15,
            game_map=self.game_map
        )
        
        first_hazard = self.game_map.hazard_manager.get_hazard_at(15, 15)
        first_turns = first_hazard.remaining_turns
        
        # Age the hazard
        first_hazard.age_one_turn()
        
        # Cast second fireball at same location
        cast_fireball(
            entities=self.entities,
            fov_map=self.fov_map,
            damage=25,
            radius=0,
            target_x=15,
            target_y=15,
            game_map=self.game_map
        )
        
        # Should have replaced with fresh hazard
        new_hazard = self.game_map.hazard_manager.get_hazard_at(15, 15)
        self.assertEqual(new_hazard.remaining_turns, 3)  # Fresh, not aged (FIREBALL.hazard_duration)


class TestDragonFartHazardCreation(unittest.TestCase):
    """Test that casting Dragon Fart creates poison gas hazards.
    
    Phase 20 Scroll Modernization: Dragon Fart now routes through SpellExecutor
    via cast_spell_by_id. This requires proper fov_map setup.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.game_map = GameMap(width=40, height=40, dungeon_level=1)
        
        # Create caster entity with proper components
        self.caster = Entity(
            x=20, y=20, char='@', color=(255, 255, 255), name="Player",
            blocks=True, render_order=5
        )
        
        self.entities = [self.caster]
        
        # Mock FOV map for spell system
        self.fov_map = Mock()
    
    @patch('spells.spell_catalog.show_dragon_fart')
    @patch('spells.spell_executor.map_is_in_fov')
    def test_dragon_fart_creates_poison_gas_hazards(self, mock_fov, mock_show):
        """Test that casting dragon fart creates poison gas hazards."""
        mock_fov.return_value = True
        
        results = cast_dragon_fart(
            self.caster,
            entities=self.entities,
            fov_map=self.fov_map,
            game_map=self.game_map,
            target_x=25,
            target_y=20
        )
        
        # Should have created hazards
        self.assertGreater(len(self.game_map.hazard_manager.hazards), 0)
        
        # At least one should be poison gas type
        all_hazards = self.game_map.hazard_manager.get_all_hazards()
        has_poison = any(h.hazard_type == HazardType.POISON_GAS for h in all_hazards)
        self.assertTrue(has_poison)
    
    @patch('spells.spell_catalog.show_dragon_fart')
    @patch('spells.spell_executor.map_is_in_fov')
    def test_poison_gas_hazard_properties(self, mock_fov, mock_show):
        """Test that poison gas hazards have correct properties."""
        mock_fov.return_value = True
        
        cast_dragon_fart(
            self.caster,
            entities=self.entities,
            fov_map=self.fov_map,
            game_map=self.game_map,
            target_x=25,
            target_y=20
        )
        
        # Get any poison gas hazard
        all_hazards = self.game_map.hazard_manager.get_all_hazards()
        gas_hazard = next(h for h in all_hazards if h.hazard_type == HazardType.POISON_GAS)
        
        self.assertEqual(gas_hazard.base_damage, 6)  # DRAGON_FART.hazard_damage
        self.assertEqual(gas_hazard.remaining_turns, 5)  # DRAGON_FART.hazard_duration
        self.assertEqual(gas_hazard.max_duration, 5)
        self.assertEqual(gas_hazard.source_name, "Dragon Fart")
    
    @patch('spells.spell_catalog.show_dragon_fart')
    @patch('spells.spell_executor.map_is_in_fov')
    def test_dragon_fart_cone_shape(self, mock_fov, mock_show):
        """Test that dragon fart creates hazards in a cone pattern."""
        mock_fov.return_value = True
        
        cast_dragon_fart(
            self.caster,
            entities=self.entities,
            fov_map=self.fov_map,
            game_map=self.game_map,
            target_x=28,
            target_y=20
        )
        
        # Should have multiple hazards in cone
        hazard_count = len(self.game_map.hazard_manager.hazards)
        self.assertGreater(hazard_count, 3)
        
        # Hazards should be roughly in direction of target (east)
        all_hazards = self.game_map.hazard_manager.get_all_hazards()
        # Most hazards should be to the right of caster
        hazards_east = sum(1 for h in all_hazards if h.x > self.caster.x)
        self.assertGreater(hazards_east, len(all_hazards) * 0.7)  # At least 70% east
    
    @patch('spells.spell_catalog.show_dragon_fart')
    @patch('spells.spell_executor.map_is_in_fov')
    def test_dragon_fart_without_game_map(self, mock_fov, mock_show):
        """Test that dragon fart works even if game_map is not provided."""
        mock_fov.return_value = True
        
        # Should not crash when game_map doesn't have hazard_manager
        game_map_no_manager = Mock()
        game_map_no_manager.hazard_manager = None
        
        results = cast_dragon_fart(
            self.caster,
            entities=self.entities,
            fov_map=self.fov_map,
            game_map=game_map_no_manager,
            target_x=25,
            target_y=20
        )
        
        # Should still return results (just no hazards created)
        self.assertIsNotNone(results)


class TestHazardPersistence(unittest.TestCase):
    """Test that hazards persist across game turns."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.game_map = GameMap(width=40, height=40, dungeon_level=1)
    
    @patch('item_functions.map_is_in_fov')
    @patch('item_functions.show_fireball')
    def test_hazards_persist_after_spell_cast(self, mock_show, mock_fov):
        """Test that hazards remain on map after spell finishes."""
        mock_fov.return_value = True
        
        cast_fireball(
            entities=[],
            fov_map=Mock(),
            damage=25,
            radius=1,
            target_x=20,
            target_y=20,
            game_map=self.game_map
        )
        
        # Hazards should still be there
        self.assertGreater(len(self.game_map.hazard_manager.hazards), 0)
        
        # Check specific hazard persists
        hazard = self.game_map.hazard_manager.get_hazard_at(20, 20)
        self.assertIsNotNone(hazard)
        self.assertEqual(hazard.remaining_turns, 3)  # FIREBALL.hazard_duration


if __name__ == '__main__':
    unittest.main()
