import logging
from game_messages import Message
from config.testing_config import is_testing_mode

# Set up combat debug logger
combat_logger = logging.getLogger('combat_debug')
combat_logger.setLevel(logging.DEBUG)


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
        
        if self.owner and hasattr(self.owner, 'equipment') and self.owner.equipment:
            equipment = self.owner.equipment
            for item in [equipment.main_hand, equipment.off_hand, 
                        equipment.head, equipment.chest, equipment.feet]:
                if item and hasattr(item, 'equippable'):
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

        return self.base_max_hp + self.constitution_mod + equipment_bonus

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

        Args:
            amount (int): Amount of damage to apply

        Returns:
            list: List of result dictionaries, may include 'dead' and 'xp' keys
        """
        results = []

        self.hp -= amount

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
        self.hp += amount

        if self.hp > self.max_hp:
            self.hp = self.max_hp

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
                "message": Message(message_text, (255, 255, 255))
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
                "message": Message(message_text, (255, 255, 255))
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
        if self.owner and hasattr(self.owner, 'equipment') and self.owner.equipment:
            if self.owner.equipment.main_hand and hasattr(self.owner.equipment.main_hand, 'equippable'):
                weapon_bonus = getattr(self.owner.equipment.main_hand.equippable, 'to_hit_bonus', 0)
        
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
                    "message": Message(message_text, (255, 215, 0))  # Gold color for crits
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
                    "message": Message(message_text, (255, 255, 255))
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
        else:
            # Miss
            if is_fumble:
                message_text = "FUMBLE! {0} attacks {1} - complete miss!".format(
                    self.owner.name.capitalize(),
                    target.name
                )
                results.append({
                    "message": Message(message_text, (200, 200, 200))  # Gray for fumble
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
                    "message": Message(message_text, (180, 180, 180))
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
        if damage_source == "weapon" and (hasattr(self.owner, 'equipment') and self.owner.equipment and
            self.owner.equipment.main_hand and self.owner.equipment.main_hand.equippable):
            equip = self.owner.equipment.main_hand.equippable
            if equip.damage_min > 0 and equip.damage_max > 0:
                damage_range = f" ({equip.damage_min}-{equip.damage_max} dmg)"
        elif damage_source == "base" and self.damage_min > 0 and self.damage_max > 0:
            # Base damage range (fists/natural attacks)
            damage_range = f" ({self.damage_min}-{self.damage_max} dmg)"
        
        armor_range = ""
        if (hasattr(target, 'equipment') and target.equipment and
            target.equipment.off_hand and target.equipment.off_hand.equippable):
            equip = target.equipment.off_hand.equippable
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
        if (hasattr(self.owner, 'equipment') and self.owner.equipment and
            self.owner.equipment.main_hand and 
            self.owner.equipment.main_hand.equippable):
            return self.owner.equipment.main_hand.equippable.roll_damage()
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
            if (hasattr(self.owner, 'equipment') and self.owner.equipment and
                hasattr(self.owner.equipment, 'off_hand') and self.owner.equipment.off_hand and 
                hasattr(self.owner.equipment.off_hand, 'equippable') and
                self.owner.equipment.off_hand.equippable):
                return self.owner.equipment.off_hand.equippable.roll_defense()
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
        if hasattr(self.owner, 'faction'):
            from components.faction import Faction
            return self.owner.faction == Faction.HOSTILE_ALL
        
        return False
    
    def _corrode_weapon(self, target):
        """Corrode target's equipped weapon.
        
        Args:
            target: Entity whose weapon to corrode
            
        Returns:
            list: List of result dictionaries with corrosion messages
        """
        results = []
        
        if (hasattr(target, 'equipment') and target.equipment and 
            target.equipment.main_hand and target.equipment.main_hand.equippable):
            
            weapon = target.equipment.main_hand
            equippable = weapon.equippable
            
            # Only corrode if max damage is greater than min damage
            if equippable.damage_max > equippable.damage_min:
                equippable.damage_max -= 1
                
                from game_messages import Message
                results.append({
                    'message': Message(
                        f'The {self.owner.name} corrodes {target.name}\'s {weapon.name}!',
                        color=(255, 165, 0)  # Orange warning
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
        
        if (hasattr(target, 'equipment') and target.equipment and 
            target.equipment.off_hand and target.equipment.off_hand.equippable):
            
            armor = target.equipment.off_hand
            equippable = armor.equippable
            
            # Only corrode if max defense is greater than min defense
            if equippable.defense_max > equippable.defense_min:
                equippable.defense_max -= 1
                
                from game_messages import Message
                results.append({
                    'message': Message(
                        f'{target.name}\'s {armor.name} is corroded by acid!',
                        color=(255, 165, 0)  # Orange warning
                    )
                })
        
        return results
