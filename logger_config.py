"""Centralized logging configuration for Yarl roguelike.

This module provides a unified logging system with:
- Centralized configuration
- Log rotation (prevents disk bloat)
- Separate error tracking
- Module-based logger hierarchy
- Consistent message formatting
"""

import logging
import logging.handlers
import os


def setup_logging(log_level=logging.WARNING):
    """Configure centralized logging for entire application.
    
    Args:
        log_level: Root logging level (default: WARNING)
        
    Returns:
        logging.Logger: Configured root logger for 'rlike' namespace
    """
    
    # Create logs directory if needed
    os.makedirs('logs', exist_ok=True)
    
    # Main application logger
    app_logger = logging.getLogger('rlike')
    app_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    app_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    simple_formatter = logging.Formatter('[%(levelname)s] %(message)s')
    
    # Main file handler with rotation (10 MB max, keep 5 backups)
    file_handler = logging.handlers.RotatingFileHandler(
        'logs/rlike.log',
        maxBytes=10_000_000,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    app_logger.addHandler(file_handler)
    
    # Separate error log (5 MB max, keep 3 backups)
    error_handler = logging.handlers.RotatingFileHandler(
        'logs/rlike_errors.log',
        maxBytes=5_000_000,  # 5 MB
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    app_logger.addHandler(error_handler)
    
    # Console handler (development - WARNING and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(simple_formatter)
    app_logger.addHandler(console_handler)
    
    return app_logger


def get_logger(module_name):
    """Get a logger for a specific module.
    
    Args:
        module_name: Name of the module (__name__ or descriptive name)
        
    Returns:
        logging.Logger: Module-specific logger
        
    Example:
        from logger_config import get_logger
        logger = get_logger(__name__)
        logger.info("Game started")
    """
    return logging.getLogger(f'rlike.{module_name}')


# Initialize logging on module import
_root_logger = setup_logging()

