"""Unit tests for bot auto-equipment functionality.

This test suite validates that the bot automatically equips better weapons
and armor to improve survivability during soak testing, without affecting
manual (human) play.

Test cases:
- Bot equips stronger weapon over weaker weapon
- Bot equips better armor over worse armor
- Bot prefers best items when multiple options available
- Weapon/armor evaluation functions work correctly
- Manual mode is unaffected by auto-equip logic
"""

import pytest
from unittest.mock import Mock

from io_layer.bot_equipment import (
    evaluate_weapon,
    evaluate_armor,
    auto_equip_better_items,
    _calculate_average_damage_from_dice,
)
from equipment_slots import EquipmentSlots
from components.component_registry import ComponentType


class TestWeaponEvaluation:
    """Test weapon scoring logic."""
    
    def test_evaluate_weapon_prefers_higher_damage(self):
        """Weapons with higher damage should score higher."""
        # Create dagger (1d4 = 2.5 avg damage)
        dagger = Mock()
        dagger.equippable = Mock()
        dagger.equippable.slot = EquipmentSlots.MAIN_HAND
        dagger.equippable.damage_min = 1
        dagger.equippable.damage_max = 4
        dagger.equippable.damage_dice = "1d4"
        dagger.equippable.to_hit_bonus = 1
        dagger.equippable.reach = 1
        dagger.equippable.power_bonus = 0
        
        # Create longsword (1d8 = 4.5 avg damage)
        longsword = Mock()
        longsword.equippable = Mock()
        longsword.equippable.slot = EquipmentSlots.MAIN_HAND
        longsword.equippable.damage_min = 1
        longsword.equippable.damage_max = 8
        longsword.equippable.damage_dice = "1d8"
        longsword.equippable.to_hit_bonus = 0
        longsword.equippable.reach = 1
        longsword.equippable.power_bonus = 0
        
        dagger_score = evaluate_weapon(dagger)
        longsword_score = evaluate_weapon(longsword)
        
        assert longsword_score > dagger_score, \
            f"Longsword (1d8) should score higher than dagger (1d4), got {longsword_score} vs {dagger_score}"
    
    def test_evaluate_weapon_considers_to_hit_bonus(self):
        """To-hit bonus should improve weapon score."""
        # Create club (1d6, +0 to-hit)
        club = Mock()
        club.equippable = Mock()
        club.equippable.slot = EquipmentSlots.MAIN_HAND
        club.equippable.damage_min = 1
        club.equippable.damage_max = 6
        club.equippable.damage_dice = "1d6"
        club.equippable.to_hit_bonus = 0
        club.equippable.reach = 1
        club.equippable.power_bonus = 0
        
        # Create shortsword (1d6, +1 to-hit)
        shortsword = Mock()
        shortsword.equippable = Mock()
        shortsword.equippable.slot = EquipmentSlots.MAIN_HAND
        shortsword.equippable.damage_min = 1
        shortsword.equippable.damage_max = 6
        shortsword.equippable.damage_dice = "1d6"
        shortsword.equippable.to_hit_bonus = 1
        shortsword.equippable.reach = 1
        shortsword.equippable.power_bonus = 0
        
        club_score = evaluate_weapon(club)
        shortsword_score = evaluate_weapon(shortsword)
        
        assert shortsword_score > club_score, \
            f"Shortsword (+1 to-hit) should score higher than club (+0), got {shortsword_score} vs {club_score}"
    
    def test_evaluate_weapon_non_weapon_returns_zero(self):
        """Non-weapon items should return 0 score."""
        # Create shield (no damage)
        shield = Mock()
        shield.equippable = Mock()
        shield.equippable.slot = EquipmentSlots.OFF_HAND
        shield.equippable.damage_min = 0
        shield.equippable.damage_max = 0
        shield.equippable.damage_dice = None
        
        score = evaluate_weapon(shield)
        assert score == 0, f"Shield (no damage) should score 0, got {score}"
    
    def test_calculate_average_damage_from_dice(self):
        """Dice notation should be parsed correctly."""
        assert _calculate_average_damage_from_dice("1d4") == 2.5
        assert _calculate_average_damage_from_dice("1d6") == 3.5
        assert _calculate_average_damage_from_dice("1d8") == 4.5
        assert _calculate_average_damage_from_dice("2d6") == 7.0


class TestArmorEvaluation:
    """Test armor scoring logic."""
    
    def test_evaluate_armor_prefers_higher_ac(self):
        """Armor with higher AC should score higher."""
        # Create leather armor (+2 AC)
        leather = Mock()
        leather.equippable = Mock()
        leather.equippable.slot = EquipmentSlots.CHEST
        leather.equippable.armor_class_bonus = 2
        leather.equippable.defense_min = 0
        leather.equippable.defense_max = 0
        leather.equippable.defense_bonus = 0
        leather.equippable.armor_type = "light"
        
        # Create chain mail (+4 AC)
        chain = Mock()
        chain.equippable = Mock()
        chain.equippable.slot = EquipmentSlots.CHEST
        chain.equippable.armor_class_bonus = 4
        chain.equippable.defense_min = 0
        chain.equippable.defense_max = 0
        chain.equippable.defense_bonus = 0
        chain.equippable.armor_type = "medium"
        
        leather_score = evaluate_armor(leather)
        chain_score = evaluate_armor(chain)
        
        assert chain_score > leather_score, \
            f"Chain mail (+4 AC) should score higher than leather (+2 AC), got {chain_score} vs {leather_score}"
    
    def test_evaluate_armor_non_armor_returns_zero(self):
        """Non-armor items should return 0 score."""
        # Create weapon (no AC bonus)
        sword = Mock()
        sword.equippable = Mock()
        sword.equippable.armor_class_bonus = 0
        sword.equippable.defense_bonus = 0
        
        score = evaluate_armor(sword)
        assert score == 0, f"Sword (no armor) should score 0, got {score}"


class TestBotAutoEquip:
    """Test bot automatic equipment functionality."""
    
    def test_bot_equips_stronger_weapon(self):
        """Bot should automatically equip stronger weapon over weaker one."""
        # Create player with inventory and equipment
        player = Mock()
        
        # Create dagger (1d4, weaker)
        dagger = Mock()
        dagger.name = "dagger"
        dagger.equippable = Mock()
        dagger.equippable.slot = EquipmentSlots.MAIN_HAND
        dagger.equippable.damage_min = 1
        dagger.equippable.damage_max = 4
        dagger.equippable.damage_dice = "1d4"
        dagger.equippable.to_hit_bonus = 1
        dagger.equippable.reach = 1
        dagger.equippable.power_bonus = 0
        
        # Create longsword (1d8, stronger)
        longsword = Mock()
        longsword.name = "longsword"
        longsword.equippable = Mock()
        longsword.equippable.slot = EquipmentSlots.MAIN_HAND
        longsword.equippable.damage_min = 1
        longsword.equippable.damage_max = 8
        longsword.equippable.damage_dice = "1d8"
        longsword.equippable.to_hit_bonus = 0
        longsword.equippable.reach = 1
        longsword.equippable.power_bonus = 0
        
        # Setup inventory with both weapons
        inventory = Mock()
        inventory.items = [dagger, longsword]
        
        # Setup equipment with dagger equipped
        equipment = Mock()
        equipment.main_hand = dagger
        equipment.off_hand = None
        equipment.head = None
        equipment.chest = None
        equipment.feet = None
        equipment.toggle_equip = Mock()
        
        # Setup player get_component_optional
        def get_component(comp_type):
            if comp_type == ComponentType.INVENTORY:
                return inventory
            elif comp_type == ComponentType.EQUIPMENT:
                return equipment
            return None
        
        player.get_component_optional = Mock(side_effect=get_component)
        
        # Act: Bot auto-equips
        auto_equip_better_items(player, is_bot_mode=True)
        
        # Assert: Should equip longsword
        equipment.toggle_equip.assert_called_with(longsword)
    
    def test_bot_equips_better_armor(self):
        """Bot should automatically equip better armor over worse armor."""
        # Create player with inventory and equipment
        player = Mock()
        
        # Create leather armor (+2 AC, worse)
        leather = Mock()
        leather.name = "leather_armor"
        leather.equippable = Mock()
        leather.equippable.slot = EquipmentSlots.CHEST
        leather.equippable.armor_class_bonus = 2
        leather.equippable.defense_min = 0
        leather.equippable.defense_max = 0
        leather.equippable.defense_bonus = 0
        leather.equippable.armor_type = "light"
        
        # Create chain mail (+4 AC, better)
        chain = Mock()
        chain.name = "chain_mail"
        chain.equippable = Mock()
        chain.equippable.slot = EquipmentSlots.CHEST
        chain.equippable.armor_class_bonus = 4
        chain.equippable.defense_min = 0
        chain.equippable.defense_max = 0
        chain.equippable.defense_bonus = 0
        chain.equippable.armor_type = "medium"
        
        # Setup inventory with both armors
        inventory = Mock()
        inventory.items = [leather, chain]
        
        # Setup equipment with leather equipped
        equipment = Mock()
        equipment.main_hand = None
        equipment.off_hand = None
        equipment.head = None
        equipment.chest = leather
        equipment.feet = None
        equipment.toggle_equip = Mock()
        
        # Setup player get_component_optional
        def get_component(comp_type):
            if comp_type == ComponentType.INVENTORY:
                return inventory
            elif comp_type == ComponentType.EQUIPMENT:
                return equipment
            return None
        
        player.get_component_optional = Mock(side_effect=get_component)
        
        # Act: Bot auto-equips
        auto_equip_better_items(player, is_bot_mode=True)
        
        # Assert: Should equip chain mail
        equipment.toggle_equip.assert_called_with(chain)
    
    def test_bot_does_not_equip_if_already_has_best(self):
        """Bot should not re-equip if already has the best item equipped."""
        # Create player with inventory and equipment
        player = Mock()
        
        # Create longsword (best weapon)
        longsword = Mock()
        longsword.name = "longsword"
        longsword.equippable = Mock()
        longsword.equippable.slot = EquipmentSlots.MAIN_HAND
        longsword.equippable.damage_min = 1
        longsword.equippable.damage_max = 8
        longsword.equippable.damage_dice = "1d8"
        longsword.equippable.to_hit_bonus = 0
        longsword.equippable.reach = 1
        longsword.equippable.power_bonus = 0
        
        # Create dagger (weaker weapon in inventory)
        dagger = Mock()
        dagger.name = "dagger"
        dagger.equippable = Mock()
        dagger.equippable.slot = EquipmentSlots.MAIN_HAND
        dagger.equippable.damage_min = 1
        dagger.equippable.damage_max = 4
        dagger.equippable.damage_dice = "1d4"
        dagger.equippable.to_hit_bonus = 1
        dagger.equippable.reach = 1
        dagger.equippable.power_bonus = 0
        
        # Setup inventory with dagger
        inventory = Mock()
        inventory.items = [dagger]
        
        # Setup equipment with longsword already equipped
        equipment = Mock()
        equipment.main_hand = longsword
        equipment.off_hand = None
        equipment.head = None
        equipment.chest = None
        equipment.feet = None
        equipment.toggle_equip = Mock()
        
        # Setup player get_component_optional
        def get_component(comp_type):
            if comp_type == ComponentType.INVENTORY:
                return inventory
            elif comp_type == ComponentType.EQUIPMENT:
                return equipment
            return None
        
        player.get_component_optional = Mock(side_effect=get_component)
        
        # Act: Bot auto-equips
        auto_equip_better_items(player, is_bot_mode=True)
        
        # Assert: Should NOT re-equip (already has best)
        equipment.toggle_equip.assert_not_called()
    
    def test_bot_does_not_equip_in_manual_mode(self):
        """Bot auto-equip should not run when is_bot_mode=False."""
        # Create player with inventory and equipment
        player = Mock()
        
        # Create weapons
        dagger = Mock()
        dagger.name = "dagger"
        dagger.equippable = Mock()
        dagger.equippable.slot = EquipmentSlots.MAIN_HAND
        dagger.equippable.damage_min = 1
        dagger.equippable.damage_max = 4
        dagger.equippable.damage_dice = "1d4"
        dagger.equippable.to_hit_bonus = 1
        dagger.equippable.reach = 1
        dagger.equippable.power_bonus = 0
        
        longsword = Mock()
        longsword.name = "longsword"
        longsword.equippable = Mock()
        longsword.equippable.slot = EquipmentSlots.MAIN_HAND
        longsword.equippable.damage_min = 1
        longsword.equippable.damage_max = 8
        longsword.equippable.damage_dice = "1d8"
        longsword.equippable.to_hit_bonus = 0
        longsword.equippable.reach = 1
        longsword.equippable.power_bonus = 0
        
        # Setup inventory
        inventory = Mock()
        inventory.items = [dagger, longsword]
        
        # Setup equipment
        equipment = Mock()
        equipment.main_hand = dagger
        equipment.off_hand = None
        equipment.head = None
        equipment.chest = None
        equipment.feet = None
        equipment.toggle_equip = Mock()
        
        # Setup player
        def get_component(comp_type):
            if comp_type == ComponentType.INVENTORY:
                return inventory
            elif comp_type == ComponentType.EQUIPMENT:
                return equipment
            return None
        
        player.get_component_optional = Mock(side_effect=get_component)
        
        # Act: Try to auto-equip with is_bot_mode=False
        auto_equip_better_items(player, is_bot_mode=False)
        
        # Assert: Should NOT equip anything (manual mode)
        equipment.toggle_equip.assert_not_called()
    
    def test_bot_handles_multiple_armor_slots(self):
        """Bot should equip best items across multiple armor slots."""
        # Create player with inventory and equipment
        player = Mock()
        
        # Create helmet
        helmet = Mock()
        helmet.name = "helmet"
        helmet.equippable = Mock()
        helmet.equippable.slot = EquipmentSlots.HEAD
        helmet.equippable.armor_class_bonus = 1
        helmet.equippable.defense_min = 0
        helmet.equippable.defense_max = 0
        helmet.equippable.defense_bonus = 0
        helmet.equippable.armor_type = "light"
        
        # Create chest armor
        chest_armor = Mock()
        chest_armor.name = "chest_armor"
        chest_armor.equippable = Mock()
        chest_armor.equippable.slot = EquipmentSlots.CHEST
        chest_armor.equippable.armor_class_bonus = 3
        chest_armor.equippable.defense_min = 0
        chest_armor.equippable.defense_max = 0
        chest_armor.equippable.defense_bonus = 0
        chest_armor.equippable.armor_type = "light"
        
        # Setup inventory
        inventory = Mock()
        inventory.items = [helmet, chest_armor]
        
        # Setup equipment (nothing equipped)
        equipment = Mock()
        equipment.main_hand = None
        equipment.off_hand = None
        equipment.head = None
        equipment.chest = None
        equipment.feet = None
        equipment.toggle_equip = Mock()
        
        # Setup player
        def get_component(comp_type):
            if comp_type == ComponentType.INVENTORY:
                return inventory
            elif comp_type == ComponentType.EQUIPMENT:
                return equipment
            return None
        
        player.get_component_optional = Mock(side_effect=get_component)
        
        # Act: Bot auto-equips
        auto_equip_better_items(player, is_bot_mode=True)
        
        # Assert: Should equip both items
        assert equipment.toggle_equip.call_count == 2
        # Check that both items were equipped (order doesn't matter)
        calls = [call.args[0] for call in equipment.toggle_equip.call_args_list]
        assert helmet in calls
        assert chest_armor in calls

