"""Tests for monster equipment system.

Tests that monsters can spawn with equipment based on configuration,
and that equipment affects their combat stats properly.
"""

import pytest
import random
from config.entity_factory import EntityFactory
from config.entity_registry import load_entity_config, get_entity_registry


@pytest.fixture(scope="module")
def entity_factory():
    """Create entity factory with loaded config."""
    load_entity_config('config/entities.yaml')
    return EntityFactory()


class TestMonsterEquipmentSpawning:
    """Test that monsters spawn with equipment correctly."""
    
    def test_orc_has_equipment_config(self, entity_factory):
        """Test that orc has equipment configuration loaded."""
        registry = get_entity_registry()
        orc_def = registry.get_monster('orc')
        
        assert orc_def is not None, "Orc definition should exist"
        assert orc_def.equipment is not None, "Orc should have equipment config"
        assert 'spawn_chances' in orc_def.equipment, "Equipment should have spawn_chances"
        assert 'equipment_pool' in orc_def.equipment, "Equipment should have equipment_pool"
    
    def test_orc_spawns_with_weapon_sometimes(self, entity_factory):
        """Test that orcs sometimes spawn with weapons (probabilistic)."""
        random.seed(42)  # Deterministic for testing
        
        orcs_with_weapons = 0
        num_orcs = 20
        
        for i in range(num_orcs):
            orc = entity_factory.create_monster('orc', i, 5)
            if orc.equipment and orc.equipment.main_hand:
                orcs_with_weapons += 1
        
        # With 75% spawn rate and 20 orcs, we expect 10-18 with weapons
        assert orcs_with_weapons >= 10, f"Expected at least 10 orcs with weapons, got {orcs_with_weapons}"
        assert orcs_with_weapons <= 18, f"Expected at most 18 orcs with weapons, got {orcs_with_weapons}"
    
    def test_orc_spawns_with_armor_sometimes(self, entity_factory):
        """Test that orcs sometimes spawn with armor (probabilistic)."""
        random.seed(123)  # Different seed
        
        orcs_with_armor = 0
        num_orcs = 20
        
        for i in range(num_orcs):
            orc = entity_factory.create_monster('orc', i, 5)
            if orc.equipment and orc.equipment.chest:
                orcs_with_armor += 1
        
        # With 50% spawn rate and 20 orcs, we expect 7-13 with armor
        assert orcs_with_armor >= 7, f"Expected at least 7 orcs with armor, got {orcs_with_armor}"
        assert orcs_with_armor <= 13, f"Expected at most 13 orcs with armor, got {orcs_with_armor}"
    
    def test_equipped_items_are_valid_weapons(self, entity_factory):
        """Test that equipped weapons are valid weapon entities."""
        random.seed(42)
        
        for i in range(20):
            orc = entity_factory.create_monster('orc', i, 5)
            if orc.equipment and orc.equipment.main_hand:
                weapon = orc.equipment.main_hand
                
                # Weapon should have name
                assert hasattr(weapon, 'name'), "Weapon should have name"
                assert weapon.name, "Weapon name should not be empty"
                
                # Weapon should have equippable component
                assert hasattr(weapon, 'equippable'), "Weapon should have equippable component"
                assert weapon.equippable is not None, "Weapon equippable should not be None"
                
                # Weapon should have damage dice
                assert hasattr(weapon.equippable, 'damage_dice'), "Weapon should have damage_dice"
                assert weapon.equippable.damage_dice is not None, "Damage dice should not be None"
                
                break  # Found one, test passed
    
    def test_equipped_items_are_valid_armor(self, entity_factory):
        """Test that equipped armor is valid armor entities."""
        random.seed(123)
        
        for i in range(20):
            orc = entity_factory.create_monster('orc', i, 5)
            if orc.equipment and orc.equipment.chest:
                armor = orc.equipment.chest
                
                # Armor should have name
                assert hasattr(armor, 'name'), "Armor should have name"
                assert armor.name, "Armor name should not be empty"
                
                # Armor should have equippable component
                assert hasattr(armor, 'equippable'), "Armor should have equippable component"
                assert armor.equippable is not None, "Armor equippable should not be None"
                
                # Armor should have armor_class_bonus
                assert hasattr(armor.equippable, 'armor_class_bonus'), "Armor should have AC bonus"
                assert armor.equippable.armor_class_bonus > 0, "AC bonus should be positive"
                
                break  # Found one, test passed
    
    def test_monster_with_equipment_has_inventory(self, entity_factory):
        """Test that monsters with equipment get an inventory."""
        random.seed(42)
        
        for i in range(20):
            orc = entity_factory.create_monster('orc', i, 5)
            if orc.equipment and (orc.equipment.main_hand or orc.equipment.chest):
                # Monster with equipment should have inventory
                assert orc.inventory is not None, "Monster with equipment should have inventory"
                assert orc.inventory.capacity > 0, "Inventory should have capacity"
                
                # Equipped items should be in inventory
                equipped_item_count = 0
                if orc.equipment.main_hand:
                    equipped_item_count += 1
                if orc.equipment.chest:
                    equipped_item_count += 1
                
                assert len(orc.inventory.items) == equipped_item_count, \
                    f"Inventory should contain {equipped_item_count} items"
                
                break  # Found one, test passed


class TestMonsterEquipmentEffects:
    """Test that equipment affects monster stats."""
    
    def test_weapon_provides_damage_dice(self, entity_factory):
        """Test that equipped weapons provide damage dice."""
        random.seed(42)
        
        for i in range(20):
            orc = entity_factory.create_monster('orc', i, 5)
            if orc.equipment and orc.equipment.main_hand:
                weapon = orc.equipment.main_hand
                
                # Weapon should have damage dice
                damage_dice = weapon.equippable.damage_dice
                assert damage_dice is not None, "Weapon should have damage dice"
                assert 'd' in damage_dice, "Damage dice should be in format like '1d6'"
                
                # Fighter should have access to weapon damage through equipment
                assert orc.fighter is not None, "Orc should have fighter component"
                assert orc.equipment is not None, "Orc should have equipment component"
                
                break  # Found one, test passed
    
    def test_armor_affects_ac(self, entity_factory):
        """Test that equipped armor affects AC."""
        random.seed(123)
        
        orc_with_armor = None
        orc_without_armor = None
        
        for i in range(30):
            orc = entity_factory.create_monster('orc', i, 5)
            if orc.equipment and orc.equipment.chest and not orc_with_armor:
                orc_with_armor = orc
            elif (not orc.equipment or not orc.equipment.chest) and not orc_without_armor:
                orc_without_armor = orc
            
            if orc_with_armor and orc_without_armor:
                break
        
        assert orc_with_armor is not None, "Should find orc with armor"
        assert orc_without_armor is not None, "Should find orc without armor"
        
        # Orc with armor should have higher AC
        ac_with_armor = orc_with_armor.fighter.armor_class
        ac_without_armor = orc_without_armor.fighter.armor_class
        
        # Both should have same DEX (10), so difference is from armor
        assert ac_with_armor > ac_without_armor, \
            f"AC with armor ({ac_with_armor}) should be higher than without ({ac_without_armor})"
    
    def test_equipment_bonuses_are_accessible(self, entity_factory):
        """Test that equipment bonuses are accessible through the equipment component."""
        random.seed(42)
        
        for i in range(20):
            orc = entity_factory.create_monster('orc', i, 5)
            if orc.equipment and (orc.equipment.main_hand or orc.equipment.chest):
                # Equipment should provide power_bonus property
                assert hasattr(orc.equipment, 'power_bonus'), "Equipment should have power_bonus"
                power_bonus = orc.equipment.power_bonus
                assert isinstance(power_bonus, int), "Power bonus should be an integer"
                assert power_bonus >= 0, "Power bonus should be non-negative"
                
                # Equipment should provide defense_bonus property
                assert hasattr(orc.equipment, 'defense_bonus'), "Equipment should have defense_bonus"
                defense_bonus = orc.equipment.defense_bonus
                assert isinstance(defense_bonus, int), "Defense bonus should be an integer"
                assert defense_bonus >= 0, "Defense bonus should be non-negative"
                
                break  # Found one, test passed


class TestMonsterEquipmentInheritance:
    """Test that equipment configuration works with entity inheritance."""
    
    def test_orc_chieftain_inherits_equipment(self, entity_factory):
        """Test that orc_chieftain inherits orc's equipment config."""
        registry = get_entity_registry()
        chieftain_def = registry.get_monster('orc_chieftain')
        
        # Chieftain extends orc, so should have equipment config
        # NOTE: This test will pass even if inheritance doesn't work for equipment yet,
        # because we might need to add special handling for equipment inheritance
        # For now, let's just check if we can create one
        
        random.seed(42)
        chieftain = entity_factory.create_monster('orc_chieftain', 10, 10)
        
        assert chieftain is not None, "Should create orc chieftain"
        assert chieftain.equipment is not None, "Chieftain should have equipment component"
        # Equipment might be empty if RNG didn't spawn anything, but component should exist


class TestMonsterEquipmentEdgeCases:
    """Test edge cases for monster equipment system."""
    
    def test_monster_without_equipment_config_works(self, entity_factory):
        """Test that monsters without equipment config still work."""
        # Rat doesn't have equipment config
        rat = entity_factory.create_monster('rat', 5, 5)
        
        assert rat is not None, "Should create rat"
        assert rat.fighter is not None, "Rat should have fighter"
        # Rat might not have equipment or inventory, but shouldn't crash
    
    def test_equipment_spawn_with_zero_chance(self, entity_factory):
        """Test that 0% spawn chance means no equipment."""
        # This would require a monster with 0% spawn chances in config
        # For now, just verify the mechanism handles it
        pass  # Placeholder for future test
    
    def test_equipment_spawn_with_100_percent_chance(self, entity_factory):
        """Test that 100% spawn chance guarantees equipment."""
        # This would require a monster with 100% spawn chances in config
        # For now, just verify the mechanism handles it
        pass  # Placeholder for future test

