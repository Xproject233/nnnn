"""
Automation Scheduler Module for Security Leads Automation

This module provides functionality for scheduling and automating the lead generation process,
allowing the system to run at specified intervals and manage the scraping workflow.
"""

import os
import time
import json
import logging
import threading
import schedule
from datetime import datetime, timedelta
from pathlib import Path

class AutomationScheduler:
    """Manages scheduling and automation of the lead generation process."""
    
    def __init__(self, config, scraper_manager, database, logger=None):
        """Initialize the automation scheduler.
        
        Args:
            config (dict): Scheduler configuration
            scraper_manager: ScraperManager instance
            database: LeadDatabase instance
            logger: Logger instance for logging scheduler operations
        """
        self.config = config
        self.scraper_manager = scraper_manager
        self.database = database
        self.logger = logger or logging.getLogger(__name__)
        
        # Default schedule settings
        self.default_schedule = {
            'daily': ['08:00'],
            'weekly': {
                'days': ['monday', 'wednesday', 'friday'],
                'time': '08:00'
            },
            'monthly': {
                'days': [1, 15],
                'time': '08:00'
            }
        }
        
        # Load schedule from config or use defaults
        self.schedule_settings = config.get('schedule', self.default_schedule)
        
        # Status tracking
        self.is_running = False
        self.last_run = None
        self.next_run = None
        self.run_history = []
        
        # Maximum history entries to keep
        self.max_history = config.get('max_history', 100)
        
        # Load run history if exists
        self._load_history()
    
    def _load_history(self):
        """Load run history from file."""
        history_path = self._get_history_path()
        
        if os.path.exists(history_path):
            try:
                with open(history_path, 'r') as f:
                    self.run_history = json.load(f)
                self.logger.info(f"Loaded {len(self.run_history)} run history entries")
            except Exception as e:
                self.logger.error(f"Error loading run history: {str(e)}")
                self.run_history = []
    
    def _save_history(self):
        """Save run history to file."""
        history_path = self._get_history_path()
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(history_path), exist_ok=True)
            
            # Trim history to max size
            if len(self.run_history) > self.max_history:
                self.run_history = self.run_history[-self.max_history:]
            
            with open(history_path, 'w') as f:
                json.dump(self.run_history, f, indent=2)
            
            self.logger.info(f"Saved {len(self.run_history)} run history entries")
        except Exception as e:
            self.logger.error(f"Error saving run history: {str(e)}")
    
    def _get_history_path(self):
        """Get path to run history file.
        
        Returns:
            str: Path to history file
        """
        base_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        return str(base_dir / "data" / "run_history.json")
    
    def setup_schedule(self):
        """Set up the automation schedule based on configuration."""
        # Clear existing schedule
        schedule.clear()
        
        # Set up daily schedule
        daily_times = self.schedule_settings.get('daily', [])
        for time_str in daily_times:
            schedule.every().day.at(time_str).do(self.run_automation)
            self.logger.info(f"Scheduled daily run at {time_str}")
        
        # Set up weekly schedule
        weekly = self.schedule_settings.get('weekly', {})
        if weekly:
            days = weekly.get('days', [])
            time_str = weekly.get('time', '08:00')
            
            for day in days:
                day = day.lower()
                if day == 'monday':
                    schedule.every().monday.at(time_str).do(self.run_automation)
                elif day == 'tuesday':
                    schedule.every().tuesday.at(time_str).do(self.run_automation)
                elif day == 'wednesday':
                    schedule.every().wednesday.at(time_str).do(self.run_automation)
                elif day == 'thursday':
                    schedule.every().thursday.at(time_str).do(self.run_automation)
                elif day == 'friday':
                    schedule.every().friday.at(time_str).do(self.run_automation)
                elif day == 'saturday':
                    schedule.every().saturday.at(time_str).do(self.run_automation)
                elif day == 'sunday':
                    schedule.every().sunday.at(time_str).do(self.run_automation)
                
                self.logger.info(f"Scheduled weekly run on {day} at {time_str}")
        
        # Set up monthly schedule
        monthly = self.schedule_settings.get('monthly', {})
        if monthly:
            days = monthly.get('days', [])
            time_str = monthly.get('time', '08:00')
            
            for day in days:
                # Use a lambda to check if it's the right day of the month
                schedule.every().day.at(time_str).do(
                    lambda d=day: self.run_automation() if datetime.now().day == d else None
                )
                self.logger.info(f"Scheduled monthly run on day {day} at {time_str}")
        
        # Calculate next run time
        self._update_next_run()
    
    def _update_next_run(self):
        """Update the next scheduled run time."""
        next_job = schedule.next_run()
        if next_job:
            self.next_run = next_job.strftime('%Y-%m-%d %H:%M:%S')
            self.logger.info(f"Next scheduled run: {self.next_run}")
    
    def run_automation(self):
        """Run the automated lead generation process."""
        if self.is_running:
            self.logger.warning("Automation already running, skipping this run")
            return
        
        self.is_running = True
        start_time = datetime.now()
        
        self.logger.info("Starting automated lead generation process")
        
        run_data = {
            'start_time': start_time.isoformat(),
            'end_time': None,
            'status': 'running',
            'sources_processed': [],
            'leads_generated': 0,
            'errors': []
        }
        
        try:
            # Get sources to scrape
            sources = self.config.get('sources', [])
            if not sources:
                sources = self.scraper_manager.get_available_sources()
            
            total_leads = 0
            
            # Process each source
            for source in sources:
                try:
                    self.logger.info(f"Processing source: {source}")
                    
                    # Run the scraper
                    leads = self.scraper_manager.run_scraper(source)
                    
                    if leads:
                        # Store leads in database
                        for lead in leads:
                            try:
                                self.database.store_lead(lead)
                                total_leads += 1
                            except Exception as e:
                                error_msg = f"Error storing lead from {source}: {str(e)}"
                                self.logger.error(error_msg)
                                run_data['errors'].append(error_msg)
                        
                        self.logger.info(f"Generated {len(leads)} leads from {source}")
                        run_data['sources_processed'].append({
                            'name': source,
                            'leads_count': len(leads),
                            'status': 'success'
                        })
                    else:
                        self.logger.warning(f"No leads generated from {source}")
                        run_data['sources_processed'].append({
                            'name': source,
                            'leads_count': 0,
                            'status': 'no_leads'
                        })
                
                except Exception as e:
                    error_msg = f"Error processing source {source}: {str(e)}"
                    self.logger.error(error_msg)
                    run_data['errors'].append(error_msg)
                    run_data['sources_processed'].append({
                        'name': source,
                        'leads_count': 0,
                        'status': 'error',
                        'error': str(e)
                    })
            
            # Update run data
            run_data['leads_generated'] = total_leads
            run_data['status'] = 'completed'
            
            self.logger.info(f"Completed automated lead generation process. Generated {total_leads} leads.")
        
        except Exception as e:
            error_msg = f"Error in automation process: {str(e)}"
            self.logger.error(error_msg)
            run_data['errors'].append(error_msg)
            run_data['status'] = 'failed'
        
        finally:
            # Update run data
            end_time = datetime.now()
            run_data['end_time'] = end_time.isoformat()
            run_data['duration_seconds'] = (end_time - start_time).total_seconds()
            
            # Update last run time
            self.last_run = start_time.isoformat()
            
            # Add to history
            self.run_history.append(run_data)
            self._save_history()
            
            # Update next run time
            self._update_next_run()
            
            # Reset running flag
            self.is_running = False
    
    def start(self):
        """Start the scheduler in a background thread."""
        self.logger.info("Starting automation scheduler")
        
        # Set up schedule
        self.setup_schedule()
        
        # Start scheduler in a background thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        self.logger.info("Automation scheduler started")
    
    def _run_scheduler(self):
        """Run the scheduler loop."""
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    def stop(self):
        """Stop the scheduler."""
        self.logger.info("Stopping automation scheduler")
        schedule.clear()
        self.logger.info("Automation scheduler stopped")
    
    def run_now(self):
        """Run the automation process immediately."""
        self.logger.info("Running automation process immediately")
        
        # Run in a separate thread to avoid blocking
        thread = threading.Thread(target=self.run_automation)
        thread.daemon = True
        thread.start()
        
        return "Automation process started"
    
    def get_status(self):
        """Get the current status of the scheduler.
        
        Returns:
            dict: Scheduler status
        """
        return {
            'is_running': self.is_running,
            'last_run': self.last_run,
            'next_run': self.next_run,
            'schedule': self.schedule_settings,
            'recent_history': self.run_history[-5:] if self.run_history else []
        }
    
    def update_schedule(self, new_schedule):
        """Update the scheduler configuration.
        
        Args:
            new_schedule (dict): New schedule configuration
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.schedule_settings = new_schedule
            self.setup_schedule()
            
            # Update config
            self.config['schedule'] = new_schedule
            
            self.logger.info("Updated scheduler configuration")
            return True
        except Exception as e:
            self.logger.error(f"Error updating scheduler configuration: {str(e)}")
            return False
