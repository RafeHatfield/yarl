#!/usr/bin/env python3
"""
Batch fix for test files that set components directly without registering them.
This script updates all test files to properly register components.
"""

import os
import re
from pathlib import Path

# Patterns to find and their fixes
patterns = [
    # Fighter component
    {
        'pattern': r'(\s+)(\w+)\.fighter = Fighter\(([^)]*)\)',
        'replacement': r'\1\2.fighter = Fighter(\3)\n\1\2.components.add(ComponentType.FIGHTER, \2.fighter)',
        'import': 'from components.component_registry import ComponentType'
    },
    # Equipment component  
    {
        'pattern': r'(\s+)(\w+)\.equipment = Equipment\((\w+)\)',
        'replacement': r'\1\2.equipment = Equipment(\3)\n\1\2.components.add(ComponentType.EQUIPMENT, \2.equipment)',
        'import': 'from components.component_registry import ComponentType'
    },
    # Inventory component
    {
        'pattern': r'(\s+)(\w+)\.inventory = Inventory\((\d+)\)',
        'replacement': r'\1\2.inventory = Inventory(\3)\n\1\2.components.add(ComponentType.INVENTORY, \2.inventory)',
        'import': 'from components.component_registry import ComponentType'
    },
]

def has_import(content, import_stmt):
    """Check if file already has the import."""
    return import_stmt in content

def add_import_if_missing(content, import_stmt):
    """Add import at the top of the file if not present."""
    if has_import(content, import_stmt):
        return content
    
    # Find the first non-docstring import line
    lines = content.split('\n')
    import_index = 0
    in_docstring = False
    
    for i, line in enumerate(lines):
        if '"""' in line or "'''" in line:
            in_docstring = not in_docstring
        if not in_docstring and (line.startswith('import ') or line.startswith('from ')):
            import_index = i
            break
    
    # Insert after the last import block
    for i in range(import_index, len(lines)):
        if not (lines[i].startswith('import ') or lines[i].startswith('from ') or lines[i].strip() == ''):
            import_index = i
            break
    
    lines.insert(import_index, import_stmt)
    return '\n'.join(lines)

def fix_test_file(filepath):
    """Fix a single test file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    changes_made = []
    
    for pattern_config in patterns:
        pattern = pattern_config['pattern']
        replacement = pattern_config['replacement']
        import_stmt = pattern_config['import']
        
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            content = add_import_if_missing(content, import_stmt)
            changes_made.append(pattern_config['pattern'][:30])
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath, changes_made
    
    return None, []

def main():
    test_dir = Path('/Users/rafehatfield/development/rlike/tests')
    fixed_files = []
    
    for test_file in test_dir.rglob('test_*.py'):
        result, changes = fix_test_file(str(test_file))
        if result:
            fixed_files.append((result, changes))
            print(f"✅ Fixed: {result}")
            for change in changes:
                print(f"   - {change}...")
    
    print(f"\n📊 Fixed {len(fixed_files)} test files")
    return len(fixed_files)

if __name__ == '__main__':
    count = main()
    print(f"Done! Fixed {count} files.")
