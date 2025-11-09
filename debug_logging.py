"""
Configure debug logging to file for diagnostics.

NOTE: This module is DEPRECATED. Use logger_config.py instead.
logger_config.py provides centralized logging with rotation and better organization.

This module is kept for backward compatibility but should not be used for new code.

Historical behavior:
- Movement and turn economy logging
- State transitions
- AI system processing
- Turn controller operations
"""

import logging
import sys
from pathlib import Path
from logger_config import get_logger

_deprecation_logger = get_logger(__name__)


def setup_debug_logging(log_file: str = "debug.log", console_level: str = "WARNING"):
    """Set up debug logging to both file and console.
    
    Args:
        log_file: Path to debug log file (default: debug.log)
        console_level: Log level for console output (default: WARNING)
                      Set to DEBUG to see everything on console too
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(exist_ok=True)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture everything
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # File handler - captures EVERYTHING at DEBUG level
    file_handler = logging.FileHandler(log_file, mode='w')  # 'w' = overwrite each run
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler - only shows WARNING and above (or DEBUG if specified)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, console_level.upper()))
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    logging.info("="*80)
    logging.info("DEBUG LOGGING INITIALIZED")
    logging.info(f"Log file: {log_file}")
    logging.info(f"Console level: {console_level}")
    logging.info("="*80)
    
    return log_file


if __name__ == "__main__":
    # Test the logging setup
    setup_debug_logging()
    
    logger = logging.getLogger("test")
    logger.debug("This is a DEBUG message (file only)")
    logger.info("This is an INFO message (file only)")
    logger.warning("This is a WARNING message (file + console)")
    logger.error("This is an ERROR message (file + console)")
    
    print("Check debug.log to see all messages!")

