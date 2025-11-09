"""AI component system - Compatibility shim for backward compatibility.

This module now re-exports all AI classes from the components/ai/ package.
The monolithic ai.py file has been split into focused modules:

- components/ai/boss_ai.py - BossAI class
- components/ai/basic_monster.py - BasicMonster class
- components/ai/mindless_zombie.py - MindlessZombieAI class
- components/ai/confused_monster.py - ConfusedMonster class
- components/ai/slime_ai.py - SlimeAI class
- components/ai/_helpers.py - Shared helper functions

All imports like "from components.ai import BasicMonster" will continue to work.

For new code, you can import directly from sub-modules if preferred:
    from components.ai.basic_monster import BasicMonster
"""

# Re-export all AI classes and helpers for backward compatibility
from components.ai import (
    BossAI,
    BasicMonster,
    MindlessZombieAI,
    ConfusedMonster,
    SlimeAI,
    find_taunted_target,
    get_weapon_reach,
)

__all__ = [
    'BossAI',
    'BasicMonster',
    'MindlessZombieAI',
    'ConfusedMonster',
    'SlimeAI',
    'find_taunted_target',
    'get_weapon_reach',
]
