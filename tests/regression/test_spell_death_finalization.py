"""Regression tests for spell death finalization.

This module tests that spell-caused deaths (single-target, AoE, cone) are properly
finalized through the centralized damage service, preventing "0 HP but no death" bugs.

Background:
- Phase 18.3: Migrated spell damage to use services/damage_service.apply_damage()
- Previously: spells called Fighter.take_damage() directly and extended results
- Risk: If death results were not properly processed, entities could reach 0 HP without dying
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from entity import Entity
from components.fighter import Fighter
from components.component_registry import ComponentType
from game_states import GameStates


class TestSpellDeathFinalizationSingleTarget(unittest.TestCase):
    """Test that single-target spell damage properly finalizes deaths."""
    
    def test_spell_damage_service_kills_player_finalizes_death(self):
        """Test that spell damage through damage_service triggers finalize_player_death."""
        # Create minimal player
        player = Entity(
            x=10, y=10,
            char='@',
            color=(255, 255, 255),
            name='Player',
            fighter=Fighter(hp=30, defense=0, power=5, xp=0)
        )
        player.fighter.hp = 5  # Low HP
        
        # Create monster as caster
        monster = Entity(
            x=12, y=12,
            char='o',
            color=(255, 0, 0),
            name='Orc',
            fighter=Fighter(hp=20, defense=0, power=5, xp=35)
        )
        
        # Mock state_manager
        mock_state_manager = Mock()
        mock_state_manager.state = Mock()
        mock_state_manager.state.player = player
        mock_state_manager.state.game_map = Mock()
        mock_state_manager.state.entities = [player, monster]
        mock_state_manager.state.constants = {}
        
        # Import damage service directly
        from services.damage_service import apply_damage
        
        # Mock engine_integration.finalize_player_death to verify it's called
        with patch('engine_integration.finalize_player_death') as mock_finalize:
            # Apply spell damage that will kill the player
            results = apply_damage(
                mock_state_manager,
                player,
                10,  # More than player's 5 HP
                cause="spell:fireball",
                attacker_entity=monster
            )
            
            # Verify player died
            self.assertLessEqual(player.fighter.hp, 0, "Player should be dead after lethal spell damage")
            
            # Verify finalize_player_death was called
            mock_finalize.assert_called_once()
            call_args = mock_finalize.call_args
            self.assertEqual(call_args[0][0], mock_state_manager, "Should pass state_manager")
            self.assertIn("spell:", call_args[1].get("cause", ""), "Death cause should mention spell")
    
    def test_spell_damage_service_kills_monster_finalizes_death(self):
        """Test that spell damage through damage_service triggers kill_monster."""
        # Create player as caster
        player = Entity(
            x=10, y=10,
            char='@',
            color=(255, 255, 255),
            name='Player',
            fighter=Fighter(hp=30, defense=0, power=5, xp=0)
        )
        
        # Create monster target
        monster = Entity(
            x=12, y=12,
            char='o',
            color=(255, 0, 0),
            name='Orc',
            fighter=Fighter(hp=20, defense=0, power=5, xp=35)
        )
        monster.fighter.hp = 3  # Low HP
        
        # Mock state_manager
        mock_state_manager = Mock()
        mock_state_manager.state = Mock()
        mock_state_manager.state.player = player
        mock_state_manager.state.game_map = Mock()
        mock_state_manager.state.entities = [player, monster]
        
        # Import damage service directly
        from services.damage_service import apply_damage
        
        # Mock death_functions.kill_monster to verify it's called
        with patch('death_functions.kill_monster') as mock_kill:
            mock_kill.return_value = Mock()  # Return a mock message
            
            # Apply spell damage that will kill the monster
            results = apply_damage(
                mock_state_manager,
                monster,
                10,  # More than monster's 3 HP
                cause="spell:lightning",
                attacker_entity=player
            )
            
            # Verify monster died
            self.assertLessEqual(monster.fighter.hp, 0, "Monster should be dead after lethal spell damage")
            
            # Verify kill_monster was called
            mock_kill.assert_called_once()
            call_args = mock_kill.call_args
            self.assertEqual(call_args[0][0], monster, "Should kill the monster")


class TestSpellDeathFinalizationAoE(unittest.TestCase):
    """Test that AoE spell damage properly finalizes deaths for all targets."""
    
    def test_spell_damage_service_kills_multiple_monsters_finalizes_all(self):
        """Test that damage_service properly finalizes death for multiple monsters (AoE simulation)."""
        # Create player as caster
        player = Entity(
            x=10, y=10,
            char='@',
            color=(255, 255, 255),
            name='Player',
            fighter=Fighter(hp=30, defense=0, power=5, xp=0)
        )
        
        # Create three monsters with low HP
        monsters = []
        for i in range(3):
            monster = Entity(
                x=15 + i, y=15,
                char='o',
                color=(255, 0, 0),
                name=f'Orc{i}',
                fighter=Fighter(hp=20, defense=0, power=5, xp=35)
            )
            monster.fighter.hp = 5  # Low HP, will die from damage
            monsters.append(monster)
        
        entities = [player] + monsters
        
        # Mock state_manager
        mock_state_manager = Mock()
        mock_state_manager.state = Mock()
        mock_state_manager.state.player = player
        mock_state_manager.state.game_map = Mock()
        mock_state_manager.state.entities = entities
        
        # Import damage service
        from services.damage_service import apply_damage
        
        # Mock death_functions.kill_monster to count calls
        with patch('death_functions.kill_monster') as mock_kill:
            mock_kill.return_value = Mock()
            
            # Apply damage to each monster (simulating AoE spell)
            for monster in monsters:
                apply_damage(
                    mock_state_manager,
                    monster,
                    10,  # Lethal
                    cause="spell:fireball",
                    attacker_entity=player
                )
            
            # Verify all monsters died
            for monster in monsters:
                self.assertLessEqual(monster.fighter.hp, 0, f"{monster.name} should be dead")
            
            # Verify kill_monster was called for each monster
            self.assertEqual(mock_kill.call_count, 3, "Should finalize death for all 3 monsters")
    
    def test_spell_damage_service_non_lethal_does_not_finalize_death(self):
        """Test that non-lethal damage does not trigger death finalization."""
        # Create player as caster
        player = Entity(
            x=10, y=10,
            char='@',
            color=(255, 255, 255),
            name='Player',
            fighter=Fighter(hp=30, defense=0, power=5, xp=0)
        )
        
        # Create monster with enough HP to survive
        monster = Entity(
            x=15, y=15,
            char='o',
            color=(255, 0, 0),
            name='Orc',
            fighter=Fighter(hp=30, defense=0, power=5, xp=35)
        )
        
        entities = [player, monster]
        
        # Mock state_manager
        mock_state_manager = Mock()
        mock_state_manager.state = Mock()
        mock_state_manager.state.player = player
        mock_state_manager.state.game_map = Mock()
        mock_state_manager.state.entities = entities
        
        # Import damage service
        from services.damage_service import apply_damage
        
        # Mock death_functions.kill_monster
        with patch('death_functions.kill_monster') as mock_kill:
            # Apply non-lethal damage
            apply_damage(
                mock_state_manager,
                monster,
                5,  # Non-lethal
                cause="spell:fireball",
                attacker_entity=player
            )
            
            # Verify monster survived
            self.assertGreater(monster.fighter.hp, 0, "Monster should survive non-lethal damage")
            
            # Verify kill_monster was NOT called
            mock_kill.assert_not_called()


class TestSpellDeathConsistency(unittest.TestCase):
    """Test that spell death behavior is consistent with other damage sources."""
    
    def test_spell_damage_service_death_result_format_matches_trap_death(self):
        """Test that spell deaths return the same result format as trap/throwing deaths."""
        # Create player
        player = Entity(
            x=10, y=10,
            char='@',
            color=(255, 255, 255),
            name='Player',
            fighter=Fighter(hp=30, defense=0, power=5, xp=0)
        )
        
        # Create monster with low HP
        monster = Entity(
            x=12, y=12,
            char='o',
            color=(255, 0, 0),
            name='Orc',
            fighter=Fighter(hp=20, defense=0, power=5, xp=35)
        )
        monster.fighter.hp = 1
        
        # Mock state_manager
        mock_state_manager = Mock()
        mock_state_manager.state = Mock()
        mock_state_manager.state.player = player
        mock_state_manager.state.game_map = Mock()
        mock_state_manager.state.entities = [player, monster]
        
        # Import damage service
        from services.damage_service import apply_damage
        
        # Mock kill_monster to observe death handling
        with patch('death_functions.kill_monster') as mock_kill:
            mock_kill.return_value = Mock()
            
            # Apply lethal damage
            results = apply_damage(
                mock_state_manager,
                monster,
                10,
                cause="spell:lightning",
                attacker_entity=player
            )
            
            # Find death result
            death_results = [r for r in results if r.get("dead")]
            self.assertEqual(len(death_results), 1, "Should have exactly one death result")
            
            death_result = death_results[0]
            self.assertIn("dead", death_result, "Result should have 'dead' key")
            self.assertIn("xp", death_result, "Result should have 'xp' key")
            self.assertEqual(death_result["dead"], monster, "Should reference correct entity")
            self.assertEqual(death_result["xp"], 35, "Should include correct XP value")


if __name__ == "__main__":
    unittest.main(verbosity=2)

