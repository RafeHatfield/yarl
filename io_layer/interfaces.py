"""Protocol definitions for renderer-agnostic and input-source-agnostic abstractions.

This module defines the Renderer and InputSource protocols that allow the game
to be decoupled from specific rendering technologies and input methods.

The protocols define minimal, focused interfaces:
- Renderer: Handles all screen drawing and display updates
- InputSource: Handles input acquisition and translation to actions

This design allows future extensions (e.g., sprite renderer, bot input) without
changing the main game loop.
"""

from typing import Protocol, Any, Dict, TypedDict, Tuple, Optional


class ActionDict(TypedDict, total=False):
    """Strongly-typed dictionary representing player actions from input.
    
    Keys are optional (total=False) to support the "sometimes-present" semantics
    of current action dictionaries. Each key corresponds to a specific input action
    and carries the relevant data for that action.
    
    Movement and click actions carry coordinate tuples.
    Most other actions are boolean flags.
    """
    
    # Movement (from keyboard or targeting)
    move: Tuple[int, int]
    wait: bool
    
    # Item/inventory actions
    pickup: bool
    show_inventory: bool
    drop_inventory: bool
    throw: bool
    inventory_index: int
    
    # Navigation/level actions
    take_stairs: bool
    start_auto_explore: bool
    search: bool
    
    # UI/menu actions
    show_character_screen: bool
    show_wizard_menu: bool
    
    # System actions
    exit: bool
    restart: bool
    fullscreen: bool
    
    # Mouse/click actions (coordinates in game world or screen space)
    left_click: Tuple[int, int]
    right_click: Tuple[int, int]
    sidebar_click: Tuple[int, int]
    sidebar_right_click: Tuple[int, int]


class Renderer(Protocol):
    """Protocol for rendering the game state to the screen.

    Implementers should handle all low-level rendering details and console
    management. The main game loop depends only on this protocol, not on
    any specific rendering backend.
    """

    def render(self, game_state: Any) -> None:
        """Render the current game state to the screen.

        Args:
            game_state: The current game state containing all entities,
                        maps, messages, and other visual data to display.
        """
        ...


class InputSource(Protocol):
    """Protocol for acquiring and translating player input to game actions.

    Implementers should handle input acquisition (keyboard, mouse, or other
    sources) and translate it into action dictionaries. The main game loop
    depends only on this protocol, not on specific input hardware or methods.
    """

    def next_action(self, game_state: Any) -> ActionDict:
        """Get the next player action based on current input and game state.

        This may block for input or return an empty dict if no input is
        available, depending on the implementation.

        Args:
            game_state: The current game state, for context-aware input handling
                        (e.g., different input modes for different game states).

        Returns:
            An ActionDict (TypedDict) mapping action keys to values.
            Returns an empty dict if no action is available.
        """
        ...

