"""Phase 19: Lich (Arch-Necromancer) AI

Lich is an elite undead controller with powerful personal combat abilities:

1. Soul Bolt (2-turn telegraph + resolve):
   - Turn 1 (charging): Apply ChargingSoulBoltEffect, message "channeling dark energy"
   - Turn 2 (resolve): If player still in LOS + range, fire Soul Bolt for ceil(0.35 * target.max_hp) damage
   - Cooldown: 4 turns after resolution
   - Soul Ward counter: If player has Soul Ward active, reduce damage by 70%, convert to Soul Burn DOT

2. Command the Dead (passive aura):
   - Allied undead within radius 6 get +1 to-hit
   - Checked during attack_d20() in fighter.py
   - Deterministic, faction-aware

3. Death Siphon (passive heal):
   - When allied undead dies within radius 6, lich heals 2 HP
   - Hooked into death finalization path
   - Deterministic

4. Hang-back AI:
   - Prefers distance 4-7 from player
   - Inherits corpse economy patterns from NecromancerBase
   - Raises dead when off Soul Bolt cooldown + no corpses for Soul Bolt

Design: Lich combines necromancer corpse economy with strong personal threat.
"""

from typing import Optional, List, TYPE_CHECKING
from components.ai.necromancer_base import NecromancerBase
from components.component_registry import ComponentType
from logger_config import get_logger
import math

if TYPE_CHECKING:
    from entity import Entity

logger = get_logger(__name__)


class LichAI(NecromancerBase):
    """AI for Lich (Arch-Necromancer) with Soul Bolt + Command + Death Siphon.
    
    Priority:
    1. If Soul Bolt is charging (has ChargingSoulBoltEffect): Resolve Soul Bolt if able
    2. If Soul Bolt off cooldown + not charging: Start charge if player in range/LOS
    3. Maintain corpse economy: raise/explode per NecromancerBase system
    4. Keep safety constraint: don't move into danger radius
    """
    
    def __init__(self):
        """Initialize lich AI."""
        super().__init__()
        self.soul_bolt_cooldown_remaining = 0
        
        # Instrumentation for diagnosing Soul Bolt gating issues
        self.ticks_alive = 0
        self.ticks_player_in_range = 0
        self.ticks_has_los = 0
        self.ticks_eligible_to_charge = 0
        
        # Debug logging can be enabled if needed
        # logger.debug(f"[LICH] LichAI initialized for {getattr(self, 'owner', 'unknown')}")
    
    def take_turn(self, target, fov_map, game_map, entities):
        """Execute one turn of lich AI behavior.
        
        Args:
            target: The target entity (usually the player)
            fov_map: Field of view map
            game_map: Game map
            entities: List of all entities
            
        Returns:
            list: List of result dictionaries
        """
        results = []
        
        # Instrumentation: Track ticks alive
        self.ticks_alive += 1
        
        # Debug logging can be enabled if needed
        # if self.ticks_alive <= 3:
        #     logger.debug(f"[LICH TURN #{self.ticks_alive}] at ({self.owner.x},{self.owner.y})")
        
        # Instrumentation: Check eligibility conditions for Soul Bolt
        soul_bolt_range = getattr(self.owner, 'soul_bolt_range', 7)
        distance = self._distance_to(target)
        
        # Check LOS: Use player-centric FOV (if lich is visible to player, player is visible to lich)
        from components.ai._helpers import map_is_in_fov
        has_los = map_is_in_fov(fov_map, self.owner.x, self.owner.y) if fov_map else False
        
        if distance <= soul_bolt_range:
            self.ticks_player_in_range += 1
            self._increment_metric('lich_ticks_player_in_range')
        if has_los:
            self.ticks_has_los += 1
            self._increment_metric('lich_ticks_has_los')
        if distance <= soul_bolt_range and has_los and self.soul_bolt_cooldown_remaining <= 0:
            self.ticks_eligible_to_charge += 1
            self._increment_metric('lich_ticks_eligible_to_charge')
        
        # Always record ticks_alive each turn (for aggregation)
        self._increment_metric('lich_ticks_alive')
        
        # Decrement Soul Bolt cooldown at start of turn
        if self.soul_bolt_cooldown_remaining > 0:
            self.soul_bolt_cooldown_remaining -= 1
        
        # Check if charging Soul Bolt
        status_effects = self.owner.status_effects if hasattr(self.owner, 'status_effects') else None
        is_charging = status_effects and status_effects.has_effect('charging_soul_bolt')
        
        # Priority 1: If charging, try to resolve Soul Bolt
        if is_charging:
            resolve_results = self._try_resolve_soul_bolt(target, fov_map)
            if resolve_results:
                results.extend(resolve_results)
                # Soul Bolt consumed the turn - return early
                if status_effects:
                    end_results = status_effects.process_turn_end()
                    results.extend(end_results)
                return results
            else:
                # Charge expired without resolution (LOS broken, out of range, etc.)
                # Remove charge effect and continue to other actions
                status_effects.remove_effect('charging_soul_bolt')
        
        # Priority 2: If Soul Bolt off cooldown + not charging, start charge
        if self.soul_bolt_cooldown_remaining <= 0 and not is_charging:
            charge_results = self._try_start_soul_bolt_charge(target, fov_map)
            if charge_results:
                results.extend(charge_results)
                # Charging consumed the turn - return early
                if status_effects:
                    end_results = status_effects.process_turn_end()
                    results.extend(end_results)
                return results
        
        # Priority 3: Fallback to necromancer base behavior (raise dead, corpse seeking, hang-back)
        base_results = super().take_turn(target, fov_map, game_map, entities)
        results.extend(base_results)
        
        return results
    
    def _try_start_soul_bolt_charge(self, target, fov_map) -> Optional[List]:
        """Try to start charging Soul Bolt if player is in range/LOS.
        
        Args:
            target: The player entity
            fov_map: Field of view map
            
        Returns:
            List of results if charging started, None otherwise
        """
        from components.status_effects import ChargingSoulBoltEffect
        
        # Get Soul Bolt config
        soul_bolt_range = getattr(self.owner, 'soul_bolt_range', 7)
        
        # Check if player is in range
        distance = self._distance_to(target)
        if distance > soul_bolt_range:
            return None
        
        # Check if lich has LOS to player (mutual visibility via player's FOV)
        from components.ai._helpers import map_is_in_fov
        if not map_is_in_fov(fov_map, self.owner.x, self.owner.y):
            return None
        
        # Start charging
        results = []
        
        # Get or create status effect manager
        status_effects = self.owner.get_status_effect_manager()
        
        charge_effect = ChargingSoulBoltEffect(owner=self.owner)
        charge_results = status_effects.add_effect(charge_effect)
        results.extend(charge_results)
        
        # Record metric
        self._increment_metric('lich_soul_bolt_charges')
        
        logger.info(f"[LICH] {self.owner.name} starts charging Soul Bolt (target: {target.name})")
        
        return results
    
    def _try_resolve_soul_bolt(self, target, fov_map) -> Optional[List]:
        """Try to resolve Soul Bolt if player still in range/LOS.
        
        Args:
            target: The player entity
            fov_map: Field of view map
            
        Returns:
            List of results if Soul Bolt fired, None otherwise
        """
        from components.status_effects import SoulWardEffect, SoulBurnEffect
        from message_builder import MessageBuilder as MB
        
        # Get Soul Bolt config
        soul_bolt_range = getattr(self.owner, 'soul_bolt_range', 7)
        soul_bolt_pct = getattr(self.owner, 'soul_bolt_damage_pct', 0.35)
        soul_bolt_cooldown = getattr(self.owner, 'soul_bolt_cooldown_turns', 4)
        
        # Check if player is still in range
        distance = self._distance_to(target)
        if distance > soul_bolt_range:
            logger.debug(f"[LICH] Soul Bolt fizzles - target out of range (distance={distance:.1f})")
            return None
        
        # Check if lich still has LOS to player (mutual visibility via player's FOV)
        from components.ai._helpers import map_is_in_fov
        if not map_is_in_fov(fov_map, self.owner.x, self.owner.y):
            logger.debug(f"[LICH] Soul Bolt fizzles - LOS broken")
            return None
        
        results = []
        
        # Calculate base Soul Bolt damage (deterministic)
        target_fighter = target.get_component_optional(ComponentType.FIGHTER)
        if not target_fighter:
            logger.warning(f"[LICH] Soul Bolt target {target.name} has no Fighter component!")
            return None
        
        base_damage = math.ceil(soul_bolt_pct * target_fighter.max_hp)
        
        # Check for Soul Ward
        target_status = target.get_component_optional(ComponentType.STATUS_EFFECTS)
        has_soul_ward = target_status and target_status.has_effect('soul_ward')
        
        if has_soul_ward:
            # Soul Ward active: reduce damage by 70%, convert to DOT
            upfront_damage = math.ceil(base_damage * 0.30)  # 30% upfront
            prevented_damage = base_damage - upfront_damage
            
            results.append({'message': MB.combat(f"⚡ The {self.owner.name} unleashes a Soul Bolt!")})
            results.append({'message': MB.combat(f"🛡️ The Soul Ward absorbs most of the blast!")})
            
            # Apply upfront damage
            if upfront_damage > 0:
                # Use Fighter.take_damage() directly - caller will finalize death
                damage_results = target_fighter.take_damage(upfront_damage)
                results.extend(damage_results)
            
            # Apply Soul Burn DOT
            if prevented_damage > 0:
                soul_burn = SoulBurnEffect(total_damage=prevented_damage, owner=target)
                burn_results = target_status.add_effect(soul_burn)
                results.extend(burn_results)
            
            # Record metrics
            self._increment_metric('lich_soul_bolt_casts')
            self._increment_metric('soul_ward_blocks')
            
        else:
            # No ward: full damage
            results.append({'message': MB.combat(f"⚡💀 The {self.owner.name} unleashes a devastating Soul Bolt!")})
            
            # Use Fighter.take_damage() directly - caller will finalize death
            damage_results = target_fighter.take_damage(base_damage)
            results.extend(damage_results)
            
            # Record metrics
            self._increment_metric('lich_soul_bolt_casts')
        
        # Remove charging effect
        status_effects = self.owner.get_component_optional(ComponentType.STATUS_EFFECTS)
        if status_effects:
            status_effects.remove_effect('charging_soul_bolt')
        
        # Set cooldown
        self.soul_bolt_cooldown_remaining = soul_bolt_cooldown
        
        logger.info(f"[LICH] Soul Bolt resolved! Damage={base_damage}, Ward={has_soul_ward}, Cooldown={soul_bolt_cooldown}")
        
        return results
    
    def _try_execute_action(
        self,
        target,
        game_map,
        entities: List,
        action_range: int,
        action_cooldown: int
    ) -> Optional[List]:
        """Attempt to raise a corpse if one is in range (standard necromancer action).
        
        Lich can still raise dead like a regular necromancer when not using Soul Bolt.
        
        Args:
            target: The player entity
            game_map: Game map
            entities: List of all entities
            action_range: Maximum range for raising
            action_cooldown: Cooldown after successful raise
            
        Returns:
            List of results if raise attempted, None otherwise
        """
        from spells import cast_spell_by_id
        
        # Find best raisable corpse in range
        corpse = self._find_best_raisable_corpse(entities, max_range=action_range)
        
        if corpse is None:
            return None
        
        # Attempt to raise the corpse
        logger.debug(f"{self.owner.name} attempting to raise {corpse.name} at ({corpse.x}, {corpse.y})")
        
        # Record metric: raise attempt
        self._increment_metric('lich_raise_attempts')
        
        try:
            # Cast raise dead with raiser_faction override
            raiser_faction = getattr(self.owner, 'faction', None)
            summon_monster_id = getattr(self.owner, 'summon_monster_id', 'zombie')
            
            raise_results = cast_spell_by_id(
                spell_id='raise_dead',
                caster=self.owner,
                target_entity=corpse,
                game_map=game_map,
                entities=entities,
                raiser_faction=raiser_faction,
                summon_monster_id=summon_monster_id
            )
            
            if raise_results:
                # Set action cooldown
                self.action_cooldown_remaining = action_cooldown
                
                # Record success metric
                self._increment_metric('lich_raise_successes')
                
                logger.info(f"[LICH] Raise successful: {corpse.name} -> {summon_monster_id}")
                
                return raise_results
        except Exception as e:
            logger.error(f"[LICH] Raise failed: {e}")
        
        return None
    
    def _try_target_seeking_movement(
        self,
        target,
        game_map,
        entities: List,
        action_range: int,
        danger_radius: int
    ) -> Optional[List]:
        """Attempt to move toward a raisable corpse while respecting danger radius.
        
        Args:
            target: The player entity
            game_map: Game map
            entities: List of all entities
            action_range: Action range (to know if corpse is out of range)
            danger_radius: Never approach within this distance of player
            
        Returns:
            List of results if movement made, None otherwise
        """
        # Find best raisable corpse (regardless of range)
        corpse = self._find_best_raisable_corpse(entities, max_range=999)
        
        if corpse is None:
            return None
        
        # Check if corpse is out of action range
        distance_to_corpse = self._distance_to_position(corpse.x, corpse.y)
        if distance_to_corpse <= action_range:
            # Corpse is in range - don't move toward it
            return None
        
        # Try to approach corpse while maintaining danger radius from player
        return self._try_safe_target_approach(
            approach_target=corpse,
            player_target=target,
            game_map=game_map,
            entities=entities,
            danger_radius=danger_radius,
            metric_name="lich_corpse_seek_moves"
        )
    
    def _find_best_raisable_corpse(self, entities: List, max_range: int):
        """Find the nearest raisable corpse within range.
        
        Args:
            entities: List of all entities
            max_range: Maximum range to consider
            
        Returns:
            Best corpse entity, or None if no corpses in range
        """
        from components.corpse import CorpseComponent
        
        best_corpse = None
        best_distance = float('inf')
        
        for entity in entities:
            corpse_comp = entity.get_component_optional(ComponentType.CORPSE)
            if corpse_comp and corpse_comp.can_be_raised():
                distance = self._distance_to_position(entity.x, entity.y)
                if distance <= max_range:
                    # Deterministic tie-break: prefer lower (y, x)
                    if distance < best_distance or (distance == best_distance and (entity.y, entity.x) < (best_corpse.y, best_corpse.x)):
                        best_corpse = entity
                        best_distance = distance
        
        return best_corpse
    
    def report_diagnostics(self) -> None:
        """Report Soul Bolt diagnostic counters (called on lich death).
        
        This helps diagnose why Soul Bolt isn't firing in scenarios.
        """
        # Log diagnostics for debugging (can be disabled in production)
        logger.info(
            f"[LICH DIAGNOSTICS] {self.owner.name} death report:\n"
            f"  - Ticks alive: {self.ticks_alive}\n"
            f"  - Ticks player in range: {self.ticks_player_in_range}\n"
            f"  - Ticks had LOS: {self.ticks_has_los}\n"
            f"  - Ticks eligible: {self.ticks_eligible_to_charge}"
        )
        
        # Record to metrics for aggregation
        try:
            from services.scenario_metrics import get_active_metrics_collector
            metrics = get_active_metrics_collector()
            if metrics:
                metrics.increment('lich_ticks_alive', self.ticks_alive)
                metrics.increment('lich_ticks_player_in_range', self.ticks_player_in_range)
                metrics.increment('lich_ticks_has_los', self.ticks_has_los)
                metrics.increment('lich_ticks_eligible_to_charge', self.ticks_eligible_to_charge)
        except Exception:
            pass  # Metrics are optional

