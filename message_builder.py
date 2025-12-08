"""Message Builder - Centralized message creation with consistent formatting.

This module provides a MessageBuilder class that standardizes message creation
across the codebase. Instead of scattering Message() calls with hardcoded colors,
use MessageBuilder methods for consistent formatting and colors.

Usage:
    
    # Combat messages
    results.append({"message": MB.combat("You hit the Orc for 10 damage!")})
    
    # Item messages
    results.append({"message": MB.item_pickup("You pick up the Sword!")})
    
    # System messages
    results.append({"message": MB.system("Game saved successfully.")})
"""

from typing import Tuple
from game_messages import Message


class MessageBuilder:
    """Factory class for creating consistently formatted game messages.
    
    This class provides categorized methods for creating messages with
    standardized colors and formatting. Using these methods ensures
    visual consistency across the game.
    
    Color Scheme:
        - Combat: White (255, 255, 255)
        - Damage dealt: Red (255, 100, 100)
        - Critical hits: Gold (255, 215, 0)
        - Misses: Gray (180, 180, 180)
        - Healing: Light green (100, 255, 100)
        - Item pickup: Blue (0, 0, 255)
        - Item use: Cyan (0, 255, 255)
        - Item equipped: Light yellow (255, 255, 100)
        - Equipment effects: Gold (255, 215, 0)
        - System: White (255, 255, 255)
        - Success: Green (0, 255, 0)
        - Failure: Red (255, 0, 0)
        - Warning: Yellow (255, 255, 0)
        - Info: Light cyan (200, 200, 255)
        - Death: Dark red (255, 30, 30)
        - Level up: Bright yellow (255, 255, 0)
        - XP gain: Gold (255, 215, 0)
    """
    
    # Color constants for consistency
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    LIGHT_RED = (255, 100, 100)
    DARK_RED = (255, 30, 30)
    GREEN = (0, 255, 0)
    LIGHT_GREEN = (100, 255, 100)
    BLUE = (0, 0, 255)
    LIGHT_BLUE = (200, 200, 255)
    CYAN = (0, 255, 255)
    YELLOW = (255, 255, 0)
    LIGHT_YELLOW = (255, 255, 100)
    GOLD = (255, 215, 0)
    ORANGE = (255, 165, 0)
    GRAY = (180, 180, 180)
    LIGHT_GRAY = (200, 200, 200)
    DARK_GRAY = (128, 128, 128)
    PURPLE = (200, 100, 255)
    
    # === Combat Messages ===
    
    @staticmethod
    def combat(text: str) -> Message:
        """Standard combat message (white).
        
        Args:
            text: Message text
            
        Returns:
            Message object
            
        Example:
            MB.combat("You attack the Orc for 8 damage!")
        """
        return Message(text, MessageBuilder.WHITE)
    
    @staticmethod
    def combat_hit(text: str) -> Message:
        """Combat hit message (light red for emphasis).
        
        Args:
            text: Message text
            
        Returns:
            Message object
            
        Example:
            MB.combat_hit("You strike the Orc for 12 damage!")
        """
        return Message(text, MessageBuilder.LIGHT_RED)
    
    @staticmethod
    def combat_critical(text: str) -> Message:
        """Critical hit message (gold).
        
        Args:
            text: Message text
            
        Returns:
            Message object
            
        Example:
            MB.combat_critical("CRITICAL HIT! You strike the Orc for 24 damage!")
        """
        return Message(text, MessageBuilder.GOLD)
    
    @staticmethod
    def combat_miss(text: str) -> Message:
        """Combat miss message (gray).
        
        Args:
            text: Message text
            
        Returns:
            Message object
            
        Example:
            MB.combat_miss("You attack the Orc - MISS!")
        """
        return Message(text, MessageBuilder.GRAY)
    
    @staticmethod
    def combat_dodge(text: str) -> Message:
        """Combat dodge message (light cyan) - Phase 8.
        
        Used when an attack is dodged due to high evasion.
        More positive tone than combat_miss (defender succeeded).
        
        Args:
            text: Message text
            
        Returns:
            Message object
            
        Example:
            MB.combat_dodge("The Wraith attacks but you dodge nimbly!")
        """
        return Message(text, (150, 220, 255))  # Light cyan
    
    @staticmethod
    def combat_fumble(text: str) -> Message:
        """Combat fumble message (light gray).
        
        Args:
            text: Message text
            
        Returns:
            Message object
            
        Example:
            MB.combat_fumble("FUMBLE! You attack the Orc - complete miss!")
        """
        return Message(text, MessageBuilder.LIGHT_GRAY)
    
    @staticmethod
    def combat_momentum(text: str) -> Message:
        """Combat momentum/speed bonus message (cyan).
        
        Used for showing speed bonus buildup during combat.
        
        Args:
            text: Message text
            
        Returns:
            Message object
            
        Example:
            MB.combat_momentum("🔥 Momentum building: 75% bonus attack chance!")
        """
        return Message(text, MessageBuilder.CYAN)
    
    @staticmethod
    def combat_bonus_attack(text: str) -> Message:
        """Bonus attack trigger message (gold).
        
        Used when speed bonus triggers an extra attack.
        
        Args:
            text: Message text
            
        Returns:
            Message object
            
        Example:
            MB.combat_bonus_attack("⚡ [BONUS ATTACK] Speed bonus triggers an extra attack!")
        """
        return Message(text, MessageBuilder.GOLD)

    @staticmethod
    def combat_monster_bonus_attack(text: str) -> Message:
        """Monster bonus attack message (muted yellow/orange).
        
        Used when a monster's speed bonus triggers an extra attack.
        Less flashy than player bonus attacks.
        
        Args:
            text: Message text
            
        Returns:
            Message object
            
        Example:
            MB.combat_monster_bonus_attack("⚡ The Orc Chieftain lashes out with a bonus strike!")
        """
        return Message(text, MessageBuilder.ORANGE)
    
    # === Healing & HP Messages ===
    
    @staticmethod
    def healing(text: str) -> Message:
        """Healing message (light green).
        
        Args:
            text: Message text
            
        Returns:
            Message object
            
        Example:
            MB.healing("You heal for 15 HP!")
        """
        return Message(text, MessageBuilder.LIGHT_GREEN)
    
    @staticmethod
    def death(text: str) -> Message:
        """Death message (dark red).
        
        Args:
            text: Message text
            
        Returns:
            Message object
            
        Example:
            MB.death("You died! Press any key to return to the main menu.")
        """
        return Message(text, MessageBuilder.DARK_RED)
    
    # === Item Messages ===
    
    @staticmethod
    def item_pickup(text: str) -> Message:
        """Item pickup message (blue).
        
        Args:
            text: Message text
            
        Returns:
            Message object
            
        Example:
            MB.item_pickup("You pick up the Longsword!")
        """
        return Message(text, MessageBuilder.BLUE)
    
    @staticmethod
    def item_drop(text: str) -> Message:
        """Item drop message (yellow).
        
        Args:
            text: Message text
            
        Returns:
            Message object
            
        Example:
            MB.item_drop("You dropped the Dagger.")
        """
        return Message(text, MessageBuilder.YELLOW)
    
    @staticmethod
    def item_use(text: str) -> Message:
        """Item use message (cyan).
        
        Args:
            text: Message text
            
        Returns:
            Message object
            
        Example:
            MB.item_use("You use the Healing Potion!")
        """
        return Message(text, MessageBuilder.CYAN)
    
    @staticmethod
    def item_equipped(text: str) -> Message:
        """Item equipped message (light yellow).
        
        Args:
            text: Message text
            
        Returns:
            Message object
            
        Example:
            MB.item_equipped("You equip the Plate Mail!")
        """
        return Message(text, MessageBuilder.LIGHT_YELLOW)
    
    @staticmethod
    def item_unequipped(text: str) -> Message:
        """Item unequipped message (light yellow).
        
        Args:
            text: Message text
            
        Returns:
            Message object
            
        Example:
            MB.item_unequipped("You unequip the Shield.")
        """
        return Message(text, MessageBuilder.LIGHT_YELLOW)
    
    @staticmethod
    def item_effect(text: str) -> Message:
        """Item effect message (gold).
        
        Args:
            text: Message text
            
        Returns:
            Message object
            
        Example:
            MB.item_effect("Your weapon glows with power! (+1 damage)")
        """
        return Message(text, MessageBuilder.GOLD)
    
    @staticmethod
    def item_charge(text: str) -> Message:
        """Wand charge message (light blue).
        
        Args:
            text: Message text
            
        Returns:
            Message object
            
        Example:
            MB.item_charge("The wand glows. (3 charges remaining)")
        """
        return Message(text, MessageBuilder.LIGHT_BLUE)
    
    # === Spell Messages ===
    
    @staticmethod
    def spell_cast(text: str) -> Message:
        """Spell cast message (purple).
        
        Args:
            text: Message text
            
        Returns:
            Message object
            
        Example:
            MB.spell_cast("You conjure a blazing fireball!")
        """
        return Message(text, MessageBuilder.PURPLE)
    
    @staticmethod
    def spell_effect(text: str) -> Message:
        """Spell effect message (light blue).
        
        Args:
            text: Message text
            
        Returns:
            Message object
            
        Example:
            MB.spell_effect("The fireball explodes, dealing 18 damage!")
        """
        return Message(text, MessageBuilder.LIGHT_BLUE)
    
    @staticmethod
    def spell_fail(text: str) -> Message:
        """Spell failure message (gray).
        
        Args:
            text: Message text
            
        Returns:
            Message object
            
        Example:
            MB.spell_fail("There is nothing to target there.")
        """
        return Message(text, MessageBuilder.GRAY)
    
    # === Status & System Messages ===
    
    @staticmethod
    def status_effect(text: str) -> Message:
        """Status effect message (cyan).
        
        Args:
            text: Message text
            
        Returns:
            Message object
            
        Example:
            MB.status_effect("You are now invisible! (10 turns)")
        """
        return Message(text, MessageBuilder.CYAN)
    
    @staticmethod
    def level_up(text: str) -> Message:
        """Level up message (bright yellow).
        
        Args:
            text: Message text
            
        Returns:
            Message object
            
        Example:
            MB.level_up("You reached level 5!")
        """
        return Message(text, MessageBuilder.YELLOW)
    
    @staticmethod
    def xp_gain(text: str) -> Message:
        """XP gain message (gold).
        
        Args:
            text: Message text
            
        Returns:
            Message object
            
        Example:
            MB.xp_gain("You gain 35 XP!")
        """
        return Message(text, MessageBuilder.GOLD)
    
    @staticmethod
    def system(text: str) -> Message:
        """System message (white).
        
        Args:
            text: Message text
            
        Returns:
            Message object
            
        Example:
            MB.system("Game saved successfully.")
        """
        return Message(text, MessageBuilder.WHITE)
    
    @staticmethod
    def success(text: str) -> Message:
        """Success message (green).
        
        Args:
            text: Message text
            
        Returns:
            Message object
            
        Example:
            MB.success("Quest completed!")
        """
        return Message(text, MessageBuilder.GREEN)
    
    @staticmethod
    def failure(text: str) -> Message:
        """Failure message (red).
        
        Args:
            text: Message text
            
        Returns:
            Message object
            
        Example:
            MB.failure("You cannot do that!")
        """
        return Message(text, MessageBuilder.RED)
    
    @staticmethod
    def warning(text: str) -> Message:
        """Warning message (yellow).
        
        Args:
            text: Message text
            
        Returns:
            Message object
            
        Example:
            MB.warning("You cannot carry any more, your inventory is full.")
        """
        return Message(text, MessageBuilder.YELLOW)
    
    @staticmethod
    def info(text: str) -> Message:
        """Info message (light blue).
        
        Args:
            text: Message text
            
        Returns:
            Message object
            
        Example:
            MB.info("You entered level 2 of the dungeon.")
        """
        return Message(text, MessageBuilder.LIGHT_BLUE)
    
    # === Custom Color ===
    
    @staticmethod
    def custom(text: str, color: Tuple[int, int, int]) -> Message:
        """Create message with custom color.
        
        Args:
            text: Message text
            color: RGB tuple (r, g, b) where each value is 0-255
            
        Returns:
            Message object
            
        Example:
            MB.custom("Special message!", (255, 128, 64))
        """
        return Message(text, color)


# Convenient alias for shorter imports
MB = MessageBuilder

