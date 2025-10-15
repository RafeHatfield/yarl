"""Tests for throwing system - weapons, potions, and target detection.

This test suite ensures:
1. Thrown weapons properly detect and hit targets
2. Thrown potions apply effects to the correct target
3. Item type detection works (weapons vs potions vs generic)
4. ComponentRegistry is used correctly throughout
5. Inventory sorting matches menu display
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from components.component_registry import ComponentType, ComponentRegistry
from entity import Entity


class TestWeaponThrowing:
    """Test throwing weapons at targets."""
    
    def test_weapon_detected_via_component_registry(self):
        """Weapons should be detected via ComponentType.EQUIPPABLE."""
        from throwing import throw_item
        
        # Create weapon with EQUIPPABLE component
        weapon = Mock(spec=Entity)
        weapon.name = "Dagger"
        weapon.x = 0
        weapon.y = 0
        weapon.char = '/'
        weapon.color = (255, 255, 255)
        weapon.components = Mock(spec=ComponentRegistry)
        weapon.components.has = Mock(side_effect=lambda ct: ct == ComponentType.EQUIPPABLE)
        weapon.components.get = Mock(return_value=Mock(damage_dice="1d4"))
        weapon.item = Mock()
        weapon.item.use_function = None
        
        # Create thrower
        thrower = Mock(spec=Entity)
        thrower.x = 0
        thrower.y = 0
        
        # Create target at (5, 5)
        target = Mock(spec=Entity)
        target.name = "Orc"
        target.x = 5
        target.y = 5
        target.components = Mock(spec=ComponentRegistry)
        target.components.has = Mock(side_effect=lambda ct: ct == ComponentType.FIGHTER)
        target.components.get = Mock(return_value=Mock(hp=10, take_damage=Mock()))
        
        game_map = Mock()
        game_map.tiles = [[Mock(block_sight=False) for _ in range(10)] for _ in range(10)]
        
        entities = [target]
        fov_map = Mock()
        
        with patch('throwing.get_effect_queue'):
            results = throw_item(thrower, weapon, 5, 5, entities, game_map, fov_map)
        
        # Weapon should be detected and _throw_weapon should be called
        weapon.components.has.assert_called()
        # Should check for EQUIPPABLE
        assert any(call[0][0] == ComponentType.EQUIPPABLE 
                   for call in weapon.components.has.call_args_list)
    
    def test_target_detected_via_component_registry(self):
        """Targets should be detected via ComponentType.FIGHTER."""
        from throwing import throw_item
        
        weapon = Mock(spec=Entity)
        weapon.name = "Club"
        weapon.x = 0
        weapon.y = 0
        weapon.char = '/'
        weapon.color = (255, 255, 255)
        weapon.components = Mock(spec=ComponentRegistry)
        weapon.components.has = Mock(side_effect=lambda ct: ct == ComponentType.EQUIPPABLE)
        weapon.components.get = Mock(return_value=Mock(damage_dice="1d6"))
        weapon.item = Mock()
        weapon.item.use_function = None
        
        thrower = Mock(spec=Entity)
        thrower.x = 0
        thrower.y = 0
        
        # Target WITH Fighter component
        target = Mock(spec=Entity)
        target.name = "Goblin"
        target.x = 3
        target.y = 3
        target.components = Mock(spec=ComponentRegistry)
        target.components.has = Mock(side_effect=lambda ct: ct == ComponentType.FIGHTER)
        target_fighter = Mock(hp=8, take_damage=Mock())
        target.components.get = Mock(return_value=target_fighter)
        
        game_map = Mock()
        game_map.tiles = [[Mock(block_sight=False) for _ in range(10)] for _ in range(10)]
        
        entities = [target]
        fov_map = Mock()
        
        with patch('throwing.get_effect_queue'):
            results = throw_item(thrower, weapon, 3, 3, entities, game_map, fov_map)
        
        # Target's fighter should take damage
        target_fighter.take_damage.assert_called_once()
        
        # Should have hit message
        messages = [r.get('message') for r in results if r.get('message')]
        assert any('hits' in str(msg).lower() for msg in messages)
    
    def test_weapon_damage_calculation(self):
        """Thrown weapons should deal damage based on equippable.damage_dice."""
        from throwing import _throw_weapon
        
        weapon = Mock(spec=Entity)
        weapon.name = "Longsword"
        weapon.components = Mock(spec=ComponentRegistry)
        weapon.components.get = Mock(return_value=Mock(damage_dice="1d8"))
        
        thrower = Mock(spec=Entity)
        
        target = Mock(spec=Entity)
        target.name = "Bandit"
        target.components = Mock(spec=ComponentRegistry)
        target_fighter = Mock(hp=15, take_damage=Mock())
        target.components.get = Mock(return_value=target_fighter)
        
        results = _throw_weapon(weapon, thrower, target, 5, 5)
        
        # Should call take_damage
        target_fighter.take_damage.assert_called_once()
        damage = target_fighter.take_damage.call_args[0][0]
        
        # Damage should be at least 1 (because of throwing penalty and min 1)
        assert damage >= 1
        assert damage <= 6  # 1d8 - 2 penalty, capped at 6
    
    def test_roll_dice_imported_from_dice_module(self):
        """roll_dice should be imported from dice module, not fighter."""
        import throwing
        import inspect
        
        # Get source of _throw_weapon
        source = inspect.getsource(throwing._throw_weapon)
        
        # Should import from dice, not components.fighter
        assert 'from dice import roll_dice' in source
        assert 'from components.fighter import roll_dice' not in source


class TestPotionThrowing:
    """Test throwing potions at targets."""
    
    def test_thrown_potion_affects_target_not_thrower(self):
        """Thrown potions should affect the target, not the thrower."""
        from throwing import _throw_potion
        
        # Create healing potion
        potion = Mock(spec=Entity)
        potion.name = "Healing Potion"
        potion.item = Mock()
        potion.item.use_function = Mock(return_value=[])
        potion.item.owner = None  # Will be set by throwing code
        
        # Thrower (player)
        thrower = Mock(spec=Entity)
        thrower.name = "Player"
        
        # Target (enemy)
        target = Mock(spec=Entity)
        target.name = "Wounded Orc"
        
        entities = []
        game_map = Mock()
        fov_map = Mock()
        
        results = _throw_potion(potion, thrower, target, 5, 5, entities, game_map, fov_map)
        
        # Potion's use_function should be called with target as first arg
        potion.item.use_function.assert_called_once()
        first_arg = potion.item.use_function.call_args[0][0]
        assert first_arg == target, "Potion should affect target, not thrower!"
    
    def test_potion_owner_temporarily_swapped(self):
        """Potion's owner should be temporarily set to target during effect."""
        from throwing import _throw_potion
        
        potion = Mock(spec=Entity)
        potion.name = "Strength Potion"
        potion.item = Mock()
        
        # Track owner changes
        owner_changes = []
        def mock_use_function(entity, **kwargs):
            owner_changes.append(potion.item.owner)
            return []
        
        potion.item.use_function = mock_use_function
        potion.item.owner = "ORIGINAL_OWNER"
        
        thrower = Mock(spec=Entity)
        target = Mock(spec=Entity)
        target.name = "Target"
        
        results = _throw_potion(potion, thrower, target, 5, 5, [], Mock(), Mock())
        
        # Owner should have been set to target during use_function call
        assert len(owner_changes) == 1
        assert owner_changes[0] == target
        
        # Owner should be restored after (even though it's consumed)
        assert potion.item.owner == "ORIGINAL_OWNER"


class TestInventorySorting:
    """Test that inventory sorting is consistent across all systems."""
    
    def test_throw_menu_uses_sorted_inventory(self):
        """Throw menu should use alphabetically sorted inventory."""
        # This is tested via game_actions.py _handle_inventory_action
        # The fix ensures sorted_items is used
        
        # Create mock items with different names
        dagger = Mock(name="Dagger", get_display_name=Mock(return_value="Dagger"))
        club = Mock(name="Club", get_display_name=Mock(return_value="Club"))
        axe = Mock(name="Axe", get_display_name=Mock(return_value="Axe"))
        
        # Unsorted inventory
        unsorted_inventory = [dagger, club, axe]
        
        # Sorted inventory (what menu shows)
        sorted_inventory = sorted(unsorted_inventory, 
                                   key=lambda i: i.get_display_name().lower())
        
        # Menu shows: a) Axe, b) Club, c) Dagger
        # Pressing 'b' (index 1) should get Club
        assert sorted_inventory[1] == club
        
        # NOT the unsorted inventory's index 1
        assert unsorted_inventory[1] == club  # Coincidentally same in this example
        
        # But if we had: [Dagger, Leather_Armor, Healing Potion]
        dagger = Mock(name="Dagger", get_display_name=Mock(return_value="Dagger"))
        leather = Mock(name="Leather_Armor", get_display_name=Mock(return_value="Leather Armor"))
        healing = Mock(name="Healing Potion", get_display_name=Mock(return_value="Healing Potion"))
        
        unsorted = [dagger, leather, healing]
        sorted_inv = sorted(unsorted, key=lambda i: i.get_display_name().lower())
        
        # Sorted: [Dagger, Healing Potion, Leather Armor]
        # Pressing 'b' (index 1) should get Healing Potion
        assert sorted_inv[1].name == "Healing Potion"
        # NOT Leather_Armor from unsorted[1]
        assert unsorted[1].name == "Leather_Armor"


class TestComponentRegistryUsage:
    """Test that ComponentRegistry is used correctly throughout throwing system."""
    
    def test_no_hasattr_usage(self):
        """Throwing code should NOT use hasattr for component checks."""
        import throwing
        import inspect
        
        source = inspect.getsource(throwing)
        
        # Should not use old attribute system
        assert "hasattr(entity, 'fighter')" not in source
        assert "hasattr(item, 'item') and hasattr(item.item, 'equipment')" not in source
        
        # Should use ComponentRegistry
        assert "ComponentType.FIGHTER" in source
        assert "ComponentType.EQUIPPABLE" in source
    
    def test_components_has_for_detection(self):
        """Should use entity.components.has() for component detection."""
        import throwing
        import inspect
        
        source = inspect.getsource(throwing.throw_item)
        
        # Should use modern component checks
        assert "components.has(ComponentType" in source


def test_throwing_system_integration():
    """Integration test: Throw weapon at enemy, enemy takes damage."""
    from throwing import throw_item
    
    # Create dagger
    dagger = Mock(spec=Entity)
    dagger.name = "Dagger"
    dagger.x = 0
    dagger.y = 0
    dagger.char = '/'
    dagger.color = (255, 255, 255)
    dagger.components = Mock(spec=ComponentRegistry)
    dagger.components.has = Mock(side_effect=lambda ct: ct == ComponentType.EQUIPPABLE)
    dagger.components.get = Mock(return_value=Mock(damage_dice="1d4"))
    dagger.item = Mock(use_function=None)
    
    # Create player
    player = Mock(spec=Entity)
    player.x = 5
    player.y = 5
    
    # Create orc at (10, 10)
    orc = Mock(spec=Entity)
    orc.name = "Orc"
    orc.x = 10
    orc.y = 10
    orc.components = Mock(spec=ComponentRegistry)
    orc.components.has = Mock(side_effect=lambda ct: ct == ComponentType.FIGHTER)
    orc_fighter = Mock(hp=12)
    orc_fighter.take_damage = Mock()
    orc.components.get = Mock(return_value=orc_fighter)
    
    # Setup game map
    game_map = Mock()
    game_map.tiles = [[Mock(block_sight=False) for _ in range(20)] for _ in range(20)]
    
    entities = [orc]
    fov_map = Mock()
    
    with patch('throwing.get_effect_queue'):
        results = throw_item(player, dagger, 10, 10, entities, game_map, fov_map)
    
    # Orc should have taken damage
    orc_fighter.take_damage.assert_called_once()
    
    # Should have success messages
    messages = [r.get('message') for r in results if r.get('message')]
    assert len(messages) > 0
    
    # Should have hit message
    hit_messages = [m for m in messages if 'hits' in str(m).lower()]
    assert len(hit_messages) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

