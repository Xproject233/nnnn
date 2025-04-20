"""
Logger module for Security Leads Automation

This module provides logging functionality for the scraper system.
"""

import os
import logging
from pathlib import Path
from datetime import datetime

class Logger:
    """Provides logging functionality for the scraper system."""
    
    def __init__(self, config=None):
        """Initialize the logger.
        
        Args:
            config (dict, optional): Logging configuration. Defaults to None.
        """
        self.base_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.config = config or {
            "level": "INFO",
            "file": str(self.base_dir / "logs" / "scraper.log")
        }
        self._setup_logger()
        
    def _setup_logger(self):
        """Set up the logger."""
        log_dir = os.path.dirname(self.config["file"])
        os.makedirs(log_dir, exist_ok=True)
        
        # Set up logging level
        level = getattr(logging, self.config["level"], logging.INFO)
        
        # Configure logging
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config["file"]),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger("SecurityLeadsAutomation")
        self.logger.info(f"Logger initialized at {datetime.now()}")
    
    def get_logger(self):
        """Get the logger instance.
        
        Returns:
            logging.Logger: Logger instance
        """
        return self.logger
