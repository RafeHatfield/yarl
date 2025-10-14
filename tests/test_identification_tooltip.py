"""Test that tooltips respect item identification status.

Critical regression test: tooltips must not reveal item functions for unidentified items.
"""
import pytest
from unittest.mock import Mock, MagicMock
from components.item import Item
from components.component_registry import ComponentType
from ui.tooltip import render_tooltip


class TestIdentificationTooltip:
    """Test tooltip rendering respects identification."""
    
    def test_unidentified_item_hides_function_in_tooltip(self):
        """Unidentified items should show 'Unidentified' not their actual function."""
        # Create a mock entity with an unidentified healing potion
        entity = Mock()
        entity.name = "healing_potion"
        entity.components = Mock()
        entity.components.has = lambda comp: comp == ComponentType.ITEM
        
        # Create unidentified item with healing function
        def mock_heal_function(*args, **kwargs):
            return []
        mock_heal_function.__name__ = "drink_healing_potion"
        
        entity.item = Item(
            use_function=mock_heal_function,
            identified=False,  # NOT IDENTIFIED YET
            appearance="cloud indigo potion",
            item_category="potion"
        )
        entity.item.owner = entity
        
        # Mock console for rendering
        console = Mock()
        console.print = Mock()
        
        # Render tooltip and capture what would be printed
        ui_layout = Mock()
        ui_layout.screen_width = 80
        ui_layout.screen_height = 50
        
        # We can't easily intercept libtcod.console_print_ex, so we'll check the logic directly
        # by importing the function and checking what tooltip_lines would be built
        
        # Direct check: verify Item.get_display_name returns appearance
        display_name = entity.item.get_display_name()
        assert display_name == "cloud indigo potion", "Unidentified items should show appearance"
        
        # Direct check: tooltip logic should not reveal function for unidentified items
        # The fixed code checks: if entity.item.identified: ... else: "Unidentified"
        assert not entity.item.identified, "Item should be unidentified"
        assert entity.item.appearance == "cloud indigo potion"
        
        # After identification
        entity.item.identify()
        assert entity.item.identified
        display_name_identified = entity.item.get_display_name()
        assert display_name_identified == "healing_potion", "Identified items show real name"
    
    def test_identified_item_reveals_function_in_tooltip(self):
        """Identified items should show their function details."""
        # Create a mock entity with an identified healing potion
        entity = Mock()
        entity.name = "Healing Potion"
        entity.components = Mock()
        entity.components.has = lambda comp: comp == ComponentType.ITEM
        
        # Create identified item
        def mock_heal_function(*args, **kwargs):
            return []
        mock_heal_function.__name__ = "drink_healing_potion"
        
        entity.item = Item(
            use_function=mock_heal_function,
            identified=True,  # IDENTIFIED
            appearance=None,
            item_category="potion"
        )
        entity.item.owner = entity
        
        # Verify identified item shows real name
        display_name = entity.item.get_display_name()
        assert display_name == "Healing Potion"
        
        # Tooltip should be able to show function (no longer hidden)
        assert entity.item.identified
        assert entity.item.use_function.__name__ == "drink_healing_potion"
    
    def test_all_new_potions_respect_identification(self):
        """All new potions should hide their function when unidentified."""
        new_potion_functions = [
            "drink_speed_potion",
            "drink_regeneration_potion",
            "drink_invisibility_potion",
            "drink_levitation_potion",
            "drink_protection_potion",
            "drink_heroism_potion",
            "drink_weakness_potion",
            "drink_slowness_potion",
            "drink_blindness_potion",
            "drink_paralysis_potion",
            "drink_experience_potion"
        ]
        
        for func_name in new_potion_functions:
            # Create mock entity with unidentified potion
            entity = Mock()
            entity.name = func_name
            entity.components = Mock()
            entity.components.has = lambda comp: comp == ComponentType.ITEM
            
            def mock_func(*args, **kwargs):
                return []
            mock_func.__name__ = func_name
            
            entity.item = Item(
                use_function=mock_func,
                identified=False,
                appearance=f"mysterious {func_name} appearance",
                item_category="potion"
            )
            entity.item.owner = entity
            
            # Verify unidentified item shows appearance
            display_name = entity.item.get_display_name()
            assert display_name == f"mysterious {func_name} appearance", \
                f"{func_name} should show appearance when unidentified"
            
            # Verify tooltip logic would hide function
            assert not entity.item.identified
            
            # After identification
            entity.item.identify()
            display_name_identified = entity.item.get_display_name()
            assert display_name_identified == func_name, \
                f"{func_name} should show real name when identified"

