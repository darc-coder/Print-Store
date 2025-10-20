# ✅ RpiPrint Deployment Checklist

Use this checklist to ensure a complete and successful deployment.

---

## 📋 Pre-Deployment Preparation

### Hardware & Network

- [ ] Raspberry Pi 4 (2GB+ RAM) is ready
- [ ] Power supply connected (official 5V/3A recommended)
- [ ] MicroSD card (16GB+ recommended)
- [ ] Raspberry Pi OS installed (Lite or Desktop)
- [ ] SSH enabled on Raspberry Pi
- [ ] Canon G3000 printer connected via USB
- [ ] Printer powered on
- [ ] Pi connected to internet (WiFi or Ethernet)
- [ ] Pi has static IP or reserved DHCP (optional but recommended)

### Accounts & Access

- [ ] Cloudflare account created (free tier)
- [ ] Domain name ready OR will use free Cloudflare subdomain
- [ ] SSH access to Raspberry Pi working
- [ ] Can access Pi: `ssh pi@raspberrypi.local`

---

## 🔧 Part 1: System Preparation

### System Updates

- [ ] Ran `sudo apt update`
- [ ] Ran `sudo apt upgrade -y`
- [ ] System is up to date

### Required Packages

- [ ] Python 3 installed (`python3 --version`)
- [ ] pip installed (`pip3 --version`)
- [ ] venv installed (`python3 -m venv --help`)
- [ ] Git installed (`git --version`)
- [ ] CUPS installed (`lpstat --version`)
- [ ] wget and curl installed

### CUPS Configuration

- [ ] User added to lpadmin group: `sudo usermod -a -G lpadmin pi`
- [ ] Canon G3000 printer added to CUPS
- [ ] Printer set as default
- [ ] Test print successful: `echo "Test" | lp`
- [ ] Printer options verified: `lpoptions -p Canon_G3000_W -l`

---

## 📥 Part 2: Application Deployment

### File Transfer

- [ ] Files transferred to Pi (via Git or SCP)
- [ ] Files located at `~/RpiPrint`
- [ ] Can access directory: `cd ~/RpiPrint`
- [ ] All required files present:
  - [ ] `app.py`
  - [ ] `app_production.py`
  - [ ] `config_production.py`
  - [ ] `requirements.txt`
  - [ ] `rpiprint.service`
  - [ ] `setup_cloudflare_tunnel.sh`
  - [ ] `install_service.sh`
  - [ ] `.env.production`
  - [ ] All other application files

### Python Environment

- [ ] Virtual environment created: `python3 -m venv venv`
- [ ] Virtual environment activated: `source venv/bin/activate`
- [ ] pip upgraded: `pip install --upgrade pip`
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] No installation errors

### Configuration

- [ ] Secret key generated (32+ characters)
- [ ] VAPID keys generated
- [ ] `.env` file created from `.env.production`
- [ ] SECRET_KEY updated in `.env`
- [ ] ADMIN_USERNAME changed (not "admin")
- [ ] ADMIN_PASSWORD set to strong password
- [ ] PRINTER_NAME set to `Canon_G3000_W`
- [ ] COST_PER_PAGE set (default 5.0)
- [ ] VAPID keys added to `.env`
- [ ] VAPID_EMAIL updated

### Database

- [ ] Database initialized: `python3 reset_db.py`
- [ ] Confirmed with 'yes'
- [ ] `jobs.db` file created
- [ ] No database errors

### Local Testing

- [ ] Production server runs: `python3 app_production.py`
- [ ] Server starts without errors
- [ ] Can access locally: `http://raspberrypi.local:5500`
- [ ] Upload page loads
- [ ] File upload works
- [ ] Admin login works
- [ ] Checkout page works
- [ ] Server stopped with Ctrl+C

---

## 🌐 Part 3: Cloudflare Tunnel Setup

### Script Preparation

- [ ] Script made executable: `chmod +x setup_cloudflare_tunnel.sh`

### Tunnel Installation

- [ ] Ran `./setup_cloudflare_tunnel.sh`
- [ ] cloudflared downloaded and installed
- [ ] cloudflared version shows: `cloudflared --version`

### Authentication

- [ ] Cloudflare authentication completed
- [ ] Browser opened (or URL copied and opened)
- [ ] Logged into Cloudflare account
- [ ] Authorized the tunnel
- [ ] Success message received

### Tunnel Creation

- [ ] Tunnel name entered (e.g., "rpiprint")
- [ ] Tunnel created successfully
- [ ] Tunnel ID received and noted
- [ ] Credentials file created in `~/.cloudflared/`

### Configuration

- [ ] Config file created: `~/.cloudflared/config.yml`
- [ ] Edited config file: `nano ~/.cloudflared/config.yml`
- [ ] Hostname updated (not "CHANGE-THIS...")
- [ ] Using either:
  - [ ] Own domain: `print.yourdomain.com`
  - [ ] Or free subdomain: `rpiprint.trycloudflare.com`
- [ ] Config file saved

### DNS Configuration

- [ ] DNS configured for chosen hostname
- [ ] Tunnel route created
- [ ] DNS propagation confirmed (may take time)

### Service Installation

- [ ] cloudflared service installed
- [ ] Service enabled: `sudo systemctl enable cloudflared`
- [ ] Service started: `sudo systemctl start cloudflared`
- [ ] Service status checked: `sudo systemctl status cloudflared`
- [ ] Service shows "active (running)"
- [ ] Logs show "Registered tunnel connection"

---

## 🔄 Part 4: RpiPrint Service Installation

### Script Preparation

- [ ] Script made executable: `chmod +x install_service.sh`

### Service Installation

- [ ] Ran `./install_service.sh`
- [ ] Service file created with correct paths
- [ ] Service file installed to `/etc/systemd/system/`
- [ ] systemd daemon reloaded
- [ ] Service enabled for auto-start

### Service Start

- [ ] Service started: `sudo systemctl start rpiprint`
- [ ] Service status checked: `sudo systemctl status rpiprint`
- [ ] Service shows "active (running)"
- [ ] No errors in status output

### Service Verification

- [ ] Logs checked: `sudo journalctl -u rpiprint -n 50`
- [ ] No error messages in logs
- [ ] Server started successfully
- [ ] Listening on 0.0.0.0:5500

---

## ✅ Part 5: Functional Testing

### Remote Access

- [ ] Site accessible via HTTPS: `https://your-domain.com`
- [ ] SSL certificate valid (green padlock)
- [ ] No certificate warnings
- [ ] Page loads correctly

### Upload Functionality

- [ ] Upload page loads
- [ ] File selection works
- [ ] Drag and drop works
- [ ] Multiple file upload works
- [ ] Upload completes successfully
- [ ] Redirects to checkout

### Checkout Page

- [ ] All uploaded files appear
- [ ] File previews show
- [ ] Copies can be adjusted (1-99)
- [ ] Orientation can be changed
- [ ] Color mode can be selected (B&W / Color)
- [ ] "Set all to..." buttons work
- [ ] Cost updates in real-time
- [ ] Cart widget shows correct total

### Payment Flow

- [ ] Cart sidebar opens
- [ ] Shows all items correctly
- [ ] Total cost correct
- [ ] Payment screenshot upload works
- [ ] Form validation works (requires screenshot)
- [ ] Submit button works
- [ ] Redirects to waiting page

### Waiting Page

- [ ] Waiting page loads
- [ ] Shows "waiting for approval" message
- [ ] WebSocket connection established
- [ ] Shows admin online/offline status
- [ ] Can replace screenshot if needed

### Admin Dashboard

- [ ] Admin login page loads: `/admin/login`
- [ ] Can login with credentials
- [ ] Dashboard loads
- [ ] Pending jobs appear
- [ ] Job details show correctly:
  - [ ] Filename
  - [ ] Pages
  - [ ] Copies
  - [ ] Orientation
  - [ ] Color mode
  - [ ] Cost
- [ ] Payment screenshot viewable
- [ ] Statistics show correctly

### Print Job Flow

- [ ] Admin can approve job
- [ ] User gets real-time notification
- [ ] User redirected to success page
- [ ] Success page shows confetti
- [ ] Job status updates in real-time
- [ ] Printer receives print job
- [ ] Print job completes
- [ ] Status changes to "Completed"

### Admin Actions

- [ ] Approve works
- [ ] Reject works (with reason)
- [ ] Refund works
- [ ] Resend print works
- [ ] Status tabs work (Pending, Printing, Completed, etc.)
- [ ] Real-time updates work (no refresh needed)

### Multi-Device Testing

- [ ] Works on desktop computer
- [ ] Works on laptop
- [ ] Works on smartphone
- [ ] Works on tablet
- [ ] Works on different browsers (Chrome, Firefox, Safari)
- [ ] Works on mobile data (not just WiFi)
- [ ] Works from different locations

---

## 🔒 Part 6: Security Verification

### Credentials

- [ ] SECRET_KEY is long and random (not default)
- [ ] ADMIN_USERNAME is not "admin"
- [ ] ADMIN_PASSWORD is strong (10+ chars, mixed case, numbers, symbols)
- [ ] Can login with new credentials
- [ ] Old default credentials don't work

### Network Security

- [ ] Port 5500 NOT exposed to internet
- [ ] Firewall enabled: `sudo ufw status`
- [ ] SSH allowed in firewall
- [ ] Only necessary ports open
- [ ] All external access via Cloudflare Tunnel

### SSL/HTTPS

- [ ] Site uses HTTPS (not HTTP)
- [ ] Certificate valid
- [ ] No mixed content warnings
- [ ] Session cookies secure

---

## 📊 Part 7: Monitoring Setup

### Service Status

- [ ] Can check RpiPrint: `sudo systemctl status rpiprint`
- [ ] Can check Cloudflare: `sudo systemctl status cloudflared`
- [ ] Can check CUPS: `sudo systemctl status cups`
- [ ] All services show "active (running)"

### Log Access

- [ ] Can view RpiPrint logs: `sudo journalctl -u rpiprint -f`
- [ ] Can view Cloudflare logs: `sudo journalctl -u cloudflared -f`
- [ ] Can view CUPS logs: `tail -f /var/log/cups/error_log`
- [ ] Can view system logs: `sudo journalctl -n 100`

### Backups

- [ ] Manual backup tested: `cp jobs.db jobs.db.backup`
- [ ] Backup script created (optional)
- [ ] Automated backups configured (optional)
- [ ] Know how to restore from backup

### Automated Cleanup

- [ ] Cleanup script tested: `./cleanup_old_files.py --dry-run`
- [ ] Cleanup script setup: `./setup_cleanup.sh`
- [ ] Daily cleanup cron job configured (runs at 3 AM)
- [ ] Cleanup logs accessible: `tail -f logs/cleanup.log`
- [ ] Know how to run manual cleanup
- [ ] Cleanup settings verified:
  - [ ] Completed jobs: 14 days
  - [ ] Rejected jobs: 7 days
  - [ ] Orphaned files: 3 days

### Disk Space

- [ ] Checked disk usage: `df -h`
- [ ] Sufficient space available (>2GB free)
- [ ] Automated cleanup will prevent disk space issues
- [ ] Monitoring plan in place

---

## 🔄 Part 8: Maintenance Planning

### Regular Tasks Scheduled

- [ ] Weekly: Check logs for errors
- [ ] Weekly: Test print functionality
- [ ] Monthly: Clean old uploads/screenshots
- [ ] Monthly: Backup database
- [ ] Monthly: System updates
- [ ] Quarterly: Change admin password

### Documentation

- [ ] DEPLOYMENT_GUIDE.md reviewed
- [ ] README.md reviewed
- [ ] Know how to restart services
- [ ] Know how to view logs
- [ ] Know how to update application

### Emergency Procedures

- [ ] Know how to stop services
- [ ] Know how to restore database
- [ ] Know how to rollback updates
- [ ] Have backup admin account (optional)
- [ ] Contact information for support

---

## 📱 Part 9: User Onboarding

### Sharing Access

- [ ] Domain URL documented
- [ ] Shared with intended users
- [ ] Admin credentials securely stored
- [ ] User instructions prepared (if needed)

### User Testing

- [ ] At least one external user tested
- [ ] User could upload successfully
- [ ] User could complete payment
- [ ] User received updates
- [ ] User feedback collected

---

## 🎉 Final Verification

### Complete System Check

- [ ] Raspberry Pi running 24/7
- [ ] Both services auto-start on boot (tested)
- [ ] Site accessible from internet
- [ ] Admin panel accessible
- [ ] Printing works end-to-end
- [ ] Real-time updates working
- [ ] Push notifications working (if enabled)
- [ ] No errors in logs
- [ ] All features tested and working

### Documentation Complete

- [ ] Deployment details documented:
  - Date deployed: **\*\***\_\_\_**\*\***
  - Domain name: **\*\***\_\_\_**\*\***
  - Admin username: **\*\***\_\_\_**\*\***
  - Tunnel name: **\*\***\_\_\_**\*\***
  - Pi IP address: **\*\***\_\_\_**\*\***
- [ ] Configuration backed up
- [ ] Credentials stored securely
- [ ] Update procedure documented

---

## 📝 Post-Deployment Notes

**Date Deployed:** **\*\***\_\_\_**\*\***

**Deployed By:** **\*\***\_\_\_**\*\***

**Domain:** **\*\***\_\_\_**\*\***

**Server Location:** **\*\***\_\_\_**\*\***

**Issues Encountered:**

- ***
- ***
- ***

**Custom Configurations:**

- ***
- ***
- ***

**Next Maintenance Date:** **\*\***\_\_\_**\*\***

**Notes:**

```
_______________________________________________
_______________________________________________
_______________________________________________
_______________________________________________
```

---

## ✅ Deployment Status

**Overall Status:**

- [ ] ✅ Complete and Production Ready
- [ ] ⚠️ Complete with Minor Issues
- [ ] ❌ Incomplete - Issues to Resolve

**Sign Off:**

Deployed By: **\*\***\_\_\_**\*\*** Date: **\*\***\_\_\_**\*\***

Verified By: **\*\***\_\_\_**\*\*** Date: **\*\***\_\_\_**\*\***

---

**🎉 Congratulations on your successful deployment!**

Keep this checklist for future reference and maintenance.
