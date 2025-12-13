"""Structured telemetry primitives for BotBrain decisions.

This module stays bot-scoped to avoid leaking bot concerns into core ECS or
combat systems. It provides lightweight data classes for per-decision telemetry
and per-run summaries, along with a recorder that can be enabled by the soak
harness or other callers. Overhead when disabled is minimal (early return).
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, Optional


@dataclass
class BotDecisionTelemetry:
    """Single bot decision record."""

    run_id: Optional[str]
    floor: Optional[int]
    turn_number: int
    action_type: str
    decision_type: Optional[str] = None
    reason: str = ""
    in_combat: bool = False
    in_explore: bool = False
    in_loot: bool = False
    low_hp: bool = False
    floor_complete: bool = False
    auto_explore_active: bool = False
    visible_enemies: int = 0
    hp: Optional[int] = None
    max_hp: Optional[int] = None
    hp_percent: Optional[float] = None
    has_healing_potion: Optional[bool] = None
    healing_potions_in_inventory: Optional[int] = None
    scenario_id: Optional[str] = None


@dataclass
class BotRunSummary:
    """Aggregate stats for a bot run."""

    run_id: Optional[str]
    total_steps: int
    floors_seen: int
    action_counts: Dict[str, int] = field(default_factory=dict)
    context_counts: Dict[str, int] = field(default_factory=dict)
    reason_counts: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        """Serialize to simple dicts (JSON/CSV friendly)."""
        return {
            "run_id": self.run_id,
            "total_steps": self.total_steps,
            "floors_seen": self.floors_seen,
            "action_counts": dict(self.action_counts),
            "context_counts": dict(self.context_counts),
            "reason_counts": dict(self.reason_counts),
        }


class BotMetricsRecorder:
    """In-memory recorder for bot decisions.

    Intended to be enabled by the soak harness; normal gameplay can pass
    enabled=False to avoid any overhead.
    """

    def __init__(self, enabled: bool = False, run_id: Optional[str] = None) -> None:
        self.enabled = enabled
        self.run_id = run_id
        self._decisions: list[BotDecisionTelemetry] = []

    def record_decision(self, decision: BotDecisionTelemetry) -> None:
        """Record a single decision if enabled."""
        if not self.enabled:
            return
        self._decisions.append(decision)

    def get_decisions(self) -> list[BotDecisionTelemetry]:
        """Return recorded decisions (copy) for downstream export."""
        return list(self._decisions)

    def summarize(self) -> BotRunSummary:
        """Aggregate recorded decisions into a summary."""
        floors_seen = {d.floor for d in self._decisions if d.floor is not None}
        action_counts: Dict[str, int] = {}
        context_counts: Dict[str, int] = {}
        reason_counts: Dict[str, int] = {}

        for decision in self._decisions:
            action_counts[decision.action_type] = action_counts.get(
                decision.action_type, 0
            ) + 1
            if decision.reason:
                reason_counts[decision.reason] = reason_counts.get(
                    decision.reason, 0
                ) + 1

            if decision.in_combat:
                context_counts["in_combat"] = context_counts.get("in_combat", 0) + 1
            if decision.in_explore:
                context_counts["in_explore"] = context_counts.get("in_explore", 0) + 1
            if decision.in_loot:
                context_counts["in_loot"] = context_counts.get("in_loot", 0) + 1
            if decision.low_hp:
                context_counts["low_hp"] = context_counts.get("low_hp", 0) + 1
            if decision.floor_complete:
                context_counts["floor_complete"] = context_counts.get(
                    "floor_complete", 0
                ) + 1
            if decision.auto_explore_active:
                context_counts["auto_explore_active"] = context_counts.get(
                    "auto_explore_active", 0
                ) + 1
            if decision.visible_enemies > 0:
                context_counts["visible_enemies_turns"] = context_counts.get(
                    "visible_enemies_turns", 0
                ) + 1

        return BotRunSummary(
            run_id=self.run_id,
            total_steps=len(self._decisions),
            floors_seen=len(floors_seen),
            action_counts=action_counts,
            context_counts=context_counts,
            reason_counts=reason_counts,
        )

    def decisions_as_dicts(self) -> list[dict]:
        """Return recorded decisions as serializable dicts."""
        return [asdict(decision) for decision in self._decisions]

