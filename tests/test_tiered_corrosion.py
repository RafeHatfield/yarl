"""Phase 19: Tests for tiered slime corrosion chance.

Tests that different slime tiers have different corrosion chances:
- Minor/small slimes: 5%
- Normal/large slimes: 10%
- Greater slimes: 15%
"""

import pytest
from config.factories import get_entity_factory


class TestTieredCorrosionChance:
    """Test that slime tiers have different corrosion chances."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = get_entity_factory()
    
    def test_minor_slime_has_5_percent_corrosion_chance(self):
        """Minor slimes should have 5% corrosion chance."""
        slime = self.factory.create_monster("slime", 5, 5)
        
        assert hasattr(slime, 'corrosion_chance'), "Minor slime should have corrosion_chance attribute"
        assert slime.corrosion_chance == 0.05, "Minor slime should have 5% (0.05) corrosion chance"
    
    def test_large_slime_has_10_percent_corrosion_chance(self):
        """Large slimes should have 10% corrosion chance."""
        large_slime = self.factory.create_monster("large_slime", 5, 5)
        
        assert hasattr(large_slime, 'corrosion_chance'), "Large slime should have corrosion_chance attribute"
        assert large_slime.corrosion_chance == 0.10, "Large slime should have 10% (0.10) corrosion chance"
    
    def test_greater_slime_has_15_percent_corrosion_chance(self):
        """Greater slimes should have 15% corrosion chance."""
        greater_slime = self.factory.create_monster("greater_slime", 5, 5)
        
        assert hasattr(greater_slime, 'corrosion_chance'), "Greater slime should have corrosion_chance attribute"
        assert greater_slime.corrosion_chance == 0.15, "Greater slime should have 15% (0.15) corrosion chance"
    
    def test_corrosion_chance_increases_with_tier(self):
        """Verify corrosion chance increases: minor < large < greater."""
        slime = self.factory.create_monster("slime", 5, 5)
        large_slime = self.factory.create_monster("large_slime", 5, 5)
        greater_slime = self.factory.create_monster("greater_slime", 5, 5)
        
        assert slime.corrosion_chance < large_slime.corrosion_chance, \
            "Large slime corrosion chance should be higher than minor slime"
        assert large_slime.corrosion_chance < greater_slime.corrosion_chance, \
            "Greater slime corrosion chance should be higher than large slime"
    
    def test_all_slimes_have_corrosion_ability(self):
        """All slime tiers should have corrosion in special_abilities."""
        slime = self.factory.create_monster("slime", 5, 5)
        large_slime = self.factory.create_monster("large_slime", 5, 5)
        greater_slime = self.factory.create_monster("greater_slime", 5, 5)
        
        assert 'corrosion' in slime.special_abilities, "Minor slime should have corrosion ability"
        assert 'corrosion' in large_slime.special_abilities, "Large slime should have corrosion ability"
        assert 'corrosion' in greater_slime.special_abilities, "Greater slime should have corrosion ability"


if __name__ == '__main__':
    pytest.main([__file__, "-v"])


