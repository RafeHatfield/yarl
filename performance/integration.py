"""Integration system for performance profiling with game engine components.

This module provides seamless integration of performance monitoring and profiling
with the existing game engine, systems, and event architecture.
"""

from typing import Any, Dict, List, Optional, Callable, Type
from dataclasses import dataclass
import time
import threading
import logging
from functools import wraps

from engine.system import System
from engine.game_engine import GameEngine
from events import EventBus, get_event_bus, Event, EventListener, event_handler
from state_machine import EnhancedStateManager

from .core import PerformanceProfiler, get_global_profiler, profile_function
from .monitor import (
    PerformanceMonitor, SystemMonitor, MemoryMonitor, FrameRateMonitor, 
    EventMonitor, CustomMonitor, MonitorConfig
)
from .analyzer import PerformanceAnalyzer, StatisticalAnalyzer, TrendAnalyzer, BottleneckDetector

logger = logging.getLogger(__name__)


@dataclass
class ProfilingConfig:
    """Configuration for performance profiling integration."""
    
    # Profiling settings
    enable_profiling: bool = True
    enable_monitoring: bool = True
    enable_analysis: bool = True
    
    # Monitoring configuration
    monitor_config: MonitorConfig = None
    
    # Profiling targets
    profile_systems: bool = True
    profile_events: bool = True
    profile_states: bool = True
    profile_functions: bool = False  # Requires manual decoration
    
    # Analysis settings
    analysis_interval: float = 60.0  # Seconds between analysis runs
    enable_trend_analysis: bool = True
    enable_bottleneck_detection: bool = True
    
    # Performance settings
    async_analysis: bool = True
    max_profiler_results: int = 1000
    max_monitor_samples: int = 300
    
    def __post_init__(self):
        """Initialize default monitor config if not provided."""
        if self.monitor_config is None:
            self.monitor_config = MonitorConfig()


class ProfiledSystem(System):
    """Base class for systems with integrated performance profiling."""
    
    def __init__(self, name: str, priority: int = 50, profiler: PerformanceProfiler = None):
        """Initialize profiled system.
        
        Args:
            name (str): System name
            priority (int): System priority
            profiler (PerformanceProfiler, optional): Profiler instance
        """
        super().__init__(name, priority)
        self.profiler = profiler or get_global_profiler()
        self.profile_enabled = True
        
        # Performance metrics
        self.update_count = 0
        self.total_update_time = 0.0
        self.min_update_time = float('inf')
        self.max_update_time = 0.0
    
    def update(self, dt: float) -> None:
        """Update system with profiling."""
        if not self.profile_enabled:
            return self._update_impl(dt)
        
        with self.profiler.profile(f"system:{self.name}") as ctx:
            ctx.metadata.update({
                'system_name': self.name,
                'system_priority': self.priority,
                'delta_time': dt,
                'update_count': self.update_count,
            })
            
            start_time = time.perf_counter()
            result = self._update_impl(dt)
            end_time = time.perf_counter()
            
            # Update performance metrics
            update_time = end_time - start_time
            self.update_count += 1
            self.total_update_time += update_time
            self.min_update_time = min(self.min_update_time, update_time)
            self.max_update_time = max(self.max_update_time, update_time)
            
            ctx.metadata.update({
                'update_time': update_time,
                'avg_update_time': self.total_update_time / self.update_count,
                'min_update_time': self.min_update_time,
                'max_update_time': self.max_update_time,
            })
            
            return result
    
    def _update_impl(self, dt: float) -> None:
        """Implementation of system update - override in subclasses."""
        pass
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics.
        
        Returns:
            Dict[str, Any]: Performance metrics
        """
        if self.update_count == 0:
            return {'update_count': 0}
        
        return {
            'update_count': self.update_count,
            'total_update_time': self.total_update_time,
            'avg_update_time': self.total_update_time / self.update_count,
            'min_update_time': self.min_update_time,
            'max_update_time': self.max_update_time,
            'updates_per_second': self.update_count / self.total_update_time if self.total_update_time > 0 else 0,
        }
    
    def enable_profiling(self) -> None:
        """Enable profiling for this system."""
        self.profile_enabled = True
    
    def disable_profiling(self) -> None:
        """Disable profiling for this system."""
        self.profile_enabled = False


class SystemProfiler:
    """Profiler for game engine systems."""
    
    def __init__(self, profiler: PerformanceProfiler = None):
        """Initialize system profiler.
        
        Args:
            profiler (PerformanceProfiler, optional): Profiler instance
        """
        self.profiler = profiler or get_global_profiler()
        self.profiled_systems: Dict[str, System] = {}
    
    def profile_system(self, system: System) -> System:
        """Add profiling to a system.
        
        Args:
            system (System): System to profile
            
        Returns:
            System: Profiled system
        """
        if isinstance(system, ProfiledSystem):
            return system  # Already profiled
        
        # Create a wrapper that adds profiling
        original_update = system.update
        
        def profiled_update(dt: float):
            with self.profiler.profile(f"system:{system.name}") as ctx:
                ctx.metadata.update({
                    'system_name': system.name,
                    'system_priority': system.priority,
                    'delta_time': dt,
                })
                return original_update(dt)
        
        system.update = profiled_update
        self.profiled_systems[system.name] = system
        
        logger.debug(f"Added profiling to system: {system.name}")
        return system
    
    def get_system_metrics(self, system_name: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific system.
        
        Args:
            system_name (str): Name of the system
            
        Returns:
            Dict[str, Any]: System metrics, None if not found
        """
        if system_name in self.profiled_systems:
            system = self.profiled_systems[system_name]
            if hasattr(system, 'get_performance_metrics'):
                return system.get_performance_metrics()
        
        return None


class EventProfiler(EventListener):
    """Profiler for event system performance."""
    
    def __init__(self, event_bus: EventBus = None, profiler: PerformanceProfiler = None):
        """Initialize event profiler.
        
        Args:
            event_bus (EventBus, optional): Event bus to profile
            profiler (PerformanceProfiler, optional): Profiler instance
        """
        super().__init__("event_profiler")
        
        self.event_bus = event_bus or get_event_bus()
        self.profiler = profiler or get_global_profiler()
        self.enabled = True
        
        # Event tracking
        self.event_counts: Dict[str, int] = {}
        self.event_times: Dict[str, List[float]] = {}
        
        # Register as listener
        try:
            self.event_bus.register_listener(self)
        except Exception as e:
            logger.warning(f"Could not register event profiler: {e}")
    
    def get_handled_events(self) -> List[str]:
        """Get list of event types this profiler handles.
        
        Returns:
            List[str]: All event types
        """
        return ["*"]  # Profile all events
    
    @event_handler("*")
    def handle_event(self, event: Event) -> Any:
        """Profile event handling.
        
        Args:
            event (Event): Event to profile
            
        Returns:
            Any: Event handling result
        """
        if not self.enabled:
            from events import EventResult
            return EventResult.CONTINUE
        
        event_type = event.event_type
        
        with self.profiler.profile(f"event:{event_type}") as ctx:
            ctx.metadata.update({
                'event_type': event_type,
                'event_source': getattr(event.context, 'source', None),
                'event_priority': getattr(event.context, 'priority', None),
            })
            
            # Track event counts
            self.event_counts[event_type] = self.event_counts.get(event_type, 0) + 1
            
            # Track event timing
            if event_type not in self.event_times:
                self.event_times[event_type] = []
            
            self.event_times[event_type].append(time.time())
            
            # Keep only recent events (last 100 per type)
            if len(self.event_times[event_type]) > 100:
                self.event_times[event_type] = self.event_times[event_type][-100:]
        
        from events import EventResult
        return EventResult.CONTINUE
    
    def get_event_metrics(self) -> Dict[str, Any]:
        """Get event profiling metrics.
        
        Returns:
            Dict[str, Any]: Event metrics
        """
        total_events = sum(self.event_counts.values())
        
        metrics = {
            'total_events': total_events,
            'unique_event_types': len(self.event_counts),
            'event_counts': self.event_counts.copy(),
        }
        
        # Calculate event rates
        current_time = time.time()
        recent_events = {}
        
        for event_type, timestamps in self.event_times.items():
            # Count events in last minute
            recent = [t for t in timestamps if current_time - t < 60.0]
            recent_events[event_type] = len(recent) / 60.0  # Events per second
        
        metrics['event_rates'] = recent_events
        
        return metrics
    
    def enable(self) -> None:
        """Enable event profiling."""
        self.enabled = True
    
    def disable(self) -> None:
        """Disable event profiling."""
        self.enabled = False


class StateProfiler:
    """Profiler for state machine performance."""
    
    def __init__(self, state_manager: EnhancedStateManager = None, 
                 profiler: PerformanceProfiler = None):
        """Initialize state profiler.
        
        Args:
            state_manager (EnhancedStateManager, optional): State manager to profile
            profiler (PerformanceProfiler, optional): Profiler instance
        """
        self.state_manager = state_manager
        self.profiler = profiler or get_global_profiler()
        self.enabled = True
        
        # State tracking
        self.state_durations: Dict[str, List[float]] = {}
        self.transition_counts: Dict[str, int] = {}
        
        if self.state_manager:
            self._integrate_with_state_manager()
    
    def _integrate_with_state_manager(self) -> None:
        """Integrate profiling with state manager."""
        # Add transition callback
        def profile_transition(from_state: str, to_state: str, context):
            transition_key = f"{from_state}->{to_state}"
            
            with self.profiler.profile(f"state_transition:{transition_key}") as ctx:
                ctx.metadata.update({
                    'from_state': from_state,
                    'to_state': to_state,
                    'transition_key': transition_key,
                })
                
                # Track transition counts
                self.transition_counts[transition_key] = self.transition_counts.get(transition_key, 0) + 1
        
        self.state_manager.add_transition_callback(profile_transition)
    
    def get_state_metrics(self) -> Dict[str, Any]:
        """Get state profiling metrics.
        
        Returns:
            Dict[str, Any]: State metrics
        """
        metrics = {
            'transition_counts': self.transition_counts.copy(),
            'total_transitions': sum(self.transition_counts.values()),
        }
        
        if self.state_manager:
            metrics.update({
                'current_state': self.state_manager.get_current_state_id(),
                'state_history_length': len(self.state_manager.get_state_history()),
                'performance_stats': self.state_manager.get_performance_stats(),
            })
        
        return metrics


class GameEngineProfiler:
    """Main profiler integration for the game engine."""
    
    def __init__(self, config: ProfilingConfig = None):
        """Initialize game engine profiler.
        
        Args:
            config (ProfilingConfig, optional): Profiling configuration
        """
        self.config = config or ProfilingConfig()
        
        # Core components
        self.profiler = get_global_profiler()
        self.monitors: Dict[str, PerformanceMonitor] = {}
        self.analyzers: List[PerformanceAnalyzer] = []
        
        # Integration components
        self.system_profiler = SystemProfiler(self.profiler)
        self.event_profiler: Optional[EventProfiler] = None
        self.state_profiler: Optional[StateProfiler] = None
        
        # Monitoring thread
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_active = False
        
        # Analysis thread
        self.analysis_thread: Optional[threading.Thread] = None
        self.analysis_active = False
        
        self._initialize_components()
    
    def _initialize_components(self) -> None:
        """Initialize profiling components."""
        # Initialize monitors
        if self.config.enable_monitoring:
            self.monitors['system'] = SystemMonitor(self.config.monitor_config)
            self.monitors['memory'] = MemoryMonitor(self.config.monitor_config)
            self.monitors['framerate'] = FrameRateMonitor(self.config.monitor_config)
            
            if self.config.monitor_config.monitor_events:
                self.monitors['events'] = EventMonitor(config=self.config.monitor_config)
        
        # Initialize analyzers
        if self.config.enable_analysis:
            self.analyzers.append(StatisticalAnalyzer())
            
            if self.config.enable_trend_analysis:
                self.analyzers.append(TrendAnalyzer())
            
            if self.config.enable_bottleneck_detection:
                self.analyzers.append(BottleneckDetector())
        
        # Initialize event profiler
        if self.config.profile_events:
            self.event_profiler = EventProfiler(profiler=self.profiler)
    
    def integrate_with_engine(self, engine: GameEngine) -> None:
        """Integrate profiling with a game engine.
        
        Args:
            engine (GameEngine): Game engine to profile
        """
        logger.info("Integrating performance profiling with game engine")
        
        # Profile existing systems
        if self.config.profile_systems:
            for system_name, system in engine.systems.items():
                self.system_profiler.profile_system(system)
        
        # Add custom monitor for engine metrics
        engine_monitor = CustomMonitor("engine", self.config.monitor_config)
        
        # Add engine-specific metrics
        engine_monitor.add_metric_callback("system_count", lambda: len(engine.systems))
        engine_monitor.add_metric_callback("target_fps", lambda: engine.target_fps)
        engine_monitor.add_metric_callback("delta_time", lambda: engine.delta_time)
        engine_monitor.add_metric_callback("running", lambda: engine.running)
        
        self.monitors['engine'] = engine_monitor
        
        # Start monitoring if configured
        if self.config.enable_monitoring:
            self.start_monitoring()
        
        # Start analysis if configured
        if self.config.enable_analysis:
            self.start_analysis()
    
    def integrate_with_state_manager(self, state_manager: EnhancedStateManager) -> None:
        """Integrate profiling with state manager.
        
        Args:
            state_manager (EnhancedStateManager): State manager to profile
        """
        if self.config.profile_states:
            self.state_profiler = StateProfiler(state_manager, self.profiler)
            logger.info("Integrated performance profiling with state manager")
    
    def start_monitoring(self) -> None:
        """Start performance monitoring."""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        if self.config.monitor_config.async_monitoring:
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            logger.info("Started asynchronous performance monitoring")
        else:
            logger.info("Performance monitoring enabled (synchronous)")
    
    def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        self.monitoring_active = False
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=1.0)
            logger.info("Stopped performance monitoring")
    
    def start_analysis(self) -> None:
        """Start performance analysis."""
        if self.analysis_active:
            return
        
        self.analysis_active = True
        
        if self.config.async_analysis:
            self.analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
            self.analysis_thread.start()
            logger.info("Started asynchronous performance analysis")
        else:
            logger.info("Performance analysis enabled (synchronous)")
    
    def stop_analysis(self) -> None:
        """Stop performance analysis."""
        self.analysis_active = False
        
        if self.analysis_thread and self.analysis_thread.is_alive():
            self.analysis_thread.join(timeout=1.0)
            logger.info("Stopped performance analysis")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                # Sample all monitors
                for monitor in self.monitors.values():
                    if monitor.is_enabled():
                        monitor.sample()
                
                # Record frame for frame rate monitor
                if 'framerate' in self.monitors:
                    self.monitors['framerate'].record_frame()
                
                # Sleep until next sample
                time.sleep(self.config.monitor_config.sample_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(1.0)  # Prevent tight error loop
    
    def _analysis_loop(self) -> None:
        """Main analysis loop."""
        while self.analysis_active:
            try:
                # Collect data for analysis
                profiler_results = self.profiler.get_results(limit=self.config.max_profiler_results)
                monitor_results = []
                
                for monitor in self.monitors.values():
                    monitor_results.extend(monitor.get_history(limit=self.config.max_monitor_samples))
                
                # Run analyzers
                all_data = profiler_results + monitor_results
                
                for analyzer in self.analyzers:
                    if analyzer.is_enabled():
                        try:
                            analysis_results = analyzer.analyze(all_data)
                            
                            # Log significant findings
                            for result in analysis_results:
                                if result.severity.value >= 3:  # MEDIUM or higher
                                    logger.warning(f"Performance issue detected: {result.title}")
                        
                        except Exception as e:
                            logger.error(f"Error in analyzer {analyzer.name}: {e}")
                
                # Sleep until next analysis
                time.sleep(self.config.analysis_interval)
                
            except Exception as e:
                logger.error(f"Error in analysis loop: {e}")
                time.sleep(10.0)  # Prevent tight error loop
    
    def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics.
        
        Returns:
            Dict[str, Any]: All performance metrics
        """
        metrics = {
            'timestamp': time.time(),
            'profiler_stats': self.profiler.get_stats(),
            'monitor_metrics': {},
            'system_metrics': {},
            'event_metrics': {},
            'state_metrics': {},
        }
        
        # Collect monitor metrics
        for name, monitor in self.monitors.items():
            metrics['monitor_metrics'][name] = monitor.get_current_metrics()
        
        # Collect system metrics
        for system_name in self.system_profiler.profiled_systems:
            system_metrics = self.system_profiler.get_system_metrics(system_name)
            if system_metrics:
                metrics['system_metrics'][system_name] = system_metrics
        
        # Collect event metrics
        if self.event_profiler:
            metrics['event_metrics'] = self.event_profiler.get_event_metrics()
        
        # Collect state metrics
        if self.state_profiler:
            metrics['state_metrics'] = self.state_profiler.get_state_metrics()
        
        return metrics
    
    def shutdown(self) -> None:
        """Shutdown the profiler and clean up resources."""
        logger.info("Shutting down performance profiler")
        
        self.stop_monitoring()
        self.stop_analysis()
        
        # Clear profiler results
        self.profiler.clear_results()
        
        # Clear monitor history
        for monitor in self.monitors.values():
            monitor.clear_history()


def integrate_profiling(engine: GameEngine, state_manager: EnhancedStateManager = None,
                       config: ProfilingConfig = None) -> GameEngineProfiler:
    """Integrate performance profiling with game engine components.
    
    Args:
        engine (GameEngine): Game engine to profile
        state_manager (EnhancedStateManager, optional): State manager to profile
        config (ProfilingConfig, optional): Profiling configuration
        
    Returns:
        GameEngineProfiler: Configured profiler instance
    """
    profiler = GameEngineProfiler(config)
    
    profiler.integrate_with_engine(engine)
    
    if state_manager:
        profiler.integrate_with_state_manager(state_manager)
    
    logger.info("Performance profiling integration complete")
    return profiler


def profile_system_method(method_name: str = None):
    """Decorator for profiling system methods.
    
    Args:
        method_name (str, optional): Custom name for the profile
        
    Returns:
        Callable: Decorated method
    """
    def decorator(method):
        profile_name = method_name or f"method:{method.__name__}"
        
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            if hasattr(self, 'profiler') and hasattr(self, 'profile_enabled') and self.profile_enabled:
                with self.profiler.profile(profile_name) as ctx:
                    ctx.metadata.update({
                        'system_name': getattr(self, 'name', 'unknown'),
                        'method_name': method.__name__,
                    })
                    return method(self, *args, **kwargs)
            else:
                return method(self, *args, **kwargs)
        
        return wrapper
    return decorator
