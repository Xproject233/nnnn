"""
USAJOBS Scraper for Security Leads Automation

This module implements a scraper for USAJOBS, extracting security guard job postings.
"""

import re
from ..core.base_scraper import BaseScraper
from ..utils.data_utils import extract_email, extract_phone, detect_security_keywords, calculate_confidence_score

class UsajobsScraper(BaseScraper):
    """Scraper for USAJOBS website."""
    
    def __init__(self, config, logger):
        """Initialize the USAJOBS scraper.
        
        Args:
            config (dict): Source configuration
            logger (logging.Logger): Logger instance
        """
        super().__init__(config, logger)
        self.base_url = config.get("url", "https://www.usajobs.gov/Search/?soc=Security%20Guards")
    
    def scrape(self, user_agent=None):
        """Scrape USAJOBS for security guard job postings.
        
        Args:
            user_agent (str, optional): User agent string. Defaults to None.
            
        Returns:
            list: Extracted leads
        """
        self.logger.info(f"Scraping USAJOBS: {self.base_url}")
        
        leads = []
        
        try:
            # Make request to the main page
            response = self._make_request(self.base_url, user_agent=user_agent)
            soup = self._parse_html(response.text)
            
            # Find all job listings
            listings = soup.find_all("div", class_=lambda c: c and "usajobs-search-result--core" in c)
            
            if not listings:
                # Try alternative selectors if the above doesn't work
                listings = soup.find_all("li", class_=lambda c: c and "usajobs-search-result" in c)
            
            self.logger.info(f"Found {len(listings)} listings on USAJOBS")
            
            # Process each listing
            for listing in listings[:10]:  # Limit to first 10 for testing
                try:
                    # Extract basic information from listing
                    title_elem = listing.find("h3", class_=lambda c: c and "title" in c) or listing.find("h3")
                    title = title_elem.text.strip() if title_elem else ""
                    
                    # Extract URL for detailed page
                    detail_url = None
                    if title_elem:
                        link_elem = title_elem.find("a")
                        if link_elem and link_elem.get("href"):
                            detail_url = link_elem["href"]
                            if not detail_url.startswith("http"):
                                detail_url = "https://www.usajobs.gov" + detail_url
                    
                    # Extract agency/department
                    agency_elem = listing.find("div", class_=lambda c: c and "agency" in c) or listing.find("h4", class_=lambda c: c and "agency" in c)
                    agency = agency_elem.text.strip() if agency_elem else ""
                    
                    # Extract department
                    dept_elem = listing.find("div", class_=lambda c: c and "department" in c)
                    department = dept_elem.text.strip() if dept_elem else ""
                    
                    # Extract location
                    location_elem = listing.find("div", class_=lambda c: c and "location" in c) or listing.find("h5", class_=lambda c: c and "location" in c)
                    location = location_elem.text.strip() if location_elem else ""
                    
                    # Extract salary
                    salary_elem = listing.find("div", class_=lambda c: c and "salary" in c) or listing.find("h5", class_=lambda c: c and "salary" in c)
                    salary = salary_elem.text.strip() if salary_elem else ""
                    
                    # If we have a detail URL, scrape the detailed page
                    description = ""
                    requirements = ""
                    contact_info = ""
                    if detail_url:
                        try:
                            detail_response = self._make_request(detail_url, user_agent=user_agent)
                            detail_soup = self._parse_html(detail_response.text)
                            
                            # Extract description
                            desc_elem = detail_soup.find("div", id=lambda i: i and "duties" in i.lower()) or detail_soup.find("div", class_=lambda c: c and "duties" in c.lower())
                            description = desc_elem.text.strip() if desc_elem else ""
                            
                            # Extract requirements
                            req_elem = detail_soup.find("div", id=lambda i: i and "requirements" in i.lower()) or detail_soup.find("div", class_=lambda c: c and "requirements" in c.lower())
                            requirements = req_elem.text.strip() if req_elem else ""
                            
                            # Extract contact information
                            contact_elem = detail_soup.find("div", id=lambda i: i and "contact" in i.lower()) or detail_soup.find("div", class_=lambda c: c and "contact" in c.lower())
                            contact_info = contact_elem.text.strip() if contact_elem else ""
                        except Exception as e:
                            self.logger.warning(f"Error scraping detail page {detail_url}: {str(e)}")
                    
                    # Create lead data
                    lead_data = self.extract_lead_data({
                        "title": title,
                        "agency": agency,
                        "department": department,
                        "location": location,
                        "salary": salary,
                        "description": description,
                        "requirements": requirements,
                        "contact_info": contact_info,
                        "source_url": detail_url or self.base_url
                    })
                    
                    leads.append(lead_data)
                except Exception as e:
                    self.logger.warning(f"Error processing listing: {str(e)}")
            
            return leads
        except Exception as e:
            self.logger.error(f"Error scraping USAJOBS: {str(e)}")
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
        requirements = item.get("requirements", "")
        contact_info = item.get("contact_info", "")
        
        all_text = f"{item.get('title', '')} {item.get('agency', '')} {description} {requirements} {contact_info}"
        
        emails = extract_email(all_text)
        phones = extract_phone(all_text)
        
        # Extract security keywords
        keywords = detect_security_keywords(all_text)
        
        # Determine if it's for armed or unarmed security
        is_armed = False
        if keywords.get('security_type'):
            is_armed = any('armed' in keyword for keyword in keywords.get('security_type', []))
        
        # Create organization data
        organization = {
            "name": f"{item.get('agency', '')} - {item.get('department', '')}".strip(' -'),
            "is_government": True  # USAJOBS is for government positions
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
            "requirements": requirements or ", ".join(keywords.get('requirements', [])),
            "location": item.get("location", ""),
            "opportunity_type": "general",
            "is_armed": is_armed,
            "estimated_value": item.get("salary", "")
        }
        
        # Create lead data
        lead_data = {
            "source": "usajobs",
            "source_url": item.get("source_url", ""),
            "lead_type": "job_posting",
            "organization": organization,
            "contacts": contacts,
            "opportunity": opportunity
        }
        
        # Calculate confidence score
        lead_data["confidence_score"] = calculate_confidence_score(lead_data)
        
        return lead_data
