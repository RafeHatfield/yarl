"""Advanced memory optimization and object pooling system.

This package provides comprehensive memory management capabilities including
object pooling, smart caching, memory leak detection, and garbage collection
optimization to minimize memory pressure and improve game performance.

Key Components:
- ObjectPool: High-performance object pooling with automatic lifecycle management
- MemoryManager: Centralized memory management and optimization
- SmartCache: Intelligent caching with automatic cleanup and LRU eviction
- MemoryProfiler: Memory usage tracking and leak detection
- GCOptimizer: Garbage collection optimization and tuning
- PooledObjects: Pre-configured pooled versions of common game objects
"""

from .core import (
    ObjectPool, PooledObject, PoolableObject, PoolManager,
    MemoryManager, MemoryConfig, MemoryStats, PoolStrategy
)
from .pools import (
    MessagePool, EntityPool, ComponentPool, EventPool,
    TemporaryObjectPool, create_default_pools,
    PooledMessage, PooledEntity, PooledEvent, PooledComponent, TemporaryObject
)
from .cache import (
    SmartCache, CacheConfig, CacheStats, LRUCache, TTLCache,
    WeakRefCache, create_cache, CacheStrategy, CacheManager
)
from .profiler import (
    MemoryProfiler, MemorySnapshot, MemoryLeak, LeakDetector,
    AllocationTracker, create_memory_profiler, LeakSeverity
)
from .gc_optimizer import (
    GCOptimizer, GCConfig, GCStats, optimize_gc_settings,
    disable_gc_during, gc_collect_if_needed, GCMode
)
from .integration import (
    GameMemoryManager, PooledSystem, integrate_memory_optimization,
    MemoryOptimizedEngine, create_optimized_engine, MemoryOptimizationConfig,
    initialize_game_memory_manager
)
from .utils import (
    get_object_size, get_memory_usage, format_memory_size,
    memory_usage_context, track_allocations, MemoryMonitor, ObjectRegistry,
    AllocationTracker as UtilsAllocationTracker, get_global_allocation_tracker,
    get_global_memory_monitor
)

__all__ = [
    # Core
    'ObjectPool',
    'PooledObject',
    'PoolableObject',
    'PoolManager',
    'MemoryManager',
    'MemoryConfig',
    'MemoryStats',
    'PoolStrategy',
    
    # Pools
    'MessagePool',
    'EntityPool',
    'ComponentPool',
    'EventPool',
    'TemporaryObjectPool',
    'create_default_pools',
    'PooledMessage',
    'PooledEntity',
    'PooledEvent',
    'PooledComponent',
    'TemporaryObject',
    
    # Cache
    'SmartCache',
    'CacheConfig',
    'CacheStats',
    'LRUCache',
    'TTLCache',
    'WeakRefCache',
    'create_cache',
    'CacheStrategy',
    'CacheManager',
    
    # Profiler
    'MemoryProfiler',
    'MemorySnapshot',
    'MemoryLeak',
    'LeakDetector',
    'AllocationTracker',
    'create_memory_profiler',
    'LeakSeverity',
    
    # GC Optimizer
    'GCOptimizer',
    'GCConfig',
    'GCStats',
    'optimize_gc_settings',
    'disable_gc_during',
    'gc_collect_if_needed',
    'GCMode',
    
    # Integration
    'GameMemoryManager',
    'PooledSystem',
    'integrate_memory_optimization',
    'MemoryOptimizedEngine',
    'create_optimized_engine',
    'MemoryOptimizationConfig',
    'initialize_game_memory_manager',
    
    # Utils
    'get_object_size',
    'get_memory_usage',
    'format_memory_size',
    'memory_usage_context',
    'track_allocations',
    'MemoryMonitor',
    'ObjectRegistry',
    'UtilsAllocationTracker',
    'get_global_allocation_tracker',
    'get_global_memory_monitor',
]
