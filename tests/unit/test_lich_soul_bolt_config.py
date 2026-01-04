"""Unit test for Lich Soul Bolt configuration from YAML.

This test prevents regression of the bug where Soul Bolt config
(damage_pct, cooldown_turns) was not propagated from entities.yaml
to the Lich entity, causing LichAI to fall back to hardcoded defaults.

Bug fixed: 2026-01-03
Root cause: MonsterDefinition dataclass and entity registry loading
            did not include soul_bolt_* fields.
"""

import pytest
from config.factories import get_entity_factory


class TestLichSoulBoltConfig:
    """Verify Lich entities receive Soul Bolt config from YAML."""

    def test_lich_has_soul_bolt_damage_pct_from_yaml(self):
        """Lich entity should have soul_bolt_damage_pct attribute set from YAML config."""
        factory = get_entity_factory()
        lich = factory.create_monster('lich', 0, 0)
        
        # The attribute must exist (not fall back to NOT SET)
        assert hasattr(lich, 'soul_bolt_damage_pct'), \
            "Lich entity missing soul_bolt_damage_pct - config not propagated from YAML"
        
        # Must be a float between 0 and 1 (percentage)
        assert isinstance(lich.soul_bolt_damage_pct, (int, float)), \
            f"soul_bolt_damage_pct should be numeric, got {type(lich.soul_bolt_damage_pct)}"
        assert 0.0 <= lich.soul_bolt_damage_pct <= 1.0, \
            f"soul_bolt_damage_pct should be 0-1, got {lich.soul_bolt_damage_pct}"

    def test_lich_has_soul_bolt_cooldown_from_yaml(self):
        """Lich entity should have soul_bolt_cooldown_turns attribute set from YAML config."""
        factory = get_entity_factory()
        lich = factory.create_monster('lich', 0, 0)
        
        # The attribute must exist
        assert hasattr(lich, 'soul_bolt_cooldown_turns'), \
            "Lich entity missing soul_bolt_cooldown_turns - config not propagated from YAML"
        
        # Must be a positive integer
        assert isinstance(lich.soul_bolt_cooldown_turns, int), \
            f"soul_bolt_cooldown_turns should be int, got {type(lich.soul_bolt_cooldown_turns)}"
        assert lich.soul_bolt_cooldown_turns > 0, \
            f"soul_bolt_cooldown_turns should be positive, got {lich.soul_bolt_cooldown_turns}"

    def test_lich_has_soul_bolt_range_from_yaml(self):
        """Lich entity should have soul_bolt_range attribute set from YAML config."""
        factory = get_entity_factory()
        lich = factory.create_monster('lich', 0, 0)
        
        # The attribute must exist
        assert hasattr(lich, 'soul_bolt_range'), \
            "Lich entity missing soul_bolt_range - config not propagated from YAML"
        
        # Must be a positive integer
        assert isinstance(lich.soul_bolt_range, int), \
            f"soul_bolt_range should be int, got {type(lich.soul_bolt_range)}"
        assert lich.soul_bolt_range > 0, \
            f"soul_bolt_range should be positive, got {lich.soul_bolt_range}"

    def test_lich_soul_bolt_config_matches_yaml_not_defaults(self):
        """Soul Bolt config on Lich must match YAML, not hardcoded LichAI defaults.
        
        LichAI has fallback defaults: damage_pct=0.35, cooldown=4
        The YAML config should override these. This test catches the exact
        bug where YAML values weren't being propagated.
        """
        factory = get_entity_factory()
        lich = factory.create_monster('lich', 0, 0)
        
        # Get the YAML-configured values from the registry for comparison
        lich_def = factory.registry.get_monster('lich')
        
        # Entity values must match the definition (which comes from YAML)
        assert lich.soul_bolt_damage_pct == lich_def.soul_bolt_damage_pct, \
            f"Entity damage_pct ({lich.soul_bolt_damage_pct}) != YAML ({lich_def.soul_bolt_damage_pct})"
        assert lich.soul_bolt_cooldown_turns == lich_def.soul_bolt_cooldown_turns, \
            f"Entity cooldown ({lich.soul_bolt_cooldown_turns}) != YAML ({lich_def.soul_bolt_cooldown_turns})"
        assert lich.soul_bolt_range == lich_def.soul_bolt_range, \
            f"Entity range ({lich.soul_bolt_range}) != YAML ({lich_def.soul_bolt_range})"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

