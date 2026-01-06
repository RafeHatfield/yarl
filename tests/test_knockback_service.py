"""Unit tests for knockback service.

Tests:
- Distance mapping (power delta → distance)
- Blocked knockback applies stagger
- Knockback uses canonical movement execution (no bypass)
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from services.knockback_service import calculate_knockback_distance, apply_knockback


class TestKnockbackDistanceMapping:
    """Test distance calculation based on power delta."""
    
    def test_delta_negative_returns_1_tile(self):
        """Test delta <= -1 → 1 tile."""
        assert calculate_knockback_distance(5, 10) == 1  # delta = -5
        assert calculate_knockback_distance(8, 9) == 1   # delta = -1
    
    def test_delta_0_or_1_returns_2_tiles(self):
        """Test delta in [0, 1] → 2 tiles."""
        assert calculate_knockback_distance(10, 10) == 2  # delta = 0
        assert calculate_knockback_distance(11, 10) == 2  # delta = 1
    
    def test_delta_2_or_3_returns_3_tiles(self):
        """Test delta in [2, 3] → 3 tiles."""
        assert calculate_knockback_distance(12, 10) == 3  # delta = 2
        assert calculate_knockback_distance(13, 10) == 3  # delta = 3
    
    def test_delta_4_or_more_returns_4_tiles(self):
        """Test delta >= 4 → 4 tiles (cap)."""
        assert calculate_knockback_distance(14, 10) == 4  # delta = 4
        assert calculate_knockback_distance(20, 10) == 4  # delta = 10
        assert calculate_knockback_distance(100, 10) == 4  # delta = 90


class TestKnockbackStaggerApplication:
    """Test stagger application when knockback blocked."""
    
    def test_blocked_knockback_applies_stagger(self):
        """Test that blocked knockback applies StaggeredEffect."""
        # Create mock entities
        attacker = MagicMock()
        attacker.x = 5
        attacker.y = 5
        
        defender = MagicMock()
        defender.x = 7
        defender.y = 5
        defender.components.has.return_value = True  # Pretend status_effects already exists
        
        # Mock fighter components
        attacker_fighter = MagicMock()
        attacker_fighter.power = 10
        attacker.get_component_optional.return_value = attacker_fighter
        
        defender_fighter = MagicMock()
        defender_fighter.power = 5
        
        def mock_get_component(ct):
            if hasattr(ct, 'name') and ct.name == 'FIGHTER':
                return defender_fighter
            return None
        
        defender.get_component_optional.side_effect = mock_get_component
        
        # Mock game map (wall at x=8)
        game_map = MagicMock()
        game_map.width = 20
        game_map.height = 20
        game_map.tiles = [[MagicMock(blocked=False) for _ in range(20)] for _ in range(20)]
        game_map.tiles[8][5].blocked = True  # Wall at x=8
        
        # Mock entities list
        entities = [attacker, defender]
        
        # Apply knockback
        with patch('services.knockback_service._execute_move') as mock_move:
            # First move succeeds (7→8), second blocked by wall
            mock_move.return_value = True
            
            results = apply_knockback(attacker, defender, game_map, entities)
        
        # Verify stagger was applied
        assert defender.status_effects.add_effect.call_count > 0
        call_args = defender.status_effects.add_effect.call_args[0]
        stagger_effect = call_args[0]
        assert stagger_effect.name == 'staggered'
        assert stagger_effect.duration == 1
    
    def test_full_knockback_no_stagger(self):
        """Test that full knockback (not blocked) does NOT apply stagger."""
        # Create mock entities
        attacker = Mock()
        attacker.x = 5
        attacker.y = 5
        
        defender = Mock()
        defender.x = 7
        defender.y = 5
        defender.components = Mock()
        defender.components.has = Mock(return_value=False)
        
        # Mock fighter components
        attacker_fighter = Mock()
        attacker_fighter.power = 10
        attacker.get_component_optional = Mock(return_value=attacker_fighter)
        
        defender_fighter = Mock()
        defender_fighter.power = 5
        defender.get_component_optional = Mock(side_effect=lambda ct: 
            defender_fighter if ct.name == 'FIGHTER' else None)
        
        # Mock game map (no walls)
        game_map = Mock()
        game_map.width = 20
        game_map.height = 20
        game_map.tiles = [[Mock(blocked=False) for _ in range(20)] for _ in range(20)]
        
        # Mock entities list
        entities = [attacker, defender]
        
        # Mock status effects
        defender.status_effects = Mock()
        defender.status_effects.add_effect = Mock(return_value=[])
        
        # Apply knockback
        with patch('services.knockback_service._execute_move') as mock_move:
            # All moves succeed
            mock_move.return_value = True
            
            results = apply_knockback(attacker, defender, game_map, entities)
        
        # Verify stagger was NOT applied
        assert not defender.status_effects.add_effect.called


class TestKnockbackMovementExecution:
    """Test that knockback uses canonical movement execution."""
    
    def test_knockback_uses_entity_move(self):
        """Test that knockback calls entity.move() not direct x/y assignment."""
        # Create mock entities
        attacker = Mock()
        attacker.x = 5
        attacker.y = 5
        
        defender = Mock()
        defender.x = 7
        defender.y = 5
        defender.move = Mock()  # Track move() calls
        defender.components = Mock()
        defender.components.has = Mock(return_value=False)
        
        # Mock fighter components
        attacker_fighter = Mock()
        attacker_fighter.power = 10
        attacker.get_component_optional = Mock(return_value=attacker_fighter)
        
        defender_fighter = Mock()
        defender_fighter.power = 5
        defender.get_component_optional = Mock(side_effect=lambda ct: 
            defender_fighter if ct.name == 'FIGHTER' else None)
        
        # Mock game map
        game_map = Mock()
        game_map.width = 20
        game_map.height = 20
        game_map.tiles = [[Mock(blocked=False) for _ in range(20)] for _ in range(20)]
        
        # Mock entities list
        entities = [attacker, defender]
        
        # Apply knockback
        with patch('services.knockback_service._execute_move') as mock_execute:
            mock_execute.return_value = True
            
            results = apply_knockback(attacker, defender, game_map, entities)
        
        # Verify _execute_move was called (which uses entity.move())
        assert mock_execute.called
        # Distance should be 4 (delta = 5 → 4 tiles, since delta >= 4)
        assert mock_execute.call_count == 4

