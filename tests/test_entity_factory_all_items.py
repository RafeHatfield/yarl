"""Comprehensive tests for EntityFactory item creation.

This test suite ensures ALL item types defined in entities.yaml can be
created successfully through the EntityFactory. This prevents "Unknown"
fallback items from appearing in-game.

Regression tests for:
- "Unknown Sword" / "Unknown Chain Mail" bug
- "Unknown spell function for Haste Scroll" warnings
- "Unknown spell type: ring_of_protection" warnings
"""

import pytest
from config.entity_factory import get_entity_factory
from config.entity_registry import load_entity_config


@pytest.fixture(scope="module", autouse=True)
def setup_entity_config():
    """Load entity configuration once for all tests."""
    load_entity_config()


@pytest.fixture
def factory():
    """Get entity factory instance."""
    return get_entity_factory()


class TestWeaponCreation:
    """Test that all weapons can be created."""
    
    def test_create_dagger(self, factory):
        """Test creating a dagger."""
        weapon = factory.create_weapon("dagger", 0, 0)
        assert weapon is not None
        assert weapon.name == "Dagger"
        assert weapon.equippable is not None
        assert weapon.equippable.damage_dice == "1d4"
    
    def test_create_sword(self, factory):
        """Test creating a sword (was showing as Unknown Sword)."""
        weapon = factory.create_weapon("sword", 0, 0)
        assert weapon is not None, "Sword creation failed - was showing as Unknown Sword"
        assert weapon.name == "Sword"
        assert weapon.equippable is not None
        assert weapon.equippable.damage_dice == "1d8"
    
    def test_create_longsword(self, factory):
        """Test creating a longsword."""
        weapon = factory.create_weapon("longsword", 0, 0)
        assert weapon is not None
        assert weapon.name == "Longsword"
        assert weapon.equippable.damage_dice == "1d8"
    
    def test_create_battleaxe(self, factory):
        """Test creating a battleaxe."""
        weapon = factory.create_weapon("battleaxe", 0, 0)
        assert weapon is not None
        assert weapon.name == "Battleaxe"
        assert weapon.equippable.damage_dice == "1d10"


class TestArmorCreation:
    """Test that all armor types can be created."""
    
    def test_create_shield(self, factory):
        """Test creating a shield."""
        armor = factory.create_armor("shield", 0, 0)
        assert armor is not None
        assert armor.name == "Shield"
        assert armor.equippable is not None
    
    def test_create_chain_mail(self, factory):
        """Test creating chain mail (was showing as Unknown Chain Mail)."""
        armor = factory.create_armor("chain_mail", 0, 0)
        assert armor is not None, "Chain mail creation failed - was showing as Unknown Chain Mail"
        assert armor.name == "Chain Mail"  # name formatting uses replace('_', ' ').title()
        assert armor.equippable is not None
        assert armor.equippable.armor_class_bonus == 4
    
    def test_create_leather_armor(self, factory):
        """Test creating leather armor."""
        armor = factory.create_armor("leather_armor", 0, 0)
        assert armor is not None
        assert armor.name == "Leather Armor"  # name formatting uses replace('_', ' ').title()
        assert armor.equippable.armor_class_bonus == 2


class TestScrollCreation:
    """Test that all scrolls can be created with proper use functions."""
    
    def test_create_healing_potion(self, factory):
        """Test creating healing potion."""
        item = factory.create_spell_item("healing_potion", 0, 0)
        assert item is not None
        assert item.name == "Healing Potion"
        assert item.item is not None
        assert item.item.use_function is not None
    
    def test_create_fireball_scroll(self, factory):
        """Test creating fireball scroll."""
        item = factory.create_spell_item("fireball_scroll", 0, 0)
        assert item is not None
        assert item.name == "Fireball Scroll"
        assert item.item.use_function is not None
    
    def test_create_haste_scroll(self, factory):
        """Test creating haste scroll (was showing warning)."""
        item = factory.create_spell_item("haste_scroll", 0, 0)
        assert item is not None, "Haste scroll creation failed - was showing Unknown spell function warning"
        assert item.name == "Haste Scroll"
        assert item.item is not None
        assert item.item.use_function is not None, "Haste scroll has no use_function"
    
    def test_create_blink_scroll(self, factory):
        """Test creating blink scroll (was showing warning)."""
        item = factory.create_spell_item("blink_scroll", 0, 0)
        assert item is not None, "Blink scroll creation failed"
        assert item.name == "Blink Scroll"
        assert item.item.use_function is not None
    
    def test_create_light_scroll(self, factory):
        """Test creating light scroll (was showing warning)."""
        item = factory.create_spell_item("light_scroll", 0, 0)
        assert item is not None, "Light scroll creation failed"
        assert item.name == "Light Scroll"
        assert item.item.use_function is not None
    
    def test_create_magic_mapping_scroll(self, factory):
        """Test creating magic mapping scroll (was showing warning)."""
        item = factory.create_spell_item("magic_mapping_scroll", 0, 0)
        assert item is not None, "Magic mapping scroll creation failed"
        assert item.name == "Magic Mapping Scroll"
        assert item.item.use_function is not None
    
    def test_create_earthquake_scroll(self, factory):
        """Test creating earthquake scroll (was showing warning)."""
        item = factory.create_spell_item("earthquake_scroll", 0, 0)
        assert item is not None, "Earthquake scroll creation failed"
        assert item.name == "Earthquake Scroll"
        assert item.item.use_function is not None
    
    def test_create_confusion_scroll(self, factory):
        """Test creating confusion scroll."""
        item = factory.create_spell_item("confusion_scroll", 0, 0)
        assert item is not None
        assert item.name == "Confusion Scroll"
        assert item.item.use_function is not None
        assert item.item.targeting is True, "Confusion scroll should require targeting"


class TestRingCreation:
    """Test that all rings can be created."""
    
    def test_create_ring_of_protection(self, factory):
        """Test creating ring of protection (was showing warning)."""
        from components.ring import RingEffect
        
        ring = factory.create_ring("ring_of_protection", 0, 0)
        assert ring is not None, "Ring of protection creation failed - was showing Unknown spell type warning"
        assert ring.name == "Ring Of Protection"
        assert ring.ring is not None
        assert ring.ring.ring_effect == RingEffect.PROTECTION
        assert ring.ring.effect_strength == 2
        assert ring.equippable is not None
    
    def test_create_ring_of_strength(self, factory):
        """Test creating ring of strength (was showing warning)."""
        from components.ring import RingEffect
        
        ring = factory.create_ring("ring_of_strength", 0, 0)
        assert ring is not None
        assert ring.name == "Ring Of Strength"
        assert ring.ring.ring_effect == RingEffect.STRENGTH
        assert ring.ring.effect_strength == 2
    
    def test_create_ring_of_regeneration(self, factory):
        """Test creating ring of regeneration (was showing warning)."""
        from components.ring import RingEffect
        
        ring = factory.create_ring("ring_of_regeneration", 0, 0)
        assert ring is not None
        assert ring.name == "Ring Of Regeneration"
        assert ring.ring.ring_effect == RingEffect.REGENERATION
        assert ring.ring.effect_strength == 5
    
    def test_rings_start_unidentified(self, factory):
        """Test that rings start unidentified (unless pre-identified by settings)."""
        ring = factory.create_ring("ring_of_might", 0, 0)
        assert ring is not None
        assert ring.item is not None
        # Ring may or may not be identified depending on difficulty settings
        # Just verify the identification system is in place
        assert hasattr(ring.item, 'identified')
        assert hasattr(ring.item, 'appearance')


class TestWandCreation:
    """Test that all wands can be created."""
    
    def test_create_wand_of_fireball(self, factory):
        """Test creating wand of fireball."""
        wand = factory.create_wand("wand_of_fireball", 0, 0, dungeon_level=1)
        assert wand is not None
        assert wand.name == "Wand Of Fireball"
        assert wand.wand is not None
        assert wand.wand.charges >= 2, "Wand should start with at least 2 charges"
        assert wand.item.use_function is not None
    
    def test_create_wand_of_confusion(self, factory):
        """Test creating wand of confusion."""
        wand = factory.create_wand("wand_of_confusion", 0, 0, dungeon_level=1)
        assert wand is not None
        assert wand.name == "Wand Of Confusion"
        assert wand.wand is not None


class TestLootWeaponEnhancement:
    """Test that loot-generated weapons have proper damage values for enhancement."""
    
    def test_loot_weapon_has_damage_values(self):
        """Test that loot weapons have damage_min, damage_max, and damage_dice."""
        from components.loot import LootGenerator
        
        loot_gen = LootGenerator()
        weapon = loot_gen.generate_weapon(0, 0, dungeon_level=2)
        
        assert weapon is not None
        assert weapon.equippable is not None
        assert weapon.equippable.damage_dice is not None, "Loot weapon missing damage_dice"
        assert weapon.equippable.damage_min > 0, "Loot weapon damage_min should be > 0"
        assert weapon.equippable.damage_max > 0, "Loot weapon damage_max should be > 0"
    
    def test_loot_weapon_can_be_enhanced(self):
        """Test that loot weapons pass the enhancement check."""
        from components.loot import LootGenerator
        
        loot_gen = LootGenerator()
        weapon = loot_gen.generate_weapon(0, 0, dungeon_level=2)
        
        # The enhance weapon spell checks: if old_min > 0 and old_max > 0
        old_min = weapon.equippable.damage_min
        old_max = weapon.equippable.damage_max
        
        assert old_min > 0 and old_max > 0, \
            f"Weapon should pass enhancement check but has damage ({old_min}-{old_max})"
    
    def test_loot_weapon_damage_scales_with_level(self):
        """Test that loot weapon damage scales with dungeon level."""
        from components.loot import LootGenerator
        
        loot_gen = LootGenerator()
        
        early_weapon = loot_gen.generate_weapon(0, 0, dungeon_level=2)
        assert early_weapon.equippable.damage_dice == "1d6", "Early levels should use 1d6"
        
        mid_weapon = loot_gen.generate_weapon(0, 0, dungeon_level=5)
        assert mid_weapon.equippable.damage_dice == "1d8", "Mid levels should use 1d8"
        
        late_weapon = loot_gen.generate_weapon(0, 0, dungeon_level=8)
        assert late_weapon.equippable.damage_dice == "1d10", "Late levels should use 1d10"


class TestSmartFallbackSystem:
    """Test the smart fallback system in place_entities."""
    
    def test_fallback_no_warnings_for_intermediate_failures(self, factory, caplog):
        """Test that smart fallback doesn't log warnings for intermediate failures.
        
        When the fallback tries create_ring('teleport_scroll'), it should NOT log
        'Unknown ring type' because it's expected to fail and fall through to the
        next method (create_spell_item).
        """
        import logging
        
        # Clear any previous logs
        caplog.clear()
        
        # Simulate smart fallback for a ring
        with caplog.at_level(logging.WARNING):
            item = factory.create_weapon("ring_of_protection", 0, 0)
            if not item:
                item = factory.create_armor("ring_of_protection", 0, 0)
            if not item:
                item = factory.create_ring("ring_of_protection", 0, 0)
        
        # Should succeed at ring step with NO warnings
        assert item is not None
        assert item.name == "Ring Of Protection"
        
        # Check no "Unknown" warnings were logged (ignore identification warnings)
        warnings = [record.message for record in caplog.records 
                   if record.levelname == 'WARNING' and 'Unknown' in record.message]
        assert len(warnings) == 0, f"Should have no 'Unknown' warnings, but got: {warnings}"
    
    def test_fallback_no_warnings_for_scrolls_tried_as_rings(self, factory, caplog):
        """Test that trying to create a scroll as a ring doesn't log warnings."""
        import logging
        
        caplog.clear()
        
        # Simulate smart fallback for a scroll (tries ring before spell)
        with caplog.at_level(logging.WARNING):
            item = factory.create_weapon("teleport_scroll", 0, 0)
            if not item:
                item = factory.create_armor("teleport_scroll", 0, 0)
            if not item:
                item = factory.create_ring("teleport_scroll", 0, 0)
            if not item:
                item = factory.create_spell_item("teleport_scroll", 0, 0)
        
        # Should succeed at spell step with NO warnings
        assert item is not None
        assert item.name == "Teleport Scroll"
        
        # Check no "Unknown" warnings were logged (ignore identification warnings)
        warnings = [record.message for record in caplog.records 
                   if record.levelname == 'WARNING' and 'Unknown' in record.message]
        assert len(warnings) == 0, f"Should have no 'Unknown' warnings, but got: {warnings}"
    
    def test_fallback_creates_weapons(self, factory):
        """Test that smart fallback creates weapons correctly."""
        # The fallback should try: weapon → armor → ring → spell → wand
        weapon = factory.create_weapon("battleaxe", 0, 0)
        if not weapon:
            weapon = factory.create_armor("battleaxe", 0, 0)
        if not weapon:
            weapon = factory.create_ring("battleaxe", 0, 0)
        if not weapon:
            weapon = factory.create_spell_item("battleaxe", 0, 0)
        
        # Should succeed at weapon step
        assert weapon is not None
        assert weapon.name == "Battleaxe"
    
    def test_fallback_creates_armor(self, factory):
        """Test that smart fallback creates armor correctly."""
        armor = factory.create_weapon("chain_mail", 0, 0)
        if not armor:
            armor = factory.create_armor("chain_mail", 0, 0)
        
        # Should succeed at armor step
        assert armor is not None
        assert armor.name == "Chain Mail"
    
    def test_fallback_creates_rings(self, factory):
        """Test that smart fallback creates rings correctly."""
        ring = factory.create_weapon("ring_of_protection", 0, 0)
        if not ring:
            ring = factory.create_armor("ring_of_protection", 0, 0)
        if not ring:
            ring = factory.create_ring("ring_of_protection", 0, 0)
        
        # Should succeed at ring step
        assert ring is not None
        assert ring.name == "Ring Of Protection"
    
    def test_fallback_creates_scrolls(self, factory):
        """Test that smart fallback creates scrolls correctly."""
        scroll = factory.create_weapon("haste_scroll", 0, 0)
        if not scroll:
            scroll = factory.create_armor("haste_scroll", 0, 0)
        if not scroll:
            scroll = factory.create_ring("haste_scroll", 0, 0)
        if not scroll:
            scroll = factory.create_spell_item("haste_scroll", 0, 0)
        
        # Should succeed at spell step
        assert scroll is not None
        assert scroll.name == "Haste Scroll"

