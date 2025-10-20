#!/bin/bash
#
# RpiPrint Service Installation Script
# This script installs RpiPrint as a systemd service for auto-start
#

set -e  # Exit on error

echo "======================================"
echo "📦 Installing RpiPrint System Service"
echo "======================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${RED}✗${NC} Don't run this script as root (no sudo needed)"
    exit 1
fi

# Get current directory
CURRENT_DIR=$(pwd)
CURRENT_USER=$(whoami)

echo "Installation directory: $CURRENT_DIR"
echo "User: $CURRENT_USER"
echo ""

# Check if service file exists
if [ ! -f "rpiprint.service" ]; then
    echo -e "${RED}✗${NC} Service file not found: rpiprint.service"
    echo "Make sure you're in the RpiPrint directory"
    exit 1
fi

# Create temporary service file with updated paths
echo "Creating service configuration..."
cat > rpiprint.service.tmp <<EOF
[Unit]
Description=RpiPrint Web Service - Print Management System
After=network.target cups.service
Wants=cups.service

[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
Environment="PATH=$CURRENT_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=$CURRENT_DIR/venv/bin/python3 $CURRENT_DIR/app_production.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=$CURRENT_DIR/uploads $CURRENT_DIR/screenshots $CURRENT_DIR/jobs.db $CURRENT_DIR/rpiprint.log

[Install]
WantedBy=multi-user.target
EOF

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠${NC} Virtual environment not found"
    read -p "Create virtual environment now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
        echo "Installing dependencies..."
        pip install --upgrade pip
        pip install -r requirements.txt
        deactivate
        echo -e "${GREEN}✓${NC} Virtual environment created"
    else
        echo -e "${RED}✗${NC} Cannot proceed without virtual environment"
        exit 1
    fi
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠${NC} .env file not found"
    if [ -f ".env.production" ]; then
        echo "Found .env.production template"
        read -p "Copy .env.production to .env? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cp .env.production .env
            echo -e "${GREEN}✓${NC} Created .env from template"
            echo -e "${YELLOW}⚠${NC} IMPORTANT: Edit .env and update credentials!"
            echo "Run: nano .env"
        fi
    else
        echo -e "${YELLOW}⚠${NC} No .env configuration found"
        echo "Create .env file with your configuration before starting the service"
    fi
fi

# Copy service file
echo ""
echo "Installing service file..."
sudo cp rpiprint.service.tmp /etc/systemd/system/rpiprint.service
rm rpiprint.service.tmp

# Reload systemd
echo "Reloading systemd..."
sudo systemctl daemon-reload

# Enable service
echo "Enabling RpiPrint service..."
sudo systemctl enable rpiprint

echo ""
echo -e "${GREEN}✓${NC} Service installed successfully!"
echo ""
echo "======================================"
echo "Useful Commands:"
echo "======================================"
echo "  Start service:   sudo systemctl start rpiprint"
echo "  Stop service:    sudo systemctl stop rpiprint"
echo "  Restart service: sudo systemctl restart rpiprint"
echo "  Check status:    sudo systemctl status rpiprint"
echo "  View logs:       sudo journalctl -u rpiprint -f"
echo "  Disable service: sudo systemctl disable rpiprint"
echo ""
echo "======================================"
echo ""

read -p "Start the service now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting RpiPrint service..."
    sudo systemctl start rpiprint
    
    sleep 2
    
    if sudo systemctl is-active --quiet rpiprint; then
        echo ""
        echo -e "${GREEN}✓${NC} Service started successfully!"
        echo ""
        sudo systemctl status rpiprint --no-pager
    else
        echo ""
        echo -e "${RED}✗${NC} Service failed to start"
        echo "Check logs with: sudo journalctl -u rpiprint -n 50"
    fi
else
    echo ""
    echo "Service is enabled but not started."
    echo "Start it manually with: sudo systemctl start rpiprint"
fi

echo ""
echo "======================================"
echo "🎉 Installation Complete!"
echo "======================================"
