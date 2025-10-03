"""Visual effects system for the game.

Provides visual feedback for combat, spells, and other actions.
Makes the game feel more responsive and 'juicy'.

Phase 1: Hit/Miss indicators
Phase 2: Area effects (Fireball)
Phase 3: Path effects (Lightning)
Phase 4: Special effects (Dragon Fart, etc.)
"""

import time
import tcod.libtcodpy as libtcodpy
from typing import List, Tuple, Optional


class VisualEffects:
    """Manages visual feedback effects for game actions."""
    
    # Effect colors
    HIT_COLOR = (255, 50, 50)           # Bright red
    CRITICAL_HIT_COLOR = (255, 255, 0)  # Bright yellow
    MISS_COLOR = (128, 128, 128)        # Grey
    FIREBALL_COLOR = (255, 100, 0)      # Orange
    LIGHTNING_COLOR = (255, 255, 100)   # Bright yellow
    DRAGON_FART_COLOR = (100, 200, 50)  # Sickly green
    
    # Effect characters
    HIT_CHAR = '!'
    CRITICAL_CHAR = '!!'
    MISS_CHAR = '-'
    FIREBALL_CHAR = '*'
    LIGHTNING_CHAR = '~'
    DRAGON_FART_CHAR = '%'
    
    # Timing (in seconds)
    HIT_DURATION = 0.12      # 120ms
    CRITICAL_DURATION = 0.20 # 200ms
    MISS_DURATION = 0.10     # 100ms
    AREA_DURATION = 0.25     # 250ms
    PATH_DURATION = 0.15     # 150ms
    
    @staticmethod
    def show_hit_effect(x: int, y: int, entity=None, is_critical: bool = False) -> None:
        """Show a hit effect on a target by flashing its color.
        
        Flashes the entity red (or yellow for crits) while keeping the
        original character visible. Much clearer than replacing with '!'.
        
        Args:
            x: X coordinate of target
            y: Y coordinate of target
            entity: The entity being hit (to preserve character)
            is_critical: Whether this was a critical hit
        """
        if is_critical:
            color = VisualEffects.CRITICAL_HIT_COLOR
            duration = VisualEffects.CRITICAL_DURATION
        else:
            color = VisualEffects.HIT_COLOR
            duration = VisualEffects.HIT_DURATION
        
        # Get the entity's character (or use a default if entity not provided)
        if entity:
            char = entity.char
        else:
            # Fallback: try to read what's at that position
            char = libtcodpy.console_get_char(0, x, y)
            if char == 0 or char == ord(' '):
                char = ord('*')  # Default if we can't determine
        
        # Flash the entity's character in the hit color
        libtcodpy.console_set_default_foreground(0, color)
        libtcodpy.console_put_char(0, x, y, char, libtcodpy.BKGND_NONE)
        libtcodpy.console_flush()
        
        # Wait for effect duration
        time.sleep(duration)
        
        # Effect will be cleared by next render cycle
    
    @staticmethod
    def show_miss_effect(x: int, y: int, entity=None) -> None:
        """Show a miss effect on a target location.
        
        Shows a brief grey '-' next to the entity to indicate a miss,
        without obscuring what's there.
        
        Args:
            x: X coordinate where attack missed
            y: Y coordinate where attack missed
            entity: The entity that was targeted (optional)
        """
        # For misses, we'll just show a brief grey character
        # You could also flash the entity grey if provided
        if entity:
            # Flash the entity grey to show the miss
            char = entity.char
        else:
            # Fallback: just show a miss indicator
            char = VisualEffects.MISS_CHAR
        
        libtcodpy.console_set_default_foreground(0, VisualEffects.MISS_COLOR)
        libtcodpy.console_put_char(0, x, y, char, libtcodpy.BKGND_NONE)
        libtcodpy.console_flush()
        
        # Wait for effect duration
        time.sleep(VisualEffects.MISS_DURATION)
        
        # Effect will be cleared by next render cycle
    
    @staticmethod
    def show_area_effect(
        tiles: List[Tuple[int, int]], 
        char: str = '*',
        color: Tuple[int, int, int] = None,
        duration: float = None
    ) -> None:
        """Show an area effect on multiple tiles.
        
        Used for Fireball, Dragon Fart, and other area spells.
        
        Args:
            tiles: List of (x, y) coordinates to show effect on
            char: Character to display (default: '*')
            color: RGB color tuple (default: fireball orange)
            duration: How long to show effect (default: 250ms)
        """
        if color is None:
            color = VisualEffects.FIREBALL_COLOR
        if duration is None:
            duration = VisualEffects.AREA_DURATION
        
        # Draw effect on all tiles
        libtcodpy.console_set_default_foreground(0, color)
        for x, y in tiles:
            libtcodpy.console_put_char(0, x, y, char, libtcodpy.BKGND_NONE)
        
        libtcodpy.console_flush()
        
        # Wait for effect duration
        time.sleep(duration)
        
        # Effect will be cleared by next render cycle
    
    @staticmethod
    def show_path_effect(
        start: Tuple[int, int],
        end: Tuple[int, int],
        char: str = '~',
        color: Tuple[int, int, int] = None,
        duration: float = None
    ) -> None:
        """Show a path effect from start to end.
        
        Used for Lightning and other projectile spells.
        
        Args:
            start: (x, y) starting coordinate
            end: (x, y) ending coordinate
            char: Character to display (default: '~')
            color: RGB color tuple (default: lightning yellow)
            duration: How long to show effect (default: 150ms)
        """
        if color is None:
            color = VisualEffects.LIGHTNING_COLOR
        if duration is None:
            duration = VisualEffects.PATH_DURATION
        
        # Calculate path using Bresenham's line algorithm (TCOD provides this)
        path_tiles = []
        libtcodpy.line_init(start[0], start[1], end[0], end[1])
        x, y = libtcodpy.line_step()
        while x is not None:
            path_tiles.append((x, y))
            x, y = libtcodpy.line_step()
        
        # Draw effect along path
        libtcodpy.console_set_default_foreground(0, color)
        for x, y in path_tiles:
            libtcodpy.console_put_char(0, x, y, char, libtcodpy.BKGND_NONE)
        
        libtcodpy.console_flush()
        
        # Wait for effect duration
        time.sleep(duration)
        
        # Effect will be cleared by next render cycle


# Convenience functions for common effects

def show_hit(x: int, y: int, entity=None, is_critical: bool = False) -> None:
    """Show a hit effect. Convenience wrapper.
    
    Args:
        x: X coordinate
        y: Y coordinate
        entity: The entity being hit (to preserve character)
        is_critical: Whether this was a critical hit
    """
    VisualEffects.show_hit_effect(x, y, entity, is_critical)


def show_miss(x: int, y: int, entity=None) -> None:
    """Show a miss effect. Convenience wrapper.
    
    Args:
        x: X coordinate
        y: Y coordinate
        entity: The entity targeted (optional)
    """
    VisualEffects.show_miss_effect(x, y, entity)


def show_fireball(tiles: List[Tuple[int, int]]) -> None:
    """Show a fireball explosion effect. Convenience wrapper."""
    VisualEffects.show_area_effect(
        tiles, 
        VisualEffects.FIREBALL_CHAR,
        VisualEffects.FIREBALL_COLOR
    )


def show_lightning(start: Tuple[int, int], end: Tuple[int, int]) -> None:
    """Show a lightning zap effect. Convenience wrapper."""
    VisualEffects.show_path_effect(
        start, 
        end,
        VisualEffects.LIGHTNING_CHAR,
        VisualEffects.LIGHTNING_COLOR
    )


def show_dragon_fart(tiles: List[Tuple[int, int]]) -> None:
    """Show a dragon fart gas cloud effect. Convenience wrapper."""
    VisualEffects.show_area_effect(
        tiles,
        VisualEffects.DRAGON_FART_CHAR,
        VisualEffects.DRAGON_FART_COLOR
    )

