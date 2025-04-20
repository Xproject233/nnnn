"""
Enhanced data extraction module with state detection and normalization
for Security Leads Automation system
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any

# US States mapping (abbreviation to full name and vice versa)
US_STATES = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 
    'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
    'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho', 
    'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
    'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland', 
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
    'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 
    'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
    'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma', 
    'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 
    'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
    'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia'
}

# Create reverse mapping (full name to abbreviation)
US_STATES_REVERSE = {v: k for k, v in US_STATES.items()}

class StateExtractor:
    """Class for extracting and normalizing state information from text."""
    
    def __init__(self, logger=None):
        """Initialize the state extractor.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        
        # Compile regex patterns for state detection
        self.state_abbr_pattern = re.compile(r'\b(' + '|'.join(US_STATES.keys()) + r')\b')
        self.state_name_pattern = re.compile(r'\b(' + '|'.join(US_STATES.values()) + r')\b', re.IGNORECASE)
        
        # Common city-state patterns
        self.city_state_pattern = re.compile(r'\b([A-Z][a-z\.\s]+),\s*(' + '|'.join(US_STATES.keys()) + r')\b')
        self.city_state_zip_pattern = re.compile(r'\b([A-Z][a-z\.\s]+),\s*(' + '|'.join(US_STATES.keys()) + r')\s+\d{5}(-\d{4})?\b')
    
    def extract_state(self, text: str) -> Optional[Dict[str, str]]:
        """Extract state information from text.
        
        Args:
            text: Text to extract state from
            
        Returns:
            Dictionary with state_code and state_name, or None if no state found
        """
        if not text:
            return None
        
        # Try to find city, state pattern first (most reliable)
        city_state_match = self.city_state_pattern.search(text)
        if city_state_match:
            state_code = city_state_match.group(2)
            return {
                'state_code': state_code,
                'state_name': US_STATES.get(state_code)
            }
        
        # Try to find city, state, zip pattern
        city_state_zip_match = self.city_state_zip_pattern.search(text)
        if city_state_zip_match:
            state_code = city_state_zip_match.group(2)
            return {
                'state_code': state_code,
                'state_name': US_STATES.get(state_code)
            }
        
        # Try to find state abbreviation
        state_abbr_match = self.state_abbr_pattern.search(text)
        if state_abbr_match:
            state_code = state_abbr_match.group(0)
            return {
                'state_code': state_code,
                'state_name': US_STATES.get(state_code)
            }
        
        # Try to find state name
        state_name_match = self.state_name_pattern.search(text)
        if state_name_match:
            state_name = state_name_match.group(0)
            # Normalize case
            state_name = state_name.title()
            # Handle special cases
            if state_name == "District Of Columbia":
                state_name = "District of Columbia"
            
            return {
                'state_code': US_STATES_REVERSE.get(state_name),
                'state_name': state_name
            }
        
        return None
    
    def extract_states_from_lead(self, lead_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract state information from various fields in a lead.
        
        Args:
            lead_data: Lead data dictionary
            
        Returns:
            List of state dictionaries found in the lead
        """
        states = []
        state_codes = set()  # To track unique states
        
        # Fields to check for state information
        fields_to_check = [
            'location', 'address', 'description', 'title',
            'company_location', 'job_location', 'contact_address'
        ]
        
        # Check each field
        for field in fields_to_check:
            if field in lead_data and lead_data[field]:
                state_info = self.extract_state(lead_data[field])
                if state_info and state_info['state_code'] not in state_codes:
                    states.append(state_info)
                    state_codes.add(state_info['state_code'])
        
        return states
    
    def normalize_state(self, state_input: str) -> Optional[Dict[str, str]]:
        """Normalize state input to standard format.
        
        Args:
            state_input: State input (code or name)
            
        Returns:
            Dictionary with state_code and state_name, or None if invalid
        """
        if not state_input:
            return None
        
        # Check if it's a state code
        state_input = state_input.strip().upper()
        if state_input in US_STATES:
            return {
                'state_code': state_input,
                'state_name': US_STATES[state_input]
            }
        
        # Check if it's a state name
        state_input_title = state_input.title()
        if state_input_title in US_STATES_REVERSE:
            return {
                'state_code': US_STATES_REVERSE[state_input_title],
                'state_name': state_input_title
            }
        
        # Try to extract from text
        return self.extract_state(state_input)
    
    def get_all_states(self) -> List[Dict[str, str]]:
        """Get list of all US states in standard format.
        
        Returns:
            List of dictionaries with state_code and state_name
        """
        return [
            {'state_code': code, 'state_name': name}
            for code, name in US_STATES.items()
        ]


# Enhanced location extraction with state detection
def extract_location_with_state(text: str, state_extractor: StateExtractor = None) -> Dict[str, Any]:
    """Extract location information including state from text.
    
    Args:
        text: Text to extract location from
        state_extractor: Optional StateExtractor instance
        
    Returns:
        Dictionary with location information
    """
    if state_extractor is None:
        state_extractor = StateExtractor()
    
    location_info = {
        'full_location': text,
        'state': None,
        'city': None,
        'zip_code': None
    }
    
    if not text:
        return location_info
    
    # Extract state
    state_info = state_extractor.extract_state(text)
    if state_info:
        location_info['state'] = state_info
    
    # Extract zip code
    zip_match = re.search(r'\b\d{5}(-\d{4})?\b', text)
    if zip_match:
        location_info['zip_code'] = zip_match.group(0)
    
    # Extract city (if we found a state with city-state pattern)
    city_state_match = state_extractor.city_state_pattern.search(text)
    if city_state_match:
        location_info['city'] = city_state_match.group(1).strip()
    
    return location_info


# Function to enhance lead data with state information
def enhance_lead_with_state_info(lead_data: Dict[str, Any]) -> Dict[str, Any]:
    """Enhance lead data with state information.
    
    Args:
        lead_data: Lead data dictionary
        
    Returns:
        Enhanced lead data with state information
    """
    state_extractor = StateExtractor()
    
    # Extract states from various fields
    states = state_extractor.extract_states_from_lead(lead_data)
    
    # Add states to lead data
    lead_data['states'] = states
    
    # If we have a primary location field, enhance it
    if 'location' in lead_data and lead_data['location']:
        lead_data['location_info'] = extract_location_with_state(
            lead_data['location'], state_extractor
        )
    
    return lead_data


# Test function
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("state_extractor_test")
    
    # Create state extractor
    extractor = StateExtractor(logger)
    
    # Test cases
    test_texts = [
        "Security guard needed in Los Angeles, CA 90001",
        "Event security in New York, NY",
        "Construction site in Chicago, Illinois requires security personnel",
        "Security services needed in Austin, TX and Dallas, TX",
        "Looking for armed guards in Washington DC area",
        "Security contract available in Miami FL",
        "RFP for security services in Seattle Washington and Portland Oregon"
    ]
    
    for text in test_texts:
        logger.info(f"Testing: {text}")
        state_info = extractor.extract_state(text)
        if state_info:
            logger.info(f"Found state: {state_info['state_name']} ({state_info['state_code']})")
        else:
            logger.info("No state found")
        
        location_info = extract_location_with_state(text, extractor)
        logger.info(f"Location info: {location_info}")
        logger.info("-" * 50)
    
    # Test lead enhancement
    test_lead = {
        "title": "Security Guard for Construction Site",
        "company": "ABC Construction",
        "location": "Phoenix, AZ 85001",
        "description": "Looking for security guards in the Phoenix area to protect construction site.",
        "contact_address": "123 Main St, Phoenix, Arizona"
    }
    
    enhanced_lead = enhance_lead_with_state_info(test_lead)
    logger.info(f"Enhanced lead: {enhanced_lead}")
