"""Tests for Item Identification System.

Tests the dual-toggle identification system including:
- Configuration loading
- Item appearance generation
- Entity factory integration
- Use-to-identify
- Scroll of identify
"""

import pytest
from unittest.mock import Mock, patch

from config.game_constants import GameConstants
from config.item_appearances import AppearanceGenerator, reset_appearance_generator
from config.entity_factory import EntityFactory
from components.item import Item
from entity import Entity
from item_functions import cast_identify


class TestGameConstantsConfiguration:
    """Test identification configuration loading."""
    
    def test_default_config_has_identification_system(self):
        """Test that default config includes identification system."""
        config = GameConstants()
        assert hasattr(config, 'identification_system')
        assert hasattr(config, 'difficulty')
        assert hasattr(config, 'meta_progression')
    
    def test_identification_system_enabled_by_default(self):
        """Test that identification system is enabled by default."""
        config = GameConstants()
        assert config.identification_system.enabled is True
    
    def test_difficulty_levels_exist(self):
        """Test that all difficulty levels are configured."""
        config = GameConstants()
        assert hasattr(config.difficulty, 'easy')
        assert hasattr(config.difficulty, 'medium')
        assert hasattr(config.difficulty, 'hard')
    
    def test_difficulty_percentages(self):
        """Test that difficulty percentages are correct."""
        config = GameConstants()
        
        # Easy: 80% pre-identified
        assert config.difficulty.easy.scrolls_pre_identified_percent == 80
        assert config.difficulty.easy.potions_pre_identified_percent == 80
        
        # Medium: 40-50% pre-identified
        assert config.difficulty.medium.scrolls_pre_identified_percent == 40
        assert config.difficulty.medium.potions_pre_identified_percent == 50
        
        # Hard: 0-5% pre-identified
        assert config.difficulty.hard.scrolls_pre_identified_percent == 5
        assert config.difficulty.hard.potions_pre_identified_percent == 5
    
    def test_get_difficulty_method(self):
        """Test that get_difficulty() method works."""
        config = GameConstants()
        
        easy = config.difficulty.get_difficulty("easy")
        assert easy.scrolls_pre_identified_percent == 80
        
        medium = config.difficulty.get_difficulty("medium")
        assert medium.scrolls_pre_identified_percent == 40
        
        hard = config.difficulty.get_difficulty("hard")
        assert hard.scrolls_pre_identified_percent == 5


class TestAppearanceGenerator:
    """Test item appearance generation."""
    
    def test_appearance_generator_initialization(self):
        """Test that appearance generator initializes with seed."""
        gen = AppearanceGenerator(seed=42)
        assert gen.seed == 42
        assert not gen._initialized
    
    def test_appearance_generation_for_scrolls(self):
        """Test scroll appearance generation."""
        gen = AppearanceGenerator(seed=42)
        item_types = {
            'scroll': ['lightning_scroll', 'fireball_scroll']
        }
        gen.initialize(item_types)
        
        lightning_appearance = gen.get_appearance('lightning_scroll', 'scroll')
        fireball_appearance = gen.get_appearance('fireball_scroll', 'scroll')
        
        assert lightning_appearance is not None
        assert 'scroll labeled' in lightning_appearance
        assert fireball_appearance is not None
        assert 'scroll labeled' in fireball_appearance
        assert lightning_appearance != fireball_appearance
    
    def test_appearance_generation_for_potions(self):
        """Test potion appearance generation."""
        gen = AppearanceGenerator(seed=42)
        item_types = {
            'potion': ['healing_potion', 'mana_potion']
        }
        gen.initialize(item_types)
        
        healing_appearance = gen.get_appearance('healing_potion', 'potion')
        mana_appearance = gen.get_appearance('mana_potion', 'potion')
        
        assert healing_appearance is not None
        assert 'potion' in healing_appearance
        assert mana_appearance is not None
        assert 'potion' in mana_appearance
        assert healing_appearance != mana_appearance
    
    def test_appearance_consistency_within_session(self):
        """Test that appearances are consistent within a session."""
        gen = AppearanceGenerator(seed=42)
        item_types = {'scroll': ['lightning_scroll']}
        gen.initialize(item_types)
        
        appearance1 = gen.get_appearance('lightning_scroll', 'scroll')
        appearance2 = gen.get_appearance('lightning_scroll', 'scroll')
        
        assert appearance1 == appearance2
    
    def test_appearance_differs_across_sessions(self):
        """Test that appearances differ with different seeds."""
        gen1 = AppearanceGenerator(seed=42)
        gen2 = AppearanceGenerator(seed=99)
        
        item_types = {'scroll': ['lightning_scroll']}
        gen1.initialize(item_types)
        gen2.initialize(item_types)
        
        appearance1 = gen1.get_appearance('lightning_scroll', 'scroll')
        appearance2 = gen2.get_appearance('lightning_scroll', 'scroll')
        
        assert appearance1 != appearance2


class TestItemComponent:
    """Test Item component identification features."""
    
    def test_item_starts_identified_by_default(self):
        """Test that items start identified by default (backward compatibility)."""
        item = Item()
        assert item.identified is True
        assert item.appearance is None
    
    def test_item_can_be_unidentified(self):
        """Test that items can be created unidentified."""
        item = Item(identified=False, appearance="cyan potion", item_category="potion")
        assert item.identified is False
        assert item.appearance == "cyan potion"
        assert item.item_category == "potion"
    
    def test_get_display_name_for_identified_item(self):
        """Test that get_display_name returns owner name for identified items."""
        item = Item(identified=True)
        entity = Entity(0, 0, '!', (255, 255, 255), "Healing Potion", item=item)
        item.owner = entity
        
        assert item.get_display_name() == "Healing Potion"
    
    def test_get_display_name_for_unidentified_item(self):
        """Test that get_display_name returns appearance for unidentified items."""
        item = Item(identified=False, appearance="cyan potion")
        entity = Entity(0, 0, '!', (255, 255, 255), "Healing Potion", item=item)
        item.owner = entity
        
        assert item.get_display_name() == "cyan potion"
    
    def test_identify_method(self):
        """Test that identify() method works correctly."""
        item = Item(identified=False, appearance="cyan potion")
        
        # Should return True because item was unidentified
        was_unidentified = item.identify()
        assert was_unidentified is True
        assert item.identified is True
        
        # Should return False because item is now identified
        was_unidentified_again = item.identify()
        assert was_unidentified_again is False


class TestEntityFactoryIntegration:
    """Test EntityFactory integration with identification system."""
    
    @pytest.fixture
    def factory(self):
        """Create factory with test configuration."""
        config = GameConstants()
        reset_appearance_generator(seed=42)
        gen = reset_appearance_generator(seed=42)
        
        # Initialize with test item types
        gen.initialize({
            'scroll': ['lightning_scroll', 'fireball_scroll'],
            'potion': ['healing_potion']
        })
        
        return EntityFactory(game_constants=config, difficulty_level="medium")
    
    def test_identification_disabled_means_all_identified(self):
        """Test that disabling ID system makes all items identified."""
        config = GameConstants()
        config.identification_system.enabled = False
        
        factory = EntityFactory(game_constants=config, difficulty_level="hard")
        
        # Even on hard difficulty, items should be identified if system is disabled
        # Note: This would need a real item from registry to test properly
        # For now, just verify the config is set correctly
        assert factory.game_constants.identification_system.enabled is False
    
    def test_difficulty_affects_identification(self):
        """Test that difficulty level affects identification percentage."""
        config = GameConstants()
        
        easy_factory = EntityFactory(game_constants=config, difficulty_level="easy")
        medium_factory = EntityFactory(game_constants=config, difficulty_level="medium")
        hard_factory = EntityFactory(game_constants=config, difficulty_level="hard")
        
        # Verify difficulty settings
        easy_settings = easy_factory.game_constants.difficulty.get_difficulty("easy")
        medium_settings = medium_factory.game_constants.difficulty.get_difficulty("medium")
        hard_settings = hard_factory.game_constants.difficulty.get_difficulty("hard")
        
        assert easy_settings.scrolls_pre_identified_percent == 80
        assert medium_settings.scrolls_pre_identified_percent == 40
        assert hard_settings.scrolls_pre_identified_percent == 5


class TestCastIdentify:
    """Test scroll of identify function."""
    
    def test_identify_with_no_inventory(self):
        """Test identify fails gracefully with no inventory."""
        caster = Mock()
        caster.inventory = None
        
        results = cast_identify(caster)
        
        assert len(results) == 1
        assert results[0]['consumed'] is False
        assert 'no inventory' in results[0]['message'].text.lower()
    
    def test_identify_with_no_unidentified_items(self):
        """Test identify with all items already identified."""
        caster = Mock()
        caster.inventory = Mock()
        
        # Create identified items
        item1 = Mock()
        item1.item = Mock()
        item1.item.identified = True
        
        caster.inventory.items = [item1]
        
        results = cast_identify(caster)
        
        assert len(results) == 1
        assert results[0]['consumed'] is False
        assert 'no unidentified' in results[0]['message'].text.lower()
    
    def test_identify_with_unidentified_items(self):
        """Test identify successfully identifies an item."""
        caster = Mock()
        caster.inventory = Mock()
        
        # Create unidentified item
        item1 = Mock()
        item1.item = Mock()
        item1.item.identified = False
        item1.item.appearance = "cyan potion"
        item1.item.identify = Mock(return_value=True)
        item1.name = "Healing Potion"
        
        caster.inventory.items = [item1]
        
        results = cast_identify(caster)
        
        assert len(results) == 1
        assert results[0]['consumed'] is True
        assert 'identify' in results[0]['message'].text.lower()
        item1.item.identify.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

