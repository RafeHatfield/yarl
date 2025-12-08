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

import tcod.libtcodpy as libtcodpy
from typing import List, Tuple, Optional, Any
from visual_effect_queue import (
    get_effect_queue,
    EffectType,
    get_effect_color,
    get_effect_char,
    EFFECT_VFX_CONFIG,
)


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
        """Queue a hit effect for deferred rendering.
        
        Instead of showing immediately, this queues the effect to be played
        during the render phase when screen state is correct.
        
        NOTE: This method is deprecated. Use visual_effects.show_hit() instead,
        which properly queues effects through the canonical renderer.
        
        Args:
            x: X coordinate of target
            y: Y coordinate of target
            entity: The entity being hit (to preserve character)
            is_critical: Whether this was a critical hit
        """
        # Queue the effect instead of showing it immediately
        # This ensures it's rendered during the proper render cycle
        get_effect_queue().queue_hit(x, y, entity, is_critical)
    
    @staticmethod
    def show_miss_effect(x: int, y: int, entity=None) -> None:
        """Queue a miss effect for deferred rendering.
        
        Shows a brief grey flash to indicate a critical miss/fumble.
        
        NOTE: This method is deprecated. Use visual_effects.show_miss() instead,
        which properly queues effects through the canonical renderer.
        
        Args:
            x: X coordinate where attack missed
            y: Y coordinate where attack missed
            entity: The entity that was targeted (optional)
        """
        # Queue the effect instead of showing it immediately
        # This ensures it's rendered during the proper render cycle
        get_effect_queue().queue_miss(x, y, entity)
    
    @staticmethod
    def show_area_effect(
        tiles: List[Tuple[int, int]], 
        char: str = '*',
        color: Tuple[int, int, int] = None,
        duration: float = None
    ) -> None:
        """Queue an area effect for deferred rendering.
        
        Used for Fireball, Dragon Fart, and other area spells.
        
        NOTE: This method is deprecated. Use visual_effects.show_fireball() or
        show_dragon_fart() instead, which properly queue effects through the canonical renderer.
        
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
        
        # Convert char to ord value if it's a string
        char_code = ord(char) if isinstance(char, str) else char
        
        # Queue the effect instead of showing it immediately
        # This ensures it's rendered during the proper render cycle
        get_effect_queue().queue_fireball(tiles, char=char_code, color=color, duration=duration)
    
    @staticmethod
    def show_path_effect(
        start: Tuple[int, int],
        end: Tuple[int, int],
        char: str = '~',
        color: Tuple[int, int, int] = None,
        duration: float = None
    ) -> None:
        """Queue a path effect for deferred rendering.
        
        Used for Lightning and other projectile spells.
        
        NOTE: This method is deprecated. Use visual_effects.show_lightning() instead,
        which properly queues effects through the canonical renderer.
        
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
        
        # Queue the effect instead of showing it immediately
        # This ensures it's rendered during the proper render cycle
        get_effect_queue().queue_lightning(path_tiles, char=ord(char) if isinstance(char, str) else char, 
                                          color=color, duration=duration)


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
        char=ord(VisualEffects.FIREBALL_CHAR),
        color=VisualEffects.FIREBALL_COLOR,
        duration=VisualEffects.AREA_DURATION
    )


def show_lightning(path: List[Tuple[int, int]]) -> None:
    """Queue a lightning bolt effect for deferred rendering."""
    get_effect_queue().queue_lightning(
        path,
        char=ord(VisualEffects.LIGHTNING_CHAR),
        color=VisualEffects.LIGHTNING_COLOR,
        duration=VisualEffects.PATH_DURATION
    )


def show_dragon_fart(tiles: List[Tuple[int, int]]) -> None:
    """Queue a dragon fart cone effect for deferred rendering."""
    get_effect_queue().queue_dragon_fart(
        tiles,
        char=ord(VisualEffects.DRAGON_FART_CHAR),
        color=VisualEffects.DRAGON_FART_COLOR,
        duration=VisualEffects.AREA_DURATION
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 7: MODULAR VFX SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════
# Central API for showing effects by type. Replaces hardcoded color/char in callers.

def show_effect_vfx(
    target_x: int,
    target_y: int,
    effect_type: EffectType,
    entity: Any = None,
    source: Any = None,
    **kwargs
) -> None:
    """Queue a visual effect using the modular VFX system.
    
    Phase 7: This is the new unified API for visual effects.
    Colors and characters are looked up from the central EFFECT_VFX_CONFIG.
    
    Usage:
        # Show a critical hit effect
        show_effect_vfx(target.x, target.y, EffectType.CRITICAL_HIT, target)
        
        # Show a slow debuff effect
        show_effect_vfx(target.x, target.y, EffectType.SLOW, target)
        
        # Override color if needed
        show_effect_vfx(x, y, EffectType.DEBUFF, color=(255, 0, 255))
    
    Args:
        target_x: X coordinate for effect
        target_y: Y coordinate for effect
        effect_type: EffectType enum value (CRITICAL_HIT, SLOW, POISON, etc.)
        entity: Optional entity at target location (for character preservation)
        source: Optional source entity (for future animation/sound features)
        **kwargs: Override params (color, char, duration)
    """
    get_effect_queue().queue_effect_vfx(
        target_x, target_y, effect_type, entity, **kwargs
    )


def show_slow_effect(x: int, y: int, entity: Any = None) -> None:
    """Queue a slow/sluggish debuff visual effect.
    
    Phase 7: Shows orange effect when slow debuff is applied.
    
    Args:
        x: X coordinate
        y: Y coordinate
        entity: Entity being slowed
    """
    get_effect_queue().queue_slow_effect(x, y, entity)


def show_poison_effect(x: int, y: int, entity: Any = None) -> None:
    """Queue a poison effect visual.
    
    Args:
        x: X coordinate
        y: Y coordinate
        entity: Entity being poisoned
    """
    get_effect_queue().queue_poison_effect(x, y, entity)


def show_debuff_effect(x: int, y: int, entity: Any = None) -> None:
    """Queue a generic debuff visual effect.
    
    Args:
        x: X coordinate
        y: Y coordinate
        entity: Entity being debuffed
    """
    get_effect_queue().queue_debuff_effect(x, y, entity)


def show_surprise_effect(x: int, y: int, entity: Any = None) -> None:
    """Queue a surprise attack visual effect.
    
    Phase 9: Shows purple/violet effect when player strikes from shadows.
    
    Args:
        x: X coordinate
        y: Y coordinate
        entity: Entity being surprise attacked
    """
    get_effect_queue().queue_surprise_effect(x, y, entity)


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 10: FACTION MANIPULATION VFX
# ═══════════════════════════════════════════════════════════════════════════════

def show_anger_effect(x: int, y: int, entity: Any = None) -> None:
    """Queue an anger/aggravation visual effect.
    
    Phase 10: Shows orange-red effect when Scroll of Unreasonable Aggravation
    is applied to a monster.
    
    Args:
        x: X coordinate
        y: Y coordinate
        entity: Entity being enraged
    """
    get_effect_queue().queue_anger_effect(x, y, entity)


def show_plague_effect(x: int, y: int, entity: Any = None) -> None:
    """Queue a plague visual effect.
    
    Phase 10: Shows sickly green effect when Plague of Restless Death
    is applied or deals damage.
    
    Args:
        x: X coordinate
        y: Y coordinate
        entity: Entity infected with plague
    """
    get_effect_queue().queue_plague_effect(x, y, entity)


def show_reanimate_effect(x: int, y: int, entity: Any = None) -> None:
    """Queue a reanimation visual effect.
    
    Phase 10: Shows necromantic green effect when a plague-infected
    creature rises as a Revenant Zombie.
    
    Args:
        x: X coordinate
        y: Y coordinate
        entity: The new revenant zombie
    """
    get_effect_queue().queue_reanimate_effect(x, y, entity)

