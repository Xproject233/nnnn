#!/bin/bash

# Run the state filtering tests
# This script executes the test suite for the state filtering functionality

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Security Leads Automation - State Filtering Tests${NC}"
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
echo -e "${YELLOW}Running state filtering tests...${NC}"
python3 -m unittest tests/test_state_filtering.py

# Check the result
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}All state filtering tests passed!${NC}"
    echo "The state extraction, filtering, and visualization features are working correctly."
else
    echo -e "\n${RED}Some tests failed.${NC}"
    echo "Please check the error messages above and fix any issues."
fi

exit 0
