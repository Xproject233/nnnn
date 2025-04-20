"""
Configuration Manager for Security Leads Automation

This module handles all configuration settings for the scraper system,
including source URLs, credentials, and operational parameters.
"""

import os
import json
from pathlib import Path

class ConfigManager:
    """Manages configuration settings for the scraper system."""
    
    def __init__(self, config_path=None):
        """Initialize the configuration manager.
        
        Args:
            config_path (str, optional): Path to configuration file. Defaults to None.
        """
        self.base_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.config_path = config_path or self.base_dir / 'config' / 'config.json'
        self.config = self._load_config()
        
    def _load_config(self):
        """Load configuration from file.
        
        Returns:
            dict: Configuration settings
        """
        if not os.path.exists(self.config_path):
            # Create default configuration if it doesn't exist
            default_config = self._create_default_config()
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
            return default_config
        
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def _create_default_config(self):
        """Create default configuration.
        
        Returns:
            dict: Default configuration settings
        """
        return {
            "sources": {
                "instantmarkets": {
                    "enabled": True,
                    "url": "https://www.instantmarkets.com/q/event_security_guard",
                    "scrape_frequency_hours": 24
                },
                "bidnetdirect": {
                    "enabled": True,
                    "url": "https://www.bidnetdirect.com/public/solicitations/open?keywords=Security+Services",
                    "scrape_frequency_hours": 24
                },
                "usajobs": {
                    "enabled": True,
                    "url": "https://www.usajobs.gov/Search/?soc=Security%20Guards",
                    "scrape_frequency_hours": 24
                },
                "securityjobsnet": {
                    "enabled": True,
                    "url": "https://securityjobs.net/",
                    "scrape_frequency_hours": 24
                },
                "securityguardsonly": {
                    "enabled": True,
                    "url": "https://www.securityguardsonly.com/",
                    "scrape_frequency_hours": 24
                }
            },
            "database": {
                "type": "sqlite",
                "path": str(self.base_dir / "data" / "leads.db")
            },
            "scraping": {
                "user_agents": [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
                ],
                "request_delay": {
                    "min_seconds": 2,
                    "max_seconds": 5
                },
                "max_retries": 3,
                "timeout_seconds": 30
            },
            "export": {
                "formats": ["csv", "excel", "json"],
                "default_path": str(self.base_dir / "data" / "exports")
            },
            "logging": {
                "level": "INFO",
                "file": str(self.base_dir / "logs" / "scraper.log")
            }
        }
    
    def get_source_config(self, source_name):
        """Get configuration for a specific source.
        
        Args:
            source_name (str): Name of the source
            
        Returns:
            dict: Source configuration
        """
        return self.config["sources"].get(source_name, {})
    
    def get_enabled_sources(self):
        """Get list of enabled sources.
        
        Returns:
            list: Names of enabled sources
        """
        return [name for name, config in self.config["sources"].items() 
                if config.get("enabled", False)]
    
    def get_database_config(self):
        """Get database configuration.
        
        Returns:
            dict: Database configuration
        """
        return self.config["database"]
    
    def get_scraping_config(self):
        """Get scraping configuration.
        
        Returns:
            dict: Scraping configuration
        """
        return self.config["scraping"]
    
    def get_export_config(self):
        """Get export configuration.
        
        Returns:
            dict: Export configuration
        """
        return self.config["export"]
    
    def get_logging_config(self):
        """Get logging configuration.
        
        Returns:
            dict: Logging configuration
        """
        return self.config["logging"]
    
    def update_config(self, new_config):
        """Update configuration.
        
        Args:
            new_config (dict): New configuration settings
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.config.update(new_config)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception:
            return False
