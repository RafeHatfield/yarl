"""Tests for combat debug logging system.

This module tests that combat debug logging works correctly in testing mode
and provides useful debugging information for combat calculations.
"""

import pytest
import logging
import tempfile
import os
from unittest.mock import Mock, patch

from components.fighter import Fighter
from components.equipment import Equipment
from components.equippable import Equippable
from equipment_slots import EquipmentSlots
from config.testing_config import set_testing_mode, is_testing_mode


class TestCombatDebugLogging:
    """Test combat debug logging functionality."""

    def setup_method(self):
        """Set up test entities and enable testing mode."""
        # Enable testing mode
        set_testing_mode(True)
        
        # Create attacker with equipment
        self.attacker = Mock()
        self.attacker.name = "orc"
        self.attacker.fighter = Fighter(hp=20, defense=0, power=4)
        self.attacker.fighter.owner = self.attacker
        self.attacker.equipment = Equipment()
        self.attacker.equipment.owner = self.attacker
        
        # Create target with equipment
        self.target = Mock()
        self.target.name = "player"
        self.target.fighter = Fighter(hp=30, defense=1, power=2)
        self.target.fighter.owner = self.target
        self.target.equipment = Equipment()
        self.target.equipment.owner = self.target

    def teardown_method(self):
        """Clean up after tests."""
        # Disable testing mode
        set_testing_mode(False)

    def test_combat_logging_enabled_in_testing_mode(self):
        """Test that combat logging is enabled when testing mode is active."""
        # Testing mode should be enabled
        assert is_testing_mode() is True
        
        # Combat logger should be configured
        combat_logger = logging.getLogger('combat_debug')
        assert combat_logger.level == logging.DEBUG
        assert len(combat_logger.handlers) > 0

    def test_combat_logging_disabled_in_normal_mode(self):
        """Test that combat logging is disabled in normal mode."""
        # Disable testing mode
        set_testing_mode(False)
        
        assert is_testing_mode() is False
        
        # Combat logger should be disabled
        combat_logger = logging.getLogger('combat_debug')
        assert combat_logger.level == logging.CRITICAL

    def test_combat_debug_logging_with_basic_attack(self):
        """Test that basic attacks are logged with correct details."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            log_file = f.name

        try:
            # Set up a custom handler to capture logs
            combat_logger = logging.getLogger('combat_debug')
            # Remove existing handlers
            for handler in combat_logger.handlers[:]:
                combat_logger.removeHandler(handler)
                handler.close()
            
            # Add our test handler
            handler = logging.FileHandler(log_file, mode='w')
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            combat_logger.addHandler(handler)
            combat_logger.setLevel(logging.DEBUG)

            # Perform attack
            results = self.attacker.fighter.attack(self.target)

            # Close handler to flush logs
            handler.close()
            combat_logger.removeHandler(handler)

            # Read log file
            with open(log_file, 'r') as f:
                log_contents = f.read()

            # Verify log contains expected information
            assert "Orc" in log_contents
            assert "player" in log_contents
            assert "attacks for" in log_contents
            assert "blocks" in log_contents
            assert "total damage" in log_contents

        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)

    def test_combat_debug_logging_with_weapon_and_armor(self):
        """Test that combat logging includes weapon and armor range information."""
        # Add weapon to attacker
        weapon = Mock()
        weapon.equippable = Equippable(
            slot=EquipmentSlots.MAIN_HAND,
            power_bonus=2,
            damage_min=2,
            damage_max=4
        )
        self.attacker.equipment.main_hand = weapon

        # Add armor to target
        armor = Mock()
        armor.equippable = Equippable(
            slot=EquipmentSlots.OFF_HAND,
            defense_bonus=1,
            defense_min=1,
            defense_max=3
        )
        self.target.equipment.off_hand = armor

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            log_file = f.name

        try:
            # Set up logging
            combat_logger = logging.getLogger('combat_debug')
            for handler in combat_logger.handlers[:]:
                combat_logger.removeHandler(handler)
                handler.close()
            
            handler = logging.FileHandler(log_file, mode='w')
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            combat_logger.addHandler(handler)

            # Mock weapon and armor rolls for predictable testing
            with patch.object(weapon.equippable, 'roll_damage', return_value=3), \
                 patch.object(armor.equippable, 'roll_defense', return_value=2):
                
                results = self.attacker.fighter.attack(self.target)

            handler.close()
            combat_logger.removeHandler(handler)

            # Read log file
            with open(log_file, 'r') as f:
                log_contents = f.read()

            # Verify weapon and armor ranges are logged
            assert "(2-4 dmg)" in log_contents  # Weapon damage range
            assert "(1-3 def)" in log_contents  # Armor defense range
            assert "base + 3 weapon" in log_contents  # Rolled weapon damage
            assert "static + 2 armor" in log_contents  # Rolled armor defense

        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)

    def test_combat_debug_logging_with_blocked_attack(self):
        """Test that completely blocked attacks are logged correctly."""
        # Create strong armor that blocks the attack
        armor = Mock()
        armor.equippable = Equippable(
            slot=EquipmentSlots.OFF_HAND,
            defense_bonus=2,
            defense_min=3,
            defense_max=5
        )
        self.target.equipment.off_hand = armor

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            log_file = f.name

        try:
            # Set up logging
            combat_logger = logging.getLogger('combat_debug')
            for handler in combat_logger.handlers[:]:
                combat_logger.removeHandler(handler)
                handler.close()
            
            handler = logging.FileHandler(log_file, mode='w')
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            combat_logger.addHandler(handler)

            # Mock armor to provide high defense
            with patch.object(armor.equippable, 'roll_defense', return_value=4):
                results = self.attacker.fighter.attack(self.target)

            handler.close()
            combat_logger.removeHandler(handler)

            # Read log file
            with open(log_file, 'r') as f:
                log_contents = f.read()

            # Verify blocked attack is logged with 0 damage
            assert "= 0 total damage" in log_contents
            assert "static + 4 armor" in log_contents

        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)

    def test_no_combat_logging_in_normal_mode(self):
        """Test that no combat logging occurs when testing mode is disabled."""
        # Disable testing mode
        set_testing_mode(False)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            log_file = f.name

        try:
            # Set up logging (this shouldn't capture anything)
            combat_logger = logging.getLogger('combat_debug')
            
            # Even if we try to set up a handler, nothing should be logged
            # because testing mode is disabled
            handler = logging.FileHandler(log_file, mode='w')
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            combat_logger.addHandler(handler)

            # Perform attack
            results = self.attacker.fighter.attack(self.target)

            handler.close()
            combat_logger.removeHandler(handler)

            # Read log file - should be empty or minimal
            with open(log_file, 'r') as f:
                log_contents = f.read()

            # No combat debug info should be logged
            assert "attacks for" not in log_contents

        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)


class TestCombatLoggerConfiguration:
    """Test combat logger configuration and setup."""

    def test_combat_logger_file_creation(self):
        """Test that combat logger creates the correct log file."""
        # Enable testing mode
        set_testing_mode(True)
        
        try:
            # Check that combat_debug.log should be created in testing mode
            combat_logger = logging.getLogger('combat_debug')
            assert combat_logger.level == logging.DEBUG
            
            # Check that handlers are configured
            assert len(combat_logger.handlers) > 0
            
            # Verify the handler is a FileHandler
            file_handlers = [h for h in combat_logger.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) > 0

        finally:
            set_testing_mode(False)

    def test_combat_logger_cleanup(self):
        """Test that combat logger is properly cleaned up when testing mode is disabled."""
        # Enable then disable testing mode
        set_testing_mode(True)
        combat_logger = logging.getLogger('combat_debug')
        initial_handler_count = len(combat_logger.handlers)
        
        set_testing_mode(False)
        
        # Logger should be disabled and handlers removed
        assert combat_logger.level == logging.CRITICAL
        assert len(combat_logger.handlers) == 0

    def test_multiple_testing_mode_toggles(self):
        """Test that toggling testing mode multiple times works correctly."""
        # Start disabled
        set_testing_mode(False)
        combat_logger = logging.getLogger('combat_debug')
        assert combat_logger.level == logging.CRITICAL
        
        # Enable
        set_testing_mode(True)
        assert combat_logger.level == logging.DEBUG
        assert len(combat_logger.handlers) > 0
        
        # Disable
        set_testing_mode(False)
        assert combat_logger.level == logging.CRITICAL
        assert len(combat_logger.handlers) == 0
        
        # Enable again
        set_testing_mode(True)
        assert combat_logger.level == logging.DEBUG
        assert len(combat_logger.handlers) > 0
        
        # Clean up
        set_testing_mode(False)
