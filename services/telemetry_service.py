"""Telemetry service for collecting gameplay metrics.

This module handles recording and dumping gameplay telemetry including:
- Encounter difficulty (ETP)
- Combat metrics (TTK, TTD)
- Map features (traps, secrets, doors)
- Item usage (keys)
- Pity events (loot rebalancing)
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class FloorTelemetry:
    """Telemetry data for a single floor.
    
    Attributes:
        depth: Floor number (1-based)
        timestamp: ISO8601 timestamp when floor was generated
        etp_sum: Total Encounter Threat Points for all monsters on floor
        etp_budget_min: Minimum ETP budget if configured
        etp_budget_max: Maximum ETP budget if configured
        ttk_hist: Time-to-kill histogram (damage values dealt to mobs)
        ttd_hist: Time-to-death histogram (damage dealt to player)
        traps_triggered: Count of traps triggered
        traps_detected: Count of traps detected
        secrets_found: Count of secret rooms found
        doors_opened: Count of doors opened
        doors_unlocked: Count of doors unlocked
        keys_used: Count of keys consumed
        pity_events: List of pity mechanism triggers
        room_count: Total rooms on floor
        monster_count: Total monsters spawned
        item_count: Total items spawned
    """
    depth: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    etp_sum: int = 0
    etp_budget_min: Optional[int] = None
    etp_budget_max: Optional[int] = None
    ttk_hist: List[int] = field(default_factory=list)  # Damage values when killing mobs
    ttd_hist: List[int] = field(default_factory=list)  # Damage taken by player
    traps_triggered: int = 0
    traps_detected: int = 0
    secrets_found: int = 0
    doors_opened: int = 0
    doors_unlocked: int = 0
    keys_used: int = 0
    pity_events: List[Dict[str, Any]] = field(default_factory=list)
    room_count: int = 0
    monster_count: int = 0
    item_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation
        """
        return asdict(self)
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update fields from dictionary.
        
        Args:
            data: Dictionary with field values to update
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)


class TelemetryService:
    """Service for collecting and dumping gameplay telemetry."""
    
    def __init__(self, output_path: Optional[str] = None):
        """Initialize telemetry service.
        
        Args:
            output_path: Path to write telemetry JSON (None = no output)
        """
        self.output_path = Path(output_path) if output_path else None
        self.floors: Dict[int, FloorTelemetry] = {}
        self.current_floor: Optional[int] = None
        self.enabled = output_path is not None
        
        if self.enabled:
            logger.info(f"Telemetry service enabled: {self.output_path}")
        else:
            logger.debug("Telemetry service disabled (no output path)")
    
    def start_floor(self, depth: int) -> None:
        """Start recording telemetry for a new floor.
        
        Args:
            depth: Floor number (1-based)
        """
        if not self.enabled:
            return
        
        self.current_floor = depth
        self.floors[depth] = FloorTelemetry(depth=depth)
        logger.debug(f"Started telemetry for floor {depth}")
    
    def end_floor(self) -> None:
        """End recording telemetry for current floor."""
        if not self.enabled or self.current_floor is None:
            return
        
        floor = self.floors.get(self.current_floor)
        if floor:
            logger.debug(f"Ended telemetry for floor {self.current_floor}: "
                        f"ETP={floor.etp_sum}, Traps={floor.traps_triggered}, "
                        f"Secrets={floor.secrets_found}")
        
        self.current_floor = None
    
    def set_floor_etp(self, etp_sum: int, budget_min: Optional[int] = None, 
                      budget_max: Optional[int] = None) -> None:
        """Set ETP sum for current floor.
        
        Args:
            etp_sum: Total ETP
            budget_min: Budget minimum if applicable
            budget_max: Budget maximum if applicable
        """
        if not self.enabled or self.current_floor is None:
            return
        
        floor = self.floors.get(self.current_floor)
        if floor:
            floor.etp_sum = etp_sum
            floor.etp_budget_min = budget_min
            floor.etp_budget_max = budget_max
    
    def set_room_counts(self, rooms: int, monsters: int, items: int) -> None:
        """Set spawn counts for current floor.
        
        Args:
            rooms: Total rooms
            monsters: Total monsters
            items: Total items
        """
        if not self.enabled or self.current_floor is None:
            return
        
        floor = self.floors.get(self.current_floor)
        if floor:
            floor.room_count = rooms
            floor.monster_count = monsters
            floor.item_count = items
    
    def record_ttk(self, damage: int) -> None:
        """Record damage dealt when defeating a mob.
        
        Args:
            damage: Damage value
        """
        if not self.enabled or self.current_floor is None:
            return
        
        floor = self.floors.get(self.current_floor)
        if floor:
            floor.ttk_hist.append(damage)
    
    def record_ttd(self, damage: int) -> None:
        """Record damage taken by player.
        
        Args:
            damage: Damage value
        """
        if not self.enabled or self.current_floor is None:
            return
        
        floor = self.floors.get(self.current_floor)
        if floor:
            floor.ttd_hist.append(damage)
    
    def record_trap_triggered(self) -> None:
        """Record a trap being triggered."""
        if not self.enabled or self.current_floor is None:
            return
        
        floor = self.floors.get(self.current_floor)
        if floor:
            floor.traps_triggered += 1
    
    def record_trap_detected(self) -> None:
        """Record a trap being detected."""
        if not self.enabled or self.current_floor is None:
            return
        
        floor = self.floors.get(self.current_floor)
        if floor:
            floor.traps_detected += 1
    
    def record_secret_found(self) -> None:
        """Record a secret room being found."""
        if not self.enabled or self.current_floor is None:
            return
        
        floor = self.floors.get(self.current_floor)
        if floor:
            floor.secrets_found += 1
    
    def record_door_opened(self) -> None:
        """Record a door being opened."""
        if not self.enabled or self.current_floor is None:
            return
        
        floor = self.floors.get(self.current_floor)
        if floor:
            floor.doors_opened += 1
    
    def record_door_unlocked(self) -> None:
        """Record a door being unlocked with a key."""
        if not self.enabled or self.current_floor is None:
            return
        
        floor = self.floors.get(self.current_floor)
        if floor:
            floor.doors_unlocked += 1
    
    def record_key_used(self) -> None:
        """Record a key being used."""
        if not self.enabled or self.current_floor is None:
            return
        
        floor = self.floors.get(self.current_floor)
        if floor:
            floor.keys_used += 1
    
    def record_pity_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Record a pity event (loot rebalancing).
        
        Args:
            event_type: Type of pity event (e.g., "soft_bias", "hard_inject")
            data: Event details
        """
        if not self.enabled or self.current_floor is None:
            return
        
        floor = self.floors.get(self.current_floor)
        if floor:
            floor.pity_events.append({
                'event_type': event_type,
                'timestamp': datetime.now().isoformat(),
                **data
            })
    
    def dump_json(self) -> None:
        """Write telemetry to JSON file.
        
        Raises:
            RuntimeError: If output_path not set
        """
        if not self.enabled or not self.output_path:
            logger.warning("Cannot dump telemetry: not enabled or no output path")
            return
        
        try:
            # Ensure parent directory exists
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to JSON-serializable format
            data = {
                'generated_at': datetime.now().isoformat(),
                'floor_count': len(self.floors),
                'floors': [
                    floor.to_dict() for floor in sorted(
                        self.floors.values(),
                        key=lambda f: f.depth
                    )
                ]
            }
            
            # Write JSON
            with open(self.output_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Telemetry dumped to {self.output_path}")
            
            # Validate schema
            self._validate_schema(data)
            
        except Exception as e:
            logger.error(f"Failed to dump telemetry: {e}")
            raise
    
    def _validate_schema(self, data: Dict[str, Any]) -> None:
        """Validate telemetry JSON schema.
        
        Args:
            data: Telemetry data dict
            
        Raises:
            ValueError: If schema invalid
        """
        required_top_level = {'generated_at', 'floor_count', 'floors'}
        if not all(k in data for k in required_top_level):
            raise ValueError(f"Missing required top-level keys: {required_top_level}")
        
        if not isinstance(data['floors'], list):
            raise ValueError("'floors' must be a list")
        
        required_floor_fields = {
            'depth', 'timestamp', 'etp_sum', 'traps_triggered', 
            'secrets_found', 'doors_opened', 'doors_unlocked', 'keys_used'
        }
        
        for floor in data['floors']:
            if not isinstance(floor, dict):
                raise ValueError("Each floor must be a dict")
            
            if not all(k in floor for k in required_floor_fields):
                missing = required_floor_fields - set(floor.keys())
                raise ValueError(f"Floor {floor.get('depth')} missing fields: {missing}")
            
            if not isinstance(floor['ttk_hist'], list):
                raise ValueError(f"Floor {floor['depth']}: ttk_hist must be a list")
            
            if not isinstance(floor['ttd_hist'], list):
                raise ValueError(f"Floor {floor['depth']}: ttd_hist must be a list")
            
            if not isinstance(floor['pity_events'], list):
                raise ValueError(f"Floor {floor['depth']}: pity_events must be a list")
        
        logger.debug("Telemetry schema validation passed")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get aggregate statistics.
        
        Returns:
            Statistics dictionary
        """
        if not self.floors:
            return {'floors': 0}
        
        all_ttk = []
        all_ttd = []
        total_traps = 0
        total_secrets = 0
        total_doors = 0
        total_keys = 0
        
        for floor in self.floors.values():
            all_ttk.extend(floor.ttk_hist)
            all_ttd.extend(floor.ttd_hist)
            total_traps += floor.traps_triggered
            total_secrets += floor.secrets_found
            total_doors += floor.doors_opened + floor.doors_unlocked
            total_keys += floor.keys_used
        
        def mean(values):
            return sum(values) / len(values) if values else 0.0
        
        return {
            'floors': len(self.floors),
            'avg_etp_per_floor': mean([f.etp_sum for f in self.floors.values()]),
            'avg_ttk': mean(all_ttk),
            'avg_ttd': mean(all_ttd),
            'total_traps': total_traps,
            'total_secrets': total_secrets,
            'total_doors': total_doors,
            'total_keys': total_keys,
        }
    
    def reset(self) -> None:
        """Reset all telemetry data."""
        self.floors.clear()
        self.current_floor = None
        logger.debug("Telemetry service reset")


# Global singleton
_telemetry_service: Optional[TelemetryService] = None


def get_telemetry_service(output_path: Optional[str] = None) -> TelemetryService:
    """Get the global telemetry service instance.
    
    Args:
        output_path: Path to write telemetry JSON (creates singleton if not exists)
        
    Returns:
        TelemetryService singleton
    """
    global _telemetry_service
    if _telemetry_service is None:
        _telemetry_service = TelemetryService(output_path)
    return _telemetry_service


def reset_telemetry_service() -> None:
    """Reset the global telemetry service (for testing)."""
    global _telemetry_service
    if _telemetry_service:
        _telemetry_service.reset()
    _telemetry_service = None

