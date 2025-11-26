"""Tests for the ETP (Effective Threat Points) budgeting system.

This module tests:
- Band configuration loading
- ETP calculation for monsters
- Room/floor budget validation
- Integration with encounter generation
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import ETP system components
from balance.etp import (
    get_monster_etp,
    get_band_for_depth,
    get_band_config,
    get_room_etp_budget,
    get_floor_etp_budget,
    get_etp_config,
    reload_etp_config,
    check_room_budget,
    get_stat_multipliers,
    calculate_monster_dps,
    calculate_durability,
    get_behavior_modifier,
    initialize_encounter_budget_engine,
    get_room_monsters_etp,
    log_room_etp_summary,
)


class TestBandConfiguration:
    """Tests for band configuration and lookup."""
    
    def test_band_for_depth_b1(self):
        """Test B1 band identification (floors 1-5)."""
        assert get_band_for_depth(1) == "B1"
        assert get_band_for_depth(3) == "B1"
        assert get_band_for_depth(5) == "B1"
    
    def test_band_for_depth_b2(self):
        """Test B2 band identification (floors 6-10)."""
        assert get_band_for_depth(6) == "B2"
        assert get_band_for_depth(8) == "B2"
        assert get_band_for_depth(10) == "B2"
    
    def test_band_for_depth_b3(self):
        """Test B3 band identification (floors 11-15)."""
        assert get_band_for_depth(11) == "B3"
        assert get_band_for_depth(13) == "B3"
        assert get_band_for_depth(15) == "B3"
    
    def test_band_for_depth_b4(self):
        """Test B4 band identification (floors 16-20)."""
        assert get_band_for_depth(16) == "B4"
        assert get_band_for_depth(18) == "B4"
        assert get_band_for_depth(20) == "B4"
    
    def test_band_for_depth_b5(self):
        """Test B5 band identification (floors 21-25)."""
        assert get_band_for_depth(21) == "B5"
        assert get_band_for_depth(23) == "B5"
        assert get_band_for_depth(25) == "B5"
    
    def test_band_for_depth_beyond_25(self):
        """Test band identification for depths beyond 25."""
        # Should default to B5 for depths beyond the defined range
        assert get_band_for_depth(26) == "B5"
        assert get_band_for_depth(30) == "B5"
    
    def test_band_config_has_required_fields(self):
        """Test that band configs have all required fields."""
        for depth in [1, 6, 11, 16, 21]:
            band_config = get_band_config(depth)
            
            assert band_config.name is not None
            assert band_config.floor_min > 0
            assert band_config.floor_max >= band_config.floor_min
            assert band_config.hp_multiplier > 0
            assert band_config.damage_multiplier > 0
            assert band_config.room_etp_min >= 0  # Can be 0 for early bands (empty rooms OK)
            assert band_config.room_etp_max >= band_config.room_etp_min
            assert band_config.floor_etp_min >= 0
            assert band_config.floor_etp_max >= band_config.floor_etp_min


class TestETPCalculation:
    """Tests for ETP calculation functions."""
    
    def test_calculate_monster_dps(self):
        """Test DPS calculation."""
        # Simple case: 4-6 damage, 0 power
        dps = calculate_monster_dps(4, 6, 0)
        assert dps == 5.0  # (4+6)/2 = 5
        
        # With power bonus
        dps_with_power = calculate_monster_dps(4, 6, 2)
        assert dps_with_power == 7.0  # 5 + 2
    
    def test_calculate_durability(self):
        """Test durability calculation."""
        # Baseline player damage is ~6.5 per hit
        # 20 HP monster: 20/6.5 = ~3 hits to kill
        # Durability = 3/3 = 1.0
        durability = calculate_durability(20)
        assert 0.9 < durability < 1.1  # Approximately 1.0
        
        # Higher HP means higher durability
        durability_high = calculate_durability(40)
        assert durability_high > durability
    
    def test_get_behavior_modifier(self):
        """Test behavior modifier lookup."""
        # Basic melee should be lower than boss
        assert get_behavior_modifier("basic") < get_behavior_modifier("boss")
        assert get_behavior_modifier("basic_melee") == 0.9
        assert get_behavior_modifier("boss") == 1.3
        
        # Unknown types should default to 1.0
        assert get_behavior_modifier("unknown_type") == 1.0
    
    def test_get_monster_etp_with_base_value(self):
        """Test ETP calculation using etp_base from entities.yaml."""
        # Orc has etp_base: 27
        orc_etp = get_monster_etp("orc", 1)
        assert orc_etp > 0
        
        # At B1 (depth 1), multiplier is 1.0, so should be close to base
        # Synergy is 1.0, band_multiplier is ~1.0
        assert 20 < orc_etp < 40  # Should be around 27
    
    def test_monster_etp_scales_with_depth(self):
        """Test that ETP increases with depth due to band multipliers."""
        orc_etp_b1 = get_monster_etp("orc", 1)   # B1
        orc_etp_b3 = get_monster_etp("orc", 11)  # B3
        orc_etp_b5 = get_monster_etp("orc", 21)  # B5
        
        # ETP should increase with band
        assert orc_etp_b3 > orc_etp_b1
        assert orc_etp_b5 > orc_etp_b3
    
    def test_troll_etp_higher_than_orc(self):
        """Test that troll (etp_base: 50) is higher than orc (etp_base: 27)."""
        orc_etp = get_monster_etp("orc", 1)
        troll_etp = get_monster_etp("troll", 1)
        
        assert troll_etp > orc_etp
    
    def test_boss_etp_very_high(self):
        """Test that boss monsters have very high ETP."""
        dragon_etp = get_monster_etp("dragon_lord", 1)
        orc_etp = get_monster_etp("orc", 1)
        
        # Dragon Lord (etp_base: 700) should be much higher than orc
        assert dragon_etp > orc_etp * 10


class TestBudgetRanges:
    """Tests for budget range functions."""
    
    def test_room_budget_increases_with_band(self):
        """Test that room ETP budgets increase with band."""
        min_b1, max_b1 = get_room_etp_budget(1)   # B1
        min_b3, max_b3 = get_room_etp_budget(11)  # B3
        min_b5, max_b5 = get_room_etp_budget(21)  # B5
        
        # Budgets should increase
        assert min_b3 > min_b1
        assert max_b3 > max_b1
        assert min_b5 > min_b3
        assert max_b5 > max_b3
    
    def test_floor_budget_increases_with_band(self):
        """Test that floor ETP budgets increase with band."""
        min_b1, max_b1 = get_floor_etp_budget(1)   # B1
        min_b3, max_b3 = get_floor_etp_budget(11)  # B3
        min_b5, max_b5 = get_floor_etp_budget(21)  # B5
        
        # Budgets should increase
        assert min_b3 > min_b1
        assert max_b3 > max_b1
        assert min_b5 > min_b3
        assert max_b5 > max_b3
    
    def test_spike_allowance(self):
        """Test that spike rooms have higher max budget."""
        min_normal, max_normal = get_room_etp_budget(1, allow_spike=False)
        min_spike, max_spike = get_room_etp_budget(1, allow_spike=True)
        
        # Spike rooms should have higher max
        assert min_spike == min_normal  # Min stays the same
        assert max_spike > max_normal   # Max is increased


class TestBudgetValidation:
    """Tests for budget validation functions."""
    
    def test_check_room_budget_within_range(self):
        """Test budget check for valid ETP."""
        min_etp, max_etp = get_room_etp_budget(1)
        mid_etp = (min_etp + max_etp) / 2
        
        is_valid, message = check_room_budget(mid_etp, 1, "test_room")
        assert is_valid
        assert "OK" in message or "within" in message.lower()
    
    def test_check_room_budget_under(self):
        """Test budget check for under-budget room."""
        # Use B3 which has non-zero min (30), so we can test under-budget
        min_etp, _ = get_room_etp_budget(11)  # B3: min=30, max=150
        under_etp = min_etp * 0.3  # Way under budget (9 vs min 30)
        
        is_valid, message = check_room_budget(under_etp, 11, "test_room")
        assert "under" in message.lower()
    
    def test_check_room_budget_over(self):
        """Test budget check for over-budget room."""
        _, max_etp = get_room_etp_budget(1)
        over_etp = max_etp * 2  # Way over budget
        
        is_valid, message = check_room_budget(over_etp, 1, "test_room")
        assert "over" in message.lower()


class TestStatMultipliers:
    """Tests for stat multiplier functions."""
    
    def test_b1_multipliers_are_baseline(self):
        """Test that B1 has baseline multipliers of 1.0."""
        hp_mult, dmg_mult = get_stat_multipliers(1)
        
        assert hp_mult == 1.0
        assert dmg_mult == 1.0
    
    def test_multipliers_increase_with_band(self):
        """Test that multipliers increase in higher bands."""
        hp_b1, dmg_b1 = get_stat_multipliers(1)   # B1
        hp_b3, dmg_b3 = get_stat_multipliers(11)  # B3
        hp_b5, dmg_b5 = get_stat_multipliers(21)  # B5
        
        assert hp_b3 > hp_b1
        assert dmg_b3 > dmg_b1
        assert hp_b5 > hp_b3
        assert dmg_b5 > dmg_b3
    
    def test_b5_multipliers_are_highest(self):
        """Test that B5 has the highest multipliers."""
        hp_mult, dmg_mult = get_stat_multipliers(25)
        
        # B5 should have 1.5x HP and 1.2x damage
        assert hp_mult == 1.5
        assert dmg_mult == 1.2


class TestETPConfigLoading:
    """Tests for ETP config loading and reload."""
    
    def test_config_loads_successfully(self):
        """Test that ETP config loads without errors."""
        config = get_etp_config()
        
        assert config is not None
        assert len(config.bands) == 5  # B1-B5
        assert len(config.behavior_modifiers) > 0
    
    def test_config_reload(self):
        """Test that config can be reloaded."""
        original_config = get_etp_config()
        reload_etp_config()
        new_config = get_etp_config()
        
        # Should still have same structure
        assert len(new_config.bands) == 5
    
    def test_all_bands_present(self):
        """Test that all 5 bands are defined."""
        config = get_etp_config()
        
        assert "B1" in config.bands
        assert "B2" in config.bands
        assert "B3" in config.bands
        assert "B4" in config.bands
        assert "B5" in config.bands


class TestEncounterBudgetEngineIntegration:
    """Tests for integration with EncounterBudgetEngine."""
    
    def test_initialize_engine(self):
        """Test that ETP values are registered with the engine."""
        from services.encounter_budget_engine import (
            get_encounter_budget_engine,
            reset_encounter_budget_engine
        )
        
        # Reset and reinitialize
        reset_encounter_budget_engine()
        initialize_encounter_budget_engine()
        
        engine = get_encounter_budget_engine()
        
        # Check that orcs were registered
        orc_etp = engine.get_etp("orc")
        assert orc_etp > 0
        
        # Check that trolls were registered
        troll_etp = engine.get_etp("troll")
        assert troll_etp > 0
    
    def test_engine_etp_matches_direct_calculation(self):
        """Test that engine ETP matches direct etp_base from entities."""
        from services.encounter_budget_engine import (
            get_encounter_budget_engine,
            reset_encounter_budget_engine
        )
        
        reset_encounter_budget_engine()
        initialize_encounter_budget_engine()
        
        engine = get_encounter_budget_engine()
        
        # Orc etp_base is 27
        assert engine.get_etp("orc") == 27
        
        # Troll etp_base is 50
        assert engine.get_etp("troll") == 50


class TestMonsterETPValues:
    """Tests to verify monster ETP values are reasonable."""
    
    def test_common_monsters_have_positive_etp(self):
        """Test that common monsters have positive ETP values."""
        orc_etp = get_monster_etp("orc", 1)
        slime_etp = get_monster_etp("slime", 1)
        troll_etp = get_monster_etp("troll", 1)
        
        # All monsters should have positive ETP
        assert orc_etp > 0
        assert slime_etp > 0
        assert troll_etp > 0
    
    def test_elite_monsters_use_more_budget(self):
        """Test that elite variants have higher ETP."""
        orc_etp = get_monster_etp("orc", 1)
        orc_chieftain_etp = get_monster_etp("orc_chieftain", 1)
        orc_veteran_etp = get_monster_etp("orc_veteran", 1)
        
        # Elites should have higher ETP
        assert orc_chieftain_etp > orc_etp
        assert orc_veteran_etp > orc_etp
    
    def test_monster_etp_ordering(self):
        """Test that monsters are ordered correctly by threat."""
        slime_etp = get_monster_etp("slime", 1)
        orc_scout_etp = get_monster_etp("orc_scout", 1)
        orc_etp = get_monster_etp("orc", 1)
        orc_veteran_etp = get_monster_etp("orc_veteran", 1)
        troll_etp = get_monster_etp("troll", 1)
        orc_chieftain_etp = get_monster_etp("orc_chieftain", 1)
        
        # Slimes are weakest, then scouts, then regular orcs
        assert slime_etp < orc_etp
        assert orc_scout_etp < orc_etp
        
        # Veterans and trolls are tougher than regular orcs
        assert orc_veteran_etp > orc_etp
        assert troll_etp > orc_etp
        
        # Chieftains are among the strongest non-boss monsters
        assert orc_chieftain_etp > orc_veteran_etp
    
    def test_boss_monster_very_high_etp(self):
        """Test that boss monsters have much higher ETP than regular monsters."""
        orc_etp = get_monster_etp("orc", 1)
        dragon_etp = get_monster_etp("dragon_lord", 1)
        
        # Dragon Lord should be at least 10x more threatening than an orc
        assert dragon_etp >= orc_etp * 10


class TestRoomMonsterETPCalculation:
    """Tests for room-level ETP calculations."""
    
    def test_get_room_monsters_etp_empty(self):
        """Test ETP calculation for empty room."""
        total_etp, breakdown = get_room_monsters_etp([], 1)
        
        assert total_etp == 0.0
        assert len(breakdown) == 0
    
    def test_get_room_monsters_etp_with_tuples(self):
        """Test ETP calculation with (type, count) tuples."""
        monsters = [("orc", 2), ("troll", 1)]
        total_etp, breakdown = get_room_monsters_etp(monsters, 1)
        
        assert total_etp > 0
        assert len(breakdown) == 2


class TestLoggingFunctions:
    """Tests for logging functions (basic smoke tests)."""
    
    def test_log_room_etp_summary_no_crash(self):
        """Test that room logging doesn't crash."""
        # This should not raise any exceptions
        log_room_etp_summary(
            room_id="test_room",
            depth=1,
            monster_list=[("orc", 27)],
            total_etp=27.0,
            budget_min=3,
            budget_max=5
        )


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

