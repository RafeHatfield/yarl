import logging
import random
from game_messages import Message
from message_builder import MessageBuilder as MB
from config.testing_config import is_testing_mode
from visual_effects import show_hit, show_miss
from components.component_registry import ComponentType

# Set up combat debug logger
combat_logger = logging.getLogger('combat_debug')
combat_logger.setLevel(logging.DEBUG)

# General logger for this module
logger = logging.getLogger(__name__)



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
                 strength=10, dexterity=10, constitution=10):
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
        """Get strength modifier.
        
        Returns:
            int: Strength modifier
        """
        return self.get_stat_modifier(self.strength)
    
    @property
    def dexterity_mod(self):
        """Get dexterity modifier.
        
        Returns:
            int: Dexterity modifier
        """
        return self.get_stat_modifier(self.dexterity)
    
    @property
    def constitution_mod(self):
        """Get constitution modifier.
        
        Returns:
            int: Constitution modifier
        """
        return self.get_stat_modifier(self.constitution)
    
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
            return entity.get_component_optional(ComponentType.EQUIPMENT)
        
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
        
        return base_ac + dex_bonus + armor_ac_bonus

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

    def take_damage(self, amount):
        """Apply damage to this fighter.

        Reduces current HP by the damage amount. If HP drops to 0 or below,
        marks the fighter as dead and returns XP reward information.
        
        For bosses, also checks for enrage and low HP dialogue triggers.

        Args:
            amount (int): Amount of damage to apply

        Returns:
            list: List of result dictionaries, may include 'dead', 'xp', 'message' keys
        """
        results = []

        self.hp -= amount
        
        # Record damage taken (only for player)
        statistics = self.owner.get_component_optional(ComponentType.STATISTICS) if self.owner else None
        if statistics:
            statistics.record_damage_taken(amount)
        
        # Flag monster as "in combat" when attacked (stops looting behavior)
        ai = self.owner.get_component_optional(ComponentType.AI) if self.owner else None
        if not ai and self.owner:
            # Fallback to direct attribute access for backward compatibility
            ai = getattr(self.owner, 'ai', None)
        if ai and hasattr(ai, 'in_combat'):
            ai.in_combat = True
        
        # Check for boss dialogue triggers (if not dead yet)
        if self.hp > 0:
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

        if self.hp <= 0:
            results.append({"dead": self.owner, "xp": self.xp})
            # Note: HP can go negative for XP calculation purposes, but should be
            # displayed as 0 in UI. The UI layer should handle the display clamping.

        return results

    def heal(self, amount):
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

    def attack(self, target):
        """Perform an attack against a target entity.

        Calculates damage based on attacker's power vs target's defense,
        including variable damage from equipped weapons and variable defense from armor.

        Args:
            target (Entity): The target entity to attack

        Returns:
            list: List of result dictionaries with combat messages and effects
        """
        results = []

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
        
        # Get variable armor defense from target
        armor_defense = target.fighter._get_armor_defense()
        
        # Apply defense (including base defense, equipment defense_bonus, and variable armor)
        total_defense = target.fighter.defense + armor_defense
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
                defense_breakdown = f"{total_defense} defense ({target.fighter.defense} base + {armor_defense} armor)"
            
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
            
            results.extend(target.fighter.take_damage(final_damage))
            
            # Apply corrosion effects if attacker has corrosion ability
            corrosion_results = self._apply_corrosion_effects(target, final_damage)
            results.extend(corrosion_results)
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
                defense_breakdown = f"{total_defense} defense ({target.fighter.defense} base + {armor_defense} armor)"
            
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
    
    def attack_d20(self, target):
        """Perform a d20-based attack against a target entity.
        
        New combat system:
        - Roll d20 + DEX modifier + weapon to-hit bonus
        - Compare to target's AC (10 + DEX mod + armor AC)
        - Natural 20 = critical hit (double damage)
        - Natural 1 = fumble (auto-miss)
        - On hit: Roll weapon damage + STR modifier
        
        Args:
            target (Entity): The target entity to attack
            
        Returns:
            list: List of result dictionaries with combat messages and effects
        """
        import random
        from game_messages import Message
        
        results = []
        
        # Roll d20 for attack
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
        target_ac = target.fighter.armor_class
        
        # Check for critical hit or fumble
        is_critical = (d20_roll == 20)
        is_fumble = (d20_roll == 1)
        
        # Determine if attack hits
        hit = False
        if is_critical:
            hit = True  # Natural 20 always hits
        elif is_fumble:
            hit = False  # Natural 1 always misses
        else:
            hit = (attack_roll >= target_ac)
        
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
            results.extend(target.fighter.take_damage(damage))
            
            # Apply corrosion effects if applicable
            corrosion_results = self._apply_corrosion_effects(target, damage)
            results.extend(corrosion_results)
            
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
                     f"{target_name} [def:{target.fighter.base_defense}+{target.fighter.defense-target.fighter.base_defense}]{armor_range} blocks {total_defense} "
                     f"({target.fighter.defense} defense + {armor_defense} rolled) "
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
        
        # 5% chance to corrode equipment on successful hit
        if random.random() < 0.05:
            # Corrode target's weapon (when slime hits player/monster)
            weapon_corrosion = self._corrode_weapon(target)
            results.extend(weapon_corrosion)
            
            # Corrode attacker's "armor" (when player/monster hits slime)
            # Note: This is a bit of a stretch since slimes don't wear armor,
            # but it represents acid splash-back from hitting the slime
            armor_corrosion = self._corrode_armor(self.owner)
            results.extend(armor_corrosion)
        
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
    
    def _corrode_weapon(self, target):
        """Corrode target's equipped weapon.
        
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
            
            # Only corrode if max damage is greater than min damage
            if equippable.damage_max > equippable.damage_min:
                equippable.damage_max -= 1
                
                results.append({
                    'message': MB.custom(
                        f'The {self.owner.name} corrodes {target.name}\'s {weapon.name}!',
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
