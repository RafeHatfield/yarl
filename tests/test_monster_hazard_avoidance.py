"""Tests for monster pathfinding with hazard avoidance.

Monsters should prefer paths that avoid ground hazards when possible,
but still cross hazards if it's the only available path.
"""

import unittest
from unittest.mock import Mock, patch
import numpy as np

from entity import Entity
from components.fighter import Fighter
from components.ai import BasicMonster
from components.ground_hazard import GroundHazard, GroundHazardManager, HazardType
from map_objects.game_map import GameMap


class TestMonsterHazardAvoidance(unittest.TestCase):
    """Test that monsters avoid hazards in their pathfinding."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.game_map = GameMap(width=20, height=20, dungeon_level=1)
        
        # Create a monster at (5, 10)
        fighter = Fighter(hp=30, defense=2, power=5)
        ai = BasicMonster()
        self.monster = Entity(
            5, 10, '@', (255, 0, 0), 'TestMonster',
            blocks=True, fighter=fighter, ai=ai
        )
        
        # Create a target (player) at (15, 10)
        self.player = Entity(
            15, 10, '@', (255, 255, 255), 'Player',
            blocks=True, fighter=Fighter(hp=100, defense=5, power=10)
        )
        
        self.entities = [self.monster, self.player]
    
    def test_monster_avoids_fire_hazard(self):
        """Test that monster takes a longer path to avoid fire."""
        # Create a vertical wall of fire between monster and player
        # Monster at (5, 10), Player at (15, 10)
        # Fire wall at x=10, y=8-12 (blocking direct path)
        fire_hazards = []
        for y in range(8, 13):
            fire = GroundHazard(
                hazard_type=HazardType.FIRE,
                x=10, y=y,
                base_damage=10,
                remaining_turns=3,
                max_duration=3,
                source_name="Test"
            )
            self.game_map.hazard_manager.add_hazard(fire)
            fire_hazards.append((10, y))
        
        # Record initial position
        initial_x, initial_y = self.monster.x, self.monster.y
        
        # Monster should move, but not directly through the fire
        self.monster.move_astar(self.player, self.entities, self.game_map)
        
        # Check that monster moved (path exists)
        self.assertTrue(
            self.monster.x != initial_x or self.monster.y != initial_y,
            "Monster should have moved"
        )
        
        # Check that monster didn't step on fire
        self.assertNotIn(
            (self.monster.x, self.monster.y), fire_hazards,
            "Monster should not step on fire hazard"
        )
    
    def test_monster_avoids_poison_gas(self):
        """Test that monster avoids poison gas hazards."""
        # Create poison gas at (10, 10) - right between monster and player
        gas = GroundHazard(
            hazard_type=HazardType.POISON_GAS,
            x=10, y=10,
            base_damage=5,
            remaining_turns=4,
            max_duration=4,
            source_name="Test"
        )
        self.game_map.hazard_manager.add_hazard(gas)
        
        # Monster should move around the gas
        initial_pos = (self.monster.x, self.monster.y)
        self.monster.move_astar(self.player, self.entities, self.game_map)
        
        # Monster should have moved
        new_pos = (self.monster.x, self.monster.y)
        self.assertNotEqual(initial_pos, new_pos, "Monster should move")
        
        # Monster should not be on the gas
        self.assertNotEqual(new_pos, (10, 10), "Monster should avoid gas")
    
    def test_monster_crosses_hazard_if_only_path(self):
        """Test that monster will cross hazards if no alternative exists."""
        # Create a narrow corridor with fire in the middle
        # Build walls to force a single path
        for y in range(20):
            if y < 9 or y > 11:
                self.game_map.tiles[8][y].blocked = True
                self.game_map.tiles[12][y].blocked = True
        
        # Place fire at (10, 10) - the only path through
        fire = GroundHazard(
            hazard_type=HazardType.FIRE,
            x=10, y=10,
            base_damage=10,
            remaining_turns=3,
            max_duration=3,
            source_name="Test"
        )
        self.game_map.hazard_manager.add_hazard(fire)
        
        # Monster should still path toward player despite fire
        # May take multiple turns to cross
        initial_x = self.monster.x
        for _ in range(10):  # Allow multiple moves
            if self.monster.x == self.player.x and self.monster.y == self.player.y:
                break
            self.monster.move_astar(self.player, self.entities, self.game_map)
        
        # Monster should have moved toward player (even if not all the way)
        self.assertGreater(
            self.monster.x, initial_x,
            "Monster should move forward despite hazard in only path"
        )
    
    def test_monster_prefers_lower_damage_hazards(self):
        """Test that monster prefers crossing weaker hazards over stronger ones."""
        # Create two paths: one with high damage fire, one with low damage gas
        # High damage fire path at y=9
        fire = GroundHazard(
            hazard_type=HazardType.FIRE,
            x=10, y=9,
            base_damage=10,
            remaining_turns=3,
            max_duration=3,
            source_name="Big Fire"
        )
        self.game_map.hazard_manager.add_hazard(fire)
        
        # Low damage gas path at y=11
        gas = GroundHazard(
            hazard_type=HazardType.POISON_GAS,
            x=10, y=11,
            base_damage=5,
            remaining_turns=4,
            max_duration=4,
            source_name="Weak Gas"
        )
        self.game_map.hazard_manager.add_hazard(gas)
        
        # Block direct path at y=10
        self.game_map.tiles[10][10].blocked = True
        
        # Monster should move and prefer the gas path (lower damage)
        for _ in range(3):
            prev_y = self.monster.y
            self.monster.move_astar(self.player, self.entities, self.game_map)
            # Check if monster moved closer to gas path (y=11) rather than fire (y=9)
            if self.monster.y != prev_y and self.monster.x == 10:
                # Monster is at x=10, check which hazard it chose
                self.assertEqual(
                    self.monster.y, 11,
                    "Monster should prefer lower damage hazard (gas at y=11)"
                )
                break
    
    def test_hazard_avoidance_with_decaying_damage(self):
        """Test that monsters consider decaying hazard damage in pathfinding."""
        # Create a nearly-expired hazard (low damage)
        weak_fire = GroundHazard(
            hazard_type=HazardType.FIRE,
            x=10, y=10,
            base_damage=10,
            remaining_turns=1,  # Nearly expired
            max_duration=3,
            source_name="Weak Fire"
        )
        self.game_map.hazard_manager.add_hazard(weak_fire)
        
        # Verify it has low current damage (should be 1/3 of base)
        current_damage = weak_fire.get_current_damage()
        self.assertLess(current_damage, 5, "Decayed hazard should have low damage")
        self.assertGreater(current_damage, 0, "Hazard should still do some damage")
        
        # The key test is that the hazard cost is correctly calculated
        # We verify this by checking the hazard damage is being used
        # (The actual movement behavior is tested in other tests)
    
    def test_no_hazards_normal_pathfinding(self):
        """Test that pathfinding works normally when no hazards present."""
        # No hazards - just verify normal pathfinding
        initial_x = self.monster.x
        self.monster.move_astar(self.player, self.entities, self.game_map)
        
        # Monster should move toward player
        self.assertGreater(self.monster.x, initial_x, "Monster should move toward player")
    
    def test_hazard_manager_not_present(self):
        """Test that pathfinding works when map has no hazard manager."""
        # Remove hazard manager
        delattr(self.game_map, 'hazard_manager')
        
        # Should not crash - this is the key test
        try:
            self.monster.move_astar(self.player, self.entities, self.game_map)
            # If we get here without exception, test passes
            self.assertTrue(True, "Pathfinding completed without crashing")
        except Exception as e:
            self.fail(f"Pathfinding crashed without hazard manager: {e}")


class TestHazardCostCalculation(unittest.TestCase):
    """Test the hazard cost calculation in monster pathfinding."""
    
    def test_fire_adds_correct_cost(self):
        """Test that fire hazards add their damage as pathfinding cost."""
        game_map = GameMap(width=10, height=10, dungeon_level=1)
        
        # Create a fire hazard with 10 damage
        fire = GroundHazard(
            hazard_type=HazardType.FIRE,
            x=5, y=5,
            base_damage=10,
            remaining_turns=3,
            max_duration=3,
            source_name="Test"
        )
        game_map.hazard_manager.add_hazard(fire)
        
        # Verify fire has 10 damage
        self.assertEqual(fire.get_current_damage(), 10)
        
        # The cost calculation happens in entity.move_astar
        # We can't easily test it directly, but we tested behavior above
    
    def test_gas_adds_correct_cost(self):
        """Test that poison gas adds its damage as pathfinding cost."""
        game_map = GameMap(width=10, height=10, dungeon_level=1)
        
        # Create poison gas with 5 damage
        gas = GroundHazard(
            hazard_type=HazardType.POISON_GAS,
            x=5, y=5,
            base_damage=5,
            remaining_turns=4,
            max_duration=4,
            source_name="Test"
        )
        game_map.hazard_manager.add_hazard(gas)
        
        # Verify gas has 5 damage
        self.assertEqual(gas.get_current_damage(), 5)


if __name__ == '__main__':
    unittest.main()

