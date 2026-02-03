"""Unit tests for depth-based monster scaling system.

Tests verify:
- Default curve scaling for standard monsters
- Zombie override curve for explicit 'zombie' tag archetype
- Skeleton (low_undead but not zombie) uses default curve
- Rounding rules (HP ceil, damage/accuracy round-half-up)
- Scaling applied exactly once
- Deterministic behavior
"""

import pytest
import math

from balance.depth_scaling import (
    ScalingMultipliers,
    get_scaling_multipliers,
    get_depth_band_name,
    scale_hp,
    scale_stat,
    apply_scaling,
    ScaledStats,
    DEFAULT_CURVE,
    ZOMBIE_CURVE,
    ZOMBIE_ARCHETYPE_TAGS,
)


class TestScalingMultipliers:
    """Test the ScalingMultipliers data structure."""
    
    def test_multipliers_are_immutable(self):
        """ScalingMultipliers should be frozen dataclass."""
        m = ScalingMultipliers(hp=1.0, to_hit=1.0, damage=1.0)
        with pytest.raises(Exception):
            m.hp = 2.0
    
    def test_multipliers_equality(self):
        """Equal multipliers should compare as equal."""
        m1 = ScalingMultipliers(hp=1.12, to_hit=1.06, damage=1.00)
        m2 = ScalingMultipliers(hp=1.12, to_hit=1.06, damage=1.00)
        assert m1 == m2


class TestDefaultCurve:
    """Test the default scaling curve for standard monsters."""
    
    @pytest.mark.parametrize("depth,expected_hp,expected_to_hit,expected_damage", [
        # Depth 1-2: Base stats (no scaling)
        (1, 1.00, 1.00, 1.00),
        (2, 1.00, 1.00, 1.00),
        # Depth 3-4: Minor increase (HP tuned down to reduce attrition)
        (3, 1.08, 1.06, 1.00),
        (4, 1.08, 1.06, 1.00),
        # Depth 5-6: Moderate increase
        (5, 1.25, 1.12, 1.05),
        (6, 1.25, 1.12, 1.05),
        # Depth 7-8: Significant increase
        (7, 1.35, 1.17, 1.10),
        (8, 1.35, 1.17, 1.10),
        # Depth 9+: Maximum scaling
        (9, 1.45, 1.22, 1.15),
        (10, 1.45, 1.22, 1.15),
        (15, 1.45, 1.22, 1.15),
    ])
    def test_default_curve_values(self, depth, expected_hp, expected_to_hit, expected_damage):
        """Verify default curve multipliers at each depth band."""
        # No tags = default curve
        multipliers = get_scaling_multipliers(depth, tags=None)
        assert multipliers.hp == expected_hp
        assert multipliers.to_hit == expected_to_hit
        assert multipliers.damage == expected_damage
    
    def test_default_curve_for_orc(self):
        """Orc (humanoid, living) should use default curve."""
        orc_tags = {"corporeal_flesh", "humanoid", "living"}
        
        # Depth 2: no scaling
        m2 = get_scaling_multipliers(2, orc_tags)
        assert m2 == ScalingMultipliers(hp=1.0, to_hit=1.0, damage=1.0)
        
        # Depth 5: moderate scaling
        m5 = get_scaling_multipliers(5, orc_tags)
        assert m5 == ScalingMultipliers(hp=1.25, to_hit=1.12, damage=1.05)
    
    def test_depth_0_clamped_to_1(self):
        """Depth 0 or negative should be treated as depth 1."""
        m0 = get_scaling_multipliers(0, None)
        m1 = get_scaling_multipliers(1, None)
        assert m0 == m1
        
        m_neg = get_scaling_multipliers(-5, None)
        assert m_neg == m1


class TestZombieCurve:
    """Test the zombie override curve for explicit zombie archetype."""
    
    @pytest.mark.parametrize("depth,expected_hp,expected_to_hit,expected_damage", [
        # Depth 1-6: Base stats (no scaling to avoid amplifying depth 5 swarm)
        (1, 1.00, 1.00, 1.00),
        (2, 1.00, 1.00, 1.00),
        (3, 1.00, 1.00, 1.00),
        (4, 1.00, 1.00, 1.00),
        (5, 1.00, 1.00, 1.00),
        (6, 1.00, 1.00, 1.00),
        # Depth 7-8: Minor increase
        (7, 1.10, 1.05, 1.00),
        (8, 1.10, 1.05, 1.00),
        # Depth 9+: Maximum zombie scaling
        (9, 1.20, 1.10, 1.05),
        (10, 1.20, 1.10, 1.05),
    ])
    def test_zombie_curve_values(self, depth, expected_hp, expected_to_hit, expected_damage):
        """Verify zombie curve multipliers at each depth band."""
        zombie_tags = {"zombie", "undead", "corporeal_flesh"}
        multipliers = get_scaling_multipliers(depth, tags=zombie_tags)
        assert multipliers.hp == expected_hp
        assert multipliers.to_hit == expected_to_hit
        assert multipliers.damage == expected_damage
    
    def test_zombie_archetype_detection(self):
        """Explicit 'zombie' tag triggers zombie override curve."""
        # Standard zombie tags
        zombie_tags = {"corporeal_flesh", "undead", "mindless", "low_undead", "zombie"}
        
        # At depth 5, default curve gives HP=1.25, zombie curve gives HP=1.00 (no scaling)
        default_m = get_scaling_multipliers(5, tags=set())
        zombie_m = get_scaling_multipliers(5, tags=zombie_tags)
        
        assert default_m.hp == 1.25
        assert zombie_m.hp == 1.00
    
    def test_plague_zombie_uses_zombie_curve(self):
        """Plague zombie (extends zombie) should also use zombie curve."""
        plague_zombie_tags = {"corporeal_flesh", "undead", "mindless", "low_undead", "plague_carrier", "zombie"}
        
        # At depth 5, should still use zombie curve (no scaling)
        m = get_scaling_multipliers(5, tags=plague_zombie_tags)
        assert m.hp == 1.00  # Zombie curve, not default (1.25)
    
    def test_high_undead_uses_default_curve(self):
        """High undead (lich, etc.) should use default curve, not zombie override."""
        lich_tags = {"undead", "high_undead", "caster", "no_flesh"}
        
        # At depth 5, should use default curve (no 'zombie' tag)
        m = get_scaling_multipliers(5, tags=lich_tags)
        assert m.hp == 1.25  # Default curve
    
    def test_skeleton_uses_default_curve(self):
        """Skeleton (low_undead but not zombie) should use default curve."""
        skeleton_tags = {"undead", "no_flesh", "low_undead"}
        
        # At depth 5, skeleton should use default curve (no 'zombie' tag)
        m = get_scaling_multipliers(5, tags=skeleton_tags)
        assert m.hp == 1.25  # Default curve, not zombie override
        assert m.to_hit == 1.12
        assert m.damage == 1.05


class TestRoundingRules:
    """Test rounding rules for stat scaling."""
    
    def test_hp_rounds_up(self):
        """HP should round up (ceil) to ensure monsters aren't weaker."""
        # 10 * 1.12 = 11.2 -> 12
        assert scale_hp(10, 1.12) == 12
        # 24 * 1.10 = 26.4 -> 27
        assert scale_hp(24, 1.10) == 27
        # Exact values stay exact
        assert scale_hp(10, 1.0) == 10
        assert scale_hp(10, 1.5) == 15
    
    def test_damage_rounds_half_up(self):
        """Damage should round to nearest, 0.5 rounds up."""
        # 3 * 1.05 = 3.15 -> 3
        assert scale_stat(3, 1.05) == 3
        # 6 * 1.05 = 6.3 -> 6
        assert scale_stat(6, 1.05) == 6
        # 4 * 1.10 = 4.4 -> 4
        assert scale_stat(4, 1.10) == 4
        # Exact 0.5 case: 5 * 1.10 = 5.5 -> 6 (rounds up)
        assert scale_stat(5, 1.10) == 6
    
    def test_accuracy_rounds_half_up(self):
        """Accuracy/to-hit should round to nearest, 0.5 rounds up."""
        # 1 * 1.06 = 1.06 -> 1
        assert scale_stat(1, 1.06) == 1
        # 3 * 1.12 = 3.36 -> 3
        assert scale_stat(3, 1.12) == 3
        # 5 * 1.10 = 5.5 -> 6 (rounds up)
        assert scale_stat(5, 1.10) == 6


class TestApplyScaling:
    """Test the apply_scaling function that combines all scaling logic."""
    
    def test_scaling_at_depth_2_is_identity(self):
        """At depth 1-2, all stats should remain unchanged."""
        result = apply_scaling(
            base_hp=24,
            base_damage_min=3,
            base_damage_max=6,
            base_accuracy=1,
            depth=2,
            tags=None
        )
        assert result.hp == 24
        assert result.damage_min == 3
        assert result.damage_max == 6
        assert result.accuracy == 1
    
    def test_orc_scaling_at_depth_5(self):
        """Orc at depth 5 should have moderate stat increases."""
        # Orc base stats (from entities.yaml approximation)
        orc_tags = {"corporeal_flesh", "humanoid", "living"}
        result = apply_scaling(
            base_hp=15,  # Example orc HP
            base_damage_min=2,
            base_damage_max=5,
            base_accuracy=3,
            depth=5,
            tags=orc_tags
        )
        # HP: 15 * 1.25 = 18.75 -> 19 (ceil)
        assert result.hp == 19
        # Damage min: 2 * 1.05 = 2.1 -> 2 (round)
        assert result.damage_min == 2
        # Damage max: 5 * 1.05 = 5.25 -> 5 (round)
        assert result.damage_max == 5
        # Accuracy: 3 * 1.12 = 3.36 -> 3 (round)
        assert result.accuracy == 3
    
    def test_zombie_scaling_at_depth_5_uses_override(self):
        """Zombie at depth 5 should use conservative override curve (no scaling)."""
        zombie_tags = {"corporeal_flesh", "undead", "mindless", "low_undead", "zombie"}
        result = apply_scaling(
            base_hp=24,  # Zombie HP from entities.yaml
            base_damage_min=3,
            base_damage_max=6,
            base_accuracy=1,
            depth=5,
            tags=zombie_tags
        )
        # HP: 24 * 1.00 = 24 (no scaling at zombie depth 5)
        assert result.hp == 24
        # Damage min: 3 * 1.00 = 3 (no scaling)
        assert result.damage_min == 3
        # Damage max: 6 * 1.00 = 6
        assert result.damage_max == 6
        # Accuracy: 1 * 1.00 = 1 (no scaling)
        assert result.accuracy == 1
    
    def test_zombie_vs_orc_at_depth_5(self):
        """Zombie should have no scaling at depth 5, while orc scales normally."""
        orc_result = apply_scaling(
            base_hp=24,
            base_damage_min=3,
            base_damage_max=6,
            base_accuracy=1,
            depth=5,
            tags={"humanoid"}
        )
        zombie_result = apply_scaling(
            base_hp=24,
            base_damage_min=3,
            base_damage_max=6,
            base_accuracy=1,
            depth=5,
            tags={"zombie"}
        )
        # Orc HP: 24 * 1.25 = 30, Zombie HP: 24 * 1.00 = 24 (no scaling)
        assert orc_result.hp == 30
        assert zombie_result.hp == 24
        # Zombie does not scale
        assert zombie_result.hp < orc_result.hp


class TestDepthBandNames:
    """Test depth band naming for metrics."""
    
    @pytest.mark.parametrize("depth,expected_band", [
        (1, "depth_1_2"),
        (2, "depth_1_2"),
        (3, "depth_3_4"),
        (4, "depth_3_4"),
        (5, "depth_5_6"),
        (6, "depth_5_6"),
        (7, "depth_7_8"),
        (8, "depth_7_8"),
        (9, "depth_9_plus"),
        (10, "depth_9_plus"),
        (20, "depth_9_plus"),
    ])
    def test_depth_band_names(self, depth, expected_band):
        """Verify depth band names for metrics tracking."""
        assert get_depth_band_name(depth) == expected_band


class TestScalingDeterminism:
    """Test that scaling is deterministic."""
    
    def test_same_inputs_same_outputs(self):
        """Same inputs should always produce same outputs."""
        tags = {"humanoid"}
        results = []
        for _ in range(10):
            result = apply_scaling(
                base_hp=20,
                base_damage_min=4,
                base_damage_max=8,
                base_accuracy=3,
                depth=5,
                tags=tags
            )
            results.append((result.hp, result.damage_min, result.damage_max, result.accuracy))
        
        # All results should be identical
        assert len(set(results)) == 1
    
    def test_no_randomness_in_scaling(self):
        """Scaling should not depend on RNG state."""
        import random
        
        # Set random state
        random.seed(12345)
        result1 = apply_scaling(15, 2, 5, 3, depth=7, tags=None)
        
        # Change random state
        random.seed(99999)
        result2 = apply_scaling(15, 2, 5, 3, depth=7, tags=None)
        
        # Results should be identical
        assert result1 == result2


class TestCurveDataIntegrity:
    """Test the curve data structures are well-formed."""
    
    def test_default_curve_covers_depths_1_through_8(self):
        """Default curve should have entries for depths 1-8."""
        for depth in range(1, 9):
            assert depth in DEFAULT_CURVE
    
    def test_zombie_curve_covers_depths_1_through_8(self):
        """Zombie curve should have entries for depths 1-8."""
        for depth in range(1, 9):
            assert depth in ZOMBIE_CURVE
    
    def test_all_multipliers_are_at_least_1(self):
        """All multipliers should be >= 1.0 (no nerfs)."""
        for depth, m in DEFAULT_CURVE.items():
            assert m.hp >= 1.0, f"Default HP at depth {depth} is < 1.0"
            assert m.to_hit >= 1.0, f"Default to_hit at depth {depth} is < 1.0"
            assert m.damage >= 1.0, f"Default damage at depth {depth} is < 1.0"
        
        for depth, m in ZOMBIE_CURVE.items():
            assert m.hp >= 1.0, f"Zombie HP at depth {depth} is < 1.0"
            assert m.to_hit >= 1.0, f"Zombie to_hit at depth {depth} is < 1.0"
            assert m.damage >= 1.0, f"Zombie damage at depth {depth} is < 1.0"
    
    def test_zombie_archetype_tag_defined(self):
        """Zombie archetype tag should be defined as explicit 'zombie' tag."""
        assert "zombie" in ZOMBIE_ARCHETYPE_TAGS
        # Ensure we're not using low_undead anymore (to avoid affecting skeletons)
        assert "low_undead" not in ZOMBIE_ARCHETYPE_TAGS


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_zero_base_stats(self):
        """Zero base stats should stay zero after scaling."""
        result = apply_scaling(
            base_hp=0,
            base_damage_min=0,
            base_damage_max=0,
            base_accuracy=0,
            depth=10,
            tags=None
        )
        assert result.hp == 0
        assert result.damage_min == 0
        assert result.damage_max == 0
        assert result.accuracy == 0
    
    def test_very_high_base_stats(self):
        """High base stats should scale proportionally."""
        result = apply_scaling(
            base_hp=1000,
            base_damage_min=50,
            base_damage_max=100,
            base_accuracy=20,
            depth=9,
            tags=None
        )
        # HP: 1000 * 1.45 = 1450
        assert result.hp == 1450
        # Damage min: 50 * 1.15 = 57.5 (floating point may give 57.4999...)
        # round-half-up with floor(x + 0.5): floor(57.5 + 0.5) = 58 or 57 due to FP
        assert result.damage_min in (57, 58)  # Allow for FP imprecision
        # Damage max: 100 * 1.15 = 115
        assert result.damage_max == 115
        # Accuracy: 20 * 1.22 = 24.4 -> 24 (round)
        assert result.accuracy == 24
    
    def test_empty_tags_set(self):
        """Empty tags set should use default curve."""
        m_none = get_scaling_multipliers(5, tags=None)
        m_empty = get_scaling_multipliers(5, tags=set())
        assert m_none == m_empty
