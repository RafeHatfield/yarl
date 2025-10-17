"""Entity configuration registry system.

This module provides a centralized system for loading and managing entity
definitions from YAML configuration files. It supports inheritance, validation,
and fallback behavior for robust entity creation.

The EntityRegistry is designed to be loaded once at startup and provide
fast lookups during entity creation.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    yaml = None

logger = logging.getLogger(__name__)


@dataclass
class EntityStats:
    """Base stats for any entity (player, monster, etc.)."""
    hp: int
    power: int
    defense: int
    xp: int = 0
    damage_min: Optional[int] = None
    damage_max: Optional[int] = None
    defense_min: Optional[int] = None
    defense_max: Optional[int] = None
    # D&D-style stats
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    # Resistance system (v3.12.0)
    resistances: Optional[Dict[str, int]] = None

    def __post_init__(self):
        """Validate stats after creation."""
        if self.hp < 1:
            raise ValueError(f"Entity HP must be >= 1, got {self.hp}")
        if self.power < 0:
            raise ValueError(f"Entity power must be >= 0, got {self.power}")
        if self.defense < 0:
            raise ValueError(f"Entity defense must be >= 0, got {self.defense}")
        if self.xp < 0:
            raise ValueError(f"Entity XP must be >= 0, got {self.xp}")
        
        # Validate damage range if specified
        if self.damage_min is not None and self.damage_max is not None:
            if self.damage_min > self.damage_max:
                raise ValueError(f"damage_min ({self.damage_min}) cannot be greater than damage_max ({self.damage_max})")
            if self.damage_min < 0:
                raise ValueError(f"damage_min must be >= 0, got {self.damage_min}")
        
        # Validate defense range if specified
        if self.defense_min is not None and self.defense_max is not None:
            if self.defense_min > self.defense_max:
                raise ValueError(f"defense_min ({self.defense_min}) cannot be greater than defense_max ({self.defense_max})")
            if self.defense_min < 0:
                raise ValueError(f"defense_min must be >= 0, got {self.defense_min}")


@dataclass
class MonsterDefinition:
    """Definition for a monster entity."""
    name: str
    stats: EntityStats
    char: str
    color: Tuple[int, int, int]
    ai_type: str = "basic"
    render_order: str = "actor"
    blocks: bool = True
    extends: Optional[str] = None
    # Faction system
    faction: str = "neutral"
    # Item-seeking behavior
    can_seek_items: bool = False
    inventory_size: int = 0
    seek_distance: int = 5
    # Special abilities
    special_abilities: Optional[List[str]] = None
    # Equipment system - monsters can spawn with equipment
    equipment: Optional[Dict[str, Any]] = None  # Equipment configuration
    # Boss system
    is_boss: bool = False
    boss_name: Optional[str] = None


@dataclass  
class WeaponDefinition:
    """Definition for a weapon item.
    
    Supports both dice notation (1d4, 2d6) and legacy damage ranges.
    Dice notation is preferred for new weapons.
    
    Weapon Properties:
    - two_handed: Requires both hands, prevents shield use
    - reach: Attack range in tiles (default 1, spears have 2)
    """
    name: str
    power_bonus: int = 0
    damage_min: int = 0
    damage_max: int = 0
    damage_dice: Optional[str] = None  # e.g., "1d4", "1d6", "1d8", "1d10", "1d12", "2d6"
    to_hit_bonus: int = 0  # Bonus to attack rolls
    two_handed: bool = False  # Requires both hands, prevents shield use
    reach: int = 1  # Attack range in tiles (1 = adjacent, 2 = spear reach)
    slot: str = "main_hand"
    char: str = "/"
    color: Tuple[int, int, int] = (139, 69, 19)  # Brown
    extends: Optional[str] = None

    def __post_init__(self):
        """Validate weapon definition."""
        if self.power_bonus < 0:
            raise ValueError(f"Weapon power_bonus must be >= 0, got {self.power_bonus}")
        if self.damage_min < 0:
            raise ValueError(f"Weapon damage_min must be >= 0, got {self.damage_min}")
        if self.damage_max < self.damage_min:
            raise ValueError(f"Weapon damage_max ({self.damage_max}) cannot be less than damage_min ({self.damage_min})")
        if self.slot not in ["main_hand", "off_hand"]:
            raise ValueError(f"Weapon slot must be 'main_hand' or 'off_hand', got '{self.slot}'")
        if self.reach < 1:
            raise ValueError(f"Weapon reach must be >= 1, got {self.reach}")


@dataclass
class ArmorDefinition:
    """Definition for an armor item.
    
    Armor Types & DEX Caps:
    - light: No DEX cap (full DEX bonus applies to AC)
    - medium: DEX cap +2 (max +2 DEX bonus to AC)
    - heavy: DEX cap 0 (no DEX bonus to AC)
    - shield: No impact on DEX cap
    """
    name: str
    defense_bonus: int = 0
    defense_min: int = 0
    defense_max: int = 0
    armor_class_bonus: int = 0  # AC bonus for d20 combat
    armor_type: Optional[str] = None  # light, medium, heavy, shield
    dex_cap: Optional[int] = None  # Max DEX modifier for AC (None = no cap)
    slot: str = "off_hand"
    char: str = "["
    color: Tuple[int, int, int] = (139, 69, 19)  # Brown
    extends: Optional[str] = None

    def __post_init__(self):
        """Validate armor definition."""
        if self.defense_bonus < 0:
            raise ValueError(f"Armor defense_bonus must be >= 0, got {self.defense_bonus}")
        if self.defense_min < 0:
            raise ValueError(f"Armor defense_min must be >= 0, got {self.defense_min}")
        if self.defense_max < self.defense_min:
            raise ValueError(f"Armor defense_max ({self.defense_max}) cannot be less than defense_min ({self.defense_min})")
        if self.armor_class_bonus < 0:
            raise ValueError(f"Armor armor_class_bonus must be >= 0, got {self.armor_class_bonus}")
        # Allow all equipment slots for armor
        valid_slots = ["main_hand", "off_hand", "head", "chest", "feet"]
        if self.slot not in valid_slots:
            raise ValueError(f"Armor slot must be one of {valid_slots}, got '{self.slot}'")


@dataclass
class SpellDefinition:
    """Definition for a spell/consumable item."""
    name: str
    spell_type: str  # "damage", "heal", "utility", "potion"
    damage: int = 0
    heal_amount: int = 0
    maximum_range: int = 0
    radius: int = 0
    char: str = "?"
    color: Tuple[int, int, int] = (255, 255, 0)  # Yellow
    extends: Optional[str] = None
    effect_function: Optional[str] = None  # For potions and custom effects

    def __post_init__(self):
        """Validate spell definition."""
        if self.damage < 0:
            raise ValueError(f"Spell damage must be >= 0, got {self.damage}")
        if self.heal_amount < 0:
            raise ValueError(f"Spell heal_amount must be >= 0, got {self.heal_amount}")
        if self.maximum_range < 0:
            raise ValueError(f"Spell maximum_range must be >= 0, got {self.maximum_range}")
        if self.radius < 0:
            raise ValueError(f"Spell radius must be >= 0, got {self.radius}")


@dataclass
class RingDefinition:
    """Definition for a ring item (passive effect jewelry).
    
    Rings provide continuous bonuses while equipped in left or right ring slots.
    Effects can include AC bonuses, stat bonuses, damage bonuses, immunities,
    regeneration, and triggered effects.
    """
    name: str
    ring_effect: str  # Type of effect (e.g., "protection", "strength", "regeneration")
    effect_strength: int  # Magnitude of the effect (e.g., +2 AC, +2 STR, heal every N turns)
    char: str = "="
    color: Tuple[int, int, int] = (200, 200, 200)
    extends: Optional[str] = None  # For inheritance


@dataclass
class WandDefinition:
    """Definition for a wand item (multi-charge spell caster).
    
    Wands are reusable versions of scrolls that have charges. They can be
    recharged by picking up matching scrolls.
    """
    name: str
    spell_name: str  # The scroll name this wand is equivalent to (for recharging)
    spell_type: str  # "damage", "heal", "utility", "offensive"
    damage: int = 0
    heal_amount: int = 0
    maximum_range: int = 0
    radius: int = 0
    duration: int = 0  # For effects that last multiple turns
    range: int = 0  # Alternate name for maximum_range (used by some spells)
    cone_width: int = 0  # For cone spells like dragon fart
    defense_bonus: int = 0  # For shield-type effects
    char: str = "/"
    color: Tuple[int, int, int] = (255, 200, 0)  # Golden yellow
    extends: Optional[str] = None

    def __post_init__(self):
        """Validate wand definition."""
        if self.damage < 0:
            raise ValueError(f"Wand damage must be >= 0, got {self.damage}")
        if self.heal_amount < 0:
            raise ValueError(f"Wand heal_amount must be >= 0, got {self.heal_amount}")
        if self.maximum_range < 0:
            raise ValueError(f"Wand maximum_range must be >= 0, got {self.maximum_range}")
        if self.radius < 0:
            raise ValueError(f"Wand radius must be >= 0, got {self.radius}")


class EntityRegistry:
    """Registry for all entity definitions loaded from configuration files.
    
    This class handles loading entity definitions from YAML files, resolving
    inheritance relationships, and providing fast lookups for entity creation.
    
    The registry supports:
    - Multiple configuration files
    - Entity inheritance via 'extends' keyword
    - Validation of all entity definitions
    - Fallback to default values for missing definitions
    """

    def __init__(self):
        """Initialize an empty entity registry."""
        self.monsters: Dict[str, MonsterDefinition] = {}
        self.weapons: Dict[str, WeaponDefinition] = {}
        self.armor: Dict[str, ArmorDefinition] = {}
        self.spells: Dict[str, SpellDefinition] = {}
        self.wands: Dict[str, WandDefinition] = {}
        self.rings: Dict[str, RingDefinition] = {}
        self.player_stats: Optional[EntityStats] = None
        self._loaded = False

    def load_from_file(self, config_path: str) -> None:
        """Load entity definitions from a YAML configuration file.
        
        Args:
            config_path: Path to the YAML configuration file
            
        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            ValueError: If the configuration file is invalid
            RuntimeError: If YAML support is not available
        """
        if not YAML_AVAILABLE:
            raise RuntimeError("YAML support not available. Install PyYAML: pip install PyYAML")

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Entity configuration file not found: {config_path}")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            if not config_data:
                logger.warning(f"Empty or invalid YAML file: {config_path}")
                return

            self._process_config_data(config_data)
            self._resolve_inheritance()
            self._loaded = True
            
            logger.info(f"Loaded entity configuration from {config_path}")
            logger.info(f"  Monsters: {len(self.monsters)}")
            logger.info(f"  Weapons: {len(self.weapons)}")
            logger.info(f"  Armor: {len(self.armor)}")
            logger.info(f"  Spells: {len(self.spells)}")
            logger.info(f"  Rings: {len(self.rings)}")

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in entity configuration: {e}")
        except Exception as e:
            logger.error(f"Error loading entity configuration from {config_path}: {e}")
            raise

    def _process_config_data(self, config_data: Dict[str, Any]) -> None:
        """Process raw configuration data into entity definitions.
        
        Args:
            config_data: Raw configuration data from YAML file
        """
        # Store raw config data for inheritance processing
        self._raw_config_data = config_data
        
        # Load player stats
        if 'player' in config_data:
            try:
                self.player_stats = EntityStats(**config_data['player'])
            except Exception as e:
                logger.error(f"Error loading player stats: {e}")
                raise ValueError(f"Invalid player configuration: {e}")

        # Load monsters - process inheritance-aware
        if 'monsters' in config_data:
            self._process_monsters_with_inheritance(config_data['monsters'])

        # Load weapons - process inheritance-aware
        if 'weapons' in config_data:
            self._process_weapons_with_inheritance(config_data['weapons'])

        # Load armor - process inheritance-aware
        if 'armor' in config_data:
            self._process_armor_with_inheritance(config_data['armor'])

        # Load spells - process inheritance-aware
        if 'spells' in config_data:
            self._process_spells_with_inheritance(config_data['spells'])
        
        # Load wands - process inheritance-aware
        if 'wands' in config_data:
            self._process_wands_with_inheritance(config_data['wands'])
        
        # Load rings - process inheritance-aware
        if 'rings' in config_data:
            self._process_rings_with_inheritance(config_data['rings'])

    def _process_monsters_with_inheritance(self, monsters_data: Dict[str, Any]) -> None:
        """Process monster data with inheritance-aware creation.
        
        This method first resolves inheritance at the raw data level, then creates
        entity definitions from the fully resolved data.
        
        Args:
            monsters_data: Raw monster configuration data from YAML
        """
        # First, resolve inheritance at the raw data level
        resolved_monsters_data = self._resolve_raw_inheritance(monsters_data, 'monster')
        
        # Now create entity definitions from resolved data
        for monster_id, monster_data in resolved_monsters_data.items():
            try:
                # Handle stats sub-object
                stats_data = monster_data.get('stats', {})
                stats = EntityStats(**stats_data)
                
                # Create monster definition
                monster_def = MonsterDefinition(
                    name=monster_id.title(),
                    stats=stats,
                    char=monster_data.get('char', '?'),
                    color=tuple(monster_data.get('color', [255, 255, 255])),
                    ai_type=monster_data.get('ai_type', 'basic'),
                    render_order=monster_data.get('render_order', 'actor'),
                    blocks=monster_data.get('blocks', True),
                    extends=None,  # Clear extends after resolution
                    # Faction system
                    faction=monster_data.get('faction', 'neutral'),
                    # Item-seeking behavior
                    can_seek_items=monster_data.get('can_seek_items', False),
                    inventory_size=monster_data.get('inventory_size', 0),
                    seek_distance=monster_data.get('seek_distance', 5),
                    # Special abilities
                    special_abilities=monster_data.get('special_abilities', None),
                    # Equipment system
                    equipment=monster_data.get('equipment', None),
                    # Boss system
                    is_boss=monster_data.get('is_boss', False),
                    boss_name=monster_data.get('boss_name', None)
                )
                
                self.monsters[monster_id] = monster_def
                
            except Exception as e:
                logger.error(f"Error creating resolved monster '{monster_id}': {e}")
                raise ValueError(f"Invalid resolved monster configuration for '{monster_id}': {e}")

    def _process_weapons_with_inheritance(self, weapons_data: Dict[str, Any]) -> None:
        """Process weapon data with inheritance-aware creation."""
        resolved_weapons_data = self._resolve_raw_inheritance(weapons_data, 'weapon')
        
        for weapon_id, weapon_data in resolved_weapons_data.items():
            try:
                # Get dice notation or damage range
                damage_dice = weapon_data.get('damage_dice')
                damage_min = weapon_data.get('damage_min', 0)
                damage_max = weapon_data.get('damage_max', 0)
                
                # If dice notation is provided but no damage range, calculate range from dice
                if damage_dice and (damage_min == 0 or damage_max == 0):
                    from dice import get_dice_min_max
                    damage_min, damage_max = get_dice_min_max(damage_dice)
                
                weapon_def = WeaponDefinition(
                    name=weapon_id.replace('_', ' ').title(),
                    power_bonus=weapon_data.get('power_bonus', 0),
                    damage_min=damage_min,
                    damage_max=damage_max,
                    damage_dice=damage_dice,
                    to_hit_bonus=weapon_data.get('to_hit_bonus', 0),
                    two_handed=weapon_data.get('two_handed', False),  # NEW!
                    reach=weapon_data.get('reach', 1),  # NEW!
                    slot=weapon_data.get('slot', 'main_hand'),
                    char=weapon_data.get('char', '/'),
                    color=tuple(weapon_data.get('color', [139, 69, 19])),
                    extends=None  # Clear extends after resolution
                )
                
                self.weapons[weapon_id] = weapon_def
                
            except Exception as e:
                logger.error(f"Error creating resolved weapon '{weapon_id}': {e}")
                raise ValueError(f"Invalid resolved weapon configuration for '{weapon_id}': {e}")

    def _process_armor_with_inheritance(self, armor_data: Dict[str, Any]) -> None:
        """Process armor data with inheritance-aware creation."""
        resolved_armor_data = self._resolve_raw_inheritance(armor_data, 'armor')
        
        for armor_id, armor_data in resolved_armor_data.items():
            try:
                armor_def = ArmorDefinition(
                    name=armor_id.replace('_', ' ').title(),
                    defense_bonus=armor_data.get('defense_bonus', 0),
                    defense_min=armor_data.get('defense_min', 0),
                    defense_max=armor_data.get('defense_max', 0),
                    armor_class_bonus=armor_data.get('armor_class_bonus', 0),
                    armor_type=armor_data.get('armor_type'),  # light, medium, heavy, shield
                    dex_cap=armor_data.get('dex_cap'),  # Max DEX modifier for AC
                    slot=armor_data.get('slot', 'off_hand'),
                    char=armor_data.get('char', '['),
                    color=tuple(armor_data.get('color', [139, 69, 19])),
                    extends=None  # Clear extends after resolution
                )
                
                self.armor[armor_id] = armor_def
                
            except Exception as e:
                logger.error(f"Error creating resolved armor '{armor_id}': {e}")
                raise ValueError(f"Invalid resolved armor configuration for '{armor_id}': {e}")

    def _process_spells_with_inheritance(self, spells_data: Dict[str, Any]) -> None:
        """Process spell data with inheritance-aware creation."""
        resolved_spells_data = self._resolve_raw_inheritance(spells_data, 'spell')
        
        for spell_id, spell_data in resolved_spells_data.items():
            try:
                spell_def = SpellDefinition(
                    name=spell_id.replace('_', ' ').title(),
                    spell_type=spell_data.get('spell_type', 'utility'),
                    damage=spell_data.get('damage', 0),
                    heal_amount=spell_data.get('heal_amount', 0),
                    maximum_range=spell_data.get('maximum_range', 0),
                    radius=spell_data.get('radius', 0),
                    char=spell_data.get('char', '?'),
                    color=tuple(spell_data.get('color', [255, 255, 0])),
                    extends=None,  # Clear extends after resolution
                    effect_function=spell_data.get('effect_function', None)  # For potions and custom effects
                )
                
                self.spells[spell_id] = spell_def
                
            except Exception as e:
                logger.error(f"Error creating resolved spell '{spell_id}': {e}")
                raise ValueError(f"Invalid resolved spell configuration for '{spell_id}': {e}")

    def _process_wands_with_inheritance(self, wands_data: Dict[str, Any]) -> None:
        """Process wand data with inheritance-aware creation."""
        resolved_wands_data = self._resolve_raw_inheritance(wands_data, 'wand')
        
        for wand_id, wand_data in resolved_wands_data.items():
            try:
                wand_def = WandDefinition(
                    name=wand_id.replace('_', ' ').title(),
                    spell_name=wand_data.get('spell_name', ''),
                    spell_type=wand_data.get('spell_type', 'utility'),
                    damage=wand_data.get('damage', 0),
                    heal_amount=wand_data.get('heal_amount', 0),
                    maximum_range=wand_data.get('maximum_range', 0),
                    radius=wand_data.get('radius', 0),
                    duration=wand_data.get('duration', 0),
                    range=wand_data.get('range', 0),
                    cone_width=wand_data.get('cone_width', 0),
                    defense_bonus=wand_data.get('defense_bonus', 0),
                    char=wand_data.get('char', '/'),
                    color=tuple(wand_data.get('color', [255, 200, 0])),
                    extends=None  # Clear extends after resolution
                )
                
                self.wands[wand_id] = wand_def
                
            except Exception as e:
                logger.error(f"Error creating resolved wand '{wand_id}': {e}")
                raise ValueError(f"Invalid resolved wand configuration for '{wand_id}': {e}")

    def _process_rings_with_inheritance(self, rings_data: Dict[str, Any]) -> None:
        """Process ring data with inheritance-aware creation."""
        resolved_rings_data = self._resolve_raw_inheritance(rings_data, 'ring')
        
        for ring_id, ring_data in resolved_rings_data.items():
            try:
                ring_def = RingDefinition(
                    name=ring_id.replace('_', ' ').title(),
                    ring_effect=ring_data.get('ring_effect', 'unknown'),
                    effect_strength=ring_data.get('effect_strength', 0),
                    char=ring_data.get('char', '='),
                    color=tuple(ring_data.get('color', [200, 200, 200])),
                    extends=None  # Clear extends after resolution
                )
                
                self.rings[ring_id] = ring_def
                
            except Exception as e:
                logger.error(f"Error creating resolved ring '{ring_id}': {e}")
                raise ValueError(f"Invalid resolved ring configuration for '{ring_id}': {e}")

    def _resolve_raw_inheritance(self, entities_data: Dict[str, Any], entity_type: str) -> Dict[str, Any]:
        """Resolve inheritance at the raw data level before entity creation.
        
        Args:
            entities_data: Raw entity data from YAML
            entity_type: Type of entity for error reporting
            
        Returns:
            Dictionary of fully resolved entity data
        """
        try:
            from config.game_constants import get_entity_config
            entity_config = get_entity_config()
        except ImportError:
            # Fallback for testing
            entity_config = type('MockConfig', (), {
                'ENABLE_ENTITY_INHERITANCE': True,
                'MAX_INHERITANCE_DEPTH': 5
            })()
        
        resolved_data = {}
        resolving = set()
        resolved = set()
        
        def resolve_entity_data(entity_id: str) -> Dict[str, Any]:
            """Recursively resolve inheritance for raw entity data."""
            if entity_id in resolved:
                return resolved_data[entity_id]
                
            if entity_id in resolving:
                raise ValueError(f"Circular inheritance detected in {entity_type} '{entity_id}'")
            
            if entity_id not in entities_data:
                raise ValueError(f"Unknown {entity_type} '{entity_id}' referenced in inheritance")
            
            entity_data = entities_data[entity_id].copy()
            
            if not entity_data.get('extends'):
                # No inheritance, store as-is
                resolved_data[entity_id] = entity_data
                resolved.add(entity_id)
                return entity_data
            
            parent_id = entity_data['extends']
            resolving.add(entity_id)
            
            try:
                # Recursively resolve parent first
                parent_data = resolve_entity_data(parent_id)
                
                # Merge parent data into child data
                merged_data = self._deep_merge_dicts(parent_data, entity_data)
                merged_data['extends'] = None  # Clear extends after resolution
                
                resolved_data[entity_id] = merged_data
                resolved.add(entity_id)
                resolving.remove(entity_id)
                
                logger.debug(f"Resolved {entity_type} '{entity_id}' extending '{parent_id}'")
                return merged_data
                
            except Exception as e:
                resolving.discard(entity_id)
                raise ValueError(f"Error resolving inheritance for {entity_type} '{entity_id}': {e}")
        
        # Resolve all entities
        for entity_id in entities_data.keys():
            if entity_id not in resolved:
                resolve_entity_data(entity_id)
        
        return resolved_data

    def _deep_merge_dicts(self, parent_dict: Dict[str, Any], child_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries, with child values overriding parent values.
        
        Args:
            parent_dict: Parent dictionary (base values)
            child_dict: Child dictionary (override values)
            
        Returns:
            Merged dictionary with child overrides applied to parent base
        """
        import copy
        
        # Start with a deep copy of parent
        merged = copy.deepcopy(parent_dict)
        
        # Apply child overrides
        for key, child_value in child_dict.items():
            if key == 'extends':
                continue  # Skip extends field
                
            if key in merged and isinstance(merged[key], dict) and isinstance(child_value, dict):
                # Recursively merge nested dictionaries
                merged[key] = self._deep_merge_dicts(merged[key], child_value)
            elif child_value is not None:
                # Child value overrides parent (only if not None)
                merged[key] = copy.deepcopy(child_value)
        
        return merged

    def _resolve_inheritance(self) -> None:
        """Resolve inheritance relationships between entity definitions.
        
        This method processes 'extends' relationships to apply inheritance,
        allowing entities to inherit properties from parent definitions.
        
        Note: All entity types are now processed with inheritance-aware methods
        during initial loading, so this method is no longer needed for the main
        entity types but is kept for backward compatibility.
        """
        # All entity types are now processed with inheritance during loading:
        # - Monsters: _process_monsters_with_inheritance
        # - Weapons: _process_weapons_with_inheritance  
        # - Armor: _process_armor_with_inheritance
        # - Spells: _process_spells_with_inheritance
        
        logger.debug("Inheritance resolution completed during entity loading")

    def _resolve_entity_inheritance(self, entity_dict: Dict[str, Any], entity_type: str) -> None:
        """Resolve inheritance for a specific entity type.
        
        This method processes inheritance relationships to create fully resolved entity
        definitions. It supports multi-level inheritance chains and detects circular
        dependencies.
        
        Args:
            entity_dict: Dictionary of entity definitions
            entity_type: Type of entity for error reporting
            
        Raises:
            ValueError: If circular dependencies or invalid inheritance is detected
        """
        try:
            from config.game_constants import get_entity_config
            entity_config = get_entity_config()
        except ImportError:
            # Fallback for testing - create a mock config
            entity_config = type('MockConfig', (), {
                'ENABLE_ENTITY_INHERITANCE': True,
                'MAX_INHERITANCE_DEPTH': 5
            })()
        
        # Track resolution state to detect circular dependencies
        resolving = set()  # Currently being resolved (for cycle detection)
        resolved = set()   # Already fully resolved
        
        def resolve_entity(entity_id: str) -> None:
            """Recursively resolve inheritance for a single entity."""
            if entity_id in resolved:
                return  # Already resolved
                
            if entity_id in resolving:
                # Circular dependency detected
                raise ValueError(f"Circular inheritance detected in {entity_type} '{entity_id}'")
            
            if entity_id not in entity_dict:
                raise ValueError(f"Unknown {entity_type} '{entity_id}' referenced in inheritance")
            
            entity_def = entity_dict[entity_id]
            
            if not entity_def.extends:
                # No inheritance, mark as resolved
                resolved.add(entity_id)
                logger.debug(f"Resolved {entity_type} '{entity_id}' (no inheritance)")
                return
            
            parent_id = entity_def.extends
            
            # Mark as currently resolving
            resolving.add(entity_id)
            
            try:
                # Recursively resolve parent first
                resolve_entity(parent_id)
                
                # Get resolved parent
                parent_def = entity_dict[parent_id]
                
                # Merge parent properties into child
                merged_def = self._merge_entity_definitions(parent_def, entity_def, entity_type)
                
                # Replace child definition with merged version
                entity_dict[entity_id] = merged_def
                
                # Mark as resolved
                resolved.add(entity_id)
                resolving.remove(entity_id)
                
                logger.debug(f"Resolved {entity_type} '{entity_id}' extending '{parent_id}'")
                
            except Exception as e:
                resolving.discard(entity_id)  # Clean up on error
                raise ValueError(f"Error resolving inheritance for {entity_type} '{entity_id}': {e}")
        
        # Resolve all entities
        entity_ids = list(entity_dict.keys())  # Copy keys to avoid modification during iteration
        for entity_id in entity_ids:
            try:
                resolve_entity(entity_id)
            except ValueError as e:
                if entity_config.ENABLE_ENTITY_INHERITANCE:
                    # Fail fast as requested
                    raise e
                else:
                    # Inheritance disabled, skip
                    logger.warning(f"Skipping inheritance for {entity_type} '{entity_id}': {e}")
                    continue

    def _merge_entity_definitions(self, parent_def: Any, child_def: Any, entity_type: str) -> Any:
        """Merge parent and child entity definitions using deep merge strategy.
        
        The child definition overrides parent properties, with special handling
        for nested objects like stats which are merged recursively.
        
        Args:
            parent_def: Parent entity definition
            child_def: Child entity definition that extends parent
            entity_type: Type of entity for error reporting
            
        Returns:
            Merged entity definition with child overrides applied to parent base
        """
        import copy
        from dataclasses import fields, is_dataclass, replace
        
        if not is_dataclass(parent_def) or not is_dataclass(child_def):
            raise ValueError(f"Cannot merge non-dataclass entities in {entity_type}")
        
        # Start with a deep copy of the parent
        merged_data = {}
        
        # Get all fields from the parent definition
        for field in fields(parent_def):
            field_name = field.name
            parent_value = getattr(parent_def, field_name)
            
            # Check if child has this field and it's not None
            if hasattr(child_def, field_name):
                child_value = getattr(child_def, field_name)
                
                # Skip extends field - it's not part of the final definition
                if field_name == 'extends':
                    merged_data[field_name] = None
                    continue
                
                # If child value is None, use parent value
                if child_value is None:
                    merged_data[field_name] = copy.deepcopy(parent_value)
                # If child value is a dataclass, merge recursively
                elif is_dataclass(child_value) and is_dataclass(parent_value):
                    merged_data[field_name] = self._merge_entity_definitions(
                        parent_value, child_value, f"{entity_type}.{field_name}"
                    )
                # Otherwise, child overrides parent
                else:
                    merged_data[field_name] = copy.deepcopy(child_value)
            else:
                # Child doesn't have this field, use parent value
                merged_data[field_name] = copy.deepcopy(parent_value)
        
        # Handle any additional fields that exist only in child
        for field in fields(child_def):
            field_name = field.name
            if field_name not in merged_data and hasattr(child_def, field_name):
                child_value = getattr(child_def, field_name)
                if child_value is not None:
                    merged_data[field_name] = copy.deepcopy(child_value)
        
        # Create new instance of the same type as child with merged data
        try:
            merged_def = type(child_def)(**merged_data)
            logger.debug(f"Successfully merged {entity_type} definitions")
            return merged_def
        except Exception as e:
            raise ValueError(f"Failed to create merged {entity_type} definition: {e}")

    def get_monster(self, monster_id: str) -> Optional[MonsterDefinition]:
        """Get a monster definition by ID.
        
        Args:
            monster_id: The monster identifier
            
        Returns:
            MonsterDefinition if found, None otherwise
        """
        return self.monsters.get(monster_id)

    def get_weapon(self, weapon_id: str) -> Optional[WeaponDefinition]:
        """Get a weapon definition by ID.
        
        Args:
            weapon_id: The weapon identifier
            
        Returns:
            WeaponDefinition if found, None otherwise
        """
        return self.weapons.get(weapon_id)

    def get_armor(self, armor_id: str) -> Optional[ArmorDefinition]:
        """Get an armor definition by ID.
        
        Args:
            armor_id: The armor identifier
            
        Returns:
            ArmorDefinition if found, None otherwise
        """
        return self.armor.get(armor_id)

    def get_spell(self, spell_id: str) -> Optional[SpellDefinition]:
        """Get a spell definition by ID.
        
        Args:
            spell_id: The spell identifier
            
        Returns:
            SpellDefinition if found, None otherwise
        """
        return self.spells.get(spell_id)

    def get_wand(self, wand_id: str) -> Optional[WandDefinition]:
        """Get a wand definition by ID.
        
        Args:
            wand_id: The wand identifier
            
        Returns:
            WandDefinition if found, None otherwise
        """
        return self.wands.get(wand_id)

    def get_ring(self, ring_id: str) -> Optional[RingDefinition]:
        """Get a ring definition by ID.
        
        Args:
            ring_id: The ring identifier
            
        Returns:
            RingDefinition if found, None otherwise
        """
        return self.rings.get(ring_id)

    def get_player_stats(self) -> Optional[EntityStats]:
        """Get the player starting stats.
        
        Returns:
            EntityStats for player if loaded, None otherwise
        """
        return self.player_stats

    def is_loaded(self) -> bool:
        """Check if the registry has been loaded from configuration.
        
        Returns:
            True if configuration has been loaded, False otherwise
        """
        return self._loaded

    def get_all_monster_ids(self) -> List[str]:
        """Get a list of all available monster IDs.
        
        Returns:
            List of monster identifiers
        """
        return list(self.monsters.keys())

    def get_all_weapon_ids(self) -> List[str]:
        """Get a list of all available weapon IDs.
        
        Returns:
            List of weapon identifiers
        """
        return list(self.weapons.keys())

    def get_all_armor_ids(self) -> List[str]:
        """Get a list of all available armor IDs.
        
        Returns:
            List of armor identifiers
        """
        return list(self.armor.keys())

    def get_all_spell_ids(self) -> List[str]:
        """Get a list of all available spell IDs.
        
        Returns:
            List of spell identifiers
        """
        return list(self.spells.keys())


# Global entity registry instance
_entity_registry = EntityRegistry()


def get_entity_registry() -> EntityRegistry:
    """Get the global entity registry instance.
    
    Returns:
        The global EntityRegistry instance
    """
    return _entity_registry


def load_entity_config(config_path: str = None) -> None:
    """Load entity configuration from file.
    
    Args:
        config_path: Path to configuration file. If None, uses path from GameConstants.
    """
    if config_path is None:
        # Get path from GameConstants
        from config.game_constants import get_entity_config
        entity_config = get_entity_config()
        config_path = entity_config.ENTITIES_CONFIG_PATH
        
        # Make path relative to project root if it's not absolute
        if not os.path.isabs(config_path):
            config_dir = Path(__file__).parent.parent  # Go up to project root
            config_path = config_dir / config_path
    
    _entity_registry.load_from_file(str(config_path))
    
    logger.info(f"Entity configuration loaded: {len(_entity_registry.weapons)} weapons, "
               f"{len(_entity_registry.monsters)} monsters, {len(_entity_registry.armor)} armor, "
               f"{len(_entity_registry.rings)} rings")