# 🚀 Quick Start - Transfer to Raspberry Pi

This guide helps you transfer RpiPrint to your Raspberry Pi quickly.

---

## Option 1: Using Git (Recommended)

### On Your Mac (if not already on GitHub)

```bash
cd /Users/nitin/1Py/Web/RpiPrint

# Initialize git (if not already done)
git init
git add .
git commit -m "Production ready deployment"

# Push to GitHub
git remote add origin https://github.com/nitin-pt/Print-Store.git
git branch -M main
git push -u origin main
```

### On Your Raspberry Pi

```bash
# SSH into Pi
ssh pi@raspberrypi.local

# Clone repository
cd ~
git clone https://github.com/nitin-pt/Print-Store.git RpiPrint
cd RpiPrint

# Continue with deployment
./setup_cloudflare_tunnel.sh
```

---

## Option 2: Using SCP (Direct Transfer)

### Find Your Pi's IP Address

**On Raspberry Pi:**

```bash
hostname -I
# Example output: 192.168.1.100
```

### Transfer Files

**On Your Mac:**

```bash
# Transfer entire project
cd /Users/nitin/1Py/Web
scp -r RpiPrint pi@raspberrypi.local:~/

# Or if you know the IP address
scp -r RpiPrint pi@192.168.1.100:~/

# Enter password when prompted
```

### Verify Transfer

**SSH into Pi:**

```bash
ssh pi@raspberrypi.local

# Check files
cd ~/RpiPrint
ls -la

# Should see all files including:
# - app.py
# - app_production.py
# - setup_cloudflare_tunnel.sh
# - etc.
```

---

## Option 3: Using rsync (Best for Updates)

**On Your Mac:**

```bash
# Transfer with progress and exclude unnecessary files
rsync -avz --progress \
  --exclude 'venv' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.git' \
  --exclude 'jobs.db' \
  --exclude 'uploads/*' \
  --exclude 'screenshots/*' \
  /Users/nitin/1Py/Web/RpiPrint/ \
  pi@raspberrypi.local:~/RpiPrint/

# Or with IP address
rsync -avz --progress \
  --exclude 'venv' \
  --exclude '__pycache__' \
  /Users/nitin/1Py/Web/RpiPrint/ \
  pi@192.168.1.100:~/RpiPrint/
```

**For subsequent updates:**

```bash
# Same command - only changed files are transferred
rsync -avz --progress \
  --exclude 'venv' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.git' \
  --exclude 'jobs.db' \
  --exclude 'uploads/*' \
  --exclude 'screenshots/*' \
  /Users/nitin/1Py/Web/RpiPrint/ \
  pi@raspberrypi.local:~/RpiPrint/
```

---

## Next Steps After Transfer

```bash
# SSH into Raspberry Pi
ssh pi@raspberrypi.local

# Navigate to project
cd ~/RpiPrint

# Follow deployment guide
cat DEPLOYMENT_GUIDE.md

# Or quick start
./setup_cloudflare_tunnel.sh
./install_service.sh
```

---

## Troubleshooting

### Cannot Connect to Pi

```bash
# Try with .local domain
ping raspberrypi.local

# Or find Pi's IP on your router
# Or use IP scanner: nmap -sn 192.168.1.0/24
```

### Permission Denied

```bash
# Ensure SSH is enabled on Pi
# On Pi: sudo raspi-config
# Interface Options → SSH → Enable

# Or check SSH service
sudo systemctl status ssh
```

### Files Not Executable

```bash
# On Raspberry Pi
cd ~/RpiPrint
chmod +x *.sh *.py
```

### Wrong Ownership

```bash
# On Raspberry Pi
cd ~
sudo chown -R pi:pi RpiPrint
```

---

## Quick Command Reference

```bash
# Find Pi's IP
hostname -I  # On Pi

# Test connection
ping raspberrypi.local  # From Mac

# SSH into Pi
ssh pi@raspberrypi.local

# Check transferred files
ls -la ~/RpiPrint

# Make scripts executable
chmod +x ~/RpiPrint/*.sh ~/RpiPrint/*.py

# Start deployment
cd ~/RpiPrint
./setup_cloudflare_tunnel.sh
```

---

**Ready to deploy? See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for complete instructions!**
