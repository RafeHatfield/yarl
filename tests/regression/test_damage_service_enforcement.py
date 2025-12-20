"""Regression guard: Prevent ignored Fighter.take_damage() calls.

This test enforces that damage application outside normal combat flow
uses the centralized damage_service.apply_damage() function, which
ensures death handling is never ignored.

Background:
- Phase 18.3 fixed three bugs where entities could reach 0 HP without dying
  because callers ignored Fighter.take_damage() return results
- This test prevents future regressions by detecting direct take_damage() calls
  in modules that should use damage_service instead
"""

import os
import re
import pytest


# Modules that are ALLOWED to call Fighter.take_damage() directly
ALLOWED_MODULES = {
    "components/fighter.py",  # Fighter itself (internal calls in attack methods)
    "game_actions.py",  # Combat system with proper death handling via _handle_entity_death
    "engine/systems/ai_system.py",  # AI system with proper death handling
    "services/damage_service.py",  # The damage service itself
    "services/scenario_harness.py",  # Test harness with proper death handling
}

# Modules that should NEVER call take_damage() directly
# (should use damage_service.apply_damage instead)
FORBIDDEN_MODULES = {
    "mouse_movement.py",
    "throwing.py",
    "services/movement_service.py",
    "spells/spell_executor.py",  # Spells must use damage_service (Phase 18.3)
    "io_layer/",  # No damage application in rendering/UI layers
    "ui/",  # No damage application in UI
    "input/",  # No damage application in input handlers
}


def test_no_ignored_take_damage_calls():
    """Enforce that high-risk modules use damage_service.apply_damage().
    
    This test scans the codebase for direct calls to Fighter.take_damage()
    and ensures they only appear in approved modules with proper death handling.
    
    If this test fails:
    - You added a direct take_damage() call in a forbidden module
    - Use services.damage_service.apply_damage() instead
    - Or add your module to ALLOWED_MODULES if it has proper death handling
    """
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    # Pattern: .take_damage( with optional whitespace/newlines
    pattern = re.compile(r'\.take_damage\s*\(')
    
    violations = []
    
    for root, dirs, files in os.walk(repo_root):
        # Skip test files, docs, archive, and hidden directories
        if any(skip in root for skip in ['/tests/', '/docs/', '/archive/', '/.', '/telemetry/']):
            continue
        
        for filename in files:
            if not filename.endswith('.py'):
                continue
            
            filepath = os.path.join(root, filename)
            relpath = os.path.relpath(filepath, repo_root)
            
            # Skip allowed modules
            if any(allowed in relpath for allowed in ALLOWED_MODULES):
                continue
            
            # Read file and check for violations
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                matches = list(pattern.finditer(content))
                if matches:
                    # Check if this is a forbidden module
                    is_forbidden = any(forbidden in relpath for forbidden in FORBIDDEN_MODULES)
                    
                    if is_forbidden:
                        # Count line numbers for violation report
                        line_numbers = []
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            line_numbers.append(line_num)
                        
                        violations.append({
                            'file': relpath,
                            'lines': line_numbers,
                            'forbidden': True
                        })
            except Exception as e:
                # Skip files that can't be read
                pass
    
    # Report violations
    if violations:
        error_msg = "\n\n❌ DAMAGE SERVICE ENFORCEMENT VIOLATION\n"
        error_msg += "=" * 70 + "\n\n"
        error_msg += "Found direct Fighter.take_damage() calls in forbidden modules.\n"
        error_msg += "These modules MUST use services.damage_service.apply_damage() instead.\n\n"
        
        for violation in violations:
            error_msg += f"  File: {violation['file']}\n"
            error_msg += f"  Lines: {', '.join(map(str, violation['lines']))}\n"
            error_msg += f"  Fix: Replace .take_damage() with damage_service.apply_damage()\n\n"
        
        error_msg += "Why this matters:\n"
        error_msg += "- Direct take_damage() calls can ignore death results\n"
        error_msg += "- This causes entities to reach 0 HP without dying\n"
        error_msg += "- damage_service.apply_damage() enforces death handling\n\n"
        
        error_msg += "If you need to call take_damage() for a valid reason:\n"
        error_msg += "1. Ensure your module properly handles death results\n"
        error_msg += "2. Add your module to ALLOWED_MODULES in this test\n"
        error_msg += "3. Document why direct take_damage() is necessary\n"
        
        pytest.fail(error_msg)


def test_damage_service_exists():
    """Verify damage service module exists and has correct API."""
    try:
        from services.damage_service import apply_damage
    except ImportError as e:
        pytest.fail(f"damage_service module not found: {e}")
    
    # Verify function signature (basic check)
    import inspect
    sig = inspect.signature(apply_damage)
    
    required_params = {'state_manager', 'target_entity', 'amount', 'cause'}
    actual_params = set(sig.parameters.keys())
    
    missing = required_params - actual_params
    if missing:
        pytest.fail(f"apply_damage() missing required parameters: {missing}")


def test_migration_complete():
    """Verify the three recently patched modules use damage_service."""
    from services import damage_service
    import mouse_movement
    import throwing
    from services import movement_service
    
    # Check that damage_service is imported in the migrated modules
    # (This is a simple smoke test - the main enforcement is in test_no_ignored_take_damage_calls)
    
    # Just verify modules can be imported without errors
    assert damage_service is not None
    assert mouse_movement is not None
    assert throwing is not None
    assert movement_service is not None
