# Spell Registry System Design

## Problem Statement
`item_functions.py` is 1,252 lines with 15+ spell functions using inconsistent patterns:
- Repetitive parameter extraction (`kwargs.get()` everywhere)
- Inconsistent error handling
- No centralized spell data
- Hard to add new spells
- Difficult to balance (damage/range/duration scattered)

## Current Spells (15 total)

### Offensive/Damage (4)
- `cast_lightning` - Single target, requires LoS, high damage
- `cast_fireball` - AoE explosion + ground hazards
- `cast_dragon_fart` - Cone AoE + poison hazards
- `cast_yo_mama` - Taunt/psychological damage

### Healing (1)
- `heal` - Restore HP

### Control/Utility (5)
- `cast_confusion` - Confuse enemies
- `cast_teleport` - Teleport to location
- `cast_slow` - Target moves every 2nd turn
- `cast_glue` - Root/immobilize target
- `cast_rage` - Berserk (attack anyone, 2x damage, 0.5x accuracy)

### Buffs/Enhancement (3)
- `cast_shield` - Defense boost
- `enhance_weapon` - Weapon enhancement
- `enhance_armor` - Armor enhancement

### Summons (1)
- `cast_raise_dead` - Summon zombie

### Special (1)
- `get_cone_tiles` - Helper for cone calculations

## Proposed Solution

### 1. Spell Data Structure
```python
@dataclass
class SpellDefinition:
    """Unified spell definition."""
    name: str
    category: SpellCategory  # OFFENSIVE, UTILITY, BUFF, HEAL
    targeting: TargetingType  # SELF, SINGLE, AOE, CONE, LOCATION
    
    # Damage/Effect
    damage: Optional[str] = None  # Dice notation: "3d6", "2d8+4"
    radius: int = 0  # For AoE
    cone_range: int = 0  # For cone spells
    cone_width: int = 45  # Degrees
    
    # Requirements
    requires_los: bool = True
    requires_target: bool = True
    max_range: int = 10
    
    # Effects
    duration: int = 0  # For status effects
    effect_type: Optional[str] = None  # "confusion", "slow", "shield"
    
    # Ground hazards
    creates_hazard: bool = False
    hazard_type: Optional[str] = None  # "fire", "poison"
    hazard_duration: int = 0
    
    # Messages
    cast_message: str = ""
    success_message: str = ""
    fail_message: str = ""
    
    # Visual
    visual_effect: Optional[Callable] = None
```

### 2. Spell Registry
```python
class SpellRegistry:
    """Central registry for all spells."""
    
    def __init__(self):
        self._spells = {}
    
    def register(self, spell_id: str, definition: SpellDefinition):
        """Register a spell."""
        self._spells[spell_id] = definition
    
    def get(self, spell_id: str) -> SpellDefinition:
        """Get spell definition."""
        return self._spells.get(spell_id)
    
    def cast(self, spell_id: str, caster, **kwargs) -> List[Dict]:
        """Cast a spell using its definition."""
        spell = self.get(spell_id)
        if not spell:
            return [{"consumed": False, "message": Message("Unknown spell!", (255, 0, 0))}]
        
        return self._execute_spell(spell, caster, **kwargs)
```

### 3. Spell Executors
```python
class SpellExecutor:
    """Executes spells based on their definitions."""
    
    @staticmethod
    def execute_offensive_spell(spell: SpellDefinition, caster, **kwargs):
        """Execute offensive spells (fireball, lightning)."""
        # Unified damage dealing logic
        pass
    
    @staticmethod
    def execute_utility_spell(spell: SpellDefinition, caster, **kwargs):
        """Execute utility spells (confusion, teleport)."""
        # Unified status effect logic
        pass
    
    @staticmethod
    def execute_buff_spell(spell: SpellDefinition, caster, **kwargs):
        """Execute buff spells (shield, enhance)."""
        # Unified buff logic
        pass
```

## Implementation Plan

### Phase 1: Foundation (Day 1-2)
- Create `spells/` module structure
- Define `SpellDefinition` dataclass
- Create `SpellRegistry` class
- Write basic tests

### Phase 2: Offensive Spells (Day 2-3)
- Migrate `cast_lightning`
- Migrate `cast_fireball`
- Migrate `cast_dragon_fart`
- Test damage calculation uniformity

### Phase 3: Utility Spells (Day 3-4)
- Migrate `cast_confusion`
- Migrate `cast_teleport`
- Migrate `cast_slow`, `cast_glue`, `cast_rage`
- Test status effect application

### Phase 4: Buffs & Special (Day 4-5)
- Migrate `cast_shield`
- Migrate `enhance_weapon`, `enhance_armor`
- Migrate `heal`
- Migrate `cast_raise_dead`

### Phase 5: Integration & Cleanup (Day 5)
- Update all spell item definitions
- Update wand system
- Remove old spell functions
- Comprehensive testing

## Benefits

1. **Easier to Add Spells**: Just add a new `SpellDefinition` to registry
2. **Centralized Balance**: All damage/range/duration in one place
3. **Consistent Behavior**: Unified targeting, LoS checks, error handling
4. **Better Testing**: Test spell definitions separately from execution
5. **Self-Documenting**: Spell data is declarative and easy to read
6. **Reduced Code**: ~800 lines → ~300 lines

## Migration Strategy

- Keep old functions temporarily (backward compatibility)
- Add `@deprecated` warnings
- Migrate one spell category at a time
- Run full test suite after each category
- Remove old code only when all tests pass

## Success Criteria

- [ ] All 1,895 tests passing
- [ ] `item_functions.py` reduced by 60%+ lines
- [ ] New spell can be added in <10 lines
- [ ] Spell balance tuning requires editing only registry
- [ ] Zero regressions in existing spell behavior

