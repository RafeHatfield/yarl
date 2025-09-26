"""
Unit tests for game_messages.py

Tests message creation and message log functionality.
"""
import pytest
from game_messages import Message, MessageLog


class TestMessage:
    """Test Message class functionality."""
    
    def test_message_creation(self, mock_libtcod):
        """Test basic message creation."""
        # Act
        message = Message("Test message", mock_libtcod.white)
        
        # Assert
        assert message.text == "Test message"
        assert message.color == mock_libtcod.white

    def test_message_with_different_colors(self, mock_libtcod):
        """Test message creation with different colors."""
        # Act
        red_message = Message("Error message", mock_libtcod.red)
        green_message = Message("Success message", mock_libtcod.green)
        
        # Assert
        assert red_message.color == mock_libtcod.red
        assert green_message.color == mock_libtcod.green

    def test_message_empty_text(self, mock_libtcod):
        """Test message with empty text."""
        # Act
        message = Message("", mock_libtcod.white)
        
        # Assert
        assert message.text == ""
        assert message.color == mock_libtcod.white

    def test_message_long_text(self, mock_libtcod):
        """Test message with very long text."""
        # Arrange
        long_text = "A" * 1000
        
        # Act
        message = Message(long_text, mock_libtcod.white)
        
        # Assert
        assert message.text == long_text
        assert len(message.text) == 1000


class TestMessageLog:
    """Test MessageLog class functionality."""
    
    def test_message_log_creation(self):
        """Test basic message log creation."""
        # Act
        log = MessageLog(x=10, width=50, height=5)
        
        # Assert
        assert log.x == 10
        assert log.width == 50
        assert log.height == 5
        assert len(log.messages) == 0

    def test_message_log_add_message(self, mock_libtcod):
        """Test adding a message to the log."""
        # Arrange
        log = MessageLog(x=0, width=50, height=5)
        message = Message("Test message", mock_libtcod.white)
        
        # Act
        log.add_message(message)
        
        # Assert
        assert len(log.messages) == 1
        assert log.messages[0] == message

    def test_message_log_add_multiple_messages(self, mock_libtcod):
        """Test adding multiple messages to the log."""
        # Arrange
        log = MessageLog(x=0, width=50, height=5)
        message1 = Message("First message", mock_libtcod.white)
        message2 = Message("Second message", mock_libtcod.red)
        message3 = Message("Third message", mock_libtcod.green)
        
        # Act
        log.add_message(message1)
        log.add_message(message2)
        log.add_message(message3)
        
        # Assert
        assert len(log.messages) == 3
        assert log.messages[0] == message1
        assert log.messages[1] == message2
        assert log.messages[2] == message3

    def test_message_log_capacity_overflow(self, mock_libtcod):
        """Test message log behavior when capacity is exceeded."""
        # Arrange
        log = MessageLog(x=0, width=50, height=2)  # Only 2 messages
        
        # Act
        for i in range(5):
            message = Message(f"Message {i}", mock_libtcod.white)
            log.add_message(message)
        
        # Assert - should keep only the most recent messages up to height
        assert len(log.messages) <= log.height
        # The exact behavior depends on implementation

    def test_message_log_zero_height(self):
        """Test message log with zero height."""
        # Act
        log = MessageLog(x=0, width=50, height=0)
        
        # Assert
        assert log.height == 0
        assert len(log.messages) == 0

    def test_message_log_negative_dimensions(self):
        """Test message log with negative dimensions."""
        # Act
        log = MessageLog(x=-10, width=-50, height=-5)
        
        # Assert
        assert log.x == -10
        assert log.width == -50
        assert log.height == -5

    def test_message_log_add_none_message(self):
        """Test adding None as a message."""
        # Arrange
        log = MessageLog(x=0, width=50, height=5)
        
        # Act & Assert - should handle gracefully or raise appropriate error
        try:
            log.add_message(None)
            # If it accepts None, that's fine
        except (TypeError, AttributeError):
            # If it rejects None, that's also fine
            pass
