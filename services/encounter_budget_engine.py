"""Encounter budget engine for ETP-based difficulty balancing.

This module provides:
- ETP (Encounter Threat Points) calculation for entities
- Budget-aware spawn candidate assembly
- Trimming logic for exceeding budgets
- Telemetry for budget constraints
"""

from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from logger_config import get_logger

logger = get_logger(__name__)


@dataclass
class SpawnCandidate:
    """A candidate spawn with its ETP cost."""
    entity_type: str  # Monster ID (e.g., "orc", "troll")
    etp_cost: int  # Encounter Threat Points
    count: int  # How many to spawn
    total_etp: int = 0  # etp_cost * count (calculated)
    
    def __post_init__(self):
        """Calculate total ETP on creation."""
        self.total_etp = self.etp_cost * self.count


class EncounterBudgetEngine:
    """Engine for managing encounter difficulty through ETP budgeting."""
    
    def __init__(self):
        """Initialize encounter budget engine."""
        self.etp_cache: Dict[str, int] = {}  # entity_type -> base ETP
        self.history: List[Dict[str, Any]] = []  # Telemetry history
    
    def register_etp(self, entity_type: str, etp_base: int) -> None:
        """Register ETP value for an entity type.
        
        Args:
            entity_type: Monster type (e.g., "orc", "troll")
            etp_base: Base ETP for this entity
        """
        if etp_base < 0:
            logger.warning(f"Negative ETP {etp_base} for {entity_type}, using 0")
            etp_base = 0
        
        self.etp_cache[entity_type] = etp_base
        logger.debug(f"Registered ETP: {entity_type} = {etp_base}")
    
    def get_etp(self, entity_type: str, default: int = 1) -> int:
        """Get ETP for an entity type.
        
        Args:
            entity_type: Monster type
            default: Default ETP if not registered
            
        Returns:
            ETP value
        """
        return self.etp_cache.get(entity_type, default)
    
    def assemble_spawns(
        self,
        candidates: List[Tuple[str, int]],  # [(entity_type, count), ...]
        budget_min: int,
        budget_max: int,
        allow_spike: bool = False
    ) -> Tuple[List[Tuple[str, int]], int, Dict[str, Any]]:
        """Assemble spawns within budget constraints.
        
        Args:
            candidates: List of (entity_type, count) tuples to spawn
            budget_min: Minimum total ETP
            budget_max: Maximum total ETP
            allow_spike: If True, can exceed max by one entity
            
        Returns:
            Tuple of (final_spawns, total_etp, telemetry_event)
        """
        if not candidates:
            return [], 0, {'trimmed': [], 'total_etp': 0}
        
        # Convert to SpawnCandidates with ETP costs
        spawn_list = []
        for entity_type, count in candidates:
            etp_cost = self.get_etp(entity_type)
            spawn_list.append(SpawnCandidate(entity_type, etp_cost, count))
        
        total_etp = sum(s.total_etp for s in spawn_list)
        trimmed = []
        
        # If under budget, return as-is
        if total_etp <= budget_max:
            event = {
                'event': 'spawns_within_budget',
                'total_etp': total_etp,
                'budget_min': budget_min,
                'budget_max': budget_max,
                'trimmed': [],
            }
            self.history.append(event)
            
            final_spawns = [(s.entity_type, s.count) for s in spawn_list]
            return final_spawns, total_etp, event
        
        # Over budget - trim candidates
        if allow_spike:
            # With allow_spike, one entity can exceed max if we're under
            # Keep all candidates
            logger.info(f"Spawns exceed max ({total_etp} > {budget_max}) "
                       f"but allow_spike=True, accepting spike")
            
            event = {
                'event': 'spawns_spike_allowed',
                'total_etp': total_etp,
                'budget_min': budget_min,
                'budget_max': budget_max,
                'spike_amount': total_etp - budget_max,
            }
            self.history.append(event)
            
            final_spawns = [(s.entity_type, s.count) for s in spawn_list]
            return final_spawns, total_etp, event
        
        else:
            # No spike allowed - trim until within budget
            current_etp = 0
            kept_spawns = []
            
            for spawn in spawn_list:
                if current_etp + spawn.total_etp <= budget_max:
                    kept_spawns.append(spawn)
                    current_etp += spawn.total_etp
                else:
                    # Try to fit partial count
                    remaining_budget = budget_max - current_etp
                    if remaining_budget > 0 and spawn.etp_cost > 0:
                        partial_count = remaining_budget // spawn.etp_cost
                        if partial_count > 0:
                            kept_spawns.append(
                                SpawnCandidate(spawn.entity_type, spawn.etp_cost, partial_count)
                            )
                            current_etp += partial_count * spawn.etp_cost
                            trimmed.append({
                                'entity_type': spawn.entity_type,
                                'original_count': spawn.count,
                                'kept_count': partial_count,
                                'trimmed_count': spawn.count - partial_count,
                            })
                        else:
                            trimmed.append({
                                'entity_type': spawn.entity_type,
                                'original_count': spawn.count,
                                'kept_count': 0,
                                'trimmed_count': spawn.count,
                            })
                    else:
                        trimmed.append({
                            'entity_type': spawn.entity_type,
                            'original_count': spawn.count,
                            'kept_count': 0,
                            'trimmed_count': spawn.count,
                        })
            
            if trimmed:
                logger.warning(f"Trimmed spawns to fit budget ({total_etp} > {budget_max}): "
                             f"{[t['entity_type'] for t in trimmed]}")
            
            event = {
                'event': 'spawns_trimmed',
                'total_etp': current_etp,
                'budget_min': budget_min,
                'budget_max': budget_max,
                'original_etp': total_etp,
                'trimmed': trimmed,
            }
            self.history.append(event)
            
            final_spawns = [(s.entity_type, s.count) for s in kept_spawns]
            return final_spawns, current_etp, event
    
    def calculate_etp(self, spawns: List[Tuple[str, int]]) -> int:
        """Calculate total ETP for a spawn list.
        
        Args:
            spawns: List of (entity_type, count) tuples
            
        Returns:
            Total ETP
        """
        total = 0
        for entity_type, count in spawns:
            etp_cost = self.get_etp(entity_type)
            total += etp_cost * count
        return total
    
    def is_within_budget(self, total_etp: int, budget_min: int, budget_max: int) -> bool:
        """Check if total ETP is within budget.
        
        Args:
            total_etp: Current total ETP
            budget_min: Minimum ETP
            budget_max: Maximum ETP
            
        Returns:
            True if budget_min <= total_etp <= budget_max
        """
        return budget_min <= total_etp <= budget_max
    
    def get_budget_status(self, total_etp: int, budget_min: int, budget_max: int) -> str:
        """Get human-readable budget status.
        
        Args:
            total_etp: Current total ETP
            budget_min: Minimum ETP
            budget_max: Maximum ETP
            
        Returns:
            Status string
        """
        if total_etp < budget_min:
            return f"UNDER ({total_etp}/{budget_min})"
        elif total_etp > budget_max:
            return f"OVER ({total_etp}/{budget_max})"
        else:
            return f"OK ({total_etp}/{budget_min}-{budget_max})"
    
    def get_telemetry(self) -> List[Dict[str, Any]]:
        """Get telemetry history.
        
        Returns:
            List of telemetry events
        """
        return self.history
    
    def clear_telemetry(self) -> None:
        """Clear telemetry history."""
        self.history.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about budget usage.
        
        Returns:
            Stats dict
        """
        if not self.history:
            return {
                'total_events': 0,
                'trim_events': 0,
                'spike_events': 0,
                'avg_overage': 0.0,
            }
        
        trim_events = [e for e in self.history if e.get('event') == 'spawns_trimmed']
        spike_events = [e for e in self.history if e.get('event') == 'spawns_spike_allowed']
        
        overages = []
        for e in trim_events + spike_events:
            if 'original_etp' in e and 'budget_max' in e:
                overage = e['original_etp'] - e['budget_max']
                if overage > 0:
                    overages.append(overage)
        
        avg_overage = sum(overages) / len(overages) if overages else 0.0
        
        return {
            'total_events': len(self.history),
            'trim_events': len(trim_events),
            'spike_events': len(spike_events),
            'avg_overage': avg_overage,
        }


# Global singleton
_encounter_budget_engine: Optional[EncounterBudgetEngine] = None


def get_encounter_budget_engine() -> EncounterBudgetEngine:
    """Get the global encounter budget engine instance.
    
    Returns:
        EncounterBudgetEngine singleton
    """
    global _encounter_budget_engine
    if _encounter_budget_engine is None:
        _encounter_budget_engine = EncounterBudgetEngine()
    return _encounter_budget_engine


def reset_encounter_budget_engine() -> None:
    """Reset the global encounter budget engine (for testing)."""
    global _encounter_budget_engine
    _encounter_budget_engine = None

