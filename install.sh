#!/bin/bash

# Installation script for Security Leads Automation System
# This script installs all required dependencies and sets up the system

echo "Installing Security Leads Automation System..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    echo "Please install Python 3 and try again."
    exit 1
fi

# Install required packages
echo "Installing required Python packages..."
pip install requests beautifulsoup4 selenium pandas lxml schedule

# Create necessary directories
echo "Setting up directory structure..."
mkdir -p data logs

# Set permissions
echo "Setting file permissions..."
chmod +x run.sh

echo "Installation complete!"
echo "You can now use the system with the following command:"
echo "./run.sh start"
echo ""
echo "For more information, please read the README.md file."

exit 0
