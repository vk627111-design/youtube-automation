"""Application logging configuration."""
import logging
import os
from datetime import datetime
from app.settings import settings


class LogManager:
    """Manages application logging."""

    def __init__(self):
        """Initialize log manager."""
        os.makedirs("data/logs", exist_ok=True)
        self.log_file = "data/logs/app.log"
        self._setup_logging()

    def _setup_logging(self):
        """Setup logging configuration."""
        log_level = settings.get('logging.log_level', 'INFO')
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(logging.Formatter(log_format))
        
        # Root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

    def get_logger(self, name: str) -> logging.Logger:
        """Get logger instance.
        
        Args:
            name: Logger name (typically __name__)
            
        Returns:
            Logger instance
        """
        return logging.getLogger(name)


# Global log manager instance
log_manager = LogManager()
