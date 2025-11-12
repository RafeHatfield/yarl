"""Faction engine for managing faction-aware room behaviors.

This module implements:
- Hostility override application when entering special rooms
- Behavior modifier application to AI components
- Per-room faction relationship management
- Telemetry for faction interaction tracking
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from logger_config import get_logger

logger = get_logger(__name__)


@dataclass
class HostilityOverride:
    """Temporary hostility override for a faction in a room."""
    faction: str
    target_factions: List[str]  # Factions to attack/interact with
    behavior: str  # "attack", "ignore", "flee", "ally"
    room_tag: str  # Room where this applies
    original_hostility: Optional[Dict[str, Any]] = None  # Store original for restoration


@dataclass
class BehaviorModifier:
    """Behavior modification applied to an entity."""
    entity_id: int
    monster_id: str  # Type of monster
    modifications: Dict[str, Any]  # {param: value}
    room_tag: str
    original_values: Optional[Dict[str, Any]] = None  # Store originals for restoration


class FactionEngine:
    """Engine for managing faction-aware behaviors in special rooms."""
    
    def __init__(self):
        """Initialize faction engine."""
        self.active_overrides: Dict[int, HostilityOverride] = {}  # entity_id -> override
        self.active_mods: Dict[int, BehaviorModifier] = {}  # entity_id -> mods
        self.room_histories: Dict[str, Dict[str, Any]] = {}  # room_tag -> history
    
    def apply_hostility_override(self, entity_id: int, faction: str, 
                                override_config: Dict[str, List[str]], 
                                room_tag: str) -> bool:
        """Apply hostility override to an entity in a special room.
        
        Args:
            entity_id: Unique entity ID
            faction: Entity's faction
            override_config: Hostility matrix from room config
            room_tag: Tag for this room
            
        Returns:
            True if override was applied
        """
        if faction not in override_config:
            return False
        
        target_factions = override_config[faction]
        
        override = HostilityOverride(
            faction=faction,
            target_factions=target_factions,
            behavior="attack",  # Default to aggressive in faction rooms
            room_tag=room_tag
        )
        
        self.active_overrides[entity_id] = override
        
        logger.info(f"Hostility override applied to entity {entity_id} ({faction}): "
                   f"will attack {target_factions} in room '{room_tag}'")
        
        self._record_telemetry(room_tag, {
            'event': 'hostility_override_applied',
            'entity_id': entity_id,
            'faction': faction,
            'target_factions': target_factions,
        })
        
        return True
    
    def apply_behavior_mods(self, entity_id: int, monster_id: str, 
                           mods_config: Dict[str, Any], 
                           room_tag: str) -> bool:
        """Apply behavior modifications to an entity.
        
        Args:
            entity_id: Unique entity ID
            monster_id: Monster type (e.g., "orc", "troll")
            mods_config: Behavior modifications for this monster type
            room_tag: Tag for this room
            
        Returns:
            True if mods were applied
        """
        if not mods_config:
            return False
        
        mod = BehaviorModifier(
            entity_id=entity_id,
            monster_id=monster_id,
            modifications=dict(mods_config),
            room_tag=room_tag
        )
        
        self.active_mods[entity_id] = mod
        
        logger.info(f"Behavior mods applied to entity {entity_id} ({monster_id}) "
                   f"in room '{room_tag}': {list(mods_config.keys())}")
        
        self._record_telemetry(room_tag, {
            'event': 'behavior_mods_applied',
            'entity_id': entity_id,
            'monster_id': monster_id,
            'mods': list(mods_config.keys()),
        })
        
        return True
    
    def get_hostility_override(self, entity_id: int) -> Optional[HostilityOverride]:
        """Get active hostility override for an entity.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            HostilityOverride or None
        """
        return self.active_overrides.get(entity_id)
    
    def get_behavior_mods(self, entity_id: int) -> Optional[Dict[str, Any]]:
        """Get active behavior mods for an entity.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            Dict of {parameter: value} or None
        """
        mod = self.active_mods.get(entity_id)
        return mod.modifications if mod else None
    
    def remove_overrides_for_entity(self, entity_id: int) -> None:
        """Remove all active overrides for an entity (e.g., on death or room exit).
        
        Args:
            entity_id: Entity ID
        """
        if entity_id in self.active_overrides:
            override = self.active_overrides.pop(entity_id)
            logger.debug(f"Removed hostility override for entity {entity_id}")
        
        if entity_id in self.active_mods:
            mod = self.active_mods.pop(entity_id)
            logger.debug(f"Removed behavior mods for entity {entity_id}")
    
    def remove_all_for_room(self, room_tag: str) -> int:
        """Remove all overrides for a specific room (e.g., on room leave).
        
        Args:
            room_tag: Room tag
            
        Returns:
            Number of overrides removed
        """
        removed = 0
        
        # Remove hostility overrides
        to_remove = [eid for eid, ovr in self.active_overrides.items() 
                    if ovr.room_tag == room_tag]
        for eid in to_remove:
            self.active_overrides.pop(eid)
            removed += 1
        
        # Remove behavior mods
        to_remove = [eid for eid, mod in self.active_mods.items() 
                    if mod.room_tag == room_tag]
        for eid in to_remove:
            self.active_mods.pop(eid)
            removed += 1
        
        if removed > 0:
            logger.info(f"Removed {removed} faction overrides for room '{room_tag}'")
        
        return removed
    
    def should_attack_faction(self, entity_id: int, target_faction: str) -> bool:
        """Check if entity should attack target faction (with overrides considered).
        
        Args:
            entity_id: Attacker entity ID
            target_faction: Faction of potential target
            
        Returns:
            True if should attack (hostility override says so)
        """
        override = self.active_overrides.get(entity_id)
        if override:
            return target_faction in override.target_factions
        
        return False  # Use default logic if no override
    
    def get_behavior_mod_value(self, entity_id: int, parameter: str, 
                              default: Any = None) -> Any:
        """Get a specific behavior mod value for an entity.
        
        Args:
            entity_id: Entity ID
            parameter: Behavior parameter (e.g., "door_priority")
            default: Default value if not found
            
        Returns:
            Modified value or default
        """
        mod = self.active_mods.get(entity_id)
        if mod and parameter in mod.modifications:
            return mod.modifications[parameter]
        
        return default
    
    def _record_telemetry(self, room_tag: str, event: Dict[str, Any]) -> None:
        """Record telemetry event for monitoring.
        
        Args:
            room_tag: Room tag
            event: Event data
        """
        if room_tag not in self.room_histories:
            self.room_histories[room_tag] = {
                'events': [],
                'active_overrides': 0,
                'active_mods': 0,
            }
        
        self.room_histories[room_tag]['events'].append(event)
        self.room_histories[room_tag]['active_overrides'] = len(
            [o for o in self.active_overrides.values() if o.room_tag == room_tag]
        )
        self.room_histories[room_tag]['active_mods'] = len(
            [m for m in self.active_mods.values() if m.room_tag == room_tag]
        )
    
    def get_telemetry(self, room_tag: Optional[str] = None) -> Dict[str, Any]:
        """Get telemetry data for monitoring.
        
        Args:
            room_tag: Specific room, or None for all
            
        Returns:
            Telemetry data
        """
        if room_tag:
            return self.room_histories.get(room_tag, {})
        
        return self.room_histories
    
    def get_stats(self) -> Dict[str, int]:
        """Get current statistics.
        
        Returns:
            Dict with counts of active overrides/mods
        """
        return {
            'total_active_overrides': len(self.active_overrides),
            'total_active_mods': len(self.active_mods),
            'rooms_with_overrides': len(self.room_histories),
        }
    
    def clear(self) -> None:
        """Clear all state (for testing or new game)."""
        self.active_overrides.clear()
        self.active_mods.clear()
        self.room_histories.clear()
        logger.info("Faction engine cleared")


# Global singleton
_faction_engine: Optional[FactionEngine] = None


def get_faction_engine() -> FactionEngine:
    """Get the global faction engine instance.
    
    Returns:
        FactionEngine singleton
    """
    global _faction_engine
    if _faction_engine is None:
        _faction_engine = FactionEngine()
    return _faction_engine


def reset_faction_engine() -> None:
    """Reset the global faction engine (for testing)."""
    global _faction_engine
    _faction_engine = None

