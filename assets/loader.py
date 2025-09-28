"""Asset loading system with format detection and validation.

This module provides the loading pipeline for assets, including format
detection, validation, and extensible loader registration for different
asset types.
"""

from abc import ABC, abstractmethod
from typing import Dict, Type, Optional, List, Callable, Any
from pathlib import Path
import mimetypes
import threading

from .types import Asset, AssetType, SpriteAsset, FontAsset, SoundAsset, ThemeAsset, DataAsset
from .exceptions import AssetLoadError, AssetFormatError, AssetValidationError


class AssetLoader(ABC):
    """Abstract base class for asset loaders.
    
    Asset loaders are responsible for loading specific types of assets
    from disk and creating the appropriate Asset objects.
    """
    
    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """Get list of supported file extensions.
        
        Returns:
            List[str]: List of supported extensions (e.g., ['.png', '.jpg'])
        """
        pass
    
    @property
    @abstractmethod
    def asset_type(self) -> AssetType:
        """Get the asset type this loader handles.
        
        Returns:
            AssetType: Asset type
        """
        pass
    
    @abstractmethod
    def can_load(self, path: str) -> bool:
        """Check if this loader can load the given asset.
        
        Args:
            path (str): Asset path
            
        Returns:
            bool: True if this loader can handle the asset
        """
        pass
    
    @abstractmethod
    def load(self, path: str) -> Asset:
        """Load an asset from the given path.
        
        Args:
            path (str): Asset path
            
        Returns:
            Asset: Loaded asset
            
        Raises:
            AssetLoadError: If loading fails
        """
        pass
    
    def validate_before_load(self, path: str) -> List[str]:
        """Validate an asset before loading.
        
        Args:
            path (str): Asset path
            
        Returns:
            List[str]: List of validation errors (empty if valid)
        """
        errors = []
        
        # Check if file exists
        if not Path(path).exists():
            errors.append(f"File does not exist: {path}")
            return errors
        
        # Check file extension
        ext = Path(path).suffix.lower()
        if ext not in self.supported_extensions:
            errors.append(f"Unsupported file extension: {ext}")
        
        return errors


class SpriteLoader(AssetLoader):
    """Loader for sprite/image assets."""
    
    @property
    def supported_extensions(self) -> List[str]:
        return ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tga', '.webp']
    
    @property
    def asset_type(self) -> AssetType:
        return AssetType.SPRITE
    
    def can_load(self, path: str) -> bool:
        """Check if this loader can load the sprite.
        
        Args:
            path (str): Asset path
            
        Returns:
            bool: True if can load
        """
        ext = Path(path).suffix.lower()
        return ext in self.supported_extensions
    
    def load(self, path: str) -> SpriteAsset:
        """Load a sprite asset.
        
        Args:
            path (str): Sprite path
            
        Returns:
            SpriteAsset: Loaded sprite asset
        """
        # Validate before loading
        errors = self.validate_before_load(path)
        if errors:
            raise AssetValidationError(path, self.asset_type.name, errors)
        
        try:
            asset = SpriteAsset(path)
            asset.load()
            return asset
        except Exception as e:
            raise AssetLoadError(path, self.asset_type.name, e)


class FontLoader(AssetLoader):
    """Loader for font assets."""
    
    @property
    def supported_extensions(self) -> List[str]:
        return ['.ttf', '.otf', '.bdf', '.fnt', '.woff', '.woff2']
    
    @property
    def asset_type(self) -> AssetType:
        return AssetType.FONT
    
    def can_load(self, path: str) -> bool:
        """Check if this loader can load the font.
        
        Args:
            path (str): Asset path
            
        Returns:
            bool: True if can load
        """
        ext = Path(path).suffix.lower()
        return ext in self.supported_extensions
    
    def load(self, path: str) -> FontAsset:
        """Load a font asset.
        
        Args:
            path (str): Font path
            
        Returns:
            FontAsset: Loaded font asset
        """
        # Validate before loading
        errors = self.validate_before_load(path)
        if errors:
            raise AssetValidationError(path, self.asset_type.name, errors)
        
        try:
            asset = FontAsset(path)
            asset.load()
            return asset
        except Exception as e:
            raise AssetLoadError(path, self.asset_type.name, e)


class SoundLoader(AssetLoader):
    """Loader for sound/audio assets."""
    
    @property
    def supported_extensions(self) -> List[str]:
        return ['.wav', '.ogg', '.mp3', '.flac', '.aiff', '.m4a']
    
    @property
    def asset_type(self) -> AssetType:
        return AssetType.SOUND
    
    def can_load(self, path: str) -> bool:
        """Check if this loader can load the sound.
        
        Args:
            path (str): Asset path
            
        Returns:
            bool: True if can load
        """
        ext = Path(path).suffix.lower()
        return ext in self.supported_extensions
    
    def load(self, path: str) -> SoundAsset:
        """Load a sound asset.
        
        Args:
            path (str): Sound path
            
        Returns:
            SoundAsset: Loaded sound asset
        """
        # Validate before loading
        errors = self.validate_before_load(path)
        if errors:
            raise AssetValidationError(path, self.asset_type.name, errors)
        
        try:
            asset = SoundAsset(path)
            asset.load()
            return asset
        except Exception as e:
            raise AssetLoadError(path, self.asset_type.name, e)


class ThemeLoader(AssetLoader):
    """Loader for UI theme assets."""
    
    @property
    def supported_extensions(self) -> List[str]:
        return ['.json', '.yaml', '.yml']
    
    @property
    def asset_type(self) -> AssetType:
        return AssetType.THEME
    
    def can_load(self, path: str) -> bool:
        """Check if this loader can load the theme.
        
        Args:
            path (str): Asset path
            
        Returns:
            bool: True if can load
        """
        ext = Path(path).suffix.lower()
        return ext in self.supported_extensions
    
    def load(self, path: str) -> ThemeAsset:
        """Load a theme asset.
        
        Args:
            path (str): Theme path
            
        Returns:
            ThemeAsset: Loaded theme asset
        """
        # Validate before loading
        errors = self.validate_before_load(path)
        if errors:
            raise AssetValidationError(path, self.asset_type.name, errors)
        
        try:
            asset = ThemeAsset(path)
            asset.load()
            return asset
        except Exception as e:
            raise AssetLoadError(path, self.asset_type.name, e)


class DataLoader(AssetLoader):
    """Loader for game data assets."""
    
    @property
    def supported_extensions(self) -> List[str]:
        return ['.json', '.yaml', '.yml', '.xml', '.csv', '.txt']
    
    @property
    def asset_type(self) -> AssetType:
        return AssetType.DATA
    
    def can_load(self, path: str) -> bool:
        """Check if this loader can load the data.
        
        Args:
            path (str): Asset path
            
        Returns:
            bool: True if can load
        """
        ext = Path(path).suffix.lower()
        return ext in self.supported_extensions
    
    def load(self, path: str) -> DataAsset:
        """Load a data asset.
        
        Args:
            path (str): Data path
            
        Returns:
            DataAsset: Loaded data asset
        """
        # Validate before loading
        errors = self.validate_before_load(path)
        if errors:
            raise AssetValidationError(path, self.asset_type.name, errors)
        
        try:
            asset = DataAsset(path)
            asset.load()
            return asset
        except Exception as e:
            raise AssetLoadError(path, self.asset_type.name, e)


class LoaderRegistry:
    """Registry for asset loaders with automatic format detection.
    
    This class manages the registration and selection of appropriate
    loaders for different asset types and file formats.
    """
    
    def __init__(self):
        """Initialize the loader registry."""
        self._loaders: List[AssetLoader] = []
        self._extension_map: Dict[str, List[AssetLoader]] = {}
        self._type_map: Dict[AssetType, List[AssetLoader]] = {}
        self._lock = threading.RLock()
        
        # Register default loaders
        self._register_default_loaders()
    
    def register_loader(self, loader: AssetLoader) -> None:
        """Register an asset loader.
        
        Args:
            loader (AssetLoader): Loader to register
        """
        with self._lock:
            if loader not in self._loaders:
                self._loaders.append(loader)
                
                # Update extension mapping
                for ext in loader.supported_extensions:
                    if ext not in self._extension_map:
                        self._extension_map[ext] = []
                    self._extension_map[ext].append(loader)
                
                # Update type mapping
                asset_type = loader.asset_type
                if asset_type not in self._type_map:
                    self._type_map[asset_type] = []
                self._type_map[asset_type].append(loader)
    
    def unregister_loader(self, loader: AssetLoader) -> None:
        """Unregister an asset loader.
        
        Args:
            loader (AssetLoader): Loader to unregister
        """
        with self._lock:
            if loader in self._loaders:
                self._loaders.remove(loader)
                
                # Update extension mapping
                for ext in loader.supported_extensions:
                    if ext in self._extension_map:
                        self._extension_map[ext] = [
                            l for l in self._extension_map[ext] if l != loader
                        ]
                        if not self._extension_map[ext]:
                            del self._extension_map[ext]
                
                # Update type mapping
                asset_type = loader.asset_type
                if asset_type in self._type_map:
                    self._type_map[asset_type] = [
                        l for l in self._type_map[asset_type] if l != loader
                    ]
                    if not self._type_map[asset_type]:
                        del self._type_map[asset_type]
    
    def get_loader(self, path: str, asset_type: Optional[AssetType] = None) -> Optional[AssetLoader]:
        """Get the appropriate loader for an asset.
        
        Args:
            path (str): Asset path
            asset_type (AssetType, optional): Hint for asset type
            
        Returns:
            AssetLoader: Appropriate loader or None if not found
        """
        with self._lock:
            # Try to find loader by extension first
            ext = Path(path).suffix.lower()
            candidates = self._extension_map.get(ext, [])
            
            # Filter by asset type if provided
            if asset_type:
                candidates = [l for l in candidates if l.asset_type == asset_type]
            
            # Find first loader that can handle this asset
            for loader in candidates:
                if loader.can_load(path):
                    return loader
            
            # Fallback: try all loaders
            for loader in self._loaders:
                if asset_type and loader.asset_type != asset_type:
                    continue
                if loader.can_load(path):
                    return loader
            
            return None
    
    def load_asset(self, path: str, asset_type: Optional[AssetType] = None) -> Asset:
        """Load an asset using the appropriate loader.
        
        Args:
            path (str): Asset path
            asset_type (AssetType, optional): Hint for asset type
            
        Returns:
            Asset: Loaded asset
            
        Raises:
            AssetLoadError: If no suitable loader found or loading fails
        """
        loader = self.get_loader(path, asset_type)
        if not loader:
            raise AssetLoadError(
                path, 
                asset_type.name if asset_type else "unknown",
                Exception(f"No suitable loader found for {path}")
            )
        
        return loader.load(path)
    
    def get_supported_extensions(self, asset_type: Optional[AssetType] = None) -> List[str]:
        """Get list of supported file extensions.
        
        Args:
            asset_type (AssetType, optional): Filter by asset type
            
        Returns:
            List[str]: List of supported extensions
        """
        with self._lock:
            if asset_type:
                loaders = self._type_map.get(asset_type, [])
                extensions = set()
                for loader in loaders:
                    extensions.update(loader.supported_extensions)
                return sorted(extensions)
            else:
                return sorted(self._extension_map.keys())
    
    def get_loaders_for_type(self, asset_type: AssetType) -> List[AssetLoader]:
        """Get all loaders for a specific asset type.
        
        Args:
            asset_type (AssetType): Asset type
            
        Returns:
            List[AssetLoader]: List of loaders
        """
        with self._lock:
            return self._type_map.get(asset_type, []).copy()
    
    def detect_asset_type(self, path: str) -> Optional[AssetType]:
        """Detect asset type from file path.
        
        Args:
            path (str): Asset path
            
        Returns:
            AssetType: Detected asset type or None
        """
        loader = self.get_loader(path)
        return loader.asset_type if loader else None
    
    def _register_default_loaders(self) -> None:
        """Register the default asset loaders."""
        self.register_loader(SpriteLoader())
        self.register_loader(FontLoader())
        self.register_loader(SoundLoader())
        self.register_loader(ThemeLoader())
        self.register_loader(DataLoader())


# Global loader registry instance
_global_registry: Optional[LoaderRegistry] = None


def get_loader_registry() -> LoaderRegistry:
    """Get the global loader registry.
    
    Returns:
        LoaderRegistry: Global loader registry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = LoaderRegistry()
    return _global_registry


def register_loader(loader: AssetLoader) -> None:
    """Register a loader with the global registry.
    
    Args:
        loader (AssetLoader): Loader to register
    """
    get_loader_registry().register_loader(loader)


def load_asset(path: str, asset_type: Optional[AssetType] = None) -> Asset:
    """Load an asset using the global registry.
    
    Args:
        path (str): Asset path
        asset_type (AssetType, optional): Asset type hint
        
    Returns:
        Asset: Loaded asset
    """
    return get_loader_registry().load_asset(path, asset_type)
