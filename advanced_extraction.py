"""
Advanced Data Extraction Module for Security Leads Automation

This module provides specialized functions for extracting and processing
data from various sources, enhancing the basic extraction capabilities.
"""

import re
import nltk
import string
from datetime import datetime
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords

# Download necessary NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class ContactExtractor:
    """Advanced contact information extractor."""
    
    def __init__(self):
        """Initialize the contact extractor."""
        # Common email domains for business emails
        self.business_domains = [
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com',
            'icloud.com', 'protonmail.com', 'mail.com', 'zoho.com'
        ]
        
        # Patterns for different phone number formats
        self.phone_patterns = [
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (123) 456-7890, 123-456-7890
            r'\d{3}[-.\s]?\d{4}',  # 456-7890
            r'\+\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'  # +1 (123) 456-7890
        ]
        
        # Patterns for contact information sections
        self.contact_section_patterns = [
            r'contact\s+information',
            r'contact\s+details',
            r'for\s+more\s+information',
            r'to\s+apply',
            r'inquiries',
            r'questions'
        ]
    
    def extract_emails(self, text):
        """Extract email addresses from text with advanced filtering.
        
        Args:
            text (str): Text to extract emails from
            
        Returns:
            list: Extracted email addresses with quality scores
        """
        if not text:
            return []
        
        # Regular expression for email extraction
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, text)
        
        # Score and filter emails
        scored_emails = []
        for email in emails:
            score = self._score_email(email)
            scored_emails.append({
                'email': email,
                'score': score,
                'is_business': self._is_business_email(email)
            })
        
        # Sort by score (highest first)
        return sorted(scored_emails, key=lambda x: x['score'], reverse=True)
    
    def _score_email(self, email):
        """Score an email based on its quality as a lead contact.
        
        Args:
            email (str): Email address
            
        Returns:
            float: Quality score (0.0-1.0)
        """
        score = 0.5  # Start with neutral score
        
        # Check for generic prefixes (lower score)
        generic_prefixes = ['info', 'contact', 'admin', 'sales', 'support', 'hello', 'office']
        prefix = email.split('@')[0].lower()
        
        if prefix in generic_prefixes:
            score -= 0.2
        
        # Check for personal-looking emails (higher score)
        if re.match(r'^[a-zA-Z]+\.[a-zA-Z]+@', email):  # first.last@ pattern
            score += 0.3
        
        # Check domain
        domain = email.split('@')[-1].lower()
        if domain not in self.business_domains:  # Not a common personal email domain
            score += 0.2
        
        # Cap at range 0.0-1.0
        return max(0.0, min(1.0, score))
    
    def _is_business_email(self, email):
        """Check if an email is likely a business email.
        
        Args:
            email (str): Email address
            
        Returns:
            bool: True if likely a business email, False otherwise
        """
        domain = email.split('@')[-1].lower()
        return domain not in self.business_domains
    
    def extract_phones(self, text):
        """Extract phone numbers from text with advanced filtering.
        
        Args:
            text (str): Text to extract phone numbers from
            
        Returns:
            list: Extracted phone numbers with formatting
        """
        if not text:
            return []
        
        results = []
        for pattern in self.phone_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Format the phone number
                formatted = self._format_phone(match)
                if formatted:
                    results.append({
                        'phone': formatted,
                        'original': match
                    })
        
        # Remove duplicates (keeping the first occurrence)
        unique_results = []
        seen = set()
        for item in results:
            normalized = re.sub(r'\D', '', item['phone'])
            if normalized not in seen and len(normalized) >= 7:
                seen.add(normalized)
                unique_results.append(item)
        
        return unique_results
    
    def _format_phone(self, phone):
        """Format a phone number consistently.
        
        Args:
            phone (str): Phone number
            
        Returns:
            str: Formatted phone number
        """
        # Remove non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Format based on length
        if len(digits) == 10:  # US number without country code
            return f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"
        elif len(digits) == 11 and digits[0] == '1':  # US number with country code
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:11]}"
        elif len(digits) >= 7:  # Other formats
            return phone  # Return original if can't format nicely
        else:
            return None  # Too short to be valid
    
    def extract_contact_sections(self, text):
        """Extract sections of text likely to contain contact information.
        
        Args:
            text (str): Full text
            
        Returns:
            list: Extracted contact sections
        """
        if not text:
            return []
        
        # Split text into sentences
        sentences = sent_tokenize(text)
        
        contact_sections = []
        in_contact_section = False
        current_section = []
        
        for sentence in sentences:
            # Check if sentence indicates start of contact section
            if any(re.search(pattern, sentence.lower()) for pattern in self.contact_section_patterns):
                if in_contact_section and current_section:
                    contact_sections.append(' '.join(current_section))
                in_contact_section = True
                current_section = [sentence]
            elif in_contact_section:
                # If we're in a contact section, add the sentence
                current_section.append(sentence)
                
                # Check if this sentence likely ends the section
                if len(current_section) > 5 or sentence.endswith('.'):
                    contact_sections.append(' '.join(current_section))
                    in_contact_section = False
                    current_section = []
        
        # Add any remaining section
        if in_contact_section and current_section:
            contact_sections.append(' '.join(current_section))
        
        return contact_sections
    
    def extract_names(self, text):
        """Extract potential person names from text.
        
        Args:
            text (str): Text to extract names from
            
        Returns:
            list: Extracted potential names
        """
        if not text:
            return []
        
        # Simple pattern for names (2-3 capitalized words in sequence)
        name_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})'
        potential_names = re.findall(name_pattern, text)
        
        # Filter out common non-name capitalized phrases
        filtered_names = []
        for name in potential_names:
            words = name.split()
            if len(words) >= 2 and all(len(word) > 1 for word in words):
                filtered_names.append(name)
        
        return filtered_names


class CompanyExtractor:
    """Advanced company information extractor."""
    
    def __init__(self):
        """Initialize the company extractor."""
        # Common company suffixes
        self.company_suffixes = [
            'Inc', 'LLC', 'Ltd', 'Corp', 'Corporation', 'Company', 'Co',
            'Limited', 'Group', 'Holdings', 'Enterprises', 'Services',
            'Solutions', 'Systems', 'Technologies', 'International'
        ]
        
        # Government agency indicators
        self.govt_indicators = [
            'Department', 'Agency', 'Bureau', 'Office', 'Commission',
            'Authority', 'Administration', 'County', 'City of', 'State of',
            'Government', 'Federal', 'Municipal', 'Public', 'District'
        ]
    
    def extract_companies(self, text):
        """Extract company names from text.
        
        Args:
            text (str): Text to extract company names from
            
        Returns:
            list: Extracted company names with metadata
        """
        if not text:
            return []
        
        # Split text into sentences for context
        sentences = sent_tokenize(text)
        
        companies = []
        
        # Pattern for company names with suffixes
        for suffix in self.company_suffixes:
            pattern = r'([A-Z][A-Za-z0-9\s&\',]+)\s+' + re.escape(suffix) + r'\b'
            for sentence in sentences:
                matches = re.findall(pattern, sentence)
                for match in matches:
                    if len(match.strip()) > 2:  # Avoid very short matches
                        companies.append({
                            'name': f"{match.strip()} {suffix}",
                            'is_government': False,
                            'context': sentence
                        })
        
        # Pattern for government agencies
        for indicator in self.govt_indicators:
            pattern = r'([A-Z][A-Za-z0-9\s&\',]+\s+' + re.escape(indicator) + r'|' + re.escape(indicator) + r'\s+[A-Z][A-Za-z0-9\s&\',]+)'
            for sentence in sentences:
                matches = re.findall(pattern, sentence)
                for match in matches:
                    if len(match.strip()) > 2:  # Avoid very short matches
                        companies.append({
                            'name': match.strip(),
                            'is_government': True,
                            'context': sentence
                        })
        
        # Remove duplicates while preserving order
        unique_companies = []
        seen = set()
        for company in companies:
            normalized = self.normalize_company_name(company['name'])
            if normalized not in seen:
                seen.add(normalized)
                unique_companies.append(company)
        
        return unique_companies
    
    def normalize_company_name(self, name):
        """Normalize company name for matching.
        
        Args:
            name (str): Company name
            
        Returns:
            str: Normalized company name
        """
        if not name:
            return ""
        
        # Convert to lowercase
        normalized = name.lower()
        
        # Remove common suffixes
        for suffix in [s.lower() for s in self.company_suffixes]:
            normalized = re.sub(r'\s+' + re.escape(suffix) + r'\s*$', '', normalized)
        
        # Remove punctuation
        normalized = normalized.translate(str.maketrans('', '', string.punctuation))
        
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def is_government_entity(self, name):
        """Check if a company name is likely a government entity.
        
        Args:
            name (str): Company name
            
        Returns:
            bool: True if likely a government entity, False otherwise
        """
        if not name:
            return False
        
        name_lower = name.lower()
        
        # Check for government indicators
        for indicator in [i.lower() for i in self.govt_indicators]:
            if indicator in name_lower:
                return True
        
        return False


class RequirementsExtractor:
    """Extracts job requirements and qualifications from text."""
    
    def __init__(self):
        """Initialize the requirements extractor."""
        # Keywords indicating requirements
        self.requirement_indicators = [
            'required', 'requirements', 'qualifications', 'must have',
            'necessary', 'essential', 'needed', 'minimum', 'mandatory'
        ]
        
        # Security-specific requirement keywords
        self.security_requirements = [
            'license', 'certification', 'guard card', 'background check',
            'experience', 'training', 'armed', 'unarmed', 'clearance',
            'first aid', 'cpr', 'driving', 'patrol', 'surveillance'
        ]
        
        # Stop words for filtering
        self.stop_words = set(stopwords.words('english'))
    
    def extract_requirements(self, text):
        """Extract job requirements from text.
        
        Args:
            text (str): Text to extract requirements from
            
        Returns:
            dict: Extracted requirements by category
        """
        if not text:
            return {}
        
        # Split text into sentences
        sentences = sent_tokenize(text)
        
        # Find requirement sections
        requirement_sections = []
        in_req_section = False
        current_section = []
        
        for sentence in sentences:
            # Check if sentence indicates start of requirements section
            if any(indicator in sentence.lower() for indicator in self.requirement_indicators):
                if in_req_section and current_section:
                    requirement_sections.append(' '.join(current_section))
                in_req_section = True
                current_section = [sentence]
            elif in_req_section:
                # If we're in a requirements section, add the sentence
                current_section.append(sentence)
                
                # Check if this sentence likely ends the section
                if len(current_section) > 10 or sentence.endswith('.') and len(sentence) < 20:
                    requirement_sections.append(' '.join(current_section))
                    in_req_section = False
                    current_section = []
        
        # Add any remaining section
        if in_req_section and current_section:
            requirement_sections.append(' '.join(current_section))
        
        # If no specific sections found, use the whole text
        if not requirement_sections:
            requirement_sections = [text]
        
        # Extract specific requirement types
        requirements = {
            'education': self._extract_education(requirement_sections),
            'experience': self._extract_experience(requirement_sections),
            'licenses': self._extract_licenses(requirement_sections),
            'skills': self._extract_skills(requirement_sections),
            'physical': self._extract_physical(requirement_sections),
            'other': self._extract_other_requirements(requirement_sections)
        }
        
        return requirements
    
    def _extract_education(self, sections):
        """Extract education requirements.
        
        Args:
            sections (list): Text sections to analyze
            
        Returns:
            list: Education requirements
        """
  
(Content truncated due to size limit. Use line ranges to read in chunks)