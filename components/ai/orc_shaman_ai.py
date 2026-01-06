"""Phase 19: Orc Shaman AI - Battlefield controller with hex + channeled chant

Orc Shaman is a hang-back support enemy with deterministic, cooldown-based abilities:
1. Crippling Hex (cooldown-based debuff):
   - Applies to player: -1 to-hit AND -1 AC
   - Range: config-driven (default 6)
   - Duration: config-driven (default 5 turns)
   - Cooldown: config-driven (default 10 turns)
   - Deterministic, no RNG

2. Chant of Dissonance (channeled movement tax, interruptible):
   - Applies to player: +1 energy cost per movement (costs 2 turns instead of 1)
   - Range: config-driven (default 5)
   - Duration: config-driven (default 3 turns, while channeling)
   - Cooldown: config-driven (default 15 turns)
   - Channeled: Shaman must maintain chant (sets is_channeling=True)
   - Interruptible: Any damage to shaman ends chant immediately
   - Deterministic, no RNG

3. Hang-back AI heuristic:
   - Shaman prefers distance 4-7 from player
   - If too close (<=2), retreats if possible
   - If allies can engage, hangs back and casts abilities
   - If no retreat possible, attacks (no stall)
"""

from typing import Optional, List, TYPE_CHECKING
from components.ai.basic_monster import BasicMonster
from logger_config import get_logger

if TYPE_CHECKING:
    from entity import Entity

logger = get_logger(__name__)


class OrcShamanAI(BasicMonster):
    """AI for Orc Shaman with Crippling Hex, Chant of Dissonance, and hang-back behavior.
    
    Phase 19: Shaman is a controller enemy that:
    - Uses Crippling Hex on cooldown when in range
    - Uses Chant of Dissonance (channeled) on cooldown when in range
    - Hangs back when allies can engage the player
    - Avoids melee combat (weak stats, prefers abilities)
    """
    
    def __init__(self):
        """Initialize Orc Shaman AI."""
        super().__init__()
        # Cooldown tracking (turns remaining until ability is ready)
        self.hex_cooldown_remaining = 0
        self.chant_cooldown_remaining = 0
        # Channeling state
        self.is_channeling = False  # True while chanting
        self.chant_target_id = None  # ID of player being chanted
        self.chant_turns_remaining = 0  # Turns left on current chant channel
    
    def take_turn(self, target, fov_map, game_map, entities):
        """Execute one turn of orc shaman AI behavior.
        
        Overrides BasicMonster to add:
        1. Crippling Hex trigger (cooldown-based)
        2. Chant of Dissonance trigger (cooldown-based, channeled)
        3. Hang-back heuristic (maintain distance 4-7)
        
        Priority:
        1. If channeling, continue channeling (no other action)
        2. If player within chant range AND chant off cooldown: Start chant
        3. Else if player within hex range AND hex off cooldown: Cast hex
        4. Else hang back or attack if forced
        
        Args:
            target: The target entity (usually the player)
            fov_map: Field of view map
            game_map: Game map
            entities: List of all entities
            
        Returns:
            list: List of result dictionaries
        """
        from components.component_registry import ComponentType
        
        results = []
        
        # Decrement cooldowns at start of turn
        if self.hex_cooldown_remaining > 0:
            self.hex_cooldown_remaining -= 1
        if self.chant_cooldown_remaining > 0:
            self.chant_cooldown_remaining -= 1
        
        # Check if we're channeling
        if self.is_channeling:
            # Continue channeling
            channel_results = self._continue_channeling(target)
            results.extend(channel_results)
            # Channeling consumes the turn - return early
            status_effects = self.owner.get_component_optional(ComponentType.STATUS_EFFECTS)
            if status_effects:
                end_results = status_effects.process_turn_end()
                results.extend(end_results)
            return results
        
        # Calculate distance to player
        from components.ai._helpers import get_weapon_reach
        distance = self.owner.chebyshev_distance_to(target)
        weapon_reach = get_weapon_reach(self.owner)
        
        # Ability priority: Chant > Hex > Movement/Attack
        
        # Try to start chant (if off cooldown and in range)
        chant_started = self._try_start_chant(target, distance)
        if chant_started:
            results.extend(chant_started)
            # Chant started - channeling consumes the turn
            status_effects = self.owner.get_component_optional(ComponentType.STATUS_EFFECTS)
            if status_effects:
                end_results = status_effects.process_turn_end()
                results.extend(end_results)
            return results
        
        # Try to cast hex (if off cooldown and in range)
        hex_cast = self._try_cast_hex(target, distance)
        if hex_cast:
            results.extend(hex_cast)
            # Hex cast consumes the turn
            status_effects = self.owner.get_component_optional(ComponentType.STATUS_EFFECTS)
            if status_effects:
                end_results = status_effects.process_turn_end()
                results.extend(end_results)
            return results
        
        # No abilities available - use positioning behavior
        # If in melee range, use normal combat behavior
        if distance <= weapon_reach:
            combat_results = super().take_turn(target, fov_map, game_map, entities)
            results.extend(combat_results)
            return results
        
        # Try hang-back behavior (maintain distance 4-7)
        hangback_results = self._try_hangback_movement(target, game_map, entities, preferred_min=4, preferred_max=7)
        if hangback_results is not None:
            # Hang-back movement succeeded - process status effects and return
            status_effects = self.owner.get_component_optional(ComponentType.STATUS_EFFECTS)
            if status_effects:
                end_results = status_effects.process_turn_end()
                results.extend(end_results)
            return results
        
        # Hang-back not applicable - use normal behavior (move toward or attack)
        combat_results = super().take_turn(target, fov_map, game_map, entities)
        results.extend(combat_results)
        return results
    
    def _try_cast_hex(self, target, distance: int) -> Optional[List]:
        """Try to cast Crippling Hex on the target.
        
        Args:
            target: Target entity (player)
            distance: Chebyshev distance to target
            
        Returns:
            list of results if hex was cast, None otherwise
        """
        from components.component_registry import ComponentType
        from message_builder import MessageBuilder as MB
        
        # Phase 20F: Canonical silence gating at execution point
        from components.status_effects import check_and_gate_silenced_cast
        blocked = check_and_gate_silenced_cast(self.owner, "cast a hex")
        if blocked:
            return blocked
        
        # Check if hex is enabled and available
        # Config is stored directly on entity (not in monster_def)
        hex_enabled = getattr(self.owner, 'hex_enabled', False)
        if not hex_enabled:
            return None
        
        # Check if hex is off cooldown
        if self.hex_cooldown_remaining > 0:
            return None
        
        # Check if target is in range
        hex_radius = getattr(self.owner, 'hex_radius', 6)
        if distance > hex_radius:
            return None
        
        # Check if target already has hex (don't stack, but can refresh)
        target_status = target.get_component_optional(ComponentType.STATUS_EFFECTS)
        if not target_status:
            return None  # Target can't have status effects applied
        
        # Cast hex!
        results = []
        hex_duration = getattr(self.owner, 'hex_duration_turns', 5)
        hex_to_hit_delta = getattr(self.owner, 'hex_to_hit_delta', -1)
        hex_ac_delta = getattr(self.owner, 'hex_ac_delta', -1)
        
        # Import here to avoid circular dependency
        from components.status_effects import CripplingHexEffect
        hex_effect = CripplingHexEffect(
            duration=hex_duration,
            owner=target,
            to_hit_delta=hex_to_hit_delta,
            ac_delta=hex_ac_delta
        )
        
        apply_results = target_status.add_effect(hex_effect)
        results.extend(apply_results)
        
        # Shaman message
        results.append({
            'message': MB.combat(f"{self.owner.name} casts a crippling hex on {target.name}!")
        })
        
        # Set cooldown
        hex_cooldown = getattr(self.owner, 'hex_cooldown_turns', 10)
        self.hex_cooldown_remaining = hex_cooldown
        
        logger.info(f"Orc Shaman cast Crippling Hex on {target.name}, cooldown={hex_cooldown}")
        
        # Record metric
        try:
            from services.scenario_metrics import get_active_metrics_collector
            metrics = get_active_metrics_collector()
            if metrics:
                metrics.increment('shaman_hex_casts')
        except Exception:
            pass
        
        return results
    
    def _try_start_chant(self, target, distance: int) -> Optional[List]:
        """Try to start Chant of Dissonance (channeled ability).
        
        Args:
            target: Target entity (player)
            distance: Chebyshev distance to target
            
        Returns:
            list of results if chant was started, None otherwise
        """
        from components.component_registry import ComponentType
        from message_builder import MessageBuilder as MB
        
        # Phase 20F: Canonical silence gating at execution point
        from components.status_effects import check_and_gate_silenced_cast
        blocked = check_and_gate_silenced_cast(self.owner, "begin a chant")
        if blocked:
            return blocked
        
        # Check if chant is enabled and available
        # Config is stored directly on entity (not in monster_def)
        chant_enabled = getattr(self.owner, 'chant_enabled', False)
        if not chant_enabled:
            return None
        
        # Check if chant is off cooldown
        if self.chant_cooldown_remaining > 0:
            return None
        
        # Check if already channeling (shouldn't happen, but defensive)
        if self.is_channeling:
            return None
        
        # Check if target is in range
        chant_radius = getattr(self.owner, 'chant_radius', 5)
        if distance > chant_radius:
            return None
        
        # Check if target can have status effects
        target_status = target.get_component_optional(ComponentType.STATUS_EFFECTS)
        if not target_status:
            return None
        
        # Start chanting!
        results = []
        chant_duration = getattr(self.owner, 'chant_duration_turns', 3)
        chant_move_energy_tax = getattr(self.owner, 'chant_move_energy_tax', 1)
        
        # Import here to avoid circular dependency
        from components.status_effects import DissonantChantEffect
        chant_effect = DissonantChantEffect(
            duration=chant_duration,
            owner=target,
            move_energy_tax=chant_move_energy_tax
        )
        
        apply_results = target_status.add_effect(chant_effect)
        results.extend(apply_results)
        
        # Shaman message
        results.append({
            'message': MB.combat(f"{self.owner.name} begins chanting a dissonant melody!")
        })
        
        # Enter channeling state
        self.is_channeling = True
        self.chant_target_id = id(target)
        self.chant_turns_remaining = chant_duration
        
        logger.info(f"Orc Shaman started Chant of Dissonance on {target.name}, duration={chant_duration}")
        
        # Record metric
        try:
            from services.scenario_metrics import get_active_metrics_collector
            metrics = get_active_metrics_collector()
            if metrics:
                metrics.increment('shaman_chant_starts')
        except Exception:
            pass
        
        return results
    
    def _continue_channeling(self, target) -> List:
        """Continue channeling Chant of Dissonance.
        
        Called each turn while channeling. Decrements chant duration.
        If chant expires naturally, ends channeling and sets cooldown.
        
        Args:
            target: Target entity (player)
            
        Returns:
            list of results
        """
        from components.component_registry import ComponentType
        from message_builder import MessageBuilder as MB
        
        results = []
        
        # Decrement chant duration
        self.chant_turns_remaining -= 1
        
        # Check if chant expired naturally
        if self.chant_turns_remaining <= 0:
            # Chant ends naturally
            results.append({
                'message': MB.info(f"{self.owner.name}'s chant fades away...")
            })
            
            # End channeling
            self.is_channeling = False
            self.chant_target_id = None
            
            # Set cooldown
            chant_cooldown = getattr(self.owner, 'chant_cooldown_turns', 15)
            self.chant_cooldown_remaining = chant_cooldown
            
            logger.info(f"Orc Shaman's chant expired naturally")
            
            # Record metric
            try:
                from services.scenario_metrics import get_active_metrics_collector
                metrics = get_active_metrics_collector()
                if metrics:
                    metrics.increment('shaman_chant_expiries')
            except Exception:
                pass
        
        # Note: If interrupted by damage, is_channeling will be set to False by take_damage()
        # and interrupt metric will be recorded there
        
        return results
    
    def _try_hangback_movement(self, target, game_map, entities, preferred_min: int = 4, preferred_max: int = 7) -> Optional[List]:
        """Try to maintain preferred distance from target.
        
        Shaman prefers to stay at distance 4-7 from player:
        - If too close (< preferred_min), try to move away
        - If too far (> preferred_max), move closer
        - If at good distance, stay put or move laterally
        
        Args:
            target: Target entity (player)
            game_map: Game map
            entities: List of all entities
            preferred_min: Minimum preferred distance
            preferred_max: Maximum preferred distance
            
        Returns:
            list of results if movement succeeded, None if hang-back not applicable
        """
        from components.component_registry import ComponentType
        
        distance = self.owner.chebyshev_distance_to(target)
        
        # If at preferred distance, stay put (hang back succeeded - no action needed)
        if preferred_min <= distance <= preferred_max:
            return []  # Empty results = hang-back succeeded, no movement
        
        # If too close, try to retreat
        if distance < preferred_min:
            # Try to move away from player
            dx_away = self.owner.x - target.x
            dy_away = self.owner.y - target.y
            
            # Normalize to get direction (-1, 0, 1)
            import math
            dist = math.sqrt(dx_away**2 + dy_away**2)
            if dist > 0:
                dx_away = int(round(dx_away / dist))
                dy_away = int(round(dy_away / dist))
            else:
                # Same tile? This shouldn't happen, but just move randomly
                dx_away, dy_away = 1, 0
            
            # Check if can move away
            new_x = self.owner.x + dx_away
            new_y = self.owner.y + dy_away
            
            from entity import get_blocking_entities_at_location
            if (not game_map.is_blocked(new_x, new_y) and
                not get_blocking_entities_at_location(entities, new_x, new_y)):
                # Move away
                self.owner.move(dx_away, dy_away)
                logger.debug(f"Shaman retreat: moved away from {target.name} to ({new_x}, {new_y})")
                return []  # Hang-back movement succeeded
        
        # If too far, move closer (but don't use hang-back for closing - use normal AI)
        # Hang-back is for AVOIDING combat, not engaging
        if distance > preferred_max:
            return None  # Too far - use normal AI to close distance
        
        # Boxed in or can't retreat - return None to use normal AI
        return None

