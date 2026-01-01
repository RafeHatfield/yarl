import pytest

class _DummyMap:
    """Minimal mock game map for testing."""
    width = 100
    height = 100

def _monster_with(store=None, name="orc"):
    from components.component_registry import ComponentRegistry
    
    class M:
        def __init__(self, name, store):
            self.name = name
            self.x = 10  # Position for loot dropping
            self.y = 10
            self._c = store or {}
            self.components = ComponentRegistry()  # Phase 19: Required for CorpseComponent
        def get_component_optional(self, key):
            if hasattr(key, "value"):  # accept Enum or str
                key = key.value
            return self._c.get(key)
    return M(name, store or {})

def test_kill_monster_nonboss_does_not_crash():
    from death_functions import kill_monster
    monster = _monster_with(store={}, name="orc")  # no 'boss' component
    kill_monster(monster, _DummyMap(), entities=[])  # must not raise

