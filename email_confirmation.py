"""
Email Confirmation System for Security Leads Automation

This module provides functionality for sending and verifying email confirmations
for invitation codes.
"""

import os
import sys
import json
import uuid
import smtplib
import logging
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# Import invitation system
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.invitation_system import InvitationCodeSystem

class EmailConfirmationSystem:
    """Manages email confirmations for invitation codes."""
    
    def __init__(self, config_path=None, logger=None):
        """Initialize the email confirmation system.
        
        Args:
            config_path (str, optional): Path to configuration file. Defaults to None.
            logger (Logger, optional): Logger instance. Defaults to None.
        """
        # Set up base paths
        self.base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.data_dir = self.base_dir / "data"
        self.template_dir = self.base_dir / "templates" / "emails"
        
        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.template_dir, exist_ok=True)
        
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
        
        # Get email system configuration
        self.email_config = self.config.get("email_system", {})
        
        # Set default values if not in config
        self.smtp_server = self.email_config.get("smtp_server", "smtp.gmail.com")
        self.smtp_port = self.email_config.get("smtp_port", 587)
        self.smtp_username = self.email_config.get("smtp_username", "")
        self.smtp_password = self.email_config.get("smtp_password", "")
        self.from_email = self.email_config.get("from_email", "noreply@securityleads.com")
        self.admin_email = self.email_config.get("admin_email", "admin@example.com")
        
        # Initialize invitation code system
        self.invitation_system = InvitationCodeSystem(config_path, logger)
        
        # Load email templates
        self._create_default_templates()
    
    def _create_default_templates(self):
        """Create default email templates if they don't exist."""
        # Admin confirmation request template
        admin_template_path = self.template_dir / "admin_confirmation.html"
        if not os.path.exists(admin_template_path):
            admin_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background-color: #0d6efd; color: white; padding: 10px; text-align: center; }
                    .content { padding: 20px; background-color: #f8f9fa; }
                    .footer { text-align: center; margin-top: 20px; font-size: 12px; color: #6c757d; }
                    .button { display: inline-block; background-color: #0d6efd; color: white; padding: 10px 20px; 
                              text-decoration: none; border-radius: 5px; margin-top: 20px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>Security Leads Automation</h2>
                    </div>
                    <div class="content">
                        <h3>New Invitation Code Confirmation</h3>
                        <p>Hello,</p>
                        <p>A new invitation code has been generated and requires your confirmation:</p>
                        <ul>
                            <li><strong>Code:</strong> {{code}}</li>
                            <li><strong>Email:</strong> {{email}}</li>
                            <li><strong>Note:</strong> {{note}}</li>
                            <li><strong>Created:</strong> {{created_at}}</li>
                            <li><strong>Expires:</strong> {{expires_at}}</li>
                        </ul>
                        <p>To confirm this invitation code, please click the button below:</p>
                        <p style="text-align: center;">
                            <a href="{{confirmation_url}}" class="button">Confirm Invitation Code</a>
                        </p>
                        <p>Or copy and paste this URL into your browser:</p>
                        <p>{{confirmation_url}}</p>
                        <p>If you did not request this invitation code, please ignore this email.</p>
                    </div>
                    <div class="footer">
                        <p>Security Leads Automation System</p>
                    </div>
                </div>
            </body>
            </html>
            """
            with open(admin_template_path, 'w') as f:
                f.write(admin_template)
        
        # User invitation template
        user_template_path = self.template_dir / "user_invitation.html"
        if not os.path.exists(user_template_path):
            user_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background-color: #0d6efd; color: white; padding: 10px; text-align: center; }
                    .content { padding: 20px; background-color: #f8f9fa; }
                    .footer { text-align: center; margin-top: 20px; font-size: 12px; color: #6c757d; }
                    .button { display: inline-block; background-color: #0d6efd; color: white; padding: 10px 20px; 
                              text-decoration: none; border-radius: 5px; margin-top: 20px; }
                    .code { background-color: #e9ecef; padding: 10px; font-family: monospace; margin: 10px 0; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>Security Leads Automation</h2>
                    </div>
                    <div class="content">
                        <h3>Your Invitation Code</h3>
                        <p>Hello,</p>
                        <p>You have been invited to use the Security Leads Automation system. Here is your invitation code:</p>
                        <div class="code">{{code}}</div>
                        <p>To access the system, please click the button below:</p>
                        <p style="text-align: center;">
                            <a href="{{deployment_url}}" class="button">Access Security Leads Automation</a>
                        </p>
                        <p>Or copy and paste this URL into your browser:</p>
                        <p>{{deployment_url}}</p>
                        <p>When prompted, enter your invitation code to gain access.</p>
                        <p>This invitation code will expire on {{expires_at}}.</p>
                    </div>
                    <div class="footer">
                        <p>Security Leads Automation System</p>
                    </div>
                </div>
            </body>
            </html>
            """
            with open(user_template_path, 'w') as f:
                f.write(user_template)
    
    def _send_email(self, to_email, subject, html_content):
        """Send an email.
        
        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            html_content (str): HTML content of the email
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        # Create message
        msg = MIMEMultipart()
        msg['From'] = self.from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Attach HTML content
        msg.attach(MIMEText(html_content, 'html'))
        
        try:
            # Connect to SMTP server
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            
            # Login if credentials provided
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Sent email to {to_email}: {subject}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error sending email to {to_email}: {str(e)}")
            return False
    
    def _load_template(self, template_name):
        """Load an email template.
        
        Args:
            template_name (str): Name of the template file
            
        Returns:
            str: Template content or None if template not found
        """
        template_path = self.template_dir / f"{template_name}.html"
        
        if not os.path.exists(template_path):
            self.logger.error(f"Email template not found: {template_name}")
            return None
        
        try:
            with open(template_path, 'r') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Error loading email template {template_name}: {str(e)}")
            return None
    
    def _render_template(self, template, context):
        """Render an email template with context variables.
        
        Args:
            template (str): Template content
            context (dict): Context variables
            
        Returns:
            str: Rendered template
        """
        # Simple template rendering
        rendered = template
        for key, value in context.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
        
        return rendered
    
    def request_admin_confirmation(self, code):
        """Send an email to the admin to confirm an invitation code.
        
        Args:
            code (str): The invitation code to confirm
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        # Get code information
        code_info = self.invitation_system.get_code_info(code)
        if not code_info:
            self.logger.error(f"Invitation code not found: {code}")
            return False
        
        # Load template
        template = self._load_template("admin_confirmation")
        if not template:
            return False
        
        # Create confirmation URL
        base_url = self.email_config.get("base_url", "https://whqaxvfd.manus.space")
        confirmation_url = f"{base_url}/confirm?code={code}"
        
        # Prepare context
        context = {
            "code": code,
            "email": code_info.get("email", "Not specified"),
            "note": code_info.get("note", "Not specified"),
            "created_at": code_info.get("created_at", "Unknown"),
            "expires_at": code_info.get("expires_at", "Unknown"),
            "confirmation_url": confirmation_url
        }
        
        # Render template
        html_content = self._render_template(template, context)
        
        # Send email
        subject = "Security Leads Automation - Invitation Code Confirmation"
        return self._send_email(self.admin_email, subject, html_content)
    
    def send_invitation_email(self, code):
        """Send an invitation email to the user.
        
        Args:
            code (str): The invitation code
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        # Get code information
        code_info = self.invitation_system.get_code_info(code)
        if not code_info:
            self.logger.error(f"Invitation code not found: {code}")
            return False
        
        # Check if code has an associated email
        email = code_info.get("email")
        if not email:
            self.logger.error(f"No email associated with invitation code: {code}")
            return False
        
        # Check if code is confirmed and active
        if not code_info.get("confirmed", False) or not code_info.get("active", False):
            self.logger.error(f"Invitation code not confirmed or active: {code}")
            return False
        
        # Load template
        template = self._load_template("user_invitation")
        if not template:
            return False
        
        # Create deployment URL
        base_url = self.email_config.get("base_url", "https://whqaxvfd.manus.space")
        deployment_url = f"{base_url}/deploy?code={code}"
        
        # Prepare context
        context = {
            "code": code,
            "expires_at": code_info.get("expires_at", "Unknown"),
            "deployment_url": deployment_url
        }
        
        # Render template
        html_content = self._render_template(template, context)
        
        # Send email
        subject = "Your Security Leads Automation Invitation"
        return self._send_email(email, subject, html_content)
    
    def generate_and_request_confirmation(self, email=None, note=None):
        """Generate a new invitation code and request admin confirmation.
        
        Args:
            email (str, optional): Email address of the invitee. Defaults to None.
            note (str, optional): Note about the invitation. Defaults to None.
            
        Returns:
            str: The generated invitation code or None if failed
        """
        # Generate code
        code = self.invitation_system.generate_code(email, note)
        if not code:
            return None
        
        # Request admin confirmation
        success = self.request_admin_confirmation(code)
        if not success:
            self.logger.error(f"Failed to send admin confirmation email for code: {code}")
            # Don't delete the code, it can still be confirmed manually
        
        return code
    
    def confirm_and_notify(self, code):
        """Confirm an invitation code and notify the user.
        
        Args:
            code (str): The invitation code to confirm
            
        Returns:
            bool: True if confirmation and notification successful, False otherwise
        """
        # Confirm code
        success = self.invitation_system.confirm_code(code)
        if not success:
            return False
        
        # Send invitation email to user
        success = self.send_invitation_email(code)
        if not success:
            self.logger.error(f"Failed to send invitation email for code: {code}")
            # Don't revert confirmation, the email can be sent manually
        
        return True


# Command-line interface
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("email_confirmation_system")
    
    # Create email confirmation system
    email_system = EmailConfirmationSystem(logger=logger)
    
    # Parse command-line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Email Confirmation System")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
(Content truncated due to size limit. Use line ranges to read in chunks)