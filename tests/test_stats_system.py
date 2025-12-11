"""Tests for the D&D-style stat system (STR/DEX/CON).

This test suite ensures that:
- Stat modifiers are calculated correctly ((stat - 10) // 2)
- Stats are properly initialized from entity configuration
- Stats default to 10 if not provided
- Stat properties (strength_mod, dexterity_mod, constitution_mod) work correctly
"""

import unittest
from components.fighter import Fighter
from entity import Entity


class TestStatModifierCalculation(unittest.TestCase):
    """Test the stat modifier calculation formula."""
    
    def test_stat_modifier_formula_negative(self):
        """Test negative modifiers (stats 8-9)."""
        self.assertEqual(Fighter.get_stat_modifier(8), -1)
        self.assertEqual(Fighter.get_stat_modifier(9), -1)
    
    def test_stat_modifier_formula_zero(self):
        """Test zero modifier (stats 10-11)."""
        self.assertEqual(Fighter.get_stat_modifier(10), 0)
        self.assertEqual(Fighter.get_stat_modifier(11), 0)
    
    def test_stat_modifier_formula_positive(self):
        """Test positive modifiers (stats 12+)."""
        self.assertEqual(Fighter.get_stat_modifier(12), 1)
        self.assertEqual(Fighter.get_stat_modifier(13), 1)
        self.assertEqual(Fighter.get_stat_modifier(14), 2)
        self.assertEqual(Fighter.get_stat_modifier(15), 2)
        self.assertEqual(Fighter.get_stat_modifier(16), 3)
        self.assertEqual(Fighter.get_stat_modifier(17), 3)
        self.assertEqual(Fighter.get_stat_modifier(18), 4)
    
    def test_stat_modifier_formula_extreme_low(self):
        """Test very low stats (edge case)."""
        self.assertEqual(Fighter.get_stat_modifier(3), -4)
        self.assertEqual(Fighter.get_stat_modifier(6), -2)
    
    def test_stat_modifier_formula_extreme_high(self):
        """Test very high stats (edge case)."""
        self.assertEqual(Fighter.get_stat_modifier(20), 5)
        self.assertEqual(Fighter.get_stat_modifier(22), 6)


class TestFighterStatProperties(unittest.TestCase):
    """Test Fighter component stat properties."""
    
    def test_strength_modifier_property(self):
        """Test strength_mod property."""
        fighter = Fighter(hp=30, defense=0, power=0, strength=14, dexterity=10, constitution=10)
        self.assertEqual(fighter.strength_mod, 2)
    
    def test_dexterity_modifier_property(self):
        """Test dexterity_mod property."""
        fighter = Fighter(hp=30, defense=0, power=0, strength=10, dexterity=16, constitution=10)
        self.assertEqual(fighter.dexterity_mod, 3)
    
    def test_constitution_modifier_property(self):
        """Test constitution_mod property."""
        fighter = Fighter(hp=30, defense=0, power=0, strength=10, dexterity=10, constitution=12)
        self.assertEqual(fighter.constitution_mod, 1)
    
    def test_all_modifiers_together(self):
        """Test all stat modifiers together."""
        fighter = Fighter(
            hp=30, defense=0, power=0,
            strength=14,  # +2
            dexterity=12,  # +1
            constitution=16  # +3
        )
        self.assertEqual(fighter.strength_mod, 2)
        self.assertEqual(fighter.dexterity_mod, 1)
        self.assertEqual(fighter.constitution_mod, 3)


class TestFighterStatDefaults(unittest.TestCase):
    """Test that stats default to 10 if not provided."""
    
    def test_default_stats_all_zero_modifiers(self):
        """Test that default stats (10) give 0 modifiers."""
        fighter = Fighter(hp=30, defense=0, power=0)
        self.assertEqual(fighter.strength, 10)
        self.assertEqual(fighter.dexterity, 10)
        self.assertEqual(fighter.constitution, 10)
        self.assertEqual(fighter.strength_mod, 0)
        self.assertEqual(fighter.dexterity_mod, 0)
        self.assertEqual(fighter.constitution_mod, 0)
    
    def test_explicit_stats_override_defaults(self):
        """Test that explicitly provided stats override defaults."""
        fighter = Fighter(
            hp=30, defense=0, power=0,
            strength=18, dexterity=8, constitution=14
        )
        self.assertEqual(fighter.strength, 18)
        self.assertEqual(fighter.dexterity, 8)
        self.assertEqual(fighter.constitution, 14)
        self.assertEqual(fighter.strength_mod, 4)
        self.assertEqual(fighter.dexterity_mod, -1)
        self.assertEqual(fighter.constitution_mod, 2)


class TestMonsterStatInitialization(unittest.TestCase):
    """Test that monsters are initialized with correct stats."""
    
    @classmethod
    def setUpClass(cls):
        """Load entity configuration once for all tests in this class."""
        from config.entity_registry import load_entity_config
        load_entity_config()
    
    def test_orc_stats(self):
        """Test orc gets STR 14, DEX 10, CON 12."""
        from config.entity_factory import get_entity_factory
        entity_factory = get_entity_factory()
        
        orc = entity_factory.create_monster("orc", 5, 5)
        
        self.assertIsNotNone(orc)
        self.assertIsNotNone(orc.fighter)
        self.assertEqual(orc.fighter.strength, 14)
        self.assertEqual(orc.fighter.dexterity, 10)
        self.assertEqual(orc.fighter.constitution, 12)
        self.assertEqual(orc.fighter.strength_mod, 2)
        self.assertEqual(orc.fighter.dexterity_mod, 0)
        self.assertEqual(orc.fighter.constitution_mod, 1)
    
    def test_troll_stats(self):
        """Test troll gets STR 16, DEX 8, CON 16."""
        from config.entity_factory import get_entity_factory
        entity_factory = get_entity_factory()
        
        troll = entity_factory.create_monster("troll", 5, 5)
        
        self.assertIsNotNone(troll)
        self.assertIsNotNone(troll.fighter)
        self.assertEqual(troll.fighter.strength, 16)
        self.assertEqual(troll.fighter.dexterity, 8)
        self.assertEqual(troll.fighter.constitution, 16)
        self.assertEqual(troll.fighter.strength_mod, 3)
        self.assertEqual(troll.fighter.dexterity_mod, -1)
        self.assertEqual(troll.fighter.constitution_mod, 3)
    
    def test_slime_stats(self):
        """Test slime gets STR 8, DEX 6, CON 10."""
        from config.entity_factory import get_entity_factory
        entity_factory = get_entity_factory()
        
        slime = entity_factory.create_monster("slime", 5, 5)
        
        self.assertIsNotNone(slime)
        self.assertIsNotNone(slime.fighter)
        self.assertEqual(slime.fighter.strength, 8)
        self.assertEqual(slime.fighter.dexterity, 6)
        self.assertEqual(slime.fighter.constitution, 10)
        self.assertEqual(slime.fighter.strength_mod, -1)
        self.assertEqual(slime.fighter.dexterity_mod, -2)
        self.assertEqual(slime.fighter.constitution_mod, 0)
    
    def test_large_slime_stats(self):
        """Test large slime gets STR 12, DEX 6, CON 14."""
        from config.entity_factory import get_entity_factory
        entity_factory = get_entity_factory()
        
        large_slime = entity_factory.create_monster("large_slime", 5, 5)
        
        self.assertIsNotNone(large_slime)
        self.assertIsNotNone(large_slime.fighter)
        self.assertEqual(large_slime.fighter.strength, 12)
        self.assertEqual(large_slime.fighter.dexterity, 6)
        self.assertEqual(large_slime.fighter.constitution, 14)
        self.assertEqual(large_slime.fighter.strength_mod, 1)
        self.assertEqual(large_slime.fighter.dexterity_mod, -2)
        self.assertEqual(large_slime.fighter.constitution_mod, 2)


class TestPlayerStatInitialization(unittest.TestCase):
    """Test that player is initialized with correct stats."""
    
    @classmethod
    def setUpClass(cls):
        """Load entity configuration once for all tests in this class."""
        from config.entity_registry import load_entity_config
        load_entity_config()
    
    def test_player_standard_stats(self):
        """Test player gets STR 14, DEX 12, CON 14 (standard fighter)."""
        from config.entity_factory import get_entity_factory
        
        # Get player stats from entity factory instead of full game initialization
        entity_factory = get_entity_factory()
        player_stats = entity_factory.get_player_stats()
        
        self.assertIsNotNone(player_stats)
        self.assertEqual(player_stats.strength, 14)
        self.assertEqual(player_stats.dexterity, 14)  # Phase 13F: buffed from 12
        self.assertEqual(player_stats.constitution, 14)


class TestStatModifierEdgeCases(unittest.TestCase):
    """Test edge cases for stat modifiers."""
    
    def test_stat_1_gives_minus_5(self):
        """Test minimum D&D stat (1) gives -5 modifier."""
        self.assertEqual(Fighter.get_stat_modifier(1), -5)
    
    def test_stat_30_gives_plus_10(self):
        """Test very high stat (30) gives +10 modifier."""
        self.assertEqual(Fighter.get_stat_modifier(30), 10)
    
    def test_stat_modifier_is_integer_division(self):
        """Test that stat modifier uses integer division (no rounding)."""
        # 11 - 10 = 1, 1 // 2 = 0 (not rounded up)
        self.assertEqual(Fighter.get_stat_modifier(11), 0)
        # 13 - 10 = 3, 3 // 2 = 1 (not rounded up to 2)
        self.assertEqual(Fighter.get_stat_modifier(13), 1)


if __name__ == '__main__':
    unittest.main()

