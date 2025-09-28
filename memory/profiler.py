"""Memory profiling and leak detection system.

This module provides comprehensive memory profiling capabilities including
memory usage tracking, leak detection, and allocation analysis.
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
import time
import threading
import logging
import sys
import traceback
import weakref
from collections import defaultdict, deque
import gc

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

logger = logging.getLogger(__name__)


class LeakSeverity(Enum):
    """Severity levels for memory leaks."""
    
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()


@dataclass
class MemorySnapshot:
    """Snapshot of memory usage at a point in time."""
    
    timestamp: float
    process_memory_mb: float
    system_memory_percent: float
    gc_counts: Tuple[int, int, int]
    object_counts: Dict[str, int] = field(default_factory=dict)
    top_objects: List[Tuple[str, int]] = field(default_factory=list)
    
    def get_memory_delta(self, other: 'MemorySnapshot') -> float:
        """Get memory difference from another snapshot.
        
        Args:
            other (MemorySnapshot): Other snapshot to compare with
            
        Returns:
            float: Memory difference in MB
        """
        return self.process_memory_mb - other.process_memory_mb
    
    def get_time_delta(self, other: 'MemorySnapshot') -> float:
        """Get time difference from another snapshot.
        
        Args:
            other (MemorySnapshot): Other snapshot to compare with
            
        Returns:
            float: Time difference in seconds
        """
        return self.timestamp - other.timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary."""
        return {
            'timestamp': self.timestamp,
            'process_memory_mb': self.process_memory_mb,
            'system_memory_percent': self.system_memory_percent,
            'gc_counts': self.gc_counts,
            'object_counts': self.object_counts,
            'top_objects': self.top_objects,
        }


@dataclass
class MemoryLeak:
    """Represents a detected memory leak."""
    
    object_type: str
    count_increase: int
    memory_increase_mb: float
    detection_time: float
    severity: LeakSeverity
    stack_trace: Optional[str] = None
    first_seen: Optional[float] = None
    last_seen: Optional[float] = None
    
    def get_age(self) -> float:
        """Get age of leak in seconds."""
        return time.time() - self.detection_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert leak to dictionary."""
        return {
            'object_type': self.object_type,
            'count_increase': self.count_increase,
            'memory_increase_mb': self.memory_increase_mb,
            'detection_time': self.detection_time,
            'severity': self.severity.name,
            'stack_trace': self.stack_trace,
            'first_seen': self.first_seen,
            'last_seen': self.last_seen,
            'age': self.get_age(),
        }


class AllocationTracker:
    """Tracks object allocations for leak detection."""
    
    def __init__(self, max_history: int = 1000):
        """Initialize allocation tracker.
        
        Args:
            max_history (int): Maximum allocation history to keep
        """
        self.max_history = max_history
        self.allocations: deque = deque(maxlen=max_history)
        self.object_counts: Dict[str, int] = defaultdict(int)
        self.enabled = False
        
        # Thread safety
        self._lock = threading.RLock()
    
    def enable(self) -> None:
        """Enable allocation tracking."""
        with self._lock:
            if not self.enabled:
                self.enabled = True
                # Note: In a real implementation, you'd hook into Python's
                # object allocation system here. This is a simplified version.
                logger.info("Allocation tracking enabled")
    
    def disable(self) -> None:
        """Disable allocation tracking."""
        with self._lock:
            self.enabled = False
            logger.info("Allocation tracking disabled")
    
    def record_allocation(self, obj_type: str, size: int = 0) -> None:
        """Record an object allocation.
        
        Args:
            obj_type (str): Type of object allocated
            size (int): Size of allocation in bytes
        """
        if not self.enabled:
            return
        
        with self._lock:
            allocation = {
                'timestamp': time.time(),
                'type': obj_type,
                'size': size,
                'stack_trace': ''.join(traceback.format_stack()[-5:])  # Last 5 frames
            }
            
            self.allocations.append(allocation)
            self.object_counts[obj_type] += 1
    
    def get_allocation_stats(self) -> Dict[str, Any]:
        """Get allocation statistics.
        
        Returns:
            Dict[str, Any]: Allocation statistics
        """
        with self._lock:
            return {
                'total_allocations': len(self.allocations),
                'object_counts': dict(self.object_counts),
                'enabled': self.enabled,
            }
    
    def clear_history(self) -> None:
        """Clear allocation history."""
        with self._lock:
            self.allocations.clear()
            self.object_counts.clear()


class LeakDetector:
    """Detects memory leaks by analyzing memory snapshots."""
    
    def __init__(self, sensitivity: float = 1.5, min_samples: int = 3):
        """Initialize leak detector.
        
        Args:
            sensitivity (float): Sensitivity multiplier for leak detection
            min_samples (int): Minimum samples needed for detection
        """
        self.sensitivity = sensitivity
        self.min_samples = min_samples
        self.snapshots: deque = deque(maxlen=100)  # Keep last 100 snapshots
        self.detected_leaks: List[MemoryLeak] = []
        
        # Thread safety
        self._lock = threading.RLock()
    
    def add_snapshot(self, snapshot: MemorySnapshot) -> None:
        """Add a memory snapshot for analysis.
        
        Args:
            snapshot (MemorySnapshot): Memory snapshot to analyze
        """
        with self._lock:
            self.snapshots.append(snapshot)
            
            # Analyze for leaks if we have enough samples
            if len(self.snapshots) >= self.min_samples:
                self._analyze_for_leaks()
    
    def _analyze_for_leaks(self) -> None:
        """Analyze snapshots for potential memory leaks."""
        if len(self.snapshots) < self.min_samples:
            return
        
        # Compare recent snapshots
        recent_snapshots = list(self.snapshots)[-self.min_samples:]
        first_snapshot = recent_snapshots[0]
        last_snapshot = recent_snapshots[-1]
        
        # Calculate memory growth
        memory_delta = last_snapshot.get_memory_delta(first_snapshot)
        time_delta = last_snapshot.get_time_delta(first_snapshot)
        
        if memory_delta <= 0 or time_delta <= 0:
            return  # No growth or invalid time delta
        
        # Calculate growth rate (MB per minute)
        growth_rate = (memory_delta / time_delta) * 60
        
        # Check if growth rate exceeds threshold
        threshold = 1.0 * self.sensitivity  # 1 MB per minute base threshold
        
        if growth_rate > threshold:
            # Analyze object count changes
            self._analyze_object_growth(first_snapshot, last_snapshot, memory_delta)
    
    def _analyze_object_growth(self, first: MemorySnapshot, last: MemorySnapshot,
                              memory_delta: float) -> None:
        """Analyze object count growth for leak detection.
        
        Args:
            first (MemorySnapshot): First snapshot
            last (MemorySnapshot): Last snapshot
            memory_delta (float): Memory increase in MB
        """
        for obj_type, last_count in last.object_counts.items():
            first_count = first.object_counts.get(obj_type, 0)
            count_increase = last_count - first_count
            
            # Check for significant object count increase
            if count_increase > 10 * self.sensitivity:  # Base threshold of 10 objects
                severity = self._calculate_leak_severity(count_increase, memory_delta)
                
                leak = MemoryLeak(
                    object_type=obj_type,
                    count_increase=count_increase,
                    memory_increase_mb=memory_delta,
                    detection_time=time.time(),
                    severity=severity,
                    first_seen=first.timestamp,
                    last_seen=last.timestamp
                )
                
                self.detected_leaks.append(leak)
                logger.warning(f"Potential memory leak detected: {obj_type} "
                             f"(+{count_increase} objects, +{memory_delta:.2f} MB)")
    
    def _calculate_leak_severity(self, count_increase: int, memory_delta: float) -> LeakSeverity:
        """Calculate leak severity based on object count and memory increase.
        
        Args:
            count_increase (int): Increase in object count
            memory_delta (float): Memory increase in MB
            
        Returns:
            LeakSeverity: Calculated severity
        """
        if memory_delta > 50 or count_increase > 1000:
            return LeakSeverity.CRITICAL
        elif memory_delta > 20 or count_increase > 500:
            return LeakSeverity.HIGH
        elif memory_delta > 5 or count_increase > 100:
            return LeakSeverity.MEDIUM
        else:
            return LeakSeverity.LOW
    
    def get_detected_leaks(self, severity: Optional[LeakSeverity] = None) -> List[MemoryLeak]:
        """Get detected leaks, optionally filtered by severity.
        
        Args:
            severity (LeakSeverity, optional): Minimum severity to include
            
        Returns:
            List[MemoryLeak]: List of detected leaks
        """
        with self._lock:
            if severity is None:
                return self.detected_leaks.copy()
            
            return [leak for leak in self.detected_leaks if leak.severity.value >= severity.value]
    
    def clear_leaks(self) -> None:
        """Clear detected leaks."""
        with self._lock:
            self.detected_leaks.clear()


class MemoryProfiler:
    """Comprehensive memory profiler with leak detection."""
    
    def __init__(self, profile_interval: float = 60.0, enable_allocation_tracking: bool = False):
        """Initialize memory profiler.
        
        Args:
            profile_interval (float): Profiling interval in seconds
            enable_allocation_tracking (bool): Whether to enable allocation tracking
        """
        self.profile_interval = profile_interval
        self.snapshots: List[MemorySnapshot] = []
        
        # Components
        self.leak_detector = LeakDetector()
        self.allocation_tracker = AllocationTracker()
        
        # Profiling thread
        self._profiling_thread: Optional[threading.Thread] = None
        self._profiling_active = False
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Enable allocation tracking if requested
        if enable_allocation_tracking:
            self.allocation_tracker.enable()
    
    def start_profiling(self) -> None:
        """Start memory profiling."""
        if self._profiling_active:
            return
        
        self._profiling_active = True
        self._profiling_thread = threading.Thread(target=self._profiling_loop, daemon=True)
        self._profiling_thread.start()
        logger.info("Memory profiling started")
    
    def stop_profiling(self) -> None:
        """Stop memory profiling."""
        self._profiling_active = False
        if self._profiling_thread and self._profiling_thread.is_alive():
            self._profiling_thread.join(timeout=1.0)
        logger.info("Memory profiling stopped")
    
    def _profiling_loop(self) -> None:
        """Main profiling loop."""
        while self._profiling_active:
            try:
                snapshot = self._take_snapshot()
                with self._lock:
                    self.snapshots.append(snapshot)
                    self.leak_detector.add_snapshot(snapshot)
                
                # Keep only recent snapshots
                if len(self.snapshots) > 1000:
                    self.snapshots = self.snapshots[-1000:]
                
                time.sleep(self.profile_interval)
                
            except Exception as e:
                logger.error(f"Error in memory profiling: {e}")
                time.sleep(1.0)
    
    def _take_snapshot(self) -> MemorySnapshot:
        """Take a memory snapshot."""
        timestamp = time.time()
        
        # Get process memory info
        process_memory_mb = 0.0
        system_memory_percent = 0.0
        
        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process()
                memory_info = process.memory_info()
                process_memory_mb = memory_info.rss / (1024 * 1024)
                
                system_memory = psutil.virtual_memory()
                system_memory_percent = system_memory.percent
            except Exception as e:
                logger.debug(f"Error getting memory info: {e}")
        
        # Get garbage collection counts
        try:
            if hasattr(gc, 'get_counts'):
                gc_counts = gc.get_counts()
            else:
                gc_counts = (0, 0, 0)  # Python 3.12+ doesn't have get_counts
        except AttributeError:
            gc_counts = (0, 0, 0)
        
        # Get object counts
        object_counts = {}
        top_objects = []
        
        try:
            # Count objects by type
            type_counts = defaultdict(int)
            for obj in gc.get_objects():
                obj_type = type(obj).__name__
                type_counts[obj_type] += 1
            
            object_counts = dict(type_counts)
            
            # Get top 10 object types by count
            top_objects = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
        except Exception as e:
            logger.debug(f"Error counting objects: {e}")
        
        return MemorySnapshot(
            timestamp=timestamp,
            process_memory_mb=process_memory_mb,
            system_memory_percent=system_memory_percent,
            gc_counts=gc_counts,
            object_counts=object_counts,
            top_objects=top_objects
        )
    
    def take_manual_snapshot(self) -> MemorySnapshot:
        """Take a manual memory snapshot.
        
        Returns:
            MemorySnapshot: Current memory snapshot
        """
        snapshot = self._take_snapshot()
        with self._lock:
            self.snapshots.append(snapshot)
            self.leak_detector.add_snapshot(snapshot)
        return snapshot
    
    def get_snapshots(self, limit: Optional[int] = None) -> List[MemorySnapshot]:
        """Get memory snapshots.
        
        Args:
            limit (int, optional): Maximum number of snapshots to return
            
        Returns:
            List[MemorySnapshot]: Memory snapshots
        """
        with self._lock:
            snapshots = self.snapshots.copy()
            if limit:
                snapshots = snapshots[-limit:]
            return snapshots
    
    def get_memory_trend(self, window_minutes: int = 30) -> Dict[str, Any]:
        """Get memory usage trend over a time window.
        
        Args:
            window_minutes (int): Time window in minutes
            
        Returns:
            Dict[str, Any]: Memory trend analysis
        """
        with self._lock:
            if not self.snapshots:
                return {'trend': 'no_data'}
            
            # Filter snapshots within time window
            cutoff_time = time.time() - (window_minutes * 60)
            recent_snapshots = [s for s in self.snapshots if s.timestamp > cutoff_time]
            
            if len(recent_snapshots) < 2:
                return {'trend': 'insufficient_data'}
            
            first_snapshot = recent_snapshots[0]
            last_snapshot = recent_snapshots[-1]
            
            memory_delta = last_snapshot.get_memory_delta(first_snapshot)
            time_delta = last_snapshot.get_time_delta(first_snapshot)
            
            if time_delta <= 0:
                return {'trend': 'invalid_time_delta'}
            
            # Calculate trend
            growth_rate_mb_per_hour = (memory_delta / time_delta) * 3600
            
            trend_classification = 'stable'
            if growth_rate_mb_per_hour > 10:
                trend_classification = 'increasing_fast'
            elif growth_rate_mb_per_hour > 2:
                trend_classification = 'increasing'
            elif growth_rate_mb_per_hour < -10:
                trend_classification = 'decreasing_fast'
            elif growth_rate_mb_per_hour < -2:
                trend_classification = 'decreasing'
            
            return {
                'trend': trend_classification,
                'memory_delta_mb': memory_delta,
                'time_delta_minutes': time_delta / 60,
                'growth_rate_mb_per_hour': growth_rate_mb_per_hour,
                'sample_count': len(recent_snapshots),
                'first_memory_mb': first_snapshot.process_memory_mb,
                'last_memory_mb': last_snapshot.process_memory_mb,
            }
    
    def get_leak_report(self) -> Dict[str, Any]:
        """Get comprehensive leak detection report.
        
        Returns:
            Dict[str, Any]: Leak detection report
        """
        leaks = self.leak_detector.get_detected_leaks()
        
        # Group leaks by severity
        leaks_by_severity = defaultdict(list)
        for leak in leaks:
            leaks_by_severity[leak.severity.name].append(leak.to_dict())
        
        return {
            'total_leaks': len(leaks),
            'leaks_by_severity': dict(leaks_by_severity),
            'critical_leaks': len([l for l in leaks if l.severity == LeakSeverity.CRITICAL]),
            'high_leaks': len([l for l in leaks if l.severity == LeakSeverity.HIGH]),
            'allocation_stats': self.allocation_tracker.get_allocation_stats(),
        }
    
    def clear_data(self) -> None:
        """Clear all profiling data."""
        with self._lock:
            self.snapshots.clear()
            self.leak_detector.clear_leaks()
            self.allocation_tracker.clear_history()
        logger.info("Memory profiler data cleared")
    
    def shutdown(self) -> None:
        """Shutdown the memory profiler."""
        self.stop_profiling()
        self.allocation_tracker.disable()
        self.clear_data()
        logger.info("Memory profiler shutdown complete")


def create_memory_profiler(profile_interval: float = 60.0,
                          enable_allocation_tracking: bool = False) -> MemoryProfiler:
    """Create a memory profiler with default settings.
    
    Args:
        profile_interval (float): Profiling interval in seconds
        enable_allocation_tracking (bool): Whether to enable allocation tracking
        
    Returns:
        MemoryProfiler: Configured memory profiler
    """
    return MemoryProfiler(profile_interval, enable_allocation_tracking)
