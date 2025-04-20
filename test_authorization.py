"""
Test script for validating the authorization system
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
from scripts.invitation_system import InvitationCodeSystem
from scripts.email_confirmation import EmailConfirmationSystem
from scripts.one_click_deployment import OneClickDeployment

class TestAuthorizationSystem(unittest.TestCase):
    """Test cases for the authorization system."""
    
    def setUp(self):
        """Set up test environment."""
        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger("test_authorization")
        
        # Create test config
        self.test_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        self.test_config_path = self.test_dir / "test_config.json"
        self.test_data_dir = self.test_dir / "test_data"
        
        # Ensure test data directory exists
        os.makedirs(self.test_data_dir, exist_ok=True)
        
        # Create test config
        test_config = {
            "invitation_system": {
                "admin_email": "admin@example.com",
                "code_expiry_days": 7,
                "max_uses": 1
            },
            "email_system": {
                "smtp_server": "smtp.example.com",
                "smtp_port": 587,
                "smtp_username": "test@example.com",
                "smtp_password": "password",
                "from_email": "noreply@example.com",
                "admin_email": "admin@example.com",
                "base_url": "https://example.com"
            },
            "deployment": {
                "script": str(self.test_dir / "mock_deploy.sh"),
                "log": str(self.test_data_dir / "deployment.log")
            }
        }
        
        with open(self.test_config_path, 'w') as f:
            json.dump(test_config, f, indent=2)
        
        # Create mock deployment script
        with open(self.test_dir / "mock_deploy.sh", 'w') as f:
            f.write("#!/bin/bash\necho 'Mock deployment executed'\nexit 0")
        os.chmod(self.test_dir / "mock_deploy.sh", 0o755)
        
        # Initialize systems
        self.invitation_system = InvitationCodeSystem(self.test_config_path, self.logger)
        self.email_system = EmailConfirmationSystem(self.test_config_path, self.logger)
        self.deployment_system = OneClickDeployment(self.test_config_path, self.logger)
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove test files
        if os.path.exists(self.test_config_path):
            os.remove(self.test_config_path)
        
        if os.path.exists(self.test_dir / "mock_deploy.sh"):
            os.remove(self.test_dir / "mock_deploy.sh")
        
        # Remove test data directory
        for file in os.listdir(self.test_data_dir):
            os.remove(os.path.join(self.test_data_dir, file))
        os.rmdir(self.test_data_dir)
    
    def test_invitation_code_generation(self):
        """Test invitation code generation."""
        # Generate a code
        code = self.invitation_system.generate_code("test@example.com", "Test invitation")
        
        # Verify code was generated
        self.assertIsNotNone(code)
        self.assertTrue(len(code) > 0)
        
        # Verify code is in the system
        code_info = self.invitation_system.get_code_info(code)
        self.assertIsNotNone(code_info)
        self.assertEqual(code_info["email"], "test@example.com")
        self.assertEqual(code_info["note"], "Test invitation")
        self.assertFalse(code_info["confirmed"])
        self.assertFalse(code_info["active"])
    
    def test_invitation_code_confirmation(self):
        """Test invitation code confirmation."""
        # Generate a code
        code = self.invitation_system.generate_code("test@example.com", "Test invitation")
        
        # Confirm the code
        success = self.invitation_system.confirm_code(code)
        self.assertTrue(success)
        
        # Verify code is confirmed and active
        code_info = self.invitation_system.get_code_info(code)
        self.assertTrue(code_info["confirmed"])
        self.assertTrue(code_info["active"])
    
    def test_invitation_code_validation(self):
        """Test invitation code validation."""
        # Generate a code
        code = self.invitation_system.generate_code("test@example.com", "Test invitation")
        
        # Validate unconfirmed code (should fail)
        valid = self.invitation_system.validate_code(code)
        self.assertFalse(valid)
        
        # Confirm the code
        self.invitation_system.confirm_code(code)
        
        # Validate confirmed code (should succeed)
        valid = self.invitation_system.validate_code(code)
        self.assertTrue(valid)
    
    def test_invitation_code_usage(self):
        """Test invitation code usage."""
        # Generate a code
        code = self.invitation_system.generate_code("test@example.com", "Test invitation")
        
        # Confirm the code
        self.invitation_system.confirm_code(code)
        
        # Use the code
        success = self.invitation_system.use_code(code)
        self.assertTrue(success)
        
        # Verify code usage count
        code_info = self.invitation_system.get_code_info(code)
        self.assertEqual(code_info["uses"], 1)
        
        # Try to use the code again (should fail with max_uses=1)
        success = self.invitation_system.use_code(code)
        self.assertFalse(success)
    
    def test_email_confirmation_workflow(self):
        """Test email confirmation workflow."""
        # Mock the _send_email method to avoid actual email sending
        original_send_email = self.email_system._send_email
        self.email_system._send_email = lambda to, subject, html: True
        
        try:
            # Generate a code and request confirmation
            code = self.email_system.generate_and_request_confirmation("test@example.com", "Test invitation")
            self.assertIsNotNone(code)
            
            # Confirm the code and notify user
            success = self.email_system.confirm_and_notify(code)
            self.assertTrue(success)
            
            # Verify code is confirmed and active
            code_info = self.invitation_system.get_code_info(code)
            self.assertTrue(code_info["confirmed"])
            self.assertTrue(code_info["active"])
        finally:
            # Restore original method
            self.email_system._send_email = original_send_email
    
    def test_one_click_deployment(self):
        """Test one-click deployment."""
        # Generate and confirm a code
        code = self.invitation_system.generate_code("test@example.com", "Test invitation")
        self.invitation_system.confirm_code(code)
        
        # Deploy using the code
        result = self.deployment_system.deploy(code, "127.0.0.1", "Test User Agent")
        
        # Verify deployment result
        self.assertEqual(result["status"], "success")
        self.assertIn("deployment_id", result)
        
        # Verify deployment was recorded
        deployment = self.deployment_system.get_deployment(result["deployment_id"])
        self.assertIsNotNone(deployment)
        self.assertEqual(deployment["code"], code)
        self.assertEqual(deployment["email"], "test@example.com")
        self.assertEqual(deployment["status"], "success")
        
        # Verify code was used
        code_info = self.invitation_system.get_code_info(code)
        self.assertEqual(code_info["uses"], 1)
    
    def test_invalid_code_deployment(self):
        """Test deployment with invalid code."""
        # Try to deploy with non-existent code
        result = self.deployment_system.deploy("invalid-code", "127.0.0.1", "Test User Agent")
        
        # Verify deployment failed
        self.assertEqual(result["status"], "error")
        self.assertIn("Invalid invitation code", result["message"])
    
    def test_expired_code_deployment(self):
        """Test deployment with expired code."""
        # Generate a code with expiry in the past
        code = self.invitation_system.generate_code("test@example.com", "Test invitation")
        code_data = self.invitation_system.get_code_info(code)
        
        # Manually set expiry to past date
        import datetime
        past_date = (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat()
        code_data["expires_at"] = past_date
        self.invitation_system._save_codes()
        
        # Confirm the code
        self.invitation_system.confirm_code(code)
        
        # Try to deploy with expired code
        result = self.deployment_system.deploy(code, "127.0.0.1", "Test User Agent")
        
        # Verify deployment failed
        self.assertEqual(result["status"], "error")
        self.assertIn("Invalid invitation code", result["message"])
    
    def test_end_to_end_workflow(self):
        """Test end-to-end authorization workflow."""
        # Mock the _send_email method to avoid actual email sending
        original_send_email = self.email_system._send_email
        self.email_system._send_email = lambda to, subject, html: True
        
        try:
            # 1. Generate a code and request admin confirmation
            code = self.email_system.generate_and_request_confirmation("test@example.com", "Test invitation")
            self.assertIsNotNone(code)
            
            # 2. Admin confirms the code
            success = self.email_system.confirm_and_notify(code)
            self.assertTrue(success)
            
            # 3. User deploys the system with the code
            result = self.deployment_system.deploy(code, "127.0.0.1", "Test User Agent")
            
            # 4. Verify deployment was successful
            self.assertEqual(result["status"], "success")
            self.assertIn("deployment_id", result)
            
            # 5. Verify code was used and is now inactive (with max_uses=1)
            code_info = self.invitation_system.get_code_info(code)
            self.assertEqual(code_info["uses"], 1)
            self.assertFalse(code_info["active"])
            
            # 6. Try to deploy again with the same code (should fail)
            result = self.deployment_system.deploy(code, "127.0.0.1", "Test User Agent")
            self.assertEqual(result["status"], "error")
        finally:
            # Restore original method
            self.email_system._send_email = original_send_email


if __name__ == "__main__":
    unittest.main()
