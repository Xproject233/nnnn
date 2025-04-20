# Security Leads Automation System

A comprehensive automation system for generating legitimate leads for security service companies in the USA. This system scrapes job boards, government contract sites, and other sources to find opportunities for security guard services.

## Features

- **Multi-source Scraping**: Extracts data from job boards, government contract sites, and specialized security job platforms
- **Advanced Data Extraction**: Identifies contact information, company details, requirements, and compensation
- **Data Validation**: Ensures leads are legitimate and relevant with confidence scoring
- **Deduplication**: Prevents duplicate leads from different sources
- **Automated Scheduling**: Runs on customizable schedules (daily, weekly, monthly)
- **Database Storage**: Stores leads in a structured database for easy retrieval
- **Export Capabilities**: Exports leads in JSON or CSV formats
- **Command-line Interface**: Simple commands to control the system

## System Requirements

- Python 3.6 or higher
- Required Python packages:
  - requests
  - beautifulsoup4
  - selenium
  - pandas
  - lxml
  - schedule

## Installation

1. Clone or download this repository
2. Install required packages:
   ```
   pip install requests beautifulsoup4 selenium pandas lxml schedule
   ```
3. Configure the system by editing `config.json`

## Configuration

The system is configured through the `config.json` file. Key configuration options include:

- **Database settings**: Type (SQLite or PostgreSQL) and connection details
- **Logging settings**: Log level, file location, and rotation settings
- **Scraper settings**: User agents, request delays, timeouts, and source URLs
- **Scheduler settings**: Schedule configuration (daily, weekly, monthly)
- **Validation settings**: Minimum confidence score and validation options

## Usage

The system includes a convenient `run.sh` script that provides a simple interface:

```bash
# Start the automation system
./run.sh start

# Stop the automation system
./run.sh stop

# Run the automation process immediately
./run.sh run

# Show the current system status
./run.sh status

# Export leads to a file (JSON or CSV)
./run.sh export --format csv --output leads.csv

# Run the system tests
./run.sh test

# Show help
./run.sh help
```

## System Architecture

The system is built with a modular architecture:

1. **Core Components**:
   - ConfigManager: Manages system configuration
   - LoggerSetup: Configures logging
   - ScraperManager: Manages and runs scrapers
   - LeadDatabase: Stores and retrieves lead data
   - AutomationScheduler: Schedules and runs automation

2. **Scrapers**:
   - BaseScraper: Base class for all scrapers
   - Source-specific scrapers (InstantMarkets, BidNetDirect, USAJOBS, etc.)

3. **Utilities**:
   - Data extraction utilities
   - Data validation and filtering
   - Lead enrichment

## Data Sources

The system scrapes the following sources:

1. **InstantMarkets**: Government RFPs and contracts for security services
2. **BidNetDirect**: Security service bids and RFPs
3. **USAJOBS**: Federal security positions
4. **Security Jobs Network**: Specialized security job board
5. **Security Guards Only**: Security-specific job listings

## Lead Data Structure

Leads are stored with the following structure:

```json
{
  "id": "unique-id",
  "source": "source-name",
  "source_url": "https://source.url/page",
  "date_extracted": "2025-04-20T10:00:00",
  "lead_type": "job_posting",
  "status": "new",
  "confidence_score": 0.85,
  "organization": {
    "name": "Company Name",
    "is_government": false
  },
  "contacts": [
    {
      "email": "contact@example.com",
      "phone": "(123) 456-7890"
    }
  ],
  "opportunity": {
    "title": "Security Guard Needed",
    "description": "Description text...",
    "requirements": "Requirements text...",
    "location": "New York, NY",
    "opportunity_type": "event",
    "is_armed": false
  }
}
```

## Extending the System

### Adding New Sources

To add a new source:

1. Create a new scraper class in `scripts/scrapers/` that inherits from BaseScraper
2. Implement the `scrape()` and `extract_lead_data()` methods
3. Add the source to the configuration in `config.json`

### Customizing Validation

Validation rules can be customized by modifying the `LeadValidator` class in `scripts/utils/data_validation.py`.

## Troubleshooting

Common issues and solutions:

- **Scraper not working**: Check the source URL in config.json and verify the website structure hasn't changed
- **Database errors**: Ensure the database path is correct and the directory exists
- **Scheduling issues**: Verify the system time and scheduler configuration

## License

This software is provided for legitimate business use only. Users are responsible for ensuring compliance with all applicable laws and regulations regarding data collection and usage.

## Support

For issues, questions, or feature requests, please contact the development team.
