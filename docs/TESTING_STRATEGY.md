# Testing Strategy for Catacombs of Yarl

This document outlines our comprehensive testing strategy designed to prevent regressions and ensure code quality while maintaining clean, maintainable tests.

## Testing Philosophy

**"Every bug fix includes tests to prevent recurrence"**

Our testing approach follows these principles:
1. **Regression Prevention**: Every fixed bug gets tests to prevent it from happening again
2. **Clean Test Code**: Tests should be as clean and maintainable as production code
3. **Real Component Integration**: Use actual classes when possible, not just mocks
4. **Comprehensive Coverage**: Unit tests, integration tests, and regression tests work together
5. **Documentation**: Tests should clearly document what they prevent or verify

## Test Structure

### 1. Unit Tests (`tests/`)
- **Purpose**: Test individual components in isolation
- **Approach**: Use mocks for dependencies, focus on single responsibility
- **Example**: `tests/engine/systems/test_ai_system.py`
- **Coverage**: Individual methods, error handling, edge cases

### 2. Integration Tests (`tests/integration/`)
- **Purpose**: Test interaction between real components
- **Approach**: Use actual game classes, minimal mocking
- **Example**: `tests/integration/test_ai_integration.py`
- **Coverage**: System interactions, interface contracts, end-to-end workflows

### 3. Regression Tests (`tests/regression/`)
- **Purpose**: Prevent specific bugs from recurring
- **Approach**: Document the exact bug being prevented
- **Example**: `tests/regression/test_ai_system_regression.py`
- **Coverage**: Known bugs, interface mismatches, signature changes

## Bug Fix Testing Pattern

When fixing a bug, follow this pattern:

### 1. Create Regression Test First
```python
def test_specific_bug_regression(self):
    \"\"\"Regression test: Prevent [specific bug description].
    
    Bug: [Original error message or symptom]
    Fix: [What was changed to fix it]
    
    This test ensures [what it prevents].
    \"\"\"
    # Test that would have caught the original bug
```

### 2. Fix the Bug
- Make minimal changes to fix the issue
- Ensure the regression test now passes

### 3. Add Integration Test
- Create a test using real components that would have caught the bug
- Verify the fix works in realistic scenarios

### 4. Update Documentation
- Document the bug and fix in commit messages
- Update relevant docstrings or comments

## Example: AI Argument Mismatch Bug

**Original Bug**: `BasicMonster.take_turn() missing 1 required positional argument: 'entities'`

**Root Cause**: AISystem was calling `take_turn(player, game_map, entities)` but the method expected `take_turn(player, fov_map, game_map, entities)`

**Testing Response**:

1. **Regression Test**: `test_ai_take_turn_argument_signature_regression()`
   - Uses real AI classes to verify correct arguments
   - Would fail if the bug is reintroduced

2. **Integration Test**: `test_ai_system_processes_real_basic_monster()`
   - Uses actual game components (Entity, Fighter, BasicMonster)
   - Catches interface mismatches between systems

3. **Meta Test**: `test_ai_method_signature_compatibility_check()`
   - Automatically detects signature changes in AI classes
   - Prevents similar bugs with new AI implementations

## Test Categories

### Regression Tests
- **When to Create**: After fixing any bug
- **Naming**: `test_[component]_[bug_description]_regression()`
- **Documentation**: Must include original error and fix description
- **Approach**: Use real classes when possible

### Integration Tests  
- **When to Create**: For system interactions and interfaces
- **Naming**: `test_[system1]_[interaction]_[system2]()`
- **Documentation**: Explain what integration is being tested
- **Approach**: Minimal mocking, real game components

### Unit Tests
- **When to Create**: For all new components and methods
- **Naming**: `test_[method_name]_[scenario]()`
- **Documentation**: Clear description of what's being tested
- **Approach**: Mock dependencies, focus on single responsibility

## Testing Tools and Patterns

### Mocking Guidelines
```python
# Good: Mock external dependencies
with patch('tcod.libtcodpy.map_is_in_fov', return_value=True):
    # Test logic

# Good: Mock complex setup
mock_entity = Mock()
mock_entity.x = 5
mock_entity.y = 5

# Avoid: Over-mocking when real classes are simple
# Use real Entity, Fighter, etc. when they don't complicate the test
```

### Signature Testing
```python
def test_interface_compatibility(self):
    \"\"\"Verify interface contracts are maintained.\"\"\"
    sig = inspect.signature(SomeClass.some_method)
    expected_params = ['self', 'param1', 'param2']
    actual_params = list(sig.parameters.keys())
    assert actual_params == expected_params
```

### Real Component Integration
```python
def test_real_component_integration(self):
    \"\"\"Test with actual game components.\"\"\"
    # Use real classes
    fighter = Fighter(hp=10, defense=2, power=3)
    entity = Entity(5, 5, 'o', (255, 0, 0), 'Orc', fighter=fighter)
    
    # Test actual behavior
    result = system.process(entity)
    assert result.success
```

## Running Tests

### All Tests
```bash
python -m pytest
```

### Specific Categories
```bash
# Unit tests only
python -m pytest tests/engine/ tests/components/

# Integration tests only  
python -m pytest tests/integration/

# Regression tests only
python -m pytest tests/regression/
```

### Verbose Output
```bash
python -m pytest -v
```

### Coverage Report
```bash
python -m pytest --cov=. --cov-report=html
```

## Test Maintenance

### Adding New AI Classes
1. Add to `test_all_ai_classes_implement_take_turn()` 
2. Verify signature compatibility
3. Add integration test with real AI class

### Refactoring Systems
1. Run regression tests first to establish baseline
2. Update integration tests for new interfaces
3. Add new regression tests for any bugs found during refactoring

### Performance Testing
- Integration tests can include basic performance verification
- Use `time.time()` to verify operations complete within reasonable bounds
- Don't make tests brittle with exact timing requirements

## Benefits

This testing strategy provides:

1. **Regression Prevention**: Bugs stay fixed
2. **Interface Verification**: System interactions work correctly  
3. **Refactoring Safety**: Changes don't break existing functionality
4. **Documentation**: Tests explain system behavior and prevent bugs
5. **Quality Assurance**: Multiple layers of testing catch different types of issues

## Future Improvements

- Add property-based testing for complex algorithms
- Implement mutation testing to verify test quality
- Add performance regression tests for critical paths
- Create visual test reports for better insight into test coverage

---

**Remember**: Good tests are an investment in code quality. They should be clean, maintainable, and clearly document what they're testing and why.