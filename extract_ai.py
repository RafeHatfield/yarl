#!/usr/bin/env python3
"""Extract components/ai.py into separate class files."""

import re

# Read original file
with open('components/ai.py', 'r') as f:
    lines = f.readlines()

# Find helper functions and imports (lines before first class)
first_class_line = None
for i, line in enumerate(lines):
    if re.match(r'^class \w+', line):
        first_class_line = i
        break

# Extract common imports and helpers (everything before first class)
common_header = ''.join(lines[:first_class_line])

# Find each class and its boundaries
classes = []
for i, line in enumerate(lines):
    if re.match(r'^class (\w+)', line):
        match = re.search(r'class (\w+)', line)
        class_name = match.group(1)
        # Find end of this class (next class or end of file)
        end_line = len(lines)
        for j in range(i + 1, len(lines)):
            if re.match(r'^class \w+', lines[j]):
                end_line = j
                break
        classes.append((class_name, i, end_line))

print("=" * 80)
print("AI CLASS EXTRACTION PLAN")
print("=" * 80)
print(f"\nCommon header: {first_class_line} lines (imports + helpers)")
print(f"\nClasses to extract:")
for name, start, end in classes:
    print(f"  {name:20} lines {start:4}-{end:4} ({end-start:3} lines)")

# Create shared helpers file
helpers_content = common_header + """
# These helper functions are used by multiple AI classes

"""

with open('components/ai/_helpers.py', 'w') as f:
    f.write(helpers_content)

print("\n✅ Created components/ai/_helpers.py")

# Create __init__.py with imports
init_content = '''"""AI component system for monster behaviors.

This package contains different AI implementations for monsters:
- BossAI: Boss monster behavior
- BasicMonster: Standard monster AI
- MindlessZombieAI: Mindless zombie behavior  
- ConfusedMonster: Confused state AI
- SlimeAI: Slime-specific behavior

Helper functions are in _helpers.py
"""

from .boss_ai import BossAI
from .basic_monster import BasicMonster
from .mindless_zombie import MindlessZombieAI
from .confused_monster import ConfusedMonster
from .slime_ai import SlimeAI
from ._helpers import find_taunted_target, get_weapon_reach

__all__ = [
    'BossAI',
    'BasicMonster',
    'MindlessZombieAI',
    'ConfusedMonster',
    'SlimeAI',
    'find_taunted_target',
    'get_weapon_reach',
]
'''

with open('components/ai/__init__.py', 'w') as f:
    f.write(init_content)

print("✅ Created components/ai/__init__.py")

# Extract each class into its own file
class_files = {
    'BossAI': 'boss_ai.py',
    'BasicMonster': 'basic_monster.py',
    'MindlessZombieAI': 'mindless_zombie.py',
    'ConfusedMonster': 'confused_monster.py',
    'SlimeAI': 'slime_ai.py',
}

for class_name, start, end in classes:
    filename = class_files.get(class_name, f'{class_name.lower()}.py')
    filepath = f'components/ai/{filename}'
    
    # Get class content
    class_lines = lines[start:end]
    
    # Create file with imports + class
    file_content = common_header.rstrip() + '\n\n\n' + ''.join(class_lines)
    
    with open(filepath, 'w') as f:
        f.write(file_content)
    
    print(f"✅ Created {filepath} ({end-start} lines)")

print("\n" + "=" * 80)
print("✅ EXTRACTION COMPLETE!")
print("=" * 80)
print("\nNext: Update components/ai.py to be a compatibility shim")
print("      (or rename to components/ai_old.py for reference)")

