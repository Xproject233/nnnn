"""
One-Click Deployment System for Security Leads Automation

This module provides functionality for authorized users to deploy the system
with a single click using validated invitation codes.
"""

import os
import sys
import json
import logging
import subprocess
import datetime
from pathlib import Path
from flask import Flask, request, render_template, redirect, url_for, flash, jsonify

# Import invitation and email systems
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.invitation_system import InvitationCodeSystem
from scripts.email_confirmation import EmailConfirmationSystem

class OneClickDeployment:
    """Manages one-click deployment for authorized users."""
    
    def __init__(self, config_path=None, logger=None):
        """Initialize the one-click deployment system.
        
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
        
        # Get deployment configuration
        self.deployment_config = self.config.get("deployment", {})
        
        # Set default values if not in config
        self.deployment_script = self.deployment_config.get("script", str(self.base_dir / "deploy-production.sh"))
        self.deployment_log = self.deployment_config.get("log", str(self.data_dir / "deployment.log"))
        
        # Initialize invitation code system
        self.invitation_system = InvitationCodeSystem(config_path, logger)
        
        # Initialize email confirmation system
        self.email_system = EmailConfirmationSystem(config_path, logger)
        
        # Track deployments
        self.deployments_file = self.data_dir / "deployments.json"
        self.deployments = self._load_deployments()
    
    def _load_deployments(self):
        """Load deployment history from file.
        
        Returns:
            dict: Dictionary of deployments
        """
        if os.path.exists(self.deployments_file):
            try:
                with open(self.deployments_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading deployments: {str(e)}")
                return {}
        else:
            return {}
    
    def _save_deployments(self):
        """Save deployment history to file."""
        try:
            with open(self.deployments_file, 'w') as f:
                json.dump(self.deployments, f, indent=2)
            self.logger.info(f"Saved {len(self.deployments)} deployments")
        except Exception as e:
            self.logger.error(f"Error saving deployments: {str(e)}")
    
    def deploy(self, code, ip_address=None, user_agent=None):
        """Deploy the system using an invitation code.
        
        Args:
            code (str): The invitation code to use
            ip_address (str, optional): IP address of the user. Defaults to None.
            user_agent (str, optional): User agent of the user. Defaults to None.
            
        Returns:
            dict: Deployment result with status and message
        """
        # Validate invitation code
        if not self.invitation_system.validate_code(code):
            self.logger.warning(f"Invalid invitation code used for deployment: {code}")
            return {"status": "error", "message": "Invalid invitation code"}
        
        # Record code usage
        self.invitation_system.use_code(code)
        
        # Get code information
        code_info = self.invitation_system.get_code_info(code)
        
        # Run deployment script
        try:
            # Create deployment ID
            deployment_id = f"deploy_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Log deployment
            self.logger.info(f"Starting deployment {deployment_id} with code {code}")
            
            # Run deployment script
            process = subprocess.Popen(
                [self.deployment_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.base_dir)
            )
            
            # Wait for process to complete
            stdout, stderr = process.communicate()
            
            # Check if deployment was successful
            if process.returncode == 0:
                status = "success"
                message = "Deployment completed successfully"
            else:
                status = "error"
                message = f"Deployment failed with exit code {process.returncode}"
            
            # Save deployment log
            with open(self.deployment_log, 'a') as f:
                f.write(f"\n\n=== Deployment {deployment_id} ===\n")
                f.write(f"Date: {datetime.datetime.now().isoformat()}\n")
                f.write(f"Code: {code}\n")
                f.write(f"Email: {code_info.get('email', 'Not specified')}\n")
                f.write(f"IP: {ip_address or 'Not specified'}\n")
                f.write(f"User Agent: {user_agent or 'Not specified'}\n")
                f.write(f"Status: {status}\n")
                f.write(f"Message: {message}\n")
                f.write("\n--- STDOUT ---\n")
                f.write(stdout)
                f.write("\n--- STDERR ---\n")
                f.write(stderr)
            
            # Record deployment
            deployment_data = {
                "id": deployment_id,
                "code": code,
                "email": code_info.get("email"),
                "date": datetime.datetime.now().isoformat(),
                "ip_address": ip_address,
                "user_agent": user_agent,
                "status": status,
                "message": message
            }
            
            self.deployments[deployment_id] = deployment_data
            self._save_deployments()
            
            self.logger.info(f"Deployment {deployment_id} completed with status {status}")
            
            return {
                "status": status,
                "message": message,
                "deployment_id": deployment_id
            }
        
        except Exception as e:
            error_message = f"Error during deployment: {str(e)}"
            self.logger.error(error_message)
            
            return {
                "status": "error",
                "message": error_message
            }
    
    def get_deployment(self, deployment_id):
        """Get information about a deployment.
        
        Args:
            deployment_id (str): The deployment ID
            
        Returns:
            dict: Deployment information or None if not found
        """
        return self.deployments.get(deployment_id)
    
    def get_deployments_by_code(self, code):
        """Get deployments associated with an invitation code.
        
        Args:
            code (str): The invitation code
            
        Returns:
            list: List of deployments
        """
        return [d for d in self.deployments.values() if d.get("code") == code]
    
    def get_all_deployments(self):
        """Get all deployments.
        
        Returns:
            dict: Dictionary of all deployments
        """
        return self.deployments


# Flask application for one-click deployment
def create_deployment_app(config_path=None):
    """Create a Flask application for one-click deployment.
    
    Args:
        config_path (str, optional): Path to configuration file. Defaults to None.
        
    Returns:
        Flask: Flask application
    """
    app = Flask(__name__)
    app.secret_key = os.urandom(24)
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("one_click_deployment")
    
    # Create one-click deployment system
    deployment_system = OneClickDeployment(config_path, logger)
    
    @app.route('/')
    def index():
        """Landing page."""
        return render_template('index.html')
    
    @app.route('/deploy', methods=['GET', 'POST'])
    def deploy():
        """Deployment page."""
        if request.method == 'POST':
            # Get invitation code
            code = request.form.get('code')
            
            if not code:
                flash('Please enter an invitation code', 'error')
                return redirect(url_for('deploy'))
            
            # Deploy the system
            result = deployment_system.deploy(
                code,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            
            if result['status'] == 'success':
                flash('Deployment completed successfully!', 'success')
                return redirect(url_for('deployment_status', deployment_id=result['deployment_id']))
            else:
                flash(f"Deployment failed: {result['message']}", 'error')
                return redirect(url_for('deploy'))
        
        # GET request - show deployment form
        code = request.args.get('code')
        return render_template('deploy.html', code=code)
    
    @app.route('/status/<deployment_id>')
    def deployment_status(deployment_id):
        """Deployment status page."""
        deployment = deployment_system.get_deployment(deployment_id)
        
        if not deployment:
            flash('Deployment not found', 'error')
            return redirect(url_for('index'))
        
        return render_template('status.html', deployment=deployment)
    
    @app.route('/confirm')
    def confirm_code():
        """Confirm an invitation code."""
        code = request.args.get('code')
        
        if not code:
            flash('No invitation code provided', 'error')
            return redirect(url_for('index'))
        
        # Confirm the code
        success = deployment_system.email_system.confirm_and_notify(code)
        
        if success:
            flash('Invitation code confirmed successfully!', 'success')
        else:
            flash('Failed to confirm invitation code', 'error')
        
        return redirect(url_for('index'))
    
    @app.route('/request', methods=['GET', 'POST'])
    def request_invitation():
        """Request an invitation code."""
        if request.method == 'POST':
            email = request.form.get('email')
            note = request.form.get('note')
            
            if not email:
                flash('Please enter your email address', 'error')
                return redirect(url_for('request_invitation'))
            
            # Generate code and request confirmation
            code = deployment_system.email_system.generate_and_request_confirmation(email, note)
            
            if code:
                flash('Invitation request submitted successfully! You will receive an email when your invitation is confirmed.', 'success')
                return redirect(url_for('index'))
            else:
                flash('Failed to submit invitation request', 'error')
                return redirect(url_for('request_invitation'))
        
        # GET request - show request form
        return render_template('request.html')
    
    @app.route('/api/deploy', methods=['POST'])
    def api_deploy():
        """API endpoint for deployment."""
        data = request.json
        
        if not data or 'code' not in data:
            return jsonify({"status": "error", "message": "Invitation code required"}), 400
        
        # Deploy the system
        result = deployment_system.deploy(
            data['code'],
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        
        return jsonify(result)
    
    @app.route('/api/status/<deployment_id>')
    def api_deployment_status(deployment_id):
        """API endpoint for deployment status."""
        deployment = deployment_system.get_deployment(deployment_id)
        
        if not deployment:
            return jsonify({"status": "error", "message": "Deployment not found"}), 404
        
        return jsonify(deployment)
    
    return app


# Command-line interface
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("one_click_deployment")
    
    # Parse command-line arguments
    import argparse
    parser = argparse.ArgumentParser(description="One-Click Deployment System")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy the system using an invitation code")
    deploy_parser.add_argument("code", help="The invitation code to use")
    
    # Run web app command
    webapp_parser = subparsers.add_parser("webapp", help="Run the web application for one-click deployment")
    webapp_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    webapp_parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    webapp_parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Execute command
    if args.command == "deploy":
        # Create one-click deployment system
        deployment_system = OneClickDeployment(logger=logger)
        
        # Deploy the system
        result = deployment_system.deploy(args.code)
        
        if result['status'] == 'success':
            print(f"Deployment completed successfully: {result['deployment_id']}")
        else:
            print(f"Deployment failed: {result['message']}")
    
    elif args.command == "webapp":
        # Create and run Flask application
        app = create_deployment_app()
        app.run(host=args.host, port=args.port, debug=args.debug)
    
    else:
        parser.print_help()
