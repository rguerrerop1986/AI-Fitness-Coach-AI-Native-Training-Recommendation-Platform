#!/bin/bash

# Script to reset the database
# Usage: ./reset_db.sh [--create-demo-data] [--flush-only]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}============================================================${NC}"
echo -e "${YELLOW}WARNING: This will DELETE ALL DATA in the database!${NC}"
echo -e "${YELLOW}============================================================${NC}"
echo ""

read -p "Are you sure you want to continue? (yes/no): " confirm
if [[ $confirm != [yY][eE][sS] && $confirm != [yY] ]]; then
    echo -e "${RED}Operation cancelled.${NC}"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if we're in the backend directory
if [ ! -f "manage.py" ]; then
    echo -e "${RED}Error: manage.py not found. Please run this script from the backend directory.${NC}"
    exit 1
fi

# Parse arguments
CREATE_DEMO_DATA=""
FLUSH_ONLY=""

for arg in "$@"; do
    case $arg in
        --create-demo-data)
            CREATE_DEMO_DATA="--create-demo-data"
            ;;
        --flush-only)
            FLUSH_ONLY="--flush-only"
            ;;
    esac
done

echo -e "${GREEN}Resetting database...${NC}"
python manage.py reset_database --no-input $CREATE_DEMO_DATA $FLUSH_ONLY

echo -e "${GREEN}Database reset completed!${NC}"
