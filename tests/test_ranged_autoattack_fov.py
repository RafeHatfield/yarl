"""Test for ranged auto-attack with FOV timing bug.

This tests the bug where ranged weapons don't auto-attack because the enemy
check uses stale FOV (before player movement) instead of updated FOV (after movement).
"""

import unittest
from unittest.mock import Mock, patch
from entity import Entity
from components.fighter import Fighter
from components.equipment import Equipment
from components.equippable import Equippable
from components.player_pathfinding import PlayerPathfinding
from equipment_slots import EquipmentSlots
from mouse_movement import process_pathfinding_movement


class TestRangedAutoAttackFOV(unittest.TestCase):
    """Test ranged weapon auto-attack with FOV considerations."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create player with longbow at (10, 10)
        self.player = Entity(x=10, y=10, char='@', color=(255, 255, 255), name='Player')
        self.player.fighter = Fighter(hp=100, defense=5, power=5)
        self.player.fighter.owner = self.player
        self.player.equipment = Equipment()
        self.player.pathfinding = PlayerPathfinding()
        self.player.pathfinding.owner = self.player
        
        # Create longbow (reach 10)
        longbow = Entity(x=0, y=0, char='}', color=(160, 82, 45), name='Longbow')
        longbow.equippable = Equippable(
            slot=EquipmentSlots.MAIN_HAND,
            damage_dice="1d8",
            reach=10
        )
        longbow.equippable.owner = longbow
        self.player.equipment.main_hand = longbow
        
        # Create orc at (20, 10) = 10 tiles away (at max longbow range)
        self.orc = Entity(x=20, y=10, char='o', color=(0, 127, 0), name='Orc')
        self.orc.fighter = Fighter(hp=20, defense=3, power=4)
        self.orc.fighter.owner = self.orc
        
        # Mock game map
        self.game_map = Mock()
        self.game_map.is_blocked = Mock(return_value=False)
        
        # Mock FOV map - enemy becomes visible AFTER move
        self.fov_map = Mock()
    
    def test_ranged_autoattack_triggers_after_moving_into_range(self):
        """Test that auto-attack triggers when moving into weapon range.
        
        Bug: Player moved adjacent to orc even with longbow equipped.
        Cause: FOV check used stale FOV from before movement.
        Fix: Enemy check should account for FOV being updated after movement.
        """
        # Player at (10, 10), moving toward orc at (20, 10)
        # After one move to (11, 10), distance = 9 tiles (within reach 10 * 1.5 = 15)
        self.player.pathfinding.current_path = [(11, 10), (12, 10)]
        self.player.pathfinding.is_moving = True
        
        # Mock FOV: enemy becomes visible after player moves
        def fov_check(fov_map, x, y):
            # Orc at (20, 10) is visible after player moves to (11, 10)
            return x == 20 and y == 10
        
        with patch('fov_functions.map_is_in_fov', side_effect=fov_check):
            result = process_pathfinding_movement(
                self.player,
                [self.player, self.orc],
                self.game_map,
                self.fov_map
            )
        
        # Should have attacked (enemy_turn flag)
        results_list = result.get("results", [])
        enemy_turn_flags = [r for r in results_list if r.get("enemy_turn")]
        
        self.assertGreater(len(enemy_turn_flags), 0,
                          "Should auto-attack when moving into weapon range")
        
        # Should NOT have continue_pathfinding flag
        continue_flags = [r for r in results_list if r.get("continue_pathfinding")]
        self.assertEqual(len(continue_flags), 0,
                        "Should stop pathfinding after auto-attack")


if __name__ == '__main__':
    unittest.main()

