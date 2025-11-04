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
    
    def handle_ruby_heart_pickup(self, player, entities, game_map, message_log) -> bool:
        """Handle the pickup of Aurelyn's Ruby Heart.

        This triggers the portal spawn and Zhyraxion's reaction.
        
        Args:
            player: Player entity
            entities: List of all entities
            game_map: Current game map
            message_log: Message log for output
            
        Returns:
            True if Ruby Heart was picked up and portal spawned
        """
        # Check if player has Victory component, add if not
        if not hasattr(player, 'victory') or player.victory is None:
            player.victory = Victory()
            player.victory.owner = player
        
        # Mark Ruby Heart as obtained
        player.victory.obtain_ruby_heart(player.x, player.y)

        # Check if player has already read the Crimson Ritual Codex
        # If so, unlock the knowledge now that victory component exists
        has_codex = any(item.name == "Crimson Ritual Codex" for item in player.inventory.items)
        if has_codex and not player.victory.has_knowledge('crimson_ritual_knowledge'):
            print("DEBUG: Player has codex, unlocking crimson ritual knowledge retroactively")
            player.victory.unlock_knowledge('crimson_ritual_knowledge')
            message_log.add_message(MB.success(
                "The knowledge from the Crimson Ritual Codex awakens! "
                "A new choice will be available at the final confrontation."
            ))
        
        # Display Zhyraxion's reaction (dramatic moment!)
        message_log.add_message(MB.item_effect("The Ruby Heart pulses with warmth in your hands!"))
        message_log.add_message(MB.warning("You feel its rhythm - not quite alive, not quite dead..."))
        message_log.add_message(MB.warning("\"You have it. After all these centuries...\""))
        
        # Check if portal already exists (prevent duplicate spawning)
        portal_already_exists = any(hasattr(e, 'is_portal') and e.is_portal for e in entities)
        if portal_already_exists:
            logger.info("Portal already exists, skipping duplicate spawn")
            message_log.add_message(MB.warning("A shimmering portal tears open before you!"))
            message_log.add_message(MB.info("The Entity's voice echoes from within..."))
            # Calculate direction for better UX (find existing portal)
            existing_portal = next((e for e in entities if hasattr(e, 'is_portal') and e.is_portal), None)
            if existing_portal:
                dx = existing_portal.x - player.x
                dy = existing_portal.y - player.y
                direction = ""
                if dx > 0:
                    direction = "to your right" if dy == 0 else ("to your lower right" if dy > 0 else "to your upper right")
                elif dx < 0:
                    direction = "to your left" if dy == 0 else ("to your lower left" if dy > 0 else "to your upper left")
                elif dy > 0:
                    direction = "below you"
                elif dy < 0:
                    direction = "above you"
                else:
                    direction = "at your feet"

                message_log.add_message(MB.info(f"[The portal is {direction} at ({existing_portal.x}, {existing_portal.y})]"))
            return True

        # Spawn portal adjacent to player (not on them!)
        # Try to find an open tile next to player
        portal_x, portal_y = self._find_adjacent_open_tile(player, game_map, entities)

        logger.info(f"Attempting to spawn portal adjacent to player: ({portal_x}, {portal_y})")
        portal = self.entity_factory.create_unique_item('entity_portal', portal_x, portal_y)
        
        if portal:
            logger.info(f"Portal created successfully. Portal location: ({portal.x}, {portal.y})")
            entities.append(portal)
            message_log.add_message(MB.warning("A shimmering portal tears open before you!"))
            message_log.add_message(MB.info("The Entity's voice echoes from within..."))
            # Calculate direction for better UX
            dx = portal.x - player.x
            dy = portal.y - player.y
            direction = ""
            if dx > 0:
                direction = "to your right" if dy == 0 else ("to your lower right" if dy > 0 else "to your upper right")
            elif dx < 0:
                direction = "to your left" if dy == 0 else ("to your lower left" if dy > 0 else "to your upper left")
            elif dy > 0:
                direction = "below you"
            elif dy < 0:
                direction = "above you"
            else:
                direction = "at your feet"
            
            message_log.add_message(MB.info(f"[The portal is {direction} at ({portal.x}, {portal.y})]"))
            logger.info(f"Victory portal spawned at ({portal.x}, {portal.y})")
            return True
        else:
            logger.error("Failed to spawn victory portal!")
            return False

    # ------------------------------------------------------------------
    # Backwards compatibility
    # ------------------------------------------------------------------
    def handle_amulet_pickup(self, player, entities, game_map, message_log) -> bool:
        """Legacy entry point that now delegates to :meth:`handle_ruby_heart_pickup`.

        Older test suites and save-game migrations still reference the amulet
        terminology.  Keeping this shim prevents attribute errors while the rest
        of the codebase adopts the updated Ruby Heart naming.
        """

        return self.handle_ruby_heart_pickup(player, entities, game_map, message_log)
    
    def _find_adjacent_open_tile(self, player, game_map, entities):
        """Find an open tile adjacent to the player for portal spawning.
        
        Tries tiles in order: right, down, left, up, then diagonals.
        Falls back to player's location if no open tile found.
        
        Args:
            player: Player entity
            game_map: Game map
            entities: List of all entities
            
        Returns:
            Tuple of (x, y) coordinates for portal spawn
        """
        # Directions to try (prioritize cardinal directions)
        directions = [
            (1, 0),   # Right
            (0, 1),   # Down
            (-1, 0),  # Left
            (0, -1),  # Up
            (1, 1),   # Down-right
            (-1, 1),  # Down-left
            (1, -1),  # Up-right
            (-1, -1), # Up-left
        ]
        
        for dx, dy in directions:
            x = player.x + dx
            y = player.y + dy
            
            # Check if tile is in bounds
            if 0 <= x < game_map.width and 0 <= y < game_map.height:
                # Check if tile is walkable
                if not game_map.tiles[x][y].blocked:
                    # Check if no entity blocking
                    blocking_entity = None
                    for entity in entities:
                        if entity.blocks and entity.x == x and entity.y == y:
                            blocking_entity = entity
                            break
                    
                    if not blocking_entity:
                        return (x, y)
        
        # Fallback: spawn at player's location if no open tile
        logger.warning("No adjacent open tile found, spawning portal at player location")
        return (player.x, player.y)
    
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
        
        message_log.add_message(MB.item_effect("You step through the portal..."))
        message_log.add_message(MB.warning("Reality twists around you!"))
    
    def get_entity_anxiety_dialogue(self, player) -> str:
        """Get Zhyraxion's current anxiety dialogue based on delay.
        
        Args:
            player: Player entity with victory component
            
        Returns:
            Anxiety-appropriate dialogue string
        """
        if not hasattr(player, 'victory') or not player.victory:
            return "\"Where is Aurelyn's heart?!\""
        
        anxiety = player.victory.entity_anxiety_level
        
        anxiety_lines = {
            0: "\"You have it. Now... bring it to me.\"",
            1: "\"What's taking so long? The heart. Bring it here.\"",
            2: "\"Where ARE you? I've waited centuries! Don't make me wait longer!\"",
            3: "\"PLEASE! I need— I MUST have that heart! Come to me! NOW!\""
        }
        
        return anxiety_lines.get(anxiety, anxiety_lines[0])
    
    def advance_anxiety(self, player):
        """Advance Zhyraxion's anxiety level if player delays with Ruby Heart.
        
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

