"""Phase 22.2.3: Net Arrow Unit Tests.

Tests that net_arrow special ammo:
- Applies entangled effect on hit with 50% chance
- Entangled effect blocks movement for 1 turn
- Ammo is consumed on hit AND miss
- Effects are deterministic under seeded RNG
"""

import pytest
import random
from entity import Entity
from components.fighter import Fighter
from components.equipment import Equipment
from components.equippable import Equippable
from components.item import Item
from components.inventory import Inventory
from components.component_registry import ComponentType
from equipment_slots import EquipmentSlots
from config.entity_factory import get_entity_factory


@pytest.mark.fast
def test_net_arrow_applies_entangled_on_hit():
    """Test that net arrows apply entangled effect on hit (with seeded RNG for 50% chance)."""
    
    # Seed for determinism - choose a seed that triggers the effect
    random.seed(1337)
    
    # Create player with shortbow
    player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
    player.fighter = Fighter(hp=50, defense=5, power=5, strength=14, dexterity=18, constitution=14)
    player.equipment = Equipment()
    player.inventory = Inventory(26)
    
    # Create shortbow
    factory = get_entity_factory()
    shortbow = factory.create_weapon('shortbow', 0, 0)
    player.equipment.toggle_equip(shortbow)
    
    # Create net arrows
    net_arrows = factory.create_special_ammo('net_arrow', 0, 0)
    assert net_arrows is not None, "Net arrows should be created"
    assert net_arrows.item.quantity == 8, "Net arrows should start with 8 quantity"
    assert net_arrows.ammo_effect_type == 'entangled', "Net arrows should have entangled effect type"
    assert net_arrows.ammo_effect_duration == 1, "Net arrows should have 1 turn duration"
    assert net_arrows.ammo_effect_chance == 0.5, "Net arrows should have 50% effect chance"
    
    # Load net arrows into quiver
    player.equipment.toggle_equip(net_arrows)
    assert player.equipment.quiver == net_arrows, "Net arrows should be in quiver"
    
    # Create target orc
    orc = Entity(5, 0, 'o', (0, 255, 0), 'Orc', blocks=True)
    orc.fighter = Fighter(hp=50, defense=5, power=5, strength=12, dexterity=8, constitution=12)
    
    # Attack orc multiple times until we get a hit with entangled effect
    entangled_applied = False
    for i in range(20):
        if not player.equipment.quiver:
            break  # Ran out of ammo
        
        # Reset RNG with a seed that might trigger effect
        random.seed(1337 + i)
        
        results = player.fighter.attack_d20(orc)
        
        # Check if entangled was applied
        if orc.components.has(ComponentType.STATUS_EFFECTS):
            status_effects = orc.get_component_optional(ComponentType.STATUS_EFFECTS)
            if status_effects and status_effects.has_effect('entangled'):
                entangled_applied = True
                # Verify effect properties
                entangled = status_effects.get_effect('entangled')
                assert entangled is not None
                assert entangled.duration == 1, f"Entangled duration should be 1, got {entangled.duration}"
                break
    
    # At least one hit should have applied entangled (probabilistically)
    # Note: This is not guaranteed due to RNG, but with 20 attempts and 50% chance on hit,
    # we should see at least one application
    assert entangled_applied, "Entangled effect should be applied at least once over 20 attacks"


@pytest.mark.fast
def test_net_arrow_effect_does_not_always_apply():
    """Test that net arrows don't always apply entangled (50% chance)."""
    
    # Use multiple seeds to verify that sometimes effect doesn't apply
    effect_applied_count = 0
    effect_not_applied_count = 0
    
    for seed in [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]:
        random.seed(seed)
        
        # Create player with shortbow
        player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
        player.fighter = Fighter(hp=50, defense=5, power=5, strength=14, dexterity=18, constitution=14)
        player.equipment = Equipment()
        player.inventory = Inventory(26)
        
        # Create shortbow
        factory = get_entity_factory()
        shortbow = factory.create_weapon('shortbow', 0, 0)
        player.equipment.toggle_equip(shortbow)
        
        # Create net arrows
        net_arrows = factory.create_special_ammo('net_arrow', 0, 0)
        player.equipment.toggle_equip(net_arrows)
        
        # Create target orc with low AC to guarantee hits
        orc = Entity(5, 0, 'o', (0, 255, 0), 'Orc', blocks=True)
        orc.fighter = Fighter(hp=100, defense=5, power=5, strength=12, dexterity=6, constitution=12)
        
        # Attack once
        results = player.fighter.attack_d20(orc)
        
        # Check if effect was applied (only if we hit)
        hit_occurred = False
        for result in results:
            if 'message' in result:
                msg = str(result['message'])
                if 'HIT' in msg or 'CRITICAL' in msg:
                    hit_occurred = True
                    break
        
        if hit_occurred:
            if orc.components.has(ComponentType.STATUS_EFFECTS):
                status_effects = orc.get_component_optional(ComponentType.STATUS_EFFECTS)
                if status_effects and status_effects.has_effect('entangled'):
                    effect_applied_count += 1
                else:
                    effect_not_applied_count += 1
            else:
                effect_not_applied_count += 1
    
    # With 50% chance, we should see both applications and non-applications
    # (This is probabilistic, but with 10 trials, very likely to see both)
    # We just verify that not all hit or all miss (not a 100% effect)
    total_hits = effect_applied_count + effect_not_applied_count
    if total_hits > 0:
        # At least one should have not applied (not 100% effect)
        assert effect_not_applied_count > 0, \
            f"With 50% chance, some hits should NOT apply effect. Got {effect_applied_count} applied, {effect_not_applied_count} not applied"


@pytest.mark.fast
def test_net_arrow_consumed_on_miss():
    """Test that net arrows are consumed even on miss."""
    
    # Seed for determinism
    random.seed(9999)
    
    # Create player with shortbow
    player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
    player.fighter = Fighter(hp=50, defense=5, power=5, strength=14, dexterity=14, constitution=14)
    player.equipment = Equipment()
    player.inventory = Inventory(26)
    
    # Create shortbow
    factory = get_entity_factory()
    shortbow = factory.create_weapon('shortbow', 0, 0)
    player.equipment.toggle_equip(shortbow)
    
    # Create net arrows
    net_arrows = factory.create_special_ammo('net_arrow', 0, 0)
    player.equipment.toggle_equip(net_arrows)
    
    # Create high-AC target to increase miss chance
    orc = Entity(5, 0, 'o', (0, 255, 0), 'Orc', blocks=True)
    orc.fighter = Fighter(hp=100, defense=20, power=5, strength=12, dexterity=18, constitution=12)
    
    # Attack multiple times
    initial_quantity = net_arrows.item.quantity
    attacks_made = 0
    
    for i in range(5):
        if player.equipment.quiver:
            before_attack = net_arrows.item.quantity
            results = player.fighter.attack_d20(orc)
            attacks_made += 1
            
            # Check if ammo was consumed (regardless of hit/miss)
            if player.equipment.quiver:  # Still have arrows
                assert net_arrows.item.quantity == before_attack - 1, \
                    "Ammo should be consumed on each attack (hit OR miss)"
            else:
                # Ran out of ammo
                break
    
    # Verify total consumption
    final_quantity = net_arrows.item.quantity if player.equipment.quiver else 0
    total_consumed = initial_quantity - final_quantity
    assert total_consumed == attacks_made, \
        f"Total ammo consumed ({total_consumed}) should equal attacks made ({attacks_made})"


@pytest.mark.fast
def test_entangled_blocks_movement():
    """Test that entangled effect from net arrow blocks movement."""
    
    # Seed for determinism
    random.seed(1337)
    
    # Create player with shortbow
    player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
    player.fighter = Fighter(hp=50, defense=5, power=5, strength=14, dexterity=18, constitution=14)
    player.equipment = Equipment()
    player.inventory = Inventory(26)
    
    # Create shortbow
    factory = get_entity_factory()
    shortbow = factory.create_weapon('shortbow', 0, 0)
    player.equipment.toggle_equip(shortbow)
    
    # Create net arrows
    net_arrows = factory.create_special_ammo('net_arrow', 0, 0)
    player.equipment.toggle_equip(net_arrows)
    
    # Create target orc
    orc = Entity(5, 0, 'o', (0, 255, 0), 'Orc', blocks=True)
    orc.fighter = Fighter(hp=50, defense=5, power=5, strength=12, dexterity=8, constitution=12)
    
    # Attack orc until entangled is applied
    for i in range(20):
        if not player.equipment.quiver:
            break
        
        random.seed(1337 + i)
        results = player.fighter.attack_d20(orc)
        
        if orc.components.has(ComponentType.STATUS_EFFECTS):
            status_effects = orc.get_component_optional(ComponentType.STATUS_EFFECTS)
            if status_effects and status_effects.has_effect('entangled'):
                # Entangled applied - try to move orc
                old_x, old_y = orc.x, orc.y
                move_result = orc.move(1, 0)
                
                # Movement should be blocked
                assert move_result == False, "Movement should be blocked by entangled effect"
                assert orc.x == old_x and orc.y == old_y, "Orc should not have moved"
                
                return  # Test passed
    
    # If we get here, entangled was never applied
    pytest.fail("Entangled effect was not applied within 20 attacks")


@pytest.mark.fast
def test_net_arrow_auto_unequip_when_empty():
    """Test that net arrows auto-unequip when quantity reaches 0."""
    
    # Seed for determinism
    random.seed(1337)
    
    # Create player with shortbow
    player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
    player.fighter = Fighter(hp=50, defense=5, power=5, strength=14, dexterity=14, constitution=14)
    player.equipment = Equipment()
    player.inventory = Inventory(26)
    
    # Create shortbow
    factory = get_entity_factory()
    shortbow = factory.create_weapon('shortbow', 0, 0)
    player.equipment.toggle_equip(shortbow)
    
    # Create net arrows with only 2 arrows for quick test
    net_arrows = factory.create_special_ammo('net_arrow', 0, 0)
    net_arrows.item.quantity = 2
    player.equipment.toggle_equip(net_arrows)
    
    # Create target orc
    orc = Entity(5, 0, 'o', (0, 255, 0), 'Orc', blocks=True)
    orc.fighter = Fighter(hp=100, defense=5, power=5, strength=12, dexterity=10, constitution=12)
    
    # Attack twice to consume all arrows
    player.fighter.attack_d20(orc)
    assert player.equipment.quiver is not None, "Quiver should still have 1 arrow"
    
    player.fighter.attack_d20(orc)
    assert player.equipment.quiver is None, "Quiver should be empty after consuming last arrow"
    
    # Verify we can still attack with basic ammo
    player.fighter.attack_d20(orc)  # Should not crash
