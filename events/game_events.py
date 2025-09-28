"""Game-specific event definitions.

This module defines all the game-specific events that are used
throughout the roguelike game, including combat, movement,
inventory, and system events.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum, auto

from .core import Event, EventContext, EventPriority


class GameEventType(Enum):
    """Enumeration of game event types."""
    
    # Combat events
    COMBAT_ATTACK = "combat.attack"
    COMBAT_DAMAGE = "combat.damage"
    COMBAT_HEAL = "combat.heal"
    COMBAT_DEATH = "combat.death"
    COMBAT_LEVEL_UP = "combat.level_up"
    
    # Movement events
    MOVEMENT_MOVE = "movement.move"
    MOVEMENT_BLOCKED = "movement.blocked"
    MOVEMENT_TELEPORT = "movement.teleport"
    
    # Inventory events
    INVENTORY_PICKUP = "inventory.pickup"
    INVENTORY_DROP = "inventory.drop"
    INVENTORY_USE = "inventory.use"
    INVENTORY_EQUIP = "inventory.equip"
    INVENTORY_UNEQUIP = "inventory.unequip"
    
    # Level/Map events
    LEVEL_ENTER = "level.enter"
    LEVEL_EXIT = "level.exit"
    LEVEL_GENERATE = "level.generate"
    
    # Player events
    PLAYER_SPAWN = "player.spawn"
    PLAYER_DEATH = "player.death"
    PLAYER_LEVEL_UP = "player.level_up"
    PLAYER_STAT_CHANGE = "player.stat_change"
    
    # Entity events
    ENTITY_SPAWN = "entity.spawn"
    ENTITY_DESTROY = "entity.destroy"
    ENTITY_TRANSFORM = "entity.transform"
    
    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_PAUSE = "system.pause"
    SYSTEM_RESUME = "system.resume"
    SYSTEM_SAVE = "system.save"
    SYSTEM_LOAD = "system.load"
    
    # UI events
    UI_MENU_OPEN = "ui.menu_open"
    UI_MENU_CLOSE = "ui.menu_close"
    UI_DIALOG_OPEN = "ui.dialog_open"
    UI_DIALOG_CLOSE = "ui.dialog_close"
    UI_INPUT = "ui.input"


class GameEvent(Event):
    """Base class for all game events."""
    
    def __init__(self, event_type: GameEventType, data: Dict[str, Any] = None,
                 context: Optional[EventContext] = None):
        """Initialize game event.
        
        Args:
            event_type (GameEventType): Type of game event
            data (Dict[str, Any], optional): Event data
            context (EventContext, optional): Event context
        """
        super().__init__(context)
        self._event_type = event_type
        self.data = data or {}
    
    @property
    def event_type(self) -> str:
        """Get the event type identifier."""
        return self._event_type.value
    
    @property
    def game_event_type(self) -> GameEventType:
        """Get the game event type enum."""
        return self._event_type
    
    def validate(self) -> List[str]:
        """Validate the event data."""
        errors = []
        
        if not isinstance(self.data, dict):
            errors.append("Event data must be a dictionary")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary representation."""
        return {
            'event_type': self._event_type.value,
            'data': self.data,
            'context': {
                'source': self.context.source,
                'target': self.context.target,
                'timestamp': self.context.timestamp,
                'priority': self.context.priority.value,
                'metadata': self.context.metadata,
                'trace_id': self.context.trace_id,
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameEvent':
        """Create event from dictionary representation."""
        context_data = data.get('context', {})
        context = EventContext(
            source=context_data.get('source'),
            target=context_data.get('target'),
            timestamp=context_data.get('timestamp'),
            priority=EventPriority(context_data.get('priority', EventPriority.NORMAL.value)),
            metadata=context_data.get('metadata', {}),
            trace_id=context_data.get('trace_id')
        )
        
        event_type = GameEventType(data['event_type'])
        
        return cls(
            event_type=event_type,
            data=data.get('data', {}),
            context=context
        )


@dataclass
class CombatEvent(GameEvent):
    """Combat-related events."""
    
    attacker_id: Optional[str] = None
    target_id: Optional[str] = None
    damage: int = 0
    damage_type: str = "physical"
    weapon: Optional[str] = None
    critical_hit: bool = False
    
    def __init__(self, event_type: GameEventType, attacker_id: str = None,
                 target_id: str = None, damage: int = 0, damage_type: str = "physical",
                 weapon: str = None, critical_hit: bool = False,
                 context: Optional[EventContext] = None):
        """Initialize combat event."""
        data = {
            'attacker_id': attacker_id,
            'target_id': target_id,
            'damage': damage,
            'damage_type': damage_type,
            'weapon': weapon,
            'critical_hit': critical_hit,
        }
        super().__init__(event_type, data, context)
        
        self.attacker_id = attacker_id
        self.target_id = target_id
        self.damage = damage
        self.damage_type = damage_type
        self.weapon = weapon
        self.critical_hit = critical_hit
    
    def validate(self) -> List[str]:
        """Validate combat event data."""
        errors = super().validate()
        
        if self.damage < 0:
            errors.append("Damage cannot be negative")
        
        if not self.damage_type:
            errors.append("Damage type cannot be empty")
        
        return errors


@dataclass
class MovementEvent(GameEvent):
    """Movement-related events."""
    
    entity_id: Optional[str] = None
    from_x: int = 0
    from_y: int = 0
    to_x: int = 0
    to_y: int = 0
    blocked_by: Optional[str] = None
    
    def __init__(self, event_type: GameEventType, entity_id: str = None,
                 from_x: int = 0, from_y: int = 0, to_x: int = 0, to_y: int = 0,
                 blocked_by: str = None, context: Optional[EventContext] = None):
        """Initialize movement event."""
        data = {
            'entity_id': entity_id,
            'from_x': from_x,
            'from_y': from_y,
            'to_x': to_x,
            'to_y': to_y,
            'blocked_by': blocked_by,
        }
        super().__init__(event_type, data, context)
        
        self.entity_id = entity_id
        self.from_x = from_x
        self.from_y = from_y
        self.to_x = to_x
        self.to_y = to_y
        self.blocked_by = blocked_by


@dataclass
class InventoryEvent(GameEvent):
    """Inventory-related events."""
    
    entity_id: Optional[str] = None
    item_id: Optional[str] = None
    item_name: str = ""
    quantity: int = 1
    slot: Optional[str] = None
    
    def __init__(self, event_type: GameEventType, entity_id: str = None,
                 item_id: str = None, item_name: str = "", quantity: int = 1,
                 slot: str = None, context: Optional[EventContext] = None):
        """Initialize inventory event."""
        data = {
            'entity_id': entity_id,
            'item_id': item_id,
            'item_name': item_name,
            'quantity': quantity,
            'slot': slot,
        }
        super().__init__(event_type, data, context)
        
        self.entity_id = entity_id
        self.item_id = item_id
        self.item_name = item_name
        self.quantity = quantity
        self.slot = slot
    
    def validate(self) -> List[str]:
        """Validate inventory event data."""
        errors = super().validate()
        
        if self.quantity <= 0:
            errors.append("Quantity must be positive")
        
        return errors


@dataclass
class LevelEvent(GameEvent):
    """Level/Map-related events."""
    
    level_id: Optional[str] = None
    level_name: str = ""
    dungeon_level: int = 1
    player_id: Optional[str] = None
    
    def __init__(self, event_type: GameEventType, level_id: str = None,
                 level_name: str = "", dungeon_level: int = 1,
                 player_id: str = None, context: Optional[EventContext] = None):
        """Initialize level event."""
        data = {
            'level_id': level_id,
            'level_name': level_name,
            'dungeon_level': dungeon_level,
            'player_id': player_id,
        }
        super().__init__(event_type, data, context)
        
        self.level_id = level_id
        self.level_name = level_name
        self.dungeon_level = dungeon_level
        self.player_id = player_id


@dataclass
class PlayerEvent(GameEvent):
    """Player-specific events."""
    
    player_id: Optional[str] = None
    stat_name: str = ""
    old_value: Any = None
    new_value: Any = None
    level: int = 1
    experience: int = 0
    
    def __init__(self, event_type: GameEventType, player_id: str = None,
                 stat_name: str = "", old_value: Any = None, new_value: Any = None,
                 level: int = 1, experience: int = 0,
                 context: Optional[EventContext] = None):
        """Initialize player event."""
        data = {
            'player_id': player_id,
            'stat_name': stat_name,
            'old_value': old_value,
            'new_value': new_value,
            'level': level,
            'experience': experience,
        }
        super().__init__(event_type, data, context)
        
        self.player_id = player_id
        self.stat_name = stat_name
        self.old_value = old_value
        self.new_value = new_value
        self.level = level
        self.experience = experience


@dataclass
class EntityEvent(GameEvent):
    """Entity lifecycle events."""
    
    entity_id: Optional[str] = None
    entity_type: str = ""
    entity_name: str = ""
    x: int = 0
    y: int = 0
    
    def __init__(self, event_type: GameEventType, entity_id: str = None,
                 entity_type: str = "", entity_name: str = "",
                 x: int = 0, y: int = 0, context: Optional[EventContext] = None):
        """Initialize entity event."""
        data = {
            'entity_id': entity_id,
            'entity_type': entity_type,
            'entity_name': entity_name,
            'x': x,
            'y': y,
        }
        super().__init__(event_type, data, context)
        
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.entity_name = entity_name
        self.x = x
        self.y = y


@dataclass
class SystemEvent(GameEvent):
    """System-level events."""
    
    system_name: str = ""
    operation: str = ""
    success: bool = True
    error_message: str = ""
    
    def __init__(self, event_type: GameEventType, system_name: str = "",
                 operation: str = "", success: bool = True,
                 error_message: str = "", context: Optional[EventContext] = None):
        """Initialize system event."""
        data = {
            'system_name': system_name,
            'operation': operation,
            'success': success,
            'error_message': error_message,
        }
        super().__init__(event_type, data, context)
        
        self.system_name = system_name
        self.operation = operation
        self.success = success
        self.error_message = error_message


@dataclass
class UIEvent(GameEvent):
    """UI-related events."""
    
    ui_element: str = ""
    action: str = ""
    data_payload: Dict[str, Any] = field(default_factory=dict)
    
    def __init__(self, event_type: GameEventType, ui_element: str = "",
                 action: str = "", data_payload: Dict[str, Any] = None,
                 context: Optional[EventContext] = None):
        """Initialize UI event."""
        data_payload = data_payload or {}
        data = {
            'ui_element': ui_element,
            'action': action,
            'data_payload': data_payload,
        }
        super().__init__(event_type, data, context)
        
        self.ui_element = ui_element
        self.action = action
        self.data_payload = data_payload


# Convenience functions for creating common events

def create_combat_event(event_type: GameEventType, attacker_id: str = None,
                       target_id: str = None, damage: int = 0,
                       **kwargs) -> CombatEvent:
    """Create a combat event.
    
    Args:
        event_type (GameEventType): Combat event type
        attacker_id (str, optional): ID of attacking entity
        target_id (str, optional): ID of target entity
        damage (int): Amount of damage
        **kwargs: Additional arguments
        
    Returns:
        CombatEvent: Created combat event
    """
    return CombatEvent(event_type, attacker_id, target_id, damage, **kwargs)


def create_movement_event(event_type: GameEventType, entity_id: str = None,
                         from_pos: tuple = (0, 0), to_pos: tuple = (0, 0),
                         **kwargs) -> MovementEvent:
    """Create a movement event.
    
    Args:
        event_type (GameEventType): Movement event type
        entity_id (str, optional): ID of moving entity
        from_pos (tuple): Starting position (x, y)
        to_pos (tuple): Ending position (x, y)
        **kwargs: Additional arguments
        
    Returns:
        MovementEvent: Created movement event
    """
    return MovementEvent(event_type, entity_id, from_pos[0], from_pos[1],
                        to_pos[0], to_pos[1], **kwargs)


def create_inventory_event(event_type: GameEventType, entity_id: str = None,
                          item_id: str = None, item_name: str = "",
                          **kwargs) -> InventoryEvent:
    """Create an inventory event.
    
    Args:
        event_type (GameEventType): Inventory event type
        entity_id (str, optional): ID of entity
        item_id (str, optional): ID of item
        item_name (str): Name of item
        **kwargs: Additional arguments
        
    Returns:
        InventoryEvent: Created inventory event
    """
    return InventoryEvent(event_type, entity_id, item_id, item_name, **kwargs)


def create_player_event(event_type: GameEventType, player_id: str = None,
                       **kwargs) -> PlayerEvent:
    """Create a player event.
    
    Args:
        event_type (GameEventType): Player event type
        player_id (str, optional): ID of player
        **kwargs: Additional arguments
        
    Returns:
        PlayerEvent: Created player event
    """
    return PlayerEvent(event_type, player_id, **kwargs)


def create_system_event(event_type: GameEventType, system_name: str = "",
                       operation: str = "", success: bool = True,
                       **kwargs) -> SystemEvent:
    """Create a system event.
    
    Args:
        event_type (GameEventType): System event type
        system_name (str): Name of system
        operation (str): Operation being performed
        success (bool): Whether operation was successful
        **kwargs: Additional arguments
        
    Returns:
        SystemEvent: Created system event
    """
    return SystemEvent(event_type, system_name, operation, success, **kwargs)
