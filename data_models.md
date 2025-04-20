# Data Models for Security Leads Automation

## Overview
This document defines the data models for storing and managing security service leads extracted from various sources. These models will ensure consistent data representation throughout the system.

## Lead Data Model

### Core Lead Entity
```python
class Lead:
    id: str                     # Unique identifier for the lead
    source: str                 # Source website where lead was found
    source_url: str             # Specific URL where lead was found
    date_extracted: datetime    # When the lead was extracted
    date_updated: datetime      # When the lead was last updated
    lead_type: str              # Type of lead (job posting, RFP, contract)
    status: str                 # Status (new, contacted, qualified, etc.)
    confidence_score: float     # Confidence in lead quality (0.0-1.0)
```

### Company/Organization Information
```python
class Organization:
    name: str                   # Company/organization name
    website: str                # Company website if available
    industry: str               # Industry classification
    size: str                   # Company size if available
    description: str            # Brief description
    is_government: bool         # Whether it's a government entity
```

### Contact Information
```python
class Contact:
    first_name: str             # First name if available
    last_name: str              # Last name if available
    title: str                  # Job title
    email: str                  # Email address
    phone: str                  # Phone number
    department: str             # Department within organization
```

### Opportunity Details
```python
class Opportunity:
    title: str                  # Job title or RFP title
    description: str            # Full description
    requirements: str           # Requirements specified
    location: str               # Geographic location
    opportunity_type: str       # Event, construction, general security, etc.
    start_date: datetime        # When the opportunity starts
    end_date: datetime          # When the opportunity ends or deadline
    estimated_value: float      # Estimated contract value if available
    is_armed: bool              # Whether armed guards are required
    guard_count: int            # Number of guards needed if specified
```

## Database Schema

### Leads Table
```sql
CREATE TABLE leads (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    source_url TEXT NOT NULL,
    date_extracted TIMESTAMP NOT NULL,
    date_updated TIMESTAMP NOT NULL,
    lead_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    confidence_score REAL NOT NULL DEFAULT 0.5
);
```

### Organizations Table
```sql
CREATE TABLE organizations (
    id TEXT PRIMARY KEY,
    lead_id TEXT NOT NULL,
    name TEXT NOT NULL,
    website TEXT,
    industry TEXT,
    size TEXT,
    description TEXT,
    is_government BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (lead_id) REFERENCES leads(id)
);
```

### Contacts Table
```sql
CREATE TABLE contacts (
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
);
```

### Opportunities Table
```sql
CREATE TABLE opportunities (
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
);
```

## Data Validation Rules

### Email Validation
- Must contain @ symbol
- Must have valid domain
- Should not be generic (e.g., info@, contact@)

### Phone Validation
- Must be in standard format
- Must have appropriate length
- Should include country code for international numbers

### Organization Validation
- Name must not be empty
- Should be normalized (remove Inc., LLC, etc. for matching)
- Should be checked against existing organizations to prevent duplicates

### Opportunity Validation
- Title must not be empty
- Description should have minimum length
- Dates should be in valid range (not in past)

## Data Relationships

- Each Lead has one Organization
- Each Lead has one Opportunity
- Each Lead can have multiple Contacts
- Organizations can be associated with multiple Leads (for deduplication)

## Data Enrichment

The system will support enriching lead data from secondary sources:
- Company information from business directories
- Contact details from professional networks
- Location data from geographic services

## Export Formats

The data model will support exporting leads in the following formats:
- CSV
- Excel
- JSON
- PDF reports
