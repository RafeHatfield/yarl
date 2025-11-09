"""Monster action logging system for testing and debugging.

This module provides comprehensive logging of all monster actions when in testing mode,
including item usage, pickup, movement, combat, and equipment changes.

NOTE: Uses centralized logger_config for consistency with rest of system.
"""

from typing import Any, Dict, List, Optional
from config.testing_config import is_testing_mode
from components.component_registry import ComponentType
from logger_config import get_logger

# Get centralized monster logger
monster_logger = get_logger('monsters')


class MonsterActionLogger:
    """Centralized logging system for monster actions in testing mode."""
    
    @staticmethod
    def setup_logging():
        """DEPRECATED: Logging is now handled by logger_config.py.
        
        This method is kept for backward compatibility but does nothing.
        Monster actions are automatically logged to logs/rlike.log by the
        centralized logger_config system.
        """
        if is_testing_mode():
            print("🤖 Monster action logging enabled (via centralized logger_config)")
    
    @staticmethod
    def log_action_attempt(monster, action_type: str, details: str = ""):
        """Log when a monster attempts an action.
        
        Args:
            monster: Monster entity
            action_type: Type of action (e.g., "item_usage", "item_pickup", "movement")
            details: Additional details about the action
        """
        if not is_testing_mode():
            return
            
        # Ensure logging is set up
        MonsterActionLogger.setup_logging()
            
        monster_name = getattr(monster, 'name', 'Unknown Monster')
        location = f"({getattr(monster, 'x', '?')}, {getattr(monster, 'y', '?')})"
        
        message = f"{monster_name} at {location} attempts {action_type}"
        if details:
            message += f": {details}"
            
        monster_logger.info(message)
    
    @staticmethod
    def log_action_result(monster, action_type: str, success: bool, details: str = ""):
        """Log the result of a monster action.
        
        Args:
            monster: Monster entity
            action_type: Type of action
            success: Whether the action succeeded
            details: Additional details about the result
        """
        if not is_testing_mode():
            return
            
        # Ensure logging is set up
        MonsterActionLogger.setup_logging()
            
        monster_name = getattr(monster, 'name', 'Unknown Monster')
        location = f"({getattr(monster, 'x', '?')}, {getattr(monster, 'y', '?')})"
        result = "SUCCESS" if success else "FAILED"
        
        message = f"{monster_name} at {location} {action_type} {result}"
        if details:
            message += f": {details}"
            
        monster_logger.info(message)
    
    @staticmethod
    def log_item_usage(monster, item, target, success: bool, failure_mode: str = None):
        """Log monster item usage with detailed information.
        
        Args:
            monster: Monster using the item
            item: Item being used
            target: Target of the item usage
            success: Whether the usage succeeded
            failure_mode: Type of failure if unsuccessful
        """
        if not is_testing_mode():
            return
            
        monster_name = getattr(monster, 'name', 'Unknown Monster')
        item_name = getattr(item, 'name', 'Unknown Item')
        target_name = getattr(target, 'name', 'Unknown Target')
        
        if success:
            details = f"used {item_name} on {target_name}"
        else:
            details = f"failed to use {item_name} on {target_name}"
            if failure_mode:
                details += f" (failure: {failure_mode})"
        
        MonsterActionLogger.log_action_result(monster, "item_usage", success, details)
    
    @staticmethod
    def log_item_pickup(monster, item, success: bool, reason: str = None):
        """Log monster item pickup attempts.
        
        Args:
            monster: Monster attempting pickup
            item: Item being picked up
            success: Whether pickup succeeded
            reason: Reason for failure if unsuccessful
        """
        if not is_testing_mode():
            return
            
        item_name = getattr(item, 'name', 'Unknown Item')
        item_location = f"({getattr(item, 'x', '?')}, {getattr(item, 'y', '?')})"
        
        if success:
            details = f"picked up {item_name} from {item_location}"
        else:
            details = f"failed to pick up {item_name} from {item_location}"
            if reason:
                details += f" ({reason})"
        
        MonsterActionLogger.log_action_result(monster, "item_pickup", success, details)
    
    @staticmethod
    def log_equipment_change(monster, item, action: str):
        """Log monster equipment changes.
        
        Args:
            monster: Monster whose equipment changed
            item: Item being equipped/unequipped
            action: "equipped" or "unequipped"
        """
        if not is_testing_mode():
            return
            
        item_name = getattr(item, 'name', 'Unknown Item')
        details = f"{action} {item_name}"
        
        MonsterActionLogger.log_action_result(monster, "equipment_change", True, details)
    
    @staticmethod
    def log_inventory_change(monster, item, action: str):
        """Log monster inventory changes.
        
        Args:
            monster: Monster whose inventory changed
            item: Item being added/removed
            action: "added" or "removed"
        """
        if not is_testing_mode():
            return
            
        item_name = getattr(item, 'name', 'Unknown Item')
        inventory = monster.get_component_optional(ComponentType.INVENTORY)
        inventory_count = len(inventory.items) if inventory else 0
        details = f"{action} {item_name} (inventory: {inventory_count} items)"
        
        MonsterActionLogger.log_action_result(monster, "inventory_change", True, details)
    
    @staticmethod
    def log_turn_summary(monster, actions_taken: List[str]):
        """Log a summary of all actions taken by a monster in one turn.
        
        Args:
            monster: Monster that took the turn
            actions_taken: List of action descriptions
        """
        if not is_testing_mode():
            return
            
        # Ensure logging is set up
        MonsterActionLogger.setup_logging()
            
        monster_name = getattr(monster, 'name', 'Unknown Monster')
        location = f"({getattr(monster, 'x', '?')}, {getattr(monster, 'y', '?')})"
        
        if actions_taken:
            actions_str = ", ".join(actions_taken)
            message = f"{monster_name} at {location} turn complete: {actions_str}"
            monster_logger.info(message)  # Log actual actions at INFO level
        else:
            message = f"{monster_name} at {location} turn complete: no actions taken"
            monster_logger.debug(message)  # Log "no actions" at DEBUG level


# Logging will be initialized on first use


# Mock class for testing
class Mock:
    def __init__(self):
        self.items = []
