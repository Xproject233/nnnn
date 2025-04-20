#!/bin/bash

# Test script for validating the web application deployment
# This script runs the deployment test and provides a summary of results

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Security Leads Automation - Deployment Validation${NC}"
echo "=================================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    echo "Please install Python 3 first."
    exit 1
fi

# Check if requests module is installed
if ! python3 -c "import requests" &> /dev/null; then
    echo -e "${YELLOW}Installing required Python packages...${NC}"
    pip install requests
fi

# Get the deployment URL from arguments or use default
URL=${1:-"http://localhost:8080"}

echo -e "${YELLOW}Testing deployment at: ${URL}${NC}"
echo ""

# Run the deployment test
python3 tests/test_deployment.py --url "$URL"

# Check the result
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}Deployment validation completed successfully!${NC}"
    echo -e "You can access the web application at: ${URL}"
else
    echo -e "\n${RED}Deployment validation failed.${NC}"
    echo "Please check the error messages above and verify your deployment."
fi

exit 0
