"""Tests for bot persona system.

Tests that:
1. Persona configs are loaded correctly
2. BotBrain respects persona parameters
3. Different personas produce different behaviors
"""

import pytest
from unittest.mock import Mock, patch

from io_layer.bot_brain import (
    BotBrain, 
    BotState, 
    BotPersonaConfig, 
    PERSONAS, 
    get_persona, 
    list_personas,
    PERSONA_HEAL_CONFIG,
    _get_persona_heal_config,
)
from io_layer.bot_input import BotInputSource
from game_states import GameStates
from components.component_registry import ComponentType


class TestPersonaConfig:
    """Tests for BotPersonaConfig and persona registry."""
    
    def test_list_personas_returns_all_personas(self):
        """list_personas() should return all defined persona names."""
        names = list_personas()
        assert "balanced" in names
        assert "cautious" in names
        assert "aggressive" in names
        assert "greedy" in names
        assert "speedrunner" in names
        assert len(names) == 5
    
    def test_get_persona_returns_correct_config(self):
        """get_persona() should return the correct config for each name."""
        balanced = get_persona("balanced")
        assert balanced.name == "balanced"
        assert balanced.potion_hp_threshold == 0.40
        
        cautious = get_persona("cautious")
        assert cautious.name == "cautious"
        assert cautious.potion_hp_threshold == 0.50  # Drinks earlier
        assert cautious.avoid_combat is True
        
        aggressive = get_persona("aggressive")
        assert aggressive.name == "aggressive"
        assert aggressive.potion_hp_threshold == 0.25  # Only when critical
        assert aggressive.loot_priority == 0  # Ignores loot
    
    def test_get_persona_raises_on_invalid_name(self):
        """get_persona() should raise ValueError for unknown persona."""
        with pytest.raises(ValueError, match="Unknown persona"):
            get_persona("nonexistent")
    
    def test_persona_config_is_frozen(self):
        """BotPersonaConfig should be immutable (frozen dataclass)."""
        config = get_persona("balanced")
        with pytest.raises(AttributeError):
            config.name = "hacked"


class TestBotBrainPersona:
    """Tests for BotBrain persona integration."""
    
    def test_botbrain_default_persona_is_balanced(self):
        """BotBrain with no persona should use balanced."""
        brain = BotBrain()
        assert brain.persona.name == "balanced"
    
    def test_botbrain_accepts_persona_parameter(self):
        """BotBrain should accept persona name and load config."""
        brain = BotBrain(persona="cautious")
        assert brain.persona.name == "cautious"
        assert brain.persona.avoid_combat is True
        
        brain2 = BotBrain(persona="aggressive")
        assert brain2.persona.name == "aggressive"
    
    def test_botbrain_invalid_persona_raises(self):
        """BotBrain should raise on invalid persona name."""
        with pytest.raises(ValueError, match="Unknown persona"):
            BotBrain(persona="invalid_persona")
    
    def test_potion_threshold_uses_persona_value(self):
        """_should_drink_potion should use persona.potion_hp_threshold."""
        # Create mock player
        mock_player = Mock()
        mock_fighter = Mock()
        mock_fighter.hp = 30
        mock_fighter.max_hp = 100
        mock_player.get_component_optional = Mock(return_value=mock_fighter)
        
        # Balanced: threshold 0.40, HP 30% should trigger
        balanced_brain = BotBrain(persona="balanced")
        result = balanced_brain._should_drink_potion(mock_player, [])
        assert result is True, "Balanced at 30% HP should drink potion"
        
        # Aggressive: threshold 0.25, HP 30% should NOT trigger
        aggressive_brain = BotBrain(persona="aggressive")
        result = aggressive_brain._should_drink_potion(mock_player, [])
        assert result is False, "Aggressive at 30% HP should NOT drink potion"
        
        # Now drop HP to 20%
        mock_fighter.hp = 20
        result = aggressive_brain._should_drink_potion(mock_player, [])
        assert result is True, "Aggressive at 20% HP should drink potion"


class TestBotInputSourcePersona:
    """Tests for BotInputSource persona passthrough."""
    
    def test_botinputsource_passes_persona_to_botbrain(self):
        """BotInputSource should pass persona to BotBrain."""
        bot = BotInputSource(persona="greedy")
        assert bot.bot_brain.persona.name == "greedy"
    
    def test_botinputsource_default_persona(self):
        """BotInputSource with no persona should use balanced."""
        bot = BotInputSource()
        assert bot.bot_brain.persona.name == "balanced"


class TestPersonaBehaviorDifferences:
    """Tests that verify personas produce different decisions."""
    
    def test_avoid_combat_persona_skips_distant_enemies(self):
        """Cautious/speedrunner personas should not engage distant enemies."""
        # Setup game state with distant enemy
        mock_game_state = Mock()
        mock_game_state.current_state = GameStates.PLAYERS_TURN
        
        mock_player = Mock()
        mock_player.x = 0
        mock_player.y = 0
        mock_player.get_component_optional = Mock(return_value=None)
        
        mock_game_state.player = mock_player
        mock_game_state.entities = []
        mock_game_state.fov_map = None
        
        # Cautious brain should have avoid_combat=True
        cautious_brain = BotBrain(persona="cautious")
        assert cautious_brain.persona.avoid_combat is True
        
        # Aggressive brain should have avoid_combat=False
        aggressive_brain = BotBrain(persona="aggressive")
        assert aggressive_brain.persona.avoid_combat is False
    
    def test_loot_priority_zero_skips_loot(self):
        """Personas with loot_priority=0 should skip loot."""
        aggressive = get_persona("aggressive")
        assert aggressive.loot_priority == 0
        
        speedrunner = get_persona("speedrunner")
        assert speedrunner.loot_priority == 0
        
        balanced = get_persona("balanced")
        assert balanced.loot_priority == 1
        
        greedy = get_persona("greedy")
        assert greedy.loot_priority == 2
    
    def test_combat_engagement_distance_varies(self):
        """Different personas have different engagement distances."""
        balanced = get_persona("balanced")
        cautious = get_persona("cautious")
        aggressive = get_persona("aggressive")
        speedrunner = get_persona("speedrunner")
        
        assert balanced.combat_engagement_distance == 8
        assert cautious.combat_engagement_distance == 5
        assert aggressive.combat_engagement_distance == 12
        assert speedrunner.combat_engagement_distance == 4


class TestPersonaHealConfig:
    """Tests for Phase 17B heal threshold configuration."""
    
    def test_all_personas_have_heal_config(self):
        """All personas should have a heal config defined."""
        for persona_name in list_personas():
            heal_config = _get_persona_heal_config(persona_name)
            assert heal_config is not None
            assert heal_config.base_heal_threshold > 0.0
            assert heal_config.panic_threshold >= 0.0
            assert heal_config.panic_multi_enemy_count >= 1
    
    def test_balanced_heal_thresholds(self):
        """Balanced persona should have survivability-tuned thresholds."""
        heal_config = _get_persona_heal_config("balanced")
        assert heal_config.base_heal_threshold == 0.30  # 30% HP
        assert heal_config.panic_threshold == 0.15  # 15% HP
        assert heal_config.panic_multi_enemy_count == 2
        assert heal_config.allow_combat_healing is True
    
    def test_cautious_heals_earlier_than_balanced(self):
        """Cautious persona should have higher thresholds than balanced."""
        cautious = _get_persona_heal_config("cautious")
        balanced = _get_persona_heal_config("balanced")
        assert cautious.base_heal_threshold > balanced.base_heal_threshold
        assert cautious.panic_threshold >= balanced.panic_threshold
    
    def test_aggressive_heals_later_than_balanced(self):
        """Aggressive persona should have lower thresholds than balanced."""
        aggressive = _get_persona_heal_config("aggressive")
        balanced = _get_persona_heal_config("balanced")
        assert aggressive.base_heal_threshold < balanced.base_heal_threshold
        assert aggressive.panic_threshold <= balanced.panic_threshold
    
    def test_unknown_persona_defaults_to_balanced(self):
        """Unknown persona should fall back to balanced heal config."""
        heal_config = _get_persona_heal_config("nonexistent_persona")
        balanced_config = _get_persona_heal_config("balanced")
        assert heal_config.base_heal_threshold == balanced_config.base_heal_threshold


class TestHealThresholdBehavior:
    """Tests for Phase 17B heal threshold behavior."""
    
    def _make_player(self, hp: int, max_hp: int) -> Mock:
        """Helper to create mock player with specified HP."""
        mock_player = Mock()
        mock_fighter = Mock()
        mock_fighter.hp = hp
        mock_fighter.max_hp = max_hp
        mock_player.get_component_optional = Mock(return_value=mock_fighter)
        return mock_player
    
    def test_balanced_heals_at_30_percent(self):
        """Balanced persona should heal at 30% HP with no enemies."""
        brain = BotBrain(persona="balanced")
        player = self._make_player(hp=30, max_hp=100)  # 30% HP
        
        # No enemies = safe to heal
        should_heal = brain._should_drink_potion(player, [])
        assert should_heal is True, "Should heal at 30% HP when safe"
    
    def test_balanced_does_not_heal_above_30_percent(self):
        """Balanced persona should NOT heal above 30% HP."""
        brain = BotBrain(persona="balanced")
        player = self._make_player(hp=35, max_hp=100)  # 35% HP
        
        should_heal = brain._should_drink_potion(player, [])
        assert should_heal is False, "Should NOT heal at 35% HP"
    
    def test_balanced_heals_at_25_percent_with_enemies(self):
        """Balanced persona should heal at 25% HP even with enemies (combat healing)."""
        brain = BotBrain(persona="balanced")
        player = self._make_player(hp=25, max_hp=100)  # 25% HP
        
        # Create mock enemy
        enemy = Mock()
        enemy.x = 10
        enemy.y = 10
        
        # Combat healing enabled for balanced
        should_heal = brain._should_drink_potion(player, [enemy])
        assert should_heal is True, "Should heal in combat at 25% HP"


class TestPanicLogic:
    """Tests for Phase 17B panic healing logic."""
    
    def _make_player(self, hp: int, max_hp: int, x: int = 5, y: int = 5) -> Mock:
        """Helper to create mock player with specified HP and position."""
        mock_player = Mock()
        mock_player.x = x
        mock_player.y = y
        mock_fighter = Mock()
        mock_fighter.hp = hp
        mock_fighter.max_hp = max_hp
        mock_player.get_component_optional = Mock(return_value=mock_fighter)
        return mock_player
    
    def _make_enemy(self, x: int, y: int) -> Mock:
        """Helper to create mock enemy at position."""
        enemy = Mock()
        enemy.x = x
        enemy.y = y
        return enemy
    
    def test_count_adjacent_enemies(self):
        """_count_adjacent_enemies should count enemies at distance 1."""
        brain = BotBrain(persona="balanced")
        player = self._make_player(hp=50, max_hp=100, x=5, y=5)
        
        # Adjacent enemies (Manhattan distance 1)
        adjacent1 = self._make_enemy(x=6, y=5)  # East
        adjacent2 = self._make_enemy(x=5, y=6)  # South
        distant = self._make_enemy(x=7, y=7)   # Distance 4
        
        enemies = [adjacent1, adjacent2, distant]
        count = brain._count_adjacent_enemies(player, enemies)
        assert count == 2, "Should count only adjacent enemies"
    
    def test_panic_with_low_hp_and_multi_attacker(self):
        """Panic state should trigger at low HP with 2+ adjacent enemies."""
        brain = BotBrain(persona="balanced")
        player = self._make_player(hp=15, max_hp=100, x=5, y=5)  # 15% HP
        
        # Two adjacent enemies
        enemy1 = self._make_enemy(x=6, y=5)
        enemy2 = self._make_enemy(x=4, y=5)
        
        heal_config = _get_persona_heal_config("balanced")
        is_panic = brain._is_panic_state(player, [enemy1, enemy2], heal_config)
        assert is_panic is True, "Should panic at 15% HP with 2 adjacent enemies"
    
    def test_no_panic_with_low_hp_and_one_enemy(self):
        """Phase 17C: Panic NOW triggers with ANY adjacent enemy at low HP (strengthened)."""
        brain = BotBrain(persona="balanced")
        player = self._make_player(hp=15, max_hp=100, x=5, y=5)  # 15% HP
        
        # One adjacent enemy
        enemy = self._make_enemy(x=6, y=5)
        
        heal_config = _get_persona_heal_config("balanced")
        is_panic = brain._is_panic_state(player, [enemy], heal_config)
        # Phase 17C: Strengthened panic - ANY adjacent enemy at low HP triggers panic
        assert is_panic is True, "Phase 17C: Should panic with 1 adjacent enemy at 15% HP"
    
    def test_no_panic_above_panic_threshold(self):
        """No panic if HP is above panic threshold, even with multiple enemies."""
        brain = BotBrain(persona="balanced")
        player = self._make_player(hp=20, max_hp=100, x=5, y=5)  # 20% HP > 15% panic threshold
        
        # Two adjacent enemies
        enemy1 = self._make_enemy(x=6, y=5)
        enemy2 = self._make_enemy(x=4, y=5)
        
        heal_config = _get_persona_heal_config("balanced")
        is_panic = brain._is_panic_state(player, [enemy1, enemy2], heal_config)
        assert is_panic is False, "Should NOT panic at 20% HP (above 15% threshold)"
    
    def test_panic_triggers_healing(self):
        """Panic state should trigger immediate healing."""
        brain = BotBrain(persona="balanced")
        player = self._make_player(hp=10, max_hp=100, x=5, y=5)  # 10% HP
        
        # Two adjacent enemies
        enemy1 = self._make_enemy(x=6, y=5)
        enemy2 = self._make_enemy(x=4, y=5)
        
        should_heal = brain._should_drink_potion(player, [enemy1, enemy2])
        assert should_heal is True, "Should heal in panic state"
    
    def test_aggressive_requires_3_enemies_for_panic(self):
        """Phase 17C: Panic triggers with ANY adjacent enemy at low HP (persona-independent)."""
        brain = BotBrain(persona="aggressive")
        player = self._make_player(hp=10, max_hp=100, x=5, y=5)  # 10% HP (at panic threshold)
        
        # Phase 17C: ANY adjacent enemy at low HP triggers panic
        enemy1 = self._make_enemy(x=6, y=5)
        
        heal_config = _get_persona_heal_config("aggressive")
        is_panic = brain._is_panic_state(player, [enemy1], heal_config)
        assert is_panic is True, "Phase 17C: Aggressive should panic with 1 adjacent enemy at 10% HP"
        
        # Multiple enemies should still trigger panic
        enemy2 = self._make_enemy(x=4, y=5)
        enemy3 = self._make_enemy(x=5, y=6)
        is_panic = brain._is_panic_state(player, [enemy1, enemy2, enemy3], heal_config)
        assert is_panic is True, "Aggressive should panic with 3 enemies"

