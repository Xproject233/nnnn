#!/bin/bash

# Run script for Security Leads Automation System
# This script provides a convenient way to run the system with various commands

# Set base directory
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check if required packages are installed
if ! python3 -c "import requests, beautifulsoup4, selenium, pandas, lxml" &> /dev/null; then
    echo "Installing required packages..."
    pip install requests beautifulsoup4 selenium pandas lxml schedule
fi

# Function to display help
show_help() {
    echo "Security Leads Automation System"
    echo ""
    echo "Usage: ./run.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start       Start the automation system"
    echo "  stop        Stop the automation system"
    echo "  run         Run the automation process immediately"
    echo "  status      Show the current system status"
    echo "  export      Export leads to a file (JSON or CSV)"
    echo "  test        Run the system tests"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./run.sh start"
    echo "  ./run.sh export --format csv --output leads.csv"
    echo ""
}

# Parse command
COMMAND=${1:-help}
shift

case "$COMMAND" in
    start)
        echo "Starting Security Leads Automation System..."
        python3 main.py --action start "$@"
        ;;
    stop)
        echo "Stopping Security Leads Automation System..."
        python3 main.py --action stop "$@"
        ;;
    run)
        echo "Running automation process immediately..."
        python3 main.py --action run "$@"
        ;;
    status)
        echo "Getting system status..."
        python3 main.py --action status "$@"
        ;;
    export)
        echo "Exporting leads..."
        python3 main.py --action export "$@"
        ;;
    test)
        echo "Running system tests..."
        # Create tests directory if it doesn't exist
        mkdir -p tests
        python3 -m unittest discover -s tests
        ;;
    help|*)
        show_help
        ;;
esac

exit 0
