"""
Utility functions for Security Leads Automation

This module provides utility functions for data extraction, validation, and processing.
"""

import re
import string
from datetime import datetime

def extract_email(text):
    """Extract email addresses from text.
    
    Args:
        text (str): Text to extract emails from
        
    Returns:
        list: Extracted email addresses
    """
    if not text:
        return []
    
    # Regular expression for email extraction
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.findall(email_pattern, text)

def extract_phone(text):
    """Extract phone numbers from text.
    
    Args:
        text (str): Text to extract phone numbers from
        
    Returns:
        list: Extracted phone numbers
    """
    if not text:
        return []
    
    # Regular expression for US phone number formats
    phone_patterns = [
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (123) 456-7890, 123-456-7890, 123.456.7890
        r'\d{3}[-.\s]?\d{4}',  # 456-7890, 456.7890
        r'\+\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'  # +1 (123) 456-7890
    ]
    
    results = []
    for pattern in phone_patterns:
        results.extend(re.findall(pattern, text))
    
    return results

def normalize_company_name(name):
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
    suffixes = [
        "inc", "inc.", "incorporated", 
        "llc", "llc.", "l.l.c.", "limited liability company",
        "ltd", "ltd.", "limited",
        "corp", "corp.", "corporation",
        "co", "co.", "company"
    ]
    
    for suffix in suffixes:
        normalized = re.sub(r'\s+' + re.escape(suffix) + r'\s*$', '', normalized)
    
    # Remove punctuation
    normalized = normalized.translate(str.maketrans('', '', string.punctuation))
    
    # Remove extra whitespace
    normalized = ' '.join(normalized.split())
    
    return normalized

def is_valid_email(email):
    """Check if an email address is valid.
    
    Args:
        email (str): Email address
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not email:
        return False
    
    # Basic validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False
    
    # Check for generic emails
    generic_prefixes = ['info', 'contact', 'admin', 'sales', 'support', 'hello', 'office']
    prefix = email.split('@')[0].lower()
    
    if prefix in generic_prefixes:
        return False
    
    return True

def is_valid_phone(phone):
    """Check if a phone number is valid.
    
    Args:
        phone (str): Phone number
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not phone:
        return False
    
    # Remove non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Check length (7-15 digits)
    return 7 <= len(digits) <= 15

def format_phone(phone):
    """Format a phone number consistently.
    
    Args:
        phone (str): Phone number
        
    Returns:
        str: Formatted phone number
    """
    if not phone:
        return ""
    
    # Remove non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Format based on length
    if len(digits) == 10:  # US number without country code
        return f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"
    elif len(digits) == 11 and digits[0] == '1':  # US number with country code
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:11]}"
    else:
        # Return with country code if available
        if len(digits) > 10:
            return f"+{digits[0:len(digits)-10]} {digits[-10:-7]}-{digits[-7:-4]}-{digits[-4:]}"
        else:
            return phone  # Return original if can't format

def extract_date(text):
    """Extract dates from text.
    
    Args:
        text (str): Text to extract dates from
        
    Returns:
        list: Extracted dates as datetime objects
    """
    if not text:
        return []
    
    # Common date formats
    date_patterns = [
        r'\d{1,2}/\d{1,2}/\d{2,4}',  # MM/DD/YYYY, M/D/YY
        r'\d{1,2}-\d{1,2}-\d{2,4}',  # MM-DD-YYYY, M-D-YY
        r'\d{1,2}\.\d{1,2}\.\d{2,4}',  # MM.DD.YYYY, M.D.YY
        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{2,4}'  # January 1, 2020
    ]
    
    results = []
    for pattern in date_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                # Try different date formats
                for fmt in ['%m/%d/%Y', '%m/%d/%y', '%m-%d-%Y', '%m-%d-%y', 
                           '%m.%d.%Y', '%m.%d.%y', '%B %d, %Y', '%B %d %Y']:
                    try:
                        dt = datetime.strptime(match, fmt)
                        results.append(dt)
                        break
                    except ValueError:
                        continue
            except Exception:
                continue
    
    return results

def detect_security_keywords(text):
    """Detect security-related keywords in text.
    
    Args:
        text (str): Text to analyze
        
    Returns:
        dict: Dictionary with keyword categories and matches
    """
    if not text:
        return {}
    
    # Convert to lowercase for case-insensitive matching
    text_lower = text.lower()
    
    # Define keyword categories
    keywords = {
        'security_type': [
            'armed security', 'unarmed security', 'security guard', 'security officer',
            'security personnel', 'security staff', 'security service'
        ],
        'event_type': [
            'event security', 'concert security', 'festival security', 'conference security',
            'wedding security', 'party security', 'corporate event'
        ],
        'construction': [
            'construction site', 'construction security', 'site security',
            'building site', 'construction project'
        ],
        'requirements': [
            'license', 'certification', 'experience', 'background check',
            'training', 'armed', 'unarmed', 'uniform', 'guard card'
        ]
    }
    
    # Find matches
    results = {}
    for category, terms in keywords.items():
        matches = []
        for term in terms:
            if term in text_lower:
                matches.append(term)
        
        if matches:
            results[category] = matches
    
    return results

def calculate_confidence_score(lead_data):
    """Calculate confidence score for a lead.
    
    Args:
        lead_data (dict): Lead data
        
    Returns:
        float: Confidence score (0.0-1.0)
    """
    score = 0.5  # Start with neutral score
    
    # Check organization name
    if lead_data.get('organization', {}).get('name'):
        score += 0.1
    
    # Check contact information
    contacts = lead_data.get('contacts', [])
    if contacts:
        # Bonus for having contacts
        score += 0.05
        
        # Check for email and phone
        has_email = any(contact.get('email') for contact in contacts)
        has_phone = any(contact.get('phone') for contact in contacts)
        
        if has_email:
            score += 0.1
        if has_phone:
            score += 0.1
    
    # Check opportunity details
    opportunity = lead_data.get('opportunity', {})
    if opportunity.get('title'):
        score += 0.05
    if opportunity.get('description'):
        score += 0.05
    if opportunity.get('location'):
        score += 0.05
    
    # Cap at 1.0
    return min(1.0, score)
