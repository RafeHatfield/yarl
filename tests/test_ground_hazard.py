"""Tests for the ground hazard system.

This module thoroughly tests all aspects of ground hazards including:
- Hazard creation and initialization
- Damage calculation and decay over time
- Aging and expiration mechanics
- Manager operations (add, remove, query)
- Serialization for save/load
- Visual properties for rendering

Test Strategy:
- Test each component in isolation first
- Test integration between components
- Test edge cases (0 damage, negative turns, etc.)
- Test all hazard types
"""

import unittest
from components.ground_hazard import (
    GroundHazard,
    GroundHazardManager,
    HazardType
)


class TestGroundHazardCreation(unittest.TestCase):
    """Test hazard initialization and basic properties."""
    
    def test_fire_hazard_creation(self):
        """Test creating a fire hazard with all properties."""
        hazard = GroundHazard(
            hazard_type=HazardType.FIRE,
            x=10,
            y=15,
            base_damage=10,
            remaining_turns=3,
            max_duration=3,
            source_name="Fireball"
        )
        
        self.assertEqual(hazard.hazard_type, HazardType.FIRE)
        self.assertEqual(hazard.x, 10)
        self.assertEqual(hazard.y, 15)
        self.assertEqual(hazard.base_damage, 10)
        self.assertEqual(hazard.remaining_turns, 3)
        self.assertEqual(hazard.max_duration, 3)
        self.assertEqual(hazard.source_name, "Fireball")
    
    def test_poison_gas_hazard_creation(self):
        """Test creating a poison gas hazard."""
        hazard = GroundHazard(
            hazard_type=HazardType.POISON_GAS,
            x=5,
            y=5,
            base_damage=5,
            remaining_turns=4,
            max_duration=4,
            source_name="Dragon Fart"
        )
        
        self.assertEqual(hazard.hazard_type, HazardType.POISON_GAS)
        self.assertEqual(hazard.base_damage, 5)
        self.assertEqual(hazard.remaining_turns, 4)
    
    def test_default_source_name(self):
        """Test that source_name has a default value."""
        hazard = GroundHazard(
            hazard_type=HazardType.FIRE,
            x=0,
            y=0,
            base_damage=10,
            remaining_turns=3,
            max_duration=3
        )
        
        self.assertEqual(hazard.source_name, "Unknown")


class TestGroundHazardDamage(unittest.TestCase):
    """Test damage calculation and decay mechanics."""
    
    def test_full_damage_on_first_turn(self):
        """Test that hazard deals full damage when fresh."""
        hazard = GroundHazard(
            HazardType.FIRE, 0, 0,
            base_damage=10,
            remaining_turns=3,
            max_duration=3
        )
        
        self.assertEqual(hazard.get_current_damage(), 10)
    
    def test_damage_decay_over_time(self):
        """Test that damage decays linearly as hazard ages."""
        hazard = GroundHazard(
            HazardType.FIRE, 0, 0,
            base_damage=9,
            remaining_turns=3,
            max_duration=3
        )
        
        # Turn 1: 100% damage
        self.assertEqual(hazard.get_current_damage(), 9)
        
        # Turn 2: 66% damage
        hazard.remaining_turns = 2
        self.assertEqual(hazard.get_current_damage(), 6)
        
        # Turn 3: 33% damage
        hazard.remaining_turns = 1
        self.assertEqual(hazard.get_current_damage(), 3)
        
        # Expired: 0 damage
        hazard.remaining_turns = 0
        self.assertEqual(hazard.get_current_damage(), 0)
    
    def test_zero_damage_when_expired(self):
        """Test that expired hazards deal no damage."""
        hazard = GroundHazard(
            HazardType.FIRE, 0, 0,
            base_damage=10,
            remaining_turns=0,
            max_duration=3
        )
        
        self.assertEqual(hazard.get_current_damage(), 0)
    
    def test_negative_remaining_turns_gives_zero_damage(self):
        """Test that negative remaining turns (edge case) gives 0 damage."""
        hazard = GroundHazard(
            HazardType.FIRE, 0, 0,
            base_damage=10,
            remaining_turns=-1,
            max_duration=3
        )
        
        self.assertEqual(hazard.get_current_damage(), 0)


class TestGroundHazardAging(unittest.TestCase):
    """Test hazard aging and expiration mechanics."""
    
    def test_age_one_turn_decrements_counter(self):
        """Test that aging decrements remaining_turns."""
        hazard = GroundHazard(
            HazardType.FIRE, 0, 0,
            base_damage=10,
            remaining_turns=3,
            max_duration=3
        )
        
        self.assertEqual(hazard.remaining_turns, 3)
        hazard.age_one_turn()
        self.assertEqual(hazard.remaining_turns, 2)
        hazard.age_one_turn()
        self.assertEqual(hazard.remaining_turns, 1)
    
    def test_age_one_turn_returns_true_while_active(self):
        """Test that age_one_turn returns True while hazard is active."""
        hazard = GroundHazard(
            HazardType.FIRE, 0, 0,
            base_damage=10,
            remaining_turns=2,
            max_duration=3
        )
        
        self.assertTrue(hazard.age_one_turn())  # 2 → 1
        self.assertFalse(hazard.age_one_turn())  # 1 → 0 (expired)
    
    def test_age_one_turn_returns_false_when_expires(self):
        """Test that age_one_turn returns False when hazard expires."""
        hazard = GroundHazard(
            HazardType.FIRE, 0, 0,
            base_damage=10,
            remaining_turns=1,
            max_duration=3
        )
        
        result = hazard.age_one_turn()
        self.assertFalse(result)
        self.assertEqual(hazard.remaining_turns, 0)
    
    def test_is_expired_check(self):
        """Test the is_expired() method."""
        hazard = GroundHazard(
            HazardType.FIRE, 0, 0,
            base_damage=10,
            remaining_turns=1,
            max_duration=3
        )
        
        self.assertFalse(hazard.is_expired())
        hazard.age_one_turn()
        self.assertTrue(hazard.is_expired())
    
    def test_aging_beyond_zero(self):
        """Test that aging below zero is handled gracefully."""
        hazard = GroundHazard(
            HazardType.FIRE, 0, 0,
            base_damage=10,
            remaining_turns=0,
            max_duration=3
        )
        
        # Already expired
        self.assertTrue(hazard.is_expired())
        
        # Aging further should not cause errors
        result = hazard.age_one_turn()
        self.assertFalse(result)
        self.assertEqual(hazard.remaining_turns, -1)


class TestGroundHazardVisuals(unittest.TestCase):
    """Test visual properties for rendering."""
    
    def test_visual_intensity_full_when_fresh(self):
        """Test that fresh hazards have full visual intensity."""
        hazard = GroundHazard(
            HazardType.FIRE, 0, 0,
            base_damage=10,
            remaining_turns=3,
            max_duration=3
        )
        
        self.assertAlmostEqual(hazard.get_visual_intensity(), 1.0)
    
    def test_visual_intensity_decays_over_time(self):
        """Test that visual intensity decays as hazard ages."""
        hazard = GroundHazard(
            HazardType.FIRE, 0, 0,
            base_damage=10,
            remaining_turns=3,
            max_duration=3
        )
        
        # Turn 1: 100%
        self.assertAlmostEqual(hazard.get_visual_intensity(), 1.0)
        
        # Turn 2: 66%
        hazard.remaining_turns = 2
        self.assertAlmostEqual(hazard.get_visual_intensity(), 0.666, places=2)
        
        # Turn 3: 33%
        hazard.remaining_turns = 1
        self.assertAlmostEqual(hazard.get_visual_intensity(), 0.333, places=2)
        
        # Expired: 0%
        hazard.remaining_turns = 0
        self.assertAlmostEqual(hazard.get_visual_intensity(), 0.0)
    
    def test_fire_hazard_color(self):
        """Test that fire hazards return correct color."""
        hazard = GroundHazard(
            HazardType.FIRE, 0, 0,
            base_damage=10,
            remaining_turns=3,
            max_duration=3
        )
        
        color = hazard.get_color()
        self.assertEqual(color, (255, 100, 0))  # Orange-red
    
    def test_poison_gas_hazard_color(self):
        """Test that poison gas hazards return correct color."""
        hazard = GroundHazard(
            HazardType.POISON_GAS, 0, 0,
            base_damage=5,
            remaining_turns=4,
            max_duration=4
        )
        
        color = hazard.get_color()
        self.assertEqual(color, (100, 200, 50))  # Sickly green


class TestGroundHazardManager(unittest.TestCase):
    """Test the hazard manager."""
    
    def setUp(self):
        """Create a fresh manager for each test."""
        self.manager = GroundHazardManager()
    
    def test_manager_starts_empty(self):
        """Test that new managers have no hazards."""
        self.assertEqual(len(self.manager.hazards), 0)
        self.assertEqual(len(self.manager.get_all_hazards()), 0)
    
    def test_add_hazard(self):
        """Test adding a hazard to the manager."""
        hazard = GroundHazard(
            HazardType.FIRE, 5, 5,
            base_damage=10,
            remaining_turns=3,
            max_duration=3
        )
        
        self.manager.add_hazard(hazard)
        
        self.assertEqual(len(self.manager.hazards), 1)
        self.assertTrue(self.manager.has_hazard_at(5, 5))
    
    def test_add_multiple_hazards_different_positions(self):
        """Test adding multiple hazards at different positions."""
        fire = GroundHazard(HazardType.FIRE, 5, 5, 10, 3, 3)
        gas = GroundHazard(HazardType.POISON_GAS, 6, 6, 5, 4, 4)
        
        self.manager.add_hazard(fire)
        self.manager.add_hazard(gas)
        
        self.assertEqual(len(self.manager.hazards), 2)
        self.assertTrue(self.manager.has_hazard_at(5, 5))
        self.assertTrue(self.manager.has_hazard_at(6, 6))
    
    def test_add_hazard_replaces_existing(self):
        """Test that adding to same position replaces old hazard (no stacking)."""
        fire1 = GroundHazard(HazardType.FIRE, 5, 5, 10, 3, 3, "First")
        fire2 = GroundHazard(HazardType.FIRE, 5, 5, 20, 3, 3, "Second")
        
        self.manager.add_hazard(fire1)
        self.assertEqual(self.manager.get_hazard_at(5, 5).source_name, "First")
        
        self.manager.add_hazard(fire2)
        self.assertEqual(len(self.manager.hazards), 1)  # Still just 1
        self.assertEqual(self.manager.get_hazard_at(5, 5).source_name, "Second")
    
    def test_get_hazard_at(self):
        """Test retrieving a hazard by position."""
        hazard = GroundHazard(HazardType.FIRE, 10, 15, 10, 3, 3)
        self.manager.add_hazard(hazard)
        
        retrieved = self.manager.get_hazard_at(10, 15)
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.x, 10)
        self.assertEqual(retrieved.y, 15)
        self.assertEqual(retrieved.base_damage, 10)
    
    def test_get_hazard_at_empty_position(self):
        """Test that get_hazard_at returns None for empty positions."""
        result = self.manager.get_hazard_at(100, 100)
        self.assertIsNone(result)
    
    def test_has_hazard_at(self):
        """Test checking if a hazard exists at a position."""
        self.assertFalse(self.manager.has_hazard_at(5, 5))
        
        hazard = GroundHazard(HazardType.FIRE, 5, 5, 10, 3, 3)
        self.manager.add_hazard(hazard)
        
        self.assertTrue(self.manager.has_hazard_at(5, 5))
        self.assertFalse(self.manager.has_hazard_at(6, 6))
    
    def test_remove_hazard_at(self):
        """Test removing a hazard by position."""
        hazard = GroundHazard(HazardType.FIRE, 5, 5, 10, 3, 3)
        self.manager.add_hazard(hazard)
        
        result = self.manager.remove_hazard_at(5, 5)
        
        self.assertTrue(result)
        self.assertFalse(self.manager.has_hazard_at(5, 5))
        self.assertEqual(len(self.manager.hazards), 0)
    
    def test_remove_nonexistent_hazard(self):
        """Test that removing non-existent hazard returns False."""
        result = self.manager.remove_hazard_at(100, 100)
        self.assertFalse(result)
    
    def test_age_all_hazards(self):
        """Test aging all hazards simultaneously."""
        fire = GroundHazard(HazardType.FIRE, 5, 5, 10, 2, 3)
        gas = GroundHazard(HazardType.POISON_GAS, 6, 6, 5, 3, 4)
        
        self.manager.add_hazard(fire)
        self.manager.add_hazard(gas)
        
        expired = self.manager.age_all_hazards()
        
        # No hazards expired yet
        self.assertEqual(len(expired), 0)
        self.assertEqual(len(self.manager.hazards), 2)
        self.assertEqual(self.manager.get_hazard_at(5, 5).remaining_turns, 1)
        self.assertEqual(self.manager.get_hazard_at(6, 6).remaining_turns, 2)
    
    def test_age_all_hazards_removes_expired(self):
        """Test that expired hazards are automatically removed."""
        fire = GroundHazard(HazardType.FIRE, 5, 5, 10, 1, 3)
        gas = GroundHazard(HazardType.POISON_GAS, 6, 6, 5, 2, 4)
        
        self.manager.add_hazard(fire)
        self.manager.add_hazard(gas)
        
        expired = self.manager.age_all_hazards()
        
        # Fire should have expired
        self.assertIn((5, 5), expired)
        self.assertFalse(self.manager.has_hazard_at(5, 5))
        self.assertTrue(self.manager.has_hazard_at(6, 6))  # Gas still active
    
    def test_get_all_hazards(self):
        """Test getting list of all hazards."""
        fire = GroundHazard(HazardType.FIRE, 5, 5, 10, 3, 3)
        gas = GroundHazard(HazardType.POISON_GAS, 6, 6, 5, 4, 4)
        
        self.manager.add_hazard(fire)
        self.manager.add_hazard(gas)
        
        all_hazards = self.manager.get_all_hazards()
        
        self.assertEqual(len(all_hazards), 2)
        self.assertIn(fire, all_hazards)
        self.assertIn(gas, all_hazards)
    
    def test_clear_all(self):
        """Test clearing all hazards."""
        fire = GroundHazard(HazardType.FIRE, 5, 5, 10, 3, 3)
        gas = GroundHazard(HazardType.POISON_GAS, 6, 6, 5, 4, 4)
        
        self.manager.add_hazard(fire)
        self.manager.add_hazard(gas)
        
        self.manager.clear_all()
        
        self.assertEqual(len(self.manager.hazards), 0)
        self.assertFalse(self.manager.has_hazard_at(5, 5))
        self.assertFalse(self.manager.has_hazard_at(6, 6))


class TestGroundHazardSerialization(unittest.TestCase):
    """Test save/load serialization."""
    
    def test_to_dict(self):
        """Test serializing hazards to dictionary."""
        manager = GroundHazardManager()
        fire = GroundHazard(
            HazardType.FIRE, 5, 5, 10, 3, 3, "Fireball"
        )
        manager.add_hazard(fire)
        
        data = manager.to_dict()
        
        self.assertIn('hazards', data)
        self.assertEqual(len(data['hazards']), 1)
        
        hazard_data = data['hazards'][0]
        self.assertEqual(hazard_data['type'], 'FIRE')
        self.assertEqual(hazard_data['x'], 5)
        self.assertEqual(hazard_data['y'], 5)
        self.assertEqual(hazard_data['base_damage'], 10)
        self.assertEqual(hazard_data['remaining_turns'], 3)
        self.assertEqual(hazard_data['max_duration'], 3)
        self.assertEqual(hazard_data['source_name'], 'Fireball')
    
    def test_from_dict(self):
        """Test deserializing hazards from dictionary."""
        data = {
            'hazards': [
                {
                    'type': 'FIRE',
                    'x': 5,
                    'y': 5,
                    'base_damage': 10,
                    'remaining_turns': 3,
                    'max_duration': 3,
                    'source_name': 'Fireball'
                },
                {
                    'type': 'POISON_GAS',
                    'x': 6,
                    'y': 6,
                    'base_damage': 5,
                    'remaining_turns': 4,
                    'max_duration': 4,
                    'source_name': 'Dragon Fart'
                }
            ]
        }
        
        manager = GroundHazardManager.from_dict(data)
        
        self.assertEqual(len(manager.hazards), 2)
        
        fire = manager.get_hazard_at(5, 5)
        self.assertIsNotNone(fire)
        self.assertEqual(fire.hazard_type, HazardType.FIRE)
        self.assertEqual(fire.base_damage, 10)
        self.assertEqual(fire.source_name, 'Fireball')
        
        gas = manager.get_hazard_at(6, 6)
        self.assertIsNotNone(gas)
        self.assertEqual(gas.hazard_type, HazardType.POISON_GAS)
        self.assertEqual(gas.base_damage, 5)
    
    def test_round_trip_serialization(self):
        """Test that save/load preserves all data."""
        original = GroundHazardManager()
        fire = GroundHazard(HazardType.FIRE, 10, 15, 10, 2, 3, "Test")
        gas = GroundHazard(HazardType.POISON_GAS, 20, 25, 5, 3, 4, "Test2")
        original.add_hazard(fire)
        original.add_hazard(gas)
        
        # Serialize
        data = original.to_dict()
        
        # Deserialize
        loaded = GroundHazardManager.from_dict(data)
        
        # Verify all data preserved
        self.assertEqual(len(loaded.hazards), 2)
        
        loaded_fire = loaded.get_hazard_at(10, 15)
        self.assertEqual(loaded_fire.base_damage, 10)
        self.assertEqual(loaded_fire.remaining_turns, 2)
        self.assertEqual(loaded_fire.max_duration, 3)
        
        loaded_gas = loaded.get_hazard_at(20, 25)
        self.assertEqual(loaded_gas.base_damage, 5)
        self.assertEqual(loaded_gas.remaining_turns, 3)
    
    def test_empty_manager_serialization(self):
        """Test serializing empty manager."""
        manager = GroundHazardManager()
        data = manager.to_dict()
        
        self.assertEqual(len(data['hazards']), 0)
        
        loaded = GroundHazardManager.from_dict(data)
        self.assertEqual(len(loaded.hazards), 0)


if __name__ == '__main__':
    unittest.main()
