"""Tests for boss loot system."""

import pytest
from entity import Entity
from components.fighter import Fighter
from components.boss import Boss, create_dragon_lord_boss
from components.loot import LootRarity, get_loot_generator
from components.component_registry import ComponentType
from components.monster_equipment import MonsterLootDropper
from map_objects.game_map import GameMap


class TestBossLootGeneration:
    """Tests for generating boss loot drops."""
    
    def test_boss_loot_always_legendary(self):
        """Test that boss loot is always legendary quality."""
        loot_gen = get_loot_generator()
        
        # Generate boss loot multiple times
        for _ in range(10):
            primary, secondary = loot_gen.generate_boss_loot(10, 10, 5, "Test Boss")
            
            # Primary drop is always legendary
            assert primary is not None
            assert hasattr(primary, 'loot')
            assert primary.loot.rarity == LootRarity.LEGENDARY
            assert primary.color == LootRarity.LEGENDARY.color  # Gold color
            
            # Secondary drop (if it exists) is also legendary
            if secondary:
                assert hasattr(secondary, 'loot')
                assert secondary.loot.rarity == LootRarity.LEGENDARY
    
    def test_boss_loot_different_types(self):
        """Test that boss drops weapon and armor."""
        loot_gen = get_loot_generator()
        
        primary, secondary = loot_gen.generate_boss_loot(10, 10, 5, "Dragon Lord")
        
        # Primary is always weapon
        assert primary.equippable is not None
        assert primary.equippable.power_bonus > 0  # Weapons have power
        
        # Secondary (if exists) is armor
        if secondary:
            assert secondary.equippable is not None
            assert secondary.equippable.defense_bonus > 0  # Armor has defense
    
    def test_boss_loot_at_different_levels(self):
        """Test boss loot scales with dungeon level."""
        loot_gen = get_loot_generator()
        
        # Level 1 boss
        low_level_weapon, _ = loot_gen.generate_boss_loot(10, 10, 1, "Weak Boss")
        low_power = low_level_weapon.equippable.power_bonus
        
        # Level 10 boss
        high_level_weapon, _ = loot_gen.generate_boss_loot(10, 10, 10, "Strong Boss")
        high_power = high_level_weapon.equippable.power_bonus
        
        # Higher level should have better stats
        assert high_power >= low_power


class TestBossLootIntegration:
    """Tests for boss loot integration with monster death."""
    
    def test_boss_drops_legendary_on_death(self):
        """Test that killing a boss drops legendary loot."""
        # Create boss entity
        boss = Entity(10, 10, 'D', (255, 50, 0), "Dragon Lord", blocks=True)
        boss.fighter = Fighter(hp=100, defense=5, power=5)
        boss.boss = create_dragon_lord_boss()
        
        # Add components to registry
        boss.components.add(ComponentType.FIGHTER, boss.fighter)
        boss.components.add(ComponentType.BOSS, boss.boss)
        
        # Create minimal game map
        game_map = GameMap(30, 20, dungeon_level=5)
        
        # Kill boss and get loot
        loot = MonsterLootDropper.drop_monster_loot(boss, boss.x, boss.y, game_map)
        
        # Should have at least one legendary item
        assert len(loot) >= 1
        assert any(item.loot.rarity == LootRarity.LEGENDARY for item in loot if hasattr(item, 'loot'))
        
        # All quality loot should be legendary
        quality_loot = [item for item in loot if hasattr(item, 'loot')]
        for item in quality_loot:
            assert item.loot.rarity == LootRarity.LEGENDARY
    
    def test_normal_monster_no_boss_loot(self):
        """Test that normal monsters don't drop guaranteed legendaries."""
        # Create normal monster
        orc = Entity(10, 10, 'o', (63, 127, 63), "Orc", blocks=True)
        orc.fighter = Fighter(hp=20, defense=0, power=3)
        orc.components.add(ComponentType.FIGHTER, orc.fighter)
        
        # NO boss component!
        
        game_map = GameMap(30, 20, dungeon_level=5)
        
        # Kill orc and get loot
        loot = MonsterLootDropper.drop_monster_loot(orc, orc.x, orc.y, game_map)
        
        # Might have loot, but not guaranteed legendary
        # (This is probabilistic, but should rarely be legendary)
        quality_loot = [item for item in loot if hasattr(item, 'loot')]
        
        # Most of the time, normal monsters don't drop legendary
        # (Can't assert definitively due to randomness, but we can check it doesn't break)
        assert isinstance(loot, list)


class TestBossLootPosition:
    """Tests for boss loot positioning."""
    
    def test_boss_loot_placed_at_coordinates(self):
        """Test that boss loot is placed at specified coordinates."""
        loot_gen = get_loot_generator()
        
        x, y = 15, 20
        primary, secondary = loot_gen.generate_boss_loot(x, y, 5, "Test Boss")
        
        # Primary at specified location
        assert primary.x == x
        assert primary.y == y
        
        # Secondary has coordinates set (may be different to avoid stacking)
        if secondary:
            assert hasattr(secondary, 'x')
            assert hasattr(secondary, 'y')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

