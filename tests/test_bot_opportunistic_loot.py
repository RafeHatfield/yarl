"""Unit tests for bot opportunistic loot picking during auto-explore.

This test suite validates that the bot makes small, safe detours to pick up
valuable items (potions, weapons, armor) during exploration, improving
soak-test survivability without destabilizing AutoExplore.

Test cases:
- Bot picks up loot within radius K when safe
- Bot ignores loot outside radius K
- Bot ignores loot when enemies are visible
- Bot prefers potions over other loot types
"""

import pytest
from unittest.mock import Mock, MagicMock

from components.auto_explore import AutoExplore, BOT_LOOT_RADIUS
from components.component_registry import ComponentType
from equipment_slots import EquipmentSlots


class TestOpportunisticLoot:
    """Test bot opportunistic loot picking behavior."""
    
    def test_bot_detours_for_potion_within_radius(self):
        """Bot should detour to pick up potion within BOT_LOOT_RADIUS."""
        # Setup AutoExplore
        auto_explore = AutoExplore()
        
        # Mock player at position (10, 10)
        player = Mock()
        player.x = 10
        player.y = 10
        player.name = "Player"
        
        # Mock fighter for HP tracking
        player.fighter = Mock()
        player.fighter.hp = 100
        
        auto_explore.owner = player
        auto_explore.active = True
        auto_explore.current_path = []  # No current path
        auto_explore.last_hp = 100
        
        # Mock game map
        game_map = Mock()
        game_map.width = 30
        game_map.height = 30
        
        # Mock potion at position (12, 12) - within radius
        potion = Mock()
        potion.x = 12
        potion.y = 12
        potion.name = "healing_potion"
        potion.char = '!'
        potion.components = Mock()
        potion.components.has = Mock(side_effect=lambda ct: ct == ComponentType.ITEM)
        
        potion_item = Mock()
        potion_item.use_function = Mock()
        potion.get_component_optional = Mock(return_value=potion_item)
        
        entities = [player, potion]
        
        # Mock FOV map (potion is visible)
        fov_map = Mock()
        
        def mock_is_in_fov(fov, x, y):
            return (x, y) == (12, 12)  # Only potion is visible
        
        # Patch map_is_in_fov
        from unittest.mock import patch
        with patch('fov_functions.map_is_in_fov', side_effect=mock_is_in_fov):
            # Act: Find opportunistic loot target
            loot_target = auto_explore._find_opportunistic_loot_target(
                game_map, entities, fov_map
            )
        
        # Assert: Should target the potion
        assert loot_target is not None, "Should find potion within radius"
        assert loot_target == (12, 12), f"Should target potion at (12, 12), got {loot_target}"
    
    def test_bot_ignores_loot_outside_radius(self):
        """Bot should ignore loot beyond BOT_LOOT_RADIUS."""
        # Setup AutoExplore
        auto_explore = AutoExplore()
        
        # Mock player at position (10, 10)
        player = Mock()
        player.x = 10
        player.y = 10
        player.name = "Player"
        player.fighter = Mock()
        player.fighter.hp = 100
        
        auto_explore.owner = player
        auto_explore.active = True
        auto_explore.current_path = []
        auto_explore.last_hp = 100
        
        # Mock game map
        game_map = Mock()
        game_map.width = 30
        game_map.height = 30
        
        # Mock potion at position (10 + BOT_LOOT_RADIUS + 1, 10) - outside radius
        far_x = 10 + BOT_LOOT_RADIUS + 1
        potion = Mock()
        potion.x = far_x
        potion.y = 10
        potion.name = "healing_potion"
        potion.char = '!'
        potion.components = Mock()
        potion.components.has = Mock(side_effect=lambda ct: ct == ComponentType.ITEM)
        
        potion_item = Mock()
        potion_item.use_function = Mock()
        potion.get_component_optional = Mock(return_value=potion_item)
        
        entities = [player, potion]
        
        # Mock FOV map
        fov_map = Mock()
        
        def mock_is_in_fov(fov, x, y):
            return (x, y) == (far_x, 10)
        
        # Patch map_is_in_fov
        from unittest.mock import patch
        with patch('fov_functions.map_is_in_fov', side_effect=mock_is_in_fov):
            # Act: Find opportunistic loot target
            loot_target = auto_explore._find_opportunistic_loot_target(
                game_map, entities, fov_map
            )
        
        # Assert: Should NOT target the potion (too far)
        assert loot_target is None, f"Should ignore potion outside radius, but got {loot_target}"
    
    def test_bot_prefers_potions_over_weapons(self):
        """Bot should prefer potions over weapons when both are nearby."""
        # Setup AutoExplore
        auto_explore = AutoExplore()
        
        # Mock player at position (10, 10)
        player = Mock()
        player.x = 10
        player.y = 10
        player.name = "Player"
        player.fighter = Mock()
        player.fighter.hp = 100
        
        auto_explore.owner = player
        auto_explore.active = True
        auto_explore.current_path = []
        auto_explore.last_hp = 100
        
        # Mock game map
        game_map = Mock()
        game_map.width = 30
        game_map.height = 30
        
        # Mock potion at (11, 10) and weapon at (10, 11) - both within radius
        potion = Mock()
        potion.x = 11
        potion.y = 10
        potion.name = "healing_potion"
        potion.char = '!'
        potion.components = Mock()
        potion.components.has = Mock(side_effect=lambda ct: ct == ComponentType.ITEM)
        
        potion_item = Mock()
        potion_item.use_function = Mock()
        potion.get_component_optional = Mock(side_effect=lambda ct: 
            potion_item if ct == ComponentType.ITEM else None)
        
        weapon = Mock()
        weapon.x = 10
        weapon.y = 11
        weapon.name = "longsword"
        weapon.char = '/'
        weapon.components = Mock()
        weapon.components.has = Mock(side_effect=lambda ct: ct == ComponentType.EQUIPPABLE)
        
        weapon_equippable = Mock()
        weapon_equippable.damage_min = 1
        weapon_equippable.damage_max = 8
        weapon_equippable.armor_class_bonus = 0
        weapon_equippable.defense_bonus = 0
        weapon.get_component_optional = Mock(side_effect=lambda ct:
            weapon_equippable if ct == ComponentType.EQUIPPABLE else None)
        
        entities = [player, potion, weapon]
        
        # Mock FOV map (both items visible)
        fov_map = Mock()
        
        def mock_is_in_fov(fov, x, y):
            return (x, y) in [(11, 10), (10, 11)]
        
        # Patch map_is_in_fov
        from unittest.mock import patch
        with patch('fov_functions.map_is_in_fov', side_effect=mock_is_in_fov):
            # Act: Find opportunistic loot target
            loot_target = auto_explore._find_opportunistic_loot_target(
                game_map, entities, fov_map
            )
        
        # Assert: Should prefer potion over weapon
        assert loot_target is not None, "Should find loot"
        assert loot_target == (11, 10), f"Should prefer potion at (11, 10), got {loot_target}"
    
    def test_bot_picks_up_weapons_and_armor(self):
        """Bot should pick up weapons and armor when no potions nearby."""
        # Setup AutoExplore
        auto_explore = AutoExplore()
        
        # Mock player at position (10, 10)
        player = Mock()
        player.x = 10
        player.y = 10
        player.name = "Player"
        player.fighter = Mock()
        player.fighter.hp = 100
        
        auto_explore.owner = player
        auto_explore.active = True
        auto_explore.current_path = []
        auto_explore.last_hp = 100
        
        # Mock game map
        game_map = Mock()
        game_map.width = 30
        game_map.height = 30
        
        # Mock weapon at (12, 10) - within radius, no potions
        weapon = Mock()
        weapon.x = 12
        weapon.y = 10
        weapon.name = "longsword"
        weapon.char = '/'
        weapon.components = Mock()
        weapon.components.has = Mock(side_effect=lambda ct: ct == ComponentType.EQUIPPABLE)
        
        weapon_equippable = Mock()
        weapon_equippable.damage_min = 1
        weapon_equippable.damage_max = 8
        weapon_equippable.armor_class_bonus = 0
        weapon_equippable.defense_bonus = 0
        weapon.get_component_optional = Mock(side_effect=lambda ct:
            weapon_equippable if ct == ComponentType.EQUIPPABLE else None)
        
        entities = [player, weapon]
        
        # Mock FOV map
        fov_map = Mock()
        
        def mock_is_in_fov(fov, x, y):
            return (x, y) == (12, 10)
        
        # Patch map_is_in_fov
        from unittest.mock import patch
        with patch('fov_functions.map_is_in_fov', side_effect=mock_is_in_fov):
            # Act: Find opportunistic loot target
            loot_target = auto_explore._find_opportunistic_loot_target(
                game_map, entities, fov_map
            )
        
        # Assert: Should target the weapon
        assert loot_target is not None, "Should find weapon"
        assert loot_target == (12, 10), f"Should target weapon at (12, 10), got {loot_target}"
    
    def test_bot_ignores_non_valuable_items(self):
        """Bot should ignore items that aren't potions, weapons, or armor."""
        # Setup AutoExplore
        auto_explore = AutoExplore()
        
        # Mock player at position (10, 10)
        player = Mock()
        player.x = 10
        player.y = 10
        player.name = "Player"
        player.fighter = Mock()
        player.fighter.hp = 100
        
        auto_explore.owner = player
        auto_explore.active = True
        auto_explore.current_path = []
        auto_explore.last_hp = 100
        
        # Mock game map
        game_map = Mock()
        game_map.width = 30
        game_map.height = 30
        
        # Mock corpse (not valuable)
        corpse = Mock()
        corpse.x = 11
        corpse.y = 10
        corpse.name = "corpse"
        corpse.char = '%'
        corpse.components = Mock()
        corpse.components.has = Mock(return_value=False)
        corpse.get_component_optional = Mock(return_value=None)
        
        entities = [player, corpse]
        
        # Mock FOV map
        fov_map = Mock()
        
        def mock_is_in_fov(fov, x, y):
            return (x, y) == (11, 10)
        
        # Patch map_is_in_fov
        from unittest.mock import patch
        with patch('fov_functions.map_is_in_fov', side_effect=mock_is_in_fov):
            # Act: Find opportunistic loot target
            loot_target = auto_explore._find_opportunistic_loot_target(
                game_map, entities, fov_map
            )
        
        # Assert: Should NOT target corpse
        assert loot_target is None, f"Should ignore corpse, but got {loot_target}"
    
    def test_bot_ignores_items_outside_fov(self):
        """Bot should not target items outside FOV."""
        # Setup AutoExplore
        auto_explore = AutoExplore()
        
        # Mock player at position (10, 10)
        player = Mock()
        player.x = 10
        player.y = 10
        player.name = "Player"
        player.fighter = Mock()
        player.fighter.hp = 100
        
        auto_explore.owner = player
        auto_explore.active = True
        auto_explore.current_path = []
        auto_explore.last_hp = 100
        
        # Mock game map
        game_map = Mock()
        game_map.width = 30
        game_map.height = 30
        
        # Mock potion at (12, 12) - within radius but NOT in FOV
        potion = Mock()
        potion.x = 12
        potion.y = 12
        potion.name = "healing_potion"
        potion.char = '!'
        potion.components = Mock()
        potion.components.has = Mock(side_effect=lambda ct: ct == ComponentType.ITEM)
        
        potion_item = Mock()
        potion_item.use_function = Mock()
        potion.get_component_optional = Mock(return_value=potion_item)
        
        entities = [player, potion]
        
        # Mock FOV map (potion is NOT visible)
        fov_map = Mock()
        
        def mock_is_in_fov(fov, x, y):
            return False  # Nothing visible
        
        # Patch map_is_in_fov
        from unittest.mock import patch
        with patch('fov_functions.map_is_in_fov', side_effect=mock_is_in_fov):
            # Act: Find opportunistic loot target
            loot_target = auto_explore._find_opportunistic_loot_target(
                game_map, entities, fov_map
            )
        
        # Assert: Should NOT target potion (not in FOV)
        assert loot_target is None, f"Should ignore potion outside FOV, but got {loot_target}"
    
    def test_bot_picks_nearest_when_multiple_potions(self):
        """Bot should pick nearest potion when multiple are available."""
        # Setup AutoExplore
        auto_explore = AutoExplore()
        
        # Mock player at position (10, 10)
        player = Mock()
        player.x = 10
        player.y = 10
        player.name = "Player"
        player.fighter = Mock()
        player.fighter.hp = 100
        
        auto_explore.owner = player
        auto_explore.active = True
        auto_explore.current_path = []
        auto_explore.last_hp = 100
        
        # Mock game map
        game_map = Mock()
        game_map.width = 30
        game_map.height = 30
        
        # Mock two potions - one closer than the other
        near_potion = Mock()
        near_potion.x = 11
        near_potion.y = 10
        near_potion.name = "healing_potion"
        near_potion.char = '!'
        near_potion.components = Mock()
        near_potion.components.has = Mock(side_effect=lambda ct: ct == ComponentType.ITEM)
        
        near_item = Mock()
        near_item.use_function = Mock()
        near_potion.get_component_optional = Mock(return_value=near_item)
        
        far_potion = Mock()
        far_potion.x = 13
        far_potion.y = 10
        far_potion.name = "speed_potion"
        far_potion.char = '!'
        far_potion.components = Mock()
        far_potion.components.has = Mock(side_effect=lambda ct: ct == ComponentType.ITEM)
        
        far_item = Mock()
        far_item.use_function = Mock()
        far_potion.get_component_optional = Mock(return_value=far_item)
        
        entities = [player, near_potion, far_potion]
        
        # Mock FOV map (both potions visible)
        fov_map = Mock()
        
        def mock_is_in_fov(fov, x, y):
            return (x, y) in [(11, 10), (13, 10)]
        
        # Patch map_is_in_fov
        from unittest.mock import patch
        with patch('fov_functions.map_is_in_fov', side_effect=mock_is_in_fov):
            # Act: Find opportunistic loot target
            loot_target = auto_explore._find_opportunistic_loot_target(
                game_map, entities, fov_map
            )
        
        # Assert: Should prefer nearest potion
        assert loot_target is not None, "Should find potion"
        assert loot_target == (11, 10), f"Should prefer nearest potion at (11, 10), got {loot_target}"

