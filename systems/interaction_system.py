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
    """
    
    def __init__(
        self,
        action_taken: bool = False,
        state_change: Optional['GameStates'] = None,
        message: Optional[str] = None,
        npc_dialogue: Optional['Entity'] = None,
        consume_turn: bool = False,
        start_pathfinding: bool = False
    ):
        self.action_taken = action_taken
        self.state_change = state_change
        self.message = message
        self.npc_dialogue = npc_dialogue
        self.consume_turn = consume_turn
        self.start_pathfinding = start_pathfinding


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
        
        # Check for victory trigger
        if item_was_added and hasattr(item, 'triggers_victory') and item.triggers_victory:
            logger.info("=== ITEM PICKUP: Victory trigger detected ===")
            # Victory handling will be done by caller
        
        return InteractionResult(
            action_taken=True,
            consume_turn=True,
            message=messages[0] if messages else None
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


class InteractionSystem:
    """Main interaction system coordinating all strategies."""
    
    def __init__(self):
        """Initialize with all interaction strategies."""
        self.strategies: List[InteractionStrategy] = [
            EnemyInteractionStrategy(),
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

