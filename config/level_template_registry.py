"""
Level Template Registry - Manages level generation overrides and guaranteed spawns.

This module provides functionality to load and manage level templates from YAML files,
supporting both normal gameplay and testing mode configurations.

Tier 1: Guaranteed spawns
Tier 2: Level parameters and special themed rooms
"""

import os
import logging
import re
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field

import yaml

from config.testing_config import is_testing_mode


logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Exception raised when template validation fails."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, key_path: Optional[str] = None):
        """Initialize validation error.
        
        Args:
            message: Human-readable error message
            file_path: Path to config file
            key_path: Path to key in YAML (e.g., "level_overrides.15.special_rooms[0].min_room_size")
        """
        self.message = message
        self.file_path = file_path
        self.key_path = key_path
        
        full_message = message
        if file_path or key_path:
            context = []
            if file_path:
                context.append(f"File: {file_path}")
            if key_path:
                context.append(f"Key: {key_path}")
            full_message = f"{message}\n{' | '.join(context)}"
        
        super().__init__(full_message)


def parse_count_range(count_value: Union[int, str]) -> Tuple[int, int]:
    """
    Parse a count value that may be an integer or a range string.
    
    Args:
        count_value: Either an integer or a string like "3-5"
        
    Returns:
        Tuple of (min_count, max_count)
        
    Examples:
        parse_count_range(5) -> (5, 5)
        parse_count_range("3-5") -> (3, 5)
        parse_count_range("1-10") -> (1, 10)
    """
    if isinstance(count_value, int):
        return (count_value, count_value)
    
    if isinstance(count_value, str):
        # Try to parse range format "X-Y"
        match = re.match(r'^(\d+)-(\d+)$', count_value.strip())
        if match:
            min_val = int(match.group(1))
            max_val = int(match.group(2))
            if min_val <= max_val:
                return (min_val, max_val)
            else:
                logger.warning(
                    f"Invalid range '{count_value}': min > max, using ({max_val}, {min_val})"
                )
                return (max_val, min_val)
        
        # Try to parse as single integer
        try:
            val = int(count_value)
            return (val, val)
        except ValueError:
            pass
    
    logger.warning(f"Invalid count value '{count_value}', defaulting to (1, 1)")
    return (1, 1)


@dataclass
class DoorStyle:
    """Represents a door type with visual and mechanical properties."""
    type: str  # e.g., "wooden_door", "iron_door", "stone_door"
    weight: int  # Weight for weighted random selection


@dataclass
class DoorLocked:
    """Configuration for locked door behavior."""
    chance: float  # 0.0-1.0, probability that a door is locked
    key_tag: str = "iron_key"  # Default tag for keys that unlock this door


@dataclass
class DoorSecret:
    """Configuration for secret door behavior."""
    chance: float  # 0.0-1.0, probability that a door is secret
    search_dc: int = 12  # DC for search checks to reveal (higher = harder)


@dataclass
class HostilityRule:
    """Single hostility rule for faction interactions."""
    vs_faction: str  # Target faction (e.g., "undead")
    behavior: str = "attack"  # "attack", "ignore", "flee", "ally"


@dataclass
class RoomMetadata:
    """Metadata for room roles and ETP handling.
    
    Controls how rooms are treated by the ETP budgeting and sanity harness.
    """
    role: str = "normal"  # "normal", "miniboss", "boss", "end_boss", "treasure", "optional"
    allow_spike: bool = False  # If True, room can exceed ETP budget without being a violation
    etp_exempt: bool = False  # If True, room is completely exempt from ETP budget checks
    
    def is_special(self) -> bool:
        """Check if this is a special room (not normal).
        
        Returns:
            True if room has a special role or flags set
        """
        return (self.role != "normal" or 
                self.allow_spike or 
                self.etp_exempt)
    
    def get_etp_status_override(self) -> Optional[str]:
        """Get ETP status override for special rooms.
        
        Returns:
            Status string for special rooms, None for normal rooms
        """
        if self.etp_exempt:
            return "EXEMPT"
        if self.role == "end_boss":
            return "ENDBOSS"
        if self.role == "boss":
            return "BOSS"
        if self.role == "miniboss":
            return "MINIBOSS"
        if self.role in ("treasure", "optional"):
            return "SPIKE"
        if self.allow_spike:
            return "SPIKE"
        return None
    
    def should_count_as_violation(self) -> bool:
        """Check if an over-budget result should count as a violation.
        
        Returns:
            True if this room should be counted in violation statistics
        """
        # Special rooms don't count as violations
        return not self.is_special()


@dataclass
class EncounterBudget:
    """Configuration for encounter difficulty budgeting using ETP (Encounter Threat Points)."""
    etp_min: int  # Minimum total ETP for a room/level
    etp_max: int  # Maximum total ETP for a room/level
    allow_spike: bool = False  # If False, never exceed etp_max even if single entity would
    
    def is_valid(self) -> bool:
        """Validate budget configuration.
        
        Returns:
            True if min <= max and both are non-negative
        """
        return 0 <= self.etp_min <= self.etp_max
    
    def is_within_budget(self, current_etp: int) -> bool:
        """Check if current ETP is within budget range.
        
        Args:
            current_etp: Current total ETP
            
        Returns:
            True if etp_min <= current_etp <= etp_max
        """
        return self.etp_min <= current_etp <= self.etp_max
    
    def is_at_max(self, current_etp: int) -> bool:
        """Check if current ETP has reached the maximum.
        
        Args:
            current_etp: Current total ETP
            
        Returns:
            True if current_etp >= etp_max
        """
        return current_etp >= self.etp_max
    
    def can_fit(self, current_etp: int, entity_etp: int) -> bool:
        """Check if adding entity would exceed max (respecting allow_spike).
        
        Args:
            current_etp: Current total ETP
            entity_etp: ETP of entity to add
            
        Returns:
            True if entity can be added within budget constraints
        """
        new_total = current_etp + entity_etp
        
        if self.allow_spike:
            # allow_spike=True: can exceed max by one entity if currently under max
            return current_etp < self.etp_max
        else:
            # allow_spike=False: never exceed max
            return new_total <= self.etp_max


@dataclass
class FactionRoomConfig:
    """Configuration for faction-aware special rooms."""
    room_tag: str  # Tag for this room (e.g., "necropolis", "orc_hall")
    hostility_matrix: Dict[str, List[str]] = field(default_factory=dict)
    # Format: {"orc": ["undead", "goblin"], "undead": ["orc", "human"]}
    # Means: orcs attack undead and goblins; undead attack orcs and humans
    
    behavior_mods: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # Format: {"orc": {"door_priority": 0.8}, "troll": {"door_priority": 1.5}}
    # Modifies AI behavior for specific monster types in this room
    
    def get_hostility_targets(self, faction: str) -> List[str]:
        """Get factions this faction should attack in this room.
        
        Args:
            faction: The faction making the decision
            
        Returns:
            List of target factions to attack
        """
        return self.hostility_matrix.get(faction, [])
    
    def has_hostility_override(self, faction: str) -> bool:
        """Check if this room overrides hostility for a faction.
        
        Args:
            faction: The faction to check
            
        Returns:
            True if hostility rules exist for this faction
        """
        return faction in self.hostility_matrix
    
    def get_behavior_mods(self, monster_id: str) -> Dict[str, Any]:
        """Get behavior modifications for a specific monster type.
        
        Args:
            monster_id: Monster type (e.g., "orc", "troll")
            
        Returns:
            Dict of {parameter: value} modifications
        """
        return self.behavior_mods.get(monster_id, {})
    
    def has_behavior_mods(self, monster_id: str) -> bool:
        """Check if behavior mods exist for a monster type.
        
        Args:
            monster_id: Monster type
            
        Returns:
            True if mods are configured
        """
        return monster_id in self.behavior_mods


@dataclass
class ConnectivityConfig:
    """Configuration for dungeon connectivity and corridor generation."""
    min_connectivity: str = "mst"  # "mst" or "mst_plus_loops"
    loop_count: int = 0  # Additional loops to create (only for mst_plus_loops)
    corridor_style: str = "orthogonal"  # "orthogonal", "jagged", or "organic"
    door_every_n_tiles: int = 0  # Place doors every N tiles (0 = no regular placement)
    
    def uses_mst(self) -> bool:
        """Check if MST is used for baseline connectivity."""
        return self.min_connectivity in ["mst", "mst_plus_loops"]
    
    def add_loops(self) -> bool:
        """Check if additional loops should be added."""
        return self.min_connectivity == "mst_plus_loops" and self.loop_count > 0
    
    def validate(self) -> Tuple[bool, str]:
        """Validate configuration consistency.
        
        Returns:
            (is_valid, error_message)
        """
        if self.min_connectivity not in ["mst", "mst_plus_loops"]:
            return False, f"Invalid min_connectivity: {self.min_connectivity}"
        
        if self.corridor_style not in ["orthogonal", "jagged", "organic"]:
            return False, f"Invalid corridor_style: {self.corridor_style}"
        
        if self.loop_count < 0:
            return False, f"loop_count must be non-negative, got {self.loop_count}"
        
        if self.door_every_n_tiles < 0:
            return False, f"door_every_n_tiles must be non-negative, got {self.door_every_n_tiles}"
        
        if self.min_connectivity == "mst" and self.loop_count > 0:
            return False, "loop_count only valid with mst_plus_loops"
        
        return True, ""


@dataclass
class StairsSpawnRules:
    """Configuration for spawn behavior near stairs."""
    near_start_bias: float = 0.5  # 0.0-1.0: bias for spawning near stairs (higher = more near stairs)


@dataclass
class StairsConfig:
    """Configuration for stairs (up/down level transitions)."""
    up: bool = True  # Can go up (to previous floor)
    down: bool = True  # Can go down (to next floor)
    restrict_return_levels: int = 0  # Levels back that player cannot return to (0 = no restriction)
    spawn_rules: StairsSpawnRules = field(default_factory=StairsSpawnRules)
    
    def can_go_up(self) -> bool:
        """Check if player can go up from this level."""
        return self.up
    
    def can_go_down(self) -> bool:
        """Check if player can go down from this level."""
        return self.down
    
    def get_min_return_level(self, current_level: int) -> int:
        """Get the minimum level the player can return to from current level.
        
        Args:
            current_level: Current dungeon level
            
        Returns:
            Minimum level player can go to (or -1 if no restriction)
        """
        if self.restrict_return_levels <= 0:
            return 1  # Can go to any level
        return max(1, current_level - self.restrict_return_levels)


@dataclass
class TrapDetection:
    """Configuration for trap detection and discovery.
    
    This defines base detection parameters, but can be extended by:
    - Player skills or perks that modify detection chances
    - Scrolls/potions that temporarily boost detection
    - Equipment that enhances trap detection
    - Environmental modifiers (lighting, etc.)
    """
    passive_chance: float = 0.1  # Base chance to passively detect when entering tile (0.0-1.0)
    reveal_on: List[str] = field(default_factory=list)  # Item/condition tags that auto-reveal
    detectable: bool = True  # If False, trap cannot be detected (always hidden)


@dataclass
class TrapTableEntry:
    """Single entry in a trap table with weighted selection."""
    trap_id: str  # Trap type: "spike_trap", "web_trap", "alarm_plate", etc.
    weight: int  # Weight for weighted random selection


@dataclass
class TrapRules:
    """Configuration for trap generation and behavior."""
    density: float = 0.0  # 0.0-1.0: probability of trap in each room tile
    whitelist_rooms: List[str] = field(default_factory=list)  # Room types that CAN have traps (empty = all)
    trap_table: List[TrapTableEntry] = field(default_factory=list)  # Available traps with weights
    detection: TrapDetection = field(default_factory=TrapDetection)
    
    def get_random_trap(self) -> Optional[str]:
        """Select a trap type using weighted random selection.
        
        Returns:
            Trap ID or None if no traps available
        """
        if not self.trap_table:
            return None
        
        total_weight = sum(entry.weight for entry in self.trap_table)
        if total_weight <= 0:
            return None
        
        from random import random
        roll = random() * total_weight
        cumulative = 0
        
        for entry in self.trap_table:
            cumulative += entry.weight
            if roll <= cumulative:
                return entry.trap_id
        
        return self.trap_table[0].trap_id if self.trap_table else None


@dataclass
class SecretRoomsDiscovery:
    """Configuration for how secret rooms can be discovered."""
    auto_on_map_item: Optional[str] = None  # Item type that auto-reveals (e.g., "map_scroll")
    search_action: bool = True  # Can be revealed via search action
    ambient_hint: str = "?"  # Tile marker displayed outside secret room wall


@dataclass
class SecretRooms:
    """Configuration for secret room generation."""
    target_per_floor: int = 0  # How many secret rooms to attempt to create per level
    min_room_size: int = 5  # Minimum dimension for secret rooms
    connection_bias: str = "any"  # "dead_end" or "any" - where to place connections
    discovery: SecretRoomsDiscovery = field(default_factory=SecretRoomsDiscovery)
    
    def __post_init__(self):
        """Validate connection_bias."""
        if self.connection_bias not in ["dead_end", "any"]:
            logger.warning(
                f"Invalid connection_bias '{self.connection_bias}', "
                f"must be 'dead_end' or 'any', defaulting to 'any'"
            )
            self.connection_bias = "any"


@dataclass
class DoorRules:
    """Configuration for door placement and behavior in corridors."""
    spawn_ratio: float = 0.0  # 0.0-1.0, probability that a corridor gets a door
    styles: List['DoorStyle'] = field(default_factory=lambda: [DoorStyle(type="wooden_door", weight=1)])
    locked: Optional[DoorLocked] = None
    secret: Optional[DoorSecret] = None
    
    def get_random_style(self) -> str:
        """Select a door style using weighted random selection."""
        if not self.styles:
            return "wooden_door"
        
        total_weight = sum(s.weight for s in self.styles)
        if total_weight <= 0:
            return self.styles[0].type
        
        from random import random
        roll = random() * total_weight
        cumulative = 0
        
        for style in self.styles:
            cumulative += style.weight
            if roll <= cumulative:
                return style.type
        
        return self.styles[0].type


@dataclass
class GuaranteedSpawn:
    """Represents a guaranteed spawn (monster or item)."""
    entity_type: str
    count_min: int
    count_max: int
    
    def get_random_count(self) -> int:
        """Get a random count within the configured range."""
        from random import randint
        return randint(self.count_min, self.count_max)


@dataclass
class LevelParameters:
    """
    Parameters that control level generation.
    
    All parameters are optional - if not specified, defaults from
    GameConstants will be used.
    """
    max_rooms: Optional[int] = None
    min_room_size: Optional[int] = None
    max_room_size: Optional[int] = None
    max_monsters_per_room: Optional[int] = None
    max_items_per_room: Optional[int] = None
    map_width: Optional[int] = None  # Map width override (for testing camera scrolling)
    map_height: Optional[int] = None  # Map height override (for testing camera scrolling)
    vault_count: Optional[int] = None  # Number of vault rooms to generate (overrides random chance)
    
    def has_overrides(self) -> bool:
        """Check if any parameters are overridden."""
        return any([
            self.max_rooms is not None,
            self.min_room_size is not None,
            self.max_room_size is not None,
            self.max_monsters_per_room is not None,
            self.max_items_per_room is not None,
            self.map_width is not None,
            self.map_height is not None,
            self.vault_count is not None
        ])


@dataclass
class SpecialRoom:
    """
    Defines a special themed room with guaranteed spawns.
    
    Special rooms are selected from generated rooms based on size
    and placement strategy, then populated with guaranteed entities.
    """
    room_type: str
    count: int  # How many of this room type to create
    min_room_size: Optional[int] = None  # Minimum room size required
    placement: str = "random"  # "random", "largest", "smallest"
    guaranteed_monsters: List[GuaranteedSpawn] = field(default_factory=list)
    guaranteed_items: List[GuaranteedSpawn] = field(default_factory=list)
    guaranteed_equipment: List[GuaranteedSpawn] = field(default_factory=list)
    door_rules: Optional['DoorRules'] = None  # Optional door configuration for connections
    trap_rules: Optional['TrapRules'] = None  # Optional trap configuration for this room type
    faction: Optional['FactionRoomConfig'] = None  # Optional faction-aware behavior for this room
    encounter_budget: Optional['EncounterBudget'] = None  # Optional ETP budget for this room
    metadata: Optional['RoomMetadata'] = None  # Room role and ETP exemption settings
    
    @property
    def all_guaranteed_spawns(self) -> List[GuaranteedSpawn]:
        """Get all guaranteed spawns combined."""
        return (self.guaranteed_monsters + 
                self.guaranteed_items + 
                self.guaranteed_equipment)


@dataclass
class LevelOverride:
    """Represents overrides for a specific dungeon level."""
    level_number: int
    mode: str  # "additional" or "replace" (for Tier 1 guaranteed spawns)
    guaranteed_monsters: List[GuaranteedSpawn]
    guaranteed_items: List[GuaranteedSpawn]
    guaranteed_equipment: List[GuaranteedSpawn]
    guaranteed_map_features: List[GuaranteedSpawn] = field(default_factory=list)  # Chests, signposts, etc.
    parameters: Optional[LevelParameters] = None  # Tier 2
    special_rooms: List[SpecialRoom] = field(default_factory=list)  # Tier 2
    door_rules: Optional[DoorRules] = None  # Door configuration for corridor connections (Tier 2)
    secret_rooms: Optional[SecretRooms] = None  # Secret room configuration (Tier 2)
    trap_rules: Optional[TrapRules] = None  # Trap configuration for level (Tier 2)
    stairs: Optional[StairsConfig] = None  # Stairs configuration for level transitions (Tier 2)
    connectivity: Optional[ConnectivityConfig] = None  # Connectivity configuration (Tier 2)
    encounter_budget: Optional[EncounterBudget] = None  # Encounter difficulty budgeting (Tier 2)
    
    @property
    def all_guaranteed_spawns(self) -> List[GuaranteedSpawn]:
        """Get all guaranteed spawns combined (Tier 1 only)."""
        return (self.guaranteed_monsters + 
                self.guaranteed_items + 
                self.guaranteed_equipment +
                self.guaranteed_map_features)
    
    def has_special_rooms(self) -> bool:
        """Check if this override has any special rooms configured."""
        return len(self.special_rooms) > 0
    
    def has_parameters(self) -> bool:
        """Check if this override has level parameters configured."""
        return self.parameters is not None and self.parameters.has_overrides()
    
    def has_map_features(self) -> bool:
        """Check if this override has guaranteed map features configured."""
        return len(self.guaranteed_map_features) > 0


class LevelTemplateRegistry:
    """
    Manages level templates and overrides from YAML configuration files.
    
    Supports two configuration files:
    - level_templates.yaml: Normal gameplay overrides
    - level_templates_testing.yaml: Testing mode overrides (takes precedence)
    """
    
    def __init__(self):
        """Initialize the registry."""
        self.overrides: Dict[int, LevelOverride] = {}
        self.version: Optional[str] = None
        
    def load_templates(self, config_dir: Optional[str] = None) -> None:
        """
        Load level templates from YAML files.
        
        Args:
            config_dir: Directory containing template files. If None, uses default.
        """
        if config_dir is None:
            config_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__))
            )
        
        # Load normal templates first
        normal_template_path = os.path.join(config_dir, 'level_templates.yaml')
        self._load_template_file(normal_template_path, is_testing=False)
        
        # Load testing templates if in testing mode (these override normal templates)
        if is_testing_mode():
            testing_template_path = os.path.join(
                config_dir, 'level_templates_testing.yaml'
            )
            self._load_template_file(testing_template_path, is_testing=True)
            
    def _load_template_file(self, filepath: str, is_testing: bool = False) -> None:
        """
        Load a single template file.
        
        Args:
            filepath: Path to the YAML file
            is_testing: Whether this is the testing template file
        """
        if not os.path.exists(filepath):
            mode_str = "testing" if is_testing else "normal"
            logger.info(f"No {mode_str} level template file found at {filepath}, skipping")
            return
            
        try:
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
                
            if not data:
                logger.warning(f"Empty template file: {filepath}")
                return
                
            # Store version (last loaded file wins)
            self.version = data.get('version', 'unknown')
            
            # Parse level overrides
            level_overrides = data.get('level_overrides', {})
            for level_num, override_data in level_overrides.items():
                level_override = self._parse_level_override(level_num, override_data)
                
                # Testing templates override normal templates
                if is_testing or level_num not in self.overrides:
                    self.overrides[level_num] = level_override
                    mode_str = "testing" if is_testing else "normal"
                    logger.info(
                        f"Loaded {mode_str} template for level {level_num} "
                        f"(mode: {level_override.mode})"
                    )
                    
        except yaml.YAMLError as e:
            logger.error(f"Error parsing template file {filepath}: {e}")
        except Exception as e:
            logger.error(f"Error loading template file {filepath}: {e}")
            
    def _parse_level_override(
        self, 
        level_num: int, 
        data: Dict[str, Any]
    ) -> LevelOverride:
        """
        Parse a level override from YAML data.
        
        Supports both Tier 1 (guaranteed_spawns) and Tier 2 (parameters, special_rooms).
        
        Args:
            level_num: The level number
            data: The YAML data for this level
            
        Returns:
            LevelOverride object
        """
        # Parse Tier 1: guaranteed_spawns
        guaranteed_spawns = data.get('guaranteed_spawns', {})
        mode = guaranteed_spawns.get('mode', 'additional')
        
        # Validate mode
        if mode not in ['additional', 'replace']:
            logger.warning(
                f"Invalid mode '{mode}' for level {level_num}, "
                f"defaulting to 'additional'"
            )
            mode = 'additional'
        
        # Parse monsters
        monsters = []
        for monster_data in guaranteed_spawns.get('monsters', []):
            count_min, count_max = parse_count_range(monster_data['count'])
            monsters.append(GuaranteedSpawn(
                entity_type=monster_data['type'],
                count_min=count_min,
                count_max=count_max
            ))
            
        # Parse items
        items = []
        for item_data in guaranteed_spawns.get('items', []):
            count_min, count_max = parse_count_range(item_data['count'])
            items.append(GuaranteedSpawn(
                entity_type=item_data['type'],
                count_min=count_min,
                count_max=count_max
            ))
            
        # Parse equipment
        equipment = []
        for equip_data in guaranteed_spawns.get('equipment', []):
            count_min, count_max = parse_count_range(equip_data['count'])
            equipment.append(GuaranteedSpawn(
                entity_type=equip_data['type'],
                count_min=count_min,
                count_max=count_max
            ))
        
        # Parse map_features (chests, signposts, etc.)
        map_features = []
        for feature_data in guaranteed_spawns.get('map_features', []):
            count_min, count_max = parse_count_range(feature_data['count'])
            map_features.append(GuaranteedSpawn(
                entity_type=feature_data['type'],
                count_min=count_min,
                count_max=count_max
            ))
        
        # Parse Tier 2: parameters
        parameters = None
        if 'parameters' in data:
            params_data = data['parameters']
            parameters = LevelParameters(
                max_rooms=params_data.get('max_rooms'),
                min_room_size=params_data.get('min_room_size'),
                max_room_size=params_data.get('max_room_size'),
                max_monsters_per_room=params_data.get('max_monsters_per_room'),
                max_items_per_room=params_data.get('max_items_per_room'),
                map_width=params_data.get('map_width'),  # Support map size overrides
                map_height=params_data.get('map_height'),
                vault_count=params_data.get('vault_count')  # Guaranteed vault rooms
            )
            
        # Parse Tier 2: special_rooms
        special_rooms = []
        for room_data in data.get('special_rooms', []):
            special_room = self._parse_special_room(room_data)
            special_rooms.append(special_room)
        
        # Parse Tier 2: door_rules (for corridor connections)
        door_rules = None
        if 'door_rules' in data:
            door_rules = self._parse_door_rules(data['door_rules'])
        
        # Parse Tier 2: secret_rooms (for secret room generation)
        secret_rooms = None
        if 'secret_rooms' in data:
            secret_rooms = self._parse_secret_rooms(data['secret_rooms'])
        
        # Parse Tier 2: trap_rules (for trap placement)
        trap_rules = None
        if 'trap_rules' in data:
            trap_rules = self._parse_trap_rules(data['trap_rules'])
        
        # Parse Tier 2: stairs (for level transitions)
        stairs_config = None
        if 'stairs' in data:
            stairs_config = self._parse_stairs(data['stairs'])
        
        # Parse Tier 2: connectivity (for dungeon layout)
        connectivity_config = None
        if 'connectivity' in data:
            connectivity_config = self._parse_connectivity(data['connectivity'])
        
        # Parse Tier 2: encounter_budget (ETP budgeting)
        encounter_budget_config = None
        if 'encounter_budget' in data:
            encounter_budget_config = self._parse_encounter_budget(data['encounter_budget'])
            
        return LevelOverride(
            level_number=level_num,
            mode=mode,
            guaranteed_monsters=monsters,
            guaranteed_items=items,
            guaranteed_equipment=equipment,
            guaranteed_map_features=map_features,
            parameters=parameters,
            special_rooms=special_rooms,
            door_rules=door_rules,
            secret_rooms=secret_rooms,
            trap_rules=trap_rules,
            stairs=stairs_config,
            connectivity=connectivity_config,
            encounter_budget=encounter_budget_config
        )
    
    def _parse_special_room(self, data: Dict[str, Any]) -> SpecialRoom:
        """
        Parse a special room definition from YAML data.
        
        Args:
            data: The YAML data for this special room
            
        Returns:
            SpecialRoom object
        """
        room_type = data.get('type', 'unknown')
        count = data.get('count', 1)
        min_room_size = data.get('min_room_size')
        placement = data.get('placement', 'random')
        
        # Validate placement strategy
        if placement not in ['random', 'largest', 'smallest']:
            logger.warning(
                f"Invalid placement '{placement}' for special room '{room_type}', "
                f"defaulting to 'random'"
            )
            placement = 'random'
        
        # Parse guaranteed spawns for this room
        spawns_data = data.get('guaranteed_spawns', {})
        
        monsters = []
        for monster_data in spawns_data.get('monsters', []):
            count_min, count_max = parse_count_range(monster_data['count'])
            monsters.append(GuaranteedSpawn(
                entity_type=monster_data['type'],
                count_min=count_min,
                count_max=count_max
            ))
        
        items = []
        for item_data in spawns_data.get('items', []):
            count_min, count_max = parse_count_range(item_data['count'])
            items.append(GuaranteedSpawn(
                entity_type=item_data['type'],
                count_min=count_min,
                count_max=count_max
            ))
        
        equipment = []
        for equip_data in spawns_data.get('equipment', []):
            count_min, count_max = parse_count_range(equip_data['count'])
            equipment.append(GuaranteedSpawn(
                entity_type=equip_data['type'],
                count_min=count_min,
                count_max=count_max
            ))
        
        # Parse door_rules for this special room (optional, overrides level door_rules)
        door_rules = None
        if 'door_rules' in data:
            door_rules = self._parse_door_rules(data['door_rules'])
        
        # Parse trap_rules for this special room (optional, overrides level trap_rules)
        trap_rules = None
        if 'trap_rules' in data:
            trap_rules = self._parse_trap_rules(data['trap_rules'])
        
        # Parse faction config for this special room (faction-aware behavior)
        faction_config = None
        if 'faction' in data:
            faction_config = self._parse_faction_config(data['faction'])
        
        # Parse encounter_budget for this special room (optional ETP budget)
        encounter_budget_config = None
        if 'encounter_budget' in data:
            encounter_budget_config = self._parse_encounter_budget(data['encounter_budget'])
        
        # Parse room metadata (role, allow_spike, etp_exempt)
        # Metadata is nested under 'metadata' key in special rooms
        metadata_data = data.get('metadata', {})
        room_metadata = self._parse_room_metadata(metadata_data)
        
        return SpecialRoom(
            room_type=room_type,
            count=count,
            min_room_size=min_room_size,
            placement=placement,
            guaranteed_monsters=monsters,
            guaranteed_items=items,
            guaranteed_equipment=equipment,
            door_rules=door_rules,
            trap_rules=trap_rules,
            faction=faction_config,
            encounter_budget=encounter_budget_config,
            metadata=room_metadata
        )
    
    def _parse_door_rules(self, data: Dict[str, Any]) -> DoorRules:
        """
        Parse door rules configuration from YAML data.
        
        Door style types must correspond to entity IDs in entities.yaml (e.g., 'wooden_door', 'iron_door').
        Invalid door types will be logged at load time to aid debugging.
        
        Args:
            data: The YAML data for door_rules
            
        Returns:
            DoorRules object
        """
        spawn_ratio = data.get('spawn_ratio', 0.0)
        
        # Validate spawn_ratio
        if not 0.0 <= spawn_ratio <= 1.0:
            logger.warning(
                f"Invalid spawn_ratio '{spawn_ratio}', must be 0.0-1.0, "
                f"defaulting to 0.0"
            )
            spawn_ratio = 0.0
        
        # Parse door styles with weights and validate entity IDs
        styles = []
        invalid_styles = []
        for style_data in data.get('styles', []):
            style_type = style_data.get('type', 'wooden_door')
            weight = style_data.get('weight', 1)
            
            # Validate weight
            if not isinstance(weight, int) or weight < 0:
                logger.warning(
                    f"Invalid weight '{weight}' for door style '{style_type}', "
                    f"using weight 1"
                )
                weight = 1
            
            # Validate that the door style corresponds to a valid entity ID
            # This is done at configuration load time (not per-placement) to avoid log spam
            if not self._is_valid_door_entity(style_type):
                invalid_styles.append(style_type)
                logger.warning(
                    f"Door style '{style_type}' does not match any door entity in entities.yaml; "
                    f"doors of this style will not be created during level generation. "
                    f"Valid door entities: wooden_door, iron_door, stone_door, bronze_door, silver_door, gold_door, crimson_door"
                )
            
            styles.append(DoorStyle(type=style_type, weight=weight))
        
        # Default to wooden_door if no styles specified
        if not styles:
            styles = [DoorStyle(type="wooden_door", weight=1)]
        
        # Parse locked configuration
        locked = None
        if 'locked' in data and data['locked']:
            locked_data = data['locked']
            locked_chance = locked_data.get('chance', 0.0)
            key_tag = locked_data.get('key_tag', 'iron_key')
            
            # Validate chance
            if not 0.0 <= locked_chance <= 1.0:
                logger.warning(
                    f"Invalid locked chance '{locked_chance}', must be 0.0-1.0, "
                    f"defaulting to 0.0"
                )
                locked_chance = 0.0
            
            if locked_chance > 0.0:
                locked = DoorLocked(chance=locked_chance, key_tag=key_tag)
        
        # Parse secret configuration
        secret = None
        if 'secret' in data and data['secret']:
            secret_data = data['secret']
            secret_chance = secret_data.get('chance', 0.0)
            search_dc = secret_data.get('search_dc', 12)
            
            # Validate chance
            if not 0.0 <= secret_chance <= 1.0:
                logger.warning(
                    f"Invalid secret chance '{secret_chance}', must be 0.0-1.0, "
                    f"defaulting to 0.0"
                )
                secret_chance = 0.0
            
            # Validate search_dc
            if not isinstance(search_dc, int) or search_dc < 0:
                logger.warning(
                    f"Invalid search_dc '{search_dc}', must be non-negative integer, "
                    f"defaulting to 12"
                )
                search_dc = 12
            
            if secret_chance > 0.0:
                secret = DoorSecret(chance=secret_chance, search_dc=search_dc)
        
        return DoorRules(
            spawn_ratio=spawn_ratio,
            styles=styles,
            locked=locked,
            secret=secret
        )
    
    def _is_valid_door_entity(self, door_type: str) -> bool:
        """Check if a door type corresponds to a valid door entity in entities.yaml.
        
        This method validates door style IDs at configuration load time to provide
        early feedback on invalid door type references in door_rules configurations.
        
        Args:
            door_type: The door type string to validate (e.g., 'wooden_door', 'iron_door')
            
        Returns:
            True if the door type exists as a map_feature entity, False otherwise
        """
        # List of all valid door entities defined in entities.yaml
        # These are the only valid values for door_rules.styles[*].type
        valid_doors = {
            'wooden_door',      # Standard corridor door
            'iron_door',        # Standard corridor door
            'stone_door',       # Standard corridor door
            'bronze_door',      # Locked vault door
            'silver_door',      # Locked vault door
            'gold_door',        # Locked vault door
            'crimson_door',     # Locked vault door (dragon-themed)
        }
        
        return door_type in valid_doors
    
    def _parse_secret_rooms(self, data: Dict[str, Any]) -> SecretRooms:
        """
        Parse secret rooms configuration from YAML data.
        
        Args:
            data: The YAML data for secret_rooms
            
        Returns:
            SecretRooms object
        """
        target_per_floor = data.get('target_per_floor', 0)
        min_room_size = data.get('min_room_size', 5)
        connection_bias = data.get('connection_bias', 'any')
        
        # Validate target_per_floor
        if not isinstance(target_per_floor, int) or target_per_floor < 0:
            logger.warning(
                f"Invalid target_per_floor '{target_per_floor}', must be non-negative integer, "
                f"defaulting to 0"
            )
            target_per_floor = 0
        
        # Validate min_room_size
        if not isinstance(min_room_size, int) or min_room_size < 3:
            logger.warning(
                f"Invalid min_room_size '{min_room_size}', must be >= 3, "
                f"defaulting to 5"
            )
            min_room_size = 5
        
        # Validate connection_bias
        if connection_bias not in ['dead_end', 'any']:
            logger.warning(
                f"Invalid connection_bias '{connection_bias}', must be 'dead_end' or 'any', "
                f"defaulting to 'any'"
            )
            connection_bias = 'any'
        
        # Parse discovery configuration
        discovery_data = data.get('discovery', {})
        discovery = SecretRoomsDiscovery(
            auto_on_map_item=discovery_data.get('auto_on_map_item'),
            search_action=discovery_data.get('search_action', True),
            ambient_hint=discovery_data.get('ambient_hint', '?')
        )
        
        return SecretRooms(
            target_per_floor=target_per_floor,
            min_room_size=min_room_size,
            connection_bias=connection_bias,
            discovery=discovery
        )
    
    def _parse_trap_rules(self, data: Dict[str, Any]) -> TrapRules:
        """
        Parse trap rules configuration from YAML data.
        
        Args:
            data: The YAML data for trap_rules
            
        Returns:
            TrapRules object
        """
        density = data.get('density', 0.0)
        whitelist_rooms = data.get('whitelist_rooms', [])
        
        # Validate density
        if not 0.0 <= density <= 1.0:
            logger.warning(
                f"Invalid density '{density}', must be 0.0-1.0, "
                f"defaulting to 0.0"
            )
            density = 0.0
        
        # Validate whitelist_rooms
        if not isinstance(whitelist_rooms, list):
            logger.warning(
                f"Invalid whitelist_rooms, must be list, "
                f"defaulting to []"
            )
            whitelist_rooms = []
        
        # Parse trap table
        trap_table = []
        for trap_data in data.get('trap_table', []):
            trap_id = trap_data.get('id', 'unknown')
            weight = trap_data.get('weight', 1)
            
            # Validate weight
            if not isinstance(weight, int) or weight < 0:
                logger.warning(
                    f"Invalid weight '{weight}' for trap '{trap_id}', using weight 1"
                )
                weight = 1
            
            trap_table.append(TrapTableEntry(trap_id=trap_id, weight=weight))
        
        # Parse detection configuration
        detection_data = data.get('detection', {})
        passive_chance = detection_data.get('passive_chance', 0.1)
        detectable = detection_data.get('detectable', True)
        
        # Validate passive_chance
        if not 0.0 <= passive_chance <= 1.0:
            logger.warning(
                f"Invalid passive_chance '{passive_chance}', must be 0.0-1.0, "
                f"defaulting to 0.1"
            )
            passive_chance = 0.1
        
        # Validate detectable
        if not isinstance(detectable, bool):
            logger.warning(
                f"Invalid detectable '{detectable}', must be boolean, "
                f"defaulting to True"
            )
            detectable = True
        
        detection = TrapDetection(
            passive_chance=passive_chance,
            reveal_on=detection_data.get('reveal_on', []),
            detectable=detectable
        )
        
        return TrapRules(
            density=density,
            whitelist_rooms=whitelist_rooms,
            trap_table=trap_table,
            detection=detection
        )
        
    def _parse_connectivity(self, data: Dict[str, Any]) -> ConnectivityConfig:
        """
        Parse connectivity configuration from YAML data.
        
        Args:
            data: The YAML data for connectivity
            
        Returns:
            ConnectivityConfig object
        """
        min_connectivity = data.get('min_connectivity', 'mst')
        loop_count = data.get('loop_count', 0)
        corridor_style = data.get('corridor_style', 'orthogonal')
        door_every_n_tiles = data.get('door_every_n_tiles', 0)
        
        # Validate min_connectivity
        if min_connectivity not in ['mst', 'mst_plus_loops']:
            logger.warning(
                f"Invalid min_connectivity '{min_connectivity}', must be 'mst' or 'mst_plus_loops', "
                f"defaulting to 'mst'"
            )
            min_connectivity = 'mst'
        
        # Validate loop_count
        if not isinstance(loop_count, int) or loop_count < 0:
            logger.warning(
                f"Invalid loop_count '{loop_count}', must be non-negative integer, "
                f"defaulting to 0"
            )
            loop_count = 0
        
        # Validate corridor_style
        if corridor_style not in ['orthogonal', 'jagged', 'organic']:
            logger.warning(
                f"Invalid corridor_style '{corridor_style}', must be 'orthogonal', 'jagged', or 'organic', "
                f"defaulting to 'orthogonal'"
            )
            corridor_style = 'orthogonal'
        
        # Validate door_every_n_tiles
        if not isinstance(door_every_n_tiles, int) or door_every_n_tiles < 0:
            logger.warning(
                f"Invalid door_every_n_tiles '{door_every_n_tiles}', must be non-negative integer, "
                f"defaulting to 0"
            )
            door_every_n_tiles = 0
        
        # Warn if loop_count used with non-plus_loops
        if min_connectivity == 'mst' and loop_count > 0:
            logger.warning(
                f"loop_count specified with min_connectivity='mst' (requires 'mst_plus_loops'), ignoring"
            )
            loop_count = 0
        
        config = ConnectivityConfig(
            min_connectivity=min_connectivity,
            loop_count=loop_count,
            corridor_style=corridor_style,
            door_every_n_tiles=door_every_n_tiles
        )
        
        # Validate full config
        is_valid, error_msg = config.validate()
        if not is_valid:
            logger.warning(f"Connectivity config validation failed: {error_msg}")
        
        return config
    
    def _parse_stairs(self, data: Dict[str, Any]) -> StairsConfig:
        """
        Parse stairs configuration from YAML data.
        
        Args:
            data: The YAML data for stairs
            
        Returns:
            StairsConfig object
        """
        up = data.get('up', True)
        down = data.get('down', True)
        restrict_return_levels = data.get('restrict_return_levels', 0)
        
        # Validate restrict_return_levels
        if not isinstance(restrict_return_levels, int) or restrict_return_levels < 0:
            logger.warning(
                f"Invalid restrict_return_levels '{restrict_return_levels}', must be non-negative integer, "
                f"defaulting to 0"
            )
            restrict_return_levels = 0
        
        # Parse spawn_rules
        spawn_rules_data = data.get('spawn_rules', {})
        near_start_bias = spawn_rules_data.get('near_start_bias', 0.5)
        
        # Validate near_start_bias
        if not 0.0 <= near_start_bias <= 1.0:
            logger.warning(
                f"Invalid near_start_bias '{near_start_bias}', must be 0.0-1.0, "
                f"defaulting to 0.5"
            )
            near_start_bias = 0.5
        
        spawn_rules = StairsSpawnRules(near_start_bias=near_start_bias)
        
        return StairsConfig(
            up=up,
            down=down,
            restrict_return_levels=restrict_return_levels,
            spawn_rules=spawn_rules
        )
    
    def _parse_encounter_budget(self, data: Dict[str, Any]) -> EncounterBudget:
        """
        Parse encounter budget configuration from YAML data.
        
        Args:
            data: The YAML data for encounter_budget
            
        Returns:
            EncounterBudget object
        """
        etp_min = data.get('etp_min', 0)
        etp_max = data.get('etp_max', 100)
        allow_spike = data.get('allow_spike', False)
        
        # Validate etp_min
        if not isinstance(etp_min, (int, float)) or etp_min < 0:
            logger.warning(
                f"Invalid etp_min '{etp_min}', must be non-negative number, "
                f"defaulting to 0"
            )
            etp_min = 0
        
        # Validate etp_max
        if not isinstance(etp_max, (int, float)) or etp_max < 0:
            logger.warning(
                f"Invalid etp_max '{etp_max}', must be non-negative number, "
                f"defaulting to 100"
            )
            etp_max = 100
        
        # Validate allow_spike
        if not isinstance(allow_spike, bool):
            logger.warning(
                f"Invalid allow_spike '{allow_spike}', must be boolean, "
                f"defaulting to False"
            )
            allow_spike = False
        
        # Validate that min <= max
        if etp_min > etp_max:
            logger.warning(
                f"etp_min ({etp_min}) > etp_max ({etp_max}), swapping values"
            )
            etp_min, etp_max = etp_max, etp_min
        
        budget = EncounterBudget(
            etp_min=int(etp_min),
            etp_max=int(etp_max),
            allow_spike=allow_spike
        )
        
        logger.debug(f"Parsed encounter budget: ETP {etp_min}-{etp_max}, allow_spike={allow_spike}")
        
        return budget
    
    def _parse_room_metadata(self, data: Dict[str, Any]) -> RoomMetadata:
        """
        Parse room metadata from YAML data.
        
        Handles room roles, ETP spike allowance, and exemptions.
        
        Args:
            data: The YAML data for the room
            
        Returns:
            RoomMetadata object
        """
        # Valid room roles
        valid_roles = {"normal", "miniboss", "boss", "end_boss", "treasure", "optional"}
        
        role = data.get('role', 'normal')
        allow_spike = data.get('allow_spike', False)
        etp_exempt = data.get('etp_exempt', False)
        
        # Validate role
        if role not in valid_roles:
            logger.warning(
                f"Invalid room role '{role}', must be one of {valid_roles}, "
                f"defaulting to 'normal'"
            )
            role = 'normal'
        
        # Validate allow_spike
        if not isinstance(allow_spike, bool):
            logger.warning(
                f"Invalid allow_spike '{allow_spike}', must be boolean, "
                f"defaulting to False"
            )
            allow_spike = False
        
        # Validate etp_exempt
        if not isinstance(etp_exempt, bool):
            logger.warning(
                f"Invalid etp_exempt '{etp_exempt}', must be boolean, "
                f"defaulting to False"
            )
            etp_exempt = False
        
        # Auto-set allow_spike for certain roles if not explicitly set
        if role in ('boss', 'miniboss', 'end_boss', 'treasure', 'optional') and not allow_spike:
            # Boss and treasure rooms should generally allow spikes
            allow_spike = True
            logger.debug(f"Auto-enabled allow_spike for room role '{role}'")
        
        metadata = RoomMetadata(
            role=role,
            allow_spike=allow_spike,
            etp_exempt=etp_exempt
        )
        
        if metadata.is_special():
            logger.debug(f"Parsed room metadata: role={role}, allow_spike={allow_spike}, etp_exempt={etp_exempt}")
        
        return metadata
        
    def get_level_override(self, level_number: int) -> Optional[LevelOverride]:
        """
        Get the override configuration for a specific level.
        
        Args:
            level_number: The dungeon level number
            
        Returns:
            LevelOverride if configured, None otherwise
        """
        return self.overrides.get(level_number)
        
    def _parse_faction_config(self, data: Dict[str, Any]) -> FactionRoomConfig:
        """
        Parse faction room configuration from YAML data.
        
        Args:
            data: The YAML data for faction config
            
        Returns:
            FactionRoomConfig object
        """
        room_tag = data.get('room_tag', 'untagged')
        hostility_matrix = data.get('hostility_matrix', {})
        behavior_mods = data.get('behavior_mods', {})
        
        # Validate hostility_matrix
        if not isinstance(hostility_matrix, dict):
            logger.warning(
                f"Invalid hostility_matrix type, expected dict, "
                f"defaulting to empty"
            )
            hostility_matrix = {}
        
        # Ensure all values in hostility_matrix are lists
        for faction, targets in list(hostility_matrix.items()):
            if not isinstance(targets, list):
                logger.warning(
                    f"Invalid hostility targets for {faction}, expected list, "
                    f"converting to list"
                )
                hostility_matrix[faction] = [targets] if targets else []
        
        # Validate behavior_mods
        if not isinstance(behavior_mods, dict):
            logger.warning(
                f"Invalid behavior_mods type, expected dict, "
                f"defaulting to empty"
            )
            behavior_mods = {}
        
        # Ensure all monster mods are dicts
        for monster_id, mods in list(behavior_mods.items()):
            if not isinstance(mods, dict):
                logger.warning(
                    f"Invalid mods for {monster_id}, expected dict, "
                    f"defaulting to empty"
                )
                behavior_mods[monster_id] = {}
        
        config = FactionRoomConfig(
            room_tag=room_tag,
            hostility_matrix=hostility_matrix,
            behavior_mods=behavior_mods
        )
        
        logger.debug(f"Parsed faction config for room '{room_tag}': "
                    f"{len(hostility_matrix)} hostility rules, "
                    f"{len(behavior_mods)} behavior mods")
        
        return config
    
    def has_override(self, level_number: int) -> bool:
        """
        Check if a level has an override configured.
        
        Args:
            level_number: The dungeon level number
            
        Returns:
            True if override exists, False otherwise
        """
        return level_number in self.overrides
        
    def clear(self) -> None:
        """Clear all loaded overrides (useful for testing)."""
        self.overrides.clear()
        self.version = None
    
    def validate_templates(self) -> None:
        """Validate all loaded templates for consistency and correctness.
        
        Checks:
        - Entity IDs exist in entity factory
        - Count ranges are valid
        - Modes and placements are valid
        - Special room sizes fit within level max_room_size
        - Encounter budgets are consistent
        
        Raises:
            ValidationError: If any validation fails
        """
        from config.entity_factory import get_entity_factory
        
        factory = get_entity_factory()
        warnings = []
        
        for level_num, override in self.overrides.items():
            level_key = f"level_overrides.{level_num}"
            
            # Validate mode
            if override.mode not in ["additional", "replace"]:
                raise ValidationError(
                    f"Invalid mode '{override.mode}', must be 'additional' or 'replace'",
                    key_path=f"{level_key}.mode"
                )
            
            # Validate guaranteed spawns
            for idx, spawn in enumerate(override.guaranteed_monsters):
                if not factory.is_valid_entity(spawn.entity_type, "monster"):
                    raise ValidationError(
                        f"Invalid monster entity type '{spawn.entity_type}' does not exist",
                        key_path=f"{level_key}.guaranteed_spawns.monsters[{idx}].type"
                    )
                
                if spawn.count_min < 0 or spawn.count_max < spawn.count_min:
                    raise ValidationError(
                        f"Invalid count range {spawn.count_min}-{spawn.count_max}",
                        key_path=f"{level_key}.guaranteed_spawns.monsters[{idx}].count"
                    )
            
            for idx, spawn in enumerate(override.guaranteed_items):
                if not factory.is_valid_entity(spawn.entity_type, "item"):
                    raise ValidationError(
                        f"Invalid item entity type '{spawn.entity_type}' does not exist",
                        key_path=f"{level_key}.guaranteed_spawns.items[{idx}].type"
                    )
            
            for idx, spawn in enumerate(override.guaranteed_equipment):
                if not factory.is_valid_entity(spawn.entity_type, "equipment"):
                    raise ValidationError(
                        f"Invalid equipment entity type '{spawn.entity_type}' does not exist",
                        key_path=f"{level_key}.guaranteed_spawns.equipment[{idx}].type"
                    )
            
            # Validate special rooms
            max_room_size = override.parameters.max_room_size if override.parameters else 16
            
            for idx, special_room in enumerate(override.special_rooms):
                room_key = f"{level_key}.special_rooms[{idx}]"
                
                # Validate placement
                if special_room.placement not in ["random", "largest", "smallest"]:
                    raise ValidationError(
                        f"Invalid placement '{special_room.placement}', "
                        f"must be 'random', 'largest', or 'smallest'",
                        key_path=f"{room_key}.placement"
                    )
                
                # Validate min_room_size
                if special_room.min_room_size and special_room.min_room_size > max_room_size:
                    warnings.append(
                        f"Special room min_room_size {special_room.min_room_size} "
                        f"exceeds level max_room_size {max_room_size} "
                        f"(key: {room_key}.min_room_size)"
                    )
                
                # Validate guaranteed spawns
                for sidx, spawn in enumerate(special_room.guaranteed_monsters):
                    if not factory.is_valid_entity(spawn.entity_type, "monster"):
                        raise ValidationError(
                            f"Invalid monster entity type '{spawn.entity_type}' does not exist",
                            key_path=f"{room_key}.guaranteed_spawns.monsters[{sidx}].type"
                        )
            
            # Validate encounter budget
            if override.encounter_budget and override.parameters:
                budget = override.encounter_budget
                params = override.parameters
                
                if not budget.is_valid():
                    raise ValidationError(
                        f"Invalid encounter budget: etp_min {budget.etp_min} > etp_max {budget.etp_max}",
                        key_path=f"{level_key}.encounter_budget"
                    )
                
                # Warn if budget seems inconsistent with max_monsters
                if params.max_monsters_per_room:
                    # Rough heuristic: with 1 ETP per monster on average,
                    # budget should be somewhat aligned with monster count
                    expected_min_etp = params.max_monsters_per_room
                    expected_max_etp = params.max_monsters_per_room * 3
                    
                    if budget.etp_max < expected_min_etp / 2:
                        warnings.append(
                            f"Encounter budget etp_max {budget.etp_max} seems low for "
                            f"max_monsters_per_room {params.max_monsters_per_room} "
                            f"(key: {level_key}.encounter_budget)"
                        )
        
        # Log warnings
        for warning in warnings:
            logger.warning(f"Template validation warning: {warning}")
        
        if warnings:
            logger.info(f"Template validation complete with {len(warnings)} warnings")
        else:
            logger.info("Template validation complete - all checks passed")


# Global registry instance
_level_template_registry: Optional[LevelTemplateRegistry] = None


def get_level_template_registry() -> LevelTemplateRegistry:
    """
    Get the global level template registry instance.
    
    Returns:
        The global LevelTemplateRegistry instance
    """
    global _level_template_registry
    if _level_template_registry is None:
        _level_template_registry = LevelTemplateRegistry()
        _level_template_registry.load_templates()
    return _level_template_registry


def load_level_templates() -> None:
    """Load (or reload) level templates from YAML files."""
    global _level_template_registry
    _level_template_registry = LevelTemplateRegistry()
    _level_template_registry.load_templates()

