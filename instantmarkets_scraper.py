"""
InstantMarkets Scraper for Security Leads Automation

This module implements a scraper for InstantMarkets, extracting security service RFPs and contracts.
"""

import re
from ..core.base_scraper import BaseScraper
from ..utils.data_utils import extract_email, extract_phone, extract_date, detect_security_keywords, calculate_confidence_score

class InstantmarketsScraper(BaseScraper):
    """Scraper for InstantMarkets website."""
    
    def __init__(self, config, logger):
        """Initialize the InstantMarkets scraper.
        
        Args:
            config (dict): Source configuration
            logger (logging.Logger): Logger instance
        """
        super().__init__(config, logger)
        self.base_url = config.get("url", "https://www.instantmarkets.com/q/event_security_guard")
    
    def scrape(self, user_agent=None):
        """Scrape InstantMarkets for security service leads.
        
        Args:
            user_agent (str, optional): User agent string. Defaults to None.
            
        Returns:
            list: Extracted leads
        """
        self.logger.info(f"Scraping InstantMarkets: {self.base_url}")
        
        leads = []
        
        try:
            # Make request to the main page
            response = self._make_request(self.base_url, user_agent=user_agent)
            soup = self._parse_html(response.text)
            
            # Find all RFP/contract listings
            listings = soup.find_all("div", class_=lambda c: c and "opportunity" in c.lower())
            
            if not listings:
                # Try alternative selectors if the above doesn't work
                listings = soup.find_all("div", class_=lambda c: c and ("rfp" in c.lower() or "bid" in c.lower()))
            
            self.logger.info(f"Found {len(listings)} listings on InstantMarkets")
            
            # Process each listing
            for listing in listings[:10]:  # Limit to first 10 for testing
                try:
                    # Extract basic information from listing
                    title_elem = listing.find("a", class_=lambda c: c and "title" in c.lower()) or listing.find("h3") or listing.find("a")
                    title = title_elem.text.strip() if title_elem else ""
                    
                    # Extract URL for detailed page
                    detail_url = None
                    if title_elem and title_elem.name == "a" and title_elem.get("href"):
                        detail_url = title_elem["href"]
                        if not detail_url.startswith("http"):
                            detail_url = "https://www.instantmarkets.com" + detail_url
                    
                    # Extract agency/organization
                    agency_elem = listing.find("div", class_=lambda c: c and "agency" in c.lower()) or listing.find("span", class_=lambda c: c and "agency" in c.lower())
                    agency = agency_elem.text.strip() if agency_elem else ""
                    
                    # Extract due date
                    due_date_elem = listing.find("div", class_=lambda c: c and "due" in c.lower()) or listing.find("span", class_=lambda c: c and "due" in c.lower())
                    due_date = due_date_elem.text.strip() if due_date_elem else ""
                    
                    # If we have a detail URL, scrape the detailed page
                    description = ""
                    contact_info = ""
                    if detail_url:
                        try:
                            detail_response = self._make_request(detail_url, user_agent=user_agent)
                            detail_soup = self._parse_html(detail_response.text)
                            
                            # Extract description
                            desc_elem = detail_soup.find("div", class_=lambda c: c and "description" in c.lower()) or detail_soup.find("div", class_=lambda c: c and "details" in c.lower())
                            description = desc_elem.text.strip() if desc_elem else ""
                            
                            # Extract contact information
                            contact_elem = detail_soup.find("div", class_=lambda c: c and "contact" in c.lower())
                            contact_info = contact_elem.text.strip() if contact_elem else ""
                        except Exception as e:
                            self.logger.warning(f"Error scraping detail page {detail_url}: {str(e)}")
                    
                    # Create lead data
                    lead_data = self.extract_lead_data({
                        "title": title,
                        "agency": agency,
                        "due_date": due_date,
                        "description": description,
                        "contact_info": contact_info,
                        "source_url": detail_url or self.base_url
                    })
                    
                    leads.append(lead_data)
                except Exception as e:
                    self.logger.warning(f"Error processing listing: {str(e)}")
            
            return leads
        except Exception as e:
            self.logger.error(f"Error scraping InstantMarkets: {str(e)}")
            return []
    
    def extract_lead_data(self, item):
        """Extract lead data from a scraped item.
        
        Args:
            item (dict): Scraped item
            
        Returns:
            dict: Lead data
        """
        # Extract emails and phones from description and contact info
        description = item.get("description", "")
        contact_info = item.get("contact_info", "")
        
        all_text = f"{item.get('title', '')} {item.get('agency', '')} {description} {contact_info}"
        
        emails = extract_email(all_text)
        phones = extract_phone(all_text)
        
        # Extract security keywords
        keywords = detect_security_keywords(all_text)
        
        # Determine if it's for armed or unarmed security
        is_armed = False
        if keywords.get('security_type'):
            is_armed = any('armed' in keyword for keyword in keywords.get('security_type', []))
        
        # Determine opportunity type
        opportunity_type = "general"
        if keywords.get('event_type'):
            opportunity_type = "event"
        elif keywords.get('construction'):
            opportunity_type = "construction"
        
        # Create organization data
        organization = {
            "name": item.get("agency", ""),
            "is_government": "county" in item.get("agency", "").lower() or 
                            "city" in item.get("agency", "").lower() or 
                            "department" in item.get("agency", "").lower() or
                            "government" in item.get("agency", "").lower()
        }
        
        # Create contacts
        contacts = []
        if emails or phones:
            contact = {
                "email": emails[0] if emails else "",
                "phone": phones[0] if phones else ""
            }
            contacts.append(contact)
        
        # Create opportunity
        opportunity = {
            "title": item.get("title", ""),
            "description": description,
            "requirements": ", ".join(keywords.get('requirements', [])),
            "opportunity_type": opportunity_type,
            "is_armed": is_armed,
            "end_date": item.get("due_date", "")
        }
        
        # Create lead data
        lead_data = {
            "source": "instantmarkets",
            "source_url": item.get("source_url", ""),
            "lead_type": "rfp",
            "organization": organization,
            "contacts": contacts,
            "opportunity": opportunity
        }
        
        # Calculate confidence score
        lead_data["confidence_score"] = calculate_confidence_score(lead_data)
        
        return lead_data
