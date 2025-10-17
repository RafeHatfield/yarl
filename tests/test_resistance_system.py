"""Tests for the resistance system.

Tests the new resistance mechanics for reducing elemental damage.
"""

import pytest
from components.fighter import Fighter, ResistanceType
from entity import Entity


def test_resistance_type_enum():
    """Test that ResistanceType enum has all expected types."""
    assert ResistanceType.FIRE
    assert ResistanceType.COLD
    assert ResistanceType.POISON
    assert ResistanceType.LIGHTNING
    assert ResistanceType.ACID
    assert ResistanceType.PHYSICAL


def test_fighter_with_no_resistances():
    """Test that fighter without resistances takes full damage."""
    fighter = Fighter(hp=100, defense=0, power=0)
    entity = Entity(0, 0, 'test', fighter=fighter)
    fighter.owner = entity
    
    # Fighter with no resistances
    resistance_pct = fighter.get_resistance(ResistanceType.FIRE)
    assert resistance_pct == 0
    
    # Take fire damage - should be full damage
    reduced_damage, res_pct = fighter.apply_resistance(20, "fire")
    assert reduced_damage == 20
    assert res_pct == 0


def test_fighter_with_base_fire_resistance():
    """Test that fighter with fire resistance takes reduced fire damage."""
    resistances = {
        ResistanceType.FIRE: 50  # 50% fire resistance
    }
    fighter = Fighter(hp=100, defense=0, power=0, resistances=resistances)
    entity = Entity(0, 0, 'test', fighter=fighter)
    fighter.owner = entity
    
    # Check resistance value
    resistance_pct = fighter.get_resistance(ResistanceType.FIRE)
    assert resistance_pct == 50
    
    # Apply 20 fire damage - should be reduced to 10
    reduced_damage, res_pct = fighter.apply_resistance(20, "fire")
    assert reduced_damage == 10
    assert res_pct == 50


def test_fighter_with_fire_immunity():
    """Test that 100% resistance provides immunity."""
    resistances = {
        ResistanceType.FIRE: 100  # Immune to fire
    }
    fighter = Fighter(hp=100, defense=0, power=0, resistances=resistances)
    entity = Entity(0, 0, 'test', fighter=fighter)
    fighter.owner = entity
    
    # Apply 100 fire damage - should be reduced to 0
    reduced_damage, res_pct = fighter.apply_resistance(100, "fire")
    assert reduced_damage == 0
    assert res_pct == 100


def test_resistance_caps_at_100_percent():
    """Test that resistance is capped at 100% (immunity)."""
    resistances = {
        ResistanceType.COLD: 150  # Over 100%
    }
    fighter = Fighter(hp=100, defense=0, power=0, resistances=resistances)
    entity = Entity(0, 0, 'test', fighter=fighter)
    fighter.owner = entity
    
    # Should be capped at 100%
    resistance_pct = fighter.get_resistance(ResistanceType.COLD)
    assert resistance_pct == 100
    
    # Apply 50 cold damage - should be reduced to 0
    reduced_damage, res_pct = fighter.apply_resistance(50, "cold")
    assert reduced_damage == 0


def test_multiple_resistance_types():
    """Test that different resistance types work independently."""
    resistances = {
        ResistanceType.FIRE: 50,
        ResistanceType.COLD: 75,
        ResistanceType.POISON: 100
    }
    fighter = Fighter(hp=100, defense=0, power=0, resistances=resistances)
    entity = Entity(0, 0, 'test', fighter=fighter)
    fighter.owner = entity
    
    # Check each resistance
    assert fighter.get_resistance(ResistanceType.FIRE) == 50
    assert fighter.get_resistance(ResistanceType.COLD) == 75
    assert fighter.get_resistance(ResistanceType.POISON) == 100
    assert fighter.get_resistance(ResistanceType.LIGHTNING) == 0  # No lightning resistance
    
    # Apply different damage types
    fire_damage, fire_res = fighter.apply_resistance(20, "fire")
    assert fire_damage == 10  # 50% resistance
    
    cold_damage, cold_res = fighter.apply_resistance(20, "cold")
    assert cold_damage == 5  # 75% resistance
    
    poison_damage, poison_res = fighter.apply_resistance(20, "poison")
    assert poison_damage == 0  # 100% resistance (immune)


def test_damage_type_string_aliases():
    """Test that string damage types are recognized."""
    resistances = {
        ResistanceType.LIGHTNING: 50
    }
    fighter = Fighter(hp=100, defense=0, power=0, resistances=resistances)
    entity = Entity(0, 0, 'test', fighter=fighter)
    fighter.owner = entity
    
    # Both "lightning" and "electric" should work
    lightning_damage, _ = fighter.apply_resistance(20, "lightning")
    assert lightning_damage == 10
    
    electric_damage, _ = fighter.apply_resistance(20, "electric")
    assert electric_damage == 10


def test_unknown_damage_type():
    """Test that unknown damage types are not reduced."""
    resistances = {
        ResistanceType.FIRE: 100
    }
    fighter = Fighter(hp=100, defense=0, power=0, resistances=resistances)
    entity = Entity(0, 0, 'test', fighter=fighter)
    fighter.owner = entity
    
    # Unknown damage type - no resistance
    damage, res_pct = fighter.apply_resistance(20, "psychic")
    assert damage == 20
    assert res_pct == 0


def test_take_damage_with_resistance():
    """Test that take_damage method applies resistances."""
    resistances = {
        ResistanceType.FIRE: 50
    }
    fighter = Fighter(hp=100, defense=0, power=0, resistances=resistances)
    entity = Entity(0, 0, 'test', fighter=fighter)
    fighter.owner = entity
    
    # Take 20 fire damage - should be reduced to 10
    results = fighter.take_damage(20, damage_type="fire")
    
    # HP should be reduced by 10, not 20
    assert fighter.hp == 90


def test_take_damage_without_damage_type():
    """Test that take_damage without damage_type applies full damage."""
    resistances = {
        ResistanceType.FIRE: 100  # Immune to fire
    }
    fighter = Fighter(hp=100, defense=0, power=0, resistances=resistances)
    entity = Entity(0, 0, 'test', fighter=fighter)
    fighter.owner = entity
    
    # Take 20 damage without specifying type - should be full damage
    results = fighter.take_damage(20)
    
    # HP should be reduced by full 20 (no resistance applied)
    assert fighter.hp == 80


def test_partial_resistances():
    """Test various partial resistance values."""
    test_cases = [
        (25, 20, 15),   # 25% resistance: 20 damage -> 15 damage
        (30, 10, 7),    # 30% resistance: 10 damage -> 7 damage
        (90, 100, 10),  # 90% resistance: 100 damage -> 10 damage
        (10, 50, 45),   # 10% resistance: 50 damage -> 45 damage
    ]
    
    for resistance, original_damage, expected_damage in test_cases:
        resistances = {ResistanceType.FIRE: resistance}
        fighter = Fighter(hp=1000, defense=0, power=0, resistances=resistances)
        entity = Entity(0, 0, 'test', fighter=fighter)
        fighter.owner = entity
        
        reduced_damage, _ = fighter.apply_resistance(original_damage, "fire")
        assert reduced_damage == expected_damage, f"Failed for {resistance}% resistance on {original_damage} damage"

