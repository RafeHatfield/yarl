"""Tests for the loot quality and rarity system."""

import pytest
from unittest.mock import Mock, patch

from components.loot import (
    LootRarity,
    LootComponent,
    LootGenerator,
    get_loot_generator
)
from components.equippable import Equippable
from equipment_slots import EquipmentSlots


class TestLootRarity:
    """Tests for loot rarity tiers."""
    
    def test_rarity_tiers_exist(self):
        """Test all rarity tiers are defined."""
        assert LootRarity.COMMON
        assert LootRarity.UNCOMMON
        assert LootRarity.RARE
        assert LootRarity.LEGENDARY
    
    def test_rarity_attributes(self):
        """Test rarity tiers have proper attributes."""
        common = LootRarity.COMMON
        assert common.display_name == "Common"
        assert common.color == (255, 255, 255)  # White
        assert common.base_chance == 0.60
        assert common.bonus_range == (0, 1)
        
        legendary = LootRarity.LEGENDARY
        assert legendary.display_name == "Legendary"
        assert legendary.color == (255, 215, 0)  # Gold
        assert legendary.base_chance == 0.02
        assert legendary.bonus_range == (3, 5)
    
    def test_get_bonus(self):
        """Test bonus generation within range."""
        rare = LootRarity.RARE
        for _ in range(10):
            bonus = rare.get_bonus()
            assert 2 <= bonus <= 4, f"Rare bonus should be 2-4, got {bonus}"


class TestLootComponent:
    """Tests for loot metadata component."""
    
    def test_loot_component_creation(self):
        """Test creating loot component."""
        loot = LootComponent(LootRarity.UNCOMMON, quality_bonus=2, is_magical=True)
        assert loot.rarity == LootRarity.UNCOMMON
        assert loot.quality_bonus == 2
        assert loot.is_magical is True
    
    def test_loot_component_defaults(self):
        """Test loot component with defaults."""
        loot = LootComponent(LootRarity.COMMON)
        assert loot.quality_bonus == 0
        assert loot.is_magical is False
        assert loot.magic_prefix is None
        assert loot.magic_suffix is None


class TestLootGenerator:
    """Tests for loot generation system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.gen = LootGenerator()
    
    def test_determine_rarity_level_1(self):
        """Test rarity determination at level 1 (mostly common)."""
        results = {r: 0 for r in LootRarity}
        
        for _ in range(100):
            rarity = self.gen.determine_rarity(1)
            results[rarity] += 1
        
        # At level 1, should be mostly common (allow for random variance)
        assert results[LootRarity.COMMON] > 40, "Most drops should be common at level 1 (>40%)"
    
    def test_determine_rarity_level_10(self):
        """Test rarity determination at level 10 (more variety)."""
        results = {r: 0 for r in LootRarity}
        
        for _ in range(200):
            rarity = self.gen.determine_rarity(10)
            results[rarity] += 1
        
        # At level 10, should get some rares and maybe legendary
        assert results[LootRarity.RARE] > 0, "Should get rare drops at level 10"
        assert results[LootRarity.UNCOMMON] > 0, "Should get uncommon drops"
    
    def test_generate_weapon_basic(self):
        """Test basic weapon generation."""
        weapon = self.gen.generate_weapon(10, 10, 1)
        
        assert weapon is not None
        assert weapon.x == 10 and weapon.y == 10
        assert weapon.equippable is not None
        assert weapon.equippable.slot == EquipmentSlots.MAIN_HAND
        assert weapon.equippable.power_bonus > 0
        assert hasattr(weapon, 'loot')
        assert isinstance(weapon.loot, LootComponent)
    
    def test_generate_weapon_scaling(self):
        """Test weapon power scales with level."""
        weapon_lv1 = self.gen.generate_weapon(10, 10, 1, rarity=LootRarity.COMMON)
        weapon_lv10 = self.gen.generate_weapon(10, 10, 10, rarity=LootRarity.COMMON)
        
        # Higher level should have more power
        assert weapon_lv10.equippable.power_bonus >= weapon_lv1.equippable.power_bonus
    
    def test_generate_weapon_rarity_bonus(self):
        """Test rarity affects weapon power."""
        common = self.gen.generate_weapon(10, 10, 5, rarity=LootRarity.COMMON)
        legendary = self.gen.generate_weapon(10, 10, 5, rarity=LootRarity.LEGENDARY)
        
        # Legendary should be significantly more powerful
        assert legendary.equippable.power_bonus > common.equippable.power_bonus
        # Legendary should be golden color
        assert legendary.color == (255, 215, 0)
    
    def test_generate_armor_basic(self):
        """Test basic armor generation."""
        armor = self.gen.generate_armor(10, 10, 1)
        
        assert armor is not None
        assert armor.equippable is not None
        assert armor.equippable.slot == EquipmentSlots.OFF_HAND
        assert armor.equippable.defense_bonus > 0
        assert hasattr(armor, 'loot')
    
    def test_generate_armor_scaling(self):
        """Test armor defense scales with level."""
        armor_lv1 = self.gen.generate_armor(10, 10, 1, rarity=LootRarity.COMMON)
        armor_lv10 = self.gen.generate_armor(10, 10, 10, rarity=LootRarity.COMMON)
        
        # Higher level should have more defense
        assert armor_lv10.equippable.defense_bonus >= armor_lv1.equippable.defense_bonus
    
    def test_weapon_names_vary(self):
        """Test weapon names have variety."""
        names = set()
        for _ in range(20):
            weapon = self.gen.generate_weapon(10, 10, 5)
            names.add(weapon.name)
        
        # Should get at least 5 different names
        assert len(names) >= 5, f"Should have variety in names, got {names}"
    
    def test_should_monster_drop_loot_slimes(self):
        """Test slimes never drop loot."""
        for _ in range(10):
            assert not self.gen.should_monster_drop_loot("Green Slime", 1)
            assert not self.gen.should_monster_drop_loot("Large Slime", 5)
    
    def test_should_monster_drop_loot_bosses(self):
        """Test bosses always drop loot."""
        for _ in range(10):
            assert self.gen.should_monster_drop_loot("Dragon Lord", 10)
            assert self.gen.should_monster_drop_loot("Demon King", 15)
    
    def test_should_monster_drop_loot_probability(self):
        """Test normal monsters have probability-based drops."""
        results = []
        for _ in range(100):
            results.append(self.gen.should_monster_drop_loot("Orc", 5))
        
        # Should get some drops but not all
        drop_rate = sum(results) / len(results)
        assert 0.3 < drop_rate < 0.7, f"Orc drop rate should be ~50%, got {drop_rate:.2%}"


class TestLootGeneratorIntegration:
    """Integration tests for loot system."""
    
    def test_generate_multiple_items_different_rarities(self):
        """Test generating items produces variety."""
        gen = LootGenerator()
        items = []
        
        for _ in range(20):
            items.append(gen.generate_weapon(10, 10, 5))
        
        rarities = {item.loot.rarity for item in items}
        
        # Should get at least 2 different rarities
        assert len(rarities) >= 2, "Should have rarity variety"
    
    def test_loot_generator_singleton(self):
        """Test get_loot_generator returns singleton."""
        gen1 = get_loot_generator()
        gen2 = get_loot_generator()
        assert gen1 is gen2, "Should return same instance"


class TestLootIntegrationWithMonsters:
    """Test loot system integration with monster death."""
    
    def test_monster_death_can_drop_loot(self):
        """Test monsters can drop loot when they die."""
        from entity import Entity
        from components.fighter import Fighter
        from map_objects.game_map import GameMap
        from components.monster_equipment import drop_loot_from_monster
        
        # Create game map
        game_map = GameMap(50, 50, dungeon_level=5)
        
        # Create monster
        monster = Entity(
            10, 10, "o", (255, 0, 0), "Orc",
            fighter=Fighter(hp=10, defense=0, power=3),
            blocks=True
        )
        
        # Drop loot
        dropped_items = drop_loot_from_monster(monster, 10, 10, game_map)
        
        # Should potentially drop loot (probability based)
        # At level 5, Orcs have 50% chance
        # Running multiple times to test system works
        assert dropped_items is not None
        assert isinstance(dropped_items, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

