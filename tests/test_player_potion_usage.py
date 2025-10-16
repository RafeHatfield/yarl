"""Test that player can use all potions without errors.

This test ensures that the player entity has ALL required components
to use every potion type in the game. Previously, missing StatusEffectManager
caused crashes when using buff/debuff potions.

BUG FIXED: Player missing status_effects component
ROOT CAUSE: Entity.create_player() didn't include StatusEffectManager
SOLUTION: Auto-create StatusEffectManager in create_player()
"""

import pytest
from unittest.mock import Mock, MagicMock

from entity import Entity
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from components.equipment import Equipment
from components.status_effects import StatusEffectManager
from components.item import Item
from item_functions import (
    cast_heal,
    drink_speed_potion,
    drink_regeneration_potion,
    drink_invisibility_potion,
    drink_levitation_potion,
    drink_protection_potion,
    drink_heroism_potion,
    drink_weakness_potion,
    drink_blindness_potion,
    drink_paralysis_potion,
)


@pytest.fixture
def player():
    """Create a fully-configured player entity."""
    fighter = Fighter(hp=100, defense=2, power=5, base_max_hp=100, base_defense=2, base_power=5)
    inventory = Inventory(26)
    level_comp = Level()
    equipment = Equipment()
    
    # This should auto-create StatusEffectManager!
    player = Entity.create_player(
        x=5, y=5,
        fighter=fighter,
        inventory=inventory,
        level=level_comp,
        equipment=equipment
    )
    
    return player


class TestPlayerHasRequiredComponents:
    """Test that player has all components needed for gameplay."""
    
    def test_player_has_fighter(self, player):
        """Player must have Fighter component."""
        assert player.fighter is not None
        assert player.fighter.hp > 0
    
    def test_player_has_inventory(self, player):
        """Player must have Inventory component."""
        assert player.inventory is not None
        assert player.inventory.capacity > 0
    
    def test_player_has_level(self, player):
        """Player must have Level component."""
        assert player.level is not None
    
    def test_player_has_equipment(self, player):
        """Player must have Equipment component."""
        assert player.equipment is not None
    
    def test_player_has_status_effects(self, player):
        """Player MUST have StatusEffectManager component!
        
        BUG: This was missing, causing crashes when using potions!
        """
        assert player.status_effects is not None
        assert isinstance(player.status_effects, StatusEffectManager)
        
        # Verify it's functional
        assert hasattr(player.status_effects, 'add_effect')
        assert hasattr(player.status_effects, 'get_effect')
        assert hasattr(player.status_effects, 'active_effects')


class TestPlayerCanUseAllPotions:
    """Test that player can use every potion type without crashing.
    
    These tests verify that all required components exist and are functional.
    """
    
    def test_player_can_use_healing_potion(self, player):
        """Test healing potion usage."""
        # Damage player first
        player.fighter.hp = 50
        
        # Use healing potion
        results = cast_heal(player, heal_amount=40)
        
        # Should not crash and should heal
        assert len(results) > 0
        assert results[0].get('consumed') is True
        assert player.fighter.hp == 90  # 50 + 40
    
    def test_player_can_use_speed_potion(self, player):
        """Test speed potion usage.
        
        BUG: This would crash if status_effects is None!
        """
        results = drink_speed_potion(player)
        
        # Should not crash
        assert len(results) > 0
        assert results[0].get('consumed') is True
        
        # Should have speed effect
        speed_effect = player.status_effects.get_effect('speed')
        assert speed_effect is not None
        assert speed_effect.duration > 0
    
    def test_player_can_use_regeneration_potion(self, player):
        """Test regeneration potion usage.
        
        BUG: This crashed with 'NoneType' object has no attribute 'add_effect'!
        """
        results = drink_regeneration_potion(player)
        
        # Should not crash
        assert len(results) > 0
        assert results[0].get('consumed') is True
        
        # Should have regen effect
        regen_effect = player.status_effects.get_effect('regeneration')
        assert regen_effect is not None
    
    def test_player_can_use_invisibility_potion(self, player):
        """Test invisibility potion usage."""
        results = drink_invisibility_potion(player)
        
        assert len(results) > 0
        assert results[0].get('consumed') is True
        
        invis_effect = player.status_effects.get_effect('invisibility')
        assert invis_effect is not None
    
    def test_player_can_use_levitation_potion(self, player):
        """Test levitation potion usage."""
        results = drink_levitation_potion(player)
        
        assert len(results) > 0
        assert results[0].get('consumed') is True
        
        levitation_effect = player.status_effects.get_effect('levitation')
        assert levitation_effect is not None
    
    def test_player_can_use_protection_potion(self, player):
        """Test protection potion usage."""
        results = drink_protection_potion(player)
        
        assert len(results) > 0
        assert results[0].get('consumed') is True
        
        protection_effect = player.status_effects.get_effect('protection')
        assert protection_effect is not None
    
    def test_player_can_use_heroism_potion(self, player):
        """Test heroism potion usage."""
        results = drink_heroism_potion(player)
        
        assert len(results) > 0
        assert results[0].get('consumed') is True
        
        heroism_effect = player.status_effects.get_effect('heroism')
        assert heroism_effect is not None
    
    def test_player_can_use_weakness_potion(self, player):
        """Test weakness potion usage (self-inflicted debuff)."""
        results = drink_weakness_potion(player)
        
        assert len(results) > 0
        assert results[0].get('consumed') is True
        
        weakness_effect = player.status_effects.get_effect('weakness')
        assert weakness_effect is not None
    
    def test_player_can_use_blindness_potion(self, player):
        """Test blindness potion usage (self-inflicted debuff)."""
        results = drink_blindness_potion(player)
        
        assert len(results) > 0
        assert results[0].get('consumed') is True
        
        blindness_effect = player.status_effects.get_effect('blindness')
        assert blindness_effect is not None
    
    def test_player_can_use_paralysis_potion(self, player):
        """Test paralysis potion usage (self-inflicted debuff)."""
        results = drink_paralysis_potion(player)
        
        assert len(results) > 0
        assert results[0].get('consumed') is True
        
        paralysis_effect = player.status_effects.get_effect('paralysis')
        assert paralysis_effect is not None


class TestPlayerPotionIntegration:
    """Integration tests for player potion usage through inventory."""
    
    def test_player_can_drink_potion_from_inventory(self, player):
        """Test full flow: add potion to inventory → use it."""
        # Create a speed potion
        speed_potion = Entity(
            x=0, y=0, char='!', color=(0, 255, 255), name='Speed Potion',
            item=Item(use_function=drink_speed_potion, identified=True)
        )
        
        # Add to inventory
        player.inventory.add_item(speed_potion)
        
        # Use from inventory
        results = player.inventory.use(speed_potion)
        
        # Should not crash and should consume
        assert len(results) > 0
        assert any(r.get('consumed') for r in results)
        
        # Should have effect
        speed_effect = player.status_effects.get_effect('speed')
        assert speed_effect is not None
    
    def test_player_can_use_multiple_buff_potions(self, player):
        """Test stacking multiple buffs."""
        # Use speed potion
        drink_speed_potion(player)
        # Use protection potion
        drink_protection_potion(player)
        # Use heroism potion
        drink_heroism_potion(player)
        
        # Should have all 3 effects
        assert player.status_effects.get_effect('speed') is not None
        assert player.status_effects.get_effect('protection') is not None
        assert player.status_effects.get_effect('heroism') is not None
        
        # Should have 3 active effects
        assert len(player.status_effects.active_effects) == 3
    
    def test_player_status_effects_survive_turn_processing(self, player):
        """Test status effects persist across turns."""
        # Add speed effect
        drink_speed_potion(player)
        
        initial_duration = player.status_effects.get_effect('speed').duration
        
        # Process turn
        player.status_effects.process_turn_start()
        
        # Effect should still exist but duration decreased
        speed_effect = player.status_effects.get_effect('speed')
        assert speed_effect is not None
        assert speed_effect.duration == initial_duration - 1


class TestPlayerComponentDefaults:
    """Test that create_player provides sensible defaults."""
    
    def test_create_player_auto_creates_status_effects(self):
        """If status_effects not provided, should auto-create."""
        player = Entity.create_player(
            x=5, y=5,
            fighter=Fighter(100, 2, 5, 100, 2, 5),
            inventory=Inventory(26),
            level=Level(),
            equipment=Equipment()
            # Note: NOT providing status_effects!
        )
        
        # Should auto-create it!
        assert player.status_effects is not None
        assert isinstance(player.status_effects, StatusEffectManager)
    
    def test_create_player_accepts_custom_status_effects(self):
        """If status_effects provided, should use it."""
        custom_status_manager = StatusEffectManager()
        
        player = Entity.create_player(
            x=5, y=5,
            fighter=Fighter(100, 2, 5, 100, 2, 5),
            inventory=Inventory(26),
            level=Level(),
            equipment=Equipment(),
            status_effects=custom_status_manager
        )
        
        # Should use the provided one
        assert player.status_effects is custom_status_manager


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

