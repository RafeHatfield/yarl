#!/usr/bin/env python3
"""Extract game_actions.py into modular structure.

This script systematically extracts methods from the monolithic game_actions.py
into focused modules while preserving functionality.
"""

import re
import os

# Read the original file
with open('game_actions.py', 'r') as f:
    content = f.read()
    lines = content.split('\n')

# Find the ActionProcessor class and all its methods
class_start = None
class_end = None

for i, line in enumerate(lines):
    if 'class ActionProcessor:' in line:
        class_start = i
    elif class_start and i > class_start and line and not line.startswith(' ') and not line.startswith('\t'):
        class_end = i
        break

if class_end is None:
    class_end = len(lines)

print(f"ActionProcessor class: lines {class_start} to {class_end}")
print(f"Total lines in class: {class_end - class_start}")

# Extract method ranges
methods = {}
current_method = None
method_start = None

for i in range(class_start, class_end):
    line = lines[i]
    if re.match(r'    def ', line):
        if current_method:
            methods[current_method] = (method_start, i - 1)
        match = re.search(r'def (\w+)\(', line)
        current_method = match.group(1)
        method_start = i

# Add last method
if current_method:
    methods[current_method] = (method_start, class_end - 1)

print(f"\nFound {len(methods)} methods:")
for name, (start, end) in sorted(methods.items()):
    print(f"  {name:40} lines {start:4}-{end:4} ({end-start+1:3} lines)")

# Categorize methods
categories = {
    'core': ['__init__', 'process_actions'],
    'items': ['_handle_pickup', '_handle_inventory_action', '_handle_throw_action', 
              '_handle_search', '_use_inventory_item', '_drop_inventory_item',
              '_handle_show_inventory_deprecated', '_handle_drop_inventory_deprecated'],
    'movement': ['_handle_movement', '_handle_start_auto_explore', '_process_auto_explore_turn',
                 '_process_pathfinding_movement_action', '_handle_mouse_movement'],
    'turns': ['_handle_wait', '_handle_stairs', '_handle_level_up', '_handle_exit'],
    'ui': ['_handle_show_character_screen', '_handle_show_wizard_menu', '_handle_left_click',
           '_handle_right_click', '_handle_sidebar_click', '_handle_sidebar_right_click'],
    'helpers': ['_handle_combat', '_handle_entity_death', '_handle_equipment',
                '_check_secret_reveals', '_create_secret_door_marker',
                '_process_player_status_effects', '_break_invisibility']
}

# Show categorization
print("\n" + "=" * 80)
print("METHOD CATEGORIZATION")
print("=" * 80)
for cat, method_names in categories.items():
    total_lines = sum(methods[m][1] - methods[m][0] + 1 for m in method_names if m in methods)
    print(f"\n{cat.upper():15} ({len(method_names):2} methods, {total_lines:4} lines)")
    for m in method_names:
        if m in methods:
            start, end = methods[m]
            print(f"  ├─ {m:40} {end-start+1:3} lines")
        else:
            print(f"  ├─ {m:40} NOT FOUND")

print("\n✅ Analysis complete. Ready for extraction.")
print("\nNext step: Create individual module files with extracted methods.")

