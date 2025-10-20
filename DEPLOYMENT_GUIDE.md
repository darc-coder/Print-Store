# 🚀 RpiPrint Production Deployment Guide

## Raspberry Pi 4 + Cloudflare Tunnel

This guide will help you deploy RpiPrint on your Raspberry Pi 4 and make it accessible from the internet using Cloudflare Tunnel.

---

## 📋 Prerequisites

- **Raspberry Pi 4** (2GB+ RAM recommended)
- **Raspbian OS** (Raspberry Pi OS Lite or Desktop)
- **Canon G3000 printer** configured with CUPS
- **Cloudflare account** (free tier works fine) - [Sign up here](https://dash.cloudflare.com/sign-up)
- **Domain name** (optional - can use free Cloudflare subdomain)
- **Internet connection** on Raspberry Pi
- **SSH access** to your Raspberry Pi

---

## 🔧 Part 1: Prepare Raspberry Pi

### 1.1 Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### 1.2 Install Required Packages

```bash
# Python and development tools
sudo apt install python3 python3-pip python3-venv git wget curl -y

# CUPS (if not already installed)
sudo apt install cups libcups2-dev -y

# Allow pi user to manage printers
sudo usermod -a -G lpadmin pi
```

### 1.3 Configure CUPS Printer

**Option A: Using Web Interface**

```bash
# Enable remote CUPS access
sudo cupsctl --remote-any
sudo systemctl restart cups

# Access CUPS web interface
# From your computer browser: http://raspberrypi.local:631
```

**Option B: Using Command Line**

```bash
# List available printers
lpinfo -v

# Add Canon G3000 printer (adjust URI as needed)
sudo lpadmin -p Canon_G3000_W -E -v usb://Canon/G3000%20series -m everywhere

# Set as default
lpoptions -d Canon_G3000_W

# Test printer options
lpoptions -p Canon_G3000_W -l

# Test print
echo "Test print from Raspberry Pi" | lp -d Canon_G3000_W
```

---

## 📥 Part 2: Deploy RpiPrint

### 2.1 Transfer Files to Raspberry Pi

**Option A: Using Git (Recommended)**

```bash
cd ~
git clone https://github.com/nitin-pt/Print-Store.git RpiPrint
cd RpiPrint
```

**Option B: Using SCP (if not using Git)**

From your Mac:

```bash
# Transfer entire project
scp -r /Users/nitin/1Py/Web/RpiPrint pi@raspberrypi.local:~/

# Or if you know the IP address
scp -r /Users/nitin/1Py/Web/RpiPrint pi@192.168.x.x:~/
```

Then SSH into Pi:

```bash
ssh pi@raspberrypi.local
cd ~/RpiPrint
```

### 2.2 Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2.3 Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install:

- Flask, Flask-SocketIO
- PyPDF2, Pillow
- PyWebPush
- And all other dependencies

### 2.4 Generate Security Keys

**Generate Secret Key:**

```bash
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
```

Copy the output.

**Generate VAPID Keys (for push notifications):**

```bash
python3 << 'EOF'
from pywebpush import webpush
import json

keys = webpush.generate_vapid_keys()
print("\nVAPID Keys (save these):")
print("=" * 50)
print(f"VAPID_PRIVATE_KEY={keys['private_key']}")
print(f"VAPID_PUBLIC_KEY={keys['public_key']}")
print("=" * 50)
EOF
```

Copy both keys.

### 2.5 Configure Environment

```bash
# Copy production template
cp .env.production .env

# Edit with your values
nano .env
```

Update these values in `.env`:

```env
# REQUIRED - Paste your generated secret key
SECRET_KEY=paste-your-generated-secret-key-here

# REQUIRED - Change admin credentials
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_secure_password

# Printer configuration
PRINTER_NAME=Canon_G3000_W
COST_PER_PAGE=5.0

# VAPID Keys (paste generated keys)
VAPID_PRIVATE_KEY=paste-your-private-key
VAPID_PUBLIC_KEY=paste-your-public-key
VAPID_EMAIL=mailto:your-email@example.com
```

Save with `Ctrl+X`, `Y`, `Enter`.

### 2.6 Initialize Database

```bash
python3 reset_db.py
# Type 'yes' when prompted
```

### 2.7 Test Application Locally

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run production server
python3 app_production.py
```

You should see:

```
======================================================================
🚀 RpiPrint Production Server
======================================================================

✅ Server Configuration:
   - Host: 0.0.0.0 (all interfaces)
   - Port: 5500
   - Debug: False
   ...
```

**Test from your computer:**

- Open browser: `http://raspberrypi.local:5500`
- Or use IP: `http://192.168.x.x:5500`

**Test the following:**

- ✅ Upload page loads
- ✅ File upload works
- ✅ Admin login works (`/admin/login`)
- ✅ Checkout page works

Press `Ctrl+C` to stop the server.

---

## 🌐 Part 3: Setup Cloudflare Tunnel

### 3.1 Create Cloudflare Account

If you don't have one:

1. Go to [dash.cloudflare.com/sign-up](https://dash.cloudflare.com/sign-up)
2. Create free account
3. Verify email

### 3.2 Prepare Domain (Optional)

**Option A: Use Your Own Domain**

1. Add domain to Cloudflare
2. Update nameservers at your registrar
3. Wait for DNS propagation (can take up to 24h)

**Option B: Use Free Cloudflare Subdomain**

- No setup needed
- Will get: `your-tunnel-name.trycloudflare.com`
- Good for testing/personal use

### 3.3 Run Cloudflare Tunnel Setup

```bash
# Make script executable
chmod +x setup_cloudflare_tunnel.sh

# Run setup script
./setup_cloudflare_tunnel.sh
```

**Follow the prompts:**

1. **Authenticate**: Browser window will open (or copy URL)

   - Login to Cloudflare
   - Authorize the tunnel

2. **Create Tunnel**: Enter a name

   - Example: `rpiprint`
   - Use lowercase, no spaces

3. **Edit Configuration**:

   ```bash
   nano ~/.cloudflared/config.yml
   ```

   Change:

   ```yaml
   - hostname: CHANGE-THIS-TO-YOUR-DOMAIN.com
   ```

   To:

   ```yaml
   - hostname: print.yourdomain.com
   ```

   Or:

   ```yaml
   - hostname: rpiprint.trycloudflare.com
   ```

4. **Configure DNS**: Enter your hostname
   - Example: `print.yourdomain.com`
   - Or: `rpiprint.trycloudflare.com`

The script will:

- ✅ Install cloudflared
- ✅ Create tunnel
- ✅ Configure DNS
- ✅ Install as system service
- ✅ Start the tunnel

### 3.4 Verify Tunnel

```bash
# Check tunnel status
sudo systemctl status cloudflared

# View logs
sudo journalctl -u cloudflared -f
```

You should see:

```
Registered tunnel connection
```

Press `Ctrl+C` to stop viewing logs.

---

## 🔄 Part 4: Install RpiPrint as Service

### 4.1 Run Installation Script

```bash
# Make script executable
chmod +x install_service.sh

# Run installation
./install_service.sh
```

The script will:

- ✅ Configure service with correct paths
- ✅ Install systemd service
- ✅ Enable auto-start on boot
- ✅ Optionally start the service

### 4.2 Start Service

If you didn't start during installation:

```bash
sudo systemctl start rpiprint
```

### 4.3 Verify Service

```bash
# Check status
sudo systemctl status rpiprint

# View logs
sudo journalctl -u rpiprint -f
```

You should see the server starting successfully.

---

## ✅ Part 5: Verify Deployment

### 5.1 Access Your Site

Open browser and go to: `https://your-domain.com`

**Replace with your actual domain!**

### 5.2 Test Functionality

1. **Upload Page**

   - ✅ Page loads with HTTPS
   - ✅ Upload a test PDF
   - ✅ Redirects to checkout

2. **Checkout Page**

   - ✅ Files appear in cart
   - ✅ Adjust copies, orientation, color mode
   - ✅ Cost calculates correctly

3. **Admin Login**

   - ✅ Go to `/admin/login`
   - ✅ Login with your credentials
   - ✅ Dashboard loads

4. **Complete Print Job**
   - ✅ Submit payment (with screenshot)
   - ✅ Wait on waiting page
   - ✅ Admin approves job
   - ✅ Printer receives job
   - ✅ Success page shows

### 5.3 Test from Different Devices

- ✅ Test on your phone (mobile data, not WiFi)
- ✅ Test from a friend's computer
- ✅ Test from different locations

---

## 🔒 Part 6: Security Hardening

### 6.1 Verify Credentials

```bash
nano .env
```

Ensure you changed:

- ✅ `SECRET_KEY` - Should be long random string
- ✅ `ADMIN_USERNAME` - Not "admin"
- ✅ `ADMIN_PASSWORD` - Strong password

After changing, restart:

```bash
sudo systemctl restart rpiprint
```

### 6.2 Enable Firewall

```bash
# Install UFW
sudo apt install ufw -y

# Allow SSH (IMPORTANT!)
sudo ufw allow ssh

# Allow CUPS web interface (optional)
sudo ufw allow 631/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

**Important:** Do NOT open port 5500 in firewall! Cloudflare tunnel handles all external access.

### 6.3 Keep System Updated

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Update Python packages
cd ~/RpiPrint
source venv/bin/activate
pip install --upgrade -r requirements.txt
deactivate

# Restart service
sudo systemctl restart rpiprint
```

---

## 📊 Part 7: Monitoring & Maintenance

### 7.1 View Logs

**Application Logs:**

```bash
# Real-time logs
sudo journalctl -u rpiprint -f

# Last 100 lines
sudo journalctl -u rpiprint -n 100

# Today's logs
sudo journalctl -u rpiprint --since today
```

**Cloudflare Tunnel Logs:**

```bash
sudo journalctl -u cloudflared -f
```

**CUPS Logs:**

```bash
tail -f /var/log/cups/error_log
```

### 7.2 Service Management

```bash
# Check status
sudo systemctl status rpiprint
sudo systemctl status cloudflared

# Restart services
sudo systemctl restart rpiprint
sudo systemctl restart cloudflared

# Stop services
sudo systemctl stop rpiprint
sudo systemctl stop cloudflared

# Start services
sudo systemctl start rpiprint
sudo systemctl start cloudflared

# Disable auto-start
sudo systemctl disable rpiprint
sudo systemctl disable cloudflared

# Re-enable auto-start
sudo systemctl enable rpiprint
sudo systemctl enable cloudflared
```

### 7.3 Database Backup

**Manual Backup:**

```bash
cd ~/RpiPrint
cp jobs.db jobs.db.backup
```

**Automated Daily Backup:**

```bash
# Create backup script
cat > ~/backup_rpiprint.sh <<'EOF'
#!/bin/bash
BACKUP_DIR=~/RpiPrint/backups
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)
cp ~/RpiPrint/jobs.db $BACKUP_DIR/jobs_$DATE.db
# Keep only last 7 days
find $BACKUP_DIR -name "jobs_*.db" -mtime +7 -delete
echo "Backup created: jobs_$DATE.db"
EOF

chmod +x ~/backup_rpiprint.sh

# Add to crontab (runs daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * ~/backup_rpiprint.sh") | crontab -
```

### 7.4 Automated File Cleanup

RpiPrint includes automatic cleanup of old files to prevent disk space issues.

**Setup Automated Cleanup:**

```bash
cd ~/RpiPrint
chmod +x setup_cleanup.sh
./setup_cleanup.sh
```

This will:

- ✅ Configure daily cleanup at 3:00 AM
- ✅ Delete completed jobs after 14 days
- ✅ Delete rejected jobs after 7 days
- ✅ Remove orphaned files after 3 days
- ✅ Log cleanup activities

**Manual Cleanup:**

```bash
# Test cleanup (dry run - no files deleted)
./cleanup_old_files.py --dry-run

# Actually run cleanup
./cleanup_old_files.py

# View cleanup logs
tail -f logs/cleanup.log
```

**Customize Cleanup Settings:**

```bash
# Edit .env file
nano .env

# Add these variables (optional):
CLEANUP_DAYS_COMPLETED=14  # Days to keep completed jobs
CLEANUP_DAYS_REJECTED=7    # Days to keep rejected jobs
CLEANUP_DAYS_ORPHANED=3    # Days to keep orphaned files
```

### 7.5 Check Disk Space

```bash
# Overall disk usage
df -h

# RpiPrint folder size
du -sh ~/RpiPrint

# Uploads folder
du -sh ~/RpiPrint/uploads

# Screenshots folder
du -sh ~/RpiPrint/screenshots

# Database size
ls -lh ~/RpiPrint/jobs.db
```

**Note:** Manual file deletion is no longer needed! Use the automated cleanup script:

````bash
# Use the cleanup script instead
./cleanup_old_files.py --dry-run  # Preview what will be deleted
./cleanup_old_files.py            # Actually delete old files
```---

## 🐛 Part 8: Troubleshooting

### Service Won't Start

```bash
# Check logs for errors
sudo journalctl -u rpiprint -n 50 --no-pager

# Common issues:
# 1. Wrong Python path
sudo systemctl cat rpiprint  # Check paths

# 2. Missing .env file
ls -la ~/RpiPrint/.env

# 3. Database permissions
ls -l ~/RpiPrint/jobs.db
chmod 664 ~/RpiPrint/jobs.db

# 4. Port already in use
sudo lsof -i :5500

# Fix: Kill process using port
sudo kill -9 $(sudo lsof -t -i :5500)
````

### Cloudflare Tunnel Not Working

```bash
# Check tunnel status
sudo systemctl status cloudflared

# View configuration
cat ~/.cloudflared/config.yml

# Verify tunnel exists
cloudflared tunnel list

# Check DNS
nslookup your-domain.com

# Test local connection
curl http://localhost:5500

# Restart tunnel
sudo systemctl restart cloudflared
```

### Can't Access Site

1. **Check if services are running:**

   ```bash
   sudo systemctl status rpiprint cloudflared
   ```

2. **Check Cloudflare DNS:**

   - Go to Cloudflare dashboard
   - Verify DNS record exists
   - Check DNS propagation: [whatsmydns.net](https://www.whatsmydns.net)

3. **Test local access:**

   ```bash
   curl http://localhost:5500
   ```

   If local works but domain doesn't → tunnel issue
   If local fails → RpiPrint issue

### Printer Not Working

```bash
# Check CUPS status
sudo systemctl status cups

# Check printer
lpstat -t

# View printer queue
lpq -a

# Test print
echo "Test" | lp -d Canon_G3000_W

# Check printer options
python3 check_printer_options.py

# View CUPS web interface
# Browser: http://raspberrypi.local:631

# Restart CUPS
sudo systemctl restart cups
```

### High CPU/Memory Usage

```bash
# Check processes
top
# Press 'q' to quit

# Check specific to RpiPrint
ps aux | grep python3

# If high CPU:
# 1. Check logs for errors
sudo journalctl -u rpiprint -n 100

# 2. Restart service
sudo systemctl restart rpiprint

# 3. Check for infinite loops in code
```

### Database Errors

```bash
# Check database integrity
cd ~/RpiPrint
source venv/bin/activate
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('jobs.db')
result = conn.execute("PRAGMA integrity_check").fetchone()
print("Database integrity:", result[0])
conn.close()
EOF

# If corrupted, restore from backup
cp jobs.db jobs.db.corrupted
cp jobs.db.backup jobs.db

# Or reset database (loses all data!)
python3 reset_db.py
```

---

## 🔄 Part 9: Updates & Maintenance

### Update Application

```bash
cd ~/RpiPrint

# Pull latest changes (if using Git)
git pull

# Or transfer new files via SCP

# Activate virtual environment
source venv/bin/activate

# Update dependencies
pip install --upgrade -r requirements.txt

# Restart service
sudo systemctl restart rpiprint

# Check logs
sudo journalctl -u rpiprint -f
```

### Update System

```bash
# Update Raspberry Pi OS
sudo apt update && sudo apt upgrade -y

# Update Python packages
cd ~/RpiPrint
source venv/bin/activate
pip list --outdated
pip install --upgrade pip
pip install --upgrade -r requirements.txt

# Update cloudflared
sudo cloudflared update

# Reboot if kernel updated
sudo reboot
```

### Rollback Changes

```bash
cd ~/RpiPrint

# If using Git
git log  # Find commit hash
git checkout <commit-hash>

# Restart service
sudo systemctl restart rpiprint
```

---

## 📱 Part 10: Mobile & Remote Access

### Access from Anywhere

Your site is accessible from:

- ✅ Any web browser (desktop, mobile, tablet)
- ✅ Any location (home, office, coffee shop)
- ✅ Any network (WiFi, mobile data)

Simply go to: `https://your-domain.com`

### Share with Users

Give users your domain:

- `https://print.yourdomain.com`

They can:

1. Upload files
2. Configure print settings
3. Pay via UPI
4. Submit payment screenshot
5. Get real-time updates

You (admin) can:

1. Login at `/admin/login`
2. Review jobs
3. Approve/reject
4. Monitor printing

---

## 💡 Part 11: Tips & Best Practices

### Security

- ✅ Use strong admin password
- ✅ Change credentials regularly
- ✅ Keep system updated
- ✅ Monitor logs for suspicious activity
- ✅ Never expose port 5500 directly

### Performance

- ✅ Clean old uploads/screenshots monthly
- ✅ Backup database weekly
- ✅ Monitor disk space
- ✅ Restart services if sluggish

### Reliability

- ✅ Keep Raspberry Pi powered 24/7
- ✅ Use stable power supply
- ✅ Ensure good WiFi signal
- ✅ Monitor printer paper/ink
- ✅ Set up backup admin account

### Monitoring

- ✅ Check logs daily for errors
- ✅ Test printing weekly
- ✅ Verify site access from mobile
- ✅ Monitor Cloudflare dashboard

---

## 📞 Part 12: Getting Help

### Check Logs First

```bash
# RpiPrint logs
sudo journalctl -u rpiprint -n 100

# Cloudflare logs
sudo journalctl -u cloudflared -n 100

# System logs
sudo journalctl -n 100
```

### Common Log Locations

- Application: `sudo journalctl -u rpiprint`
- Tunnel: `sudo journalctl -u cloudflared`
- CUPS: `/var/log/cups/error_log`
- System: `/var/log/syslog`

### Test Checklist

- [ ] Services running? `sudo systemctl status rpiprint cloudflared`
- [ ] Local access works? `curl http://localhost:5500`
- [ ] Tunnel connected? `sudo journalctl -u cloudflared | grep "Registered"`
- [ ] DNS resolves? `nslookup your-domain.com`
- [ ] Printer working? `lpstat -t`
- [ ] Firewall okay? `sudo ufw status`

---

## 🎉 Congratulations!

Your RpiPrint service is now live on the internet! 🚀

**What you have:**

- ✅ Professional print management system
- ✅ Secure HTTPS access from anywhere
- ✅ Real-time WebSocket updates
- ✅ Auto-start on boot
- ✅ Automatic tunnel reconnection
- ✅ Production-grade security
- ✅ Complete monitoring and logging

**Access your service:**

- Main site: `https://your-domain.com`
- Admin panel: `https://your-domain.com/admin/login`

**Enjoy your automated print service!** 🖨️✨

---

_For questions or issues, check the troubleshooting section or review the logs._
