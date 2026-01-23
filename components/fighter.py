import random
from enum import Enum, auto
from typing import Optional, Dict, Any, List
from game_messages import Message
from message_builder import MessageBuilder as MB
from config.testing_config import is_testing_mode
from visual_effects import show_hit, show_miss
from components.component_registry import ComponentType


def _get_metrics_collector():
    try:
        from services.scenario_metrics import get_active_metrics_collector
        return get_active_metrics_collector()
    except Exception:
        return None
from logger_config import get_logger

# Module-specific loggers (using centralized system)
logger = get_logger(__name__)
combat_logger = get_logger('combat_debug')
resistance_logger = get_logger('resistance_debug')

# Log that resistance system is active (on startup)
if is_testing_mode():
    import logging as _logging
    resistance_logger.setLevel(_logging.INFO)
    if not resistance_logger.handlers:
        console_handler = _logging.StreamHandler()
        console_handler.setLevel(_logging.INFO)
        formatter = _logging.Formatter('%(message)s')
        console_handler.setFormatter(formatter)
        resistance_logger.addHandler(console_handler)
        resistance_logger.info("=" * 60)
        resistance_logger.info("🛡️ RESISTANCE SYSTEM ACTIVE - Logging enabled")
    resistance_logger.info("   Watch for resistance messages when damage is dealt")
    resistance_logger.info("=" * 60)


class ResistanceType(Enum):
    """Types of damage resistance."""
    FIRE = auto()
    COLD = auto()
    POISON = auto()
    LIGHTNING = auto()
    ACID = auto()
    PHYSICAL = auto()  # For future use


def normalize_resistance_type(damage_type: Any) -> Optional[ResistanceType]:
    """Convert string or ResistanceType to ResistanceType enum.
    
    Args:
        damage_type: String ('fire', 'cold', etc.) or ResistanceType enum
    
    Returns:
        ResistanceType enum or None if unknown
    """
    if isinstance(damage_type, ResistanceType):
        return damage_type
    
    if isinstance(damage_type, str):
        # Map string names to ResistanceType
        type_map = {
            'fire': ResistanceType.FIRE,
            'cold': ResistanceType.COLD,
            'ice': ResistanceType.COLD,  # Alias
            'poison': ResistanceType.POISON,
            'lightning': ResistanceType.LIGHTNING,
            'electric': ResistanceType.LIGHTNING,  # Alias
            'acid': ResistanceType.ACID,
            'physical': ResistanceType.PHYSICAL
        }
        return type_map.get(damage_type.lower())
    
    return None


class Fighter:
    """Component that handles combat statistics and actions.

    This component manages health points, attack power, defense, and experience
    points for entities that can engage in combat. It also handles equipment
    bonuses that modify base stats.

    New D&D-style stat system:
    - STR (Strength): Affects melee damage
    - DEX (Dexterity): Affects to-hit and AC (armor class)
    - CON (Constitution): Affects HP

    Attributes:
        base_max_hp (int): Base maximum health points
        hp (int): Current health points
        base_defense (int): Base defense value (legacy, will be replaced by AC)
        base_power (int): Base attack power (legacy, will be replaced by STR)
        strength (int): Strength stat (8-18)
        dexterity (int): Dexterity stat (8-18)
        constitution (int): Constitution stat (8-18)
        xp (int): Experience points earned
        owner (Entity): The entity that owns this component
    """

    def __init__(self, hp, defense, power, xp=0, damage_min=0, damage_max=0, 
                 strength=10, dexterity=10, constitution=10, resistances=None,
                 accuracy=None, evasion=None):
        """Initialize a Fighter component.

        Args:
            hp (int): Maximum health points
            defense (int): Defense value (legacy)
            power (int): Attack power (legacy)
            xp (int, optional): Starting experience points. Defaults to 0.
            damage_min (int, optional): Minimum base damage (fists/natural attacks). Defaults to 0.
            damage_max (int, optional): Maximum base damage (fists/natural attacks). Defaults to 0.
            strength (int, optional): Strength stat (8-18). Defaults to 10.
            dexterity (int, optional): Dexterity stat (8-18). Defaults to 10.
            constitution (int, optional): Constitution stat (8-18). Defaults to 10.
            resistances (dict, optional): Dict mapping ResistanceType to percentage (0-100). Defaults to None.
            accuracy (int, optional): Accuracy stat for hit chance. Defaults to 2.
            evasion (int, optional): Evasion stat for dodge chance. Defaults to 1.
        """
        self.base_max_hp = hp
        self.hp = hp
        self.base_defense = defense
        self.base_power = power
        self.xp = xp
        self.damage_min = damage_min
        self.damage_max = damage_max
        
        # D&D-style stats
        self.strength = strength
        self.dexterity = dexterity
        self.constitution = constitution
        
        # Phase 8: Accuracy and Evasion stats
        # These control hit/miss probability independent of damage
        # Defaults from balance/hit_model.py: accuracy=2, evasion=1
        from balance.hit_model import DEFAULT_ACCURACY, DEFAULT_EVASION
        self.accuracy = accuracy if accuracy is not None else DEFAULT_ACCURACY
        self.evasion = evasion if evasion is not None else DEFAULT_EVASION
        
        # Resistance system: Maps ResistanceType enum to percentage (0-100)
        # 0 = no resistance, 50 = half damage, 100 = immune
        self.base_resistances = resistances if resistances else {}
        
        self.owner = None  # Will be set by Entity when component is registered

    @staticmethod
    def get_stat_modifier(stat):
        """Calculate D&D-style stat modifier.
        
        Formula: (stat - 10) // 2
        Examples:
            8-9   → -1
            10-11 → 0
            12-13 → +1
            14-15 → +2
            16-17 → +3
            18    → +4
        
        Args:
            stat (int): The ability score (typically 3-18)
            
        Returns:
            int: The stat modifier (-4 to +4 typically)
        """
        return (stat - 10) // 2
    
    @property
    def strength_mod(self):
        """Get strength modifier including ring bonuses.
        
        Returns:
            int: Strength modifier (including Ring of Strength bonus)
        """
        base_str = self.strength
        
        # Add ring bonuses
        equipment = self._get_equipment(self.owner)
        if equipment:
            for ring in [equipment.left_ring, equipment.right_ring]:
                if ring and ring.components.has(ComponentType.RING):
                    base_str += ring.ring.get_stat_bonus('strength')
        
        return self.get_stat_modifier(base_str)
    
    @property
    def dexterity_mod(self):
        """Get dexterity modifier including ring bonuses.
        
        Returns:
            int: Dexterity modifier (including Ring of Dexterity bonus)
        """
        base_dex = self.dexterity
        
        # Add ring bonuses
        equipment = self._get_equipment(self.owner)
        if equipment:
            for ring in [equipment.left_ring, equipment.right_ring]:
                if ring and ring.components.has(ComponentType.RING):
                    base_dex += ring.ring.get_stat_bonus('dexterity')
        
        return self.get_stat_modifier(base_dex)
    
    @property
    def constitution_mod(self):
        """Get constitution modifier including ring bonuses.
        
        Returns:
            int: Constitution modifier (including Ring of Constitution bonus)
        """
        base_con = self.constitution
        
        # Add ring bonuses
        equipment = self._get_equipment(self.owner)
        if equipment:
            for ring in [equipment.left_ring, equipment.right_ring]:
                if ring and ring.components.has(ComponentType.RING):
                    base_con += ring.ring.get_stat_bonus('constitution')
        
        return self.get_stat_modifier(base_con)
    
    def get_resistance(self, resistance_type):
        """Get total resistance percentage for a damage type.
        
        Combines base resistances with equipment bonuses.
        
        Args:
            resistance_type (ResistanceType): Type of resistance to check
            
        Returns:
            int: Resistance percentage (0-100). 0 = no resistance, 50 = half damage, 100 = immune
        """
        # Normalize the resistance type (handle both string and enum)
        normalized_type = normalize_resistance_type(resistance_type)
        if not normalized_type:
            return 0
        
        # Start with base resistance - check both enum and string keys for backward compat
        total_resistance = self.base_resistances.get(normalized_type, 0)
        if total_resistance == 0:
            # Try string key (from YAML configs)
            total_resistance = self.base_resistances.get(resistance_type if isinstance(resistance_type, str) else normalized_type.name.lower(), 0)
        
        # Add equipment resistances (use Equipment's aggregation method)
        equipment = self._get_equipment(self.owner)
        if equipment and hasattr(equipment, 'get_resistance_bonus'):
            total_resistance += equipment.get_resistance_bonus(normalized_type)
        
        # Cap at 100% (immune)
        return min(total_resistance, 100)
    
    def apply_resistance(self, damage, damage_type):
        """Apply resistance to reduce damage.
        
        Args:
            damage (int): Base damage amount
            damage_type (str or ResistanceType): Type of damage (e.g., "fire", "cold", etc.)
            
        Returns:
            tuple: (reduced_damage, resistance_pct) - The damage after resistance and the resistance %
        """
        # Convert string damage type to ResistanceType enum
        if isinstance(damage_type, str):
            damage_type_lower = damage_type.lower()
            type_mapping = {
                'fire': ResistanceType.FIRE,
                'cold': ResistanceType.COLD,
                'poison': ResistanceType.POISON,
                'lightning': ResistanceType.LIGHTNING,
                'electric': ResistanceType.LIGHTNING,  # Alias
                'acid': ResistanceType.ACID,
                'physical': ResistanceType.PHYSICAL
            }
            resistance_type = type_mapping.get(damage_type_lower)
            if not resistance_type:
                # Unknown damage type - no resistance applies
                logger.debug(f"Unknown damage type '{damage_type}' - no resistance applies")
                return damage, 0
        else:
            resistance_type = damage_type
        
        # Get resistance percentage
        resistance_pct = self.get_resistance(resistance_type)
        
        # Log resistance calculation (visible in test mode)
        entity_name = self.owner.name if self.owner else "Unknown"
        damage_type_name = resistance_type.name.lower() if hasattr(resistance_type, 'name') else str(damage_type)
        
        if resistance_pct <= 0:
            # No resistance
            logger.debug(f"{entity_name}: No resistance to {damage_type_name} damage ({damage} damage)")
            return damage, 0
        
        # Calculate reduced damage
        # resistance_pct is 0-100, where 100 = immune (0 damage)
        reduction_multiplier = (100 - resistance_pct) / 100.0
        reduced_damage = int(damage * reduction_multiplier)
        
        # Log the resistance application (visible in console)
        if resistance_pct >= 100:
            resistance_logger.info(f"🛡️ RESISTANCE: {entity_name} is IMMUNE to {damage_type_name} ({resistance_pct}% resistance) - {damage} damage → 0")
        elif reduced_damage < damage:
            resistance_logger.info(f"🛡️ RESISTANCE: {entity_name} resists {damage_type_name} ({resistance_pct}% resistance) - {damage} damage → {reduced_damage}")
        
        return reduced_damage, resistance_pct
    
    def _get_equipment(self, entity):
        """Get equipment component from entity, with backward compatibility.
        
        Args:
            entity: The entity to get equipment from
            
        Returns:
            Equipment component or None
        """
        if not entity:
            return None
        
        # Use new component access helper for real Entity objects
        # Equipment is optional (not all entities have equipment)
        # Note: Mock objects also pass hasattr/callable checks, so check for Entity type
        from entity import Entity
        if isinstance(entity, Entity):
            result = entity.get_component_optional(ComponentType.EQUIPMENT)
            # FALLBACK: If component system returns None but direct attribute exists, use it
            # This provides backward compatibility with tests that assign equipment directly
            # without using the component registration system
            if result is None and hasattr(entity, 'equipment'):
                result = entity.equipment
            return result
        
        # Fall back to direct attribute access (for Mock objects in tests)
        return getattr(entity, 'equipment', None)
    
    @property
    def armor_class(self):
        """Calculate Armor Class (AC) for d20 combat system with DEX caps.
        
        AC = 10 + capped DEX modifier + armor AC bonus from all equipped items + shield wall bonus
        
        DEX Modifier Capping:
        - Light Armor: No cap (full DEX bonus)
        - Medium Armor: Cap at +2 DEX
        - Heavy Armor: Cap at 0 DEX (no DEX bonus!)
        - Multiple armor pieces: Use the MOST RESTRICTIVE cap
        
        Phase 19 Shield Wall:
        - Skeletons gain +1 AC per adjacent skeleton ally (4-way adjacency)
        - NO CAP on shield wall bonus
        
        Example:
            DEX 18 (+4), wearing Plate Mail (heavy, dex_cap=0):
            AC = 10 + 0 (capped) + 6 (plate) = 16
            
            DEX 18 (+4), wearing Studded Leather (light, no cap):
            AC = 10 + 4 (full) + 3 (studded) = 17
            
            Skeleton with 3 adjacent skeleton allies:
            AC = 10 + 1 (DEX) + 0 (no armor) + 3 (shield wall) = 14
        
        Returns:
            int: Armor Class (typically 10-25)
        """
        base_ac = 10
        dex_bonus = self.dexterity_mod
        
        # Get armor AC bonus and determine DEX cap from ALL equipped items
        armor_ac_bonus = 0
        most_restrictive_dex_cap = None  # None = no cap
        
        equipment = self._get_equipment(self.owner)
        if equipment:
            for item in [equipment.main_hand, equipment.off_hand, 
                        equipment.head, equipment.chest, equipment.feet]:
                # Check ComponentRegistry first, fallback to direct attribute for backward compatibility
                if item and (item.components.has(ComponentType.EQUIPPABLE) or hasattr(item, 'equippable')):
                    equippable = item.equippable
                    
                    # Add AC bonus
                    armor_ac_bonus += getattr(equippable, 'armor_class_bonus', 0)
                    
                    # Check for DEX cap (only for armor, not weapons/shields)
                    armor_type = getattr(equippable, 'armor_type', None)
                    item_dex_cap = getattr(equippable, 'dex_cap', None)
                    
                    # Apply DEX cap if this is armor (not weapon or shield)
                    if armor_type in ['light', 'medium', 'heavy'] and item_dex_cap is not None:
                        # Use the most restrictive (lowest) cap
                        if most_restrictive_dex_cap is None:
                            most_restrictive_dex_cap = item_dex_cap
                        else:
                            most_restrictive_dex_cap = min(most_restrictive_dex_cap, item_dex_cap)
        
        # Apply DEX cap if we found one
        if most_restrictive_dex_cap is not None:
            dex_bonus = min(dex_bonus, most_restrictive_dex_cap)
        
        # Apply status effect bonuses/penalties
        status_ac_bonus = 0
        if hasattr(self.owner, 'status_effects') and self.owner.status_effects is not None:
            # Protection: +ac_bonus to AC
            protection = self.owner.status_effects.get_effect('protection')
            if protection:
                status_ac_bonus += protection.ac_bonus
            
            # Phase 19: Crippling Hex: -AC penalty
            hex_debuff = self.owner.status_effects.get_effect('crippling_hex')
            if hex_debuff and hasattr(hex_debuff, 'ac_delta'):
                status_ac_bonus += hex_debuff.ac_delta  # Delta is negative
        
        # Apply ring bonuses (Ring of Protection)
        ring_ac_bonus = 0
        if equipment:
            for ring in [equipment.left_ring, equipment.right_ring]:
                if ring and ring.components.has(ComponentType.RING):
                    ring_ac_bonus += ring.ring.get_ac_bonus()
        
        # Phase 19: Shield Wall bonus - count adjacent skeleton allies (4-way adjacency)
        shield_wall_bonus = self._calculate_shield_wall_bonus()
        
        return base_ac + dex_bonus + armor_ac_bonus + status_ac_bonus + ring_ac_bonus + shield_wall_bonus

    def _calculate_shield_wall_bonus(self) -> int:
        """Calculate Shield Wall AC bonus from adjacent skeleton allies.
        
        Phase 19: Skeletons gain +1 AC per adjacent skeleton ally (4-way adjacency).
        NO CAP on the bonus.
        
        Returns:
            int: AC bonus from shield wall (0 if not a skeleton or no allies nearby)
        """
        # Check if this entity has shield wall ability
        if not self.owner or not hasattr(self.owner, 'shieldwall_ac_per_adjacent'):
            return 0
        
        ac_per_adjacent = getattr(self.owner, 'shieldwall_ac_per_adjacent', 0)
        if ac_per_adjacent <= 0:
            return 0
        
        # Count adjacent skeleton allies (4-way adjacency: N, S, E, W)
        # Need access to game state to find other entities
        # This is called during AC calculation, so we need a way to pass entities
        # For now, use a cached value if available (set during combat/AI turns)
        adjacent_count = getattr(self.owner, '_cached_adjacent_skeleton_count', 0)
        
        return adjacent_count * ac_per_adjacent
    
    @property
    def max_hp(self):
        """Get maximum HP including CON modifier and equipment bonuses.
        
        Formula: base_max_hp + CON modifier + equipment bonuses
        
        Example:
            Base HP: 60
            CON: 14 (+2 modifier)
            Equipment: +0
            Max HP: 62

        Returns:
            int: Maximum health points including all modifiers
        """
        if self.owner and self.owner.equipment:
            equipment_bonus = self.owner.equipment.max_hp_bonus
        else:
            equipment_bonus = 0

        # Defensive: ensure all components are valid integers
        base_hp = self.base_max_hp if self.base_max_hp is not None else 0
        con_mod = self.constitution_mod if self.constitution_mod is not None else 0
        equip_bonus = equipment_bonus if equipment_bonus is not None else 0
        
        return base_hp + con_mod + equip_bonus

    @property
    def power(self):
        """Get attack power including equipment bonuses.

        Returns:
            int: Attack power including equipment bonuses
        """
        if self.owner and self.owner.equipment:
            bonus = self.owner.equipment.power_bonus
        else:
            bonus = 0

        return self.base_power + bonus

    @property
    def defense(self):
        """Get defense value including equipment bonuses.

        Returns:
            int: Defense value including equipment bonuses
        """
        if self.owner and self.owner.equipment:
            bonus = self.owner.equipment.defense_bonus
        else:
            bonus = 0

        return self.base_defense + bonus

    def take_damage(self, amount: int, damage_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Apply damage to this fighter.
        
        Reduces current HP by the damage amount, applying resistances if damage_type specified.
        If HP drops to 0 or below, marks the fighter as dead and returns XP reward information.
        
        For bosses, also checks for enrage and low HP dialogue triggers.

        Args:
            amount (int): Amount of damage to apply
            damage_type (str or ResistanceType, optional): Type of damage for resistance calculation.
                Can be "fire", "cold", "poison", "lightning", "acid", etc. Defaults to None (no resistance).

        Returns:
            list: List of result dictionaries, may include 'dead', 'xp', 'message' keys
        """
        results = []
        
        # Apply resistances if damage type is specified
        original_damage = amount
        resistance_pct = 0
        if damage_type:
            amount, resistance_pct = self.apply_resistance(amount, damage_type)
            
            # Add message if resistance reduced damage significantly
            if resistance_pct > 0 and self.owner:
                if resistance_pct >= 100:
                    results.append({
                        'message': MB.custom(f"{self.owner.name} is immune to {damage_type}!", (100, 255, 100))
                    })
                elif resistance_pct >= 50:
                    results.append({
                        'message': MB.info(f"{self.owner.name} resists {damage_type} damage! ({resistance_pct}% resistance, {original_damage} → {amount})")
                    })

        # DEBUG: God mode protection (Tier 1)
        from config.testing_config import get_testing_config
        config = get_testing_config()
        if config.god_mode and self.owner and hasattr(self.owner, 'name') and self.owner.name == "Player":
            # Player in god mode - prevent HP from going below 1
            if self.hp - amount < 1:
                # Reduce damage to leave player at 1 HP
                amount = self.hp - 1
                results.append({
                    'message': MB.warning("🛡️ GOD MODE: Fatal damage prevented!")
                })
        
        self.hp -= amount
        
        # Phase 19: Track damage type for regeneration suppression (troll identity)
        if damage_type and self.owner and hasattr(self.owner, 'regeneration_amount'):
            # Suppress regeneration if damage type is acid or fire
            if damage_type.lower() in ['acid', 'fire']:
                # Get current turn number from TurnManager if available
                turn_number = None
                try:
                    from engine.turn_manager import TurnManager
                    turn_mgr = TurnManager.get_instance()
                    if turn_mgr:
                        turn_number = turn_mgr.turn_number
                except:
                    pass
                
                # Suppress regeneration until next turn
                if turn_number is not None:
                    self.owner.regeneration_suppressed_until_turn = turn_number + 1
                    logger.debug(f"[REGEN SUPPRESSION] {self.owner.name} regeneration suppressed by {damage_type} until turn {turn_number + 1}")
        
        # Record damage taken (only for player)
        statistics = self.owner.get_component_optional(ComponentType.STATISTICS) if self.owner else None
        if statistics:
            statistics.record_damage_taken(amount)
        
        # Check for ring triggers when taking damage (Ring of Teleportation)
        equipment = self._get_equipment(self.owner)
        if equipment:
            for ring in [equipment.left_ring, equipment.right_ring]:
                if ring and ring.components.has(ComponentType.RING):
                    ring_results = ring.ring.on_take_damage(self.owner, amount)
                    results.extend(ring_results)
        
        # Flag monster as "in combat" when attacked (stops looting behavior)
        ai = self.owner.get_component_optional(ComponentType.AI) if self.owner else None
        if not ai and self.owner:
            # Fallback to direct attribute access for backward compatibility
            ai = getattr(self.owner, 'ai', None)
        if ai and hasattr(ai, 'in_combat'):
            ai.in_combat = True
        
        # Phase 19: Interrupt abilities only if final damage > 0
        # Zero damage (from full resistance) should not interrupt abilities
        if amount > 0:
            # Phase 19: Check if this is an Orc Chieftain taking damage
            # If chieftain has an active rally, end it immediately for all rallied orcs
            if ai and hasattr(ai, 'rally_active') and ai.rally_active:
                # Rally is active - end it!
                results.append({'message': MB.combat("The rally falters as the chieftain is struck!")})
                
                # End rally for all rallied orcs
                # We need to find all entities with rally_buff from this chieftain
                # This is handled by the game state, but we mark the rally as ended here
                ai.rally_active = False
                
                # Mark that rally should be cleared (game state will handle removal)
                results.append({
                    'end_rally': True,
                    'chieftain_id': id(self.owner)
                })
            
            # Phase 19: Check if this is an Orc Shaman taking damage while channeling
            # If shaman is channeling Chant of Dissonance, interrupt it immediately
            # IMPORTANT: Only interrupt if final damage > 0 (after resistances)
            if ai and hasattr(ai, 'is_channeling') and ai.is_channeling:
                # Shaman is channeling - interrupt it!
                results.append({'message': MB.combat("The chant is broken!")})
                
                # End channeling
                ai.is_channeling = False
                ai.chant_target_id = None
                
                # Remove DissonantChant effect from target (player)
                # Mark that chant should be cleared (will be handled by result processor)
                results.append({
                    'interrupt_chant': True,
                    'shaman_id': id(self.owner)
                })
        
        # Phase 19: Check for Split Under Pressure (before death check)
        # If split triggers, entity is removed and replaced by children
        # This happens even if HP would cause death - split takes precedence
        split_triggered = False
        if self.owner:
            try:
                from services.slime_split_service import check_split_trigger
                # Note: We don't pass game_map/entities here - caller will handle execution
                # We just check if conditions are met
                split_data = check_split_trigger(self.owner, game_map=None, entities=None)
                if split_data:
                    # Split triggered! Store data and mark entity
                    results.append({
                        "split": split_data,
                        "message": split_data['message']
                    })
                    split_triggered = True
            except ImportError:
                pass  # Service not available (shouldn't happen in production)
        
        # Check for boss dialogue triggers (if not dead yet and not splitting)
        if self.hp > 0 and not split_triggered:
            boss = self.owner.get_component_optional(ComponentType.BOSS) if self.owner else None
            if boss:
                # Check for enrage trigger (only triggers once)
                if boss.check_enrage(self.hp, self.max_hp):
                    enrage_line = boss.get_dialogue("enrage")
                    if enrage_line:
                        results.append({"message": MB.custom(f"{boss.boss_name}: \"{enrage_line}\"", MB.ORANGE)})
                
                # Check for low HP dialogue (<20%)
                hp_percentage = self.hp / self.max_hp if self.max_hp > 0 else 0
                if hp_percentage < 0.2 and not boss.has_used_dialogue("low_hp"):
                    low_hp_line = boss.get_dialogue("low_hp")
                    if low_hp_line:
                        boss.mark_dialogue_used("low_hp")
                        results.append({"message": MB.custom(f"{boss.boss_name}: \"{low_hp_line}\"", MB.YELLOW)})
                
                # Random "hit" reaction (10% chance when boss takes damage)
                elif not boss.has_used_dialogue("hit") and random.random() < 0.1:
                    hit_line = boss.get_dialogue("hit")
                    if hit_line:
                        results.append({"message": MB.custom(f"{boss.boss_name}: \"{hit_line}\"", MB.LIGHT_GRAY)})

        # Normal death check (only if not splitting)
        if self.hp <= 0 and not split_triggered:
            results.append({"dead": self.owner, "xp": self.xp})
            # Note: HP can go negative for XP calculation purposes, but should be
            # displayed as 0 in UI. The UI layer should handle the display clamping.
            
            # Phase 11: Register kill for monster knowledge
            # Only if this entity is a monster (has AI) and killed by player
            try:
                from services.monster_knowledge import get_monster_knowledge_system
                ai = self.owner.get_component_optional(ComponentType.AI) if self.owner else None
                if ai:
                    # This monster was killed - register it
                    knowledge = get_monster_knowledge_system()
                    knowledge.register_killed(self.owner)
            except ImportError:
                pass  # Knowledge system not available

        return results

    def heal(self, amount: int) -> None:
        """Restore health points to this fighter.

        Increases current HP by the heal amount, capped at maximum HP.

        Args:
            amount (int): Amount of health to restore
        """
        # Defensive: ensure values are not None (prevents crashes from configuration errors)
        if amount is None:
            logger.error(f"heal() called with amount=None for {self.owner.name if self.owner else 'unknown'}")
            return
        
        if self.hp is None:
            logger.error(f"heal() called but self.hp is None for {self.owner.name if self.owner else 'unknown'}")
            self.hp = 0
        
        max_hp = self.max_hp
        if max_hp is None:
            logger.error(f"heal() called but max_hp is None for {self.owner.name if self.owner else 'unknown'}")
            max_hp = amount  # Just heal the amount without cap
        
        actual_healing = min(amount, max_hp - self.hp)
        self.hp += amount

        if self.hp > max_hp:
            self.hp = max_hp
        
        # Record healing (only for player)
        statistics = self.owner.get_component_optional(ComponentType.STATISTICS) if self.owner else None
        if statistics:
            statistics.record_healing(actual_healing)

    def attack(self, target: Any) -> List[Dict[str, Any]]:
        """Perform an attack against a target entity.

        Calculates damage based on attacker's power vs target's defense,
        including variable damage from equipped weapons and variable defense from armor.
        
        For ranged weapons (bow/crossbow), animates projectile flight before applying damage.

        Args:
            target (Entity): The target entity to attack

        Returns:
            list: List of result dictionaries with combat messages and effects
        """
        results = []
        
        # Check if using ranged weapon and animate projectile
        if self.owner and hasattr(self.owner, 'equipment') and self.owner.equipment:
            main_hand = self.owner.equipment.main_hand
            if main_hand and hasattr(main_hand, 'item') and hasattr(main_hand.item, 'equipment'):
                equipment = main_hand.item.equipment
                reach = getattr(equipment, 'reach', None)
                
                # If reach > 1, it's a ranged weapon (bow/crossbow) - animate projectile!
                if reach and reach > 1:
                    self._animate_ranged_attack(target, main_hand)

        # Calculate base damage from attacker's power
        base_damage = self.power
        
        # Get variable damage - weapon damage overrides base damage if weapon equipped
        weapon_damage = self._get_weapon_damage()
        if weapon_damage > 0:
            # Weapon equipped - use weapon damage
            variable_damage = weapon_damage
            damage_source = "weapon"
        else:
            # No weapon - use base damage (fists/natural attacks)
            variable_damage = self._get_base_variable_damage()
            damage_source = "base"
        
        total_attack = base_damage + variable_damage
        
        # Apply status effect bonuses/penalties to attack
        if hasattr(self.owner, 'status_effects') and self.owner.status_effects is not None:
            # Heroism: +attack_bonus to attack
            heroism = self.owner.status_effects.get_effect('heroism')
            if heroism:
                total_attack += heroism.attack_bonus
            
            # Weakness: -damage_penalty to attack
            weakness = self.owner.status_effects.get_effect('weakness')
            if weakness:
                total_attack -= weakness.damage_penalty
                total_attack = max(0, total_attack)  # Can't go negative
        
        # Apply ring damage bonuses (Ring of Might)
        equipment = self._get_equipment(self.owner)
        if equipment:
            for ring in [equipment.left_ring, equipment.right_ring]:
                if ring and ring.components.has(ComponentType.RING):
                    damage_bonus_dice = ring.ring.get_damage_bonus()
                    if damage_bonus_dice:
                        # Parse dice notation (e.g., "1d4") and roll
                        import random
                        parts = damage_bonus_dice.split('d')
                        if len(parts) == 2:
                            num_dice = int(parts[0])
                            die_size = int(parts[1])
                            bonus_damage = sum(random.randint(1, die_size) for _ in range(num_dice))
                            total_attack += bonus_damage
        
        # Apply boss damage multiplier if attacker is an enraged boss
        boss = self.owner.get_component_optional(ComponentType.BOSS) if self.owner else None
        if boss and boss.is_enraged:
            multiplier = boss.get_damage_multiplier()
            total_attack = int(total_attack * multiplier)
        
        # Get variable armor defense from target
        armor_defense = target.require_component(ComponentType.FIGHTER)._get_armor_defense()
        
        # Apply defense (including base defense, equipment defense_bonus, and variable armor)
        total_defense = target.require_component(ComponentType.FIGHTER).defense + armor_defense
        final_damage = max(0, total_attack - total_defense)

        if final_damage > 0:
            # Create detailed combat message with clearer format
            # Show: "Attacker attacks Target for X damage (Y attack - Z defense)"
            attack_breakdown = f"{total_attack} attack"
            if variable_damage > 0:
                if damage_source == "weapon":
                    attack_breakdown = f"{total_attack} attack ({self.power} power + {variable_damage} weapon)"
                else:
                    attack_breakdown = f"{total_attack} attack ({self.power} power + {variable_damage} natural)"
            
            defense_breakdown = f"{total_defense} defense"
            if armor_defense > 0:
                defense_breakdown = f"{total_defense} defense ({target.require_component(ComponentType.FIGHTER).defense} base + {armor_defense} armor)"
            
            message_text = "{0} attacks {1} for {2} damage ({3} - {4}).".format(
                self.owner.name.capitalize(), 
                target.name, 
                str(final_damage),
                attack_breakdown,
                defense_breakdown
            )
            
            results.append({
                "message": MB.combat(message_text)
            })
            
            # Log detailed combat breakdown in testing mode
            if is_testing_mode():
                self._log_combat_debug(target, total_attack, variable_damage, damage_source, total_defense, armor_defense, final_damage)
            
            results.extend(target.require_component(ComponentType.FIGHTER).take_damage(final_damage))
            
            # Apply corrosion effects if attacker has corrosion ability
            corrosion_results = self._apply_corrosion_effects(target, final_damage)
            results.extend(corrosion_results)
            
            # Phase 19: Apply engulf effects if attacker has engulf ability
            engulf_results = self._apply_engulf_effects(target, final_damage)
            results.extend(engulf_results)
        else:
            # Attack was completely blocked - show the same clear breakdown
            attack_breakdown = f"{total_attack} attack"
            if variable_damage > 0:
                if damage_source == "weapon":
                    attack_breakdown = f"{total_attack} attack ({self.power} power + {variable_damage} weapon)"
                else:
                    attack_breakdown = f"{total_attack} attack ({self.power} power + {variable_damage} natural)"
            
            defense_breakdown = f"{total_defense} defense"
            if armor_defense > 0:
                defense_breakdown = f"{total_defense} defense ({target.require_component(ComponentType.FIGHTER).defense} base + {armor_defense} armor)"
            
            message_text = "{0} attacks {1} for 0 damage ({2} - {3}) - attack blocked!".format(
                self.owner.name.capitalize(), 
                target.name,
                attack_breakdown,
                defense_breakdown
            )
            
            results.append({
                "message": MB.combat(message_text)
            })
            
            # Log detailed combat breakdown for blocked attacks in testing mode
            if is_testing_mode():
                self._log_combat_debug(target, total_attack, variable_damage, damage_source, total_defense, armor_defense, final_damage)

        return results
    
    def _animate_ranged_attack(self, target, weapon):
        """Animate arrow/bolt flying from attacker to target.
        
        Creates a projectile animation showing an arrow or bolt traveling
        from the attacker's position to the target. The projectile character
        is chosen based on the direction of flight:
        - Horizontal: '-'
        - Vertical: '|'
        - Diagonal: '/' or '\'
        
        Args:
            target (Entity): Target being attacked
            weapon (Entity): Ranged weapon being used
        """
        from tcod.los import bresenham
        from visual_effect_queue import get_effect_queue
        
        # Calculate arrow path using Bresenham's line algorithm
        # bresenham returns numpy array of shape (length, 2), convert to list of tuples
        path_array = bresenham((self.owner.x, self.owner.y), (target.x, target.y))
        path = [(int(x), int(y)) for x, y in path_array]
        
        if not path:
            return  # No path to animate
        
        # Calculate direction for arrow character
        dx = target.x - self.owner.x
        dy = target.y - self.owner.y
        
        # Choose arrow character based on direction
        abs_dx = abs(dx)
        abs_dy = abs(dy)
        
        if abs_dx > abs_dy * 1.5:
            # Mostly horizontal
            arrow_char = ord('-')
        elif abs_dy > abs_dx * 1.5:
            # Mostly vertical
            arrow_char = ord('|')
        elif (dx > 0 and dy > 0) or (dx < 0 and dy < 0):
            # Diagonal: top-left to bottom-right
            arrow_char = ord('\\')
        else:
            # Diagonal: bottom-left to top-right
            arrow_char = ord('/')
        
        # Queue arrow animation
        effect_queue = get_effect_queue()
        effect_queue.queue_projectile(
            path=path,
            char=arrow_char,
            color=(139, 69, 19),  # Brown arrow/bolt
            frame_duration=0.03  # Fast! 30ms per tile
        )
    
    def attack_d20(self, target, is_surprise: bool = False, game_map=None, entities=None):
        """Perform a d20-based attack against a target entity.
        
        New combat system:
        - Roll d20 + DEX modifier + weapon to-hit bonus
        - Compare to target's AC (10 + DEX mod + armor AC)
        - Natural 20 = critical hit (double damage)
        - Natural 1 = fumble (auto-miss)
        - On hit: Roll weapon damage + STR modifier
        
        Phase 9: Surprise attacks force critical hit for 2× damage.
        Phase 21: Invisibility grants surprise attack (canonical execution point).
        
        Args:
            target (Entity): The target entity to attack
            is_surprise (bool): If True, this is a surprise attack (forced crit, already auto-hit).
                               Can also be triggered internally if attacker is invisible.
            game_map (GameMap, optional): Game map for knockback terrain checks
            entities (List[Entity], optional): All entities for knockback blocking checks
            
        Returns:
            list: List of result dictionaries with combat messages and effects
        """
        import random
        from game_messages import Message
        
        results = []
        
        # ═══════════════════════════════════════════════════════════════════════
        # PHASE 22.2: RANGED COMBAT RANGE VALIDATION
        # ═══════════════════════════════════════════════════════════════════════
        # If wielding a ranged weapon, check range bands BEFORE hit roll.
        # Out-of-range attacks are denied (no damage roll).
        from services.ranged_combat_service import is_ranged_weapon, check_ranged_attack_validity
        
        is_ranged_attack = is_ranged_weapon(self.owner)
        ranged_band_info = None
        
        if is_ranged_attack:
            ranged_validity = check_ranged_attack_validity(self.owner, target)
            if not ranged_validity["valid"]:
                # Attack denied - out of range
                results.append({
                    "message": MB.warning(ranged_validity["reason"])
                })
                return results
            ranged_band_info = ranged_validity["band"]
            logger.info(f"[RANGED ATTACK] {self.owner.name} → {target.name}, "
                       f"distance={ranged_validity['distance']}, band={ranged_band_info['band_name']}")
        
        # ═══════════════════════════════════════════════════════════════════════
        # PHASE 21: CANONICAL INVISIBILITY CHECK
        # ═══════════════════════════════════════════════════════════════════════
        # Check if attacker is invisible at moment of attack.
        # This is the single point of truth for invisibility-based surprise attacks.
        # All callers (keyboard, mouse, bot, harness) converge here.
        # Note: Use `is True` to handle Mock objects in tests correctly.
        attacker_was_invisible = getattr(self.owner, 'invisible', None) is True
        invis_surprise = False
        
        if attacker_was_invisible and not is_surprise:
            # Attacker is invisible - this grants surprise attack bonus
            # (unless caller already computed is_surprise=True for other reasons)
            target_ai = target.get_component_optional(ComponentType.AI) if target else None
            attacker_ai = self.owner.get_component_optional(ComponentType.AI) if self.owner else None
            
            # Only player attacks (no AI = player) against monsters (has AI) get invis bonus
            if not attacker_ai and target_ai:
                is_surprise = True
                invis_surprise = True
                logger.info(f"[INVIS ATTACK] {self.owner.name} strikes {target.name} from invisibility!")
                
                # Track metrics
                collector = _get_metrics_collector()
                if collector:
                    collector.increment('invis_attacks')
                    collector.increment('surprise_attacks')
        
        # Phase 11: Register combat engagement for monster knowledge
        try:
            from services.monster_knowledge import get_monster_knowledge_system
            knowledge = get_monster_knowledge_system()
            
            # Check if attacker is player attacking a monster
            attacker_ai = self.owner.get_component_optional(ComponentType.AI) if self.owner else None
            target_ai = target.get_component_optional(ComponentType.AI) if target else None
            
            if not attacker_ai and target_ai:
                # Player attacking monster
                knowledge.register_engaged(target)
            elif attacker_ai and not target_ai:
                # Monster attacking player
                knowledge.register_engaged(self.owner)
        except ImportError:
            pass  # Knowledge system not available
        
        # Roll d20 for attack (still roll for natural 20 display, but surprise bypasses miss)
        d20_roll = random.randint(1, 20)
        
        # Get attacker's to-hit bonus
        to_hit_bonus = self.dexterity_mod
        weapon_bonus = 0
        equipment = self._get_equipment(self.owner)
        if equipment and equipment.main_hand and (equipment.main_hand.components.has(ComponentType.EQUIPPABLE) or hasattr(equipment.main_hand, 'equippable')):
            weapon_bonus = getattr(equipment.main_hand.equippable, 'to_hit_bonus', 0)
        
        # Phase 19: Check for status effect bonuses/penalties
        status_effect_to_hit_bonus = 0
        status_effects = self.owner.get_component_optional(ComponentType.STATUS_EFFECTS) if self.owner else None
        if status_effects:
            # Rally buff: +to-hit
            rally_buff = status_effects.get_effect('rally_buff')
            if rally_buff and hasattr(rally_buff, 'to_hit_bonus'):
                status_effect_to_hit_bonus += rally_buff.to_hit_bonus
            
            # Heroism: +to-hit
            heroism = status_effects.get_effect('heroism')
            if heroism and hasattr(heroism, 'attack_bonus'):
                status_effect_to_hit_bonus += heroism.attack_bonus
            
            # Sonic Bellow debuff: -to-hit
            bellow_debuff = status_effects.get_effect('sonic_bellow_debuff')
            if bellow_debuff and hasattr(bellow_debuff, 'to_hit_penalty'):
                status_effect_to_hit_bonus -= bellow_debuff.to_hit_penalty
            
            # Phase 19: Crippling Hex debuff: -to-hit
            hex_debuff = status_effects.get_effect('crippling_hex')
            if hex_debuff and hasattr(hex_debuff, 'to_hit_delta'):
                status_effect_to_hit_bonus += hex_debuff.to_hit_delta  # Delta is negative
            
            # Blindness: -to-hit (severe penalty)
            blindness = status_effects.get_effect('blindness')
            if blindness:
                status_effect_to_hit_bonus -= 5  # Blindness is a major penalty
            
            # Phase 20E.1: Blinded effect: -to-hit penalty
            blinded = status_effects.get_effect('blinded')
            if blinded and hasattr(blinded, 'to_hit_penalty'):
                status_effect_to_hit_bonus -= blinded.to_hit_penalty
                # Track blind attack attempts
                collector = _get_metrics_collector()
                if collector:
                    collector.increment('blind_attacks_attempted')
            
            # Phase 20E.1: Focused effect: +to-hit bonus
            focused = status_effects.get_effect('focused')
            if focused and hasattr(focused, 'to_hit_bonus'):
                status_effect_to_hit_bonus += focused.to_hit_bonus
        
        # Phase 19: Command the Dead - Lich aura bonus for undead allies
        command_the_dead_bonus = self._check_command_the_dead_aura()
        
        # Calculate total attack roll
        attack_roll = d20_roll + to_hit_bonus + weapon_bonus + status_effect_to_hit_bonus + command_the_dead_bonus
        
        # Get target's AC
        target_ac = target.require_component(ComponentType.FIGHTER).armor_class
        
        # Phase 18: Get crit threshold from weapon (default 20, Keen weapons 19)
        crit_threshold = 20  # Default: only natural 20 crits
        if equipment and equipment.main_hand:
            weapon = equipment.main_hand
            if weapon.components.has(ComponentType.EQUIPPABLE) or hasattr(weapon, 'equippable'):
                equippable = weapon.equippable if hasattr(weapon, 'equippable') else weapon.get_component_optional(ComponentType.EQUIPPABLE)
                if equippable and hasattr(equippable, 'crit_threshold'):
                    threshold_value = equippable.crit_threshold
                    # Defensive: ensure it's an integer (handle mocks)
                    if isinstance(threshold_value, int) and 1 <= threshold_value <= 20:
                        crit_threshold = threshold_value
        
        # Check for critical hit or fumble
        # Phase 9: Surprise attacks are always critical hits
        # Phase 18: Keen weapons crit on expanded range (e.g., 19-20)
        is_critical = (d20_roll >= crit_threshold) or is_surprise
        is_fumble = (d20_roll == 1) and not is_surprise  # Surprise attacks can't fumble
        
        # Determine if attack hits
        # Phase 9: Surprise attacks always hit (already handled in game_actions, but defense-in-depth)
        hit = False
        if is_surprise:
            hit = True  # Surprise attacks always hit
        elif is_critical:
            hit = True  # Natural 20 always hits
        elif is_fumble:
            hit = False  # Natural 1 always misses
        else:
            hit = (attack_roll >= target_ac)
        
        # Phase 13A: Record attack metrics (player vs monster)
        collector = _get_metrics_collector()
        if collector:
            # Determine if attacker is player or monster
            attacker_ai = self.owner.get_component_optional(ComponentType.AI) if self.owner else None
            if not attacker_ai:
                # No AI = player
                collector.record_player_attack(hit)
            else:
                # Has AI = monster
                collector.record_monster_attack(hit)
        
        if hit:
            # Visual feedback: Flash target red (or yellow for crits)!
            show_hit(target.x, target.y, entity=target, is_critical=is_critical)
            
            # ═══════════════════════════════════════════════════════════════════════
            # PHASE 22.2: RANGED CLOSE-RANGE RETALIATION (d==1 only)
            # ═══════════════════════════════════════════════════════════════════════
            # If ranged attack at adjacent range, target gets free melee strike BEFORE
            # ranged damage is applied. For this strike only, player armor is halved.
            # Retaliation uses context manager for armor penalty (scoped, exception-safe).
            if is_ranged_attack and ranged_band_info and ranged_band_info.get("retaliation_triggered"):
                from services.ranged_combat_service import process_retaliation
                retaliation_damage, retaliation_results = process_retaliation(self.owner, target)
                results.extend(retaliation_results)
                
                # Check if attacker died from retaliation
                if self.owner and hasattr(self.owner, 'fighter') and self.owner.fighter:
                    if self.owner.fighter.hp <= 0:
                        logger.info(f"[RANGED RETALIATION] {self.owner.name} killed by retaliation before ranged shot!")
                        return results  # Attacker died, can't complete ranged attack
            
            # Calculate damage
            base_damage = 0
            
            # Phase 20E.2: Check if attacker is disarmed
            # If disarmed, force unarmed damage (weapon attack prevented)
            is_disarmed = False
            if status_effects and status_effects.has_effect('disarmed'):
                is_disarmed = True
                # Track disarmed attack attempt
                collector = _get_metrics_collector()
                if collector:
                    collector.increment('disarmed_attacks_attempted')
            
            # Get weapon damage or fist damage
            # IMPORTANT: Only call _get_weapon_damage() once to avoid side-effect issues
            weapon_damage = self._get_weapon_damage()
            
            if is_disarmed and weapon_damage > 0:
                # Weapon would have been used, but disarmed - force minimal unarmed fallback
                collector = _get_metrics_collector()
                if collector:
                    collector.increment('disarmed_weapon_attacks_prevented')
                # Phase 20E.2: Use fixed minimal unarmed damage (1-2) instead of natural attacks
                # This prevents monsters with high natural damage from trivializing disarm
                import random
                base_damage = random.randint(1, 2)  # Minimal unarmed: punching/grappling
            elif weapon_damage > 0:
                base_damage = weapon_damage
            else:
                # Normal unarmed: use base damage range (player fists, monster natural attacks)
                base_damage = self._get_base_variable_damage()
            
            # Add STR modifier to damage
            damage = base_damage + self.strength_mod
            
            # Phase 19: Add status effect damage bonuses
            status_effect_damage_bonus = 0
            if status_effects:
                # Rally buff: +damage
                rally_buff = status_effects.get_effect('rally_buff')
                if rally_buff and hasattr(rally_buff, 'damage_bonus'):
                    status_effect_damage_bonus += rally_buff.damage_bonus
                
                # Heroism: +damage
                heroism = status_effects.get_effect('heroism')
                if heroism and hasattr(heroism, 'damage_bonus'):
                    status_effect_damage_bonus += heroism.damage_bonus
                
                # Weakness: -damage
                weakness = status_effects.get_effect('weakness')
                if weakness and hasattr(weakness, 'damage_penalty'):
                    status_effect_damage_bonus -= weakness.damage_penalty
            
            damage += status_effect_damage_bonus
            
            # Phase 18/19: Apply damage type modifier (resistance/vulnerability/multipliers)
            # Get weapon damage type (or natural damage type for monsters)
            weapon_damage_type = None
            if equipment and equipment.main_hand:
                weapon = equipment.main_hand
                if weapon.components.has(ComponentType.EQUIPPABLE) or hasattr(weapon, 'equippable'):
                    equippable = weapon.equippable if hasattr(weapon, 'equippable') else weapon.get_component_optional(ComponentType.EQUIPPABLE)
                    if equippable and hasattr(equippable, 'damage_type'):
                        weapon_damage_type = equippable.damage_type
            elif hasattr(self.owner, 'natural_damage_type'):
                # Phase 19: Use natural damage type for unarmed monsters (slimes = acid, etc.)
                weapon_damage_type = self.owner.natural_damage_type
            
            # Check target for resistance/vulnerability
            if weapon_damage_type:
                # Phase 19: Check for damage_type_modifiers dict (multiplier system)
                damage_type_modifiers = getattr(target, 'damage_type_modifiers', None)
                if damage_type_modifiers and isinstance(damage_type_modifiers, dict):
                    multiplier = damage_type_modifiers.get(weapon_damage_type, 1.0)
                    if multiplier != 1.0:
                        # Apply multiplier and round
                        original_damage = damage
                        damage = int(damage * multiplier)
                        # Log damage type modifier application
                        logger.debug(f"[DAMAGE TYPE] {target.name} takes {multiplier}x damage from {weapon_damage_type}: {original_damage} → {damage}")
                else:
                    # Phase 18: Fallback to old ±1 system for backward compatibility
                    target_resistance = getattr(target, 'damage_resistance', None)
                    target_vulnerability = getattr(target, 'damage_vulnerability', None)
                    
                    if target_resistance == weapon_damage_type:
                        damage = damage - 1  # Resistant: -1 damage
                    elif target_vulnerability == weapon_damage_type:
                        damage = damage + 1  # Vulnerable: +1 damage
            
            # ═══════════════════════════════════════════════════════════════════════
            # PHASE 22.2: RANGED DAMAGE RANGE BAND MODIFIER
            # ═══════════════════════════════════════════════════════════════════════
            # Apply range band damage multiplier (before crit doubling).
            # Service owns the multiplier calculation; we just call it.
            ranged_damage_penalty = 0
            if is_ranged_attack and ranged_band_info:
                from services.ranged_combat_service import apply_damage_modifier
                damage, ranged_damage_penalty = apply_damage_modifier(damage, ranged_band_info)
                
                # Log range penalty if any
                if ranged_damage_penalty > 0:
                    multiplier = ranged_band_info.get("damage_multiplier", 1.0)
                    penalty_pct = int((1.0 - multiplier) * 100)
                    results.append({
                        "message": MB.combat(f"📏 Range penalty: {penalty_pct}% damage reduction")
                    })
            
            # Record statistics (only for player)
            statistics = self.owner.get_component_optional(ComponentType.STATISTICS) if self.owner else None
            if statistics:
                statistics.record_attack(hit=True, critical=is_critical)
                statistics.record_damage_dealt(max(1, damage if not is_critical else damage * 2))
            
            # Critical hit: double all damage
            if is_critical:
                damage = damage * 2
                damage = max(1, damage)  # Minimum 1 damage even on crit
                
                message_text = "CRITICAL HIT! {0} strikes {1} for {2} damage!".format(
                    self.owner.name.capitalize(),
                    target.name,
                    damage
                )
                results.append({
                    "message": MB.combat_critical(message_text)
                })
            else:
                # Normal hit
                damage = max(1, damage)  # Minimum 1 damage
                
                # Calculate hit percentage for display
                min_roll_needed = target_ac - (to_hit_bonus + weapon_bonus)
                hit_percentage = max(5, min(95, (21 - min_roll_needed) * 5))
                
                message_text = "{0} attacks {1} ({2}% to hit) - HIT for {3} damage!".format(
                    self.owner.name.capitalize(),
                    target.name,
                    hit_percentage,
                    damage
                )
                results.append({
                    "message": MB.combat(message_text)
                })
            
            # Log detailed combat info in testing mode
            if is_testing_mode():
                self._log_d20_combat(d20_roll, to_hit_bonus, weapon_bonus, attack_roll,
                                    target_ac, hit, is_critical, damage, base_damage)
            
            # Apply damage (pass damage type for regeneration suppression)
            results.extend(target.require_component(ComponentType.FIGHTER).take_damage(damage, damage_type=weapon_damage_type))
            
            # Phase 22.2: Track ranged damage metrics (service owns metric recording)
            if is_ranged_attack:
                from services.ranged_combat_service import record_ranged_damage_metrics
                record_ranged_damage_metrics(damage, ranged_damage_penalty)
            
            # Apply corrosion effects if applicable
            corrosion_results = self._apply_corrosion_effects(target, damage)
            results.extend(corrosion_results)
            
            # Phase 19: Apply engulf effects if applicable
            engulf_results = self._apply_engulf_effects(target, damage)
            results.extend(engulf_results)
            
            # Phase 19: Apply life drain effects if applicable
            life_drain_results = self._apply_life_drain_effects(target, damage)
            results.extend(life_drain_results)
            
            # Phase 10.1: Apply plague spread if attacker has plague_attack ability
            plague_results = self._apply_plague_spread(target)
            results.extend(plague_results)
            
            # Phase 20A: Apply poison effect if attacker has poison_attack ability
            poison_results = self._apply_poison_effect(target)
            results.extend(poison_results)

            # Phase 20B.1: Apply burning effect if attacker has burning_attack ability
            burning_results = self._apply_burning_effect(target)
            results.extend(burning_results)

            # Phase 20C.1: Apply slow effect if attacker has web_spit ability
            slow_results = self._apply_slow_effect(target)
            results.extend(slow_results)

            # Phase 20A.1: Player-facing poison weapon delivery (successful hit only)
            weapon_poison_results = self._apply_player_weapon_poison_on_hit(target)
            results.extend(weapon_poison_results)
            
            # ═══════════════════════════════════════════════════════════════════════
            # PHASE 22.2.2: SPECIAL AMMO EFFECTS (on hit only)
            # ═══════════════════════════════════════════════════════════════════════
            # If ranged attack with loaded quiver, apply ammo-specific rider effect.
            # Consumption happens below (after hit/miss determination).
            if is_ranged_attack:
                ammo_effect_results = self._apply_special_ammo_effects(target)
                results.extend(ammo_effect_results)
            
            # ═══════════════════════════════════════════════════════════════════════
            # PHASE 22.2: RANGED KNOCKBACK (10% chance for 1-tile knockback)
            # ═══════════════════════════════════════════════════════════════════════
            # Ranged attacks have a 10% chance to knock target back 1 tile.
            # Service owns the roll and execution; Fighter just orchestrates.
            if is_ranged_attack and game_map and entities:
                from services.ranged_combat_service import roll_ranged_knockback, apply_ranged_knockback
                if roll_ranged_knockback():
                    kb_result = apply_ranged_knockback(self.owner, target, game_map, entities)
                    if kb_result["applied"]:
                        results.extend(kb_result["results"])
                    # Note: Metrics are recorded by the service
            
            # Weapon knockback delivery (successful hit only, player + monsters)
            # Execute directly if game_map/entities available (canonical path)
            # Note: This is for melee knockback weapons, not ranged knockback
            if game_map and entities and not is_ranged_attack:
                knockback_results = self._apply_weapon_knockback_on_hit(target, game_map, entities)
                results.extend(knockback_results)
            
            # Phase 22.1: Apply Oath effects (Run Identity) if player has an Oath
            oath_results = self._apply_oath_effects(target)
            results.extend(oath_results)
            
            # IMPORTANT: Set attacker's in_combat flag when attacking the PLAYER
            # This keeps monsters engaged even if they leave FOV
            # But DON'T set it for monster-vs-monster combat (taunt scenarios)
            # so they return to normal AI after taunt ends
            attacker_ai = self.owner.get_component_optional(ComponentType.AI) if self.owner else None
            
            # Only set in_combat if attacking the player (not other monsters)
            if attacker_ai and hasattr(attacker_ai, 'in_combat'):
                # Check if target is the player (has no AI component)
                target_ai = target.get_component_optional(ComponentType.AI) if target else None
                
                if not target_ai:
                    # Target has no AI = it's the player
                    attacker_ai.in_combat = True
        else:
            # Visual feedback: Only show animation on fumbles (critical fails)!
            if is_fumble:
                show_miss(target.x, target.y, entity=target)
            
            # Record miss statistics (only for player)
            statistics = self.owner.get_component_optional(ComponentType.STATISTICS) if self.owner else None
            if statistics:
                statistics.record_attack(hit=False, fumble=is_fumble)
            
            # Phase 20E.1: Track blind_attacks_missed
            if status_effects and status_effects.has_effect('blinded'):
                collector = _get_metrics_collector()
                if collector:
                    collector.increment('blind_attacks_missed')
            
            # Miss
            if is_fumble:
                message_text = "FUMBLE! {0} attacks {1} - complete miss!".format(
                    self.owner.name.capitalize(),
                    target.name
                )
                results.append({
                    "message": MB.combat_fumble(message_text)
                })
            else:
                # Calculate hit percentage for display
                min_roll_needed = target_ac - (to_hit_bonus + weapon_bonus)
                hit_percentage = max(5, min(95, (21 - min_roll_needed) * 5))
                
                message_text = "{0} attacks {1} ({2}% to hit) - MISS!".format(
                    self.owner.name.capitalize(),
                    target.name,
                    hit_percentage
                )
                results.append({
                    "message": MB.combat_miss(message_text)
                })
            
            # Log miss in testing mode
            if is_testing_mode():
                self._log_d20_combat(d20_roll, to_hit_bonus, weapon_bonus, attack_roll,
                                    target_ac, hit, is_fumble, 0, 0)
        
        # ═══════════════════════════════════════════════════════════════════════
        # PHASE 22.2.2: QUIVER CONSUMPTION (hit OR miss, but not denied)
        # ═══════════════════════════════════════════════════════════════════════
        # Consume 1 special ammo from quiver on ranged attack (hit or miss).
        # Denied attacks (out of range) don't consume ammo (handled earlier).
        if is_ranged_attack:
            consumption_results = self._consume_special_ammo()
            results.extend(consumption_results)
        
        # ═══════════════════════════════════════════════════════════════════════
        # PHASE 21: BREAK INVISIBILITY AFTER ATTACK
        # ═══════════════════════════════════════════════════════════════════════
        # Invisibility breaks after attack resolution (whether hit or miss).
        # This is the canonical execution point - all callers converge here.
        if attacker_was_invisible:
            status_manager = self.owner.get_component_optional(ComponentType.STATUS_EFFECTS)
            if status_manager and status_manager.has_effect("invisibility"):
                break_results = status_manager.remove_effect("invisibility")
                results.extend(break_results)
                
                # Track metrics
                collector = _get_metrics_collector()
                if collector:
                    collector.increment('invis_broken_by_attack')
        
        return results
    
    def _log_d20_combat(self, d20_roll, to_hit_bonus, weapon_bonus, attack_roll,
                        target_ac, hit, is_special, damage, base_damage):
        """Log detailed d20 combat breakdown for debugging.
        
        Args:
            d20_roll: The raw d20 roll (1-20)
            to_hit_bonus: DEX modifier
            weapon_bonus: Weapon to-hit bonus
            attack_roll: Total attack roll
            target_ac: Target's armor class
            hit: Whether attack hit
            is_special: Whether it was a crit or fumble
            damage: Damage dealt
            base_damage: Base damage before STR modifier
        """
        special_text = ""
        if is_special and d20_roll == 20:
            special_text = " [CRITICAL HIT]"
        elif is_special and d20_roll == 1:
            special_text = " [FUMBLE]"
        
        result_text = "HIT" if hit else "MISS"
        
        debug_text = (f"d20 Combat: {self.owner.name} rolled {d20_roll} + {to_hit_bonus} (DEX) "
                     f"+ {weapon_bonus} (weapon) = {attack_roll} vs AC {target_ac} → {result_text}{special_text}")
        
        if hit and damage > 0:
            debug_text += f" | Damage: {base_damage} (base) + {self.strength_mod} (STR) = {damage}"
            if is_special and d20_roll == 20:
                debug_text += " × 2 (crit)"
        
        combat_logger.debug(debug_text)
    
    def _log_combat_debug(self, target, total_attack: int, variable_damage: int, 
                         damage_source: str, total_defense: int, armor_defense: int, final_damage: int) -> None:
        """Log detailed combat breakdown for debugging in testing mode.
        
        Args:
            target: Target entity being attacked
            total_attack: Total attack value (power + variable damage)
            variable_damage: Variable damage rolled (weapon or base)
            damage_source: Source of variable damage ("weapon" or "base")
            total_defense: Total defense value (defense + armor)
            armor_defense: Variable armor defense rolled
            final_damage: Final damage after calculations
        """
        # Get damage range info for display based on source
        damage_range = ""
        equipment = self._get_equipment(self.owner)
        if damage_source == "weapon" and equipment and equipment.main_hand and equipment.main_hand.equippable:
            equip = equipment.main_hand.equippable
            if equip.damage_min > 0 and equip.damage_max > 0:
                damage_range = f" ({equip.damage_min}-{equip.damage_max} dmg)"
        elif damage_source == "base" and self.damage_min > 0 and self.damage_max > 0:
            # Base damage range (fists/natural attacks)
            damage_range = f" ({self.damage_min}-{self.damage_max} dmg)"
        
        armor_range = ""
        target_equipment = self._get_equipment(target)
        if target_equipment and target_equipment.off_hand and target_equipment.off_hand.equippable:
            equip = target_equipment.off_hand.equippable
            if equip.defense_min > 0 and equip.defense_max > 0:
                armor_range = f" ({equip.defense_min}-{equip.defense_max} def)"
        
        # Build and log debug information
        attacker_name = self.owner.name.capitalize()
        target_name = target.name
        
        debug_text = (f"{attacker_name} [power:{self.base_power}+{self.power-self.base_power}]{damage_range} attacks for {total_attack} "
                     f"({self.power} power + {variable_damage} rolled), "
                     f"{target_name} [def:{target.require_component(ComponentType.FIGHTER).base_defense}+{target.require_component(ComponentType.FIGHTER).defense-target.require_component(ComponentType.FIGHTER).base_defense}]{armor_range} blocks {total_defense} "
                     f"({target.require_component(ComponentType.FIGHTER).defense} defense + {armor_defense} rolled) "
                     f"= {final_damage} total damage")
        
        combat_logger.debug(debug_text)
    
    def _get_weapon_damage(self) -> int:
        """Get variable damage from equipped weapon.
        
        Returns:
            int: Random damage from equipped weapon, or 0 if no weapon
        """
        equipment = self._get_equipment(self.owner)
        if equipment and equipment.main_hand and equipment.main_hand.equippable:
            return equipment.main_hand.equippable.roll_damage()
        return 0
    
    def _get_base_variable_damage(self) -> int:
        """Get variable base damage (fists for players, natural attacks for monsters).
        
        Returns:
            int: Random damage within the entity's base damage range, or 0 if no range configured
        """
        if self.damage_min > 0 and self.damage_max > 0:
            import random
            return random.randint(self.damage_min, self.damage_max)
        return 0
    
    def _get_monster_variable_damage(self) -> int:
        """Legacy method - now redirects to _get_base_variable_damage for compatibility.
        
        Returns:
            int: Random damage within the entity's base damage range
        """
        return self._get_base_variable_damage()
    
    def _get_armor_defense(self) -> int:
        """Get variable defense from equipped armor.
        
        Returns:
            int: Random defense from equipped armor, or 0 if no armor
        """
        try:
            equipment = self._get_equipment(self.owner)
            if equipment and equipment.off_hand and equipment.off_hand.equippable:
                return equipment.off_hand.equippable.roll_defense()
        except (AttributeError, TypeError):
            pass
        return 0
    
    def _apply_corrosion_effects(self, target, damage_dealt):
        """Apply corrosion effects if attacker has corrosion ability.
        
        Phase 19: Corrosive Contact - Only affects METAL weapons with small
        chance per successful hit. Permanent degradation clamped at 50% base.
        
        Args:
            target: The entity that was attacked
            damage_dealt: Amount of damage that was dealt
            
        Returns:
            list: List of result dictionaries with corrosion messages
        """
        results = []
        
        # Only apply corrosion if damage was dealt and attacker has corrosion ability
        if damage_dealt <= 0:
            return results
        
        # Check if attacker has corrosion ability
        if not self._has_corrosion_ability():
            return results
        
        # Import here to avoid circular imports
        import random
        from game_messages import Message
        
        # Phase 19: Tiered corrosion chance by slime type (5%/10%/15%)
        # Get corrosion chance from entity config, default to 0.05 for backward compatibility
        corrosion_chance = getattr(self.owner, 'corrosion_chance', 0.05)
        
        # Chance to corrode equipment on successful hit (deterministic under seeded runs)
        if random.random() < corrosion_chance:
            # Phase 19: Only corrode target's METAL weapon
            weapon_corrosion = self._corrode_weapon(target)
            results.extend(weapon_corrosion)
        
        return results
    
    def _apply_engulf_effects(self, target, damage_dealt):
        """Apply engulf effects if attacker has engulf ability.
        
        Phase 19: Slime Engulf - Movement penalty that persists while adjacent.
        Deterministic (no RNG) - always applies on successful hit.
        
        Args:
            target: The entity that was attacked
            damage_dealt: Amount of damage that was dealt
            
        Returns:
            list: List of result dictionaries with engulf messages
        """
        results = []
        
        # Only apply engulf if damage was dealt and attacker has engulf ability
        if damage_dealt <= 0:
            return results
        
        # Check if attacker has engulf ability
        if not self._has_engulf_ability():
            return results
        
        # Phase 19: Engulf is deterministic (no RNG) - always applies on hit
        # Apply EngulfedEffect to target
        from components.status_effects import EngulfedEffect
        from components.component_registry import ComponentType
        
        # Ensure target has status effect manager
        if not target.status_effects:
            target.status_effects = target.get_status_effect_manager()
        
        # Apply or refresh engulfed effect (3 turn duration)
        engulf_effect = EngulfedEffect(duration=3, owner=target)
        engulf_results = target.add_status_effect(engulf_effect)
        results.extend(engulf_results)
        
        return results
    
    def _apply_life_drain_effects(self, target, damage_dealt):
        """Apply life drain effects if attacker has life_drain_pct attribute.
        
        Phase 19: Wraith Life Drain - Heals attacker for % of damage dealt.
        Deterministic (no RNG) - always applies on successful hit.
        Capped at attacker's missing HP (can't overheal).
        Blocked by WardAgainstDrainEffect status on target.
        
        Args:
            target: The entity that was attacked
            damage_dealt: Amount of damage that was dealt (after resistances)
            
        Returns:
            list: List of result dictionaries with drain messages
        """
        results = []
        
        # Only apply drain if damage was dealt
        if damage_dealt <= 0:
            return results
        
        # Check if attacker has life_drain_pct attribute
        life_drain_pct = getattr(self.owner, 'life_drain_pct', None)
        if life_drain_pct is None or not isinstance(life_drain_pct, (int, float)) or life_drain_pct <= 0:
            return results
        
        # Check if target has ward against drain effect (full immunity)
        if target.status_effects and target.status_effects.has_effect('ward_against_drain'):
            # Ward blocks drain - emit message
            results.append({
                'message': MB.status_effect("The ward repels the drain!")
            })
            
            # Record blocked drain attempt for metrics
            try:
                from services.scenario_metrics import get_active_metrics_collector
                collector = get_active_metrics_collector()
                if collector:
                    collector.record_life_drain_attempt(
                        attacker=self.owner,
                        target=target,
                        heal_amount=0,
                        blocked=True
                    )
            except ImportError:
                pass  # Metrics not available
            
            return results
        
        # Calculate drain amount: ceil(damage * drain_pct)
        import math
        drain_amount = math.ceil(damage_dealt * life_drain_pct)
        
        # Cap drain at attacker's missing HP (can't overheal)
        missing_hp = self.base_max_hp - self.hp
        drain_amount = min(drain_amount, missing_hp)
        
        # Only heal if there's missing HP to recover
        if drain_amount > 0:
            # Heal the attacker
            self.hp += drain_amount
            
            # Emit drain message
            results.append({
                'message': MB.combat("The wraith drains your life! (+{0} HP)".format(drain_amount))
            })
            
            # Record successful drain for metrics
            try:
                from services.scenario_metrics import get_active_metrics_collector
                collector = get_active_metrics_collector()
                if collector:
                    collector.record_life_drain_attempt(
                        attacker=self.owner,
                        target=target,
                        heal_amount=drain_amount,
                        blocked=False
                    )
            except ImportError:
                pass  # Metrics not available
        
        return results
    
    def _has_corrosion_ability(self):
        """Check if this entity has corrosion ability.
        
        Returns:
            bool: True if entity can corrode equipment
        """
        # Check if entity has special_abilities with corrosion
        if (hasattr(self.owner, 'special_abilities') and 
            self.owner.special_abilities and 
            isinstance(self.owner.special_abilities, (list, tuple)) and
            'corrosion' in self.owner.special_abilities):
            return True
        
        # Check faction-based corrosion (slimes)
        if self.owner:
            from components.faction import Faction
            # Try ComponentRegistry first, fallback to direct attribute
            from components.component_registry import ComponentRegistry
            if isinstance(getattr(self.owner, 'components', None), ComponentRegistry):
                faction = self.owner.get_component_optional(ComponentType.FACTION)
                if faction and faction == Faction.HOSTILE_ALL:
                    return True
        
        return False
    
    def _apply_plague_spread(self, target):
        """Apply plague spread if attacker has plague_attack ability.
        
        Phase 10.1: Plague zombies have a chance to spread the Plague of
        Restless Death on successful melee attacks against corporeal flesh targets.
        
        Args:
            target: The entity that was attacked
            
        Returns:
            list: List of result dictionaries with plague infection messages
        """
        results = []
        
        # Check if attacker has plague_attack ability
        if not self._has_plague_attack_ability():
            return results
        
        # Import helper to check if target is eligible (corporeal flesh)
        from item_functions import _is_corporeal_flesh
        if not _is_corporeal_flesh(target):
            return results
        
        # Check if target already has the plague
        target_status = target.get_component_optional(ComponentType.STATUS_EFFECTS)
        if target_status and target_status.has_effect("plague_of_restless_death"):
            return results  # Already infected
        
        # Plague spread chance: 25%
        import random
        PLAGUE_SPREAD_CHANCE = 0.25
        
        if random.random() < PLAGUE_SPREAD_CHANCE:
            # Apply plague effect to target
            # NOTE: apply_plague_effect expects target as keyword arg, not positional
            from item_functions import apply_plague_effect
            plague_results = apply_plague_effect(self.owner, target=target)
            
            collector = _get_metrics_collector()
            if collector:
                collector.record_plague_infection(self.owner, target)
            
            # Add our own message about the spread
            from message_builder import MessageBuilder as MB
            results.append({
                "message": MB.custom(
                    f"☠️ {self.owner.name}'s diseased touch spreads the plague to {target.name}!",
                    (150, 200, 50)  # Sickly green
                )
            })
            
            # Phase 11: Register plague_carrier trait discovery
            try:
                from services.monster_knowledge import get_monster_knowledge_system
                from balance.knowledge_config import TRAIT_PLAGUE_CARRIER
                knowledge = get_monster_knowledge_system()
                knowledge.register_trait(self.owner, TRAIT_PLAGUE_CARRIER)
            except ImportError:
                pass  # Knowledge system not available
            
            # Merge in results from apply_plague_effect
            results.extend(plague_results)
        
        return results
    
    def _has_plague_attack_ability(self):
        """Check if this entity has plague_attack ability.
        
        Phase 10.1: Plague zombies can spread plague on melee hits.
        
        Returns:
            bool: True if entity can spread plague on attacks
        """
        # Check if entity has special_abilities with plague_attack
        if (hasattr(self.owner, 'special_abilities') and 
            self.owner.special_abilities and 
            isinstance(self.owner.special_abilities, (list, tuple)) and
            'plague_attack' in self.owner.special_abilities):
            return True
        
        # Also check tags for plague_carrier
        if (hasattr(self.owner, 'tags') and 
            self.owner.tags and 
            isinstance(self.owner.tags, (list, tuple, set)) and
            'plague_carrier' in self.owner.tags):
            return True
        
        return False
    
    def _apply_poison_effect(self, target):
        """Apply poison effect if attacker has poison_attack ability.
        
        Phase 20A: Venomous creatures (spiders, etc.) can poison targets on hit.
        Poison is applied on every successful hit if not already poisoned.
        If already poisoned, the duration is refreshed (non-stacking).
        
        Args:
            target: The entity that was attacked
            
        Returns:
            list: List of result dictionaries with poison application messages
        """
        results = []
        
        # Check if attacker has poison_attack ability
        if not self._has_poison_attack_ability():
            return results
        
        # Get metrics collector for tracking
        collector = _get_metrics_collector()
        
        # Apply poison effect to target
        from components.status_effects import PoisonEffect, StatusEffectManager
        
        # Ensure target has status_effects component
        if not target.components.has(ComponentType.STATUS_EFFECTS):
            target.status_effects = StatusEffectManager(target)
            target.components.add(ComponentType.STATUS_EFFECTS, target.status_effects)
        
        # Check if target already has poison (will be refreshed by add_effect)
        already_poisoned = target.status_effects.has_effect('poison')
        
        # Create and apply poison effect
        poison = PoisonEffect(owner=target)
        poison_results = target.status_effects.add_effect(poison)
        results.extend(poison_results)
        
        # Register poison trait with monster knowledge system
        if hasattr(target, 'has_status_effect') and target.has_status_effect('poison'):
            try:
                from services.monster_knowledge import get_monster_knowledge_system
                knowledge = get_monster_knowledge_system()
                # Register that this attacker type applies poison
                knowledge.register_trait(self.owner, 'poison_attack')
            except ImportError:
                pass  # Knowledge system not available
        
        return results

    def _apply_burning_effect(self, target):
        """Apply burning effect if attacker has burning_attack ability.
        
        Phase 20B.1: Fire Beetles and other fire creatures can ignite targets on hit.
        Burning is applied on every successful hit if not already burning.
        If already burning, the duration is refreshed (non-stacking).
        
        Args:
            target: The entity that was attacked
            
        Returns:
            list: List of result dictionaries with burning application messages
        """
        results = []
        
        # Check if attacker has burning_attack ability
        if not self._has_burning_attack_ability():
            return results
        
        # Apply burning effect to target
        from components.status_effects import BurningEffect, StatusEffectManager
        
        # Ensure target has status_effects component
        if not target.components.has(ComponentType.STATUS_EFFECTS):
            target.status_effects = StatusEffectManager(target)
            target.components.add(ComponentType.STATUS_EFFECTS, target.status_effects)
        
        # Create and apply burning effect
        # Standard fire beetle burning: duration 4, damage 1
        burning = BurningEffect(duration=4, owner=target, damage_per_turn=1)
        burning_results = target.status_effects.add_effect(burning)
        results.extend(burning_results)
        
        # Record metrics (burning_applications is handled in BurningEffect.apply())
        
        # Register burning trait with monster knowledge system
        if hasattr(target, 'has_status_effect') and target.has_status_effect('burning'):
            try:
                from services.monster_knowledge import get_monster_knowledge_system
                knowledge = get_monster_knowledge_system()
                # Register that this attacker type applies burning
                knowledge.register_trait(self.owner, 'burning_attack')
            except ImportError:
                pass  # Knowledge system not available
        
        return results

    def _apply_slow_effect(self, target):
        """Apply slow effect if attacker has web_spit ability.
        
        Phase 20C.1: Web Spiders and other creatures can slow targets on hit.
        Slow is applied on every successful hit if not already slowed.
        If already slowed, the duration is refreshed (non-stacking).
        
        Args:
            target: The entity that was attacked
            
        Returns:
            list: List of result dictionaries with slow application messages
        """
        results = []
        
        # Check if attacker has web_spit or slow_attack ability
        if not self._has_web_spit_ability():
            return results
        
        # Apply slow effect to target
        from components.status_effects import SlowedEffect, StatusEffectManager
        
        # Ensure target has status_effects component
        if not target.components.has(ComponentType.STATUS_EFFECTS):
            target.status_effects = StatusEffectManager(target)
            target.components.add(ComponentType.STATUS_EFFECTS, target.status_effects)
        
        # Create and apply slow effect
        # Standard web spider slow: duration 6
        slow = SlowedEffect(duration=6, owner=target)
        slow_results = target.status_effects.add_effect(slow)
        results.extend(slow_results)
        
        # Register web_spit trait with monster knowledge system
        if hasattr(target, 'has_status_effect') and target.has_status_effect('slowed'):
            try:
                from services.monster_knowledge import get_monster_knowledge_system
                knowledge = get_monster_knowledge_system()
                # Register that this attacker type applies web_spit
                knowledge.register_trait(self.owner, 'web_spit')
            except ImportError:
                pass  # Knowledge system not available
        
        return results

    def _apply_oath_effects(self, target):
        """Apply Oath effects if attacker (player) has an active Oath.
        
        Phase 22.1.1: Run Identity via Oaths (refined).
        Oaths are permanent status effects chosen at run start that bias playstyle.
        
        - Oath of Embers: 33% burning proc + self-burn if adjacent (risk/reward)
        - Oath of Venom: 25% poison proc + duration extension if already poisoned (focus-fire)
        - Oath of Chains: Handled in knockback_service (positioning constraint)
        
        Enforcement happens at canonical execution point (Fighter.attack_d20).
        Called AFTER knockback resolution (tactical feature for Embers).
        
        Args:
            target: The entity that was attacked
            
        Returns:
            list: List of result dictionaries with Oath effect messages
        """
        results = []
        
        # Only apply Oaths if attacker is player (no AI component)
        attacker_ai = self.owner.get_component_optional(ComponentType.AI) if self.owner else None
        if attacker_ai:
            # Attacker is a monster, not player - no Oath effects
            return results
        
        # Check for status effects component
        status_effects = self.owner.get_component_optional(ComponentType.STATUS_EFFECTS) if self.owner else None
        if not status_effects:
            return results
        
        # Get metrics collector
        collector = _get_metrics_collector()
        
        # =====================================================================
        # Oath of Embers: Burning proc + self-burn risk
        # =====================================================================
        oath_embers = status_effects.get_effect('oath_of_embers')
        if oath_embers:
            import random
            # 33% chance to apply burning to target
            if random.random() < oath_embers.burn_chance:
                from components.status_effects import BurningEffect, StatusEffectManager
                
                # Ensure target has status_effects component
                if not target.components.has(ComponentType.STATUS_EFFECTS):
                    target.status_effects = StatusEffectManager(target)
                    target.components.add(ComponentType.STATUS_EFFECTS, target.status_effects)
                
                # Create and apply burning effect to target
                burning = BurningEffect(
                    duration=oath_embers.burn_duration, 
                    owner=target, 
                    damage_per_turn=oath_embers.burn_damage_per_turn
                )
                burning_results = target.status_effects.add_effect(burning)
                results.extend(burning_results)
                
                # Track proc
                if collector:
                    collector.increment('oath_embers_procs')
                
                # Phase 22.1.1: Check if player is adjacent after knockback (risk/reward)
                # This is called AFTER knockback resolution, so adjacency check is tactical
                import math
                distance = math.sqrt((self.owner.x - target.x)**2 + (self.owner.y - target.y)**2)
                if distance <= 1.5:  # Adjacent (including diagonals)
                    # Apply self-burn (1 dmg, 1 turn)
                    if not self.owner.components.has(ComponentType.STATUS_EFFECTS):
                        self.owner.status_effects = StatusEffectManager(self.owner)
                        self.owner.components.add(ComponentType.STATUS_EFFECTS, self.owner.status_effects)
                    
                    self_burn = BurningEffect(
                        duration=oath_embers.self_burn_duration,
                        owner=self.owner,
                        damage_per_turn=oath_embers.self_burn_damage
                    )
                    self_burn_results = self.owner.status_effects.add_effect(self_burn)
                    results.extend(self_burn_results)
                    
                    # Track self-burn proc
                    if collector:
                        collector.increment('oath_embers_self_burn_procs')
        
        # =====================================================================
        # Oath of Venom: Poison proc + duration extension on re-proc
        # =====================================================================
        oath_venom = status_effects.get_effect('oath_of_venom')
        if oath_venom:
            import random
            # 25% chance to apply/extend poison
            if random.random() < oath_venom.poison_chance:
                from components.status_effects import PoisonEffect, StatusEffectManager
                
                # Ensure target has status_effects component
                if not target.components.has(ComponentType.STATUS_EFFECTS):
                    target.status_effects = StatusEffectManager(target)
                    target.components.add(ComponentType.STATUS_EFFECTS, target.status_effects)
                
                # Check if target already has poison (focus-fire reward)
                target_status_effects = target.get_component_optional(ComponentType.STATUS_EFFECTS)
                already_poisoned = target_status_effects and target_status_effects.has_effect('poison')
                
                if already_poisoned:
                    # Extend existing poison duration (refresh + bonus)
                    existing_poison = target_status_effects.get_effect('poison')
                    if existing_poison:
                        # Refresh to base duration + extension bonus
                        existing_poison.duration = oath_venom.poison_duration + oath_venom.duration_extension
                        results.append({
                            'message': MB.status_effect(f"{target.name}'s poison is extended!")
                        })
                        
                        # Track extension
                        if collector:
                            collector.increment('oath_venom_duration_extensions')
                else:
                    # Apply fresh poison
                    poison = PoisonEffect(
                        owner=target,
                        duration=oath_venom.poison_duration,
                        damage_per_tick=oath_venom.poison_damage_per_turn
                    )
                    poison_results = target.status_effects.add_effect(poison)
                    results.extend(poison_results)
                
                # Track proc (both fresh and extensions)
                if collector:
                    collector.increment('oath_venom_procs')
        
        return results

    def _has_web_spit_ability(self):
        """Check if this entity has web_spit ability."""
        if not self.owner:
            return False
        
        # Check special_abilities list if it exists
        if hasattr(self.owner, 'special_abilities') and self.owner.special_abilities:
            return ('web_spit' in self.owner.special_abilities or 
                    'slow_attack' in self.owner.special_abilities)
            
        return False

    def _apply_player_weapon_poison_on_hit(self, target):
        """Phase 20A.1: Apply poison to target if PLAYER is using a poisoned weapon.
        
        Hard constraints:
        - Player-facing only (do NOT allow monsters to poison via weapon flag in this phase)
        - Apply only on successful hit (caller is inside hit branch)
        - Reuse canonical PoisonEffect unchanged (duration/damage/refresh/resistance)
        - Use existing StatusEffectManager.add_effect() semantics (non-stacking refresh)
        """
        results = []
        
        # Player-only gate:
        # - Primary: faction == PLAYER (canonical identity for actual player entity today)
        # - Secondary: must NOT have AI (defense-in-depth against future friendly AI companions)
        from components.faction import Faction
        if getattr(self.owner, 'faction', None) != Faction.PLAYER:
            return results
        if (self.owner.get_component_optional(ComponentType.AI) if self.owner else None) is not None:
            return results
        
        equipment = self._get_equipment(self.owner)
        if not equipment or not equipment.main_hand or not getattr(equipment.main_hand, 'equippable', None):
            return results
        
        equippable = equipment.main_hand.equippable
        if not getattr(equippable, 'applies_poison_on_hit', False):
            return results
        
        from components.status_effects import PoisonEffect, StatusEffectManager
        
        # Ensure target has status_effects component
        if not target.components.has(ComponentType.STATUS_EFFECTS):
            target.status_effects = StatusEffectManager(target)
            target.components.add(ComponentType.STATUS_EFFECTS, target.status_effects)
        
        # Apply (or refresh) poison
        poison = PoisonEffect(owner=target)
        results.extend(target.status_effects.add_effect(poison))
        
        return results
    
    def _has_poison_attack_ability(self):
        """Check if this entity has poison_attack ability.
        
        Phase 20A: Venomous creatures can apply poison on melee hits.
        
        Returns:
            bool: True if entity can apply poison on attacks
        """
        # Check if entity has special_abilities with poison_attack
        if (hasattr(self.owner, 'special_abilities') and 
            self.owner.special_abilities and 
            isinstance(self.owner.special_abilities, (list, tuple)) and
            'poison_attack' in self.owner.special_abilities):
            return True
        
        # Also check tags for venomous
        if (hasattr(self.owner, 'tags') and 
            self.owner.tags and 
            isinstance(self.owner.tags, (list, tuple, set)) and
            'venomous' in self.owner.tags):
            return True
        
        return False
    
    def _has_burning_attack_ability(self):
        """Check if this entity has burning_attack ability.
        
        Phase 20B.1: Fire creatures can apply burning on melee hits.
        
        Returns:
            bool: True if entity can apply burning on attacks
        """
        # Check if entity has special_abilities with burning_attack
        if (hasattr(self.owner, 'special_abilities') and 
            self.owner.special_abilities and 
            isinstance(self.owner.special_abilities, (list, tuple)) and
            'burning_attack' in self.owner.special_abilities):
            return True
        
        return False
    
    def _apply_weapon_knockback_on_hit(self, target, game_map, entities):
        """Apply knockback to target if attacker is using a knockback weapon.
        
        Weapon knockback delivery (player + monsters):
        - Apply only on successful hit (caller is inside hit branch)
        - Execute knockback via knockback_service (canonical movement execution)
        - Works for both player and monsters (no faction gating)
        
        Args:
            target: Entity that was hit
            game_map: Game map for terrain checks
            entities: List of all entities for blocking checks
        
        Returns:
            List of result dictionaries with knockback messages and effects
        """
        results = []
        
        equipment = self._get_equipment(self.owner)
        if not equipment or not equipment.main_hand or not getattr(equipment.main_hand, 'equippable', None):
            return results
        
        equippable = equipment.main_hand.equippable
        has_knockback = getattr(equippable, 'applies_knockback_on_hit', False)
        
        if not has_knockback:
            return results
        
        # Execute knockback directly
        from services.knockback_service import apply_knockback
        knockback_results = apply_knockback(
            attacker=self.owner,
            defender=target,
            game_map=game_map,
            entities=entities
        )
        results.extend(knockback_results)
        
        return results
    
    def _has_engulf_ability(self):
        """Check if this entity has engulf ability.
        
        Phase 19: Slime Engulf - Slimes can engulf targets on hit.
        
        Returns:
            bool: True if entity can engulf
        """
        # Check if entity has special_abilities with engulf
        if (hasattr(self.owner, 'special_abilities') and 
            self.owner.special_abilities and 
            isinstance(self.owner.special_abilities, (list, tuple)) and
            'engulf' in self.owner.special_abilities):
            return True
        
        return False
    
    def _corrode_weapon(self, target):
        """Corrode target's equipped weapon.
        
        Phase 19: Only corrodes METAL weapons. Reduces damage in small steps
        but clamps at 50% of base effectiveness.
        
        Args:
            target: Entity whose weapon to corrode
            
        Returns:
            list: List of result dictionaries with corrosion messages
        """
        results = []
        
        target_equipment = self._get_equipment(target)
        if target_equipment and target_equipment.main_hand and target_equipment.main_hand.equippable:
            weapon = target_equipment.main_hand
            equippable = weapon.equippable
            
            # Phase 19: Only corrode metal weapons
            if not equippable.material or equippable.material.lower() != "metal":
                return results  # Non-metal weapons are immune
            
            # Calculate 50% floor based on base damage
            base_damage_max = equippable.base_damage_max
            damage_floor = max(1, int(base_damage_max * 0.5))  # 50% of base, minimum 1
            
            # Only corrode if current damage is above the floor
            if equippable.damage_max > damage_floor:
                equippable.damage_max -= 1
                
                # Show current condition (optional: could show percentage)
                condition_pct = int((equippable.damage_max / base_damage_max) * 100)
                condition_note = f" [{condition_pct}%]" if condition_pct < 100 else ""
                
                results.append({
                    'message': MB.custom(
                        f'The {self.owner.name} corrodes {target.name}\'s {weapon.name}{condition_note}!',
                        MB.ORANGE
                    )
                })
        
        return results
    
    def _corrode_armor(self, target):
        """Corrode target's equipped armor.
        
        Args:
            target: Entity whose armor to corrode
            
        Returns:
            list: List of result dictionaries with corrosion messages
        """
        results = []
        
        target_equipment = self._get_equipment(target)
        if target_equipment and target_equipment.off_hand and target_equipment.off_hand.equippable:
            armor = target_equipment.off_hand
            equippable = armor.equippable
            
            # Only corrode if max defense is greater than min defense
            if equippable.defense_max > equippable.defense_min:
                equippable.defense_max -= 1
                
                results.append({
                    'message': MB.custom(
                        f'{target.name}\'s {armor.name} is corroded by acid!',
                        MB.ORANGE
                    )
                })
        
        return results
    
    def _check_command_the_dead_aura(self, entities=None) -> int:
        """Phase 19: Check if attacker benefits from Lich's Command the Dead aura.
        
        Command the Dead: Allied undead within radius 6 of a living lich get +1 to-hit.
        
        Defensive checks to prevent accidental player buffing:
        - Attacker must be undead faction
        - Attacker must have AI component (player never has AI)
        - Lich must be alive
        - Lich faction must match attacker faction
        - Distance <= 6
        
        Args:
            entities: Optional list of all entities (for finding liches)
                     If None, will be retrieved from game state
        
        Returns:
            int: +1 if undead attacker is within aura range of allied lich, 0 otherwise
        """
        # DEFENSE 1: Only applies to undead faction attackers
        attacker_faction = getattr(self.owner, 'faction', None)
        if attacker_faction != 'undead':
            return 0
        
        # DEFENSE 2: Must have AI component (player never has AI)
        # This is the primary player-exclusion check
        attacker_ai = self.owner.get_component_optional(ComponentType.AI)
        if not attacker_ai:
            return 0
        
        # Get entities list (either passed in or from game state)
        if entities is None:
            try:
                from state_management.state_manager import get_state_manager
                state_manager = get_state_manager()
                if not state_manager or not state_manager.state:
                    return 0  # Fail closed: no entities = no buff
                entities = state_manager.state.entities
            except Exception as e:
                # FAIL CLOSED: If we can't access game state, don't buff
                logger.debug(f"Command the Dead: Failed to get entities, returning 0: {e}")
                return 0
        
        if not entities:
            return 0  # Fail closed: no entities = no buff
        
        # Look for allied liches within radius 6
        command_radius = 6
        
        for entity in entities:
            # Skip self (lich doesn't buff itself)
            if entity == self.owner:
                continue
            
            # Check if entity is a lich (by AI type)
            ai = entity.get_component_optional(ComponentType.AI)
            if not ai:
                continue
            
            from components.ai.lich_ai import LichAI
            if not isinstance(ai, LichAI):
                continue
            
            # Check if lich is alive
            fighter = entity.get_component_optional(ComponentType.FIGHTER)
            if not fighter or fighter.hp <= 0:
                continue
            
            # Check faction match (both must be undead)
            lich_faction = getattr(entity, 'faction', None)
            if lich_faction != 'undead' or lich_faction != attacker_faction:
                continue
            
            # Check distance
            import math
            distance = math.sqrt((entity.x - self.owner.x)**2 + (entity.y - self.owner.y)**2)
            if distance <= command_radius:
                # Within aura range!
                logger.debug(f"Command the Dead: {self.owner.name} gets +1 to-hit from {entity.name}")
                return 1
        
        return 0  # No lich found in range
    
    def _apply_special_ammo_effects(self, target):
        """Apply special ammo rider effects on successful ranged hit (Phase 22.2.2).
        
        If attacker has special ammo loaded in quiver, apply the ammo-specific
        effect to the target (e.g., burning, poison).
        
        Only called on HIT (not miss). Consumption happens separately.
        
        Args:
            target: The entity that was hit
            
        Returns:
            list: List of result dictionaries with effect messages
        """
        results = []
        
        # Only apply if attacker has equipment component
        equipment = self._get_equipment(self.owner)
        if not equipment or not equipment.quiver:
            return results
        
        # Get loaded ammo
        ammo = equipment.quiver
        effect_type = getattr(ammo, 'ammo_effect_type', None)
        
        if not effect_type:
            return results  # No effect to apply
        
        # Get effect parameters
        effect_duration = getattr(ammo, 'ammo_effect_duration', 0)
        effect_damage_dice = getattr(ammo, 'ammo_effect_damage_dice', None)
        effect_chance = getattr(ammo, 'ammo_effect_chance', 1.0)  # Phase 22.2.3
        
        # Phase 22.2.3: Roll for effect chance (deterministic via seeded RNG)
        import random
        if random.random() >= effect_chance:
            # Effect didn't trigger
            return results
        
        # Apply effect based on type
        if effect_type == 'burning':
            from components.status_effects import BurningEffect, StatusEffectManager
            from message_builder import MessageBuilder as MB
            
            # Ensure target has status_effects component
            if not target.components.has(ComponentType.STATUS_EFFECTS):
                target.status_effects = StatusEffectManager(target)
                target.components.add(ComponentType.STATUS_EFFECTS, target.status_effects)
            
            # Create burning effect (Phase 22.2.2: 1 dmg/turn for 3 turns)
            burning = BurningEffect(
                duration=effect_duration,
                owner=target,
                damage_per_turn=1  # Tuned to match existing burning norms
            )
            
            # Apply to target
            target.status_effects.add_effect(burning)
            
            results.append({
                "message": MB.custom(f"🔥 {target.name} is set ablaze by the fire arrow!", MB.ORANGE)
            })
            
            # Track metric
            collector = _get_metrics_collector()
            if collector:
                collector.increment('special_ammo_effects_applied')
        
        elif effect_type == 'entangled':
            # Phase 22.2.3: Net Arrow - apply entangled effect
            from components.status_effects import EntangledEffect, StatusEffectManager
            from message_builder import MessageBuilder as MB
            
            # Ensure target has status_effects component
            if not target.components.has(ComponentType.STATUS_EFFECTS):
                target.status_effects = StatusEffectManager(target)
                target.components.add(ComponentType.STATUS_EFFECTS, target.status_effects)
            
            # Create entangled effect
            entangled = EntangledEffect(
                duration=effect_duration,
                owner=target
            )
            
            # Apply to target
            target.status_effects.add_effect(entangled)
            
            results.append({
                "message": MB.custom(f"🕸️ {target.name} is snared by the net arrow!", (139, 90, 43))
            })
            
            # Track metric
            collector = _get_metrics_collector()
            if collector:
                collector.increment('special_ammo_effects_applied')
        
        # TODO: Add other effect types (poison, etc.) as needed
        
        return results
    
    def _consume_special_ammo(self):
        """Consume 1 special ammo from quiver on ranged attack (Phase 22.2.2).
        
        Called after hit/miss determination, consumes 1 ammo regardless of outcome.
        If ammo quantity reaches 0, automatically unequip from quiver.
        
        Returns:
            list: List of result dictionaries with consumption messages
        """
        results = []
        
        # Only consume if attacker has equipment component
        equipment = self._get_equipment(self.owner)
        if not equipment or not equipment.quiver:
            return results  # No ammo loaded
        
        # Get loaded ammo
        ammo = equipment.quiver
        
        # Check if ammo has item component with quantity
        if not ammo.item or not hasattr(ammo.item, 'quantity'):
            return results  # Not a stackable item
        
        # Consume 1 ammo
        ammo.item.quantity -= 1
        
        # Track metric
        collector = _get_metrics_collector()
        if collector:
            collector.increment('special_ammo_shots_fired')
        
        from message_builder import MessageBuilder as MB
        
        if ammo.item.quantity <= 0:
            # Out of ammo - unequip from quiver
            equipment.quiver = None
            
            # Remove from inventory if present
            if self.owner and hasattr(self.owner, 'inventory'):
                inventory = self.owner.get_component_optional(ComponentType.INVENTORY)
                if inventory and ammo in inventory.items:
                    inventory.items.remove(ammo)
            
            results.append({
                "message": MB.warning(f"⚠️ Out of {ammo.name}!")
            })
        else:
            # Still have ammo remaining
            results.append({
                "message": MB.info(f"({ammo.item.quantity} {ammo.name} remaining)")
            })
        
        return results