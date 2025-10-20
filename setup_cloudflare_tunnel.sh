#!/bin/bash
#
# Cloudflare Tunnel Setup Script for RpiPrint
# This script automates the installation and configuration of Cloudflare Tunnel
#

set -e  # Exit on error

echo "======================================"
echo "🌐 Cloudflare Tunnel Setup for RpiPrint"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Raspberry Pi
if [ -f /proc/device-tree/model ]; then
    PI_MODEL=$(cat /proc/device-tree/model)
    echo -e "${GREEN}✓${NC} Detected: $PI_MODEL"
else
    echo -e "${YELLOW}⚠${NC} Warning: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "======================================"
echo "Step 1: Installing Cloudflare Tunnel"
echo "======================================"
echo ""

# Determine architecture
ARCH=$(uname -m)
if [[ "$ARCH" == "aarch64" ]] || [[ "$ARCH" == "arm64" ]]; then
    CLOUDFLARED_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
elif [[ "$ARCH" == "armv7l" ]]; then
    CLOUDFLARED_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm"
else
    echo -e "${RED}✗${NC} Unsupported architecture: $ARCH"
    exit 1
fi

echo "Architecture: $ARCH"
echo "Download URL: $CLOUDFLARED_URL"

if [ ! -f /usr/local/bin/cloudflared ]; then
    echo "Downloading cloudflared..."
    wget -q --show-progress "$CLOUDFLARED_URL" -O cloudflared
    sudo mv cloudflared /usr/local/bin/cloudflared
    sudo chmod +x /usr/local/bin/cloudflared
    echo -e "${GREEN}✓${NC} cloudflared installed"
else
    echo -e "${GREEN}✓${NC} cloudflared already installed"
    cloudflared --version
fi

echo ""
echo "======================================"
echo "Step 2: Authenticate with Cloudflare"
echo "======================================"
echo ""
echo "This will open a browser window for authentication."
echo "If you're SSH'd into the Pi, the script will show a URL."
echo "Copy and paste it into your browser to authenticate."
echo ""
read -p "Press Enter to continue..."

cloudflared tunnel login

if [ $? -ne 0 ]; then
    echo -e "${RED}✗${NC} Authentication failed"
    exit 1
fi

echo -e "${GREEN}✓${NC} Authentication successful"

echo ""
echo "======================================"
echo "Step 3: Create a Tunnel"
echo "======================================"
echo ""
read -p "Enter a name for your tunnel (e.g., rpiprint): " TUNNEL_NAME

if [ -z "$TUNNEL_NAME" ]; then
    echo -e "${RED}✗${NC} Tunnel name cannot be empty"
    exit 1
fi

cloudflared tunnel create "$TUNNEL_NAME"

if [ $? -ne 0 ]; then
    echo -e "${RED}✗${NC} Failed to create tunnel"
    exit 1
fi

echo -e "${GREEN}✓${NC} Tunnel created: $TUNNEL_NAME"

# Get tunnel ID
TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')

if [ -z "$TUNNEL_ID" ]; then
    echo -e "${RED}✗${NC} Could not retrieve tunnel ID"
    exit 1
fi

echo "Tunnel ID: $TUNNEL_ID"

echo ""
echo "======================================"
echo "Step 4: Create Tunnel Configuration"
echo "======================================"
echo ""

# Create config directory
mkdir -p ~/.cloudflared

# Find the credentials file
CRED_FILE=$(find ~/.cloudflared -name "$TUNNEL_ID.json" 2>/dev/null | head -n 1)

if [ -z "$CRED_FILE" ]; then
    echo -e "${YELLOW}⚠${NC} Could not find credentials file automatically"
    CRED_FILE="~/.cloudflared/$TUNNEL_ID.json"
fi

# Create tunnel config
cat > ~/.cloudflared/config.yml <<EOF
tunnel: $TUNNEL_ID
credentials-file: $CRED_FILE

ingress:
  - hostname: CHANGE-THIS-TO-YOUR-DOMAIN.com
    service: http://localhost:5500
  - service: http_status:404
EOF

echo -e "${GREEN}✓${NC} Configuration created at ~/.cloudflared/config.yml"
echo ""
echo -e "${YELLOW}⚠ IMPORTANT:${NC} Edit the config file and replace the hostname!"
echo ""
echo "Run this command:"
echo "  nano ~/.cloudflared/config.yml"
echo ""
echo "Replace 'CHANGE-THIS-TO-YOUR-DOMAIN.com' with your actual domain"
echo "Examples:"
echo "  - print.yourdomain.com (if you own a domain)"
echo "  - your-unique-name.example.com"
echo ""
read -p "Press Enter after you've updated the hostname in config.yml..."

echo ""
echo "======================================"
echo "Step 5: Configure DNS"
echo "======================================"
echo ""
read -p "Enter your domain/subdomain (e.g., print.yourdomain.com): " HOSTNAME

if [ -z "$HOSTNAME" ]; then
    echo -e "${RED}✗${NC} Hostname cannot be empty"
    exit 1
fi

cloudflared tunnel route dns "$TUNNEL_NAME" "$HOSTNAME"

if [ $? -ne 0 ]; then
    echo -e "${RED}✗${NC} DNS configuration failed"
    echo "You may need to configure DNS manually in Cloudflare dashboard"
else
    echo -e "${GREEN}✓${NC} DNS configured for $HOSTNAME"
fi

echo ""
echo "======================================"
echo "Step 6: Install as System Service"
echo "======================================"
echo ""

sudo cloudflared service install

if [ $? -ne 0 ]; then
    echo -e "${RED}✗${NC} Service installation failed"
    exit 1
fi

echo -e "${GREEN}✓${NC} Cloudflared service installed"

echo ""
echo "======================================"
echo "Step 7: Start the Tunnel"
echo "======================================"
echo ""

sudo systemctl enable cloudflared
sudo systemctl start cloudflared

sleep 2

if sudo systemctl is-active --quiet cloudflared; then
    echo -e "${GREEN}✓${NC} Tunnel started and enabled"
else
    echo -e "${RED}✗${NC} Tunnel failed to start"
    echo "Check logs with: sudo journalctl -u cloudflared -n 50"
    exit 1
fi

echo ""
echo "======================================"
echo "🎉 Setup Complete!"
echo "======================================"
echo ""
echo "Your RpiPrint service will be accessible at:"
echo "  https://$HOSTNAME"
echo ""
echo "Useful commands:"
echo "  - Check status: sudo systemctl status cloudflared"
echo "  - View logs:    sudo journalctl -u cloudflared -f"
echo "  - Restart:      sudo systemctl restart cloudflared"
echo "  - Stop:         sudo systemctl stop cloudflared"
echo ""
echo "Configuration files:"
echo "  - Config:       ~/.cloudflared/config.yml"
echo "  - Credentials:  ~/.cloudflared/$TUNNEL_ID.json"
echo ""
echo "Next steps:"
echo "  1. Install RpiPrint service: ./install_service.sh"
echo "  2. Start RpiPrint: sudo systemctl start rpiprint"
echo "  3. Access your site at: https://$HOSTNAME"
echo ""
echo "======================================"
