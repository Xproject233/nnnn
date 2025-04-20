"""
Database Manager for Security Leads Automation

This module handles database operations for storing and retrieving lead data.
"""

import os
import sqlite3
import json
from pathlib import Path
from datetime import datetime
import uuid

class DatabaseManager:
    """Manages database operations for the scraper system."""
    
    def __init__(self, config=None):
        """Initialize the database manager.
        
        Args:
            config (dict, optional): Database configuration. Defaults to None.
        """
        self.base_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.config = config or {
            "type": "sqlite",
            "path": str(self.base_dir / "data" / "leads.db")
        }
        self.conn = None
        self._setup_database()
        
    def _setup_database(self):
        """Set up the database."""
        db_dir = os.path.dirname(self.config["path"])
        os.makedirs(db_dir, exist_ok=True)
        
        self.conn = sqlite3.connect(self.config["path"])
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Create leads table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            source_url TEXT NOT NULL,
            date_extracted TIMESTAMP NOT NULL,
            date_updated TIMESTAMP NOT NULL,
            lead_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'new',
            confidence_score REAL NOT NULL DEFAULT 0.5
        )
        ''')
        
        # Create organizations table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS organizations (
            id TEXT PRIMARY KEY,
            lead_id TEXT NOT NULL,
            name TEXT NOT NULL,
            website TEXT,
            industry TEXT,
            size TEXT,
            description TEXT,
            is_government BOOLEAN NOT NULL DEFAULT FALSE,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
        ''')
        
        # Create contacts table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id TEXT PRIMARY KEY,
            lead_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            title TEXT,
            email TEXT,
            phone TEXT,
            department TEXT,
            FOREIGN KEY (lead_id) REFERENCES leads(id),
            FOREIGN KEY (organization_id) REFERENCES organizations(id)
        )
        ''')
        
        # Create opportunities table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS opportunities (
            id TEXT PRIMARY KEY,
            lead_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            requirements TEXT,
            location TEXT,
            opportunity_type TEXT,
            start_date TIMESTAMP,
            end_date TIMESTAMP,
            estimated_value REAL,
            is_armed BOOLEAN,
            guard_count INTEGER,
            FOREIGN KEY (lead_id) REFERENCES leads(id),
            FOREIGN KEY (organization_id) REFERENCES organizations(id)
        )
        ''')
        
        self.conn.commit()
    
    def insert_lead(self, lead_data):
        """Insert a new lead into the database.
        
        Args:
            lead_data (dict): Lead data
            
        Returns:
            str: Lead ID
        """
        cursor = self.conn.cursor()
        
        # Generate a unique ID for the lead
        lead_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # Insert lead
        cursor.execute('''
        INSERT INTO leads (
            id, source, source_url, date_extracted, date_updated, 
            lead_type, status, confidence_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            lead_id,
            lead_data.get('source', ''),
            lead_data.get('source_url', ''),
            now,
            now,
            lead_data.get('lead_type', 'job_posting'),
            lead_data.get('status', 'new'),
            lead_data.get('confidence_score', 0.5)
        ))
        
        # Insert organization
        org_data = lead_data.get('organization', {})
        org_id = str(uuid.uuid4())
        
        cursor.execute('''
        INSERT INTO organizations (
            id, lead_id, name, website, industry, size, description, is_government
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            org_id,
            lead_id,
            org_data.get('name', ''),
            org_data.get('website', ''),
            org_data.get('industry', ''),
            org_data.get('size', ''),
            org_data.get('description', ''),
            org_data.get('is_government', False)
        ))
        
        # Insert opportunity
        opp_data = lead_data.get('opportunity', {})
        opp_id = str(uuid.uuid4())
        
        cursor.execute('''
        INSERT INTO opportunities (
            id, lead_id, organization_id, title, description, requirements,
            location, opportunity_type, start_date, end_date, estimated_value,
            is_armed, guard_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            opp_id,
            lead_id,
            org_id,
            opp_data.get('title', ''),
            opp_data.get('description', ''),
            opp_data.get('requirements', ''),
            opp_data.get('location', ''),
            opp_data.get('opportunity_type', ''),
            opp_data.get('start_date', None),
            opp_data.get('end_date', None),
            opp_data.get('estimated_value', None),
            opp_data.get('is_armed', False),
            opp_data.get('guard_count', None)
        ))
        
        # Insert contacts
        contacts_data = lead_data.get('contacts', [])
        for contact in contacts_data:
            contact_id = str(uuid.uuid4())
            cursor.execute('''
            INSERT INTO contacts (
                id, lead_id, organization_id, first_name, last_name,
                title, email, phone, department
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                contact_id,
                lead_id,
                org_id,
                contact.get('first_name', ''),
                contact.get('last_name', ''),
                contact.get('title', ''),
                contact.get('email', ''),
                contact.get('phone', ''),
                contact.get('department', '')
            ))
        
        self.conn.commit()
        return lead_id
    
    def get_lead(self, lead_id):
        """Get a lead by ID.
        
        Args:
            lead_id (str): Lead ID
            
        Returns:
            dict: Lead data
        """
        cursor = self.conn.cursor()
        
        # Get lead
        cursor.execute('SELECT * FROM leads WHERE id = ?', (lead_id,))
        lead_row = cursor.fetchone()
        if not lead_row:
            return None
        
        lead_data = {
            'id': lead_row[0],
            'source': lead_row[1],
            'source_url': lead_row[2],
            'date_extracted': lead_row[3],
            'date_updated': lead_row[4],
            'lead_type': lead_row[5],
            'status': lead_row[6],
            'confidence_score': lead_row[7]
        }
        
        # Get organization
        cursor.execute('SELECT * FROM organizations WHERE lead_id = ?', (lead_id,))
        org_row = cursor.fetchone()
        if org_row:
            org_id = org_row[0]
            lead_data['organization'] = {
                'id': org_id,
                'name': org_row[2],
                'website': org_row[3],
                'industry': org_row[4],
                'size': org_row[5],
                'description': org_row[6],
                'is_government': bool(org_row[7])
            }
            
            # Get opportunity
            cursor.execute('SELECT * FROM opportunities WHERE lead_id = ?', (lead_id,))
            opp_row = cursor.fetchone()
            if opp_row:
                lead_data['opportunity'] = {
                    'id': opp_row[0],
                    'title': opp_row[3],
                    'description': opp_row[4],
                    'requirements': opp_row[5],
                    'location': opp_row[6],
                    'opportunity_type': opp_row[7],
                    'start_date': opp_row[8],
                    'end_date': opp_row[9],
                    'estimated_value': opp_row[10],
                    'is_armed': bool(opp_row[11]),
                    'guard_count': opp_row[12]
                }
            
            # Get contacts
            cursor.execute('SELECT * FROM contacts WHERE lead_id = ?', (lead_id,))
            contact_rows = cursor.fetchall()
            lead_data['contacts'] = []
            for contact_row in contact_rows:
                lead_data['contacts'].append({
                    'id': contact_row[0],
                    'first_name': contact_row[3],
                    'last_name': contact_row[4],
                    'title': contact_row[5],
                    'email': contact_row[6],
                    'phone': contact_row[7],
                    'department': contact_row[8]
                })
        
        return lead_data
    
    def get_all_leads(self, limit=100, offset=0):
        """Get all leads.
        
        Args:
            limit (int, optional): Maximum number of leads to return. Defaults to 100.
            offset (int, optional): Offset for pagination. Defaults to 0.
            
        Returns:
            list: List of lead data
        """
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT id FROM leads ORDER BY date_updated DESC LIMIT ? OFFSET ?', 
                      (limit, offset))
        lead_ids = [row[0] for row in cursor.fetchall()]
        
        return [self.get_lead(lead_id) for lead_id in lead_ids]
    
    def update_lead_status(self, lead_id, status):
        """Update lead status.
        
        Args:
            lead_id (str): Lead ID
            status (str): New status
            
        Returns:
            bool: True if successful, False otherwise
        """
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        try:
            cursor.execute('''
            UPDATE leads SET status = ?, date_updated = ? WHERE id = ?
            ''', (status, now, lead_id))
            self.conn.commit()
            return True
        except Exception:
            return False
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
