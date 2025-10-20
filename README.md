# RpiPrint

A modern web-based print service with **WebSocket real-time updates**, persistent shopping cart, **B&W and Color printing**, payment screenshot verification, admin dashboard, and automated CUPS print monitoring. Built with Flask-SocketIO for instant status updates without polling. Features a **modular blueprint architecture** for maintainability and scalability.

## ✨ Key Features

### 🔴 Real-Time Updates (WebSocket)

- **Instant notifications** - No polling, true WebSocket bidirectional communication
- **Live status updates** - See print job changes immediately
- **Admin presence** - Users see when admin is online/offline
- **Auto-reconnect** - Socket.IO handles connection drops gracefully
- **Background monitoring** - Server checks CUPS every 30 seconds

### 📤 Smart File Upload

- **Multi-file support** - Upload multiple PDFs and images at once
- **Drag & drop** - Intuitive file selection
- **Format support** - PDF, JPG, PNG, GIF, BMP, TIFF, WebP, SVG
- **Real-time preview** - See your files before printing

### 🛒 Persistent Shopping Cart

- **Session-based cart** - Never lose your files (7-day persistence)
- **Floating cart widget** - Horizontal layout: 🛒 | 1 item | ₹50
- **Real-time sync** - Settings update across all pages
- **Smart navigation** - Browser back/forward buttons work correctly

### 🎨 Color & B&W Printing

- **Print mode selection** - Choose Black & White or Color for each file
- **Visual indicators** - Grayscale/CMYK icons for easy identification
- **Bulk settings** - Apply color mode to all files at once
- **Same pricing** - ₹5/page for both B&W and Color
- **Canon G3000 support** - Uses printer-specific CNIJGrayScale option
- **Admin visibility** - Dashboard shows each job's color mode

### ⚙️ Advanced Print Settings

- **Copies** - 1-99 copies per job with instant cost updates
- **Orientation** - Portrait or Landscape
- **Color Mode** - Black & White or Color printing
- **Copy indicator** - Visual badges showing "×20" for multiple copies
- **Page calculation** - Clear breakdown: "10 pages × 20 copies = 200 pages"

### 💳 Payment Flow

- **UPI QR Code** - Scan and pay with any UPI app
- **Screenshot upload** - Submit payment proof with validation
- **Replace screenshot** - Can update screenshot if wrong file uploaded
- **Waiting page** - Real-time WebSocket updates (no manual refresh)
- **Success page** - Beautiful confetti animation with live status tracking

### 🔐 Admin Dashboard

- **Real-time job updates** - New jobs appear instantly without refresh
- **Approve/Reject/Refund** - One-click actions with WebSocket broadcast
- **Status tabs** - Pending, Printing, Completed, Rejected, Refunded, All
- **Live stats** - Today's jobs, revenue, pending count
- **Push notifications** - Browser alerts for new submissions
- **Screenshot viewer** - View payment proof before approval

### 🎯 Smart Features

- **Zero polling** - Eliminated all manual status checking
- **CUPS integration** - Automatic print job monitoring via lpstat
- **Responsive shutdown** - Graceful Ctrl+C with signal handlers
- **Thread safety** - Single background monitor in debug mode
- **Modular architecture** - Clean code organization with blueprints
- **Enhanced status display** - 7 status types with emoji icons
- **Form validation** - Dynamic required attributes for file inputs

## 🚀 Quick Start

### Prerequisites

- **Python 3.13+** (tested on 3.13.3)
- **CUPS** printer configured (or testing without actual printer)
- **Modern web browser** with WebSocket support

### Installation

1. **Clone and navigate:**

```bash
cd /path/to/RpiPrint
```

2. **Create virtual environment:**

```bash
python3 -m venv venv
source venv/bin/activate # On macOS/Linux
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Configure (optional):**
   Create `.env` file:

```env
SECRET_KEY=your-secret-key-change-in-production
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
PRINTER_NAME=Canon_G3000_W
COST_PER_PAGE=5.0
```

5. **Initialize database (first run only):**

```bash
python app.py
# Database will be created automatically
# If you need to reset: python reset_db.py
```

6. **Run the server:**

```bash
python app.py
```

Server starts on:

- **http://localhost:5500**
- **http://192.168.0.116:5500** (local network access)

7. **Access:**

- **Main app:** http://localhost:5500
- **Admin login:** http://localhost:5500/admin/login
- **Test notifications:** http://localhost:5500/test-notifications

## 🛠️ Utility Scripts

### Database Reset

Reset the database to apply schema updates or start fresh:

```bash
python reset_db.py
```

⚠️ **Warning:** This will delete all existing jobs and reset the database!

### Check Printer Options

Test your CUPS printer to discover available options:

```bash
python check_printer_options.py
```

Outputs all available CUPS options for the configured printer, including color modes, paper sizes, and quality settings.

### Automated File Cleanup

Prevent disk space issues with automatic cleanup:

```bash
# Setup automated daily cleanup (runs at 3 AM)
./setup_cleanup.sh

# Manual cleanup (test first with dry run)
./cleanup_old_files.py --dry-run
./cleanup_old_files.py
```

**What gets cleaned:**

- Completed jobs after 14 days
- Rejected jobs after 7 days
- Orphaned files after 3 days

⚠️ **Warning:** This permanently deletes old files to save disk space!

## 📋 User Flow

### 1. Upload Files

```
Home (/) → Upload/Drag files → Auto-redirect to checkout
```

- Select multiple files or drag & drop
- Supports PDF and image formats
- Files saved to persistent cart (7 days)
- Cart widget appears with item count

### 2. Configure Settings

```
Checkout (/checkout) → Adjust copies/orientation/color mode → See real-time price
```

- Change copies: 1-99
- Select orientation: Portrait/Landscape
- Choose color mode: Black & White or Color
- Set all files to same color mode with one click
- Instant cost calculation
- Visual "×20" badges for multiple copies

### 3. Pay & Submit Proof

```
Click Cart → Scan UPI QR → Pay → Upload screenshot → Submit
```

- Cart sidebar shows all items with bill breakdown
- Upload payment screenshot (required)
- Form validation ensures screenshot is uploaded
- Auto-redirect to waiting page

### 4. Wait for Approval (Real-Time)

```
Waiting (/waiting) → WebSocket updates → Auto-redirect on approval
```

- **No polling** - Instant WebSocket notifications
- Shows admin online/offline status
- Can replace screenshot if needed
- Auto-redirects to success page when approved
- Or shows rejection reason with retry button

### 5. Success & Print

```
Success (/success) → Confetti animation → Live print status → Receipt
```

- Beautiful confetti animation
- Real-time print status updates via WebSocket:
  - 🕒 Pending
  - ✅ Approved
  - 🖨️ Printing
  - ✅ Completed
  - ❌ Error
  - 🚫 Rejected
  - 💰 Refunded
- Order details with job IDs
- Print receipt option
- Auto-redirect to home after 30s when all jobs complete

## 🔧 Admin Workflow

### 1. Login

```
/admin/login → Enter credentials → Dashboard
```

### 2. Review Jobs (Real-Time)

```
Dashboard (/admin) → Pending tab → New jobs appear instantly
```

- See all pending jobs without refresh
- WebSocket updates when new jobs submitted
- View uploaded payment screenshot
- Check job details (pages, copies, cost, **color mode**)
- Visual color mode indicator (🎨 Black & White / Color)

### 3. Approve/Reject/Refund

```
Click Approve → Instant WebSocket broadcast → Print with color mode → User sees success page
```

- **Approve** - Job sent to CUPS printer with correct color settings
- **Reject** - User sees rejection with retry button
- **Refund** - Admin can refund completed jobs
- **Resend Print** - Reprint job with original color mode
- Instant user notification via WebSocket
- Push notification sent to admin for new jobs

### 4. Track Status

```
Tabs: Pending | Printing | Completed | Rejected | Refunded | All
```

- Filter by status
- Real-time statistics
- Time tracking ("5 minutes ago")
- Screenshot preview modal

## 🏗️ Architecture

### Tech Stack

**Backend:**

- **Flask 2.3.2** - Web framework
- **Flask-SocketIO 5.3.4** - WebSocket support (threading async mode)
- **Python-SocketIO 5.9.0** - WebSocket engine
- **SQLite3** - Database
- **PyPDF2 3.0.1** - PDF processing
- **PyWebPush 2.0.1** - Browser push notifications (Python 3.13 compatible)
- **Python 3.13.3** - Runtime

**Frontend:**

- **Socket.IO 4.5.4 client** - WebSocket client library
- **Vanilla JavaScript** - No frameworks
- **CSS3** - Modern styling with animations
- **Service Worker** - Push notifications

**System:**

- **CUPS** - Print system (lpstat, lp commands)
- **Canon G3000** - Target printer with CNIJGrayScale support
- **macOS** - Development environment (compatible with Linux)

### WebSocket Events

**Client → Server:**

- `connect` - Client connects to WebSocket
- `disconnect` - Client disconnects

**Server → Client:**

- `subscription_status_update` - Admin online/offline status
  ```json
  { "isSubscribed": true }
  ```
- `job_status_update` - Job status changed
  ```json
  {
    "jobId": "abc123",
    "status": "approved",
    "job": {
      /* full job object */
    }
  }
  ```

### Background Tasks

**CUPS Monitor Thread:**

- Runs in main worker process only (`WERKZEUG_RUN_MAIN` check)
- Checks every 30 seconds for jobs with `status='printing'`
- Uses `lpstat` to query CUPS job status
- Updates database and broadcasts via WebSocket when status changes
- Graceful shutdown with signal handlers (SIGINT, SIGTERM)
- Sleeps in 1-second chunks for responsive shutdown

### Routes

#### Public Routes (user_bp)

| Route                      | Method | Description                         |
| -------------------------- | ------ | ----------------------------------- |
| `/`                        | GET    | Upload page (home)                  |
| `/upload`                  | POST   | Upload files to cart                |
| `/checkout`                | GET    | Cart view with settings             |
| `/payment`                 | POST   | Submit payment with screenshot      |
| `/waiting`                 | GET    | Wait for admin approval (WebSocket) |
| `/success`                 | GET    | Success page with print status      |
| `/get-screenshot/<job_id>` | GET    | View payment screenshot             |
| `/uploads/<filename>`      | GET    | Serve uploaded files                |

#### Admin Routes (admin_bp - `/admin` prefix)

| Route                        | Method   | Description                      |
| ---------------------------- | -------- | -------------------------------- |
| `/admin/login`               | GET/POST | Admin login                      |
| `/admin/logout`              | GET      | Admin logout                     |
| `/admin`                     | GET      | Admin dashboard                  |
| `/admin/approve`             | POST     | Approve job + CUPS print         |
| `/admin/reject`              | POST     | Reject job + WebSocket broadcast |
| `/admin/refund`              | POST     | Refund job + WebSocket broadcast |
| `/admin/resend-print`        | POST     | Resend print to CUPS             |
| `/admin/update-print-status` | POST     | Update CUPS job status           |

#### API Endpoints (api_bp - `/api` prefix)

| Endpoint                | Method | Description                          |
| ----------------------- | ------ | ------------------------------------ |
| `/api/cart-summary`     | GET    | Cart count and total cost            |
| `/api/cart-details`     | GET    | Full cart with all items             |
| `/api/update-cart-item` | POST   | Update copies/orientation/color mode |
| `/api/job-status`       | POST   | Get job status by IDs                |
| `/api/get-screenshot`   | GET    | Get screenshot base64                |
| `/api/subscribe`        | POST   | Subscribe to push notifications      |
| `/api/unsubscribe`      | POST   | Unsubscribe from push                |

#### Test Routes (test_bp)

| Endpoint              | Method | Description             |
| --------------------- | ------ | ----------------------- |
| `/test-notifications` | GET    | Test push notifications |

**Removed Endpoints (obsolete polling):**

- `/api/subscription-status` ❌ Replaced by WebSocket
- `/api/check-status` ❌ Replaced by WebSocket
- `/api/check-all-printing-jobs` ❌ Replaced by background task

### Directory Structure

```
RpiPrint/
├── app.py                      # Main Flask application (modular blueprint architecture)
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── jobs.db                     # SQLite database
├── vapid.json                  # Push notification keys
├── sw.js                       # Service worker for push notifications
├── .env                        # Environment configuration (create manually)
├── reset_db.py                 # Database reset utility
├── check_printer_options.py    # CUPS printer testing tool
├── venv/                       # Virtual environment
│
├── models/                     # Database layer
│   └── database.py             # SQLite operations, schema management
│
├── utils/                      # Utility functions
│   ├── file_utils.py           # File handling, PDF processing
│   ├── print_utils.py          # CUPS printing with CNIJGrayScale
│   └── notification_utils.py   # Push notifications
│
├── services/                   # Business logic
│   ├── cart_service.py         # Session cart management
│   └── cups_monitor.py         # Background CUPS job monitoring
│
├── websocket/                  # WebSocket handlers
│   └── events.py               # SocketIO event handlers
│
├── routes/                     # HTTP endpoints (Blueprints)
│   ├── user_routes.py          # Public routes (user_bp)
│   ├── admin_routes.py         # Admin routes (admin_bp)
│   ├── api_routes.py           # API routes (api_bp)
│   └── test_routes.py          # Test routes (test_bp)
│
├── uploads/                    # Uploaded PDF/image files
├── screenshots/                # Payment screenshots
│
├── templates/                  # Jinja2 templates
│   ├── upload.jinja            # Home/upload page
│   ├── checkout.jinja          # Cart with color mode selection
│   ├── waiting.jinja           # Approval waiting (WebSocket)
│   ├── success.jinja           # Success with live status
│   ├── admin_dashboard.jinja   # Admin dashboard (WebSocket)
│   ├── admin_login.jinja       # Admin login page
│   ├── test_notifications.jinja# Push notification testing
│   └── partials/               # Reusable template components
│
├── static/
│   ├── assets/
│   │   └── drop-file.avif      # File upload illustration
│   ├── css/
│   │   ├── common.css          # Shared styles (195 lines)
│   │   ├── upload.css          # Upload page styles
│   │   ├── checkout.css        # Checkout page with color selection
│   │   ├── waiting.css         # Waiting page styles (468 lines)
│   │   ├── success.css         # Success page styles
│   │   ├── admin.css           # Admin dashboard styles
│   │   └── cart-widget.css     # Floating cart widget (125 lines)
│   └── js/
│       ├── checkout.js         # Checkout logic with color mode
│       └── cart-widget.js      # Cart widget logic
└── __pycache__/                # Python bytecode cache
```

### Modular Architecture

The application uses **Flask Blueprints** for clean separation of concerns:

- **user_bp** (`/`) - Public-facing routes
- **admin_bp** (`/admin`) - Admin-only routes with authentication
- **api_bp** (`/api`) - RESTful API endpoints
- **test_bp** (`/`) - Testing and debugging routes

**Key Benefits:**

- ✅ Easy to maintain and extend
- ✅ Clear separation of concerns
- ✅ Independent testing of modules
- ✅ Reusable components across blueprints

## 💾 Database Schema

```sql
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,                      -- Unique job ID (UUID)
    filename TEXT NOT NULL,                   -- Original filename
    stored_path TEXT NOT NULL,                -- Path to uploaded file
    pages INTEGER NOT NULL,                   -- Number of pages
    cost REAL NOT NULL,                       -- Total cost (pages × copies × rate)
    status TEXT NOT NULL,                     -- pending_approval/approved/printing/completed/rejected/refunded
    copies INTEGER DEFAULT 1,                 -- Number of copies (1-99)
    orientation TEXT DEFAULT 'portrait',      -- portrait/landscape
    print_color TEXT DEFAULT 'bw',            -- bw/color - NEW in v2.0
    payment_screenshot TEXT,                  -- Path to payment screenshot
    submitted_at TEXT NOT NULL,               -- ISO timestamp (submission)
    approved_at TEXT,                         -- ISO timestamp (approval)
    approved_by TEXT,                         -- Admin username
    rejection_reason TEXT,                    -- Reason for rejection (if any)
    print_job_id TEXT,                        -- CUPS print job ID (lpstat tracking)
    refunded_at TEXT,                         -- ISO timestamp (refund)
    refunded_by TEXT                          -- Admin who refunded
);
```

**Status Flow:**

```
pending_approval → approved → printing → completed
                 ↓ rejected (can retry)
                 ↓ refunded (admin action)
```

**Color Mode Options:**

- `bw` - Black & White (CNIJGrayScale=1)
- `color` - Color (CNIJGrayScale=0)

## �️ Printer Configuration

### Canon G3000 Series

This application is optimized for **Canon G3000** printers using CUPS on macOS/Linux.

**Color Mode Implementation:**

- Uses Canon's proprietary `CNIJGrayScale` option
- `CNIJGrayScale=1` - Black & White printing
- `CNIJGrayScale=0` - Color printing

**CUPS Print Command Example:**

```bash
lp -d Canon_G3000_W -n 1 -o portrait -o CNIJGrayScale=1 file.pdf
```

**Printer Setup:**

1. Install Canon printer drivers for your OS
2. Add printer to CUPS: `System Preferences → Printers & Scanners`
3. Note the printer name (e.g., `Canon_G3000_W`)
4. Update `PRINTER_NAME` in `.env` or `config.py`

**Testing Printer Options:**

```bash
lpoptions -p Canon_G3000_W -l  # List all available options
python check_printer_options.py  # Formatted output with highlights
```

### Other Printers

For non-Canon printers, you may need to modify `utils/print_utils.py`:

```python
# Standard CUPS color options (most printers):
if color_mode == 'bw':
    cmd.extend(['-o', 'ColorModel=Gray'])
else:
    cmd.extend(['-o', 'ColorModel=RGB'])
```

Test your printer's options first with `lpoptions -p YOUR_PRINTER -l`

---

## 🌐 Production Deployment

### Deploy to Raspberry Pi with Cloudflare Tunnel

For a complete production deployment, see **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** for detailed step-by-step instructions.

**Quick Overview:**

```bash
# On Raspberry Pi
cd ~/RpiPrint

# 1. Setup Cloudflare Tunnel
./setup_cloudflare_tunnel.sh

# 2. Install as System Service
./install_service.sh

# 3. Access from anywhere
# https://your-domain.com
```

**What You Get:**

- ✅ **Secure HTTPS** access from anywhere in the world
- ✅ **No port forwarding** needed - tunnel handles everything
- ✅ **Free SSL certificate** from Cloudflare
- ✅ **DDoS protection** and CDN
- ✅ **Auto-start on boot** - runs 24/7
- ✅ **Professional setup** with monitoring and logging
- ✅ **Own domain support** or free Cloudflare subdomain

**Deployment Files:**

| File                         | Purpose                                     |
| ---------------------------- | ------------------------------------------- |
| `DEPLOYMENT_GUIDE.md`        | Complete deployment instructions (12 parts) |
| `DEPLOYMENT_CHECKLIST.md`    | Step-by-step checklist                      |
| `app_production.py`          | Production server with security hardening   |
| `config_production.py`       | Production configuration                    |
| `setup_cloudflare_tunnel.sh` | Automated Cloudflare tunnel setup           |
| `install_service.sh`         | Service installation script                 |
| `rpiprint.service`           | Systemd service file                        |
| `.env.production`            | Production environment template             |
| `make_executable.sh`         | Makes all scripts executable                |

**System Requirements:**

- Raspberry Pi 4 (2GB+ RAM)
- Raspberry Pi OS (Lite or Desktop)
- Canon G3000 printer with CUPS
- Internet connection
- Cloudflare account (free)

**Access:**

- **Main site:** `https://your-domain.com`
- **Admin panel:** `https://your-domain.com/admin/login`
- **Works on:** Any device, any browser, anywhere in the world

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for complete instructions.

---

## 📚 Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete production deployment guide
- **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - Deployment verification checklist
- **[TRANSFER_GUIDE.md](TRANSFER_GUIDE.md)** - File transfer options to Raspberry Pi
- **[CLEANUP_GUIDE.md](CLEANUP_GUIDE.md)** - Automated file cleanup documentation
- **[MODULARIZATION_SUMMARY.md](MODULARIZATION_SUMMARY.md)** - Full details on modular architecture
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Developer quick reference guide

## 🔄 Version History

### v2.0 - Color Print Edition (Current)

- ✅ Added Black & White and Color print mode selection
- ✅ Modularized app into blueprints (models, utils, services, routes, websocket)
- ✅ Canon G3000 CNIJGrayScale support
- ✅ Enhanced database schema with `print_color` field
- ✅ Admin dashboard shows color mode for each job
- ✅ Bulk color mode setting for all files
- ✅ Database reset utility

### v1.0 - Real-Time Edition

- ✅ WebSocket real-time updates
- ✅ Persistent shopping cart
- ✅ CUPS monitoring with background task
- ✅ Admin dashboard with push notifications
- ✅ Payment screenshot verification
- ✅ Multiple copies and orientation support

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Test your changes** with actual printing
2. **Update documentation** if adding features
3. **Follow the modular structure** - use appropriate blueprints
4. **Test printer compatibility** with `check_printer_options.py`

## 📝 License

This project is for educational and personal use.

---

**Made with ❤️ for hassle-free printing | Real-Time Color Edition** 🖨️⚡🎨✨
