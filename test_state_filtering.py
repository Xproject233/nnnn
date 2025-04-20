"""
Test script for validating the state filtering functionality
"""

import os
import sys
import json
import logging
import unittest
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules to test
from scripts.utils.state_extraction import StateExtractor, enhance_lead_with_state_info
from scripts.core.lead_database import LeadDatabase

class TestStateFiltering(unittest.TestCase):
    """Test cases for the state filtering functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger("test_state_filtering")
        
        # Create test directory
        self.test_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        self.test_data_dir = self.test_dir / "test_data"
        
        # Ensure test data directory exists
        os.makedirs(self.test_data_dir, exist_ok=True)
        
        # Create test database
        self.test_db_path = str(self.test_data_dir / "test_leads.db")
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        
        self.db = LeadDatabase(self.test_db_path, self.logger)
        
        # Create state extractor
        self.state_extractor = StateExtractor(self.logger)
        
        # Add test leads
        self.test_leads = [
            {
                "title": "Security Guard for Construction Site",
                "company": "ABC Construction",
                "location": "Phoenix, AZ 85001",
                "description": "Looking for security guards in the Phoenix area to protect construction site.",
                "contact_name": "John Smith",
                "contact_email": "john@abcconstruction.com",
                "contact_phone": "555-123-4567",
                "source": "ConstructionJobs",
                "url": "https://example.com/job1",
                "date_posted": "2025-04-15",
                "date_scraped": "2025-04-20",
                "confidence_score": 0.85,
                "status": "new"
            },
            {
                "title": "Event Security Staff",
                "company": "XYZ Events",
                "location": "Los Angeles, CA 90001",
                "description": "Security staff needed for upcoming events in the Los Angeles area.",
                "contact_name": "Jane Doe",
                "contact_email": "jane@xyzevents.com",
                "contact_phone": "555-987-6543",
                "source": "EventJobs",
                "url": "https://example.com/job2",
                "date_posted": "2025-04-16",
                "date_scraped": "2025-04-20",
                "confidence_score": 0.92,
                "status": "new"
            },
            {
                "title": "Armed Security Guard",
                "company": "Secure Solutions",
                "location": "New York, NY 10001",
                "description": "Armed security guards needed for various locations in New York City.",
                "contact_name": "Bob Johnson",
                "contact_email": "bob@securesolutions.com",
                "contact_phone": "555-456-7890",
                "source": "SecurityJobs",
                "url": "https://example.com/job3",
                "date_posted": "2025-04-17",
                "date_scraped": "2025-04-20",
                "confidence_score": 0.78,
                "status": "new"
            },
            {
                "title": "Security Officer - Multiple Locations",
                "company": "National Security Inc.",
                "location": "Multiple locations: Chicago IL, Dallas TX, Miami FL",
                "description": "Security officers needed for various client sites across the country.",
                "contact_name": "Sarah Williams",
                "contact_email": "sarah@nationalsecurity.com",
                "contact_phone": "555-789-0123",
                "source": "SecurityJobs",
                "url": "https://example.com/job4",
                "date_posted": "2025-04-18",
                "date_scraped": "2025-04-20",
                "confidence_score": 0.88,
                "status": "new"
            },
            {
                "title": "Construction Site Security",
                "company": "Build Safe Security",
                "location": "Denver, Colorado",
                "description": "Security personnel needed for construction sites in Denver metro area.",
                "contact_name": "Mike Brown",
                "contact_email": "mike@buildsafe.com",
                "contact_phone": "555-234-5678",
                "source": "ConstructionJobs",
                "url": "https://example.com/job5",
                "date_posted": "2025-04-19",
                "date_scraped": "2025-04-20",
                "confidence_score": 0.90,
                "status": "new"
            }
        ]
        
        for lead in self.test_leads:
            self.db.add_lead(lead)
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove test database
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def test_state_extraction(self):
        """Test state extraction from text."""
        # Test state abbreviation
        state_info = self.state_extractor.extract_state("Phoenix, AZ 85001")
        self.assertIsNotNone(state_info)
        self.assertEqual(state_info["state_code"], "AZ")
        self.assertEqual(state_info["state_name"], "Arizona")
        
        # Test state name
        state_info = self.state_extractor.extract_state("Denver, Colorado")
        self.assertIsNotNone(state_info)
        self.assertEqual(state_info["state_code"], "CO")
        self.assertEqual(state_info["state_name"], "Colorado")
        
        # Test city-state pattern
        state_info = self.state_extractor.extract_state("Los Angeles, CA")
        self.assertIsNotNone(state_info)
        self.assertEqual(state_info["state_code"], "CA")
        self.assertEqual(state_info["state_name"], "California")
        
        # Test multiple states in text
        state_info = self.state_extractor.extract_state("Multiple locations: Chicago IL, Dallas TX, Miami FL")
        self.assertIsNotNone(state_info)
        # Should extract the first state found
        self.assertEqual(state_info["state_code"], "IL")
        self.assertEqual(state_info["state_name"], "Illinois")
    
    def test_lead_enhancement_with_states(self):
        """Test enhancing lead data with state information."""
        # Test lead with state abbreviation
        lead = {
            "title": "Test Lead",
            "location": "Phoenix, AZ 85001"
        }
        
        enhanced_lead = enhance_lead_with_state_info(lead)
        self.assertIn("states", enhanced_lead)
        self.assertEqual(len(enhanced_lead["states"]), 1)
        self.assertEqual(enhanced_lead["states"][0]["state_code"], "AZ")
        
        # Test lead with multiple states
        lead = {
            "title": "Test Lead",
            "location": "Multiple locations: Chicago IL, Dallas TX, Miami FL"
        }
        
        enhanced_lead = enhance_lead_with_state_info(lead)
        self.assertIn("states", enhanced_lead)
        self.assertGreaterEqual(len(enhanced_lead["states"]), 1)
        
        # Test lead with state in description
        lead = {
            "title": "Test Lead",
            "location": "United States",
            "description": "Position available in Denver, Colorado"
        }
        
        enhanced_lead = enhance_lead_with_state_info(lead)
        self.assertIn("states", enhanced_lead)
        self.assertEqual(len(enhanced_lead["states"]), 1)
        self.assertEqual(enhanced_lead["states"][0]["state_code"], "CO")
    
    def test_database_state_filtering(self):
        """Test database filtering by state."""
        # Test filtering by state code
        az_leads, az_count = self.db.get_leads({"state": "AZ"})
        self.assertEqual(az_count, 1)
        self.assertEqual(az_leads[0]["location"], "Phoenix, AZ 85001")
        
        # Test filtering by state name
        ca_leads, ca_count = self.db.get_leads({"state": "California"})
        self.assertEqual(ca_count, 1)
        self.assertEqual(ca_leads[0]["location"], "Los Angeles, CA 90001")
        
        # Test filtering by state in multi-state lead
        tx_leads, tx_count = self.db.get_leads({"state": "TX"})
        self.assertEqual(tx_count, 1)
        self.assertIn("Dallas TX", tx_leads[0]["location"])
        
        # Test filtering by state with no leads
        wa_leads, wa_count = self.db.get_leads({"state": "WA"})
        self.assertEqual(wa_count, 0)
        self.assertEqual(len(wa_leads), 0)
    
    def test_state_summary(self):
        """Test getting state summary."""
        state_summary = self.db.get_states_summary()
        
        # Check that we have the expected states
        state_codes = [state["state_code"] for state in state_summary]
        self.assertIn("AZ", state_codes)
        self.assertIn("CA", state_codes)
        self.assertIn("NY", state_codes)
        self.assertIn("IL", state_codes)
        self.assertIn("TX", state_codes)
        self.assertIn("FL", state_codes)
        self.assertIn("CO", state_codes)
        
        # Check lead counts
        for state in state_summary:
            if state["state_code"] == "AZ":
                self.assertEqual(state["lead_count"], 1)
            if state["state_code"] == "CA":
                self.assertEqual(state["lead_count"], 1)
            if state["state_code"] == "NY":
                self.assertEqual(state["lead_count"], 1)
    
    def test_combined_filtering(self):
        """Test combining state filtering with other filters."""
        # Filter by state and source
        results, count = self.db.get_leads({
            "state": "AZ",
            "source": "ConstructionJobs"
        })
        self.assertEqual(count, 1)
        self.assertEqual(results[0]["location"], "Phoenix, AZ 85001")
        
        # Filter by state and minimum confidence
        results, count = self.db.get_leads({
            "state": "NY",
            "min_confidence": 0.7
        })
        self.assertEqual(count, 1)
        self.assertEqual(results[0]["location"], "New York, NY 10001")
        
        # Filter by state and keyword
        results, count = self.db.get_leads({
            "state": "CO",
            "keyword": "construction"
        })
        self.assertEqual(count, 1)
        self.assertIn("Denver", results[0]["location"])
    
    def test_reprocessing_leads(self):
        """Test reprocessing leads for state information."""
        # Add a lead without state information
        lead_without_state = {
            "title": "Security Guard",
            "company": "Test Company",
            "location": "Unknown Location",
            "description": "This is a test lead without state information.",
            "source": "Test",
            "date_scraped": "2025-04-20",
            "confidence_score": 0.5
        }
        
        lead_id = self.db.add_lead(lead_without_state)
        
        # Update the lead with state information in the description
        lead = self.db.get_lead(lead_id)
        lead["description"] = "This is a test lead with state information added. Located in Seattle, WA."
        self.db.add_lead(lead)
        
        # Reprocess all leads
        processed, updated = self.db.reprocess_all_leads_for_states()
        
        # Check that the lead was updated with state information
        lead = self.db.get_lead(lead_id)
        self.assertIn("states", lead)
        self.assertGreaterEqual(len(lead["states"]), 1)
        
        # Check that we can now filter by the new state
        wa_leads, wa_count = self.db.get_leads({"state": "WA"})
        self.assertEqual(wa_count, 1)
        self.assertEqual(wa_leads[0]["id"], lead_id)


if __name__ == "__main__":
    unittest.main()
