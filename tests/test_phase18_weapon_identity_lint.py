"""Phase 18 Weapon Identity Validation Tests.

Ensures that:
1. Every weapon has at least one mechanical differentiator
2. Affix names (keen, fine, vicious, masterwork) match their mechanics
3. No "fake" affixes (name without stats)

This is a LINT test - it prevents future regression where weapons
are named with affixes but don't have the corresponding bonuses.
"""

import pytest
from config.entity_registry import load_entity_config, get_entity_registry


class TestWeaponIdentityLint:
    """Validation tests for weapon mechanical identity."""
    
    @classmethod
    def setup_class(cls):
        """Load entity config once for all tests."""
        load_entity_config()
        cls.registry = get_entity_registry()
    
    def _get_all_weapons(self):
        """Extract all weapon entities from entity registry."""
        weapons = []
        weapon_ids = self.registry.get_all_weapon_ids()
        
        for weapon_id in weapon_ids:
            weapon_def = self.registry.get_weapon(weapon_id)
            if weapon_def:
                # Convert WeaponDefinition to dict-like structure
                weapons.append((weapon_id, weapon_def))
        
        return weapons
    
    def test_all_weapons_have_mechanical_identity(self):
        """Every weapon must have at least one mechanical differentiator.
        
        Phase 18: Weapons must have at least ONE of:
        - crit_threshold < 20 (Keen weapons)
        - to_hit_bonus != 0 (Fine weapons, finesse weapons)
        - damage_dice with bonus (e.g., "1d8+1" for Vicious)
        - damage_type (slashing/piercing/bludgeoning)
        
        This prevents "fake" weapons with fancy names but no stats.
        """
        weapons = self._get_all_weapons()
        
        failing_weapons = []
        
        for weapon_id, weapon_def in weapons:
            has_identity = False
            
            # Check for crit threshold
            if hasattr(weapon_def, 'crit_threshold') and weapon_def.crit_threshold < 20:
                has_identity = True
            
            # Check for to-hit bonus
            if hasattr(weapon_def, 'to_hit_bonus') and weapon_def.to_hit_bonus != 0:
                has_identity = True
            
            # Check for damage bonus in dice notation
            damage_dice = getattr(weapon_def, 'damage_dice', '')
            if damage_dice and ('+' in damage_dice or '-' in damage_dice):
                has_identity = True
            
            # Check for damage type
            if hasattr(weapon_def, 'damage_type') and weapon_def.damage_type:
                has_identity = True
            
            # Check for reach (spear = 2)
            if hasattr(weapon_def, 'reach') and weapon_def.reach > 1:
                has_identity = True
            
            # Check for two_handed
            if hasattr(weapon_def, 'two_handed') and weapon_def.two_handed:
                has_identity = True
            
            # Check for speed bonus
            if hasattr(weapon_def, 'speed_bonus') and weapon_def.speed_bonus != 0:
                has_identity = True
            
            if not has_identity:
                failing_weapons.append(weapon_id)
        
        assert len(failing_weapons) == 0, \
            f"Weapons with no mechanical identity: {', '.join(failing_weapons)}"
    
    def test_keen_affix_has_crit_threshold(self):
        """Weapons with 'keen' in name must have crit_threshold < 20.
        
        Phase 18: Prevents fake "Keen" weapons that don't actually crit more.
        """
        weapons = self._get_all_weapons()
        
        failing_weapons = []
        
        for weapon_id, weapon_def in weapons:
            if 'keen' in weapon_id.lower():
                crit_threshold = getattr(weapon_def, 'crit_threshold', 20)
                if crit_threshold >= 20:
                    failing_weapons.append(f"{weapon_id} (crit_threshold={crit_threshold}, expected <20)")
        
        assert len(failing_weapons) == 0, \
            f"Keen weapons without expanded crit range: {', '.join(failing_weapons)}"
    
    def test_fine_affix_has_to_hit_bonus(self):
        """Weapons with 'fine' in name must have to_hit_bonus > base.
        
        Phase 18: Fine = better accuracy/craftsmanship.
        """
        weapons = self._get_all_weapons()
        
        failing_weapons = []
        
        for weapon_id, weapon_def in weapons:
            if 'fine' in weapon_id.lower():
                to_hit_bonus = getattr(weapon_def, 'to_hit_bonus', 0)
                
                # Fine weapons should have positive to-hit bonus
                # (or higher than equivalent non-fine version)
                if to_hit_bonus <= 0:
                    failing_weapons.append(f"{weapon_id} (to_hit_bonus={to_hit_bonus}, expected >0)")
        
        assert len(failing_weapons) == 0, \
            f"Fine weapons without to-hit bonus: {', '.join(failing_weapons)}"
    
    def test_vicious_affix_has_damage_bonus(self):
        """Weapons with 'vicious' in name must have damage bonus.
        
        Phase 18: Vicious = extra damage (dice notation like "1d8+1").
        """
        weapons = self._get_all_weapons()
        
        failing_weapons = []
        
        for weapon_id, weapon_def in weapons:
            if 'vicious' in weapon_id.lower():
                damage_dice = getattr(weapon_def, 'damage_dice', '')
                
                # Vicious weapons should have +N in dice notation
                if '+' not in damage_dice:
                    failing_weapons.append(f"{weapon_id} (damage_dice={damage_dice}, expected +bonus)")
        
        assert len(failing_weapons) == 0, \
            f"Vicious weapons without damage bonus: {', '.join(failing_weapons)}"
    
    def test_masterwork_affix_has_multiple_bonuses(self):
        """Weapons with 'masterwork' in name must have multiple bonuses.
        
        Phase 18: Masterwork = combined quality (hit + damage).
        """
        weapons = self._get_all_weapons()
        
        failing_weapons = []
        
        for weapon_id, weapon_def in weapons:
            if 'masterwork' in weapon_id.lower():
                to_hit_bonus = getattr(weapon_def, 'to_hit_bonus', 0)
                damage_dice = getattr(weapon_def, 'damage_dice', '')
                
                has_hit_bonus = to_hit_bonus > 0
                has_damage_bonus = '+' in damage_dice
                
                # Masterwork should have BOTH bonuses
                if not (has_hit_bonus and has_damage_bonus):
                    failing_weapons.append(
                        f"{weapon_id} (to_hit={to_hit_bonus}, damage={damage_dice}, "
                        f"expected both bonuses)"
                    )
        
        assert len(failing_weapons) == 0, \
            f"Masterwork weapons without combined bonuses: {', '.join(failing_weapons)}"


class TestDamageTypePresence:
    """Validation that damage types are properly configured."""
    
    @classmethod
    def setup_class(cls):
        """Load entity config once for all tests."""
        load_entity_config()
        cls.registry = get_entity_registry()
    
    def test_phase18_weapons_have_damage_types(self):
        """Phase 18 affixed weapons should all have damage_type.
        
        This ensures new weapons don't forget damage type annotation.
        """
        registry = self.registry
        
        # Phase 18 affixed weapons (should all have damage type)
        phase18_weapons = [
            'keen_dagger', 'keen_rapier',
            'vicious_battleaxe', 'vicious_warhammer',
            'fine_longsword', 'fine_mace',
            'masterwork_greatsword'
        ]
        
        missing_damage_type = []
        
        for weapon_id in phase18_weapons:
            weapon_def = registry.get_weapon(weapon_id)
            if weapon_def:
                if not hasattr(weapon_def, 'damage_type') or not weapon_def.damage_type:
                    missing_damage_type.append(weapon_id)
        
        assert len(missing_damage_type) == 0, \
            f"Phase 18 weapons missing damage_type: {', '.join(missing_damage_type)}"
    
    def test_damage_types_are_valid(self):
        """All damage_type values must be from allowed set.
        
        Phase 18: Only slashing, piercing, bludgeoning are valid.
        """
        registry = self.registry
        weapon_ids = registry.get_all_weapon_ids()
        
        valid_damage_types = {'slashing', 'piercing', 'bludgeoning'}
        invalid_weapons = []
        
        for weapon_id in weapon_ids:
            weapon_def = registry.get_weapon(weapon_id)
            if weapon_def:
                damage_type = getattr(weapon_def, 'damage_type', None)
                if damage_type and damage_type not in valid_damage_types:
                    invalid_weapons.append(f"{weapon_id} (damage_type={damage_type})")
        
        assert len(invalid_weapons) == 0, \
            f"Weapons with invalid damage_type: {', '.join(invalid_weapons)}"







