"""Central asset management system.

This module provides the main AssetManager class that coordinates all
asset management functionality including loading, caching, discovery,
and resource management.
"""

from typing import Optional, Dict, List, Any, Callable, Union
from pathlib import Path
import threading
import logging

from .types import Asset, AssetType, AssetMetadata
from .cache import AssetCache, CachePolicy, CacheStats
from .loader import LoaderRegistry, get_loader_registry
from .discovery import ResourceDiscovery, AssetCatalog, ScanResult
from .exceptions import (
    AssetError, AssetNotFoundError, AssetLoadError, 
    AssetCacheError, AssetDependencyError
)


logger = logging.getLogger(__name__)


class AssetManager:
    """Central asset management system.
    
    The AssetManager coordinates all asset-related operations including
    loading, caching, discovery, and resource management. It provides
    a unified interface for accessing game assets.
    """
    
    def __init__(self,
                 asset_paths: Optional[List[str]] = None,
                 cache_size: int = 100 * 1024 * 1024,  # 100MB
                 max_cached_assets: int = 1000,
                 enable_hot_reload: bool = True,
                 auto_discover: bool = True):
        """Initialize the asset manager.
        
        Args:
            asset_paths (List[str], optional): Paths to search for assets
            cache_size (int): Maximum cache size in bytes
            max_cached_assets (int): Maximum number of cached assets
            enable_hot_reload (bool): Enable hot-reloading of assets
            auto_discover (bool): Automatically discover assets on startup
        """
        self.asset_paths = asset_paths or ['assets', 'data', 'resources']
        self.enable_hot_reload = enable_hot_reload
        self.auto_discover = auto_discover
        
        # Core components
        self.cache = AssetCache(
            max_memory=cache_size,
            max_assets=max_cached_assets,
            enable_hot_reload=enable_hot_reload
        )
        self.loader_registry = get_loader_registry()
        self.discovery = ResourceDiscovery(
            scan_paths=self.asset_paths,
            follow_symlinks=False
        )
        
        # Asset tracking
        self._loaded_assets: Dict[str, Asset] = {}
        self._asset_aliases: Dict[str, str] = {}  # alias -> real_path
        self._dependencies: Dict[str, List[str]] = {}  # asset -> dependencies
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Event callbacks
        self._load_callbacks: List[Callable[[str, Asset], None]] = []
        self._error_callbacks: List[Callable[[str, Exception], None]] = []
        
        # Set up hot-reload callback
        if enable_hot_reload:
            self.cache.add_reload_callback(self._on_asset_reloaded)
        
        # Auto-discover assets if enabled
        if auto_discover:
            self._discover_assets()
    
    def load(self, path: str, 
             asset_type: Optional[AssetType] = None,
             cache_policy: Optional[CachePolicy] = None,
             force_reload: bool = False) -> Asset:
        """Load an asset.
        
        Args:
            path (str): Asset path or alias
            asset_type (AssetType, optional): Expected asset type
            cache_policy (CachePolicy, optional): Cache policy for this asset
            force_reload (bool): Force reload even if cached
            
        Returns:
            Asset: Loaded asset
            
        Raises:
            AssetNotFoundError: If asset cannot be found
            AssetLoadError: If asset fails to load
        """
        with self._lock:
            # Resolve aliases
            real_path = self._resolve_path(path)
            
            # Check cache first (unless force reload)
            if not force_reload:
                cached_asset = self.cache.get(real_path)
                if cached_asset:
                    logger.debug(f"Asset loaded from cache: {real_path}")
                    return cached_asset
            
            # Find asset file
            asset_file = self._find_asset_file(real_path)
            if not asset_file:
                raise AssetNotFoundError(real_path, 
                                       asset_type.name if asset_type else None,
                                       self.asset_paths)
            
            try:
                # Load the asset
                asset = self.loader_registry.load_asset(asset_file, asset_type)
                
                # Cache the asset
                self.cache.put(real_path, asset, cache_policy)
                
                # Track the asset
                self._loaded_assets[real_path] = asset
                
                # Load dependencies
                self._load_dependencies(asset)
                
                # Notify callbacks
                for callback in self._load_callbacks:
                    try:
                        callback(real_path, asset)
                    except Exception as e:
                        logger.warning(f"Load callback error: {e}")
                
                logger.info(f"Asset loaded: {real_path}")
                return asset
                
            except Exception as e:
                # Notify error callbacks
                for callback in self._error_callbacks:
                    try:
                        callback(real_path, e)
                    except Exception:
                        pass  # Don't let callback errors propagate
                
                if isinstance(e, (AssetNotFoundError, AssetLoadError)):
                    raise
                else:
                    raise AssetLoadError(real_path, 
                                       asset_type.name if asset_type else None, 
                                       e)
    
    def get(self, path: str, default: Optional[Asset] = None) -> Optional[Asset]:
        """Get an asset if it's loaded, without triggering a load.
        
        Args:
            path (str): Asset path or alias
            default (Asset, optional): Default value if not found
            
        Returns:
            Asset: Loaded asset or default
        """
        with self._lock:
            real_path = self._resolve_path(path)
            return self.cache.get(real_path) or default
    
    def unload(self, path: str) -> bool:
        """Unload an asset from memory.
        
        Args:
            path (str): Asset path or alias
            
        Returns:
            bool: True if asset was unloaded
        """
        with self._lock:
            real_path = self._resolve_path(path)
            
            # Remove from cache
            cache_removed = self.cache.remove(real_path)
            
            # Remove from tracking
            if real_path in self._loaded_assets:
                del self._loaded_assets[real_path]
            
            # Clean up dependencies
            if real_path in self._dependencies:
                del self._dependencies[real_path]
            
            logger.debug(f"Asset unloaded: {real_path}")
            return cache_removed
    
    def reload(self, path: str) -> Asset:
        """Reload an asset from disk.
        
        Args:
            path (str): Asset path or alias
            
        Returns:
            Asset: Reloaded asset
        """
        return self.load(path, force_reload=True)
    
    def is_loaded(self, path: str) -> bool:
        """Check if an asset is currently loaded.
        
        Args:
            path (str): Asset path or alias
            
        Returns:
            bool: True if asset is loaded
        """
        with self._lock:
            real_path = self._resolve_path(path)
            return self.cache.contains(real_path)
    
    def add_alias(self, alias: str, path: str) -> None:
        """Add an alias for an asset path.
        
        Args:
            alias (str): Alias name
            path (str): Real asset path
        """
        with self._lock:
            self._asset_aliases[alias] = path
            logger.debug(f"Asset alias added: {alias} -> {path}")
    
    def remove_alias(self, alias: str) -> bool:
        """Remove an asset alias.
        
        Args:
            alias (str): Alias to remove
            
        Returns:
            bool: True if alias was removed
        """
        with self._lock:
            if alias in self._asset_aliases:
                del self._asset_aliases[alias]
                logger.debug(f"Asset alias removed: {alias}")
                return True
            return False
    
    def get_aliases(self) -> Dict[str, str]:
        """Get all asset aliases.
        
        Returns:
            Dict[str, str]: Dictionary of aliases -> paths
        """
        with self._lock:
            return self._asset_aliases.copy()
    
    def add_asset_path(self, path: str) -> None:
        """Add a path to search for assets.
        
        Args:
            path (str): Path to add
        """
        with self._lock:
            if path not in self.asset_paths:
                self.asset_paths.append(path)
                self.discovery.add_scan_path(path)
                logger.info(f"Asset path added: {path}")
    
    def remove_asset_path(self, path: str) -> None:
        """Remove an asset search path.
        
        Args:
            path (str): Path to remove
        """
        with self._lock:
            if path in self.asset_paths:
                self.asset_paths.remove(path)
                self.discovery.remove_scan_path(path)
                logger.info(f"Asset path removed: {path}")
    
    def discover_assets(self, force_rescan: bool = False) -> ScanResult:
        """Discover assets in all configured paths.
        
        Args:
            force_rescan (bool): Force rescan even if files haven't changed
            
        Returns:
            ScanResult: Results of the discovery operation
        """
        logger.info("Starting asset discovery...")
        result = self.discovery.scan(force_rescan)
        logger.info(f"Asset discovery completed: {result.assets_found} assets found "
                   f"in {result.scan_time:.2f}s")
        return result
    
    def get_catalog(self) -> AssetCatalog:
        """Get the asset catalog.
        
        Returns:
            AssetCatalog: Current asset catalog
        """
        return self.discovery.get_catalog()
    
    def find_assets(self, 
                   asset_type: Optional[AssetType] = None,
                   tag: Optional[str] = None,
                   query: Optional[str] = None) -> List[AssetMetadata]:
        """Find assets matching criteria.
        
        Args:
            asset_type (AssetType, optional): Filter by asset type
            tag (str, optional): Filter by tag
            query (str, optional): Search query
            
        Returns:
            List[AssetMetadata]: Matching assets
        """
        catalog = self.get_catalog()
        
        if query:
            return catalog.search_assets(query)
        elif tag:
            return catalog.get_assets_by_tag(tag)
        elif asset_type:
            return catalog.get_assets_by_type(asset_type)
        else:
            return list(catalog.assets.values())
    
    def get_cache_stats(self) -> CacheStats:
        """Get cache statistics.
        
        Returns:
            CacheStats: Current cache statistics
        """
        return self.cache.get_stats()
    
    def clear_cache(self) -> None:
        """Clear the asset cache."""
        with self._lock:
            self.cache.clear()
            self._loaded_assets.clear()
            logger.info("Asset cache cleared")
    
    def set_cache_policy(self, path: str, policy: CachePolicy) -> None:
        """Set cache policy for an asset.
        
        Args:
            path (str): Asset path or alias
            policy (CachePolicy): Cache policy
        """
        with self._lock:
            real_path = self._resolve_path(path)
            self.cache.set_policy(real_path, policy)
    
    def add_load_callback(self, callback: Callable[[str, Asset], None]) -> None:
        """Add a callback for asset load events.
        
        Args:
            callback (Callable): Callback function (path, asset)
        """
        self._load_callbacks.append(callback)
    
    def remove_load_callback(self, callback: Callable[[str, Asset], None]) -> None:
        """Remove a load callback.
        
        Args:
            callback (Callable): Callback to remove
        """
        if callback in self._load_callbacks:
            self._load_callbacks.remove(callback)
    
    def add_error_callback(self, callback: Callable[[str, Exception], None]) -> None:
        """Add a callback for asset error events.
        
        Args:
            callback (Callable): Callback function (path, error)
        """
        self._error_callbacks.append(callback)
    
    def remove_error_callback(self, callback: Callable[[str, Exception], None]) -> None:
        """Remove an error callback.
        
        Args:
            callback (Callable): Callback to remove
        """
        if callback in self._error_callbacks:
            self._error_callbacks.remove(callback)
    
    def save_catalog(self, path: str) -> None:
        """Save the asset catalog to a file.
        
        Args:
            path (str): Path to save catalog to
        """
        self.discovery.save_catalog(path)
        logger.info(f"Asset catalog saved to: {path}")
    
    def load_catalog(self, path: str) -> None:
        """Load an asset catalog from a file.
        
        Args:
            path (str): Path to load catalog from
        """
        self.discovery.load_catalog(path)
        logger.info(f"Asset catalog loaded from: {path}")
    
    def get_memory_usage(self) -> int:
        """Get current memory usage in bytes.
        
        Returns:
            int: Memory usage in bytes
        """
        return self.cache.get_memory_usage()
    
    def get_loaded_asset_count(self) -> int:
        """Get number of loaded assets.
        
        Returns:
            int: Number of loaded assets
        """
        return self.cache.get_asset_count()
    
    def _resolve_path(self, path: str) -> str:
        """Resolve an asset path, handling aliases.
        
        Args:
            path (str): Asset path or alias
            
        Returns:
            str: Resolved real path
        """
        return self._asset_aliases.get(path, path)
    
    def _find_asset_file(self, path: str) -> Optional[str]:
        """Find an asset file in the search paths.
        
        Args:
            path (str): Asset path
            
        Returns:
            str: Full path to asset file or None if not found
        """
        # If path is absolute and exists, use it directly
        if Path(path).is_absolute() and Path(path).exists():
            return path
        
        # Search in asset paths
        for asset_path in self.asset_paths:
            full_path = Path(asset_path) / path
            if full_path.exists():
                return str(full_path)
        
        # Check if it exists relative to current directory
        if Path(path).exists():
            return path
        
        return None
    
    def _load_dependencies(self, asset: Asset) -> None:
        """Load dependencies for an asset.
        
        Args:
            asset (Asset): Asset to load dependencies for
        """
        if not asset.metadata.dependencies:
            return
        
        dependencies = []
        for dep_path in asset.metadata.dependencies:
            try:
                dep_asset = self.load(dep_path)
                dependencies.append(dep_path)
            except Exception as e:
                logger.warning(f"Failed to load dependency {dep_path} for {asset.path}: {e}")
                # Could raise AssetDependencyError here if strict dependency loading is required
        
        if dependencies:
            self._dependencies[asset.path] = dependencies
    
    def _discover_assets(self) -> None:
        """Discover assets on startup."""
        try:
            result = self.discover_assets()
            logger.info(f"Auto-discovery found {result.assets_found} assets")
        except Exception as e:
            logger.warning(f"Auto-discovery failed: {e}")
    
    def _on_asset_reloaded(self, path: str, asset: Asset) -> None:
        """Handle asset reload events.
        
        Args:
            path (str): Asset path
            asset (Asset): Reloaded asset
        """
        logger.info(f"Asset hot-reloaded: {path}")
        
        # Update tracking
        self._loaded_assets[path] = asset
        
        # Reload dependencies if needed
        self._load_dependencies(asset)


# Global asset manager instance
_global_manager: Optional[AssetManager] = None


def get_asset_manager() -> AssetManager:
    """Get the global asset manager instance.
    
    Returns:
        AssetManager: Global asset manager
    """
    global _global_manager
    if _global_manager is None:
        _global_manager = AssetManager()
    return _global_manager


def initialize_asset_manager(**kwargs) -> AssetManager:
    """Initialize the global asset manager with custom settings.
    
    Args:
        **kwargs: Arguments to pass to AssetManager constructor
        
    Returns:
        AssetManager: Initialized asset manager
    """
    global _global_manager
    _global_manager = AssetManager(**kwargs)
    return _global_manager


def shutdown_asset_manager() -> None:
    """Shutdown the global asset manager."""
    global _global_manager
    if _global_manager:
        _global_manager.clear_cache()
        _global_manager = None
