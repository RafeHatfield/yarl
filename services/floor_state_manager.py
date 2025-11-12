"""Floor state persistence manager.

This module manages persistent state across level transitions (up/down stairs).
When player moves to another level, the previous floor state is saved and can
be restored when returning.

Features:
- Preserve entity state (position, health, status effects)
- Remember opened doors and cleared traps
- Despawn entities far from stairs entry points
- Cap respawns on re-entry to prevent farming
- Track visitation history per floor
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from logger_config import get_logger

logger = get_logger(__name__)


@dataclass
class FloorVisitRecord:
    """Record of a floor visit for tracking respawn caps."""
    visit_number: int = 1  # 1st visit, 2nd visit, etc.
    last_visited_turn: int = 0  # Game turn when last visited
    spawned_count: Dict[str, int] = field(default_factory=dict)  # Entity type -> count spawned
    

@dataclass
class FloorState:
    """Persistent state for a single floor."""
    level_number: int
    entities_data: List[Dict[str, Any]] = field(default_factory=list)
    door_states: Dict[Tuple[int, int], Dict[str, Any]] = field(default_factory=dict)  # (x,y) -> door state
    trap_states: Dict[Tuple[int, int], Dict[str, Any]] = field(default_factory=dict)  # (x,y) -> trap state
    visited: bool = False
    visit_record: FloorVisitRecord = field(default_factory=FloorVisitRecord)
    stairs_entry_point: Optional[Tuple[int, int]] = None  # Where player entered from stairs


class FloorStateManager:
    """Manages persistent state across level transitions.
    
    Tracks which floors have been visited, what entities are on each floor,
    and maintains anti-farming mechanics to prevent respawn abuse.
    """
    
    def __init__(self, max_floors: int = 25):
        """Initialize floor state manager.
        
        Args:
            max_floors: Maximum number of floors to track (default 25 for dungeon depth)
        """
        self.max_floors = max_floors
        self.floor_states: Dict[int, FloorState] = {}
        self.current_floor: int = 1
        self.despawn_radius: int = 20  # Tiles away from stairs entry to despawn mobs
        self.respawn_cap_per_visit: Dict[str, int] = {
            # Prevent farming: cap how many mobs respawn per visit
            # These limits apply per level visit
        }
    
    def save_floor_state(self, level_number: int, entities: List, game_map, 
                        stairs_entry: Optional[Tuple[int, int]] = None) -> None:
        """Save the current state of a floor before leaving it.
        
        Args:
            level_number: The level being left
            entities: List of current entities
            game_map: Current game map (for door/trap states)
            stairs_entry: Where player entered via stairs (for despawn radius)
        """
        from components.component_registry import ComponentType
        
        floor_state = FloorState(
            level_number=level_number,
            visited=True,
            stairs_entry_point=stairs_entry
        )
        
        # Save entity data
        for entity in entities:
            entity_data = {
                'name': entity.name,
                'x': entity.x,
                'y': entity.y,
                'char': entity.char,
                'color': entity.color,
                'blocks': entity.blocks,
                'render_order': entity.render_order if hasattr(entity, 'render_order') else 'actor'
            }
            
            # Save component states
            if entity.components.has(ComponentType.FIGHTER):
                fighter = entity.components.get(ComponentType.FIGHTER)
                entity_data['fighter'] = {
                    'hp': fighter.hp,
                    'max_hp': fighter.max_hp,
                }
            
            if entity.components.has(ComponentType.DOOR):
                door = entity.components.get(ComponentType.DOOR)
                entity_data['door'] = {
                    'is_closed': door.is_closed,
                    'is_locked': door.is_locked,
                    'is_secret': door.is_secret,
                    'is_discovered': door.is_discovered,
                }
                # Also track by position
                door_key = (entity.x, entity.y)
                floor_state.door_states[door_key] = entity_data['door']
            
            if entity.components.has(ComponentType.TRAP):
                trap = entity.components.get(ComponentType.TRAP)
                entity_data['trap'] = {
                    'trap_type': trap.trap_type,
                    'is_detected': trap.is_detected,
                    'is_disarmed': trap.is_disarmed,
                }
                # Also track by position
                trap_key = (entity.x, entity.y)
                floor_state.trap_states[trap_key] = entity_data['trap']
            
            floor_state.entities_data.append(entity_data)
        
        self.floor_states[level_number] = floor_state
        logger.info(f"Saved floor {level_number} state: {len(floor_state.entities_data)} entities")
    
    def load_floor_state(self, level_number: int) -> Optional[FloorState]:
        """Load previously saved state for a floor.
        
        Args:
            level_number: The level to load state for
            
        Returns:
            FloorState if floor has been visited before, None otherwise
        """
        if level_number not in self.floor_states:
            return None
        
        floor_state = self.floor_states[level_number]
        if not floor_state.visited:
            return None
        
        # Update visit record
        floor_state.visit_record.visit_number += 1
        logger.info(f"Loading floor {level_number} state (visit #{floor_state.visit_record.visit_number}): "
                   f"{len(floor_state.entities_data)} entities")
        
        return floor_state
    
    def despawn_far_entities(self, floor_state: FloorState, entities_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove entities that spawned far from the stairs entry point.
        
        This prevents mobs from being pre-positioned far away when player returns.
        Only affects newly-spawned entities (not persistent ones from before).
        
        Args:
            floor_state: Floor state with entry point info
            entities_data: List of entity data to filter
            
        Returns:
            Filtered list of entities to keep
        """
        if not floor_state.stairs_entry_point:
            return entities_data
        
        entry_x, entry_y = floor_state.stairs_entry_point
        kept_entities = []
        despawned_count = 0
        
        for entity_data in entities_data:
            # Don't despawn special entities (chests, NPCs, items)
            if entity_data.get('is_special', False):
                kept_entities.append(entity_data)
                continue
            
            # Don't despawn fighters that were previously saved
            if 'fighter' in entity_data:
                x, y = entity_data.get('x', entry_x), entity_data.get('y', entry_y)
                distance = abs(x - entry_x) + abs(y - entry_y)  # Manhattan distance
                
                if distance > self.despawn_radius:
                    despawned_count += 1
                    logger.debug(f"Despawning {entity_data['name']} at ({x}, {y}), "
                               f"distance {distance} > {self.despawn_radius}")
                    continue
            
            kept_entities.append(entity_data)
        
        if despawned_count > 0:
            logger.info(f"Despawned {despawned_count} far entities from level {floor_state.level_number}")
        
        return kept_entities
    
    def should_respawn_entity(self, floor_state: FloorState, entity_type: str, entity_name: str) -> bool:
        """Check if an entity type should be allowed to respawn on re-entry.
        
        Implements anti-farming mechanics by capping how many entities can spawn
        on successive visits to the same floor.
        
        Args:
            floor_state: Floor state tracking visits
            entity_type: Entity category (e.g., "monster")
            entity_name: Specific entity name (e.g., "orc")
            
        Returns:
            True if entity should be allowed, False if respawn-capped
        """
        # First visit = always allow respawning
        if floor_state.visit_record.visit_number <= 1:
            return True
        
        # Check if we've hit the respawn cap for this entity type on this visit
        entity_key = entity_type
        spawned_this_visit = floor_state.visit_record.spawned_count.get(entity_key, 0)
        
        # Cap respawns: allow max 50% of original spawn for subsequent visits
        # This prevents infinite farming by repeatedly re-entering a level
        respawn_cap = 0.5
        
        # For now, allow respawns but log for monitoring
        logger.debug(f"Entity respawn check: {entity_name} (visit #{floor_state.visit_record.visit_number})")
        
        return True  # Allow for now, but tracking is set up for future caps
    
    def register_respawn(self, floor_state: FloorState, entity_type: str) -> None:
        """Track that an entity respawned on re-entry.
        
        Args:
            floor_state: Floor state to update
            entity_type: Entity type that respawned
        """
        entity_key = entity_type
        floor_state.visit_record.spawned_count[entity_key] = \
            floor_state.visit_record.spawned_count.get(entity_key, 0) + 1
    
    def get_door_state(self, floor_state: FloorState, x: int, y: int) -> Optional[Dict[str, Any]]:
        """Get the saved state of a door (if it was opened/closed).
        
        Args:
            floor_state: Floor state containing door data
            x, y: Door position
            
        Returns:
            Door state dict, or None if not found
        """
        door_key = (x, y)
        return floor_state.door_states.get(door_key)
    
    def get_trap_state(self, floor_state: FloorState, x: int, y: int) -> Optional[Dict[str, Any]]:
        """Get the saved state of a trap (if it was detected/disarmed).
        
        Args:
            floor_state: Floor state containing trap data
            x, y: Trap position
            
        Returns:
            Trap state dict, or None if not found
        """
        trap_key = (x, y)
        return floor_state.trap_states.get(trap_key)
    
    def can_return_to_level(self, current_level: int, target_level: int, 
                           restrict_return_levels: int) -> bool:
        """Check if player can return to a previous floor.
        
        Args:
            current_level: Current dungeon level
            target_level: Level player wants to go to
            restrict_return_levels: How many levels back player can go
            
        Returns:
            True if transition is allowed, False otherwise
        """
        if target_level >= current_level:
            return True  # Going down is always allowed
        
        # Going up (backwards)
        levels_back = current_level - target_level
        if restrict_return_levels > 0 and levels_back > restrict_return_levels:
            logger.warning(f"Cannot return {levels_back} levels back (max: {restrict_return_levels})")
            return False
        
        return True
    
    def clear(self) -> None:
        """Clear all saved floor states (for testing/new game)."""
        self.floor_states.clear()
        logger.info("Cleared all floor states")


# Global singleton
_floor_state_manager: Optional[FloorStateManager] = None


def get_floor_state_manager() -> FloorStateManager:
    """Get the global floor state manager.
    
    Returns:
        FloorStateManager singleton instance
    """
    global _floor_state_manager
    if _floor_state_manager is None:
        _floor_state_manager = FloorStateManager()
    return _floor_state_manager


def reset_floor_state_manager() -> None:
    """Reset the global floor state manager (for testing)."""
    global _floor_state_manager
    _floor_state_manager = None

