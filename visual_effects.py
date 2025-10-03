"""Visual effects system for the game.

Provides visual feedback for combat, spells, and other actions.
Makes the game feel more responsive and 'juicy'.

ARCHITECTURE:
This module now uses a deferred rendering system. Effects are QUEUED
during action processing, then PLAYED during rendering after the screen
state is correct. This eliminates double-entity artifacts.

Phase 1: Hit/Miss indicators
Phase 2: Area effects (Fireball)
Phase 3: Path effects (Lightning)
Phase 4: Special effects (Dragon Fart, etc.)
"""

import time
import tcod.libtcodpy as libtcodpy
from typing import List, Tuple, Optional
from visual_effect_queue import get_effect_queue


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
        original character visible.
        
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
        
        # Get the entity's character
        if entity:
            char = entity.char
        else:
            char = libtcodpy.console_get_char(0, x, y)
            if char == 0 or char == ord(' '):
                char = ord('*')
        
        # Flash the entity's character in the hit color
        libtcodpy.console_set_default_foreground(0, color)
        libtcodpy.console_put_char(0, x, y, char, libtcodpy.BKGND_NONE)
        libtcodpy.console_flush()
        
        # Wait for effect duration
        time.sleep(duration)
        
        # Let the next render cycle clean up naturally
    
    @staticmethod
    def show_miss_effect(x: int, y: int, entity=None) -> None:
        """Show a miss effect on a target location (fumbles only).
        
        Shows a brief grey flash to indicate a critical miss/fumble.
        
        Args:
            x: X coordinate where attack missed
            y: Y coordinate where attack missed
            entity: The entity that was targeted (optional)
        """
        # Get character to display
        if entity:
            char = entity.char
        else:
            char = libtcodpy.console_get_char(0, x, y)
            if char == 0 or char == ord(' '):
                char = VisualEffects.MISS_CHAR
        
        # Flash grey
        libtcodpy.console_set_default_foreground(0, VisualEffects.MISS_COLOR)
        libtcodpy.console_put_char(0, x, y, char, libtcodpy.BKGND_NONE)
        libtcodpy.console_flush()
        
        # Wait for effect duration
        time.sleep(VisualEffects.MISS_DURATION)
        
        # Let the next render cycle clean up naturally
    
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
    """Queue a hit effect for deferred rendering.
    
    Instead of showing immediately, this queues the effect to be played
    during the render phase when screen state is correct.
    
    Args:
        x: X coordinate
        y: Y coordinate
        entity: The entity being hit (to preserve character)
        is_critical: Whether this was a critical hit
    """
    get_effect_queue().queue_hit(x, y, entity, is_critical)


def show_miss(x: int, y: int, entity=None) -> None:
    """Queue a miss effect for deferred rendering.
    
    Instead of showing immediately, this queues the effect to be played
    during the render phase when screen state is correct.
    
    Args:
        x: X coordinate
        y: Y coordinate
        entity: The entity targeted (optional)
    """
    get_effect_queue().queue_miss(x, y, entity)


def show_fireball(tiles: List[Tuple[int, int]]) -> None:
    """Queue a fireball explosion effect for deferred rendering."""
    get_effect_queue().queue_fireball(
        tiles,
        char=VisualEffects.FIREBALL_CHAR,
        color=VisualEffects.FIREBALL_COLOR,
        duration=VisualEffects.AREA_DURATION
    )


def show_lightning(path: List[Tuple[int, int]]) -> None:
    """Queue a lightning bolt effect for deferred rendering."""
    get_effect_queue().queue_lightning(
        path,
        char=VisualEffects.LIGHTNING_CHAR,
        color=VisualEffects.LIGHTNING_COLOR,
        duration=VisualEffects.PATH_DURATION
    )


def show_dragon_fart(tiles: List[Tuple[int, int]]) -> None:
    """Queue a dragon fart cone effect for deferred rendering."""
    get_effect_queue().queue_dragon_fart(
        tiles,
        char=VisualEffects.DRAGON_FART_CHAR,
        color=VisualEffects.DRAGON_FART_COLOR,
        duration=VisualEffects.AREA_DURATION
    )

