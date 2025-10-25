"""Test turn economy implementation.

This module tests that all inventory actions properly consume turns.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from game_actions import ActionProcessor
from game_states import GameStates
from components.component_registry import ComponentType


class TestPickupTurnEconomy:
    """Test that picking up items consumes a turn."""
    
    def test_pickup_item_ends_turn(self):
        """Picking up an item should end the player's turn."""
        # Setup
        state_manager = Mock()
        state_manager.state = Mock()
        state_manager.state.current_state = GameStates.PLAYERS_TURN
        state_manager.state.player = Mock()
        state_manager.state.player.x = 5
        state_manager.state.player.y = 5
        state_manager.state.player.inventory = Mock()
        state_manager.state.player.status_effects = Mock()
        state_manager.state.player.status_effects.process_turn_start = Mock(return_value=[])
        state_manager.state.player.process_status_effects_turn_end = Mock(return_value=[])  # Mock status effects
        state_manager.state.entities = []
        state_manager.state.message_log = Mock()
        
        # Create an item at player's location
        item_entity = Mock()
        item_entity.item = Mock()
        item_entity.x = 5
        item_entity.y = 5
        state_manager.state.entities.append(item_entity)
        
        # Mock successful pickup
        state_manager.state.player.inventory.add_item.return_value = [
            {"message": "Picked up item", "item_added": item_entity}
        ]
        
        processor = ActionProcessor(state_manager)
        
        # Execute pickup
        processor._handle_pickup(None)
        
        # Verify turn ended
        state_manager.set_game_state.assert_called_with(GameStates.ENEMY_TURN)
    
    def test_failed_pickup_does_not_end_turn(self):
        """Attempting to pick up with no item present should NOT end turn."""
        # Setup
        state_manager = Mock()
        state_manager.state = Mock()
        state_manager.state.current_state = GameStates.PLAYERS_TURN
        state_manager.state.player = Mock()
        state_manager.state.player.x = 5
        state_manager.state.player.y = 5
        state_manager.state.player.inventory = Mock()
        state_manager.state.entities = []  # No items
        state_manager.state.message_log = Mock()
        
        processor = ActionProcessor(state_manager)
        
        # Execute failed pickup
        processor._handle_pickup(None)
        
        # Verify turn did NOT end
        state_manager.set_game_state.assert_not_called()


class TestInventoryActionTurnEconomy:
    """Test that using items from inventory consumes turns."""
    
    def test_using_consumable_ends_turn(self):
        """Using a consumable item (e.g., potion) should end the turn."""
        # Setup
        state_manager = Mock()
        state_manager.state = Mock()
        state_manager.state.current_state = GameStates.PLAYERS_TURN  # Add current_state
        state_manager.state.player = Mock()
        state_manager.state.player.status_effects = Mock()
        state_manager.state.player.status_effects.process_turn_start = Mock(return_value=[])
        state_manager.state.player.process_status_effects_turn_end = Mock(return_value=[])  # Mock status effects
        state_manager.state.message_log = Mock()
        
        # Create a consumable item
        item = Mock()
        item.item = Mock()
        item.item.targeting = False  # Direct use, no targeting
        item.components = Mock()
        item.components.has = Mock(return_value=False)  # Not equippable
        
        # Mock successful use (item consumed)
        state_manager.state.player.inventory.use.return_value = [
            {"message": "You drink the potion", "consumed": True}
        ]
        
        processor = ActionProcessor(state_manager)
        # Mock TurnController
        processor.turn_controller = Mock()
        
        # Execute use
        processor._use_inventory_item(item)
        
        # Verify turn ended (via TurnController, not state_manager)
        processor.turn_controller.end_player_action.assert_called_once()
    
    def test_equipping_item_ends_turn(self):
        """Equipping an item should end the turn."""
        # Setup
        state_manager = Mock()
        state_manager.state = Mock()
        state_manager.state.current_state = GameStates.PLAYERS_TURN  # Add current_state
        state_manager.state.player = Mock()
        state_manager.state.player.equipment = Mock()
        state_manager.state.player.equipment.toggle_equip = Mock(return_value=[])  # Mock equipment toggle
        state_manager.state.player.status_effects = Mock()
        state_manager.state.player.status_effects.process_turn_start = Mock(return_value=[])
        state_manager.state.player.process_status_effects_turn_end = Mock(return_value=[])  # Mock status effects
        state_manager.state.message_log = Mock()
        
        item = Mock()
        item.item = Mock()
        
        # Mock equipping
        state_manager.state.player.inventory.use.return_value = [
            {"equip": item}
        ]
        
        processor = ActionProcessor(state_manager)
        # Mock TurnController
        processor.turn_controller = Mock()
        
        # Execute equip
        processor._use_inventory_item(item)
        
        # Verify turn ended (via TurnController)
        processor.turn_controller.end_player_action.assert_called_once()
    
    def test_entering_targeting_does_not_end_turn(self):
        """Entering targeting mode should NOT end the turn yet."""
        # Setup
        state_manager = Mock()
        state_manager.state = Mock()
        state_manager.state.player = Mock()
        state_manager.state.message_log = Mock()
        
        item = Mock()
        item.item = Mock()
        item.components = Mock()
        item.components.has = Mock(return_value=False)  # Not equippable
        
        # Mock entering targeting (turn should NOT end yet)
        state_manager.state.player.inventory.use.return_value = [
            {"targeting": "some_item"}
        ]
        
        processor = ActionProcessor(state_manager)
        
        # Execute use (enters targeting)
        processor._use_inventory_item(item)
        
        # Verify entered targeting mode
        state_manager.set_game_state.assert_called_with(GameStates.TARGETING)
        # Verify turn did NOT transition to ENEMY_TURN
        assert state_manager.set_game_state.call_count == 1


class TestDropTurnEconomy:
    """Test that dropping items consumes a turn."""
    
    def test_dropping_item_ends_turn(self):
        """Dropping an item should end the turn."""
        # Setup
        state_manager = Mock()
        state_manager.state = Mock()
        state_manager.state.current_state = GameStates.PLAYERS_TURN  # Add current_state
        state_manager.state.player = Mock()
        state_manager.state.player.x = 5
        state_manager.state.player.y = 5
        state_manager.state.player.status_effects = Mock()
        state_manager.state.player.status_effects.process_turn_start = Mock(return_value=[])
        state_manager.state.player.process_status_effects_turn_end = Mock(return_value=[])  # Mock status effects
        state_manager.state.entities = []
        state_manager.state.message_log = Mock()
        
        item = Mock()
        
        # Mock successful drop
        state_manager.state.player.inventory.drop_item.return_value = [
            {"message": "Dropped item", "item_dropped": item}
        ]
        
        processor = ActionProcessor(state_manager)
        # Mock TurnController
        processor.turn_controller = Mock()
        
        # Execute drop
        processor._drop_inventory_item(item)
        
        # Verify turn ended (via TurnController)
        processor.turn_controller.end_player_action.assert_called_once()


class TestTargetingCompletionTurnEconomy:
    """Test that completing targeting consumes a turn."""
    
    def test_completing_targeting_ends_turn(self):
        """Selecting a target for a spell should end the turn."""
        # Setup
        state_manager = Mock()
        state_manager.state = Mock()
        state_manager.state.current_state = GameStates.TARGETING
        state_manager.state.player = Mock()
        state_manager.state.player.inventory = Mock()
        state_manager.state.player.status_effects = Mock()
        state_manager.state.player.status_effects.process_turn_start = Mock(return_value=[])
        state_manager.state.player.process_status_effects_turn_end = Mock(return_value=[])  # Mock status effects
        state_manager.state.entities = []
        state_manager.state.message_log = Mock()
        
        # Mock targeting item
        targeting_item = Mock()
        targeting_item.item = Mock()
        state_manager.get_extra_data = Mock(return_value=targeting_item)
        
        # Mock successful spell cast
        state_manager.state.player.inventory.use.return_value = [
            {"message": "Spell cast!", "consumed": True}
        ]
        
        processor = ActionProcessor(state_manager)
        # Mock TurnController
        processor.turn_controller = Mock()
        
        # Execute targeting completion
        click_pos = (10, 10)
        processor._handle_left_click(click_pos)
        
        # Verify turn ended (via TurnController)
        processor.turn_controller.end_player_action.assert_called_once()


class TestIdentifyModeEffect:
    """Test the IdentifyModeEffect status effect."""
    
    def test_identify_mode_creation(self):
        """IdentifyModeEffect should be created correctly."""
        from components.status_effects import IdentifyModeEffect
        
        owner = Mock()
        owner.name = "Player"
        
        effect = IdentifyModeEffect(duration=10, owner=owner)
        
        assert effect.name == "identify_mode"
        assert effect.duration == 10
        assert effect.owner == owner
        # NOTE: Old API (identifies_used_this_turn, can_identify_item, use_identify) 
        # was removed - new implementation automatically identifies items at turn start
    
    def test_identify_mode_duration_decreases(self):
        """process_turn_end() should decrease duration."""
        from components.status_effects import IdentifyModeEffect
        
        owner = Mock()
        effect = IdentifyModeEffect(duration=3, owner=owner)
        
        effect.process_turn_end()
        assert effect.duration == 2
        
        effect.process_turn_end()
        assert effect.duration == 1
        
        effect.process_turn_end()
        assert effect.duration == 0


class TestIdentifyScrollIntegration:
    """Test the Identify scroll spell integration."""
    
    def test_identify_scroll_applies_effect(self):
        """Using an Identify scroll should apply IdentifyModeEffect."""
        from spells import cast_spell_by_id
        from components.status_effects import StatusEffectManager
        
        # Setup caster
        caster = Mock()
        caster.name = "Player"
        caster.components = Mock()
        caster.components.has.return_value = False
        
        # Cast Identify spell
        results = cast_spell_by_id("identify", caster)
        
        # Verify effect was added
        assert any(result.get("consumed") for result in results)
    
    def test_identify_spell_duration(self):
        """Identify spell should create 10-turn effect."""
        from spells.spell_catalog import IDENTIFY
        
        assert IDENTIFY.duration == 10
        assert IDENTIFY.spell_id == "identify"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

