"""Asset caching system for memory management and performance.

This module provides caching functionality for the asset management system,
including memory management, hot-reloading, and cache policies for different
types of assets.
"""

from enum import Enum, auto
from typing import Dict, Optional, List, Any, Callable
from dataclasses import dataclass
import time
import threading
from collections import OrderedDict
import weakref

from .types import Asset, AssetType
from .exceptions import AssetCacheError


class CachePolicy(Enum):
    """Cache policies for different asset management strategies."""
    
    NEVER = auto()          # Never cache (always load from disk)
    ALWAYS = auto()         # Always cache (never unload)
    LRU = auto()           # Least Recently Used eviction
    LFU = auto()           # Least Frequently Used eviction
    TTL = auto()           # Time To Live based eviction
    SIZE_BASED = auto()    # Size-based eviction
    REFERENCE_BASED = auto() # Reference counting based eviction


@dataclass
class CacheStats:
    """Statistics for cache performance monitoring."""
    
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    memory_usage: int = 0
    asset_count: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate."""
        return 1.0 - self.hit_rate
    
    def reset(self) -> None:
        """Reset all statistics."""
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.memory_usage = 0
        self.asset_count = 0


class AssetCache:
    """Asset cache with configurable policies and memory management.
    
    This class provides caching functionality for assets with support for
    different eviction policies, memory limits, and hot-reloading.
    """
    
    def __init__(self, 
                 max_memory: int = 100 * 1024 * 1024,  # 100MB default
                 max_assets: int = 1000,
                 default_policy: CachePolicy = CachePolicy.LRU,
                 enable_hot_reload: bool = True):
        """Initialize the asset cache.
        
        Args:
            max_memory (int): Maximum memory usage in bytes
            max_assets (int): Maximum number of cached assets
            default_policy (CachePolicy): Default cache policy
            enable_hot_reload (bool): Enable hot-reloading of assets
        """
        self.max_memory = max_memory
        self.max_assets = max_assets
        self.default_policy = default_policy
        self.enable_hot_reload = enable_hot_reload
        
        # Cache storage
        self._cache: OrderedDict[str, Asset] = OrderedDict()
        self._access_times: Dict[str, float] = {}
        self._access_counts: Dict[str, int] = {}
        self._load_times: Dict[str, float] = {}
        self._policies: Dict[str, CachePolicy] = {}
        
        # Reference tracking for REFERENCE_BASED policy
        self._references: Dict[str, weakref.WeakSet] = {}
        
        # Statistics
        self.stats = CacheStats()
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Hot-reload monitoring
        self._file_watchers: Dict[str, float] = {}
        self._reload_callbacks: List[Callable[[str, Asset], None]] = []
    
    def get(self, path: str) -> Optional[Asset]:
        """Get an asset from the cache.
        
        Args:
            path (str): Asset path
            
        Returns:
            Asset: Cached asset or None if not found
        """
        with self._lock:
            if path in self._cache:
                asset = self._cache[path]
                
                # Check for hot-reload
                if self.enable_hot_reload and asset.is_stale():
                    self._handle_hot_reload(path, asset)
                
                # Update access statistics
                self._access_times[path] = time.time()
                self._access_counts[path] = self._access_counts.get(path, 0) + 1
                
                # Move to end for LRU
                self._cache.move_to_end(path)
                
                self.stats.hits += 1
                return asset
            else:
                self.stats.misses += 1
                return None
    
    def put(self, path: str, asset: Asset, policy: Optional[CachePolicy] = None) -> None:
        """Put an asset in the cache.
        
        Args:
            path (str): Asset path
            asset (Asset): Asset to cache
            policy (CachePolicy, optional): Cache policy for this asset
        """
        with self._lock:
            # Set policy
            cache_policy = policy or self.default_policy
            self._policies[path] = cache_policy
            
            # Check if we should cache this asset
            if cache_policy == CachePolicy.NEVER:
                return
            
            # Remove existing entry if present
            if path in self._cache:
                self.remove(path)
            
            # Check cache limits before adding
            self._enforce_limits()
            
            # Add to cache
            self._cache[path] = asset
            self._access_times[path] = time.time()
            self._access_counts[path] = 1
            self._load_times[path] = time.time()
            
            # Set up hot-reload monitoring
            if self.enable_hot_reload:
                self._file_watchers[path] = asset.metadata.modified_time
            
            # Update statistics
            self.stats.asset_count = len(self._cache)
            self.stats.memory_usage += asset.get_memory_usage()
    
    def remove(self, path: str) -> bool:
        """Remove an asset from the cache.
        
        Args:
            path (str): Asset path
            
        Returns:
            bool: True if asset was removed, False if not found
        """
        with self._lock:
            if path not in self._cache:
                return False
            
            asset = self._cache[path]
            
            # Update statistics
            self.stats.memory_usage -= asset.get_memory_usage()
            self.stats.asset_count -= 1
            
            # Clean up tracking data
            del self._cache[path]
            self._access_times.pop(path, None)
            self._access_counts.pop(path, None)
            self._load_times.pop(path, None)
            self._policies.pop(path, None)
            self._file_watchers.pop(path, None)
            self._references.pop(path, None)
            
            # Unload asset if it's loaded
            if asset.loaded:
                asset.unload()
            
            return True
    
    def clear(self) -> None:
        """Clear all assets from the cache."""
        with self._lock:
            # Unload all assets
            for asset in self._cache.values():
                if asset.loaded:
                    asset.unload()
            
            # Clear all tracking data
            self._cache.clear()
            self._access_times.clear()
            self._access_counts.clear()
            self._load_times.clear()
            self._policies.clear()
            self._file_watchers.clear()
            self._references.clear()
            
            # Reset statistics
            self.stats.reset()
    
    def contains(self, path: str) -> bool:
        """Check if an asset is in the cache.
        
        Args:
            path (str): Asset path
            
        Returns:
            bool: True if asset is cached
        """
        with self._lock:
            return path in self._cache
    
    def get_memory_usage(self) -> int:
        """Get current memory usage in bytes.
        
        Returns:
            int: Current memory usage
        """
        with self._lock:
            return self.stats.memory_usage
    
    def get_asset_count(self) -> int:
        """Get number of cached assets.
        
        Returns:
            int: Number of cached assets
        """
        with self._lock:
            return len(self._cache)
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics.
        
        Returns:
            CacheStats: Current cache statistics
        """
        with self._lock:
            return CacheStats(
                hits=self.stats.hits,
                misses=self.stats.misses,
                evictions=self.stats.evictions,
                memory_usage=self.stats.memory_usage,
                asset_count=self.stats.asset_count
            )
    
    def add_reload_callback(self, callback: Callable[[str, Asset], None]) -> None:
        """Add a callback for hot-reload events.
        
        Args:
            callback (Callable): Callback function (path, asset)
        """
        self._reload_callbacks.append(callback)
    
    def remove_reload_callback(self, callback: Callable[[str, Asset], None]) -> None:
        """Remove a hot-reload callback.
        
        Args:
            callback (Callable): Callback function to remove
        """
        if callback in self._reload_callbacks:
            self._reload_callbacks.remove(callback)
    
    def _enforce_limits(self) -> None:
        """Enforce cache limits by evicting assets if necessary."""
        # Check asset count limit
        while len(self._cache) >= self.max_assets:
            self._evict_asset()
        
        # Check memory limit
        while self.stats.memory_usage > self.max_memory:
            if not self._evict_asset():
                break  # No more assets to evict
    
    def _evict_asset(self) -> bool:
        """Evict an asset based on the cache policy.
        
        Returns:
            bool: True if an asset was evicted
        """
        if not self._cache:
            return False
        
        # Find asset to evict based on policies
        evict_path = None
        current_time = time.time()
        
        # Group assets by policy
        policy_groups = {}
        for path, policy in self._policies.items():
            if policy not in policy_groups:
                policy_groups[policy] = []
            policy_groups[policy].append(path)
        
        # Try to evict based on policy priority
        policy_priority = [
            CachePolicy.TTL,
            CachePolicy.REFERENCE_BASED,
            CachePolicy.LFU,
            CachePolicy.LRU,
            CachePolicy.SIZE_BASED
        ]
        
        for policy in policy_priority:
            if policy in policy_groups and policy_groups[policy]:
                evict_path = self._select_eviction_candidate(policy_groups[policy], policy, current_time)
                if evict_path:
                    break
        
        # Fallback to LRU if no specific policy candidate found
        if not evict_path and self._cache:
            evict_path = next(iter(self._cache))  # First item (oldest in OrderedDict)
        
        if evict_path:
            self.remove(evict_path)
            self.stats.evictions += 1
            return True
        
        return False
    
    def _select_eviction_candidate(self, candidates: List[str], policy: CachePolicy, current_time: float) -> Optional[str]:
        """Select an eviction candidate based on policy.
        
        Args:
            candidates (List[str]): Candidate asset paths
            policy (CachePolicy): Cache policy to use
            current_time (float): Current time
            
        Returns:
            str: Path of asset to evict, or None
        """
        if not candidates:
            return None
        
        if policy == CachePolicy.LRU:
            # Least recently used
            return min(candidates, key=lambda p: self._access_times.get(p, 0))
        
        elif policy == CachePolicy.LFU:
            # Least frequently used
            return min(candidates, key=lambda p: self._access_counts.get(p, 0))
        
        elif policy == CachePolicy.TTL:
            # Time to live (oldest loaded)
            return min(candidates, key=lambda p: self._load_times.get(p, current_time))
        
        elif policy == CachePolicy.SIZE_BASED:
            # Largest asset first
            return max(candidates, key=lambda p: self._cache[p].get_memory_usage())
        
        elif policy == CachePolicy.REFERENCE_BASED:
            # Assets with no external references
            for path in candidates:
                if path not in self._references or not self._references[path]:
                    return path
            return None
        
        # Default to first candidate
        return candidates[0]
    
    def _handle_hot_reload(self, path: str, asset: Asset) -> None:
        """Handle hot-reload of a stale asset.
        
        Args:
            path (str): Asset path
            asset (Asset): Stale asset
        """
        try:
            # Reload the asset
            asset.reload()
            
            # Update file watcher
            self._file_watchers[path] = asset.metadata.modified_time
            
            # Notify callbacks
            for callback in self._reload_callbacks:
                try:
                    callback(path, asset)
                except Exception as e:
                    # Don't let callback errors break the cache
                    print(f"Hot-reload callback error: {e}")
        
        except Exception as e:
            # If reload fails, remove from cache
            self.remove(path)
            raise AssetCacheError(f"Hot-reload failed for {path}: {e}", path, "hot_reload")
    
    def register_reference(self, path: str, ref_holder: Any) -> None:
        """Register a reference to an asset for reference-based caching.
        
        Args:
            path (str): Asset path
            ref_holder (Any): Object holding a reference to the asset
        """
        with self._lock:
            if path not in self._references:
                self._references[path] = weakref.WeakSet()
            self._references[path].add(ref_holder)
    
    def unregister_reference(self, path: str, ref_holder: Any) -> None:
        """Unregister a reference to an asset.
        
        Args:
            path (str): Asset path
            ref_holder (Any): Object that held a reference to the asset
        """
        with self._lock:
            if path in self._references:
                self._references[path].discard(ref_holder)
    
    def get_cached_paths(self) -> List[str]:
        """Get list of all cached asset paths.
        
        Returns:
            List[str]: List of cached asset paths
        """
        with self._lock:
            return list(self._cache.keys())
    
    def get_policy(self, path: str) -> Optional[CachePolicy]:
        """Get the cache policy for an asset.
        
        Args:
            path (str): Asset path
            
        Returns:
            CachePolicy: Cache policy or None if not cached
        """
        with self._lock:
            return self._policies.get(path)
    
    def set_policy(self, path: str, policy: CachePolicy) -> None:
        """Set the cache policy for an asset.
        
        Args:
            path (str): Asset path
            policy (CachePolicy): New cache policy
        """
        with self._lock:
            if path in self._cache:
                self._policies[path] = policy
