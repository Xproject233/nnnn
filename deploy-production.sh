#!/bin/bash

# Production deployment script for Security Leads Automation Web Application
# This script deploys the web application using Docker Compose in production mode

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Security Leads Automation - Production Deployment${NC}"
echo "=================================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed.${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed.${NC}"
    echo "Please install Docker Compose first: https://docs.docker.com/compose/install/"
    exit 1
fi

# Create necessary directories if they don't exist
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p data logs
chmod -R 777 data logs

# Build and start the Docker containers using production configuration
echo -e "${YELLOW}Building and starting Docker containers in production mode...${NC}"
docker-compose -f production-compose.yml up -d --build

# Check if containers are running
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Production deployment successful!${NC}"
    
    # Get the server's IP address
    IP_ADDRESS=$(hostname -I | awk '{print $1}')
    
    echo -e "${GREEN}The web application is now running at:${NC}"
    echo -e "http://${IP_ADDRESS}"
    echo ""
    echo "You can also access it at http://localhost if you're on the same machine."
    echo ""
    echo -e "${YELLOW}To stop the application, run:${NC}"
    echo "docker-compose -f production-compose.yml down"
    
    # Run validation tests
    echo ""
    echo -e "${YELLOW}Running deployment validation tests...${NC}"
    ./validate_deployment.sh "http://${IP_ADDRESS}"
else
    echo -e "${RED}Production deployment failed. Please check the error messages above.${NC}"
    exit 1
fi

exit 0
