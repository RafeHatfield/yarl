#!/usr/bin/env python3
"""
Comprehensive batch fix for test components - handles all component types.
"""

import os
import re
from pathlib import Path

def process_file(filepath):
    """Process a single test file to add component registration."""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    modified = False
    new_lines = []
    needs_import = False
    has_import = False
    
    # Check if already has import
    for line in lines:
        if 'ComponentType' in line:
            has_import = True
            break
    
    i = 0
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        
        # Check for direct component assignment patterns
        # Pattern: entity.component = Component(...)
        match = re.match(r'^(\s+)(\w+)\.(\w+)\s*=\s*(\w+)\((.*)\)\s*$', line)
        if match:
            indent, var, component, component_class, args = match.groups()
            
            # Map component names to ComponentType
            component_type_map = {
                'fighter': 'FIGHTER',
                'equipment': 'EQUIPMENT',
                'inventory': 'INVENTORY',
                'item': 'ITEM',
                'ai': 'AI',
                'wand': 'WAND',
                'equippable': 'EQUIPPABLE',
                'level': 'LEVEL',
                'loot': 'LOOT',
                'signpost': 'SIGNPOST',
                'mural': 'MURAL',
                'portal': 'PORTAL',
            }
            
            if component in component_type_map:
                needs_import = True
                component_type = component_type_map[component]
                # Add component registration line
                registration = f'{indent}{var}.components.add(ComponentType.{component_type}, {var}.{component})\n'
                new_lines.append(registration)
                modified = True
        
        i += 1
    
    # Add import if needed
    if needs_import and not has_import:
        # Find where to insert import
        for j, line in enumerate(new_lines):
            if line.startswith('import ') or line.startswith('from '):
                # Find end of import block
                k = j
                while k < len(new_lines) and (new_lines[k].startswith('import ') or new_lines[k].startswith('from ') or new_lines[k].strip() == ''):
                    k += 1
                new_lines.insert(k, 'from components.component_registry import ComponentType\n')
                break
    
    if modified or needs_import:
        with open(filepath, 'w') as f:
            f.writelines(new_lines)
        return True
    
    return False

def main():
    test_dir = Path('/Users/rafehatfield/development/rlike/tests')
    fixed_count = 0
    
    for test_file in sorted(test_dir.rglob('test_*.py')):
        if process_file(str(test_file)):
            fixed_count += 1
            print(f"✅ {test_file.name}")
    
    return fixed_count

if __name__ == '__main__':
    count = main()
    print(f"\n📊 Updated {count} test files")
