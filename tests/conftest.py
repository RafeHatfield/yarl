"""
Pytest configuration and shared fixtures for rlike game testing.
"""

import pytest
import config.level_template_registry as ltr_module
from unittest.mock import Mock, MagicMock, patch
from components.ai import BasicMonster
from components.equipment import Equipment
from components.fighter import Fighter
from components.inventory import Inventory
from components.item import Item
from entity import Entity
from game_messages import Message
from item_functions import heal, cast_fireball
from render_functions import RenderOrder
from spells.spell_catalog import register_all_spells
from spells import get_spell_registry


# ---------------------------------------------------------------------------
# pytest-mock fallback
# ---------------------------------------------------------------------------

try:  # pragma: no cover - imported for typing/availability check only
    import pytest_mock  # type: ignore
except Exception:  # pragma: no cover - fallback path when plugin missing
    pytest_mock = None  # type: ignore


if not pytest_mock:  # pragma: no cover - executed only when plugin unavailable

    @pytest.fixture
    def mocker():
        """Minimal fallback for the ``pytest-mock`` fixture.

        Some CI environments in this codebase run without the optional
        ``pytest-mock`` dependency installed.  The majority of tests only need
        the fixture's ``patch`` helper, so we provide a tiny shim that mirrors
        the subset of behaviour our tests rely on.
        """

        active_patches = []

        class _Mocker:
            """Lightweight substitute exposing ``patch`` and ``stopall``."""

            def patch(self, target, *args, **kwargs):
                patcher = patch(target, *args, **kwargs)
                mocked = patcher.start()
                active_patches.append(patcher)
                return mocked

            def stopall(self):
                while active_patches:
                    active_patches.pop().stop()

        helper = _Mocker()
        try:
            yield helper
        finally:
            helper.stopall()


@pytest.fixture(autouse=True)
def reset_level_template_registry():
    """Reset the global level template registry between tests.
    
    This prevents test pollution where templates loaded in one test
    affect subsequent tests. The autouse=True makes this run automatically
    for every test.
    """
    # Clear the global registry before each test
    ltr_module._level_template_registry = None
    yield
    # Clear it after the test too for good measure
    ltr_module._level_template_registry = None


@pytest.fixture
def mock_libtcod(mocker):
    """Mock the libtcod library for headless testing."""
    # Mock common libtcod functions
    mock_tcod = MagicMock()

    # Mock colors as simple tuples
    mock_tcod.white = (255, 255, 255)
    mock_tcod.red = (255, 0, 0)
    mock_tcod.green = (0, 255, 0)
    mock_tcod.blue = (0, 0, 255)
    mock_tcod.yellow = (255, 255, 0)
    mock_tcod.orange = (255, 127, 0)
    mock_tcod.violet = (127, 0, 255)
    mock_tcod.light_red = (255, 63, 63)
    mock_tcod.dark_red = (191, 0, 0)
    mock_tcod.light_cyan = (63, 255, 255)
    mock_tcod.desaturated_green = (63, 127, 63)
    mock_tcod.darker_green = (0, 127, 0)
    mock_tcod.light_gray = (159, 159, 159)
    mock_tcod.black = (0, 0, 0)

    # Create a proper mock FOV map that behaves like the real thing
    mock_fov_map = MagicMock()
    mock_fov_map.map_c = MagicMock()  # Required for tcod internal calls
    mock_fov_map.transparent = MagicMock()
    mock_fov_map.walkable = MagicMock()
    mock_fov_map.compute_fov = MagicMock()

    # Mock the tcod.map module
    mock_tcod.map = MagicMock()
    mock_tcod.map.Map.return_value = mock_fov_map

    # Mock FOV functions to return predictable results
    mock_tcod.map_is_in_fov.return_value = True
    mock_tcod.map_new.return_value = mock_fov_map
    mock_tcod.map_set_properties.return_value = None
    mock_tcod.map_compute_fov.return_value = None

    # Mock pathfinding functions
    mock_path = MagicMock()
    mock_tcod.path_new_using_map.return_value = mock_path
    mock_tcod.path_compute.return_value = None
    mock_tcod.path_is_empty.return_value = False
    mock_tcod.path_size.return_value = 5
    mock_tcod.path_walk.return_value = (11, 11)
    mock_tcod.path_delete.return_value = None

    # Apply the mock at multiple levels to catch all imports
    mocker.patch("tcod.libtcodpy", mock_tcod)
    mocker.patch("item_functions.libtcodpy", mock_tcod)
    mocker.patch("components.ai.libtcod", mock_tcod)
    mocker.patch("entity.libtcodpy", mock_tcod)
    mocker.patch("entity.tcod", mock_tcod)
    mocker.patch("render_functions.libtcod", mock_tcod)

    return mock_tcod


@pytest.fixture
def basic_fighter():
    """Create a basic fighter component for testing."""
    return Fighter(hp=30, defense=2, power=5)


@pytest.fixture
def basic_inventory():
    """Create a basic inventory component for testing."""
    return Inventory(26)


@pytest.fixture
def player_entity(basic_fighter, basic_inventory, mock_libtcod):
    """Create a basic player entity for testing."""

    equipment = Equipment()
    return Entity(
        x=10,
        y=10,
        char="@",
        color=mock_libtcod.white,
        name="Player",
        blocks=True,
        render_order=RenderOrder.ACTOR,
        fighter=basic_fighter,
        inventory=basic_inventory,
        equipment=equipment,
    )


@pytest.fixture
def enemy_entity(mock_libtcod):
    """Create a basic enemy entity for testing."""

    fighter = Fighter(hp=20, defense=1, power=3)
    ai = BasicMonster()
    equipment = Equipment()
    return Entity(
        x=15,
        y=15,
        char="o",
        color=mock_libtcod.desaturated_green,
        name="Orc",
        blocks=True,
        render_order=RenderOrder.ACTOR,
        fighter=fighter,
        ai=ai,
        equipment=equipment,
    )


@pytest.fixture
def healing_potion(mock_libtcod):
    """Create a healing potion item for testing."""

    item_component = Item(use_function=heal, amount=10)
    return Entity(
        x=5,
        y=5,
        char="!",
        color=mock_libtcod.violet,
        name="Healing Potion",
        render_order=RenderOrder.ITEM,
        item=item_component,
    )


@pytest.fixture
def fireball_scroll(mock_libtcod):
    """Create a fireball scroll item for testing."""

    item_component = Item(
        use_function=cast_fireball,
        targeting=True,
        targeting_message=Message(
            "Left-click a target tile for the fireball, or right-click to cancel.",
            mock_libtcod.light_cyan,
        ),
        damage=12,
        radius=3,
    )
    return Entity(
        x=5,
        y=5,
        char="#",
        color=mock_libtcod.red,
        name="Fireball Scroll",
        render_order=RenderOrder.ITEM,
        item=item_component,
    )


@pytest.fixture
def mock_entities(player_entity, enemy_entity):
    """Create a list of mock entities for testing."""
    return [player_entity, enemy_entity]


@pytest.fixture
def mock_fov_map(mock_libtcod):
    """Create a mock FOV map for testing."""
    mock_fov_map = MagicMock()
    mock_fov_map.map_c = MagicMock()  # Required for tcod internal calls
    return mock_fov_map


@pytest.fixture
def mock_game_state():
    """Create mock game state data."""
    return {
        "entities": [],
        "fov_map": Mock(),
        "game_map": Mock(),
        "target_x": 12,
        "target_y": 12,
    }


@pytest.fixture(autouse=True, scope="function")
def reset_spell_registry():
    """Reset and re-register spells before each test.
    
    This ensures that all spells are available in every test without
    requiring manual registration, and prevents test pollution.
    """
    # Clear any existing spells
    get_spell_registry().clear()
    
    # Register all spells
    register_all_spells()
    
    yield
    
    # Cleanup after test (optional - could leave for performance)
    # get_spell_registry().clear()
