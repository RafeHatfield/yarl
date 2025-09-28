"""Performance monitoring system for real-time metrics collection.

This module provides comprehensive monitoring of system performance including
memory usage, CPU utilization, frame rates, and custom metrics.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum, auto
import time
import threading
import logging
from collections import deque, defaultdict
import psutil
import gc

from events import EventBus, get_event_bus, Event, EventListener, event_handler

logger = logging.getLogger(__name__)


class MonitorType(Enum):
    """Types of performance monitors."""
    
    SYSTEM = auto()         # System-level monitoring (CPU, memory)
    FRAME_RATE = auto()     # Frame rate and timing monitoring
    MEMORY = auto()         # Memory usage monitoring
    EVENT = auto()          # Event system monitoring
    CUSTOM = auto()         # Custom metric monitoring


@dataclass
class MonitorConfig:
    """Configuration for performance monitors."""
    
    # Sampling configuration
    sample_interval: float = 1.0        # Seconds between samples
    history_size: int = 300             # Number of samples to keep (5 minutes at 1Hz)
    
    # System monitoring
    monitor_cpu: bool = True
    monitor_memory: bool = True
    monitor_disk: bool = False
    monitor_network: bool = False
    
    # Frame rate monitoring
    target_fps: float = 60.0
    frame_history_size: int = 60        # Number of frames to track
    
    # Event monitoring
    monitor_events: bool = True
    event_history_size: int = 1000
    
    # Alerting
    enable_alerts: bool = True
    cpu_threshold: float = 80.0         # CPU usage alert threshold (%)
    memory_threshold: float = 80.0      # Memory usage alert threshold (%)
    fps_threshold: float = 30.0         # FPS alert threshold
    
    # Performance
    async_monitoring: bool = True       # Use separate thread for monitoring
    batch_size: int = 10               # Number of samples to process at once


@dataclass
class MonitorResult:
    """Result from a monitoring operation."""
    
    timestamp: float
    monitor_type: MonitorType
    metrics: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_metric(self, name: str, default: Any = None) -> Any:
        """Get a specific metric value.
        
        Args:
            name (str): Metric name
            default (Any): Default value if metric not found
            
        Returns:
            Any: Metric value or default
        """
        return self.metrics.get(name, default)
    
    def has_metric(self, name: str) -> bool:
        """Check if a metric exists.
        
        Args:
            name (str): Metric name
            
        Returns:
            bool: True if metric exists
        """
        return name in self.metrics


class PerformanceMonitor(ABC):
    """Abstract base class for performance monitors."""
    
    def __init__(self, name: str, config: MonitorConfig = None):
        """Initialize performance monitor.
        
        Args:
            name (str): Monitor name
            config (MonitorConfig, optional): Monitor configuration
        """
        self.name = name
        self.config = config or MonitorConfig()
        self.enabled = True
        
        # Data storage
        self.samples: deque = deque(maxlen=self.config.history_size)
        self.current_metrics: Dict[str, Any] = {}
        
        # Statistics
        self.stats = {
            'total_samples': 0,
            'start_time': time.time(),
            'last_sample_time': None,
        }
        
        # Thread safety
        self._lock = threading.RLock()
    
    @abstractmethod
    def collect_metrics(self) -> Dict[str, Any]:
        """Collect current metrics.
        
        Returns:
            Dict[str, Any]: Current metrics
        """
        pass
    
    def sample(self) -> Optional[MonitorResult]:
        """Take a performance sample.
        
        Returns:
            MonitorResult: Monitoring result, None if disabled
        """
        if not self.enabled:
            return None
        
        try:
            timestamp = time.time()
            metrics = self.collect_metrics()
            
            result = MonitorResult(
                timestamp=timestamp,
                monitor_type=self.get_monitor_type(),
                metrics=metrics,
                metadata={'monitor_name': self.name}
            )
            
            with self._lock:
                self.samples.append(result)
                self.current_metrics = metrics
                self.stats['total_samples'] += 1
                self.stats['last_sample_time'] = timestamp
            
            return result
            
        except Exception as e:
            logger.error(f"Error sampling {self.name}: {e}")
            return None
    
    @abstractmethod
    def get_monitor_type(self) -> MonitorType:
        """Get the monitor type.
        
        Returns:
            MonitorType: Type of this monitor
        """
        pass
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics.
        
        Returns:
            Dict[str, Any]: Current metrics
        """
        with self._lock:
            return self.current_metrics.copy()
    
    def get_history(self, limit: int = None) -> List[MonitorResult]:
        """Get monitoring history.
        
        Args:
            limit (int, optional): Maximum number of samples to return
            
        Returns:
            List[MonitorResult]: Historical monitoring results
        """
        with self._lock:
            samples = list(self.samples)
        
        if limit:
            samples = samples[-limit:]
        
        return samples
    
    def get_stats(self) -> Dict[str, Any]:
        """Get monitor statistics.
        
        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        with self._lock:
            stats = self.stats.copy()
            stats['enabled'] = self.enabled
            stats['sample_count'] = len(self.samples)
            stats['uptime'] = time.time() - self.stats['start_time']
            return stats
    
    def clear_history(self) -> None:
        """Clear monitoring history."""
        with self._lock:
            self.samples.clear()
    
    def enable(self) -> None:
        """Enable monitoring."""
        self.enabled = True
    
    def disable(self) -> None:
        """Disable monitoring."""
        self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if monitoring is enabled.
        
        Returns:
            bool: True if monitoring is enabled
        """
        return self.enabled


class SystemMonitor(PerformanceMonitor):
    """Monitor for system-level performance metrics."""
    
    def __init__(self, config: MonitorConfig = None):
        """Initialize system monitor.
        
        Args:
            config (MonitorConfig, optional): Monitor configuration
        """
        super().__init__("system", config)
        
        # System information
        try:
            self.process = psutil.Process()
            self.system_available = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            self.process = None
            self.system_available = False
            logger.warning("System monitoring not available")
    
    def collect_metrics(self) -> Dict[str, Any]:
        """Collect system performance metrics.
        
        Returns:
            Dict[str, Any]: System metrics
        """
        metrics = {}
        
        if not self.system_available:
            return metrics
        
        try:
            # CPU metrics
            if self.config.monitor_cpu:
                metrics['cpu_percent'] = psutil.cpu_percent(interval=None)
                metrics['cpu_count'] = psutil.cpu_count()
                metrics['cpu_freq'] = psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
                
                # Process CPU
                if self.process:
                    metrics['process_cpu_percent'] = self.process.cpu_percent()
                    metrics['process_cpu_times'] = self.process.cpu_times()._asdict()
            
            # Memory metrics
            if self.config.monitor_memory:
                memory = psutil.virtual_memory()
                metrics['memory_total'] = memory.total
                metrics['memory_available'] = memory.available
                metrics['memory_used'] = memory.used
                metrics['memory_percent'] = memory.percent
                
                # Process memory
                if self.process:
                    process_memory = self.process.memory_info()
                    metrics['process_memory_rss'] = process_memory.rss
                    metrics['process_memory_vms'] = process_memory.vms
                    metrics['process_memory_percent'] = self.process.memory_percent()
            
            # Disk metrics
            if self.config.monitor_disk:
                disk_usage = psutil.disk_usage('/')
                metrics['disk_total'] = disk_usage.total
                metrics['disk_used'] = disk_usage.used
                metrics['disk_free'] = disk_usage.free
                metrics['disk_percent'] = (disk_usage.used / disk_usage.total) * 100
            
            # Network metrics
            if self.config.monitor_network:
                network = psutil.net_io_counters()
                metrics['network_bytes_sent'] = network.bytes_sent
                metrics['network_bytes_recv'] = network.bytes_recv
                metrics['network_packets_sent'] = network.packets_sent
                metrics['network_packets_recv'] = network.packets_recv
            
            # Garbage collection
            try:
                if hasattr(gc, 'get_counts'):
                    gc_counts = gc.get_counts()
                    metrics['gc_gen0'] = gc_counts[0]
                    metrics['gc_gen1'] = gc_counts[1]
                    metrics['gc_gen2'] = gc_counts[2]
                else:
                    # gc.get_counts() was removed in Python 3.12
                    metrics['gc_gen0'] = 0
                    metrics['gc_gen1'] = 0
                    metrics['gc_gen2'] = 0
            except AttributeError:
                metrics['gc_gen0'] = 0
                metrics['gc_gen1'] = 0
                metrics['gc_gen2'] = 0
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
        
        return metrics
    
    def get_monitor_type(self) -> MonitorType:
        """Get monitor type."""
        return MonitorType.SYSTEM


class MemoryMonitor(PerformanceMonitor):
    """Specialized monitor for memory usage tracking."""
    
    def __init__(self, config: MonitorConfig = None):
        """Initialize memory monitor.
        
        Args:
            config (MonitorConfig, optional): Monitor configuration
        """
        super().__init__("memory", config)
        
        # Memory tracking
        self.peak_memory = 0
        self.memory_allocations = 0
        self.gc_collections = 0
        
        # Track initial state
        try:
            self.process = psutil.Process()
            self.initial_memory = self.process.memory_info().rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            self.process = None
            self.initial_memory = 0
    
    def collect_metrics(self) -> Dict[str, Any]:
        """Collect memory metrics.
        
        Returns:
            Dict[str, Any]: Memory metrics
        """
        metrics = {}
        
        try:
            # Process memory
            if self.process:
                memory_info = self.process.memory_info()
                metrics['rss'] = memory_info.rss
                metrics['vms'] = memory_info.vms
                metrics['percent'] = self.process.memory_percent()
                
                # Track peak memory
                self.peak_memory = max(self.peak_memory, memory_info.rss)
                metrics['peak_rss'] = self.peak_memory
                
                # Memory delta from start
                metrics['memory_delta'] = memory_info.rss - self.initial_memory
            
            # System memory
            system_memory = psutil.virtual_memory()
            metrics['system_total'] = system_memory.total
            metrics['system_available'] = system_memory.available
            metrics['system_percent'] = system_memory.percent
            
            # Garbage collection
            try:
                if hasattr(gc, 'get_counts'):
                    gc_counts = gc.get_counts()
                    total_gc = sum(gc_counts)
                    metrics['gc_total'] = total_gc
                    metrics['gc_gen0'] = gc_counts[0]
                    metrics['gc_gen1'] = gc_counts[1]
                    metrics['gc_gen2'] = gc_counts[2]
                else:
                    # gc.get_counts() was removed in Python 3.12
                    total_gc = 0
                    metrics['gc_total'] = 0
                    metrics['gc_gen0'] = 0
                    metrics['gc_gen1'] = 0
                    metrics['gc_gen2'] = 0
            except AttributeError:
                total_gc = 0
                metrics['gc_total'] = 0
                metrics['gc_gen0'] = 0
                metrics['gc_gen1'] = 0
                metrics['gc_gen2'] = 0
            
            # GC delta
            gc_delta = total_gc - self.gc_collections
            self.gc_collections = total_gc
            metrics['gc_delta'] = gc_delta
            
        except Exception as e:
            logger.error(f"Error collecting memory metrics: {e}")
        
        return metrics
    
    def get_monitor_type(self) -> MonitorType:
        """Get monitor type."""
        return MonitorType.MEMORY


class FrameRateMonitor(PerformanceMonitor):
    """Monitor for frame rate and timing metrics."""
    
    def __init__(self, config: MonitorConfig = None):
        """Initialize frame rate monitor.
        
        Args:
            config (MonitorConfig, optional): Monitor configuration
        """
        super().__init__("framerate", config)
        
        # Frame timing
        self.frame_times: deque = deque(maxlen=config.frame_history_size if config else 60)
        self.last_frame_time: Optional[float] = None
        self.frame_count = 0
        
        # Performance tracking
        self.min_frame_time = float('inf')
        self.max_frame_time = 0.0
        self.total_frame_time = 0.0
    
    def record_frame(self) -> None:
        """Record a frame for timing analysis."""
        current_time = time.time()
        
        if self.last_frame_time is not None:
            frame_time = current_time - self.last_frame_time
            self.frame_times.append(frame_time)
            
            # Update statistics
            self.min_frame_time = min(self.min_frame_time, frame_time)
            self.max_frame_time = max(self.max_frame_time, frame_time)
            self.total_frame_time += frame_time
            self.frame_count += 1
        
        self.last_frame_time = current_time
    
    def collect_metrics(self) -> Dict[str, Any]:
        """Collect frame rate metrics.
        
        Returns:
            Dict[str, Any]: Frame rate metrics
        """
        metrics = {}
        
        try:
            if self.frame_times:
                # Current frame rate
                recent_frame_time = sum(self.frame_times) / len(self.frame_times)
                metrics['fps'] = 1.0 / recent_frame_time if recent_frame_time > 0 else 0.0
                metrics['frame_time_ms'] = recent_frame_time * 1000
                
                # Frame time statistics
                frame_times_list = list(self.frame_times)
                metrics['min_frame_time_ms'] = min(frame_times_list) * 1000
                metrics['max_frame_time_ms'] = max(frame_times_list) * 1000
                
                # Frame rate stability
                frame_time_variance = sum((ft - recent_frame_time) ** 2 for ft in frame_times_list) / len(frame_times_list)
                metrics['frame_time_variance'] = frame_time_variance
                metrics['frame_time_std'] = frame_time_variance ** 0.5
                
                # Performance classification
                target_frame_time = 1.0 / self.config.target_fps
                metrics['performance_ratio'] = recent_frame_time / target_frame_time
                
                if metrics['fps'] >= self.config.target_fps * 0.9:
                    metrics['performance_class'] = 'excellent'
                elif metrics['fps'] >= self.config.target_fps * 0.7:
                    metrics['performance_class'] = 'good'
                elif metrics['fps'] >= self.config.target_fps * 0.5:
                    metrics['performance_class'] = 'fair'
                else:
                    metrics['performance_class'] = 'poor'
            
            # Overall statistics
            metrics['total_frames'] = self.frame_count
            if self.frame_count > 0:
                metrics['average_fps'] = self.frame_count / self.total_frame_time if self.total_frame_time > 0 else 0.0
                metrics['min_fps'] = 1.0 / self.max_frame_time if self.max_frame_time > 0 else 0.0
                metrics['max_fps'] = 1.0 / self.min_frame_time if self.min_frame_time < float('inf') else 0.0
            
        except Exception as e:
            logger.error(f"Error collecting frame rate metrics: {e}")
        
        return metrics
    
    def get_monitor_type(self) -> MonitorType:
        """Get monitor type."""
        return MonitorType.FRAME_RATE


class EventMonitor(PerformanceMonitor, EventListener):
    """Monitor for event system performance."""
    
    def __init__(self, event_bus: EventBus = None, config: MonitorConfig = None):
        """Initialize event monitor.
        
        Args:
            event_bus (EventBus, optional): Event bus to monitor
            config (MonitorConfig, optional): Monitor configuration
        """
        PerformanceMonitor.__init__(self, "events", config)
        EventListener.__init__(self, "event_monitor")
        
        self.event_bus = event_bus or get_event_bus()
        
        # Event tracking
        self.event_counts: Dict[str, int] = defaultdict(int)
        self.event_times: Dict[str, List[float]] = defaultdict(list)
        self.total_events = 0
        self.start_time = time.time()
        
        # Register as listener
        if self.config.monitor_events:
            try:
                self.event_bus.register_listener(self)
            except Exception as e:
                logger.warning(f"Could not register event monitor: {e}")
    
    def get_handled_events(self) -> List[str]:
        """Get list of event types this monitor handles.
        
        Returns:
            List[str]: All event types (monitor all events)
        """
        return ["*"]  # Monitor all events
    
    @event_handler("*")
    def handle_event(self, event: Event) -> Any:
        """Handle any event for monitoring.
        
        Args:
            event (Event): Event to monitor
            
        Returns:
            Any: Event handling result
        """
        try:
            event_type = event.event_type
            current_time = time.time()
            
            # Track event counts
            self.event_counts[event_type] += 1
            self.total_events += 1
            
            # Track event timing
            event_times = self.event_times[event_type]
            event_times.append(current_time)
            
            # Keep only recent events
            cutoff_time = current_time - 60.0  # Last minute
            self.event_times[event_type] = [t for t in event_times if t > cutoff_time]
            
        except Exception as e:
            logger.error(f"Error monitoring event {event.event_type}: {e}")
        
        from events import EventResult
        return EventResult.CONTINUE
    
    def collect_metrics(self) -> Dict[str, Any]:
        """Collect event system metrics.
        
        Returns:
            Dict[str, Any]: Event metrics
        """
        metrics = {}
        
        try:
            current_time = time.time()
            uptime = current_time - self.start_time
            
            # Overall event statistics
            metrics['total_events'] = self.total_events
            metrics['events_per_second'] = self.total_events / uptime if uptime > 0 else 0.0
            metrics['unique_event_types'] = len(self.event_counts)
            
            # Recent event rates (last minute)
            recent_events = 0
            for event_times in self.event_times.values():
                recent_events += len(event_times)
            
            metrics['recent_events_per_second'] = recent_events / 60.0
            
            # Top event types
            top_events = sorted(self.event_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            metrics['top_event_types'] = dict(top_events)
            
            # Event distribution
            if self.total_events > 0:
                event_distribution = {}
                for event_type, count in self.event_counts.items():
                    event_distribution[event_type] = (count / self.total_events) * 100
                
                # Top 5 by percentage
                top_distribution = sorted(event_distribution.items(), key=lambda x: x[1], reverse=True)[:5]
                metrics['event_distribution'] = dict(top_distribution)
            
        except Exception as e:
            logger.error(f"Error collecting event metrics: {e}")
        
        return metrics
    
    def get_monitor_type(self) -> MonitorType:
        """Get monitor type."""
        return MonitorType.EVENT


class CustomMonitor(PerformanceMonitor):
    """Monitor for custom application metrics."""
    
    def __init__(self, name: str, config: MonitorConfig = None):
        """Initialize custom monitor.
        
        Args:
            name (str): Monitor name
            config (MonitorConfig, optional): Monitor configuration
        """
        super().__init__(name, config)
        
        # Custom metrics storage
        self.custom_metrics: Dict[str, Any] = {}
        self.metric_callbacks: Dict[str, Callable[[], Any]] = {}
    
    def add_metric(self, name: str, value: Any) -> None:
        """Add a custom metric value.
        
        Args:
            name (str): Metric name
            value (Any): Metric value
        """
        self.custom_metrics[name] = value
    
    def add_metric_callback(self, name: str, callback: Callable[[], Any]) -> None:
        """Add a callback for dynamic metric collection.
        
        Args:
            name (str): Metric name
            callback (Callable): Function that returns the metric value
        """
        self.metric_callbacks[name] = callback
    
    def remove_metric(self, name: str) -> None:
        """Remove a custom metric.
        
        Args:
            name (str): Metric name to remove
        """
        self.custom_metrics.pop(name, None)
        self.metric_callbacks.pop(name, None)
    
    def collect_metrics(self) -> Dict[str, Any]:
        """Collect custom metrics.
        
        Returns:
            Dict[str, Any]: Custom metrics
        """
        metrics = self.custom_metrics.copy()
        
        # Execute callbacks
        for name, callback in self.metric_callbacks.items():
            try:
                metrics[name] = callback()
            except Exception as e:
                logger.error(f"Error executing metric callback {name}: {e}")
                metrics[name] = None
        
        return metrics
    
    def get_monitor_type(self) -> MonitorType:
        """Get monitor type."""
        return MonitorType.CUSTOM
