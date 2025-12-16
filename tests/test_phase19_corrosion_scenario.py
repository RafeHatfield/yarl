"""Phase 19 Corrosion scenario tests - Deterministic validation.

These tests verify the Phase 19 Corrosive Contact system:
- Only metal weapons corrode
- Non-metal weapons are immune
- Corrosion is bounded at 50% of base damage
- System is deterministic under seeded runs
"""

import pytest
from unittest.mock import patch

from entity import Entity
from components.fighter import Fighter
from components.equipment import Equipment
from components.equippable import Equippable
from components.faction import Faction
from equipment_slots import EquipmentSlots
from render_functions import RenderOrder


class TestPhase19CorrosionScenario:
    """Scenario tests for Phase 19 corrosion mechanics."""
    
    def test_metal_weapon_corrodes_to_floor(self):
        """Test that a metal weapon corrodes down to 50% base but not further."""
        # Create slime with corrosion
        slime = Entity(
            x=5, y=5, char='s', color=(0, 255, 0), name='Slime',
            blocks=True, render_order=RenderOrder.ACTOR, faction=Faction.HOSTILE_ALL,
            fighter=Fighter(hp=15, defense=0, power=5, xp=25, damage_min=1, damage_max=3)
        )
        slime.special_abilities = ['corrosion']
        
        # Create player with metal sword (base 1-8 damage)
        player = Entity(
            x=3, y=3, char='@', color=(255, 255, 255), name='Player',
            blocks=True, render_order=RenderOrder.ACTOR, faction=Faction.PLAYER,
            fighter=Fighter(hp=100, defense=0, power=0, xp=0),
            equipment=Equipment()
        )
        
        longsword = Entity(
            x=0, y=0, char='/', color=(192, 192, 192), name='Longsword',
            equippable=Equippable(
                EquipmentSlots.MAIN_HAND,
                damage_min=1,
                damage_max=8,
                material="metal"
            )
        )
        player.equipment.toggle_equip(longsword)
        
        # Base damage is 8, floor is 50% = 4
        base_max = longsword.equippable.base_damage_max
        assert base_max == 8
        floor = max(1, int(base_max * 0.5))
        assert floor == 4
        
        # Corrode weapon multiple times (should stop at floor)
        with patch('random.random', return_value=0.01):  # Always trigger corrosion
            corrosion_count = 0
            
            # Corrode down to floor
            for _ in range(10):  # More than enough to hit floor
                with patch.object(player.fighter, 'take_damage', return_value=[]):
                    results = slime.fighter.attack(player)
                    
                    # Check if corrosion happened
                    messages = [r.get('message') for r in results if 'message' in r]
                    corrosion_messages = [m for m in messages if m and 'corrodes' in m.text]
                    if corrosion_messages:
                        corrosion_count += 1
                
                # Should not go below floor
                assert longsword.equippable.damage_max >= floor
            
            # Verify we hit the floor
            assert longsword.equippable.damage_max == floor
            # Verify we corroded at least once
            assert corrosion_count > 0
    
    def test_wooden_weapon_immune_to_corrosion(self):
        """Test that wooden weapons are immune to acid corrosion."""
        # Create slime with corrosion
        slime = Entity(
            x=5, y=5, char='s', color=(0, 255, 0), name='Slime',
            blocks=True, render_order=RenderOrder.ACTOR, faction=Faction.HOSTILE_ALL,
            fighter=Fighter(hp=15, defense=0, power=5, xp=25, damage_min=1, damage_max=3)
        )
        slime.special_abilities = ['corrosion']
        
        # Create player with wooden club
        player = Entity(
            x=3, y=3, char='@', color=(255, 255, 255), name='Player',
            blocks=True, render_order=RenderOrder.ACTOR, faction=Faction.PLAYER,
            fighter=Fighter(hp=100, defense=0, power=0, xp=0),
            equipment=Equipment()
        )
        
        wooden_club = Entity(
            x=0, y=0, char=')', color=(101, 67, 33), name='Wooden Club',
            equippable=Equippable(
                EquipmentSlots.MAIN_HAND,
                damage_min=1,
                damage_max=6,
                material="wood"
            )
        )
        player.equipment.toggle_equip(wooden_club)
        
        initial_max = wooden_club.equippable.damage_max
        
        # Try to corrode wooden weapon many times
        with patch('random.random', return_value=0.01):  # Always trigger corrosion check
            for _ in range(20):  # Many attempts
                with patch.object(player.fighter, 'take_damage', return_value=[]):
                    results = slime.fighter.attack(player)
                    
                    # Check for corrosion messages
                    messages = [r.get('message') for r in results if 'message' in r]
                    corrosion_messages = [m for m in messages if m and 'corrodes' in m.text]
                    # Should never corrode wood
                    assert len(corrosion_messages) == 0
        
        # Weapon should still have original damage
        assert wooden_club.equippable.damage_max == initial_max
    
    def test_metal_vs_wood_side_by_side(self):
        """Test metal and wooden weapons side by side for comparison."""
        # Create slime
        slime = Entity(
            x=5, y=5, char='s', color=(0, 255, 0), name='Slime',
            blocks=True, render_order=RenderOrder.ACTOR, faction=Faction.HOSTILE_ALL,
            fighter=Fighter(hp=100, defense=0, power=5, xp=25, damage_min=1, damage_max=3)
        )
        slime.special_abilities = ['corrosion']
        
        # Player with metal sword
        player_metal = Entity(
            x=3, y=3, char='@', color=(255, 255, 255), name='Player Metal',
            blocks=True, render_order=RenderOrder.ACTOR, faction=Faction.PLAYER,
            fighter=Fighter(hp=100, defense=0, power=0, xp=0),
            equipment=Equipment()
        )
        metal_sword = Entity(
            x=0, y=0, char='/', color=(192, 192, 192), name='Metal Sword',
            equippable=Equippable(EquipmentSlots.MAIN_HAND, damage_min=2, damage_max=8, material="metal")
        )
        player_metal.equipment.toggle_equip(metal_sword)
        
        # Player with wooden spear
        player_wood = Entity(
            x=4, y=4, char='@', color=(255, 255, 255), name='Player Wood',
            blocks=True, render_order=RenderOrder.ACTOR, faction=Faction.PLAYER,
            fighter=Fighter(hp=100, defense=0, power=0, xp=0),
            equipment=Equipment()
        )
        wooden_spear = Entity(
            x=0, y=0, char='/', color=(160, 82, 45), name='Wooden Spear',
            equippable=Equippable(EquipmentSlots.MAIN_HAND, damage_min=2, damage_max=8, material="wood")
        )
        player_wood.equipment.toggle_equip(wooden_spear)
        
        # Force corrosion
        with patch('random.random', return_value=0.01):
            # Attack metal player - should corrode
            with patch.object(player_metal.fighter, 'take_damage', return_value=[]):
                results_metal = slime.fighter.attack(player_metal)
                corrosion_metal = [r for r in results_metal if 'message' in r and 'corrodes' in r['message'].text]
                assert len(corrosion_metal) == 1
                assert metal_sword.equippable.damage_max == 7  # Corroded from 8 to 7
            
            # Attack wood player - should NOT corrode
            with patch.object(player_wood.fighter, 'take_damage', return_value=[]):
                results_wood = slime.fighter.attack(player_wood)
                corrosion_wood = [r for r in results_wood if 'message' in r and 'corrodes' in r['message'].text]
                assert len(corrosion_wood) == 0
                assert wooden_spear.equippable.damage_max == 8  # Unchanged
    
    def test_deterministic_under_seed(self):
        """Test that corrosion is deterministic under fixed seed."""
        import random
        
        def run_corrosion_sequence(seed):
            """Run a sequence of attacks with fixed seed."""
            random.seed(seed)
            
            # Create entities
            slime = Entity(
                x=5, y=5, char='s', color=(0, 255, 0), name='Slime',
                blocks=True, render_order=RenderOrder.ACTOR, faction=Faction.HOSTILE_ALL,
                fighter=Fighter(hp=15, defense=0, power=5, xp=25, damage_min=1, damage_max=3)
            )
            slime.special_abilities = ['corrosion']
            
            player = Entity(
                x=3, y=3, char='@', color=(255, 255, 255), name='Player',
                blocks=True, render_order=RenderOrder.ACTOR, faction=Faction.PLAYER,
                fighter=Fighter(hp=100, defense=0, power=0, xp=0),
                equipment=Equipment()
            )
            
            sword = Entity(
                x=0, y=0, char='/', color=(192, 192, 192), name='Sword',
                equippable=Equippable(EquipmentSlots.MAIN_HAND, damage_min=4, damage_max=7, material="metal")
            )
            player.equipment.toggle_equip(sword)
            
            # Run 50 attacks
            corrosion_events = []
            with patch.object(player.fighter, 'take_damage', return_value=[]):
                for i in range(50):
                    results = slime.fighter.attack(player)
                    messages = [r.get('message') for r in results if 'message' in r]
                    if any(m and 'corrodes' in m.text for m in messages):
                        corrosion_events.append(i)
            
            return corrosion_events, sword.equippable.damage_max
        
        # Run twice with same seed
        events1, damage1 = run_corrosion_sequence(12345)
        events2, damage2 = run_corrosion_sequence(12345)
        
        # Should be identical
        assert events1 == events2
        assert damage1 == damage2
        
        # Run with different seed - should be different
        events3, damage3 = run_corrosion_sequence(54321)
        # Very unlikely to be identical (but not impossible)
        # Just verify it runs without error
        assert isinstance(events3, list)
        assert isinstance(damage3, int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

