"""Unit tests for Phase 10.1: Wire-Up & Surfacing.

Tests cover:
- Reanimation processing in environment system
- Faction selection for aggravation scroll
- Plague spread on plague_zombie attacks
- Loot tags for new items
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from components.faction import Faction
from components.component_registry import ComponentType


class TestReanimationProcessing:
    """Tests for reanimation processing in environment system."""
    
    def test_process_pending_reanimations_decrements_timer(self):
        """Reanimation timer should decrement each turn."""
        from death_functions import process_pending_reanimations
        
        # Create a corpse with pending reanimation
        corpse = Mock()
        corpse.name = "remains of Orc"
        corpse._pending_reanimation = {
            'corpse_x': 5,
            'corpse_y': 5,
            'revenant_stats': {
                'max_hp': 40,
                'hp': 40,
                'damage_min': 3,
                'damage_max': 4,
                'accuracy': 1,
                'evasion': 0,
                'defense': 0,
                'power': 0,
                'original_name': 'Orc',
            },
            'reanimate_in_turns': 3
        }
        
        entities = [corpse]
        
        # Process one turn
        results = process_pending_reanimations(entities, None, 0)
        
        # Timer should have decremented
        assert corpse._pending_reanimation['reanimate_in_turns'] == 2
        # No reanimation yet
        assert len(results) == 0
    
    def test_process_pending_reanimations_creates_revenant(self):
        """Revenant should spawn when timer reaches zero."""
        from death_functions import process_pending_reanimations
        
        # Create a corpse with timer at 1 (will trigger this turn)
        corpse = Mock()
        corpse.name = "remains of Orc"
        corpse._pending_reanimation = {
            'corpse_x': 5,
            'corpse_y': 5,
            'revenant_stats': {
                'max_hp': 40,
                'hp': 40,
                'damage_min': 3,
                'damage_max': 4,
                'accuracy': 1,
                'evasion': 0,
                'defense': 0,
                'power': 0,
                'original_name': 'Orc',
            },
            'reanimate_in_turns': 1
        }
        
        entities = [corpse]
        
        # Process one turn - should trigger reanimation
        results = process_pending_reanimations(entities, None, 0)
        
        # Should have a result with new entity
        assert len(results) == 1
        assert 'new_entity' in results[0]
        assert 'message' in results[0]
        
        # Reanimation data should be cleared
        assert not hasattr(corpse, '_pending_reanimation')
    
    def test_entities_without_reanimation_ignored(self):
        """Entities without _pending_reanimation should be ignored."""
        from death_functions import process_pending_reanimations
        
        # Create a normal entity (no pending reanimation)
        entity = Mock(spec=['x', 'y', 'name'])
        entity.name = "Orc"
        
        entities = [entity]
        
        results = process_pending_reanimations(entities, None, 0)
        
        # No results
        assert len(results) == 0


class TestFactionSelectionHandling:
    """Tests for faction selection in aggravation scroll."""
    
    def test_aggravation_returns_faction_options(self):
        """Scroll should return faction options when multiple factions present."""
        from item_functions import use_aggravation_scroll
        
        # Create caster (player)
        caster = Mock()
        caster.faction = Faction.PLAYER
        
        # Create target orc
        target = Mock()
        target.x, target.y = 5, 5
        target.name = "Orc"
        target.faction = Faction.ORC_FACTION
        target.get_component_optional = Mock(return_value=Mock(hp=20))
        
        # Create nearby undead
        zombie = Mock()
        zombie.x, zombie.y = 6, 6
        zombie.faction = Faction.UNDEAD
        zombie.get_component_optional = Mock(return_value=Mock(hp=25))
        
        # Create nearby cultist
        cultist = Mock()
        cultist.x, cultist.y = 7, 7
        cultist.faction = Faction.CULTIST
        cultist.get_component_optional = Mock(return_value=Mock(hp=30))
        
        entities = [caster, target, zombie, cultist]
        
        # Mock FOV to return True for all positions
        fov_map = Mock()
        
        with patch('item_functions.map_is_in_fov', return_value=True):
            results = use_aggravation_scroll(
                caster,
                entities=entities,
                fov_map=fov_map,
                target_x=5,
                target_y=5
            )
        
        # Should return requires_faction_selection
        assert any(r.get('requires_faction_selection') for r in results)
        
        # Should include faction options
        faction_result = next(r for r in results if r.get('requires_faction_selection'))
        assert 'faction_options' in faction_result
        assert len(faction_result['faction_options']) >= 2  # At least UNDEAD and CULTIST + PLAYER
    
    def test_aggravation_auto_selects_single_faction(self):
        """Scroll should auto-select when only one faction available."""
        from item_functions import use_aggravation_scroll
        from components.status_effects import StatusEffectManager
        
        # Create caster (player)
        caster = Mock()
        caster.faction = Faction.PLAYER
        
        # Create target orc with proper component system
        target = Mock()
        target.x, target.y = 5, 5
        target.name = "Orc"
        target.faction = Faction.ORC_FACTION
        
        fighter = Mock()
        fighter.hp = 20
        
        # Set up components properly
        target.components = Mock()
        target.components.has = Mock(return_value=False)
        target.components.add = Mock()
        target.status_effects = None
        
        def get_component_optional(comp_type):
            if comp_type == ComponentType.AI:
                return Mock()
            if comp_type == ComponentType.FIGHTER:
                return fighter
            if comp_type == ComponentType.STATUS_EFFECTS:
                return target.status_effects
            return None
        
        target.get_component_optional = get_component_optional
        
        entities = [caster, target]
        
        fov_map = Mock()
        
        with patch('item_functions.map_is_in_fov', return_value=True):
            results = use_aggravation_scroll(
                caster,
                entities=entities,
                fov_map=fov_map,
                target_x=5,
                target_y=5
            )
        
        # Should NOT require faction selection (only PLAYER available, auto-selected)
        assert not any(r.get('requires_faction_selection') for r in results)
        # Should have consumed the scroll
        assert any(r.get('consumed') for r in results)


class TestPlagueSpreadOnAttack:
    """Tests for plague spread on plague_zombie melee attacks."""
    
    def test_has_plague_attack_ability_with_special_abilities(self):
        """Entity with plague_attack in special_abilities should return True."""
        from components.fighter import Fighter
        
        owner = Mock()
        owner.special_abilities = ['swarm', 'plague_attack']
        owner.tags = None
        
        fighter = Fighter(hp=20, defense=0, power=0)
        fighter.owner = owner
        
        assert fighter._has_plague_attack_ability() is True
    
    def test_has_plague_attack_ability_with_tags(self):
        """Entity with plague_carrier tag should return True."""
        from components.fighter import Fighter
        
        owner = Mock()
        owner.special_abilities = None
        owner.tags = ['corporeal_flesh', 'undead', 'plague_carrier']
        
        fighter = Fighter(hp=20, defense=0, power=0)
        fighter.owner = owner
        
        assert fighter._has_plague_attack_ability() is True
    
    def test_has_plague_attack_ability_without_ability(self):
        """Entity without plague_attack should return False."""
        from components.fighter import Fighter
        
        owner = Mock()
        owner.special_abilities = ['swarm']
        owner.tags = ['corporeal_flesh']
        
        fighter = Fighter(hp=20, defense=0, power=0)
        fighter.owner = owner
        
        assert fighter._has_plague_attack_ability() is False
    
    def test_plague_spread_chance(self):
        """Plague should spread with 25% chance on successful attack."""
        from components.fighter import Fighter
        
        # Create plague zombie attacker
        attacker_owner = Mock()
        attacker_owner.name = "Plague Zombie"
        attacker_owner.special_abilities = ['plague_attack']
        attacker_owner.tags = ['plague_carrier']
        
        attacker = Fighter(hp=30, defense=0, power=0)
        attacker.owner = attacker_owner
        
        # Create corporeal target
        target = Mock()
        target.name = "Orc"
        target.faction = Faction.ORC_FACTION
        target.tags = None
        target.get_component_optional = Mock(return_value=None)  # No status effects yet
        
        # Force random to be below 0.25 (plague spreads)
        with patch('components.fighter.random.random', return_value=0.10):
            with patch('item_functions._is_corporeal_flesh', return_value=True):
                with patch('item_functions.apply_plague_effect', return_value=[]) as mock_apply:
                    results = attacker._apply_plague_spread(target)
                    
                    # Should have called apply_plague_effect with target as keyword arg
                    mock_apply.assert_called_once_with(attacker_owner, target=target)
                    
                    # Should have a message about plague spread
                    assert len(results) >= 1
    
    def test_plague_no_spread_above_chance(self):
        """Plague should not spread when random is above 25%."""
        from components.fighter import Fighter
        
        # Create plague zombie attacker
        attacker_owner = Mock()
        attacker_owner.name = "Plague Zombie"
        attacker_owner.special_abilities = ['plague_attack']
        attacker_owner.tags = ['plague_carrier']
        
        attacker = Fighter(hp=30, defense=0, power=0)
        attacker.owner = attacker_owner
        
        # Create corporeal target
        target = Mock()
        target.name = "Orc"
        target.faction = Faction.ORC_FACTION
        target.tags = None
        target.get_component_optional = Mock(return_value=None)
        
        # Force random to be above 0.25 (plague does not spread)
        with patch('components.fighter.random.random', return_value=0.50):
            with patch('item_functions._is_corporeal_flesh', return_value=True):
                results = attacker._apply_plague_spread(target)
                
                # No results (plague didn't spread)
                assert len(results) == 0


class TestNewItemLootTags:
    """Tests for new items in loot bands."""
    
    def test_aggravation_scroll_has_loot_tags(self):
        """Aggravation scroll should be registered in loot tags."""
        from balance.loot_tags import get_loot_tags
        
        tags = get_loot_tags("aggravation_scroll")
        
        assert tags is not None
        assert tags.has_category("utility")
        assert tags.band_min >= 3  # Mid-game or later
    
    def test_plague_scroll_has_loot_tags(self):
        """Plague scroll should be registered in loot tags."""
        from balance.loot_tags import get_loot_tags
        
        tags = get_loot_tags("plague_scroll")
        
        assert tags is not None
        assert tags.has_category("utility") or tags.has_category("offensive")
        assert tags.band_min >= 4  # Late game only
    
    def test_antidote_potion_has_loot_tags(self):
        """Antidote potion should be registered in loot tags."""
        from balance.loot_tags import get_loot_tags
        
        tags = get_loot_tags("antidote_potion")
        
        assert tags is not None
        assert tags.has_category("utility") or tags.has_category("healing")
        assert tags.band_min >= 3  # Available where plague sources exist
    
    def test_new_items_available_in_late_game(self):
        """New Phase 10 items should be available in band 5."""
        from balance.loot_tags import get_items_for_band
        
        band_5_items = get_items_for_band(5)
        
        assert "aggravation_scroll" in band_5_items
        assert "plague_scroll" in band_5_items
        assert "antidote_potion" in band_5_items


class TestEnvironmentSystemReanimation:
    """Tests for reanimation processing in environment system."""
    
    def test_environment_system_has_reanimation_method(self):
        """EnvironmentSystem should have _process_reanimations method."""
        from engine.systems.environment_system import EnvironmentSystem
        
        system = EnvironmentSystem()
        
        assert hasattr(system, '_process_reanimations')
        assert callable(system._process_reanimations)
    
    def test_process_calls_reanimation_processing(self):
        """EnvironmentSystem.process should call reanimation processing."""
        from engine.systems.environment_system import EnvironmentSystem
        
        system = EnvironmentSystem()
        
        # Create mock game state
        game_state = Mock()
        game_state.entities = []
        game_state.game_map = Mock()
        game_state.message_log = Mock()
        game_state.turn_number = 0
        
        # Process should call _process_reanimations
        with patch.object(system, '_process_hazards'):
            with patch.object(system, '_process_reanimations') as mock_reanimate:
                system.process(game_state)
                
                mock_reanimate.assert_called_once_with(game_state)
