#!/usr/bin/env python3
"""
Demo script showing the combat debug logging system.

This script demonstrates how combat calculations are logged in detail
when testing mode is enabled, showing the breakdown of attack vs defense.
"""

import os
import sys
from unittest.mock import Mock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from components.fighter import Fighter
from components.equipment import Equipment
from components.equippable import Equippable
from equipment_slots import EquipmentSlots
from config.testing_config import set_testing_mode


def demo_combat_logging():
    """Demonstrate combat debug logging with various scenarios."""
    print("🎮 Combat Debug Logging Demo")
    print("=" * 50)
    
    # Enable testing mode
    set_testing_mode(True)
    print("✅ Testing mode enabled - combat logging active")
    print("📝 Combat details will be logged to: combat_debug.log")
    print()
    
    # Create entities
    orc = Mock()
    orc.name = "orc"
    orc.fighter = Fighter(hp=20, defense=0, power=4)
    orc.fighter.owner = orc
    orc.equipment = Equipment()
    orc.equipment.owner = orc
    
    player = Mock()
    player.name = "player"
    player.fighter = Fighter(hp=100, defense=1, power=3)
    player.fighter.owner = player
    player.equipment = Equipment()
    player.equipment.owner = player
    
    print("📊 Scenario 1: Basic attack (no equipment)")
    print(f"   Orc (power {orc.fighter.power}) attacks Player (defense {player.fighter.defense})")
    results = orc.fighter.attack(player)
    for result in results:
        if 'message' in result:
            print(f"   💬 {result['message'].text}")
    print()
    
    # Add weapon to orc
    sword = Mock()
    sword.equippable = Equippable(
        slot=EquipmentSlots.MAIN_HAND,
        power_bonus=2,
        damage_min=2,
        damage_max=5
    )
    orc.equipment.main_hand = sword
    
    print("📊 Scenario 2: Attack with weapon")
    print(f"   Orc with sword (2-5 dmg) attacks Player")
    results = orc.fighter.attack(player)
    for result in results:
        if 'message' in result:
            print(f"   💬 {result['message'].text}")
    print()
    
    # Add armor to player
    shield = Mock()
    shield.equippable = Equippable(
        slot=EquipmentSlots.OFF_HAND,
        defense_bonus=1,
        defense_min=1,
        defense_max=3
    )
    player.equipment.off_hand = shield
    
    print("📊 Scenario 3: Attack with weapon vs armor")
    print(f"   Orc with sword (2-5 dmg) attacks Player with shield (1-3 def)")
    results = orc.fighter.attack(player)
    for result in results:
        if 'message' in result:
            print(f"   💬 {result['message'].text}")
    print()
    
    # Create heavily armored target
    tank = Mock()
    tank.name = "armored_knight"
    tank.fighter = Fighter(hp=200, defense=3, power=1)
    tank.fighter.owner = tank
    tank.equipment = Equipment()
    tank.equipment.owner = tank
    
    heavy_armor = Mock()
    heavy_armor.equippable = Equippable(
        slot=EquipmentSlots.OFF_HAND,
        defense_bonus=2,
        defense_min=4,
        defense_max=6
    )
    tank.equipment.off_hand = heavy_armor
    
    print("📊 Scenario 4: Attack completely blocked by armor")
    print(f"   Orc with sword attacks heavily armored knight")
    results = orc.fighter.attack(tank)
    for result in results:
        if 'message' in result:
            print(f"   💬 {result['message'].text}")
    print()
    
    print("🔍 Detailed combat breakdowns have been logged to: combat_debug.log")
    print("📖 Check the log file to see the complete calculation details!")
    print()
    
    # Show a sample of what's in the log
    try:
        with open('combat_debug.log', 'r') as f:
            log_content = f.read()
        
        print("📋 Sample log entries:")
        print("-" * 30)
        lines = log_content.strip().split('\n')
        for line in lines[-4:]:  # Show last 4 entries
            if 'COMBAT:' in line:
                # Extract just the combat message part
                combat_msg = line.split('COMBAT: ', 1)[1]
                print(f"   🔍 {combat_msg}")
    except FileNotFoundError:
        print("❌ Log file not found - make sure testing mode created it")
    
    print()
    print("🎯 How to use this in your game:")
    print("   1. Run game with: python engine.py --testing")
    print("   2. Engage in combat")
    print("   3. Check combat_debug.log for detailed calculations")
    print("   4. Use this to debug combat balance and mechanics")
    
    # Clean up
    set_testing_mode(False)


if __name__ == "__main__":
    demo_combat_logging()
