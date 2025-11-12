"""Unit tests for the performance configuration module.

Tests the config layer for frame rate limiting, logging behavior, and debug overlay.
Covers defaults, environment variable overrides, constants overrides, and type validation.
"""

import os
import pytest
# from config.performance import get_performance_config, _parse_bool
from performance.config import get_performance_config, _parse_bool


class TestParseBool:
    """Tests for the internal _parse_bool helper."""

    def test_parse_bool_true_values(self):
        """Test parsing of truthy string values."""
        assert _parse_bool(True) is True
        assert _parse_bool("1") is True
        assert _parse_bool("true") is True
        assert _parse_bool("TRUE") is True
        assert _parse_bool("True") is True
        assert _parse_bool("yes") is True
        assert _parse_bool("YES") is True
        assert _parse_bool("on") is True
        assert _parse_bool("ON") is True

    def test_parse_bool_false_values(self):
        """Test parsing of falsy string values."""
        assert _parse_bool(False) is False
        assert _parse_bool("0") is False
        assert _parse_bool("false") is False
        assert _parse_bool("FALSE") is False
        assert _parse_bool("False") is False
        assert _parse_bool("no") is False
        assert _parse_bool("NO") is False
        assert _parse_bool("off") is False
        assert _parse_bool("OFF") is False

    def test_parse_bool_invalid(self):
        """Test that invalid values return None."""
        assert _parse_bool("maybe") is None
        assert _parse_bool("") is None
        assert _parse_bool(42) is None
        assert _parse_bool(None) is None
        assert _parse_bool([]) is None

    def test_parse_bool_whitespace_handling(self):
        """Test that whitespace is properly stripped."""
        assert _parse_bool("  true  ") is True
        assert _parse_bool("  false  ") is False
        assert _parse_bool("\ttrue\n") is True


class TestDefaultsOnly:
    """Tests with no environment or config overrides."""

    def test_defaults_only(self, monkeypatch):
        """Verify defaults are returned with no overrides."""
        # Ensure all env vars are cleared
        monkeypatch.delenv("YARL_FRAME_RATE_LIMIT", raising=False)
        monkeypatch.delenv("YARL_LOGGING_ENABLED", raising=False)
        monkeypatch.delenv("YARL_DEBUG_OVERLAY", raising=False)

        cfg = get_performance_config(None)

        assert cfg["frame_rate_limit"] == 60
        assert cfg["logging_enabled"] is True
        assert cfg["debug_overlay"] is False

    def test_defaults_with_empty_constants(self, monkeypatch):
        """Verify defaults work when constants is an empty dict."""
        monkeypatch.delenv("YARL_FRAME_RATE_LIMIT", raising=False)
        monkeypatch.delenv("YARL_LOGGING_ENABLED", raising=False)
        monkeypatch.delenv("YARL_DEBUG_OVERLAY", raising=False)

        cfg = get_performance_config({})

        assert cfg["frame_rate_limit"] == 60
        assert cfg["logging_enabled"] is True
        assert cfg["debug_overlay"] is False


class TestConstantsOverride:
    """Tests for constants dict override layer."""

    def test_constants_frame_rate_override(self, monkeypatch):
        """Test frame_rate_limit override via constants."""
        monkeypatch.delenv("YARL_FRAME_RATE_LIMIT", raising=False)
        monkeypatch.delenv("YARL_LOGGING_ENABLED", raising=False)
        monkeypatch.delenv("YARL_DEBUG_OVERLAY", raising=False)

        constants = {"performance": {"frame_rate_limit": 75}}
        cfg = get_performance_config(constants)

        assert cfg["frame_rate_limit"] == 75
        assert cfg["logging_enabled"] is True
        assert cfg["debug_overlay"] is False

    def test_constants_logging_override(self, monkeypatch):
        """Test logging_enabled override via constants."""
        monkeypatch.delenv("YARL_FRAME_RATE_LIMIT", raising=False)
        monkeypatch.delenv("YARL_LOGGING_ENABLED", raising=False)
        monkeypatch.delenv("YARL_DEBUG_OVERLAY", raising=False)

        constants = {"performance": {"logging_enabled": False}}
        cfg = get_performance_config(constants)

        assert cfg["frame_rate_limit"] == 60
        assert cfg["logging_enabled"] is False
        assert cfg["debug_overlay"] is False

    def test_constants_debug_overlay_override(self, monkeypatch):
        """Test debug_overlay override via constants."""
        monkeypatch.delenv("YARL_FRAME_RATE_LIMIT", raising=False)
        monkeypatch.delenv("YARL_LOGGING_ENABLED", raising=False)
        monkeypatch.delenv("YARL_DEBUG_OVERLAY", raising=False)

        constants = {"performance": {"debug_overlay": True}}
        cfg = get_performance_config(constants)

        assert cfg["frame_rate_limit"] == 60
        assert cfg["logging_enabled"] is True
        assert cfg["debug_overlay"] is True

    def test_constants_all_overrides(self, monkeypatch):
        """Test all three values overridden via constants."""
        monkeypatch.delenv("YARL_FRAME_RATE_LIMIT", raising=False)
        monkeypatch.delenv("YARL_LOGGING_ENABLED", raising=False)
        monkeypatch.delenv("YARL_DEBUG_OVERLAY", raising=False)

        constants = {
            "performance": {
                "frame_rate_limit": 90,
                "logging_enabled": False,
                "debug_overlay": True,
            }
        }
        cfg = get_performance_config(constants)

        assert cfg["frame_rate_limit"] == 90
        assert cfg["logging_enabled"] is False
        assert cfg["debug_overlay"] is True


class TestEnvironmentOverride:
    """Tests for environment variable override layer."""

    def test_env_frame_rate_override(self, monkeypatch):
        """Test YARL_FRAME_RATE_LIMIT env var."""
        monkeypatch.setenv("YARL_FRAME_RATE_LIMIT", "120")
        monkeypatch.delenv("YARL_LOGGING_ENABLED", raising=False)
        monkeypatch.delenv("YARL_DEBUG_OVERLAY", raising=False)

        cfg = get_performance_config(None)

        assert cfg["frame_rate_limit"] == 120
        assert cfg["logging_enabled"] is True
        assert cfg["debug_overlay"] is False

    def test_env_logging_enabled_override(self, monkeypatch):
        """Test YARL_LOGGING_ENABLED env var with true."""
        monkeypatch.delenv("YARL_FRAME_RATE_LIMIT", raising=False)
        monkeypatch.setenv("YARL_LOGGING_ENABLED", "true")
        monkeypatch.delenv("YARL_DEBUG_OVERLAY", raising=False)

        cfg = get_performance_config(None)

        assert cfg["frame_rate_limit"] == 60
        assert cfg["logging_enabled"] is True
        assert cfg["debug_overlay"] is False

    def test_env_logging_disabled_override(self, monkeypatch):
        """Test YARL_LOGGING_ENABLED env var with false."""
        monkeypatch.delenv("YARL_FRAME_RATE_LIMIT", raising=False)
        monkeypatch.setenv("YARL_LOGGING_ENABLED", "0")
        monkeypatch.delenv("YARL_DEBUG_OVERLAY", raising=False)

        cfg = get_performance_config(None)

        assert cfg["frame_rate_limit"] == 60
        assert cfg["logging_enabled"] is False
        assert cfg["debug_overlay"] is False

    def test_env_debug_overlay_override(self, monkeypatch):
        """Test YARL_DEBUG_OVERLAY env var."""
        monkeypatch.delenv("YARL_FRAME_RATE_LIMIT", raising=False)
        monkeypatch.delenv("YARL_LOGGING_ENABLED", raising=False)
        monkeypatch.setenv("YARL_DEBUG_OVERLAY", "yes")

        cfg = get_performance_config(None)

        assert cfg["frame_rate_limit"] == 60
        assert cfg["logging_enabled"] is True
        assert cfg["debug_overlay"] is True

    def test_env_all_overrides(self, monkeypatch):
        """Test all three env vars set."""
        monkeypatch.setenv("YARL_FRAME_RATE_LIMIT", "45")
        monkeypatch.setenv("YARL_LOGGING_ENABLED", "false")
        monkeypatch.setenv("YARL_DEBUG_OVERLAY", "1")

        cfg = get_performance_config(None)

        assert cfg["frame_rate_limit"] == 45
        assert cfg["logging_enabled"] is False
        assert cfg["debug_overlay"] is True


class TestPrecedence:
    """Tests for the precedence order: constants > env vars > defaults."""

    def test_constants_overrides_env(self, monkeypatch):
        """Test that constants overrides environment variables."""
        monkeypatch.setenv("YARL_FRAME_RATE_LIMIT", "30")
        monkeypatch.setenv("YARL_LOGGING_ENABLED", "true")
        monkeypatch.setenv("YARL_DEBUG_OVERLAY", "0")

        constants = {
            "performance": {
                "frame_rate_limit": 90,
                # Leave logging_enabled to env
                # Leave debug_overlay to env
            }
        }
        cfg = get_performance_config(constants)

        # frame_rate_limit from constants wins over env
        assert cfg["frame_rate_limit"] == 90
        # logging_enabled from env
        assert cfg["logging_enabled"] is True
        # debug_overlay from env
        assert cfg["debug_overlay"] is False

    def test_constants_all_override_env(self, monkeypatch):
        """Test constants win for all keys."""
        monkeypatch.setenv("YARL_FRAME_RATE_LIMIT", "30")
        monkeypatch.setenv("YARL_LOGGING_ENABLED", "true")
        monkeypatch.setenv("YARL_DEBUG_OVERLAY", "0")

        constants = {
            "performance": {
                "frame_rate_limit": 100,
                "logging_enabled": False,
                "debug_overlay": True,
            }
        }
        cfg = get_performance_config(constants)

        assert cfg["frame_rate_limit"] == 100
        assert cfg["logging_enabled"] is False
        assert cfg["debug_overlay"] is True

    def test_env_overrides_defaults(self, monkeypatch):
        """Test env vars override defaults."""
        monkeypatch.setenv("YARL_FRAME_RATE_LIMIT", "50")
        monkeypatch.setenv("YARL_LOGGING_ENABLED", "0")
        monkeypatch.delenv("YARL_DEBUG_OVERLAY", raising=False)

        cfg = get_performance_config(None)

        assert cfg["frame_rate_limit"] == 50
        assert cfg["logging_enabled"] is False
        assert cfg["debug_overlay"] is False  # Not in env, so default


class TestTypeValidation:
    """Tests for graceful type validation and fallback."""

    def test_invalid_frame_rate_string(self, monkeypatch, caplog):
        """Test invalid frame_rate_limit falls back to default."""
        monkeypatch.delenv("YARL_FRAME_RATE_LIMIT", raising=False)
        monkeypatch.delenv("YARL_LOGGING_ENABLED", raising=False)
        monkeypatch.delenv("YARL_DEBUG_OVERLAY", raising=False)

        constants = {"performance": {"frame_rate_limit": "not_a_number"}}
        cfg = get_performance_config(constants)

        assert cfg["frame_rate_limit"] == 60  # Falls back to default
        assert "invalid" in caplog.text.lower()

    def test_invalid_frame_rate_float(self, monkeypatch, caplog):
        """Test invalid frame_rate_limit with invalid value."""
        monkeypatch.delenv("YARL_FRAME_RATE_LIMIT", raising=False)
        monkeypatch.delenv("YARL_LOGGING_ENABLED", raising=False)
        monkeypatch.delenv("YARL_DEBUG_OVERLAY", raising=False)

        constants = {"performance": {"frame_rate_limit": None}}
        cfg = get_performance_config(constants)

        assert cfg["frame_rate_limit"] == 60  # Falls back to default

    def test_invalid_logging_enabled_value(self, monkeypatch, caplog):
        """Test invalid logging_enabled falls back to default."""
        monkeypatch.delenv("YARL_FRAME_RATE_LIMIT", raising=False)
        monkeypatch.delenv("YARL_LOGGING_ENABLED", raising=False)
        monkeypatch.delenv("YARL_DEBUG_OVERLAY", raising=False)

        constants = {"performance": {"logging_enabled": "maybe"}}
        cfg = get_performance_config(constants)

        assert cfg["logging_enabled"] is True  # Falls back to default
        assert "invalid" in caplog.text.lower()

    def test_invalid_debug_overlay_value(self, monkeypatch, caplog):
        """Test invalid debug_overlay falls back to default."""
        monkeypatch.delenv("YARL_FRAME_RATE_LIMIT", raising=False)
        monkeypatch.delenv("YARL_LOGGING_ENABLED", raising=False)
        monkeypatch.delenv("YARL_DEBUG_OVERLAY", raising=False)

        constants = {"performance": {"debug_overlay": []}}
        cfg = get_performance_config(constants)

        assert cfg["debug_overlay"] is False  # Falls back to default

    def test_performance_not_dict(self, monkeypatch, caplog):
        """Test that non-dict performance config is handled gracefully."""
        monkeypatch.delenv("YARL_FRAME_RATE_LIMIT", raising=False)
        monkeypatch.delenv("YARL_LOGGING_ENABLED", raising=False)
        monkeypatch.delenv("YARL_DEBUG_OVERLAY", raising=False)

        constants = {"performance": "invalid"}
        cfg = get_performance_config(constants)

        # Should use defaults
        assert cfg["frame_rate_limit"] == 60
        assert cfg["logging_enabled"] is True
        assert cfg["debug_overlay"] is False
        assert "not a dict" in caplog.text.lower()


class TestValidIntegerConversion:
    """Tests for valid integer conversions."""

    def test_frame_rate_as_int(self, monkeypatch):
        """Test frame_rate_limit accepts integer directly."""
        monkeypatch.delenv("YARL_FRAME_RATE_LIMIT", raising=False)
        monkeypatch.delenv("YARL_LOGGING_ENABLED", raising=False)
        monkeypatch.delenv("YARL_DEBUG_OVERLAY", raising=False)

        constants = {"performance": {"frame_rate_limit": 100}}
        cfg = get_performance_config(constants)

        assert cfg["frame_rate_limit"] == 100

    def test_frame_rate_as_string(self, monkeypatch):
        """Test frame_rate_limit accepts string representation of int."""
        monkeypatch.delenv("YARL_FRAME_RATE_LIMIT", raising=False)
        monkeypatch.delenv("YARL_LOGGING_ENABLED", raising=False)
        monkeypatch.delenv("YARL_DEBUG_OVERLAY", raising=False)

        constants = {"performance": {"frame_rate_limit": "100"}}
        cfg = get_performance_config(constants)

        assert cfg["frame_rate_limit"] == 100

    def test_env_frame_rate_as_string(self, monkeypatch):
        """Test YARL_FRAME_RATE_LIMIT env var as string."""
        monkeypatch.setenv("YARL_FRAME_RATE_LIMIT", "88")
        monkeypatch.delenv("YARL_LOGGING_ENABLED", raising=False)
        monkeypatch.delenv("YARL_DEBUG_OVERLAY", raising=False)

        cfg = get_performance_config(None)

        assert cfg["frame_rate_limit"] == 88


class TestCompleteScenarios:
    """Integration tests for realistic scenarios."""

    def test_full_yaml_config(self, monkeypatch):
        """Test a realistic YAML-loaded config scenario."""
        monkeypatch.delenv("YARL_FRAME_RATE_LIMIT", raising=False)
        monkeypatch.delenv("YARL_LOGGING_ENABLED", raising=False)
        monkeypatch.delenv("YARL_DEBUG_OVERLAY", raising=False)

        # Simulates YAML load result
        constants = {
            "performance": {
                "frame_rate_limit": 75,
                "logging_enabled": True,
                "debug_overlay": False,
            },
            "screen_width": 120,
            "screen_height": 30,
        }
        cfg = get_performance_config(constants)

        assert cfg["frame_rate_limit"] == 75
        assert cfg["logging_enabled"] is True
        assert cfg["debug_overlay"] is False
        # Verify other keys in constants don't interfere
        assert "screen_width" not in cfg

    def test_partial_yaml_override(self, monkeypatch):
        """Test YAML override with only some keys specified."""
        monkeypatch.delenv("YARL_FRAME_RATE_LIMIT", raising=False)
        monkeypatch.setenv("YARL_LOGGING_ENABLED", "false")
        monkeypatch.delenv("YARL_DEBUG_OVERLAY", raising=False)

        constants = {"performance": {"frame_rate_limit": 50}}  # Only one key
        cfg = get_performance_config(constants)

        assert cfg["frame_rate_limit"] == 50  # From constants
        assert cfg["logging_enabled"] is False  # From env
        assert cfg["debug_overlay"] is False  # Default

    def test_returns_dict_copy(self, monkeypatch):
        """Test that returned config is independent copy."""
        monkeypatch.delenv("YARL_FRAME_RATE_LIMIT", raising=False)
        monkeypatch.delenv("YARL_LOGGING_ENABLED", raising=False)
        monkeypatch.delenv("YARL_DEBUG_OVERLAY", raising=False)

        cfg1 = get_performance_config(None)
        cfg2 = get_performance_config(None)

        # Modify cfg1
        cfg1["frame_rate_limit"] = 999

        # cfg2 should not be affected
        assert cfg2["frame_rate_limit"] == 60

    def test_all_keys_always_present(self, monkeypatch):
        """Verify all required keys are always in returned dict."""
        monkeypatch.delenv("YARL_FRAME_RATE_LIMIT", raising=False)
        monkeypatch.delenv("YARL_LOGGING_ENABLED", raising=False)
        monkeypatch.delenv("YARL_DEBUG_OVERLAY", raising=False)

        cfg = get_performance_config({})

        assert "frame_rate_limit" in cfg
        assert "logging_enabled" in cfg
        assert "debug_overlay" in cfg
        assert len(cfg) == 3  # Only these three keys

