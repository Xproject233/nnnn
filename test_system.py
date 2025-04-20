"""
Test Script for Security Leads Automation System

This script tests the functionality of the security leads automation system,
validating that all components work together correctly.
"""

import os
import sys
import json
import time
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import SecurityLeadsAutomation

class TestSecurityLeadsAutomation(unittest.TestCase):
    """Test cases for the Security Leads Automation system."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Use a test configuration
        cls.base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        cls.test_config_path = str(cls.base_dir / "test_config.json")
        
        # Create test config with test database path
        test_config = {
            "database": {
                "type": "sqlite",
                "path": str(cls.base_dir / "data" / "test_leads.db")
            },
            "logging": {
                "level": "INFO",
                "file": str(cls.base_dir / "logs" / "test_security_leads.log"),
                "max_size": 10485760,
                "backup_count": 5
            },
            "scrapers": {
                "user_agents": [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                ],
                "request_delay": 1,
                "timeout": 10,
                "max_retries": 2,
                "sources": {
                    "instantmarkets": {
                        "url": "https://www.instantmarkets.com/q/event_security_guard",
                        "enabled": True
                    }
                }
            },
            "scheduler": {
                "schedule": {
                    "daily": ["08:00"]
                },
                "max_history": 10,
                "sources": ["instantmarkets"]
            },
            "validation": {
                "min_confidence_score": 0.3,
                "deduplication_enabled": True,
                "enrichment_enabled": True
            }
        }
        
        # Write test config
        with open(cls.test_config_path, 'w') as f:
            json.dump(test_config, f, indent=2)
        
        # Initialize system with test config
        cls.system = SecurityLeadsAutomation(cls.test_config_path)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after tests."""
        # Stop the system
        cls.system.stop()
        
        # Remove test database
        test_db_path = cls.base_dir / "data" / "test_leads.db"
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        # Remove test config
        if os.path.exists(cls.test_config_path):
            os.remove(cls.test_config_path)
    
    def test_01_system_initialization(self):
        """Test system initialization."""
        # Check that components are initialized
        self.assertIsNotNone(self.system.database)
        self.assertIsNotNone(self.system.scraper_manager)
        self.assertIsNotNone(self.system.lead_validator)
        self.assertIsNotNone(self.system.lead_deduplicator)
        self.assertIsNotNone(self.system.lead_enricher)
        self.assertIsNotNone(self.system.lead_filter)
        self.assertIsNotNone(self.system.scheduler)
    
    def test_02_start_stop(self):
        """Test starting and stopping the system."""
        # Start the system
        result = self.system.start()
        self.assertTrue(result)
        
        # Check that scheduler is running
        status = self.system.get_status()
        self.assertIn("scheduler", status)
        
        # Stop the system
        result = self.system.stop()
        self.assertTrue(result)
    
    def test_03_mock_lead_storage(self):
        """Test storing and retrieving leads."""
        # Create a mock lead
        mock_lead = {
            "source": "test",
            "source_url": "https://example.com/test",
            "lead_type": "job_posting",
            "confidence_score": 0.8,
            "organization": {
                "name": "Test Security Company",
                "is_government": False
            },
            "contacts": [
                {
                    "email": "contact@example.com",
                    "phone": "(123) 456-7890"
                }
            ],
            "opportunity": {
                "title": "Security Guard Needed",
                "description": "Looking for security guards for an event",
                "opportunity_type": "event",
                "is_armed": False,
                "location": "New York, NY"
            }
        }
        
        # Store the lead
        lead_id = self.system.database.store_lead(mock_lead)
        self.assertIsNotNone(lead_id)
        
        # Retrieve the lead
        retrieved_lead = self.system.database.get_lead(lead_id)
        self.assertIsNotNone(retrieved_lead)
        self.assertEqual(retrieved_lead["source"], "test")
        self.assertEqual(retrieved_lead["organization"]["name"], "Test Security Company")
    
    def test_04_lead_filtering(self):
        """Test lead filtering."""
        # Create mock leads with different properties
        leads = [
            {
                "source": "test1",
                "confidence_score": 0.9,
                "opportunity": {"opportunity_type": "event", "is_armed": False}
            },
            {
                "source": "test2",
                "confidence_score": 0.4,
                "opportunity": {"opportunity_type": "construction", "is_armed": True}
            },
            {
                "source": "test3",
                "confidence_score": 0.2,
                "opportunity": {"opportunity_type": "event", "is_armed": True}
            }
        ]
        
        # Test filtering by confidence score
        filtered = self.system.lead_filter.filter_leads(leads, {"min_confidence": 0.5})
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["source"], "test1")
        
        # Test filtering by opportunity type
        filtered = self.system.lead_filter.filter_leads(leads, {"opportunity_type": "event"})
        self.assertEqual(len(filtered), 2)
        
        # Test filtering by armed status
        filtered = self.system.lead_filter.filter_leads(leads, {"is_armed": True})
        self.assertEqual(len(filtered), 2)
        
        # Test combined filters
        filtered = self.system.lead_filter.filter_leads(
            leads, {"opportunity_type": "event", "is_armed": True}
        )
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["source"], "test3")
    
    def test_05_lead_validation(self):
        """Test lead validation."""
        # Valid lead
        valid_lead = {
            "confidence_score": 0.8,
            "organization": {"name": "Test Company"},
            "opportunity": {"title": "Security Guard", "description": "Need security guards for event"},
            "contacts": [{"email": "test@example.com"}]
        }
        
        # Invalid lead (low confidence)
        invalid_lead1 = {
            "confidence_score": 0.2,
            "organization": {"name": "Test Company"},
            "opportunity": {"title": "Security Guard"},
            "contacts": [{"email": "test@example.com"}]
        }
        
        # Invalid lead (no contact)
        invalid_lead2 = {
            "confidence_score": 0.8,
            "organization": {"name": "Test Company"},
            "opportunity": {"title": "Security Guard"},
            "contacts": []
        }
        
        # Test validation
        is_valid, issues = self.system.lead_validator.validate_lead(valid_lead)
        self.assertTrue(is_valid)
        self.assertEqual(len(issues), 0)
        
        is_valid, issues = self.system.lead_validator.validate_lead(invalid_lead1)
        self.assertFalse(is_valid)
        self.assertIn("Confidence score below threshold", issues)
        
        is_valid, issues = self.system.lead_validator.validate_lead(invalid_lead2)
        self.assertFalse(is_valid)
        self.assertIn("No valid contact information", issues)
    
    def test_06_export_leads(self):
        """Test exporting leads."""
        # Create some test leads in the database
        for i in range(3):
            mock_lead = {
                "source": f"test{i}",
                "source_url": f"https://example.com/test{i}",
                "lead_type": "job_posting",
                "confidence_score": 0.8,
                "organization": {
                    "name": f"Test Company {i}",
                    "is_government": False
                },
                "contacts": [
                    {
                        "email": f"contact{i}@example.com",
                        "phone": f"(123) 456-789{i}"
                    }
                ],
                "opportunity": {
                    "title": f"Security Guard {i}",
                    "description": "Looking for security guards",
                    "opportunity_type": "event",
                    "is_armed": False,
                    "location": "New York, NY"
                }
            }
            self.system.database.store_lead(mock_lead)
        
        # Test JSON export
        json_path = self.system.export_leads(format="json")
        self.assertTrue(os.path.exists(json_path))
        
        # Verify JSON content
        with open(json_path, 'r') as f:
            exported_leads = json.load(f)
        
        self.assertGreaterEqual(len(exported_leads), 3)
        
        # Test CSV export
        csv_path = self.system.export_leads(format="csv")
        self.assertTrue(os.path.exists(csv_path))
        
        # Clean up export files
        if os.path.exists(json_path):
            os.remove(json_path)
        if os.path.exists(csv_path):
            os.remove(csv_path)
    
    def test_07_scheduler_status(self):
        """Test scheduler status reporting."""
        # Start the system
        self.system.start()
        
        # Get status
        status = self.system.get_status()
        
        # Check status structure
        self.assertIn("scheduler", status)
        self.assertIn("database", status)
        self.assertIn("scrapers", status)
        self.assertIn("system_time", status)
        
        # Check scheduler status
        scheduler_status = status["scheduler"]
        self.assertIn("is_running", scheduler_status)
        self.assertIn("next_run", scheduler_status)
        self.assertIn("schedule", scheduler_status)
        
        # Stop the system
        self.system.stop()


if __name__ == "__main__":
    unittest.main()
