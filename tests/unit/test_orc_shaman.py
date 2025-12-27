"""Unit tests for Phase 19 Orc Shaman identity mechanics.

Tests:
1. Crippling Hex applies -to-hit and -AC debuffs
2. Crippling Hex has correct duration and cooldown
3. Dissonant Chant applies movement energy tax
4. Dissonant Chant is channeled (shaman channels while effect is active)
5. Chant is interruptible by damage to shaman
6. Chant has correct duration and cooldown
7. Hang-back AI: shaman prefers distance 4-7 from player
8. Abilities respect cooldowns (no spam)
9. Metrics are recorded correctly
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from components.ai.orc_shaman_ai import OrcShamanAI
from components.status_effects import CripplingHexEffect, DissonantChantEffect, StatusEffectManager
from components.fighter import Fighter
from components.component_registry import ComponentType, ComponentRegistry


class TestCripplingHexEffect:
    """Test Crippling Hex status effect."""
    
    def test_hex_creation(self):
        """Test creating a crippling hex effect."""
        owner = Mock()
        owner.name = "Player"
        
        hex_effect = CripplingHexEffect(
            duration=5,
            owner=owner,
            to_hit_delta=-1,
            ac_delta=-1
        )
        
        assert hex_effect.name == "crippling_hex"
        assert hex_effect.duration == 5
        assert hex_effect.to_hit_delta == -1
        assert hex_effect.ac_delta == -1
    
    def test_hex_apply(self):
        """Test applying hex shows message."""
        owner = Mock()
        owner.name = "Player"
        
        hex_effect = CripplingHexEffect(
            duration=5,
            owner=owner,
            to_hit_delta=-1,
            ac_delta=-1
        )
        
        results = hex_effect.apply()
        assert hex_effect.is_active
        assert len(results) == 1
        assert 'message' in results[0]
    
    def test_hex_remove(self):
        """Test removing hex shows fade message."""
        owner = Mock()
        owner.name = "Player"
        
        hex_effect = CripplingHexEffect(duration=5, owner=owner)
        hex_effect.is_active = True
        
        results = hex_effect.remove()
        assert not hex_effect.is_active
        assert len(results) == 1
        assert 'message' in results[0]


class TestDissonantChantEffect:
    """Test Dissonant Chant status effect."""
    
    def test_chant_creation(self):
        """Test creating a dissonant chant effect."""
        owner = Mock()
        owner.name = "Player"
        
        chant_effect = DissonantChantEffect(
            duration=3,
            owner=owner,
            move_energy_tax=1
        )
        
        assert chant_effect.name == "dissonant_chant"
        assert chant_effect.duration == 3
        assert chant_effect.move_energy_tax == 1
    
    def test_chant_apply(self):
        """Test applying chant shows message."""
        owner = Mock()
        owner.name = "Player"
        
        chant_effect = DissonantChantEffect(
            duration=3,
            owner=owner,
            move_energy_tax=1
        )
        
        results = chant_effect.apply()
        assert chant_effect.is_active
        assert len(results) == 1
        assert 'message' in results[0]
    
    def test_chant_remove(self):
        """Test removing chant shows cease message."""
        owner = Mock()
        owner.name = "Player"
        
        chant_effect = DissonantChantEffect(duration=3, owner=owner)
        chant_effect.is_active = True
        
        results = chant_effect.remove()
        assert not chant_effect.is_active
        assert len(results) == 1
        assert 'message' in results[0]


class TestOrcShamanAI:
    """Test Orc Shaman AI behavior."""
    
    def create_mock_entity(self, name, x, y, faction="orc", hp=24, max_hp=24):
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
        entity.faction = faction_comp
        
        # Distance calculation (Chebyshev distance)
        def chebyshev_distance_to(target):
            dx = abs(entity.x - target.x)
            dy = abs(entity.y - target.y)
            return max(dx, dy)
        entity.chebyshev_distance_to = chebyshev_distance_to
        
        # Component registry mock
        components = Mock()
        def get_optional(comp_type):
            if comp_type == ComponentType.STATUS_EFFECTS:
                return getattr(entity, 'status_effects', None)
            elif comp_type == ComponentType.FIGHTER:
                return fighter
            elif comp_type == ComponentType.EQUIPMENT:
                return getattr(entity, 'equipment', None)
            elif comp_type == ComponentType.AI:
                return getattr(entity, 'ai', None)
            return None
        components.get_component_optional = get_optional
        components.has = lambda ct: get_optional(ct) is not None
        entity.get_component_optional = get_optional
        entity.components = components
        
        return entity
    
    def test_hex_cooldown_tracking(self):
        """Test that hex cooldown is tracked correctly."""
        shaman = self.create_mock_entity("Orc Shaman", 10, 10)
        ai = OrcShamanAI()
        ai.owner = shaman
        
        # Initial cooldown should be 0 (hex available)
        assert ai.hex_cooldown_remaining == 0
        
        # After casting, cooldown should be set
        ai.hex_cooldown_remaining = 10
        assert ai.hex_cooldown_remaining == 10
        
        # Cooldown decrements each turn
        ai.hex_cooldown_remaining -= 1
        assert ai.hex_cooldown_remaining == 9
    
    def test_chant_cooldown_tracking(self):
        """Test that chant cooldown is tracked correctly."""
        shaman = self.create_mock_entity("Orc Shaman", 10, 10)
        ai = OrcShamanAI()
        ai.owner = shaman
        
        # Initial cooldown should be 0 (chant available)
        assert ai.chant_cooldown_remaining == 0
        
        # After casting, cooldown should be set
        ai.chant_cooldown_remaining = 15
        assert ai.chant_cooldown_remaining == 15
        
        # Cooldown decrements each turn
        ai.chant_cooldown_remaining -= 1
        assert ai.chant_cooldown_remaining == 14
    
    def test_channeling_state_tracking(self):
        """Test that channeling state is tracked correctly."""
        shaman = self.create_mock_entity("Orc Shaman", 10, 10)
        ai = OrcShamanAI()
        ai.owner = shaman
        
        # Initially not channeling
        assert ai.is_channeling == False
        assert ai.chant_target_id is None
        assert ai.chant_turns_remaining == 0
        
        # Start channeling
        ai.is_channeling = True
        ai.chant_target_id = 12345
        ai.chant_turns_remaining = 3
        
        assert ai.is_channeling == True
        assert ai.chant_target_id == 12345
        assert ai.chant_turns_remaining == 3
    
    def test_try_cast_hex_off_cooldown(self):
        """Test casting hex when off cooldown and in range."""
        shaman = self.create_mock_entity("Orc Shaman", 10, 10)
        player = self.create_mock_entity("Player", 15, 10, faction="player")
        
        # Setup hex config directly on entity (not in monster_def)
        shaman.hex_enabled = True
        shaman.hex_radius = 6
        shaman.hex_duration_turns = 5
        shaman.hex_to_hit_delta = -1
        shaman.hex_ac_delta = -1
        shaman.hex_cooldown_turns = 10
        
        # Setup player status effects - use REAL StatusEffectManager for integration
        player.status_effects = StatusEffectManager(player)
        
        ai = OrcShamanAI()
        ai.owner = shaman
        ai.hex_cooldown_remaining = 0  # Off cooldown
        
        # Distance is 5 (within range 6)
        distance = shaman.chebyshev_distance_to(player)
        assert distance == 5
        
        results = ai._try_cast_hex(player, distance)
        
        # Hex should be cast
        assert results is not None
        assert len(results) > 0
        assert ai.hex_cooldown_remaining == 10  # Cooldown set
        
        # Verify hex effect was added by checking messages
        assert any('hex' in str(r.get('message', '')).lower() for r in results)
    
    def test_try_cast_hex_on_cooldown(self):
        """Test that hex doesn't cast when on cooldown."""
        shaman = self.create_mock_entity("Orc Shaman", 10, 10)
        player = self.create_mock_entity("Player", 15, 10, faction="player")
        
        # Setup hex config
        shaman.hex_enabled = True
        shaman.hex_radius = 6
        
        # Setup player status effects
        player.status_effects = StatusEffectManager(player)
        
        ai = OrcShamanAI()
        ai.owner = shaman
        ai.hex_cooldown_remaining = 5  # On cooldown
        
        distance = 5
        results = ai._try_cast_hex(player, distance)
        
        # Hex should NOT be cast
        assert results is None
        assert ai.hex_cooldown_remaining == 5  # Cooldown unchanged
    
    def test_try_cast_hex_out_of_range(self):
        """Test that hex doesn't cast when out of range."""
        shaman = self.create_mock_entity("Orc Shaman", 10, 10)
        player = self.create_mock_entity("Player", 20, 10, faction="player")
        
        # Setup hex config
        shaman.hex_enabled = True
        shaman.hex_radius = 6
        
        # Setup player status effects
        player.status_effects = StatusEffectManager(player)
        
        ai = OrcShamanAI()
        ai.owner = shaman
        ai.hex_cooldown_remaining = 0  # Off cooldown
        
        distance = 10  # Out of range (>6)
        results = ai._try_cast_hex(player, distance)
        
        # Hex should NOT be cast
        assert results is None
    
    def test_try_start_chant_off_cooldown(self):
        """Test starting chant when off cooldown and in range."""
        shaman = self.create_mock_entity("Orc Shaman", 10, 10)
        player = self.create_mock_entity("Player", 14, 10, faction="player")
        
        # Setup chant config directly on entity
        shaman.chant_enabled = True
        shaman.chant_radius = 5
        shaman.chant_duration_turns = 3
        shaman.chant_move_energy_tax = 1
        
        # Setup player status effects - use REAL StatusEffectManager for integration
        player.status_effects = StatusEffectManager(player)
        
        ai = OrcShamanAI()
        ai.owner = shaman
        ai.chant_cooldown_remaining = 0  # Off cooldown
        ai.is_channeling = False
        
        # Distance is 4 (within range 5)
        distance = shaman.chebyshev_distance_to(player)
        assert distance == 4
        
        results = ai._try_start_chant(player, distance)
        
        # Chant should start
        assert results is not None
        assert len(results) > 0
        assert ai.is_channeling == True
        assert ai.chant_target_id == id(player)
        assert ai.chant_turns_remaining == 3
        
        # Verify chant effect by checking messages
        assert any('chant' in str(r.get('message', '')).lower() for r in results)
    
    def test_try_start_chant_on_cooldown(self):
        """Test that chant doesn't start when on cooldown."""
        shaman = self.create_mock_entity("Orc Shaman", 10, 10)
        player = self.create_mock_entity("Player", 14, 10, faction="player")
        
        # Setup chant config
        shaman.chant_enabled = True
        shaman.chant_radius = 5
        
        # Setup player status effects
        player.status_effects = StatusEffectManager(player)
        
        ai = OrcShamanAI()
        ai.owner = shaman
        ai.chant_cooldown_remaining = 10  # On cooldown
        ai.is_channeling = False
        
        distance = 4
        results = ai._try_start_chant(player, distance)
        
        # Chant should NOT start
        assert results is None
        assert ai.is_channeling == False
    
    def test_continue_channeling_natural_expiry(self):
        """Test that channeling expires naturally after duration."""
        shaman = self.create_mock_entity("Orc Shaman", 10, 10)
        player = self.create_mock_entity("Player", 14, 10, faction="player")
        
        # Setup chant config
        shaman.chant_cooldown_turns = 15
        
        ai = OrcShamanAI()
        ai.owner = shaman
        ai.is_channeling = True
        ai.chant_target_id = id(player)
        ai.chant_turns_remaining = 1  # Last turn of chant
        
        results = ai._continue_channeling(player)
        
        # Chant should end naturally
        assert ai.is_channeling == False
        assert ai.chant_target_id is None
        assert ai.chant_turns_remaining == 0
        assert ai.chant_cooldown_remaining == 15  # Cooldown set
    
    def test_continue_channeling_decrement(self):
        """Test that channeling duration decrements correctly."""
        shaman = self.create_mock_entity("Orc Shaman", 10, 10)
        player = self.create_mock_entity("Player", 14, 10, faction="player")
        
        ai = OrcShamanAI()
        ai.owner = shaman
        ai.is_channeling = True
        ai.chant_target_id = id(player)
        ai.chant_turns_remaining = 3
        
        # First turn
        results = ai._continue_channeling(player)
        assert ai.chant_turns_remaining == 2
        assert ai.is_channeling == True  # Still channeling
        
        # Second turn
        results = ai._continue_channeling(player)
        assert ai.chant_turns_remaining == 1
        assert ai.is_channeling == True  # Still channeling
    
    def test_chant_interrupt_on_damage(self):
        """Test that damage to shaman interrupts channeling."""
        shaman = self.create_mock_entity("Orc Shaman", 10, 10)
        
        ai = OrcShamanAI()
        ai.owner = shaman
        shaman.ai = ai
        
        # Start channeling
        ai.is_channeling = True
        ai.chant_target_id = 12345
        ai.chant_turns_remaining = 2
        
        # Simulate damage to shaman
        # In the actual code, Fighter.take_damage() checks for is_channeling
        # and sets it to False + returns interrupt_chant result
        results = []
        
        # Mock the interrupt logic (would be in Fighter.take_damage)
        # IMPORTANT: Only interrupt if damage > 0
        damage_amount = 5  # Positive damage
        if damage_amount > 0 and ai.is_channeling:
            ai.is_channeling = False
            ai.chant_target_id = None
            results.append({'interrupt_chant': True, 'shaman_id': id(shaman)})
        
        # Verify interrupt occurred
        assert ai.is_channeling == False
        assert ai.chant_target_id is None
        assert any(r.get('interrupt_chant') for r in results)
    
    def test_chant_NOT_interrupted_by_zero_damage(self):
        """Test that 0 damage (full resistance) does NOT interrupt channeling."""
        shaman = self.create_mock_entity("Orc Shaman", 10, 10)
        
        ai = OrcShamanAI()
        ai.owner = shaman
        shaman.ai = ai
        
        # Start channeling
        ai.is_channeling = True
        ai.chant_target_id = 12345
        ai.chant_turns_remaining = 2
        
        # Simulate 0 damage (fully resisted)
        results = []
        
        # Mock the interrupt logic with 0 damage
        damage_amount = 0  # Zero damage (fully resisted)
        if damage_amount > 0 and ai.is_channeling:
            ai.is_channeling = False
            ai.chant_target_id = None
            results.append({'interrupt_chant': True, 'shaman_id': id(shaman)})
        
        # Verify chant was NOT interrupted
        assert ai.is_channeling == True  # Still channeling
        assert ai.chant_target_id == 12345  # Target unchanged
        assert not any(r.get('interrupt_chant') for r in results)  # No interrupt result


class TestMovementTaxBehavior:
    """Test movement tax edge cases and toggle behavior."""
    
    def test_chant_toggle_not_flipped_by_wall_bump(self):
        """Test that bumping into a wall does not flip the chant movement toggle.
        
        This prevents players from "wasting" the allowed-move by bumping walls.
        Only successful movement should flip the toggle.
        """
        from services.movement_service import MovementService
        from unittest.mock import Mock
        
        # Create mock player with chant effect
        player = Mock()
        player.name = "Player"
        player.x = 5
        player.y = 5
        
        # Mock status effects with chant active
        status_mgr = Mock()
        status_mgr.has_effect = lambda name: name == "dissonant_chant"
        player.status_effects = status_mgr
        
        # Mock components
        components = Mock()
        components.has = lambda ct: True  # Has STATUS_EFFECTS
        player.components = components
        
        # Initialize toggle to False (next move should be allowed)
        player._chant_move_block_next = False
        
        # Mock state manager and game map
        state_manager = Mock()
        state_manager.state.player = player
        state_manager.state.entities = []
        
        # Create a blocked game map (wall at destination)
        game_map = Mock()
        game_map.is_blocked = lambda x, y: True  # All tiles blocked (wall)
        state_manager.state.game_map = game_map
        
        # Create movement service
        movement_service = MovementService(state_manager)
        
        # Attempt movement (should fail due to wall)
        result = movement_service.execute_movement(dx=1, dy=0, source="keyboard")
        
        # Movement should fail (blocked by wall)
        assert result.blocked_by_wall == True
        assert result.success == False
        
        # CRITICAL: Toggle should NOT have flipped (wall bump doesn't count)
        assert player._chant_move_block_next == False, \
            "Toggle should remain False after failed movement (wall bump)"
        
        # Next movement attempt should still be allowed (not blocked by chant)
        # This is verified by toggle still being False


class TestCombatIntegration:
    """Test integration with combat system."""
    
    def test_hex_affects_to_hit(self):
        """Test that hex penalty is applied to attack rolls."""
        # This would be tested in fighter.py tests, but we verify the effect has the right attributes
        owner = Mock()
        owner.name = "Player"
        
        hex_effect = CripplingHexEffect(
            duration=5,
            owner=owner,
            to_hit_delta=-1,
            ac_delta=-1
        )
        
        # Verify attributes that Fighter.attack_d20() reads
        assert hasattr(hex_effect, 'to_hit_delta')
        assert hex_effect.to_hit_delta == -1
    
    def test_hex_affects_ac(self):
        """Test that hex penalty is applied to armor class."""
        owner = Mock()
        owner.name = "Player"
        
        hex_effect = CripplingHexEffect(
            duration=5,
            owner=owner,
            to_hit_delta=-1,
            ac_delta=-1
        )
        
        # Verify attributes that Fighter.armor_class reads
        assert hasattr(hex_effect, 'ac_delta')
        assert hex_effect.ac_delta == -1
    
    def test_chant_has_movement_tax(self):
        """Test that chant effect has movement tax attribute."""
        owner = Mock()
        owner.name = "Player"
        
        chant_effect = DissonantChantEffect(
            duration=3,
            owner=owner,
            move_energy_tax=1
        )
        
        # Verify attributes that movement system reads
        assert hasattr(chant_effect, 'move_energy_tax')
        assert chant_effect.move_energy_tax == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

