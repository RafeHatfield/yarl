"""State persistence system for saving and loading state machine data.

This module provides functionality to save and restore state machine
configurations, state data, and transition history.
"""

from typing import Any, Dict, List, Optional, Union, Type
from dataclasses import dataclass, field, asdict
from abc import ABC, abstractmethod
import json
import pickle
import time
import logging
from pathlib import Path

from .core import State, StateContext, StateMachine
from .events import StateEvent


logger = logging.getLogger(__name__)


class PersistenceError(Exception):
    """Exception raised by persistence operations."""
    
    def __init__(self, message: str, operation: str = None, 
                 file_path: str = None, cause: Exception = None):
        """Initialize persistence error.
        
        Args:
            message (str): Error message
            operation (str, optional): Operation that failed
            file_path (str, optional): File path involved
            cause (Exception, optional): Underlying exception
        """
        super().__init__(message)
        self.operation = operation
        self.file_path = file_path
        self.cause = cause


@dataclass
class StateSnapshot:
    """Snapshot of state machine data at a point in time."""
    
    # Metadata
    timestamp: float = field(default_factory=time.time)
    version: str = "1.0"
    machine_id: str = ""
    
    # State machine data
    current_state_id: Optional[str] = None
    previous_state_id: Optional[str] = None
    context_data: Dict[str, Any] = field(default_factory=dict)
    
    # State history
    state_history: List[str] = field(default_factory=list)
    
    # Performance data
    stats: Dict[str, Any] = field(default_factory=dict)
    
    # Custom data
    custom_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary.

        Returns:
            Dict[str, Any]: Snapshot data as dictionary
        """
        return {
            "timestamp": self.timestamp,
            "version": self.version,
            "machine_id": self.machine_id,
            "current_state_id": self.current_state_id,
            "previous_state_id": self.previous_state_id,
            "context_data": dict(self.context_data) if self.context_data is not None else {},
            "state_history": list(self.state_history) if self.state_history is not None else [],
            "stats": dict(self.stats) if self.stats is not None else {},
            "custom_data": dict(self.custom_data) if self.custom_data is not None else {},
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateSnapshot':
        """Create snapshot from dictionary.
        
        Args:
            data (Dict[str, Any]): Snapshot data dictionary
            
        Returns:
            StateSnapshot: Created snapshot
        """
        return cls(**data)
    
    def get_age(self) -> float:
        """Get age of snapshot in seconds.
        
        Returns:
            float: Age in seconds
        """
        return time.time() - self.timestamp
    
    def is_valid(self) -> bool:
        """Check if snapshot is valid.
        
        Returns:
            bool: True if snapshot is valid
        """
        return (
            self.version and
            self.machine_id and
            isinstance(self.context_data, dict) and
            isinstance(self.state_history, list)
        )


class PersistenceBackend(ABC):
    """Abstract base class for persistence backends."""
    
    @abstractmethod
    def save(self, data: Dict[str, Any], path: str) -> None:
        """Save data to storage.
        
        Args:
            data (Dict[str, Any]): Data to save
            path (str): Storage path
        """
        pass
    
    @abstractmethod
    def load(self, path: str) -> Dict[str, Any]:
        """Load data from storage.
        
        Args:
            path (str): Storage path
            
        Returns:
            Dict[str, Any]: Loaded data
        """
        pass
    
    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if data exists at path.
        
        Args:
            path (str): Storage path
            
        Returns:
            bool: True if data exists
        """
        pass
    
    @abstractmethod
    def delete(self, path: str) -> bool:
        """Delete data at path.
        
        Args:
            path (str): Storage path
            
        Returns:
            bool: True if data was deleted
        """
        pass


class JsonPersistenceBackend(PersistenceBackend):
    """JSON-based persistence backend."""
    
    def __init__(self, base_path: str = "saves"):
        """Initialize JSON persistence backend.
        
        Args:
            base_path (str): Base directory for save files
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def save(self, data: Dict[str, Any], path: str) -> None:
        """Save data to JSON file.
        
        Args:
            data (Dict[str, Any]): Data to save
            path (str): File path relative to base path
        """
        full_path = self.base_path / f"{path}.json"
        
        try:
            # Ensure directory exists
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            serializer = self._json_serializer if callable(self._json_serializer) else None

            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=serializer)
            
            logger.debug(f"Saved data to {full_path}")
            
        except Exception as e:
            raise PersistenceError(
                f"Failed to save JSON data: {e}",
                operation="save",
                file_path=str(full_path),
                cause=e
            )
    
    def load(self, path: str) -> Dict[str, Any]:
        """Load data from JSON file.
        
        Args:
            path (str): File path relative to base path
            
        Returns:
            Dict[str, Any]: Loaded data
        """
        full_path = self.base_path / f"{path}.json"
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.debug(f"Loaded data from {full_path}")
            return data
            
        except FileNotFoundError:
            raise PersistenceError(
                f"Save file not found: {full_path}",
                operation="load",
                file_path=str(full_path)
            )
        except Exception as e:
            raise PersistenceError(
                f"Failed to load JSON data: {e}",
                operation="load",
                file_path=str(full_path),
                cause=e
            )
    
    def exists(self, path: str) -> bool:
        """Check if JSON file exists.
        
        Args:
            path (str): File path relative to base path
            
        Returns:
            bool: True if file exists
        """
        full_path = self.base_path / f"{path}.json"
        return full_path.exists()
    
    def delete(self, path: str) -> bool:
        """Delete JSON file.
        
        Args:
            path (str): File path relative to base path
            
        Returns:
            bool: True if file was deleted
        """
        full_path = self.base_path / f"{path}.json"
        
        try:
            if full_path.exists():
                full_path.unlink()
                logger.debug(f"Deleted {full_path}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete {full_path}: {e}")
            return False
    
    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for complex objects.
        
        Args:
            obj (Any): Object to serialize
            
        Returns:
            Any: Serializable representation
        """
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)


class PicklePersistenceBackend(PersistenceBackend):
    """Pickle-based persistence backend for complex objects."""
    
    def __init__(self, base_path: str = "saves"):
        """Initialize pickle persistence backend.
        
        Args:
            base_path (str): Base directory for save files
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def save(self, data: Dict[str, Any], path: str) -> None:
        """Save data to pickle file.
        
        Args:
            data (Dict[str, Any]): Data to save
            path (str): File path relative to base path
        """
        full_path = self.base_path / f"{path}.pkl"
        
        try:
            # Ensure directory exists
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'wb') as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            logger.debug(f"Saved pickle data to {full_path}")
            
        except Exception as e:
            raise PersistenceError(
                f"Failed to save pickle data: {e}",
                operation="save",
                file_path=str(full_path),
                cause=e
            )
    
    def load(self, path: str) -> Dict[str, Any]:
        """Load data from pickle file.
        
        Args:
            path (str): File path relative to base path
            
        Returns:
            Dict[str, Any]: Loaded data
        """
        full_path = self.base_path / f"{path}.pkl"
        
        try:
            with open(full_path, 'rb') as f:
                data = pickle.load(f)
            
            logger.debug(f"Loaded pickle data from {full_path}")
            return data
            
        except FileNotFoundError:
            raise PersistenceError(
                f"Save file not found: {full_path}",
                operation="load",
                file_path=str(full_path)
            )
        except Exception as e:
            raise PersistenceError(
                f"Failed to load pickle data: {e}",
                operation="load",
                file_path=str(full_path),
                cause=e
            )
    
    def exists(self, path: str) -> bool:
        """Check if pickle file exists.
        
        Args:
            path (str): File path relative to base path
            
        Returns:
            bool: True if file exists
        """
        full_path = self.base_path / f"{path}.pkl"
        return full_path.exists()
    
    def delete(self, path: str) -> bool:
        """Delete pickle file.
        
        Args:
            path (str): File path relative to base path
            
        Returns:
            bool: True if file was deleted
        """
        full_path = self.base_path / f"{path}.pkl"
        
        try:
            if full_path.exists():
                full_path.unlink()
                logger.debug(f"Deleted {full_path}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete {full_path}: {e}")
            return False


class StatePersistence:
    """Main class for state machine persistence operations."""
    
    def __init__(self, backend: PersistenceBackend = None):
        """Initialize state persistence.
        
        Args:
            backend (PersistenceBackend, optional): Persistence backend to use
        """
        self.backend = backend or JsonPersistenceBackend()
        self.snapshots: Dict[str, StateSnapshot] = {}
        
        # Configuration
        self.auto_save_interval = 300.0  # 5 minutes
        self.max_snapshots = 10
        self.compress_old_snapshots = True
        
        # Statistics
        self.stats = {
            'saves_performed': 0,
            'loads_performed': 0,
            'snapshots_created': 0,
            'errors_occurred': 0,
        }
    
    def create_snapshot(self, state_machine: StateMachine, 
                       custom_data: Dict[str, Any] = None) -> StateSnapshot:
        """Create a snapshot of the current state machine.
        
        Args:
            state_machine (StateMachine): State machine to snapshot
            custom_data (Dict[str, Any], optional): Additional custom data
            
        Returns:
            StateSnapshot: Created snapshot
        """
        current_state = state_machine.get_current_state()
        previous_state = state_machine.get_previous_state()
        
        snapshot = StateSnapshot(
            machine_id=state_machine.machine_id,
            current_state_id=current_state.state_id if current_state else None,
            previous_state_id=previous_state.state_id if previous_state else None,
            context_data=state_machine.context.data.copy(),
            stats=state_machine.get_stats(),
            custom_data=custom_data or {}
        )
        
        # Store snapshot
        snapshot_id = f"{state_machine.machine_id}_{int(snapshot.timestamp)}"
        self.snapshots[snapshot_id] = snapshot
        
        # Cleanup old snapshots
        self._cleanup_snapshots()
        
        self.stats['snapshots_created'] += 1
        logger.debug(f"Created snapshot: {snapshot_id}")
        
        return snapshot
    
    def save_snapshot(self, snapshot: StateSnapshot, save_name: str) -> None:
        """Save a snapshot to persistent storage.
        
        Args:
            snapshot (StateSnapshot): Snapshot to save
            save_name (str): Name for the save file
        """
        try:
            data = snapshot.to_dict()
            self.backend.save(data, f"snapshots/{save_name}")
            
            self.stats['saves_performed'] += 1
            logger.info(f"Saved snapshot: {save_name}")
            
        except Exception as e:
            self.stats['errors_occurred'] += 1
            logger.error(f"Failed to save snapshot {save_name}: {e}")
            raise
    
    def load_snapshot(self, save_name: str) -> StateSnapshot:
        """Load a snapshot from persistent storage.
        
        Args:
            save_name (str): Name of the save file
            
        Returns:
            StateSnapshot: Loaded snapshot
        """
        try:
            data = self.backend.load(f"snapshots/{save_name}")
            snapshot = StateSnapshot.from_dict(data)
            
            if not snapshot.is_valid():
                raise PersistenceError(f"Invalid snapshot data: {save_name}")
            
            self.stats['loads_performed'] += 1
            logger.info(f"Loaded snapshot: {save_name}")
            
            return snapshot
            
        except Exception as e:
            self.stats['errors_occurred'] += 1
            logger.error(f"Failed to load snapshot {save_name}: {e}")
            raise
    
    def restore_state_machine(self, state_machine: StateMachine, 
                             snapshot: StateSnapshot) -> bool:
        """Restore a state machine from a snapshot.
        
        Args:
            state_machine (StateMachine): State machine to restore
            snapshot (StateSnapshot): Snapshot to restore from
            
        Returns:
            bool: True if restoration was successful
        """
        try:
            # Validate snapshot
            if not snapshot.is_valid():
                raise PersistenceError("Invalid snapshot for restoration")
            
            if snapshot.machine_id != state_machine.machine_id:
                logger.warning(f"Machine ID mismatch: {snapshot.machine_id} != {state_machine.machine_id}")
            
            # Stop state machine if running
            was_running = state_machine.is_running()
            if was_running:
                state_machine.stop()
            
            # Restore context data
            state_machine.context.data.clear()
            state_machine.context.data.update(snapshot.context_data)
            
            # Restore state if specified
            if snapshot.current_state_id:
                if was_running:
                    success = state_machine.start(snapshot.current_state_id)
                    if not success:
                        logger.error(f"Failed to start state machine with state: {snapshot.current_state_id}")
                        return False
            
            logger.info(f"Restored state machine from snapshot (age: {snapshot.get_age():.1f}s)")
            return True
            
        except Exception as e:
            self.stats['errors_occurred'] += 1
            logger.error(f"Failed to restore state machine: {e}")
            return False
    
    def save_state_machine(self, state_machine: StateMachine, save_name: str,
                          custom_data: Dict[str, Any] = None) -> bool:
        """Save a state machine to persistent storage.
        
        Args:
            state_machine (StateMachine): State machine to save
            save_name (str): Name for the save file
            custom_data (Dict[str, Any], optional): Additional custom data
            
        Returns:
            bool: True if save was successful
        """
        try:
            snapshot = self.create_snapshot(state_machine, custom_data)
            self.save_snapshot(snapshot, save_name)
            return True
            
        except Exception as e:
            logger.error(f"Failed to save state machine: {e}")
            return False
    
    def load_state_machine(self, state_machine: StateMachine, save_name: str) -> bool:
        """Load a state machine from persistent storage.
        
        Args:
            state_machine (StateMachine): State machine to load into
            save_name (str): Name of the save file
            
        Returns:
            bool: True if load was successful
        """
        try:
            snapshot = self.load_snapshot(save_name)
            return self.restore_state_machine(state_machine, snapshot)
            
        except Exception as e:
            logger.error(f"Failed to load state machine: {e}")
            return False
    
    def list_saves(self) -> List[str]:
        """List available save files.
        
        Returns:
            List[str]: List of save file names
        """
        try:
            # This would need to be implemented by the backend
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"Failed to list saves: {e}")
            return []
    
    def delete_save(self, save_name: str) -> bool:
        """Delete a save file.
        
        Args:
            save_name (str): Name of save file to delete
            
        Returns:
            bool: True if deletion was successful
        """
        try:
            return self.backend.delete(f"snapshots/{save_name}")
            
        except Exception as e:
            logger.error(f"Failed to delete save {save_name}: {e}")
            return False
    
    def _cleanup_snapshots(self) -> None:
        """Clean up old snapshots to maintain memory limits."""
        if len(self.snapshots) <= self.max_snapshots:
            return
        
        # Sort by timestamp and keep only the most recent
        sorted_snapshots = sorted(
            self.snapshots.items(),
            key=lambda x: x[1].timestamp,
            reverse=True
        )
        
        # Keep only the most recent snapshots
        to_keep = dict(sorted_snapshots[:self.max_snapshots])
        
        # Log cleanup
        removed_count = len(self.snapshots) - len(to_keep)
        if removed_count > 0:
            logger.debug(f"Cleaned up {removed_count} old snapshots")
        
        self.snapshots = to_keep
    
    def get_stats(self) -> Dict[str, Any]:
        """Get persistence statistics.
        
        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        stats = self.stats.copy()
        stats['snapshots_in_memory'] = len(self.snapshots)
        stats['backend_type'] = type(self.backend).__name__
        return stats
    
    def reset_stats(self) -> None:
        """Reset persistence statistics."""
        self.stats = {
            'saves_performed': 0,
            'loads_performed': 0,
            'snapshots_created': 0,
            'errors_occurred': 0,
        }


# Convenience functions

def create_json_persistence(base_path: str = "saves") -> StatePersistence:
    """Create a JSON-based state persistence system.
    
    Args:
        base_path (str): Base directory for save files
        
    Returns:
        StatePersistence: Configured persistence system
    """
    backend = JsonPersistenceBackend(base_path)
    return StatePersistence(backend)


def create_pickle_persistence(base_path: str = "saves") -> StatePersistence:
    """Create a pickle-based state persistence system.
    
    Args:
        base_path (str): Base directory for save files
        
    Returns:
        StatePersistence: Configured persistence system
    """
    backend = PicklePersistenceBackend(base_path)
    return StatePersistence(backend)
