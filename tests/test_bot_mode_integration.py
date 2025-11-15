"""Integration test for bot mode with the game engine.

This test verifies that the bot input source integrates correctly with
the engine integration layer without hanging or crashing.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from io_layer.bot_input import BotInputSource
from io_layer.keyboard_input import KeyboardInputSource
from engine_integration import create_renderer_and_input_source
from game_states import GameStates


class TestBotModeEngineIntegration:
    """Test bot mode integration with engine systems."""
    
    def test_create_renderer_and_input_source_with_bot_mode(self):
        """Test that create_renderer_and_input_source creates BotInputSource in bot mode."""
        # Mock the consoles
        mock_console = Mock()
        colors = {'default': (255, 255, 255)}
        
        renderer, input_source = create_renderer_and_input_source(
            sidebar_console=mock_console,
            viewport_console=mock_console,
            status_console=mock_console,
            colors=colors,
            input_mode="bot"
        )
        
        assert isinstance(input_source, BotInputSource)
    
    def test_create_renderer_and_input_source_with_keyboard_mode(self):
        """Test that create_renderer_and_input_source creates KeyboardInputSource in keyboard mode."""
        mock_console = Mock()
        colors = {'default': (255, 255, 255)}
        
        renderer, input_source = create_renderer_and_input_source(
            sidebar_console=mock_console,
            viewport_console=mock_console,
            status_console=mock_console,
            colors=colors,
            input_mode="keyboard"
        )
        
        assert isinstance(input_source, KeyboardInputSource)
    
    def test_bot_input_never_blocks_game_loop(self):
        """Test that bot input throttles correctly to prevent tight loops.
        
        Note: After the throttling fix, bot.next_action() includes a small sleep
        (~16ms) when generating actions to prevent OS unresponsiveness. This test
        verifies that throttling works as expected.
        
        With action_interval=1, every call returns an action (with sleep).
        With action_interval=2, pattern is: {} (no sleep), {'wait': True} (sleep).
        """
        import time
        
        # Test with action_interval=2 to see both throttled and action-returning calls
        bot = BotInputSource(action_interval=2)
        
        # Create a mock game state
        mock_state = Mock()
        mock_state.game_state = GameStates.PLAYERS_TURN
        mock_state.current_state = GameStates.PLAYERS_TURN
        
        # First call: counter 0→1, 1 < 2, returns {} (no sleep, instant)
        start = time.time()
        action1 = bot.next_action(mock_state)
        elapsed = time.time() - start
        
        assert action1 == {}, "First call should be throttled (counter 1 < 2)"
        assert elapsed < 0.001, f"Throttled call should be instant, got {elapsed}s"
        
        # Second call: counter 1→2, 2 >= 2, returns action with sleep (~16ms)
        start = time.time()
        action2 = bot.next_action(mock_state)
        elapsed = time.time() - start
        
        assert action2 == {'wait': True}, "Second call should return action (counter 2 >= 2)"
        # Sleep should be ~16ms, allow some variance for system timing
        assert 0.015 <= elapsed <= 0.025, f"Action generation sleep should be ~16ms, got {elapsed}s"
        
        # Third call: counter 0→1 (reset), 1 < 2, returns {} (no sleep, instant)
        start = time.time()
        action3 = bot.next_action(mock_state)
        elapsed = time.time() - start
        
        assert action3 == {}, "Third call should be throttled (counter 1 < 2)"
        assert elapsed < 0.001, f"Throttled call should be instant, got {elapsed}s"
    
    def test_bot_input_vs_keyboard_input_both_return_dicts(self):
        """Test that both bot and keyboard input sources return ActionDicts."""
        mock_state = Mock()
        mock_state.game_state = GameStates.PLAYERS_TURN
        mock_state.current_state = GameStates.PLAYERS_TURN
        mock_state.camera = None
        
        # Bot input
        bot = BotInputSource()
        bot_action = bot.next_action(mock_state)
        assert isinstance(bot_action, dict)
        
        # Keyboard input (with mocked libtcod)
        with patch('io_layer.keyboard_input.libtcod') as mock_libtcod:
            mock_libtcod.EVENT_KEY_PRESS = 1
            mock_libtcod.EVENT_MOUSE = 2
            mock_libtcod.KEY_NONE = 0
            
            keyboard = KeyboardInputSource()
            keyboard.current_key = Mock()
            keyboard.current_key.vk = mock_libtcod.KEY_NONE
            keyboard.current_key.c = 0
            keyboard.current_mouse = Mock()
            keyboard.current_mouse.lbutton_pressed = False
            keyboard.current_mouse.rbutton_pressed = False
            keyboard.current_mouse.cx = -1
            keyboard.current_mouse.cy = -1
            
            with patch('io_layer.keyboard_input.handle_keys', return_value={}):
                keyboard_action = keyboard.next_action(mock_state)
                assert isinstance(keyboard_action, dict)
    
    def test_bot_mode_in_constants_config(self):
        """Test that bot_enabled config flag works correctly."""
        # Simulate the engine.py bot configuration
        constants = {
            "input_config": {
                "bot_enabled": True
            }
        }
        
        # This is how engine_integration.py uses it
        input_mode = "bot" if constants.get("input_config", {}).get("bot_enabled") else "keyboard"
        assert input_mode == "bot"
        
        # Test with bot disabled
        constants["input_config"]["bot_enabled"] = False
        input_mode = "bot" if constants.get("input_config", {}).get("bot_enabled") else "keyboard"
        assert input_mode == "keyboard"

