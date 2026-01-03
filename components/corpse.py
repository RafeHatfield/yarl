"""Corpse component for tracking raisable remains.

This module provides the CorpseComponent which marks entities as corpses
and tracks their raise/resurrection state. This prevents infinite raise loops
and enables safe Necromancer AI.

Architecture:
- CorpseComponent: Metadata for corpses (original monster, raise count, consumption)
- Attached by kill_monster() when monster dies
- Checked by raise_dead spell before resurrection

Design Decisions:
- Corpses are entities transformed in-place (not new entities)
- raise_count enforces max raises (default 1)
- consumed flag prevents re-targeting
- original_monster_id enables stat lookup without name parsing

Phase 20 Lifecycle:
- FRESH: Created on death, raisable, NOT explodable
- SPENT: Created on re-death of raised entity, explodable, NOT raisable  
- CONSUMED: Post-explosion/full-consumption, inert
"""

from typing import Optional
from dataclasses import dataclass
from enum import Enum, auto


class CorpseState(Enum):
    """Lifecycle state for corpses (Phase 20).
    
    States:
        FRESH: Newly dead, can be raised, cannot be exploded
        SPENT: Already raised once and died again, can be exploded, cannot be raised
        CONSUMED: Fully consumed (exploded or max raises), inert
    """
    FRESH = auto()
    SPENT = auto()
    CONSUMED = auto()


@dataclass
class CorpseComponent:
    """Component marking an entity as a raisable corpse.
    
    Attached to entities when they die via kill_monster().
    Tracks resurrection state to prevent infinite raise loops.
    
    Attributes:
        original_monster_id: Original monster type ID (e.g., "orc", "troll")
        death_turn: Turn number when entity died (for decay mechanics)
        raise_count: Number of times this corpse has been raised
        max_raises: Maximum times corpse can be raised (default 1)
        consumed: True if corpse has been used/raised and is no longer targetable
        raised_by_name: Name of entity that raised this corpse (for tracking)
    
    Examples:
        >>> # Create corpse component when monster dies
        >>> corpse = CorpseComponent(
        ...     original_monster_id="orc",
        ...     death_turn=42,
        ...     raise_count=0,
        ...     max_raises=1,
        ...     consumed=False
        ... )
        >>> 
        >>> # Check if corpse can be raised
        >>> corpse.can_be_raised()
        True
        >>> 
        >>> # Consume corpse on raise
        >>> corpse.consume("Necromancer")
        >>> corpse.can_be_raised()
        False
    """
    original_monster_id: str
    death_turn: int = 0
    raise_count: int = 0
    max_raises: int = 1
    consumed: bool = False
    raised_by_name: Optional[str] = None
    corpse_state: CorpseState = CorpseState.FRESH  # Phase 20
    corpse_id: Optional[str] = None  # Phase 20: lineage tracking
    
    # Owner reference (set by Entity when component is attached)
    owner: Optional['Entity'] = None
    
    def can_be_raised(self) -> bool:
        """Check if this corpse is eligible for resurrection.
        
        Phase 20: Now enforces FRESH state.
        
        Returns:
            True if corpse can be raised, False otherwise
        """
        return (
            self.corpse_state == CorpseState.FRESH and
            not self.consumed and 
            self.raise_count < self.max_raises
        )
    
    def can_raise(self) -> bool:
        """Alias for can_be_raised() (Phase 20)."""
        return self.can_be_raised()
    
    def can_explode(self) -> bool:
        """Check if this corpse can be exploded (Phase 20).
        
        Returns:
            True if corpse state is SPENT
        """
        return self.corpse_state == CorpseState.SPENT
    
    def mark_spent(self) -> None:
        """Mark corpse as SPENT (Phase 20: raised and died again)."""
        self.corpse_state = CorpseState.SPENT
    
    def mark_consumed(self) -> None:
        """Mark corpse as CONSUMED (Phase 20: exploded or fully used)."""
        self.corpse_state = CorpseState.CONSUMED
        self.consumed = True
    
    def consume(self, raiser_name: Optional[str] = None) -> None:
        """Mark corpse as consumed/raised.
        
        Increments raise count and marks as consumed if at max raises.
        
        Args:
            raiser_name: Name of entity raising this corpse (optional tracking)
        """
        self.raise_count += 1
        self.raised_by_name = raiser_name
        
        # Mark consumed if at max raises
        if self.raise_count >= self.max_raises:
            self.mark_consumed()
    
    def __repr__(self) -> str:
        return (
            f"CorpseComponent(id={self.original_monster_id}, "
            f"raises={self.raise_count}/{self.max_raises}, "
            f"state={self.corpse_state.name}, "
            f"consumed={self.consumed})"
        )

