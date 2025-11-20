"""Auto-exploration component for systematic dungeon discovery.

This module provides automated dungeon exploration functionality, allowing
the player to efficiently map unexplored areas with a single command. It
serves as a foundation for future auto-play features.

Architecture:
- AutoExplore: Component for managing automated exploration state
- Uses Dijkstra pathfinding to find optimal exploration paths
- Room-by-room exploration (finishes current room before moving to next)
- Avoids ground hazards (treats them as impassable)
- Stops on threats (monsters, items, traps, damage, etc.)

Design Decisions:
- One tile per turn (animated, not instant) for player control
- Extensible for future auto-play (auto-combat, auto-loot)
- Treats hazards as walls to ensure safe exploration
- Clear stop messages so player knows why exploration halted
"""

import logging
import random
from typing import List, Tuple, Optional, Set, TYPE_CHECKING
from collections import deque
import heapq

from map_objects.rectangle import Rect

if TYPE_CHECKING:
    from map_objects.game_map import GameMap

logger = logging.getLogger(__name__)


# Pithy adventure quotes for starting auto-explore
ADVENTURE_QUOTES = [
    "Into the unknown!",
    "Adventure awaits!",
    "Fortune favors the bold!",
    "Let's see what's out there...",
    "Time to map this place out.",
    "Onward to glory!",
    "No stone left unturned!",
    "The dungeon calls...",
    "Let's find some treasure!",
    "Exploring the unexplored!",
    "Into the depths we go!",
    "What secrets await?",
    "Boldly pressing forward!",
    "The map won't draw itself!",
    "Adventure is out there!",
    "Mapping the mysteries!",
    "Seeking the unseen!",
    "Charting new territory!",
]


class AutoExplore:
    """Component for automated dungeon exploration.
    
    Manages systematic exploration of the dungeon using intelligent pathfinding.
    Explores room-by-room, avoiding hazards, and stops when threats are detected.
    Designed to be extensible for future auto-play features (combat, looting).
    
    Attributes:
        owner (Entity): The player entity that owns this component
        active (bool): Whether auto-explore is currently running
        current_path (List[Tuple[int, int]]): Current path being followed
        current_room (Optional[Rect]): Room currently being explored
        stop_reason (Optional[str]): Human-readable reason for stopping
        last_hp (int): Player HP at last turn check (for damage detection)
        target_tile (Optional[Tuple[int, int]]): Current exploration target
    
    Example:
        >>> auto_explore = AutoExplore()
        >>> auto_explore.owner = player
        >>> quote = auto_explore.start(game_map, entities)
        >>> print(quote)  # "Into the unknown!"
        >>> 
        >>> # Each turn:
        >>> action = auto_explore.get_next_action(game_map, entities, fov_map)
        >>> if action is None:
        >>>     print(f"Stopped: {auto_explore.stop_reason}")
    """
    
    def __init__(self):
        """Initialize the auto-explore component."""
        self.owner: Optional['Entity'] = None
        self.active: bool = False
        self.current_path: List[Tuple[int, int]] = []
        self.current_room: Optional[Rect] = None
        self.stop_reason: Optional[str] = None
        self.last_hp: int = 0
        self.target_tile: Optional[Tuple[int, int]] = None
        self.known_items: Set[int] = set()  # IDs of items visible when exploration started
        self.known_monsters: Set[int] = set()  # IDs of monsters visible when exploration started
        self.explored_tiles_at_start: Set[Tuple[int, int]] = set()  # Tiles explored before auto-explore started
        self.known_stairs: Set[Tuple[int, int]] = set()  # Positions of stairs we've already discovered
    
    def start(self, game_map: 'GameMap', entities: List['Entity'], fov_map=None) -> str:
        """Begin auto-exploring the dungeon.
        
        Initializes exploration state and returns a random adventure quote
        for the player.
        
        Args:
            game_map: Current dungeon level
            entities: All entities on the map
            fov_map: Field-of-view map (optional, for tracking visible items)
            
        Returns:
            str: Random pithy adventure quote
        """
        if not self.owner:
            logger.error("AutoExplore component has no owner")
            return "Error: No owner"
        
        player_pos = (self.owner.x, self.owner.y) if self.owner else None
        was_active = self.active
        
        # CRITICAL FIX: Check if there are any unexplored tiles BEFORE activating
        # This prevents the bot from getting stuck in a restart loop when the map is fully explored
        # Wrap in try/except to handle mock objects in tests gracefully
        try:
            unexplored_tiles = self._get_all_unexplored_tiles(game_map)
            if not unexplored_tiles:
                logger.warning(
                    f"🔍 DIAGNOSTIC: AutoExplore.start: No unexplored tiles found, NOT activating! "
                    f"pos={player_pos}, was_active={was_active}"
                )
                self.active = False
                self.stop_reason = "All areas explored"
                return "Nothing left to explore"
            
            logger.info(
                f"🔍 DIAGNOSTIC: AutoExplore.start: Found {len(unexplored_tiles)} unexplored tiles, "
                f"activating at pos={player_pos}, was_active={was_active}"
            )
        except (TypeError, AttributeError):
            # game_map is a mock or doesn't have proper tiles - skip the check
            logger.debug(f"AutoExplore.start: Unable to check unexplored tiles (mock?), activating anyway")
            pass
        
        self.active = True
        self.current_path = []
        self.current_room = None
        self.stop_reason = None
        self.target_tile = None
        self.known_items = set()  # Reset known items
        self.known_monsters = set()  # Reset known monsters
        self.explored_tiles_at_start = set()  # Reset explored tiles snapshot
        self.known_stairs = set()  # Reset known stairs
        
        # Store initial HP for damage detection
        if hasattr(self.owner, 'fighter') and self.owner.fighter:
            self.last_hp = self.owner.fighter.hp
        else:
            self.last_hp = 0
        
        # Snapshot all currently explored tiles
        # This lets us distinguish between "already seen" vs "discovered during auto-explore"
        for x in range(game_map.width):
            for y in range(game_map.height):
                if game_map.is_explored(x, y):
                    self.explored_tiles_at_start.add((x, y))
        
        # Record entities already visible (so we don't stop for them)
        if fov_map:
            from fov_functions import map_is_in_fov
            from components.component_registry import ComponentType
            
            for entity in entities:
                # Track known items/chests/signposts
                if (entity.components.has(ComponentType.ITEM) or 
                    entity.components.has(ComponentType.CHEST) or
                    entity.components.has(ComponentType.SIGNPOST)):
                    if map_is_in_fov(fov_map, entity.x, entity.y):
                        self.known_items.add(id(entity))
                
                # Track known monsters (so we only stop for NEW monsters)
                if entity.components.has(ComponentType.AI) and entity != self.owner:
                    fighter = entity.get_component_optional(ComponentType.FIGHTER)
                    if fighter and fighter.hp > 0:
                        if map_is_in_fov(fov_map, entity.x, entity.y):
                            self.known_monsters.add(id(entity))
                
                # Track known stairs (so we only stop for NEW stairs)
                if entity.components.has(ComponentType.STAIRS):
                    if map_is_in_fov(fov_map, entity.x, entity.y):
                        self.known_stairs.add((entity.x, entity.y))
            
            logger.debug(f"Auto-explore initialized with {len(self.known_items)} known items, {len(self.known_monsters)} known monsters, and {len(self.known_stairs)} known stairs in FOV")
        
        logger.info(f"Auto-explore started for {self.owner.name}")
        return random.choice(ADVENTURE_QUOTES)
    
    def stop(self, reason: str) -> None:
        """Stop auto-exploring.
        
        Args:
            reason: Human-readable explanation for why exploration stopped
        """
        player_pos = (self.owner.x, self.owner.y) if self.owner else None
        was_active = self.active
        logger.warning(
            f"🔍 DIAGNOSTIC: AutoExplore.stop: reason='{reason}', "
            f"pos={player_pos}, was_active={was_active}, "
            f"path_len={len(self.current_path) if self.current_path else 0}, "
            f"target={self.target_tile}"
        )
        self.active = False
        self.stop_reason = reason
        self.current_path = []
        self.target_tile = None
        logger.info(f"Auto-explore stopped: {reason}")
    
    def is_active(self) -> bool:
        """Check if auto-explore is currently running.
        
        Returns:
            bool: True if actively exploring
        """
        return self.active
    
    def get_next_action(
        self,
        game_map: 'GameMap',
        entities: List['Entity'],
        fov_map
    ) -> Optional[dict]:
        """Calculate the next move for auto-exploration.
        
        This is called once per turn when auto-explore is active. It:
        1. Checks stop conditions (threats, completion, etc.)
        2. Follows current path if available
        3. Finds next unexplored tile if path exhausted
        4. Returns movement action or None if stopped
        
        Args:
            game_map: Current game map
            entities: All entities on the map
            fov_map: Field-of-view map for visibility checks
            
        Returns:
            dict: Action dict with 'dx' and 'dy' keys for movement,
                  or None if auto-explore should stop
        """
        if not self.active or not self.owner:
            logger.debug(f"AutoExplore.get_next_action: not active or no owner (active={self.active}, owner={self.owner})")
            return None
        
        player_pos = (self.owner.x, self.owner.y)
        logger.debug(f"AutoExplore.get_next_action: player_pos={player_pos}, active={self.active}, target={self.target_tile}, path_len={len(self.current_path)}")
        
        # Check stop conditions
        stop_reason = self._check_stop_conditions(game_map, entities, fov_map)
        if stop_reason:
            logger.warning(
                f"🔍 DIAGNOSTIC: AutoExplore.get_next_action: STOPPING at {player_pos}, "
                f"reason='{stop_reason}', path_len={len(self.current_path)}, "
                f"target={self.target_tile}"
            )
            self.stop(stop_reason)
            return None
        
        # If we have a current path, follow it
        if self.current_path:
            next_pos = self.current_path.pop(0)
            dx = next_pos[0] - self.owner.x
            dy = next_pos[1] - self.owner.y
            logger.debug(f"AutoExplore.get_next_action: following path from {player_pos} to {next_pos}, delta=({dx},{dy}), remaining_path_len={len(self.current_path)}")
            return {'dx': dx, 'dy': dy}
        
        # Need to find a new target
        next_target = self._find_next_unexplored_tile(game_map)
        
        if next_target is None:
            # No more unexplored tiles reachable
            logger.debug(f"AutoExplore.get_next_action: STOPPING at {player_pos}, reason='All areas explored' (no unexplored tiles found)")
            self.stop("All areas explored")
            return None
        
        logger.debug(f"AutoExplore.get_next_action: found new target={next_target} from {player_pos}")
        
        # Calculate path to target
        self.target_tile = next_target
        self.current_path = self._calculate_path_to(next_target, game_map, entities)
        
        if not self.current_path:
            # No path found
            logger.debug(f"AutoExplore.get_next_action: STOPPING at {player_pos}, reason='Cannot reach unexplored areas' (no path to {next_target})")
            self.stop("Cannot reach unexplored areas")
            return None
        
        logger.debug(f"AutoExplore.get_next_action: calculated path from {player_pos} to {next_target}, path_len={len(self.current_path)}")
        
        # Follow the path
        next_pos = self.current_path.pop(0)
        dx = next_pos[0] - self.owner.x
        dy = next_pos[1] - self.owner.y
        logger.debug(f"AutoExplore.get_next_action: starting new path from {player_pos} to {next_pos}, delta=({dx},{dy}), remaining_path_len={len(self.current_path)}")
        return {'dx': dx, 'dy': dy}
    
    def _check_stop_conditions(
        self,
        game_map: 'GameMap',
        entities: List['Entity'],
        fov_map
    ) -> Optional[str]:
        """Check if any stop condition is met.
        
        Stop conditions (in priority order):
        1. Monster in FOV
        2. Entered treasure vault
        3. Secret door discovered
        4. Chest in FOV (unopened)
        5. Signpost in FOV
        6. Valuable item in FOV
        7. Standing on stairs
        8. Took damage
        9. Has status effect
        10. Trap triggered (detected via damage)
        
        Args:
            game_map: Current game map
            entities: All entities on the map
            fov_map: Field-of-view map for visibility checks
            
        Returns:
            str: Human-readable stop reason, or None to continue
        """
        if not self.owner:
            return "Error: No owner"
        
        # 1. Check for monsters in FOV
        monster = self._monster_in_fov(entities, fov_map)
        if monster:
            return f"Monster spotted: {monster.name}"
        
        # 2. Check if entered a treasure vault
        if self._in_vault_room(game_map):
            return "Discovered treasure vault!"
        
        # 3. Check for newly revealed secret doors
        secret_door = self._secret_door_in_fov(entities, fov_map)
        if secret_door:
            return "Found secret door!"
        
        # 3. Check for chests in FOV (only in unexplored areas)
        chest = self._chest_in_fov(entities, fov_map, game_map)
        if chest:
            return "Found chest"
        
        # 4. Check for signposts in FOV (only in unexplored areas)
        signpost = self._signpost_in_fov(entities, fov_map, game_map)
        if signpost:
            return f"Found {signpost.name}"
        
        # 5. Check for valuable items in FOV (only in unexplored areas)
        item = self._valuable_item_in_fov(entities, fov_map, game_map)
        if item:
            return f"Found {item.name}"
        
        # 6. Check if standing on stairs
        if self._on_stairs(entities):
            return "Stairs found"
        
        # 7. Check for damage taken
        if self._took_damage():
            return "Took damage"
        
        # 8. Check for status effects
        effect_name = self._has_status_effect()
        if effect_name:
            return f"Affected by {effect_name}"
        
        # 9. Trap triggered - detected via damage check (already covered by #7)
        
        return None  # Continue exploring
    
    def _monster_in_fov(self, entities: List['Entity'], fov_map) -> Optional['Entity']:
        """Check if any NEW hostile monster is visible.
        
        Only returns monsters that weren't visible when auto-explore started.
        This allows auto-explore to continue past known monsters.
        
        Args:
            entities: All entities on the map
            fov_map: Field-of-view map
            
        Returns:
            Entity: First NEW hostile monster found, or None
        """
        if not self.owner or not fov_map:
            return None
        
        from fov_functions import map_is_in_fov
        from components.component_registry import ComponentType
        
        for entity in entities:
            # Skip non-monsters
            if not entity.components.has(ComponentType.AI):
                continue
            
            # Skip self
            if entity == self.owner:
                continue
            
            # Check if in FOV
            if map_is_in_fov(fov_map, entity.x, entity.y):
                # Check if hostile (has fighter component AND is alive)
                fighter = entity.get_component_optional(ComponentType.FIGHTER)
                if fighter and fighter.hp > 0:
                    # Check if this is a NEW monster (not known when we started)
                    entity_id = id(entity)
                    if entity_id in self.known_monsters:
                        # This monster was already visible, skip it
                        continue
                    
                    # NEW monster discovered! Add to known and return it
                    self.known_monsters.add(entity_id)
                    # Living, hostile NEW monster found
                    return entity
        
        return None
    
    def _in_vault_room(self, game_map: 'GameMap') -> bool:
        """Check if player is currently in a treasure vault room.
        
        Only triggers once per vault (tracks visited vaults).
        
        Args:
            game_map: Current game map
            
        Returns:
            bool: True if player just entered a new vault
        """
        if not self.owner or not game_map:
            return False
        
        # Need to check all rooms on the map to find which one we're in
        # This requires access to the rooms list, which isn't stored
        # So we'll use a simpler approach: check tile color for golden walls nearby
        
        # Look for golden vault walls in nearby tiles (within 3 tiles)
        gold_color = (200, 150, 50)
        vault_wall_found = False
        
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                x, y = self.owner.x + dx, self.owner.y + dy
                
                # Check bounds
                if not (0 <= x < game_map.width and 0 <= y < game_map.height):
                    continue
                
                # Check if this tile is a golden wall (vault indicator)
                tile = game_map.tiles[x][y]
                if tile.blocked and hasattr(tile, 'light') and tile.light == gold_color:
                    vault_wall_found = True
                    break
            
            if vault_wall_found:
                break
        
        if not vault_wall_found:
            return False
        
        # Track visited vaults to only trigger once per vault
        # Use a simple position-based key (this vault's approximate center)
        vault_key = (self.owner.x // 10, self.owner.y // 10)  # Grid-based tracking
        
        if not hasattr(self, '_visited_vaults'):
            self._visited_vaults = set()
        
        if vault_key in self._visited_vaults:
            return False  # Already visited this vault
        
        # New vault discovered!
        self._visited_vaults.add(vault_key)
        logger.debug(f"Entered new treasure vault at grid {vault_key}")
        return True
    
    def _valuable_item_in_fov(
        self, entities: List['Entity'], fov_map, game_map: 'GameMap'
    ) -> Optional['Entity']:
        """Check if any valuable item is visible IN UNEXPLORED AREAS.
        
        Only returns items in tiles that were NOT explored when auto-explore started.
        This allows exploring past items in already-explored rooms without stopping.
        
        Valuable items: equipment, scrolls, potions, wands, rings
        Not valuable: corpses, gold (if we add it), junk
        
        Args:
            entities: All entities on the map
            fov_map: Field-of-view map
            game_map: Game map for tile exploration state
            
        Returns:
            Entity: First valuable item in unexplored area, or None
        """
        if not self.owner or not fov_map or not game_map:
            return None
        
        from fov_functions import map_is_in_fov
        from components.component_registry import ComponentType
        
        for entity in entities:
            # Must have item component
            if not entity.components.has(ComponentType.ITEM):
                continue
            
            # Check if in FOV
            if map_is_in_fov(fov_map, entity.x, entity.y):
                entity_id = id(entity)
                
                # Skip items in tiles that were already explored when auto-explore started
                # This allows circling back through known areas without stopping
                if (entity.x, entity.y) in self.explored_tiles_at_start:
                    self.known_items.add(entity_id)  # Mark as known for consistency
                    continue
                
                # Skip items we already knew about
                if entity_id in self.known_items:
                    continue
                
                # Check if valuable
                is_valuable = False
                
                # Equipment: has equippable component
                if entity.components.has(ComponentType.EQUIPPABLE):
                    is_valuable = True
                
                # Consumables: has item component with use_function
                item_comp = entity.components.get(ComponentType.ITEM)
                if item_comp and item_comp.use_function:
                    is_valuable = True
                
                # Wands: has wand component
                if entity.components.has(ComponentType.WAND):
                    is_valuable = True
                
                if is_valuable:
                    # Found a new valuable item! Mark it as known and return it
                    self.known_items.add(entity_id)
                    logger.debug(f"New valuable item found: {entity.name}")
                    return entity
        
        return None
    
    def _secret_door_in_fov(
        self, entities: List['Entity'], fov_map
    ) -> Optional['Entity']:
        """Check if any newly revealed secret door is visible.
        
        Only returns NEW secret door markers that weren't visible when auto-explore started.
        This allows exploring past already-discovered secret doors.
        
        Args:
            entities: All entities on the map
            fov_map: Field-of-view map
            
        Returns:
            Entity: First new secret door marker found, or None
        """
        if not self.owner or not fov_map:
            return None
        
        from fov_functions import map_is_in_fov
        
        for entity in entities:
            # Must be a secret door marker
            if not (hasattr(entity, 'is_secret_door_marker') and entity.is_secret_door_marker):
                continue
            
            # Check if in FOV
            if map_is_in_fov(fov_map, entity.x, entity.y):
                entity_id = id(entity)
                
                # Skip doors we already knew about
                if entity_id in self.known_items:
                    continue
                
                # Found a new secret door! Mark it as known and return it
                self.known_items.add(entity_id)
                logger.debug(f"New secret door found at ({entity.x}, {entity.y})")
                return entity
        
        return None
    
    def _chest_in_fov(
        self, entities: List['Entity'], fov_map, game_map: 'GameMap'
    ) -> Optional['Entity']:
        """Check if any unopened chest is visible IN UNEXPLORED AREAS.
        
        Only returns chests in tiles that were NOT explored when auto-explore started.
        
        Args:
            entities: All entities on the map
            fov_map: Field-of-view map
            game_map: Game map for tile exploration state
            
        Returns:
            Entity: First unopened chest in unexplored area, or None
        """
        if not self.owner or not fov_map or not game_map:
            return None
        
        from fov_functions import map_is_in_fov
        from components.component_registry import ComponentType
        from components.chest import ChestState
        
        for entity in entities:
            # Must have chest component
            if not entity.components.has(ComponentType.CHEST):
                continue
            
            # Check if in FOV
            if map_is_in_fov(fov_map, entity.x, entity.y):
                entity_id = id(entity)
                chest = entity.chest
                
                # Skip chests in tiles that were already explored when auto-explore started
                if (entity.x, entity.y) in self.explored_tiles_at_start:
                    self.known_items.add(entity_id)
                    continue
                
                # Skip chests we already knew about
                if entity_id in self.known_items:
                    continue
                
                # Only stop for unopened chests (skip already looted ones)
                if chest and chest.state != ChestState.OPEN:
                    # Found a new unopened chest! Mark it as known and return it
                    self.known_items.add(entity_id)
                    logger.debug(f"New unopened chest found: {entity.name}")
                    return entity
        
        return None
    
    def _signpost_in_fov(
        self, entities: List['Entity'], fov_map, game_map: 'GameMap'
    ) -> Optional['Entity']:
        """Check if any unread signpost is visible IN UNEXPLORED AREAS.
        
        Only returns signposts in tiles that were NOT explored when auto-explore started.
        
        Args:
            entities: All entities on the map
            fov_map: Field-of-view map
            game_map: Game map for tile exploration state
            
        Returns:
            Entity: First unread signpost in unexplored area, or None
        """
        if not self.owner or not fov_map or not game_map:
            return None
        
        from fov_functions import map_is_in_fov
        from components.component_registry import ComponentType
        
        for entity in entities:
            # Must have signpost component
            if not entity.components.has(ComponentType.SIGNPOST):
                continue
            
            # Check if in FOV
            if map_is_in_fov(fov_map, entity.x, entity.y):
                entity_id = id(entity)
                signpost = entity.signpost
                
                # Skip signposts in tiles that were already explored when auto-explore started
                if (entity.x, entity.y) in self.explored_tiles_at_start:
                    self.known_items.add(entity_id)
                    continue
                
                # Skip signposts we already knew about
                if entity_id in self.known_items:
                    continue
                
                # Only stop for unread signposts (skip already read ones)
                if signpost and not signpost.has_been_read:
                    # Found a new unread signpost! Mark it as known and return it
                    self.known_items.add(entity_id)
                    logger.debug(f"New unread signpost found: {entity.name}")
                    return entity
        
        return None
    
    def _on_stairs(self, entities: List['Entity']) -> bool:
        """Check if player is standing on NEW stairs (not already known).
        
        This prevents the bot from getting stuck in a loop when it stops on stairs
        and then tries to restart auto-explore while still standing on them.
        
        Args:
            entities: All entities on the map
            
        Returns:
            bool: True if on NEW stairs (position not in known_stairs)
        """
        if not self.owner:
            return False
        
        from components.component_registry import ComponentType
        
        player_pos = (self.owner.x, self.owner.y)
        
        # Check for stairs entity at player position
        for entity in entities:
            if entity.components.has(ComponentType.STAIRS):
                if entity.x == self.owner.x and entity.y == self.owner.y:
                    # Found stairs at player position
                    # Only stop if these are NEW stairs (not already known)
                    if player_pos not in self.known_stairs:
                        # New stairs discovered! Add to known and return True to stop
                        self.known_stairs.add(player_pos)
                        logger.debug(f"New stairs discovered at {player_pos}")
                        return True
                    else:
                        # Already knew about these stairs - don't stop
                        logger.debug(f"Standing on known stairs at {player_pos} - continuing exploration")
                        return False
        
        return False
    
    def _took_damage(self) -> bool:
        """Check if player took damage since last turn.
        
        Returns:
            bool: True if HP decreased
        """
        if not self.owner or not hasattr(self.owner, 'fighter'):
            return False
        
        current_hp = self.owner.fighter.hp
        took_damage = current_hp < self.last_hp
        
        # Update last_hp for next check
        self.last_hp = current_hp
        
        return took_damage
    
    def _has_status_effect(self) -> Optional[str]:
        """Check if player has any negative status effects.
        
        Returns:
            str: Name of status effect, or None
        """
        if not self.owner:
            return None
        
        from components.component_registry import ComponentType
        
        if not self.owner.components.has(ComponentType.STATUS_EFFECTS):
            return None
        
        status_effects = self.owner.components.get(ComponentType.STATUS_EFFECTS)
        
        # Check for any active negative effects
        negative_effects = ['poisoned', 'confused', 'slowed', 'blinded', 'stuck']
        
        for effect_name in negative_effects:
            if hasattr(status_effects, effect_name):
                effect = getattr(status_effects, effect_name)
                if effect and effect > 0:  # Effect is active
                    return effect_name.capitalize()
        
        return None
    
    def _find_next_unexplored_tile(self, game_map: 'GameMap') -> Optional[Tuple[int, int]]:
        """Find the nearest unexplored tile using room-by-room priority.
        
        Strategy:
        1. Identify current room (if any)
        2. Find unexplored tiles in current room
        3. If room complete, find nearest unexplored tile in any room
        4. Use Dijkstra to find closest reachable unexplored tile
        
        Args:
            game_map: Game map with tile data
            
        Returns:
            (x, y): Coordinates of next tile to explore, or None if all explored
        """
        if not self.owner:
            return None
        
        player_pos = (self.owner.x, self.owner.y)
        
        # Identify current room
        self.current_room = self._identify_current_room(game_map)
        
        # If in a room, prioritize finishing it
        if self.current_room:
            room_unexplored = self._get_unexplored_tiles_in_room(
                self.current_room, game_map
            )
            if room_unexplored:
                # Find closest unexplored tile in current room
                logger.debug(f"AutoExplore._find_next_unexplored_tile: at {player_pos}, in room {self.current_room}, found {len(room_unexplored)} unexplored tiles in room")
                closest = self._find_closest_tile(room_unexplored, game_map)
                logger.debug(f"AutoExplore._find_next_unexplored_tile: closest in room is {closest}")
                return closest
        
        # Either not in a room, or current room is done
        # Find any unexplored tile
        all_unexplored = self._get_all_unexplored_tiles(game_map)
        
        logger.debug(f"AutoExplore._find_next_unexplored_tile: at {player_pos}, current_room={self.current_room}, found {len(all_unexplored)} total unexplored tiles")
        
        if not all_unexplored:
            logger.debug(f"AutoExplore._find_next_unexplored_tile: NO unexplored tiles remaining")
            return None  # Map fully explored!
        
        # Find closest reachable unexplored tile
        closest = self._find_closest_tile(all_unexplored, game_map)
        logger.debug(f"AutoExplore._find_next_unexplored_tile: closest unexplored tile (any room) is {closest}")
        return closest
    
    def _identify_current_room(self, game_map: 'GameMap') -> Optional[Rect]:
        """Identify which room the player is currently in.
        
        Scans nearby tiles to find room boundaries. Rooms are defined as
        contiguous open areas surrounded by walls.
        
        Args:
            game_map: Game map with tile data
            
        Returns:
            Rect: Room boundaries if in a room, None if in hallway
        """
        if not self.owner:
            return None
        
        px, py = self.owner.x, self.owner.y
        
        # Flood fill from player position to find room bounds
        visited = set()
        queue = deque([(px, py)])
        room_tiles = []
        
        while queue and len(visited) < 100:  # Limit search to reasonable room size
            x, y = queue.popleft()
            
            if (x, y) in visited:
                continue
            
            if not (0 <= x < game_map.width and 0 <= y < game_map.height):
                continue
            
            # Check if tile is walkable
            if game_map.tiles[x][y].blocked:
                continue
            
            visited.add((x, y))
            room_tiles.append((x, y))
            
            # Add neighbors
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                queue.append((x + dx, y + dy))
        
        if len(room_tiles) < 9:  # Too small to be a room (min 3x3)
            return None
        
        # Calculate bounding box
        if not room_tiles:
            return None
        
        xs = [x for x, y in room_tiles]
        ys = [y for x, y in room_tiles]
        
        x1, x2 = min(xs), max(xs)
        y1, y2 = min(ys), max(ys)
        
        # Create Rect (note: Rect uses width/height, not x2/y2)
        return Rect(x1, y1, x2 - x1, y2 - y1)
    
    def _get_unexplored_tiles_in_room(
        self, room: Rect, game_map: 'GameMap'
    ) -> List[Tuple[int, int]]:
        """Get all unexplored walkable tiles in a room.
        
        Args:
            room: Room boundaries
            game_map: Game map with tile data
            
        Returns:
            List of (x, y) tuples for unexplored tiles
        """
        unexplored = []
        
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                if not (0 <= x < game_map.width and 0 <= y < game_map.height):
                    continue
                
                tile = game_map.tiles[x][y]
                
                # Must be walkable and not yet explored
                if not tile.blocked and not tile.explored:
                    # Also check for hazards (treat as blocked)
                    if not game_map.hazard_manager.has_hazard_at(x, y):
                        unexplored.append((x, y))
        
        return unexplored
    
    def _get_all_unexplored_tiles(self, game_map: 'GameMap') -> List[Tuple[int, int]]:
        """Get all unexplored walkable tiles on the map.
        
        Args:
            game_map: Game map with tile data
            
        Returns:
            List of (x, y) tuples for unexplored tiles
        """
        unexplored = []
        
        for x in range(game_map.width):
            for y in range(game_map.height):
                tile = game_map.tiles[x][y]
                
                # Must be walkable and not yet explored
                if not tile.blocked and not tile.explored:
                    # Also check for hazards (treat as blocked)
                    if not game_map.hazard_manager.has_hazard_at(x, y):
                        unexplored.append((x, y))
        
        return unexplored
    
    def _find_closest_tile(
        self, tiles: List[Tuple[int, int]], game_map: 'GameMap'
    ) -> Optional[Tuple[int, int]]:
        """Find the closest reachable tile from the list using Dijkstra.
        
        Args:
            tiles: List of candidate tiles
            game_map: Game map for pathfinding
            
        Returns:
            (x, y): Closest reachable tile, or None if none reachable
        """
        if not self.owner or not tiles:
            return None
        
        # Use Dijkstra to find closest tile
        # Priority queue: (distance, (x, y))
        start = (self.owner.x, self.owner.y)
        pq = [(0, start)]
        visited = set()
        distances = {start: 0}
        target_tiles = set(tiles)
        
        while pq:
            dist, pos = heapq.heappop(pq)
            
            if pos in visited:
                continue
            
            visited.add(pos)
            
            # Check if we reached a target
            if pos in target_tiles:
                logger.debug(f"AutoExplore._find_closest_tile: found reachable target {pos} at distance {dist} from {start}")
                return pos
            
            x, y = pos
            
            # Check neighbors
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                neighbor = (nx, ny)
                
                # Check bounds
                if not (0 <= nx < game_map.width and 0 <= ny < game_map.height):
                    continue
                
                # Check if walkable
                if game_map.tiles[nx][ny].blocked:
                    continue
                
                # Check for hazards (treat as blocked)
                if game_map.hazard_manager.has_hazard_at(nx, ny):
                    continue
                
                # Calculate new distance
                new_dist = dist + 1
                
                if neighbor not in distances or new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    heapq.heappush(pq, (new_dist, neighbor))
        
        # No reachable target found
        logger.debug(f"AutoExplore._find_closest_tile: NO reachable targets found from {start} among {len(tiles)} candidates")
        return None
    
    def _calculate_path_to(
        self,
        target: Tuple[int, int],
        game_map: 'GameMap',
        entities: List['Entity']
    ) -> List[Tuple[int, int]]:
        """Calculate A* path to target, avoiding hazards.
        
        Args:
            target: (x, y) destination
            game_map: Game map for pathfinding
            entities: All entities (for collision detection)
            
        Returns:
            List of (x, y) positions to visit (excluding start position)
        """
        if not self.owner:
            return []
        
        # Use A* pathfinding with hazard avoidance
        import tcod
        import numpy as np
        
        # Create cost map using numpy (indexed as [y, x])
        # This matches entity.py's approach (lines 392-395)
        cost = np.zeros((game_map.height, game_map.width), dtype=np.int8)
        
        for y in range(game_map.height):
            for x in range(game_map.width):
                # Blocked tiles are impassable
                if game_map.tiles[x][y].blocked:
                    cost[y, x] = 0
                # Hazards are treated as impassable
                elif game_map.hazard_manager.has_hazard_at(x, y):
                    cost[y, x] = 0
                else:
                    cost[y, x] = 1
        
        # Entities block movement (except target tile)
        for entity in entities:
            if entity.blocks and entity != self.owner:
                ex, ey = entity.x, entity.y
                if 0 <= ex < game_map.width and 0 <= ey < game_map.height:
                    if (ex, ey) != target:  # Allow moving to target even if entity there
                        cost[ey, ex] = 0
        
        # Transpose cost array from [y, x] to [x, y] for tcod
        # This matches entity.py line 431
        cost_array = cost.T
        
        # Bounds check for player position (prevent IndexError)
        start_x, start_y = self.owner.x, self.owner.y
        
        # Log dimensions for debugging
        logger.debug(f"Map dimensions: {game_map.width}x{game_map.height}, "
                    f"Player position: ({start_x}, {start_y}), "
                    f"Target: {target}, "
                    f"Cost array shape after transpose: {cost_array.shape}")
        
        # Validate player position is within map bounds
        if start_x < 0 or start_x >= game_map.width or start_y < 0 or start_y >= game_map.height:
            logger.error(f"Player position ({start_x}, {start_y}) out of map bounds "
                        f"({game_map.width}x{game_map.height})")
            return []  # Cannot pathfind from invalid position
        
        # Create graph and pathfinder (modern tcod API)
        graph = tcod.path.SimpleGraph(cost=cost_array, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)
        pathfinder.add_root((start_x, start_y))
        
        # Find path
        path = pathfinder.path_to((target[0], target[1]))
        
        # Convert to list of tuples (excluding start position)
        return [(x, y) for x, y in path[1:]]

