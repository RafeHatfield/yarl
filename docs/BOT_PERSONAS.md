# Bot Personas

Bot personas define different playstyles for the automated bot player, allowing varied behavior during soak testing and automated runs.

## Overview

Each persona configures thresholds and weights that influence `BotBrain` decisions:

- **Combat behavior**: When to engage, how far to chase, when to retreat
- **Loot behavior**: Whether to pick up items, priority level
- **Exploration**: Full exploration vs rushing to stairs
- **Survival**: When to drink potions

## Available Personas

### `balanced` (default)

The standard playstyle — explores fully, fights when needed, picks up loot.

| Parameter | Value | Description |
|-----------|-------|-------------|
| `retreat_hp_threshold` | 25% | Retreat when HP drops below this |
| `potion_hp_threshold` | 40% | Drink potion when HP below this |
| `combat_engagement_distance` | 8 | Max tiles to chase enemies |
| `loot_priority` | 1 (normal) | Pick up items normally |
| `prefer_stairs` | false | Explore fully before descending |
| `avoid_combat` | false | Engage visible enemies |

### `cautious`

Plays it safe — retreats early, drinks potions sooner, avoids unnecessary fights.

| Parameter | Value | Description |
|-----------|-------|-------------|
| `retreat_hp_threshold` | 40% | Retreat earlier |
| `potion_hp_threshold` | 50% | Drink potions earlier |
| `combat_engagement_distance` | 5 | Don't chase far |
| `loot_priority` | 1 (normal) | Pick up items normally |
| `prefer_stairs` | false | Explore fully |
| `avoid_combat` | true | Skip non-adjacent enemies |

### `aggressive`

Fights to the death — chases enemies far, ignores loot during combat, rarely retreats.

| Parameter | Value | Description |
|-----------|-------|-------------|
| `retreat_hp_threshold` | 10% | Fight until nearly dead |
| `potion_hp_threshold` | 25% | Only drink when critical |
| `combat_engagement_distance` | 12 | Chase enemies far |
| `loot_priority` | 0 (skip) | Ignore loot |
| `prefer_stairs` | false | Explore fully |
| `avoid_combat` | false | Always engage |

### `greedy`

Prioritizes loot — will detour for items, otherwise balanced combat behavior.

| Parameter | Value | Description |
|-----------|-------|-------------|
| `retreat_hp_threshold` | 25% | Standard retreat |
| `potion_hp_threshold` | 40% | Standard potion use |
| `combat_engagement_distance` | 6 | Moderate chase distance |
| `loot_priority` | 2 (high) | Prioritize loot heavily |
| `prefer_stairs` | false | Explore fully |
| `avoid_combat` | false | Engage visible enemies |

### `speedrunner`

Rushes to stairs — avoids combat, skips loot, minimal engagement.

| Parameter | Value | Description |
|-----------|-------|-------------|
| `retreat_hp_threshold` | 30% | Retreat moderately early |
| `potion_hp_threshold` | 40% | Standard potion use |
| `combat_engagement_distance` | 4 | Minimal chase |
| `loot_priority` | 0 (skip) | Skip all loot |
| `prefer_stairs` | true | Rush to stairs when safe |
| `avoid_combat` | true | Avoid non-adjacent enemies |

## Usage

### Command Line

```bash
# Single bot run with persona
python engine.py --bot --bot-persona cautious

# Soak testing with persona
python engine.py --bot-soak --runs 50 --bot-persona aggressive

# Available personas
python engine.py --bot --bot-persona {balanced,cautious,aggressive,greedy,speedrunner}
```

### Programmatic

```python
from io_layer.bot_brain import BotBrain, get_persona, list_personas

# List available personas
print(list_personas())  # ['balanced', 'cautious', 'aggressive', 'greedy', 'speedrunner']

# Get persona config
config = get_persona("cautious")
print(config.retreat_hp_threshold)  # 0.4

# Create BotBrain with persona
brain = BotBrain(persona="aggressive")
```

## Configuration Parameters

### `retreat_hp_threshold` (float, 0.0-1.0)

HP fraction below which the bot considers retreating from combat. Lower values mean the bot fights longer before fleeing.

### `potion_hp_threshold` (float, 0.0-1.0)

HP fraction below which the bot drinks healing potions (when safe). Higher values mean more conservative potion usage.

### `combat_engagement_distance` (int)

Maximum Manhattan distance at which the bot will chase/engage visible enemies. Beyond this distance, enemies are ignored.

### `loot_priority` (int, 0-2)

- `0` = Skip loot entirely
- `1` = Normal loot pickup (pick up items when standing on them)
- `2` = High priority (future: may detour for visible items)

### `prefer_stairs` (bool)

If `true`, the bot prioritizes finding and using stairs over full floor exploration when the area is safe.

### `avoid_combat` (bool)

If `true`, the bot will not engage enemies that are not adjacent (distance > 1). Adjacent enemies are always fought.

## Soak Testing Use Cases

| Goal | Recommended Persona |
|------|---------------------|
| General stability testing | `balanced` |
| Survivability testing | `cautious` |
| Combat system stress test | `aggressive` |
| Item/inventory testing | `greedy` |
| Stairs/floor transition testing | `speedrunner` |
| Death rate analysis | `aggressive` |

## Implementation Details

- **Source**: `io_layer/bot_brain.py`
- **Tests**: `tests/test_bot_personas.py`
- **CLI integration**: `engine.py` (`--bot-persona` flag)

Personas are implemented as frozen dataclasses (`BotPersonaConfig`) stored in a `PERSONAS` dict. The `BotBrain` class accepts a persona name and loads the corresponding config at initialization.

## Adding New Personas

To add a new persona:

1. Add a new entry to `PERSONAS` dict in `io_layer/bot_brain.py`:

```python
PERSONAS["my_persona"] = BotPersonaConfig(
    name="my_persona",
    retreat_hp_threshold=0.35,
    potion_hp_threshold=0.45,
    combat_engagement_distance=7,
    loot_priority=1,
    prefer_stairs=False,
    avoid_combat=False,
)
```

2. Update the CLI choices in `engine.py`:

```python
parser.add_argument(
    '--bot-persona',
    choices=['balanced', 'cautious', 'aggressive', 'greedy', 'speedrunner', 'my_persona'],
    ...
)
```

3. Add tests in `tests/test_bot_personas.py`

4. Update this documentation








