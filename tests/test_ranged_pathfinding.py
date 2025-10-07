"""Tests for ranged weapon pathfinding and auto-attack behavior.

This module tests the bug fix for ranged weapons not auto-attacking during pathfinding.
The bug was that "enemy spotted" would interrupt pathfinding before reaching weapon range.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from entity import Entity
from components.fighter import Fighter
from components.equipment import Equipment
from components.equippable import Equippable
from components.player_pathfinding import PlayerPathfinding
from equipment_slots import EquipmentSlots
from mouse_movement import process_pathfinding_movement, _check_for_close_enemies, _check_for_enemy_in_weapon_range


class TestRangedPathfindingAutoAttack(unittest.TestCase):
    """Test ranged weapon auto-attack during pathfinding."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create player with longbow (reach 10)
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
        
        # Create orc enemy at distance
        self.orc = Entity(x=25, y=10, char='o', color=(0, 127, 0), name='Orc')
        self.orc.fighter = Fighter(hp=20, defense=3, power=4)
        self.orc.fighter.owner = self.orc
        
        # Mock game map
        self.game_map = Mock()
        self.game_map.is_blocked = Mock(return_value=False)
        self.game_map.hazard_manager = None  # No hazards for these tests
        
        # Mock FOV map
        self.fov_map = Mock()
        
    def test_ranged_weapon_continues_approaching_distant_enemy(self):
        """Test that ranged weapons don't stop when enemy is beyond weapon range.
        
        Bug: Player with longbow (reach 10) would stop at ANY distance when enemy spotted.
        Fix: Player should continue approaching until within weapon range.
        """
        # Player at (10, 10), Orc at (30, 10) = 20 tiles away (beyond reach 10 * 1.5 = 15)
        # After one step to (11, 10), orc will still be 19 tiles away (still beyond range)
        self.orc.x = 30
        self.orc.y = 10
        
        # Set up pathfinding toward orc
        self.player.pathfinding.current_path = [(11, 10), (12, 10), (13, 10)]  # Moving toward orc
        self.player.pathfinding.is_moving = True
        
        # Mock FOV to show orc is visible
        with patch('fov_functions.map_is_in_fov', return_value=True):
            # Process one pathfinding step
            result = process_pathfinding_movement(
                self.player, 
                [self.player, self.orc], 
                self.game_map, 
                self.fov_map
            )
        
        # Should continue pathfinding (not stop with "enemy spotted")
        results_list = result.get("results", [])
        
        # Should NOT have "Movement stopped" message
        messages = [r.get("message") for r in results_list if "message" in r]
        stopped_messages = [m for m in messages if m and "stopped" in str(m).lower()]
        self.assertEqual(len(stopped_messages), 0, 
                        "Should not stop when enemy is beyond weapon range")
        
        # Should have continue_pathfinding flag
        continue_flags = [r for r in results_list if r.get("continue_pathfinding")]
        self.assertGreater(len(continue_flags), 0,
                          "Should continue pathfinding toward distant enemy")
    
    def test_ranged_weapon_auto_attacks_at_range(self):
        """Test that ranged weapons auto-attack when enemy reaches weapon range.
        
        Bug: Auto-attack check was never reached because "enemy spotted" stopped movement first.
        Fix: Player should auto-attack when within longbow range (10 tiles).
        """
        # Player at (10, 10), Orc at (20, 10) = 10 tiles away (exactly at reach)
        self.orc.x = 20
        self.orc.y = 10
        
        # Set up pathfinding with one more step
        self.player.pathfinding.current_path = [(11, 10)]
        self.player.pathfinding.is_moving = True
        
        # Mock FOV to show orc is visible
        with patch('fov_functions.map_is_in_fov', return_value=True):
            # Process pathfinding step
            result = process_pathfinding_movement(
                self.player,
                [self.player, self.orc],
                self.game_map,
                self.fov_map
            )
        
        # Should trigger auto-attack
        results_list = result.get("results", [])
        
        # Should have enemy_turn flag (indicates attack happened)
        enemy_turn_flags = [r for r in results_list if r.get("enemy_turn")]
        self.assertGreater(len(enemy_turn_flags), 0,
                          "Should auto-attack when enemy is within weapon range")
    
    def test_ranged_weapon_stops_if_melee_enemy_gets_close(self):
        """Test that ranged weapons still stop if melee enemies get dangerously close.
        
        Safety feature: Even with longbow, stop if enemy gets within melee range (~2 tiles).
        """
        # Player at (10, 10), Orc at (12, 10) = 2 tiles away (melee threat range)
        self.orc.x = 12
        self.orc.y = 10
        
        # Set up pathfinding
        self.player.pathfinding.current_path = [(11, 10)]
        self.player.pathfinding.is_moving = True
        
        # Check if close enemy detection works
        weapon_reach = 10  # Longbow
        is_close = _check_for_close_enemies(
            self.player,
            [self.player, self.orc],
            self.fov_map,
            weapon_reach
        )
        
        # Should detect close enemy even with ranged weapon
        with patch('fov_functions.map_is_in_fov', return_value=True):
            self.assertTrue(is_close, 
                          "Should detect enemy within melee threat range (2 tiles)")
    
    def test_melee_weapon_still_stops_immediately(self):
        """Test that melee weapons still stop immediately when enemy is spotted.
        
        Ensure the fix doesn't break melee weapon behavior.
        """
        # Give player a sword (reach 1) instead of longbow
        sword = Entity(x=0, y=0, char='/', color=(192, 192, 192), name='Sword')
        sword.equippable = Equippable(
            slot=EquipmentSlots.MAIN_HAND,
            damage_dice="1d8",
            reach=1
        )
        sword.equippable.owner = sword
        self.player.equipment.main_hand = sword
        
        # Orc at (15, 10) = 5 tiles away
        self.orc.x = 15
        self.orc.y = 10
        
        # Set up pathfinding
        self.player.pathfinding.current_path = [(11, 10)]
        self.player.pathfinding.is_moving = True
        
        # Check close enemy detection with melee weapon
        weapon_reach = 1  # Sword
        
        with patch('fov_functions.map_is_in_fov', return_value=True):
            is_close = _check_for_close_enemies(
                self.player,
                [self.player, self.orc],
                self.fov_map,
                weapon_reach
            )
        
        # Melee weapons: enemy at 5 tiles is NOT close (threat_distance = min(1, 2) * 1.5 = 1.5)
        # So this should return False
        self.assertFalse(is_close,
                        "Melee weapon: enemy at 5 tiles should not be in threat range")
    
    def test_check_for_enemy_in_weapon_range_longbow(self):
        """Test that weapon range check correctly identifies enemies within longbow range."""
        # Player at (10, 10) with longbow (reach 10)
        # Orc at (20, 10) = 10 tiles away (at max range)
        self.orc.x = 20
        self.orc.y = 10
        
        with patch('fov_functions.map_is_in_fov', return_value=True):
            enemy = _check_for_enemy_in_weapon_range(
                self.player,
                [self.player, self.orc],
                self.fov_map
            )
        
        self.assertIsNotNone(enemy, "Should find enemy within longbow range (10 tiles)")
        self.assertEqual(enemy, self.orc, "Should return the orc")
    
    def test_check_for_enemy_in_weapon_range_beyond_range(self):
        """Test that weapon range check doesn't find enemies beyond weapon range."""
        # Player at (10, 10) with longbow (reach 10)
        # Orc at (27, 10) = 17 tiles away (beyond reach 10 * 1.5 = 15)
        self.orc.x = 27
        self.orc.y = 10
        
        with patch('fov_functions.map_is_in_fov', return_value=True):
            enemy = _check_for_enemy_in_weapon_range(
                self.player,
                [self.player, self.orc],
                self.fov_map
            )
        
        self.assertIsNone(enemy, "Should NOT find enemy beyond weapon range (17 > 15)")


if __name__ == '__main__':
    unittest.main()

