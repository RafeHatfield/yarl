"""Unit tests for BotBrain potion-drinking behavior.

This test suite validates that the bot can drink potions when low on HP
for improved survivability during soak testing.

Test cases:
- Bot drinks known healing potion when low HP and safe
- Bot drinks any potion when low HP and no known healing potions
- Bot doesn't drink when enemies are visible
- Bot doesn't drink when HP is healthy
- Bot prefers healing potions over other potions
"""

import pytest
from unittest.mock import Mock

from io_layer.bot_brain import BotBrain, BotState
from game_states import GameStates
from components.component_registry import ComponentType


class TestBotPotionDrinking:
    """Test bot potion-drinking behavior for soak testing survivability."""

    def test_bot_drinks_known_healing_potion_when_low_hp_and_safe(self):
        """Bot should drink a known healing potion when HP ≤ 40% and no enemies visible."""
        brain = BotBrain()
        
        # Setup: Player at low HP (30%), no enemies, has healing potion
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.entities = []
        game_state.fov_map = Mock()
        
        # Mock player with low HP
        player = Mock()
        player.x = 10
        player.y = 10
        player.faction = Mock()
        player.components = Mock()
        player.components.has = Mock(return_value=False)
        
        # Mock fighter component with low HP
        mock_fighter = Mock()
        mock_fighter.hp = 30
        mock_fighter.max_hp = 100
        
        # Mock healing potion in inventory
        healing_potion = Mock()
        healing_potion.name = "healing_potion"
        healing_potion.char = '!'
        healing_potion.get_display_name = Mock(return_value="Healing Potion")
        healing_potion.components = Mock()
        healing_potion.components.has = Mock(return_value=False)
        
        healing_potion_item = Mock()
        healing_potion_item.identified = True  # Known healing potion
        healing_potion_item.use_function = Mock()
        healing_potion.get_component_optional = Mock(return_value=healing_potion_item)
        
        # Mock inventory with healing potion
        mock_inventory = Mock()
        mock_inventory.items = [healing_potion]
        
        # Setup player get_component_optional
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
        
        # Act
        action = brain.decide_action(game_state)
        
        # Assert: Should drink the potion (inventory index 0)
        assert action == {'inventory_index': 0}, \
            f"Expected bot to drink healing potion, got {action}"

    def test_bot_drinks_any_potion_when_low_hp_and_no_known_healing_potions(self):
        """Bot should drink an unidentified potion when low HP, no enemies, and no known healing potions."""
        brain = BotBrain()
        
        # Setup: Player at low HP (25%), no enemies, has unidentified potion
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.entities = []
        game_state.fov_map = Mock()
        
        # Mock player with low HP
        player = Mock()
        player.x = 10
        player.y = 10
        player.faction = Mock()
        player.components = Mock()
        player.components.has = Mock(return_value=False)
        
        # Mock fighter component with low HP
        mock_fighter = Mock()
        mock_fighter.hp = 25
        mock_fighter.max_hp = 100
        
        # Mock unidentified potion in inventory
        unknown_potion = Mock()
        unknown_potion.name = "speed_potion"
        unknown_potion.char = '!'
        unknown_potion.get_display_name = Mock(return_value="cloudy yellow potion")
        unknown_potion.components = Mock()
        unknown_potion.components.has = Mock(return_value=False)  # Not a wand
        
        unknown_potion_item = Mock()
        unknown_potion_item.identified = False  # Unidentified
        unknown_potion_item.use_function = Mock()
        unknown_potion.get_component_optional = Mock(return_value=unknown_potion_item)
        
        # Mock inventory with unidentified potion
        mock_inventory = Mock()
        mock_inventory.items = [unknown_potion]
        
        # Setup player get_component_optional
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
        
        # Act
        action = brain.decide_action(game_state)
        
        # Assert: Should drink the unidentified potion (inventory index 0)
        assert action == {'inventory_index': 0}, \
            f"Expected bot to drink unidentified potion, got {action}"

    def test_bot_does_not_drink_when_enemies_visible(self):
        """Bot should NOT drink potions when enemies are visible (unsafe)."""
        brain = BotBrain()
        
        # Setup: Player at low HP (30%), enemy visible, has healing potion
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.fov_map = Mock()
        
        # Mock player with low HP
        player = Mock()
        player.x = 10
        player.y = 10
        player.faction = Mock()
        player.components = Mock()
        player.components.has = Mock(return_value=False)
        
        # Mock fighter component with low HP
        mock_fighter = Mock()
        mock_fighter.hp = 30
        mock_fighter.max_hp = 100
        
        # Mock healing potion in inventory
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
        
        # Mock inventory with healing potion
        mock_inventory = Mock()
        mock_inventory.items = [healing_potion]
        
        # Mock enemy (visible, not adjacent)
        enemy = Mock()
        enemy.x = 15
        enemy.y = 10
        enemy.faction = Mock()
        enemy.components = Mock()
        enemy.components.has = Mock(side_effect=lambda ct: ct == ComponentType.AI)
        
        mock_enemy_fighter = Mock()
        mock_enemy_fighter.hp = 20
        enemy.get_component_optional = Mock(side_effect=lambda ct: 
            mock_enemy_fighter if ct == ComponentType.FIGHTER else None)
        
        game_state.entities = [player, enemy]
        
        # Setup player get_component_optional
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
        
        # Mock FOV: enemy is visible
        from unittest.mock import patch
        def mock_is_in_fov(fov_map, x, y):
            return (x, y) == (15, 10)
        
        with patch('io_layer.bot_brain.map_is_in_fov', side_effect=mock_is_in_fov), \
             patch('io_layer.bot_brain.are_factions_hostile', return_value=True):
            # Act
            action = brain.decide_action(game_state)
        
        # Assert: Should NOT drink potion (should move toward enemy instead)
        assert action != {'inventory_index': 0}, \
            f"Bot should NOT drink potion when enemy visible, got {action}"
        # Should be in combat and moving toward enemy
        assert brain.state == BotState.COMBAT

    def test_bot_does_not_drink_when_above_threshold(self):
        """Bot should NOT drink potions when HP > 40% (healthy enough)."""
        brain = BotBrain()
        
        # Setup: Player at healthy HP (60%), no enemies, has healing potion
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.entities = []
        game_state.fov_map = Mock()
        
        # Mock player with healthy HP
        player = Mock()
        player.x = 10
        player.y = 10
        player.faction = Mock()
        player.components = Mock()
        player.components.has = Mock(return_value=False)
        
        # Mock fighter component with healthy HP
        mock_fighter = Mock()
        mock_fighter.hp = 60
        mock_fighter.max_hp = 100
        
        # Mock healing potion in inventory
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
        
        # Mock inventory with healing potion
        mock_inventory = Mock()
        mock_inventory.items = [healing_potion]
        
        # Setup player get_component_optional
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
        
        # Act
        action = brain.decide_action(game_state)
        
        # Assert: Should NOT drink potion (should explore instead)
        assert action != {'inventory_index': 0}, \
            f"Bot should NOT drink potion when HP healthy, got {action}"
        # Should start auto-explore
        assert action == {'start_auto_explore': True}

    def test_bot_prefers_healing_potions_over_other_potions(self):
        """Bot should prefer known healing potions over unidentified potions."""
        brain = BotBrain()
        
        # Setup: Player at low HP (35%), no enemies, has both unidentified and healing potion
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.entities = []
        game_state.fov_map = Mock()
        
        # Mock player with low HP
        player = Mock()
        player.x = 10
        player.y = 10
        player.faction = Mock()
        player.components = Mock()
        player.components.has = Mock(return_value=False)
        
        # Mock fighter component with low HP
        mock_fighter = Mock()
        mock_fighter.hp = 35
        mock_fighter.max_hp = 100
        
        # Mock unidentified potion (index 0)
        unknown_potion = Mock()
        unknown_potion.name = "speed_potion"
        unknown_potion.char = '!'
        unknown_potion.get_display_name = Mock(return_value="cloudy yellow potion")
        unknown_potion.components = Mock()
        unknown_potion.components.has = Mock(return_value=False)  # Not a wand
        
        unknown_potion_item = Mock()
        unknown_potion_item.identified = False
        unknown_potion_item.use_function = Mock()
        unknown_potion.get_component_optional = Mock(return_value=unknown_potion_item)
        
        # Mock healing potion (index 1)
        healing_potion = Mock()
        healing_potion.name = "healing_potion"
        healing_potion.char = '!'
        healing_potion.get_display_name = Mock(return_value="Healing Potion")
        healing_potion.components = Mock()
        healing_potion.components.has = Mock(return_value=False)  # Not a wand
        
        healing_potion_item = Mock()
        healing_potion_item.identified = True
        healing_potion_item.use_function = Mock()
        healing_potion.get_component_optional = Mock(return_value=healing_potion_item)
        
        # Mock inventory with both potions (unidentified first, healing second)
        mock_inventory = Mock()
        mock_inventory.items = [unknown_potion, healing_potion]
        
        # Setup player get_component_optional
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
        
        # Act
        action = brain.decide_action(game_state)
        
        # Assert: Should drink the healing potion (inventory index 1), not the unidentified one
        assert action == {'inventory_index': 1}, \
            f"Expected bot to prefer healing potion at index 1, got {action}"

    def test_bot_does_nothing_when_low_hp_but_no_potions(self):
        """Bot should continue normal behavior when low HP but no potions available."""
        brain = BotBrain()
        
        # Setup: Player at low HP (20%), no enemies, empty inventory
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.entities = []
        game_state.fov_map = Mock()
        
        # Mock player with low HP
        player = Mock()
        player.x = 10
        player.y = 10
        player.faction = Mock()
        player.components = Mock()
        player.components.has = Mock(return_value=False)
        
        # Mock fighter component with low HP
        mock_fighter = Mock()
        mock_fighter.hp = 20
        mock_fighter.max_hp = 100
        
        # Mock empty inventory
        mock_inventory = Mock()
        mock_inventory.items = []
        
        # Setup player get_component_optional
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
        
        # Act
        action = brain.decide_action(game_state)
        
        # Assert: Should NOT attempt to drink (no potions), should continue with EXPLORE
        assert action == {'start_auto_explore': True}, \
            f"Expected bot to explore when no potions available, got {action}"

    def test_bot_drinks_at_exactly_40_percent_hp(self):
        """Bot should drink potions at exactly 40% HP (boundary condition)."""
        brain = BotBrain()
        
        # Setup: Player at exactly 40% HP, no enemies, has healing potion
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.entities = []
        game_state.fov_map = Mock()
        
        # Mock player at exactly 40% HP
        player = Mock()
        player.x = 10
        player.y = 10
        player.faction = Mock()
        player.components = Mock()
        player.components.has = Mock(return_value=False)
        
        # Mock fighter component at exactly 40% HP
        mock_fighter = Mock()
        mock_fighter.hp = 40
        mock_fighter.max_hp = 100
        
        # Mock healing potion in inventory
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
        
        # Mock inventory with healing potion
        mock_inventory = Mock()
        mock_inventory.items = [healing_potion]
        
        # Setup player get_component_optional
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
        
        # Act
        action = brain.decide_action(game_state)
        
        # Assert: Should drink the potion (≤ 40% threshold)
        assert action == {'inventory_index': 0}, \
            f"Expected bot to drink at exactly 40% HP, got {action}"

    def test_bot_does_not_drink_at_41_percent_hp(self):
        """Bot should NOT drink potions at 41% HP (just above threshold)."""
        brain = BotBrain()
        
        # Setup: Player at 41% HP, no enemies, has healing potion
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.entities = []
        game_state.fov_map = Mock()
        
        # Mock player at 41% HP
        player = Mock()
        player.x = 10
        player.y = 10
        player.faction = Mock()
        player.components = Mock()
        player.components.has = Mock(return_value=False)
        
        # Mock fighter component at 41% HP
        mock_fighter = Mock()
        mock_fighter.hp = 41
        mock_fighter.max_hp = 100
        
        # Mock healing potion in inventory
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
        
        # Mock inventory with healing potion
        mock_inventory = Mock()
        mock_inventory.items = [healing_potion]
        
        # Setup player get_component_optional
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
        
        # Act
        action = brain.decide_action(game_state)
        
        # Assert: Should NOT drink (above threshold), should explore
        assert action != {'inventory_index': 0}, \
            f"Bot should NOT drink at 41% HP, got {action}"
        assert action == {'start_auto_explore': True}
    
    def test_bot_does_not_drink_wands(self):
        """Bot should NOT try to drink wands (regression test for wand/potion confusion)."""
        brain = BotBrain()
        
        # Setup: Player at low HP, no enemies, has wand in inventory (NO potions)
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.entities = []
        game_state.fov_map = Mock()
        
        # Mock player at low HP (30%)
        player = Mock()
        player.x = 10
        player.y = 10
        player.faction = Mock()
        player.components = Mock()
        player.components.has = Mock(return_value=False)
        
        # Mock fighter component with low HP
        mock_fighter = Mock()
        mock_fighter.hp = 30
        mock_fighter.max_hp = 100
        
        # Mock wand in inventory (has use_function like potions!)
        wand = Mock()
        wand.name = "wand_of_portals"
        wand.char = '/'  # Wands typically use different char
        wand.wand = Mock()  # Has wand component
        wand.get_display_name = Mock(return_value="Wand of Portals")
        wand.components = Mock()
        wand.components.has = Mock(side_effect=lambda ct: ct == ComponentType.WAND)
        
        wand_item = Mock()
        wand_item.use_function = Mock()  # Wands have use_function too!
        wand.get_component_optional = Mock(side_effect=lambda ct:
            wand_item if ct == ComponentType.ITEM else (wand.wand if ct == ComponentType.WAND else None))
        
        # Mock inventory with only wand (no potions!)
        mock_inventory = Mock()
        mock_inventory.items = [wand]
        
        # Setup player get_component_optional
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
        
        # Act
        action = brain.decide_action(game_state)
        
        # Assert: Should NOT try to drink wand, should continue with explore
        assert action != {'inventory_index': 0}, \
            f"Bot should NOT try to drink wand, got {action}"
        assert action == {'start_auto_explore': True}, \
            f"Bot should explore when no potions available, got {action}"
    
    def test_bot_uses_correct_sorted_inventory_index(self):
        """Bot should use sorted inventory indices (regression test for index mismatch).
        
        Real-world scenario that caused the bug:
        - Inventory (unsorted): [Dagger, Healing Potion, Leather Armor, Wand]
        - Inventory (sorted): [Dagger, Healing Potion, Leather Armor, Wand]
        - Bot should use index 1 (Healing Potion), not index 0 (Dagger)
        """
        brain = BotBrain()
        
        # Setup: Player at low HP, no enemies
        game_state = Mock()
        game_state.current_state = GameStates.PLAYERS_TURN
        game_state.entities = []
        game_state.fov_map = Mock()
        
        player = Mock()
        player.x = 10
        player.y = 10
        player.faction = Mock()
        player.components = Mock()
        player.components.has = Mock(return_value=False)
        
        # Mock fighter with low HP
        mock_fighter = Mock()
        mock_fighter.hp = 30
        mock_fighter.max_hp = 100
        
        # Create items in a specific order that tests alphabetical sorting
        # Unsorted order: [Dagger, Healing Potion, Leather Armor, Wand]
        # Sorted order: [Dagger, Healing Potion, Leather Armor, Wand]
        # (happens to be same, but displays 'a)', 'b)', 'c)', 'd)')
        
        dagger = Mock()
        dagger.name = "dagger"
        dagger.char = '-'
        dagger.get_display_name = Mock(return_value="Dagger")
        dagger.components = Mock()
        dagger.components.has = Mock(return_value=False)
        dagger.get_component_optional = Mock(return_value=None)
        
        healing_potion = Mock()
        healing_potion.name = "healing_potion"
        healing_potion.char = '!'
        healing_potion.get_display_name = Mock(return_value="Healing Potion")
        healing_potion.components = Mock()
        healing_potion.components.has = Mock(return_value=False)
        
        healing_potion_item = Mock()
        healing_potion_item.identified = True
        healing_potion_item.use_function = Mock()
        healing_potion.get_component_optional = Mock(side_effect=lambda ct:
            healing_potion_item if ct == ComponentType.ITEM else None)
        
        leather = Mock()
        leather.name = "leather_armor"
        leather.char = '['
        leather.get_display_name = Mock(return_value="Leather Armor")
        leather.components = Mock()
        leather.components.has = Mock(return_value=False)
        leather.get_component_optional = Mock(return_value=None)
        
        wand = Mock()
        wand.name = "wand_of_portals"
        wand.char = '/'
        wand.get_display_name = Mock(return_value="Wand of Portals")
        wand.components = Mock()
        wand.components.has = Mock(side_effect=lambda ct: ct == ComponentType.WAND)
        wand.get_component_optional = Mock(return_value=Mock(use_function=Mock()))
        
        # Mock inventory with items in unsorted order
        mock_inventory = Mock()
        mock_inventory.items = [dagger, healing_potion, leather, wand]
        
        # Setup player
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
        
        # Act
        action = brain.decide_action(game_state)
        
        # Assert: Should use index 1 (Healing Potion in sorted inventory), NOT index 0 (Dagger)
        assert action == {'inventory_index': 1}, \
            f"Expected bot to use sorted index 1 (Healing Potion), got {action}"

