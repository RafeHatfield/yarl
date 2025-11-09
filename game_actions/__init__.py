"""Game action processing system - Refactored into focused modules.

This package provides a clean, modular way to handle game actions by breaking
down the monolithic action processing into focused, testable components.

Also integrates Entity dialogue for key game moments (Phase 1 expansion).

NOTE: This is a refactored version of the original game_actions.py module.
For backward compatibility, ActionProcessor is still imported from here.

Module Structure:
- action_processor.py: Core ActionProcessor class and process_actions()
- item_actions.py: Item pickup, drop, use, and search actions
- combat_actions.py: Combat and attack-related actions
- equipment_actions.py: Equipment equipping/unequipping
- movement_actions.py: Movement, pathfinding, and auto-explore
- turn_actions.py: Turn transitions (wait, stairs, level up, exit)
"""

from .action_processor import ActionProcessor

__all__ = ['ActionProcessor']

