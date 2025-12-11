"""NPC Dialogue Screen for Guide encounters.

Renders dialogue trees for NPCs like the Ghost Guide.
Displays NPC responses and player choices in a menu format.
"""

import tcod
import textwrap
from typing import Optional, Tuple, List
from game_states import GameStates
from components.npc_dialogue import DialogueOption


def render_npc_dialogue(console: int, npc_name: str, npc_response: str, 
                       options: List[DialogueOption], selected_index: int = 0,
                       screen_width: int = 80, screen_height: int = 50) -> None:
    """Render an NPC dialogue screen with player choices.
    
    Args:
        console: libtcod console reference (0 for root)
        npc_name: Name of the NPC speaking
        npc_response: The NPC's current dialogue text
        options: List of DialogueOption objects the player can choose
        selected_index: Currently highlighted choice
        screen_width: Width of the screen
        screen_height: Height of the screen
    """
    # Clear the console
    tcod.console_clear(console)
    
    # Define colors
    bg_color = tcod.Color(20, 12, 28)  # Dark purple
    title_color = tcod.Color(150, 220, 255)  # Light cyan (ghostly)
    text_color = tcod.Color(200, 200, 200)  # Light gray
    choice_color = tcod.Color(255, 255, 100)  # Yellow for choices
    selected_color = tcod.Color(255, 150, 50)  # Orange for selected
    
    # Fill background
    for y in range(screen_height):
        for x in range(screen_width):
            tcod.console_set_char_background(console, x, y, bg_color, tcod.BKGND_SET)
    
    # Title
    title = f"=== {npc_name} ==="
    tcod.console_set_default_foreground(console, title_color)
    tcod.console_print_ex(
        console,
        screen_width // 2, 2,
        tcod.BKGND_NONE, tcod.CENTER,
        title
    )
    
    # NPC Response (wrapped text)
    y_offset = 5
    response_width = screen_width - 10
    wrapped_response = textwrap.wrap(npc_response, response_width)
    
    tcod.console_set_default_foreground(console, text_color)
    for i, line in enumerate(wrapped_response):
        if y_offset + i >= screen_height - 15:  # Leave room for choices
            break
        tcod.console_print(console, 5, y_offset + i, line)
    
    # Player Choices
    y_offset = y_offset + len(wrapped_response) + 3
    
    if y_offset < screen_height - 10:
        tcod.console_set_default_foreground(console, text_color)
        tcod.console_print(console, 5, y_offset, "Your response:")
        y_offset += 2
        
        for i, option in enumerate(options):
            if y_offset >= screen_height - 2:
                break
            
            # Highlight selected option
            if i == selected_index:
                tcod.console_set_default_foreground(console, selected_color)
                prefix = "> "
            else:
                tcod.console_set_default_foreground(console, choice_color)
                prefix = "  "
            
            # Wrap long options
            option_text = f"{chr(ord('a') + i)}) {option.player_option}"
            wrapped_option = textwrap.wrap(option_text, response_width - 4)
            
            for j, line in enumerate(wrapped_option):
                if y_offset >= screen_height - 2:
                    break
                tcod.console_print(console, 7, y_offset, f"{prefix if j == 0 else '   '}{line}")
                y_offset += 1
            y_offset += 1  # Extra space between options
    
    # Instructions
    tcod.console_set_default_foreground(console, tcod.Color(128, 128, 128))
    instructions = "Arrow keys / letter keys to select | Enter/Space to choose | ESC to leave"
    tcod.console_print_ex(
        console,
        screen_width // 2, screen_height - 2,
        tcod.BKGND_NONE, tcod.CENTER,
        instructions
    )
    
    # Flush to screen
    tcod.console_flush()


def handle_dialogue_input(key: tcod.Key, options: List[DialogueOption], 
                         selected_index: int) -> Tuple[Optional[str], int, bool]:
    """Process player input during dialogue.
    
    Args:
        key: The pressed key
        options: Available dialogue options
        selected_index: Currently selected option index
    
    Returns:
        Tuple of (chosen_option_id, new_selected_index, should_exit)
        - chosen_option_id is None if no choice was made
        - should_exit is True if player wants to close dialogue
    """
    # ESC - exit dialogue
    if key.vk == tcod.KEY_ESCAPE:
        return (None, selected_index, True)
    
    # Arrow keys - navigate
    if key.vk == tcod.KEY_UP and selected_index > 0:
        return (None, selected_index - 1, False)
    
    if key.vk == tcod.KEY_DOWN and selected_index < len(options) - 1:
        return (None, selected_index + 1, False)
    
    # Enter/Space - confirm selection
    if key.vk in (tcod.KEY_ENTER, tcod.KEY_SPACE):
        chosen = options[selected_index]
        return (chosen.id, selected_index, chosen.ends_conversation)
    
    # Letter keys - quick select
    if key.c >= ord('a') and key.c < ord('a') + len(options):
        index = key.c - ord('a')
        chosen = options[index]
        return (chosen.id, index, chosen.ends_conversation)
    
    # No action
    return (None, selected_index, False)


def show_npc_dialogue_screen(npc, game_state_manager) -> GameStates:
    """Display the dialogue interface for an NPC.
    
    This is the main entry point for dialogue interactions.
    
    Args:
        npc: The NPC entity to talk to (must have npc_dialogue component)
        game_state_manager: The game's state manager
    
    Returns:
        The game state to transition to (PLAYERS_TURN or NPC_DIALOGUE)
    """
    if not hasattr(npc, 'npc_dialogue') or not npc.npc_dialogue:
        # No dialogue available
        return GameStates.PLAYERS_TURN
    
    dialogue = npc.npc_dialogue
    selected_index = 0
    
    # Track current NPC response
    current_response = None
    
    # Show greeting and introduction on first interaction
    first_time = True
    
    while True:
        # Check if encounter is still active
        if not dialogue.current_encounter:
            # Dialogue ended
            return GameStates.PLAYERS_TURN
        
        # Get available options
        available_options = dialogue.get_available_options()
        if not available_options:
            # No options left - end dialogue with farewell
            farewell = dialogue.end_encounter()
            # TODO: Show farewell in message log or as overlay
            return GameStates.PLAYERS_TURN
        
        # Build NPC response text
        if first_time:
            # First time: Show greeting + introduction
            greeting = dialogue.get_greeting() or ""
            introduction = dialogue.get_introduction() or ""
            npc_response = f"{greeting}\n\n{introduction}"
            first_time = False
        elif current_response:
            # After player choice: Show the response for that choice
            npc_response = current_response
            current_response = None  # Clear for next iteration
        else:
            # Fallback: show introduction
            npc_response = dialogue.get_introduction() or ""
        
        # Render the dialogue screen
        render_npc_dialogue(
            console=0,  # Root console
            npc_name=npc.name,
            npc_response=npc_response,
            options=available_options,
            selected_index=selected_index,
            screen_width=80,
            screen_height=50
        )
        
        # Wait for input
        key = tcod.console_wait_for_keypress(True)
        
        # Handle input
        chosen_id, selected_index, should_exit = handle_dialogue_input(
            key, available_options, selected_index
        )
        
        if should_exit:
            # Player wants to leave
            farewell = dialogue.end_encounter()
            return GameStates.PLAYERS_TURN
        
        if chosen_id:
            # Player made a choice
            chosen_option = dialogue.select_option(chosen_id)
            
            if chosen_option:
                # Store the NPC's response to show on next render
                current_response = chosen_option.npc_response
                
                # Reset selection for next set of options
                selected_index = 0
                
                # Sync knowledge with player's Victory component
                if chosen_option.unlocks_knowledge:
                    player = game_state_manager.state.player
                    if player:
                        # Ensure player has victory component (create if needed for early-game knowledge)
                        if not hasattr(player, 'victory') or not player.victory:
                            from components.victory import Victory
                            player.victory = Victory()
                            player.victory.owner = player

                        player.victory.unlock_knowledge(chosen_option.unlocks_knowledge)
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.info(f"Player unlocked knowledge: {chosen_option.unlocks_knowledge}")
                
                # Check if this ends the conversation
                if chosen_option.ends_conversation:
                    farewell = dialogue.end_encounter()
                    return GameStates.PLAYERS_TURN

