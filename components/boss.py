"""Boss component for unique boss encounter mechanics.

This component marks entities as bosses and provides special behavior:
- Phase tracking for multi-phase encounters
- Enrage mode when HP drops below threshold
- Dialogue triggers for personality
- Boss-specific metadata (name, type, abilities)

Usage:
    boss_comp = Boss(
        boss_name="Dragon Lord",
        enrage_threshold=0.5,  # Enrage at 50% HP
        max_phases=1
    )
    boss_entity.boss = boss_comp
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class Boss:
    """Component for boss monster mechanics.
    
    Bosses are special powerful enemies with unique behaviors:
    - Track combat phases (for multi-phase encounters)
    - Enrage when damaged (increased power/aggression)
    - Dialogue system for personality and taunts
    - Immunity to certain status effects
    
    Attributes:
        boss_name: Display name for the boss
        boss_type: Type identifier (e.g., "dragon", "demon", "undead")
        phase: Current phase of encounter (0-indexed)
        max_phases: Maximum number of phases
        enrage_threshold: HP percentage to trigger enrage (0.0-1.0)
        is_enraged: Whether boss is currently enraged
        enrage_damage_multiplier: Damage multiplier when enraged
        dialogue: Dialogue lines organized by trigger
        status_immunities: List of status effects boss is immune to
        defeated: Whether boss has been defeated (for achievements)
    """
    
    # Core identity
    boss_name: str
    boss_type: str = "generic"
    
    # Phase system
    phase: int = 0
    max_phases: int = 1
    
    # Enrage mechanic
    enrage_threshold: float = 0.5  # Enrage at 50% HP
    is_enraged: bool = False
    enrage_damage_multiplier: float = 1.5  # 50% more damage when enraged
    
    # Dialogue system
    dialogue: Dict[str, List[str]] = field(default_factory=dict)
    dialogue_used: Dict[str, bool] = field(default_factory=dict)  # Track what's been said
    
    # Status effect immunity
    status_immunities: List[str] = field(default_factory=list)
    
    # Victory tracking
    defeated: bool = False
    
    # Owner reference
    owner: Optional[object] = None
    
    def __post_init__(self):
        """Initialize boss component with default dialogue."""
        if not self.dialogue:
            self.dialogue = {
                "spawn": [f"You dare challenge {self.boss_name}?"],
                "hit": ["You'll pay for that!"],
                "enrage": [f"{self.boss_name} becomes enraged!"],
                "low_hp": ["This cannot be..."],
                "death": ["Impossible..."]
            }
        
        # Initialize dialogue tracking
        for category in self.dialogue.keys():
            if category not in self.dialogue_used:
                self.dialogue_used[category] = False
        
        # Default status immunities for bosses
        if not self.status_immunities:
            self.status_immunities = ["confusion", "slow"]  # Bosses resist confusion and slow
    
    def check_enrage(self, current_hp: int, max_hp: int) -> bool:
        """Check if boss should enter enrage mode.
        
        Args:
            current_hp: Boss's current HP
            max_hp: Boss's maximum HP
            
        Returns:
            True if boss just entered enrage mode (for triggering dialogue)
        """
        if self.is_enraged:
            return False  # Already enraged
        
        hp_percentage = current_hp / max_hp if max_hp > 0 else 0
        
        if hp_percentage <= self.enrage_threshold:
            self.is_enraged = True
            return True  # Just enraged!
        
        return False
    
    def advance_phase(self) -> bool:
        """Advance to next combat phase.
        
        Returns:
            True if phase advanced, False if already at max phase
        """
        if self.phase < self.max_phases - 1:
            self.phase += 1
            return True
        return False
    
    def get_dialogue(self, trigger: str, use_random: bool = True) -> Optional[str]:
        """Get dialogue line for a specific trigger.
        
        Args:
            trigger: Dialogue trigger category (e.g., "spawn", "hit", "enrage")
            use_random: If True, pick random line; if False, use first
            
        Returns:
            Dialogue string, or None if no dialogue for trigger
        """
        if trigger not in self.dialogue:
            return None
        
        lines = self.dialogue[trigger]
        if not lines:
            return None
        
        if use_random:
            from random import choice
            return choice(lines)
        else:
            return lines[0]
    
    def mark_dialogue_used(self, trigger: str) -> None:
        """Mark a dialogue trigger as used (for one-time dialogue).
        
        Args:
            trigger: Dialogue trigger to mark as used
        """
        self.dialogue_used[trigger] = True
    
    def has_used_dialogue(self, trigger: str) -> bool:
        """Check if dialogue trigger has been used.
        
        Args:
            trigger: Dialogue trigger to check
            
        Returns:
            True if dialogue has been used
        """
        return self.dialogue_used.get(trigger, False)
    
    def is_immune_to(self, status_effect: str) -> bool:
        """Check if boss is immune to a status effect.
        
        Args:
            status_effect: Name of status effect (e.g., "confusion", "slow")
            
        Returns:
            True if boss is immune
        """
        return status_effect.lower() in [s.lower() for s in self.status_immunities]
    
    def get_damage_multiplier(self) -> float:
        """Get current damage multiplier based on boss state.
        
        Returns:
            Damage multiplier (1.0 = normal, >1.0 = enraged)
        """
        if self.is_enraged:
            return self.enrage_damage_multiplier
        return 1.0
    
    def mark_defeated(self) -> None:
        """Mark boss as defeated (for achievements and statistics)."""
        self.defeated = True


def create_dragon_lord_boss() -> Boss:
    """Create Boss component for Dragon Lord.
    
    Returns:
        Configured Boss component for Dragon Lord
    """
    return Boss(
        boss_name="Dragon Lord",
        boss_type="dragon",
        enrage_threshold=0.5,
        enrage_damage_multiplier=1.5,
        dialogue={
            "spawn": [
                "A puny mortal dares enter my lair?",
                "You will make a fine addition to my hoard... as ash!",
                "Foolish creature. You should have stayed away."
            ],
            "hit": [
                "You dare strike me?!",
                "Insolent worm!",
                "That... actually hurt. Impressive."
            ],
            "enrage": [
                "ENOUGH! Feel my true wrath!",
                "You've angered me for the last time!",
                "Now you face the Dragon Lord's fury!"
            ],
            "low_hp": [
                "This... this cannot be!",
                "My scales... my invincible scales!",
                "How can a mere mortal..."
            ],
            "death": [
                "Impossible... defeated by... a mortal...",
                "My hoard... my precious hoard...",
                "I... am... the Dragon... Lord..."
            ]
        },
        status_immunities=["confusion", "slow", "fire"]  # Dragon immune to fire
    )


def create_demon_king_boss() -> Boss:
    """Create Boss component for Demon King.
    
    Returns:
        Configured Boss component for Demon King
    """
    return Boss(
        boss_name="Demon King",
        boss_type="demon",
        enrage_threshold=0.4,  # Enrages earlier (40%)
        enrage_damage_multiplier=1.75,  # More aggressive enrage
        dialogue={
            "spawn": [
                "Another soul for my collection.",
                "You seek death? I am happy to oblige.",
                "Kneel before the Demon King!"
            ],
            "hit": [
                "Your defiance amuses me.",
                "Pain is meaningless to me.",
                "I will make you suffer for that."
            ],
            "enrage": [
                "You try my patience! Witness TRUE power!",
                "I will tear your soul apart!",
                "Enough games. Die!"
            ],
            "low_hp": [
                "What... what sorcery is this?",
                "My demonic power... failing?",
                "You are stronger than you appear..."
            ],
            "death": [
                "Banished... by a mortal... inconceivable...",
                "I will return... this is not... over...",
                "The abyss... calls me back..."
            ]
        },
        status_immunities=["confusion", "slow", "curse", "poison"]  # Demon immunities
    )

