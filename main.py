"""
Main Application Module for Security Leads Automation

This module serves as the entry point for the security leads automation system,
integrating all components and providing a command-line interface for operation.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.core.config import ConfigManager
from scripts.core.logger import LoggerSetup
from scripts.core.scraper_manager import ScraperManager
from scripts.core.lead_database import LeadDatabase
from scripts.core.automation_scheduler import AutomationScheduler
from scripts.utils.data_validation import LeadValidator, LeadDeduplicator, LeadEnricher, LeadFilter

class SecurityLeadsAutomation:
    """Main application class for security leads automation."""
    
    def __init__(self, config_path=None):
        """Initialize the security leads automation system.
        
        Args:
            config_path (str, optional): Path to configuration file. Defaults to None.
        """
        # Set up base paths
        self.base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.data_dir = self.base_dir / "data"
        self.logs_dir = self.base_dir / "logs"
        
        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Load configuration
        if not config_path:
            config_path = str(self.base_dir / "config.json")
        
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        
        # Set up logging
        log_setup = LoggerSetup(self.config.get("logging", {}))
        self.logger = log_setup.get_logger("security_leads")
        
        self.logger.info("Initializing Security Leads Automation System")
        
        # Initialize components
        self._init_components()
    
    def _init_components(self):
        """Initialize system components."""
        try:
            # Initialize database
            self.logger.info("Initializing database")
            self.database = LeadDatabase(self.config.get("database", {}), self.logger)
            
            # Initialize scraper manager
            self.logger.info("Initializing scraper manager")
            self.scraper_manager = ScraperManager(self.config.get("scrapers", {}), self.logger)
            
            # Initialize data validation components
            self.logger.info("Initializing data validation components")
            self.lead_validator = LeadValidator(self.logger)
            self.lead_deduplicator = LeadDeduplicator(self.database, self.logger)
            self.lead_enricher = LeadEnricher(self.logger)
            self.lead_filter = LeadFilter(self.logger)
            
            # Initialize automation scheduler
            self.logger.info("Initializing automation scheduler")
            self.scheduler = AutomationScheduler(
                self.config.get("scheduler", {}),
                self.scraper_manager,
                self.database,
                self.logger
            )
            
            self.logger.info("All components initialized successfully")
        
        except Exception as e:
            self.logger.error(f"Error initializing components: {str(e)}")
            raise
    
    def start(self):
        """Start the automation system."""
        self.logger.info("Starting Security Leads Automation System")
        
        try:
            # Start the scheduler
            self.scheduler.start()
            
            self.logger.info("Security Leads Automation System started successfully")
            return True
        
        except Exception as e:
            self.logger.error(f"Error starting system: {str(e)}")
            return False
    
    def stop(self):
        """Stop the automation system."""
        self.logger.info("Stopping Security Leads Automation System")
        
        try:
            # Stop the scheduler
            self.scheduler.stop()
            
            # Close database connection
            self.database.close()
            
            self.logger.info("Security Leads Automation System stopped successfully")
            return True
        
        except Exception as e:
            self.logger.error(f"Error stopping system: {str(e)}")
            return False
    
    def run_now(self):
        """Run the automation process immediately."""
        self.logger.info("Running automation process immediately")
        
        try:
            return self.scheduler.run_now()
        
        except Exception as e:
            self.logger.error(f"Error running automation: {str(e)}")
            return f"Error: {str(e)}"
    
    def get_status(self):
        """Get the current status of the system.
        
        Returns:
            dict: System status
        """
        try:
            # Get scheduler status
            scheduler_status = self.scheduler.get_status()
            
            # Get database stats
            db_stats = self.database.get_lead_stats()
            
            # Combine into system status
            status = {
                "scheduler": scheduler_status,
                "database": db_stats,
                "scrapers": self.scraper_manager.get_scraper_status(),
                "system_time": datetime.now().isoformat()
            }
            
            return status
        
        except Exception as e:
            self.logger.error(f"Error getting system status: {str(e)}")
            return {"error": str(e)}
    
    def get_leads(self, filters=None, limit=100, offset=0):
        """Get leads with optional filtering.
        
        Args:
            filters (dict, optional): Filter criteria. Defaults to None.
            limit (int, optional): Maximum number of leads to return. Defaults to 100.
            offset (int, optional): Offset for pagination. Defaults to 0.
            
        Returns:
            list: List of lead data
        """
        try:
            # Get leads from database
            leads = self.database.get_leads(filters, limit, offset)
            
            # Apply additional filtering if needed
            if filters and any(k in filters for k in ['opportunity_type', 'is_armed', 'location']):
                leads = self.lead_filter.filter_leads(leads, filters)
            
            return leads
        
        except Exception as e:
            self.logger.error(f"Error getting leads: {str(e)}")
            return []
    
    def export_leads(self, output_path=None, format="json", filters=None):
        """Export leads to a file.
        
        Args:
            output_path (str, optional): Path to output file. Defaults to None.
            format (str, optional): Export format ('json', 'csv'). Defaults to "json".
            filters (dict, optional): Filter criteria. Defaults to None.
            
        Returns:
            str: Path to exported file
        """
        try:
            # Get leads
            leads = self.get_leads(filters, limit=1000)
            
            if not leads:
                return "No leads to export"
            
            # Generate default output path if not provided
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.data_dir / f"leads_export_{timestamp}.{format}")
            
            # Export based on format
            if format.lower() == "json":
                with open(output_path, 'w') as f:
                    json.dump(leads, f, indent=2)
            
            elif format.lower() == "csv":
                import csv
                
                # Flatten lead data for CSV
                flattened_leads = []
                for lead in leads:
                    flat_lead = {
                        "id": lead.get("id", ""),
                        "source": lead.get("source", ""),
                        "source_url": lead.get("source_url", ""),
                        "lead_type": lead.get("lead_type", ""),
                        "confidence_score": lead.get("confidence_score", 0),
                        "date_extracted": lead.get("date_extracted", ""),
                        "organization_name": lead.get("organization", {}).get("name", ""),
                        "organization_is_government": lead.get("organization", {}).get("is_government", False),
                        "contact_email": lead.get("contacts", [{}])[0].get("email", "") if lead.get("contacts") else "",
                        "contact_phone": lead.get("contacts", [{}])[0].get("phone", "") if lead.get("contacts") else "",
                        "opportunity_title": lead.get("opportunity", {}).get("title", ""),
                        "opportunity_type": lead.get("opportunity", {}).get("opportunity_type", ""),
                        "opportunity_location": lead.get("opportunity", {}).get("location", ""),
                        "opportunity_is_armed": lead.get("opportunity", {}).get("is_armed", False),
                        "opportunity_end_date": lead.get("opportunity", {}).get("end_date", "")
                    }
                    flattened_leads.append(flat_lead)
                
                # Write CSV
                if flattened_leads:
                    with open(output_path, 'w', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=flattened_leads[0].keys())
                        writer.writeheader()
                        writer.writerows(flattened_leads)
            
            else:
                return f"Unsupported export format: {format}"
            
            self.logger.info(f"Exported {len(leads)} leads to {output_path}")
            return output_path
        
        except Exception as e:
            self.logger.error(f"Error exporting leads: {str(e)}")
            return f"Error: {str(e)}"


def main():
    """Main entry point for command-line interface."""
    parser = argparse.ArgumentParser(description="Security Leads Automation System")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--action", choices=["start", "stop", "run", "status", "export"], 
                        default="start", help="Action to perform")
    parser.add_argument("--format", choices=["json", "csv"], default="json",
                        help="Export format (for export action)")
    parser.add_argument("--output", help="Output file path (for export action)")
    
    args = parser.parse_args()
    
    try:
        # Initialize the system
        system = SecurityLeadsAutomation(args.config)
        
        # Perform requested action
        if args.action == "start":
            success = system.start()
            print(f"System {'started successfully' if success else 'failed to start'}")
        
        elif args.action == "stop":
            success = system.stop()
            print(f"System {'stopped successfully' if success else 'failed to stop'}")
        
        elif args.action == "run":
            result = system.run_now()
            print(f"Run result: {result}")
        
        elif args.action == "status":
            status = system.get_status()
            print(json.dumps(status, indent=2))
        
        elif args.action == "export":
            result = system.export_leads(args.output, args.format)
            print(f"Export result: {result}")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
