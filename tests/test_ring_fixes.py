"""Tests for ring identification and Ring of Invisibility fixes.

This test suite verifies:
1. Equipment auto-identifies when equipped
2. Ring of Invisibility grants invisibility when entering new levels
"""

import pytest
from entity import Entity
from components.fighter import Fighter
from components.inventory import Inventory
from components.equipment import Equipment
from components.equippable import Equippable
from components.ring import Ring, RingEffect
from components.item import Item
from components.component_registry import ComponentType
from components.status_effects import StatusEffectManager
from equipment_slots import EquipmentSlots


def create_test_player():
    """Create a test player with all necessary components."""
    fighter = Fighter(hp=100, defense=10, power=10)
    inventory = Inventory(capacity=20)
    equipment = Equipment()
    status_effects = StatusEffectManager(None)  # Will set owner after creation
    
    player = Entity(
        x=0, y=0,
        char='@',
        color=(255, 255, 255),
        name="Test Player",
        blocks=True,
        fighter=fighter,
        inventory=inventory,
        equipment=equipment
    )
    
    # Set status effects
    player.status_effects = status_effects
    status_effects.owner = player
    
    return player


def create_test_ring(name="Test Ring", ring_effect=RingEffect.REGENERATION, identified=False):
    """Create a test ring entity."""
    ring_component = Ring(
        ring_effect=ring_effect,
        effect_strength=5
    )
    
    equippable_component = Equippable(
        slot=EquipmentSlots.RING
    )
    
    item_component = Item()
    item_component.identified = identified
    if not identified:
        item_component.appearance = "copper ring"  # Unidentified appearance
    
    ring_entity = Entity(
        x=0, y=0,
        char='=',
        color=(200, 200, 200),
        name=name,
        item=item_component,
        equippable=equippable_component
    )
    
    # Attach ring component
    ring_entity.ring = ring_component
    ring_component.owner = ring_entity
    ring_entity.components.add(ComponentType.RING, ring_component)
    
    return ring_entity


class TestEquipmentAutoIdentification:
    """Test that equipment auto-identifies when equipped."""
    
    def test_unidentified_ring_becomes_identified_on_equip(self):
        """Equipping an unidentified ring should identify it."""
        player = create_test_player()
        ring = create_test_ring("Ring of Protection", RingEffect.PROTECTION, identified=False)
        
        # Verify ring starts unidentified
        assert not ring.item.identified, "Ring should start unidentified"
        assert ring.item.appearance == "copper ring"
        
        # Add to inventory and equip
        player.inventory.add_item(ring)
        results = player.equipment.toggle_equip(ring)
        
        # Ring should now be identified
        assert ring.item.identified, "Ring should be identified after equipping"
        
        # Should have identification message in results
        has_id_message = any(
            'identified' in result or 'recognize' in str(result.get('message', '')).lower()
            for result in results
        )
        assert has_id_message, "Should have identification message in results"
    
    def test_already_identified_ring_no_duplicate_message(self):
        """Equipping an already identified ring should not show identification message."""
        player = create_test_player()
        ring = create_test_ring("Ring of Strength", RingEffect.STRENGTH, identified=True)
        
        assert ring.item.identified, "Ring should start identified"
        
        player.inventory.add_item(ring)
        results = player.equipment.toggle_equip(ring)
        
        # Should not have identification message
        has_id_message = any(
            'identified' in result or 'recognize' in str(result.get('message', '')).lower()
            for result in results
        )
        assert not has_id_message, "Should NOT have identification message for already identified item"
    
    def test_display_name_updates_after_identification(self):
        """Ring display name should update after identification."""
        player = create_test_player()
        ring = create_test_ring("Ring of Might", RingEffect.MIGHT, identified=False)
        
        # Unidentified display name
        display_before = ring.item.get_display_name()
        assert "copper ring" in display_before.lower(), f"Should show unidentified name, got: {display_before}"
        
        # Equip (which identifies)
        player.inventory.add_item(ring)
        player.equipment.toggle_equip(ring)
        
        # Identified display name
        display_after = ring.item.get_display_name()
        assert "Ring of Might" in display_after, f"Should show real name after ID, got: {display_after}"


class TestRingOfInvisibility:
    """Test Ring of Invisibility functionality."""
    
    def test_ring_of_invisibility_grants_invisibility_on_new_level(self):
        """Ring of Invisibility should grant invisibility when on_new_level is called."""
        player = create_test_player()
        ring = create_test_ring("Ring of Invisibility", RingEffect.INVISIBILITY, identified=True)
        
        # Verify player is not invisible
        assert not player.invisible, "Player should not be invisible initially"
        
        # Trigger new level effect
        results = ring.ring.on_new_level(player)
        
        # Player should now be invisible
        assert player.invisible, "Player should be invisible after Ring of Invisibility triggers"
        
        # Should have status effect
        assert player.status_effects.has_effect('invisibility'), \
            "Player should have invisibility status effect"
        
        # Should have message
        has_invis_message = any(
            'shimmers' in str(result.get('message', '')).lower() or
            'invisible' in str(result.get('message', '')).lower()
            for result in results
        )
        assert has_invis_message, "Should have invisibility message"
    
    def test_ring_invisibility_duration(self):
        """Ring of Invisibility should grant invisibility for effect_strength turns."""
        player = create_test_player()
        ring = create_test_ring("Ring of Invisibility", RingEffect.INVISIBILITY, identified=True)
        
        # Ring has effect_strength = 5 (from create_test_ring)
        assert ring.ring.effect_strength == 5
        
        # Trigger new level
        ring.ring.on_new_level(player)
        
        # Check invisibility effect duration
        invis_effect = player.status_effects.get_effect('invisibility')
        assert invis_effect is not None, "Should have invisibility effect"
        assert invis_effect.duration == 5, f"Duration should be 5, got {invis_effect.duration}"
    
    def test_two_rings_of_invisibility_do_not_stack(self):
        """Two Rings of Invisibility should not stack duration."""
        player = create_test_player()
        ring1 = create_test_ring("Ring of Invisibility 1", RingEffect.INVISIBILITY, identified=True)
        ring2 = create_test_ring("Ring of Invisibility 2", RingEffect.INVISIBILITY, identified=True)
        
        # Trigger both
        ring1.ring.on_new_level(player)
        ring2.ring.on_new_level(player)
        
        # Should only have one invisibility effect (not stacked)
        # The second one either replaces or doesn't add a duplicate
        invis_effect = player.status_effects.get_effect('invisibility')
        assert invis_effect is not None
        # Duration should be 5 (not 10)
        assert invis_effect.duration <= 5, \
            "Duration should not stack from two rings"
    
    def test_other_rings_do_not_trigger_invisibility(self):
        """Other ring types should not grant invisibility."""
        player = create_test_player()
        ring = create_test_ring("Ring of Protection", RingEffect.PROTECTION, identified=True)
        
        # Trigger new level
        results = ring.ring.on_new_level(player)
        
        # Should not be invisible
        assert not player.invisible, "Ring of Protection should not grant invisibility"
        assert not player.status_effects.has_effect('invisibility'), \
            "Should not have invisibility status effect"
        
        # Should have no results (or empty results)
        assert len(results) == 0, "Ring of Protection should not produce new level effects"


class TestRingOnNewLevelIntegration:
    """Test that ring effects integrate properly with game flow."""
    
    def test_equipped_ring_triggers_on_stairs(self):
        """When equipped, Ring of Invisibility should trigger when taking stairs."""
        player = create_test_player()
        ring = create_test_ring("Ring of Invisibility", RingEffect.INVISIBILITY, identified=True)
        
        # Equip ring
        player.inventory.add_item(ring)
        player.equipment.toggle_equip(ring)
        
        # Verify ring is equipped
        assert player.equipment.left_ring == ring or player.equipment.right_ring == ring
        
        # Simulate stairs logic (from game_actions.py)
        rings = [player.equipment.left_ring, player.equipment.right_ring]
        for ring_entity in rings:
            if ring_entity and hasattr(ring_entity, 'ring') and ring_entity.ring:
                ring_results = ring_entity.ring.on_new_level(player)
                # Ring of Invisibility should produce results
                if ring_entity == ring:
                    assert len(ring_results) > 0, "Ring of Invisibility should produce results"
        
        # Player should be invisible
        assert player.invisible, "Player should be invisible after stairs with Ring of Invisibility"
    
    def test_unequipped_ring_does_not_trigger(self):
        """Unequipped Ring of Invisibility should not grant invisibility."""
        player = create_test_player()
        ring = create_test_ring("Ring of Invisibility", RingEffect.INVISIBILITY, identified=True)
        
        # Add to inventory but don't equip
        player.inventory.add_item(ring)
        
        # Verify not equipped
        assert player.equipment.left_ring != ring and player.equipment.right_ring != ring
        
        # Simulate stairs logic (checks equipped rings only)
        rings = [player.equipment.left_ring, player.equipment.right_ring]
        for ring_entity in rings:
            if ring_entity and hasattr(ring_entity, 'ring') and ring_entity.ring:
                ring_entity.ring.on_new_level(player)
        
        # Player should NOT be invisible
        assert not player.invisible, "Player should not be invisible if ring is not equipped"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

