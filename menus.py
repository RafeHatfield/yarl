"""Menu and UI screen functions.

This module provides functions for displaying various game menus
including inventory, main menu, level up, character screen, and
message boxes. All menus are rendered as centered overlays.
"""

import tcod as libtcod
from tcod import libtcodpy
from entity_dialogue import EntityDialogue
from config.ui_layout import get_ui_layout
from typing import Optional
from components.component_registry import ComponentType


def get_menu_click_index(mouse_x: int, mouse_y: int, header: str, options: list, 
                         width: int, screen_width: int, screen_height: int) -> Optional[int]:
    """Check if mouse click is on a menu item and return the index.
    
    Args:
        mouse_x: Mouse X coordinate (screen space)
        mouse_y: Mouse Y coordinate (screen space)
        header: Menu header text
        options: List of menu option strings
        width: Width of menu
        screen_width: Screen width
        screen_height: Screen height
    
    Returns:
        int: Index of clicked option, or None if click wasn't on an option
    """
    if len(options) > 26 or len(options) == 0:
        return None
    
    # Calculate menu position (same logic as menu() function)
    # Need to calculate header height
    header_height = libtcodpy.console_get_height_rect(
        0, 0, 0, width, screen_height, header
    )
    
    height = len(options) + header_height
    
    # Calculate menu position
    if header == "":
        # Main menu - center on full screen
        menu_x = int(screen_width / 2 - width / 2)
        menu_y = int(screen_height / 2 - height / 2)
    else:
        # In-game menu - center in viewport area
        ui_layout = get_ui_layout()
        viewport_pos = ui_layout.viewport_position
        
        # Center within viewport
        menu_x = viewport_pos[0] + int(ui_layout.viewport_width / 2 - width / 2)
        menu_y = viewport_pos[1] + int(ui_layout.viewport_height / 2 - height / 2)
    
    # Check if click is within menu bounds
    if mouse_x < menu_x or mouse_x >= menu_x + width:
        return None
    if mouse_y < menu_y or mouse_y >= menu_y + height:
        return None
    
    # Calculate which line was clicked
    relative_y = mouse_y - menu_y
    
    # Options start after the header
    if relative_y < header_height:
        return None
    
    option_line = relative_y - header_height
    
    # Check if within options range
    if option_line < 0 or option_line >= len(options):
        return None
    
    return option_line


def menu(con, header, options, width, screen_width, screen_height):
    """Display a menu with options for the player to choose from.

    Creates a centered menu window with a header and lettered options.
    Supports up to 26 options (a-z).

    Args:
        con: The console to draw on
        header (str): Header text for the menu
        options (list): List of option strings
        width (int): Width of the menu window
        screen_width (int): Width of the screen for centering
        screen_height (int): Height of the screen for centering

    Raises:
        ValueError: If more than 26 options are provided
    """
    if len(options) > 26:
        raise ValueError("Cannot have a menu with more than 26 options.")

    # calculate total height for the header (after auto-wrap) and one line per option
    header_height = libtcodpy.console_get_height_rect(
        con, 0, 0, width, screen_height, header
    )
    height = len(options) + header_height

    # create an off-screen console that represents the menu's window
    window = libtcodpy.console_new(width, height)

    # print the header, with auto-wrap
    libtcodpy.console_set_default_foreground(window, (255, 255, 255))
    libtcodpy.console_print_rect_ex(
        window, 0, 0, width, height, libtcodpy.BKGND_NONE, libtcodpy.LEFT, header
    )

    # print all the options
    y = header_height
    letter_index = ord("a")
    for option_text in options:
        text = "(" + chr(letter_index) + ") " + option_text
        libtcodpy.console_print_ex(window, 0, y, libtcodpy.BKGND_NONE, libtcodpy.LEFT, text)
        y += 1
        letter_index += 1

    # Blit the contents of "window" to the root console
    # For main menu (called with empty header), center on FULL screen
    # For in-game menus (called with header), center in viewport
    if header == "":
        # Main menu - center on full screen
        x = int(screen_width / 2 - width / 2)
        y = int(screen_height / 2 - height / 2)
    else:
        # In-game menu - center in viewport area
        from config.ui_layout import get_ui_layout
        ui_layout = get_ui_layout()
        viewport_pos = ui_layout.viewport_position
        
        # Center within viewport
        x = viewport_pos[0] + int(ui_layout.viewport_width / 2 - width / 2)
        y = viewport_pos[1] + int(ui_layout.viewport_height / 2 - height / 2)
    
    libtcodpy.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)


def inventory_menu(con, header, player, inventory_width, screen_width, screen_height):
    """Display the player's inventory as a selectable menu.

    Shows each item in the inventory with equipment status indicators.

    Args:
        con: Console to draw on
        header (str): Menu header text
        player (Entity): Player entity with inventory component
        inventory_width (int): Width of the inventory menu
        screen_width (int): Screen width for centering
        screen_height (int): Screen height for centering
    """
    # show a menu with each item of the inventory as an option
    if len(player.inventory.items) == 0:
        options = ["Inventory is empty."]
    else:
        options = []
        
        # Sort inventory alphabetically for better UX
        sorted_items = sorted(player.inventory.items, key=lambda item: item.name.lower())

        for item in sorted_items:
            display_name = item.get_display_name()
            
            # Check if item is equipped in any slot
            if player.equipment.main_hand == item:
                options.append("{0} (equipped)".format(display_name))
            elif player.equipment.off_hand == item:
                options.append("{0} (equipped)".format(display_name))
            elif player.equipment.head == item:
                options.append("{0} (equipped)".format(display_name))
            elif player.equipment.chest == item:
                options.append("{0} (equipped)".format(display_name))
            elif player.equipment.feet == item:
                options.append("{0} (equipped)".format(display_name))
            else:
                options.append(display_name)

    menu(con, header, options, inventory_width, screen_width, screen_height)


def main_menu(con, background_image, screen_width, screen_height, entity_quote=None):
    """Display the main menu screen with Entity presence.
    
    The Entity's voice greets (mocks) the player on the menu screen,
    establishing the tone immediately. Alan Rickman would be proud.
    
    Note: entity_quote should be selected once outside the render loop
    to prevent flickering. Pass it in rather than generating here.

    Args:
        con: Console to draw on
        background_image: Background image for the menu
        screen_width (int): Screen width
        screen_height (int): Screen height
        entity_quote (str, optional): Pre-selected Entity quote (prevents flickering)
    """
    # Use deprecated method but warnings are suppressed in engine.py
    libtcodpy.image_blit_2x(background_image, 0, 0, 0)

    # Calculate center positions for new screen dimensions (100x52)
    center_x = screen_width // 2  # 50
    center_y = screen_height // 2  # 26
    
    # Title
    libtcodpy.console_set_default_foreground(0, (255, 255, 63))
    libtcodpy.console_print_ex(
        0,
        center_x,
        center_y - 8,  # Back to original vertical spacing
        libtcodpy.BKGND_NONE,
        libtcodpy.CENTER,
        "CATACOMBS OF YARL",
    )
    
    # Entity quote - the personality begins HERE
    # Only generate if not provided (prevents flickering in render loop)
    if entity_quote is None:
        entity_quote = EntityDialogue.get_main_menu_quote()
    
    libtcodpy.console_set_default_foreground(0, (180, 180, 150))  # Muted gold
    libtcodpy.console_print_ex(
        0,
        center_x,
        center_y - 5,  # Between title and menu
        libtcodpy.BKGND_NONE,
        libtcodpy.CENTER,
        f'"{entity_quote}"',
    )
    
    # Author credit
    libtcodpy.console_print_ex(
        0,
        center_x,
        screen_height - 2,
        libtcodpy.BKGND_NONE,
        libtcodpy.CENTER,
        "By Rastaphibian",
    )

    menu(
        con,
        "",
        ["Play a new game", "Continue last game", "Quit"],
        24,
        screen_width,
        screen_height,
    )


def level_up_menu(con, header, player, menu_width, screen_width, screen_height):
    """Display the level up menu for stat selection.

    Args:
        con: Console to draw on
        header (str): Menu header text
        player (Entity): Player entity with level component
        menu_width (int): Width of the menu
        screen_width (int): Screen width for centering
        screen_height (int): Screen height for centering
    """
    options = [
        "Constitution (+20 HP, from {0})".format(player.fighter.max_hp),
        "Strength (+1 attack, from {0})".format(player.fighter.power),
        "Agility (+1 defense, from {0})".format(player.fighter.defense),
    ]

    menu(con, header, options, menu_width, screen_width, screen_height)


def message_box(con, header, width, screen_width, screen_height):
    """Display a simple message box.

    Args:
        con: Console to draw on
        header (str): Message to display
        width (int): Width of the message box
        screen_width (int): Screen width for centering
        screen_height (int): Screen height for centering
    """
    menu(con, header, [], width, screen_width, screen_height)


def character_screen(
    player, character_screen_width, character_screen_height, screen_width, screen_height
):
    """Display the character information screen with slot-based equipment layout.

    Shows player stats, equipped items in slots, and inventory consumables separately.
    Items are lettered for selection (equip/unequip/use).

    Args:
        player (Entity): Player entity with stats
        character_screen_width (int): Width of the character screen
        character_screen_height (int): Height of the character screen
        screen_width (int): Screen width for centering
        screen_height (int): Screen height for centering

    Returns:
        Console: The character screen console
    """
    window = libtcodpy.console_new(character_screen_width, character_screen_height)
    libtcodpy.console_set_default_foreground(window, (255, 255, 255))

    y = 0
    
    # ═══════════════════════════════════════════════════════════
    # TITLE & LEVEL
    # ═══════════════════════════════════════════════════════════
    libtcodpy.console_print_rect_ex(
        window, 0, y, character_screen_width, character_screen_height,
        libtcodpy.BKGND_NONE, libtcodpy.LEFT,
        "CHARACTER INFORMATION"
    )
    y += 1
    
    libtcodpy.console_print_rect_ex(
        window, 0, y, character_screen_width, character_screen_height,
        libtcodpy.BKGND_NONE, libtcodpy.LEFT,
        f"Level: {player.level.current_level}        XP: {player.level.current_xp}/{player.level.experience_to_next_level}"
    )
    y += 2
    
    # ═══════════════════════════════════════════════════════════
    # ATTRIBUTES & COMBAT STATS
    # ═══════════════════════════════════════════════════════════
    libtcodpy.console_print_rect_ex(
        window, 0, y, character_screen_width, character_screen_height,
        libtcodpy.BKGND_NONE, libtcodpy.LEFT,
        "ATTRIBUTES                      COMBAT STATS"
    )
    y += 1
    
    # Get stat modifiers
    str_mod = player.fighter.strength_mod
    dex_mod = player.fighter.dexterity_mod
    con_mod = player.fighter.constitution_mod
    
    # Format modifiers with + or -
    str_mod_str = f"+{str_mod}" if str_mod >= 0 else str(str_mod)
    dex_mod_str = f"+{dex_mod}" if dex_mod >= 0 else str(dex_mod)
    con_mod_str = f"+{con_mod}" if con_mod >= 0 else str(con_mod)
    
    # Get AC breakdown
    ac_breakdown = _get_ac_breakdown(player)
    
    # Get to-hit
    to_hit = dex_mod
    to_hit_str = f"+{to_hit}" if to_hit >= 0 else str(to_hit)
    
    # Attributes (left side)
    libtcodpy.console_print_rect_ex(
        window, 0, y, character_screen_width, character_screen_height,
        libtcodpy.BKGND_NONE, libtcodpy.LEFT,
        f"STR: {player.fighter.strength} ({str_mod_str})  HP:  {player.fighter.hp}/{player.fighter.max_hp}"
    )
    y += 1
    
    libtcodpy.console_print_rect_ex(
        window, 0, y, character_screen_width, character_screen_height,
        libtcodpy.BKGND_NONE, libtcodpy.LEFT,
        f"DEX: {player.fighter.dexterity} ({dex_mod_str})  AC:  {ac_breakdown}"
    )
    y += 1
    
    # Get damage display
    damage_text = _get_damage_display(player)
    libtcodpy.console_print_rect_ex(
        window, 0, y, character_screen_width, character_screen_height,
        libtcodpy.BKGND_NONE, libtcodpy.LEFT,
        f"CON: {player.fighter.constitution} ({con_mod_str})  Dmg: {damage_text}"
    )
    y += 1
    
    # To-hit
    libtcodpy.console_print_rect_ex(
        window, 0, y, character_screen_width, character_screen_height,
        libtcodpy.BKGND_NONE, libtcodpy.LEFT,
        f"                                Hit: {to_hit_str} (DEX)"
    )
    y += 2
    
    # ═══════════════════════════════════════════════════════════
    # EQUIPMENT SLOTS
    # ═══════════════════════════════════════════════════════════
    libtcodpy.console_print_rect_ex(
        window, 0, y, character_screen_width, character_screen_height,
        libtcodpy.BKGND_NONE, libtcodpy.LEFT,
        "EQUIPMENT"
    )
    y += 1
    
    # Display equipment slots with letters for selection
    letter_index = ord('a')
    equipment_items = []
    
    # Weapon slot
    weapon_text, weapon_item = _get_slot_display(player.equipment.main_hand, "Weapon", chr(letter_index))
    equipment_items.append(weapon_item)
    libtcodpy.console_print_rect_ex(
        window, 0, y, character_screen_width, character_screen_height,
        libtcodpy.BKGND_NONE, libtcodpy.LEFT, weapon_text
    )
    y += 1
    letter_index += 1
    
    # Shield/Off-hand slot
    shield_text, shield_item = _get_slot_display(player.equipment.off_hand, "Shield", chr(letter_index))
    equipment_items.append(shield_item)
    libtcodpy.console_print_rect_ex(
        window, 0, y, character_screen_width, character_screen_height,
        libtcodpy.BKGND_NONE, libtcodpy.LEFT, shield_text
    )
    y += 1
    letter_index += 1
    
    # Head slot
    head_text, head_item = _get_slot_display(player.equipment.head, "Head", chr(letter_index))
    equipment_items.append(head_item)
    libtcodpy.console_print_rect_ex(
        window, 0, y, character_screen_width, character_screen_height,
        libtcodpy.BKGND_NONE, libtcodpy.LEFT, head_text
    )
    y += 1
    letter_index += 1
    
    # Chest slot
    chest_text, chest_item = _get_slot_display(player.equipment.chest, "Chest", chr(letter_index))
    equipment_items.append(chest_item)
    libtcodpy.console_print_rect_ex(
        window, 0, y, character_screen_width, character_screen_height,
        libtcodpy.BKGND_NONE, libtcodpy.LEFT, chest_text
    )
    y += 1
    letter_index += 1
    
    # Feet slot
    feet_text, feet_item = _get_slot_display(player.equipment.feet, "Feet", chr(letter_index))
    equipment_items.append(feet_item)
    libtcodpy.console_print_rect_ex(
        window, 0, y, character_screen_width, character_screen_height,
        libtcodpy.BKGND_NONE, libtcodpy.LEFT, feet_text
    )
    y += 2
    letter_index += 1
    
    # ═══════════════════════════════════════════════════════════
    # INVENTORY (Consumables only)
    # ═══════════════════════════════════════════════════════════
    # Get non-equipped items (consumables, unequipped equipment)
    inventory_items = [item for item in player.inventory.items if item not in equipment_items]
    
    libtcodpy.console_print_rect_ex(
        window, 0, y, character_screen_width, character_screen_height,
        libtcodpy.BKGND_NONE, libtcodpy.LEFT,
        f"INVENTORY ({len(inventory_items)}/{player.inventory.capacity})"
    )
    y += 1
    
    if len(inventory_items) == 0:
        libtcodpy.console_print_rect_ex(
            window, 0, y, character_screen_width, character_screen_height,
            libtcodpy.BKGND_NONE, libtcodpy.LEFT,
            "  (empty)"
        )
    else:
        for item in inventory_items[:10]:  # Show up to 10 items
            item_letter = chr(letter_index)
            # Check if item has get_display_name method
            item_name = item.get_display_name() if hasattr(item, 'get_display_name') else item.name
            libtcodpy.console_print_rect_ex(
                window, 0, y, character_screen_width, character_screen_height,
                libtcodpy.BKGND_NONE, libtcodpy.LEFT,
                f"  ({item_letter}) {item_name}"
            )
            y += 1
            letter_index += 1
            
            # Stop if we run out of room
            if y >= character_screen_height - 1:
                break

    # Blit the contents of "window" to the root console
    # Center in viewport area for split-screen layout
    ui_layout = get_ui_layout()
    viewport_pos = ui_layout.viewport_position
    
    # Center within viewport
    x = viewport_pos[0] + ui_layout.viewport_width // 2 - character_screen_width // 2
    y_pos = viewport_pos[1] + ui_layout.viewport_height // 2 - character_screen_height // 2
    libtcodpy.console_blit(
        window, 0, 0, character_screen_width, character_screen_height, 0, x, y_pos, 1.0, 0.7
    )


def _get_slot_display(equipped_item, slot_name, letter):
    """Get display text for an equipment slot with selection letter.
    
    Args:
        equipped_item: The equipped item entity (or None if empty)
        slot_name (str): Name of the slot (e.g., "Weapon", "Head")
        letter (str): Selection letter for this slot
        
    Returns:
        tuple: (display_text, equipped_item)
            - display_text: Formatted string for display
            - equipped_item: The item (for tracking what's equipped)
    """
    if equipped_item is None:
        return (f"({letter}) [{slot_name:7s}] (empty)", None)
    
    # Get item name
    item_name = equipped_item.get_display_name() if hasattr(equipped_item, 'get_display_name') else equipped_item.name
    
    # Get item stats for display
    stats = []
    if equipped_item.components.has(ComponentType.EQUIPPABLE):
        equippable = equipped_item.equippable
        
        # Weapon stats (prefer dice notation over damage range)
        # damage_dice is a direct attribute on equippable
        if hasattr(equippable, 'damage_dice') and equippable.damage_dice:
            # Show dice notation
            stats.append(equippable.damage_dice)
        elif hasattr(equippable, 'damage_min') and hasattr(equippable, 'damage_max') and equippable.damage_max > 0:
            # Fall back to damage range for legacy weapons
            if equippable.damage_min == equippable.damage_max:
                stats.append(f"{equippable.damage_max}")
            else:
                stats.append(f"{equippable.damage_min}-{equippable.damage_max}")
        
        # Armor stats
        # armor_class_bonus is a direct attribute on equippable
        if hasattr(equippable, 'armor_class_bonus') and equippable.armor_class_bonus > 0:
            stats.append(f"+{equippable.armor_class_bonus} AC")
        
        # To-hit bonus
        # to_hit_bonus is a direct attribute on equippable
        if hasattr(equippable, 'to_hit_bonus') and equippable.to_hit_bonus != 0:
            stats.append(f"+{equippable.to_hit_bonus} hit")
    
    stats_text = f" ({', '.join(stats)})" if stats else ""
    return (f"({letter}) [{slot_name:7s}] {item_name}{stats_text}", equipped_item)


def _get_ac_breakdown(player):
    """Get detailed AC breakdown showing base + DEX + armor.
    
    Args:
        player: Player entity
        
    Returns:
        str: AC breakdown (e.g., "13 (10 + 1 DEX + 2 armor)")
    """
    base_ac = 10
    dex_bonus = player.fighter.dexterity_mod
    
    # Get armor AC bonus and check for DEX caps
    armor_ac_bonus = 0
    most_restrictive_dex_cap = None
    
    equipment = player.get_component_optional(ComponentType.EQUIPMENT)
    if equipment:
        for item in [equipment.main_hand, equipment.off_hand,
                    equipment.head, equipment.chest, equipment.feet]:
            if item and item.components.has(ComponentType.EQUIPPABLE):
                equippable = item.equippable
                
                # Add AC bonus
                armor_ac_bonus += getattr(equippable, 'armor_class_bonus', 0)
                
                # Check for DEX cap
                armor_type = getattr(equippable, 'armor_type', None)
                item_dex_cap = getattr(equippable, 'dex_cap', None)
                
                if armor_type in ['light', 'medium', 'heavy'] and item_dex_cap is not None:
                    if most_restrictive_dex_cap is None:
                        most_restrictive_dex_cap = item_dex_cap
                    else:
                        most_restrictive_dex_cap = min(most_restrictive_dex_cap, item_dex_cap)
    
    # Apply DEX cap
    original_dex_bonus = dex_bonus
    if most_restrictive_dex_cap is not None:
        dex_bonus = min(dex_bonus, most_restrictive_dex_cap)
    
    total_ac = base_ac + dex_bonus + armor_ac_bonus
    
    # Format with cap indicator if applicable
    if most_restrictive_dex_cap is not None and original_dex_bonus > most_restrictive_dex_cap:
        dex_str = f"{dex_bonus} DEX*"  # Asterisk indicates capped
    else:
        dex_str = f"{dex_bonus} DEX" if dex_bonus != 0 else "0 DEX"
    
    # Format AC display
    if armor_ac_bonus > 0:
        return f"{total_ac} ({base_ac}+{dex_str}+{armor_ac_bonus})"
    elif dex_bonus != 0:
        return f"{total_ac} ({base_ac}+{dex_str})"
    else:
        return f"{total_ac}"


def _get_damage_display(player):
    """Get damage display for character screen.
    
    Args:
        player: Player entity
        
    Returns:
        str: Damage display (e.g., "1d4+2" or "1-2+2")
    """
    str_mod = player.fighter.strength_mod
    
    # Check for equipped weapon
    equipment = player.get_component_optional(ComponentType.EQUIPMENT)
    if (equipment and equipment.main_hand and
        equipment.main_hand.components.has(ComponentType.EQUIPPABLE)):
        
        weapon = equipment.main_hand.equippable
        
        # Prefer dice notation if available
        if hasattr(weapon, 'damage_dice') and weapon.damage_dice:
            if str_mod != 0:
                str_mod_str = f"+{str_mod}" if str_mod > 0 else str(str_mod)
                return f"{weapon.damage_dice}{str_mod_str}"
            else:
                return weapon.damage_dice
        
        # Fall back to damage range for legacy weapons
        if hasattr(weapon, 'damage_min') and weapon.damage_max > 0:
            if str_mod != 0:
                str_mod_str = f"+{str_mod}" if str_mod > 0 else str(str_mod)
                return f"{weapon.damage_min}-{weapon.damage_max}{str_mod_str}"
            else:
                return f"{weapon.damage_min}-{weapon.damage_max}"
    
    # Natural damage
    if hasattr(player.fighter, 'damage_min') and player.fighter.damage_max > 0:
        if str_mod != 0:
            str_mod_str = f"+{str_mod}" if str_mod > 0 else str(str_mod)
            return f"{player.fighter.damage_min}-{player.fighter.damage_max}{str_mod_str}"
        else:
            return f"{player.fighter.damage_min}-{player.fighter.damage_max}"
    
    # Fallback
    if str_mod != 0:
        return f"+{str_mod}" if str_mod > 0 else str(str_mod)
    return "0"


def _get_attack_display_text(player):
    """Get attack display text with weapon damage range and power bonuses.
    
    Args:
        player (Entity): Player entity with fighter and equipment components
        
    Returns:
        str: Attack display text showing physical damage + magical power
    """
    # Get base power (should be 0 for natural, bonuses from equipment/magic)
    base_power = player.fighter.base_power
    
    # Check for equipped weapon with damage range
    equipment = player.get_component_optional(ComponentType.EQUIPMENT)
    if (equipment and equipment.main_hand and 
        equipment.main_hand.components.has(ComponentType.EQUIPPABLE)):
        
        weapon = equipment.main_hand
        equippable = weapon.equippable
        
        # Get weapon damage range
        if hasattr(equippable, 'damage_min') and hasattr(equippable, 'damage_max'):
            if (equippable.damage_min is not None and equippable.damage_max is not None and
                equippable.damage_max > 0):
                weapon_range = f"{equippable.damage_min}-{equippable.damage_max}"
                
                # Get power bonus from weapon
                power_bonus = getattr(equippable, 'power_bonus', 0)
                total_power = base_power + power_bonus
                
                if total_power > 0:
                    total_min = equippable.damage_min + total_power
                    total_max = equippable.damage_max + total_power
                    return f"Attack: {weapon_range} + {total_power} power = {total_min}-{total_max}"
                else:
                    return f"Attack: {weapon_range} (weapon damage)"
        
        # Fallback to power bonus only if no damage range
        power_bonus = getattr(equippable, 'power_bonus', 0)
        if power_bonus > 0:
            total_power = base_power + power_bonus
            return f"Attack: {total_power} power"
    
    # No weapon - show natural damage + any base power
    if hasattr(player.fighter, 'damage_min') and hasattr(player.fighter, 'damage_max'):
        if (player.fighter.damage_min is not None and player.fighter.damage_max is not None and
            player.fighter.damage_max > 0):
            natural_range = f"{player.fighter.damage_min}-{player.fighter.damage_max}"
            
            if base_power > 0:
                total_min = player.fighter.damage_min + base_power
                total_max = player.fighter.damage_max + base_power
                return f"Attack: {natural_range} + {base_power} power = {total_min}-{total_max}"
            else:
                return f"Attack: {natural_range} (natural)"
    
    # Fallback to just power
    return f"Attack: {base_power} power"


def _get_defense_display_text(player):
    """Get defense display text with armor defense range.
    
    Args:
        player (Entity): Player entity with fighter and equipment components
        
    Returns:
        str: Defense display text with armor defense range if applicable
    """
    # Get base defense without equipment bonuses
    base_defense = player.fighter.base_defense
    
    # Check for equipped armor with defense range
    equipment = player.get_component_optional(ComponentType.EQUIPMENT)
    if (equipment and equipment.off_hand and 
        equipment.off_hand.components.has(ComponentType.EQUIPPABLE)):
        
        armor = equipment.off_hand
        equippable = armor.equippable
        
        # If armor has meaningful defense range, show it
        if hasattr(equippable, 'defense_min') and hasattr(equippable, 'defense_max'):
            if (equippable.defense_min is not None and equippable.defense_max is not None and
                equippable.defense_max > 0):
                armor_range = f"{equippable.defense_min}-{equippable.defense_max}"
                total_min = base_defense + equippable.defense_min
                total_max = base_defense + equippable.defense_max
                return f"Defense: {base_defense} + {armor_range} = {total_min}-{total_max}"
        
        # Fallback to defense bonus if no defense range
        defense_bonus = getattr(equippable, 'defense_bonus', 0)
        if defense_bonus > 0:
            total_defense = base_defense + defense_bonus
            return f"Defense: {base_defense} + {defense_bonus} = {total_defense}"
    
    # No armor or no bonus
    return f"Defense: {base_defense}"
