"""Tests for spell executor and spell casting."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from spells.spell_executor import SpellExecutor
from spells.spell_definition import SpellDefinition
from spells.spell_types import SpellCategory, TargetingType, DamageType
from spells import cast_spell_by_id, get_spell_registry
from spells.spell_catalog import register_all_spells
from entity import Entity
from components.fighter import Fighter


class TestSpellExecutor:
    """Tests for SpellExecutor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.executor = SpellExecutor()
        
        # Create test entities
        self.caster = Mock()
        self.caster.x = 5
        self.caster.y = 5
        self.caster.fighter = Mock()
        self.caster.distance_to = Mock(return_value=3)
        
        self.target = Mock()
        self.target.x = 8
        self.target.y = 8
        self.target.name = "Orc"
        self.target.fighter = Mock()
        self.target.fighter.take_damage = Mock(return_value=[])
        
        self.entities = [self.caster, self.target]
        
        # Mock FOV map
        self.fov_map = Mock()
        
        # Mock game map
        self.game_map = Mock()
        self.game_map.hazard_manager = Mock()
    
    def test_cast_returns_results(self):
        """Test that cast returns a list of results."""
        spell = SpellDefinition(
            spell_id="test",
            name="Test",
            category=SpellCategory.OFFENSIVE,
            targeting=TargetingType.SINGLE_ENEMY
        )
        
        with patch('spells.spell_executor.map_is_in_fov', return_value=True):
            results = self.executor.cast(
                spell,
                self.caster,
                self.entities,
                self.fov_map
            )
        
        assert isinstance(results, list)
        assert len(results) > 0
    
    @patch('spells.spell_executor.map_is_in_fov')
    def test_auto_target_spell_finds_closest_enemy(self, mock_fov):
        """Test that auto-targeting finds the closest visible enemy."""
        mock_fov.return_value = True
        
        spell = SpellDefinition(
            spell_id="lightning",
            name="Lightning",
            category=SpellCategory.OFFENSIVE,
            targeting=TargetingType.SINGLE_ENEMY,
            damage="2d6",
            max_range=10
        )
        
        with patch('spells.spell_executor.roll_dice', return_value=7):
            results = self.executor.cast(
                spell,
                self.caster,
                self.entities,
                self.fov_map
            )
        
        assert results[0]["consumed"] is True
        assert results[0]["target"] == self.target
        assert self.target.fighter.take_damage.called
    
    @patch('spells.spell_executor.map_is_in_fov')
    def test_auto_target_spell_fails_if_no_target(self, mock_fov):
        """Test that auto-targeting fails gracefully if no target in range."""
        mock_fov.return_value=False
        
        spell = SpellDefinition(
            spell_id="lightning",
            name="Lightning",
            category=SpellCategory.OFFENSIVE,
            targeting=TargetingType.SINGLE_ENEMY,
            damage="2d6",
            max_range=10,
            fail_message="No target!"
        )
        
        results = self.executor.cast(
            spell,
            self.caster,
            [self.caster],  # Only caster, no target
            self.fov_map
        )
        
        assert results[0]["consumed"] is False
        assert "No target!" in results[0]["message"].text
    
    @patch('spells.spell_executor.map_is_in_fov')
    def test_aoe_spell_requires_los(self, mock_fov):
        """Test that AoE spells check line of sight."""
        mock_fov.return_value = False  # Target not visible
        
        spell = SpellDefinition(
            spell_id="fireball",
            name="Fireball",
            category=SpellCategory.OFFENSIVE,
            targeting=TargetingType.AOE,
            damage="3d6",
            radius=3,
            requires_los=True
        )
        
        results = self.executor.cast(
            spell,
            self.caster,
            self.entities,
            self.fov_map,
            target_x=10,
            target_y=10
        )
        
        assert results[0]["consumed"] is False
        assert "field of view" in results[0]["message"].text.lower()
    
    @patch('spells.spell_executor.map_is_in_fov')
    def test_aoe_spell_damages_entities_in_radius(self, mock_fov):
        """Test that AoE spells damage all entities in radius."""
        mock_fov.return_value = True
        
        # Create multiple targets
        target1 = Mock()
        target1.x = 10
        target1.y = 10
        target1.name = "Orc1"
        target1.fighter = Mock()
        target1.fighter.take_damage = Mock(return_value=[])
        
        target2 = Mock()
        target2.x = 11
        target2.y = 10
        target2.name = "Orc2"
        target2.fighter = Mock()
        target2.fighter.take_damage = Mock(return_value=[])
        
        entities = [self.caster, target1, target2]
        
        spell = SpellDefinition(
            spell_id="fireball",
            name="Fireball",
            category=SpellCategory.OFFENSIVE,
            targeting=TargetingType.AOE,
            damage="3d6",
            radius=3,
            requires_los=True
        )
        
        with patch('spells.spell_executor.roll_dice', return_value=10):
            results = self.executor.cast(
                spell,
                self.caster,
                entities,
                self.fov_map,
                target_x=10,
                target_y=10
            )
        
        assert results[0]["consumed"] is True
        assert target1.fighter.take_damage.called
        assert target2.fighter.take_damage.called
    
    @patch('spells.spell_executor.map_is_in_fov')
    def test_aoe_spell_creates_ground_hazards(self, mock_fov):
        """Test that AoE spells create ground hazards when configured."""
        mock_fov.return_value = True
        
        spell = SpellDefinition(
            spell_id="fireball",
            name="Fireball",
            category=SpellCategory.OFFENSIVE,
            targeting=TargetingType.AOE,
            damage="3d6",
            radius=2,
            creates_hazard=True,
            hazard_type="fire",
            hazard_duration=3,
            hazard_damage=2
        )
        
        with patch('spells.spell_executor.roll_dice', return_value=10):
            results = self.executor.cast(
                spell,
                self.caster,
                self.entities,
                self.fov_map,
                game_map=self.game_map,
                target_x=10,
                target_y=10
            )
        
        # Should have called add_hazard multiple times (one for each tile in radius)
        assert self.game_map.hazard_manager.add_hazard.called
        assert self.game_map.hazard_manager.add_hazard.call_count > 5
    
    def test_healing_spell_restores_hp(self):
        """Test that healing spells restore HP."""
        self.caster.fighter.hp = 10
        self.caster.fighter.max_hp = 20
        self.caster.fighter.heal = Mock()
        
        spell = SpellDefinition(
            spell_id="heal",
            name="Heal",
            category=SpellCategory.HEALING,
            targeting=TargetingType.SELF,
            heal_amount=10
        )
        
        results = self.executor.cast(
            spell,
            self.caster,
            [],
            None
        )
        
        assert results[0]["consumed"] is True
        self.caster.fighter.heal.assert_called_once_with(10)
    
    def test_healing_spell_fails_at_full_health(self):
        """Test that healing fails when already at max HP."""
        self.caster.fighter.hp = 20
        self.caster.fighter.max_hp = 20
        
        spell = SpellDefinition(
            spell_id="heal",
            name="Heal",
            category=SpellCategory.HEALING,
            targeting=TargetingType.SELF,
            heal_amount=10
        )
        
        results = self.executor.cast(
            spell,
            self.caster,
            [],
            None
        )
        
        assert results[0]["consumed"] is False
        assert "full health" in results[0]["message"].text.lower()
    
    def test_bresenham_line(self):
        """Test Bresenham line calculation."""
        line = self.executor._bresenham_line(0, 0, 3, 3)
        
        assert (0, 0) in line
        assert (3, 3) in line
        assert len(line) == 4  # (0,0), (1,1), (2,2), (3,3)


class TestSpellIntegration:
    """Integration tests for the spell system."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        # Clear and re-register spells
        get_spell_registry().clear()
        register_all_spells()
        
        # Create real entities
        self.player = Entity(
            x=10, y=10, char="@", color=(255, 255, 255), name="Player",
            blocks=True, render_order=1,
            fighter=Fighter(hp=30, defense=2, power=5)
        )
        
        self.orc = Entity(
            x=12, y=12, char="o", color=(0, 255, 0), name="Orc",
            blocks=True, render_order=1,
            fighter=Fighter(hp=10, defense=0, power=3)
        )
        
        self.entities = [self.player, self.orc]
        
        # Mock FOV
        self.fov_map = Mock()
    
    @patch('spells.spell_executor.map_is_in_fov')
    @patch('spells.spell_executor.roll_dice')
    def test_cast_lightning_by_id(self, mock_roll, mock_fov):
        """Test casting lightning spell using convenience function."""
        mock_fov.return_value = True
        mock_roll.return_value = 10
        
        results = cast_spell_by_id(
            "lightning",
            self.player,
            entities=self.entities,
            fov_map=self.fov_map
        )
        
        assert len(results) > 0
        assert results[0]["consumed"] is True
        assert self.orc.fighter.hp < 10  # Took damage
    
    @patch('spells.spell_executor.map_is_in_fov')
    @patch('spells.spell_executor.roll_dice')
    def test_cast_fireball_by_id(self, mock_roll, mock_fov):
        """Test casting fireball spell using convenience function."""
        mock_fov.return_value = True
        mock_roll.return_value = 10
        
        game_map = Mock()
        game_map.hazard_manager = Mock()
        
        results = cast_spell_by_id(
            "fireball",
            self.player,
            entities=self.entities,
            fov_map=self.fov_map,
            game_map=game_map,
            target_x=12,
            target_y=12
        )
        
        assert len(results) > 0
        assert results[0]["consumed"] is True
        assert self.orc.fighter.hp < 10  # Took damage
        assert game_map.hazard_manager.add_hazard.called
    
    def test_cast_heal_by_id(self):
        """Test casting heal spell using convenience function."""
        self.player.fighter.hp = 10
        
        results = cast_spell_by_id(
            "heal",
            self.player,
            entities=[],
            fov_map=None
        )
        
        assert len(results) > 0
        assert results[0]["consumed"] is True
        assert self.player.fighter.hp > 10  # HP increased
    
    def test_cast_unknown_spell_fails(self):
        """Test that casting an unknown spell fails gracefully."""
        results = cast_spell_by_id(
            "nonexistent_spell",
            self.player,
            entities=[],
            fov_map=None
        )
        
        assert results[0]["consumed"] is False
        assert "Unknown spell" in results[0]["message"].text

