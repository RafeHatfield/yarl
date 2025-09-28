"""Smart caching system with automatic cleanup and optimization.

This module provides intelligent caching mechanisms including LRU cache,
TTL cache, and weak reference cache for optimal memory usage.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum, auto
import time
import threading
import weakref
import logging
from collections import OrderedDict, defaultdict

logger = logging.getLogger(__name__)

K = TypeVar('K')  # Key type
V = TypeVar('V')  # Value type


class CacheStrategy(Enum):
    """Cache eviction strategies."""
    
    LRU = auto()        # Least Recently Used
    LFU = auto()        # Least Frequently Used
    TTL = auto()        # Time To Live
    WEAK_REF = auto()   # Weak Reference
    HYBRID = auto()     # Combination of strategies


@dataclass
class CacheConfig:
    """Configuration for cache systems."""
    
    # Basic settings
    max_size: int = 256
    strategy: CacheStrategy = CacheStrategy.LRU
    
    # TTL settings
    default_ttl: float = 300.0      # 5 minutes
    cleanup_interval: float = 60.0  # 1 minute
    
    # Performance settings
    enable_statistics: bool = True
    thread_safe: bool = True
    
    # Memory settings
    max_memory_mb: float = 50.0     # Maximum cache memory usage
    memory_check_interval: float = 30.0  # Memory check frequency


@dataclass
class CacheStats:
    """Cache usage statistics."""
    
    # Hit/miss statistics
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    
    # Size statistics
    current_size: int = 0
    max_size_reached: int = 0
    
    # Memory statistics
    estimated_memory_bytes: int = 0
    
    # Performance statistics
    average_access_time_ms: float = 0.0
    total_access_time_ms: float = 0.0
    access_count: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate hit rate percentage."""
        total = self.hits + self.misses
        return (self.hits / total) * 100 if total > 0 else 0.0
    
    @property
    def miss_rate(self) -> float:
        """Calculate miss rate percentage."""
        return 100.0 - self.hit_rate
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'evictions': self.evictions,
            'hit_rate': self.hit_rate,
            'miss_rate': self.miss_rate,
            'current_size': self.current_size,
            'max_size_reached': self.max_size_reached,
            'estimated_memory_bytes': self.estimated_memory_bytes,
            'average_access_time_ms': self.average_access_time_ms,
            'access_count': self.access_count,
        }


class CacheEntry:
    """Entry in a cache with metadata."""
    
    def __init__(self, key: Any, value: Any, ttl: Optional[float] = None):
        """Initialize cache entry.
        
        Args:
            key (Any): Cache key
            value (Any): Cache value
            ttl (float, optional): Time to live in seconds
        """
        self.key = key
        self.value = value
        self.created_time = time.time()
        self.last_accessed = self.created_time
        self.access_count = 0
        self.ttl = ttl
        self.expires_at = self.created_time + ttl if ttl else None
    
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        return self.expires_at is not None and time.time() > self.expires_at
    
    def touch(self) -> None:
        """Update access time and count."""
        self.last_accessed = time.time()
        self.access_count += 1
    
    def get_age(self) -> float:
        """Get age of entry in seconds."""
        return time.time() - self.created_time
    
    def get_time_since_access(self) -> float:
        """Get time since last access in seconds."""
        return time.time() - self.last_accessed


class SmartCache(Generic[K, V], ABC):
    """Abstract base class for smart caches."""
    
    def __init__(self, config: CacheConfig = None):
        """Initialize smart cache.
        
        Args:
            config (CacheConfig, optional): Cache configuration
        """
        self.config = config or CacheConfig()
        self.stats = CacheStats()
        
        # Thread safety
        self._lock = threading.RLock() if self.config.thread_safe else None
        
        # Cleanup thread
        self._cleanup_thread: Optional[threading.Thread] = None
        self._cleanup_active = False
        
        if self.config.cleanup_interval > 0:
            self._start_cleanup_thread()
    
    @abstractmethod
    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    def put(self, key: K, value: V, ttl: Optional[float] = None) -> None:
        """Put value in cache."""
        pass
    
    @abstractmethod
    def remove(self, key: K) -> bool:
        """Remove value from cache."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all cache entries."""
        pass
    
    @abstractmethod
    def size(self) -> int:
        """Get current cache size."""
        pass
    
    def contains(self, key: K) -> bool:
        """Check if key exists in cache."""
        return self.get(key) is not None
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        with self._get_lock():
            return self.stats
    
    def _get_lock(self):
        """Get lock context manager."""
        if self._lock:
            return self._lock
        else:
            # Dummy context manager for non-thread-safe mode
            class DummyLock:
                def __enter__(self): return self
                def __exit__(self, *args): pass
            return DummyLock()
    
    def _record_hit(self) -> None:
        """Record cache hit."""
        if self.config.enable_statistics:
            self.stats.hits += 1
    
    def _record_miss(self) -> None:
        """Record cache miss."""
        if self.config.enable_statistics:
            self.stats.misses += 1
    
    def _record_eviction(self) -> None:
        """Record cache eviction."""
        if self.config.enable_statistics:
            self.stats.evictions += 1
    
    def _start_cleanup_thread(self) -> None:
        """Start cleanup thread."""
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            return
        
        self._cleanup_active = True
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
    
    def _cleanup_loop(self) -> None:
        """Main cleanup loop."""
        while self._cleanup_active:
            try:
                time.sleep(self.config.cleanup_interval)
                self._perform_cleanup()
            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")
    
    def _perform_cleanup(self) -> None:
        """Perform cleanup operations - override in subclasses."""
        pass
    
    def shutdown(self) -> None:
        """Shutdown cache and cleanup resources."""
        self._cleanup_active = False
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=1.0)


class LRUCache(SmartCache[K, V]):
    """Least Recently Used cache implementation."""
    
    def __init__(self, config: CacheConfig = None):
        """Initialize LRU cache."""
        super().__init__(config)
        self._cache: OrderedDict[K, CacheEntry] = OrderedDict()
    
    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """Get value from cache."""
        with self._get_lock():
            if key in self._cache:
                entry = self._cache[key]
                
                # Check if expired
                if entry.is_expired():
                    del self._cache[key]
                    self._record_miss()
                    return default
                
                # Move to end (most recently used)
                self._cache.move_to_end(key)
                entry.touch()
                self._record_hit()
                return entry.value
            else:
                self._record_miss()
                return default
    
    def put(self, key: K, value: V, ttl: Optional[float] = None) -> None:
        """Put value in cache."""
        with self._get_lock():
            # Use default TTL if not specified
            if ttl is None:
                ttl = self.config.default_ttl
            
            # Create new entry
            entry = CacheEntry(key, value, ttl)
            
            # Remove existing entry if present
            if key in self._cache:
                del self._cache[key]
            
            # Add new entry
            self._cache[key] = entry
            
            # Evict if necessary
            while len(self._cache) > self.config.max_size:
                # Remove least recently used (first item)
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._record_eviction()
            
            # Update stats
            self.stats.current_size = len(self._cache)
            self.stats.max_size_reached = max(self.stats.max_size_reached, self.stats.current_size)
    
    def remove(self, key: K) -> bool:
        """Remove value from cache."""
        with self._get_lock():
            if key in self._cache:
                del self._cache[key]
                self.stats.current_size = len(self._cache)
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._get_lock():
            self._cache.clear()
            self.stats.current_size = 0
    
    def size(self) -> int:
        """Get current cache size."""
        with self._get_lock():
            return len(self._cache)
    
    def _perform_cleanup(self) -> None:
        """Remove expired entries."""
        with self._get_lock():
            expired_keys = []
            current_time = time.time()
            
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
                self._record_eviction()
            
            if expired_keys:
                self.stats.current_size = len(self._cache)
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")


class TTLCache(SmartCache[K, V]):
    """Time To Live cache implementation."""
    
    def __init__(self, config: CacheConfig = None):
        """Initialize TTL cache."""
        super().__init__(config)
        self._cache: Dict[K, CacheEntry] = {}
    
    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """Get value from cache."""
        with self._get_lock():
            if key in self._cache:
                entry = self._cache[key]
                
                # Check if expired
                if entry.is_expired():
                    del self._cache[key]
                    self._record_miss()
                    return default
                
                entry.touch()
                self._record_hit()
                return entry.value
            else:
                self._record_miss()
                return default
    
    def put(self, key: K, value: V, ttl: Optional[float] = None) -> None:
        """Put value in cache."""
        with self._get_lock():
            # Use default TTL if not specified
            if ttl is None:
                ttl = self.config.default_ttl
            
            # Create new entry
            entry = CacheEntry(key, value, ttl)
            self._cache[key] = entry
            
            # Update stats
            self.stats.current_size = len(self._cache)
            self.stats.max_size_reached = max(self.stats.max_size_reached, self.stats.current_size)
    
    def remove(self, key: K) -> bool:
        """Remove value from cache."""
        with self._get_lock():
            if key in self._cache:
                del self._cache[key]
                self.stats.current_size = len(self._cache)
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._get_lock():
            self._cache.clear()
            self.stats.current_size = 0
    
    def size(self) -> int:
        """Get current cache size."""
        with self._get_lock():
            return len(self._cache)
    
    def _perform_cleanup(self) -> None:
        """Remove expired entries."""
        with self._get_lock():
            expired_keys = []
            
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
                self._record_eviction()
            
            if expired_keys:
                self.stats.current_size = len(self._cache)
                logger.debug(f"Cleaned up {len(expired_keys)} expired TTL cache entries")


class WeakRefCache(SmartCache[K, V]):
    """Weak reference cache that automatically removes entries when objects are garbage collected."""
    
    def __init__(self, config: CacheConfig = None):
        """Initialize weak reference cache."""
        super().__init__(config)
        self._cache: Dict[K, weakref.ReferenceType] = {}
        self._callbacks: Dict[K, Callable] = {}
    
    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """Get value from cache."""
        with self._get_lock():
            if key in self._cache:
                ref = self._cache[key]
                value = ref()
                
                if value is None:
                    # Object was garbage collected
                    del self._cache[key]
                    if key in self._callbacks:
                        del self._callbacks[key]
                    self._record_miss()
                    return default
                
                self._record_hit()
                return value
            else:
                self._record_miss()
                return default
    
    def put(self, key: K, value: V, ttl: Optional[float] = None) -> None:
        """Put value in cache."""
        with self._get_lock():
            # Create callback to clean up when object is garbage collected
            def cleanup_callback(ref):
                with self._get_lock():
                    if key in self._cache and self._cache[key] is ref:
                        del self._cache[key]
                        if key in self._callbacks:
                            del self._callbacks[key]
                        self.stats.current_size = len(self._cache)
            
            # Create weak reference
            ref = weakref.ref(value, cleanup_callback)
            self._cache[key] = ref
            self._callbacks[key] = cleanup_callback
            
            # Update stats
            self.stats.current_size = len(self._cache)
            self.stats.max_size_reached = max(self.stats.max_size_reached, self.stats.current_size)
    
    def remove(self, key: K) -> bool:
        """Remove value from cache."""
        with self._get_lock():
            if key in self._cache:
                del self._cache[key]
                if key in self._callbacks:
                    del self._callbacks[key]
                self.stats.current_size = len(self._cache)
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._get_lock():
            self._cache.clear()
            self._callbacks.clear()
            self.stats.current_size = 0
    
    def size(self) -> int:
        """Get current cache size."""
        with self._get_lock():
            return len(self._cache)
    
    def _perform_cleanup(self) -> None:
        """Remove dead weak references."""
        with self._get_lock():
            dead_keys = []
            
            for key, ref in self._cache.items():
                if ref() is None:
                    dead_keys.append(key)
            
            for key in dead_keys:
                del self._cache[key]
                if key in self._callbacks:
                    del self._callbacks[key]
                self._record_eviction()
            
            if dead_keys:
                self.stats.current_size = len(self._cache)
                logger.debug(f"Cleaned up {len(dead_keys)} dead weak references")


def create_cache(strategy: CacheStrategy = CacheStrategy.LRU, 
                config: CacheConfig = None) -> SmartCache:
    """Create a cache with the specified strategy.
    
    Args:
        strategy (CacheStrategy): Cache strategy to use
        config (CacheConfig, optional): Cache configuration
        
    Returns:
        SmartCache: Created cache instance
    """
    config = config or CacheConfig()
    config.strategy = strategy
    
    if strategy == CacheStrategy.LRU:
        return LRUCache(config)
    elif strategy == CacheStrategy.TTL:
        return TTLCache(config)
    elif strategy == CacheStrategy.WEAK_REF:
        return WeakRefCache(config)
    else:
        raise ValueError(f"Unsupported cache strategy: {strategy}")


class CacheManager:
    """Manages multiple caches with centralized configuration."""
    
    def __init__(self, config: CacheConfig = None):
        """Initialize cache manager.
        
        Args:
            config (CacheConfig, optional): Default cache configuration
        """
        self.default_config = config or CacheConfig()
        self.caches: Dict[str, SmartCache] = {}
        
        # Thread safety
        self._lock = threading.RLock()
    
    def create_cache(self, name: str, strategy: CacheStrategy = None,
                    config: CacheConfig = None) -> SmartCache:
        """Create a new cache.
        
        Args:
            name (str): Cache name
            strategy (CacheStrategy, optional): Cache strategy
            config (CacheConfig, optional): Cache configuration
            
        Returns:
            SmartCache: Created cache
        """
        with self._lock:
            if name in self.caches:
                raise ValueError(f"Cache {name} already exists")
            
            # Use defaults if not specified
            strategy = strategy or self.default_config.strategy
            config = config or self.default_config
            
            cache = create_cache(strategy, config)
            self.caches[name] = cache
            
            logger.info(f"Created cache {name} with strategy {strategy.name}")
            return cache
    
    def get_cache(self, name: str) -> Optional[SmartCache]:
        """Get a cache by name.
        
        Args:
            name (str): Cache name
            
        Returns:
            SmartCache: Cache instance or None if not found
        """
        with self._lock:
            return self.caches.get(name)
    
    def remove_cache(self, name: str) -> bool:
        """Remove a cache.
        
        Args:
            name (str): Cache name
            
        Returns:
            bool: True if cache was removed
        """
        with self._lock:
            if name in self.caches:
                cache = self.caches[name]
                cache.shutdown()
                del self.caches[name]
                logger.info(f"Removed cache {name}")
                return True
            return False
    
    def clear_all_caches(self) -> None:
        """Clear all caches."""
        with self._lock:
            for cache in self.caches.values():
                cache.clear()
            logger.info("Cleared all caches")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for all caches.
        
        Returns:
            Dict[str, Any]: Cache manager statistics
        """
        with self._lock:
            stats = {
                'total_caches': len(self.caches),
                'caches': {},
                'aggregate': {
                    'total_hits': 0,
                    'total_misses': 0,
                    'total_size': 0,
                    'average_hit_rate': 0.0,
                }
            }
            
            total_hits = 0
            total_misses = 0
            
            for name, cache in self.caches.items():
                cache_stats = cache.get_stats()
                stats['caches'][name] = cache_stats.to_dict()
                
                total_hits += cache_stats.hits
                total_misses += cache_stats.misses
                stats['aggregate']['total_size'] += cache_stats.current_size
            
            stats['aggregate']['total_hits'] = total_hits
            stats['aggregate']['total_misses'] = total_misses
            
            if total_hits + total_misses > 0:
                stats['aggregate']['average_hit_rate'] = (total_hits / (total_hits + total_misses)) * 100
            
            return stats
    
    def shutdown(self) -> None:
        """Shutdown all caches."""
        with self._lock:
            for cache in self.caches.values():
                cache.shutdown()
            self.caches.clear()
            logger.info("Cache manager shutdown complete")
