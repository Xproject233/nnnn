"""
Web Application for Security Leads Automation

This module provides a Flask web interface for the security leads automation system,
allowing users to interact with the system through a browser.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import SecurityLeadsAutomation

# Initialize Flask app
app = Flask(__name__)

# Initialize the security leads automation system
base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
config_path = str(base_dir / "config.json")
system = SecurityLeadsAutomation(config_path)

# Start the system
system.start()

@app.route('/')
def index():
    """Render the dashboard page."""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Render the dashboard page with system status."""
    status = system.get_status()
    return render_template('dashboard.html', status=status)

@app.route('/leads')
def leads():
    """Render the leads page."""
    # Get filter parameters from query string
    source = request.args.get('source')
    lead_type = request.args.get('lead_type')
    status = request.args.get('status')
    min_confidence = request.args.get('min_confidence')
    opportunity_type = request.args.get('opportunity_type')
    is_armed = request.args.get('is_armed')
    location = request.args.get('location')
    
    # Build filters dictionary
    filters = {}
    if source:
        filters['source'] = source
    if lead_type:
        filters['lead_type'] = lead_type
    if status:
        filters['status'] = status
    if min_confidence:
        filters['min_confidence'] = float(min_confidence)
    if opportunity_type:
        filters['opportunity_type'] = opportunity_type
    if is_armed is not None:
        filters['is_armed'] = is_armed.lower() == 'true'
    if location:
        filters['location'] = location
    
    # Get leads with filters
    leads_data = system.get_leads(filters, limit=100)
    
    return render_template('leads.html', leads=leads_data, filters=filters)

@app.route('/lead/<lead_id>')
def lead_detail(lead_id):
    """Render the lead detail page."""
    lead = system.database.get_lead(lead_id)
    if not lead:
        return redirect(url_for('leads'))
    
    return render_template('lead_detail.html', lead=lead)

@app.route('/sources')
def sources():
    """Render the sources page."""
    scraper_status = system.scraper_manager.get_scraper_status()
    return render_template('sources.html', scrapers=scraper_status)

@app.route('/settings')
def settings():
    """Render the settings page."""
    return render_template('settings.html', config=system.config)

@app.route('/api/status')
def api_status():
    """API endpoint for system status."""
    status = system.get_status()
    return jsonify(status)

@app.route('/api/run', methods=['POST'])
def api_run():
    """API endpoint to run the automation process."""
    result = system.run_now()
    return jsonify({'result': result})

@app.route('/api/leads')
def api_leads():
    """API endpoint for leads data."""
    # Get filter parameters from query string
    source = request.args.get('source')
    lead_type = request.args.get('lead_type')
    status = request.args.get('status')
    min_confidence = request.args.get('min_confidence')
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # Build filters dictionary
    filters = {}
    if source:
        filters['source'] = source
    if lead_type:
        filters['lead_type'] = lead_type
    if status:
        filters['status'] = status
    if min_confidence:
        filters['min_confidence'] = float(min_confidence)
    
    # Get leads with filters
    leads = system.get_leads(filters, limit=limit, offset=offset)
    
    return jsonify(leads)

@app.route('/api/lead/<lead_id>')
def api_lead_detail(lead_id):
    """API endpoint for lead detail."""
    lead = system.database.get_lead(lead_id)
    if not lead:
        return jsonify({'error': 'Lead not found'}), 404
    
    return jsonify(lead)

@app.route('/api/lead/<lead_id>/status', methods=['POST'])
def api_update_lead_status(lead_id):
    """API endpoint to update lead status."""
    status = request.json.get('status')
    if not status:
        return jsonify({'error': 'Status is required'}), 400
    
    result = system.database.update_lead_status(lead_id, status)
    return jsonify({'success': result})

@app.route('/api/lead/<lead_id>/note', methods=['POST'])
def api_add_lead_note(lead_id):
    """API endpoint to add a note to a lead."""
    note = request.json.get('note')
    if not note:
        return jsonify({'error': 'Note content is required'}), 400
    
    note_id = system.database.add_note(lead_id, note)
    return jsonify({'note_id': note_id})

@app.route('/api/lead/<lead_id>/tag', methods=['POST'])
def api_add_lead_tag(lead_id):
    """API endpoint to add a tag to a lead."""
    tag = request.json.get('tag')
    if not tag:
        return jsonify({'error': 'Tag name is required'}), 400
    
    tag_id = system.database.add_tag(lead_id, tag)
    return jsonify({'tag_id': tag_id})

@app.route('/api/export', methods=['GET'])
def api_export():
    """API endpoint to export leads."""
    format = request.args.get('format', 'json')
    if format not in ['json', 'csv']:
        return jsonify({'error': 'Unsupported format'}), 400
    
    # Get filter parameters
    source = request.args.get('source')
    lead_type = request.args.get('lead_type')
    status = request.args.get('status')
    min_confidence = request.args.get('min_confidence')
    
    # Build filters dictionary
    filters = {}
    if source:
        filters['source'] = source
    if lead_type:
        filters['lead_type'] = lead_type
    if status:
        filters['status'] = status
    if min_confidence:
        filters['min_confidence'] = float(min_confidence)
    
    # Export leads
    output_path = system.export_leads(format=format, filters=filters)
    
    # Return file for download
    return send_file(output_path, as_attachment=True)

@app.route('/api/settings', methods=['POST'])
def api_update_settings():
    """API endpoint to update system settings."""
    settings = request.json
    if not settings:
        return jsonify({'error': 'Settings data is required'}), 400
    
    # Update config
    system.config_manager.update_config(settings)
    
    # Restart system to apply changes
    system.stop()
    system.start()
    
    return jsonify({'success': True})

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
