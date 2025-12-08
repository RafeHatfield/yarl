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

from typing import List, Tuple, Optional, Dict, Any, Union
from enum import Enum, auto
import tcod.libtcodpy as libtcodpy

# Forward reference for Entity type
Entity = Any  # Avoid circular import


def _world_to_screen(ui_layout, camera, world_x: int, world_y: int):
    """Translate world coordinates to screen coordinates using the layout/camera."""

    camera_x = getattr(camera, "x", 0) if camera else 0
    camera_y = getattr(camera, "y", 0) if camera else 0
    return ui_layout.world_to_screen(world_x, world_y, camera_x, camera_y)


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
    # Phase 7: Debuff effect types
    SLOW = auto()  # Sluggish/slow debuff applied
    POISON = auto()  # Poison damage/application
    HEAL = auto()  # Healing effect
    BUFF = auto()  # Generic buff applied
    DEBUFF = auto()  # Generic debuff applied
    # Phase 9: Surprise attack effect
    SURPRISE = auto()  # Surprise attack from shadows
    # Phase 10: Faction manipulation effects
    ANGER = auto()  # Unreasonable aggravation applied
    PLAGUE = auto()  # Plague of Restless Death applied/ticking
    REANIMATE = auto()  # Revenant zombie rising


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 7: CENTRAL VFX COLOR/CONFIG MAPPING
# ═══════════════════════════════════════════════════════════════════════════════
# Central registry for effect type → visual properties.
# This enables consistent styling and easy expansion for new effects.

EFFECT_VFX_CONFIG: Dict[EffectType, Dict[str, Any]] = {
    # Combat effects
    EffectType.HIT: {
        "color": (255, 50, 50),      # Bright red
        "char": ord('*'),
        "duration": 0.12,
    },
    EffectType.CRITICAL_HIT: {
        "color": (255, 255, 0),      # Bright yellow
        "char": ord('!'),
        "duration": 0.20,
    },
    EffectType.MISS: {
        "color": (128, 128, 128),    # Grey
        "char": ord('-'),
        "duration": 0.10,
    },
    
    # Area/path effects
    EffectType.FIREBALL: {
        "color": (255, 100, 0),      # Orange
        "char": ord('*'),
        "duration": 0.25,
    },
    EffectType.LIGHTNING: {
        "color": (255, 255, 100),    # Bright yellow
        "char": ord('~'),
        "duration": 0.15,
    },
    EffectType.DRAGON_FART: {
        "color": (100, 200, 50),     # Sickly green
        "char": ord('%'),
        "duration": 0.25,
    },
    
    # Phase 7: Debuff/buff effects
    EffectType.SLOW: {
        "color": (255, 165, 0),      # Orange (tar/molasses)
        "char": ord('~'),
        "duration": 0.15,
    },
    EffectType.POISON: {
        "color": (0, 255, 0),        # Bright green
        "char": ord('*'),
        "duration": 0.15,
    },
    EffectType.HEAL: {
        "color": (0, 255, 100),      # Green-cyan
        "char": ord('+'),
        "duration": 0.15,
    },
    EffectType.BUFF: {
        "color": (100, 200, 255),    # Light blue
        "char": ord('^'),
        "duration": 0.15,
    },
    EffectType.DEBUFF: {
        "color": (200, 100, 100),    # Dark red
        "char": ord('v'),
        "duration": 0.15,
    },
    
    # Utility effects
    EffectType.WAND_RECHARGE: {
        "color": (255, 255, 150),    # Light yellow sparkle
        "char": ord('✦'),
        "duration": 0.15,
    },
    # Phase 9: Surprise attack
    EffectType.SURPRISE: {
        "color": (200, 100, 255),    # Purple/violet for shadowy strike
        "char": ord('✧'),            # Star burst
        "duration": 0.25,            # Longer duration for dramatic effect
    },
    # Phase 10: Faction manipulation effects
    EffectType.ANGER: {
        "color": (255, 100, 50),     # Orange-red for rage/anger
        "char": ord('!'),            # Exclamation for aggravation
        "duration": 0.20,
    },
    EffectType.PLAGUE: {
        "color": (150, 200, 50),     # Sickly yellow-green for plague
        "char": ord('☠'),            # Skull for death plague
        "duration": 0.20,
    },
    EffectType.REANIMATE: {
        "color": (100, 255, 100),    # Necromantic green
        "char": ord('✝'),            # Cross/resurrection symbol
        "duration": 0.30,            # Dramatic reanimation
    },
}


def get_effect_color(effect_type: EffectType) -> Tuple[int, int, int]:
    """Get the color for an effect type from the central registry.
    
    Phase 7: Centralized color lookup for consistent VFX styling.
    
    Args:
        effect_type: The type of visual effect
        
    Returns:
        RGB color tuple
    """
    config = EFFECT_VFX_CONFIG.get(effect_type, {})
    return config.get("color", (255, 255, 255))  # Default white


def get_effect_char(effect_type: EffectType) -> int:
    """Get the character for an effect type from the central registry.
    
    Args:
        effect_type: The type of visual effect
        
    Returns:
        Character code (ord value)
    """
    config = EFFECT_VFX_CONFIG.get(effect_type, {})
    return config.get("char", ord('*'))  # Default asterisk


class QueuedEffect:
    """Represents a visual effect that will be played later."""

    def __init__(
        self,
        effect_type: EffectType,
        x: int,
        y: int,
        entity=None,
        **kwargs,
    ) -> None:
        self.effect_type = effect_type
        self.x = x
        self.y = y
        self.entity = entity
        self.params = kwargs
        self.screen_x: Optional[int] = None
        self.screen_y: Optional[int] = None

    def play(self, con=0, camera=None) -> None:
        """Play this queued effect using the provided console and camera."""

        from config.ui_layout import get_ui_layout

        ui_layout = get_ui_layout()

        needs_world_sampling = self.effect_type in {
            EffectType.FIREBALL,
            EffectType.LIGHTNING,
            EffectType.DRAGON_FART,
            EffectType.AREA_EFFECT,
            EffectType.PATH_EFFECT,
            EffectType.PROJECTILE,
        }

        screen_coords = _world_to_screen(ui_layout, camera, self.x, self.y)
        if screen_coords is None and not needs_world_sampling:
            return

        if screen_coords is not None:
            self.screen_x, self.screen_y = screen_coords
        else:
            self.screen_x = self.screen_y = None

        dispatch = {
            EffectType.HIT: self._play_hit,
            EffectType.CRITICAL_HIT: self._play_critical_hit,
            EffectType.MISS: self._play_miss,
            EffectType.FIREBALL: lambda: self._play_area_tiles(
                con, camera, 'tiles', default_color=(255, 100, 0), default_char=ord('*')
            ),
            EffectType.LIGHTNING: lambda: self._play_path_tiles(
                con, camera, 'path', default_color=(255, 255, 100), default_char=ord('|')
            ),
            EffectType.DRAGON_FART: lambda: self._play_area_tiles(
                con, camera, 'tiles', default_color=(100, 200, 50), default_char=ord('~')
            ),
            EffectType.AREA_EFFECT: lambda: self._play_area_tiles(
                con, camera, 'tiles', default_color=(255, 100, 0), default_char=ord('*')
            ),
            EffectType.PATH_EFFECT: lambda: self._play_path_tiles(
                con, camera, 'path', default_color=(255, 255, 100), default_char=ord('|')
            ),
            EffectType.WAND_RECHARGE: lambda: self._play_wand_recharge(con),
            EffectType.PROJECTILE: lambda: self._play_projectile(con, camera),
            # Phase 7: Debuff/buff effect handlers (use central config)
            EffectType.SLOW: lambda: self._play_effect_from_config(con, EffectType.SLOW),
            EffectType.POISON: lambda: self._play_effect_from_config(con, EffectType.POISON),
            EffectType.HEAL: lambda: self._play_effect_from_config(con, EffectType.HEAL),
            EffectType.BUFF: lambda: self._play_effect_from_config(con, EffectType.BUFF),
            EffectType.DEBUFF: lambda: self._play_effect_from_config(con, EffectType.DEBUFF),
            # Phase 9: Surprise attack
            EffectType.SURPRISE: lambda: self._play_effect_from_config(con, EffectType.SURPRISE),
            # Phase 10: Faction manipulation effects
            EffectType.ANGER: lambda: self._play_effect_from_config(con, EffectType.ANGER),
            EffectType.PLAGUE: lambda: self._play_effect_from_config(con, EffectType.PLAGUE),
            EffectType.REANIMATE: lambda: self._play_effect_from_config(con, EffectType.REANIMATE),
        }

        handler = dispatch.get(self.effect_type)
        if handler:
            handler()

    def _play_hit(self, con=0) -> None:
        self._single_tile_flash(con, (255, 50, 50), ord('*'))

    def _play_critical_hit(self, con=0) -> None:
        self._single_tile_flash(con, (255, 255, 0), ord('*'))

    def _play_miss(self, con=0) -> None:
        self._single_tile_flash(con, (128, 128, 128), ord('-'))

    def _play_wand_recharge(self, con=0) -> None:
        if self.screen_x is None or self.screen_y is None:
            return
        libtcodpy.console_set_default_foreground(con, (255, 255, 150))
        libtcodpy.console_put_char(
            con, self.screen_x, self.screen_y, ord('✦'), libtcodpy.BKGND_NONE
        )

    def _play_projectile(self, con=0, camera=None) -> None:
        path = self.params.get('path', [])
        if not path:
            return

        from config.ui_layout import get_ui_layout

        ui_layout = get_ui_layout()
        world_x, world_y = path[-1]
        screen_coords = _world_to_screen(ui_layout, camera, world_x, world_y)
        if screen_coords is None:
            return

        color = self.params.get('color', (255, 255, 255))
        char = self.params.get('char', ord('*'))
        screen_x, screen_y = screen_coords
        libtcodpy.console_set_default_foreground(con, color)
        libtcodpy.console_put_char(con, screen_x, screen_y, char, libtcodpy.BKGND_NONE)

    def _play_area_tiles(
        self,
        con,
        camera,
        tiles_key: str,
        *,
        default_color,
        default_char,
        color_key: str = 'color',
        char_key: str = 'char',
    ) -> None:
        tiles = self.params.get(tiles_key, [])
        color = self.params.get(color_key, default_color)
        char = self.params.get(char_key, default_char)

        from config.ui_layout import get_ui_layout

        ui_layout = get_ui_layout()

        for world_x, world_y in tiles:
            screen_coords = _world_to_screen(ui_layout, camera, world_x, world_y)
            if screen_coords is None:
                continue
            screen_x, screen_y = screen_coords
            libtcodpy.console_set_default_foreground(con, color)
            libtcodpy.console_put_char(
                con, screen_x, screen_y, char, libtcodpy.BKGND_NONE
            )

    def _play_path_tiles(
        self,
        con,
        camera,
        path_key: str,
        *,
        default_color,
        default_char,
    ) -> None:
        path = self.params.get(path_key, [])
        color = self.params.get('color', default_color)
        char = self.params.get('char', default_char)

        from config.ui_layout import get_ui_layout

        ui_layout = get_ui_layout()

        for world_x, world_y in path:
            screen_coords = _world_to_screen(ui_layout, camera, world_x, world_y)
            if screen_coords is None:
                continue
            screen_x, screen_y = screen_coords
            libtcodpy.console_set_default_foreground(con, color)
            libtcodpy.console_put_char(
                con, screen_x, screen_y, char, libtcodpy.BKGND_NONE
            )

    def _single_tile_flash(self, con, color, fallback_char):
        if self.screen_x is None or self.screen_y is None:
            return

        char = self._resolve_char(con, fallback=fallback_char)
        libtcodpy.console_set_default_foreground(con, color)
        libtcodpy.console_put_char(
            con, self.screen_x, self.screen_y, char, libtcodpy.BKGND_NONE
        )
    
    def _play_effect_from_config(self, con, effect_type: EffectType) -> None:
        """Play an effect using the central VFX config registry.
        
        Phase 7: Unified effect rendering using EFFECT_VFX_CONFIG.
        
        Args:
            con: Console to draw on
            effect_type: Effect type to look up in config
        """
        if self.screen_x is None or self.screen_y is None:
            return
        
        # Get config from central registry, allow param overrides
        config = EFFECT_VFX_CONFIG.get(effect_type, {})
        color = self.params.get('color', config.get('color', (255, 255, 255)))
        char = self.params.get('char', config.get('char', ord('*')))
        
        self._single_tile_flash(con, color, char)

    def _resolve_char(self, con, fallback: int) -> int:
        if self.entity and hasattr(self.entity, 'char'):
            return self.entity.char

        if self.screen_x is None or self.screen_y is None:
            return fallback

        char = libtcodpy.console_get_char(con, self.screen_x, self.screen_y)
        if char == 0 or char == ord(' '):
            return fallback
        return char


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
    
    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 7: DEBUFF/BUFF EFFECT QUEUING
    # ─────────────────────────────────────────────────────────────────────────
    
    def queue_effect_vfx(
        self,
        x: int,
        y: int,
        effect_type: EffectType,
        entity=None,
        **kwargs
    ) -> None:
        """Queue a visual effect by type using the central VFX registry.
        
        Phase 7: This is the new unified API for queuing effects.
        Colors and characters are looked up from EFFECT_VFX_CONFIG.
        
        Args:
            x: X coordinate of effect
            y: Y coordinate of effect
            effect_type: The type of effect (from EffectType enum)
            entity: Optional entity at the location
            **kwargs: Override params (color, char, duration)
        """
        self.effects.append(QueuedEffect(
            effect_type, x, y, entity, **kwargs
        ))
    
    def queue_slow_effect(self, x: int, y: int, entity=None) -> None:
        """Queue a slow/sluggish debuff visual effect.
        
        Phase 7: Shows orange effect when slow debuff is applied.
        
        Args:
            x: X coordinate
            y: Y coordinate
            entity: Entity being slowed
        """
        self.queue_effect_vfx(x, y, EffectType.SLOW, entity)
    
    def queue_poison_effect(self, x: int, y: int, entity=None) -> None:
        """Queue a poison effect visual.
        
        Args:
            x: X coordinate
            y: Y coordinate
            entity: Entity being poisoned
        """
        self.queue_effect_vfx(x, y, EffectType.POISON, entity)
    
    def queue_debuff_effect(self, x: int, y: int, entity=None) -> None:
        """Queue a generic debuff visual effect.
        
        Args:
            x: X coordinate
            y: Y coordinate
            entity: Entity being debuffed
        """
        self.queue_effect_vfx(x, y, EffectType.DEBUFF, entity)
    
    def queue_surprise_effect(self, x: int, y: int, entity=None) -> None:
        """Queue a surprise attack visual effect.
        
        Phase 9: Shows purple/violet effect when player strikes from shadows.
        
        Args:
            x: X coordinate
            y: Y coordinate
            entity: Entity being surprise attacked
        """
        self.queue_effect_vfx(x, y, EffectType.SURPRISE, entity)
    
    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 10: FACTION MANIPULATION EFFECT QUEUING
    # ─────────────────────────────────────────────────────────────────────────
    
    def queue_anger_effect(self, x: int, y: int, entity=None) -> None:
        """Queue an anger/aggravation visual effect.
        
        Phase 10: Shows orange-red effect when Scroll of Unreasonable Aggravation
        is applied to a monster.
        
        Args:
            x: X coordinate
            y: Y coordinate
            entity: Entity being enraged
        """
        self.queue_effect_vfx(x, y, EffectType.ANGER, entity)
    
    def queue_plague_effect(self, x: int, y: int, entity=None) -> None:
        """Queue a plague visual effect.
        
        Phase 10: Shows sickly green effect when Plague of Restless Death
        is applied or deals damage.
        
        Args:
            x: X coordinate
            y: Y coordinate
            entity: Entity infected with plague
        """
        self.queue_effect_vfx(x, y, EffectType.PLAGUE, entity)
    
    def queue_reanimate_effect(self, x: int, y: int, entity=None) -> None:
        """Queue a reanimation visual effect.
        
        Phase 10: Shows necromantic green effect when a plague-infected
        creature rises as a Revenant Zombie.
        
        Args:
            x: X coordinate
            y: Y coordinate
            entity: The new revenant zombie
        """
        self.queue_effect_vfx(x, y, EffectType.REANIMATE, entity)
    
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

