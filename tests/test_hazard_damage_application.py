"""Tests for hazard status effect application to entities.

Phase 20 Scroll Modernization: Hazards now apply status effects (BurningEffect,
PoisonEffect) instead of direct damage. Damage is dealt when the effect ticks
at the entity's turn start, routing through damage_service.

This module tests that ground hazards properly apply effects at turn start:
- Status effects applied to entities standing on hazards
- Hazards age and expire correctly
- Levitating entities are immune to ground hazards
- Messages are generated for status application
"""

import unittest
from unittest.mock import patch, Mock

from engine import GameEngine, TurnPhase
from engine.systems.environment_system import EnvironmentSystem
from map_objects.game_map import GameMap
from components.ground_hazard import GroundHazard, HazardType
from components.fighter import Fighter
from components.status_effects import StatusEffectManager, BurningEffect, PoisonEffect
from entity import Entity
from game_messages import MessageLog
from components.component_registry import ComponentType


class TestHazardStatusEffectApplication(unittest.TestCase):
    """Test that hazards apply status effects at turn start."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.game_map = GameMap(width=40, height=40, dungeon_level=1)
        self.message_log = MessageLog(x=0, width=40, height=5)
        
        # Create player entity with fighter and status_effects components
        player_fighter = Fighter(hp=100, defense=5, power=10)
        self.player = Entity(
            10, 10, '@', (255, 255, 255), 'Player',
            blocks=True, render_order=5, fighter=player_fighter
        )
        self.player.status_effects = StatusEffectManager(self.player)
        self.player.components.add(ComponentType.STATUS_EFFECTS, self.player.status_effects)
        
        # Create monster entity with fighter and status_effects components
        monster_fighter = Fighter(hp=30, defense=2, power=5)
        self.monster = Entity(
            15, 15, 'g', (0, 255, 0), 'Goblin',
            blocks=True, render_order=4, fighter=monster_fighter
        )
        self.monster.status_effects = StatusEffectManager(self.monster)
        self.monster.components.add(ComponentType.STATUS_EFFECTS, self.monster.status_effects)
        
        self.entities = [self.player, self.monster]

        # Initialize engine and register environment system
        self.engine = GameEngine()
        self.env_system = EnvironmentSystem()
        self.engine.register_system(self.env_system)

        # Populate engine game state
        self.engine.state_manager.update_state(
            player=self.player,
            entities=self.entities,
            game_map=self.game_map,
            message_log=self.message_log,
        )
        self.game_state = self.engine.state_manager.state
        self.turn_manager = self.engine.turn_manager

    def _run_environment_phase(self):
        """Advance the turn manager through the environment phase."""
        self.turn_manager.advance_turn(to_phase=TurnPhase.ENVIRONMENT)
        self.turn_manager.advance_turn(to_phase=TurnPhase.PLAYER)
    
    def test_fire_hazard_applies_burning_effect(self):
        """Test that standing on fire applies BurningEffect."""
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
        
        # Verify no burning effect initially
        self.assertFalse(self.player.has_status_effect('burning'))
        
        # Process hazard turn
        self._run_environment_phase()
        
        # Player should now have burning effect
        self.assertTrue(self.player.has_status_effect('burning'))
    
    def test_poison_hazard_applies_poison_effect(self):
        """Test that standing on poison gas applies PoisonEffect."""
        gas = GroundHazard(
            hazard_type=HazardType.POISON_GAS,
            x=10, y=10,
            base_damage=5,
            remaining_turns=4,
            max_duration=4,
            source_name="Test Gas"
        )
        self.game_map.hazard_manager.add_hazard(gas)
        
        # Verify no poison effect initially
        self.assertFalse(self.player.has_status_effect('poison'))
        
        # Process hazard turn
        self._run_environment_phase()
        
        # Player should now have poison effect
        self.assertTrue(self.player.has_status_effect('poison'))
    
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
        self._run_environment_phase()  # Turn 1
        self.assertTrue(self.game_map.hazard_manager.has_hazard_at(10, 10))
        
        self._run_environment_phase()  # Turn 2
        self.assertFalse(self.game_map.hazard_manager.has_hazard_at(10, 10))
    
    def test_multiple_entities_get_effects(self):
        """Test that multiple entities on hazards all receive effects."""
        # Place hazards under both entities
        fire1 = GroundHazard(
            hazard_type=HazardType.FIRE,
            x=10, y=10,
            base_damage=10,
            remaining_turns=3,
            max_duration=3,
            source_name="Fire 1"
        )
        gas2 = GroundHazard(
            hazard_type=HazardType.POISON_GAS,
            x=15, y=15,
            base_damage=8,
            remaining_turns=3,
            max_duration=3,
            source_name="Gas 2"
        )
        self.game_map.hazard_manager.add_hazard(fire1)
        self.game_map.hazard_manager.add_hazard(gas2)
        
        # Process hazard turn
        self._run_environment_phase()
        
        # Both entities should have received effects
        self.assertTrue(self.player.has_status_effect('burning'))
        self.assertTrue(self.monster.has_status_effect('poison'))
    
    def test_entity_off_hazard_gets_no_effect(self):
        """Test that entities not on hazards don't get effects."""
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
        
        # Process hazard turn
        self._run_environment_phase()
        
        # No entities should have effects
        self.assertFalse(self.player.has_status_effect('burning'))
        self.assertFalse(self.monster.has_status_effect('burning'))
    
    def test_dead_entity_gets_no_effect(self):
        """Test that dead entities don't receive hazard effects."""
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
        self._run_environment_phase()
        
        # Dead monster should not have effect
        self.assertFalse(self.monster.has_status_effect('burning'))
    
    def test_levitating_entity_immune_to_hazard(self):
        """Test that levitating entities are immune to ground hazards."""
        from components.status_effects import LevitationEffect
        
        # Give player levitation
        lev_effect = LevitationEffect(duration=10, owner=self.player)
        self.player.status_effects.add_effect(lev_effect)
        
        # Place hazard under player
        fire = GroundHazard(
            hazard_type=HazardType.FIRE,
            x=10, y=10,
            base_damage=10,
            remaining_turns=3,
            max_duration=3,
            source_name="Test Fire"
        )
        self.game_map.hazard_manager.add_hazard(fire)
        
        # Process hazard turn
        self._run_environment_phase()
        
        # Levitating player should not get burning effect
        self.assertFalse(self.player.has_status_effect('burning'))


class TestHazardAgingWithoutEntities(unittest.TestCase):
    """Test hazard aging when no entities are affected."""

    def setUp(self):
        """Set up test fixtures."""
        self.game_map = GameMap(width=40, height=40, dungeon_level=1)
        self.engine = GameEngine()
        self.env_system = EnvironmentSystem()
        self.engine.register_system(self.env_system)

        self.engine.state_manager.update_state(
            player=None,
            entities=[],
            game_map=self.game_map,
            message_log=None,
        )
        self.turn_manager = self.engine.turn_manager

    def _run_environment_phase(self):
        """Advance through the environment phase to age hazards."""
        self.turn_manager.advance_turn(to_phase=TurnPhase.ENVIRONMENT)
        self.turn_manager.advance_turn(to_phase=TurnPhase.PLAYER)
    
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
        self._run_environment_phase()
        
        # Hazard should have aged
        hazard = self.game_map.hazard_manager.get_hazard_at(10, 10)
        self.assertIsNotNone(hazard)
        self.assertEqual(hazard.remaining_turns, 2)  # Aged from 3 to 2


if __name__ == '__main__':
    unittest.main()
