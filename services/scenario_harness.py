"""Scenario Harness for Phase 12B.

This module provides infrastructure for running scenario-based simulations,
enabling automated testing of specific game mechanics.

Phase 12B: Scenario Harness & Basic Metrics
- RunMetrics: Per-run metrics tracking
- AggregatedMetrics: Multi-run aggregation
- BotPolicy: Abstraction for player control in scenarios
- run_scenario_once: Single scenario execution
- run_scenario_many: Multi-run aggregation

Usage:
    from services.scenario_harness import (
        run_scenario_once,
        run_scenario_many,
        make_bot_policy,
    )
    
    scenario = get_scenario_definition("backstab_training")
    policy = make_bot_policy("observe_only")
    metrics = run_scenario_once(scenario, policy, turn_limit=200)
"""

import logging
import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Tuple

from components.component_registry import ComponentType
from game_states import GameStates
from loader_functions.initialize_new_game import get_constants
from game_messages import MessageLog
from services.scenario_invariants import ScenarioInvariantError, validate_scenario_instance
from services.scenario_level_loader import (
    ScenarioBuildError,
    ScenarioMapResult,
    build_scenario_map,
)

logger = logging.getLogger(__name__)


# =============================================================================
# RunMetrics: Per-run metrics tracking
# =============================================================================

@dataclass
class RunMetrics:
    """Metrics collected from a single scenario run."""
    turns_taken: int = 0
    player_died: bool = False
    kills_by_faction: Dict[str, int] = field(default_factory=dict)
    kills_by_source: Dict[str, int] = field(default_factory=dict)
    plague_infections: int = 0
    reanimations: int = 0
    surprise_attacks: int = 0
    # Phase 21: Invisibility attack metrics
    invis_attacks: int = 0
    invis_broken_by_attack: int = 0
    bonus_attacks_triggered: int = 0
    player_attacks: int = 0
    player_hits: int = 0
    monster_attacks: int = 0
    monster_hits: int = 0
    portals_used: int = 0
    # Phase 19: Wraith drain metrics
    life_drain_attempts: int = 0
    life_drain_heal_total: int = 0
    life_drain_blocked_attempts: int = 0
    # Phase 19: Orc Shaman metrics
    shaman_hex_casts: int = 0
    shaman_chant_starts: int = 0
    shaman_chant_interrupts: int = 0
    shaman_chant_expiries: int = 0
    # Phase 19: Necromancer metrics
    necro_raise_attempts: int = 0
    necro_raise_successes: int = 0
    necro_corpse_seek_moves: int = 0
    necro_unsafe_move_blocks: int = 0
    # Phase 20: Corpse lifecycle metrics
    fresh_corpses_created: int = 0
    spent_corpses_created: int = 0
    raises_completed: int = 0
    spent_corpses_exploded: int = 0
    # Phase 20A: Poison DOT metrics
    poison_applications: int = 0
    poison_damage_dealt: int = 0
    poison_ticks_processed: int = 0
    poison_kills: int = 0
    deaths_with_active_poison: int = 0
    # Phase 20B.1: Burning DOT metrics
    burning_applications: int = 0
    burning_damage_dealt: int = 0
    burning_ticks_processed: int = 0
    burning_kills: int = 0
    # Phase 20C.1: Slow metrics
    slow_applications: int = 0
    slow_turns_skipped: int = 0
    # Phase 20C.1: Reflex metrics
    reflex_potions_used: int = 0
    bonus_attacks_while_reflexes_active: int = 0
    # Phase 20D.1: Entangle metrics (Root Potion)
    entangle_applications: int = 0
    entangle_moves_blocked: int = 0
    # Phase 20E.2: Disarm metrics (Disarm Scroll)
    disarm_applications: int = 0
    disarmed_attacks_attempted: int = 0
    disarmed_weapon_attacks_prevented: int = 0
    # Phase 20F: Silence metrics (Silence Scroll)
    silence_applications: int = 0
    silenced_casts_blocked: int = 0
    # Phase 21.1: Trap metrics
    traps_triggered_total: int = 0
    trap_root_triggered: int = 0
    trap_root_effects_applied: int = 0
    # Phase 21.2: Spike trap metrics
    trap_spike_triggered: int = 0
    trap_spike_damage_total: int = 0
    # Phase 21.3: Teleport trap metrics
    trap_teleport_triggered: int = 0
    trap_teleport_success: int = 0
    trap_teleport_failed_no_valid_tile: int = 0
    # Phase 21.4: Gas trap metrics
    trap_gas_triggered: int = 0
    trap_gas_effects_applied: int = 0
    # Phase 21.4: Fire trap metrics
    trap_fire_triggered: int = 0
    trap_fire_effects_applied: int = 0
    # Phase 21.5: Hole trap metrics
    trap_hole_triggered: int = 0
    trap_hole_transition_requested: int = 0
    # Phase 21.6: Trapped chest metrics
    chest_traps_triggered_total: int = 0
    chest_trap_spike_triggered: int = 0
    chest_trap_spike_damage_total: int = 0
    # Phase 21.7: Trap detection and disarm metrics
    traps_detected_total: int = 0
    trap_disarms_attempted: int = 0
    trap_disarms_succeeded: int = 0
    # Phase 22.1.1: Oath metrics (Run Identity - refined)
    oath_embers_chosen: int = 0
    oath_venom_chosen: int = 0
    oath_chains_chosen: int = 0
    oath_embers_procs: int = 0
    oath_embers_self_burn_procs: int = 0  # Phase 22.1.1: risk/reward tracking
    oath_venom_procs: int = 0
    oath_venom_duration_extensions: int = 0  # Phase 22.1.1: focus-fire tracking
    oath_chains_bonus_applied: int = 0  # Phase 22.1.1: conditional bonus tracking
    oath_chains_bonus_denied: int = 0  # Phase 22.1.1: proves constraint works
    knockback_tiles_moved_by_player: int = 0
    # Phase 22.2: Ranged combat metrics
    ranged_attacks_made_by_player: int = 0
    ranged_attacks_denied_out_of_range: int = 0
    ranged_damage_dealt_by_player: int = 0
    ranged_damage_penalty_total: int = 0
    ranged_adjacent_retaliations_triggered: int = 0
    ranged_knockback_procs: int = 0
    # Terminal state overwrite attempts (diagnostic metric for harness observability)
    terminal_overwrite_attempts: int = 0
    terminal_overwrite_by_target: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            'turns_taken': self.turns_taken,
            'player_died': self.player_died,
            'kills_by_faction': dict(self.kills_by_faction),
            'kills_by_source': dict(self.kills_by_source),
            'plague_infections': self.plague_infections,
            'reanimations': self.reanimations,
            'surprise_attacks': self.surprise_attacks,
            'invis_attacks': self.invis_attacks,
            'invis_broken_by_attack': self.invis_broken_by_attack,
            'bonus_attacks_triggered': self.bonus_attacks_triggered,
            'player_attacks': self.player_attacks,
            'player_hits': self.player_hits,
            'monster_attacks': self.monster_attacks,
            'monster_hits': self.monster_hits,
            'portals_used': self.portals_used,
        }
        # Phase 19: Split metrics (optional)
        if hasattr(self, 'split_events_total'):
            result['split_events_total'] = self.split_events_total
        if hasattr(self, 'split_children_spawned'):
            result['split_children_spawned'] = self.split_children_spawned
        if hasattr(self, 'split_events_by_type'):
            result['split_events_by_type'] = dict(self.split_events_by_type)
        # Phase 19: Wraith drain metrics (optional)
        if hasattr(self, 'life_drain_attempts'):
            result['life_drain_attempts'] = self.life_drain_attempts
        if hasattr(self, 'life_drain_heal_total'):
            result['life_drain_heal_total'] = self.life_drain_heal_total
        if hasattr(self, 'life_drain_blocked_attempts'):
            result['life_drain_blocked_attempts'] = self.life_drain_blocked_attempts
        # Phase 19: Orc Shaman metrics (optional)
        if hasattr(self, 'shaman_hex_casts'):
            result['shaman_hex_casts'] = self.shaman_hex_casts
        if hasattr(self, 'shaman_chant_starts'):
            result['shaman_chant_starts'] = self.shaman_chant_starts
        if hasattr(self, 'shaman_chant_interrupts'):
            result['shaman_chant_interrupts'] = self.shaman_chant_interrupts
        if hasattr(self, 'shaman_chant_expiries'):
            result['shaman_chant_expiries'] = self.shaman_chant_expiries
        # Phase 19: Necromancer metrics (optional)
        if hasattr(self, 'necro_raise_attempts'):
            result['necro_raise_attempts'] = self.necro_raise_attempts
        if hasattr(self, 'necro_raise_successes'):
            result['necro_raise_successes'] = self.necro_raise_successes
        if hasattr(self, 'necro_corpse_seek_moves'):
            result['necro_corpse_seek_moves'] = self.necro_corpse_seek_moves
        if hasattr(self, 'necro_unsafe_move_blocks'):
            result['necro_unsafe_move_blocks'] = self.necro_unsafe_move_blocks
        # Phase 20A: Poison metrics (optional)
        if hasattr(self, 'poison_applications'):
            result['poison_applications'] = self.poison_applications
        if hasattr(self, 'poison_damage_dealt'):
            result['poison_damage_dealt'] = self.poison_damage_dealt
        if hasattr(self, 'poison_ticks_processed'):
            result['poison_ticks_processed'] = self.poison_ticks_processed
        if hasattr(self, 'poison_kills'):
            result['poison_kills'] = self.poison_kills
        if hasattr(self, 'deaths_with_active_poison'):
            result['deaths_with_active_poison'] = self.deaths_with_active_poison
        # Phase 20B.1: Burning metrics (optional)
        if hasattr(self, 'burning_applications'):
            result['burning_applications'] = self.burning_applications
        if hasattr(self, 'burning_damage_dealt'):
            result['burning_damage_dealt'] = self.burning_damage_dealt
        if hasattr(self, 'burning_ticks_processed'):
            result['burning_ticks_processed'] = self.burning_ticks_processed
        if hasattr(self, 'burning_kills'):
            result['burning_kills'] = self.burning_kills
        # Phase 20C.1: Slow metrics
        if hasattr(self, 'slow_applications'):
            result['slow_applications'] = self.slow_applications
        if hasattr(self, 'slow_turns_skipped'):
            result['slow_turns_skipped'] = self.slow_turns_skipped
        # Phase 20C.1: Reflex metrics
        if hasattr(self, 'reflex_potions_used'):
            result['reflex_potions_used'] = self.reflex_potions_used
        if hasattr(self, 'bonus_attacks_while_reflexes_active'):
            result['bonus_attacks_while_reflexes_active'] = self.bonus_attacks_while_reflexes_active
        # Phase 20D.1: Entangle metrics
        if hasattr(self, 'entangle_applications'):
            result['entangle_applications'] = self.entangle_applications
        if hasattr(self, 'entangle_moves_blocked'):
            result['entangle_moves_blocked'] = self.entangle_moves_blocked
        # Phase 21.1: Trap metrics
        if hasattr(self, 'traps_triggered_total'):
            result['traps_triggered_total'] = self.traps_triggered_total
        if hasattr(self, 'trap_root_triggered'):
            result['trap_root_triggered'] = self.trap_root_triggered
        if hasattr(self, 'trap_root_effects_applied'):
            result['trap_root_effects_applied'] = self.trap_root_effects_applied
        # Phase 22.1.1: Oath metrics (Run Identity - refined)
        if hasattr(self, 'oath_embers_chosen'):
            result['oath_embers_chosen'] = self.oath_embers_chosen
        if hasattr(self, 'oath_venom_chosen'):
            result['oath_venom_chosen'] = self.oath_venom_chosen
        if hasattr(self, 'oath_chains_chosen'):
            result['oath_chains_chosen'] = self.oath_chains_chosen
        if hasattr(self, 'oath_embers_procs'):
            result['oath_embers_procs'] = self.oath_embers_procs
        if hasattr(self, 'oath_embers_self_burn_procs'):
            result['oath_embers_self_burn_procs'] = self.oath_embers_self_burn_procs
        if hasattr(self, 'oath_venom_procs'):
            result['oath_venom_procs'] = self.oath_venom_procs
        if hasattr(self, 'oath_venom_duration_extensions'):
            result['oath_venom_duration_extensions'] = self.oath_venom_duration_extensions
        if hasattr(self, 'oath_chains_bonus_applied'):
            result['oath_chains_bonus_applied'] = self.oath_chains_bonus_applied
        if hasattr(self, 'oath_chains_bonus_denied'):
            result['oath_chains_bonus_denied'] = self.oath_chains_bonus_denied
        if hasattr(self, 'knockback_tiles_moved_by_player'):
            result['knockback_tiles_moved_by_player'] = self.knockback_tiles_moved_by_player
        # Phase 22.2: Ranged combat metrics
        if hasattr(self, 'ranged_attacks_made_by_player'):
            result['ranged_attacks_made_by_player'] = self.ranged_attacks_made_by_player
        if hasattr(self, 'ranged_attacks_denied_out_of_range'):
            result['ranged_attacks_denied_out_of_range'] = self.ranged_attacks_denied_out_of_range
        if hasattr(self, 'ranged_damage_dealt_by_player'):
            result['ranged_damage_dealt_by_player'] = self.ranged_damage_dealt_by_player
        if hasattr(self, 'ranged_damage_penalty_total'):
            result['ranged_damage_penalty_total'] = self.ranged_damage_penalty_total
        if hasattr(self, 'ranged_adjacent_retaliations_triggered'):
            result['ranged_adjacent_retaliations_triggered'] = self.ranged_adjacent_retaliations_triggered
        if hasattr(self, 'ranged_knockback_procs'):
            result['ranged_knockback_procs'] = self.ranged_knockback_procs
        # Terminal state overwrite metrics (diagnostic)
        if hasattr(self, 'terminal_overwrite_attempts'):
            result['terminal_overwrite_attempts'] = self.terminal_overwrite_attempts
        if hasattr(self, 'terminal_overwrite_by_target'):
            result['terminal_overwrite_by_target'] = dict(self.terminal_overwrite_by_target)
        return result


# =============================================================================
# AggregatedMetrics: Multi-run aggregation
# =============================================================================

@dataclass
class AggregatedMetrics:
    """Aggregated metrics from multiple scenario runs."""
    runs: int = 0
    average_turns: float = 0.0
    player_deaths: int = 0
    depth: Optional[int] = None
    total_kills_by_faction: Dict[str, int] = field(default_factory=dict)
    total_kills_by_source: Dict[str, int] = field(default_factory=dict)
    total_plague_infections: int = 0
    total_reanimations: int = 0
    total_surprise_attacks: int = 0
    # Phase 21: Invisibility attack metrics
    total_invis_attacks: int = 0
    total_invis_broken_by_attack: int = 0
    total_bonus_attacks_triggered: int = 0
    total_player_attacks: int = 0
    total_player_hits: int = 0
    total_monster_attacks: int = 0
    total_monster_hits: int = 0
    total_portals_used: int = 0
    # Phase 19: Split metrics
    total_split_events: int = 0
    total_split_children_spawned: int = 0
    total_split_events_by_type: Dict[str, int] = field(default_factory=dict)
    # Phase 19: Wraith drain metrics
    total_life_drain_attempts: int = 0
    total_life_drain_heal_total: int = 0
    total_life_drain_blocked_attempts: int = 0
    # Phase 19: Orc Shaman metrics
    total_shaman_hex_casts: int = 0
    total_shaman_chant_starts: int = 0
    total_shaman_chant_interrupts: int = 0
    total_shaman_chant_expiries: int = 0
    # Phase 19: Necromancer metrics
    total_necro_raise_attempts: int = 0
    total_necro_raise_successes: int = 0
    total_necro_corpse_seek_moves: int = 0
    total_necro_unsafe_move_blocks: int = 0
    # Phase 20: Corpse lifecycle metrics
    total_fresh_corpses_created: int = 0
    total_spent_corpses_created: int = 0
    total_raises_completed: int = 0
    total_spent_corpses_exploded: int = 0
    # Phase 19: Lich metrics
    total_lich_ticks_alive: int = 0
    total_lich_ticks_player_in_range: int = 0
    total_lich_ticks_has_los: int = 0
    total_lich_ticks_eligible_to_charge: int = 0
    total_lich_soul_bolt_charges: int = 0
    total_lich_soul_bolt_casts: int = 0
    total_soul_ward_blocks: int = 0
    total_lich_death_siphon_heals: int = 0
    # Phase 20A: Poison DOT metrics
    total_poison_applications: int = 0
    total_poison_damage_dealt: int = 0
    total_poison_ticks_processed: int = 0
    total_poison_kills: int = 0
    total_deaths_with_active_poison: int = 0
    # Phase 20B.1: Burning DOT metrics
    total_burning_applications: int = 0
    total_burning_damage_dealt: int = 0
    total_burning_ticks_processed: int = 0
    total_burning_kills: int = 0
    # Phase 20C.1: Slow metrics
    total_slow_applications: int = 0
    total_slow_turns_skipped: int = 0
    # Phase 20C.1: Reflex metrics
    total_reflex_potions_used: int = 0
    total_bonus_attacks_while_reflexes_active: int = 0
    # Phase 20D.1: Entangle metrics (Root Potion)
    total_entangle_applications: int = 0
    total_entangle_moves_blocked: int = 0
    # Phase 20E.1: Blind metrics (Sunburst Potion)
    total_blind_applications: int = 0
    total_blind_attacks_attempted: int = 0
    total_blind_attacks_missed: int = 0
    # Phase 20E.2: Disarm metrics (Disarm Scroll)
    total_disarm_applications: int = 0
    total_disarmed_attacks_attempted: int = 0
    total_disarmed_weapon_attacks_prevented: int = 0
    # Phase 20F: Silence metrics (Silence Scroll)
    total_silence_applications: int = 0
    total_silenced_casts_blocked: int = 0
    # Weapon Knockback metrics
    total_knockback_applications: int = 0
    total_knockback_tiles_moved: int = 0
    total_knockback_blocked_events: int = 0
    total_stagger_applications: int = 0
    total_stagger_turns_skipped: int = 0
    # Phase 20 Scroll Modernization: Dragon Fart metrics
    total_dragon_fart_casts: int = 0
    total_dragon_fart_tiles_created: int = 0
    total_sleep_applications: int = 0
    total_sleep_turns_prevented: int = 0
    # Phase 20 Scroll Modernization: Fireball metrics
    total_fireball_casts: int = 0
    total_fireball_tiles_created: int = 0
    total_fireball_direct_damage: int = 0
    # Phase 22.1.1: Oath metrics (Run Identity - refined)
    total_oath_embers_chosen: int = 0
    total_oath_venom_chosen: int = 0
    total_oath_chains_chosen: int = 0
    total_oath_embers_procs: int = 0
    total_oath_embers_self_burn_procs: int = 0
    total_oath_venom_procs: int = 0
    total_oath_venom_duration_extensions: int = 0
    total_oath_chains_bonus_applied: int = 0
    total_oath_chains_bonus_denied: int = 0
    total_knockback_tiles_moved_by_player: int = 0
    # Phase 22.2: Ranged combat metrics
    total_ranged_attacks_made_by_player: int = 0
    total_ranged_attacks_denied_out_of_range: int = 0
    total_ranged_damage_dealt_by_player: int = 0
    total_ranged_damage_penalty_total: int = 0
    total_ranged_adjacent_retaliations_triggered: int = 0
    total_ranged_knockback_procs: int = 0
    # Terminal state overwrite attempts (diagnostic metric for harness observability)
    total_terminal_overwrite_attempts: int = 0
    total_terminal_overwrite_by_target: Dict[str, int] = field(default_factory=dict)
    
    def get_oath_summary(self) -> Dict[str, Any]:
        """Get Oath Identity summary for reporting.
        
        Phase 22.1.2: Convenience view for Oath metrics that shows:
        - Which Oath was chosen (if any)
        - Proc counts (how often effects triggered)
        - Decision-lever metrics (risk/reward, focus-fire, positioning)
        
        Returns:
            Dictionary with Oath summary or empty if no Oath chosen
        """
        # Determine which Oath was chosen
        chosen_oath = None
        if self.total_oath_embers_chosen > 0:
            chosen_oath = "embers"
        elif self.total_oath_venom_chosen > 0:
            chosen_oath = "venom"
        elif self.total_oath_chains_chosen > 0:
            chosen_oath = "chains"
        
        if not chosen_oath:
            return {}  # No Oath active
        
        summary = {
            'oath': chosen_oath,
            'runs': self.runs,
        }
        
        if chosen_oath == "embers":
            summary.update({
                'procs': self.total_oath_embers_procs,
                'self_burn_procs': self.total_oath_embers_self_burn_procs,
                'risk_ratio': f"{self.total_oath_embers_self_burn_procs}/{self.total_oath_embers_procs}" if self.total_oath_embers_procs > 0 else "0/0",
            })
        elif chosen_oath == "venom":
            summary.update({
                'procs': self.total_oath_venom_procs,
                'duration_extensions': self.total_oath_venom_duration_extensions,
                'extension_ratio': f"{self.total_oath_venom_duration_extensions}/{self.total_oath_venom_procs}" if self.total_oath_venom_procs > 0 else "0/0",
            })
        elif chosen_oath == "chains":
            summary.update({
                'bonus_applied': self.total_oath_chains_bonus_applied,
                'bonus_denied': self.total_oath_chains_bonus_denied,
                'total_knockback_attempts': self.total_oath_chains_bonus_applied + self.total_oath_chains_bonus_denied,
                'mobility_cost_pct': round(100 * self.total_oath_chains_bonus_denied / (self.total_oath_chains_bonus_applied + self.total_oath_chains_bonus_denied), 1) if (self.total_oath_chains_bonus_applied + self.total_oath_chains_bonus_denied) > 0 else 0,
            })
        
        return summary
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            'runs': self.runs,
            'average_turns': round(self.average_turns, 2),
            'player_deaths': self.player_deaths,
            'depth': self.depth,
            'total_kills_by_faction': dict(self.total_kills_by_faction),
            'total_kills_by_source': dict(self.total_kills_by_source),
            'total_plague_infections': self.total_plague_infections,
            'total_reanimations': self.total_reanimations,
            'total_surprise_attacks': self.total_surprise_attacks,
            'total_invis_attacks': self.total_invis_attacks,
            'total_invis_broken_by_attack': self.total_invis_broken_by_attack,
            'total_bonus_attacks_triggered': self.total_bonus_attacks_triggered,
            'total_player_attacks': self.total_player_attacks,
            'total_player_hits': self.total_player_hits,
            'total_monster_attacks': self.total_monster_attacks,
            'total_monster_hits': self.total_monster_hits,
            'total_portals_used': self.total_portals_used,
            # Phase 19: Split metrics
            'total_split_events': self.total_split_events,
            'total_split_children_spawned': self.total_split_children_spawned,
            'total_split_events_by_type': dict(self.total_split_events_by_type),
            # Phase 20A: Poison metrics
            'total_poison_applications': self.total_poison_applications,
            'total_poison_damage_dealt': self.total_poison_damage_dealt,
            'total_poison_ticks_processed': self.total_poison_ticks_processed,
            'total_poison_kills': self.total_poison_kills,
            'total_deaths_with_active_poison': self.total_deaths_with_active_poison,
            # Phase 20B.1: Burning metrics
            'total_burning_applications': self.total_burning_applications,
            'total_burning_damage_dealt': self.total_burning_damage_dealt,
            'total_burning_ticks_processed': self.total_burning_ticks_processed,
            'total_burning_kills': self.total_burning_kills,
            'total_slow_applications': self.total_slow_applications,
            'total_slow_turns_skipped': self.total_slow_turns_skipped,
            'total_reflex_potions_used': self.total_reflex_potions_used,
            'total_bonus_attacks_while_reflexes_active': self.total_bonus_attacks_while_reflexes_active,
            # Phase 20D.1: Entangle metrics
            'total_entangle_applications': self.total_entangle_applications,
            'total_entangle_moves_blocked': self.total_entangle_moves_blocked,
            # Phase 20E.1: Blind metrics
            'total_blind_applications': self.total_blind_applications,
            'total_blind_attacks_attempted': self.total_blind_attacks_attempted,
            'total_blind_attacks_missed': self.total_blind_attacks_missed,
            # Phase 20E.2: Disarm metrics
            'total_disarm_applications': self.total_disarm_applications,
            'total_disarmed_attacks_attempted': self.total_disarmed_attacks_attempted,
            'total_disarmed_weapon_attacks_prevented': self.total_disarmed_weapon_attacks_prevented,
            # Phase 20F: Silence metrics
            'total_silence_applications': self.total_silence_applications,
            'total_silenced_casts_blocked': self.total_silenced_casts_blocked,
            # Weapon Knockback metrics
            'knockback_applications': self.total_knockback_applications,
            'knockback_tiles_moved': self.total_knockback_tiles_moved,
            'knockback_blocked_events': self.total_knockback_blocked_events,
            'stagger_applications': self.total_stagger_applications,
            'stagger_turns_skipped': self.total_stagger_turns_skipped,
            # Phase 20 Scroll Modernization: Dragon Fart metrics
            'total_dragon_fart_casts': self.total_dragon_fart_casts,
            'total_dragon_fart_tiles_created': self.total_dragon_fart_tiles_created,
            'total_sleep_applications': self.total_sleep_applications,
            'total_sleep_turns_prevented': self.total_sleep_turns_prevented,
            # Phase 20 Scroll Modernization: Fireball metrics
            'total_fireball_casts': self.total_fireball_casts,
            'total_fireball_tiles_created': self.total_fireball_tiles_created,
            'total_fireball_direct_damage': self.total_fireball_direct_damage,
            # Phase 22.1.1: Oath metrics (Run Identity - refined)
            'total_oath_embers_chosen': self.total_oath_embers_chosen,
            'total_oath_venom_chosen': self.total_oath_venom_chosen,
            'total_oath_chains_chosen': self.total_oath_chains_chosen,
            'total_oath_embers_procs': self.total_oath_embers_procs,
            'total_oath_embers_self_burn_procs': self.total_oath_embers_self_burn_procs,
            'total_oath_venom_procs': self.total_oath_venom_procs,
            'total_oath_venom_duration_extensions': self.total_oath_venom_duration_extensions,
            'total_oath_chains_bonus_applied': self.total_oath_chains_bonus_applied,
            'total_oath_chains_bonus_denied': self.total_oath_chains_bonus_denied,
            'total_knockback_tiles_moved_by_player': self.total_knockback_tiles_moved_by_player,
            # Phase 22.2: Ranged combat metrics
            'total_ranged_attacks_made_by_player': self.total_ranged_attacks_made_by_player,
            'total_ranged_attacks_denied_out_of_range': self.total_ranged_attacks_denied_out_of_range,
            'total_ranged_damage_dealt_by_player': self.total_ranged_damage_dealt_by_player,
            'total_ranged_damage_penalty_total': self.total_ranged_damage_penalty_total,
            'total_ranged_adjacent_retaliations_triggered': self.total_ranged_adjacent_retaliations_triggered,
            'total_ranged_knockback_procs': self.total_ranged_knockback_procs,
            # Terminal state overwrite metrics (diagnostic)
            'total_terminal_overwrite_attempts': self.total_terminal_overwrite_attempts,
            'total_terminal_overwrite_by_target': dict(self.total_terminal_overwrite_by_target),
        }
        
        # Phase 22.1.2: Add Oath summary if present
        oath_summary = self.get_oath_summary()
        if oath_summary:
            result['oath_summary'] = oath_summary
        
        return result


from services.scenario_metrics import (
    get_active_metrics_collector,
    scoped_metrics_collector,
)


# =============================================================================
# BotPolicy: Protocol for player control
# =============================================================================

class BotPolicy(Protocol):
    """Protocol for bot policies that control the player in scenarios.
    
    Bot policies decide what action the player takes each turn during
    automated scenario runs. Different policies can implement different
    behaviors (passive observation, aggressive combat, etc.).
    """
    
    def choose_action(self, game_state: Any) -> Optional[Dict[str, Any]]:
        """Choose an action for the player to take.
        
        Args:
            game_state: Current game state object containing player, entities,
                        game_map, message_log, and current_state.
        
        Returns:
            Action dict compatible with ActionProcessor, or None for no-op/wait.
            Common actions:
            - {'wait': True} - Wait/pass turn
            - {'move': (dx, dy)} - Move in direction
            - None - Interpreted as wait
        """
        ...


def make_bot_policy(name: str) -> BotPolicy:
    """Factory function to create bot policies by name.
    
    DEPRECATED: Use services.scenario_policies.make_scenario_bot_policy() directly.
    This wrapper exists for backwards compatibility with existing scenarios.
    
    Args:
        name: Policy name (see scenario_policies module for supported names)
            
    Returns:
        BotPolicy instance
        
    Raises:
        ValueError: If policy name is not recognized
    """
    from services.scenario_policies import make_scenario_bot_policy
    return make_scenario_bot_policy(name)


# =============================================================================
# Scenario Runner
# =============================================================================

def _initialize_headless_mode() -> None:
    """Initialize headless mode for scenario runs.
    
    Sets environment variables to disable display output for automated
    scenario testing.
    """
    os.environ['SDL_VIDEODRIVER'] = 'dummy'


def _create_game_state_from_map(result: ScenarioMapResult, constants: Dict[str, Any]):
    """Create a simple game state object from a scenario map result."""
    message_log = MessageLog(
        constants["message_x"],
        constants["message_width"],
        constants["message_height"],
    )

    class SimpleGameState:
        def __init__(self, player, entities, game_map, message_log, constants):
            self.player = player
            self.entities = entities
            self.game_map = game_map
            self.message_log = message_log
            self.current_state = GameStates.PLAYERS_TURN
            self.constants = constants
            self.fov_recompute = True
            
            self.fov_map = None

    return SimpleGameState(
        player=result.player,
        entities=result.entities,
        game_map=result.game_map,
        message_log=message_log,
        constants=constants,
    )


def _handle_combat_results(
    results: List[Dict[str, Any]],
    game_state: Any,
    attacker: Any,
    target: Any,
    message_log: Any,
) -> bool:
    """Handle combat action results in a centralized, future-proof way.
    
    Processes all known result types from combat actions:
    - "message": Add to message log
    - "split": Execute split, spawn children, record kill
    - "dead": Handle death, record kill
    - Unknown types: Log warning to prevent silent drops
    
    Args:
        results: List of result dictionaries from combat
        game_state: Current game state
        attacker: The attacking entity
        target: The target entity
        message_log: Message log for combat messages
        
    Returns:
        bool: True if target died or split, False otherwise
    """
    collector = get_active_metrics_collector()
    target_died = False
    
    # Known result types we handle
    # Note: 'xp' is part of 'dead' result, not a separate type
    # Phase 19: Added interrupt_chant, shaman_id, end_rally, chieftain_id
    KNOWN_RESULT_TYPES = {'message', 'split', 'dead', 'xp', 'interrupt_chant', 'shaman_id', 'end_rally', 'chieftain_id'}
    
    for result in results:
        # Check for unknown result types (future-proofing)
        unknown_types = set(result.keys()) - KNOWN_RESULT_TYPES
        if unknown_types:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Scenario harness: Unknown combat result types {unknown_types} "
                f"from {attacker.name if attacker else 'unknown'} -> {target.name if target else 'unknown'}. "
                f"These may not be handled correctly. Result: {result}"
            )
        
        # Handle message
        msg = result.get("message")
        if msg:
            message_log.add_message(msg)
        
        # Phase 19: Handle Split Under Pressure
        split_data = result.get("split")
        if split_data:
            # Entity is splitting - execute the split
            from services.slime_split_service import execute_split
            spawned_children = execute_split(
                split_data,
                game_map=game_state.game_map,
                entities=game_state.entities
            )
            # Add children to entities list
            if spawned_children:
                game_state.entities.extend(spawned_children)
            
            # Check if split caused death (for combat tracking)
            if split_data.get('original_entity') == target:
                target_died = True
                if collector:
                    collector.record_kill(attacker, split_data['original_entity'])
        
        # Phase 19: Handle chant interruption
        if result.get('interrupt_chant'):
            # Chant was interrupted - record metric
            if collector:
                collector.increment('shaman_chant_interrupts')
            
            # Remove dissonant_chant effect from all entities (handled by AI system in normal flow)
            # In scenario harness, we just record the metric
        
        # Handle death
        dead_entity = result.get("dead")
        if dead_entity:
            # Record kill attribution
            if collector:
                collector.record_kill(attacker, dead_entity)
            if dead_entity == target:
                target_died = True
            _handle_entity_death_simple(game_state, dead_entity, message_log)
    
    return target_died


def _process_player_action(
    game_state: Any,
    action: Optional[Dict[str, Any]],
    metrics: RunMetrics,
) -> None:
    """Process a player action and update game state.
    
    Args:
        game_state: Current game state
        action: Action dict from bot policy (or None for wait)
        metrics: RunMetrics to update
    """
    from game_states import GameStates
    
    collector = get_active_metrics_collector()
    
    # Default to wait
    if action is None:
        action = {'wait': True}
    
    # Handle wait action
    if action.get('wait'):
        game_state.current_state = GameStates.ENEMY_TURN
        return
    
    player = game_state.player
    game_map = game_state.game_map
    entities = game_state.entities
    message_log = game_state.message_log
    
    # Simple move action
    if 'move' in action:
        dx, dy = action['move']
        dest_x, dest_y = player.x + dx, player.y + dy
        
        # Check map bounds and blocking entities
        if (0 <= dest_x < game_map.width and 0 <= dest_y < game_map.height
            and not game_map.is_blocked(dest_x, dest_y)):
            blocking = next((e for e in entities if e.blocks and e.x == dest_x and e.y == dest_y), None)
            if blocking is None:
                player.x = dest_x
                player.y = dest_y
        
        game_state.current_state = GameStates.ENEMY_TURN
        return

    # Phase 20C.1: Simple pickup action
    if 'pickup' in action:
        item = action['pickup']
        inventory = player.get_component_optional(ComponentType.INVENTORY)
        if inventory:
            inventory.add_item(item)
            if item in entities:
                entities.remove(item)
            from game_messages import Message
            message_log.add_message(Message(f"You pick up {item.name}."))
        game_state.current_state = GameStates.ENEMY_TURN
        return

    # Phase 20C.1: Simple use item action
    if 'use_item' in action:
        item_index = action['use_item']
        inventory = player.get_component_optional(ComponentType.INVENTORY)
        if inventory and 0 <= item_index < len(inventory.items):
            item_entity = inventory.items.pop(item_index)
            item_comp = item_entity.get_component_optional(ComponentType.ITEM)
            if item_comp and item_comp.use_function:
                # Prepare kwargs for the use function
                use_kwargs = {
                    'entities': entities,
                    'game_map': game_map,
                    'fov_map': game_state.fov_map
                }
                # Call use function
                # Note: most potion functions use item.owner if it exists
                if hasattr(item_comp, 'owner'):
                    item_comp.owner = player
                
                results = item_comp.use_function(player, **use_kwargs)
                # Handle results (mostly just messages)
                from game_messages import Message
                for res in results:
                    msg = res.get('message')
                    if msg:
                        if isinstance(msg, str):
                            message_log.add_message(Message(msg))
                        else:
                            message_log.add_message(msg)
                    
        game_state.current_state = GameStates.ENEMY_TURN
        return
    
    # Phase 20D.1: Throw item action (for root potion entangle scenario)
    if 'throw_item' in action:
        item_index = action['throw_item']
        target = action.get('target')
        inventory = player.get_component_optional(ComponentType.INVENTORY)
        if inventory and 0 <= item_index < len(inventory.items) and target:
            item_entity = inventory.items.pop(item_index)
            item_comp = item_entity.get_component_optional(ComponentType.ITEM)
            if item_comp and item_comp.use_function:
                # Phase 20F: Canonical silence gating for scrolls (spell-like items)
                # Scrolls are blocked by silence; potions are NOT blocked
                item_name_lower = item_entity.name.lower() if hasattr(item_entity, 'name') else ''
                is_scroll = 'scroll' in item_name_lower
                
                if is_scroll:
                    from components.status_effects import check_and_gate_silenced_cast
                    blocked = check_and_gate_silenced_cast(player, f"use the {item_entity.name}")
                    if blocked:
                        # Put item back in inventory (not consumed)
                        inventory.items.insert(item_index, item_entity)
                        # Handle blocked message
                        from game_messages import Message
                        for res in blocked:
                            msg = res.get('message')
                            if msg:
                                if isinstance(msg, str):
                                    message_log.add_message(Message(msg))
                                else:
                                    message_log.add_message(msg)
                        game_state.current_state = GameStates.ENEMY_TURN
                        return
                
                # Prepare kwargs - include target coordinates to signal throw mode
                use_kwargs = {
                    'entities': entities,
                    'game_map': game_map,
                    'fov_map': game_state.fov_map,
                    'target_x': target.x,
                    'target_y': target.y,
                    'throw_mode': True,  # Explicit throw mode flag
                }
                # Apply effect to target (not player)
                results = item_comp.use_function(target, **use_kwargs)
                # Handle results
                from game_messages import Message
                for res in results:
                    msg = res.get('message')
                    if msg:
                        if isinstance(msg, str):
                            message_log.add_message(Message(msg))
                        else:
                            message_log.add_message(msg)
                    
        game_state.current_state = GameStates.ENEMY_TURN
        return
    
    # Simple melee attack action
    if 'attack' in action:
        target = action['attack']
        player_fighter = player.get_component_optional(ComponentType.FIGHTER)
        target_fighter = target.get_component_optional(ComponentType.FIGHTER) if target else None
        
        if player_fighter and target_fighter and target_fighter.hp > 0:
            # Phase 9: Check for surprise attack (unaware monster)
            # Phase 21: Invisibility-based surprise is now handled canonically in
            # Fighter.attack_d20() - all callers converge there for invis bonus + break.
            is_surprise = False
            try:
                from components.ai.basic_monster import is_monster_aware, set_monster_aware
                target_ai = target.get_component_optional(ComponentType.AI)
                if target_ai and not is_monster_aware(target):
                    is_surprise = True
                    if collector:
                        collector.record_surprise_attack(player, target)
                    # Mark monster as aware after surprise attack
                    set_monster_aware(target)
            except Exception as e:
                logger.debug(f"Surprise check error: {e}")
            
            # Perform attack (with surprise flag if applicable, plus game_map/entities for knockback)
            attack_results = player_fighter.attack_d20(
                target, 
                is_surprise=is_surprise,
                game_map=game_state.game_map,
                entities=game_state.entities
            )
            
            # Handle all combat results (centralized for future-proofing)
            target_died = _handle_combat_results(
                attack_results, game_state, player, target, message_log
            )
            
            # Phase 13D: Check for player bonus attack (speed momentum system)
            # Only roll if target is still alive and player is faster than target
            if not target_died and target_fighter and target_fighter.hp > 0:
                speed_tracker = player.get_component_optional(ComponentType.SPEED_BONUS_TRACKER)
                if speed_tracker:
                    # Gate: Only roll if player is faster than target
                    player_speed = speed_tracker.speed_bonus_ratio
                    target_speed_tracker = target.get_component_optional(ComponentType.SPEED_BONUS_TRACKER)
                    target_speed = target_speed_tracker.speed_bonus_ratio if target_speed_tracker else 0.0
                    
                    if player_speed > target_speed:
                        # Roll for bonus attack
                        if speed_tracker.roll_for_bonus_attack():
                            if collector:
                                collector.record_bonus_attack(player, target)
                            # Execute bonus attack immediately (with game_map/entities for knockback)
                            bonus_attack_results = player_fighter.attack_d20(
                                target, 
                                is_surprise=False,
                                game_map=game_state.game_map,
                                entities=game_state.entities
                            )
                            
                            # Handle all combat results (centralized for future-proofing)
                            _handle_combat_results(
                                bonus_attack_results, game_state, player, target, message_log
                            )
        game_state.current_state = GameStates.ENEMY_TURN
        return
    
    # Fallback: wait
    game_state.current_state = GameStates.ENEMY_TURN


def _process_pending_reanimations(game_state: Any, metrics: RunMetrics) -> None:
    """Process pending plague reanimations.
    
    Phase 10: Check for corpses that should reanimate and spawn revenant zombies.
    
    Args:
        game_state: Current game state
        metrics: RunMetrics to update (reanimations)
    """
    from death_functions import process_pending_reanimations
    
    collector = get_active_metrics_collector()
    entities = game_state.entities
    game_map = game_state.game_map
    turn_number = getattr(game_state, 'turn_number', 0)
    
    # Process reanimations
    results = process_pending_reanimations(entities, game_map, turn_number)
    
    # Add any newly reanimated entities to the entity list and record metrics
    for result in results:
        if 'new_entity' in result:
            new_entity = result['new_entity']
            entities.append(new_entity)
            if collector:
                collector.record_reanimation(new_entity)
            logger.debug(f"Plague reanimation: {new_entity.name} spawned")


def _process_enemy_turn(game_state: Any, metrics: RunMetrics, state_manager=None) -> None:
    """Process the enemy turn phase.
    
    Args:
        game_state: Current game state
        metrics: RunMetrics to update (kills_by_faction)
        state_manager: Optional StateManager for death finalization
    """
    # Get all AI entities
    ai_entities = [
        e for e in game_state.entities
        if e != game_state.player
        and hasattr(e, 'ai') and e.ai is not None
        and hasattr(e, 'fighter') and e.fighter is not None
        and e.fighter.hp > 0
    ]
    
    # Phase 19: Lich diagnostics can be enabled if needed
    # liches = [e for e in ai_entities if 'lich' in e.name.lower()]
    # if liches:
    #     logger.debug(f"[ENEMY TURN] {len(liches)} lich(es) alive")
    
    # Process each AI entity's turn
    for entity in ai_entities:
        try:
            if entity.ai and callable(getattr(entity.ai, 'take_turn', None)):
                # Get state required for AI turn
                target = game_state.player
                fov_map = getattr(game_state, 'fov_map', None)
                game_map = game_state.game_map
                entities = game_state.entities
                
                # Process AI turn
                ai_results = entity.ai.take_turn(target, fov_map, game_map, entities)
                
                # Phase 20C.1: Handle AI results (combat, messages, etc.)
                if ai_results:
                    # Use the shared combat result handler if possible, or handle simply
                    for result in ai_results:
                        if 'message' in result:
                            msg = result['message']
                            if isinstance(msg, str):
                                from game_messages import Message
                                game_state.message_log.add_message(Message(msg))
                            else:
                                game_state.message_log.add_message(msg)
                        
                        # Handle player death detection from monster attack
                        dead_entity = result.get('dead')
                        if dead_entity == game_state.player:
                            game_state.current_state = GameStates.PLAYER_DEAD

        except Exception as e:
            logger.debug(f"AI turn error for {entity.name}: {e}")
    
    # Process pending reanimations (Phase 10: plague zombies)
    _process_pending_reanimations(game_state, metrics)
    
    # Phase 20A: Process player status effects (DOT ticks, debuff durations, etc.)
    _process_player_status_effects_harness(game_state, state_manager=state_manager)
    
    # Return to player turn
    game_state.current_state = GameStates.PLAYERS_TURN


def _process_player_status_effects_harness(game_state: Any, state_manager=None) -> None:
    """Process player status effects at end of enemy turn.
    
    Phase 20A: This handles DOT effects like poison, soul burn, etc.
    The harness needs to tick status effects since it bypasses the full engine.
    
    Args:
        game_state: Current game state
        state_manager: Optional StateManager for death finalization (CRITICAL for DOT deaths)
    """
    player = game_state.player
    if not player or not hasattr(player, 'status_effects') or not player.status_effects:
        return
    
    # Process status effects at turn start (this is when DOTs tick)
    # Pass state_manager to ensure DOT effects can properly finalize player death
    status_results = player.status_effects.process_turn_start(
        entities=game_state.entities,
        state_manager=state_manager  # CRITICAL: Enables proper death finalization
    )
    
    # Add any messages to the message log
    message_log = game_state.message_log
    for result in status_results:
        if 'message' in result:
            message_log.add_message(result['message'])
        
        # Check for player death from status effects
        if result.get('dead'):
            game_state.current_state = GameStates.PLAYER_DEAD
    
    # Process turn end (decrement durations)
    end_results = player.status_effects.process_turn_end()
    for result in end_results:
        if 'message' in result:
            message_log.add_message(result['message'])


def _handle_entity_death_simple(game_state: Any, dead_entity: Any, message_log: Any) -> None:
    """Minimal death handling for harness to keep state consistent."""
    from death_functions import kill_player, kill_monster
    
    player = game_state.player
    if dead_entity == player:
        death_message, new_state = kill_player(player)
        message_log.add_message(death_message)
        game_state.current_state = new_state
        return
    
    game_map = game_state.game_map
    entities = game_state.entities
    death_message = kill_monster(dead_entity, game_map, entities)
    if death_message:
        message_log.add_message(death_message)


def _check_player_death(game_state: Any) -> bool:
    """Check if the player has died.
    
    Args:
        game_state: Current game state
        
    Returns:
        True if player is dead, False otherwise
    """
    player = game_state.player
    if player is None:
        return True
    
    if hasattr(player, 'fighter') and player.fighter is not None:
        return player.fighter.hp <= 0
    
    return False


def _count_dead_entities(game_state: Any, metrics: RunMetrics) -> None:
    """Count dead entities and update kill metrics.
    
    This is a simplified kill tracking for Phase 12B.
    
    TODO (Phase 12C): Wire into death events for accurate kill attribution.
    
    Args:
        game_state: Current game state
        metrics: RunMetrics to update
    """
    # For now, we just count player kills as a simple metric
    # More sophisticated kill tracking will come in Phase 12C
    pass


def run_scenario_once(
    scenario,
    bot_policy: BotPolicy,
    turn_limit: int,
) -> RunMetrics:
    """Run a scenario once and collect metrics.
    
    This function:
    1. Initializes a minimal game state for the scenario
    2. Runs the game loop until turn_limit or termination
    3. Collects and returns metrics
    
    Args:
        scenario: ScenarioDefinition from the registry
        bot_policy: BotPolicy for player control
        turn_limit: Maximum turns to run
        
    Returns:
        RunMetrics with collected data
    """
    logger.info(f"Starting scenario run: {scenario.scenario_id} (turn_limit={turn_limit})")
    
    # Initialize headless mode
    _initialize_headless_mode()
    
    # Phase 19: Initialize spell registry for raise_dead and other spells
    from spells.spell_catalog import register_all_spells
    register_all_spells()
    
    # Initialize metrics
    metrics = RunMetrics(
        turns_taken=0,
        player_died=False,
        kills_by_faction=defaultdict(int),
        kills_by_source=defaultdict(int),
    )
    
    try:
        with scoped_metrics_collector(metrics):
            constants = get_constants()
            if scenario.depth is not None:
                constants["start_level"] = scenario.depth

            map_result = build_scenario_map(scenario)
            validate_scenario_instance(scenario, map_result.game_map, map_result.player, map_result.entities)

            game_state = _create_game_state_from_map(map_result, constants)
            game_state.turn_number = 0  # Track turn number for reanimations

            # Create a minimal StateManager for death finalization
            # This ensures DOT effects can properly finalize player death
            from state_management.state_config import StateManager
            state_manager = StateManager()
            state_manager.state = game_state

            # Main loop
            for turn in range(turn_limit):
                if _check_player_death(game_state):
                    metrics.player_died = True
                    logger.info(f"Scenario ended: player death at turn {turn + 1}")
                    break

                if game_state.current_state == GameStates.PLAYERS_TURN:
                    action = bot_policy.choose_action(game_state)
                    # logger.info(f"Turn {turn}: Player action: {action}")
                    _process_player_action(game_state, action, metrics)

                elif game_state.current_state == GameStates.ENEMY_TURN:
                    # logger.info(f"Turn {turn}: Enemy turn")
                    _process_enemy_turn(game_state, metrics, state_manager=state_manager)
                    metrics.turns_taken += 1
                    game_state.turn_number += 1  # Increment turn for reanimation timing

                elif game_state.current_state == GameStates.PLAYER_DEAD:
                    metrics.player_died = True
                    logger.info(f"Scenario ended: player death at turn {metrics.turns_taken}")
                    break

                else:
                    game_state.current_state = GameStates.PLAYERS_TURN

            if metrics.turns_taken == 0:
                metrics.turns_taken = min(turn_limit, 1)

            _count_dead_entities(game_state, metrics)

    except (ScenarioBuildError, ScenarioInvariantError) as e:
        logger.error(f"Scenario setup failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Scenario run error: {e}", exc_info=True)
        if metrics.turns_taken == 0:
            metrics.turns_taken = 1
    
    # Convert defaultdict to regular dict for serialization
    metrics.kills_by_faction = dict(metrics.kills_by_faction)
    metrics.kills_by_source = dict(metrics.kills_by_source)
    
    logger.info(f"Scenario run complete: turns={metrics.turns_taken}, "
                f"player_died={metrics.player_died}")
    
    return metrics


def run_scenario_many(
    scenario,
    bot_policy: BotPolicy,
    runs: int,
    turn_limit: int,
    seed_base: Optional[int] = None,
) -> AggregatedMetrics:
    """Run a scenario multiple times and aggregate metrics.
    
    Args:
        scenario: ScenarioDefinition from the registry
        bot_policy: BotPolicy for player control
        runs: Number of times to run the scenario
        turn_limit: Maximum turns per run
        seed_base: Base seed for deterministic runs (or None for non-deterministic)
        
    Returns:
        AggregatedMetrics with combined data from all runs
    """
    logger.info(f"Starting {runs} scenario runs: {scenario.scenario_id}")
    if seed_base is not None:
        logger.info(f"Deterministic mode enabled: seed_base={seed_base}")
    
    # Collect individual run results
    all_runs: List[RunMetrics] = []
    
    for run_num in range(1, runs + 1):
        logger.info(f"Run {run_num}/{runs}")
        
        # Reset any necessary state between runs
        _reset_global_services()
        
        # Set deterministic seed for this run if seed_base is provided
        if seed_base is not None:
            from engine.rng_config import stable_scenario_seed, set_global_seed
            run_seed = stable_scenario_seed(scenario.scenario_id, run_num - 1, seed_base)
            set_global_seed(run_seed)
            logger.debug(f"Run {run_num}: seed={run_seed}")
        
        # Run the scenario
        run_metrics = run_scenario_once(scenario, bot_policy, turn_limit)
        all_runs.append(run_metrics)
    
    # Aggregate results
    total_turns = sum(r.turns_taken for r in all_runs)
    player_deaths = sum(1 for r in all_runs if r.player_died)
    
    # Merge kills by faction/source
    merged_kills_by_faction: Dict[str, int] = defaultdict(int)
    merged_kills_by_source: Dict[str, int] = defaultdict(int)
    total_plague_infections = 0
    total_reanimations = 0
    total_surprise_attacks = 0
    total_invis_attacks = 0
    total_invis_broken_by_attack = 0
    total_bonus_attacks = 0
    total_player_attacks = 0
    total_player_hits = 0
    total_monster_attacks = 0
    total_monster_hits = 0
    total_portals_used = 0
    
    for run in all_runs:
        for faction, count in run.kills_by_faction.items():
            merged_kills_by_faction[faction] += count
        for source, count in run.kills_by_source.items():
            merged_kills_by_source[source] += count
        total_plague_infections += run.plague_infections
        total_reanimations += run.reanimations
        total_surprise_attacks += run.surprise_attacks
        total_invis_attacks += getattr(run, 'invis_attacks', 0)
        total_invis_broken_by_attack += getattr(run, 'invis_broken_by_attack', 0)
        total_bonus_attacks += run.bonus_attacks_triggered
        total_player_attacks += run.player_attacks
        total_player_hits += run.player_hits
        total_monster_attacks += run.monster_attacks
        total_monster_hits += run.monster_hits
        total_portals_used += getattr(run, "portals_used", 0)
    
    # Phase 19: Aggregate split metrics
    total_split_events = 0
    total_split_children = 0
    merged_split_by_type = {}
    # Phase 19: Aggregate wraith drain metrics
    total_drain_attempts = 0
    total_drain_heal = 0
    total_drain_blocked = 0
    for run in all_runs:
        total_drain_attempts += getattr(run, "life_drain_attempts", 0)
        total_drain_heal += getattr(run, "life_drain_heal_total", 0)
        total_drain_blocked += getattr(run, "life_drain_blocked_attempts", 0)
    
    # Phase 19: Aggregate orc shaman metrics
    total_shaman_hex_casts = 0
    total_shaman_chant_starts = 0
    total_shaman_chant_interrupts = 0
    total_shaman_chant_expiries = 0
    for run in all_runs:
        total_shaman_hex_casts += getattr(run, "shaman_hex_casts", 0)
        total_shaman_chant_starts += getattr(run, "shaman_chant_starts", 0)
        total_shaman_chant_interrupts += getattr(run, "shaman_chant_interrupts", 0)
        total_shaman_chant_expiries += getattr(run, "shaman_chant_expiries", 0)
    
    # Phase 19: Aggregate necromancer metrics
    total_necro_raise_attempts = 0
    total_necro_raise_successes = 0
    total_necro_corpse_seek_moves = 0
    total_necro_unsafe_move_blocks = 0
    for run in all_runs:
        total_necro_raise_attempts += getattr(run, "necro_raise_attempts", 0)
        total_necro_raise_successes += getattr(run, "necro_raise_successes", 0)
        total_necro_corpse_seek_moves += getattr(run, "necro_corpse_seek_moves", 0)
        total_necro_unsafe_move_blocks += getattr(run, "necro_unsafe_move_blocks", 0)
    
    # Phase 20: Aggregate corpse lifecycle metrics
    total_fresh_corpses_created = 0
    total_spent_corpses_created = 0
    total_raises_completed = 0
    total_spent_corpses_exploded = 0
    for run in all_runs:
        total_fresh_corpses_created += getattr(run, "fresh_corpses_created", 0)
        total_spent_corpses_created += getattr(run, "spent_corpses_created", 0)
        total_raises_completed += getattr(run, "raises_completed", 0)
        total_spent_corpses_exploded += getattr(run, "spent_corpses_exploded", 0)
    
    # Phase 19: Aggregate lich metrics
    total_lich_ticks_alive = 0
    total_lich_ticks_in_range = 0
    total_lich_ticks_has_los = 0
    total_lich_ticks_eligible = 0
    total_lich_soul_bolt_charges = 0
    total_lich_soul_bolt_casts = 0
    total_soul_ward_blocks = 0
    total_lich_death_siphon_heals = 0
    for run in all_runs:
        total_lich_ticks_alive += getattr(run, "lich_ticks_alive", 0)
        total_lich_ticks_in_range += getattr(run, "lich_ticks_player_in_range", 0)
        total_lich_ticks_has_los += getattr(run, "lich_ticks_has_los", 0)
        total_lich_ticks_eligible += getattr(run, "lich_ticks_eligible_to_charge", 0)
        total_lich_soul_bolt_charges += getattr(run, "lich_soul_bolt_charges", 0)
        total_lich_soul_bolt_casts += getattr(run, "lich_soul_bolt_casts", 0)
        total_soul_ward_blocks += getattr(run, "soul_ward_blocks", 0)
        total_lich_death_siphon_heals += getattr(run, "lich_death_siphon_heals", 0)
    
    for run in all_runs:
        total_split_events += getattr(run, "split_events_total", 0)
        total_split_children += getattr(run, "split_children_spawned", 0)
        if hasattr(run, "split_events_by_type"):
            for monster_type, count in run.split_events_by_type.items():
                merged_split_by_type[monster_type] = merged_split_by_type.get(monster_type, 0) + count
    
    # Phase 20A: Aggregate poison metrics
    total_poison_applications = 0
    total_poison_damage_dealt = 0
    total_poison_ticks_processed = 0
    total_poison_kills = 0
    total_deaths_with_active_poison = 0
    for run in all_runs:
        total_poison_applications += getattr(run, "poison_applications", 0)
        total_poison_damage_dealt += getattr(run, "poison_damage_dealt", 0)
        total_poison_ticks_processed += getattr(run, "poison_ticks_processed", 0)
        total_poison_kills += getattr(run, "poison_kills", 0)
        total_deaths_with_active_poison += getattr(run, "deaths_with_active_poison", 0)

    # Phase 20B.1: Aggregate burning metrics
    total_burning_applications = 0
    total_burning_damage_dealt = 0
    total_burning_ticks_processed = 0
    total_burning_kills = 0
    for run in all_runs:
        total_burning_applications += getattr(run, "burning_applications", 0)
        total_burning_damage_dealt += getattr(run, "burning_damage_dealt", 0)
        total_burning_ticks_processed += getattr(run, "burning_ticks_processed", 0)
        total_burning_kills += getattr(run, "burning_kills", 0)
    
    # Phase 20C.1: Aggregate slow metrics
    total_slow_applications = 0
    total_slow_turns_skipped = 0
    for run in all_runs:
        total_slow_applications += getattr(run, "slow_applications", 0)
        total_slow_turns_skipped += getattr(run, "slow_turns_skipped", 0)

    # Phase 20C.1: Aggregate reflex metrics
    total_reflex_potions_used = 0
    total_bonus_attacks_while_reflexes_active = 0
    for run in all_runs:
        total_reflex_potions_used += getattr(run, "reflex_potions_used", 0)
        total_bonus_attacks_while_reflexes_active += getattr(run, "bonus_attacks_while_reflexes_active", 0)
    
    # Phase 20D.1: Aggregate entangle metrics
    total_entangle_applications = 0
    total_entangle_moves_blocked = 0
    for run in all_runs:
        total_entangle_applications += getattr(run, "entangle_applications", 0)
        total_entangle_moves_blocked += getattr(run, "entangle_moves_blocked", 0)
    
    # Phase 20E.1: Aggregate blind metrics
    total_blind_applications = 0
    total_blind_attacks_attempted = 0
    total_blind_attacks_missed = 0
    for run in all_runs:
        total_blind_applications += getattr(run, "blind_applications", 0)
        total_blind_attacks_attempted += getattr(run, "blind_attacks_attempted", 0)
        total_blind_attacks_missed += getattr(run, "blind_attacks_missed", 0)
    
    # Phase 20E.2: Aggregate disarm metrics
    total_disarm_applications = 0
    total_disarmed_attacks_attempted = 0
    total_disarmed_weapon_attacks_prevented = 0
    for run in all_runs:
        total_disarm_applications += getattr(run, "disarm_applications", 0)
        total_disarmed_attacks_attempted += getattr(run, "disarmed_attacks_attempted", 0)
        total_disarmed_weapon_attacks_prevented += getattr(run, "disarmed_weapon_attacks_prevented", 0)
    
    # Phase 20F: Aggregate silence metrics
    total_silence_applications = 0
    total_silenced_casts_blocked = 0
    for run in all_runs:
        total_silence_applications += getattr(run, "silence_applications", 0)
        total_silenced_casts_blocked += getattr(run, "silenced_casts_blocked", 0)
    
    # Weapon Knockback metrics aggregation
    total_knockback_applications = 0
    total_knockback_tiles_moved = 0
    total_knockback_blocked_events = 0
    total_stagger_applications = 0
    total_stagger_turns_skipped = 0
    for run in all_runs:
        total_knockback_applications += getattr(run, "knockback_applications", 0)
        total_knockback_tiles_moved += getattr(run, "knockback_tiles_moved", 0)
        total_knockback_blocked_events += getattr(run, "knockback_blocked_events", 0)
        total_stagger_applications += getattr(run, "stagger_applications", 0)
        total_stagger_turns_skipped += getattr(run, "stagger_turns_skipped", 0)

    # Phase 20 Scroll Modernization: Aggregate Dragon Fart metrics
    total_dragon_fart_casts = 0
    total_dragon_fart_tiles_created = 0
    total_sleep_applications = 0
    total_sleep_turns_prevented = 0
    for run in all_runs:
        total_dragon_fart_casts += getattr(run, "dragon_fart_casts", 0)
        total_dragon_fart_tiles_created += getattr(run, "dragon_fart_tiles_created", 0)
        total_sleep_applications += getattr(run, "sleep_applications", 0)
        total_sleep_turns_prevented += getattr(run, "sleep_turns_prevented", 0)

    # Phase 20 Scroll Modernization: Aggregate Fireball metrics
    total_fireball_casts = 0
    total_fireball_tiles_created = 0
    total_fireball_direct_damage = 0
    for run in all_runs:
        total_fireball_casts += getattr(run, "fireball_casts", 0)
        total_fireball_tiles_created += getattr(run, "fireball_tiles_created", 0)
        total_fireball_direct_damage += getattr(run, "fireball_direct_damage", 0)

    # Phase 22.1.1: Aggregate Oath metrics (Run Identity - refined)
    total_oath_embers_chosen = 0
    total_oath_venom_chosen = 0
    total_oath_chains_chosen = 0
    total_oath_embers_procs = 0
    total_oath_embers_self_burn_procs = 0
    total_oath_venom_procs = 0
    total_oath_venom_duration_extensions = 0
    total_oath_chains_bonus_applied = 0
    total_oath_chains_bonus_denied = 0
    total_knockback_tiles_moved_by_player = 0
    for run in all_runs:
        total_oath_embers_chosen += getattr(run, "oath_embers_chosen", 0)
        total_oath_venom_chosen += getattr(run, "oath_venom_chosen", 0)
        total_oath_chains_chosen += getattr(run, "oath_chains_chosen", 0)
        total_oath_embers_procs += getattr(run, "oath_embers_procs", 0)
        total_oath_embers_self_burn_procs += getattr(run, "oath_embers_self_burn_procs", 0)
        total_oath_venom_procs += getattr(run, "oath_venom_procs", 0)
        total_oath_venom_duration_extensions += getattr(run, "oath_venom_duration_extensions", 0)
        total_oath_chains_bonus_applied += getattr(run, "oath_chains_bonus_applied", 0)
        total_oath_chains_bonus_denied += getattr(run, "oath_chains_bonus_denied", 0)
        total_knockback_tiles_moved_by_player += getattr(run, "knockback_tiles_moved_by_player", 0)

    # Phase 22.2: Aggregate ranged combat metrics
    total_ranged_attacks_made_by_player = 0
    total_ranged_attacks_denied_out_of_range = 0
    total_ranged_damage_dealt_by_player = 0
    total_ranged_damage_penalty_total = 0
    total_ranged_adjacent_retaliations_triggered = 0
    total_ranged_knockback_procs = 0
    for run in all_runs:
        total_ranged_attacks_made_by_player += getattr(run, "ranged_attacks_made_by_player", 0)
        total_ranged_attacks_denied_out_of_range += getattr(run, "ranged_attacks_denied_out_of_range", 0)
        total_ranged_damage_dealt_by_player += getattr(run, "ranged_damage_dealt_by_player", 0)
        total_ranged_damage_penalty_total += getattr(run, "ranged_damage_penalty_total", 0)
        total_ranged_adjacent_retaliations_triggered += getattr(run, "ranged_adjacent_retaliations_triggered", 0)
        total_ranged_knockback_procs += getattr(run, "ranged_knockback_procs", 0)

    # Terminal state overwrite metrics (diagnostic)
    total_terminal_overwrite_attempts = 0
    merged_terminal_overwrite_by_target: Dict[str, int] = {}
    for run in all_runs:
        total_terminal_overwrite_attempts += getattr(run, "terminal_overwrite_attempts", 0)
        run_by_target = getattr(run, "terminal_overwrite_by_target", {})
        for target, count in run_by_target.items():
            merged_terminal_overwrite_by_target[target] = \
                merged_terminal_overwrite_by_target.get(target, 0) + count

    aggregated = AggregatedMetrics(
        runs=runs,
        average_turns=total_turns / runs if runs > 0 else 0.0,
        player_deaths=player_deaths,
        depth=getattr(scenario, "depth", None),
        total_kills_by_faction=dict(merged_kills_by_faction),
        total_kills_by_source=dict(merged_kills_by_source),
        total_plague_infections=total_plague_infections,
        total_reanimations=total_reanimations,
        total_surprise_attacks=total_surprise_attacks,
        total_invis_attacks=total_invis_attacks,
        total_invis_broken_by_attack=total_invis_broken_by_attack,
        total_bonus_attacks_triggered=total_bonus_attacks,
        total_player_attacks=total_player_attacks,
        total_player_hits=total_player_hits,
        total_monster_attacks=total_monster_attacks,
        total_monster_hits=total_monster_hits,
        total_portals_used=total_portals_used,
        total_split_events=total_split_events,
        total_split_children_spawned=total_split_children,
        total_split_events_by_type=dict(merged_split_by_type),
        total_life_drain_attempts=total_drain_attempts,
        total_life_drain_heal_total=total_drain_heal,
        total_life_drain_blocked_attempts=total_drain_blocked,
        total_shaman_hex_casts=total_shaman_hex_casts,
        total_shaman_chant_starts=total_shaman_chant_starts,
        total_shaman_chant_interrupts=total_shaman_chant_interrupts,
        total_shaman_chant_expiries=total_shaman_chant_expiries,
        total_lich_ticks_alive=total_lich_ticks_alive,
        total_lich_ticks_player_in_range=total_lich_ticks_in_range,
        total_lich_ticks_has_los=total_lich_ticks_has_los,
        total_lich_ticks_eligible_to_charge=total_lich_ticks_eligible,
        total_lich_soul_bolt_charges=total_lich_soul_bolt_charges,
        total_lich_soul_bolt_casts=total_lich_soul_bolt_casts,
        total_soul_ward_blocks=total_soul_ward_blocks,
        total_lich_death_siphon_heals=total_lich_death_siphon_heals,
        total_necro_raise_attempts=total_necro_raise_attempts,
        total_necro_raise_successes=total_necro_raise_successes,
        total_necro_corpse_seek_moves=total_necro_corpse_seek_moves,
        total_necro_unsafe_move_blocks=total_necro_unsafe_move_blocks,
        total_fresh_corpses_created=total_fresh_corpses_created,
        total_spent_corpses_created=total_spent_corpses_created,
        total_raises_completed=total_raises_completed,
        total_spent_corpses_exploded=total_spent_corpses_exploded,
        total_poison_applications=total_poison_applications,
        total_poison_damage_dealt=total_poison_damage_dealt,
        total_poison_ticks_processed=total_poison_ticks_processed,
        total_poison_kills=total_poison_kills,
        total_deaths_with_active_poison=total_deaths_with_active_poison,
        total_burning_applications=total_burning_applications,
        total_burning_damage_dealt=total_burning_damage_dealt,
        total_burning_ticks_processed=total_burning_ticks_processed,
        total_burning_kills=total_burning_kills,
        total_slow_applications=total_slow_applications,
        total_slow_turns_skipped=total_slow_turns_skipped,
        total_reflex_potions_used=total_reflex_potions_used,
        total_bonus_attacks_while_reflexes_active=total_bonus_attacks_while_reflexes_active,
        total_entangle_applications=total_entangle_applications,
        total_entangle_moves_blocked=total_entangle_moves_blocked,
        total_blind_applications=total_blind_applications,
        total_blind_attacks_attempted=total_blind_attacks_attempted,
        total_blind_attacks_missed=total_blind_attacks_missed,
        total_disarm_applications=total_disarm_applications,
        total_disarmed_attacks_attempted=total_disarmed_attacks_attempted,
        total_disarmed_weapon_attacks_prevented=total_disarmed_weapon_attacks_prevented,
        total_silence_applications=total_silence_applications,
        total_silenced_casts_blocked=total_silenced_casts_blocked,
        # Weapon Knockback metrics
        total_knockback_applications=total_knockback_applications,
        total_knockback_tiles_moved=total_knockback_tiles_moved,
        total_knockback_blocked_events=total_knockback_blocked_events,
        total_stagger_applications=total_stagger_applications,
        total_stagger_turns_skipped=total_stagger_turns_skipped,
        # Phase 20 Scroll Modernization: Dragon Fart metrics
        total_dragon_fart_casts=total_dragon_fart_casts,
        total_dragon_fart_tiles_created=total_dragon_fart_tiles_created,
        total_sleep_applications=total_sleep_applications,
        total_sleep_turns_prevented=total_sleep_turns_prevented,
        # Phase 20 Scroll Modernization: Fireball metrics
        total_fireball_casts=total_fireball_casts,
        total_fireball_tiles_created=total_fireball_tiles_created,
        total_fireball_direct_damage=total_fireball_direct_damage,
        # Phase 22.1.1: Oath metrics (Run Identity - refined)
        total_oath_embers_chosen=total_oath_embers_chosen,
        total_oath_venom_chosen=total_oath_venom_chosen,
        total_oath_chains_chosen=total_oath_chains_chosen,
        total_oath_embers_procs=total_oath_embers_procs,
        total_oath_embers_self_burn_procs=total_oath_embers_self_burn_procs,
        total_oath_venom_procs=total_oath_venom_procs,
        total_oath_venom_duration_extensions=total_oath_venom_duration_extensions,
        total_oath_chains_bonus_applied=total_oath_chains_bonus_applied,
        total_oath_chains_bonus_denied=total_oath_chains_bonus_denied,
        total_knockback_tiles_moved_by_player=total_knockback_tiles_moved_by_player,
        # Phase 22.2: Ranged combat metrics
        total_ranged_attacks_made_by_player=total_ranged_attacks_made_by_player,
        total_ranged_attacks_denied_out_of_range=total_ranged_attacks_denied_out_of_range,
        total_ranged_damage_dealt_by_player=total_ranged_damage_dealt_by_player,
        total_ranged_damage_penalty_total=total_ranged_damage_penalty_total,
        total_ranged_adjacent_retaliations_triggered=total_ranged_adjacent_retaliations_triggered,
        total_ranged_knockback_procs=total_ranged_knockback_procs,
        # Terminal state overwrite metrics (diagnostic)
        total_terminal_overwrite_attempts=total_terminal_overwrite_attempts,
        total_terminal_overwrite_by_target=merged_terminal_overwrite_by_target,
    )
    
    logger.info(f"Scenario runs complete: {runs} runs, "
                f"avg_turns={aggregated.average_turns:.1f}, "
                f"deaths={aggregated.player_deaths}")
    
    # Phase 22.1.2: Print Oath summary if present
    oath_summary = aggregated.get_oath_summary()
    if oath_summary:
        logger.info("=" * 60)
        logger.info("OATH IDENTITY SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Oath: {oath_summary['oath'].upper()}")
        logger.info(f"Runs: {oath_summary['runs']}")
        
        if oath_summary['oath'] == 'embers':
            logger.info(f"  Burn Procs: {oath_summary['procs']}")
            logger.info(f"  Self-Burn Procs: {oath_summary['self_burn_procs']}")
            logger.info(f"  Risk Ratio: {oath_summary['risk_ratio']} (self-burns per proc)")
        elif oath_summary['oath'] == 'venom':
            logger.info(f"  Poison Procs: {oath_summary['procs']}")
            logger.info(f"  Duration Extensions: {oath_summary['duration_extensions']}")
            logger.info(f"  Extension Ratio: {oath_summary['extension_ratio']} (extensions per proc)")
        elif oath_summary['oath'] == 'chains':
            logger.info(f"  Bonus Applied: {oath_summary['bonus_applied']}")
            logger.info(f"  Bonus Denied: {oath_summary['bonus_denied']}")
            logger.info(f"  Total Attempts: {oath_summary['total_knockback_attempts']}")
            logger.info(f"  Mobility Cost: {oath_summary['mobility_cost_pct']}% (times bonus denied)")
        
        logger.info("=" * 60)
    
    return aggregated


def _reset_global_services() -> None:
    """Reset global services between scenario runs.
    
    This ensures each run has a clean state, similar to what
    the soak harness does.
    """
    try:
        from instrumentation.run_metrics import reset_run_metrics_recorder
        reset_run_metrics_recorder()
    except ImportError:
        pass
    
    try:
        from services.telemetry_service import reset_telemetry_service
        reset_telemetry_service()
    except ImportError:
        pass
    
    try:
        from services.movement_service import reset_movement_service
        reset_movement_service()
    except ImportError:
        pass
    
    try:
        from services.pickup_service import reset_pickup_service
        reset_pickup_service()
    except ImportError:
        pass
    
    try:
        from services.floor_state_manager import reset_floor_state_manager
        reset_floor_state_manager()
    except ImportError:
        pass
    
    # Reset identification manager (caches item identification decisions)
    try:
        from config.identification_manager import reset_identification_manager
        reset_identification_manager()
    except ImportError:
        pass


# =============================================================================
# Expected invariants evaluation
# =============================================================================


@dataclass
class ExpectationResult:
    """Result for a single expectation check."""
    key: str
    expected: Any
    actual: Any
    comparator: str
    passed: bool
    message: str


@dataclass
class ExpectedCheckResult:
    passed: bool
    failures: List[str]


def evaluate_expectations(
    scenario: Any,
    metrics: AggregatedMetrics,
) -> Tuple[List[ExpectationResult], List[str]]:
    """Evaluate supported expectations and return results plus unsupported keys."""
    expected = getattr(scenario, "expected", {}) or {}
    results: List[ExpectationResult] = []
    unsupported: List[str] = []

    def _record(
        key: str,
        expected_value: Any,
        actual_value: Any,
        comparator: str,
        comparison_fn,
    ) -> None:
        passed = comparison_fn(actual_value, expected_value)
        message = f"{key}: expected {comparator} {expected_value}, actual {actual_value}"
        results.append(
            ExpectationResult(
                key=key,
                expected=expected_value,
                actual=actual_value,
                comparator=comparator,
                passed=passed,
                message=message,
            )
        )

    supported_checks = {
        "min_player_kills": (
            ">=",
            lambda m: m.total_kills_by_source.get("PLAYER", 0),
            lambda actual, expected_value: actual >= expected_value,
        ),
        "max_player_deaths": (
            "<=",
            lambda m: m.player_deaths,
            lambda actual, expected_value: actual <= expected_value,
        ),
        "plague_infections_min": (
            ">=",
            lambda m: m.total_plague_infections,
            lambda actual, expected_value: actual >= expected_value,
        ),
        "reanimations_min": (
            ">=",
            lambda m: m.total_reanimations,
            lambda actual, expected_value: actual >= expected_value,
        ),
        "surprise_attacks_min": (
            ">=",
            lambda m: m.total_surprise_attacks,
            lambda actual, expected_value: actual >= expected_value,
        ),
        "bonus_attacks_min": (
            ">=",
            lambda m: m.total_bonus_attacks_triggered,
            lambda actual, expected_value: actual >= expected_value,
        ),
    }

    for key, expected_value in expected.items():
        if key not in supported_checks:
            unsupported.append(key)
            continue
        comparator, actual_getter, compare_fn = supported_checks[key]
        actual_value = actual_getter(metrics)
        _record(key, expected_value, actual_value, comparator, compare_fn)

    return results, unsupported


def evaluate_expected_invariants(
    scenario: Any,
    metrics: AggregatedMetrics,
) -> ExpectedCheckResult:
    """Evaluate scenario.expected constraints against aggregated metrics."""
    results, unsupported = evaluate_expectations(scenario, metrics)
    failures = [r.message for r in results if not r.passed]
    # Unsupported keys are not treated as failures for backwards compatibility.
    return ExpectedCheckResult(passed=len(failures) == 0, failures=failures)


# =============================================================================
# Convenience exports
# =============================================================================

__all__ = [
    'RunMetrics',
    'AggregatedMetrics',
    'BotPolicy',
    'make_bot_policy',  # Deprecated wrapper, use scenario_policies directly
    'ExpectationResult',
    'ExpectedCheckResult',
    'evaluate_expectations',
    'evaluate_expected_invariants',
    'run_scenario_once',
    'run_scenario_many',
]
