"""
Base Scraper for Security Leads Automation

This module provides a base class for all source-specific scrapers.
"""

import requests
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
import time
import random

class BaseScraper(ABC):
    """Base class for all scrapers."""
    
    def __init__(self, config, logger):
        """Initialize the base scraper.
        
        Args:
            config (dict): Source configuration
            logger (logging.Logger): Logger instance
        """
        self.config = config
        self.logger = logger
        self.session = requests.Session()
        self.max_retries = 3
        self.timeout = 30
    
    def _make_request(self, url, user_agent=None, headers=None, params=None):
        """Make an HTTP request with retry logic.
        
        Args:
            url (str): URL to request
            user_agent (str, optional): User agent string. Defaults to None.
            headers (dict, optional): Additional headers. Defaults to None.
            params (dict, optional): URL parameters. Defaults to None.
            
        Returns:
            requests.Response: Response object
        """
        if headers is None:
            headers = {}
        
        if user_agent:
            headers['User-Agent'] = user_agent
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(
                    url, 
                    headers=headers, 
                    params=params,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request failed (attempt {attempt+1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    # Wait before retrying with exponential backoff
                    wait_time = 2 ** attempt + random.uniform(0, 1)
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Request failed after {self.max_retries} attempts: {str(e)}")
                    raise
    
    def _parse_html(self, html_content):
        """Parse HTML content using BeautifulSoup.
        
        Args:
            html_content (str): HTML content
            
        Returns:
            BeautifulSoup: Parsed HTML
        """
        return BeautifulSoup(html_content, 'html.parser')
    
    @abstractmethod
    def scrape(self, user_agent=None):
        """Scrape the source for leads.
        
        Args:
            user_agent (str, optional): User agent string. Defaults to None.
            
        Returns:
            list: Extracted leads
        """
        pass
    
    @abstractmethod
    def extract_lead_data(self, item):
        """Extract lead data from a scraped item.
        
        Args:
            item: Scraped item
            
        Returns:
            dict: Lead data
        """
        pass
