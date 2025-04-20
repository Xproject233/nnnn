"""
Invitation Code System for Security Leads Automation

This module provides functionality for generating, validating, and managing
invitation codes that control access to the system.
"""

import os
import sys
import json
import uuid
import hashlib
import datetime
import logging
from pathlib import Path

class InvitationCodeSystem:
    """Manages invitation codes for system access control."""
    
    def __init__(self, config_path=None, logger=None):
        """Initialize the invitation code system.
        
        Args:
            config_path (str, optional): Path to configuration file. Defaults to None.
            logger (Logger, optional): Logger instance. Defaults to None.
        """
        # Set up base paths
        self.base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.data_dir = self.base_dir / "data"
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Set up logger
        self.logger = logger or logging.getLogger(__name__)
        
        # Load configuration
        if not config_path:
            config_path = str(self.base_dir / "config.json")
        
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading configuration: {str(e)}")
            self.config = {}
        
        # Get invitation system configuration
        self.invitation_config = self.config.get("invitation_system", {})
        
        # Set default values if not in config
        self.admin_email = self.invitation_config.get("admin_email", "admin@example.com")
        self.code_expiry_days = self.invitation_config.get("code_expiry_days", 7)
        self.max_uses = self.invitation_config.get("max_uses", 1)
        
        # Load existing invitation codes
        self.codes_file = self.data_dir / "invitation_codes.json"
        self.codes = self._load_codes()
    
    def _load_codes(self):
        """Load invitation codes from file.
        
        Returns:
            dict: Dictionary of invitation codes
        """
        if os.path.exists(self.codes_file):
            try:
                with open(self.codes_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading invitation codes: {str(e)}")
                return {}
        else:
            return {}
    
    def _save_codes(self):
        """Save invitation codes to file."""
        try:
            with open(self.codes_file, 'w') as f:
                json.dump(self.codes, f, indent=2)
            self.logger.info(f"Saved {len(self.codes)} invitation codes")
        except Exception as e:
            self.logger.error(f"Error saving invitation codes: {str(e)}")
    
    def generate_code(self, email=None, note=None):
        """Generate a new invitation code.
        
        Args:
            email (str, optional): Email address of the invitee. Defaults to None.
            note (str, optional): Note about the invitation. Defaults to None.
            
        Returns:
            str: The generated invitation code
        """
        # Generate a unique code
        code = str(uuid.uuid4())
        
        # Create code data
        now = datetime.datetime.now().isoformat()
        expiry = (datetime.datetime.now() + datetime.timedelta(days=self.code_expiry_days)).isoformat()
        
        code_data = {
            "code": code,
            "created_at": now,
            "expires_at": expiry,
            "email": email,
            "note": note,
            "confirmed": False,
            "confirmed_at": None,
            "uses": 0,
            "max_uses": self.max_uses,
            "active": False
        }
        
        # Save code
        self.codes[code] = code_data
        self._save_codes()
        
        self.logger.info(f"Generated invitation code: {code}")
        return code
    
    def confirm_code(self, code):
        """Confirm an invitation code.
        
        Args:
            code (str): The invitation code to confirm
            
        Returns:
            bool: True if confirmation successful, False otherwise
        """
        if code not in self.codes:
            self.logger.warning(f"Attempted to confirm non-existent code: {code}")
            return False
        
        code_data = self.codes[code]
        
        # Check if already confirmed
        if code_data["confirmed"]:
            self.logger.warning(f"Code already confirmed: {code}")
            return False
        
        # Check if expired
        expiry = datetime.datetime.fromisoformat(code_data["expires_at"])
        if datetime.datetime.now() > expiry:
            self.logger.warning(f"Attempted to confirm expired code: {code}")
            return False
        
        # Confirm code
        code_data["confirmed"] = True
        code_data["confirmed_at"] = datetime.datetime.now().isoformat()
        code_data["active"] = True
        
        # Save changes
        self._save_codes()
        
        self.logger.info(f"Confirmed invitation code: {code}")
        return True
    
    def validate_code(self, code):
        """Validate an invitation code.
        
        Args:
            code (str): The invitation code to validate
            
        Returns:
            bool: True if code is valid, False otherwise
        """
        if code not in self.codes:
            self.logger.warning(f"Attempted to validate non-existent code: {code}")
            return False
        
        code_data = self.codes[code]
        
        # Check if confirmed
        if not code_data["confirmed"]:
            self.logger.warning(f"Attempted to use unconfirmed code: {code}")
            return False
        
        # Check if active
        if not code_data["active"]:
            self.logger.warning(f"Attempted to use inactive code: {code}")
            return False
        
        # Check if expired
        expiry = datetime.datetime.fromisoformat(code_data["expires_at"])
        if datetime.datetime.now() > expiry:
            self.logger.warning(f"Attempted to use expired code: {code}")
            return False
        
        # Check if max uses reached
        if code_data["uses"] >= code_data["max_uses"] and code_data["max_uses"] > 0:
            self.logger.warning(f"Attempted to use code that reached max uses: {code}")
            return False
        
        return True
    
    def use_code(self, code):
        """Record a use of an invitation code.
        
        Args:
            code (str): The invitation code to use
            
        Returns:
            bool: True if code use recorded successfully, False otherwise
        """
        if not self.validate_code(code):
            return False
        
        # Increment uses
        self.codes[code]["uses"] += 1
        
        # If max uses reached, deactivate code
        if self.codes[code]["uses"] >= self.codes[code]["max_uses"] and self.codes[code]["max_uses"] > 0:
            self.codes[code]["active"] = False
        
        # Save changes
        self._save_codes()
        
        self.logger.info(f"Used invitation code: {code}")
        return True
    
    def deactivate_code(self, code):
        """Deactivate an invitation code.
        
        Args:
            code (str): The invitation code to deactivate
            
        Returns:
            bool: True if deactivation successful, False otherwise
        """
        if code not in self.codes:
            self.logger.warning(f"Attempted to deactivate non-existent code: {code}")
            return False
        
        # Deactivate code
        self.codes[code]["active"] = False
        
        # Save changes
        self._save_codes()
        
        self.logger.info(f"Deactivated invitation code: {code}")
        return True
    
    def get_code_info(self, code):
        """Get information about an invitation code.
        
        Args:
            code (str): The invitation code
            
        Returns:
            dict: Code information or None if code doesn't exist
        """
        return self.codes.get(code)
    
    def get_all_codes(self):
        """Get all invitation codes.
        
        Returns:
            dict: Dictionary of all invitation codes
        """
        return self.codes
    
    def get_active_codes(self):
        """Get all active invitation codes.
        
        Returns:
            dict: Dictionary of active invitation codes
        """
        return {code: data for code, data in self.codes.items() if data["active"]}
    
    def get_pending_codes(self):
        """Get all pending (unconfirmed) invitation codes.
        
        Returns:
            dict: Dictionary of pending invitation codes
        """
        return {code: data for code, data in self.codes.items() if not data["confirmed"]}
    
    def cleanup_expired_codes(self):
        """Remove expired invitation codes.
        
        Returns:
            int: Number of codes removed
        """
        now = datetime.datetime.now()
        expired_codes = []
        
        for code, data in self.codes.items():
            expiry = datetime.datetime.fromisoformat(data["expires_at"])
            if now > expiry:
                expired_codes.append(code)
        
        # Remove expired codes
        for code in expired_codes:
            del self.codes[code]
        
        # Save changes
        if expired_codes:
            self._save_codes()
            self.logger.info(f"Removed {len(expired_codes)} expired invitation codes")
        
        return len(expired_codes)


# Command-line interface
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("invitation_system")
    
    # Create invitation code system
    invitation_system = InvitationCodeSystem(logger=logger)
    
    # Parse command-line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Invitation Code System")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate a new invitation code")
    generate_parser.add_argument("--email", help="Email address of the invitee")
    generate_parser.add_argument("--note", help="Note about the invitation")
    
    # Confirm command
    confirm_parser = subparsers.add_parser("confirm", help="Confirm an invitation code")
    confirm_parser.add_argument("code", help="The invitation code to confirm")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate an invitation code")
    validate_parser.add_argument("code", help="The invitation code to validate")
    
    # Use command
    use_parser = subparsers.add_parser("use", help="Record a use of an invitation code")
    use_parser.add_argument("code", help="The invitation code to use")
    
    # Deactivate command
    deactivate_parser = subparsers.add_parser("deactivate", help="Deactivate an invitation code")
    deactivate_parser.add_argument("code", help="The invitation code to deactivate")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Get information about an invitation code")
    info_parser.add_argument("code", help="The invitation code")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List invitation codes")
    list_parser.add_argument("--status", choices=["all", "active", "pending"], default="all", help="Filter by status")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Remove expired invitation codes")
    
    args = parser.parse_args()
    
    # Execute command
    if args.command == "generate":
        code = invitation_system.generate_code(args.email, args.note)
        print(f"Generated invitation code: {code}")
    
    elif args.command == "confirm":
        success = invitation_system.confirm_code(args.code)
        if success:
            print(f"Confirmed invitation code: {args.code}")
        else:
            print(f"Failed to confirm invitation code: {args.code}")
    
    elif args.command == "validate":
        valid = invitation_system.validate_code(args.code)
        if valid:
            print(f"Invitation code is valid: {args.code}")
        else:
            print(f"Invitation code is invalid: {args.code}")
    
    elif args.command == "use":
        success = invitation_system.use_code(args.code)
        if success:
            print(f"Used invitation code: {args.code}")
        else:
            print(f"Failed to use invitation code: {args.code}")
    
    elif args.command == "deactivate":
        success = invitation_system.deactivate_code(args.code)
        if success:
            print(f"Deactivated invitation code: {args.code}")
        else:
            print(f"Failed to deactivate invitation code: {args.code}")
    
    elif args.command == "info":
        info = invitation_system.get_code_info(args.code)
        if info:
            print(json.dumps(info, indent=2))
        else:
            print(f"Invitation code not found: {args.code}")
    
    elif args.command == "list":
        if args.status == "all":
            codes = invitation_system.get_all_codes()
        elif args.status == "active":
            codes = invitation_system.get_active_codes()
        elif args.status == "pending":
            codes = invitation_system.get_pending_codes()
        
        print(f"Found {len(codes)} invitation codes:")
        for code, data in codes.items():
            print(f"- {code}: {data['email']} (Active: {data['active']}, Confirmed: {data['confirmed']}, Uses: {data['uses']}/{data['max_uses']})")
    
    elif args.command == "cleanup":
        count = invitation_system.cleanup_expired_codes()
        print(f"Removed {count} expired invitation codes")
    
    else:
        parser.print_help()
