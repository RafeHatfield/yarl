"""Unit tests for Phase 20 corpse lifecycle state machine."""

import pytest
from components.corpse import CorpseComponent, CorpseState


class TestCorpseStates:
    """Test Phase 20 corpse state transitions."""
    
    def test_fresh_corpse_can_raise_not_explode(self):
        """FRESH corpses can be raised but not exploded."""
        corpse = CorpseComponent(
            original_monster_id="orc",
            corpse_state=CorpseState.FRESH
        )
        
        assert corpse.can_raise() is True
        assert corpse.can_be_raised() is True  # Legacy API
        assert corpse.can_explode() is False
        assert corpse.corpse_state == CorpseState.FRESH
    
    def test_spent_corpse_can_explode_not_raise(self):
        """SPENT corpses can be exploded but not raised."""
        corpse = CorpseComponent(
            original_monster_id="orc",
            corpse_state=CorpseState.SPENT
        )
        
        assert corpse.can_raise() is False
        assert corpse.can_be_raised() is False
        assert corpse.can_explode() is True
        assert corpse.corpse_state == CorpseState.SPENT
    
    def test_consumed_corpse_inert(self):
        """CONSUMED corpses are inert."""
        corpse = CorpseComponent(
            original_monster_id="orc",
            corpse_state=CorpseState.CONSUMED
        )
        
        assert corpse.can_raise() is False
        assert corpse.can_explode() is False
        assert corpse.corpse_state == CorpseState.CONSUMED
    
    def test_mark_spent_transition(self):
        """mark_spent() transitions FRESH → SPENT."""
        corpse = CorpseComponent(
            original_monster_id="orc",
            corpse_state=CorpseState.FRESH
        )
        
        corpse.mark_spent()
        
        assert corpse.corpse_state == CorpseState.SPENT
        assert corpse.can_raise() is False
        assert corpse.can_explode() is True
    
    def test_mark_consumed_transition(self):
        """mark_consumed() transitions to CONSUMED and sets legacy flag."""
        corpse = CorpseComponent(
            original_monster_id="orc",
            corpse_state=CorpseState.SPENT
        )
        
        corpse.mark_consumed()
        
        assert corpse.corpse_state == CorpseState.CONSUMED
        assert corpse.consumed is True  # Legacy flag set
        assert corpse.can_raise() is False
        assert corpse.can_explode() is False


class TestCorpseLineage:
    """Test Phase 20 lineage tracking."""
    
    def test_corpse_id_tracking(self):
        """Corpse ID enables lineage tracking."""
        corpse = CorpseComponent(
            original_monster_id="orc",
            corpse_state=CorpseState.FRESH,
            corpse_id="corpse_10_5_42"
        )
        
        assert corpse.corpse_id == "corpse_10_5_42"
    
    def test_spent_corpse_preserves_id(self):
        """SPENT corpses preserve corpse_id from original."""
        spent = CorpseComponent(
            original_monster_id="orc",
            corpse_state=CorpseState.SPENT,
            corpse_id="corpse_10_5_42"
        )
        
        assert spent.corpse_id == "corpse_10_5_42"
        assert spent.corpse_state == CorpseState.SPENT


class TestBackwardCompatibility:
    """Test Phase 20 backward compatibility."""
    
    def test_default_state_is_fresh(self):
        """Corpses default to FRESH state for backward compatibility."""
        corpse = CorpseComponent(original_monster_id="orc")
        
        assert corpse.corpse_state == CorpseState.FRESH
        assert corpse.can_be_raised() is True
    
    def test_consume_marks_consumed_at_max_raises(self):
        """Legacy consume() method marks CONSUMED when at max raises."""
        corpse = CorpseComponent(
            original_monster_id="orc",
            max_raises=1
        )
        
        corpse.consume("Necromancer")
        
        assert corpse.raise_count == 1
        assert corpse.corpse_state == CorpseState.CONSUMED
        assert corpse.consumed is True
    
    def test_repr_includes_state(self):
        """__repr__ includes state for debugging."""
        corpse = CorpseComponent(
            original_monster_id="orc",
            corpse_state=CorpseState.SPENT
        )
        
        repr_str = repr(corpse)
        
        assert "state=SPENT" in repr_str
        assert "id=orc" in repr_str


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

