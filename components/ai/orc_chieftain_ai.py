"""Phase 19: Orc Chieftain AI - Leader with Rally Cry and Sonic Bellow abilities

Orc Chieftain is a high-priority leader enemy with deterministic, scenario-backed behavior:
1. Rallying Cry (ONE-TIME, very impactful):
   - Applies to nearby ORC allies: +1 to-hit AND +1 damage
   - Cleanses fear-like / morale-debuff effects from those allies
   - Issues a "call to attack" directive: nearby orcs prioritize the chieftain's target
   - Rally persists UNTIL THE CHIEFTAIN IS DAMAGED (first time), then ends immediately for all rallied orcs

2. Sonic Bellow (personal shout, ONE-TIME):
   - When chieftain drops below 50% HP (first time only), apply to player: -1 to-hit for 2 turns
   - Deterministic, no RNG

3. Hang-back AI heuristic:
   - Chieftain prefers to "hang back" when other orcs can engage
   - Encourages tactical play (reach him via flanking/ranged/funneling)
"""

from typing import Optional, List, TYPE_CHECKING
from components.ai.basic_monster import BasicMonster
from logger_config import get_logger

if TYPE_CHECKING:
    from entity import Entity

logger = get_logger(__name__)


class OrcChieftainAI(BasicMonster):
    """AI for Orc Chieftain with Rally Cry, Sonic Bellow, and hang-back behavior.
    
    Phase 19: Chieftain is a leader enemy that:
    - Uses Rally Cry once when enough allies are nearby
    - Uses Sonic Bellow once when dropping below 50% HP
    - Hangs back when allies can engage the player
    """
    
    def __init__(self):
        """Initialize Orc Chieftain AI."""
        super().__init__()
        self.has_rallied = False  # Track if rally has been used (one-time)
        self.has_bellowed = False  # Track if bellow has been used (one-time)
        self.rally_active = False  # Track if rally is currently active
        self.rallied_orc_ids = []  # Track which orcs are rallied
    
    def take_turn(self, target, fov_map, game_map, entities):
        """Execute one turn of orc chieftain AI behavior.
        
        Overrides BasicMonster to add:
        1. Rally Cry trigger (once, at start of turn if enough allies)
        2. Sonic Bellow trigger (once, when HP < 50%)
        3. Hang-back heuristic (avoid leading charge if allies can engage)
        
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
        
        # Check for Sonic Bellow trigger (before other actions)
        bellow_results = self._check_sonic_bellow_trigger(target)
        if bellow_results:
            results.extend(bellow_results)
        
        # Check for Rally Cry trigger (at start of turn, before movement/attack)
        rally_results = self._check_rally_trigger(entities, target)
        if rally_results:
            results.extend(rally_results)
        
        # Check if we should hang back
        # Only hang back if:
        # 1. Not in immediate attack range
        # 2. Other orc allies can attack the player
        # 3. Not boxed in or forced to engage
        
        from components.ai._helpers import get_weapon_reach
        distance = self.owner.chebyshev_distance_to(target)
        weapon_reach = get_weapon_reach(self.owner)
        
        # If in attack range, use normal combat behavior
        if distance <= weapon_reach:
            combat_results = super().take_turn(target, fov_map, game_map, entities)
            results.extend(combat_results)
            return results
        
        # Try hang-back behavior
        hangback_results = self._try_hangback_movement(target, game_map, entities)
        if hangback_results is not None:
            # Hang-back movement succeeded - process status effects and return
            status_effects = self.owner.get_component_optional(ComponentType.STATUS_EFFECTS)
            if status_effects:
                end_results = status_effects.process_turn_end()
                results.extend(end_results)
            return results
        
        # Hang-back not applicable - use normal behavior
        combat_results = super().take_turn(target, fov_map, game_map, entities)
        results.extend(combat_results)
        return results
    
    def _check_rally_trigger(self, entities, target) -> List:
        """Check if Rally Cry should trigger.
        
        Rally triggers once when:
        - Not yet rallied
        - >= rally_min_allies orc allies within rally_radius
        
        Args:
            entities: List of all entities
            target: Target entity (player)
            
        Returns:
            list: Results if rally triggered, empty list otherwise
        """
        if self.has_rallied:
            return []
        
        # Get rally config from owner
        rally_radius = getattr(self.owner, 'rally_radius', 5)
        rally_min_allies = getattr(self.owner, 'rally_min_allies', 2)
        rally_hit_bonus = getattr(self.owner, 'rally_hit_bonus', 1)
        rally_damage_bonus = getattr(self.owner, 'rally_damage_bonus', 1)
        rally_cleanses_tags = getattr(self.owner, 'rally_cleanses_tags', ['fear', 'morale_debuff'])
        
        # Find orc allies within radius
        from components.component_registry import ComponentType
        orc_allies = []
        for entity in entities:
            if entity == self.owner:
                continue
            if not entity.components.has(ComponentType.FIGHTER):
                continue
            fighter = entity.fighter
            if fighter.hp <= 0:
                continue
            # Check if entity is an orc (has orc faction)
            faction_comp = entity.get_component_optional(ComponentType.FACTION)
            if faction_comp and faction_comp.faction_name == "orc":
                # Check distance (Chebyshev distance for rally radius)
                distance = max(abs(entity.x - self.owner.x), abs(entity.y - self.owner.y))
                if distance <= rally_radius:
                    orc_allies.append(entity)
        
        # Check if we have enough allies
        if len(orc_allies) < rally_min_allies:
            return []
        
        # Trigger rally!
        from components.status_effects import RallyBuffEffect
        from message_builder import MessageBuilder as MB
        
        results = []
        results.append({'message': MB.combat(f"The Orc Chieftain bellows a rallying cry!")})
        
        # Apply rally buff to each ally
        rallied_count = 0
        for ally in orc_allies:
            status_effects = ally.get_component_optional(ComponentType.STATUS_EFFECTS)
            if not status_effects:
                continue
            
            # Cleanse fear/morale debuffs first
            for tag in rally_cleanses_tags:
                if status_effects.has_effect(tag):
                    cleanse_results = status_effects.remove_effect(tag)
                    results.extend(cleanse_results)
            
            # Apply rally buff (infinite duration - ends when chieftain is damaged)
            rally_buff = RallyBuffEffect(
                duration=9999,  # Effectively infinite - ends when chieftain damaged
                owner=ally,
                chieftain_id=id(self.owner),
                to_hit_bonus=rally_hit_bonus,
                damage_bonus=rally_damage_bonus
            )
            rally_buff.directive_target_id = id(target)  # Set directive target
            
            buff_results = status_effects.add_effect(rally_buff)
            results.extend(buff_results)
            
            # Set AI directive
            if hasattr(ally, 'ai'):
                ally.ai.rally_directive_target_id = id(target)
            
            rallied_count += 1
            self.rallied_orc_ids.append(id(ally))
        
        # Mark rally as used and active
        self.has_rallied = True
        self.rally_active = True
        
        logger.info(f"[ORC CHIEFTAIN] Rally triggered! Rallied {rallied_count} orc allies.")
        
        return results
    
    def _check_sonic_bellow_trigger(self, target) -> List:
        """Check if Sonic Bellow should trigger.
        
        Bellow triggers once when:
        - Not yet bellowed
        - HP drops below 50% of max for the first time
        
        Args:
            target: Target entity (player)
            
        Returns:
            list: Results if bellow triggered, empty list otherwise
        """
        if self.has_bellowed:
            return []
        
        from components.component_registry import ComponentType
        fighter = self.owner.get_component_optional(ComponentType.FIGHTER)
        if not fighter:
            return []
        
        # Get bellow config from owner
        bellow_hp_threshold = getattr(self.owner, 'bellow_hp_threshold', 0.5)
        bellow_to_hit_penalty = getattr(self.owner, 'bellow_to_hit_penalty', 1)
        bellow_duration = getattr(self.owner, 'bellow_duration', 2)
        
        # Check if HP is below threshold
        hp_pct = fighter.hp / fighter.max_hp
        if hp_pct >= bellow_hp_threshold:
            return []
        
        # Trigger bellow!
        from components.status_effects import SonicBellowDebuffEffect
        from message_builder import MessageBuilder as MB
        
        results = []
        results.append({'message': MB.combat(f"The Orc Chieftain's bellow rings in your ears!")})
        
        # Apply debuff to player
        target_status_effects = target.get_component_optional(ComponentType.STATUS_EFFECTS)
        if target_status_effects:
            bellow_debuff = SonicBellowDebuffEffect(
                duration=bellow_duration,
                owner=target,
                to_hit_penalty=bellow_to_hit_penalty
            )
            debuff_results = target_status_effects.add_effect(bellow_debuff)
            results.extend(debuff_results)
        
        # Mark bellow as used
        self.has_bellowed = True
        
        logger.info(f"[ORC CHIEFTAIN] Sonic Bellow triggered! HP: {fighter.hp}/{fighter.max_hp}")
        
        return results
    
    def _try_hangback_movement(self, target, game_map, entities) -> Optional[List]:
        """Try to hang back when allies can engage.
        
        Chieftain prefers to avoid becoming adjacent to the player when:
        - Any non-chieftain orc ally currently has an attack available on the player
        - Multiple moves are plausible
        
        If chieftain is boxed in or already adjacent and cannot move away, attacks normally.
        
        Args:
            target: Target entity (player)
            game_map: Game map
            entities: List of all entities
            
        Returns:
            list: Results if hang-back movement taken, None if should use normal movement
        """
        from components.component_registry import ComponentType
        from components.ai._helpers import get_weapon_reach
        
        # Check if any orc ally can attack the player
        ally_can_attack = False
        for entity in entities:
            if entity == self.owner:
                continue
            if not entity.components.has(ComponentType.FIGHTER):
                continue
            fighter = entity.fighter
            if fighter.hp <= 0:
                continue
            # Check if entity is an orc (has orc faction)
            faction_comp = entity.get_component_optional(ComponentType.FACTION)
            if faction_comp and faction_comp.faction_name == "orc":
                # Check if ally can attack player
                weapon_reach = get_weapon_reach(entity)
                distance = max(abs(entity.x - target.x), abs(entity.y - target.y))
                if distance <= weapon_reach:
                    ally_can_attack = True
                    break
        
        if not ally_can_attack:
            # No allies can engage - chieftain should engage normally
            return None
        
        # Allies can engage - try to maintain distance 2-4 from player
        from components.monster_action_logger import MonsterActionLogger
        
        results = []
        
        # Calculate current distance to player
        current_distance = max(abs(self.owner.x - target.x), abs(self.owner.y - target.y))
        
        # If already at good distance (2-4), stay put or move laterally
        if 2 <= current_distance <= 4:
            # Try to find a lateral move that maintains distance
            best_move = self._find_lateral_move(target, game_map, entities)
            if best_move:
                dx, dy = best_move
                self.owner.move(dx, dy)
                MonsterActionLogger.log_turn_summary(self.owner, ["hangback_lateral"])
                logger.debug(f"[ORC CHIEFTAIN] Hanging back (lateral move)")
                return results
            # No lateral move available - stay put
            MonsterActionLogger.log_turn_summary(self.owner, ["hangback_stay"])
            return results
        
        # If too close (distance 1), try to move away
        if current_distance == 1:
            # Try to move away from player
            away_move = self._find_move_away(target, game_map, entities)
            if away_move:
                dx, dy = away_move
                self.owner.move(dx, dy)
                MonsterActionLogger.log_turn_summary(self.owner, ["hangback_retreat"])
                logger.debug(f"[ORC CHIEFTAIN] Hanging back (retreat)")
                return results
            # Boxed in - use normal combat behavior
            return None
        
        # If too far (distance > 4), move closer but not adjacent
        # Use normal pathfinding but stop at distance 2-4
        # For now, just use normal pathfinding (this is edge case)
        return None
    
    def _find_lateral_move(self, target, game_map, entities) -> Optional[tuple]:
        """Find a lateral move that maintains distance from target.
        
        Args:
            target: Target entity
            game_map: Game map
            entities: List of all entities
            
        Returns:
            tuple: (dx, dy) if found, None otherwise
        """
        current_distance = max(abs(self.owner.x - target.x), abs(self.owner.y - target.y))
        
        # Try all 8 directions
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            new_x = self.owner.x + dx
            new_y = self.owner.y + dy
            
            # Check if move is valid
            if not game_map.walkable[new_x, new_y]:
                continue
            if game_map.blocked[new_x, new_y]:
                continue
            
            # Check if any entity blocks this tile
            blocking_entity = None
            for entity in entities:
                if entity.blocks and entity.x == new_x and entity.y == new_y:
                    blocking_entity = entity
                    break
            if blocking_entity:
                continue
            
            # Check new distance
            new_distance = max(abs(new_x - target.x), abs(new_y - target.y))
            
            # Accept if distance stays in range 2-4
            if 2 <= new_distance <= 4:
                return (dx, dy)
        
        return None
    
    def _find_move_away(self, target, game_map, entities) -> Optional[tuple]:
        """Find a move that increases distance from target.
        
        Args:
            target: Target entity
            game_map: Game map
            entities: List of all entities
            
        Returns:
            tuple: (dx, dy) if found, None otherwise
        """
        current_distance = max(abs(self.owner.x - target.x), abs(self.owner.y - target.y))
        
        best_move = None
        best_distance = current_distance
        
        # Try all 8 directions
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            new_x = self.owner.x + dx
            new_y = self.owner.y + dy
            
            # Check if move is valid
            if not game_map.walkable[new_x, new_y]:
                continue
            if game_map.blocked[new_x, new_y]:
                continue
            
            # Check if any entity blocks this tile
            blocking_entity = None
            for entity in entities:
                if entity.blocks and entity.x == new_x and entity.y == new_y:
                    blocking_entity = entity
                    break
            if blocking_entity:
                continue
            
            # Check new distance
            new_distance = max(abs(new_x - target.x), abs(new_y - target.y))
            
            # Keep track of move that increases distance most
            if new_distance > best_distance:
                best_distance = new_distance
                best_move = (dx, dy)
        
        return best_move




