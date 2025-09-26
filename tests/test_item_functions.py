"""
Unit tests for item_functions.py

Tests all item functions with various inputs and edge cases.
"""
import pytest
from unittest.mock import Mock, patch
from item_functions import heal, cast_lightning, cast_fireball
from game_messages import Message
from components.fighter import Fighter
from entity import Entity
from render_functions import RenderOrder


class TestHealFunction:
    """Test the heal function with various scenarios."""
    
    def test_heal_full_health_entity(self, player_entity, mock_libtcod):
        """Test healing an entity that's already at full health."""
        # Arrange
        player_entity.fighter.hp = player_entity.fighter.max_hp
        original_hp = player_entity.fighter.hp
        
        # Act
        results = heal(player_entity, amount=10)
        
        # Assert
        assert len(results) == 1
        assert results[0]['consumed'] is True
        assert 'message' in results[0]
        assert player_entity.fighter.hp == original_hp  # HP shouldn't exceed max

    def test_heal_injured_entity(self, player_entity, mock_libtcod):
        """Test healing an injured entity."""
        # Arrange
        player_entity.fighter.hp = 10  # Injured
        
        # Act
        results = heal(player_entity, amount=15)
        
        # Assert
        assert len(results) == 1
        assert results[0]['consumed'] is True
        assert 'message' in results[0]
        assert player_entity.fighter.hp == 25  # 10 + 15

    def test_heal_zero_amount(self, player_entity, mock_libtcod):
        """Test healing with zero amount."""
        # Arrange
        original_hp = player_entity.fighter.hp
        
        # Act
        results = heal(player_entity, amount=0)
        
        # Assert
        assert len(results) == 1
        assert results[0]['consumed'] is True
        assert player_entity.fighter.hp == original_hp

    def test_heal_negative_amount(self, player_entity, mock_libtcod):
        """Test healing with negative amount (shouldn't damage)."""
        # Arrange
        original_hp = player_entity.fighter.hp
        
        # Act
        results = heal(player_entity, amount=-5)
        
        # Assert
        assert len(results) == 1
        assert results[0]['consumed'] is True
        assert player_entity.fighter.hp == original_hp

    def test_heal_massive_amount(self, player_entity, mock_libtcod):
        """Test healing with amount exceeding max HP."""
        # Arrange
        player_entity.fighter.hp = 1
        max_hp = player_entity.fighter.max_hp
        
        # Act
        results = heal(player_entity, amount=1000)
        
        # Assert
        assert len(results) == 1
        assert results[0]['consumed'] is True
        assert player_entity.fighter.hp == max_hp


class TestCastLightning:
    """Test the cast_lightning function."""
    
    def test_lightning_with_valid_target_in_range(self, player_entity, enemy_entity, mock_entities, mock_fov_map, mock_libtcod):
        """Test lightning bolt hitting a target in range."""
        # Arrange
        # Place enemy close to player
        enemy_entity.x = 12
        enemy_entity.y = 12
        entities = [player_entity, enemy_entity]
        
        # Act
        results = cast_lightning(
            player_entity,
            entities=entities,
            fov_map=mock_fov_map,
            damage=10,
            maximum_range=5
        )
        
        # Assert
        assert len(results) >= 1
        consumed_result = next((r for r in results if 'consumed' in r), None)
        assert consumed_result is not None
        assert consumed_result['consumed'] is True
        assert 'message' in consumed_result

    def test_lightning_no_targets_in_range(self, player_entity, enemy_entity, mock_fov_map, mock_libtcod):
        """Test lightning bolt with no valid targets in range."""
        # Arrange
        # Place enemy far from player
        enemy_entity.x = 50
        enemy_entity.y = 50
        entities = [player_entity, enemy_entity]
        
        # Act
        results = cast_lightning(
            player_entity,
            entities=entities,
            fov_map=mock_fov_map,
            damage=10,
            maximum_range=5
        )
        
        # Assert
        assert len(results) == 1
        assert results[0]['consumed'] is False
        assert 'message' in results[0]

    def test_lightning_target_out_of_fov(self, player_entity, enemy_entity, mock_fov_map, mock_libtcod):
        """Test lightning bolt with target out of field of view."""
        # Arrange
        mock_libtcod.map_is_in_fov.return_value = False
        enemy_entity.x = 12
        enemy_entity.y = 12
        entities = [player_entity, enemy_entity]
        
        # Act
        results = cast_lightning(
            player_entity,
            entities=entities,
            fov_map=mock_fov_map,
            damage=10,
            maximum_range=5
        )
        
        # Assert
        assert len(results) == 1
        assert results[0]['consumed'] is False

    def test_lightning_zero_damage(self, player_entity, enemy_entity, mock_entities, mock_fov_map, mock_libtcod):
        """Test lightning bolt with zero damage."""
        # Arrange
        enemy_entity.x = 12
        enemy_entity.y = 12
        entities = [player_entity, enemy_entity]
        original_hp = enemy_entity.fighter.hp
        
        # Act
        results = cast_lightning(
            player_entity,
            entities=entities,
            fov_map=mock_fov_map,
            damage=0,
            maximum_range=5
        )
        
        # Assert
        assert len(results) >= 1
        # Enemy should still be alive with same HP
        assert enemy_entity.fighter.hp == original_hp

    def test_lightning_negative_range(self, player_entity, enemy_entity, mock_fov_map, mock_libtcod):
        """Test lightning bolt with negative maximum range."""
        # Arrange
        enemy_entity.x = 11
        enemy_entity.y = 11
        entities = [player_entity, enemy_entity]
        
        # Act
        results = cast_lightning(
            player_entity,
            entities=entities,
            fov_map=mock_fov_map,
            damage=10,
            maximum_range=-1
        )
        
        # Assert
        assert len(results) == 1
        assert results[0]['consumed'] is False


class TestCastFireball:
    """Test the cast_fireball function."""
    
    def test_fireball_valid_target_in_fov(self, player_entity, enemy_entity, mock_fov_map, mock_libtcod):
        """Test fireball with valid target coordinates in FOV."""
        # Arrange
        entities = [player_entity, enemy_entity]
        target_x, target_y = 15, 15
        
        # Act
        results = cast_fireball(
            player_entity,
            entities=entities,
            fov_map=mock_fov_map,
            damage=12,
            radius=3,
            target_x=target_x,
            target_y=target_y
        )
        
        # Assert
        assert len(results) >= 1
        consumed_result = next((r for r in results if 'consumed' in r), None)
        assert consumed_result is not None
        assert consumed_result['consumed'] is True

    def test_fireball_target_out_of_fov(self, player_entity, enemy_entity, mock_fov_map, mock_libtcod):
        """Test fireball with target outside field of view."""
        # Arrange
        mock_libtcod.map_is_in_fov.return_value = False
        entities = [player_entity, enemy_entity]
        target_x, target_y = 20, 20
        
        # Act
        results = cast_fireball(
            player_entity,
            entities=entities,
            fov_map=mock_fov_map,
            damage=12,
            radius=3,
            target_x=target_x,
            target_y=target_y
        )
        
        # Assert
        assert len(results) == 1
        assert results[0]['consumed'] is False
        assert 'cannot target' in results[0]['message'].text.lower()

    def test_fireball_area_damage(self, player_entity, mock_fov_map, mock_libtcod):
        """Test fireball damages multiple entities in area."""
        # Arrange
        # Create multiple enemies within fireball radius
        enemy1 = Entity(14, 14, 'o', mock_libtcod.red, 'Orc1', blocks=True, 
                       render_order=RenderOrder.ACTOR, fighter=Fighter(hp=10, defense=0, power=1))
        enemy2 = Entity(16, 16, 'o', mock_libtcod.red, 'Orc2', blocks=True,
                       render_order=RenderOrder.ACTOR, fighter=Fighter(hp=10, defense=0, power=1))
        enemy3 = Entity(25, 25, 'o', mock_libtcod.red, 'Orc3', blocks=True,  # Far away
                       render_order=RenderOrder.ACTOR, fighter=Fighter(hp=10, defense=0, power=1))
        
        entities = [player_entity, enemy1, enemy2, enemy3]
        target_x, target_y = 15, 15
        
        # Act
        results = cast_fireball(
            player_entity,
            entities=entities,
            fov_map=mock_fov_map,
            damage=12,
            radius=3,
            target_x=target_x,
            target_y=target_y
        )
        
        # Assert
        assert len(results) >= 2  # At least consumed + damage messages
        damage_messages = [r for r in results if 'message' in r and 'burned' in r['message'].text.lower()]
        assert len(damage_messages) >= 2  # Should hit enemy1 and enemy2, not enemy3

    def test_fireball_zero_radius(self, player_entity, enemy_entity, mock_fov_map, mock_libtcod):
        """Test fireball with zero radius."""
        # Arrange
        entities = [player_entity, enemy_entity]
        target_x, target_y = 15, 15  # Enemy location
        
        # Act
        results = cast_fireball(
            player_entity,
            entities=entities,
            fov_map=mock_fov_map,
            damage=12,
            radius=0,
            target_x=target_x,
            target_y=target_y
        )
        
        # Assert
        assert len(results) >= 1
        consumed_result = next((r for r in results if 'consumed' in r), None)
        assert consumed_result['consumed'] is True

    def test_fireball_none_coordinates(self, player_entity, enemy_entity, mock_fov_map, mock_libtcod):
        """Test fireball with None coordinates."""
        # Arrange
        entities = [player_entity, enemy_entity]
        
        # Act & Assert
        with pytest.raises(TypeError):
            cast_fireball(
                player_entity,
                entities=entities,
                fov_map=mock_fov_map,
                damage=12,
                radius=3,
                target_x=None,
                target_y=None
            )

    def test_fireball_zero_damage(self, player_entity, enemy_entity, mock_fov_map, mock_libtcod):
        """Test fireball with zero damage."""
        # Arrange
        entities = [player_entity, enemy_entity]
        target_x, target_y = 15, 15
        original_hp = enemy_entity.fighter.hp
        
        # Act
        results = cast_fireball(
            player_entity,
            entities=entities,
            fov_map=mock_fov_map,
            damage=0,
            radius=3,
            target_x=target_x,
            target_y=target_y
        )
        
        # Assert
        assert len(results) >= 1
        consumed_result = next((r for r in results if 'consumed' in r), None)
        assert consumed_result['consumed'] is True
        # Enemy should be unharmed
        assert enemy_entity.fighter.hp == original_hp

    def test_fireball_negative_damage(self, player_entity, enemy_entity, mock_fov_map, mock_libtcod):
        """Test fireball with negative damage."""
        # Arrange
        entities = [player_entity, enemy_entity]
        target_x, target_y = 15, 15
        original_hp = enemy_entity.fighter.hp
        
        # Act
        results = cast_fireball(
            player_entity,
            entities=entities,
            fov_map=mock_fov_map,
            damage=-5,
            radius=3,
            target_x=target_x,
            target_y=target_y
        )
        
        # Assert
        assert len(results) >= 1
        consumed_result = next((r for r in results if 'consumed' in r), None)
        assert consumed_result['consumed'] is True
        # Enemy should be unharmed (negative damage shouldn't heal)
        assert enemy_entity.fighter.hp == original_hp


class TestItemFunctionEdgeCases:
    """Test edge cases and error conditions for item functions."""
    
    def test_functions_with_missing_kwargs(self, player_entity, mock_libtcod):
        """Test item functions with missing required kwargs."""
        # Test heal without amount
        results = heal(player_entity)
        assert len(results) == 1
        assert results[0]['consumed'] is True
        
        # Test lightning without damage
        results = cast_lightning(player_entity, entities=[])
        assert len(results) == 1
        
        # Test fireball without damage/radius
        results = cast_fireball(player_entity, entities=[], target_x=10, target_y=10)
        assert len(results) >= 1

    def test_functions_with_none_entities(self, player_entity, mock_fov_map, mock_libtcod):
        """Test item functions with None entities list."""
        # Lightning with None entities
        results = cast_lightning(player_entity, entities=None, fov_map=mock_fov_map, damage=10, maximum_range=5)
        assert len(results) == 1
        assert results[0]['consumed'] is False
        
        # Fireball with None entities  
        results = cast_fireball(player_entity, entities=None, fov_map=mock_fov_map, damage=10, radius=3, target_x=10, target_y=10)
        assert len(results) >= 1
