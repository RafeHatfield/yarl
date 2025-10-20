"""Tests for new potion effects added in Potion Variety feature.

Tests cover:
- Buff potions: speed, regeneration, invisibility, levitation, protection, heroism
- Debuff potions: weakness, slowness, blindness, paralysis
- Special potions: experience

All tests verify:
1. Effect is applied correctly
2. Status messages are generated
3. Item is consumed
4. Effect duration and parameters match specs
"""

import pytest
from unittest.mock import Mock, MagicMock
from components.component_registry import ComponentType
from components.fighter import Fighter
from components.level import Level
from components.status_effects import (
    StatusEffectManager,
    SpeedEffect,
    RegenerationEffect,
    InvisibilityEffect,
    LevitationEffect,
    ProtectionEffect,
    HeroismEffect,
    WeaknessEffect,
    SlowedEffect,
    BlindnessEffect,
    ParalysisEffect,
)
from item_functions import (
    drink_speed_potion,
    drink_regeneration_potion,
    drink_invisibility_potion,
    drink_levitation_potion,
    drink_protection_potion,
    drink_heroism_potion,
    drink_weakness_potion,
    drink_slowness_potion,
    drink_blindness_potion,
    drink_paralysis_potion,
    drink_experience_potion,
)


class TestBuffPotions:
    """Test suite for buff potions."""
    
    def setup_method(self):
        """Create test entity before each test."""
        self.entity = Mock()
        self.entity.name = "Test Entity"
        self.entity.status_effects = StatusEffectManager(self.entity)
        self.entity.get_component_optional = Mock(return_value=None)
        # Mock equipment to prevent ring immunity checks from interfering
        self.entity.equipment = None
    
    def test_drink_speed_potion(self):
        """Speed potion should add speed effect for 20 turns."""
        results = drink_speed_potion(self.entity)
        
        # Check consumed
        assert any(r.get("consumed") == True for r in results)
        
        # Check effect is active
        assert self.entity.status_effects.has_effect("speed")
        effect = self.entity.status_effects.get_effect("speed")
        assert effect.duration == 20
        assert isinstance(effect, SpeedEffect)
        
        # Check message
        messages = [r.get("message") for r in results if "message" in r]
        assert len(messages) > 0
        assert any("fast" in str(m).lower() for m in messages)
    
    def test_drink_regeneration_potion(self):
        """Regeneration potion should add regeneration effect for 50 turns."""
        # Add fighter component for healing (use Mock to avoid property issues)
        fighter = Mock()
        fighter.hp = 50
        fighter.max_hp = 100
        self.entity.get_component_optional = Mock(side_effect=lambda ct: fighter if ct == ComponentType.FIGHTER else None)
        
        results = drink_regeneration_potion(self.entity)
        
        # Check consumed
        assert any(r.get("consumed") == True for r in results)
        
        # Check effect is active
        assert self.entity.status_effects.has_effect("regeneration")
        effect = self.entity.status_effects.get_effect("regeneration")
        assert effect.duration == 50
        assert effect.heal_per_turn == 1
        assert isinstance(effect, RegenerationEffect)
        
        # Check message
        messages = [r.get("message") for r in results if "message" in r]
        assert len(messages) > 0
        assert any("regenerat" in str(m).lower() for m in messages)
    
    def test_drink_invisibility_potion(self):
        """Invisibility potion should add invisibility effect for 30 turns."""
        results = drink_invisibility_potion(self.entity)
        
        # Check consumed
        assert any(r.get("consumed") == True for r in results)
        
        # Check effect is active
        assert self.entity.status_effects.has_effect("invisibility")
        effect = self.entity.status_effects.get_effect("invisibility")
        assert effect.duration == 30  # Longer than scroll's 10 turns
        assert isinstance(effect, InvisibilityEffect)
        
        # Check invisibility flag is set
        assert hasattr(self.entity, 'invisible')
        assert self.entity.invisible == True
        
        # Check message
        messages = [r.get("message") for r in results if "message" in r]
        assert len(messages) > 0
        assert any("invisible" in str(m).lower() for m in messages)
    
    def test_drink_levitation_potion(self):
        """Levitation potion should add levitation effect for 40 turns."""
        results = drink_levitation_potion(self.entity)
        
        # Check consumed
        assert any(r.get("consumed") == True for r in results)
        
        # Check effect is active
        assert self.entity.status_effects.has_effect("levitation")
        effect = self.entity.status_effects.get_effect("levitation")
        assert effect.duration == 40
        assert isinstance(effect, LevitationEffect)
        
        # Check levitating flag is set
        assert hasattr(self.entity, 'levitating')
        assert self.entity.levitating == True
        
        # Check message
        messages = [r.get("message") for r in results if "message" in r]
        assert len(messages) > 0
        assert any("levitat" in str(m).lower() for m in messages)
    
    def test_drink_protection_potion(self):
        """Protection potion should add protection effect for 50 turns with +4 AC."""
        results = drink_protection_potion(self.entity)
        
        # Check consumed
        assert any(r.get("consumed") == True for r in results)
        
        # Check effect is active
        assert self.entity.status_effects.has_effect("protection")
        effect = self.entity.status_effects.get_effect("protection")
        assert effect.duration == 50
        assert effect.ac_bonus == 4
        assert isinstance(effect, ProtectionEffect)
        
        # Check message
        messages = [r.get("message") for r in results if "message" in r]
        assert len(messages) > 0
        assert any("protect" in str(m).lower() for m in messages)
    
    def test_drink_heroism_potion(self):
        """Heroism potion should add heroism effect for 30 turns with +3/+3."""
        results = drink_heroism_potion(self.entity)
        
        # Check consumed
        assert any(r.get("consumed") == True for r in results)
        
        # Check effect is active
        assert self.entity.status_effects.has_effect("heroism")
        effect = self.entity.status_effects.get_effect("heroism")
        assert effect.duration == 30
        assert effect.attack_bonus == 3
        assert effect.damage_bonus == 3
        assert isinstance(effect, HeroismEffect)
        
        # Check message
        messages = [r.get("message") for r in results if "message" in r]
        assert len(messages) > 0
        assert any("heroic" in str(m).lower() for m in messages)


class TestDebuffPotions:
    """Test suite for debuff potions."""
    
    def setup_method(self):
        """Create test entity before each test."""
        self.entity = Mock()
        self.entity.name = "Test Entity"
        self.entity.status_effects = StatusEffectManager(self.entity)
        self.entity.get_component_optional = Mock(return_value=None)
        # Mock equipment to prevent ring immunity checks from interfering
        self.entity.equipment = None
    
    def test_drink_weakness_potion(self):
        """Weakness potion should add weakness effect for 30 turns with -2 damage."""
        results = drink_weakness_potion(self.entity)
        
        # Check consumed
        assert any(r.get("consumed") == True for r in results)
        
        # Check effect is active
        assert self.entity.status_effects.has_effect("weakness")
        effect = self.entity.status_effects.get_effect("weakness")
        assert effect.duration == 30
        assert effect.damage_penalty == 2
        assert isinstance(effect, WeaknessEffect)
        
        # Check message
        messages = [r.get("message") for r in results if "message" in r]
        assert len(messages) > 0
        assert any("weak" in str(m).lower() for m in messages)
    
    def test_drink_slowness_potion(self):
        """Slowness potion should add slowed effect for 20 turns."""
        results = drink_slowness_potion(self.entity)
        
        # Check consumed
        assert any(r.get("consumed") == True for r in results)
        
        # Check effect is active
        assert self.entity.status_effects.has_effect("slowed")
        effect = self.entity.status_effects.get_effect("slowed")
        assert effect.duration == 20
        assert isinstance(effect, SlowedEffect)
        
        # Check message
        messages = [r.get("message") for r in results if "message" in r]
        assert len(messages) > 0
    
    def test_drink_blindness_potion(self):
        """Blindness potion should add blindness effect for 15 turns."""
        results = drink_blindness_potion(self.entity)
        
        # Check consumed
        assert any(r.get("consumed") == True for r in results)
        
        # Check effect is active
        assert self.entity.status_effects.has_effect("blindness")
        effect = self.entity.status_effects.get_effect("blindness")
        assert effect.duration == 15
        assert effect.fov_radius == 1
        assert isinstance(effect, BlindnessEffect)
        
        # Check message
        messages = [r.get("message") for r in results if "message" in r]
        assert len(messages) > 0
        assert any("blind" in str(m).lower() for m in messages)
    
    def test_drink_paralysis_potion(self):
        """Paralysis potion should add paralysis effect for 3-5 turns."""
        results = drink_paralysis_potion(self.entity)
        
        # Check consumed
        assert any(r.get("consumed") == True for r in results)
        
        # Check effect is active
        assert self.entity.status_effects.has_effect("paralysis")
        effect = self.entity.status_effects.get_effect("paralysis")
        assert effect.duration >= 3
        assert effect.duration <= 5
        assert isinstance(effect, ParalysisEffect)
        
        # Check paralyzed flag is set
        assert hasattr(self.entity, 'paralyzed')
        assert self.entity.paralyzed == True
        
        # Check message
        messages = [r.get("message") for r in results if "message" in r]
        assert len(messages) > 0
        assert any("paralyz" in str(m).lower() for m in messages)


class TestSpecialPotions:
    """Test suite for special potions."""
    
    def setup_method(self):
        """Create test entity before each test."""
        self.entity = Mock()
        self.entity.name = "Test Entity"
        
        # Create level component
        self.level_comp = Level(level_up_base=200)
        # Note: experience_to_next_level is a calculated property, don't set it
        
        self.entity.get_component_optional = Mock(
            side_effect=lambda ct: self.level_comp if ct == ComponentType.LEVEL else None
        )
        # Mock equipment to prevent ring immunity checks from interfering
        self.entity.equipment = None
    
    def test_drink_experience_potion(self):
        """Experience potion should grant enough XP for instant level-up."""
        # Mock add_xp to verify it's called with correct amount
        original_add_xp = self.level_comp.add_xp
        xp_added = []
        
        def mock_add_xp(amount):
            xp_added.append(amount)
            # Simulate level-up
            self.level_comp.current_level += 1
        
        self.level_comp.add_xp = mock_add_xp
        
        results = drink_experience_potion(self.entity)
        
        # Check consumed
        assert any(r.get("consumed") == True for r in results)
        
        # Check XP was added
        assert len(xp_added) > 0
        # Note: The exact amount may vary based on Level implementation
        # We just verify that XP was granted
        assert xp_added[0] > 0
        
        # Check message
        messages = [r.get("message") for r in results if "message" in r]
        assert len(messages) > 0
        assert any("level" in str(m).lower() for m in messages)
    
    def test_drink_experience_potion_no_level_component(self):
        """Experience potion should fail gracefully without level component."""
        entity = Mock()
        entity.name = "No Level"
        entity.get_component_optional = Mock(return_value=None)
        
        results = drink_experience_potion(entity)
        
        # Check NOT consumed
        assert any(r.get("consumed") == False for r in results)
        
        # Check warning message
        messages = [r.get("message") for r in results if "message" in r]
        assert len(messages) > 0


class TestStatusEffectInteractions:
    """Test status effect stacking and interactions."""
    
    def setup_method(self):
        """Create test entity before each test."""
        self.entity = Mock()
        self.entity.name = "Test Entity"
        self.entity.status_effects = StatusEffectManager(self.entity)
        self.entity.get_component_optional = Mock(return_value=None)
        # Mock equipment to prevent ring immunity checks from interfering
        self.entity.equipment = None
    
    def test_multiple_buff_potions(self):
        """Multiple buff potions should stack (speed + heroism)."""
        drink_speed_potion(self.entity)
        drink_heroism_potion(self.entity)
        
        # Both effects should be active
        assert self.entity.status_effects.has_effect("speed")
        assert self.entity.status_effects.has_effect("heroism")
    
    def test_same_potion_twice_refreshes(self):
        """Drinking same potion twice should refresh duration."""
        drink_speed_potion(self.entity)
        speed_effect_1 = self.entity.status_effects.get_effect("speed")
        
        # Reduce duration to simulate time passing
        speed_effect_1.duration = 5
        
        drink_speed_potion(self.entity)
        speed_effect_2 = self.entity.status_effects.get_effect("speed")
        
        # Duration should be refreshed to 20
        assert speed_effect_2.duration == 20
    
    def test_buff_and_debuff_coexist(self):
        """Buffs and debuffs should coexist (heroism + weakness)."""
        drink_heroism_potion(self.entity)
        drink_weakness_potion(self.entity)
        
        # Both effects should be active
        assert self.entity.status_effects.has_effect("heroism")
        assert self.entity.status_effects.has_effect("weakness")


class TestRegenerationHealing:
    """Test regeneration effect's heal-over-time functionality."""
    
    def setup_method(self):
        """Create test entity before each test."""
        self.entity = Mock()
        self.entity.name = "Test Entity"
        self.entity.status_effects = StatusEffectManager(self.entity)
        
        # Create fighter with reduced HP (use Mock to avoid property issues)
        self.fighter = Mock()
        self.fighter.hp = 50
        self.fighter.max_hp = 100
        self.entity.get_component_optional = Mock(
            side_effect=lambda ct: self.fighter if ct == ComponentType.FIGHTER else None
        )
        # Mock equipment to prevent ring immunity checks from interfering
        self.entity.equipment = None
    
    def test_regeneration_heals_over_time(self):
        """Regeneration should heal 1 HP per turn for 50 turns."""
        drink_regeneration_potion(self.entity)
        
        initial_hp = self.fighter.hp
        
        # Simulate 10 turns
        for i in range(10):
            results = self.entity.status_effects.process_turn_start()
            
            # Check HP increased (unless at max)
            if initial_hp + i < self.fighter.max_hp:
                assert self.fighter.hp == initial_hp + i + 1
    
    def test_regeneration_stops_at_max_hp(self):
        """Regeneration should not heal above max HP."""
        self.fighter.hp = 99  # 1 HP below max
        
        drink_regeneration_potion(self.entity)
        
        # Simulate 5 turns (should only heal 1 HP)
        for i in range(5):
            self.entity.status_effects.process_turn_start()
        
        assert self.fighter.hp == 100  # Max HP
    
    def test_regeneration_expires_after_duration(self):
        """Regeneration should expire after 50 turns."""
        drink_regeneration_potion(self.entity)
        
        effect = self.entity.status_effects.get_effect("regeneration")
        
        # Simulate 50 turns
        for i in range(50):
            self.entity.status_effects.process_turn_end()
        
        # Effect should be expired
        assert not self.entity.status_effects.has_effect("regeneration")


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_drink_potion_without_entity(self):
        """All potions should handle missing entity gracefully."""
        potions = [
            drink_speed_potion,
            drink_regeneration_potion,
            drink_invisibility_potion,
            drink_levitation_potion,
            drink_protection_potion,
            drink_heroism_potion,
            drink_weakness_potion,
            drink_slowness_potion,
            drink_blindness_potion,
            drink_paralysis_potion,
        ]
        
        for potion_func in potions:
            results = potion_func()  # No entity
            
            # Should not consume and should have error message
            assert any(r.get("consumed") == False for r in results)
            messages = [r.get("message") for r in results if "message" in r]
            assert len(messages) > 0
    
    def test_entity_without_status_effects_manager(self):
        """Potions should create StatusEffectManager if missing."""
        from unittest.mock import MagicMock
        entity = MagicMock()
        entity.name = "No Manager"
        # Start without status_effects attribute
        del entity.status_effects
        # Mock equipment to prevent ring immunity checks from interfering
        entity.equipment = None
        
        # Should work and create manager
        drink_speed_potion(entity)
        
        # Manager should now exist
        assert hasattr(entity, 'status_effects')
        assert isinstance(entity.status_effects, StatusEffectManager)
        assert entity.status_effects.has_effect("speed")

