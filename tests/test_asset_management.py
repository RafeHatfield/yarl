"""Comprehensive tests for the asset management system.

This module contains tests for all components of the asset management
system including types, cache, loader, discovery, and manager.
"""

import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from assets import (
    AssetManager, get_asset_manager, initialize_asset_manager,
    AssetType, Asset, SpriteAsset, FontAsset, SoundAsset, ThemeAsset, DataAsset,
    AssetLoader, LoaderRegistry, get_loader_registry,
    AssetCache, CachePolicy, CacheStats,
    ResourceDiscovery, AssetCatalog, ScanResult, AssetMetadata,
    AssetError, AssetNotFoundError, AssetLoadError, AssetValidationError
)


class TestAssetTypes:
    """Test cases for asset type classes."""
    
    def test_asset_metadata_creation(self):
        """Test asset metadata creation."""
        metadata = AssetMetadata("test.png", AssetType.SPRITE)
        assert metadata.path == "test.png"
        assert metadata.asset_type == AssetType.SPRITE
        assert metadata.size == 0
        assert metadata.dependencies == []
        assert metadata.tags == []
        assert isinstance(metadata.properties, dict)
    
    def test_sprite_asset_creation(self):
        """Test sprite asset creation."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'fake png data')
            temp_path = f.name
        
        try:
            sprite = SpriteAsset(temp_path)
            assert sprite.path == temp_path
            assert sprite.asset_type == AssetType.SPRITE
            assert not sprite.loaded
            assert sprite.width == 0
            assert sprite.height == 0
        finally:
            os.unlink(temp_path)
    
    def test_sprite_asset_load(self):
        """Test sprite asset loading."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'fake png data')
            temp_path = f.name
        
        try:
            sprite = SpriteAsset(temp_path)
            sprite.load()
            
            assert sprite.loaded
            assert sprite.data is not None
            assert sprite.format == '.png'
            assert sprite.load_time > 0
        finally:
            os.unlink(temp_path)
    
    def test_sprite_asset_validation(self):
        """Test sprite asset validation."""
        # Valid sprite
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'fake png data')
            temp_path = f.name
        
        try:
            sprite = SpriteAsset(temp_path)
            errors = sprite.validate()
            assert len(errors) == 0
        finally:
            os.unlink(temp_path)
        
        # Invalid sprite (non-existent file)
        sprite = SpriteAsset("nonexistent.png")
        errors = sprite.validate()
        assert len(errors) > 0
        assert "does not exist" in errors[0]
    
    def test_font_asset_creation(self):
        """Test font asset creation."""
        with tempfile.NamedTemporaryFile(suffix='.ttf', delete=False) as f:
            f.write(b'fake ttf data')
            temp_path = f.name
        
        try:
            font = FontAsset(temp_path)
            assert font.asset_type == AssetType.FONT
            assert font.family_name == ""
            assert font.size == 12
            assert not font.scalable
        finally:
            os.unlink(temp_path)
    
    def test_sound_asset_creation(self):
        """Test sound asset creation."""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b'fake wav data')
            temp_path = f.name
        
        try:
            sound = SoundAsset(temp_path)
            assert sound.asset_type == AssetType.SOUND
            assert sound.duration == 0.0
            assert sound.sample_rate == 0
        finally:
            os.unlink(temp_path)
    
    def test_theme_asset_creation(self):
        """Test theme asset creation."""
        theme_data = {
            "name": "test_theme",
            "version": "1.0",
            "colors": {
                "primary": "#ff0000",
                "secondary": [0, 255, 0]
            },
            "fonts": {
                "default": "arial.ttf"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(theme_data, f)
            temp_path = f.name
        
        try:
            theme = ThemeAsset(temp_path)
            theme.load()
            
            assert theme.loaded
            assert theme.theme_name == "test_theme"
            assert theme.version == "1.0"
            assert len(theme.colors) == 2
            assert "default" in theme.fonts
        finally:
            os.unlink(temp_path)
    
    def test_data_asset_json(self):
        """Test data asset with JSON format."""
        data = {"test": "value", "number": 42}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name
        
        try:
            asset = DataAsset(temp_path)
            asset.load()
            
            assert asset.loaded
            assert asset.format == '.json'
            assert asset.data == data
        finally:
            os.unlink(temp_path)


class TestAssetCache:
    """Test cases for asset cache."""
    
    def test_cache_creation(self):
        """Test cache creation with default settings."""
        cache = AssetCache()
        assert cache.max_memory == 100 * 1024 * 1024
        assert cache.max_assets == 1000
        assert cache.default_policy == CachePolicy.LRU
        assert cache.enable_hot_reload == True
    
    def test_cache_put_get(self):
        """Test basic cache put/get operations."""
        cache = AssetCache()
        
        # Create mock asset
        asset = Mock(spec=Asset)
        asset.get_memory_usage.return_value = 1024
        asset.is_stale.return_value = False
        
        # Create mock metadata
        mock_metadata = Mock()
        mock_metadata.modified_time = 0.0
        asset.metadata = mock_metadata
        
        # Put asset in cache
        cache.put("test.png", asset)
        
        # Get asset from cache
        retrieved = cache.get("test.png")
        assert retrieved == asset
        assert cache.stats.hits == 1
        assert cache.stats.misses == 0
    
    def test_cache_miss(self):
        """Test cache miss."""
        cache = AssetCache()
        
        result = cache.get("nonexistent.png")
        assert result is None
        assert cache.stats.hits == 0
        assert cache.stats.misses == 1
    
    def test_cache_remove(self):
        """Test cache removal."""
        cache = AssetCache()
        
        # Create and add mock asset
        asset = Mock(spec=Asset)
        asset.get_memory_usage.return_value = 1024
        asset.loaded = True
        
        # Create mock metadata
        mock_metadata = Mock()
        mock_metadata.modified_time = 0.0
        asset.metadata = mock_metadata
        
        cache.put("test.png", asset)
        assert cache.contains("test.png")
        
        # Remove asset
        removed = cache.remove("test.png")
        assert removed == True
        assert not cache.contains("test.png")
        asset.unload.assert_called_once()
    
    def test_cache_clear(self):
        """Test cache clearing."""
        cache = AssetCache()
        
        # Add multiple assets
        for i in range(3):
            asset = Mock(spec=Asset)
            asset.get_memory_usage.return_value = 1024
            asset.loaded = True
            
            # Create mock metadata
            mock_metadata = Mock()
            mock_metadata.modified_time = 0.0
            asset.metadata = mock_metadata
            
            cache.put(f"test{i}.png", asset)
        
        assert cache.get_asset_count() == 3
        
        # Clear cache
        cache.clear()
        assert cache.get_asset_count() == 0
        assert cache.stats.memory_usage == 0
    
    def test_cache_stats(self):
        """Test cache statistics."""
        cache = AssetCache()
        
        # Initial stats
        stats = cache.get_stats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.hit_rate == 0.0
        
        # Add some hits and misses
        asset = Mock(spec=Asset)
        asset.get_memory_usage.return_value = 1024
        asset.is_stale.return_value = False
        
        # Create mock metadata
        mock_metadata = Mock()
        mock_metadata.modified_time = 0.0
        asset.metadata = mock_metadata
        
        cache.put("test.png", asset)
        cache.get("test.png")  # Hit
        cache.get("missing.png")  # Miss
        
        stats = cache.get_stats()
        assert stats.hits == 1
        assert stats.misses == 1
        assert stats.hit_rate == 0.5


class TestAssetLoader:
    """Test cases for asset loaders."""
    
    def test_loader_registry_creation(self):
        """Test loader registry creation."""
        registry = LoaderRegistry()
        assert len(registry._loaders) > 0  # Should have default loaders
        assert '.png' in registry._extension_map
        assert AssetType.SPRITE in registry._type_map
    
    def test_get_loader_by_extension(self):
        """Test getting loader by file extension."""
        registry = LoaderRegistry()
        
        loader = registry.get_loader("test.png")
        assert loader is not None
        assert loader.asset_type == AssetType.SPRITE
        
        loader = registry.get_loader("test.ttf")
        assert loader is not None
        assert loader.asset_type == AssetType.FONT
    
    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        registry = LoaderRegistry()
        
        # All extensions
        all_extensions = registry.get_supported_extensions()
        assert '.png' in all_extensions
        assert '.ttf' in all_extensions
        assert '.json' in all_extensions
        
        # Sprite extensions only
        sprite_extensions = registry.get_supported_extensions(AssetType.SPRITE)
        assert '.png' in sprite_extensions
        assert '.ttf' not in sprite_extensions
    
    def test_detect_asset_type(self):
        """Test asset type detection."""
        registry = LoaderRegistry()
        
        assert registry.detect_asset_type("test.png") == AssetType.SPRITE
        assert registry.detect_asset_type("test.ttf") == AssetType.FONT
        assert registry.detect_asset_type("test.wav") == AssetType.SOUND
        assert registry.detect_asset_type("theme.json") == AssetType.THEME  # Could be theme or data
    
    def test_load_asset_with_registry(self):
        """Test loading asset through registry."""
        registry = LoaderRegistry()
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'fake png data')
            temp_path = f.name
        
        try:
            asset = registry.load_asset(temp_path, AssetType.SPRITE)
            assert isinstance(asset, SpriteAsset)
            assert asset.loaded
        finally:
            os.unlink(temp_path)


class TestResourceDiscovery:
    """Test cases for resource discovery."""
    
    def test_discovery_creation(self):
        """Test resource discovery creation."""
        discovery = ResourceDiscovery()
        assert isinstance(discovery.catalog, AssetCatalog)
        assert len(discovery.ignore_patterns) > 0
        assert '.*' in discovery.ignore_patterns  # Hidden files
    
    def test_scan_single_file(self):
        """Test scanning a single file."""
        discovery = ResourceDiscovery()
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'fake png data')
            temp_path = f.name
        
        try:
            result = discovery.scan_path(temp_path)
            assert result.total_files == 1
            assert result.assets_found == 1
            assert AssetType.SPRITE in result.assets_by_type
        finally:
            os.unlink(temp_path)
    
    def test_scan_directory(self):
        """Test scanning a directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            (Path(temp_dir) / "test.png").write_bytes(b'fake png')
            (Path(temp_dir) / "test.ttf").write_bytes(b'fake ttf')
            (Path(temp_dir) / "readme.txt").write_text("readme")
            
            discovery = ResourceDiscovery()
            result = discovery.scan_path(temp_dir)
            
            assert result.total_files == 3
            assert result.assets_found >= 2  # png and ttf should be detected
    
    def test_catalog_operations(self):
        """Test asset catalog operations."""
        catalog = AssetCatalog()
        
        # Add asset
        metadata = AssetMetadata("test.png", AssetType.SPRITE, size=1024)
        catalog.add_asset("test.png", metadata)
        
        assert catalog.get_asset_count() == 1
        assert catalog.get_total_size() == 1024
        
        # Get by type
        sprites = catalog.get_assets_by_type(AssetType.SPRITE)
        assert len(sprites) == 1
        assert sprites[0].path == "test.png"
        
        # Remove asset
        removed = catalog.remove_asset("test.png")
        assert removed == True
        assert catalog.get_asset_count() == 0
    
    def test_catalog_serialization(self):
        """Test catalog serialization/deserialization."""
        catalog = AssetCatalog()
        metadata = AssetMetadata("test.png", AssetType.SPRITE, size=1024, tags=["ui"])
        catalog.add_asset("test.png", metadata)
        
        # Serialize
        data = catalog.to_dict()
        assert 'assets' in data
        assert 'test.png' in data['assets']
        
        # Deserialize
        new_catalog = AssetCatalog.from_dict(data)
        assert new_catalog.get_asset_count() == 1
        assert "test.png" in new_catalog.assets


class TestAssetManager:
    """Test cases for asset manager."""
    
    def test_manager_creation(self):
        """Test asset manager creation."""
        manager = AssetManager(auto_discover=False)
        assert isinstance(manager.cache, AssetCache)
        assert isinstance(manager.loader_registry, LoaderRegistry)
        assert isinstance(manager.discovery, ResourceDiscovery)
    
    def test_manager_load_asset(self):
        """Test loading asset through manager."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test asset
            asset_path = Path(temp_dir) / "test.png"
            asset_path.write_bytes(b'fake png data')
            
            manager = AssetManager(asset_paths=[temp_dir], auto_discover=False)
            
            # Load asset
            asset = manager.load("test.png")
            assert isinstance(asset, SpriteAsset)
            assert asset.loaded
            assert manager.is_loaded("test.png")
    
    def test_manager_asset_not_found(self):
        """Test asset not found error."""
        manager = AssetManager(asset_paths=[], auto_discover=False)
        
        with pytest.raises(AssetNotFoundError):
            manager.load("nonexistent.png")
    
    def test_manager_aliases(self):
        """Test asset aliases."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test asset
            asset_path = Path(temp_dir) / "test.png"
            asset_path.write_bytes(b'fake png data')
            
            manager = AssetManager(asset_paths=[temp_dir], auto_discover=False)
            
            # Add alias
            manager.add_alias("player_sprite", "test.png")
            
            # Load using alias
            asset = manager.load("player_sprite")
            assert isinstance(asset, SpriteAsset)
            
            # Check aliases
            aliases = manager.get_aliases()
            assert "player_sprite" in aliases
            assert aliases["player_sprite"] == "test.png"
    
    def test_manager_unload(self):
        """Test asset unloading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test asset
            asset_path = Path(temp_dir) / "test.png"
            asset_path.write_bytes(b'fake png data')
            
            manager = AssetManager(asset_paths=[temp_dir], auto_discover=False)
            
            # Load and unload
            asset = manager.load("test.png")
            assert manager.is_loaded("test.png")
            
            unloaded = manager.unload("test.png")
            assert unloaded == True
            assert not manager.is_loaded("test.png")
    
    def test_manager_reload(self):
        """Test asset reloading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test asset
            asset_path = Path(temp_dir) / "test.png"
            asset_path.write_bytes(b'fake png data')
            
            manager = AssetManager(asset_paths=[temp_dir], auto_discover=False)
            
            # Load asset
            asset1 = manager.load("test.png")
            
            # Reload asset
            asset2 = manager.reload("test.png")
            
            # Should be different instances but same type
            assert isinstance(asset2, SpriteAsset)
            assert asset2.loaded
    
    def test_manager_cache_operations(self):
        """Test cache operations through manager."""
        manager = AssetManager(auto_discover=False)
        
        # Get cache stats
        stats = manager.get_cache_stats()
        assert isinstance(stats, CacheStats)
        
        # Clear cache
        manager.clear_cache()
        assert manager.get_loaded_asset_count() == 0
    
    def test_manager_discovery(self):
        """Test asset discovery through manager."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test assets
            (Path(temp_dir) / "test.png").write_bytes(b'fake png')
            (Path(temp_dir) / "test.ttf").write_bytes(b'fake ttf')
            
            manager = AssetManager(asset_paths=[temp_dir], auto_discover=False)
            
            # Discover assets
            result = manager.discover_assets()
            assert result.assets_found >= 2
            
            # Get catalog
            catalog = manager.get_catalog()
            assert catalog.get_asset_count() >= 2
    
    def test_manager_find_assets(self):
        """Test finding assets by criteria."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test assets
            (Path(temp_dir) / "player.png").write_bytes(b'fake png')
            (Path(temp_dir) / "enemy.png").write_bytes(b'fake png')
            
            manager = AssetManager(asset_paths=[temp_dir], auto_discover=True)
            
            # Find by type
            sprites = manager.find_assets(asset_type=AssetType.SPRITE)
            assert len(sprites) >= 2
            
            # Find by query
            player_assets = manager.find_assets(query="player")
            assert len(player_assets) >= 1


class TestGlobalFunctions:
    """Test cases for global functions."""
    
    def test_get_asset_manager(self):
        """Test getting global asset manager."""
        manager1 = get_asset_manager()
        manager2 = get_asset_manager()
        assert manager1 is manager2  # Should be singleton
    
    def test_initialize_asset_manager(self):
        """Test initializing asset manager with custom settings."""
        manager = initialize_asset_manager(
            asset_paths=['custom_path'],
            cache_size=50 * 1024 * 1024,
            auto_discover=False
        )
        assert 'custom_path' in manager.asset_paths
        assert manager.cache.max_memory == 50 * 1024 * 1024


class TestAssetExceptions:
    """Test cases for asset exceptions."""
    
    def test_asset_error(self):
        """Test base asset error."""
        error = AssetError("Test error", "test.png", "SPRITE")
        assert str(error) == "Test error | Asset: test.png | Type: SPRITE"
        assert error.asset_path == "test.png"
        assert error.asset_type == "SPRITE"
    
    def test_asset_not_found_error(self):
        """Test asset not found error."""
        error = AssetNotFoundError("test.png", "SPRITE", ["path1", "path2"])
        assert "not found" in str(error)
        assert "path1" in str(error)
        assert error.search_paths == ["path1", "path2"]
    
    def test_asset_load_error(self):
        """Test asset load error."""
        cause = ValueError("Invalid format")
        error = AssetLoadError("test.png", "SPRITE", cause)
        assert "Failed to load" in str(error)
        assert "ValueError" in str(error)
        assert error.cause == cause
    
    def test_asset_validation_error(self):
        """Test asset validation error."""
        errors = ["Error 1", "Error 2"]
        error = AssetValidationError("test.png", "SPRITE", errors)
        assert "validation failed" in str(error)
        assert "Error 1" in str(error)
        assert error.validation_errors == errors
