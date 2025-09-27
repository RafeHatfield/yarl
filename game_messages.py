"""Game messaging system.

This module handles game messages and the message log display.
Provides classes for individual messages and the scrolling message log.
"""

import textwrap


class Message:
    """A single game message with text and color.

    Attributes:
        text (str): The message text
        color (tuple): RGB color tuple for display
    """

    def __init__(self, text, color=(255, 255, 255)):
        """Initialize a Message.

        Args:
            text (str): The message text
            color (tuple, optional): RGB color tuple. Defaults to white.
        """
        self.text = text
        self.color = color

    def __eq__(self, other):
        """Compare messages based on text and color."""
        if not isinstance(other, Message):
            return False
        return self.text == other.text and self.color == other.color

    def __repr__(self):
        """String representation for debugging."""
        return f"Message('{self.text}', {self.color})"


class MessageLog:
    def __init__(self, x, width, height):
        self.messages = []
        self.x = x
        self.width = width
        self.height = height

    def add_message(self, message):
        # Split the message if necessary, among multiple lines
        new_msg_lines = textwrap.wrap(message.text, self.width)

        for line in new_msg_lines:
            # If the buffer is full, remove the first line to make room for the new one
            if len(self.messages) == self.height:
                del self.messages[0]

            # Add the new line as a Message object, with the text and the color
            self.messages.append(Message(line, message.color))
