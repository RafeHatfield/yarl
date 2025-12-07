"""Speed Bonus Tracker component for ratcheting attack speed system.

This module implements a momentum-based bonus attack mechanic. Instead of
simply granting bonus attacks at fixed intervals, the system builds up
"momentum" through consecutive attacks, creating a more dynamic feel.

The ratcheting system works as follows:
- Each attack increments an internal counter
- Chance of bonus attack = counter * speed_bonus_ratio
- When chance >= 1.0: bonus is guaranteed and counter resets
- When chance < 1.0: RNG roll determines bonus; if successful, counter does NOT reset
- Counter only resets when the threshold (1.0) is hit or exceeded

Example with 25% speed bonus:
- Attack 1: 1 * 0.25 = 0.25 (25% chance, roll RNG)
- Attack 2: 2 * 0.25 = 0.50 (50% chance, roll RNG)
- Attack 3: 3 * 0.25 = 0.75 (75% chance, roll RNG)
- Attack 4: 4 * 0.25 = 1.00 (100% chance, guaranteed bonus, counter resets)

If an early RNG roll succeeds (e.g., at attack 2), the player gets a bonus
attack but the counter does NOT reset, so they still build toward the
guaranteed bonus at attack 4.

Phase 5 additions:
- Equipment-based speed bonuses (dagger, boots, ring)
- Temporary speed boosts from potions (override base during effect)
- Dynamic ratio updates via set_bonus_ratio() and set_temporary_bonus()
"""

import random
from typing import Optional, Callable, List
from logger_config import get_logger

logger = get_logger(__name__)


class SpeedBonusTracker:
    """Tracks attack momentum and determines bonus attack opportunities.
    
    This component manages the ratcheting bonus attack system where players
    can earn extra attacks based on their speed bonus ratio. The system
    creates a momentum feel by accumulating attack "pressure" until a
    guaranteed bonus is triggered.
    
    Attributes:
        speed_bonus_ratio (float): Effective speed bonus (base + equipment - debuff or temporary override)
        attack_counter (int): Current number of attacks in the ratchet cycle
        owner: The entity that owns this component (set by Entity when registered)
        _base_ratio (float): Base speed ratio (from character/monster stats)
        _equipment_ratio (float): Speed bonus from equipped items
        _temporary_ratio (float): Temporary override from potions (0.0 = not active)
        _debuff_ratio (float): Speed penalty from debuffs (positive value = penalty)
        _temporary_sources (list): Names of sources providing temporary bonus
    
    Example:
        >>> tracker = SpeedBonusTracker(speed_bonus_ratio=0.25)
        >>> tracker.roll_for_bonus_attack()  # 25% chance
        False
        >>> tracker.roll_for_bonus_attack()  # 50% chance
        False
        >>> tracker.roll_for_bonus_attack()  # 75% chance
        True  # Got lucky!
        >>> tracker.attack_counter  # Counter NOT reset on early bonus
        3
        >>> tracker.roll_for_bonus_attack()  # 100% - guaranteed!
        True
        >>> tracker.attack_counter  # Counter resets after guaranteed bonus
        0
    """
    
    def __init__(
        self, 
        speed_bonus_ratio: float = 0.0,
        rng: Optional[Callable[[], float]] = None
    ):
        """Initialize a SpeedBonusTracker.
        
        Args:
            speed_bonus_ratio: Speed bonus as a ratio (e.g., 0.25 for +25% speed).
                Must be >= 0.0. Values > 1.0 guarantee at least one bonus per attack.
            rng: Optional RNG function that returns float in [0.0, 1.0).
                Defaults to random.random(). Useful for testing.
        
        Raises:
            ValueError: If speed_bonus_ratio is negative
        """
        if speed_bonus_ratio < 0.0:
            raise ValueError(
                f"speed_bonus_ratio must be >= 0.0, got {speed_bonus_ratio}"
            )
        
        # Track separate sources of speed bonus (Phase 5)
        self._base_ratio = speed_bonus_ratio  # From character/monster base stats
        self._equipment_ratio = 0.0  # From equipped items (additive)
        self._temporary_ratio = 0.0  # From potions (overrides when active)
        self._debuff_ratio = 0.0  # Phase 7: Speed penalty from debuffs (additive penalty)
        self._equipment_sources: List[str] = []  # Names of items providing speed bonus
        
        self.attack_counter = 0
        self._rng = rng if rng is not None else random.random
        self.owner = None  # Will be set by Entity when component is registered
    
    @property
    def speed_bonus_ratio(self) -> float:
        """Get the effective speed bonus ratio.
        
        If a temporary bonus (potion) is active, it OVERRIDES the base+equipment.
        Otherwise, returns base + equipment bonuses - debuff penalties.
        
        Phase 7: Debuffs are applied additively. If equipment gives +25% and
        debuff applies -25%, the net result is 0%. Can go negative but clamped to 0.
        
        Returns:
            float: Effective speed bonus ratio (minimum 0.0)
        """
        if self._temporary_ratio > 0.0:
            return self._temporary_ratio
        # Phase 7: Apply debuff penalty (clamped to 0 minimum)
        net_ratio = self._base_ratio + self._equipment_ratio - self._debuff_ratio
        return max(0.0, net_ratio)
    
    @speed_bonus_ratio.setter
    def speed_bonus_ratio(self, value: float) -> None:
        """Set the base speed bonus ratio directly.
        
        This sets the base ratio only. Use add_equipment_bonus() for equipment
        and set_temporary_bonus() for potion effects.
        
        Args:
            value: New base speed bonus ratio
        """
        if value < 0.0:
            raise ValueError(f"speed_bonus_ratio must be >= 0.0, got {value}")
        self._base_ratio = value
    
    def add_equipment_bonus(self, bonus: float, source_name: str = "item") -> None:
        """Add a speed bonus from equipped item.
        
        Phase 5: Called when equipping an item with speed_bonus attribute.
        
        Args:
            bonus: Speed bonus to add (e.g., 0.25 for +25%)
            source_name: Name of the item providing the bonus
        """
        self._equipment_ratio += bonus
        self._equipment_sources.append(source_name)
        logger.debug(f"SpeedBonusTracker: Added {bonus:.0%} from {source_name}, "
                    f"total equipment bonus: {self._equipment_ratio:.0%}")
    
    def remove_equipment_bonus(self, bonus: float, source_name: str = "item") -> None:
        """Remove a speed bonus from unequipped item.
        
        Phase 5: Called when unequipping an item with speed_bonus attribute.
        
        Args:
            bonus: Speed bonus to remove (e.g., 0.25 for +25%)
            source_name: Name of the item that was providing the bonus
        """
        self._equipment_ratio = max(0.0, self._equipment_ratio - bonus)
        if source_name in self._equipment_sources:
            self._equipment_sources.remove(source_name)
        logger.debug(f"SpeedBonusTracker: Removed {bonus:.0%} from {source_name}, "
                    f"total equipment bonus: {self._equipment_ratio:.0%}")
    
    def set_temporary_bonus(self, bonus: float) -> None:
        """Set a temporary speed bonus (from potion).
        
        Phase 5: Temporary bonuses OVERRIDE base+equipment while active.
        Call clear_temporary_bonus() when the effect expires.
        
        Args:
            bonus: Temporary speed bonus (e.g., 0.50 for +50%)
        """
        self._temporary_ratio = bonus
        logger.debug(f"SpeedBonusTracker: Set temporary bonus to {bonus:.0%}")
    
    def clear_temporary_bonus(self) -> None:
        """Clear the temporary speed bonus.
        
        Phase 5: Called when a potion effect expires. Reverts to base+equipment.
        """
        logger.debug(f"SpeedBonusTracker: Cleared temporary bonus (was {self._temporary_ratio:.0%})")
        self._temporary_ratio = 0.0
    
    def has_temporary_bonus(self) -> bool:
        """Check if a temporary bonus is active.
        
        Returns:
            bool: True if temporary bonus (potion) is active
        """
        return self._temporary_ratio > 0.0
    
    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 7: DEBUFF MANAGEMENT
    # ─────────────────────────────────────────────────────────────────────────
    
    def add_debuff(self, penalty: float, source_name: str = "debuff") -> None:
        """Add a speed penalty from a debuff effect.
        
        Phase 7: Called when a debuff (like Potion of Tar) is applied.
        Debuffs stack additively with each other and are subtracted from
        the total bonus.
        
        Args:
            penalty: Speed penalty to add (e.g., 0.25 for -25% speed)
            source_name: Name of the debuff source for logging
        """
        self._debuff_ratio += penalty
        logger.debug(f"SpeedBonusTracker: Added {penalty:.0%} debuff from {source_name}, "
                    f"total debuff: {self._debuff_ratio:.0%}")
    
    def remove_debuff(self, penalty: float, source_name: str = "debuff") -> None:
        """Remove a speed penalty when a debuff expires.
        
        Phase 7: Called when a debuff effect ends.
        
        Args:
            penalty: Speed penalty to remove (e.g., 0.25 for -25% speed)
            source_name: Name of the debuff source for logging
        """
        self._debuff_ratio = max(0.0, self._debuff_ratio - penalty)
        logger.debug(f"SpeedBonusTracker: Removed {penalty:.0%} debuff from {source_name}, "
                    f"total debuff: {self._debuff_ratio:.0%}")
    
    def has_debuff(self) -> bool:
        """Check if any speed debuff is active.
        
        Returns:
            bool: True if any debuff penalty is active
        """
        return self._debuff_ratio > 0.0
    
    def get_debuff_ratio(self) -> float:
        """Get the current total debuff penalty.
        
        Returns:
            float: Total debuff penalty (0.0 if no debuffs)
        """
        return self._debuff_ratio
    
    def get_bonus_sources(self) -> str:
        """Get a human-readable description of speed bonus sources.
        
        Phase 5/7: Used for character sheet display.
        
        Returns:
            str: Description like "Boots + Ring" or "Potion active" or "Debuffed!"
        """
        if self._temporary_ratio > 0.0:
            return "Potion active"
        
        parts = []
        if self._equipment_sources:
            parts.append(" + ".join(self._equipment_sources))
        elif self._base_ratio > 0.0:
            parts.append("Base")
        
        # Phase 7: Show debuff status
        if self._debuff_ratio > 0.0:
            parts.append(f"Debuffed (-{self._debuff_ratio:.0%})")
        
        return " | ".join(parts) if parts else ""
    
    @property
    def current_chance(self) -> float:
        """Calculate the current chance for a bonus attack.
        
        This is the chance that would apply if roll_for_bonus_attack()
        were called right now (after incrementing the counter).
        
        Returns:
            float: Probability of bonus attack (0.0 to 1.0+)
        """
        return (self.attack_counter + 1) * self.speed_bonus_ratio
    
    def roll_for_bonus_attack(self) -> bool:
        """Roll for a bonus attack opportunity.
        
        Call this method each time the owning entity performs an attack.
        The method:
        1. Increments the attack counter
        2. Calculates chance based on counter * speed_bonus_ratio
        3. If chance >= 1.0: returns True and resets counter (guaranteed bonus)
        4. If chance < 1.0: rolls RNG; if success returns True (no reset)
        
        The key mechanic: early bonus hits do NOT reset the counter, allowing
        the player to continue building toward the guaranteed bonus.
        
        Returns:
            bool: True if a bonus attack is earned, False otherwise
        """
        # No bonus attacks with 0% speed bonus
        if self.speed_bonus_ratio <= 0.0:
            return False
        
        # Increment attack counter
        self.attack_counter += 1
        
        # Calculate current bonus chance
        chance = self.attack_counter * self.speed_bonus_ratio
        
        logger.debug(
            f"SpeedBonusTracker: attack #{self.attack_counter}, "
            f"chance = {chance:.2%} (ratio={self.speed_bonus_ratio})"
        )
        
        # Check for guaranteed bonus (threshold reached)
        if chance >= 1.0:
            logger.debug(
                f"SpeedBonusTracker: Guaranteed bonus! "
                f"Resetting counter from {self.attack_counter}"
            )
            self.attack_counter = 0
            return True
        
        # Roll for early bonus
        roll = self._rng()
        if roll < chance:
            logger.debug(
                f"SpeedBonusTracker: Early bonus! "
                f"Roll {roll:.3f} < {chance:.3f}. Counter stays at {self.attack_counter}"
            )
            return True
        
        logger.debug(
            f"SpeedBonusTracker: No bonus. "
            f"Roll {roll:.3f} >= {chance:.3f}"
        )
        return False
    
    def reset(self) -> None:
        """Manually reset the attack counter.
        
        Call this when the combat momentum is broken, such as when:
        - Player moves (instead of attacking)
        - Player uses an item (drinks potion, reads scroll)
        - Combat ends (no enemies nearby)
        - Player takes a non-attack action
        
        This ensures the ratcheting bonus is tied to sustained combat
        rather than accumulating across separate encounters.
        """
        if self.attack_counter > 0:
            logger.debug(
                f"SpeedBonusTracker: Manual reset, "
                f"counter was {self.attack_counter}"
            )
        self.attack_counter = 0
    
    def __repr__(self) -> str:
        """Return string representation for debugging."""
        debuff_str = f", debuff={self._debuff_ratio}" if self._debuff_ratio > 0 else ""
        return (
            f"SpeedBonusTracker("
            f"ratio={self.speed_bonus_ratio}, "
            f"counter={self.attack_counter}, "
            f"next_chance={self.current_chance:.2%}{debuff_str})"
        )
