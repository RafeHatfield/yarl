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

    Attributes:
        base_max_hp (int): Base maximum health points
        hp (int): Current health points
        base_defense (int): Base defense value
        base_power (int): Base attack power
        xp (int): Experience points earned
        owner (Entity): The entity that owns this component
    """

    def __init__(self, hp, defense, power, xp=0, damage_min=0, damage_max=0):
        """Initialize a Fighter component.

        Args:
            hp (int): Maximum health points
            defense (int): Defense value
            power (int): Attack power
            xp (int, optional): Starting experience points. Defaults to 0.
            damage_min (int, optional): Minimum base damage (fists/natural attacks). Defaults to 0.
            damage_max (int, optional): Maximum base damage (fists/natural attacks). Defaults to 0.
        """
        self.base_max_hp = hp
        self.hp = hp
        self.base_defense = defense
        self.base_power = power
        self.xp = xp
        self.damage_min = damage_min
        self.damage_max = damage_max
        self.owner = None  # Will be set by Entity when component is registered

    @property
    def max_hp(self):
        """Get maximum HP including equipment bonuses.

        Returns:
            int: Maximum health points including equipment bonuses
        """
        if self.owner and self.owner.equipment:
            bonus = self.owner.equipment.max_hp_bonus
        else:
            bonus = 0

        return self.base_max_hp + bonus

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
