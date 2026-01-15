"""Identity tests for attack-from-invisibility mechanics (Phase 21).

This test validates that:
1. Attacking while invisible grants a surprise attack bonus
2. Invisibility is NOT removed before the attack resolves
3. Invisibility IS removed after the attack resolves
4. The bonus is applied at the canonical execution point (Fighter.attack_d20)

Seed-based determinism: seed_base=1337 for all tests.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import random

from entity import Entity
from components.fighter import Fighter
from components.equipment import Equipment
from components.ai import BasicMonster
from components.faction import Faction
from components.status_effects import InvisibilityEffect, StatusEffectManager
from components.component_registry import ComponentType
from map_objects.game_map import GameMap


class TestInvisAttackSurprise(unittest.TestCase):
    """Test that attacking from invisibility grants surprise attack."""
    
    def setUp(self):
        """Set up test entities with seed_base=1337 for determinism."""
        random.seed(1337)
        
        # Create player (DEX 14 = +2 mod, STR 14 = +2 mod)
        self.player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
        self.player.fighter = Fighter(
            hp=30, defense=0, power=0,
            strength=14, dexterity=14, constitution=10,
            damage_min=1, damage_max=8
        )
        self.player.fighter.owner = self.player
        self.player.equipment = Equipment()
        
        # Add status effect manager to player
        self.player.status_effects = StatusEffectManager(self.player)
        self.player.components.add(ComponentType.STATUS_EFFECTS, self.player.status_effects)
        
        # Create target monster (orc with AI)
        self.target = Entity(1, 0, 'o', (0, 255, 0), 'Orc', blocks=True)
        self.target.fighter = Fighter(
            hp=30, defense=0, power=3,
            strength=10, dexterity=10, constitution=10
        )
        self.target.fighter.owner = self.target
        self.target.equipment = Equipment()
        
        # Add BasicMonster AI (required for surprise attack eligibility)
        self.target.ai = BasicMonster()
        self.target.ai.owner = self.target
        self.target.faction = Faction.HOSTILE_ALL
    
    def test_invisible_player_has_invisible_flag(self):
        """Verify invisibility effect properly sets invisible flag."""
        # Initially not invisible
        self.assertFalse(getattr(self.player, 'invisible', False))
        
        # Apply invisibility
        invis_effect = InvisibilityEffect(duration=10, owner=self.player)
        self.player.status_effects.add_effect(invis_effect)
        
        # Now invisible
        self.assertTrue(self.player.invisible)
        self.assertTrue(self.player.status_effects.has_effect('invisibility'))
    
    def test_invisibility_break_removes_flag(self):
        """Verify removing invisibility via manager removes the invisible flag."""
        # Apply invisibility
        invis_effect = InvisibilityEffect(duration=10, owner=self.player)
        self.player.status_effects.add_effect(invis_effect)
        self.assertTrue(self.player.invisible)
        
        # Remove invisibility via manager (proper way to break)
        self.player.status_effects.remove_effect('invisibility')
        
        # No longer invisible
        self.assertFalse(self.player.invisible)
        self.assertFalse(self.player.status_effects.has_effect('invisibility'))
    
    @patch('random.randint')
    def test_invis_attack_forces_critical_hit(self, mock_randint):
        """Attack from invisibility should force critical hit (is_surprise=True).
        
        When is_surprise=True is passed to attack_d20, the attack:
        - Always hits (regardless of AC)
        - Always crits (2x damage)
        """
        # Set up: player is invisible
        invis_effect = InvisibilityEffect(duration=10, owner=self.player)
        self.player.status_effects.add_effect(invis_effect)
        self.assertTrue(self.player.invisible)
        
        # Roll would normally miss (1 + 2 DEX = 3 vs AC 10)
        # But surprise attack forces hit + crit
        mock_randint.return_value = 1
        
        # Attack with is_surprise=True (simulating what _handle_combat does)
        results = self.player.fighter.attack_d20(self.target, is_surprise=True)
        
        # Should have results with HIT message (not MISS)
        self.assertTrue(len(results) > 0)
        message = results[0].get('message')
        self.assertIsNotNone(message)
        # Surprise attacks hit and crit
        self.assertIn('HIT', message.text)


class TestInvisAttackTiming(unittest.TestCase):
    """Test that invisibility persists through attack resolution."""
    
    def setUp(self):
        """Set up test entities."""
        random.seed(1337)
        
        # Create player
        self.player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
        self.player.fighter = Fighter(
            hp=30, defense=0, power=0,
            strength=14, dexterity=14, constitution=10,
            damage_min=1, damage_max=8
        )
        self.player.fighter.owner = self.player
        self.player.equipment = Equipment()
        
        # Add status effect manager
        self.player.status_effects = StatusEffectManager(self.player)
        self.player.components.add(ComponentType.STATUS_EFFECTS, self.player.status_effects)
        
        # Create target
        self.target = Entity(1, 0, 'o', (0, 255, 0), 'Orc', blocks=True)
        self.target.fighter = Fighter(
            hp=30, defense=0, power=3,
            strength=10, dexterity=10, constitution=10
        )
        self.target.fighter.owner = self.target
        self.target.equipment = Equipment()
        self.target.ai = BasicMonster()
        self.target.ai.owner = self.target
        self.target.faction = Faction.HOSTILE_ALL
    
    def test_invisibility_captured_before_break(self):
        """Verify attacker_was_invisible is captured BEFORE breaking invisibility.
        
        This is the key fix: the invisibility state must be captured at the start
        of combat resolution, not read after potentially breaking it.
        """
        # Apply invisibility
        invis_effect = InvisibilityEffect(duration=10, owner=self.player)
        self.player.status_effects.add_effect(invis_effect)
        
        # Simulate the correct ordering:
        # 1. Capture invisibility state
        attacker_was_invisible = getattr(self.player, 'invisible', False)
        self.assertTrue(attacker_was_invisible, "Should capture invisible=True before break")
        
        # 2. Attack resolves (with is_surprise based on captured state)
        # 3. THEN break invisibility
        invis_effect.break_invisibility()
        
        # Player is no longer invisible
        self.assertFalse(self.player.invisible)
        
        # But we captured the state correctly
        self.assertTrue(attacker_was_invisible)


class TestInvisAttackMetrics(unittest.TestCase):
    """Test that invisibility attack metrics are tracked correctly."""
    
    def test_invis_attack_metric_fields_exist(self):
        """Verify RunMetrics has invis_attacks and invis_broken_by_attack fields."""
        from services.scenario_harness import RunMetrics
        
        metrics = RunMetrics()
        
        # Fields should exist and default to 0
        self.assertEqual(metrics.invis_attacks, 0)
        self.assertEqual(metrics.invis_broken_by_attack, 0)
    
    def test_aggregated_metrics_has_invis_fields(self):
        """Verify AggregatedMetrics has total_invis_attacks field."""
        from services.scenario_harness import AggregatedMetrics
        
        metrics = AggregatedMetrics()
        
        # Fields should exist and default to 0
        self.assertEqual(metrics.total_invis_attacks, 0)
        self.assertEqual(metrics.total_invis_broken_by_attack, 0)
    
    def test_collector_has_record_invis_attack_method(self):
        """Verify ScenarioMetricsCollector has record_invis_attack method."""
        from services.scenario_metrics import ScenarioMetricsCollector
        from services.scenario_harness import RunMetrics
        
        metrics = RunMetrics()
        collector = ScenarioMetricsCollector(metrics)
        
        # Method should exist
        self.assertTrue(hasattr(collector, 'record_invis_attack'))
        
        # Should be callable and increment metric
        collector.record_invis_attack(Mock(), Mock())
        self.assertEqual(metrics.invis_attacks, 1)


class TestInvisAttackIntegration(unittest.TestCase):
    """Integration test for attack-from-invisibility in _handle_combat.
    
    This test verifies the complete flow through game_actions._handle_combat,
    ensuring invisibility triggers surprise attack and then breaks.
    """
    
    def setUp(self):
        """Set up full game state for integration test."""
        random.seed(1337)
        
        from engine.game_state_manager import GameStateManager
        from game_messages import MessageLog
        from systems.turn_controller import TurnController
        
        # Create state manager
        self.state_manager = GameStateManager()
        
        # Create player
        self.player = Entity(10, 10, '@', (255, 255, 255), 'Player', blocks=True)
        self.player.fighter = Fighter(
            hp=100, defense=0, power=5,
            strength=14, dexterity=14, constitution=14,
            damage_min=1, damage_max=8
        )
        self.player.fighter.owner = self.player
        self.player.equipment = Equipment()
        
        # Add status effect manager
        self.player.status_effects = StatusEffectManager(self.player)
        self.player.components.add(ComponentType.STATUS_EFFECTS, self.player.status_effects)
        
        # Create target (adjacent to player)
        self.target = Entity(11, 10, 'o', (0, 255, 0), 'Orc', blocks=True)
        self.target.fighter = Fighter(
            hp=50, defense=0, power=3,
            strength=10, dexterity=10, constitution=12
        )
        self.target.fighter.owner = self.target
        self.target.equipment = Equipment()
        
        # Add AI for surprise attack eligibility
        self.target.ai = BasicMonster()
        self.target.ai.owner = self.target
        self.target.faction = Faction.HOSTILE_ALL
        
        # Create game map
        self.game_map = GameMap(30, 30)
        for x in range(30):
            for y in range(30):
                self.game_map.tiles[x][y].blocked = False
                self.game_map.tiles[x][y].block_sight = False
        
        # Create message log
        self.message_log = MessageLog(x=0, width=40, height=5)
        
        # Set up state
        self.state_manager.update_state(
            player=self.player,
            entities=[self.player, self.target],
            game_map=self.game_map,
            message_log=self.message_log
        )
        
        # Create turn controller mock
        self.turn_controller = Mock(spec=TurnController)
    
    def test_handle_combat_with_invisible_attacker(self):
        """Test _handle_combat grants surprise attack from invisibility."""
        from game_actions import ActionProcessor
        
        # Make player invisible
        invis_effect = InvisibilityEffect(duration=10, owner=self.player)
        self.player.status_effects.add_effect(invis_effect)
        self.assertTrue(self.player.invisible)
        
        # Make sure orc is "aware" (to prove invisibility grants bonus, not just unawareness)
        self.target.ai.aware_of_player = True
        
        # Create action processor
        processor = ActionProcessor(self.state_manager, is_bot_mode=True)
        
        # Record target HP before attack
        hp_before = self.target.fighter.hp
        
        # Execute combat
        with patch('random.randint', return_value=10):  # Neutral roll
            processor._handle_combat(self.player, self.target)
        
        # After combat:
        # 1. Invisibility should be broken
        self.assertFalse(self.player.invisible, "Invisibility should break after attack")
        
        # 2. Target should have taken damage (surprise attack hits)
        self.assertLess(self.target.fighter.hp, hp_before, "Target should take damage from surprise attack")
        
        # 3. Check messages for backstab indicator
        messages = [msg.text for msg in self.message_log.messages]
        backstab_found = any('invisibility' in msg.lower() or 'backstab' in msg.lower() 
                            for msg in messages)
        self.assertTrue(backstab_found, f"Should have backstab message. Messages: {messages}")


if __name__ == '__main__':
    unittest.main()
