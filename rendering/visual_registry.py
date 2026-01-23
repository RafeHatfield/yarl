"""Centralized visual registry for entity rendering.

This module provides a single source of truth for mapping render keys to
visual properties (char, colors). It supports both ASCII rendering and
serves as the foundation for future tileset support.

The registry is populated from config/entities.yaml on module load,
ensuring consistency with entity definitions.

Usage:
    from rendering.visual_registry import get_visual, VisualSpec
    
    visual = get_visual("orc")
    print(visual.char, visual.fg_color)  # 'o', (63, 127, 63)
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Any
from pathlib import Path
import yaml


@dataclass(frozen=True)
class VisualSpec:
    """Visual specification for an entity or feature.
    
    Attributes:
        char: ASCII character to display
        fg_color: Foreground RGB color tuple
        bg_color: Optional background RGB color tuple
        description: Optional human-readable description
    """
    char: str
    fg_color: Tuple[int, int, int]
    bg_color: Optional[Tuple[int, int, int]] = None
    description: Optional[str] = None


# Default visual for unknown render keys
DEFAULT_VISUAL = VisualSpec(
    char='?',
    fg_color=(255, 255, 255),
    bg_color=None,
    description="Unknown entity"
)

# Global registry populated on module load
_VISUAL_REGISTRY: Dict[str, VisualSpec] = {}
_REGISTRY_LOADED = False


def _parse_color(color_value: Any) -> Optional[Tuple[int, int, int]]:
    """Parse a color value from YAML into an RGB tuple.
    
    Args:
        color_value: Color as list [r,g,b] or tuple (r,g,b)
        
    Returns:
        RGB tuple or None if invalid
    """
    if color_value is None:
        return None
    if isinstance(color_value, (list, tuple)) and len(color_value) >= 3:
        return (int(color_value[0]), int(color_value[1]), int(color_value[2]))
    return None


def _load_registry_from_yaml() -> Dict[str, VisualSpec]:
    """Load visual definitions from config/entities.yaml.
    
    Returns:
        Dictionary mapping render_key -> VisualSpec
    """
    registry: Dict[str, VisualSpec] = {}
    
    # Find entities.yaml relative to this module
    config_path = Path(__file__).parent.parent / "config" / "entities.yaml"
    
    if not config_path.exists():
        # Fallback: try relative to workspace root
        config_path = Path("config/entities.yaml")
        if not config_path.exists():
            return registry
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except (yaml.YAMLError, IOError):
        return registry
    
    if not data:
        return registry
    
    # Process monsters section
    monsters = data.get('monsters', {})
    for key, monster in monsters.items():
        char = monster.get('char', '?')
        color = _parse_color(monster.get('color'))
        if color:
            registry[key] = VisualSpec(
                char=char,
                fg_color=color,
                description=monster.get('name', key.replace('_', ' ').title())
            )
    
    # Process weapons section
    weapons = data.get('weapons', {})
    for key, weapon in weapons.items():
        char = weapon.get('char', '/')
        color = _parse_color(weapon.get('color'))
        if color:
            registry[key] = VisualSpec(
                char=char,
                fg_color=color,
                description=key.replace('_', ' ').title()
            )
    
    # Process armor section
    armor = data.get('armor', {})
    for key, arm in armor.items():
        char = arm.get('char', '[')
        color = _parse_color(arm.get('color'))
        if color:
            registry[key] = VisualSpec(
                char=char,
                fg_color=color,
                description=key.replace('_', ' ').title()
            )
    
    # Process spells/consumables section
    spells = data.get('spells', {})
    for key, spell in spells.items():
        char = spell.get('char', '!')
        color = _parse_color(spell.get('color'))
        if color:
            registry[key] = VisualSpec(
                char=char,
                fg_color=color,
                description=key.replace('_', ' ').title()
            )
    
    # Process wands section
    wands = data.get('wands', {})
    for key, wand in wands.items():
        char = wand.get('char', '/')
        color = _parse_color(wand.get('color'))
        if color:
            registry[key] = VisualSpec(
                char=char,
                fg_color=color,
                description=key.replace('_', ' ').title()
            )
    
    # Process rings section
    rings = data.get('rings', {})
    for key, ring in rings.items():
        char = ring.get('char', '=')
        color = _parse_color(ring.get('color'))
        if color:
            registry[key] = VisualSpec(
                char=char,
                fg_color=color,
                description=key.replace('_', ' ').title()
            )
    
    # Process map_features section
    map_features = data.get('map_features', {})
    for key, feature in map_features.items():
        char = feature.get('char', '?')
        color = _parse_color(feature.get('color'))
        if color:
            registry[key] = VisualSpec(
                char=char,
                fg_color=color,
                description=feature.get('description', key.replace('_', ' ').title())
            )
    
    # Process map_traps section with state variants
    map_traps = data.get('map_traps', {})
    for key, trap in map_traps.items():
        char = trap.get('char', '^')
        color = _parse_color(trap.get('color'))
        trap_type = trap.get('trap_type', key)
        
        if color:
            # Detected state - shows trap character
            registry[f"trap_{trap_type}_detected"] = VisualSpec(
                char=char,
                fg_color=color,
                description=trap.get('description', f"Detected {key}")
            )
            
            # Hidden state - appears as floor
            registry[f"trap_{trap_type}_hidden"] = VisualSpec(
                char='.',
                fg_color=(100, 100, 100),
                description=f"Hidden {key}"
            )
            
            # Disarmed state
            registry[f"trap_{trap_type}_disarmed"] = VisualSpec(
                char='x',
                fg_color=(80, 80, 80),
                description=f"Disarmed {key}"
            )
    
    # Process unique_items section
    unique_items = data.get('unique_items', {})
    for key, item in unique_items.items():
        char = item.get('char', '*')
        color = _parse_color(item.get('color'))
        if color:
            registry[key] = VisualSpec(
                char=char,
                fg_color=color,
                description=item.get('description', key.replace('_', ' ').title())
            )
    
    # Process unique_npcs section
    unique_npcs = data.get('unique_npcs', {})
    for key, npc in unique_npcs.items():
        char = npc.get('char', '@')
        color = _parse_color(npc.get('color'))
        if color:
            registry[key] = VisualSpec(
                char=char,
                fg_color=color,
                description=npc.get('description', npc.get('name', key))
            )
    
    # Add chest state variants
    chest_base = map_features.get('chest', {})
    chest_color = _parse_color(chest_base.get('color', [139, 69, 19]))
    if chest_color:
        registry['chest_closed'] = VisualSpec(
            char='C',
            fg_color=chest_color,
            description="Closed chest"
        )
        registry['chest_open'] = VisualSpec(
            char='C',
            fg_color=(100, 100, 100),  # Grey for opened
            description="Empty chest"
        )
        registry['chest_trapped'] = VisualSpec(
            char='C',
            fg_color=(150, 75, 25),
            description="Suspicious chest"
        )
        registry['chest_locked'] = VisualSpec(
            char='C',
            fg_color=(150, 150, 180),
            description="Locked chest"
        )
    
    # Add tile visuals for map rendering
    registry['tile_wall_visible'] = VisualSpec(
        char='#',
        fg_color=(130, 110, 50),
        description="Wall (visible)"
    )
    registry['tile_wall_explored'] = VisualSpec(
        char='#',
        fg_color=(0, 0, 100),
        description="Wall (explored)"
    )
    registry['tile_floor_visible'] = VisualSpec(
        char='.',
        fg_color=(200, 180, 50),
        description="Floor (visible)"
    )
    registry['tile_floor_explored'] = VisualSpec(
        char='.',
        fg_color=(50, 50, 150),
        description="Floor (explored)"
    )
    
    # Add hazard visuals
    registry['hazard_fire'] = VisualSpec(
        char='*',
        fg_color=(255, 100, 0),
        description="Fire hazard"
    )
    registry['hazard_poison_gas'] = VisualSpec(
        char='%',
        fg_color=(100, 200, 80),
        description="Poison gas"
    )
    
    # Add player visual
    registry['player'] = VisualSpec(
        char='@',
        fg_color=(255, 255, 255),
        description="Player"
    )
    
    # Add corpse visual
    registry['corpse'] = VisualSpec(
        char='%',
        fg_color=(191, 0, 0),
        description="Corpse"
    )
    
    # Add stairs visuals
    registry['stairs_down'] = VisualSpec(
        char='>',
        fg_color=(255, 255, 255),
        description="Stairs down"
    )
    registry['stairs_up'] = VisualSpec(
        char='<',
        fg_color=(255, 255, 255),
        description="Stairs up"
    )
    
    return registry


def _ensure_registry_loaded() -> None:
    """Ensure the registry is loaded (lazy initialization)."""
    global _VISUAL_REGISTRY, _REGISTRY_LOADED
    if not _REGISTRY_LOADED:
        _VISUAL_REGISTRY = _load_registry_from_yaml()
        _REGISTRY_LOADED = True


def get_visual(render_key: str) -> VisualSpec:
    """Get visual properties for a render key.
    
    Args:
        render_key: Canonical render key (e.g., "orc", "trap_spike_detected")
        
    Returns:
        VisualSpec with char, colors, and description.
        Returns DEFAULT_VISUAL if key is not found.
    """
    _ensure_registry_loaded()
    return _VISUAL_REGISTRY.get(render_key, DEFAULT_VISUAL)


def has_visual(render_key: str) -> bool:
    """Check if a render key has a registered visual.
    
    Args:
        render_key: Canonical render key to check
        
    Returns:
        True if the key is registered, False otherwise
    """
    _ensure_registry_loaded()
    return render_key in _VISUAL_REGISTRY


def get_all_render_keys() -> list:
    """Get all registered render keys.
    
    Returns:
        List of all registered render key strings
    """
    _ensure_registry_loaded()
    return list(_VISUAL_REGISTRY.keys())


def register_visual(render_key: str, visual: VisualSpec) -> None:
    """Register a visual for a render key.
    
    This allows runtime registration of visuals not defined in YAML.
    
    Args:
        render_key: The render key to register
        visual: The VisualSpec to associate with the key
    """
    _ensure_registry_loaded()
    _VISUAL_REGISTRY[render_key] = visual


def reload_registry() -> None:
    """Reload the visual registry from YAML.
    
    Useful for testing or hot-reloading visual definitions.
    """
    global _VISUAL_REGISTRY, _REGISTRY_LOADED
    _REGISTRY_LOADED = False
    _ensure_registry_loaded()
