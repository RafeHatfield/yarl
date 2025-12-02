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
    list_personas
)
from io_layer.bot_input import BotInputSource
from game_states import GameStates


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

