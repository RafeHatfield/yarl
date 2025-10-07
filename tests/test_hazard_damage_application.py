"""Tests for hazard damage application to entities.

This module tests that ground hazards properly damage entities at the start
of each turn, including:
- Damage applied to entities standing on hazards
- Damage decays over time as hazards age
- Hazards age and expire correctly
- Entities can die from hazard damage
- Messages are generated for hazard damage
"""

import unittest
from unittest.mock import Mock, MagicMock, patch

from engine.systems.ai_system import AISystem
from engine.game_state_manager import GameState
from map_objects.game_map import GameMap
from components.ground_hazard import GroundHazard, HazardType
from components.fighter import Fighter
from entity import Entity
from game_messages import MessageLog


class TestHazardDamageApplication(unittest.TestCase):
    """Test that hazards damage entities at turn start."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.game_map = GameMap(width=40, height=40, dungeon_level=1)
        self.message_log = MessageLog(x=0, width=40, height=5)
        
        # Create player entity
        self.player = Entity(
            10, 10, '@', (255, 255, 255), 'Player',
            blocks=True, render_order=5
        )
        self.player.fighter = Fighter(hp=100, defense=5, power=10)
        
        # Create monster entity
        self.monster = Entity(
            15, 15, 'g', (0, 255, 0), 'Goblin',
            blocks=True, render_order=4
        )
        self.monster.fighter = Fighter(hp=30, defense=2, power=5)
        
        self.entities = [self.player, self.monster]
        
        # Create game state
        self.game_state = GameState(
            player=self.player,
            entities=self.entities,
            game_map=self.game_map,
            message_log=self.message_log
        )
        
        # Create AI system
        self.ai_system = AISystem()
        self.ai_system._engine = Mock()
        self.ai_system._engine.state_manager = Mock()
        self.ai_system._engine.state_manager.state = self.game_state
    
    def test_entity_takes_damage_from_hazard(self):
        """Test that an entity takes damage when standing on a hazard."""
        # Place fire hazard under player
        fire = GroundHazard(
            hazard_type=HazardType.FIRE,
            x=10, y=10,
            base_damage=10,
            remaining_turns=3,
            max_duration=3,
            source_name="Test Fire"
        )
        self.game_map.hazard_manager.add_hazard(fire)
        
        initial_hp = self.player.fighter.hp
        
        # Process hazard turn
        self.ai_system._process_hazard_turn(self.game_state)
        
        # Player should have taken damage
        self.assertLess(self.player.fighter.hp, initial_hp)
        self.assertEqual(self.player.fighter.hp, initial_hp - 10)
    
    def test_hazard_damage_decays_over_time(self):
        """Test that hazard damage decreases as it ages."""
        # Place fire hazard
        fire = GroundHazard(
            hazard_type=HazardType.FIRE,
            x=10, y=10,
            base_damage=12,  # Divisible by 3 for clean testing
            remaining_turns=3,
            max_duration=3,
            source_name="Test Fire"
        )
        self.game_map.hazard_manager.add_hazard(fire)
        
        # Turn 1: Full damage (12)
        initial_hp = self.player.fighter.hp
        self.ai_system._process_hazard_turn(self.game_state)
        damage_turn1 = initial_hp - self.player.fighter.hp
        self.assertEqual(damage_turn1, 12)  # 100% damage
        
        # Turn 2: Reduced damage (8)
        hp_turn2 = self.player.fighter.hp
        self.ai_system._process_hazard_turn(self.game_state)
        damage_turn2 = hp_turn2 - self.player.fighter.hp
        self.assertLess(damage_turn2, damage_turn1)  # Less than turn 1
        self.assertEqual(damage_turn2, 8)  # 66% damage
        
        # Turn 3: Further reduced damage (4)
        hp_turn3 = self.player.fighter.hp
        self.ai_system._process_hazard_turn(self.game_state)
        damage_turn3 = hp_turn3 - self.player.fighter.hp
        self.assertLess(damage_turn3, damage_turn2)  # Less than turn 2
        self.assertEqual(damage_turn3, 4)  # 33% damage
    
    def test_hazard_expires_after_duration(self):
        """Test that hazards disappear after their duration expires."""
        fire = GroundHazard(
            hazard_type=HazardType.FIRE,
            x=10, y=10,
            base_damage=10,
            remaining_turns=2,
            max_duration=2,
            source_name="Test Fire"
        )
        self.game_map.hazard_manager.add_hazard(fire)
        
        # Process turns until hazard expires
        self.ai_system._process_hazard_turn(self.game_state)  # Turn 1
        self.assertTrue(self.game_map.hazard_manager.has_hazard_at(10, 10))
        
        self.ai_system._process_hazard_turn(self.game_state)  # Turn 2
        self.assertFalse(self.game_map.hazard_manager.has_hazard_at(10, 10))
    
    def test_multiple_entities_take_damage(self):
        """Test that multiple entities on hazards all take damage."""
        # Place hazards under both entities
        fire1 = GroundHazard(
            hazard_type=HazardType.FIRE,
            x=10, y=10,
            base_damage=10,
            remaining_turns=3,
            max_duration=3,
            source_name="Fire 1"
        )
        fire2 = GroundHazard(
            hazard_type=HazardType.FIRE,
            x=15, y=15,
            base_damage=8,
            remaining_turns=3,
            max_duration=3,
            source_name="Fire 2"
        )
        self.game_map.hazard_manager.add_hazard(fire1)
        self.game_map.hazard_manager.add_hazard(fire2)
        
        player_initial_hp = self.player.fighter.hp
        monster_initial_hp = self.monster.fighter.hp
        
        # Process hazard turn
        self.ai_system._process_hazard_turn(self.game_state)
        
        # Both entities should have taken damage
        self.assertEqual(self.player.fighter.hp, player_initial_hp - 10)
        self.assertEqual(self.monster.fighter.hp, monster_initial_hp - 8)
    
    def test_entity_off_hazard_takes_no_damage(self):
        """Test that entities not on hazards don't take damage."""
        # Place hazard away from entities
        fire = GroundHazard(
            hazard_type=HazardType.FIRE,
            x=20, y=20,  # Far from any entity
            base_damage=10,
            remaining_turns=3,
            max_duration=3,
            source_name="Test Fire"
        )
        self.game_map.hazard_manager.add_hazard(fire)
        
        player_initial_hp = self.player.fighter.hp
        monster_initial_hp = self.monster.fighter.hp
        
        # Process hazard turn
        self.ai_system._process_hazard_turn(self.game_state)
        
        # No entities should have taken damage
        self.assertEqual(self.player.fighter.hp, player_initial_hp)
        self.assertEqual(self.monster.fighter.hp, monster_initial_hp)
    
    def test_dead_entity_takes_no_damage(self):
        """Test that dead entities don't take hazard damage."""
        # Kill the monster
        self.monster.fighter.hp = 0
        
        # Place hazard under dead monster
        fire = GroundHazard(
            hazard_type=HazardType.FIRE,
            x=15, y=15,
            base_damage=10,
            remaining_turns=3,
            max_duration=3,
            source_name="Test Fire"
        )
        self.game_map.hazard_manager.add_hazard(fire)
        
        # Process hazard turn (should not crash)
        self.ai_system._process_hazard_turn(self.game_state)
        
        # Dead monster HP stays at 0
        self.assertEqual(self.monster.fighter.hp, 0)
    
    def test_entity_dies_from_hazard_damage(self):
        """Test that hazard damage can reduce entity HP to zero."""
        # Reduce monster to low HP
        self.monster.fighter.hp = 5
        
        # Place lethal hazard
        fire = GroundHazard(
            hazard_type=HazardType.FIRE,
            x=15, y=15,
            base_damage=10,
            remaining_turns=3,
            max_duration=3,
            source_name="Test Fire"
        )
        self.game_map.hazard_manager.add_hazard(fire)
        
        # Mock death function and entity cache invalidation to avoid side effects
        with patch('death_functions.kill_monster'), \
             patch('engine.systems.ai_system.invalidate_entity_cache'):
            
            # Process hazard turn
            self.ai_system._process_hazard_turn(self.game_state)
            
            # Monster should have died (HP <= 0)
            self.assertLessEqual(self.monster.fighter.hp, 0)
    
    def test_damage_message_generated(self):
        """Test that damage messages are added to message log."""
        fire = GroundHazard(
            hazard_type=HazardType.FIRE,
            x=10, y=10,
            base_damage=10,
            remaining_turns=3,
            max_duration=3,
            source_name="Test Fire"
        )
        self.game_map.hazard_manager.add_hazard(fire)
        
        initial_message_count = len(self.message_log.messages)
        
        # Process hazard turn
        self.ai_system._process_hazard_turn(self.game_state)
        
        # Message should have been added
        self.assertGreater(len(self.message_log.messages), initial_message_count)
        
        # Check message content
        last_message = self.message_log.messages[-1].text
        self.assertIn("Fire", last_message)
        self.assertIn("10", last_message)  # Damage amount
    
    def test_poison_gas_damage(self):
        """Test that poison gas hazards work correctly."""
        gas = GroundHazard(
            hazard_type=HazardType.POISON_GAS,
            x=10, y=10,
            base_damage=5,
            remaining_turns=4,
            max_duration=4,
            source_name="Test Gas"
        )
        self.game_map.hazard_manager.add_hazard(gas)
        
        initial_hp = self.player.fighter.hp
        
        # Process hazard turn
        self.ai_system._process_hazard_turn(self.game_state)
        
        # Player should have taken damage
        self.assertEqual(self.player.fighter.hp, initial_hp - 5)
        
        # Check message mentions poison gas
        last_message = self.message_log.messages[-1].text
        self.assertIn("Poison Gas", last_message)
    
    def test_player_death_from_hazard(self):
        """Test that hazard damage can reduce player HP to zero."""
        # Reduce player to low HP
        self.player.fighter.hp = 5
        
        # Place lethal hazard
        fire = GroundHazard(
            hazard_type=HazardType.FIRE,
            x=10, y=10,
            base_damage=10,
            remaining_turns=3,
            max_duration=3,
            source_name="Test Fire"
        )
        self.game_map.hazard_manager.add_hazard(fire)
        
        initial_hp = self.player.fighter.hp
        
        # Process hazard turn
        self.ai_system._process_hazard_turn(self.game_state)
        
        # Player should have taken lethal damage (HP <= 0)
        self.assertLessEqual(self.player.fighter.hp, 0)
        self.assertLess(self.player.fighter.hp, initial_hp)


class TestHazardAgingWithoutEntities(unittest.TestCase):
    """Test hazard aging when no entities are affected."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.game_map = GameMap(width=40, height=40, dungeon_level=1)
        self.game_state = GameState(
            player=None,
            entities=[],
            game_map=self.game_map,
            message_log=None
        )
        
        self.ai_system = AISystem()
        self.ai_system._engine = Mock()
    
    def test_hazards_age_without_entities(self):
        """Test that hazards age even if no entities are on them."""
        fire = GroundHazard(
            hazard_type=HazardType.FIRE,
            x=10, y=10,
            base_damage=10,
            remaining_turns=3,
            max_duration=3,
            source_name="Test Fire"
        )
        self.game_map.hazard_manager.add_hazard(fire)
        
        # Process turn
        self.ai_system._process_hazard_turn(self.game_state)
        
        # Hazard should have aged
        hazard = self.game_map.hazard_manager.get_hazard_at(10, 10)
        self.assertIsNotNone(hazard)
        self.assertEqual(hazard.remaining_turns, 2)  # Aged from 3 to 2


if __name__ == '__main__':
    unittest.main()
