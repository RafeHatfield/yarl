"""Unit tests for Phase 20 corpse lifecycle (FRESH → SPENT → CONSUMED)."""

import pytest
from components.corpse import CorpseComponent, CorpseState


class TestCorpseLifecycleStates:
    """Test Phase 20 corpse lifecycle state transitions."""
    
    def test_fresh_corpse_can_raise_not_explode(self):
        """FRESH corpses can be raised but not exploded."""
        corpse = CorpseComponent(
            original_monster_id="orc",
            corpse_state=CorpseState.FRESH
        )
        
        assert corpse.can_raise() is True
        assert corpse.can_explode() is False
        assert corpse.corpse_state == CorpseState.FRESH
    
    def test_spent_corpse_can_explode_not_raise(self):
        """SPENT corpses can be exploded but not raised."""
        corpse = CorpseComponent(
            original_monster_id="orc",
            corpse_state=CorpseState.SPENT
        )
        
        assert corpse.can_raise() is False
        assert corpse.can_explode() is True
        assert corpse.corpse_state == CorpseState.SPENT
    
    def test_consumed_corpse_cannot_raise_or_explode(self):
        """CONSUMED corpses are inert."""
        corpse = CorpseComponent(
            original_monster_id="orc",
            corpse_state=CorpseState.CONSUMED
        )
        
        assert corpse.can_raise() is False
        assert corpse.can_explode() is False
        assert corpse.corpse_state == CorpseState.CONSUMED
    
    def test_mark_spent_transitions_fresh_to_spent(self):
        """mark_spent() transitions FRESH → SPENT."""
        corpse = CorpseComponent(
            original_monster_id="orc",
            corpse_state=CorpseState.FRESH
        )
        
        corpse.mark_spent()
        
        assert corpse.corpse_state == CorpseState.SPENT
        assert corpse.can_raise() is False
        assert corpse.can_explode() is True
    
    def test_mark_consumed_transitions_to_consumed(self):
        """mark_consumed() transitions to CONSUMED state."""
        corpse = CorpseComponent(
            original_monster_id="orc",
            corpse_state=CorpseState.SPENT
        )
        
        corpse.mark_consumed()
        
        assert corpse.corpse_state == CorpseState.CONSUMED
        assert corpse.consumed is True  # Legacy flag set
        assert corpse.can_raise() is False
        assert corpse.can_explode() is False
    
    def test_consume_preserves_state_until_max_raises(self):
        """consume() increments raise count but doesn't change state until max raises."""
        corpse = CorpseComponent(
            original_monster_id="orc",
            corpse_state=CorpseState.FRESH,
            max_raises=2
        )
        
        # First raise: state stays FRESH (legacy consume behavior)
        corpse.consume("Necromancer")
        
        assert corpse.raise_count == 1
        assert corpse.corpse_state == CorpseState.FRESH  # consume() doesn't change state
        assert corpse.can_raise() is True  # Can still raise (1 < 2)
        
        # Second raise: hits max, marks CONSUMED
        corpse.consume("Necromancer")
        
        assert corpse.raise_count == 2
        assert corpse.corpse_state == CorpseState.CONSUMED
        assert corpse.can_raise() is False


class TestCorpseLineageTracking:
    """Test Phase 20 lineage tracking with corpse_id."""
    
    def test_corpse_id_for_lineage(self):
        """Corpse ID enables lineage tracking through raise cycle."""
        corpse = CorpseComponent(
            original_monster_id="orc",
            corpse_state=CorpseState.FRESH,
            corpse_id="corpse_10_5_42"
        )
        
        assert corpse.corpse_id == "corpse_10_5_42"
    
    def test_spent_corpse_inherits_corpse_id(self):
        """SPENT corpses preserve corpse_id from original."""
        # Simulate re-death: same corpse_id, SPENT state
        corpse = CorpseComponent(
            original_monster_id="orc",
            corpse_state=CorpseState.SPENT,
            corpse_id="corpse_10_5_42"  # Same ID as original
        )
        
        assert corpse.corpse_id == "corpse_10_5_42"
        assert corpse.corpse_state == CorpseState.SPENT


class TestBackwardCompatibility:
    """Test Phase 20 maintains backward compatibility with legacy APIs."""
    
    def test_can_be_raised_legacy_api(self):
        """can_be_raised() is legacy alias for can_raise()."""
        corpse = CorpseComponent(
            original_monster_id="orc",
            corpse_state=CorpseState.FRESH
        )
        
        assert corpse.can_be_raised() == corpse.can_raise()
        assert corpse.can_be_raised() is True
    
    def test_consumed_flag_set_on_mark_consumed(self):
        """Legacy consumed flag set when marking consumed."""
        corpse = CorpseComponent(
            original_monster_id="orc",
            corpse_state=CorpseState.SPENT
        )
        
        assert corpse.consumed is False
        
        corpse.mark_consumed()
        
        assert corpse.consumed is True
        assert corpse.corpse_state == CorpseState.CONSUMED


class TestCorpseRepr:
    """Test Phase 20 corpse __repr__ includes state."""
    
    def test_repr_includes_state(self):
        """__repr__ includes corpse_state for debugging."""
        corpse = CorpseComponent(
            original_monster_id="orc",
            corpse_state=CorpseState.SPENT
        )
        
        repr_str = repr(corpse)
        
        assert "state=SPENT" in repr_str
        assert "id=orc" in repr_str


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


