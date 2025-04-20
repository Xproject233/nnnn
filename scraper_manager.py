"""
Update the scraper manager to include state extraction for all scraped leads
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import state extraction utilities
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.utils.state_extraction import enhance_lead_with_state_info

class ScraperManager:
    """Manages the execution of multiple scrapers with state extraction."""
    
    def __init__(self, config_path=None, logger=None):
        """Initialize the scraper manager.
        
        Args:
            config_path: Path to configuration file
            logger: Optional logger instance
        """
        # Set up base paths
        self.base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.data_dir = self.base_dir / "data"
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Set up logger
        self.logger = logger or logging.getLogger(__name__)
        
        # Load configuration
        if not config_path:
            config_path = str(self.base_dir / "config.json")
        
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading configuration: {str(e)}")
            self.config = {}
        
        # Get scraper configuration
        self.scraper_config = self.config.get("scrapers", {})
        
        # Initialize scrapers
        self.scrapers = self._init_scrapers()
    
    def _init_scrapers(self) -> Dict[str, Any]:
        """Initialize scrapers based on configuration.
        
        Returns:
            Dictionary of scraper instances
        """
        scrapers = {}
        
        # Get enabled scrapers from config
        enabled_scrapers = self.scraper_config.get("enabled", [])
        
        # Import and initialize each scraper
        for scraper_name in enabled_scrapers:
            try:
                # Import scraper module
                module_name = f"scripts.scrapers.{scraper_name}_scraper"
                module = __import__(module_name, fromlist=["Scraper"])
                
                # Initialize scraper
                scraper_class = getattr(module, "Scraper")
                scraper = scraper_class(self.config, self.logger)
                
                # Add to scrapers dictionary
                scrapers[scraper_name] = scraper
                
                self.logger.info(f"Initialized scraper: {scraper_name}")
            
            except Exception as e:
                self.logger.error(f"Error initializing scraper {scraper_name}: {str(e)}")
        
        return scrapers
    
    def run_scrapers(self, sources=None) -> List[Dict[str, Any]]:
        """Run scrapers to collect leads with state information.
        
        Args:
            sources: Optional list of source names to run
            
        Returns:
            List of lead data dictionaries
        """
        all_leads = []
        
        # Determine which scrapers to run
        scrapers_to_run = {}
        if sources:
            # Run only specified sources
            for source in sources:
                if source in self.scrapers:
                    scrapers_to_run[source] = self.scrapers[source]
                else:
                    self.logger.warning(f"Scraper not found: {source}")
        else:
            # Run all scrapers
            scrapers_to_run = self.scrapers
        
        # Run each scraper
        for name, scraper in scrapers_to_run.items():
            try:
                self.logger.info(f"Running scraper: {name}")
                
                # Run scraper
                leads = scraper.scrape()
                
                # Enhance leads with state information
                enhanced_leads = []
                for lead in leads:
                    try:
                        # Add source information
                        lead['source'] = name
                        
                        # Enhance with state information
                        enhanced_lead = enhance_lead_with_state_info(lead)
                        
                        enhanced_leads.append(enhanced_lead)
                    
                    except Exception as e:
                        self.logger.error(f"Error enhancing lead with state information: {str(e)}")
                        # Still include the original lead
                        enhanced_leads.append(lead)
                
                self.logger.info(f"Collected {len(enhanced_leads)} leads from {name}")
                
                # Add to all leads
                all_leads.extend(enhanced_leads)
            
            except Exception as e:
                self.logger.error(f"Error running scraper {name}: {str(e)}")
        
        self.logger.info(f"Collected {len(all_leads)} leads from {len(scrapers_to_run)} scrapers")
        
        return all_leads
    
    def get_available_sources(self) -> List[str]:
        """Get list of available scraper sources.
        
        Returns:
            List of source names
        """
        return list(self.scrapers.keys())
    
    def get_source_info(self, source: str) -> Optional[Dict[str, Any]]:
        """Get information about a scraper source.
        
        Args:
            source: Source name
            
        Returns:
            Dictionary with source information or None if not found
        """
        if source not in self.scrapers:
            return None
        
        scraper = self.scrapers[source]
        
        # Get source information
        return {
            "name": source,
            "description": getattr(scraper, "description", f"{source} scraper"),
            "url": getattr(scraper, "base_url", ""),
            "enabled": True
        }
    
    def get_all_source_info(self) -> List[Dict[str, Any]]:
        """Get information about all scraper sources.
        
        Returns:
            List of dictionaries with source information
        """
        return [self.get_source_info(source) for source in self.scrapers.keys()]
