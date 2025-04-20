"""
Security Jobs Network Scraper for Security Leads Automation

This module implements a scraper for Security Jobs Network, extracting security job postings.
"""

import re
from ..core.base_scraper import BaseScraper
from ..utils.data_utils import extract_email, extract_phone, detect_security_keywords, calculate_confidence_score

class SecurityjobsnetScraper(BaseScraper):
    """Scraper for Security Jobs Network website."""
    
    def __init__(self, config, logger):
        """Initialize the Security Jobs Network scraper.
        
        Args:
            config (dict): Source configuration
            logger (logging.Logger): Logger instance
        """
        super().__init__(config, logger)
        self.base_url = config.get("url", "https://securityjobs.net/")
        self.jobs_url = "https://securityjobs.net/jobs/"
    
    def scrape(self, user_agent=None):
        """Scrape Security Jobs Network for security job postings.
        
        Args:
            user_agent (str, optional): User agent string. Defaults to None.
            
        Returns:
            list: Extracted leads
        """
        self.logger.info(f"Scraping Security Jobs Network: {self.jobs_url}")
        
        leads = []
        
        try:
            # Make request to the jobs page
            response = self._make_request(self.jobs_url, user_agent=user_agent)
            soup = self._parse_html(response.text)
            
            # Find all job listings
            listings = soup.find_all("div", class_=lambda c: c and "job-listing" in c.lower())
            
            if not listings:
                # Try alternative selectors if the above doesn't work
                listings = soup.find_all("article", class_=lambda c: c and "job" in c.lower())
            
            if not listings:
                # Try more generic approach
                listings = soup.select("div.job, article.job, li.job-listing")
            
            self.logger.info(f"Found {len(listings)} listings on Security Jobs Network")
            
            # Process each listing
            for listing in listings[:10]:  # Limit to first 10 for testing
                try:
                    # Extract basic information from listing
                    title_elem = listing.find("h2") or listing.find("h3") or listing.find("a", class_=lambda c: c and "title" in c.lower())
                    title = title_elem.text.strip() if title_elem else ""
                    
                    # Extract URL for detailed page
                    detail_url = None
                    if title_elem:
                        if title_elem.name == "a" and title_elem.get("href"):
                            detail_url = title_elem["href"]
                        else:
                            link_elem = title_elem.find("a")
                            if link_elem and link_elem.get("href"):
                                detail_url = link_elem["href"]
                    
                    # Extract company/organization
                    company_elem = listing.find("div", class_=lambda c: c and "company" in c.lower()) or listing.find("span", class_=lambda c: c and "company" in c.lower())
                    company = company_elem.text.strip() if company_elem else ""
                    
                    # Extract location
                    location_elem = listing.find("div", class_=lambda c: c and "location" in c.lower()) or listing.find("span", class_=lambda c: c and "location" in c.lower())
                    location = location_elem.text.strip() if location_elem else ""
                    
                    # If we have a detail URL, scrape the detailed page
                    description = ""
                    requirements = ""
                    contact_info = ""
                    if detail_url:
                        try:
                            detail_response = self._make_request(detail_url, user_agent=user_agent)
                            detail_soup = self._parse_html(detail_response.text)
                            
                            # Extract description
                            desc_elem = detail_soup.find("div", class_=lambda c: c and "description" in c.lower()) or detail_soup.find("div", class_=lambda c: c and "content" in c.lower())
                            description = desc_elem.text.strip() if desc_elem else ""
                            
                            # Extract contact information
                            contact_elem = detail_soup.find("div", class_=lambda c: c and "contact" in c.lower()) or detail_soup.find("div", class_=lambda c: c and "apply" in c.lower())
                            contact_info = contact_elem.text.strip() if contact_elem else ""
                        except Exception as e:
                            self.logger.warning(f"Error scraping detail page {detail_url}: {str(e)}")
                    
                    # Create lead data
                    lead_data = self.extract_lead_data({
                        "title": title,
                        "company": company,
                        "location": location,
                        "description": description,
                        "contact_info": contact_info,
                        "source_url": detail_url or self.jobs_url
                    })
                    
                    leads.append(lead_data)
                except Exception as e:
                    self.logger.warning(f"Error processing listing: {str(e)}")
            
            return leads
        except Exception as e:
            self.logger.error(f"Error scraping Security Jobs Network: {str(e)}")
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
        
        all_text = f"{item.get('title', '')} {item.get('company', '')} {description} {contact_info}"
        
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
            "name": item.get("company", ""),
            "is_government": "government" in item.get("company", "").lower() or 
                            "federal" in item.get("company", "").lower() or 
                            "state" in item.get("company", "").lower()
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
            "location": item.get("location", ""),
            "opportunity_type": opportunity_type,
            "is_armed": is_armed
        }
        
        # Create lead data
        lead_data = {
            "source": "securityjobsnet",
            "source_url": item.get("source_url", ""),
            "lead_type": "job_posting",
            "organization": organization,
            "contacts": contacts,
            "opportunity": opportunity
        }
        
        # Calculate confidence score
        lead_data["confidence_score"] = calculate_confidence_score(lead_data)
        
        return lead_data
