"""Tests for action replay system.

Tests that:
1. ActionLogger correctly records actions
2. ActionLogger saves to JSONL format
3. ReplayDriver loads and provides actions
4. Replay flow preserves action order
"""

import json
import pytest
import tempfile
from pathlib import Path

from engine.replay import (
    ActionRecord,
    ReplayHeader,
    ActionLogger,
    ReplayDriver,
    get_action_logger,
    reset_action_logger,
)


class TestActionRecord:
    """Tests for ActionRecord dataclass."""
    
    def test_to_dict(self):
        """to_dict should serialize all fields."""
        record = ActionRecord(
            tick=5,
            action={"move": (1, 0)},
            game_state="PLAYERS_TURN",
            timestamp="2024-01-01T12:00:00",
        )
        d = record.to_dict()
        
        assert d["tick"] == 5
        assert d["action"] == {"move": (1, 0)}
        assert d["game_state"] == "PLAYERS_TURN"
        assert d["timestamp"] == "2024-01-01T12:00:00"
    
    def test_from_dict(self):
        """from_dict should deserialize correctly."""
        data = {
            "tick": 10,
            "action": {"pickup": True},
            "game_state": "PLAYERS_TURN",
            "timestamp": "2024-01-01T12:00:00",
        }
        record = ActionRecord.from_dict(data)
        
        assert record.tick == 10
        assert record.action == {"pickup": True}
        assert record.game_state == "PLAYERS_TURN"
    
    def test_from_dict_missing_fields(self):
        """from_dict should handle missing optional fields."""
        data = {"tick": 1, "action": {}}
        record = ActionRecord.from_dict(data)
        
        assert record.tick == 1
        assert record.game_state is None


class TestReplayHeader:
    """Tests for ReplayHeader dataclass."""
    
    def test_to_dict_includes_type(self):
        """to_dict should include type='header' marker."""
        header = ReplayHeader(seed=12345)
        d = header.to_dict()
        
        assert d["type"] == "header"
        assert d["seed"] == 12345
    
    def test_from_dict(self):
        """from_dict should deserialize correctly."""
        data = {
            "type": "header",
            "seed": 99999,
            "persona": "aggressive",
            "start_floor": 3,
        }
        header = ReplayHeader.from_dict(data)
        
        assert header.seed == 99999
        assert header.persona == "aggressive"
        assert header.start_floor == 3


class TestActionLogger:
    """Tests for ActionLogger class."""
    
    def setup_method(self):
        """Reset global state before each test."""
        reset_action_logger()
    
    def test_not_enabled_by_default(self):
        """Logger should not record unless start() is called."""
        logger = ActionLogger()
        logger.log_action({"move": (1, 0)})
        
        assert logger.action_count == 0
    
    def test_start_enables_recording(self):
        """start() should enable recording."""
        logger = ActionLogger()
        logger.start(seed=42)
        
        assert logger.is_enabled
    
    def test_log_action_records_actions(self):
        """log_action should record actions when enabled."""
        logger = ActionLogger()
        logger.start(seed=42)
        
        logger.log_action({"move": (1, 0)})
        logger.log_action({"pickup": True})
        
        assert logger.action_count == 2
    
    def test_log_action_auto_increments_tick(self):
        """log_action should auto-increment tick if not provided."""
        logger = ActionLogger()
        logger.start(seed=42)
        
        logger.log_action({"move": (1, 0)})
        logger.log_action({"move": (0, 1)})
        
        actions = logger.get_actions()
        assert actions[0].tick == 0
        assert actions[1].tick == 1
    
    def test_log_action_respects_explicit_tick(self):
        """log_action should use explicit tick if provided."""
        logger = ActionLogger()
        logger.start(seed=42)
        
        logger.log_action({"move": (1, 0)}, tick=100)
        
        actions = logger.get_actions()
        assert actions[0].tick == 100
    
    def test_stop_disables_recording(self):
        """stop() should disable recording."""
        logger = ActionLogger()
        logger.start(seed=42)
        logger.log_action({"move": (1, 0)})
        logger.stop()
        logger.log_action({"pickup": True})  # Should be ignored
        
        assert logger.action_count == 1
    
    def test_save_creates_jsonl_file(self):
        """save() should create a valid JSONL file."""
        logger = ActionLogger()
        logger.start(seed=42, persona="cautious", start_floor=2)
        logger.log_action({"move": (1, 0)})
        logger.log_action({"pickup": True})
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.jsonl"
            logger.save(str(path))
            
            # File should exist
            assert path.exists()
            
            # Read and verify
            with open(path, 'r') as f:
                lines = f.readlines()
            
            # First line is header
            header = json.loads(lines[0])
            assert header["type"] == "header"
            assert header["seed"] == 42
            assert header["persona"] == "cautious"
            
            # Subsequent lines are actions
            action1 = json.loads(lines[1])
            assert action1["action"] == {"move": [1, 0]}  # JSON converts tuple to list
            
            action2 = json.loads(lines[2])
            assert action2["action"] == {"pickup": True}
    
    def test_save_creates_parent_directories(self):
        """save() should create parent directories if needed."""
        logger = ActionLogger()
        logger.start(seed=42)
        logger.log_action({"wait": True})
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "a" / "b" / "replay.jsonl"
            logger.save(str(path))
            
            assert path.exists()


class TestReplayDriver:
    """Tests for ReplayDriver class."""
    
    def _create_replay_file(self, tmpdir, actions, seed=42):
        """Helper to create a replay file for testing."""
        path = Path(tmpdir) / "replay.jsonl"
        
        with open(path, 'w') as f:
            # Write header
            header = {"type": "header", "seed": seed, "persona": "balanced", "start_floor": 1}
            f.write(json.dumps(header) + '\n')
            
            # Write actions
            for i, action in enumerate(actions):
                record = {"tick": i, "action": action}
                f.write(json.dumps(record) + '\n')
        
        return str(path)
    
    def test_load_reads_header(self):
        """ReplayDriver should load header from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self._create_replay_file(tmpdir, [], seed=12345)
            driver = ReplayDriver(path)
            
            assert driver.get_seed() == 12345
    
    def test_load_reads_actions(self):
        """ReplayDriver should load actions from file."""
        actions = [{"move": [1, 0]}, {"pickup": True}, {"wait": True}]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self._create_replay_file(tmpdir, actions)
            driver = ReplayDriver(path)
            
            assert driver.total_actions == 3
    
    def test_get_next_action_returns_in_order(self):
        """get_next_action should return actions in recorded order."""
        actions = [{"move": [1, 0]}, {"move": [0, 1]}, {"pickup": True}]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self._create_replay_file(tmpdir, actions)
            driver = ReplayDriver(path)
            
            assert driver.get_next_action() == {"move": [1, 0]}
            assert driver.get_next_action() == {"move": [0, 1]}
            assert driver.get_next_action() == {"pickup": True}
            assert driver.get_next_action() is None  # Replay complete
    
    def test_is_complete(self):
        """is_complete should track replay progress."""
        actions = [{"move": [1, 0]}]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self._create_replay_file(tmpdir, actions)
            driver = ReplayDriver(path)
            
            assert not driver.is_complete()
            driver.get_next_action()
            assert driver.is_complete()
    
    def test_actions_remaining(self):
        """actions_remaining should count remaining actions."""
        actions = [{"move": [1, 0]}, {"pickup": True}]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self._create_replay_file(tmpdir, actions)
            driver = ReplayDriver(path)
            
            assert driver.actions_remaining == 2
            driver.get_next_action()
            assert driver.actions_remaining == 1
    
    def test_reset_restarts_replay(self):
        """reset() should restart replay from the beginning."""
        actions = [{"move": [1, 0]}, {"pickup": True}]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self._create_replay_file(tmpdir, actions)
            driver = ReplayDriver(path)
            
            driver.get_next_action()
            driver.get_next_action()
            assert driver.is_complete()
            
            driver.reset()
            assert not driver.is_complete()
            assert driver.get_next_action() == {"move": [1, 0]}
    
    def test_file_not_found_raises(self):
        """ReplayDriver should raise if file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            ReplayDriver("/nonexistent/path/replay.jsonl")


class TestGlobalActionLogger:
    """Tests for global action logger singleton."""
    
    def setup_method(self):
        """Reset global state before each test."""
        reset_action_logger()
    
    def test_get_action_logger_returns_singleton(self):
        """get_action_logger should return the same instance."""
        logger1 = get_action_logger()
        logger2 = get_action_logger()
        
        assert logger1 is logger2
    
    def test_reset_clears_singleton(self):
        """reset_action_logger should clear the singleton."""
        logger1 = get_action_logger()
        reset_action_logger()
        logger2 = get_action_logger()
        
        assert logger1 is not logger2


class TestRoundTrip:
    """Integration tests for record-then-replay flow."""
    
    def test_roundtrip_preserves_actions(self):
        """Recording and replaying should preserve action sequence."""
        original_actions = [
            {"move": (1, 0)},
            {"move": (0, -1)},
            {"pickup": True},
            {"inventory_index": 0},
            {"wait": True},
        ]
        
        # Record
        logger = ActionLogger()
        logger.start(seed=99999, persona="greedy", start_floor=5)
        for action in original_actions:
            logger.log_action(action)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "roundtrip.jsonl"
            logger.save(str(path))
            
            # Replay
            driver = ReplayDriver(str(path))
            
            # Verify header
            assert driver.get_seed() == 99999
            assert driver.get_persona() == "greedy"
            assert driver.get_start_floor() == 5
            
            # Verify actions
            replayed = []
            while not driver.is_complete():
                action = driver.get_next_action()
                replayed.append(action)
            
            # Note: JSON converts tuples to lists
            expected = [
                {"move": [1, 0]},
                {"move": [0, -1]},
                {"pickup": True},
                {"inventory_index": 0},
                {"wait": True},
            ]
            assert replayed == expected

