"""Ground hazard system for persistent area effects.

This module provides a system for managing hazardous ground effects left by
area-of-effect spells like Fireball and Dragon Fart. Hazards persist for
multiple turns, deal damage to entities, and provide visual feedback.

Architecture:
- GroundHazard: Individual hazard instance with type, damage, and duration
- GroundHazardManager: Manages all active hazards on the game map
- HazardType: Enumeration of different hazard types

Design Decisions:
- Damage applied once per turn at turn start (predictable, easy to understand)
- Damage decays over time (100% → 66% → 33%) to simulate fading effects
- No stacking - newest effect replaces old one to keep behavior simple
- Hazards are map-level, not entity-level, for clean separation of concerns
"""

from enum import Enum, auto
from typing import Optional, Tuple, Dict, List, Any
from dataclasses import dataclass


class HazardType(Enum):
    """Types of ground hazards that can be created.
    
    Each hazard type has different characteristics (damage, duration, visuals).
    """
    FIRE = auto()      # Left by Fireball spell
    POISON_GAS = auto() # Left by Dragon Fart spell
    # Future: ACID, ICE, LIGHTNING, etc.


@dataclass
class GroundHazard:
    """Represents a hazardous effect on a specific ground tile.
    
    Ground hazards are created by area-of-effect spells and persist for
    multiple turns. They damage entities that start their turn on the tile.
    Damage decays over time to simulate the hazard fading.
    
    Attributes:
        hazard_type (HazardType): Type of hazard (fire, poison gas, etc.)
        x (int): X coordinate of hazard
        y (int): Y coordinate of hazard
        base_damage (int): Initial damage per turn
        remaining_turns (int): Number of turns before hazard disappears
        max_duration (int): Total duration in turns (for decay calculation)
        source_name (str): Name of entity/spell that created this hazard
    
    Examples:
        >>> # Create a fire hazard from fireball
        >>> hazard = GroundHazard(
        ...     hazard_type=HazardType.FIRE,
        ...     x=10, y=15,
        ...     base_damage=10,
        ...     remaining_turns=3,
        ...     max_duration=3,
        ...     source_name="Fireball"
        ... )
        >>> 
        >>> # Calculate current damage (decays over time)
        >>> hazard.get_current_damage()  # Turn 1: 10 damage
        10
        >>> hazard.age_one_turn()
        >>> hazard.get_current_damage()  # Turn 2: 6 damage (66%)
        6
    """
    hazard_type: HazardType
    x: int
    y: int
    base_damage: int
    remaining_turns: int
    max_duration: int
    source_name: str = "Unknown"
    
    def get_current_damage(self) -> int:
        """Calculate current damage based on remaining duration.
        
        Damage decays linearly as the hazard ages:
        - 100% damage for turns remaining = max_duration
        - 66% damage for turns remaining = max_duration * 2/3
        - 33% damage for turns remaining = max_duration * 1/3
        - 0% damage when expired
        
        Returns:
            int: Current damage value (0 if expired)
        
        Examples:
            >>> hazard = GroundHazard(HazardType.FIRE, 0, 0, 9, 3, 3)
            >>> hazard.get_current_damage()
            9
            >>> hazard.remaining_turns = 2
            >>> hazard.get_current_damage()
            6
            >>> hazard.remaining_turns = 1
            >>> hazard.get_current_damage()
            3
        """
        if self.remaining_turns <= 0:
            return 0
        
        # Calculate decay percentage based on remaining turns
        decay_factor = self.remaining_turns / self.max_duration
        return int(self.base_damage * decay_factor)
    
    def age_one_turn(self) -> bool:
        """Age the hazard by one turn.
        
        Decrements the remaining turns counter. When it reaches 0,
        the hazard should be removed from the map.
        
        Returns:
            bool: True if hazard is still active, False if expired
        
        Examples:
            >>> hazard = GroundHazard(HazardType.FIRE, 0, 0, 10, 2, 3)
            >>> hazard.age_one_turn()
            True
            >>> hazard.remaining_turns
            1
            >>> hazard.age_one_turn()
            False
            >>> hazard.remaining_turns
            0
        """
        self.remaining_turns -= 1
        return self.remaining_turns > 0
    
    def is_expired(self) -> bool:
        """Check if the hazard has expired.
        
        Returns:
            bool: True if remaining_turns <= 0
        """
        return self.remaining_turns <= 0
    
    def get_visual_intensity(self) -> float:
        """Get the visual intensity for rendering (0.0 to 1.0).
        
        Visual intensity decreases as the hazard ages, providing
        feedback about how dangerous it still is.
        
        Returns:
            float: Intensity value between 0.0 (expired) and 1.0 (fresh)
        
        Examples:
            >>> hazard = GroundHazard(HazardType.FIRE, 0, 0, 10, 3, 3)
            >>> hazard.get_visual_intensity()
            1.0
            >>> hazard.remaining_turns = 1
            >>> hazard.get_visual_intensity()
            0.333...
        """
        if self.remaining_turns <= 0:
            return 0.0
        return self.remaining_turns / self.max_duration
    
    def get_color(self) -> Tuple[int, int, int]:
        """Get the base color for this hazard type.
        
        Returns:
            Tuple[int, int, int]: RGB color tuple
        
        Examples:
            >>> hazard = GroundHazard(HazardType.FIRE, 0, 0, 10, 3, 3)
            >>> hazard.get_color()
            (255, 100, 0)
            >>> hazard = GroundHazard(HazardType.POISON_GAS, 0, 0, 5, 4, 4)
            >>> hazard.get_color()
            (100, 200, 50)
        """
        if self.hazard_type == HazardType.FIRE:
            return (255, 100, 0)  # Bright orange-red
        elif self.hazard_type == HazardType.POISON_GAS:
            return (100, 200, 50)  # Sickly green
        else:
            return (128, 128, 128)  # Gray fallback


class GroundHazardManager:
    """Manages all active ground hazards on the game map.
    
    This class tracks hazards, ages them each turn, applies damage to entities,
    and provides queries for rendering and AI pathfinding.
    
    Attributes:
        hazards (Dict[Tuple[int, int], GroundHazard]): Active hazards by position
    
    Examples:
        >>> manager = GroundHazardManager()
        >>> hazard = GroundHazard(HazardType.FIRE, 5, 5, 10, 3, 3)
        >>> manager.add_hazard(hazard)
        >>> manager.has_hazard_at(5, 5)
        True
        >>> manager.get_hazard_at(5, 5).get_current_damage()
        10
    """
    
    def __init__(self):
        """Initialize an empty hazard manager."""
        self.hazards: Dict[Tuple[int, int], GroundHazard] = {}
    
    def add_hazard(self, hazard: GroundHazard) -> None:
        """Add a hazard to the manager.
        
        If a hazard already exists at the same position, it is replaced
        (no stacking of effects).
        
        Args:
            hazard (GroundHazard): The hazard to add
        
        Examples:
            >>> manager = GroundHazardManager()
            >>> fire = GroundHazard(HazardType.FIRE, 5, 5, 10, 3, 3)
            >>> manager.add_hazard(fire)
            >>> len(manager.hazards)
            1
        """
        pos = (hazard.x, hazard.y)
        self.hazards[pos] = hazard
    
    def get_hazard_at(self, x: int, y: int) -> Optional[GroundHazard]:
        """Get the hazard at a specific position.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
        
        Returns:
            Optional[GroundHazard]: The hazard at that position, or None
        
        Examples:
            >>> manager = GroundHazardManager()
            >>> fire = GroundHazard(HazardType.FIRE, 5, 5, 10, 3, 3)
            >>> manager.add_hazard(fire)
            >>> hazard = manager.get_hazard_at(5, 5)
            >>> hazard.base_damage
            10
            >>> manager.get_hazard_at(10, 10) is None
            True
        """
        return self.hazards.get((x, y))
    
    def has_hazard_at(self, x: int, y: int) -> bool:
        """Check if there's a hazard at a specific position.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
        
        Returns:
            bool: True if hazard exists at position
        
        Examples:
            >>> manager = GroundHazardManager()
            >>> manager.has_hazard_at(5, 5)
            False
            >>> fire = GroundHazard(HazardType.FIRE, 5, 5, 10, 3, 3)
            >>> manager.add_hazard(fire)
            >>> manager.has_hazard_at(5, 5)
            True
        """
        return (x, y) in self.hazards
    
    def remove_hazard_at(self, x: int, y: int) -> bool:
        """Remove a hazard at a specific position.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
        
        Returns:
            bool: True if a hazard was removed, False if none existed
        
        Examples:
            >>> manager = GroundHazardManager()
            >>> fire = GroundHazard(HazardType.FIRE, 5, 5, 10, 3, 3)
            >>> manager.add_hazard(fire)
            >>> manager.remove_hazard_at(5, 5)
            True
            >>> manager.remove_hazard_at(5, 5)
            False
        """
        pos = (x, y)
        if pos in self.hazards:
            del self.hazards[pos]
            return True
        return False
    
    def age_all_hazards(self) -> List[Tuple[int, int]]:
        """Age all hazards by one turn and remove expired ones.
        
        Should be called at the start of each game turn. Automatically
        removes hazards that have expired.
        
        Returns:
            List[Tuple[int, int]]: List of positions where hazards expired
        
        Examples:
            >>> manager = GroundHazardManager()
            >>> fire = GroundHazard(HazardType.FIRE, 5, 5, 10, 1, 3)
            >>> manager.add_hazard(fire)
            >>> expired = manager.age_all_hazards()
            >>> (5, 5) in expired
            True
            >>> manager.has_hazard_at(5, 5)
            False
        """
        expired_positions = []
        
        for pos, hazard in list(self.hazards.items()):
            if not hazard.age_one_turn():
                # Hazard expired
                expired_positions.append(pos)
                del self.hazards[pos]
        
        return expired_positions
    
    def get_all_hazards(self) -> List[GroundHazard]:
        """Get a list of all active hazards.
        
        Returns:
            List[GroundHazard]: List of all active hazards
        
        Examples:
            >>> manager = GroundHazardManager()
            >>> fire = GroundHazard(HazardType.FIRE, 5, 5, 10, 3, 3)
            >>> gas = GroundHazard(HazardType.POISON_GAS, 6, 6, 5, 4, 4)
            >>> manager.add_hazard(fire)
            >>> manager.add_hazard(gas)
            >>> len(manager.get_all_hazards())
            2
        """
        return list(self.hazards.values())
    
    def clear_all(self) -> None:
        """Remove all hazards from the manager.
        
        Useful for testing or level transitions.
        
        Examples:
            >>> manager = GroundHazardManager()
            >>> fire = GroundHazard(HazardType.FIRE, 5, 5, 10, 3, 3)
            >>> manager.add_hazard(fire)
            >>> manager.clear_all()
            >>> len(manager.hazards)
            0
        """
        self.hazards.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize hazards to dictionary for saving.
        
        Returns:
            Dict[str, Any]: Serializable dictionary representation
        
        Examples:
            >>> manager = GroundHazardManager()
            >>> fire = GroundHazard(HazardType.FIRE, 5, 5, 10, 3, 3, "Fireball")
            >>> manager.add_hazard(fire)
            >>> data = manager.to_dict()
            >>> data['hazards'][0]['x']
            5
        """
        return {
            'hazards': [
                {
                    'type': hazard.hazard_type.name,
                    'x': hazard.x,
                    'y': hazard.y,
                    'base_damage': hazard.base_damage,
                    'remaining_turns': hazard.remaining_turns,
                    'max_duration': hazard.max_duration,
                    'source_name': hazard.source_name
                }
                for hazard in self.hazards.values()
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GroundHazardManager':
        """Deserialize hazards from dictionary when loading.
        
        Args:
            data (Dict[str, Any]): Dictionary data from save file
        
        Returns:
            GroundHazardManager: New manager with loaded hazards
        
        Examples:
            >>> data = {
            ...     'hazards': [{
            ...         'type': 'FIRE',
            ...         'x': 5, 'y': 5,
            ...         'base_damage': 10,
            ...         'remaining_turns': 3,
            ...         'max_duration': 3,
            ...         'source_name': 'Fireball'
            ...     }]
            ... }
            >>> manager = GroundHazardManager.from_dict(data)
            >>> manager.has_hazard_at(5, 5)
            True
        """
        manager = cls()
        
        for hazard_data in data.get('hazards', []):
            hazard = GroundHazard(
                hazard_type=HazardType[hazard_data['type']],
                x=hazard_data['x'],
                y=hazard_data['y'],
                base_damage=hazard_data['base_damage'],
                remaining_turns=hazard_data['remaining_turns'],
                max_duration=hazard_data['max_duration'],
                source_name=hazard_data.get('source_name', 'Unknown')
            )
            manager.add_hazard(hazard)
        
        return manager
