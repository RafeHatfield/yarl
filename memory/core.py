"""Core memory management and object pooling components.

This module provides the fundamental infrastructure for memory optimization
including object pools, memory managers, and poolable object interfaces.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
import threading
import time
import logging
import weakref
from collections import deque, defaultdict

logger = logging.getLogger(__name__)

T = TypeVar('T')


class PoolStrategy(Enum):
    """Strategies for object pool management."""
    
    FIXED_SIZE = auto()      # Fixed pool size, fail when exhausted
    DYNAMIC = auto()         # Grow pool as needed
    BOUNDED_DYNAMIC = auto() # Grow up to maximum size
    LAZY_CLEANUP = auto()    # Clean up unused objects periodically


@dataclass
class MemoryConfig:
    """Configuration for memory management."""
    
    # Object pooling
    enable_pooling: bool = True
    default_pool_size: int = 100
    max_pool_size: int = 1000
    pool_strategy: PoolStrategy = PoolStrategy.BOUNDED_DYNAMIC
    
    # Caching
    enable_caching: bool = True
    default_cache_size: int = 256
    cache_ttl_seconds: float = 300.0  # 5 minutes
    
    # Memory profiling
    enable_profiling: bool = True
    profile_interval: float = 60.0    # 1 minute
    track_allocations: bool = False   # Expensive, only for debugging
    
    # Garbage collection
    optimize_gc: bool = True
    gc_threshold_0: int = 700         # Default Python values
    gc_threshold_1: int = 10
    gc_threshold_2: int = 10
    
    # Cleanup
    cleanup_interval: float = 30.0    # 30 seconds
    max_unused_time: float = 300.0    # 5 minutes


@dataclass
class MemoryStats:
    """Memory usage statistics."""
    
    # Pool statistics
    total_pools: int = 0
    total_pooled_objects: int = 0
    pool_hit_rate: float = 0.0
    pool_miss_count: int = 0
    
    # Cache statistics
    total_caches: int = 0
    cache_hit_rate: float = 0.0
    cache_memory_usage: int = 0
    
    # Memory statistics
    current_memory_mb: float = 0.0
    peak_memory_mb: float = 0.0
    gc_collections: int = 0
    
    # Performance statistics
    allocation_time_saved_ms: float = 0.0
    cleanup_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            'total_pools': self.total_pools,
            'total_pooled_objects': self.total_pooled_objects,
            'pool_hit_rate': self.pool_hit_rate,
            'pool_miss_count': self.pool_miss_count,
            'total_caches': self.total_caches,
            'cache_hit_rate': self.cache_hit_rate,
            'cache_memory_usage': self.cache_memory_usage,
            'current_memory_mb': self.current_memory_mb,
            'peak_memory_mb': self.peak_memory_mb,
            'gc_collections': self.gc_collections,
            'allocation_time_saved_ms': self.allocation_time_saved_ms,
            'cleanup_time_ms': self.cleanup_time_ms,
        }


class PoolableObject(ABC):
    """Interface for objects that can be pooled."""
    
    @abstractmethod
    def reset(self) -> None:
        """Reset object to initial state for reuse."""
        pass
    
    def on_acquire(self) -> None:
        """Called when object is acquired from pool."""
        pass
    
    def on_release(self) -> None:
        """Called when object is released back to pool."""
        pass
    
    def can_be_pooled(self) -> bool:
        """Check if object can be safely pooled."""
        return True


class PooledObject:
    """Wrapper for pooled objects with automatic lifecycle management."""
    
    def __init__(self, obj: Any, pool: 'ObjectPool'):
        """Initialize pooled object wrapper.
        
        Args:
            obj (Any): The wrapped object
            pool (ObjectPool): Pool that owns this object
        """
        self._obj = obj
        self._pool = pool
        self._acquired = True
        self._acquisition_time = time.time()
    
    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to wrapped object."""
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        return getattr(self._obj, name)
    
    def __enter__(self):
        """Context manager entry."""
        return self._obj
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically release object."""
        self.release()
    
    def release(self) -> None:
        """Release object back to pool."""
        if self._acquired:
            self._acquired = False
            self._pool._release_object(self._obj)
    
    def get_wrapped_object(self) -> Any:
        """Get the wrapped object directly."""
        return self._obj
    
    def is_acquired(self) -> bool:
        """Check if object is currently acquired."""
        return self._acquired
    
    def get_acquisition_time(self) -> float:
        """Get time when object was acquired."""
        return self._acquisition_time


class ObjectPool(Generic[T]):
    """High-performance object pool with automatic lifecycle management."""
    
    def __init__(self, object_class: Type[T], initial_size: int = 10,
                 max_size: int = 100, strategy: PoolStrategy = PoolStrategy.BOUNDED_DYNAMIC,
                 factory: Optional[Callable[[], T]] = None):
        """Initialize object pool.
        
        Args:
            object_class (Type[T]): Class of objects to pool
            initial_size (int): Initial pool size
            max_size (int): Maximum pool size
            strategy (PoolStrategy): Pool management strategy
            factory (Callable, optional): Custom object factory function
        """
        self.object_class = object_class
        self.initial_size = initial_size
        self.max_size = max_size
        self.strategy = strategy
        self.factory = factory or (lambda: object_class())
        
        # Pool storage
        self._available: deque = deque()
        self._acquired: weakref.WeakSet = weakref.WeakSet()
        
        # Statistics
        self.stats = {
            'created': 0,
            'acquired': 0,
            'released': 0,
            'hits': 0,
            'misses': 0,
            'peak_size': 0,
        }
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Initialize pool
        self._initialize_pool()
    
    def _initialize_pool(self) -> None:
        """Initialize pool with initial objects."""
        with self._lock:
            for _ in range(self.initial_size):
                obj = self._create_object()
                self._available.append(obj)
    
    def _create_object(self) -> T:
        """Create a new object for the pool."""
        try:
            obj = self.factory()
            self.stats['created'] += 1
            return obj
        except Exception as e:
            logger.error(f"Failed to create object for pool {self.object_class.__name__}: {e}")
            raise
    
    def acquire(self, auto_release: bool = False) -> T:
        """Acquire an object from the pool.
        
        Args:
            auto_release (bool): Whether to wrap in PooledObject for auto-release
            
        Returns:
            T: Object from pool (wrapped if auto_release=True)
        """
        with self._lock:
            obj = None
            
            # Try to get from available objects
            if self._available:
                obj = self._available.popleft()
                self.stats['hits'] += 1
            else:
                # Pool is empty, handle based on strategy
                if self.strategy == PoolStrategy.FIXED_SIZE:
                    raise RuntimeError(f"Pool {self.object_class.__name__} is exhausted")
                elif self.strategy in (PoolStrategy.DYNAMIC, PoolStrategy.BOUNDED_DYNAMIC):
                    if (self.strategy == PoolStrategy.BOUNDED_DYNAMIC and 
                        self.stats['created'] >= self.max_size):
                        raise RuntimeError(f"Pool {self.object_class.__name__} reached maximum size")
                    
                    obj = self._create_object()
                    self.stats['misses'] += 1
            
            if obj is None:
                raise RuntimeError(f"Failed to acquire object from pool {self.object_class.__name__}")
            
            # Reset object if it's poolable
            if isinstance(obj, PoolableObject):
                obj.reset()
                obj.on_acquire()
            
            # Track acquisition
            self._acquired.add(obj)
            self.stats['acquired'] += 1
            
            # Update peak size
            current_size = len(self._available) + len(self._acquired)
            self.stats['peak_size'] = max(self.stats['peak_size'], current_size)
            
            # Return wrapped object if auto-release requested
            if auto_release:
                return PooledObject(obj, self)
            else:
                return obj
    
    def release(self, obj: T) -> None:
        """Release an object back to the pool.
        
        Args:
            obj (T): Object to release
        """
        self._release_object(obj)
    
    def _release_object(self, obj: T) -> None:
        """Internal method to release object back to pool."""
        with self._lock:
            if obj not in self._acquired:
                logger.warning(f"Attempting to release object not acquired from pool {self.object_class.__name__}")
                return
            
            # Remove from acquired set
            self._acquired.discard(obj)
            
            # Call release callback if poolable
            if isinstance(obj, PoolableObject):
                obj.on_release()
                
                # Check if object can still be pooled
                if not obj.can_be_pooled():
                    logger.debug(f"Object {obj} cannot be pooled, discarding")
                    return
            
            # Return to available pool if there's space
            if len(self._available) < self.max_size:
                self._available.append(obj)
                self.stats['released'] += 1
            else:
                # Pool is full, discard object
                logger.debug(f"Pool {self.object_class.__name__} is full, discarding object")
    
    def clear(self) -> None:
        """Clear all objects from the pool."""
        with self._lock:
            self._available.clear()
            # Note: We can't clear _acquired as those objects are still in use
            logger.info(f"Cleared pool {self.object_class.__name__}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics.
        
        Returns:
            Dict[str, Any]: Pool statistics
        """
        with self._lock:
            stats = self.stats.copy()
            stats.update({
                'available_count': len(self._available),
                'acquired_count': len(self._acquired),
                'total_count': len(self._available) + len(self._acquired),
                'hit_rate': (stats['hits'] / (stats['hits'] + stats['misses'])) * 100 
                           if (stats['hits'] + stats['misses']) > 0 else 0.0,
                'object_class': self.object_class.__name__,
                'strategy': self.strategy.name,
                'max_size': self.max_size,
            })
            return stats
    
    def resize(self, new_size: int) -> None:
        """Resize the pool.
        
        Args:
            new_size (int): New maximum pool size
        """
        with self._lock:
            old_size = self.max_size
            self.max_size = new_size
            
            # If shrinking, remove excess objects
            if new_size < old_size:
                while len(self._available) > new_size:
                    self._available.pop()
            
            logger.info(f"Resized pool {self.object_class.__name__} from {old_size} to {new_size}")
    
    def __len__(self) -> int:
        """Get total number of objects in pool."""
        with self._lock:
            return len(self._available) + len(self._acquired)
    
    def __repr__(self) -> str:
        """String representation of pool."""
        return (f"ObjectPool({self.object_class.__name__}, "
                f"available={len(self._available)}, "
                f"acquired={len(self._acquired)}, "
                f"max_size={self.max_size})")


class PoolManager:
    """Manages multiple object pools with centralized configuration."""
    
    def __init__(self, config: MemoryConfig = None):
        """Initialize pool manager.
        
        Args:
            config (MemoryConfig, optional): Memory configuration
        """
        self.config = config or MemoryConfig()
        self.pools: Dict[str, ObjectPool] = {}
        self.pool_configs: Dict[str, Dict[str, Any]] = {}
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Cleanup thread
        self._cleanup_thread: Optional[threading.Thread] = None
        self._cleanup_active = False
        
        if self.config.cleanup_interval > 0:
            self._start_cleanup_thread()
    
    def create_pool(self, name: str, object_class: Type[T], 
                   initial_size: Optional[int] = None,
                   max_size: Optional[int] = None,
                   strategy: Optional[PoolStrategy] = None,
                   factory: Optional[Callable[[], T]] = None) -> ObjectPool[T]:
        """Create a new object pool.
        
        Args:
            name (str): Pool name
            object_class (Type[T]): Class of objects to pool
            initial_size (int, optional): Initial pool size
            max_size (int, optional): Maximum pool size
            strategy (PoolStrategy, optional): Pool strategy
            factory (Callable, optional): Custom object factory
            
        Returns:
            ObjectPool[T]: Created pool
        """
        with self._lock:
            if name in self.pools:
                raise ValueError(f"Pool {name} already exists")
            
            # Use config defaults if not specified
            initial_size = initial_size or self.config.default_pool_size
            max_size = max_size or self.config.max_pool_size
            strategy = strategy or self.config.pool_strategy
            
            pool = ObjectPool(
                object_class=object_class,
                initial_size=initial_size,
                max_size=max_size,
                strategy=strategy,
                factory=factory
            )
            
            self.pools[name] = pool
            self.pool_configs[name] = {
                'object_class': object_class,
                'initial_size': initial_size,
                'max_size': max_size,
                'strategy': strategy,
                'factory': factory,
            }
            
            logger.info(f"Created pool {name} for {object_class.__name__}")
            return pool
    
    def get_pool(self, name: str) -> Optional[ObjectPool]:
        """Get a pool by name.
        
        Args:
            name (str): Pool name
            
        Returns:
            ObjectPool: Pool instance or None if not found
        """
        with self._lock:
            return self.pools.get(name)
    
    def remove_pool(self, name: str) -> bool:
        """Remove a pool.
        
        Args:
            name (str): Pool name
            
        Returns:
            bool: True if pool was removed
        """
        with self._lock:
            if name in self.pools:
                pool = self.pools[name]
                pool.clear()
                del self.pools[name]
                del self.pool_configs[name]
                logger.info(f"Removed pool {name}")
                return True
            return False
    
    def clear_all_pools(self) -> None:
        """Clear all pools."""
        with self._lock:
            for pool in self.pools.values():
                pool.clear()
            logger.info("Cleared all pools")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for all pools.
        
        Returns:
            Dict[str, Any]: Pool manager statistics
        """
        with self._lock:
            stats = {
                'total_pools': len(self.pools),
                'pools': {},
                'aggregate': {
                    'total_objects': 0,
                    'total_hits': 0,
                    'total_misses': 0,
                    'average_hit_rate': 0.0,
                }
            }
            
            total_hits = 0
            total_misses = 0
            
            for name, pool in self.pools.items():
                pool_stats = pool.get_stats()
                stats['pools'][name] = pool_stats
                
                stats['aggregate']['total_objects'] += pool_stats['total_count']
                total_hits += pool_stats['hits']
                total_misses += pool_stats['misses']
            
            stats['aggregate']['total_hits'] = total_hits
            stats['aggregate']['total_misses'] = total_misses
            
            if total_hits + total_misses > 0:
                stats['aggregate']['average_hit_rate'] = (total_hits / (total_hits + total_misses)) * 100
            
            return stats
    
    def _start_cleanup_thread(self) -> None:
        """Start the cleanup thread."""
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            return
        
        self._cleanup_active = True
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        logger.info("Started pool cleanup thread")
    
    def _cleanup_loop(self) -> None:
        """Main cleanup loop."""
        while self._cleanup_active:
            try:
                time.sleep(self.config.cleanup_interval)
                self._perform_cleanup()
            except Exception as e:
                logger.error(f"Error in pool cleanup: {e}")
    
    def _perform_cleanup(self) -> None:
        """Perform cleanup operations."""
        # This is a placeholder for future cleanup operations
        # such as removing unused objects, compacting pools, etc.
        pass
    
    def shutdown(self) -> None:
        """Shutdown the pool manager."""
        self._cleanup_active = False
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=1.0)
        
        self.clear_all_pools()
        logger.info("Pool manager shutdown complete")


class MemoryManager:
    """Centralized memory management system."""
    
    def __init__(self, config: MemoryConfig = None):
        """Initialize memory manager.
        
        Args:
            config (MemoryConfig, optional): Memory configuration
        """
        self.config = config or MemoryConfig()
        
        # Components
        self.pool_manager = PoolManager(self.config) if self.config.enable_pooling else None
        
        # Statistics
        self.stats = MemoryStats()
        
        # Thread safety
        self._lock = threading.RLock()
        
        logger.info("Memory manager initialized")
    
    def get_pool_manager(self) -> Optional[PoolManager]:
        """Get the pool manager.
        
        Returns:
            PoolManager: Pool manager instance or None if disabled
        """
        return self.pool_manager
    
    def get_stats(self) -> MemoryStats:
        """Get comprehensive memory statistics.
        
        Returns:
            MemoryStats: Current memory statistics
        """
        with self._lock:
            stats = MemoryStats()
            
            # Pool statistics
            if self.pool_manager:
                pool_stats = self.pool_manager.get_stats()
                stats.total_pools = pool_stats['total_pools']
                stats.total_pooled_objects = pool_stats['aggregate']['total_objects']
                stats.pool_hit_rate = pool_stats['aggregate']['average_hit_rate']
                stats.pool_miss_count = pool_stats['aggregate']['total_misses']
            
            return stats
    
    def shutdown(self) -> None:
        """Shutdown the memory manager."""
        if self.pool_manager:
            self.pool_manager.shutdown()
        
        logger.info("Memory manager shutdown complete")


# Global memory manager instance
_global_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """Get the global memory manager instance.
    
    Returns:
        MemoryManager: Global memory manager
    """
    global _global_memory_manager
    if _global_memory_manager is None:
        _global_memory_manager = MemoryManager()
    return _global_memory_manager


def initialize_memory_manager(config: MemoryConfig = None) -> MemoryManager:
    """Initialize the global memory manager.
    
    Args:
        config (MemoryConfig, optional): Memory configuration
        
    Returns:
        MemoryManager: Initialized memory manager
    """
    global _global_memory_manager
    _global_memory_manager = MemoryManager(config)
    return _global_memory_manager


def shutdown_memory_manager() -> None:
    """Shutdown the global memory manager."""
    global _global_memory_manager
    if _global_memory_manager:
        _global_memory_manager.shutdown()
        _global_memory_manager = None
