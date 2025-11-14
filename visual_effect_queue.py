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
    PROJECTILE = auto()  # Animated flying projectile (arrows, thrown items)


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
        from config.ui_layout import get_ui_layout

        ui_layout = get_ui_layout()
        camera_x = getattr(camera, "x", 0) if camera else 0
        camera_y = getattr(camera, "y", 0) if camera else 0

        is_area_effect = self.effect_type in [
            EffectType.FIREBALL,
            EffectType.LIGHTNING,
            EffectType.DRAGON_FART,
            EffectType.AREA_EFFECT,
            EffectType.PATH_EFFECT,
        ]

        screen_coords = ui_layout.world_to_screen(self.x, self.y, camera_x, camera_y)

        if screen_coords is None and not is_area_effect:
            return

        if screen_coords is not None:
            self.screen_x, self.screen_y = screen_coords
        else:
            self.screen_x = self.screen_y = None  # Area effect will compute per tile

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
        elif self.effect_type == EffectType.PROJECTILE:
            self._play_projectile(con, camera)


def _world_to_screen(ui_layout, camera, world_x: int, world_y: int):
    camera_x = getattr(camera, "x", 0) if camera else 0
    camera_y = getattr(camera, "y", 0) if camera else 0
    return ui_layout.world_to_screen(world_x, world_y, camera_x, camera_y)
    
    def _play_hit(self, con=0) -> None:
        """Play a hit effect (draw only, no flush or sleep).
        
        NOTE: This draws the effect but does NOT call console_flush().
        The main renderer is responsible for all flush calls.
        All timing is now driven by the main game loop.
        """
        color = (255, 50, 50)  # Bright red
        
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
    
    def _play_critical_hit(self, con=0) -> None:
        """Play a critical hit effect (draw only, no flush or sleep).
        
        NOTE: This draws the effect but does NOT call console_flush().
        The main renderer is responsible for all flush calls.
        All timing is now driven by the main game loop.
        """
        color = (255, 255, 0)  # Bright yellow
        
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
    
    def _play_miss(self, con=0) -> None:
        """Play a miss effect (draw only, no flush or sleep).
        
        NOTE: This draws the effect but does NOT call console_flush().
        The main renderer is responsible for all flush calls.
        All timing is now driven by the main game loop.
        """
        color = (128, 128, 128)  # Grey
        
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
    
    def _play_fireball(self, con=0, camera=None) -> None:
        """Play a fireball area effect (draw only, no flush or sleep).
        
        NOTE: This draws the effect but does NOT call console_flush().
        The main renderer is responsible for all flush calls.
        All timing is now driven by the main game loop.
        
        TODO: Eventually reintroduce multi-frame animation for fireball spread
        effect, but driven by main loop frame timing, not time.sleep().
        """
        tiles = self.params.get('tiles', [])
        color = self.params.get('color', (255, 100, 0))  # Orange
        char = self.params.get('char', ord('*'))
        
        from config.ui_layout import get_ui_layout

        ui_layout = get_ui_layout()

        # Draw explosion area (translate world coords → screen coords)
        for world_x, world_y in tiles:
            screen_coords = _world_to_screen(ui_layout, camera, world_x, world_y)
            if screen_coords is None:
                continue

            screen_x, screen_y = screen_coords

            libtcodpy.console_set_default_foreground(con, color)
            libtcodpy.console_put_char(con, screen_x, screen_y, char, libtcodpy.BKGND_NONE)
    
    def _play_lightning(self, con=0, camera=None) -> None:
        """Play a lightning path effect (draw only, no flush or sleep).
        
        NOTE: This draws the effect but does NOT call console_flush().
        The main renderer is responsible for all flush calls.
        All timing is now driven by the main game loop.
        
        TODO: Eventually reintroduce multi-frame lightning animation
        (branching, pulsing), driven by main loop frame timing, not time.sleep().
        """
        path = self.params.get('path', [])
        color = self.params.get('color', (255, 255, 100))  # Cyan-yellow
        char = self.params.get('char', ord('|'))
        
        from config.ui_layout import get_ui_layout

        ui_layout = get_ui_layout()

        # Draw lightning path using shared world→screen conversion
        for world_x, world_y in path:
            screen_coords = _world_to_screen(ui_layout, camera, world_x, world_y)
            if screen_coords is None:
                continue

            screen_x, screen_y = screen_coords

            libtcodpy.console_set_default_foreground(con, color)
            libtcodpy.console_put_char(con, screen_x, screen_y, char, libtcodpy.BKGND_NONE)
    
    def _play_dragon_fart(self, con=0, camera=None) -> None:
        """Play a dragon fart cone effect (draw only, no flush or sleep).
        
        NOTE: This draws the effect but does NOT call console_flush().
        The main renderer is responsible for all flush calls.
        All timing is now driven by the main game loop.
        
        TODO: Eventually reintroduce multi-frame cone expansion animation,
        driven by main loop frame timing, not time.sleep().
        """
        tiles = self.params.get('tiles', [])
        color = self.params.get('color', (100, 200, 50))  # Sickly green
        char = self.params.get('char', ord('~'))
        
        from config.ui_layout import get_ui_layout

        ui_layout = get_ui_layout()

        for world_x, world_y in tiles:
            screen_coords = _world_to_screen(ui_layout, camera, world_x, world_y)
            if screen_coords is None:
                continue

            screen_x, screen_y = screen_coords
            
            libtcodpy.console_set_default_foreground(con, color)
            libtcodpy.console_put_char(con, screen_x, screen_y, char, libtcodpy.BKGND_NONE)
    
    def _play_area_effect(self, con=0, camera=None) -> None:
        """Play a generic area effect (draw only, no flush or sleep).
        
        NOTE: This draws the effect but does NOT call console_flush().
        The main renderer is responsible for all flush calls.
        All timing is now driven by the main game loop.
        
        TODO: Eventually reintroduce multi-frame area animation,
        driven by main loop frame timing, not time.sleep().
        """
        tiles = self.params.get('tiles', [])
        color = self.params.get('color', (255, 100, 0))
        char = self.params.get('char', ord('*'))
        
        from config.ui_layout import get_ui_layout

        ui_layout = get_ui_layout()

        for world_x, world_y in tiles:
            screen_coords = _world_to_screen(ui_layout, camera, world_x, world_y)
            if screen_coords is None:
                continue

            screen_x, screen_y = screen_coords
            
            libtcodpy.console_set_default_foreground(con, color)
            libtcodpy.console_put_char(con, screen_x, screen_y, char, libtcodpy.BKGND_NONE)
    
    def _play_path_effect(self, con=0, camera=None) -> None:
        """Play a generic path effect (draw only, no flush or sleep).
        
        NOTE: This draws the effect but does NOT call console_flush().
        The main renderer is responsible for all flush calls.
        All timing is now driven by the main game loop.
        
        TODO: Eventually reintroduce multi-frame path animation,
        driven by main loop frame timing, not time.sleep().
        """
        path = self.params.get('path', [])
        color = self.params.get('color', (255, 255, 100))
        char = self.params.get('char', ord('|'))
        
        from config.ui_layout import get_ui_layout

        ui_layout = get_ui_layout()

        for world_x, world_y in path:
            screen_coords = _world_to_screen(ui_layout, camera, world_x, world_y)
            if screen_coords is None:
                continue

            screen_x, screen_y = screen_coords
            
            libtcodpy.console_set_default_foreground(con, color)
            libtcodpy.console_put_char(con, screen_x, screen_y, char, libtcodpy.BKGND_NONE)
    
    def _play_wand_recharge(self, con=0) -> None:
        """Play a wand recharge sparkle effect (draw only, no flush or sleep).
        
        Shows a sparkle glyph to indicate a wand gained a charge.
        Effect plays at the player's position (self.screen_x, self.screen_y).
        
        NOTE: This draws the effect but does NOT call console_flush().
        The main renderer is responsible for all flush calls.
        All timing is now driven by the main game loop.
        
        TODO: Eventually reintroduce multi-frame sparkle animation,
        driven by main loop frame timing, not time.sleep().
        """
        # For now, draw a simple bright sparkle (single frame)
        # instead of the multi-frame sequence
        libtcodpy.console_set_default_foreground(con, (255, 255, 150))  # Bright gold
        libtcodpy.console_put_char(con, self.screen_x, self.screen_y, ord('✦'), libtcodpy.BKGND_NONE)
    
    def _play_projectile(self, con=0, camera=None) -> None:
        """Play projectile effect (draw only, no flush or sleep).
        
        Shows projectile at final destination. No longer animates tile-by-tile
        as that requires blocking time.sleep() calls.
        Used for: arrows, thrown potions, thrown weapons, and any other projectiles.
        
        NOTE: This draws the effect but does NOT call console_flush().
        The main renderer is responsible for all flush calls.
        All timing is now driven by the main game loop.
        
        Params (from self.params):
            - path: List[(x, y)] of tiles projectile travels through
            - char: Character to display (arrow, potion char, etc.)
            - color: RGB tuple for projectile color
            - frame_duration: UNUSED (for now)
        
        TODO: Reintroduce multi-frame projectile animation driven by main loop,
        not time.sleep(). Track animation frame count and update over multiple
        game loop iterations instead of within this single call.
        """
        path = self.params.get('path', [])
        char = self.params.get('char', ord('*'))
        color = self.params.get('color', (255, 255, 255))
        
        from config.ui_layout import get_ui_layout

        ui_layout = get_ui_layout()

        for world_x, world_y in path:
            screen_coords = _world_to_screen(ui_layout, camera, world_x, world_y)
            if screen_coords is None:
                continue

            screen_x, screen_y = screen_coords
            
            # Draw projectile at this position
            libtcodpy.console_set_default_foreground(con, color)
            libtcodpy.console_put_char(con, screen_x, screen_y, char, libtcodpy.BKGND_NONE)


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
    
    def queue_projectile(
        self,
        path: List[Tuple[int, int]],
        char: int,
        color: Tuple[int, int, int],
        **kwargs
    ) -> None:
        """Queue an animated projectile effect.
        
        Shows a projectile (arrow, thrown item, etc.) flying along a path
        with tile-by-tile animation.
        
        Args:
            path: List of (x, y) coordinates projectile travels through
            char: Character to display (arrow, item char, etc.)
            color: RGB color tuple for the projectile
            **kwargs: Additional params (frame_duration, etc.)
        """
        x, y = path[-1] if path else (0, 0)  # Target position
        self.effects.append(QueuedEffect(
            EffectType.PROJECTILE, x, y, None,
            path=path, char=char, color=color, **kwargs
        ))
    
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

