"""
Test script for validating the web application deployment
"""

import os
import sys
import requests
import time
import json
import argparse
from urllib.parse import urljoin

def test_deployment(base_url):
    """Test the web application deployment by making requests to various endpoints."""
    print(f"Testing deployment at {base_url}...")
    
    # Test endpoints and expected status codes
    endpoints = [
        # Route, Expected Status Code, Description
        ('/', 200, 'Home page'),
        ('/dashboard', 200, 'Dashboard page'),
        ('/leads', 200, 'Leads page'),
        ('/sources', 200, 'Sources page'),
        ('/settings', 200, 'Settings page'),
        ('/api/status', 200, 'API status endpoint'),
    ]
    
    success_count = 0
    failure_count = 0
    
    for endpoint, expected_status, description in endpoints:
        url = urljoin(base_url, endpoint)
        try:
            print(f"Testing {description} ({url})...", end='')
            response = requests.get(url, timeout=10)
            
            if response.status_code == expected_status:
                print(f" SUCCESS ({response.status_code})")
                success_count += 1
            else:
                print(f" FAILED (Expected: {expected_status}, Got: {response.status_code})")
                failure_count += 1
        except requests.exceptions.RequestException as e:
            print(f" ERROR: {str(e)}")
            failure_count += 1
    
    # Test API functionality
    print("\nTesting API functionality...")
    
    # Test status API
    try:
        print("Testing API status endpoint...", end='')
        response = requests.get(urljoin(base_url, '/api/status'), timeout=10)
        if response.status_code == 200 and 'scheduler' in response.json():
            print(" SUCCESS")
            success_count += 1
        else:
            print(" FAILED (Invalid response data)")
            failure_count += 1
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        print(f" ERROR: {str(e)}")
        failure_count += 1
    
    # Print summary
    print("\n=== Deployment Test Summary ===")
    print(f"Total tests: {success_count + failure_count}")
    print(f"Successful: {success_count}")
    print(f"Failed: {failure_count}")
    
    if failure_count == 0:
        print("\nDEPLOYMENT VALIDATION SUCCESSFUL!")
        print(f"The web application is running correctly at {base_url}")
        return True
    else:
        print("\nDEPLOYMENT VALIDATION FAILED!")
        print("Please check the logs and error messages above.")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test Security Leads Automation web deployment')
    parser.add_argument('--url', default='http://localhost:8080', help='Base URL of the deployed application')
    args = parser.parse_args()
    
    success = test_deployment(args.url)
    sys.exit(0 if success else 1)
