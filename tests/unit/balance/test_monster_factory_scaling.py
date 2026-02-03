"""Integration tests for monster factory depth scaling.

Tests verify that depth scaling is applied correctly through the
MonsterFactory.create_monster() pathway.
"""

import pytest

from config.factories import EntityFactory
from components.component_registry import ComponentType


class TestMonsterFactoryScaling:
    """Test that monster factory applies depth scaling correctly."""
    
    @pytest.fixture
    def factory(self):
        """Create a fresh entity factory."""
        return EntityFactory()
    
    def test_orc_at_depth_1_has_base_stats(self, factory):
        """Orc at depth 1 should have unscaled base stats."""
        orc = factory.create_monster("orc", 0, 0, depth=1)
        assert orc is not None
        
        fighter = orc.get_component_optional(ComponentType.FIGHTER)
        assert fighter is not None
        
        # Get expected base stats from registry
        registry = factory.registry
        orc_def = registry.get_monster("orc")
        
        # At depth 1, BASE stats should match base definition
        # Note: max_hp includes CON modifier, so check base_max_hp instead
        assert fighter.base_max_hp == orc_def.stats.hp
        assert fighter.damage_min == (orc_def.stats.damage_min or 0)
        assert fighter.damage_max == (orc_def.stats.damage_max or 0)
    
    def test_orc_at_depth_5_has_scaled_stats(self, factory):
        """Orc at depth 5 should have scaled stats (default curve)."""
        orc_d1 = factory.create_monster("orc", 0, 0, depth=1)
        orc_d5 = factory.create_monster("orc", 0, 0, depth=5)
        
        assert orc_d1 is not None
        assert orc_d5 is not None
        
        fighter_d1 = orc_d1.get_component_optional(ComponentType.FIGHTER)
        fighter_d5 = orc_d5.get_component_optional(ComponentType.FIGHTER)
        
        # Depth 5 default curve: HP 1.25x, ToHit 1.12x, Damage 1.05x
        # HP should be higher at depth 5
        assert fighter_d5.max_hp >= fighter_d1.max_hp
        # With 1.25 multiplier, should be noticeably higher
        assert fighter_d5.max_hp > fighter_d1.max_hp or fighter_d1.max_hp <= 4  # Unless base is tiny
    
    def test_zombie_at_depth_5_uses_override_curve(self, factory):
        """Zombie at depth 5 should use conservative zombie curve (no scaling)."""
        zombie = factory.create_monster("zombie", 0, 0, depth=5)
        assert zombie is not None
        
        fighter = zombie.get_component_optional(ComponentType.FIGHTER)
        registry = factory.registry
        zombie_def = registry.get_monster("zombie")
        
        # Zombie curve at depth 5: HP 1.00x (no scaling to avoid amplifying swarm)
        base_hp = zombie_def.stats.hp
        # Expected: 24 * 1.00 = 24 (no scaling)
        expected_base_hp = base_hp
        # Check base_max_hp (not max_hp which includes CON modifier)
        assert fighter.base_max_hp == expected_base_hp
    
    def test_zombie_scales_less_than_orc_at_same_depth(self, factory):
        """Zombie should have no scaling at depth 5, while orc scales normally."""
        # Get base stats
        registry = factory.registry
        orc_def = registry.get_monster("orc")
        zombie_def = registry.get_monster("zombie")
        
        # Create both at depth 5
        orc = factory.create_monster("orc", 0, 0, depth=5)
        zombie = factory.create_monster("zombie", 0, 0, depth=5)
        
        orc_fighter = orc.get_component_optional(ComponentType.FIGHTER)
        zombie_fighter = zombie.get_component_optional(ComponentType.FIGHTER)
        
        # Calculate scaling ratios using base_max_hp (excludes CON modifier)
        orc_hp_ratio = orc_fighter.base_max_hp / orc_def.stats.hp
        zombie_hp_ratio = zombie_fighter.base_max_hp / zombie_def.stats.hp
        
        # Orc should scale (1.25x), zombie should not scale (1.00x)
        assert orc_hp_ratio > zombie_hp_ratio
        # Zombie should have no scaling at depth 5
        assert zombie_hp_ratio == 1.0
    
    def test_current_hp_matches_base_max_hp_on_spawn(self, factory):
        """Newly spawned monster should have current HP = base_max_hp.
        
        Note: This is existing behavior - monsters spawn with hp = base_max_hp,
        not hp = max_hp (which includes CON modifier). The CON bonus only
        affects max_hp for healing purposes.
        """
        monster = factory.create_monster("orc", 0, 0, depth=7)
        assert monster is not None
        
        fighter = monster.get_component_optional(ComponentType.FIGHTER)
        # Current HP matches base_max_hp on spawn
        assert fighter.hp == fighter.base_max_hp
    
    def test_depth_default_is_1(self, factory):
        """If depth not specified, should default to 1 (no scaling)."""
        # Without depth parameter
        monster_default = factory.create_monster("orc", 0, 0)
        # With explicit depth=1
        monster_d1 = factory.create_monster("orc", 0, 0, depth=1)
        
        f_default = monster_default.get_component_optional(ComponentType.FIGHTER)
        f_d1 = monster_d1.get_component_optional(ComponentType.FIGHTER)
        
        assert f_default.max_hp == f_d1.max_hp
        assert f_default.damage_min == f_d1.damage_min
        assert f_default.damage_max == f_d1.damage_max
    
    def test_scaling_does_not_affect_xp(self, factory):
        """XP reward should not be scaled by depth."""
        registry = factory.registry
        orc_def = registry.get_monster("orc")
        
        orc_d1 = factory.create_monster("orc", 0, 0, depth=1)
        orc_d9 = factory.create_monster("orc", 0, 0, depth=9)
        
        f_d1 = orc_d1.get_component_optional(ComponentType.FIGHTER)
        f_d9 = orc_d9.get_component_optional(ComponentType.FIGHTER)
        
        # XP should be unchanged
        assert f_d1.xp == orc_def.stats.xp
        assert f_d9.xp == orc_def.stats.xp
    
    def test_scaling_does_not_affect_defense(self, factory):
        """Defense stat should not be scaled by depth."""
        registry = factory.registry
        orc_def = registry.get_monster("orc")
        
        orc_d1 = factory.create_monster("orc", 0, 0, depth=1)
        orc_d9 = factory.create_monster("orc", 0, 0, depth=9)
        
        f_d1 = orc_d1.get_component_optional(ComponentType.FIGHTER)
        f_d9 = orc_d9.get_component_optional(ComponentType.FIGHTER)
        
        # Defense should be unchanged
        assert f_d1.defense == orc_def.stats.defense
        assert f_d9.defense == orc_def.stats.defense
    
    def test_scaling_does_not_affect_evasion(self, factory):
        """Evasion stat should not be scaled by depth."""
        orc_d1 = factory.create_monster("orc", 0, 0, depth=1)
        orc_d9 = factory.create_monster("orc", 0, 0, depth=9)
        
        f_d1 = orc_d1.get_component_optional(ComponentType.FIGHTER)
        f_d9 = orc_d9.get_component_optional(ComponentType.FIGHTER)
        
        # Evasion should be unchanged (check _base_evasion if base_evasion not available)
        evasion_d1 = getattr(f_d1, 'base_evasion', None) or getattr(f_d1, '_base_evasion', None)
        evasion_d9 = getattr(f_d9, 'base_evasion', None) or getattr(f_d9, '_base_evasion', None)
        assert evasion_d1 == evasion_d9


class TestScalingAppliedOnce:
    """Test that scaling is applied exactly once."""
    
    @pytest.fixture
    def factory(self):
        """Create a fresh entity factory."""
        return EntityFactory()
    
    def test_creating_same_monster_twice_gives_same_stats(self, factory):
        """Creating the same monster at same depth should give identical stats."""
        m1 = factory.create_monster("orc", 0, 0, depth=5)
        m2 = factory.create_monster("orc", 0, 0, depth=5)
        
        f1 = m1.get_component_optional(ComponentType.FIGHTER)
        f2 = m2.get_component_optional(ComponentType.FIGHTER)
        
        assert f1.max_hp == f2.max_hp
        assert f1.damage_min == f2.damage_min
        assert f1.damage_max == f2.damage_max
        assert f1.accuracy == f2.accuracy


class TestPlaguseZombieInheritance:
    """Test that plague zombie inherits zombie curve via explicit 'zombie' tag."""
    
    @pytest.fixture
    def factory(self):
        """Create a fresh entity factory."""
        return EntityFactory()
    
    def test_plague_zombie_uses_zombie_curve(self, factory):
        """Plague zombie should use zombie override curve (no scaling at depth 5)."""
        # This test assumes plague_zombie exists and has 'zombie' tag
        plague_zombie = factory.create_monster("plague_zombie", 0, 0, depth=5)
        
        if plague_zombie is None:
            pytest.skip("plague_zombie monster type not found")
        
        fighter = plague_zombie.get_component_optional(ComponentType.FIGHTER)
        registry = factory.registry
        pz_def = registry.get_monster("plague_zombie")
        
        # Should use zombie curve: HP 1.00x at depth 5 (no scaling)
        base_hp = pz_def.stats.hp
        expected_base_hp = base_hp
        # Check base_max_hp (not max_hp which includes CON modifier)
        assert fighter.base_max_hp == expected_base_hp
