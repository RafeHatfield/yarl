"""Signpost Message Registry - Manages signpost messages from YAML configuration.

This module loads and provides access to signpost messages from the configuration file.
Messages can be filtered by type and dungeon depth for contextual signposts.
"""

import os
import logging
import random
from typing import Dict, List, Optional
from dataclasses import dataclass

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class SignpostMessage:
    """Represents a signpost message with optional depth constraints."""
    text: str
    min_depth: Optional[int] = None
    max_depth: Optional[int] = None
    
    def is_valid_for_depth(self, depth: int) -> bool:
        """Check if this message is valid for the given dungeon depth.
        
        Args:
            depth: Current dungeon level
            
        Returns:
            True if message can appear at this depth
        """
        if self.min_depth is not None and depth < self.min_depth:
            return False
        if self.max_depth is not None and depth > self.max_depth:
            return False
        return True


class SignpostMessageRegistry:
    """Registry for managing signpost messages from YAML configuration."""
    
    def __init__(self):
        """Initialize the registry."""
        self.messages: Dict[str, List[SignpostMessage]] = {
            'lore': [],
            'warning': [],
            'humor': [],
            'hint': [],
            'directional': []
        }
        self.version: Optional[str] = None
        self._loaded = False
    
    def load_from_file(self, config_path: Optional[str] = None) -> None:
        """Load signpost messages from YAML configuration file.
        
        Args:
            config_path: Path to signpost_messages.yaml. If None, uses default location.
        """
        if not YAML_AVAILABLE:
            logger.warning("YAML support not available. Using fallback messages.")
            self._load_fallback_messages()
            return
        
        if config_path is None:
            config_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(config_dir, 'signpost_messages.yaml')
        
        if not os.path.exists(config_path):
            logger.warning(f"Signpost messages file not found at {config_path}. Using fallback messages.")
            self._load_fallback_messages()
            return
        
        try:
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data:
                logger.warning("Empty signpost messages file. Using fallback messages.")
                self._load_fallback_messages()
                return
            
            self.version = data.get('version', 'unknown')
            
            # Load messages by type
            messages_data = data.get('messages', {})
            for message_type in self.messages.keys():
                type_messages = messages_data.get(message_type, [])
                for msg_data in type_messages:
                    if isinstance(msg_data, dict):
                        message = SignpostMessage(
                            text=msg_data.get('text', ''),
                            min_depth=msg_data.get('min_depth'),
                            max_depth=msg_data.get('max_depth')
                        )
                        self.messages[message_type].append(message)
                    elif isinstance(msg_data, str):
                        # Simple string format (no depth constraints)
                        message = SignpostMessage(text=msg_data)
                        self.messages[message_type].append(message)
            
            self._loaded = True
            logger.info(
                f"Loaded signpost messages (version {self.version}): "
                f"lore={len(self.messages['lore'])}, "
                f"warning={len(self.messages['warning'])}, "
                f"humor={len(self.messages['humor'])}, "
                f"hint={len(self.messages['hint'])}, "
                f"directional={len(self.messages['directional'])}"
            )
            
        except Exception as e:
            logger.error(f"Error loading signpost messages from {config_path}: {e}")
            self._load_fallback_messages()
    
    def _load_fallback_messages(self) -> None:
        """Load hardcoded fallback messages if YAML loading fails."""
        self.messages = {
            'lore': [
                SignpostMessage("These catacombs were once a sacred burial ground..."),
                SignpostMessage("Many have sought the Amulet. Few have returned."),
                SignpostMessage("Ancient runes mark this place as cursed ground."),
            ],
            'warning': [
                SignpostMessage("Beware: Dangerous creatures ahead!"),
                SignpostMessage("Warning: The path beyond is treacherous."),
                SignpostMessage("Turn back now, or face certain doom!"),
            ],
            'humor': [
                SignpostMessage("Free treasure! (Just kidding. There's a troll.)"),
                SignpostMessage("Achievement unlocked: Reading Signs"),
                SignpostMessage("Welcome to the dungeon! Please die quietly."),
            ],
            'hint': [
                SignpostMessage("Check the walls for hidden passages..."),
                SignpostMessage("Not all chests are what they seem."),
                SignpostMessage("Some secrets reveal themselves to the patient."),
            ],
            'directional': [
                SignpostMessage("Stairs down this way →"),
                SignpostMessage("Exit: Probably not this way"),
                SignpostMessage("Boss Room: Straight ahead (Good luck!)"),
            ]
        }
        self._loaded = True
        logger.info("Loaded fallback signpost messages")
    
    def get_random_message(self, sign_type: str, depth: int = 1) -> str:
        """Get a random message for the specified sign type and depth.
        
        Args:
            sign_type: Type of sign ('lore', 'warning', 'humor', 'hint', 'directional')
            depth: Current dungeon level (for depth-specific messages)
            
        Returns:
            Random message text appropriate for the sign type and depth
        """
        if not self._loaded:
            self.load_from_file()
        
        message_pool = self.messages.get(sign_type, self.messages['lore'])
        
        if not message_pool:
            return f"[Error: No messages for type '{sign_type}']"
        
        # Filter messages by depth
        valid_messages = [
            msg for msg in message_pool 
            if msg.is_valid_for_depth(depth)
        ]
        
        # If no messages valid for this depth, use all messages (fallback)
        if not valid_messages:
            valid_messages = message_pool
        
        selected_message = random.choice(valid_messages)
        return selected_message.text
    
    def get_all_messages_for_type(self, sign_type: str) -> List[str]:
        """Get all messages for a specific sign type (ignoring depth).
        
        Args:
            sign_type: Type of sign to get messages for
            
        Returns:
            List of all message texts for that type
        """
        if not self._loaded:
            self.load_from_file()
        
        message_pool = self.messages.get(sign_type, [])
        return [msg.text for msg in message_pool]


# Global registry instance
_signpost_message_registry = None


def get_signpost_message_registry() -> SignpostMessageRegistry:
    """Get the global signpost message registry instance.
    
    Returns:
        SignpostMessageRegistry singleton instance
    """
    global _signpost_message_registry
    if _signpost_message_registry is None:
        _signpost_message_registry = SignpostMessageRegistry()
        _signpost_message_registry.load_from_file()
    return _signpost_message_registry

