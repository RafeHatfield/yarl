"""
Regression test for wand targeting bug.

Bug: Clicking wands in sidebar while in TARGETING state did nothing.
The _handle_inventory_action method had no case for GameStates.TARGETING.

Expected: Should be able to switch between wands while targeting.
"""
import pytest
from unittest.mock import Mock
from game_states import GameStates
from entity import Entity
from components.inventory import Inventory
from components.item import Item
from components.wand import Wand


class TestWandTargetingRegression:
    """Test that wands can be switched while in targeting mode."""
    
    def test_can_switch_wands_while_targeting(self):
        """Test that clicking different wands while targeting switches the targeted item.
        
        This is a regression test for a bug where clicking a wand in the sidebar
        while already in TARGETING mode did nothing because _handle_inventory_action
        had no handler for GameStates.TARGETING.
        """
        from game_actions import ActionProcessor
        from engine.game_state_manager import GameStateManager
        from engine.turn_manager import TurnManager
        from game_messages import MessageLog
        
        # Create player with two wands
        player = Entity(0, 0, '@', (255, 255, 255), 'Player', blocks=True)
        player.inventory = Inventory(26)
        
        # Create lightning wand
        lightning_wand = Entity(0, 0, '/', (255, 200, 0), 'Wand Of Lightning', blocks=False)
        lightning_wand.wand = Wand(spell_type="lightning_scroll", charges=3)
        lightning_wand.wand.owner = lightning_wand
        lightning_wand.item = Item(use_function=Mock(return_value=[]), targeting=True)
        lightning_wand.item.owner = lightning_wand
        
        # Create fireball wand
        fireball_wand = Entity(0, 0, '/', (255, 200, 0), 'Wand Of Fireball', blocks=False)
        fireball_wand.wand = Wand(spell_type="fireball_scroll", charges=3)
        fireball_wand.wand.owner = fireball_wand
        fireball_wand.item = Item(use_function=Mock(return_value=[]), targeting=True)
        fireball_wand.item.owner = fireball_wand
        
        # Add to inventory
        player.inventory.add_item(lightning_wand)
        player.inventory.add_item(fireball_wand)
        
        # Setup game state
        game_map = Mock()
        game_map.width = 80
        game_map.height = 60
        message_log = MessageLog(x=21, width=40, height=5)
        
        state_manager = GameStateManager(
            player=player,
            entities=[player],
            game_map=game_map,
            fov_map=Mock(),
            message_log=message_log
        )
        
        turn_manager = TurnManager(state_manager)
        action_processor = ActionProcessor(state_manager, turn_manager)
        
        # Simulate using first wand (should enter TARGETING mode)
        state_manager.set_game_state(GameStates.PLAYERS_TURN)
        action_processor._use_inventory_item(lightning_wand)
        
        # Should now be in TARGETING mode with lightning wand targeted
        assert state_manager.state.current_state == GameStates.TARGETING
        assert state_manager.get_extra_data("targeting_item") == lightning_wand
        
        # Simulate clicking the second wand while in TARGETING mode
        # This is what happens when you click a wand in the sidebar
        sorted_items = sorted(player.inventory.items, key=lambda item: item.get_display_name().lower())
        fireball_index = sorted_items.index(fireball_wand)
        
        # This should switch to targeting the fireball wand
        action_processor._handle_inventory_action(fireball_index)
        
        # Should still be in TARGETING mode, but now targeting the fireball wand
        assert state_manager.state.current_state == GameStates.TARGETING
        assert state_manager.get_extra_data("targeting_item") == fireball_wand
        
        print("✅ Test passed! Can now switch wands while in TARGETING mode")
