"""Pickup service - single source of truth for all item pickup logic.

This service handles item pickup from ANY input source (keyboard 'g', mouse right-click)
and ensures all pickup-related checks happen consistently:
- Victory triggers (Ruby Heart)
- Quest items
- Inventory management
- Portal spawning

By centralizing pickup logic, we prevent bugs where a feature works
for keyboard input but not mouse input (or vice versa).
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PickupResult:
    """Result of a pickup attempt.
    
    Attributes:
        success: Whether pickup succeeded
        item_name: Name of picked up item
        victory_triggered: Ruby Heart picked up (spawns portal)
        inventory_full: Pickup failed due to full inventory
        no_items: No items at player location
        messages: List of message dictionaries to display
    """
    success: bool = False
    item_name: Optional[str] = None
    victory_triggered: bool = False
    inventory_full: bool = False
    no_items: bool = False
    messages: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.messages is None:
            self.messages = []


class PickupService:
    """Service for handling all item pickup logic.
    
    This is the single source of truth for pickup mechanics.
    All input methods (keyboard 'g', mouse right-click) should use this service.
    """
    
    def __init__(self, state_manager):
        """Initialize pickup service.
        
        Args:
            state_manager: The game's state manager
        """
        self.state_manager = state_manager
    
    def execute_pickup(self, source: str = "keyboard") -> PickupResult:
        """Execute a pickup action at player's current location.
        
        This is the ONLY place pickup logic should exist.
        Call this from keyboard 'g' handler, right-click handler, or any other input source.
        
        Args:
            source: Input source ("keyboard", "mouse", "other") - for debugging
            
        Returns:
            PickupResult with success status and side effects
        """
        from game_states import GameStates
        from message_builder import MessageBuilder as MB
        from components.component_registry import ComponentType
        
        result = PickupResult()
        
        player = self.state_manager.state.player
        if not player:
            logger.error("No player found for pickup")
            return result
        
        entities = self.state_manager.state.entities
        game_map = self.state_manager.state.game_map
        message_log = self.state_manager.state.message_log
        
        logger.debug(f"Pickup attempt at ({player.x}, {player.y}) via {source}")
        print(f">>> PickupService: Pickup at ({player.x}, {player.y}) via {source}")
        
        # Find items at player's location
        items_at_location = [
            entity for entity in entities
            if entity.x == player.x and entity.y == player.y and hasattr(entity, 'item') and entity.item
        ]
        
        if not items_at_location:
            result.no_items = True
            result.messages.append({"message": MB.info("There is nothing here to pick up.")})
            logger.debug("No items at player location")
            return result
        
        # Pick up the first item (TODO: implement item selection menu if multiple items)
        item = items_at_location[0]
        result.item_name = item.name
        
        logger.info(f"Attempting to pick up: {item.name} via {source}")
        print(f">>> PickupService: Attempting pickup: {item.name}")
        
        # Check if player has inventory
        inventory = player.get_component_optional(ComponentType.INVENTORY)
        if not inventory:
            result.messages.append({"message": MB.failure(f"{player.name} cannot pick up items!")})
            logger.warning(f"Player has no inventory component")
            return result
        
        # Attempt to add to inventory
        pickup_results = inventory.add_item(item)
        
        # Process results
        for pickup_result in pickup_results:
            msg = pickup_result.get('message')
            if msg:
                result.messages.append({"message": msg})
            
            # Check if item was successfully added
            if pickup_result.get('item_added'):
                result.success = True
                entities.remove(item)
                logger.info(f"Successfully picked up: {item.name}")
                print(f">>> PickupService: Pickup successful: {item.name}")
                
                # ===================================================================
                # POST-PICKUP CHECKS (Phase 5: Victory Trigger, Quest Items, etc.)
                # ===================================================================
                
                # Check if this item triggers victory (Ruby Heart in Phase 5)
                if hasattr(item, 'triggers_victory') and item.triggers_victory:
                    print(f">>> PickupService: VICTORY TRIGGER detected for {item.name}!")
                    logger.info(f"=== PICKUP_SERVICE: Victory trigger for {item.name}")
                    
                    result.victory_triggered = True
                    
                    # Spawn portal and transition to RUBY_HEART_OBTAINED state
                    from victory_manager import get_victory_manager
                    victory_mgr = get_victory_manager()
                    
                    if victory_mgr.handle_ruby_heart_pickup(player, entities, game_map, message_log):
                        logger.info("=== PICKUP_SERVICE: Victory sequence initiated, portal spawned")
                        print(f">>> PickupService: Portal spawned successfully!")
                        
                        # Transition to RUBY_HEART_OBTAINED state
                        self.state_manager.set_game_state(GameStates.RUBY_HEART_OBTAINED)
                    else:
                        logger.error("=== PICKUP_SERVICE: Victory sequence FAILED")
                        print(f">>> PickupService: ERROR - Portal spawn failed!")
                
                break  # Only pick up one item
            
            # Check if inventory was full
            if 'Inventory is full' in str(msg):
                result.inventory_full = True
        
        return result


# Singleton instance
_pickup_service = None


def get_pickup_service(state_manager=None):
    """Get the global pickup service instance.
    
    Args:
        state_manager: State manager (required on first call)
        
    Returns:
        PickupService instance
    """
    global _pickup_service
    if _pickup_service is None:
        if state_manager is None:
            raise ValueError("state_manager required to initialize PickupService")
        _pickup_service = PickupService(state_manager)
    return _pickup_service

