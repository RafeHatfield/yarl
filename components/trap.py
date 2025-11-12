"""Trap component for hazardous map features.

This module provides the Trap component that manages trap state, detection,
and triggering. Traps can be:
- Detected: Found via passive checks or search action
- Hidden: Not yet discovered by player
- Disarmed: Removed after discovery to prevent triggering

Trap effects include:
- Damage + Bleed (spike traps)
- Slow + Snare (web traps)
- Faction Alert (alarm plates)

Traps maintain extensible detection mechanics for future skill/item bonuses.
"""

from typing import Optional, List, TYPE_CHECKING
from enum import Enum
from logger_config import get_logger

if TYPE_CHECKING:
    from entity import Entity

logger = get_logger(__name__)


class TrapType(Enum):
    """Enumeration of trap types."""
    SPIKE_TRAP = "spike_trap"      # Damage + bleed
    WEB_TRAP = "web_trap"          # Slow + snare
    ALARM_PLATE = "alarm_plate"    # Alert nearby mobs


class Trap:
    """Represents a trap that can damage or hinder the player.
    
    A trap can be:
    - Hidden: Not yet detected by player
    - Detected: Found but not disarmed
    - Disarmed: Made safe and no longer triggers
    
    Attributes:
        owner: The Entity that owns this trap
        trap_type: Type of trap (SPIKE_TRAP, WEB_TRAP, ALARM_PLATE)
        is_detected: Whether the trap has been found
        is_disarmed: Whether the trap has been disarmed (safe)
        detectable: Whether this trap can be detected at all
        passive_detect_chance: Base chance to detect when stepping on trap (0.0-1.0)
        reveal_tags: Item/condition tags that auto-reveal this trap
        
    Spike Trap Attributes:
        spike_damage: Damage dealt on trigger
        spike_bleed_severity: Bleed status severity (0-2, higher = worse)
        spike_bleed_duration: Turns bleed lasts
        
    Web Trap Attributes:
        web_slow_severity: Slow penalty to apply (0-2, higher = worse)
        web_duration: Turns slow lasts
        
    Alarm Trap Attributes:
        alarm_faction: Faction tag to alert
        alarm_radius: Tiles to search for matching faction mobs
    """
    
    def __init__(
        self,
        trap_type: str = "spike_trap",
        detectable: bool = True,
        passive_detect_chance: float = 0.1,
        reveal_tags: Optional[List[str]] = None,
        # Spike attributes
        spike_damage: int = 5,
        spike_bleed_severity: int = 1,
        spike_bleed_duration: int = 3,
        # Web attributes
        web_slow_severity: int = 1,
        web_duration: int = 5,
        # Alarm attributes
        alarm_faction: str = "orc",
        alarm_radius: int = 8
    ):
        """Initialize a Trap component.
        
        Args:
            trap_type: Type of trap ("spike_trap", "web_trap", "alarm_plate")
            detectable: If False, trap cannot be detected by any means
            passive_detect_chance: Base chance to detect when stepping (0.0-1.0)
            reveal_tags: List of item/condition tags that auto-reveal
            spike_damage: Damage spike traps deal
            spike_bleed_severity: Bleed severity (0-2)
            spike_bleed_duration: Bleed duration in turns
            web_slow_severity: Slow severity (0-2)
            web_duration: Slow duration in turns
            alarm_faction: Faction to alert
            alarm_radius: Radius to search for faction mobs
        """
        self.owner: Optional['Entity'] = None
        
        # Base trap state
        self.trap_type: str = trap_type
        self.is_detected: bool = False
        self.is_disarmed: bool = False
        self.detectable: bool = detectable
        self.passive_detect_chance: float = max(0.0, min(1.0, passive_detect_chance))
        self.reveal_tags: List[str] = reveal_tags or []
        
        # Spike trap config
        self.spike_damage: int = spike_damage
        self.spike_bleed_severity: int = spike_bleed_severity
        self.spike_bleed_duration: int = spike_bleed_duration
        
        # Web trap config
        self.web_slow_severity: int = web_slow_severity
        self.web_duration: int = web_duration
        
        # Alarm trap config
        self.alarm_faction: str = alarm_faction
        self.alarm_radius: int = alarm_radius
    
    def can_be_detected(self) -> bool:
        """Check if this trap can be detected.
        
        Returns:
            True if detectable and not already detected, False otherwise
        """
        return self.detectable and not self.is_detected
    
    def detect(self, reason: str = "search") -> bool:
        """Mark the trap as detected.
        
        Args:
            reason: Why trap was detected ("passive", "search", "auto_item", etc.)
            
        Returns:
            True if trap was successfully detected, False if already detected/undetectable
        """
        if not self.detectable or self.is_detected:
            return False
        
        self.is_detected = True
        logger.info(f"Trap {self.trap_type} at ({self.owner.x}, {self.owner.y}) detected ({reason})")
        return True
    
    def disarm(self) -> bool:
        """Disarm the trap, making it safe and preventing trigger.
        
        Returns:
            True if successfully disarmed, False if already disarmed
        """
        if self.is_disarmed:
            return False
        
        self.is_disarmed = True
        logger.info(f"Trap {self.trap_type} at ({self.owner.x}, {self.owner.y}) disarmed")
        return True
    
    def check_auto_reveal(self, item_tags: List[str]) -> bool:
        """Check if player has item(s) that auto-reveal this trap.
        
        Args:
            item_tags: List of tags from items player has
            
        Returns:
            True if any reveal_tag matches player's items
        """
        for tag in self.reveal_tags:
            if tag in item_tags:
                return True
        return False
    
    def is_triggered(self) -> bool:
        """Check if trap will trigger when player steps on it.
        
        Trap triggers unless:
        - It's disarmed
        - It's detected (player can avoid it)
        
        Returns:
            True if trap should trigger, False otherwise
        """
        return not self.is_disarmed and not self.is_detected
    
    def get_visible_char(self) -> str:
        """Get the character to render for this trap.
        
        Undiscovered traps render as floor.
        Discovered traps show their type visually.
        Disarmed traps show neutralized appearance.
        
        Returns:
            Character to display ('.' for hidden, '^' for detected spike, etc.)
        """
        if not self.is_detected:
            return '.'  # Hidden as normal floor
        
        if self.is_disarmed:
            return 'x'  # Disarmed trap
        
        # Show trap type
        if self.trap_type == "spike_trap":
            return '^'
        elif self.trap_type == "web_trap":
            return 'w'
        elif self.trap_type == "alarm_plate":
            return '@'
        
        return '?'  # Unknown trap type
    
    def get_description(self) -> str:
        """Get player-facing description of trap state.
        
        Returns:
            Human-readable trap description
        """
        if self.is_disarmed:
            return f"a disarmed {self.trap_type}"
        
        if not self.is_detected:
            return f"a hidden trap"
        
        if self.trap_type == "spike_trap":
            return f"a spike trap ({self.spike_damage} damage, {self.spike_bleed_severity} bleed)"
        elif self.trap_type == "web_trap":
            return f"a web trap ({self.web_slow_severity} slow, {self.web_duration} turns)"
        elif self.trap_type == "alarm_plate":
            return f"an alarm plate (alerts {self.alarm_faction})"
        
        return f"a {self.trap_type}"
    
    def __repr__(self) -> str:
        """String representation of trap."""
        status = "disarmed" if self.is_disarmed else ("detected" if self.is_detected else "hidden")
        return f"<Trap {self.trap_type} ({status})>"

