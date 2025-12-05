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
"""

import random
from typing import Optional, Callable
from logger_config import get_logger

logger = get_logger(__name__)


class SpeedBonusTracker:
    """Tracks attack momentum and determines bonus attack opportunities.
    
    This component manages the ratcheting bonus attack system where players
    can earn extra attacks based on their speed bonus ratio. The system
    creates a momentum feel by accumulating attack "pressure" until a
    guaranteed bonus is triggered.
    
    Attributes:
        speed_bonus_ratio (float): Speed bonus as a ratio (e.g., 0.25 = +25% speed)
        attack_counter (int): Current number of attacks in the ratchet cycle
        owner: The entity that owns this component (set by Entity when registered)
    
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
        
        self.speed_bonus_ratio = speed_bonus_ratio
        self.attack_counter = 0
        self._rng = rng if rng is not None else random.random
        self.owner = None  # Will be set by Entity when component is registered
    
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
        return (
            f"SpeedBonusTracker("
            f"ratio={self.speed_bonus_ratio}, "
            f"counter={self.attack_counter}, "
            f"next_chance={self.current_chance:.2%})"
        )
