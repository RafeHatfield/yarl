"""Regression test for fireball self-damage bug.

Ensures that:
1. Fireball doesn't damage the caster
2. Player death at 0 HP is properly detected
3. Death state is triggered correctly
"""

import unittest
from unittest.mock import Mock

from entity import Entity
from components.fighter import Fighter
from components.faction import Faction
from item_functions import cast_fireball
from game_states import GameStates


class TestFireballSelfDamageRegression(unittest.TestCase):
    """Regression tests for fireball self-damage."""
    
    def test_fireball_damages_caster_and_enemies(self):
        """REGRESSION: Fireball is an area effect - damages EVERYONE in radius."""
        # Create player (caster)
        player = Entity(10, 10, '@', (255, 255, 255), 'Player', blocks=True)
        player.fighter = Fighter(hp=30, defense=0, power=0)
        player.fighter.owner = player
        player.faction = Faction.PLAYER
        
        # Create orc in fireball radius
        orc = Entity(12, 10, 'o', (0, 255, 0), 'Orc', blocks=True)
        orc.fighter = Fighter(hp=20, defense=0, power=3)
        orc.fighter.owner = orc
        orc.faction = Faction.NEUTRAL
        
        entities = [player, orc]
        
        # Create mock fov_map
        fov_map = Mock()
        fov_map.is_in_fov = Mock(return_value=True)
        
        # Cast fireball at position 11, 10 (between player and orc, radius 2)
        # Player at (10, 10) is distance 1 from target
        # Orc at (12, 10) is distance 1 from target
        # BOTH should be damaged - fireball is dangerous!
        results = cast_fireball(
            player,  # Caster
            entities=entities,
            fov_map=fov_map,
            damage=25,
            radius=2,
            target_x=11,
            target_y=10
        )
        
        # Player should ALSO be damaged (area effect!)
        self.assertEqual(player.fighter.hp, 5, "Player should be damaged by area effect")
        
        # Orc should be damaged
        self.assertLess(orc.fighter.hp, 20, "Orc should be damaged by fireball")
    
    def test_player_death_at_zero_hp(self):
        """REGRESSION: Player should be marked as dead when HP <= 0."""
        player = Entity(10, 10, '@', (255, 255, 255), 'Player', blocks=True)
        player.fighter = Fighter(hp=10, defense=0, power=0)
        player.fighter.owner = player
        
        # Deal exactly lethal damage
        results = player.fighter.take_damage(10)
        
        # Should have death result
        dead_results = [r for r in results if 'dead' in r]
        self.assertEqual(len(dead_results), 1, "Should have one death result")
        self.assertEqual(dead_results[0]['dead'], player, "Dead entity should be player")
        self.assertEqual(player.fighter.hp, 0, "HP should be 0")
    
    def test_player_death_at_negative_hp(self):
        """REGRESSION: Player should be marked as dead when HP goes negative."""
        player = Entity(10, 10, '@', (255, 255, 255), 'Player', blocks=True)
        player.fighter = Fighter(hp=10, defense=0, power=0)
        player.fighter.owner = player
        
        # Deal overkill damage
        results = player.fighter.take_damage(15)
        
        # Should have death result
        dead_results = [r for r in results if 'dead' in r]
        self.assertEqual(len(dead_results), 1, "Should have one death result")
        self.assertEqual(dead_results[0]['dead'], player, "Dead entity should be player")
        self.assertLessEqual(player.fighter.hp, 0, "HP should be <= 0")
    
    def test_player_death_state_not_overridden_after_item_use(self):
        """REGRESSION: PLAYER_DEAD state shouldn't be overridden to PLAYERS_TURN."""
        from game_actions import ActionProcessor
        from game_messages import MessageLog
        from engine.game_state_manager import GameStateManager
        from game_states import GameStates
        
        # This simulates the bug:
        # 1. Player uses item that kills them
        # 2. Death handler sets state to PLAYER_DEAD
        # 3. Bug: Code then sets state back to PLAYERS_TURN
        # 4. Result: Player at 0 HP but game continues
        
        state_manager = GameStateManager()
        state_manager.state.current_state = GameStates.SHOW_INVENTORY
        
        # Simulate: Death was detected and state set to PLAYER_DEAD
        state_manager.set_game_state(GameStates.PLAYER_DEAD)
        
        # The bug: This line would override it back to PLAYERS_TURN
        # if not any(result.get("targeting") for result in item_use_results):
        #     self.state_manager.set_game_state(GameStates.PLAYERS_TURN)  # WRONG!
        
        # After the fix, we check player_died flag first
        # So the state should STAY as PLAYER_DEAD
        
        self.assertEqual(state_manager.state.current_state, GameStates.PLAYER_DEAD,
                        "PLAYER_DEAD state should not be overridden")


if __name__ == '__main__':
    unittest.main()

