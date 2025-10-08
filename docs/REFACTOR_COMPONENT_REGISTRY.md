# 🔧 Component Registry Refactor - Implementation Plan

**Branch:** `refactor/component-registry`  
**Status:** 🟢 In Progress  
**Priority:** P0 - CRITICAL  
**Effort:** 3 days  
**Goal:** Replace 121 hasattr() checks with type-safe component registry

---

## 📋 **Implementation Checklist**

### **Day 1: Foundation** (4-5 hours)
- [ ] ✅ Create `components/component_registry.py`
- [ ] ✅ Design `ComponentType` enum
- [ ] ✅ Implement `ComponentRegistry` class
- [ ] ✅ Add `Entity.components` property
- [ ] ✅ Add `Entity.add_component()` method
- [ ] ✅ Add `Entity.get_component()` method
- [ ] ✅ Add `Entity.has_component()` method
- [ ] ✅ Write tests for ComponentRegistry
- [ ] ✅ Ensure backward compatibility (keep old attrs temporarily)

### **Day 2: Entity Refactoring** (6-8 hours)
- [ ] Update `Entity.__init__()` to use registry
- [ ] Update `Entity._register_components()` to use registry
- [ ] Refactor `entity.py` hasattr() calls
- [ ] Refactor `components/fighter.py` 
- [ ] Refactor `components/ai.py`
- [ ] Refactor `components/inventory.py`
- [ ] Refactor `components/equipment.py`
- [ ] Run tests after each file (incremental verification)

### **Day 3: System-Wide Migration** (6-8 hours)
- [ ] Refactor `game_actions.py` (4 hasattr calls)
- [ ] Refactor `render_functions.py` (1 hasattr call)
- [ ] Refactor `mouse_movement.py` (3 hasattr calls)
- [ ] Refactor `item_functions.py` (7 hasattr calls)
- [ ] Refactor `ui/tooltip.py` (8 hasattr calls)
- [ ] Refactor `menus.py` (7 hasattr calls)
- [ ] Refactor `engine/systems/ai_system.py` (1 hasattr call)
- [ ] Refactor remaining files (~18 files, ~87 hasattr calls)
- [ ] Final test run (all 1,855 tests)
- [ ] Remove backward compatibility code
- [ ] Update documentation

---

## 🎯 **Design Decisions**

### **ComponentType Enum**
```python
from enum import Enum, auto

class ComponentType(Enum):
    """Type-safe component identifiers."""
    FIGHTER = auto()
    AI = auto()
    ITEM = auto()
    INVENTORY = auto()
    EQUIPMENT = auto()
    EQUIPPABLE = auto()
    LEVEL = auto()
    STAIRS = auto()
    PATHFINDING = auto()
    STATUS_EFFECTS = auto()
    WAND = auto()
    GROUND_HAZARD = auto()
    STATISTICS = auto()
    FACTION = auto()
```

### **ComponentRegistry Class**
```python
from typing import Dict, Optional, Any, Type

class ComponentRegistry:
    """Type-safe component storage and lookup."""
    
    def __init__(self):
        self._components: Dict[ComponentType, Any] = {}
    
    def add(self, component_type: ComponentType, component: Any) -> None:
        """Add a component with type safety."""
        if component_type in self._components:
            raise ValueError(f"Component {component_type} already exists")
        self._components[component_type] = component
    
    def get(self, component_type: ComponentType) -> Optional[Any]:
        """Get a component by type."""
        return self._components.get(component_type)
    
    def has(self, component_type: ComponentType) -> bool:
        """Check if component exists."""
        return component_type in self._components
    
    def remove(self, component_type: ComponentType) -> None:
        """Remove a component."""
        self._components.pop(component_type, None)
    
    def __contains__(self, component_type: ComponentType) -> bool:
        """Support 'in' operator."""
        return component_type in self._components
    
    def __iter__(self):
        """Support iteration over components."""
        return iter(self._components.values())
```

### **Entity Integration**
```python
class Entity:
    def __init__(self, x, y, char, color, name, blocks=False, 
                 render_order=RenderOrder.CORPSE, faction=None, **components):
        # ... existing setup ...
        
        # NEW: Component registry
        self.components = ComponentRegistry()
        
        # Register components with type safety
        self._register_components(components)
    
    def _register_components(self, components: dict[str, Any]) -> None:
        """Register components with type-safe registry."""
        component_mapping = {
            'fighter': ComponentType.FIGHTER,
            'ai': ComponentType.AI,
            'item': ComponentType.ITEM,
            'inventory': ComponentType.INVENTORY,
            'equipment': ComponentType.EQUIPMENT,
            'equippable': ComponentType.EQUIPPABLE,
            'level': ComponentType.LEVEL,
            'stairs': ComponentType.STAIRS,
            'pathfinding': ComponentType.PATHFINDING,
            'status_effects': ComponentType.STATUS_EFFECTS,
            'wand': ComponentType.WAND,
        }
        
        for component_name, component in components.items():
            if component_name not in component_mapping:
                raise ValueError(f"Unknown component: {component_name}")
            
            component_type = component_mapping[component_name]
            self.components.add(component_type, component)
            
            # Maintain backward compatibility (temporary)
            setattr(self, component_name, component)
            
            # Establish ownership
            if component and hasattr(component, 'owner'):
                component.owner = self
    
    # Helper methods for common components
    @property
    def fighter(self):
        """Get Fighter component (backward compatible)."""
        return self.components.get(ComponentType.FIGHTER)
    
    @property
    def ai(self):
        """Get AI component (backward compatible)."""
        return self.components.get(ComponentType.AI)
    
    # ... repeat for other common components ...
```

---

## 🔄 **Migration Strategy**

### **Phase 1: Additive (Backward Compatible)**
- Add ComponentRegistry alongside existing attributes
- Both systems work in parallel
- Tests pass with no changes

### **Phase 2: Gradual Migration**
- File by file, replace hasattr() with component checks
- Test after each file
- Both systems still work

### **Phase 3: Remove Old System**
- Once all hasattr() calls migrated
- Remove attribute assignments
- Switch to property-based access

---

## ✅ **Testing Strategy**

### **Unit Tests**
```python
# test_component_registry.py
def test_add_component():
    """Test adding component to registry."""
    registry = ComponentRegistry()
    fighter = Fighter(hp=10, defense=5, power=3)
    
    registry.add(ComponentType.FIGHTER, fighter)
    
    assert registry.has(ComponentType.FIGHTER)
    assert registry.get(ComponentType.FIGHTER) == fighter

def test_get_nonexistent_component():
    """Test getting component that doesn't exist."""
    registry = ComponentRegistry()
    
    assert registry.get(ComponentType.FIGHTER) is None
    assert not registry.has(ComponentType.FIGHTER)

def test_component_type_safety():
    """Test that only ComponentType values work."""
    registry = ComponentRegistry()
    
    with pytest.raises(TypeError):
        registry.add("fighter", Fighter())  # String not allowed
```

### **Integration Tests**
```python
def test_entity_with_component_registry():
    """Test entity creation with new registry."""
    fighter = Fighter(hp=10, defense=5, power=3)
    ai = BasicMonster()
    
    entity = Entity(5, 5, 'o', (255, 0, 0), "Orc",
                   fighter=fighter, ai=ai)
    
    # New API works
    assert entity.components.has(ComponentType.FIGHTER)
    assert entity.components.get(ComponentType.FIGHTER) == fighter
    
    # Backward compatible API still works
    assert entity.fighter == fighter
    assert entity.ai == ai
```

### **Regression Tests**
- Run full test suite after each phase
- No existing tests should break
- All 1,855 tests must pass

---

## 📊 **Success Metrics**

### **Quantitative**
- [ ] hasattr() calls reduced from 121 → <30
- [ ] All 1,855 tests passing
- [ ] No performance regression (test suite <30s)
- [ ] Code coverage maintained at 98%+

### **Qualitative**
- [ ] IDE autocomplete works for components
- [ ] Type checker (mypy) passes
- [ ] Code is more readable
- [ ] Adding new component type is 1 line (enum + mapping)

---

## 🚨 **Risk Mitigation**

### **Risk 1: Breaking Changes**
**Mitigation:** 
- Maintain backward compatibility during migration
- Run tests after every file change
- Keep old API as properties during transition

### **Risk 2: Performance Impact**
**Mitigation:**
- ComponentRegistry uses dict lookup (O(1))
- Benchmark before/after
- Profile if needed

### **Risk 3: Incomplete Migration**
**Mitigation:**
- Track hasattr() count with grep
- Code review checklist
- Linter rule to prevent new hasattr()

---

## 📚 **Future Enhancements**

Once registry is in place, we can add:

### **Component Querying**
```python
# Find all entities with Fighter component
fighters = world.query_entities(ComponentType.FIGHTER)

# Find all entities with Fighter AND AI
monsters = world.query_entities(ComponentType.FIGHTER, ComponentType.AI)

# Find all items (has ITEM but not AI)
items = world.query_entities(
    has=[ComponentType.ITEM],
    without=[ComponentType.AI]
)
```

### **Component Lifecycle Hooks**
```python
class Fighter:
    def on_add(self, entity):
        """Called when component is added to entity."""
        print(f"Fighter added to {entity.name}")
    
    def on_remove(self, entity):
        """Called when component is removed."""
        print(f"Fighter removed from {entity.name}")
    
    def on_update(self, dt):
        """Called every frame if entity is active."""
        # Regeneration logic here
        pass
```

### **Component Dependencies**
```python
class Equipment:
    REQUIRES = [ComponentType.INVENTORY]  # Must have inventory
    
    def on_add(self, entity):
        if not entity.components.has(ComponentType.INVENTORY):
            raise ValueError("Equipment requires Inventory component")
```

---

## 🎯 **Next Steps After Completion**

1. ✅ Update TECH_DEBT.md (move to COMPLETED)
2. ✅ Create PR with detailed description
3. ✅ Code review
4. ✅ Merge to main
5. ✅ Tag as `v3.7.0-refactor-components`
6. ✅ Start refactor #2 (Spell Registry)

---

**Started:** TBD  
**Completed:** TBD  
**PR:** TBD
