"""Tests for the invisibility system including scrolls, status effects, and rendering."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from entity import Entity
from components.fighter import Fighter
from components.status_effects import InvisibilityEffect, StatusEffectManager
from components.faction import Faction
from item_functions import cast_invisibility
from game_messages import Message
from config.entity_registry import load_entity_config
from config.entity_factory import EntityFactory


class TestInvisibilityEffect:
    """Test the InvisibilityEffect status effect."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True, 
                           render_order=4, fighter=Fighter(hp=30, defense=2, power=5),
                           faction=Faction.PLAYER)
    
    def test_invisibility_effect_creation(self):
        """Test creating an invisibility effect."""
        effect = InvisibilityEffect(duration=10, owner=self.player)
        
        assert effect.name == "invisibility"
        assert effect.duration == 10
        assert effect.owner == self.player
        assert not effect.is_active
    
    def test_invisibility_effect_apply(self):
        """Test applying invisibility effect."""
        effect = InvisibilityEffect(duration=10, owner=self.player)
        
        results = effect.apply()
        
        assert effect.is_active
        assert self.player.invisible
        assert len(results) == 1
        assert "becomes invisible" in results[0]["message"].text
    
    def test_invisibility_effect_remove(self):
        """Test removing invisibility effect."""
        effect = InvisibilityEffect(duration=10, owner=self.player)
        effect.apply()  # Apply first
        
        results = effect.remove()
        
        assert not effect.is_active
        assert not self.player.invisible
        assert len(results) == 1
        assert "no longer invisible" in results[0]["message"].text
    
    def test_invisibility_effect_break(self):
        """Test breaking invisibility effect."""
        effect = InvisibilityEffect(duration=10, owner=self.player)
        effect.apply()  # Apply first
        
        results = effect.break_invisibility()
        
        assert not effect.is_active
        assert not self.player.invisible
        assert effect.duration == 0  # Should be set to 0
        assert len(results) == 1
        assert "no longer invisible" in results[0]["message"].text
    
    def test_invisibility_effect_turn_processing(self):
        """Test invisibility effect duration countdown."""
        effect = InvisibilityEffect(duration=3, owner=self.player)
        effect.apply()
        
        # Process turn end - should reduce duration
        results = effect.process_turn_end()
        assert effect.duration == 2
        assert len(results) == 0  # No removal yet
        
        # Process another turn
        results = effect.process_turn_end()
        assert effect.duration == 1
        assert len(results) == 0  # No removal yet
        
        # Final turn - should expire but not auto-remove (manager handles removal)
        results = effect.process_turn_end()
        assert effect.duration == 0
        assert effect.is_active  # Still active until manager removes it
        assert self.player.invisible  # Still invisible until manager removes it
        assert len(results) == 0  # No removal message from effect itself


class TestStatusEffectManager:
    """Test the StatusEffectManager component."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True, 
                           render_order=4, fighter=Fighter(hp=30, defense=2, power=5),
                           faction=Faction.PLAYER)
        self.manager = StatusEffectManager(self.player)
    
    def test_add_invisibility_effect(self):
        """Test adding invisibility effect to manager."""
        effect = InvisibilityEffect(duration=10, owner=self.player)
        
        results = self.manager.add_effect(effect)
        
        assert self.manager.has_effect("invisibility")
        assert self.manager.get_effect("invisibility") == effect
        assert self.player.invisible
        assert len(results) == 1
    
    def test_replace_existing_effect(self):
        """Test replacing an existing effect with a new one."""
        effect1 = InvisibilityEffect(duration=5, owner=self.player)
        effect2 = InvisibilityEffect(duration=10, owner=self.player)
        
        self.manager.add_effect(effect1)
        results = self.manager.add_effect(effect2)
        
        assert self.manager.get_effect("invisibility") == effect2
        assert self.manager.get_effect("invisibility").duration == 10
        assert "refreshed" in results[0]["message"].text
    
    def test_remove_effect(self):
        """Test removing an effect by name."""
        effect = InvisibilityEffect(duration=10, owner=self.player)
        self.manager.add_effect(effect)
        
        results = self.manager.remove_effect("invisibility")
        
        assert not self.manager.has_effect("invisibility")
        assert not self.player.invisible
        assert len(results) == 1
    
    def test_process_turn_end_removes_expired_effects(self):
        """Test that expired effects are removed during turn processing."""
        effect = InvisibilityEffect(duration=1, owner=self.player)
        self.manager.add_effect(effect)
        
        # Process turn end - should remove expired effect
        results = self.manager.process_turn_end()
        
        assert not self.manager.has_effect("invisibility")
        assert not self.player.invisible
        assert len(results) == 1  # Removal message


class TestInvisibilityScroll:
    """Test the invisibility scroll item function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Register spells for spell system
        from spells import get_spell_registry
        from spells.spell_catalog import register_all_spells
        get_spell_registry().clear()
        register_all_spells()
        
        self.player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True, 
                           render_order=4, fighter=Fighter(hp=30, defense=2, power=5),
                           faction=Faction.PLAYER)
    
    def test_cast_invisibility_success(self):
        """Test successfully casting invisibility."""
        results = cast_invisibility(self.player, duration=10)
        
        assert len(results) == 2  # Message + consumed
        # New spell system returns message and consumed separately
        assert "message" in results[0]
        assert "becomes invisible" in results[0]["message"].text
        assert results[1]["consumed"] is True
        assert self.player.invisible
    
    def test_cast_invisibility_already_invisible(self):
        """Test casting invisibility when already invisible."""
        # Make player invisible first
        self.player.invisible = True
        
        results = cast_invisibility(self.player, duration=10)
        
        # Spell system returns separate message and consumed results
        assert len(results) >= 1
        consumed_result = next((r for r in results if "consumed" in r), None)
        assert consumed_result is not None
        assert consumed_result["consumed"] is False
        message_result = next((r for r in results if "message" in r), None)
        assert message_result is not None
        assert "already invisible" in message_result["message"].text
    
    def test_cast_invisibility_default_duration(self):
        """Test casting invisibility with default duration."""
        results = cast_invisibility(self.player)
        
        # Check that the effect was applied with default duration
        status_manager = self.player.get_status_effect_manager()
        effect = status_manager.get_effect("invisibility")
        assert effect.duration == 10  # Default duration


class TestInvisibilityScrollCreation:
    """Test creating invisibility scrolls through the entity factory."""
    
    def setup_method(self):
        """Set up test fixtures."""
        load_entity_config()  # Load YAML definitions
        self.factory = EntityFactory()
    
    def test_create_invisibility_scroll(self):
        """Test creating an invisibility scroll."""
        scroll = self.factory.create_spell_item("invisibility_scroll", 0, 0)
        
        assert scroll is not None
        assert scroll.name == "Invisibility Scroll"
        assert scroll.item is not None
        assert scroll.item.use_function == cast_invisibility
        assert 'duration' in scroll.item.function_kwargs
        assert scroll.item.function_kwargs['duration'] == 10  # From YAML config


class TestInvisibilityRendering:
    """Test invisibility rendering effects."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True, 
                           render_order=4, fighter=Fighter(hp=30, defense=2, power=5),
                           faction=Faction.PLAYER)
    
    @patch('render_functions.libtcod')
    def test_invisible_player_rendering(self, mock_libtcod):
        """Test that invisible players are rendered differently."""
        from render_functions import draw_entity
        
        # Make player invisible
        self.player.invisible = True
        
        # Mock console and other required objects
        mock_con = Mock()
        mock_fov_map = Mock()
        mock_game_map = Mock()
        
        # Mock FOV check to return True
        with patch('render_functions.map_is_in_fov', return_value=True):
            draw_entity(mock_con, self.player, mock_fov_map, mock_game_map)
        
        # Verify that the rendering was called with modified color and character
        mock_libtcod.console_set_default_foreground.assert_called_once()
        mock_libtcod.console_put_char.assert_called_once()
        
        # Check that the color was darkened (should be much darker than original)
        call_args = mock_libtcod.console_set_default_foreground.call_args[0]
        darkened_color = call_args[1]
        assert darkened_color[0] < 100  # Much darker than original (255)
        assert darkened_color[1] < 100  # Much darker than original (255)
        assert darkened_color[2] < 100  # Much darker than original (255)
        
        # Check that the character was changed to '?'
        char_call_args = mock_libtcod.console_put_char.call_args[0]
        assert char_call_args[3] == '?'  # Should be '?' for invisible player
    
    @patch('render_functions.libtcod')
    def test_visible_player_rendering(self, mock_libtcod):
        """Test that visible players are rendered normally."""
        from render_functions import draw_entity
        
        # Player is visible (default)
        assert not hasattr(self.player, 'invisible') or not self.player.invisible
        
        # Mock console and other required objects
        mock_con = Mock()
        mock_fov_map = Mock()
        mock_game_map = Mock()
        
        # Mock FOV check to return True
        with patch('render_functions.map_is_in_fov', return_value=True):
            draw_entity(mock_con, self.player, mock_fov_map, mock_game_map)
        
        # Verify normal rendering
        mock_libtcod.console_set_default_foreground.assert_called_once()
        mock_libtcod.console_put_char.assert_called_once()
        
        # Check that the original color was used
        call_args = mock_libtcod.console_set_default_foreground.call_args[0]
        color = call_args[1]
        assert color == (255, 255, 255)  # Original color
        
        # Check that the original character was used
        char_call_args = mock_libtcod.console_put_char.call_args[0]
        assert char_call_args[3] == '@'  # Original character


class TestInvisibilityGameIntegration:
    """Test invisibility integration with game systems."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True, 
                           render_order=4, fighter=Fighter(hp=30, defense=2, power=5),
                           faction=Faction.PLAYER)
        
        # Mock game state manager
        self.mock_state_manager = Mock()
        self.mock_state_manager.state.player = self.player
        self.mock_state_manager.state.message_log = Mock()
    
    def test_invisibility_breaks_on_attack(self):
        """Test that invisibility breaks when the player attacks."""
        from game_actions import ActionProcessor
        
        # Make player invisible
        effect = InvisibilityEffect(duration=10, owner=self.player)
        self.player.add_status_effect(effect)
        assert self.player.invisible
        
        # Create action processor
        processor = ActionProcessor(self.mock_state_manager)
        
        # Create a target to attack
        target = Entity(1, 0, 'o', (255, 0, 0), 'Orc', blocks=True, 
                       render_order=4, fighter=Fighter(hp=10, defense=0, power=3))
        
        # Mock the break invisibility method
        with patch.object(processor, '_break_invisibility') as mock_break:
            processor._handle_combat(self.player, target)
            
            # Verify that break invisibility was called
            mock_break.assert_called_once_with(self.player)
    
    def test_status_effects_processed_on_turn_end(self):
        """Test that status effects are processed at the end of player turns."""
        from game_actions import ActionProcessor
        
        # Add invisibility effect
        effect = InvisibilityEffect(duration=2, owner=self.player)
        self.player.add_status_effect(effect)
        
        # Create action processor
        processor = ActionProcessor(self.mock_state_manager)
        
        # Process status effects
        processor._process_player_status_effects()
        
        # Verify that the effect duration was reduced
        status_manager = self.player.get_status_effect_manager()
        remaining_effect = status_manager.get_effect("invisibility")
        assert remaining_effect.duration == 1  # Should be reduced by 1
