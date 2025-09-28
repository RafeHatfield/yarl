"""Asset management exceptions.

This module defines all exceptions used by the asset management system,
providing clear error handling and debugging information for asset-related
operations.
"""


class AssetError(Exception):
    """Base exception for all asset-related errors."""
    
    def __init__(self, message: str, asset_path: str = None, asset_type: str = None):
        """Initialize asset error.
        
        Args:
            message (str): Error message
            asset_path (str, optional): Path to the asset that caused the error
            asset_type (str, optional): Type of asset that caused the error
        """
        super().__init__(message)
        self.asset_path = asset_path
        self.asset_type = asset_type
        self.message = message
    
    def __str__(self) -> str:
        """String representation of the error."""
        parts = [self.message]
        if self.asset_path:
            parts.append(f"Asset: {self.asset_path}")
        if self.asset_type:
            parts.append(f"Type: {self.asset_type}")
        return " | ".join(parts)


class AssetNotFoundError(AssetError):
    """Exception raised when an asset cannot be found."""
    
    def __init__(self, asset_path: str, asset_type: str = None, search_paths: list = None):
        """Initialize asset not found error.
        
        Args:
            asset_path (str): Path to the missing asset
            asset_type (str, optional): Type of asset
            search_paths (list, optional): Paths that were searched
        """
        message = f"Asset not found: {asset_path}"
        if search_paths:
            message += f" (searched in: {', '.join(search_paths)})"
        
        super().__init__(message, asset_path, asset_type)
        self.search_paths = search_paths or []


class AssetLoadError(AssetError):
    """Exception raised when an asset fails to load."""
    
    def __init__(self, asset_path: str, asset_type: str = None, cause: Exception = None):
        """Initialize asset load error.
        
        Args:
            asset_path (str): Path to the asset that failed to load
            asset_type (str, optional): Type of asset
            cause (Exception, optional): Underlying exception that caused the failure
        """
        message = f"Failed to load asset: {asset_path}"
        if cause:
            message += f" ({type(cause).__name__}: {cause})"
        
        super().__init__(message, asset_path, asset_type)
        self.cause = cause


class AssetValidationError(AssetError):
    """Exception raised when an asset fails validation."""
    
    def __init__(self, asset_path: str, asset_type: str = None, validation_errors: list = None):
        """Initialize asset validation error.
        
        Args:
            asset_path (str): Path to the invalid asset
            asset_type (str, optional): Type of asset
            validation_errors (list, optional): List of validation error messages
        """
        message = f"Asset validation failed: {asset_path}"
        if validation_errors:
            message += f" (errors: {', '.join(validation_errors)})"
        
        super().__init__(message, asset_path, asset_type)
        self.validation_errors = validation_errors or []


class AssetCacheError(AssetError):
    """Exception raised when asset cache operations fail."""
    
    def __init__(self, message: str, asset_path: str = None, cache_operation: str = None):
        """Initialize asset cache error.
        
        Args:
            message (str): Error message
            asset_path (str, optional): Path to the asset
            cache_operation (str, optional): Cache operation that failed
        """
        super().__init__(message, asset_path)
        self.cache_operation = cache_operation


class AssetDependencyError(AssetError):
    """Exception raised when asset dependency resolution fails."""
    
    def __init__(self, asset_path: str, dependency_path: str, asset_type: str = None):
        """Initialize asset dependency error.
        
        Args:
            asset_path (str): Path to the asset with dependency issues
            dependency_path (str): Path to the missing dependency
            asset_type (str, optional): Type of asset
        """
        message = f"Asset dependency not found: {asset_path} requires {dependency_path}"
        super().__init__(message, asset_path, asset_type)
        self.dependency_path = dependency_path


class AssetFormatError(AssetError):
    """Exception raised when an asset has an unsupported or invalid format."""
    
    def __init__(self, asset_path: str, expected_format: str = None, actual_format: str = None):
        """Initialize asset format error.
        
        Args:
            asset_path (str): Path to the asset with format issues
            expected_format (str, optional): Expected asset format
            actual_format (str, optional): Actual detected format
        """
        message = f"Invalid asset format: {asset_path}"
        if expected_format:
            message += f" (expected: {expected_format}"
            if actual_format:
                message += f", got: {actual_format}"
            message += ")"
        
        super().__init__(message, asset_path)
        self.expected_format = expected_format
        self.actual_format = actual_format
