"""Unit tests for Phase 19 Orc Chieftain identity mechanics.

Tests:
1. Rally Cry triggers when enough allies are nearby
2. Rally applies +to-hit and +damage buffs to orc allies
3. Rally cleanses fear/morale debuffs from allies
4. Rally sets AI directive for allies to prioritize chieftain's target
5. Rally ends when chieftain takes damage (any damage)
6. Rally only triggers once
7. Sonic Bellow triggers exactly once at <50% HP
8. Sonic Bellow applies -to-hit debuff to player for 2 turns
9. Hang-back AI: chieftain prefers non-adjacent moves when allies can attack
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from components.ai.orc_chieftain_ai import OrcChieftainAI
from components.status_effects import RallyBuffEffect, SonicBellowDebuffEffect, StatusEffectManager
from components.fighter import Fighter
from components.component_registry import ComponentType, ComponentRegistry


class TestRallyBuffEffect:
    """Test Rally Buff status effect."""
    
    def test_rally_buff_creation(self):
        """Test creating a rally buff effect."""
        owner = Mock()
        owner.name = "Orc Warrior"
        
        rally_buff = RallyBuffEffect(
            duration=9999,
            owner=owner,
            chieftain_id=12345,
            to_hit_bonus=1,
            damage_bonus=1
        )
        
        assert rally_buff.name == "rally_buff"
        assert rally_buff.duration == 9999
        assert rally_buff.chieftain_id == 12345
        assert rally_buff.to_hit_bonus == 1
        assert rally_buff.damage_bonus == 1
    
    def test_rally_buff_apply(self):
        """Test applying rally buff (should not spam messages)."""
        owner = Mock()
        owner.name = "Orc Warrior"
        
        rally_buff = RallyBuffEffect(
            duration=9999,
            owner=owner,
            chieftain_id=12345
        )
        
        results = rally_buff.apply()
        assert rally_buff.is_active
        # Should not add per-orc messages (chieftain message is enough)
        assert len(results) == 0
    
    def test_rally_buff_remove_clears_directive(self):
        """Test removing rally buff clears AI directive."""
        owner = Mock()
        owner.name = "Orc Warrior"
        owner.ai = Mock()
        owner.ai.rally_directive_target_id = 99999
        
        rally_buff = RallyBuffEffect(
            duration=9999,
            owner=owner,
            chieftain_id=12345
        )
        rally_buff.is_active = True
        
        results = rally_buff.remove()
        assert not rally_buff.is_active
        assert owner.ai.rally_directive_target_id is None


class TestSonicBellowDebuffEffect:
    """Test Sonic Bellow debuff status effect."""
    
    def test_sonic_bellow_creation(self):
        """Test creating a sonic bellow debuff."""
        owner = Mock()
        owner.name = "Player"
        
        bellow_debuff = SonicBellowDebuffEffect(
            duration=2,
            owner=owner,
            to_hit_penalty=1
        )
        
        assert bellow_debuff.name == "sonic_bellow_debuff"
        assert bellow_debuff.duration == 2
        assert bellow_debuff.to_hit_penalty == 1
    
    def test_sonic_bellow_apply(self):
        """Test applying sonic bellow debuff shows message."""
        owner = Mock()
        owner.name = "Player"
        
        bellow_debuff = SonicBellowDebuffEffect(
            duration=2,
            owner=owner,
            to_hit_penalty=1
        )
        
        results = bellow_debuff.apply()
        assert bellow_debuff.is_active
        assert len(results) == 1
        assert 'message' in results[0]
    
    def test_sonic_bellow_remove(self):
        """Test removing sonic bellow debuff shows recovery message."""
        owner = Mock()
        owner.name = "Player"
        
        bellow_debuff = SonicBellowDebuffEffect(
            duration=2,
            owner=owner
        )
        bellow_debuff.is_active = True
        
        results = bellow_debuff.remove()
        assert not bellow_debuff.is_active
        assert len(results) == 1
        assert 'message' in results[0]


class TestOrcChieftainAI:
    """Test Orc Chieftain AI behavior."""
    
    def create_mock_entity(self, name, x, y, faction="orc", hp=30, max_hp=30):
        """Helper to create a mock entity."""
        entity = Mock()
        entity.name = name
        entity.x = x
        entity.y = y
        
        # Fighter component
        fighter = Mock()
        fighter.hp = hp
        fighter.max_hp = max_hp
        entity.fighter = fighter
        
        # Faction component
        faction_comp = Mock()
        faction_comp.faction_name = faction
        
        # Component registry
        components = Mock(spec=ComponentRegistry)
        components.has = Mock(return_value=True)
        entity.components = components
        
        # Component access
        def get_component_optional(comp_type):
            if comp_type == ComponentType.FIGHTER:
                return fighter
            elif comp_type == ComponentType.FACTION:
                return faction_comp
            elif comp_type == ComponentType.STATUS_EFFECTS:
                status_mgr = Mock(spec=StatusEffectManager)
                status_mgr.has_effect = Mock(return_value=False)
                status_mgr.add_effect = Mock(return_value=[])
                status_mgr.remove_effect = Mock(return_value=[])
                return status_mgr
            return None
        
        entity.get_component_optional = get_component_optional
        entity.chebyshev_distance_to = Mock(return_value=5)
        
        return entity
    
    def test_rally_trigger_with_enough_allies(self):
        """Test rally triggers when enough allies are nearby."""
        # Create chieftain
        chieftain = self.create_mock_entity("Orc Chieftain", 10, 10)
        chieftain.rally_radius = 5
        chieftain.rally_min_allies = 2
        chieftain.rally_hit_bonus = 1
        chieftain.rally_damage_bonus = 1
        chieftain.rally_cleanses_tags = ['fear']
        
        # Create AI
        ai = OrcChieftainAI()
        ai.owner = chieftain
        
        # Create allies within radius
        ally1 = self.create_mock_entity("Orc 1", 12, 10)
        ally2 = self.create_mock_entity("Orc 2", 11, 11)
        ally3 = self.create_mock_entity("Orc 3", 9, 9)
        
        # Add AI to allies
        for ally in [ally1, ally2, ally3]:
            ally.ai = Mock()
        
        # Create target (player)
        target = self.create_mock_entity("Player", 5, 10, faction="player")
        
        entities = [chieftain, ally1, ally2, ally3, target]
        
        # Check rally trigger
        results = ai._check_rally_trigger(entities, target)
        
        # Rally should trigger
        assert len(results) > 0
        assert ai.has_rallied
        assert ai.rally_active
        assert len(ai.rallied_orc_ids) == 3
    
    def test_rally_does_not_trigger_without_enough_allies(self):
        """Test rally does not trigger without enough allies."""
        # Create chieftain
        chieftain = self.create_mock_entity("Orc Chieftain", 10, 10)
        chieftain.rally_radius = 5
        chieftain.rally_min_allies = 2
        
        # Create AI
        ai = OrcChieftainAI()
        ai.owner = chieftain
        
        # Create only 1 ally (not enough)
        ally1 = self.create_mock_entity("Orc 1", 12, 10)
        
        # Create target (player)
        target = self.create_mock_entity("Player", 5, 10, faction="player")
        
        entities = [chieftain, ally1, target]
        
        # Check rally trigger
        results = ai._check_rally_trigger(entities, target)
        
        # Rally should NOT trigger
        assert len(results) == 0
        assert not ai.has_rallied
        assert not ai.rally_active
    
    def test_rally_only_triggers_once(self):
        """Test rally only triggers once."""
        # Create chieftain
        chieftain = self.create_mock_entity("Orc Chieftain", 10, 10)
        chieftain.rally_radius = 5
        chieftain.rally_min_allies = 2
        chieftain.rally_hit_bonus = 1
        chieftain.rally_damage_bonus = 1
        chieftain.rally_cleanses_tags = []
        
        # Create AI
        ai = OrcChieftainAI()
        ai.owner = chieftain
        
        # Create allies
        ally1 = self.create_mock_entity("Orc 1", 12, 10)
        ally2 = self.create_mock_entity("Orc 2", 11, 11)
        
        # Add AI to allies
        for ally in [ally1, ally2]:
            ally.ai = Mock()
        
        # Create target
        target = self.create_mock_entity("Player", 5, 10, faction="player")
        
        entities = [chieftain, ally1, ally2, target]
        
        # First trigger
        results1 = ai._check_rally_trigger(entities, target)
        assert len(results1) > 0
        assert ai.has_rallied
        
        # Second attempt (should not trigger)
        results2 = ai._check_rally_trigger(entities, target)
        assert len(results2) == 0
    
    def test_sonic_bellow_triggers_below_50_percent_hp(self):
        """Test sonic bellow triggers when HP drops below 50%."""
        # Create chieftain
        chieftain = self.create_mock_entity("Orc Chieftain", 10, 10, hp=15, max_hp=35)
        chieftain.bellow_hp_threshold = 0.5
        chieftain.bellow_to_hit_penalty = 1
        chieftain.bellow_duration = 2
        
        # Create AI
        ai = OrcChieftainAI()
        ai.owner = chieftain
        
        # Create target (player)
        target = self.create_mock_entity("Player", 5, 10, faction="player")
        target_status_effects = Mock(spec=StatusEffectManager)
        target_status_effects.add_effect = Mock(return_value=[])
        target.get_component_optional = Mock(return_value=target_status_effects)
        
        # Check bellow trigger
        results = ai._check_sonic_bellow_trigger(target)
        
        # Bellow should trigger
        assert len(results) > 0
        assert ai.has_bellowed
        target_status_effects.add_effect.assert_called_once()
    
    def test_sonic_bellow_does_not_trigger_above_50_percent_hp(self):
        """Test sonic bellow does not trigger above 50% HP."""
        # Create chieftain with HP above threshold
        chieftain = self.create_mock_entity("Orc Chieftain", 10, 10, hp=20, max_hp=35)
        chieftain.bellow_hp_threshold = 0.5
        
        # Create AI
        ai = OrcChieftainAI()
        ai.owner = chieftain
        
        # Create target
        target = self.create_mock_entity("Player", 5, 10, faction="player")
        
        # Check bellow trigger
        results = ai._check_sonic_bellow_trigger(target)
        
        # Bellow should NOT trigger
        assert len(results) == 0
        assert not ai.has_bellowed
    
    def test_sonic_bellow_only_triggers_once(self):
        """Test sonic bellow only triggers once."""
        # Create chieftain below threshold
        chieftain = self.create_mock_entity("Orc Chieftain", 10, 10, hp=10, max_hp=35)
        chieftain.bellow_hp_threshold = 0.5
        chieftain.bellow_to_hit_penalty = 1
        chieftain.bellow_duration = 2
        
        # Create AI
        ai = OrcChieftainAI()
        ai.owner = chieftain
        
        # Create target
        target = self.create_mock_entity("Player", 5, 10, faction="player")
        target_status_effects = Mock(spec=StatusEffectManager)
        target_status_effects.add_effect = Mock(return_value=[])
        target.get_component_optional = Mock(return_value=target_status_effects)
        
        # First trigger
        results1 = ai._check_sonic_bellow_trigger(target)
        assert len(results1) > 0
        assert ai.has_bellowed
        
        # Second attempt (should not trigger)
        results2 = ai._check_sonic_bellow_trigger(target)
        assert len(results2) == 0


class TestRallyBreakOnDamage:
    """Test rally ends when chieftain takes damage."""
    
    def test_rally_ends_when_chieftain_damaged(self):
        """Test rally ends immediately when chieftain takes damage."""
        # Create chieftain with rally active
        chieftain = Mock()
        chieftain.name = "Orc Chieftain"
        
        # Create AI with active rally
        ai = Mock()
        ai.rally_active = True
        ai.in_combat = False
        
        # Create fighter
        fighter = Fighter(hp=35, defense=0, power=2)
        fighter.owner = chieftain
        
        # Mock component access
        components = Mock()
        components.has = Mock(return_value=True)
        chieftain.components = components
        
        # Mock equipment (no rings)
        equipment = Mock()
        equipment.left_ring = None
        equipment.right_ring = None
        chieftain.equipment = equipment
        
        def get_component_optional(comp_type):
            if comp_type == ComponentType.AI:
                return ai
            elif comp_type == ComponentType.STATISTICS:
                return None
            elif comp_type == ComponentType.EQUIPMENT:
                return equipment
            return None
        
        chieftain.get_component_optional = get_component_optional
        
        # Take damage
        results = fighter.take_damage(5)
        
        # Rally should be marked as ended
        assert not ai.rally_active
        # Results should include end_rally flag
        end_rally_result = next((r for r in results if r.get('end_rally')), None)
        assert end_rally_result is not None
        assert end_rally_result['chieftain_id'] == id(chieftain)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])



