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
        
        AC = 10 + capped DEX modifier + armor AC bonus from all equipped items
        
        DEX Modifier Capping:
        - Light Armor: No cap (full DEX bonus)
        - Medium Armor: Cap at +2 DEX
        - Heavy Armor: Cap at 0 DEX (no DEX bonus!)
        - Multiple armor pieces: Use the MOST RESTRICTIVE cap
        
        Example:
            DEX 18 (+4), wearing Plate Mail (heavy, dex_cap=0):
            AC = 10 + 0 (capped) + 6 (plate) = 16
            
            DEX 18 (+4), wearing Studded Leather (light, no cap):
            AC = 10 + 4 (full) + 3 (studded) = 17
        
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
        
        # Apply status effect bonuses
        status_ac_bonus = 0
        if hasattr(self.owner, 'status_effects') and self.owner.status_effects is not None:
            # Protection: +ac_bonus to AC
            protection = self.owner.status_effects.get_effect('protection')
            if protection:
                status_ac_bonus += protection.ac_bonus
        
        # Apply ring bonuses (Ring of Protection)
        ring_ac_bonus = 0
        if equipment:
            for ring in [equipment.left_ring, equipment.right_ring]:
                if ring and ring.components.has(ComponentType.RING):
                    ring_ac_bonus += ring.ring.get_ac_bonus()
        
        return base_ac + dex_bonus + armor_ac_bonus + status_ac_bonus + ring_ac_bonus

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
    
    def attack_d20(self, target, is_surprise: bool = False):
        """Perform a d20-based attack against a target entity.
        
        New combat system:
        - Roll d20 + DEX modifier + weapon to-hit bonus
        - Compare to target's AC (10 + DEX mod + armor AC)
        - Natural 20 = critical hit (double damage)
        - Natural 1 = fumble (auto-miss)
        - On hit: Roll weapon damage + STR modifier
        
        Phase 9: Surprise attacks force critical hit for 2× damage.
        
        Args:
            target (Entity): The target entity to attack
            is_surprise (bool): If True, this is a surprise attack (forced crit, already auto-hit)
            
        Returns:
            list: List of result dictionaries with combat messages and effects
        """
        import random
        from game_messages import Message
        
        results = []
        
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
        
        # Calculate total attack roll
        attack_roll = d20_roll + to_hit_bonus + weapon_bonus
        
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
            
            # Calculate damage
            base_damage = 0
            
            # Get weapon damage or fist damage
            weapon_damage = self._get_weapon_damage()
            if weapon_damage > 0:
                base_damage = weapon_damage
            else:
                # Unarmed: use base damage range
                base_damage = self._get_base_variable_damage()
            
            # Add STR modifier to damage
            damage = base_damage + self.strength_mod
            
            # Phase 18: Apply damage type modifier (resistance/vulnerability)
            # Get weapon damage type
            weapon_damage_type = None
            if equipment and equipment.main_hand:
                weapon = equipment.main_hand
                if weapon.components.has(ComponentType.EQUIPPABLE) or hasattr(weapon, 'equippable'):
                    equippable = weapon.equippable if hasattr(weapon, 'equippable') else weapon.get_component_optional(ComponentType.EQUIPPABLE)
                    if equippable and hasattr(equippable, 'damage_type'):
                        weapon_damage_type = equippable.damage_type
            
            # Check target for resistance/vulnerability
            if weapon_damage_type:
                target_resistance = getattr(target, 'damage_resistance', None)
                target_vulnerability = getattr(target, 'damage_vulnerability', None)
                
                if target_resistance == weapon_damage_type:
                    damage = damage - 1  # Resistant: -1 damage
                elif target_vulnerability == weapon_damage_type:
                    damage = damage + 1  # Vulnerable: +1 damage
            
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
            
            # Apply damage
            results.extend(target.require_component(ComponentType.FIGHTER).take_damage(damage))
            
            # Apply corrosion effects if applicable
            corrosion_results = self._apply_corrosion_effects(target, damage)
            results.extend(corrosion_results)
            
            # Phase 19: Apply engulf effects if applicable
            engulf_results = self._apply_engulf_effects(target, damage)
            results.extend(engulf_results)
            
            # Phase 10.1: Apply plague spread if attacker has plague_attack ability
            plague_results = self._apply_plague_spread(target)
            results.extend(plague_results)
            
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
