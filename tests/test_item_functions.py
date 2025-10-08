"""
Unit tests for item_functions.py

Tests all item functions with various inputs and edge cases.
"""

import pytest
from unittest.mock import Mock, patch
from item_functions import heal, cast_lightning, cast_fireball, cast_confuse
from components.ai import BasicMonster, ConfusedMonster
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
        assert results[0]["consumed"] is False  # Don't consume when at full health
        assert "message" in results[0]
        assert "full health" in results[0]["message"].text
        assert player_entity.fighter.hp == original_hp  # HP shouldn't exceed max

    def test_heal_injured_entity(self, player_entity, mock_libtcod):
        """Test healing an injured entity."""
        # Arrange
        player_entity.fighter.hp = 10  # Injured

        # Act
        results = heal(player_entity, amount=15)

        # Assert
        assert len(results) == 1
        assert results[0]["consumed"] is True
        assert "message" in results[0]
        assert player_entity.fighter.hp == 25  # 10 + 15

    def test_heal_zero_amount(self, player_entity, mock_libtcod):
        """Test healing with zero amount."""
        # Arrange
        player_entity.fighter.hp = 20  # Damage entity so it's not at full health
        original_hp = player_entity.fighter.hp

        # Act
        results = heal(player_entity, amount=0)

        # Assert
        assert len(results) == 1
        assert results[0]["consumed"] is True  # Consumes because not at full health
        assert player_entity.fighter.hp == original_hp  # No healing effect

    def test_heal_negative_amount(self, player_entity, mock_libtcod):
        """Test healing with negative amount (actually damages due to current implementation)."""
        # Arrange
        player_entity.fighter.hp = 20  # Damage entity so it's not at full health
        original_hp = player_entity.fighter.hp

        # Act
        results = heal(player_entity, amount=-5)

        # Assert
        assert len(results) == 1
        assert results[0]["consumed"] is True  # Consumes because not at full health
        # Note: Current implementation allows negative healing (damages)
        assert player_entity.fighter.hp == original_hp - 5  # 20 - 5 = 15

    def test_heal_massive_amount(self, player_entity, mock_libtcod):
        """Test healing with amount exceeding max HP."""
        # Arrange
        player_entity.fighter.hp = 1
        max_hp = player_entity.fighter.max_hp

        # Act
        results = heal(player_entity, amount=1000)

        # Assert
        assert len(results) == 1
        assert results[0]["consumed"] is True
        assert player_entity.fighter.hp == max_hp


class TestCastLightning:
    """Test the cast_lightning function."""

    def test_lightning_with_valid_target_in_range(
        self, player_entity, enemy_entity, mock_entities, mock_fov_map, mock_libtcod
    ):
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
            maximum_range=5,
        )

        # Assert
        assert len(results) >= 1
        consumed_result = next((r for r in results if "consumed" in r), None)
        assert consumed_result is not None
        assert consumed_result["consumed"] is True
        assert "message" in consumed_result

    def test_lightning_no_targets_in_range(
        self, player_entity, enemy_entity, mock_fov_map, mock_libtcod
    ):
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
            maximum_range=5,
        )

        # Assert
        assert len(results) == 1
        assert results[0]["consumed"] is False
        assert "message" in results[0]

    def test_lightning_target_out_of_fov(
        self, player_entity, enemy_entity, mock_fov_map, mock_libtcod
    ):
        """Test lightning bolt with target out of field of view."""
        # Arrange
        enemy_entity.x = 12
        enemy_entity.y = 12
        entities = [player_entity, enemy_entity]

        # Act
        with patch("spells.spell_executor.map_is_in_fov", return_value=False):
            results = cast_lightning(
                player_entity,
                entities=entities,
                fov_map=mock_fov_map,
                damage=10,
                maximum_range=5,
            )

        # Assert
        assert len(results) == 1
        assert results[0]["consumed"] is False

    def test_lightning_zero_damage(
        self, player_entity, enemy_entity, mock_entities, mock_fov_map, mock_libtcod
    ):
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
            maximum_range=5,
        )

        # Assert
        assert len(results) >= 1
        # Enemy should still be alive with same HP
        assert enemy_entity.fighter.hp == original_hp

    def test_lightning_negative_range(
        self, player_entity, enemy_entity, mock_fov_map, mock_libtcod
    ):
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
            maximum_range=-1,
        )

        # Assert
        assert len(results) == 1
        assert results[0]["consumed"] is False


class TestCastFireball:
    """Test the cast_fireball function."""

    def test_fireball_valid_target_in_fov(
        self, player_entity, enemy_entity, mock_fov_map, mock_libtcod
    ):
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
            target_y=target_y,
        )

        # Assert
        assert len(results) >= 1
        consumed_result = next((r for r in results if "consumed" in r), None)
        assert consumed_result is not None
        assert consumed_result["consumed"] is True

    def test_fireball_target_out_of_fov(
        self, player_entity, enemy_entity, mock_fov_map, mock_libtcod
    ):
        """Test fireball with target outside field of view."""
        # Arrange
        entities = [player_entity, enemy_entity]
        target_x, target_y = 20, 20

        # Act
        with patch("spells.spell_executor.map_is_in_fov", return_value=False):
            results = cast_fireball(
                player_entity,
                entities=entities,
                fov_map=mock_fov_map,
                damage=12,
                radius=3,
                target_x=target_x,
                target_y=target_y,
            )

        # Assert
        assert len(results) == 1
        assert results[0]["consumed"] is False
        assert "cannot target" in results[0]["message"].text.lower()

    def test_fireball_area_damage(self, player_entity, mock_fov_map, mock_libtcod):
        """Test fireball damages multiple entities in area."""
        # Arrange
        # Create multiple enemies within fireball radius
        enemy1 = Entity(
            14,
            14,
            "o",
            mock_libtcod.red,
            "Orc1",
            blocks=True,
            render_order=RenderOrder.ACTOR,
            fighter=Fighter(hp=10, defense=0, power=1),
        )
        enemy2 = Entity(
            16,
            16,
            "o",
            mock_libtcod.red,
            "Orc2",
            blocks=True,
            render_order=RenderOrder.ACTOR,
            fighter=Fighter(hp=10, defense=0, power=1),
        )
        enemy3 = Entity(
            25,
            25,
            "o",
            mock_libtcod.red,
            "Orc3",
            blocks=True,  # Far away
            render_order=RenderOrder.ACTOR,
            fighter=Fighter(hp=10, defense=0, power=1),
        )

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
            target_y=target_y,
        )

        # Assert
        assert len(results) >= 2  # At least consumed + damage messages
        damage_messages = [
            r
            for r in results
            if "message" in r and "burned" in r["message"].text.lower()
        ]
        assert len(damage_messages) >= 2  # Should hit enemy1 and enemy2, not enemy3

    def test_fireball_zero_radius(
        self, player_entity, enemy_entity, mock_fov_map, mock_libtcod
    ):
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
            target_y=target_y,
        )

        # Assert
        assert len(results) >= 1
        consumed_result = next((r for r in results if "consumed" in r), None)
        assert consumed_result["consumed"] is True

    def test_fireball_none_coordinates(
        self, player_entity, enemy_entity, mock_fov_map, mock_libtcod
    ):
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
                target_y=None,
            )

    def test_fireball_zero_damage(
        self, player_entity, enemy_entity, mock_fov_map, mock_libtcod
    ):
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
            target_y=target_y,
        )

        # Assert
        assert len(results) >= 1
        consumed_result = next((r for r in results if "consumed" in r), None)
        assert consumed_result["consumed"] is True
        # Enemy should be unharmed
        assert enemy_entity.fighter.hp == original_hp

    # DELETED: test_fireball_negative_damage
    # This was testing a bug where negative damage would heal enemies.
    # The new spell system correctly rejects negative damage as invalid.


class TestItemFunctionEdgeCases:
    """Test edge cases and error conditions for item functions."""

    def test_functions_with_missing_kwargs(self, player_entity, mock_libtcod):
        """Test item functions gracefully handle missing required kwargs."""
        # Test heal without amount on full health entity
        results = heal(player_entity)
        assert len(results) == 1
        assert results[0]["consumed"] is False  # Not consumed when at full health

        # Test lightning without required kwargs - should gracefully handle
        # New spell system returns error messages instead of raising TypeError
        results = cast_lightning(player_entity, entities=[])
        assert len(results) >= 1
        assert results[0]["consumed"] is False  # Spell not consumed on error
        
        # Note: Spell system gracefully handles missing parameters with error messages

    def test_functions_with_none_entities(
        self, player_entity, mock_fov_map, mock_libtcod
    ):
        """Test item functions with None entities list."""
        # Lightning with None entities
        results = cast_lightning(
            player_entity,
            entities=None,
            fov_map=mock_fov_map,
            damage=10,
            maximum_range=5,
        )
        assert len(results) == 1
        assert results[0]["consumed"] is False

        # Fireball with None entities
        results = cast_fireball(
            player_entity,
            entities=None,
            fov_map=mock_fov_map,
            damage=10,
            radius=3,
            target_x=10,
            target_y=10,
        )
        assert len(results) >= 1


class TestCastConfuse:
    """Test cast_confuse function behavior."""

    def test_confuse_valid_target_in_fov(
        self, player_entity, enemy_entity, mock_fov_map, mock_libtcod
    ):
        """Test confuse spell with valid target coordinates in FOV."""
        # Arrange
        entities = [player_entity, enemy_entity]
        target_x, target_y = 15, 15

        # Act
        results = cast_confuse(
            entities=entities,
            fov_map=mock_fov_map,
            target_x=target_x,
            target_y=target_y,
        )

        # Assert
        assert len(results) == 1
        assert results[0]["consumed"] is True
        assert "message" in results[0]
        assert "look vacant" in results[0]["message"].text
        assert isinstance(enemy_entity.ai, ConfusedMonster)
        assert enemy_entity.ai.number_of_turns == 10

    def test_confuse_target_outside_fov(
        self, player_entity, enemy_entity, mock_libtcod
    ):
        """Test confuse spell with target outside FOV."""
        # Arrange
        entities = [player_entity, enemy_entity]
        target_x, target_y = 15, 15
        mock_fov_map = Mock()

        # Mock FOV check to return False (outside FOV)
        with patch("spells.spell_executor.map_is_in_fov", return_value=False):
            # Act
            results = cast_confuse(
                entities=entities,
                fov_map=mock_fov_map,
                target_x=target_x,
                target_y=target_y,
            )

        # Assert
        assert len(results) == 1
        assert results[0]["consumed"] is False
        assert "outside your field of view" in results[0]["message"].text

    def test_confuse_no_enemy_at_target_location(
        self, player_entity, mock_fov_map, mock_libtcod
    ):
        """Test confuse spell when no enemy exists at target location."""
        # Arrange
        entities = [player_entity]  # Only player, no enemy at target
        target_x, target_y = 20, 20

        # Act
        results = cast_confuse(
            entities=entities,
            fov_map=mock_fov_map,
            target_x=target_x,
            target_y=target_y,
        )

        # Assert
        assert len(results) == 1
        assert results[0]["consumed"] is False
        assert "no targetable enemy" in results[0]["message"].text

    def test_confuse_target_without_ai(self, player_entity, mock_fov_map, mock_libtcod):
        """Test confuse spell on entity without AI component."""
        # Arrange
        # Create an entity without AI (like an item)
        item_entity = Entity(15, 15, "!", mock_libtcod.violet, "Potion")
        entities = [player_entity, item_entity]
        target_x, target_y = 15, 15

        # Act
        results = cast_confuse(
            entities=entities,
            fov_map=mock_fov_map,
            target_x=target_x,
            target_y=target_y,
        )

        # Assert
        assert len(results) == 1
        assert results[0]["consumed"] is False
        assert "no targetable enemy" in results[0]["message"].text

    def test_confuse_preserves_previous_ai(
        self, player_entity, mock_fov_map, mock_libtcod
    ):
        """Test confuse spell preserves the original AI."""
        # Arrange
        original_ai = BasicMonster()
        enemy_entity = Entity(15, 15, "o", mock_libtcod.red, "Orc", ai=original_ai)
        entities = [player_entity, enemy_entity]
        target_x, target_y = 15, 15

        # Act
        results = cast_confuse(
            entities=entities,
            fov_map=mock_fov_map,
            target_x=target_x,
            target_y=target_y,
        )

        # Assert
        assert len(results) == 1
        assert results[0]["consumed"] is True
        confused_ai = enemy_entity.ai
        assert isinstance(confused_ai, ConfusedMonster)
        assert confused_ai.previous_ai == original_ai
        assert confused_ai.owner == enemy_entity

    def test_confuse_multiple_entities_at_same_location(
        self, player_entity, mock_fov_map, mock_libtcod
    ):
        """Test confuse spell when multiple entities are at target location."""
        # Arrange
        enemy1 = Entity(15, 15, "o", mock_libtcod.red, "Orc1", ai=BasicMonster())
        enemy2 = Entity(15, 15, "g", mock_libtcod.green, "Goblin", ai=BasicMonster())
        entities = [player_entity, enemy1, enemy2]
        target_x, target_y = 15, 15

        # Act
        results = cast_confuse(
            entities=entities,
            fov_map=mock_fov_map,
            target_x=target_x,
            target_y=target_y,
        )

        # Assert
        assert len(results) == 1
        assert results[0]["consumed"] is True
        # Should confuse the first enemy found (enemy1)
        assert isinstance(enemy1.ai, ConfusedMonster)
        # Second enemy should remain unchanged
        assert isinstance(enemy2.ai, BasicMonster)

    def test_confuse_already_confused_monster(
        self, player_entity, mock_fov_map, mock_libtcod
    ):
        """Test confuse spell on already confused monster."""
        # Arrange
        original_ai = BasicMonster()
        confused_ai = ConfusedMonster(original_ai, number_of_turns=5)
        enemy_entity = Entity(
            15, 15, "o", mock_libtcod.red, "Confused Orc", ai=confused_ai
        )
        entities = [player_entity, enemy_entity]
        target_x, target_y = 15, 15

        # Act
        results = cast_confuse(
            entities=entities,
            fov_map=mock_fov_map,
            target_x=target_x,
            target_y=target_y,
        )

        # Assert
        assert len(results) == 1
        assert results[0]["consumed"] is True
        # Should create a NEW confused AI, replacing the old one
        new_confused_ai = enemy_entity.ai
        assert isinstance(new_confused_ai, ConfusedMonster)
        assert new_confused_ai != confused_ai  # Different instance
        assert new_confused_ai.number_of_turns == 10  # Fresh confusion

    def test_confuse_with_none_coordinates(
        self, player_entity, enemy_entity, mock_libtcod
    ):
        """Test confuse spell with None coordinates."""
        # Arrange
        entities = [player_entity, enemy_entity]
        mock_fov_map = Mock()

        # Mock FOV to handle None coordinates gracefully
        with patch("item_functions.libtcod") as mock_tcod:
            mock_tcod.map_is_in_fov.return_value = False
            mock_tcod.yellow = mock_libtcod.yellow

            # Act
            results = cast_confuse(
                entities=entities, fov_map=mock_fov_map, target_x=None, target_y=None
            )

        # Assert
        assert len(results) == 1
        assert results[0]["consumed"] is False

    def test_confuse_empty_entities_list(self, mock_fov_map, mock_libtcod):
        """Test confuse spell with empty entities list."""
        # Arrange
        entities = []
        target_x, target_y = 15, 15

        # Act
        results = cast_confuse(
            entities=entities,
            fov_map=mock_fov_map,
            target_x=target_x,
            target_y=target_y,
        )

        # Assert
        assert len(results) == 1
        assert results[0]["consumed"] is False
        assert "no targetable enemy" in results[0]["message"].text

    def test_confuse_with_missing_kwargs(self, mock_libtcod):
        """Test confuse spell with missing required parameters."""
        # Act - Missing entities causes TypeError in actual code
        with pytest.raises(TypeError):
            cast_confuse(fov_map=Mock(), target_x=10, target_y=10)

    def test_confuse_message_content(self, player_entity, mock_fov_map, mock_libtcod):
        """Test confuse spell produces correct message content."""
        # Arrange
        enemy_entity = Entity(
            15, 15, "o", mock_libtcod.red, "TestOrc", ai=BasicMonster()
        )
        entities = [player_entity, enemy_entity]
        target_x, target_y = 15, 15

        # Act
        results = cast_confuse(
            entities=entities,
            fov_map=mock_fov_map,
            target_x=target_x,
            target_y=target_y,
        )

        # Assert
        assert len(results) == 1
        assert results[0]["consumed"] is True
        message = results[0]["message"]
        assert "TestOrc" in message.text
        assert "eyes" in message.text
        assert "vacant" in message.text
        assert "stumble" in message.text
