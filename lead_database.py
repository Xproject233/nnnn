"""
Database module with state filtering capabilities for Security Leads Automation
"""

import os
import sys
import json
import sqlite3
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# Import state extraction utilities
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.utils.state_extraction import StateExtractor, enhance_lead_with_state_info

class LeadDatabase:
    """Database for storing and retrieving security service leads with state filtering."""
    
    def __init__(self, db_path=None, logger=None):
        """Initialize the lead database.
        
        Args:
            db_path: Path to SQLite database file
            logger: Optional logger instance
        """
        # Set up base paths
        self.base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.data_dir = self.base_dir / "data"
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Set up logger
        self.logger = logger or logging.getLogger(__name__)
        
        # Set database path
        if db_path is None:
            db_path = str(self.data_dir / "leads.db")
        self.db_path = db_path
        
        # Initialize state extractor
        self.state_extractor = StateExtractor(logger)
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """Initialize the database schema."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create leads table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id TEXT PRIMARY KEY,
                title TEXT,
                company TEXT,
                location TEXT,
                description TEXT,
                contact_name TEXT,
                contact_email TEXT,
                contact_phone TEXT,
                source TEXT,
                url TEXT,
                date_posted TEXT,
                date_scraped TEXT,
                confidence_score REAL,
                status TEXT,
                notes TEXT,
                data JSON
            )
            ''')
            
            # Create states table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id TEXT,
                state_code TEXT,
                state_name TEXT,
                FOREIGN KEY (lead_id) REFERENCES leads(id),
                UNIQUE(lead_id, state_code)
            )
            ''')
            
            # Create index on state_code for faster filtering
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_states_state_code ON states(state_code)')
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Initialized database at {self.db_path}")
        
        except Exception as e:
            self.logger.error(f"Error initializing database: {str(e)}")
            raise
    
    def add_lead(self, lead_data: Dict[str, Any]) -> str:
        """Add a lead to the database with state information.
        
        Args:
            lead_data: Lead data dictionary
            
        Returns:
            Lead ID
        """
        try:
            # Generate ID if not provided
            if 'id' not in lead_data:
                import uuid
                lead_data['id'] = str(uuid.uuid4())
            
            # Enhance lead with state information
            enhanced_lead = enhance_lead_with_state_info(lead_data)
            
            # Extract states for separate storage
            states = enhanced_lead.get('states', [])
            
            # Convert data to JSON
            data_json = json.dumps(enhanced_lead)
            
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert lead
            cursor.execute('''
            INSERT OR REPLACE INTO leads (
                id, title, company, location, description, contact_name, 
                contact_email, contact_phone, source, url, date_posted, 
                date_scraped, confidence_score, status, notes, data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                enhanced_lead.get('id'),
                enhanced_lead.get('title'),
                enhanced_lead.get('company'),
                enhanced_lead.get('location'),
                enhanced_lead.get('description'),
                enhanced_lead.get('contact_name'),
                enhanced_lead.get('contact_email'),
                enhanced_lead.get('contact_phone'),
                enhanced_lead.get('source'),
                enhanced_lead.get('url'),
                enhanced_lead.get('date_posted'),
                enhanced_lead.get('date_scraped'),
                enhanced_lead.get('confidence_score'),
                enhanced_lead.get('status', 'new'),
                enhanced_lead.get('notes'),
                data_json
            ))
            
            # Insert states
            for state in states:
                cursor.execute('''
                INSERT OR REPLACE INTO states (lead_id, state_code, state_name)
                VALUES (?, ?, ?)
                ''', (
                    enhanced_lead.get('id'),
                    state.get('state_code'),
                    state.get('state_name')
                ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Added lead {enhanced_lead.get('id')} with {len(states)} states")
            
            return enhanced_lead.get('id')
        
        except Exception as e:
            self.logger.error(f"Error adding lead: {str(e)}")
            raise
    
    def get_lead(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Get a lead from the database.
        
        Args:
            lead_id: Lead ID
            
        Returns:
            Lead data dictionary or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get lead
            cursor.execute('SELECT data FROM leads WHERE id = ?', (lead_id,))
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return None
            
            # Parse JSON data
            lead_data = json.loads(result[0])
            
            # Get states
            cursor.execute('SELECT state_code, state_name FROM states WHERE lead_id = ?', (lead_id,))
            states = [{'state_code': row[0], 'state_name': row[1]} for row in cursor.fetchall()]
            
            # Add states to lead data
            lead_data['states'] = states
            
            conn.close()
            
            return lead_data
        
        except Exception as e:
            self.logger.error(f"Error getting lead {lead_id}: {str(e)}")
            return None
    
    def get_leads(self, 
                 filters: Optional[Dict[str, Any]] = None, 
                 limit: int = 100, 
                 offset: int = 0,
                 sort_by: str = 'date_scraped',
                 sort_order: str = 'DESC') -> Tuple[List[Dict[str, Any]], int]:
        """Get leads from the database with filtering options.
        
        Args:
            filters: Dictionary of filters
            limit: Maximum number of leads to return
            offset: Offset for pagination
            sort_by: Field to sort by
            sort_order: Sort order (ASC or DESC)
            
        Returns:
            Tuple of (list of lead data dictionaries, total count)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build query
            query = 'SELECT l.data FROM leads l'
            count_query = 'SELECT COUNT(*) FROM leads l'
            
            # Add state filtering if needed
            state_filter = None
            if filters and 'state' in filters and filters['state']:
                # Normalize state input
                state_info = self.state_extractor.normalize_state(filters['state'])
                if state_info:
                    query = query + ' INNER JOIN states s ON l.id = s.lead_id'
                    count_query = count_query + ' INNER JOIN states s ON l.id = s.lead_id'
                    state_filter = state_info['state_code']
            
            # Build WHERE clause
            where_clauses = []
            query_params = []
            
            if filters:
                # Add state filter
                if state_filter:
                    where_clauses.append('s.state_code = ?')
                    query_params.append(state_filter)
                
                # Add other filters
                for field in ['title', 'company', 'location', 'source', 'status']:
                    if field in filters and filters[field]:
                        where_clauses.append(f'l.{field} LIKE ?')
                        query_params.append(f'%{filters[field]}%')
                
                # Add confidence score filter
                if 'min_confidence' in filters and filters['min_confidence'] is not None:
                    where_clauses.append('l.confidence_score >= ?')
                    query_params.append(filters['min_confidence'])
                
                # Add date filters
                if 'date_from' in filters and filters['date_from']:
                    where_clauses.append('l.date_scraped >= ?')
                    query_params.append(filters['date_from'])
                
                if 'date_to' in filters and filters['date_to']:
                    where_clauses.append('l.date_scraped <= ?')
                    query_params.append(filters['date_to'])
            
            # Add WHERE clause to queries
            if where_clauses:
                query = query + ' WHERE ' + ' AND '.join(where_clauses)
                count_query = count_query + ' WHERE ' + ' AND '.join(where_clauses)
            
            # Add GROUP BY for state joins to avoid duplicates
            if state_filter:
                query = query + ' GROUP BY l.id'
                count_query = count_query + ' GROUP BY l.id'
            
            # Add sorting
            if sort_by and sort_by in ['id', 'title', 'company', 'location', 'date_posted', 
                                      'date_scraped', 'confidence_score', 'status']:
                query = query + f' ORDER BY l.{sort_by} {sort_order}'
            
            # Add limit and offset
            query = query + ' LIMIT ? OFFSET ?'
            query_params.extend([limit, offset])
            
            # Execute count query
            cursor.execute(count_query, query_params[:-2] if query_params else [])
            total_count = len(cursor.fetchall())  # Count results after GROUP BY
            
            # Execute main query
            cursor.execute(query, query_params)
            results = cursor.fetchall()
            
            # Parse results
            leads = []
            for row in results:
                lead_data = json.loads(row[0])
                
                # Get states for each lead
                cursor.execute('SELECT state_code, state_name FROM states WHERE lead_id = ?', (lead_data.get('id'),))
                states = [{'state_code': row[0], 'state_name': row[1]} for row in cursor.fetchall()]
                
                # Add states to lead data
                lead_data['states'] = states
                
                leads.append(lead_data)
            
            conn.close()
            
            return leads, total_count
        
        except Exception as e:
            self.logger.error(f"Error getting leads: {str(e)}")
            return [], 0
    
    def get_states_summary(self) -> List[Dict[str, Any]]:
        """Get summary of leads by state.
        
        Returns:
            List of dictionaries with state information and lead counts
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get state counts
            cursor.execute('''
            SELECT s.state_code, s.state_name, COUNT(DISTINCT s.lead_id) as lead_count
            FROM states s
            GROUP BY s.state_code
            ORDER BY lead_count DESC
            ''')
            
            results = cursor.fetchall()
            
            # Format results
            state_summary = [
                {
                    'state_code': row[0],
                    'state_name': row[1],
                    'lead_count': row[2]
                }
                for row in results
            ]
            
            conn.close()
            
            return state_summary
        
        except Exception as e:
            self.logger.error(f"Error getting states summary: {str(e)}")
            return []
    
    def get_all_states(self) -> List[Dict[str, str]]:
        """Get list of all US states.
        
        Returns:
            List of dictionaries with state_code and state_name
        """
        return self.state_extractor.get_all_states()
    
    def update_lead_states(self, lead_id: str, states: List[Dict[str, str]]) -> bool:
        """Update the states associated with a lead.
        
        Args:
            lead_id: Lead ID
            states: List of state dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Delete existing states
            cursor.execute('DELETE FROM states WHERE lead_id = ?', (lead_id,))
            
            # Insert new states
            for state in states:
                cursor.execute('''
                INSERT INTO states (lead_id, state_code, state_name)
                VALUES (?, ?, ?)
                ''', (
                    lead_id,
                    state.get('state_code'),
                    state.get('state_name')
                ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Updated states for lead {lead_id}")
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error updating lead states: {str(e)}")
            return False
    
    def reprocess_all_leads_for_states(self) -> Tuple[int, int]:
        """Reprocess all leads to extract and update state information.
        
        Returns:
            Tuple of (number of leads processed, number of leads updated)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all leads
            cursor.execute('SELECT id, data FROM leads')
            results = cursor.fetchall()
            
            processed_count = 0
            updated_count = 0
            
            for lead_id, lead_data_json in results:
                try:
                    # Parse lead data
                    lead_data = json.loads(lead_data_json)
                    
                    # Enhance lead with state information
                    enhanced_lead = enhance_lead_with_state_info(lead_data)
                    
                    # Extract states
                    states = enhanced_lead.get('states', [])
                    
                    # Update states in database
                    cursor.execute('DELETE FROM states WHERE lead_id = ?', (lead_id,))

(Content truncated due to size limit. Use line ranges to read in chunks)