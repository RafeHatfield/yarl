"""Tests for persona-level potion-in-combat behavior.

This test suite validates that the drink_potion_in_combat persona flag
correctly controls whether bots can drink potions when enemies are visible.

Test cases:
- Cautious persona drinks potions while in combat (flag True)
- Balanced persona does NOT drink potions while in combat (flag False)
- All personas drink potions when no enemies are visible
"""

import pytest
from unittest.mock import Mock

from io_layer.bot_brain import BotBrain, BotState, BotPersonaConfig, PERSONAS
from game_states import GameStates
from components.component_registry import ComponentType


class TestBotPersonaDrinkPotionInCombat:
    """Tests for drink_potion_in_combat persona flag."""

    def test_cautious_persona_has_drink_potion_in_combat_true(self):
        """Cautious persona should have drink_potion_in_combat=True."""
        cautious = PERSONAS["cautious"]
        assert cautious.drink_potion_in_combat is True

    def test_balanced_persona_has_drink_potion_in_combat_false(self):
        """Balanced persona should have drink_potion_in_combat=False (default)."""
        balanced = PERSONAS["balanced"]
        assert balanced.drink_potion_in_combat is False

    def test_aggressive_persona_has_drink_potion_in_combat_false(self):
        """Aggressive persona should have drink_potion_in_combat=False (default)."""
        aggressive = PERSONAS["aggressive"]
        assert aggressive.drink_potion_in_combat is False

    def test_greedy_persona_has_drink_potion_in_combat_false(self):
        """Greedy persona should have drink_potion_in_combat=False (default)."""
        greedy = PERSONAS["greedy"]
        assert greedy.drink_potion_in_combat is False

    def test_speedrunner_persona_has_drink_potion_in_combat_false(self):
        """Speedrunner persona should have drink_potion_in_combat=False (default)."""
        speedrunner = PERSONAS["speedrunner"]
        assert speedrunner.drink_potion_in_combat is False


class TestBotBrainPotionInCombatBehavior:
    """Tests for BotBrain potion drinking behavior based on persona."""

    def _create_game_state_with_enemy(self, player_hp_fraction=0.3, has_potion=True):
        """Create a mock game state with an enemy visible and optional potion.
        
        Args:
            player_hp_fraction: Player HP as fraction of max (0.0-1.0)
            has_potion: Whether player has a healing potion
        """
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.fov_map = Mock()
        
        # Create visible enemy
        enemy = Mock()
        enemy.x = 12
        enemy.y = 10
        enemy.ai = Mock()  # Has AI = hostile
        enemy.faction = Mock()
        enemy.faction.is_hostile_to = Mock(return_value=True)
        enemy.components = Mock()
        enemy.components.has = Mock(return_value=False)
        enemy.get_component_optional = Mock(return_value=None)
        
        game_state.entities = [enemy]
        
        # Mock FOV to show enemy is visible
        game_state.fov_map.fov = Mock()
        
        # Mock player with low HP
        player = Mock()
        player.x = 10
        player.y = 10
        player.faction = Mock()
        player.faction.is_hostile_to = Mock(return_value=True)
        player.components = Mock()
        player.components.has = Mock(return_value=False)
        
        # Mock fighter component
        mock_fighter = Mock()
        mock_fighter.hp = int(100 * player_hp_fraction)
        mock_fighter.max_hp = 100
        
        # Mock healing potion if enabled
        if has_potion:
            healing_potion = Mock()
            healing_potion.name = "healing_potion"
            healing_potion.char = '!'
            healing_potion.get_display_name = Mock(return_value="Healing Potion")
            healing_potion.components = Mock()
            healing_potion.components.has = Mock(return_value=False)
            
            healing_potion_item = Mock()
            healing_potion_item.identified = True
            healing_potion_item.use_function = Mock()
            healing_potion.get_component_optional = Mock(return_value=healing_potion_item)
            
            mock_inventory = Mock()
            mock_inventory.items = [healing_potion]
        else:
            mock_inventory = Mock()
            mock_inventory.items = []
        
        def get_component(comp_type):
            if comp_type == ComponentType.FIGHTER:
                return mock_fighter
            elif comp_type == ComponentType.INVENTORY:
                return mock_inventory
            elif comp_type == ComponentType.AUTO_EXPLORE:
                return None
            return None
        
        player.get_component_optional = Mock(side_effect=get_component)
        game_state.player = player
        
        return game_state

    def test_cautious_bot_should_drink_potion_returns_true_in_combat(self):
        """Cautious bot _should_drink_potion() should return True when in combat."""
        brain = BotBrain(persona="cautious")
        
        # Create mock player with low HP
        player = Mock()
        mock_fighter = Mock()
        mock_fighter.hp = 30  # 30% HP (below cautious threshold of 50%)
        mock_fighter.max_hp = 100
        player.get_component_optional = Mock(return_value=mock_fighter)
        
        # Create visible enemies
        enemy = Mock()
        visible_enemies = [enemy]
        
        # Cautious should allow potion drinking even with enemies
        result = brain._should_drink_potion(player, visible_enemies)
        assert result is True

    def test_balanced_bot_should_drink_potion_returns_false_in_combat(self):
        """Balanced bot _should_drink_potion() should return False when in combat."""
        brain = BotBrain(persona="balanced")
        
        # Create mock player with low HP
        player = Mock()
        mock_fighter = Mock()
        mock_fighter.hp = 30  # 30% HP (below balanced threshold of 40%)
        mock_fighter.max_hp = 100
        player.get_component_optional = Mock(return_value=mock_fighter)
        
        # Create visible enemies
        enemy = Mock()
        visible_enemies = [enemy]
        
        # Balanced should NOT allow potion drinking with enemies
        result = brain._should_drink_potion(player, visible_enemies)
        assert result is False

    def test_both_personas_drink_when_no_enemies(self):
        """Both cautious and balanced should drink potions when no enemies visible."""
        # Test cautious
        cautious_brain = BotBrain(persona="cautious")
        player = Mock()
        mock_fighter = Mock()
        mock_fighter.hp = 30
        mock_fighter.max_hp = 100
        player.get_component_optional = Mock(return_value=mock_fighter)
        
        result = cautious_brain._should_drink_potion(player, [])
        assert result is True
        
        # Test balanced
        balanced_brain = BotBrain(persona="balanced")
        result = balanced_brain._should_drink_potion(player, [])
        assert result is True

    def test_neither_persona_drinks_at_full_hp(self):
        """Neither persona should drink potions at full HP."""
        # Test cautious
        cautious_brain = BotBrain(persona="cautious")
        player = Mock()
        mock_fighter = Mock()
        mock_fighter.hp = 100  # Full HP
        mock_fighter.max_hp = 100
        player.get_component_optional = Mock(return_value=mock_fighter)
        
        # Even with enemies present, high HP means no potion needed
        result = cautious_brain._should_drink_potion(player, [])
        assert result is False
        
        # Test balanced
        balanced_brain = BotBrain(persona="balanced")
        result = balanced_brain._should_drink_potion(player, [])
        assert result is False


class TestBotPersonaConfigDefaults:
    """Tests for BotPersonaConfig default values."""

    def test_persona_config_default_drink_potion_in_combat_false(self):
        """BotPersonaConfig should default drink_potion_in_combat to False."""
        config = BotPersonaConfig(name="test")
        assert config.drink_potion_in_combat is False

    def test_persona_config_explicit_drink_potion_in_combat(self):
        """BotPersonaConfig should accept explicit drink_potion_in_combat value."""
        config_true = BotPersonaConfig(name="test", drink_potion_in_combat=True)
        assert config_true.drink_potion_in_combat is True
        
        config_false = BotPersonaConfig(name="test", drink_potion_in_combat=False)
        assert config_false.drink_potion_in_combat is False

