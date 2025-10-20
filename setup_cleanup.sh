#!/bin/bash
#
# Setup automated cleanup cron job for RpiPrint
#

set -e

echo "======================================"
echo "🕐 Setup Automated Cleanup"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get current directory
CURRENT_DIR=$(pwd)
CURRENT_USER=$(whoami)

echo "Configuration:"
echo "  - User: $CURRENT_USER"
echo "  - Directory: $CURRENT_DIR"
echo ""

# Make cleanup script executable
chmod +x cleanup_old_files.py

echo "Cleanup script configuration:"
echo "  - Completed jobs: Keep 14 days"
echo "  - Rejected jobs: Keep 7 days"
echo "  - Orphaned files: Keep 3 days"
echo ""

# Test cleanup script
echo "Testing cleanup script (dry run)..."
./cleanup_old_files.py --dry-run
echo ""

read -p "Setup automatic daily cleanup? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Setup cancelled"
    exit 0
fi

# Create log directory
mkdir -p logs

# Create cron job
CRON_CMD="0 3 * * * cd $CURRENT_DIR && $CURRENT_DIR/venv/bin/python3 $CURRENT_DIR/cleanup_old_files.py >> $CURRENT_DIR/logs/cleanup.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "cleanup_old_files.py"; then
    echo -e "${YELLOW}⚠${NC} Cleanup cron job already exists"
    read -p "Update existing cron job? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing cron job"
        exit 0
    fi
    # Remove old cron job
    (crontab -l 2>/dev/null | grep -v "cleanup_old_files.py") | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

echo ""
echo -e "${GREEN}✓${NC} Automatic cleanup configured!"
echo ""
echo "======================================"
echo "Schedule Details:"
echo "======================================"
echo "  - Runs daily at 3:00 AM"
echo "  - Logs to: logs/cleanup.log"
echo ""
echo "What will be cleaned:"
echo "  - Completed jobs older than 14 days"
echo "  - Rejected jobs older than 7 days"
echo "  - Refunded jobs older than 14 days"
echo "  - Orphaned files older than 3 days"
echo ""
echo "======================================"
echo "Useful Commands:"
echo "======================================"
echo "  View cron jobs:    crontab -l"
echo "  Edit cron jobs:    crontab -e"
echo "  Remove cleanup:    crontab -l | grep -v cleanup_old_files.py | crontab -"
echo "  View cleanup log:  tail -f logs/cleanup.log"
echo "  Manual cleanup:    ./cleanup_old_files.py"
echo "  Dry run test:      ./cleanup_old_files.py --dry-run"
echo ""
echo "======================================"
echo ""

read -p "Run cleanup now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Running cleanup..."
    ./cleanup_old_files.py
fi

echo ""
echo -e "${GREEN}✓${NC} Setup complete!"
