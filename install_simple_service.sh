#!/bin/bash
# Install simple RpiPrint systemd service (no complex security restrictions)

echo "🔧 Installing RpiPrint as a simple systemd service..."

# Get the absolute path of the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "📁 Project directory: $PROJECT_DIR"

# Make start script executable
chmod +x "$PROJECT_DIR/start_rpiprint.sh"

# Update service file with actual project path
sed "s|/home/pi/RpiPrint|$PROJECT_DIR|g" "$PROJECT_DIR/rpiprint-simple.service" > /tmp/rpiprint-simple.service

# Copy service file to systemd directory
echo "📋 Installing service file..."
sudo cp /tmp/rpiprint-simple.service /etc/systemd/system/rpiprint.service

# Reload systemd
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

# Enable service to start on boot
echo "✅ Enabling service to start on boot..."
sudo systemctl enable rpiprint

# Start the service
echo "🚀 Starting service..."
sudo systemctl start rpiprint

# Show status
echo ""
echo "✅ Service installed successfully!"
echo ""
echo "Service controls:"
echo "  Check status:   sudo systemctl status rpiprint"
echo "  View logs:      sudo journalctl -u rpiprint -f"
echo "  Stop service:   sudo systemctl stop rpiprint"
echo "  Start service:  sudo systemctl start rpiprint"
echo "  Restart:        sudo systemctl restart rpiprint"
echo "  Disable:        sudo systemctl disable rpiprint"
echo ""

# Show current status
sudo systemctl status rpiprint --no-pager
