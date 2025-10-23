"""Victory manager for handling victory condition triggers and progression.

This module manages the victory sequence from amulet pickup through
final confrontation to game ending.
"""

from typing import Optional, Dict, Any
from game_states import GameStates
from components.victory import Victory
from config.entity_factory import get_entity_factory
from message_builder import MessageBuilder as MB
import logging

logger = logging.getLogger(__name__)


class VictoryManager:
    """Manages victory condition progression and state transitions."""
    
    def __init__(self):
        """Initialize victory manager."""
        self.entity_factory = get_entity_factory()
    
    def handle_amulet_pickup(self, player, entities, game_map, message_log) -> bool:
        """Handle the pickup of the Amulet of Yendor.
        
        This triggers the portal spawn and Entity dialogue.
        
        Args:
            player: Player entity
            entities: List of all entities
            game_map: Current game map
            message_log: Message log for output
            
        Returns:
            True if amulet was picked up and portal spawned
        """
        # Check if player has Victory component, add if not
        if not hasattr(player, 'victory') or player.victory is None:
            player.victory = Victory()
            player.victory.owner = player
        
        # Mark amulet as obtained
        player.victory.obtain_amulet(player.x, player.y)
        
        # Display Entity's reaction (dramatic moment!)
        message_log.add_message(MB.critical("The Amulet pulses with power in your hands!"))
        message_log.add_message(MB.entity("\"AT LAST! You've done it!\""))
        message_log.add_message(MB.entity("\"Now... bring it to me. QUICKLY.\""))
        
        # Spawn portal at player's current location
        portal = self.entity_factory.create_unique_item('entity_portal', player.x, player.y)
        
        if portal:
            entities.append(portal)
            message_log.add_message(MB.warning("A shimmering portal tears open before you!"))
            message_log.add_message(MB.info("The Entity's voice echoes from within..."))
            logger.info(f"Victory portal spawned at ({player.x}, {player.y})")
            return True
        else:
            logger.error("Failed to spawn victory portal!")
            return False
    
    def check_portal_entry(self, player, entities) -> bool:
        """Check if player is standing on the victory portal.
        
        Args:
            player: Player entity
            entities: List of all entities
            
        Returns:
            True if player is on portal and can enter
        """
        for entity in entities:
            if hasattr(entity, 'is_portal') and entity.is_portal:
                if entity.x == player.x and entity.y == player.y:
                    return True
        return False
    
    def enter_portal(self, player, message_log):
        """Handle player entering the Entity's portal.
        
        Args:
            player: Player entity
            message_log: Message log for output
        """
        if hasattr(player, 'victory') and player.victory:
            player.victory.start_confrontation()
        
        message_log.add_message(MB.critical("You step through the portal..."))
        message_log.add_message(MB.warning("Reality twists around you!"))
    
    def get_entity_anxiety_dialogue(self, player) -> str:
        """Get Entity's current anxiety dialogue based on delay.
        
        Args:
            player: Player entity with victory component
            
        Returns:
            Anxiety-appropriate dialogue string
        """
        if not hasattr(player, 'victory') or not player.victory:
            return "\"Where is my Amulet?!\""
        
        anxiety = player.victory.entity_anxiety_level
        
        anxiety_lines = {
            0: "\"Excellent. Now, let's conclude our arrangement.\"",
            1: "\"What took you so long? No matter. Hand it over.\"",
            2: "\"Where have you BEEN? I've been waiting! The Amulet. NOW.\"",
            3: "\"FINALLY! Do you have ANY idea how long— Never mind. Give. It. To. Me.\""
        }
        
        return anxiety_lines.get(anxiety, anxiety_lines[0])
    
    def advance_anxiety(self, player):
        """Advance Entity's anxiety level if player delays with amulet.
        
        Args:
            player: Player entity with victory component
        """
        if hasattr(player, 'victory') and player.victory:
            player.victory.advance_turn()
    
    def get_player_stats_for_ending(self, player, game_map) -> Dict[str, Any]:
        """Gather player statistics for ending screen.
        
        Args:
            player: Player entity
            game_map: Current game map
            
        Returns:
            Dictionary of player statistics
        """
        stats = {
            'deaths': 0,  # TODO: Track this in player component
            'turns': 0,   # TODO: Track this in game state
            'deepest_level': game_map.dungeon_level if game_map else 0,
            'final_level': game_map.dungeon_level if game_map else 0,
            'kills': 0    # TODO: Track this in player component
        }
        
        # Try to get actual stats if they exist
        if hasattr(player, 'stats'):
            stats.update(player.stats)
        
        return stats


# Global instance
_victory_manager = None


def get_victory_manager() -> VictoryManager:
    """Get the global victory manager instance.
    
    Returns:
        VictoryManager instance
    """
    global _victory_manager
    if _victory_manager is None:
        _victory_manager = VictoryManager()
    return _victory_manager

