"""Asset management system for game resources.

This package provides a comprehensive asset management system that handles
loading, caching, and managing various types of game resources including
sprites, fonts, sounds, UI themes, and configuration files.

Key Components:
- AssetManager: Central resource management and caching
- AssetType: Different types of assets (sprites, fonts, sounds, etc.)
- AssetLoader: Loading pipeline with format detection and validation
- AssetCache: Memory management with hot-reloading support
- ResourceDiscovery: Asset scanning and organization
"""

from .manager import AssetManager, get_asset_manager, initialize_asset_manager, shutdown_asset_manager
from .types import AssetType, Asset, SpriteAsset, FontAsset, SoundAsset, ThemeAsset, DataAsset
from .loader import AssetLoader, LoaderRegistry, get_loader_registry
from .cache import AssetCache, CachePolicy, CacheStats
from .discovery import ResourceDiscovery, AssetMetadata, ScanResult, AssetCatalog
from .exceptions import AssetError, AssetNotFoundError, AssetLoadError, AssetValidationError

__all__ = [
    'AssetManager',
    'get_asset_manager',
    'initialize_asset_manager',
    'shutdown_asset_manager',
    'AssetType',
    'Asset',
    'SpriteAsset',
    'FontAsset', 
    'SoundAsset',
    'ThemeAsset',
    'DataAsset',
    'AssetLoader',
    'LoaderRegistry',
    'get_loader_registry',
    'AssetCache',
    'CachePolicy',
    'CacheStats',
    'ResourceDiscovery',
    'AssetMetadata',
    'ScanResult',
    'AssetCatalog',
    'AssetError',
    'AssetNotFoundError',
    'AssetLoadError',
    'AssetValidationError',
]
