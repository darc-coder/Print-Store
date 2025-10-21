#!/bin/bash
# Setup autostart for RpiPrint on Raspberry Pi
# This configures the desktop environment to auto-launch RpiPrint on boot

echo "🔧 Setting up RpiPrint autostart..."

# Get the absolute path of the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "📁 Project directory: $PROJECT_DIR"

# Create autostart directory if it doesn't exist
mkdir -p ~/.config/autostart

# Create desktop entry for autostart
cat > ~/.config/autostart/rpiprint.desktop << EOF
[Desktop Entry]
Type=Application
Name=RpiPrint Server
Comment=Start RpiPrint Flask application on boot
Exec=lxterminal --title="RpiPrint Server" -e "$PROJECT_DIR/start_rpiprint.sh"
Terminal=false
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

# Make the start script executable
chmod +x "$PROJECT_DIR/start_rpiprint.sh"

echo "✅ Autostart configured!"
echo ""
echo "RpiPrint will now start automatically when you log in to the desktop."
echo ""
echo "Manual controls:"
echo "  Start now:  $PROJECT_DIR/start_rpiprint.sh"
echo "  Disable autostart:  rm ~/.config/autostart/rpiprint.desktop"
echo ""
