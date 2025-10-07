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
    WAND_RECHARGE = auto()  # Sparkle effect when wand gains a charge


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
    
    def play(self, con=0, camera=None) -> None:
        """Play this effect immediately with camera and viewport offset.
        
        Visual effects use world coordinates but need to be translated:
        1. World coords → Viewport coords (via camera)
        2. Viewport coords → Screen coords (via viewport offset)
        
        Args:
            con: Console to draw on (default: root console 0)
            camera: Camera for world→viewport translation (optional)
        """
        # Step 1: Translate world coordinates to viewport coordinates using camera
        if camera:
            # For single-point effects (hit, miss, crit), check if in viewport
            # For area effects (fireball, lightning, etc.), skip this check and let
            # individual tiles be culled in the helper methods
            is_area_effect = self.effect_type in [
                EffectType.FIREBALL, EffectType.LIGHTNING, EffectType.DRAGON_FART,
                EffectType.AREA_EFFECT, EffectType.PATH_EFFECT
            ]
            
            if not is_area_effect and not camera.is_in_viewport(self.x, self.y):
                return  # Single-point effect is off-screen, don't render
            
            viewport_x, viewport_y = camera.world_to_viewport(self.x, self.y)
        else:
            # No camera, world coords = viewport coords (backward compatibility)
            viewport_x, viewport_y = self.x, self.y
        
        # Step 2: Translate viewport coordinates to screen coordinates
        from config.ui_layout import get_ui_layout
        ui_layout = get_ui_layout()
        viewport_offset = ui_layout.viewport_position
        
        self.screen_x = viewport_x + viewport_offset[0]
        self.screen_y = viewport_y + viewport_offset[1]
        
        # Now play the effect at screen coordinates
        if self.effect_type == EffectType.HIT:
            self._play_hit(con)
        elif self.effect_type == EffectType.CRITICAL_HIT:
            self._play_critical_hit(con)
        elif self.effect_type == EffectType.MISS:
            self._play_miss(con)
        elif self.effect_type == EffectType.FIREBALL:
            self._play_fireball(con, camera)
        elif self.effect_type == EffectType.LIGHTNING:
            self._play_lightning(con, camera)
        elif self.effect_type == EffectType.DRAGON_FART:
            self._play_dragon_fart(con, camera)
        elif self.effect_type == EffectType.AREA_EFFECT:
            self._play_area_effect(con, camera)
        elif self.effect_type == EffectType.PATH_EFFECT:
            self._play_path_effect(con, camera)
        elif self.effect_type == EffectType.WAND_RECHARGE:
            self._play_wand_recharge(con)
    
    def _play_hit(self, con=0) -> None:
        """Play a hit effect."""
        color = (255, 50, 50)  # Bright red
        duration = 0.12  # 120ms
        
        # Get entity character
        if self.entity and hasattr(self.entity, 'char'):
            char = self.entity.char
        else:
            char = libtcodpy.console_get_char(con, self.screen_x, self.screen_y)
            if char == 0 or char == ord(' '):
                char = ord('*')
        
        # Flash red at screen position (viewport offset already applied)
        libtcodpy.console_set_default_foreground(con, color)
        libtcodpy.console_put_char(con, self.screen_x, self.screen_y, char, libtcodpy.BKGND_NONE)
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
            char = libtcodpy.console_get_char(con, self.screen_x, self.screen_y)
            if char == 0 or char == ord(' '):
                char = ord('*')
        
        # Flash yellow at screen position (viewport offset already applied)
        libtcodpy.console_set_default_foreground(con, color)
        libtcodpy.console_put_char(con, self.screen_x, self.screen_y, char, libtcodpy.BKGND_NONE)
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
            char = libtcodpy.console_get_char(con, self.screen_x, self.screen_y)
            if char == 0 or char == ord(' '):
                char = ord('-')
        
        # Flash grey at screen position (viewport offset already applied)
        libtcodpy.console_set_default_foreground(con, color)
        libtcodpy.console_put_char(con, self.screen_x, self.screen_y, char, libtcodpy.BKGND_NONE)
        libtcodpy.console_flush()
        
        time.sleep(duration)
    
    def _play_fireball(self, con=0, camera=None) -> None:
        """Play a fireball area effect with proper camera translation."""
        tiles = self.params.get('tiles', [])
        color = self.params.get('color', (255, 100, 0))  # Orange
        char = self.params.get('char', ord('*'))
        duration = 0.25  # 250ms
        
        # Get viewport offset for coordinate translation
        from config.ui_layout import get_ui_layout
        ui_layout = get_ui_layout()
        viewport_offset = ui_layout.viewport_position
        
        # Draw explosion area (translate world coords → viewport coords → screen coords)
        for world_x, world_y in tiles:
            # Step 1: Translate world → viewport via camera
            if camera:
                if not camera.is_in_viewport(world_x, world_y):
                    continue  # Skip tiles outside viewport
                viewport_x, viewport_y = camera.world_to_viewport(world_x, world_y)
            else:
                viewport_x, viewport_y = world_x, world_y
            
            # Step 2: Translate viewport → screen
            screen_x = viewport_x + viewport_offset[0]
            screen_y = viewport_y + viewport_offset[1]
            
            libtcodpy.console_set_default_foreground(con, color)
            libtcodpy.console_put_char(con, screen_x, screen_y, char, libtcodpy.BKGND_NONE)
        
        libtcodpy.console_flush()
        time.sleep(duration)
    
    def _play_lightning(self, con=0, camera=None) -> None:
        """Play a lightning path effect with proper camera translation."""
        path = self.params.get('path', [])
        color = self.params.get('color', (255, 255, 100))  # Cyan-yellow
        char = self.params.get('char', ord('|'))
        duration = 0.15  # 150ms
        
        # Get viewport offset for coordinate translation
        from config.ui_layout import get_ui_layout
        ui_layout = get_ui_layout()
        viewport_offset = ui_layout.viewport_position
        
        # Draw lightning path (translate world coords → viewport coords → screen coords)
        for world_x, world_y in path:
            # Step 1: Translate world → viewport via camera
            if camera:
                if not camera.is_in_viewport(world_x, world_y):
                    continue  # Skip tiles outside viewport
                viewport_x, viewport_y = camera.world_to_viewport(world_x, world_y)
            else:
                viewport_x, viewport_y = world_x, world_y
            
            # Step 2: Translate viewport → screen
            screen_x = viewport_x + viewport_offset[0]
            screen_y = viewport_y + viewport_offset[1]
            
            libtcodpy.console_set_default_foreground(con, color)
            libtcodpy.console_put_char(con, screen_x, screen_y, char, libtcodpy.BKGND_NONE)
        
        libtcodpy.console_flush()
        time.sleep(duration)
    
    def _play_dragon_fart(self, con=0, camera=None) -> None:
        """Play a dragon fart cone effect with proper camera translation."""
        tiles = self.params.get('tiles', [])
        color = self.params.get('color', (100, 200, 50))  # Sickly green
        char = self.params.get('char', ord('~'))
        duration = 0.25  # 250ms
        
        # Get viewport offset for coordinate translation
        from config.ui_layout import get_ui_layout
        ui_layout = get_ui_layout()
        viewport_offset = ui_layout.viewport_position
        
        # Draw cone area (translate world coords → viewport coords → screen coords)
        for world_x, world_y in tiles:
            # Step 1: Translate world → viewport via camera
            if camera:
                if not camera.is_in_viewport(world_x, world_y):
                    continue  # Skip tiles outside viewport
                viewport_x, viewport_y = camera.world_to_viewport(world_x, world_y)
            else:
                viewport_x, viewport_y = world_x, world_y
            
            # Step 2: Translate viewport → screen
            screen_x = viewport_x + viewport_offset[0]
            screen_y = viewport_y + viewport_offset[1]
            
            libtcodpy.console_set_default_foreground(con, color)
            libtcodpy.console_put_char(con, screen_x, screen_y, char, libtcodpy.BKGND_NONE)
        
        libtcodpy.console_flush()
        time.sleep(duration)
    
    def _play_area_effect(self, con=0, camera=None) -> None:
        """Play a generic area effect with proper camera translation."""
        tiles = self.params.get('tiles', [])
        color = self.params.get('color', (255, 100, 0))
        char = self.params.get('char', ord('*'))
        duration = self.params.get('duration', 0.25)
        
        # Get viewport offset for coordinate translation
        from config.ui_layout import get_ui_layout
        ui_layout = get_ui_layout()
        viewport_offset = ui_layout.viewport_position
        
        # Draw area (translate world coords → viewport coords → screen coords)
        for world_x, world_y in tiles:
            # Step 1: Translate world → viewport via camera
            if camera:
                if not camera.is_in_viewport(world_x, world_y):
                    continue  # Skip tiles outside viewport
                viewport_x, viewport_y = camera.world_to_viewport(world_x, world_y)
            else:
                viewport_x, viewport_y = world_x, world_y
            
            # Step 2: Translate viewport → screen
            screen_x = viewport_x + viewport_offset[0]
            screen_y = viewport_y + viewport_offset[1]
            
            libtcodpy.console_set_default_foreground(con, color)
            libtcodpy.console_put_char(con, screen_x, screen_y, char, libtcodpy.BKGND_NONE)
        
        libtcodpy.console_flush()
        time.sleep(duration)
    
    def _play_path_effect(self, con=0, camera=None) -> None:
        """Play a generic path effect with proper camera translation."""
        path = self.params.get('path', [])
        color = self.params.get('color', (255, 255, 100))
        char = self.params.get('char', ord('|'))
        duration = self.params.get('duration', 0.15)
        
        # Get viewport offset for coordinate translation
        from config.ui_layout import get_ui_layout
        ui_layout = get_ui_layout()
        viewport_offset = ui_layout.viewport_position
        
        # Draw path (translate world coords → viewport coords → screen coords)
        for world_x, world_y in path:
            # Step 1: Translate world → viewport via camera
            if camera:
                if not camera.is_in_viewport(world_x, world_y):
                    continue  # Skip tiles outside viewport
                viewport_x, viewport_y = camera.world_to_viewport(world_x, world_y)
            else:
                viewport_x, viewport_y = world_x, world_y
            
            # Step 2: Translate viewport → screen
            screen_x = viewport_x + viewport_offset[0]
            screen_y = viewport_y + viewport_offset[1]
            
            libtcodpy.console_set_default_foreground(con, color)
            libtcodpy.console_put_char(con, screen_x, screen_y, char, libtcodpy.BKGND_NONE)
        
        libtcodpy.console_flush()
        time.sleep(duration)
    
    def _play_wand_recharge(self, con=0) -> None:
        """Play a wand recharge sparkle effect at screen position.
        
        Shows a beautiful sparkle/glow animation to indicate a wand gained a charge.
        Effect plays at the player's position (self.screen_x, self.screen_y).
        """
        # Sparkle sequence: dim → bright → brighter → bright → dim (5 frames)
        sparkle_sequence = [
            {'char': ord('·'), 'color': (200, 180, 0), 'duration': 0.04},  # Dim gold dot
            {'char': ord('*'), 'color': (255, 215, 0), 'duration': 0.06},  # Gold star
            {'char': ord('✦'), 'color': (255, 255, 150), 'duration': 0.08},  # Bright sparkle
            {'char': ord('*'), 'color': (255, 215, 0), 'duration': 0.06},  # Gold star
            {'char': ord('·'), 'color': (200, 180, 0), 'duration': 0.04},  # Dim gold dot
        ]
        
        for frame in sparkle_sequence:
            # Draw the sparkle at screen coordinates
            libtcodpy.console_set_default_foreground(con, frame['color'])
            libtcodpy.console_put_char(con, self.screen_x, self.screen_y, frame['char'], libtcodpy.BKGND_NONE)
            libtcodpy.console_flush()
            time.sleep(frame['duration'])


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
    
    def queue_wand_recharge(self, x: int, y: int, entity=None) -> None:
        """Queue a wand recharge sparkle effect.
        
        Args:
            x: X coordinate of player
            y: Y coordinate of player
            entity: Player entity
        """
        self.effects.append(QueuedEffect(EffectType.WAND_RECHARGE, x, y, entity))
    
    def play_all(self, con=0, camera=None) -> None:
        """Play all queued effects and clear the queue.
        
        This should be called during rendering, after entities are drawn
        but before the final screen flush.
        
        Args:
            con: Console to draw on (default: root console 0)
            camera: Camera for coordinate translation (optional)
        """
        for effect in self.effects:
            effect.play(con, camera)
        
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

