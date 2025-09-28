"""Memory optimization utilities and helper functions.

This module provides utility functions for memory analysis, formatting,
and tracking to support the memory optimization system.
"""

from typing import Any, Dict, List, Optional, Tuple, ContextManager
from dataclasses import dataclass
import sys
import time
import threading
import logging
import contextlib
from collections import defaultdict, deque
import weakref

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

logger = logging.getLogger(__name__)


@dataclass
class MemoryUsage:
    """Memory usage information."""
    
    rss_mb: float = 0.0          # Resident Set Size in MB
    vms_mb: float = 0.0          # Virtual Memory Size in MB
    percent: float = 0.0         # Percentage of system memory
    available_mb: float = 0.0    # Available system memory in MB
    timestamp: float = 0.0       # Timestamp of measurement
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'rss_mb': self.rss_mb,
            'vms_mb': self.vms_mb,
            'percent': self.percent,
            'available_mb': self.available_mb,
            'timestamp': self.timestamp,
        }


class AllocationTracker:
    """Tracks memory allocations for analysis."""
    
    def __init__(self, max_entries: int = 10000):
        """Initialize allocation tracker.
        
        Args:
            max_entries (int): Maximum allocation entries to track
        """
        self.max_entries = max_entries
        self.allocations: deque = deque(maxlen=max_entries)
        self.allocation_counts: Dict[str, int] = defaultdict(int)
        self.allocation_sizes: Dict[str, int] = defaultdict(int)
        self.enabled = False
        
        # Thread safety
        self._lock = threading.RLock()
    
    def enable(self) -> None:
        """Enable allocation tracking."""
        with self._lock:
            self.enabled = True
            logger.debug("Allocation tracking enabled")
    
    def disable(self) -> None:
        """Disable allocation tracking."""
        with self._lock:
            self.enabled = False
            logger.debug("Allocation tracking disabled")
    
    def track_allocation(self, obj_type: str, size: int = 0, location: str = "") -> None:
        """Track an allocation.
        
        Args:
            obj_type (str): Type of object allocated
            size (int): Size in bytes
            location (str): Location/context of allocation
        """
        if not self.enabled:
            return
        
        with self._lock:
            allocation = {
                'timestamp': time.time(),
                'type': obj_type,
                'size': size,
                'location': location,
            }
            
            self.allocations.append(allocation)
            self.allocation_counts[obj_type] += 1
            self.allocation_sizes[obj_type] += size
    
    def get_stats(self) -> Dict[str, Any]:
        """Get allocation statistics.
        
        Returns:
            Dict[str, Any]: Allocation statistics
        """
        with self._lock:
            total_allocations = sum(self.allocation_counts.values())
            total_size = sum(self.allocation_sizes.values())
            
            # Top allocations by count
            top_by_count = sorted(
                self.allocation_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            # Top allocations by size
            top_by_size = sorted(
                self.allocation_sizes.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            return {
                'enabled': self.enabled,
                'total_allocations': total_allocations,
                'total_size_bytes': total_size,
                'total_size_mb': total_size / (1024 * 1024),
                'unique_types': len(self.allocation_counts),
                'top_by_count': top_by_count,
                'top_by_size': top_by_size,
                'recent_count': len(self.allocations),
            }
    
    def clear(self) -> None:
        """Clear allocation data."""
        with self._lock:
            self.allocations.clear()
            self.allocation_counts.clear()
            self.allocation_sizes.clear()


class MemoryMonitor:
    """Monitors memory usage over time."""
    
    def __init__(self, sample_interval: float = 1.0, max_samples: int = 3600):
        """Initialize memory monitor.
        
        Args:
            sample_interval (float): Sampling interval in seconds
            max_samples (int): Maximum samples to keep
        """
        self.sample_interval = sample_interval
        self.max_samples = max_samples
        self.samples: deque = deque(maxlen=max_samples)
        self.monitoring = False
        
        # Monitoring thread
        self._monitor_thread: Optional[threading.Thread] = None
        
        # Thread safety
        self._lock = threading.RLock()
    
    def start_monitoring(self) -> None:
        """Start memory monitoring."""
        if self.monitoring:
            return
        
        self.monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("Memory monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop memory monitoring."""
        self.monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1.0)
        logger.info("Memory monitoring stopped")
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self.monitoring:
            try:
                usage = get_memory_usage()
                with self._lock:
                    self.samples.append(usage)
                
                time.sleep(self.sample_interval)
                
            except Exception as e:
                logger.error(f"Error in memory monitoring: {e}")
                time.sleep(1.0)
    
    def get_current_usage(self) -> Optional[MemoryUsage]:
        """Get current memory usage.
        
        Returns:
            MemoryUsage: Current memory usage or None
        """
        with self._lock:
            return self.samples[-1] if self.samples else None
    
    def get_usage_history(self, minutes: int = 60) -> List[MemoryUsage]:
        """Get memory usage history.
        
        Args:
            minutes (int): Minutes of history to return
            
        Returns:
            List[MemoryUsage]: Memory usage history
        """
        with self._lock:
            if not self.samples:
                return []
            
            cutoff_time = time.time() - (minutes * 60)
            return [s for s in self.samples if s.timestamp > cutoff_time]
    
    def get_usage_stats(self, minutes: int = 60) -> Dict[str, Any]:
        """Get memory usage statistics.
        
        Args:
            minutes (int): Minutes to analyze
            
        Returns:
            Dict[str, Any]: Usage statistics
        """
        history = self.get_usage_history(minutes)
        
        if not history:
            return {'error': 'no_data'}
        
        rss_values = [s.rss_mb for s in history]
        vms_values = [s.vms_mb for s in history]
        
        return {
            'sample_count': len(history),
            'time_span_minutes': minutes,
            'rss_mb': {
                'current': rss_values[-1],
                'min': min(rss_values),
                'max': max(rss_values),
                'avg': sum(rss_values) / len(rss_values),
                'delta': rss_values[-1] - rss_values[0] if len(rss_values) > 1 else 0,
            },
            'vms_mb': {
                'current': vms_values[-1],
                'min': min(vms_values),
                'max': max(vms_values),
                'avg': sum(vms_values) / len(vms_values),
                'delta': vms_values[-1] - vms_values[0] if len(vms_values) > 1 else 0,
            }
        }


def get_object_size(obj: Any) -> int:
    """Get the size of an object in bytes.
    
    Args:
        obj (Any): Object to measure
        
    Returns:
        int: Size in bytes
    """
    try:
        return sys.getsizeof(obj)
    except (TypeError, AttributeError):
        return 0


def get_deep_object_size(obj: Any, seen: Optional[set] = None) -> int:
    """Get the deep size of an object including referenced objects.
    
    Args:
        obj (Any): Object to measure
        seen (set, optional): Set of already seen objects
        
    Returns:
        int: Deep size in bytes
    """
    if seen is None:
        seen = set()
    
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    
    seen.add(obj_id)
    size = sys.getsizeof(obj)
    
    # Handle different object types
    if isinstance(obj, dict):
        size += sum(get_deep_object_size(k, seen) + get_deep_object_size(v, seen) 
                   for k, v in obj.items())
    elif isinstance(obj, (list, tuple, set, frozenset)):
        size += sum(get_deep_object_size(item, seen) for item in obj)
    elif hasattr(obj, '__dict__'):
        size += get_deep_object_size(obj.__dict__, seen)
    elif hasattr(obj, '__slots__'):
        size += sum(get_deep_object_size(getattr(obj, slot, None), seen) 
                   for slot in obj.__slots__ if hasattr(obj, slot))
    
    return size


def get_memory_usage() -> MemoryUsage:
    """Get current memory usage information.
    
    Returns:
        MemoryUsage: Current memory usage
    """
    usage = MemoryUsage(timestamp=time.time())
    
    if PSUTIL_AVAILABLE:
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            usage.rss_mb = memory_info.rss / (1024 * 1024)
            usage.vms_mb = memory_info.vms / (1024 * 1024)
            usage.percent = process.memory_percent()
            
            # System memory info
            system_memory = psutil.virtual_memory()
            usage.available_mb = system_memory.available / (1024 * 1024)
            
        except Exception as e:
            logger.debug(f"Error getting memory usage: {e}")
    
    return usage


def format_memory_size(bytes_size: int) -> str:
    """Format memory size in human-readable format.
    
    Args:
        bytes_size (int): Size in bytes
        
    Returns:
        str: Formatted size string
    """
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f} KB"
    elif bytes_size < 1024 * 1024 * 1024:
        return f"{bytes_size / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_size / (1024 * 1024 * 1024):.1f} GB"


def format_memory_delta(delta_bytes: int) -> str:
    """Format memory delta with +/- sign.
    
    Args:
        delta_bytes (int): Delta in bytes
        
    Returns:
        str: Formatted delta string
    """
    sign = "+" if delta_bytes >= 0 else ""
    return f"{sign}{format_memory_size(abs(delta_bytes))}"


def format_percentage(value: float, precision: int = 1) -> str:
    """Format percentage value.
    
    Args:
        value (float): Percentage value
        precision (int): Decimal precision
        
    Returns:
        str: Formatted percentage string
    """
    return f"{value:.{precision}f}%"


@contextlib.contextmanager
def memory_usage_context(description: str = "") -> ContextManager[Dict[str, Any]]:
    """Context manager to track memory usage during execution.
    
    Args:
        description (str): Description of the operation
        
    Yields:
        Dict[str, Any]: Memory usage information
    """
    start_usage = get_memory_usage()
    start_time = time.time()
    
    result = {
        'description': description,
        'start_time': start_time,
        'start_usage': start_usage,
        'end_time': None,
        'end_usage': None,
        'duration_seconds': None,
        'memory_delta_mb': None,
    }
    
    try:
        yield result
    finally:
        end_time = time.time()
        end_usage = get_memory_usage()
        
        result.update({
            'end_time': end_time,
            'end_usage': end_usage,
            'duration_seconds': end_time - start_time,
            'memory_delta_mb': end_usage.rss_mb - start_usage.rss_mb,
        })


@contextlib.contextmanager
def track_allocations(tracker: AllocationTracker, 
                     description: str = "") -> ContextManager[Dict[str, Any]]:
    """Context manager to track allocations during execution.
    
    Args:
        tracker (AllocationTracker): Allocation tracker to use
        description (str): Description of the operation
        
    Yields:
        Dict[str, Any]: Allocation tracking information
    """
    was_enabled = tracker.enabled
    start_stats = tracker.get_stats()
    
    if not was_enabled:
        tracker.enable()
    
    result = {
        'description': description,
        'start_stats': start_stats,
        'end_stats': None,
        'allocations_delta': None,
    }
    
    try:
        yield result
    finally:
        end_stats = tracker.get_stats()
        
        result.update({
            'end_stats': end_stats,
            'allocations_delta': {
                'total_allocations': (end_stats['total_allocations'] - 
                                    start_stats['total_allocations']),
                'total_size_bytes': (end_stats['total_size_bytes'] - 
                                   start_stats['total_size_bytes']),
            }
        })
        
        if not was_enabled:
            tracker.disable()


class ObjectRegistry:
    """Registry for tracking object instances."""
    
    def __init__(self):
        """Initialize object registry."""
        self.objects: Dict[str, weakref.WeakSet] = defaultdict(weakref.WeakSet)
        self._lock = threading.RLock()
    
    def register(self, obj: Any, category: str = None) -> None:
        """Register an object.
        
        Args:
            obj (Any): Object to register
            category (str, optional): Object category
        """
        with self._lock:
            category = category or type(obj).__name__
            self.objects[category].add(obj)
    
    def get_count(self, category: str) -> int:
        """Get count of objects in category.
        
        Args:
            category (str): Object category
            
        Returns:
            int: Number of objects
        """
        with self._lock:
            return len(self.objects.get(category, []))
    
    def get_all_counts(self) -> Dict[str, int]:
        """Get counts for all categories.
        
        Returns:
            Dict[str, int]: Category counts
        """
        with self._lock:
            return {category: len(objects) 
                   for category, objects in self.objects.items()}
    
    def clear_category(self, category: str) -> None:
        """Clear a category.
        
        Args:
            category (str): Category to clear
        """
        with self._lock:
            if category in self.objects:
                self.objects[category].clear()
    
    def clear_all(self) -> None:
        """Clear all categories."""
        with self._lock:
            self.objects.clear()


def calculate_memory_efficiency(before_mb: float, after_mb: float, 
                              operations: int) -> Dict[str, float]:
    """Calculate memory efficiency metrics.
    
    Args:
        before_mb (float): Memory usage before optimization
        after_mb (float): Memory usage after optimization
        operations (int): Number of operations performed
        
    Returns:
        Dict[str, float]: Efficiency metrics
    """
    memory_saved_mb = before_mb - after_mb
    memory_saved_percent = (memory_saved_mb / before_mb) * 100 if before_mb > 0 else 0
    memory_per_operation = memory_saved_mb / operations if operations > 0 else 0
    
    return {
        'memory_saved_mb': memory_saved_mb,
        'memory_saved_percent': memory_saved_percent,
        'memory_per_operation_kb': memory_per_operation * 1024,
        'efficiency_ratio': after_mb / before_mb if before_mb > 0 else 1.0,
    }


def get_system_memory_info() -> Dict[str, Any]:
    """Get system memory information.
    
    Returns:
        Dict[str, Any]: System memory information
    """
    info = {
        'psutil_available': PSUTIL_AVAILABLE,
        'total_mb': 0,
        'available_mb': 0,
        'used_mb': 0,
        'percent_used': 0,
    }
    
    if PSUTIL_AVAILABLE:
        try:
            memory = psutil.virtual_memory()
            info.update({
                'total_mb': memory.total / (1024 * 1024),
                'available_mb': memory.available / (1024 * 1024),
                'used_mb': memory.used / (1024 * 1024),
                'percent_used': memory.percent,
            })
        except Exception as e:
            info['error'] = str(e)
    
    return info


# Global instances
_global_allocation_tracker: Optional[AllocationTracker] = None
_global_memory_monitor: Optional[MemoryMonitor] = None
_global_object_registry: Optional[ObjectRegistry] = None


def get_global_allocation_tracker() -> AllocationTracker:
    """Get global allocation tracker."""
    global _global_allocation_tracker
    if _global_allocation_tracker is None:
        _global_allocation_tracker = AllocationTracker()
    return _global_allocation_tracker


def get_global_memory_monitor() -> MemoryMonitor:
    """Get global memory monitor."""
    global _global_memory_monitor
    if _global_memory_monitor is None:
        _global_memory_monitor = MemoryMonitor()
    return _global_memory_monitor


def get_global_object_registry() -> ObjectRegistry:
    """Get global object registry."""
    global _global_object_registry
    if _global_object_registry is None:
        _global_object_registry = ObjectRegistry()
    return _global_object_registry
