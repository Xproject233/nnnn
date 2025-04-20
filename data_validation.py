"""
Data Validation Module for Security Leads Automation

This module provides functions for validating and filtering lead data
to ensure quality and relevance of extracted information.
"""

import re
import string
from datetime import datetime

class LeadValidator:
    """Validates and filters lead data."""
    
    def __init__(self, logger=None):
        """Initialize the lead validator.
        
        Args:
            logger: Logger instance for logging validation issues
        """
        self.logger = logger
        
        # Minimum confidence score for valid leads
        self.min_confidence_score = 0.3
        
        # Keywords indicating security-related content
        self.security_keywords = [
            'security', 'guard', 'officer', 'patrol', 'surveillance',
            'protection', 'monitor', 'safety', 'secure', 'watch'
        ]
        
        # Blacklisted terms indicating irrelevant content
        self.blacklist_terms = [
            'cyber security', 'information security', 'network security',
            'security clearance', 'food security', 'financial security',
            'social security', 'security deposit'
        ]
    
    def validate_lead(self, lead_data):
        """Validate a lead and determine if it should be included.
        
        Args:
            lead_data (dict): Lead data to validate
            
        Returns:
            tuple: (is_valid, validation_issues)
        """
        validation_issues = []
        
        # Check confidence score
        if lead_data.get('confidence_score', 0) < self.min_confidence_score:
            validation_issues.append("Confidence score below threshold")
        
        # Check if lead is security-related
        if not self._is_security_related(lead_data):
            validation_issues.append("Not security guard related")
        
        # Check organization name
        if not self._validate_organization(lead_data.get('organization', {})):
            validation_issues.append("Invalid organization data")
        
        # Check opportunity details
        if not self._validate_opportunity(lead_data.get('opportunity', {})):
            validation_issues.append("Invalid opportunity data")
        
        # Check contact information
        if not self._validate_contacts(lead_data.get('contacts', [])):
            validation_issues.append("No valid contact information")
        
        # Log validation issues if logger is available
        if self.logger and validation_issues:
            source_url = lead_data.get('source_url', 'unknown')
            self.logger.warning(f"Validation issues for lead from {source_url}: {', '.join(validation_issues)}")
        
        # Lead is valid if there are no validation issues
        is_valid = len(validation_issues) == 0
        
        return is_valid, validation_issues
    
    def _is_security_related(self, lead_data):
        """Check if lead is related to security guard services.
        
        Args:
            lead_data (dict): Lead data to check
            
        Returns:
            bool: True if security-related, False otherwise
        """
        # Extract text from various fields for analysis
        title = lead_data.get('opportunity', {}).get('title', '')
        description = lead_data.get('opportunity', {}).get('description', '')
        
        # Combine text for analysis
        all_text = f"{title} {description}".lower()
        
        # Check for security keywords
        has_security_keyword = any(keyword in all_text for keyword in self.security_keywords)
        
        # Check for blacklisted terms
        has_blacklist_term = any(term in all_text for term in self.blacklist_terms)
        
        # If has blacklist term but no security keyword, it's likely not relevant
        if has_blacklist_term and not has_security_keyword:
            return False
        
        # If has security keyword, it's likely relevant
        if has_security_keyword:
            return True
        
        # If no clear indicators, default to False
        return False
    
    def _validate_organization(self, organization):
        """Validate organization data.
        
        Args:
            organization (dict): Organization data to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Organization must have a name
        if not organization.get('name'):
            return False
        
        # Name should be at least 2 characters
        if len(organization.get('name', '')) < 2:
            return False
        
        return True
    
    def _validate_opportunity(self, opportunity):
        """Validate opportunity data.
        
        Args:
            opportunity (dict): Opportunity data to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Opportunity must have a title
        if not opportunity.get('title'):
            return False
        
        # Title should be at least 3 characters
        if len(opportunity.get('title', '')) < 3:
            return False
        
        return True
    
    def _validate_contacts(self, contacts):
        """Validate contact information.
        
        Args:
            contacts (list): Contact data to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Must have at least one contact
        if not contacts:
            return False
        
        # At least one contact should have email or phone
        for contact in contacts:
            if contact.get('email') or contact.get('phone'):
                return True
        
        return False


class LeadDeduplicator:
    """Identifies and handles duplicate leads."""
    
    def __init__(self, database_manager=None, logger=None):
        """Initialize the lead deduplicator.
        
        Args:
            database_manager: Database manager instance
            logger: Logger instance for logging deduplication actions
        """
        self.database_manager = database_manager
        self.logger = logger
    
    def is_duplicate(self, lead_data, existing_leads=None):
        """Check if a lead is a duplicate of existing leads.
        
        Args:
            lead_data (dict): Lead data to check
            existing_leads (list, optional): List of existing leads to check against.
                If None, will query database. Defaults to None.
            
        Returns:
            tuple: (is_duplicate, duplicate_lead_id, similarity_score)
        """
        # Get organization name
        org_name = lead_data.get('organization', {}).get('name', '')
        if not org_name:
            return False, None, 0.0
        
        # Get opportunity title
        opp_title = lead_data.get('opportunity', {}).get('title', '')
        if not opp_title:
            return False, None, 0.0
        
        # Normalize organization name and title for comparison
        normalized_org = self._normalize_text(org_name)
        normalized_title = self._normalize_text(opp_title)
        
        # Get existing leads if not provided
        if existing_leads is None and self.database_manager:
            existing_leads = self.database_manager.get_all_leads()
        
        if not existing_leads:
            return False, None, 0.0
        
        # Check for duplicates
        highest_similarity = 0.0
        duplicate_lead_id = None
        
        for existing_lead in existing_leads:
            # Skip if same source URL
            if existing_lead.get('source_url') == lead_data.get('source_url'):
                continue
            
            # Get existing lead organization and title
            existing_org = existing_lead.get('organization', {}).get('name', '')
            existing_title = existing_lead.get('opportunity', {}).get('title', '')
            
            if not existing_org or not existing_title:
                continue
            
            # Normalize for comparison
            normalized_existing_org = self._normalize_text(existing_org)
            normalized_existing_title = self._normalize_text(existing_title)
            
            # Calculate similarity
            org_similarity = self._calculate_similarity(normalized_org, normalized_existing_org)
            title_similarity = self._calculate_similarity(normalized_title, normalized_existing_title)
            
            # Combined similarity score (weighted)
            similarity = (org_similarity * 0.6) + (title_similarity * 0.4)
            
            # Check if similarity exceeds threshold
            if similarity > 0.8 and similarity > highest_similarity:
                highest_similarity = similarity
                duplicate_lead_id = existing_lead.get('id')
        
        is_duplicate = duplicate_lead_id is not None
        
        # Log if duplicate found
        if is_duplicate and self.logger:
            self.logger.info(f"Duplicate lead found: {org_name} - {opp_title} (similarity: {highest_similarity:.2f})")
        
        return is_duplicate, duplicate_lead_id, highest_similarity
    
    def _normalize_text(self, text):
        """Normalize text for comparison.
        
        Args:
            text (str): Text to normalize
            
        Returns:
            str: Normalized text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        normalized = text.lower()
        
        # Remove punctuation
        normalized = normalized.translate(str.maketrans('', '', string.punctuation))
        
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def _calculate_similarity(self, text1, text2):
        """Calculate similarity between two texts.
        
        Args:
            text1 (str): First text
            text2 (str): Second text
            
        Returns:
            float: Similarity score (0.0-1.0)
        """
        if not text1 or not text2:
            return 0.0
        
        # Simple Jaccard similarity
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)


class LeadEnricher:
    """Enriches lead data with additional information."""
    
    def __init__(self, logger=None):
        """Initialize the lead enricher.
        
        Args:
            logger: Logger instance for logging enrichment actions
        """
        self.logger = logger
    
    def enrich_lead(self, lead_data):
        """Enrich lead data with additional information.
        
        Args:
            lead_data (dict): Lead data to enrich
            
        Returns:
            dict: Enriched lead data
        """
        # Make a copy to avoid modifying the original
        enriched_data = lead_data.copy()
        
        # Enrich organization data
        if 'organization' in enriched_data:
            enriched_data['organization'] = self._enrich_organization(enriched_data['organization'])
        
        # Enrich opportunity data
        if 'opportunity' in enriched_data:
            enriched_data['opportunity'] = self._enrich_opportunity(enriched_data['opportunity'])
        
        # Enrich contact data
        if 'contacts' in enriched_data:
            enriched_data['contacts'] = self._enrich_contacts(enriched_data['contacts'])
        
        # Recalculate confidence score
        from ..utils.data_utils import calculate_confidence_score
        enriched_data['confidence_score'] = calculate_confidence_score(enriched_data)
        
        return enriched_data
    
    def _enrich_organization(self, organization):
        """Enrich organization data.
        
        Args:
            organization (dict): Organization data to enrich
            
        Returns:
            dict: Enriched organization data
        """
        # Make a copy to avoid modifying the original
        enriched_org = organization.copy()
        
        # Add industry if missing
        if not enriched_org.get('industry') and enriched_org.get('name'):
            # Simple industry detection based on name
            name_lower = enriched_org['name'].lower()
            
            if any(term in name_lower for term in ['school', 'university', 'college', 'academy']):
                enriched_org['industry'] = 'Education'
            elif any(term in name_lower for term in ['hospital', 'medical', 'health', 'clinic']):
                enriched_org['industry'] = 'Healthcare'
            elif any(term in name_lower for term in ['government', 'city of', 'county', 'state', 'federal']):
                enriched_org['industry'] = 'Government'
            elif any(term in name_lower for term in ['construction', 'builder', 'development']):
                enriched_org['industry'] = 'Construction'
            elif any(term in name_lower for term in ['event', 'entertainment', 'production']):
                enriched_org['industry'] = 'Entertainment'
            elif any(term in name_lower for term in ['retail', 'store', 'shop', 'mall']):
                enriched_org['industry'] = 'Retail'
            else:
                enriched_org['industry'] = 'Security Services'
        
        return enriched_org
    
    def _enrich_opportunity(self, opportunity):
        """Enrich opportunity data.
        
        Args:
            opportunity (dict): Opportunity data to enrich
            
        Returns:
            dict: Enriched opportunity data
        """
        # Make a copy to avoid modifying the original
        enriched_opp = opportunity.copy()
        
        # Add guard count estimate if missing
        if not enriched_opp.get('guard_count') and enriched_opp.get('description'):
            description = enriched_opp['description'].lower()
            
            # Look for numbers followed by guards/officers
            guard_count_matches = re.findall(r'(\d+)\s+(?:guard|officer|security)', description)
            if guard_count_matches:
                try:
                    enriched_opp['guard_count'] = int(guard_count_matches[0])
                except ValueError:
                    pass
        
        # Determine if armed if not specified
        if 'is_armed' not in enriched_opp and enriched_opp.get('description'):
            description = enriched_opp['description'].lower()
            
            if 'armed' in description and not ('unarmed' in description):
                enriched_opp['is_armed'] = True
            elif 'unarmed' in description:
                enriched_opp['is_armed'] = False
        
        return enriched_opp
    
    def _enrich_contacts(self, contacts):
        """Enrich contact data.
        
        Args:
            contacts (list): Contact data to enrich
            
        Returns:
            list: Enriched contact data
        """
        # Make a copy to avoid modifying the original
        enriched_contacts = [contact.copy() for contact in contacts]
        
        for contact in enriched_contacts:
            # Format phone number if present
            if contact.get('phone'):
                contact['phone'] = self._format_phone(contact['phone'])
            
            # Try to extract name parts if not present
            if not contact.get('first_name') and not contact.get('last_name') and contact.get('email'):
                email_prefix = contact['email'].split('@')[0]
                
                # Check for common name patterns in email
                if '.' in email_prefix:
                    # Likely first.last format
                    parts = email_prefix.split('.')
                    if len(parts) >= 2:
                        contact['first_
(Content truncated due to size limit. Use line ranges to read in chunks)