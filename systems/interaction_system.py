"""Interaction System - Clean, testable right-click interactions.

This module provides a strategy-based interaction system that replaces
the brittle nested if/elif logic in the right-click handler.

Design:
- Strategy Pattern: Each interaction type (Enemy, Item, NPC) is a strategy
- Clear Priority: Explicit priority ordering, easy to modify
- Shared Logic: Pathfinding extracted to avoid duplication
- Testable: Each strategy can be tested independently

Usage:
    system = InteractionSystem()
    result = system.handle_click(world_x, world_y, player, entities, game_map, fov_map)
    
    if result.action_taken:
        # Process result (state change, message, etc.)
"""

from typing import List, Optional, Tuple, Dict, Any
from abc import ABC, abstractmethod
import logging

from components.component_registry import ComponentType

logger = logging.getLogger(__name__)


class InteractionResult:
    """Result of an interaction attempt.
    
    Attributes:
        action_taken: Whether an action was performed
        state_change: Optional new game state
        message: Optional message to display
        npc_dialogue: Optional NPC to start dialogue with
        consume_turn: Whether to consume a turn
        start_pathfinding: Whether pathfinding was initiated
        victory_triggered: Whether picking up a victory item (Ruby Heart)
        loot_items: Items dropped by interaction (e.g., from chest)
    """
    
    def __init__(
        self,
        action_taken: bool = False,
        state_change: Optional['GameStates'] = None,
        message: Optional[str] = None,
        npc_dialogue: Optional['Entity'] = None,
        consume_turn: bool = False,
        start_pathfinding: bool = False,
        victory_triggered: bool = False,
        loot_items: Optional[List['Entity']] = None
    ):
        self.action_taken = action_taken
        self.state_change = state_change
        self.message = message
        self.npc_dialogue = npc_dialogue
        self.consume_turn = consume_turn
        self.start_pathfinding = start_pathfinding
        self.victory_triggered = victory_triggered
        self.loot_items = loot_items or []


class InteractionStrategy(ABC):
    """Base class for interaction strategies."""
    
    @abstractmethod
    def can_interact(self, entity: 'Entity', player: 'Entity') -> bool:
        """Check if this strategy can interact with the given entity.
        
        Args:
            entity: The entity to check
            player: The player entity
            
        Returns:
            bool: True if this strategy handles this entity type
        """
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        """Get the priority of this strategy (lower = higher priority).
        
        Returns:
            int: Priority value (0 = highest)
        """
        pass
    
    @abstractmethod
    def interact(
        self,
        entity: 'Entity',
        player: 'Entity',
        game_map: 'GameMap',
        entities: List['Entity'],
        fov_map,
        pathfinder: 'PathfindingHelper'
    ) -> InteractionResult:
        """Perform the interaction.
        
        Args:
            entity: The entity to interact with
            player: The player entity
            game_map: The game map
            entities: List of all entities
            fov_map: Field of view map
            pathfinder: Helper for pathfinding operations
            
        Returns:
            InteractionResult: Result of the interaction
        """
        pass


class EnemyInteractionStrategy(InteractionStrategy):
    """Strategy for interacting with enemies (throw item)."""
    
    def can_interact(self, entity: 'Entity', player: 'Entity') -> bool:
        """Check if entity is a living enemy."""
        if entity == player:
            return False
        
        if not entity.components.has(ComponentType.FIGHTER):
            return False
        
        fighter = entity.components.get(ComponentType.FIGHTER)
        return fighter and fighter.hp > 0
    
    def get_priority(self) -> int:
        """Enemies have highest priority (combat is urgent)."""
        return 0
    
    def interact(
        self,
        entity: 'Entity',
        player: 'Entity',
        game_map: 'GameMap',
        entities: List['Entity'],
        fov_map,
        pathfinder: 'PathfindingHelper'
    ) -> InteractionResult:
        """Open throw item menu for enemy."""
        if not player.inventory or not player.inventory.items:
            from message_builder import MessageBuilder as MB
            return InteractionResult(
                action_taken=True,
                message=MB.warning("You have nothing to throw.")
            )
        
        # Trigger throw item selection state
        from game_states import GameStates
        return InteractionResult(
            action_taken=True,
            state_change=GameStates.THROW_SELECT_ITEM,
            # Store target coordinates for after item selection
            # (caller will handle this via state manager)
        )


class ItemInteractionStrategy(InteractionStrategy):
    """Strategy for interacting with items (pickup)."""
    
    def can_interact(self, entity: 'Entity', player: 'Entity') -> bool:
        """Check if entity is an item."""
        return entity.components.has(ComponentType.ITEM)
    
    def get_priority(self) -> int:
        """Items have medium priority."""
        return 1
    
    def interact(
        self,
        entity: 'Entity',
        player: 'Entity',
        game_map: 'GameMap',
        entities: List['Entity'],
        fov_map,
        pathfinder: 'PathfindingHelper'
    ) -> InteractionResult:
        """Pick up item or pathfind to it."""
        distance = player.distance_to(entity)
        
        if distance <= 1:
            # Adjacent - pick up immediately
            return self._pickup_item(entity, player, entities)
        else:
            # Too far - pathfind
            return pathfinder.pathfind_to_item(entity, player, game_map, entities, fov_map)
    
    def _pickup_item(
        self,
        item: 'Entity',
        player: 'Entity',
        entities: List['Entity']
    ) -> InteractionResult:
        """Immediate pickup logic."""
        if not player.inventory:
            from message_builder import MessageBuilder as MB
            return InteractionResult(
                action_taken=True,
                message=MB.warning("You cannot carry items.")
            )
        
        pickup_results = player.inventory.add_item(item)
        item_was_added = False
        messages = []
        
        for result in pickup_results:
            message = result.get("message")
            if message:
                messages.append(message)
            
            if result.get("item_added") or result.get("item_consumed"):
                if item in entities:
                    entities.remove(item)
                item_was_added = True
        
        # Check for victory trigger (Ruby Heart)
        victory_triggered = False
        if item_was_added and hasattr(item, 'triggers_victory') and item.triggers_victory:
            logger.info("=== ITEM PICKUP: Victory trigger detected ===")
            victory_triggered = True
        
        return InteractionResult(
            action_taken=True,
            consume_turn=True,
            message=messages[0] if messages else None,
            victory_triggered=victory_triggered
        )


class NPCInteractionStrategy(InteractionStrategy):
    """Strategy for interacting with NPCs (dialogue)."""
    
    def can_interact(self, entity: 'Entity', player: 'Entity') -> bool:
        """Check if entity is an NPC with dialogue."""
        return (hasattr(entity, 'is_npc') and entity.is_npc and
                hasattr(entity, 'npc_dialogue') and entity.npc_dialogue)
    
    def get_priority(self) -> int:
        """NPCs have lowest priority (they can wait)."""
        return 2
    
    def interact(
        self,
        entity: 'Entity',
        player: 'Entity',
        game_map: 'GameMap',
        entities: List['Entity'],
        fov_map,
        pathfinder: 'PathfindingHelper'
    ) -> InteractionResult:
        """Start dialogue or pathfind to NPC."""
        distance = player.distance_to(entity)
        
        if distance <= 1.5:  # Adjacent or same tile
            # Close enough - start dialogue
            return self._start_dialogue(entity, game_map)
        else:
            # Too far - pathfind
            return pathfinder.pathfind_to_npc(entity, player, game_map, entities, fov_map)
    
    def _start_dialogue(self, npc: 'Entity', game_map: 'GameMap') -> InteractionResult:
        """Start dialogue with NPC."""
        dungeon_level = game_map.dungeon_level if game_map else 1
        
        if not npc.npc_dialogue.start_encounter(dungeon_level):
            from message_builder import MessageBuilder as MB
            return InteractionResult(
                action_taken=True,
                message=MB.info(f"{npc.name} has nothing to say right now.")
            )
        
        from message_builder import MessageBuilder as MB
        from game_states import GameStates
        
        return InteractionResult(
            action_taken=True,
            state_change=GameStates.NPC_DIALOGUE,
            npc_dialogue=npc,
            message=MB.info(f"You approach {npc.name}..."),
            consume_turn=False  # Dialogue doesn't consume turn
        )


class ChestInteractionStrategy(InteractionStrategy):
    """Strategy for interacting with chests (open and loot)."""
    
    def can_interact(self, entity: 'Entity', player: 'Entity') -> bool:
        """Check if entity is an openable chest.
        
        Checks for 'openable' tag (added by chest factory) and ensures chest
        has a chest component.
        
        Note: We return True even for already-open chests, so we can display
        a message. The interact() method will handle already-open state.
        """
        if 'openable' not in entity.tags:
            return False
        
        # Must have a chest component (check via direct attribute first, then registry)
        chest = getattr(entity, 'chest', None) or (entity.components.get(ComponentType.CHEST) if hasattr(entity.components, 'get') else None)
        if not chest:
            return False
        
        # Return True for both openable and already-open chests
        # The interact() method will handle already-open appropriately
        return True
    
    def get_priority(self) -> int:
        """Chests have medium-high priority (more important than items, less than combat)."""
        return 0.5  # Between enemies (0) and items (1)
    
    def interact(
        self,
        entity: 'Entity',
        player: 'Entity',
        game_map: 'GameMap',
        entities: List['Entity'],
        fov_map,
        pathfinder: 'PathfindingHelper'
    ) -> InteractionResult:
        """Open chest or pathfind to adjacent tile and open.
        
        Strategy:
        1. If adjacent (Manhattan ≤ 1): open immediately (or show already-open message)
        2. If far: pathfind to adjacent tile, then queue open action
        """
        from message_builder import MessageBuilder as MB
        
        chest = entity.chest
        distance = player.distance_to(entity)
        
        # Check if chest is already open
        if not chest.can_interact():
            return InteractionResult(
                action_taken=True,
                message=MB.info("This chest is already empty."),
                consume_turn=False  # No turn consumed for just looking at open chest
            )
        
        if distance <= 1:
            # Adjacent - open immediately
            return self._open_chest_immediate(entity, player)
        else:
            # Too far - pathfind to adjacent tile
            return pathfinder.pathfind_to_chest(entity, player, game_map, entities, fov_map)
    
    def _open_chest_immediate(self, chest_entity: 'Entity', player: 'Entity') -> InteractionResult:
        """Immediately open the chest.
        
        Args:
            chest_entity: The chest to open
            player: The player
            
        Returns:
            InteractionResult with chest opening outcome
        """
        from message_builder import MessageBuilder as MB
        
        chest = chest_entity.chest
        
        # Call chest.open() to handle trap/lock/loot logic
        results = chest.open(player, has_key=False)  # TODO: Check for actual key items
        
        # Collect all messages and loot from results
        messages = []
        loot_items = []
        
        for result in results:
            if 'message' in result:
                messages.append(result['message'])
            if result.get('loot'):
                loot_items.extend(result['loot'])
        
        # Build composite message with loot details
        primary_message = messages[0] if messages else MB.success("You open the chest.")
        
        if loot_items:
            # Add loot description to the message
            display_names = []
            for item in loot_items:
                if hasattr(item, 'item') and item.item:
                    display_names.append(item.item.get_display_name(show_quantity=False))
                else:
                    display_names.append(item.name)
            
            loot_desc = ", ".join(display_names)
            if len(display_names) == 1:
                final_message = MB.success(f"You open the chest! It contains: {loot_desc}")
            else:
                final_message = MB.success(f"You open the chest! It contains: {loot_desc}")
        else:
            final_message = MB.info("You open the chest, but it's empty.")
        
        logger.debug(f"Chest opened immediately: {chest_entity.name}")
        
        return InteractionResult(
            action_taken=True,
            message=final_message,
            consume_turn=True,
            loot_items=loot_items  # Return loot so caller can add to entities
        )


class SignpostInteractionStrategy(InteractionStrategy):
    """Strategy for interacting with signposts (reading messages)."""
    
    def can_interact(self, entity: 'Entity', player: 'Entity') -> bool:
        """Check if entity is a readable signpost."""
        return 'interactable' in entity.tags and hasattr(entity, 'signpost') and entity.signpost is not None
    
    def get_priority(self) -> int:
        """Signposts have same priority as chests and murals."""
        return 0.5
    
    def interact(
        self,
        entity: 'Entity',
        player: 'Entity',
        game_map: 'GameMap',
        entities: List['Entity'],
        fov_map,
        pathfinder: 'PathfindingHelper'
    ) -> InteractionResult:
        """Read signpost or pathfind to adjacent tile and read.
        
        Strategy:
        1. If adjacent (Manhattan ≤ 1): read immediately
        2. If far: pathfind to adjacent tile, then read
        """
        from message_builder import MessageBuilder as MB
        
        distance = player.distance_to(entity)
        signpost = entity.signpost
        
        if distance <= 1:
            # Adjacent - read immediately
            return InteractionResult(
                action_taken=True,
                message=MB.custom(signpost.message, (200, 200, 200)),  # Light gray for signpost text
                consume_turn=False  # Reading doesn't consume turn
            )
        else:
            # Too far - pathfind to adjacent tile
            pathfinding = player.get_component_optional(ComponentType.PATHFINDING)
            if not pathfinding:
                return InteractionResult(
                    action_taken=True,
                    message=MB.warning("Cannot path to that location.")
                )
            
            # Find a walkable adjacent tile to the signpost (since signposts block movement)
            adjacent_tile = self._find_adjacent_walkable_tile(
                entity.x, entity.y, game_map, entities
            )
            
            if not adjacent_tile:
                return InteractionResult(
                    action_taken=True,
                    message=MB.warning("Cannot reach that signpost.")
                )
            
            # Pathfind to the adjacent tile instead of the signpost itself
            success = pathfinding.set_destination(
                adjacent_tile[0], adjacent_tile[1], game_map, entities, fov_map
            )
            
            if not success:
                return InteractionResult(
                    action_taken=True,
                    message=MB.warning("Cannot reach that signpost.")
                )
            
            # Store target for auto-read
            pathfinding.auto_read_target = entity
            
            return InteractionResult(
                action_taken=True,
                start_pathfinding=True,
                message=MB.info(f"Moving closer to read {entity.name}...")
            )


class MuralInteractionStrategy(InteractionStrategy):
    """Strategy for interacting with murals (reading environmental lore)."""
    
    def can_interact(self, entity: 'Entity', player: 'Entity') -> bool:
        """Check if entity is a readable mural."""
        return 'interactable' in entity.tags and hasattr(entity, 'mural') and entity.mural is not None
    
    def get_priority(self) -> int:
        """Murals have same priority as chests (medium-high)."""
        return 0.5  # Same as chests
    
    def interact(
        self,
        entity: 'Entity',
        player: 'Entity',
        game_map: 'GameMap',
        entities: List['Entity'],
        fov_map,
        pathfinder: 'PathfindingHelper'
    ) -> InteractionResult:
        """Read mural or pathfind to adjacent tile and read.
        
        Strategy:
        1. If adjacent (Manhattan ≤ 1): read immediately
        2. If far: pathfind to adjacent tile, then read
        """
        from message_builder import MessageBuilder as MB
        
        distance = player.distance_to(entity)
        mural = entity.mural
        
        if distance <= 1:
            # Adjacent - read immediately
            return InteractionResult(
                action_taken=True,
                message=MB.custom(mural.text, (220, 20, 60)),  # Crimson red for mural text
                consume_turn=False  # Reading doesn't consume turn
            )
        else:
            # Too far - pathfind to adjacent tile
            pathfinding = player.get_component_optional(ComponentType.PATHFINDING)
            if not pathfinding:
                return InteractionResult(
                    action_taken=True,
                    message=MB.warning("Cannot path to that location.")
                )
            
            # Find a walkable adjacent tile to the mural (since murals block movement)
            adjacent_tile = self._find_adjacent_walkable_tile(
                entity.x, entity.y, game_map, entities
            )
            
            if not adjacent_tile:
                return InteractionResult(
                    action_taken=True,
                    message=MB.warning("Cannot reach that mural.")
                )
            
            # Pathfind to the adjacent tile instead of the mural itself
            success = pathfinding.set_destination(
                adjacent_tile[0], adjacent_tile[1], game_map, entities, fov_map
            )
            
            if not success:
                return InteractionResult(
                    action_taken=True,
                    message=MB.warning("Cannot reach that mural.")
                )
            
            # Store target for auto-read
            pathfinding.auto_read_target = entity
            
            return InteractionResult(
                action_taken=True,
                start_pathfinding=True,
                message=MB.info(f"Moving closer to read {entity.name}...")
            )


class PathfindingHelper:
    """Helper class for pathfinding operations."""
    
    def pathfind_to_item(
        self,
        item: 'Entity',
        player: 'Entity',
        game_map: 'GameMap',
        entities: List['Entity'],
        fov_map
    ) -> InteractionResult:
        """Pathfind to item for pickup."""
        pathfinding = player.get_component_optional(ComponentType.PATHFINDING)
        if not pathfinding:
            return InteractionResult(action_taken=False)
        
        success = pathfinding.set_destination(
            item.x, item.y, game_map, entities, fov_map
        )
        
        if not success:
            from message_builder import MessageBuilder as MB
            return InteractionResult(
                action_taken=True,
                message=MB.warning("Cannot path to that location.")
            )
        
        # Mark for auto-pickup
        player.pathfinding.auto_pickup_target = item
        
        # Get display name
        display_name = item.name
        if item.item:
            display_name = item.item.get_display_name(show_quantity=False)
        
        from message_builder import MessageBuilder as MB
        return InteractionResult(
            action_taken=True,
            start_pathfinding=True,
            message=MB.info(f"Moving to pick up {display_name}...")
        )
    
    def pathfind_to_npc(
        self,
        npc: 'Entity',
        player: 'Entity',
        game_map: 'GameMap',
        entities: List['Entity'],
        fov_map
    ) -> InteractionResult:
        """Pathfind to NPC for dialogue."""
        pathfinding = player.get_component_optional(ComponentType.PATHFINDING)
        if not pathfinding:
            return InteractionResult(action_taken=False)
        
        success = pathfinding.set_destination(
            npc.x, npc.y, game_map, entities, fov_map
        )
        
        if not success:
            from message_builder import MessageBuilder as MB
            return InteractionResult(
                action_taken=True,
                message=MB.warning(f"Can't reach {npc.name}.")
            )
        
        # Mark for auto-talk
        player.pathfinding.auto_talk_target = npc
        
        from message_builder import MessageBuilder as MB
        return InteractionResult(
            action_taken=True,
            start_pathfinding=True,
            message=MB.info(f"Moving to {npc.name}...")
        )
    
    def pathfind_to_chest(
        self,
        chest_entity: 'Entity',
        player: 'Entity',
        game_map: 'GameMap',
        entities: List['Entity'],
        fov_map
    ) -> InteractionResult:
        """Pathfind to adjacent tile of chest, then auto-open.
        
        Finds walkable adjacent tile to chest and paths there, queuing
        auto-open action on arrival.
        """
        pathfinding = player.get_component_optional(ComponentType.PATHFINDING)
        if not pathfinding:
            from message_builder import MessageBuilder as MB
            return InteractionResult(
                action_taken=True,
                message=MB.warning("Cannot path to that location.")
            )
        
        # Find a walkable adjacent tile to the chest (since chest blocks movement)
        adjacent_tile = self._find_adjacent_walkable_tile(
            chest_entity.x, chest_entity.y, game_map, entities
        )
        
        if not adjacent_tile:
            from message_builder import MessageBuilder as MB
            return InteractionResult(
                action_taken=True,
                message=MB.warning("Cannot reach that chest.")
            )
        
        # Pathfind to the adjacent tile instead of the chest itself
        success = pathfinding.set_destination(
            adjacent_tile[0], adjacent_tile[1], game_map, entities, fov_map
        )
        
        if not success:
            from message_builder import MessageBuilder as MB
            return InteractionResult(
                action_taken=True,
                message=MB.warning("Cannot path to that chest.")
            )
        
        # Mark for auto-open
        player.pathfinding.auto_open_target = chest_entity
        
        from message_builder import MessageBuilder as MB
        return InteractionResult(
            action_taken=True,
            start_pathfinding=True,
            message=MB.info(f"Moving to open {chest_entity.name}...")
        )
    
    @staticmethod
    def _find_adjacent_walkable_tile(center_x: int, center_y: int, 
                                     game_map: 'GameMap', 
                                     entities: List['Entity']) -> Optional[Tuple[int, int]]:
        """Find a walkable adjacent tile to the given center position.
        
        Args:
            center_x, center_y: Center position
            game_map: Game map to check walkability
            entities: Entity list to check for blocking entities
            
        Returns:
            Tuple of (x, y) for adjacent walkable tile, or None if none found
        """
        # Check all 8 adjacent tiles
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue  # Skip center
                
                adj_x = center_x + dx
                adj_y = center_y + dy
                
                # Check bounds
                if not (0 <= adj_x < game_map.width and 0 <= adj_y < game_map.height):
                    continue
                
                # Check if tile is walkable (not blocked by terrain)
                if game_map.tiles[adj_x][adj_y].blocked:
                    continue
                
                # Check if tile is blocked by an entity
                blocked_by_entity = False
                for entity in entities:
                    if entity.blocks and entity.x == adj_x and entity.y == adj_y:
                        blocked_by_entity = True
                        break
                
                if not blocked_by_entity:
                    return (adj_x, adj_y)
        
        return None


class InteractionSystem:
    """Main interaction system coordinating all strategies."""
    
    def __init__(self):
        """Initialize with all interaction strategies."""
        self.strategies: List[InteractionStrategy] = [
            EnemyInteractionStrategy(),
            ChestInteractionStrategy(),
            SignpostInteractionStrategy(),
            MuralInteractionStrategy(),
            ItemInteractionStrategy(),
            NPCInteractionStrategy(),
        ]
        
        # Sort by priority (lower number = higher priority)
        self.strategies.sort(key=lambda s: s.get_priority())
        
        self.pathfinder = PathfindingHelper()
        
        logger.info(f"InteractionSystem initialized with {len(self.strategies)} strategies")
    
    def handle_click(
        self,
        world_x: int,
        world_y: int,
        player: 'Entity',
        entities: List['Entity'],
        game_map: 'GameMap',
        fov_map
    ) -> InteractionResult:
        """Handle a right-click at the given coordinates.
        
        Tries each strategy in priority order until one handles the interaction.
        
        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            player: Player entity
            entities: List of all entities
            game_map: Game map
            fov_map: Field of view map
            
        Returns:
            InteractionResult: Result of the interaction
        """
        # Find entity at click location
        target_entity = None
        for entity in entities:
            if entity.x == world_x and entity.y == world_y:
                # Try each strategy in priority order
                for strategy in self.strategies:
                    if strategy.can_interact(entity, player):
                        logger.debug(f"Using {strategy.__class__.__name__} for {entity.name}")
                        return strategy.interact(
                            entity, player, game_map, entities, fov_map, self.pathfinder
                        )
        
        # No entity found or no strategy handled it
        return InteractionResult(action_taken=False)


# Global system instance
_interaction_system: Optional[InteractionSystem] = None


def get_interaction_system() -> InteractionSystem:
    """Get the global interaction system instance.
    
    Returns:
        InteractionSystem: The singleton instance
    """
    global _interaction_system
    if _interaction_system is None:
        _interaction_system = InteractionSystem()
    return _interaction_system

