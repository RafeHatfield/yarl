"""Core performance profiling components.

This module provides the fundamental profiling infrastructure including
high-precision timers, profiler contexts, and result management.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, Union, ContextManager
from dataclasses import dataclass, field
from enum import Enum, auto
import time
import threading
import logging
from collections import defaultdict, deque
from contextlib import contextmanager
import psutil
import gc

logger = logging.getLogger(__name__)


class ProfilerError(Exception):
    """Exception raised by profiler operations."""
    
    def __init__(self, message: str, profiler_name: str = None, 
                 operation: str = None, cause: Exception = None):
        """Initialize profiler error.
        
        Args:
            message (str): Error message
            profiler_name (str, optional): Name of profiler that caused error
            operation (str, optional): Operation that failed
            cause (Exception, optional): Underlying exception
        """
        super().__init__(message)
        self.profiler_name = profiler_name
        self.operation = operation
        self.cause = cause


class TimerType(Enum):
    """Types of timing measurements."""
    
    WALL_CLOCK = auto()     # Real-world elapsed time
    CPU_TIME = auto()       # CPU processing time
    MONOTONIC = auto()      # Monotonic clock (not affected by system clock adjustments)
    PERF_COUNTER = auto()   # High-resolution performance counter


@dataclass
class ProfilerResult:
    """Result of a profiling operation."""
    
    # Basic information
    name: str
    start_time: float
    end_time: float
    duration: float
    
    # Detailed metrics
    cpu_time: Optional[float] = None
    memory_usage: Optional[int] = None
    memory_peak: Optional[int] = None
    gc_collections: Optional[int] = None
    
    # Context information
    thread_id: Optional[int] = None
    process_id: Optional[int] = None
    call_count: int = 1
    
    # Nested profiling
    children: List['ProfilerResult'] = field(default_factory=list)
    parent: Optional['ProfilerResult'] = None
    
    # Additional data
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def total_duration(self) -> float:
        """Get total duration including children."""
        return self.duration + sum(child.duration for child in self.children)
    
    @property
    def self_duration(self) -> float:
        """Get duration excluding children."""
        return self.duration - sum(child.duration for child in self.children)
    
    @property
    def average_duration(self) -> float:
        """Get average duration per call."""
        return self.duration / self.call_count if self.call_count > 0 else 0.0
    
    def add_child(self, child: 'ProfilerResult') -> None:
        """Add a child profiler result.
        
        Args:
            child (ProfilerResult): Child result to add
        """
        child.parent = self
        self.children.append(child)
    
    def get_memory_delta(self) -> Optional[int]:
        """Get memory usage change during profiling.
        
        Returns:
            int: Memory change in bytes, None if not available
        """
        if self.memory_peak is not None and self.memory_usage is not None:
            return self.memory_peak - self.memory_usage
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary representation."""
        return {
            'name': self.name,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'cpu_time': self.cpu_time,
            'memory_usage': self.memory_usage,
            'memory_peak': self.memory_peak,
            'gc_collections': self.gc_collections,
            'thread_id': self.thread_id,
            'process_id': self.process_id,
            'call_count': self.call_count,
            'total_duration': self.total_duration,
            'self_duration': self.self_duration,
            'average_duration': self.average_duration,
            'children': [child.to_dict() for child in self.children],
            'metadata': self.metadata,
        }


class Timer(ABC):
    """Abstract base class for timing measurements."""
    
    @abstractmethod
    def start(self) -> float:
        """Start timing and return start time."""
        pass
    
    @abstractmethod
    def stop(self) -> float:
        """Stop timing and return end time."""
        pass
    
    @abstractmethod
    def elapsed(self) -> float:
        """Get elapsed time since start."""
        pass
    
    @abstractmethod
    def reset(self) -> None:
        """Reset the timer."""
        pass


class HighPrecisionTimer(Timer):
    """High-precision timer using performance counter."""
    
    def __init__(self):
        """Initialize high-precision timer."""
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
    
    def start(self) -> float:
        """Start timing using performance counter."""
        self._start_time = time.perf_counter()
        self._end_time = None
        return self._start_time
    
    def stop(self) -> float:
        """Stop timing and return end time."""
        if self._start_time is None:
            raise ProfilerError("Timer not started", operation="stop")
        
        self._end_time = time.perf_counter()
        return self._end_time
    
    def elapsed(self) -> float:
        """Get elapsed time since start."""
        if self._start_time is None:
            return 0.0
        
        end_time = self._end_time or time.perf_counter()
        return end_time - self._start_time
    
    def reset(self) -> None:
        """Reset the timer."""
        self._start_time = None
        self._end_time = None


class FrameTimer(Timer):
    """Timer specialized for frame rate measurements."""
    
    def __init__(self, window_size: int = 60):
        """Initialize frame timer.
        
        Args:
            window_size (int): Number of frames to track for averaging
        """
        self.window_size = window_size
        self.frame_times: deque = deque(maxlen=window_size)
        self._last_frame_time: Optional[float] = None
        self._frame_count = 0
    
    def start(self) -> float:
        """Start frame timing."""
        current_time = time.perf_counter()
        
        if self._last_frame_time is not None:
            frame_duration = current_time - self._last_frame_time
            self.frame_times.append(frame_duration)
            self._frame_count += 1
        
        self._last_frame_time = current_time
        return current_time
    
    def stop(self) -> float:
        """Stop frame timing (same as start for frame timer)."""
        return self.start()
    
    def elapsed(self) -> float:
        """Get average frame time."""
        if not self.frame_times:
            return 0.0
        return sum(self.frame_times) / len(self.frame_times)
    
    def reset(self) -> None:
        """Reset frame timer."""
        self.frame_times.clear()
        self._last_frame_time = None
        self._frame_count = 0
    
    def get_fps(self) -> float:
        """Get current frames per second."""
        avg_frame_time = self.elapsed()
        return 1.0 / avg_frame_time if avg_frame_time > 0 else 0.0
    
    def get_frame_count(self) -> int:
        """Get total frame count."""
        return self._frame_count


class SystemTimer(Timer):
    """Timer that tracks both wall clock and CPU time."""
    
    def __init__(self):
        """Initialize system timer."""
        self._start_wall_time: Optional[float] = None
        self._start_cpu_time: Optional[float] = None
        self._end_wall_time: Optional[float] = None
        self._end_cpu_time: Optional[float] = None
    
    def start(self) -> float:
        """Start system timing."""
        self._start_wall_time = time.perf_counter()
        self._start_cpu_time = time.process_time()
        self._end_wall_time = None
        self._end_cpu_time = None
        return self._start_wall_time
    
    def stop(self) -> float:
        """Stop system timing."""
        if self._start_wall_time is None:
            raise ProfilerError("Timer not started", operation="stop")
        
        self._end_wall_time = time.perf_counter()
        self._end_cpu_time = time.process_time()
        return self._end_wall_time
    
    def elapsed(self) -> float:
        """Get elapsed wall clock time."""
        if self._start_wall_time is None:
            return 0.0
        
        end_time = self._end_wall_time or time.perf_counter()
        return end_time - self._start_wall_time
    
    def cpu_elapsed(self) -> float:
        """Get elapsed CPU time."""
        if self._start_cpu_time is None:
            return 0.0
        
        end_time = self._end_cpu_time or time.process_time()
        return end_time - self._start_cpu_time
    
    def reset(self) -> None:
        """Reset system timer."""
        self._start_wall_time = None
        self._start_cpu_time = None
        self._end_wall_time = None
        self._end_cpu_time = None


class ProfilerContext:
    """Context manager for profiling operations."""
    
    def __init__(self, profiler: 'PerformanceProfiler', name: str, 
                 metadata: Dict[str, Any] = None):
        """Initialize profiler context.
        
        Args:
            profiler (PerformanceProfiler): Profiler instance
            name (str): Name of the profiling operation
            metadata (Dict[str, Any], optional): Additional metadata
        """
        self.profiler = profiler
        self.name = name
        self.metadata = metadata or {}
        self.result: Optional[ProfilerResult] = None
        
        # Timing
        self.timer = SystemTimer()
        
        # Memory tracking
        self.start_memory: Optional[int] = None
        self.peak_memory: Optional[int] = None
        self.start_gc_count: Optional[int] = None
        
        # Thread information
        self.thread_id = threading.get_ident()
        self.process_id = psutil.os.getpid()
    
    def __enter__(self) -> 'ProfilerContext':
        """Enter profiler context."""
        try:
            # Start timing
            self.timer.start()
            
            # Track memory if available
            try:
                process = psutil.Process(self.process_id)
                self.start_memory = process.memory_info().rss
                self.peak_memory = self.start_memory
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self.start_memory = None
                self.peak_memory = None
            
            # Track garbage collection
            try:
                # gc.get_counts() was removed in Python 3.12
                if hasattr(gc, 'get_counts'):
                    self.start_gc_count = sum(gc.get_counts())
                else:
                    self.start_gc_count = 0
            except AttributeError:
                self.start_gc_count = 0
            
            # Notify profiler
            self.profiler._enter_context(self)
            
            return self
            
        except Exception as e:
            raise ProfilerError(f"Failed to enter profiler context: {e}", 
                              self.name, "enter", e)
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit profiler context."""
        try:
            # Stop timing
            self.timer.stop()
            
            # Calculate final memory usage
            end_memory = None
            if self.start_memory is not None:
                try:
                    process = psutil.Process(self.process_id)
                    end_memory = process.memory_info().rss
                    self.peak_memory = max(self.peak_memory or 0, end_memory)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Calculate GC collections
            try:
                if hasattr(gc, 'get_counts'):
                    end_gc_count = sum(gc.get_counts())
                else:
                    end_gc_count = 0
            except AttributeError:
                end_gc_count = 0
            gc_collections = end_gc_count - (self.start_gc_count or 0)
            
            # Create result
            self.result = ProfilerResult(
                name=self.name,
                start_time=self.timer._start_wall_time,
                end_time=self.timer._end_wall_time,
                duration=self.timer.elapsed(),
                cpu_time=self.timer.cpu_elapsed(),
                memory_usage=self.start_memory,
                memory_peak=self.peak_memory,
                gc_collections=gc_collections,
                thread_id=self.thread_id,
                process_id=self.process_id,
                metadata=self.metadata
            )
            
            # Add any child results that were stored during nested profiling
            if hasattr(self, '_child_results'):
                for child_result in self._child_results:
                    self.result.add_child(child_result)
            
            # Notify profiler
            self.profiler._exit_context(self)
            
        except Exception as e:
            logger.error(f"Error exiting profiler context {self.name}: {e}")
            raise ProfilerError(f"Failed to exit profiler context: {e}", 
                              self.name, "exit", e)


class PerformanceProfiler:
    """Main performance profiler class."""
    
    def __init__(self, name: str = "default", enabled: bool = True):
        """Initialize performance profiler.
        
        Args:
            name (str): Name of this profiler instance
            enabled (bool): Whether profiling is enabled
        """
        self.name = name
        self.enabled = enabled
        
        # Results storage
        self.results: List[ProfilerResult] = []
        self.active_contexts: List[ProfilerContext] = []
        
        # Statistics
        self.stats = {
            'total_profiles': 0,
            'total_duration': 0.0,
            'average_duration': 0.0,
            'min_duration': float('inf'),
            'max_duration': 0.0,
        }
        
        # Configuration
        self.max_results = 1000  # Maximum number of results to keep
        self.auto_gc = True      # Whether to trigger GC before profiling
        
        # Thread safety
        self._lock = threading.RLock()
    
    def profile(self, name: str, metadata: Dict[str, Any] = None) -> ProfilerContext:
        """Create a profiling context.
        
        Args:
            name (str): Name of the operation to profile
            metadata (Dict[str, Any], optional): Additional metadata
            
        Returns:
            ProfilerContext: Context manager for profiling
        """
        if not self.enabled:
            return _NullProfilerContext()
        
        return ProfilerContext(self, name, metadata)
    
    @contextmanager
    def profile_function(self, func: Callable, *args, **kwargs):
        """Profile a function call.
        
        Args:
            func (Callable): Function to profile
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Yields:
            Any: Function result
        """
        func_name = getattr(func, '__name__', str(func))
        
        with self.profile(f"function:{func_name}") as ctx:
            result = func(*args, **kwargs)
            ctx.metadata['function_result'] = type(result).__name__
            yield result
    
    def profile_decorator(self, name: str = None, metadata: Dict[str, Any] = None):
        """Decorator for profiling functions.
        
        Args:
            name (str, optional): Custom name for the profile
            metadata (Dict[str, Any], optional): Additional metadata
            
        Returns:
            Callable: Decorated function
        """
        def decorator(func: Callable) -> Callable:
            profile_name = name or f"function:{func.__name__}"
            
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)
                
                with self.profile(profile_name, metadata) as ctx:
                    result = func(*args, **kwargs)
                    ctx.metadata['args_count'] = len(args)
                    ctx.metadata['kwargs_count'] = len(kwargs)
                    return result
            
            wrapper.__name__ = func.__name__
            wrapper.__doc__ = func.__doc__
            return wrapper
        
        return decorator
    
    def _enter_context(self, context: ProfilerContext) -> None:
        """Handle context entry.
        
        Args:
            context (ProfilerContext): Context being entered
        """
        with self._lock:
            self.active_contexts.append(context)
            
            # Trigger GC if configured
            if self.auto_gc:
                gc.collect()
    
    def _exit_context(self, context: ProfilerContext) -> None:
        """Handle context exit.
        
        Args:
            context (ProfilerContext): Context being exited
        """
        with self._lock:
            if context in self.active_contexts:
                self.active_contexts.remove(context)
            
            if context.result:
                # Handle nested profiling
                if self.active_contexts:
                    parent_context = self.active_contexts[-1]
                    # Store child reference in parent context for later processing
                    if not hasattr(parent_context, '_child_results'):
                        parent_context._child_results = []
                    parent_context._child_results.append(context.result)
                
                # Store result
                self.results.append(context.result)
                
                # Update statistics
                self._update_stats(context.result)
                
                # Cleanup old results if needed
                if len(self.results) > self.max_results:
                    self.results = self.results[-self.max_results:]
    
    def _update_stats(self, result: ProfilerResult) -> None:
        """Update profiler statistics.
        
        Args:
            result (ProfilerResult): Result to include in statistics
        """
        self.stats['total_profiles'] += 1
        self.stats['total_duration'] += result.duration
        self.stats['average_duration'] = (
            self.stats['total_duration'] / self.stats['total_profiles']
        )
        self.stats['min_duration'] = min(self.stats['min_duration'], result.duration)
        self.stats['max_duration'] = max(self.stats['max_duration'], result.duration)
    
    def get_results(self, name_filter: str = None, limit: int = None) -> List[ProfilerResult]:
        """Get profiling results.
        
        Args:
            name_filter (str, optional): Filter results by name
            limit (int, optional): Maximum number of results to return
            
        Returns:
            List[ProfilerResult]: Filtered profiling results
        """
        with self._lock:
            results = self.results.copy()
        
        if name_filter:
            results = [r for r in results if name_filter in r.name]
        
        if limit:
            results = results[-limit:]
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get profiler statistics.
        
        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        with self._lock:
            stats = self.stats.copy()
            stats['active_contexts'] = len(self.active_contexts)
            stats['total_results'] = len(self.results)
            stats['enabled'] = self.enabled
            return stats
    
    def clear_results(self) -> None:
        """Clear all profiling results."""
        with self._lock:
            self.results.clear()
            self.stats = {
                'total_profiles': 0,
                'total_duration': 0.0,
                'average_duration': 0.0,
                'min_duration': float('inf'),
                'max_duration': 0.0,
            }
    
    def enable(self) -> None:
        """Enable profiling."""
        self.enabled = True
    
    def disable(self) -> None:
        """Disable profiling."""
        self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if profiling is enabled.
        
        Returns:
            bool: True if profiling is enabled
        """
        return self.enabled


class _NullProfilerContext:
    """Null profiler context for when profiling is disabled."""
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


# Global profiler instance
_global_profiler = PerformanceProfiler("global")


def get_global_profiler() -> PerformanceProfiler:
    """Get the global profiler instance.
    
    Returns:
        PerformanceProfiler: Global profiler instance
    """
    return _global_profiler


def profile(name: str, metadata: Dict[str, Any] = None) -> ProfilerContext:
    """Create a profiling context using the global profiler.
    
    Args:
        name (str): Name of the operation to profile
        metadata (Dict[str, Any], optional): Additional metadata
        
    Returns:
        ProfilerContext: Context manager for profiling
    """
    return _global_profiler.profile(name, metadata)


def profile_function(name: str = None, metadata: Dict[str, Any] = None):
    """Decorator for profiling functions using the global profiler.
    
    Args:
        name (str, optional): Custom name for the profile
        metadata (Dict[str, Any], optional): Additional metadata
        
    Returns:
        Callable: Decorated function
    """
    return _global_profiler.profile_decorator(name, metadata)
