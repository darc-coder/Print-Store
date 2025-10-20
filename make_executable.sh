#!/bin/bash
#
# Make all deployment scripts executable
#

echo "======================================"
echo "🔧 Making Scripts Executable"
echo "======================================"
echo ""

# Array of scripts to make executable
scripts=(
    "setup_cloudflare_tunnel.sh"
    "install_service.sh"
    "setup_cleanup.sh"
    "app_production.py"
    "cleanup_old_files.py"
    "reset_db.py"
    "check_printer_options.py"
)

# Make scripts executable
for script in "${scripts[@]}"; do
    if [ -f "$script" ]; then
        chmod +x "$script"
        echo "✅ $script"
    else
        echo "⚠️  $script (not found)"
    fi
done

echo ""
echo "======================================"
echo "✅ All scripts are now executable!"
echo "======================================"
echo ""
echo "Deployment scripts:"
echo "  - ./setup_cloudflare_tunnel.sh  (Setup Cloudflare Tunnel)"
echo "  - ./install_service.sh          (Install RpiPrint service)"
echo "  - ./setup_cleanup.sh            (Setup automated file cleanup)"
echo ""
echo "Utility scripts:"
echo "  - ./app_production.py           (Run production server)"
echo "  - ./cleanup_old_files.py        (Clean up old files)"
echo "  - ./reset_db.py                 (Reset database)"
echo "  - ./check_printer_options.py    (Check printer options)"
echo ""
echo "Next steps:"
echo "  1. Transfer files to Raspberry Pi"
echo "  2. Run: ./setup_cloudflare_tunnel.sh"
echo "  3. Run: ./install_service.sh"
echo "  4. Access your site!"
echo ""
