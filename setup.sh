#!/bin/bash
# PATH: ./setup.sh
# MCP setup script

# Exit immediately on error
set -e

# Define color codes for better output readability
GREEN='\033[1;32m'
BLUE='\033[1;34m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

APPNAME=file_rank_mcp
LOGFILE="/tmp/${APPNAME}_$(date +%Y%m%d_%H%M%S).log"

print_header() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local message="[${timestamp}] ### $1 ###"
    echo -e "${GREEN}${message}${NC}"
    echo "$message" >> "$LOGFILE"
}

print_action() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local message="[${timestamp}] >>> $1"
    echo -e "${BLUE}${message}${NC}"
    echo "$message" >> "$LOGFILE"
}

print_warning() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local message="[${timestamp}] !!! $1"
    echo -e "${YELLOW}${message}${NC}"
    echo "$message" >> "$LOGFILE"
}

print_error() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local message="[${timestamp}] ERROR: $1"
    echo -e "${RED}${message}${NC}"
    echo "$message" >> "$LOGFILE"
}

print_detail() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local message="[${timestamp}]     $1"
    echo -e "${CYAN}${message}${NC}"
    echo "$message" >> "$LOGFILE"
}

print_header "${APPNAME} MCP Setup"
if [ -f ./venv ]; then
    print_detail "Venv already exists, skipping..."
else
    print_detail "Creating Python Virtual Environment"
    python3 -m venv venv
fi

print_detail "Activating Virtual Environment"
source ./venv/bin/activate

print_header "Upgrading pip"
python3 -m pip install --upgrade pip

print_header "Install Python Packages"
pip3 install -r requirements.txt

print_header "Setup Complete."
exit 0
