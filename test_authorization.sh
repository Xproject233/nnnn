#!/bin/bash

# Run the authorization system tests
# This script executes the test suite for the invitation code and deployment authorization system

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Security Leads Automation - Authorization System Tests${NC}"
echo "=================================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    echo "Please install Python 3 first."
    exit 1
fi

# Create test directory if it doesn't exist
mkdir -p tests/test_data

# Run the tests
echo -e "${YELLOW}Running authorization system tests...${NC}"
python3 -m unittest tests/test_authorization.py

# Check the result
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}All authorization system tests passed!${NC}"
    echo "The invitation code system, email confirmation workflow, and one-click deployment are working correctly."
else
    echo -e "\n${RED}Some tests failed.${NC}"
    echo "Please check the error messages above and fix any issues."
fi

exit 0
