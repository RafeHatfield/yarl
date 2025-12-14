"""Tests for Phase 17C adaptive healing and survivability features.

Tests:
- Damage tracking and spike detection
- Adaptive heal threshold calculation
- Retreat logic (safe tile finding, retreat decisions)
- Potion conservation behavior
"""

import pytest
from unittest.mock import Mock
from collections import deque

from io_layer.bot_brain import BotBrain, _get_persona_heal_config
from components.component_registry import ComponentType


class TestDamageTracking:
    """Tests for Phase 17C damage tracking system."""
    
    def _make_player(self, hp: int, max_hp: int = 100, x: int = 5, y: int = 5) -> Mock:
        """Helper to create mock player."""
        player = Mock()
        player.x = x
        player.y = y
        fighter = Mock()
        fighter.hp = hp
        fighter.max_hp = max_hp
        player.get_component_optional = Mock(return_value=fighter)
        return player
    
    def test_damage_tracking_initializes_empty(self):
        """Damage history should start empty."""
        brain = BotBrain(persona="balanced")
        assert len(brain._damage_history) == 0
        assert brain._last_hp is None
    
    def test_damage_tracking_records_damage(self):
        """Should record damage when HP decreases."""
        brain = BotBrain(persona="balanced")
        player = self._make_player(hp=100)
        
        # First update - no history yet
        brain._update_damage_tracking(player)
        assert brain._last_hp == 100
        assert len(brain._damage_history) == 0
        
        # Take 20 damage
        player.get_component_optional().hp = 80
        brain._update_damage_tracking(player)
        assert brain._last_hp == 80
        assert len(brain._damage_history) == 1
        assert brain._damage_history[0] == 20
    
    def test_damage_tracking_ignores_healing(self):
        """Should not record negative damage when healed."""
        brain = BotBrain(persona="balanced")
        player = self._make_player(hp=50)
        
        brain._update_damage_tracking(player)
        
        # Heal to 80
        player.get_component_optional().hp = 80
        brain._update_damage_tracking(player)
        
        # Should not record -30 damage
        assert len(brain._damage_history) == 0
    
    def test_damage_tracking_maintains_window_of_3(self):
        """Should keep only last 3 damage events."""
        brain = BotBrain(persona="balanced")
        player = self._make_player(hp=100)
        
        brain._update_damage_tracking(player)
        
        # Take damage 4 times
        for damage in [10, 15, 20, 25]:
            current_hp = player.get_component_optional().hp
            player.get_component_optional().hp = current_hp - damage
            brain._update_damage_tracking(player)
        
        # Should only have last 3
        assert len(brain._damage_history) == 3
        assert list(brain._damage_history) == [15, 20, 25]


class TestAdaptiveHealThreshold:
    """Tests for Phase 17C adaptive heal threshold."""
    
    def _make_player(self, hp: int, max_hp: int = 100) -> Mock:
        """Helper to create mock player."""
        player = Mock()
        fighter = Mock()
        fighter.hp = hp
        fighter.max_hp = max_hp
        player.get_component_optional = Mock(return_value=fighter)
        return player
    
    def test_adaptive_threshold_no_damage_history(self):
        """With no damage history, should return base threshold."""
        brain = BotBrain(persona="balanced")
        player = self._make_player(hp=50)
        
        threshold = brain._get_adaptive_heal_threshold(player, 0.30)
        assert threshold == 0.30
    
    def test_adaptive_threshold_spike_detected(self):
        """Phase 17C revised: Adaptive threshold DISABLED (was causing early heals)."""
        brain = BotBrain(persona="balanced")
        player = self._make_player(hp=50, max_hp=100)
        
        # Simulate spike: 25 damage in one turn (> 20% of 100)
        brain._damage_history.append(25)
        
        # Adaptive logic disabled - should return base threshold
        threshold = brain._get_adaptive_heal_threshold(player, 0.30)
        assert threshold == 0.30  # No adjustment
    
    def test_adaptive_threshold_sustained_damage(self):
        """Phase 17C revised: Adaptive threshold DISABLED."""
        brain = BotBrain(persona="balanced")
        player = self._make_player(hp=50, max_hp=100)
        
        # Simulate sustained: 45 total damage over 3 turns (> 40% of 100)
        brain._damage_history.extend([15, 15, 15])
        
        # Adaptive logic disabled - should return base threshold
        threshold = brain._get_adaptive_heal_threshold(player, 0.30)
        assert threshold == 0.30  # No adjustment
    
    def test_adaptive_threshold_small_damage_no_change(self):
        """Small damage should not change threshold."""
        brain = BotBrain(persona="balanced")
        player = self._make_player(hp=50, max_hp=100)
        
        # Small damage: 10 in one turn (< 20% spike)
        brain._damage_history.append(10)
        
        threshold = brain._get_adaptive_heal_threshold(player, 0.30)
        assert threshold == 0.30  # No change
    
    def test_adaptive_threshold_capped_at_15_percent(self):
        """Phase 17C revised: Adaptive threshold DISABLED."""
        brain = BotBrain(persona="balanced")
        player = self._make_player(hp=50, max_hp=100)
        
        # Huge spike: 50 damage (> 20%)
        brain._damage_history.append(50)
        
        # Adaptive logic disabled - should return base threshold
        threshold = brain._get_adaptive_heal_threshold(player, 0.30)
        assert threshold == 0.30  # No adjustment


class TestRetreatLogic:
    """Tests for Phase 17C retreat decision making."""
    
    def _make_player(self, hp: int, max_hp: int = 100, x: int = 5, y: int = 5) -> Mock:
        """Helper to create mock player."""
        player = Mock()
        player.x = x
        player.y = y
        fighter = Mock()
        fighter.hp = hp
        fighter.max_hp = max_hp
        player.get_component_optional = Mock(return_value=fighter)
        return player
    
    def _make_enemy(self, x: int, y: int) -> Mock:
        """Helper to create mock enemy."""
        enemy = Mock()
        enemy.x = x
        enemy.y = y
        return enemy
    
    def test_should_retreat_critical_no_potion(self):
        """Should retreat when HP ≤ panic threshold and no potion."""
        brain = BotBrain(persona="balanced")
        player = self._make_player(hp=15)  # 15% HP
        enemy = self._make_enemy(x=6, y=5)  # Adjacent
        
        heal_config = _get_persona_heal_config("balanced")
        should_retreat = brain._should_retreat(player, [enemy], heal_config, has_potion=False)
        
        assert should_retreat is True
    
    def test_should_not_retreat_with_potion(self):
        """Should not retreat when has potion at low HP (will heal instead)."""
        brain = BotBrain(persona="balanced")
        player = self._make_player(hp=15)  # 15% HP
        enemy = self._make_enemy(x=6, y=5)
        
        heal_config = _get_persona_heal_config("balanced")
        should_retreat = brain._should_retreat(player, [enemy], heal_config, has_potion=True)
        
        # At panic threshold with potion, should heal not retreat
        assert should_retreat is False
    
    def test_should_retreat_conserve_potion_single_enemy(self):
        """Should retreat to conserve potion when single enemy and moderate HP."""
        brain = BotBrain(persona="balanced")
        player = self._make_player(hp=25)  # 25% HP (between panic 15% and base 30%)
        enemy = self._make_enemy(x=6, y=5)
        
        heal_config = _get_persona_heal_config("balanced")
        should_retreat = brain._should_retreat(player, [enemy], heal_config, has_potion=True)
        
        assert should_retreat is True
    
    def test_should_not_retreat_multiple_enemies(self):
        """Should not retreat for potion conservation when multiple enemies."""
        brain = BotBrain(persona="balanced")
        player = self._make_player(hp=25)  # 25% HP
        enemies = [self._make_enemy(x=6, y=5), self._make_enemy(x=4, y=5)]
        
        heal_config = _get_persona_heal_config("balanced")
        should_retreat = brain._should_retreat(player, enemies, heal_config, has_potion=True)
        
        assert should_retreat is False
    
    def test_find_safe_retreat_tile_basic(self):
        """Should find unblocked tile with no adjacent enemies."""
        brain = BotBrain(persona="balanced")
        player = self._make_player(hp=50, x=5, y=5)
        
        # Mock game map
        game_map = Mock()
        game_map.width = 10
        game_map.height = 10
        game_map.tiles = [[Mock(blocked=False) for _ in range(10)] for _ in range(10)]
        
        # One enemy to the east
        enemy = self._make_enemy(x=6, y=5)
        
        # Find retreat tile (should prefer tiles away from enemy)
        retreat_tile = brain._find_safe_retreat_tile(player, game_map, [], [enemy])
        
        assert retreat_tile is not None
        # Should be adjacent to player
        assert abs(retreat_tile[0] - player.x) <= 1
        assert abs(retreat_tile[1] - player.y) <= 1
    
    def test_find_safe_retreat_tile_blocked(self):
        """Should skip blocked tiles."""
        brain = BotBrain(persona="balanced")
        player = self._make_player(hp=50, x=5, y=5)
        
        # Mock game map with all tiles blocked except one
        game_map = Mock()
        game_map.width = 10
        game_map.height = 10
        game_map.tiles = [[Mock(blocked=True) for _ in range(10)] for _ in range(10)]
        
        # Unblock one tile to the west
        game_map.tiles[4][5].blocked = False
        
        retreat_tile = brain._find_safe_retreat_tile(player, game_map, [], [])
        
        assert retreat_tile == (4, 5)
    
    def test_find_safe_retreat_tile_no_safe_tiles(self):
        """Should return None when all tiles blocked."""
        brain = BotBrain(persona="balanced")
        player = self._make_player(hp=50, x=5, y=5)
        
        # Mock game map with all tiles blocked
        game_map = Mock()
        game_map.width = 10
        game_map.height = 10
        game_map.tiles = [[Mock(blocked=True) for _ in range(10)] for _ in range(10)]
        
        retreat_tile = brain._find_safe_retreat_tile(player, game_map, [], [])
        
        assert retreat_tile is None
    
    def test_find_safe_retreat_tile_entity_blocking(self):
        """Should skip tiles occupied by blocking entities."""
        brain = BotBrain(persona="balanced")
        player = self._make_player(hp=50, x=5, y=5)
        
        # Mock game map
        game_map = Mock()
        game_map.width = 10
        game_map.height = 10
        game_map.tiles = [[Mock(blocked=False) for _ in range(10)] for _ in range(10)]
        
        # Blocking entity to the west
        blocking_entity = Mock()
        blocking_entity.x = 4
        blocking_entity.y = 5
        blocking_entity.blocks = True
        
        retreat_tile = brain._find_safe_retreat_tile(player, game_map, [blocking_entity], [])
        
        # Should not choose (4, 5)
        assert retreat_tile != (4, 5)


class TestIntegratedAdaptiveBehavior:
    """Integration tests for Phase 17C adaptive features."""
    
    def test_damage_spike_triggers_early_heal(self):
        """Phase 17C revised: Adaptive threshold disabled, no early heal from spikes."""
        brain = BotBrain(persona="balanced")
        player = Mock()
        player.x = 5
        player.y = 5
        
        fighter = Mock()
        fighter.max_hp = 100
        fighter.hp = 35  # 35% HP (above base 30% threshold)
        player.get_component_optional = Mock(return_value=fighter)
        
        # Simulate damage spike
        brain._last_hp = 60  # Was at 60 HP
        brain._update_damage_tracking(player)  # Now at 35 HP (took 25 damage = spike)
        
        # Adaptive logic disabled - should NOT heal at 35% (above 30% base)
        heal_config = _get_persona_heal_config("balanced")
        should_heal = brain._should_heal_now(player, [], heal_config)
        
        assert should_heal is False  # Changed: no adaptive boost
    
    def test_no_spike_no_early_heal(self):
        """Without damage spike, should not heal above base threshold."""
        brain = BotBrain(persona="balanced")
        player = Mock()
        player.x = 5
        player.y = 5
        
        fighter = Mock()
        fighter.max_hp = 100
        fighter.hp = 35  # 35% HP
        player.get_component_optional = Mock(return_value=fighter)
        
        # Simulate small damage (no spike)
        brain._last_hp = 45  # Was at 45 HP
        brain._update_damage_tracking(player)  # Now at 35 HP (took 10 damage = no spike)
        
        # Should NOT heal (35% > base 30%, no adaptive bonus)
        heal_config = _get_persona_heal_config("balanced")
        should_heal = brain._should_heal_now(player, [], heal_config)
        
        assert should_heal is False
