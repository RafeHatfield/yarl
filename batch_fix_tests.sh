#!/bin/bash
# Batch fix common test patterns across all failing test files

cd /Users/rafehatfield/development/rlike

# List of files with failing tests to process
FILES=(
  "tests/test_item_seeking_ai.py"
  "tests/test_player_migration.py"
  "tests/test_armor_dex_caps.py"
  "tests/test_slime_splitting.py"
  "tests/test_d20_combat.py"
  "tests/test_base_damage_system.py"
  "tests/test_combat_debug_logging.py"
  "tests/test_corpse_behavior.py"
  "tests/test_healing_and_init_fixes.py"
  "tests/test_pathfinding_turn_transitions.py"
  "tests/test_save_load_basic.py"
  "tests/test_loot_dropping_positions.py"
  "tests/test_armor_slots.py"
  "tests/test_json_save_load_comprehensive.py"
  "tests/test_map_rendering_regression.py"
  "tests/test_room_generators.py"
  "tests/test_item_drop_fix.py"
  "tests/test_monster_loot_dropping.py"
  "tests/test_entity_sorting_cache.py"
  "tests/test_corrosion_mechanics.py"
  "tests/test_component_type_scoping.py"
  "tests/test_combat_message_clarity.py"
  "tests/test_boss_dialogue.py"
  "tests/test_fighter_equipment.py"
  "tests/test_equipment_migration.py"
  "tests/test_engine_integration.py"
  "tests/integration/test_spell_scenario_integration.py"
  "tests/smoke/test_game_startup.py"
)

echo "Processing ${#FILES[@]} test files..."

for file in "${FILES[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "⚠️  Skipping $file (not found)"
    continue
  fi
  
  echo "📝 Processing: $file"
  
  # Add ComponentType import if not present and needed
  if grep -q "from components\." "$file" && ! grep -q "from components.component_registry import ComponentType" "$file"; then
    # Find last import line
    last_import=$(grep -n "^from \|^import " "$file" | tail -n 1 | cut -d: -f1)
    if [[ -n "$last_import" ]]; then
      sed -i.bak "${last_import}a\\
from components.component_registry import ComponentType
" "$file"
      echo "  ✓ Added ComponentType import"
    fi
  fi
  
done

echo "✅ Batch processing complete!"
echo "Run pytest to see results"

