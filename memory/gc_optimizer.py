"""Garbage collection optimization and tuning system.

This module provides tools for optimizing Python's garbage collection
to reduce GC pressure and improve game performance.
"""

from typing import Any, Dict, List, Optional, Tuple, Callable, ContextManager
from dataclasses import dataclass
from enum import Enum, auto
import time
import threading
import logging
import gc
import contextlib
from collections import deque

logger = logging.getLogger(__name__)


class GCMode(Enum):
    """Garbage collection optimization modes."""
    
    DISABLED = auto()       # Disable automatic GC
    CONSERVATIVE = auto()   # Conservative GC settings
    BALANCED = auto()       # Balanced performance/memory
    AGGRESSIVE = auto()     # Aggressive memory reclamation
    CUSTOM = auto()         # Custom settings


@dataclass
class GCConfig:
    """Configuration for garbage collection optimization."""
    
    # GC mode
    mode: GCMode = GCMode.BALANCED
    
    # Generation thresholds
    threshold_0: int = 700      # Gen 0 threshold
    threshold_1: int = 10       # Gen 1 threshold  
    threshold_2: int = 10       # Gen 2 threshold
    
    # Collection intervals
    manual_collect_interval: float = 30.0  # Manual collection interval
    full_collect_interval: float = 300.0   # Full collection interval
    
    # Performance settings
    disable_during_critical: bool = True    # Disable GC during critical sections
    collect_on_memory_pressure: bool = True # Collect when memory pressure is high
    
    # Monitoring
    track_collections: bool = True          # Track GC statistics
    log_collections: bool = False           # Log GC events


@dataclass
class GCStats:
    """Garbage collection statistics."""
    
    # Collection counts
    collections_gen0: int = 0
    collections_gen1: int = 0
    collections_gen2: int = 0
    manual_collections: int = 0
    
    # Timing statistics
    total_gc_time_ms: float = 0.0
    average_gc_time_ms: float = 0.0
    max_gc_time_ms: float = 0.0
    
    # Object statistics
    objects_collected: int = 0
    objects_uncollectable: int = 0
    
    # Memory statistics
    memory_freed_mb: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            'collections_gen0': self.collections_gen0,
            'collections_gen1': self.collections_gen1,
            'collections_gen2': self.collections_gen2,
            'manual_collections': self.manual_collections,
            'total_collections': self.total_collections,
            'total_gc_time_ms': self.total_gc_time_ms,
            'average_gc_time_ms': self.average_gc_time_ms,
            'max_gc_time_ms': self.max_gc_time_ms,
            'objects_collected': self.objects_collected,
            'objects_uncollectable': self.objects_uncollectable,
            'memory_freed_mb': self.memory_freed_mb,
        }
    
    @property
    def total_collections(self) -> int:
        """Get total number of collections."""
        return (self.collections_gen0 + self.collections_gen1 + 
                self.collections_gen2 + self.manual_collections)


class GCOptimizer:
    """Garbage collection optimizer with automatic tuning."""
    
    def __init__(self, config: GCConfig = None):
        """Initialize GC optimizer.
        
        Args:
            config (GCConfig, optional): GC configuration
        """
        self.config = config or GCConfig()
        self.stats = GCStats()
        
        # State tracking
        self.original_thresholds: Optional[Tuple[int, int, int]] = None
        self.gc_disabled_count = 0
        self.last_manual_collect = 0.0
        self.last_full_collect = 0.0
        
        # Performance tracking
        self.gc_times: deque = deque(maxlen=100)  # Keep last 100 GC times
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Optimization thread
        self._optimizer_thread: Optional[threading.Thread] = None
        self._optimizer_active = False
        
        # Apply initial configuration
        self._apply_gc_config()
    
    def _apply_gc_config(self) -> None:
        """Apply GC configuration."""
        with self._lock:
            # Store original thresholds if not already stored
            if self.original_thresholds is None:
                try:
                    self.original_thresholds = gc.get_threshold()
                except AttributeError:
                    # Python 3.12+ might not have get_threshold
                    self.original_thresholds = (700, 10, 10)
            
            # Apply mode-specific settings
            if self.config.mode == GCMode.DISABLED:
                gc.disable()
                logger.info("Garbage collection disabled")
            
            elif self.config.mode == GCMode.CONSERVATIVE:
                gc.enable()
                # Use larger thresholds to reduce GC frequency
                self._set_thresholds(1000, 15, 15)
                logger.info("Conservative GC mode enabled")
            
            elif self.config.mode == GCMode.BALANCED:
                gc.enable()
                # Use default-ish thresholds
                self._set_thresholds(700, 10, 10)
                logger.info("Balanced GC mode enabled")
            
            elif self.config.mode == GCMode.AGGRESSIVE:
                gc.enable()
                # Use smaller thresholds for frequent collection
                self._set_thresholds(400, 5, 5)
                logger.info("Aggressive GC mode enabled")
            
            elif self.config.mode == GCMode.CUSTOM:
                gc.enable()
                self._set_thresholds(
                    self.config.threshold_0,
                    self.config.threshold_1,
                    self.config.threshold_2
                )
                logger.info(f"Custom GC mode enabled: {self.config.threshold_0}, "
                           f"{self.config.threshold_1}, {self.config.threshold_2}")
    
    def _set_thresholds(self, gen0: int, gen1: int, gen2: int) -> None:
        """Set GC thresholds safely.
        
        Args:
            gen0 (int): Generation 0 threshold
            gen1 (int): Generation 1 threshold
            gen2 (int): Generation 2 threshold
        """
        try:
            gc.set_threshold(gen0, gen1, gen2)
        except AttributeError:
            # Python 3.12+ might not have set_threshold
            logger.debug("GC threshold setting not available in this Python version")
    
    def start_optimization(self) -> None:
        """Start automatic GC optimization."""
        if self._optimizer_active:
            return
        
        self._optimizer_active = True
        self._optimizer_thread = threading.Thread(target=self._optimization_loop, daemon=True)
        self._optimizer_thread.start()
        logger.info("GC optimization started")
    
    def stop_optimization(self) -> None:
        """Stop automatic GC optimization."""
        self._optimizer_active = False
        if self._optimizer_thread and self._optimizer_thread.is_alive():
            self._optimizer_thread.join(timeout=1.0)
        logger.info("GC optimization stopped")
    
    def _optimization_loop(self) -> None:
        """Main optimization loop."""
        while self._optimizer_active:
            try:
                current_time = time.time()
                
                # Manual collection if interval elapsed
                if (self.config.manual_collect_interval > 0 and
                    current_time - self.last_manual_collect >= self.config.manual_collect_interval):
                    self.collect_generation(0)
                    self.last_manual_collect = current_time
                
                # Full collection if interval elapsed
                if (self.config.full_collect_interval > 0 and
                    current_time - self.last_full_collect >= self.config.full_collect_interval):
                    self.collect_all_generations()
                    self.last_full_collect = current_time
                
                # Sleep for a short interval
                time.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Error in GC optimization loop: {e}")
                time.sleep(1.0)
    
    def collect_generation(self, generation: int = 0) -> Dict[str, Any]:
        """Manually collect a specific generation.
        
        Args:
            generation (int): Generation to collect (0, 1, or 2)
            
        Returns:
            Dict[str, Any]: Collection results
        """
        with self._lock:
            if not gc.isenabled():
                return {'collected': 0, 'time_ms': 0.0, 'generation': generation}
            
            start_time = time.time()
            
            try:
                # Collect the specified generation
                collected = gc.collect(generation)
                
                end_time = time.time()
                gc_time_ms = (end_time - start_time) * 1000
                
                # Update statistics
                self._update_collection_stats(generation, collected, gc_time_ms)
                
                if self.config.log_collections:
                    logger.info(f"GC generation {generation}: collected {collected} objects "
                               f"in {gc_time_ms:.2f}ms")
                
                return {
                    'collected': collected,
                    'time_ms': gc_time_ms,
                    'generation': generation
                }
                
            except Exception as e:
                logger.error(f"Error during GC collection: {e}")
                return {'collected': 0, 'time_ms': 0.0, 'generation': generation, 'error': str(e)}
    
    def collect_all_generations(self) -> Dict[str, Any]:
        """Collect all generations.
        
        Returns:
            Dict[str, Any]: Collection results
        """
        with self._lock:
            if not gc.isenabled():
                return {'total_collected': 0, 'total_time_ms': 0.0}
            
            start_time = time.time()
            total_collected = 0
            
            try:
                # Collect all generations
                for generation in range(3):
                    collected = gc.collect(generation)
                    total_collected += collected
                
                end_time = time.time()
                total_time_ms = (end_time - start_time) * 1000
                
                # Update statistics
                self.stats.manual_collections += 1
                self.stats.total_gc_time_ms += total_time_ms
                self.stats.objects_collected += total_collected
                
                # Update timing statistics
                self.gc_times.append(total_time_ms)
                if len(self.gc_times) > 0:
                    self.stats.average_gc_time_ms = sum(self.gc_times) / len(self.gc_times)
                    self.stats.max_gc_time_ms = max(self.stats.max_gc_time_ms, total_time_ms)
                
                if self.config.log_collections:
                    logger.info(f"Full GC: collected {total_collected} objects "
                               f"in {total_time_ms:.2f}ms")
                
                return {
                    'total_collected': total_collected,
                    'total_time_ms': total_time_ms
                }
                
            except Exception as e:
                logger.error(f"Error during full GC collection: {e}")
                return {'total_collected': 0, 'total_time_ms': 0.0, 'error': str(e)}
    
    def _update_collection_stats(self, generation: int, collected: int, time_ms: float) -> None:
        """Update collection statistics.
        
        Args:
            generation (int): Generation that was collected
            collected (int): Number of objects collected
            time_ms (float): Collection time in milliseconds
        """
        # Update generation-specific counts
        if generation == 0:
            self.stats.collections_gen0 += 1
        elif generation == 1:
            self.stats.collections_gen1 += 1
        elif generation == 2:
            self.stats.collections_gen2 += 1
        
        # Update general statistics
        self.stats.objects_collected += collected
        self.stats.total_gc_time_ms += time_ms
        
        # Update timing statistics
        self.gc_times.append(time_ms)
        if len(self.gc_times) > 0:
            self.stats.average_gc_time_ms = sum(self.gc_times) / len(self.gc_times)
            self.stats.max_gc_time_ms = max(self.stats.max_gc_time_ms, time_ms)
    
    def disable_gc(self) -> None:
        """Temporarily disable garbage collection."""
        with self._lock:
            if gc.isenabled():
                gc.disable()
                self.gc_disabled_count += 1
                logger.debug("GC temporarily disabled")
    
    def enable_gc(self) -> None:
        """Re-enable garbage collection."""
        with self._lock:
            if self.gc_disabled_count > 0:
                self.gc_disabled_count -= 1
                
                if self.gc_disabled_count == 0 and self.config.mode != GCMode.DISABLED:
                    gc.enable()
                    logger.debug("GC re-enabled")
    
    def get_gc_info(self) -> Dict[str, Any]:
        """Get current GC information.
        
        Returns:
            Dict[str, Any]: GC information
        """
        with self._lock:
            info = {
                'enabled': gc.isenabled(),
                'mode': self.config.mode.name,
                'disabled_count': self.gc_disabled_count,
            }
            
            # Add threshold information if available
            try:
                thresholds = gc.get_threshold()
                info['thresholds'] = thresholds
            except AttributeError:
                info['thresholds'] = None
            
            # Add count information if available
            try:
                if hasattr(gc, 'get_counts'):
                    counts = gc.get_counts()
                    info['counts'] = counts
                else:
                    info['counts'] = None
            except AttributeError:
                info['counts'] = None
            
            return info
    
    def get_stats(self) -> GCStats:
        """Get GC statistics.
        
        Returns:
            GCStats: Current GC statistics
        """
        with self._lock:
            return self.stats
    
    def reset_stats(self) -> None:
        """Reset GC statistics."""
        with self._lock:
            self.stats = GCStats()
            self.gc_times.clear()
            logger.info("GC statistics reset")
    
    def restore_original_settings(self) -> None:
        """Restore original GC settings."""
        with self._lock:
            if self.original_thresholds:
                self._set_thresholds(*self.original_thresholds)
            
            gc.enable()
            self.gc_disabled_count = 0
            logger.info("Original GC settings restored")
    
    def shutdown(self) -> None:
        """Shutdown GC optimizer."""
        self.stop_optimization()
        self.restore_original_settings()
        logger.info("GC optimizer shutdown complete")


@contextlib.contextmanager
def disable_gc_during() -> ContextManager[None]:
    """Context manager to disable GC during critical sections.
    
    Yields:
        None
    """
    gc_was_enabled = gc.isenabled()
    
    try:
        if gc_was_enabled:
            gc.disable()
        yield
    finally:
        if gc_was_enabled:
            gc.enable()


def gc_collect_if_needed(memory_threshold_mb: float = 100.0) -> bool:
    """Collect garbage if memory usage exceeds threshold.
    
    Args:
        memory_threshold_mb (float): Memory threshold in MB
        
    Returns:
        bool: True if collection was performed
    """
    try:
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / (1024 * 1024)
        
        if memory_mb > memory_threshold_mb:
            gc.collect()
            logger.debug(f"GC collection triggered by memory threshold: {memory_mb:.1f}MB")
            return True
            
    except ImportError:
        # psutil not available, can't check memory
        pass
    except Exception as e:
        logger.debug(f"Error checking memory for GC: {e}")
    
    return False


def optimize_gc_settings(mode: GCMode = GCMode.BALANCED) -> GCOptimizer:
    """Optimize GC settings for the specified mode.
    
    Args:
        mode (GCMode): GC optimization mode
        
    Returns:
        GCOptimizer: Configured GC optimizer
    """
    config = GCConfig(mode=mode)
    optimizer = GCOptimizer(config)
    optimizer.start_optimization()
    
    logger.info(f"GC settings optimized for {mode.name} mode")
    return optimizer


# Global GC optimizer instance
_global_gc_optimizer: Optional[GCOptimizer] = None


def get_gc_optimizer() -> Optional[GCOptimizer]:
    """Get the global GC optimizer instance.
    
    Returns:
        GCOptimizer: Global GC optimizer or None if not initialized
    """
    return _global_gc_optimizer


def initialize_gc_optimizer(config: GCConfig = None) -> GCOptimizer:
    """Initialize the global GC optimizer.
    
    Args:
        config (GCConfig, optional): GC configuration
        
    Returns:
        GCOptimizer: Initialized GC optimizer
    """
    global _global_gc_optimizer
    _global_gc_optimizer = GCOptimizer(config)
    return _global_gc_optimizer


def shutdown_gc_optimizer() -> None:
    """Shutdown the global GC optimizer."""
    global _global_gc_optimizer
    if _global_gc_optimizer:
        _global_gc_optimizer.shutdown()
        _global_gc_optimizer = None
