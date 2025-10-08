"""Regression tests for entity blocking and overlap prevention.

This test suite ensures that:
- Entities cannot move onto tiles occupied by blocking entities
- move_astar validates destination before moving
- move_towards validates destination before moving  
- Zombies cannot resurrect on occupied tiles
- Zombies cannot move onto the player
- Multiple blocking entities cannot occupy the same tile
"""

import unittest
from unittest.mock import MagicMock, patch
from entity import Entity, get_blocking_entities_at_location
from components.fighter import Fighter
from components.ai import MindlessZombieAI
from map_objects.game_map import GameMap
from item_functions import cast_raise_dead


class TestMoveAstarBlocking(unittest.TestCase):
    """Test that move_astar prevents moving onto occupied tiles."""
    
    def setUp(self):
        """Set up test entities and game map."""
        self.game_map = GameMap(20, 20)
        
        # Create attacker (zombie or monster)
        self.attacker = Entity(5, 5, 'Z', (255, 255, 255), 'Zombie', blocks=True)
        self.attacker.fighter = Fighter(hp=30, defense=0, power=0)
        self.attacker.fighter.owner = self.attacker
        
        # Create target (player)
        self.target = Entity(7, 5, '@', (255, 255, 0), 'Player', blocks=True)
        self.target.fighter = Fighter(hp=30, defense=0, power=0)
        self.target.fighter.owner = self.target
        
        # Create blocking entity between them
        self.blocker = Entity(6, 5, 'X', (100, 100, 100), 'Wall', blocks=True)
        
        self.entities = [self.attacker, self.target, self.blocker]
    
    def test_move_astar_does_not_overlap_blocking_entity(self):
        """Test that move_astar doesn't move onto a tile with a blocking entity."""
        initial_x = self.attacker.x
        initial_y = self.attacker.y
        
        # Try to move towards target (path goes through blocker at 6,5)
        self.attacker.move_astar(self.target, self.entities, self.game_map)
        
        # Attacker should NOT have moved to blocker's position
        self.assertFalse(
            self.attacker.x == self.blocker.x and self.attacker.y == self.blocker.y,
            "Attacker moved onto blocking entity!"
        )
        
        # Verify only one entity at each position
        positions = {}
        for entity in self.entities:
            if entity.blocks:
                pos = (entity.x, entity.y)
                self.assertNotIn(pos, positions, 
                    f"Multiple blocking entities at {pos}: {positions.get(pos)} and {entity.name}")
                positions[pos] = entity.name
    
    def test_move_astar_does_not_overlap_player(self):
        """Test that zombies/monsters don't move onto the player."""
        # Place zombie adjacent to player
        self.attacker.x = 6
        self.attacker.y = 5
        
        # Remove blocker
        self.entities.remove(self.blocker)
        
        # Try to move towards player
        self.attacker.move_astar(self.target, self.entities, self.game_map)
        
        # Zombie should NOT have moved onto player
        self.assertFalse(
            self.attacker.x == self.target.x and self.attacker.y == self.target.y,
            "Zombie moved onto player!"
        )
    
    def test_move_astar_validates_destination_after_pathfinding(self):
        """Test that move_astar validates the final destination is clear."""
        # Position entities: attacker at (5,5), target at (7,5), blocker at (6,5)
        # Blocker is directly in the path
        
        # Try to move towards target (blocker is in the way at 6,5)
        self.attacker.move_astar(self.target, self.entities, self.game_map)
        
        # Attacker should not have moved onto blocker
        self.assertFalse(
            self.attacker.x == 6 and self.attacker.y == 5,
            "Attacker should not move onto blocker's tile"
        )
        
        # Verify no two blocking entities share a position
        positions = {}
        for entity in self.entities:
            if entity.blocks:
                pos = (entity.x, entity.y)
                if pos in positions:
                    self.fail(f"Multiple blocking entities at {pos}: {positions[pos]} and {entity.name}")
                positions[pos] = entity.name


class TestMoveTowardsBlocking(unittest.TestCase):
    """Test that move_towards prevents moving onto occupied tiles."""
    
    def setUp(self):
        """Set up test entities and game map."""
        self.game_map = GameMap(20, 20)
        
        self.attacker = Entity(5, 5, 'A', (255, 255, 255), 'Attacker', blocks=True)
        self.target = Entity(7, 5, 'T', (255, 0, 0), 'Target', blocks=True)
        self.blocker = Entity(6, 5, 'X', (100, 100, 100), 'Blocker', blocks=True)
        
        self.entities = [self.attacker, self.target, self.blocker]
    
    def test_move_towards_does_not_overlap_blocking_entity(self):
        """Test that move_towards doesn't move onto a tile with a blocking entity."""
        initial_x = self.attacker.x
        initial_y = self.attacker.y
        
        # Try to move towards target (blocker is in the way)
        self.attacker.move_towards(self.target.x, self.target.y, self.game_map, self.entities)
        
        # Attacker should NOT have moved onto blocker
        self.assertFalse(
            self.attacker.x == self.blocker.x and self.attacker.y == self.blocker.y,
            "Attacker moved onto blocking entity via move_towards!"
        )


class TestZombieResurrectionBlocking(unittest.TestCase):
    """Test that zombies cannot be resurrected on occupied tiles."""
    
    def setUp(self):
        """Set up test entities."""
        # Create player/caster
        self.caster = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
        self.caster.fighter = Fighter(hp=30, defense=0, power=0)
        self.caster.fighter.owner = self.caster
        
        # Create corpse
        self.corpse = Entity(3, 3, '%', (127, 0, 0), 'remains of orc', blocks=False)
        
        # Create blocking entity on corpse
        self.blocker = Entity(3, 3, 'o', (0, 255, 0), 'Living Orc', blocks=True)
        self.blocker.fighter = Fighter(hp=20, defense=0, power=4)
        self.blocker.fighter.owner = self.blocker
        
        self.entities = [self.caster, self.corpse, self.blocker]
    
    def test_raise_dead_fails_when_entity_on_corpse(self):
        """Test that raise dead scroll fails if a blocking entity is on the corpse."""
        from config.entity_registry import load_entity_config
        load_entity_config()
        
        results = cast_raise_dead(
            self.caster,
            entities=self.entities,
            target_x=3,
            target_y=3,
            range=5
        )
        
        # Should have failed
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].get("consumed", True))
        self.assertIn("in the way", results[0]["message"].text)
        
        # Corpse should still be a corpse
        self.assertEqual(self.corpse.name, "remains of orc")
        self.assertFalse(self.corpse.blocks)
    
    def test_raise_dead_succeeds_when_no_blocker(self):
        """Test that raise dead works when tile is clear."""
        from config.entity_registry import load_entity_config
        load_entity_config()
        
        # Remove blocker
        self.entities.remove(self.blocker)
        
        results = cast_raise_dead(
            self.caster,
            entities=self.entities,
            target_x=3,
            target_y=3,
            range=5
        )
        
        # Should have succeeded
        consumed = any(r.get("consumed") for r in results)
        self.assertTrue(consumed, "Raise dead should have succeeded")
        
        # Corpse should now be a zombie
        self.assertTrue(self.corpse.name.startswith("Zombified"))
        self.assertTrue(self.corpse.blocks)


class TestZombieMindlessAIBlocking(unittest.TestCase):
    """Test that zombie AI doesn't move onto occupied tiles."""
    
    def setUp(self):
        """Set up test entities."""
        self.game_map = GameMap(20, 20)
        
        # Create zombie
        zombie_fighter = Fighter(hp=40, defense=0, power=3)
        zombie_ai = MindlessZombieAI()
        self.zombie = Entity(5, 5, 'Z', (40, 40, 40), 'Zombie', blocks=True,
                           fighter=zombie_fighter, ai=zombie_ai)
        
        # Create player
        player_fighter = Fighter(hp=30, defense=0, power=5)
        self.player = Entity(7, 5, '@', (255, 255, 0), 'Player', blocks=True,
                           fighter=player_fighter)
        
        self.entities = [self.zombie, self.player]
    
    def test_zombie_does_not_move_onto_player_during_chase(self):
        """Test that zombie doesn't move onto player while chasing."""
        # Zombie is at (5, 5), player at (7, 5)
        # Zombie should move closer but not onto player
        
        # Run several turns to let zombie chase
        for _ in range(3):
            initial_player_pos = (self.player.x, self.player.y)
            
            # Mock FOV to make player visible
            mock_fov = MagicMock()
            mock_fov.fov = [[True] * 20 for _ in range(20)]
            
            self.zombie.ai.take_turn(
                target=self.player,
                fov_map=mock_fov,
                game_map=self.game_map,
                entities=self.entities
            )
            
            # Zombie should NOT be on player's position
            self.assertFalse(
                self.zombie.x == self.player.x and self.zombie.y == self.player.y,
                f"Zombie moved onto player! Zombie at ({self.zombie.x}, {self.zombie.y}), "
                f"Player at ({self.player.x}, {self.player.y})"
            )
    
    @patch('random.randint')
    def test_zombie_attacks_instead_of_overlapping_when_adjacent(self, mock_randint):
        """Test that zombie attacks when adjacent instead of trying to move onto player."""
        # Mock d20 roll to guarantee a hit (20 = critical)
        mock_randint.return_value = 20
        
        # Place zombie adjacent to player
        self.zombie.x = 6
        self.zombie.y = 5
        
        initial_player_hp = self.player.fighter.hp
        
        # Mock FOV
        mock_fov = MagicMock()
        mock_fov.fov = [[True] * 20 for _ in range(20)]
        
        results = self.zombie.ai.take_turn(
            target=self.player,
            fov_map=mock_fov,
            game_map=self.game_map,
            entities=self.entities
        )
        
        # Zombie should NOT have moved onto player
        self.assertFalse(
            self.zombie.x == self.player.x and self.zombie.y == self.player.y,
            "Zombie moved onto player instead of attacking!"
        )
        
        # Player should have taken damage (zombie attacked with guaranteed crit)
        self.assertLess(
            self.player.fighter.hp, initial_player_hp,
            "Player should have taken damage from adjacent zombie"
        )


class TestGetBlockingEntitiesHelper(unittest.TestCase):
    """Test the get_blocking_entities_at_location helper function."""
    
    def test_finds_blocking_entity(self):
        """Test that it finds a blocking entity at a location."""
        blocker = Entity(5, 5, 'X', (100, 100, 100), 'Blocker', blocks=True)
        non_blocker = Entity(5, 5, 'i', (200, 200, 0), 'Item', blocks=False)
        other = Entity(6, 6, 'O', (255, 0, 0), 'Other', blocks=True)
        
        entities = [blocker, non_blocker, other]
        
        result = get_blocking_entities_at_location(entities, 5, 5)
        
        self.assertEqual(result, blocker)
    
    def test_returns_none_if_no_blocker(self):
        """Test that it returns None if no blocking entity at location."""
        non_blocker = Entity(5, 5, 'i', (200, 200, 0), 'Item', blocks=False)
        other = Entity(6, 6, 'O', (255, 0, 0), 'Other', blocks=True)
        
        entities = [non_blocker, other]
        
        result = get_blocking_entities_at_location(entities, 5, 5)
        
        self.assertIsNone(result)
    
    def test_ignores_non_blocking_entities(self):
        """Test that it ignores non-blocking entities."""
        non_blocker1 = Entity(5, 5, 'i', (200, 200, 0), 'Item', blocks=False)
        non_blocker2 = Entity(5, 5, 'j', (200, 200, 0), 'Potion', blocks=False)
        
        entities = [non_blocker1, non_blocker2]
        
        result = get_blocking_entities_at_location(entities, 5, 5)
        
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()

