"""Resource discovery system for asset scanning and organization.

This module provides functionality for discovering, scanning, and organizing
assets within the file system, including metadata extraction and asset
cataloging.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Set, Callable, Any, Iterator
from dataclasses import dataclass, field, asdict
import threading
import time

from .types import AssetType, AssetMetadata
from .loader import get_loader_registry
from .exceptions import AssetError


@dataclass
class ScanResult:
    """Result of an asset discovery scan."""
    
    total_files: int = 0
    assets_found: int = 0
    errors: List[str] = field(default_factory=list)
    scan_time: float = 0.0
    assets_by_type: Dict[AssetType, int] = field(default_factory=dict)
    
    def add_asset(self, asset_type: AssetType) -> None:
        """Add an asset to the scan results.
        
        Args:
            asset_type (AssetType): Type of asset found
        """
        self.assets_found += 1
        if asset_type not in self.assets_by_type:
            self.assets_by_type[asset_type] = 0
        self.assets_by_type[asset_type] += 1
    
    def add_error(self, error: str) -> None:
        """Add an error to the scan results.
        
        Args:
            error (str): Error message
        """
        self.errors.append(error)


@dataclass
class AssetCatalog:
    """Catalog of discovered assets with metadata."""
    
    assets: Dict[str, AssetMetadata] = field(default_factory=dict)
    scan_paths: List[str] = field(default_factory=list)
    last_scan: float = 0.0
    version: str = "1.0"
    
    def add_asset(self, path: str, metadata: AssetMetadata) -> None:
        """Add an asset to the catalog.
        
        Args:
            path (str): Asset path
            metadata (AssetMetadata): Asset metadata
        """
        self.assets[path] = metadata
    
    def remove_asset(self, path: str) -> bool:
        """Remove an asset from the catalog.
        
        Args:
            path (str): Asset path
            
        Returns:
            bool: True if asset was removed
        """
        if path in self.assets:
            del self.assets[path]
            return True
        return False
    
    def get_assets_by_type(self, asset_type: AssetType) -> List[AssetMetadata]:
        """Get all assets of a specific type.
        
        Args:
            asset_type (AssetType): Asset type to filter by
            
        Returns:
            List[AssetMetadata]: List of matching assets
        """
        return [metadata for metadata in self.assets.values() 
                if metadata.asset_type == asset_type]
    
    def get_assets_by_tag(self, tag: str) -> List[AssetMetadata]:
        """Get all assets with a specific tag.
        
        Args:
            tag (str): Tag to filter by
            
        Returns:
            List[AssetMetadata]: List of matching assets
        """
        return [metadata for metadata in self.assets.values() 
                if tag in metadata.tags]
    
    def search_assets(self, query: str) -> List[AssetMetadata]:
        """Search assets by name or path.
        
        Args:
            query (str): Search query
            
        Returns:
            List[AssetMetadata]: List of matching assets
        """
        query_lower = query.lower()
        results = []
        
        for path, metadata in self.assets.items():
            if (query_lower in path.lower() or 
                query_lower in Path(path).name.lower()):
                results.append(metadata)
        
        return results
    
    def get_total_size(self) -> int:
        """Get total size of all assets in bytes.
        
        Returns:
            int: Total size in bytes
        """
        return sum(metadata.size for metadata in self.assets.values())
    
    def get_asset_count(self) -> int:
        """Get total number of assets.
        
        Returns:
            int: Number of assets
        """
        return len(self.assets)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert catalog to dictionary for serialization.
        
        Returns:
            Dict[str, Any]: Catalog as dictionary
        """
        return {
            'version': self.version,
            'last_scan': self.last_scan,
            'scan_paths': self.scan_paths,
            'assets': {
                path: {
                    'path': metadata.path,
                    'asset_type': metadata.asset_type.name,
                    'size': metadata.size,
                    'modified_time': metadata.modified_time,
                    'checksum': metadata.checksum,
                    'dependencies': metadata.dependencies,
                    'tags': metadata.tags,
                    'properties': metadata.properties
                }
                for path, metadata in self.assets.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AssetCatalog':
        """Create catalog from dictionary.
        
        Args:
            data (Dict[str, Any]): Catalog data
            
        Returns:
            AssetCatalog: Reconstructed catalog
        """
        catalog = cls()
        catalog.version = data.get('version', '1.0')
        catalog.last_scan = data.get('last_scan', 0.0)
        catalog.scan_paths = data.get('scan_paths', [])
        
        assets_data = data.get('assets', {})
        for path, asset_data in assets_data.items():
            try:
                asset_type = AssetType[asset_data['asset_type']]
                metadata = AssetMetadata(
                    path=asset_data['path'],
                    asset_type=asset_type,
                    size=asset_data.get('size', 0),
                    modified_time=asset_data.get('modified_time', 0.0),
                    checksum=asset_data.get('checksum', ''),
                    dependencies=asset_data.get('dependencies', []),
                    tags=asset_data.get('tags', []),
                    properties=asset_data.get('properties', {})
                )
                catalog.add_asset(path, metadata)
            except (KeyError, ValueError) as e:
                # Skip invalid asset entries
                continue
        
        return catalog


class ResourceDiscovery:
    """Resource discovery system for scanning and cataloging assets.
    
    This class provides functionality for discovering assets in the file
    system, extracting metadata, and maintaining an asset catalog.
    """
    
    def __init__(self, 
                 scan_paths: Optional[List[str]] = None,
                 ignore_patterns: Optional[List[str]] = None,
                 follow_symlinks: bool = False):
        """Initialize the resource discovery system.
        
        Args:
            scan_paths (List[str], optional): Paths to scan for assets
            ignore_patterns (List[str], optional): Patterns to ignore during scanning
            follow_symlinks (bool): Whether to follow symbolic links
        """
        self.scan_paths = scan_paths or []
        self.ignore_patterns = ignore_patterns or [
            '.*',           # Hidden files
            '__pycache__',  # Python cache
            '*.pyc',        # Python bytecode
            '*.tmp',        # Temporary files
            '*.bak',        # Backup files
            'node_modules', # Node.js modules
            '.git',         # Git repository
            '.svn',         # SVN repository
        ]
        self.follow_symlinks = follow_symlinks
        
        # Discovery state
        self.catalog = AssetCatalog()
        self.loader_registry = get_loader_registry()
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Progress callbacks
        self._progress_callbacks: List[Callable[[str, int, int], None]] = []
    
    def add_scan_path(self, path: str) -> None:
        """Add a path to scan for assets.
        
        Args:
            path (str): Path to add
        """
        with self._lock:
            if path not in self.scan_paths:
                self.scan_paths.append(path)
                self.catalog.scan_paths = self.scan_paths.copy()
    
    def remove_scan_path(self, path: str) -> None:
        """Remove a path from scanning.
        
        Args:
            path (str): Path to remove
        """
        with self._lock:
            if path in self.scan_paths:
                self.scan_paths.remove(path)
                self.catalog.scan_paths = self.scan_paths.copy()
    
    def add_ignore_pattern(self, pattern: str) -> None:
        """Add a pattern to ignore during scanning.
        
        Args:
            pattern (str): Pattern to ignore (supports wildcards)
        """
        if pattern not in self.ignore_patterns:
            self.ignore_patterns.append(pattern)
    
    def remove_ignore_pattern(self, pattern: str) -> None:
        """Remove an ignore pattern.
        
        Args:
            pattern (str): Pattern to remove
        """
        if pattern in self.ignore_patterns:
            self.ignore_patterns.remove(pattern)
    
    def scan(self, force_rescan: bool = False) -> ScanResult:
        """Scan for assets in all configured paths.
        
        Args:
            force_rescan (bool): Force rescan even if files haven't changed
            
        Returns:
            ScanResult: Results of the scan operation
        """
        with self._lock:
            start_time = time.time()
            result = ScanResult()
            
            try:
                for scan_path in self.scan_paths:
                    self._scan_path(scan_path, result, force_rescan)
                
                # Update catalog timestamp
                self.catalog.last_scan = time.time()
                result.scan_time = time.time() - start_time
                
            except Exception as e:
                result.add_error(f"Scan failed: {e}")
            
            return result
    
    def scan_path(self, path: str, force_rescan: bool = False) -> ScanResult:
        """Scan a specific path for assets.
        
        Args:
            path (str): Path to scan
            force_rescan (bool): Force rescan even if files haven't changed
            
        Returns:
            ScanResult: Results of the scan operation
        """
        start_time = time.time()
        result = ScanResult()
        
        try:
            self._scan_path(path, result, force_rescan)
            result.scan_time = time.time() - start_time
        except Exception as e:
            result.add_error(f"Scan failed for {path}: {e}")
        
        return result
    
    def _scan_path(self, path: str, result: ScanResult, force_rescan: bool) -> None:
        """Internal method to scan a path.
        
        Args:
            path (str): Path to scan
            result (ScanResult): Scan result to update
            force_rescan (bool): Force rescan flag
        """
        path_obj = Path(path)
        
        if not path_obj.exists():
            result.add_error(f"Path does not exist: {path}")
            return
        
        if path_obj.is_file():
            # Single file
            self._process_file(path_obj, result, force_rescan)
        else:
            # Directory
            for file_path in self._walk_directory(path_obj):
                self._process_file(file_path, result, force_rescan)
                
                # Update progress
                for callback in self._progress_callbacks:
                    try:
                        callback(str(file_path), result.total_files, result.assets_found)
                    except Exception:
                        pass  # Don't let callback errors break scanning
    
    def _walk_directory(self, directory: Path) -> Iterator[Path]:
        """Walk directory and yield file paths.
        
        Args:
            directory (Path): Directory to walk
            
        Yields:
            Path: File paths
        """
        try:
            for root, dirs, files in os.walk(directory, followlinks=self.follow_symlinks):
                root_path = Path(root)
                
                # Filter directories based on ignore patterns
                dirs[:] = [d for d in dirs if not self._should_ignore(d)]
                
                for file_name in files:
                    if not self._should_ignore(file_name):
                        yield root_path / file_name
        except (OSError, PermissionError) as e:
            # Skip directories we can't access
            pass
    
    def _process_file(self, file_path: Path, result: ScanResult, force_rescan: bool) -> None:
        """Process a single file.
        
        Args:
            file_path (Path): File to process
            result (ScanResult): Scan result to update
            force_rescan (bool): Force rescan flag
        """
        result.total_files += 1
        
        try:
            # Check if we should skip this file
            if not force_rescan and self._is_file_unchanged(file_path):
                return
            
            # Try to detect asset type
            asset_type = self.loader_registry.detect_asset_type(str(file_path))
            if not asset_type:
                return  # Not a recognized asset type
            
            # Create metadata
            metadata = self._create_metadata(file_path, asset_type)
            
            # Add to catalog
            self.catalog.add_asset(str(file_path), metadata)
            result.add_asset(asset_type)
            
        except Exception as e:
            result.add_error(f"Error processing {file_path}: {e}")
    
    def _create_metadata(self, file_path: Path, asset_type: AssetType) -> AssetMetadata:
        """Create metadata for an asset.
        
        Args:
            file_path (Path): Asset file path
            asset_type (AssetType): Asset type
            
        Returns:
            AssetMetadata: Created metadata
        """
        stat = file_path.stat()
        
        # Calculate checksum
        checksum = self._calculate_checksum(file_path)
        
        # Extract tags from path
        tags = self._extract_tags(file_path)
        
        # Create metadata
        metadata = AssetMetadata(
            path=str(file_path),
            asset_type=asset_type,
            size=stat.st_size,
            modified_time=stat.st_mtime,
            checksum=checksum,
            tags=tags
        )
        
        return metadata
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of a file.
        
        Args:
            file_path (Path): File to checksum
            
        Returns:
            str: MD5 checksum
        """
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def _extract_tags(self, file_path: Path) -> List[str]:
        """Extract tags from file path.
        
        Args:
            file_path (Path): File path
            
        Returns:
            List[str]: Extracted tags
        """
        tags = []
        
        # Add directory names as tags
        for part in file_path.parts[:-1]:  # Exclude filename
            if part and not part.startswith('.'):
                tags.append(part.lower())
        
        # Add file extension as tag
        if file_path.suffix:
            tags.append(file_path.suffix[1:].lower())  # Remove dot
        
        return tags
    
    def _should_ignore(self, name: str) -> bool:
        """Check if a file/directory should be ignored.
        
        Args:
            name (str): File or directory name
            
        Returns:
            bool: True if should be ignored
        """
        import fnmatch
        
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(name, pattern):
                return True
        
        return False
    
    def _is_file_unchanged(self, file_path: Path) -> bool:
        """Check if a file is unchanged since last scan.
        
        Args:
            file_path (Path): File to check
            
        Returns:
            bool: True if file is unchanged
        """
        path_str = str(file_path)
        if path_str not in self.catalog.assets:
            return False
        
        metadata = self.catalog.assets[path_str]
        try:
            stat = file_path.stat()
            return stat.st_mtime <= metadata.modified_time
        except OSError:
            return False
    
    def get_catalog(self) -> AssetCatalog:
        """Get the current asset catalog.
        
        Returns:
            AssetCatalog: Current catalog
        """
        with self._lock:
            return self.catalog
    
    def save_catalog(self, path: str) -> None:
        """Save the asset catalog to a file.
        
        Args:
            path (str): Path to save catalog to
        """
        with self._lock:
            catalog_data = self.catalog.to_dict()
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(catalog_data, f, indent=2)
    
    def load_catalog(self, path: str) -> None:
        """Load an asset catalog from a file.
        
        Args:
            path (str): Path to load catalog from
        """
        with self._lock:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    catalog_data = json.load(f)
                
                self.catalog = AssetCatalog.from_dict(catalog_data)
                self.scan_paths = self.catalog.scan_paths.copy()
                
            except Exception as e:
                raise AssetError(f"Failed to load catalog: {e}")
    
    def add_progress_callback(self, callback: Callable[[str, int, int], None]) -> None:
        """Add a progress callback for scanning operations.
        
        Args:
            callback (Callable): Callback function (file_path, total_files, assets_found)
        """
        self._progress_callbacks.append(callback)
    
    def remove_progress_callback(self, callback: Callable[[str, int, int], None]) -> None:
        """Remove a progress callback.
        
        Args:
            callback (Callable): Callback to remove
        """
        if callback in self._progress_callbacks:
            self._progress_callbacks.remove(callback)
