"""Phase B: Advanced Portal Mechanics Tests

Tests for monster portal interaction, AI flags, and combat positioning.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from components.ai import BasicMonster, BossAI, MindlessZombieAI, ConfusedMonster, SlimeAI
from components.portal import Portal
from services.portal_manager import PortalManager
from entity import Entity
from render_functions import RenderOrder


class TestAIPortalUsableFlag:
    """Test that AI classes have portal_usable flag set correctly."""
    
    def test_basic_monster_portal_usable_true(self):
        """BasicMonster should be able to use portals."""
        ai = BasicMonster()
        assert hasattr(ai, 'portal_usable')
        assert ai.portal_usable is True
    
    def test_boss_ai_portal_usable_false(self):
        """BossAI should NOT be able to use portals (tactical advantage)."""
        ai = BossAI()
        assert hasattr(ai, 'portal_usable')
        assert ai.portal_usable is False
    
    def test_mindless_zombie_portal_usable_true(self):
        """Mindless zombies can use portals (they're chaotic anyway)."""
        ai = MindlessZombieAI()
        assert hasattr(ai, 'portal_usable')
        assert ai.portal_usable is True
    
    def test_confused_monster_portal_usable_false(self):
        """Confused monsters shouldn't use portals."""
        previous_ai = BasicMonster()
        ai = ConfusedMonster(previous_ai)
        assert hasattr(ai, 'portal_usable')
        assert ai.portal_usable is False
    
    def test_slime_ai_portal_usable_true(self):
        """SlimeAI should be able to use portals."""
        ai = SlimeAI()
        assert hasattr(ai, 'portal_usable')
        assert ai.portal_usable is True


class TestPortalCollisionWithAIFlag:
    """Test that PortalManager respects AI portal_usable flag."""
    
    def test_monster_with_portal_usable_true_can_teleport(self):
        """Monster with portal_usable=True should teleport through portals."""
        # Create monster with BasicMonster AI
        monster = Entity(5, 5, 'o', (100, 100, 100), 'Test Monster')
        monster.ai = BasicMonster()
        monster.ai.portal_usable = True  # Explicitly set
        
        # Create portal pair
        entrance = Entity(5, 5, '[', (0, 255, 255), 'Entrance')
        exit_portal = Entity(10, 10, ']', (255, 255, 0), 'Exit')
        
        entrance.portal = Portal('entrance')
        exit_portal.portal = Portal('exit')
        entrance.portal.owner = entrance
        exit_portal.portal.owner = exit_portal
        entrance.portal.linked_portal = exit_portal.portal
        exit_portal.portal.linked_portal = entrance.portal
        entrance.portal.is_deployed = True
        exit_portal.portal.is_deployed = True
        
        entities = [monster, entrance, exit_portal]
        
        # Monster is on entrance portal
        result = PortalManager.check_portal_collision(monster, entities)
        
        assert result is not None
        assert result.get('teleported') is True
        assert monster.x == 10
        assert monster.y == 10
        # Message can be string or Message object
        message_str = str(result.get('message', ''))
        assert "Test Monster" in message_str or "Monster" in message_str
    
    def test_monster_with_portal_usable_false_cannot_teleport(self):
        """Monster with portal_usable=False should NOT teleport."""
        # Create monster with BossAI (portal_usable=False)
        monster = Entity(5, 5, 'B', (200, 50, 50), 'Boss')
        monster.ai = BossAI()
        assert monster.ai.portal_usable is False
        
        # Create portal pair
        entrance = Entity(5, 5, '[', (0, 255, 255), 'Entrance')
        exit_portal = Entity(10, 10, ']', (255, 255, 0), 'Exit')
        
        entrance.portal = Portal('entrance')
        exit_portal.portal = Portal('exit')
        entrance.portal.owner = entrance
        exit_portal.portal.owner = exit_portal
        entrance.portal.linked_portal = exit_portal.portal
        exit_portal.portal.linked_portal = entrance.portal
        entrance.portal.is_deployed = True
        exit_portal.portal.is_deployed = True
        
        entities = [monster, entrance, exit_portal]
        
        # Monster is on entrance portal
        result = PortalManager.check_portal_collision(monster, entities)
        
        # Should return None - boss doesn't use portals
        assert result is None
        assert monster.x == 5  # Position unchanged
        assert monster.y == 5
    
    def test_player_always_can_teleport(self):
        """Player should always be able to teleport (no AI flag)."""
        # Create player (no AI)
        player = Entity(5, 5, '@', (255, 255, 255), 'Player')
        # No AI component - player has no portal_usable flag
        
        # Create portal pair
        entrance = Entity(5, 5, '[', (0, 255, 255), 'Entrance')
        exit_portal = Entity(10, 10, ']', (255, 255, 0), 'Exit')
        
        entrance.portal = Portal('entrance')
        exit_portal.portal = Portal('exit')
        entrance.portal.owner = entrance
        exit_portal.portal.owner = exit_portal
        entrance.portal.linked_portal = exit_portal.portal
        exit_portal.portal.linked_portal = entrance.portal
        entrance.portal.is_deployed = True
        exit_portal.portal.is_deployed = True
        
        entities = [player, entrance, exit_portal]
        
        # Player is on entrance portal
        result = PortalManager.check_portal_collision(player, entities)
        
        assert result is not None
        assert result.get('teleported') is True
        assert player.x == 10
        assert player.y == 10
    
    def test_confused_monster_cannot_teleport(self):
        """Confused monsters should not use portals."""
        # Create monster with ConfusedMonster AI
        original_ai = BasicMonster()
        monster = Entity(5, 5, 'o', (100, 100, 100), 'Confused Orc')
        monster.ai = ConfusedMonster(original_ai, number_of_turns=5)
        
        assert monster.ai.portal_usable is False
        
        # Create portal pair
        entrance = Entity(5, 5, '[', (0, 255, 255), 'Entrance')
        exit_portal = Entity(10, 10, ']', (255, 255, 0), 'Exit')
        
        entrance.portal = Portal('entrance')
        exit_portal.portal = Portal('exit')
        entrance.portal.owner = entrance
        exit_portal.portal.owner = exit_portal
        entrance.portal.linked_portal = exit_portal.portal
        exit_portal.portal.linked_portal = entrance.portal
        entrance.portal.is_deployed = True
        exit_portal.portal.is_deployed = True
        
        entities = [monster, entrance, exit_portal]
        
        # Monster is on entrance portal
        result = PortalManager.check_portal_collision(monster, entities)
        
        # Confused monster can't use portals
        assert result is None
        assert monster.x == 5
        assert monster.y == 5


class TestPortalTeleportationMessages:
    """Test that portal teleportation messages distinguish player from monsters."""
    
    def test_player_teleportation_message(self):
        """Player teleportation should say 'You step through...'."""
        player = Entity(5, 5, '@', (255, 255, 255), 'Player')
        
        entrance = Entity(5, 5, '[', (0, 255, 255), 'Entrance')
        exit_portal = Entity(10, 10, ']', (255, 255, 0), 'Exit')
        
        entrance.portal = Portal('entrance')
        exit_portal.portal = Portal('exit')
        entrance.portal.owner = entrance
        exit_portal.portal.owner = exit_portal
        entrance.portal.linked_portal = exit_portal.portal
        exit_portal.portal.linked_portal = entrance.portal
        entrance.portal.is_deployed = True
        exit_portal.portal.is_deployed = True
        
        entities = [player, entrance, exit_portal]
        
        result = PortalManager.check_portal_collision(player, entities)
        
        # Message can be string or Message object - check as string
        message_str = str(result.get('message', ''))
        assert "step" in message_str.lower() or "reality" in message_str.lower()
    
    def test_monster_teleportation_message(self):
        """Monster teleportation should include monster name."""
        monster = Entity(5, 5, 'o', (100, 100, 100), 'Evil Orc')
        monster.ai = BasicMonster()
        
        entrance = Entity(5, 5, '[', (0, 255, 255), 'Entrance')
        exit_portal = Entity(10, 10, ']', (255, 255, 0), 'Exit')
        
        entrance.portal = Portal('entrance')
        exit_portal.portal = Portal('exit')
        entrance.portal.owner = entrance
        exit_portal.portal.owner = exit_portal
        entrance.portal.linked_portal = exit_portal.portal
        exit_portal.portal.linked_portal = entrance.portal
        entrance.portal.is_deployed = True
        exit_portal.portal.is_deployed = True
        
        entities = [monster, entrance, exit_portal]
        
        result = PortalManager.check_portal_collision(monster, entities)
        
        # Message can be string or Message object - check as string
        message_str = str(result.get('message', ''))
        assert "Evil Orc" in message_str or "shimmers" in message_str.lower()


class TestPortalTeleportationEdgeCases:
    """Test edge cases in portal teleportation."""
    
    def test_monster_cannot_teleport_if_holding_entry_portal(self):
        """Monster carrying entry portal shouldn't be able to teleport."""
        monster = Entity(5, 5, 'o', (100, 100, 100), 'Orc')
        monster.ai = BasicMonster()
        
        # Give monster an inventory with entry portal
        from components.inventory import Inventory
        monster.inventory = Inventory(capacity=20)
        
        # Create entry portal item
        entry_item = Entity(0, 0, '[', (0, 255, 255), 'Portal Entrance')
        entry_item.portal = Portal('entrance')
        entry_item.portal.is_deployed = False  # In inventory
        
        monster.inventory.add_item(entry_item)
        
        # Create portal pair
        entrance = Entity(5, 5, '[', (0, 255, 255), 'Entrance')
        exit_portal = Entity(10, 10, ']', (255, 255, 0), 'Exit')
        
        entrance.portal = Portal('entrance')
        exit_portal.portal = Portal('exit')
        entrance.portal.owner = entrance
        exit_portal.portal.owner = exit_portal
        entrance.portal.linked_portal = exit_portal.portal
        exit_portal.portal.linked_portal = entrance.portal
        entrance.portal.is_deployed = True
        exit_portal.portal.is_deployed = True
        
        entities = [monster, entrance, exit_portal, entry_item]
        
        # Should NOT teleport
        result = PortalManager.check_portal_collision(monster, entities)
        assert result is None
        assert monster.x == 5
        assert monster.y == 5
    
    def test_monster_needs_valid_linked_portal(self):
        """Monster shouldn't teleport if portal has no linked destination."""
        monster = Entity(5, 5, 'o', (100, 100, 100), 'Orc')
        monster.ai = BasicMonster()
        
        # Create broken portal pair
        entrance = Entity(5, 5, '[', (0, 255, 255), 'Entrance')
        entrance.portal = Portal('entrance')
        entrance.portal.owner = entrance
        entrance.portal.linked_portal = None  # No link!
        entrance.portal.is_deployed = True
        
        entities = [monster, entrance]
        
        # Should NOT teleport
        result = PortalManager.check_portal_collision(monster, entities)
        assert result is None
        assert monster.x == 5
        assert monster.y == 5


class TestMultipleMonsterPortalUsage:
    """Test scenarios with multiple monsters and portals."""
    
    def test_boss_ignores_portal_while_basic_monster_uses_it(self):
        """Different monster AI types should have different portal behavior."""
        boss = Entity(5, 5, 'B', (200, 50, 50), 'Boss')
        boss.ai = BossAI()
        
        basic = Entity(5, 5, 'o', (100, 100, 100), 'Orc')
        basic.ai = BasicMonster()
        
        # Create portal pair
        entrance = Entity(5, 5, '[', (0, 255, 255), 'Entrance')
        exit_portal = Entity(10, 10, ']', (255, 255, 0), 'Exit')
        
        entrance.portal = Portal('entrance')
        exit_portal.portal = Portal('exit')
        entrance.portal.owner = entrance
        exit_portal.portal.owner = exit_portal
        entrance.portal.linked_portal = exit_portal.portal
        exit_portal.portal.linked_portal = entrance.portal
        entrance.portal.is_deployed = True
        exit_portal.portal.is_deployed = True
        
        entities = [boss, basic, entrance, exit_portal]
        
        # Boss doesn't teleport
        boss_result = PortalManager.check_portal_collision(boss, entities)
        assert boss_result is None
        assert boss.x == 5
        
        # Reset basic monster position
        basic.x = 5
        basic.y = 5
        
        # Basic orc DOES teleport
        orc_result = PortalManager.check_portal_collision(basic, entities)
        assert orc_result is not None
        assert basic.x == 10
        assert basic.y == 10


class TestPortalUsableDefaultValues:
    """Test that all new AI instances get correct default portal_usable values."""
    
    def test_all_ai_classes_have_portal_usable(self):
        """Every AI class should have portal_usable attribute."""
        ai_classes = [
            (BasicMonster(), True),
            (BossAI(), False),
            (MindlessZombieAI(), True),
            (ConfusedMonster(BasicMonster()), False),
            (SlimeAI(), True),
        ]
        
        for ai, expected_value in ai_classes:
            assert hasattr(ai, 'portal_usable'), f"{ai.__class__.__name__} missing portal_usable"
            assert ai.portal_usable == expected_value, (
                f"{ai.__class__.__name__} portal_usable should be {expected_value}, "
                f"got {ai.portal_usable}"
            )


class TestPortalCollisionIntegrationWithEntityCache:
    """Test that portal collisions properly invalidate entity cache."""
    
    @patch('entity_sorting_cache.invalidate_entity_cache')
    def test_portal_teleportation_invalidates_cache(self, mock_invalidate):
        """Portal teleportation should invalidate entity cache."""
        monster = Entity(5, 5, 'o', (100, 100, 100), 'Orc')
        monster.ai = BasicMonster()
        
        entrance = Entity(5, 5, '[', (0, 255, 255), 'Entrance')
        exit_portal = Entity(10, 10, ']', (255, 255, 0), 'Exit')
        
        entrance.portal = Portal('entrance')
        exit_portal.portal = Portal('exit')
        entrance.portal.owner = entrance
        exit_portal.portal.owner = exit_portal
        entrance.portal.linked_portal = exit_portal.portal
        exit_portal.portal.linked_portal = entrance.portal
        entrance.portal.is_deployed = True
        exit_portal.portal.is_deployed = True
        
        entities = [monster, entrance, exit_portal]
        
        result = PortalManager.check_portal_collision(monster, entities)
        
        # Cache should be invalidated
        mock_invalidate.assert_called_once()
        assert result.get('teleported') is True

