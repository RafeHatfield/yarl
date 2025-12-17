"""Scenario metrics collector helpers (optional, harness-scoped)."""

from contextlib import contextmanager
from typing import Any, Optional

from components.component_registry import ComponentType


class ScenarioMetricsCollector:
    """Lightweight, optional collector used only during scenario harness runs."""
    
    def __init__(self, metrics: Any):
        self.metrics = metrics
    
    def record_kill(self, killer: Any, victim: Any) -> None:
        if not killer or not victim:
            return
        source = _classify_kill_source(killer)
        faction = _get_faction_name(killer)
        self.metrics.kills_by_source[source] = self.metrics.kills_by_source.get(source, 0) + 1
        self.metrics.kills_by_faction[faction] = self.metrics.kills_by_faction.get(faction, 0) + 1
    
    def record_plague_infection(self, source: Any, target: Any) -> None:
        self.metrics.plague_infections += 1
    
    def record_reanimation(self, entity: Any) -> None:
        self.metrics.reanimations += 1
    
    def record_surprise_attack(self, attacker: Any, defender: Any) -> None:
        self.metrics.surprise_attacks += 1
    
    def record_bonus_attack(self, attacker: Any, defender: Any) -> None:
        self.metrics.bonus_attacks_triggered += 1
    
    def record_split_event(self, original_entity: Any, child_type: str, num_children: int) -> None:
        """Record a slime split event.
        
        Args:
            original_entity: The entity that split
            child_type: Type of children spawned
            num_children: Number of children spawned
        """
        # Increment total split counter
        if not hasattr(self.metrics, 'split_events_total'):
            self.metrics.split_events_total = 0
        self.metrics.split_events_total += 1
        
        # Track by monster type
        if not hasattr(self.metrics, 'split_events_by_type'):
            self.metrics.split_events_by_type = {}
        monster_type = getattr(original_entity, 'name', 'unknown')
        self.metrics.split_events_by_type[monster_type] = \
            self.metrics.split_events_by_type.get(monster_type, 0) + 1
        
        # Track children spawned
        if not hasattr(self.metrics, 'split_children_spawned'):
            self.metrics.split_children_spawned = 0
        self.metrics.split_children_spawned += num_children
    
    def record_player_attack(self, hit: bool) -> None:
        """Record a player attack attempt and whether it hit.
        
        Args:
            hit: True if the attack hit, False if it missed
        """
        self.metrics.player_attacks += 1
        if hit:
            self.metrics.player_hits += 1
    
    def record_monster_attack(self, hit: bool) -> None:
        """Record a monster attack attempt and whether it hit.
        
        Args:
            hit: True if the attack hit, False if it missed
        """
        self.metrics.monster_attacks += 1
        if hit:
            self.metrics.monster_hits += 1

    def record_portal_use(self) -> None:
        """Record a portal teleportation event."""
        if hasattr(self.metrics, "portals_used"):
            self.metrics.portals_used += 1


_active_scenario_metrics_collector: Optional[ScenarioMetricsCollector] = None


def set_active_metrics_collector(collector: Optional[ScenarioMetricsCollector]) -> None:
    """Set the active metrics collector for scenario runs."""
    global _active_scenario_metrics_collector
    _active_scenario_metrics_collector = collector


def clear_active_metrics_collector() -> None:
    """Clear the active metrics collector."""
    set_active_metrics_collector(None)


def get_active_metrics_collector() -> Optional[ScenarioMetricsCollector]:
    """Return the active metrics collector if one is set."""
    return _active_scenario_metrics_collector


@contextmanager
def scoped_metrics_collector(metrics: Any):
    """Context manager to scope the active collector to a scenario run."""
    collector = ScenarioMetricsCollector(metrics)
    set_active_metrics_collector(collector)
    try:
        yield collector
    finally:
        clear_active_metrics_collector()


def _classify_kill_source(killer: Any) -> str:
    """Return source bucket for kills (PLAYER | MONSTERS | OTHER)."""
    try:
        from components.ai import BasicMonster  # type: ignore
        if killer and hasattr(killer, 'name') and killer.name == "Player":
            return "PLAYER"
        if killer and getattr(killer, 'ai', None):
            return "MONSTERS"
        if killer and isinstance(killer, BasicMonster):
            return "MONSTERS"
    except Exception:
        pass
    return "OTHER"


def _get_faction_name(entity: Any) -> str:
    """Best-effort faction name for metrics bucketing."""
    try:
        from components.faction import get_faction_display_name
        faction = None
        if hasattr(entity, 'get_component_optional'):
            faction = entity.get_component_optional(ComponentType.FACTION)
        elif hasattr(entity, 'faction'):
            faction = getattr(entity, 'faction')
        if faction is not None:
            return get_faction_display_name(faction)
    except Exception:
        pass
    return getattr(entity, 'name', 'UNKNOWN_FACTION')

