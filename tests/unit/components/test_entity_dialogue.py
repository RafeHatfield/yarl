"""
Tests for Entity Dialogue System (Phase 2)

Verifies that Entity dialogue loads correctly and triggers at appropriate dungeon levels.
"""

import pytest
from config.entity_dialogue_loader import EntityDialogueLoader, get_entity_dialogue_loader, reset_entity_dialogue


class TestEntityDialogueLoader:
    """Tests for EntityDialogueLoader class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.loader = EntityDialogueLoader()
        
    def test_loader_initialization(self):
        """Test that dialogue loader initializes correctly."""
        assert self.loader is not None
        assert len(self.loader.depth_dialogue) > 0
        assert self.loader.config is not None
        
    def test_dialogue_loaded_for_key_levels(self):
        """Test that dialogue exists for key story levels."""
        key_levels = [1, 5, 10, 15, 20, 25]
        
        for level in key_levels:
            dialogue = self.loader.get_dialogue_for_level(level, force=True)
            assert dialogue is not None, f"Expected dialogue for level {level}"
            assert dialogue.message, f"Dialogue for level {level} has no message"
            assert dialogue.color, f"Dialogue for level {level} has no color"
            
    def test_no_dialogue_for_unlisted_levels(self):
        """Test that no dialogue triggers for levels without entries."""
        unlisted_levels = [2, 3, 4, 6, 7, 8, 9, 11, 13, 14, 16, 17, 19, 21, 23, 24]
        
        for level in unlisted_levels:
            dialogue = self.loader.get_dialogue_for_level(level, force=True)
            assert dialogue is None, f"Unexpected dialogue for level {level}"
            
    def test_dialogue_progression_tone(self):
        """Test that dialogue tone progresses (color changes)."""
        # Early levels should be light_purple (curious)
        early = self.loader.get_dialogue_for_level(1, force=True)
        assert early.color == 'light_purple'
        
        # Mid levels should be purple/violet (anxious)
        mid = self.loader.get_dialogue_for_level(15, force=True)
        assert mid.color in ['purple', 'violet']
        
        # Late levels should be red (desperate/enraged)
        late = self.loader.get_dialogue_for_level(20, force=True)
        assert late.color in ['red', 'light_red']
        
    def test_cooldown_prevents_spam(self):
        """Test that cooldown prevents same level from triggering repeatedly."""
        level = 5
        
        # First trigger should work
        first = self.loader.get_dialogue_for_level(level, force=False)
        assert first is not None
        
        # Second trigger immediately after should be blocked
        second = self.loader.get_dialogue_for_level(level, force=False)
        assert second is None, "Cooldown should prevent immediate re-trigger"
        
        # Force flag should bypass cooldown
        forced = self.loader.get_dialogue_for_level(level, force=True)
        assert forced is not None
        
    def test_cooldown_resets_after_turns(self):
        """Test that cooldown expires after enough turns."""
        level = 5
        cooldown = self.loader.config.get('cooldown_turns', 50)
        
        # Trigger dialogue
        first = self.loader.get_dialogue_for_level(level, force=False)
        assert first is not None
        
        # Blocked immediately
        blocked = self.loader.get_dialogue_for_level(level, force=False)
        assert blocked is None
        
        # Advance turns beyond cooldown
        for _ in range(cooldown + 1):
            self.loader.increment_turn_counter()
            
        # Should work again
        after_cooldown = self.loader.get_dialogue_for_level(level, force=False)
        assert after_cooldown is not None
        
    def test_reset_clears_state(self):
        """Test that reset() clears dialogue state."""
        # Trigger some dialogue
        self.loader.get_dialogue_for_level(5, force=False)
        assert self.loader.last_triggered_level == 5
        assert self.loader.turns_since_last == 0
        
        # Advance turns
        self.loader.increment_turn_counter()
        assert self.loader.turns_since_last > 0
        
        # Reset
        self.loader.reset()
        assert self.loader.last_triggered_level is None
        assert self.loader.turns_since_last == 0
        
    def test_config_values(self):
        """Test that config values are loaded correctly."""
        assert self.loader.should_show_in_log() == True
        assert self.loader.should_interrupt() == False
        assert self.loader.config.get('cooldown_turns') == 50
        
    def test_all_dialogue_has_required_fields(self):
        """Test that all dialogue entries have required fields."""
        for level, dialogue in self.loader.depth_dialogue.items():
            assert dialogue.level == level
            assert dialogue.message is not None and len(dialogue.message) > 0
            assert dialogue.color is not None
            assert dialogue.style is not None


class TestEntityDialogueSingleton:
    """Tests for singleton pattern."""
    
    def test_singleton_returns_same_instance(self):
        """Test that get_entity_dialogue_loader returns singleton."""
        loader1 = get_entity_dialogue_loader()
        loader2 = get_entity_dialogue_loader()
        
        assert loader1 is loader2
        
    def test_reset_entity_dialogue_works(self):
        """Test that global reset function works."""
        loader = get_entity_dialogue_loader()
        
        # Trigger dialogue
        loader.get_dialogue_for_level(5, force=False)
        assert loader.last_triggered_level is not None
        
        # Reset globally
        reset_entity_dialogue()
        
        # Should be reset
        assert loader.last_triggered_level is None


class TestEntityDialogueContent:
    """Tests for dialogue content quality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.loader = EntityDialogueLoader()
        
    def test_level_1_sets_tone(self):
        """Test that level 1 dialogue introduces the Entity."""
        dialogue = self.loader.get_dialogue_for_level(1, force=True)
        assert dialogue is not None
        # Should be subtle/mysterious
        message_lower = dialogue.message.lower()
        assert 'whisper' in message_lower or 'deeper' in message_lower
        
    def test_level_25_is_desperate(self):
        """Test that level 25 dialogue shows desperation."""
        dialogue = self.loader.get_dialogue_for_level(25, force=True)
        assert dialogue is not None
        # Should mention amulet and freedom
        message_lower = dialogue.message.lower()
        assert 'amulet' in message_lower
        assert 'free' in message_lower or 'take' in message_lower
        
    def test_progression_shows_increasing_emotion(self):
        """Test that dialogue becomes more emotional over time."""
        level_5 = self.loader.get_dialogue_for_level(5, force=True)
        level_20 = self.loader.get_dialogue_for_level(20, force=True)
        
        # Level 20 should have more capitals, exclamation marks
        assert level_20.message.count('!') >= level_5.message.count('!')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
