"""Asset type definitions and base classes.

This module defines the various types of assets that can be managed by
the asset system, including sprites, fonts, sounds, themes, and data files.
Each asset type provides specific functionality for its resource type.
"""

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Dict, Optional, List, Union
from dataclasses import dataclass, field
from pathlib import Path
import json
import time

from rendering import Color


class AssetType(Enum):
    """Enumeration of supported asset types."""
    
    SPRITE = auto()      # Image/sprite assets (PNG, JPG, BMP)
    FONT = auto()        # Font assets (TTF, OTF, BDF)
    SOUND = auto()       # Audio assets (WAV, OGG, MP3)
    MUSIC = auto()       # Music assets (longer audio files)
    THEME = auto()       # UI theme definitions (JSON, YAML)
    DATA = auto()        # Game data files (JSON, YAML, XML)
    CONFIG = auto()      # Configuration files
    SHADER = auto()      # Shader programs (GLSL, HLSL)
    MODEL = auto()       # 3D model assets (OBJ, FBX)
    ANIMATION = auto()   # Animation data
    TILESET = auto()     # Tileset definitions
    MAP = auto()         # Game map data
    SCRIPT = auto()      # Script files (Python, Lua)
    BINARY = auto()      # Binary data files
    TEXT = auto()        # Plain text files


@dataclass
class AssetMetadata:
    """Metadata information for an asset."""
    
    path: str
    asset_type: AssetType
    size: int = 0
    modified_time: float = 0.0
    checksum: str = ""
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize metadata from file system if path exists."""
        path_obj = Path(self.path)
        if path_obj.exists():
            stat = path_obj.stat()
            self.size = stat.st_size
            self.modified_time = stat.st_mtime


class Asset(ABC):
    """Abstract base class for all asset types.
    
    This class provides the common interface and functionality that all
    asset types must implement, including loading, validation, and
    resource management.
    """
    
    def __init__(self, path: str, asset_type: AssetType, metadata: Optional[AssetMetadata] = None):
        """Initialize the asset.
        
        Args:
            path (str): Path to the asset file
            asset_type (AssetType): Type of this asset
            metadata (AssetMetadata, optional): Asset metadata
        """
        self.path = path
        self.asset_type = asset_type
        self.metadata = metadata or AssetMetadata(path, asset_type)
        
        # Asset state
        self.loaded = False
        self.load_time = 0.0
        self.last_accessed = 0.0
        self.access_count = 0
        
        # Asset data (populated by subclasses)
        self._data: Any = None
        self._dependencies: List['Asset'] = []
    
    @property
    def data(self) -> Any:
        """Get the asset data, loading if necessary."""
        if not self.loaded:
            self.load()
        
        self.last_accessed = time.time()
        self.access_count += 1
        return self._data
    
    @property
    def dependencies(self) -> List['Asset']:
        """Get asset dependencies."""
        return self._dependencies
    
    @abstractmethod
    def load(self) -> None:
        """Load the asset from disk.
        
        This method should be implemented by subclasses to handle
        the specific loading logic for their asset type.
        """
        pass
    
    @abstractmethod
    def unload(self) -> None:
        """Unload the asset from memory.
        
        This method should be implemented by subclasses to handle
        proper cleanup of their asset data.
        """
        pass
    
    @abstractmethod
    def validate(self) -> List[str]:
        """Validate the asset data.
        
        Returns:
            List[str]: List of validation error messages (empty if valid)
        """
        pass
    
    def reload(self) -> None:
        """Reload the asset from disk."""
        if self.loaded:
            self.unload()
        self.load()
    
    def is_stale(self) -> bool:
        """Check if the asset is stale (file modified since load).
        
        Returns:
            bool: True if asset needs reloading
        """
        if not self.loaded:
            return True
        
        path_obj = Path(self.path)
        if not path_obj.exists():
            return True
        
        return path_obj.stat().st_mtime > self.metadata.modified_time
    
    def get_memory_usage(self) -> int:
        """Get estimated memory usage in bytes.
        
        Returns:
            int: Estimated memory usage
        """
        # Base implementation - subclasses should override for accuracy
        if not self.loaded or self._data is None:
            return 0
        
        # Rough estimate based on object size
        import sys
        return sys.getsizeof(self._data)
    
    def __repr__(self) -> str:
        """String representation of the asset."""
        return f"{self.__class__.__name__}(path='{self.path}', loaded={self.loaded})"


class SpriteAsset(Asset):
    """Asset class for sprite/image resources."""
    
    def __init__(self, path: str, metadata: Optional[AssetMetadata] = None):
        """Initialize sprite asset.
        
        Args:
            path (str): Path to the sprite file
            metadata (AssetMetadata, optional): Asset metadata
        """
        super().__init__(path, AssetType.SPRITE, metadata)
        
        # Sprite-specific properties
        self.width = 0
        self.height = 0
        self.channels = 0
        self.format = ""
    
    def load(self) -> None:
        """Load the sprite from disk."""
        try:
            # For now, we'll use a placeholder implementation
            # In a real implementation, this would use PIL, pygame, or similar
            path_obj = Path(self.path)
            
            if not path_obj.exists():
                raise FileNotFoundError(f"Sprite file not found: {self.path}")
            
            # Mock sprite data - in reality this would be pixel data
            self._data = {
                'path': self.path,
                'format': path_obj.suffix.lower(),
                'size': path_obj.stat().st_size,
                'loaded_at': time.time()
            }
            
            # Update metadata
            self.format = path_obj.suffix.lower()
            self.loaded = True
            self.load_time = time.time()
            
        except Exception as e:
            from .exceptions import AssetLoadError
            raise AssetLoadError(self.path, self.asset_type.name, e)
    
    def unload(self) -> None:
        """Unload the sprite from memory."""
        self._data = None
        self.loaded = False
        self.width = 0
        self.height = 0
        self.channels = 0
    
    def validate(self) -> List[str]:
        """Validate the sprite asset.
        
        Returns:
            List[str]: List of validation errors
        """
        errors = []
        
        if not Path(self.path).exists():
            errors.append(f"Sprite file does not exist: {self.path}")
            return errors
        
        # Check file extension
        valid_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tga'}
        if Path(self.path).suffix.lower() not in valid_extensions:
            errors.append(f"Unsupported sprite format: {Path(self.path).suffix}")
        
        # Check file size
        if Path(self.path).stat().st_size == 0:
            errors.append("Sprite file is empty")
        
        return errors


class FontAsset(Asset):
    """Asset class for font resources."""
    
    def __init__(self, path: str, metadata: Optional[AssetMetadata] = None):
        """Initialize font asset.
        
        Args:
            path (str): Path to the font file
            metadata (AssetMetadata, optional): Asset metadata
        """
        super().__init__(path, AssetType.FONT, metadata)
        
        # Font-specific properties
        self.family_name = ""
        self.style = ""
        self.size = 12
        self.scalable = False
    
    def load(self) -> None:
        """Load the font from disk."""
        try:
            path_obj = Path(self.path)
            
            if not path_obj.exists():
                raise FileNotFoundError(f"Font file not found: {self.path}")
            
            # Mock font data - in reality this would use freetype, pygame.font, etc.
            self._data = {
                'path': self.path,
                'format': path_obj.suffix.lower(),
                'family': path_obj.stem,
                'loaded_at': time.time()
            }
            
            # Update properties
            self.family_name = path_obj.stem
            self.scalable = path_obj.suffix.lower() in {'.ttf', '.otf'}
            self.loaded = True
            self.load_time = time.time()
            
        except Exception as e:
            from .exceptions import AssetLoadError
            raise AssetLoadError(self.path, self.asset_type.name, e)
    
    def unload(self) -> None:
        """Unload the font from memory."""
        self._data = None
        self.loaded = False
        self.family_name = ""
        self.style = ""
    
    def validate(self) -> List[str]:
        """Validate the font asset.
        
        Returns:
            List[str]: List of validation errors
        """
        errors = []
        
        if not Path(self.path).exists():
            errors.append(f"Font file does not exist: {self.path}")
            return errors
        
        # Check file extension
        valid_extensions = {'.ttf', '.otf', '.bdf', '.fnt'}
        if Path(self.path).suffix.lower() not in valid_extensions:
            errors.append(f"Unsupported font format: {Path(self.path).suffix}")
        
        return errors


class SoundAsset(Asset):
    """Asset class for sound/audio resources."""
    
    def __init__(self, path: str, metadata: Optional[AssetMetadata] = None):
        """Initialize sound asset.
        
        Args:
            path (str): Path to the sound file
            metadata (AssetMetadata, optional): Asset metadata
        """
        super().__init__(path, AssetType.SOUND, metadata)
        
        # Sound-specific properties
        self.duration = 0.0
        self.sample_rate = 0
        self.channels = 0
        self.format = ""
    
    def load(self) -> None:
        """Load the sound from disk."""
        try:
            path_obj = Path(self.path)
            
            if not path_obj.exists():
                raise FileNotFoundError(f"Sound file not found: {self.path}")
            
            # Mock sound data - in reality this would use pygame.mixer, pydub, etc.
            self._data = {
                'path': self.path,
                'format': path_obj.suffix.lower(),
                'size': path_obj.stat().st_size,
                'loaded_at': time.time()
            }
            
            self.format = path_obj.suffix.lower()
            self.loaded = True
            self.load_time = time.time()
            
        except Exception as e:
            from .exceptions import AssetLoadError
            raise AssetLoadError(self.path, self.asset_type.name, e)
    
    def unload(self) -> None:
        """Unload the sound from memory."""
        self._data = None
        self.loaded = False
        self.duration = 0.0
        self.sample_rate = 0
        self.channels = 0
    
    def validate(self) -> List[str]:
        """Validate the sound asset.
        
        Returns:
            List[str]: List of validation errors
        """
        errors = []
        
        if not Path(self.path).exists():
            errors.append(f"Sound file does not exist: {self.path}")
            return errors
        
        # Check file extension
        valid_extensions = {'.wav', '.ogg', '.mp3', '.flac', '.aiff'}
        if Path(self.path).suffix.lower() not in valid_extensions:
            errors.append(f"Unsupported sound format: {Path(self.path).suffix}")
        
        return errors


class ThemeAsset(Asset):
    """Asset class for UI theme resources."""
    
    def __init__(self, path: str, metadata: Optional[AssetMetadata] = None):
        """Initialize theme asset.
        
        Args:
            path (str): Path to the theme file
            metadata (AssetMetadata, optional): Asset metadata
        """
        super().__init__(path, AssetType.THEME, metadata)
        
        # Theme-specific properties
        self.theme_name = ""
        self.version = "1.0"
        self.colors: Dict[str, Color] = {}
        self.fonts: Dict[str, str] = {}
        self.styles: Dict[str, Dict[str, Any]] = {}
    
    def load(self) -> None:
        """Load the theme from disk."""
        try:
            path_obj = Path(self.path)
            
            if not path_obj.exists():
                raise FileNotFoundError(f"Theme file not found: {self.path}")
            
            # Load theme data from JSON
            with open(path_obj, 'r', encoding='utf-8') as f:
                theme_data = json.load(f)
            
            self._data = theme_data
            
            # Parse theme properties
            self.theme_name = theme_data.get('name', path_obj.stem)
            self.version = theme_data.get('version', '1.0')
            
            # Parse colors
            colors_data = theme_data.get('colors', {})
            for name, color_value in colors_data.items():
                if isinstance(color_value, str):
                    # Hex color
                    self.colors[name] = Color.from_hex(color_value)
                elif isinstance(color_value, list) and len(color_value) >= 3:
                    # RGB array
                    self.colors[name] = Color(color_value[0], color_value[1], color_value[2])
            
            # Parse fonts and styles
            self.fonts = theme_data.get('fonts', {})
            self.styles = theme_data.get('styles', {})
            
            self.loaded = True
            self.load_time = time.time()
            
        except Exception as e:
            from .exceptions import AssetLoadError
            raise AssetLoadError(self.path, self.asset_type.name, e)
    
    def unload(self) -> None:
        """Unload the theme from memory."""
        self._data = None
        self.loaded = False
        self.theme_name = ""
        self.colors.clear()
        self.fonts.clear()
        self.styles.clear()
    
    def validate(self) -> List[str]:
        """Validate the theme asset.
        
        Returns:
            List[str]: List of validation errors
        """
        errors = []
        
        if not Path(self.path).exists():
            errors.append(f"Theme file does not exist: {self.path}")
            return errors
        
        # Check file extension
        if Path(self.path).suffix.lower() not in {'.json', '.yaml', '.yml'}:
            errors.append(f"Unsupported theme format: {Path(self.path).suffix}")
            return errors
        
        # Validate JSON structure
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                theme_data = json.load(f)
            
            # Check required fields
            if 'name' not in theme_data:
                errors.append("Theme missing required 'name' field")
            
            # Validate colors
            colors = theme_data.get('colors', {})
            for color_name, color_value in colors.items():
                if isinstance(color_value, str):
                    try:
                        Color.from_hex(color_value)
                    except ValueError:
                        errors.append(f"Invalid hex color '{color_name}': {color_value}")
                elif isinstance(color_value, list):
                    if len(color_value) < 3 or not all(isinstance(c, int) for c in color_value[:3]):
                        errors.append(f"Invalid RGB color '{color_name}': {color_value}")
                else:
                    errors.append(f"Invalid color format '{color_name}': {color_value}")
        
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON format: {e}")
        except Exception as e:
            errors.append(f"Theme validation error: {e}")
        
        return errors


class DataAsset(Asset):
    """Asset class for game data resources."""
    
    def __init__(self, path: str, metadata: Optional[AssetMetadata] = None):
        """Initialize data asset.
        
        Args:
            path (str): Path to the data file
            metadata (AssetMetadata, optional): Asset metadata
        """
        super().__init__(path, AssetType.DATA, metadata)
        
        # Data-specific properties
        self.format = ""
        self.schema_version = ""
    
    def load(self) -> None:
        """Load the data from disk."""
        try:
            path_obj = Path(self.path)
            
            if not path_obj.exists():
                raise FileNotFoundError(f"Data file not found: {self.path}")
            
            self.format = path_obj.suffix.lower()
            
            # Load based on format
            if self.format == '.json':
                with open(path_obj, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
            elif self.format in {'.yaml', '.yml'}:
                try:
                    import yaml
                    with open(path_obj, 'r', encoding='utf-8') as f:
                        self._data = yaml.safe_load(f)
                except ImportError:
                    raise ImportError("PyYAML required for YAML data files")
            else:
                # Plain text or binary
                mode = 'r' if self.format in {'.txt', '.csv', '.xml'} else 'rb'
                with open(path_obj, mode, encoding='utf-8' if mode == 'r' else None) as f:
                    self._data = f.read()
            
            # Extract schema version if available
            if isinstance(self._data, dict):
                self.schema_version = self._data.get('version', '')
            
            self.loaded = True
            self.load_time = time.time()
            
        except Exception as e:
            from .exceptions import AssetLoadError
            raise AssetLoadError(self.path, self.asset_type.name, e)
    
    def unload(self) -> None:
        """Unload the data from memory."""
        self._data = None
        self.loaded = False
        self.format = ""
        self.schema_version = ""
    
    def validate(self) -> List[str]:
        """Validate the data asset.
        
        Returns:
            List[str]: List of validation errors
        """
        errors = []
        
        if not Path(self.path).exists():
            errors.append(f"Data file does not exist: {self.path}")
            return errors
        
        # Validate based on format
        path_obj = Path(self.path)
        format_ext = path_obj.suffix.lower()
        
        if format_ext == '.json':
            try:
                with open(path_obj, 'r', encoding='utf-8') as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                errors.append(f"Invalid JSON format: {e}")
        elif format_ext in {'.yaml', '.yml'}:
            try:
                import yaml
                with open(path_obj, 'r', encoding='utf-8') as f:
                    yaml.safe_load(f)
            except ImportError:
                errors.append("PyYAML required for YAML validation")
            except yaml.YAMLError as e:
                errors.append(f"Invalid YAML format: {e}")
        
        return errors
