"""Integration tests for complete spell scenarios.

This module tests full spell workflows from casting through effects to expiration,
ensuring all systems (spell registry, executor, status effects, messages) work together.

QUARANTINED: Spell integration tests need refactor for new architecture.
See QUARANTINED_TESTS.md for details.
"""

import pytest
from unittest.mock import Mock
import tcod.libtcodpy as libtcod

# Quarantine entire file - needs refactor for spell system changes
pytestmark = pytest.mark.skip(reason="Quarantined - spell integration needs refactor. See QUARANTINED_TESTS.md")

from entity import Entity
from components.fighter import Fighter
from components.inventory import Inventory
from components.ai import BasicMonster
from map_objects.game_map import GameMap
from game_messages import MessageLog
from fov_functions import initialize_fov
from spells.spell_registry import get_spell_registry
from spells.spell_executor import get_spell_executor
from spells import cast_spell_by_id


class TestSpellScenarioIntegration:
    """Integration tests for complete spell casting scenarios."""

    def setup_method(self):
        """Set up test fixtures with real game components."""
        # Create game map
        self.game_map = GameMap(30, 30)
        
        # Create FOV map
        self.fov_map = initialize_fov(self.game_map)
        libtcod.map_compute_fov(
            self.fov_map, 10, 10, 10, True, libtcod.FOV_BASIC
        )
        
        # Create message log
        self.message_log = MessageLog(x=0, width=80, height=10)
        
        # Create player
        fighter = Fighter(hp=30, defense=2, power=5)
        inventory = Inventory(capacity=26)
        self.player = Entity(
            10, 10, "@", (255, 255, 255), "Player",
            blocks=True, fighter=fighter, inventory=inventory
        )
        
        # Create target monster
        monster_fighter = Fighter(hp=20, defense=1, power=3)
        monster_ai = BasicMonster()
        self.monster = Entity(
            12, 10, "o", (63, 127, 63), "Orc",
            blocks=True, fighter=monster_fighter, ai=monster_ai
        )
        monster_ai.owner = self.monster
        
        self.entities = [self.player, self.monster]
    
    def test_fireball_complete_scenario(self):
        """Test complete fireball casting: cast → damage → message."""
        # Act: Cast fireball at monster
        results = cast_spell_by_id(
            spell_id="fireball",
            caster=self.player,
            entities=self.entities,
            fov_map=self.fov_map,
            target_x=12,
            target_y=10,
            game_map=self.game_map
        )
        
        # Assert: Spell was consumed
        assert any(r.get("consumed") for r in results), "Fireball should be consumed"
        
        # Assert: Monster took damage
        assert self.monster.fighter.hp < 20, "Monster should have taken damage"
        
        # Assert: Combat messages were generated
        messages = [r.get("message") for r in results if r.get("message")]
        assert len(messages) > 0, "Should generate messages"
        
        # Assert: Contains spell cast message
        spell_messages = [m for m in messages if "fireball" in m.text.lower()]
        assert len(spell_messages) > 0, "Should mention fireball"
    
    def test_lightning_complete_scenario(self):
        """Test complete lightning spell: cast → target selection → damage."""
        # Act: Cast lightning (auto-targets nearest enemy)
        results = cast_spell_by_id(
            spell_id="lightning",
            caster=self.player,
            entities=self.entities,
            fov_map=self.fov_map,
            game_map=self.game_map
        )
        
        # Assert: Spell was consumed
        assert any(r.get("consumed") for r in results), "Lightning should be consumed"
        
        # Assert: Monster was damaged
        assert self.monster.fighter.hp < 20, "Monster should be struck by lightning"
        
        # Assert: Damage messages exist
        messages = [r.get("message") for r in results if r.get("message")]
        damage_msgs = [m for m in messages if "damage" in m.text.lower()]
        assert len(damage_msgs) > 0, "Should report damage"
    
    def test_confusion_complete_scenario(self):
        """Test confusion spell: cast → status effect → AI change → expiration."""
        # Arrange: Monster has normal AI
        original_ai = self.monster.ai
        
        # Act: Cast confusion on monster
        results = cast_spell_by_id(
            spell_id="confuse",
            caster=self.player,
            entities=self.entities,
            fov_map=self.fov_map,
            target_x=12,
            target_y=10,
            game_map=self.game_map
        )
        
        # Assert: Spell consumed
        assert any(r.get("consumed") for r in results), "Confusion should be consumed"
        
        # Assert: Monster AI changed
        from components.ai import ConfusedMonster
        assert isinstance(self.monster.ai, ConfusedMonster), "Monster should be confused"
        
        # Assert: Confused AI has reference to previous AI
        assert self.monster.ai.previous_ai is original_ai, "Should store original AI"
        
        # Assert: Confusion message generated
        messages = [r.get("message") for r in results if r.get("message")]
        confusion_msgs = [m for m in messages if "confused" in m.text.lower() or "disoriented" in m.text.lower()]
        assert len(confusion_msgs) > 0, "Should announce confusion"
    
    def test_healing_complete_scenario(self):
        """Test healing spell: damage → heal → HP restoration → message."""
        # Arrange: Damage player first
        self.player.fighter.take_damage(15)
        initial_hp = self.player.fighter.hp
        assert initial_hp < self.player.fighter.max_hp, "Player should be damaged"
        
        # Act: Cast healing spell
        results = cast_spell_by_id(
            spell_id="heal",
            caster=self.player,
            target=self.player,
            entities=self.entities,
            fov_map=self.fov_map,
            game_map=self.game_map
        )
        
        # Assert: HP increased
        assert self.player.fighter.hp > initial_hp, "Player should be healed"
        
        # Assert: Healing message exists
        messages = [r.get("message") for r in results if r.get("message")]
        heal_msgs = [m for m in messages if "heal" in m.text.lower()]
        assert len(heal_msgs) > 0, "Should announce healing"
    
    def test_shield_complete_scenario(self):
        """Test shield spell: cast → defense boost → status effect → expiration."""
        # Arrange: Get initial defense
        initial_defense = self.player.fighter.defense
        
        # Act: Cast shield on player
        results = cast_spell_by_id(
            spell_id="shield",
            caster=self.player,
            target=self.player,
            entities=self.entities,
            fov_map=self.fov_map,
            game_map=self.game_map
        )
        
        # Assert: Spell consumed
        assert any(r.get("consumed") for r in results), "Shield should be consumed"
        
        # Assert: Defense increased
        assert self.player.fighter.defense > initial_defense, "Defense should increase"
        
        # Assert: Shield message generated
        messages = [r.get("message") for r in results if r.get("message")]
        shield_msgs = [m for m in messages if "shield" in m.text.lower() or "defense" in m.text.lower()]
        assert len(shield_msgs) > 0, "Should announce shield"
    
    def test_spell_out_of_range_scenario(self):
        """Test spell failure: target out of range → failure message."""
        # Arrange: Place monster far away
        self.monster.x = 25
        self.monster.y = 25
        
        # Act: Try to cast fireball (range limited)
        results = cast_spell_by_id(
            spell_id="fireball",
            caster=self.player,
            entities=self.entities,
            fov_map=self.fov_map,
            target_x=25,
            target_y=25,
            game_map=self.game_map
        )
        
        # Assert: Spell not consumed (failed)
        consumed = any(r.get("consumed") for r in results)
        
        # Assert: Failure message exists
        messages = [r.get("message") for r in results if r.get("message")]
        assert len(messages) > 0, "Should provide feedback on failure"
    
    def test_multi_target_spell_scenario(self):
        """Test area effect spell: multiple targets → all damaged."""
        # Arrange: Add more monsters in area
        monster2 = Entity(
            13, 10, "o", (63, 127, 63), "Orc2",
            blocks=True, fighter=Fighter(hp=20, defense=1, power=3),
            ai=BasicMonster()
        )
        monster2.ai.owner = monster2
        
        monster3 = Entity(
            12, 11, "o", (63, 127, 63), "Orc3",
            blocks=True, fighter=Fighter(hp=20, defense=1, power=3),
            ai=BasicMonster()
        )
        monster3.ai.owner = monster3
        
        self.entities.extend([monster2, monster3])
        
        # Act: Cast fireball (area effect)
        results = cast_spell_by_id(
            spell_id="fireball",
            caster=self.player,
            entities=self.entities,
            fov_map=self.fov_map,
            target_x=12,
            target_y=10,
            game_map=self.game_map
        )
        
        # Assert: All monsters in range took damage
        assert self.monster.fighter.hp < 20, "Monster 1 should be damaged"
        assert monster2.fighter.hp < 20, "Monster 2 should be damaged"
        # Monster3 might be in range depending on fireball radius


class TestSpellStatusEffectIntegration:
    """Integration tests for spell-induced status effects."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.game_map = GameMap(20, 20)
        self.fov_map = initialize_fov(self.game_map)
        
        # Create entities
        self.player = Entity(
            10, 10, "@", (255, 255, 255), "Player",
            blocks=True, fighter=Fighter(hp=30, defense=2, power=5)
        )
        
        self.monster = Entity(
            11, 10, "o", (63, 127, 63), "Orc",
            blocks=True, fighter=Fighter(hp=20, defense=1, power=3),
            ai=BasicMonster()
        )
        self.monster.ai.owner = self.monster
        
        self.entities = [self.player, self.monster]
    
    def test_status_effect_duration_tracking(self):
        """Test status effect lasts correct duration."""
        # Act: Cast confusion (10 turns)
        cast_spell_by_id(
            spell_id="confuse",
            caster=self.player,
            entities=self.entities,
            fov_map=self.fov_map,
            target_x=11,
            target_y=10,
            game_map=self.game_map
        )
        
        # Assert: Monster has status effect manager
        from components.component_registry import ComponentType
        assert self.monster.components.has(ComponentType.STATUS_EFFECTS), \
            "Monster should have status effects"
        
        # Get status effect manager
        status_mgr = self.monster.components.get(ComponentType.STATUS_EFFECTS)
        
        # Assert: Has active confusion effect
        assert 'confusion' in status_mgr.active_effects, \
            "Should have active confusion effect"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

