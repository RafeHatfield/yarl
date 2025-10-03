"""Visual Effect Queue System.

This module provides a deferred rendering system for visual effects.
Instead of displaying effects immediately during action processing
(which causes double-entity artifacts), effects are queued and then
played back during the render phase when the screen state is correct.

Architecture:
1. Actions queue effects instead of showing them
2. Render system plays queued effects AFTER entities are drawn
3. Screen state matches game state when effects display
"""

from typing import List, Tuple, Optional, Dict, Any
from enum import Enum, auto
import time
import tcod.libtcodpy as libtcodpy


class EffectType(Enum):
    """Types of visual effects that can be queued."""
    HIT = auto()
    CRITICAL_HIT = auto()
    MISS = auto()
    FIREBALL = auto()
    LIGHTNING = auto()
    DRAGON_FART = auto()
    AREA_EFFECT = auto()
    PATH_EFFECT = auto()


class QueuedEffect:
    """Represents a visual effect that will be played later."""
    
    def __init__(
        self,
        effect_type: EffectType,
        x: int,
        y: int,
        entity=None,
        **kwargs
    ):
        """Initialize a queued effect.
        
        Args:
            effect_type: Type of effect to display
            x: X coordinate
            y: Y coordinate
            entity: Entity involved (for getting character/color)
            **kwargs: Additional effect-specific parameters
        """
        self.effect_type = effect_type
        self.x = x
        self.y = y
        self.entity = entity
        self.params = kwargs
    
    def play(self, con=0) -> None:
        """Play this effect immediately.
        
        Args:
            con: Console to draw on (default: root console 0)
        """
        if self.effect_type == EffectType.HIT:
            self._play_hit(con)
        elif self.effect_type == EffectType.CRITICAL_HIT:
            self._play_critical_hit(con)
        elif self.effect_type == EffectType.MISS:
            self._play_miss(con)
        elif self.effect_type == EffectType.FIREBALL:
            self._play_fireball(con)
        elif self.effect_type == EffectType.LIGHTNING:
            self._play_lightning(con)
        elif self.effect_type == EffectType.DRAGON_FART:
            self._play_dragon_fart(con)
        elif self.effect_type == EffectType.AREA_EFFECT:
            self._play_area_effect(con)
        elif self.effect_type == EffectType.PATH_EFFECT:
            self._play_path_effect(con)
    
    def _play_hit(self, con=0) -> None:
        """Play a hit effect."""
        color = (255, 50, 50)  # Bright red
        duration = 0.12  # 120ms
        
        # Get entity character
        if self.entity and hasattr(self.entity, 'char'):
            char = self.entity.char
        else:
            char = libtcodpy.console_get_char(con, self.x, self.y)
            if char == 0 or char == ord(' '):
                char = ord('*')
        
        # Flash red
        libtcodpy.console_set_default_foreground(con, color)
        libtcodpy.console_put_char(con, self.x, self.y, char, libtcodpy.BKGND_NONE)
        libtcodpy.console_flush()
        
        time.sleep(duration)
    
    def _play_critical_hit(self, con=0) -> None:
        """Play a critical hit effect."""
        color = (255, 255, 0)  # Bright yellow
        duration = 0.20  # 200ms
        
        # Get entity character
        if self.entity and hasattr(self.entity, 'char'):
            char = self.entity.char
        else:
            char = libtcodpy.console_get_char(con, self.x, self.y)
            if char == 0 or char == ord(' '):
                char = ord('*')
        
        # Flash yellow
        libtcodpy.console_set_default_foreground(con, color)
        libtcodpy.console_put_char(con, self.x, self.y, char, libtcodpy.BKGND_NONE)
        libtcodpy.console_flush()
        
        time.sleep(duration)
    
    def _play_miss(self, con=0) -> None:
        """Play a miss effect (fumbles only)."""
        color = (128, 128, 128)  # Grey
        duration = 0.10  # 100ms
        
        # Get entity character
        if self.entity and hasattr(self.entity, 'char'):
            char = self.entity.char
        else:
            char = libtcodpy.console_get_char(con, self.x, self.y)
            if char == 0 or char == ord(' '):
                char = ord('-')
        
        # Flash grey
        libtcodpy.console_set_default_foreground(con, color)
        libtcodpy.console_put_char(con, self.x, self.y, char, libtcodpy.BKGND_NONE)
        libtcodpy.console_flush()
        
        time.sleep(duration)
    
    def _play_fireball(self, con=0) -> None:
        """Play a fireball area effect."""
        tiles = self.params.get('tiles', [])
        color = self.params.get('color', (255, 100, 0))  # Orange
        char = self.params.get('char', ord('*'))
        duration = 0.25  # 250ms
        
        # Draw explosion area
        for tile_x, tile_y in tiles:
            libtcodpy.console_set_default_foreground(con, color)
            libtcodpy.console_put_char(con, tile_x, tile_y, char, libtcodpy.BKGND_NONE)
        
        libtcodpy.console_flush()
        time.sleep(duration)
    
    def _play_lightning(self, con=0) -> None:
        """Play a lightning path effect."""
        path = self.params.get('path', [])
        color = self.params.get('color', (255, 255, 100))  # Cyan-yellow
        char = self.params.get('char', ord('|'))
        duration = 0.15  # 150ms
        
        # Draw lightning path
        for tile_x, tile_y in path:
            libtcodpy.console_set_default_foreground(con, color)
            libtcodpy.console_put_char(con, tile_x, tile_y, char, libtcodpy.BKGND_NONE)
        
        libtcodpy.console_flush()
        time.sleep(duration)
    
    def _play_dragon_fart(self, con=0) -> None:
        """Play a dragon fart cone effect."""
        tiles = self.params.get('tiles', [])
        color = self.params.get('color', (100, 200, 50))  # Sickly green
        char = self.params.get('char', ord('~'))
        duration = 0.25  # 250ms
        
        # Draw cone area
        for tile_x, tile_y in tiles:
            libtcodpy.console_set_default_foreground(con, color)
            libtcodpy.console_put_char(con, tile_x, tile_y, char, libtcodpy.BKGND_NONE)
        
        libtcodpy.console_flush()
        time.sleep(duration)
    
    def _play_area_effect(self, con=0) -> None:
        """Play a generic area effect."""
        tiles = self.params.get('tiles', [])
        color = self.params.get('color', (255, 100, 0))
        char = self.params.get('char', ord('*'))
        duration = self.params.get('duration', 0.25)
        
        # Draw area
        for tile_x, tile_y in tiles:
            libtcodpy.console_set_default_foreground(con, color)
            libtcodpy.console_put_char(con, tile_x, tile_y, char, libtcodpy.BKGND_NONE)
        
        libtcodpy.console_flush()
        time.sleep(duration)
    
    def _play_path_effect(self, con=0) -> None:
        """Play a generic path effect."""
        path = self.params.get('path', [])
        color = self.params.get('color', (255, 255, 100))
        char = self.params.get('char', ord('|'))
        duration = self.params.get('duration', 0.15)
        
        # Draw path
        for tile_x, tile_y in path:
            libtcodpy.console_set_default_foreground(con, color)
            libtcodpy.console_put_char(con, tile_x, tile_y, char, libtcodpy.BKGND_NONE)
        
        libtcodpy.console_flush()
        time.sleep(duration)


class VisualEffectQueue:
    """Queue system for deferred visual effects.
    
    This class manages a queue of visual effects that are played back
    during rendering, after the screen state is correct. This eliminates
    the double-entity artifacts caused by showing effects during action
    processing.
    """
    
    def __init__(self):
        """Initialize an empty effect queue."""
        self.effects: List[QueuedEffect] = []
    
    def queue_hit(self, x: int, y: int, entity=None, is_critical: bool = False) -> None:
        """Queue a hit effect for playback during rendering.
        
        Args:
            x: X coordinate of hit
            y: Y coordinate of hit
            entity: Entity that was hit
            is_critical: Whether this was a critical hit
        """
        effect_type = EffectType.CRITICAL_HIT if is_critical else EffectType.HIT
        self.effects.append(QueuedEffect(effect_type, x, y, entity))
    
    def queue_miss(self, x: int, y: int, entity=None) -> None:
        """Queue a miss effect (fumble) for playback during rendering.
        
        Args:
            x: X coordinate of miss
            y: Y coordinate of miss
            entity: Entity that was targeted
        """
        self.effects.append(QueuedEffect(EffectType.MISS, x, y, entity))
    
    def queue_fireball(self, tiles: List[Tuple[int, int]], **kwargs) -> None:
        """Queue a fireball explosion effect.
        
        Args:
            tiles: List of (x, y) coordinates for explosion area
            **kwargs: Additional parameters (color, char, duration)
        """
        # Use first tile as reference position (doesn't matter for area effects)
        x, y = tiles[0] if tiles else (0, 0)
        self.effects.append(QueuedEffect(
            EffectType.FIREBALL, x, y, None, tiles=tiles, **kwargs
        ))
    
    def queue_lightning(self, path: List[Tuple[int, int]], **kwargs) -> None:
        """Queue a lightning bolt effect.
        
        Args:
            path: List of (x, y) coordinates for lightning path
            **kwargs: Additional parameters (color, char, duration)
        """
        x, y = path[-1] if path else (0, 0)  # Target position
        self.effects.append(QueuedEffect(
            EffectType.LIGHTNING, x, y, None, path=path, **kwargs
        ))
    
    def queue_dragon_fart(self, tiles: List[Tuple[int, int]], **kwargs) -> None:
        """Queue a dragon fart cone effect.
        
        Args:
            tiles: List of (x, y) coordinates for cone area
            **kwargs: Additional parameters (color, char, duration)
        """
        x, y = tiles[0] if tiles else (0, 0)
        self.effects.append(QueuedEffect(
            EffectType.DRAGON_FART, x, y, None, tiles=tiles, **kwargs
        ))
    
    def play_all(self, con=0) -> None:
        """Play all queued effects and clear the queue.
        
        This should be called during rendering, after entities are drawn
        but before the final screen flush.
        
        Args:
            con: Console to draw on (default: root console 0)
        """
        for effect in self.effects:
            effect.play(con)
        
        # Clear the queue
        self.effects.clear()
    
    def clear(self) -> None:
        """Clear all queued effects without playing them."""
        self.effects.clear()
    
    def has_effects(self) -> bool:
        """Check if there are any queued effects.
        
        Returns:
            bool: True if effects are queued, False otherwise
        """
        return len(self.effects) > 0
    
    def __len__(self) -> int:
        """Get the number of queued effects."""
        return len(self.effects)


# Global effect queue instance
# This is accessed by visual_effects.py and render systems
_global_effect_queue = VisualEffectQueue()


def get_effect_queue() -> VisualEffectQueue:
    """Get the global visual effect queue.
    
    Returns:
        VisualEffectQueue: The global effect queue instance
    """
    return _global_effect_queue

