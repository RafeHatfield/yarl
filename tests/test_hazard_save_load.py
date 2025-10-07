"""Tests for ground hazard save/load persistence.

This module tests that ground hazards are correctly saved to and loaded from
save files, ensuring players don't lose hazard state when saving mid-game.
"""

import unittest
import json
import os
from unittest.mock import Mock, patch

from map_objects.game_map import GameMap
from components.ground_hazard import GroundHazard, HazardType, GroundHazardManager
from loader_functions.data_loaders import _serialize_game_map, _deserialize_game_map


class TestHazardSerialization(unittest.TestCase):
    """Test hazard serialization and deserialization."""
    
    def test_serialize_game_map_with_hazards(self):
        """Test that game_map serialization includes hazards."""
        game_map = GameMap(width=40, height=40, dungeon_level=1)
        
        # Add some hazards
        fire = GroundHazard(
            hazard_type=HazardType.FIRE,
            x=10, y=10,
            base_damage=10,
            remaining_turns=3,
            max_duration=3,
            source_name="Fireball"
        )
        gas = GroundHazard(
            hazard_type=HazardType.POISON_GAS,
            x=15, y=15,
            base_damage=5,
            remaining_turns=4,
            max_duration=4,
            source_name="Dragon Fart"
        )
        game_map.hazard_manager.add_hazard(fire)
        game_map.hazard_manager.add_hazard(gas)
        
        # Serialize
        data = _serialize_game_map(game_map)
        
        # Should have hazards key
        self.assertIn("hazards", data)
        self.assertIn("hazards", data["hazards"])
        self.assertEqual(len(data["hazards"]["hazards"]), 2)
    
    def test_serialize_game_map_without_hazards(self):
        """Test that game_map serialization works without hazards."""
        game_map = GameMap(width=40, height=40, dungeon_level=1)
        
        # Don't add any hazards
        
        # Serialize
        data = _serialize_game_map(game_map)
        
        # Should have hazards key (empty)
        self.assertIn("hazards", data)
    
    def test_deserialize_game_map_with_hazards(self):
        """Test that game_map deserialization restores hazards."""
        # Create original map with hazards
        original_map = GameMap(width=40, height=40, dungeon_level=1)
        fire = GroundHazard(
            hazard_type=HazardType.FIRE,
            x=10, y=10,
            base_damage=10,
            remaining_turns=3,
            max_duration=3,
            source_name="Fireball"
        )
        original_map.hazard_manager.add_hazard(fire)
        
        # Serialize then deserialize
        data = _serialize_game_map(original_map)
        loaded_map = _deserialize_game_map(data)
        
        # Check hazard was restored
        self.assertTrue(loaded_map.hazard_manager.has_hazard_at(10, 10))
        hazard = loaded_map.hazard_manager.get_hazard_at(10, 10)
        self.assertEqual(hazard.hazard_type, HazardType.FIRE)
        self.assertEqual(hazard.base_damage, 10)
        self.assertEqual(hazard.remaining_turns, 3)
        self.assertEqual(hazard.max_duration, 3)
        self.assertEqual(hazard.source_name, "Fireball")
    
    def test_deserialize_game_map_without_hazards(self):
        """Test that game_map deserialization works with old saves without hazards."""
        # Create data without hazards key (old save format)
        data = {
            "width": 40,
            "height": 40,
            "dungeon_level": 1,
            "tiles": [[{"blocked": True, "block_sight": True, "explored": False} 
                      for _ in range(40)] for _ in range(40)]
        }
        
        # Should deserialize without error
        loaded_map = _deserialize_game_map(data)
        
        # Should have an empty hazard manager
        self.assertIsNotNone(loaded_map.hazard_manager)
        self.assertEqual(len(loaded_map.hazard_manager.hazards), 0)
    
    def test_hazard_roundtrip(self):
        """Test complete save/load roundtrip of hazards."""
        # Create map with multiple hazards
        game_map = GameMap(width=40, height=40, dungeon_level=1)
        
        hazards = [
            GroundHazard(HazardType.FIRE, 5, 5, 10, 3, 3, "Test1"),
            GroundHazard(HazardType.POISON_GAS, 10, 10, 5, 4, 4, "Test2"),
            GroundHazard(HazardType.FIRE, 15, 15, 8, 2, 3, "Test3"),
        ]
        
        for hazard in hazards:
            game_map.hazard_manager.add_hazard(hazard)
        
        # Serialize and deserialize
        data = _serialize_game_map(game_map)
        loaded_map = _deserialize_game_map(data)
        
        # Check all hazards restored
        self.assertEqual(len(loaded_map.hazard_manager.hazards), 3)
        self.assertTrue(loaded_map.hazard_manager.has_hazard_at(5, 5))
        self.assertTrue(loaded_map.hazard_manager.has_hazard_at(10, 10))
        self.assertTrue(loaded_map.hazard_manager.has_hazard_at(15, 15))
        
        # Check specific hazard properties
        fire = loaded_map.hazard_manager.get_hazard_at(5, 5)
        self.assertEqual(fire.hazard_type, HazardType.FIRE)
        self.assertEqual(fire.base_damage, 10)
        
        gas = loaded_map.hazard_manager.get_hazard_at(10, 10)
        self.assertEqual(gas.hazard_type, HazardType.POISON_GAS)
        self.assertEqual(gas.base_damage, 5)
        self.assertEqual(gas.remaining_turns, 4)
    
    def test_hazard_properties_preserved(self):
        """Test that all hazard properties are preserved through save/load."""
        game_map = GameMap(width=40, height=40, dungeon_level=1)
        
        # Create hazard with specific properties
        hazard = GroundHazard(
            hazard_type=HazardType.FIRE,
            x=20,
            y=25,
            base_damage=15,
            remaining_turns=2,
            max_duration=5,
            source_name="Big Fireball"
        )
        game_map.hazard_manager.add_hazard(hazard)
        
        # Roundtrip
        data = _serialize_game_map(game_map)
        loaded_map = _deserialize_game_map(data)
        
        # Verify all properties
        loaded_hazard = loaded_map.hazard_manager.get_hazard_at(20, 25)
        self.assertEqual(loaded_hazard.x, 20)
        self.assertEqual(loaded_hazard.y, 25)
        self.assertEqual(loaded_hazard.hazard_type, HazardType.FIRE)
        self.assertEqual(loaded_hazard.base_damage, 15)
        self.assertEqual(loaded_hazard.remaining_turns, 2)
        self.assertEqual(loaded_hazard.max_duration, 5)
        self.assertEqual(loaded_hazard.source_name, "Big Fireball")


if __name__ == '__main__':
    unittest.main()
