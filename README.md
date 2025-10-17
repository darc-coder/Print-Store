# RpiPrint

A modern web-based print service with **WebSocket real-time updates**, persistent shopping cart, payment screenshot verification, admin dashboard, and automated CUPS print monitoring. Built with Flask-SocketIO for instant status updates without polling.

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

### ⚙️ Advanced Print Settings

- **Copies** - 1-99 copies per job with instant cost updates
- **Orientation** - Portrait or Landscape
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
- **Consolidated CSS** - Shared styles in common.css (195 lines)
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
PRINTER_NAME=Canon_G3000
COST_PER_PAGE=5.0
```

5. **Run the server:**

```bash
python app.py
```

Server starts on:

- **http://localhost:5500**
- **http://192.168.0.116:5500** (local network access)

6. **Access:**

- **Main app:** http://localhost:5500
- **Admin login:** http://localhost:5500/admin/login
- **Test notifications:** http://localhost:5500/test-notifications

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
Checkout (/checkout) → Adjust copies/orientation → See real-time price
```

- Change copies: 1-99
- Select orientation: Portrait/Landscape
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
- Check job details (pages, copies, cost)

### 3. Approve/Reject/Refund

```
Click Approve → Instant WebSocket broadcast → User sees success page
```

- **Approve** - Job moves to Printing, user redirected to success
- **Reject** - User sees rejection with retry button
- **Refund** - Admin can refund completed jobs
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

#### Public Routes

| Route                      | Method | Description                         |
| -------------------------- | ------ | ----------------------------------- |
| `/`                        | GET    | Upload page (home)                  |
| `/upload`                  | POST   | Upload files to cart                |
| `/checkout`                | GET    | Cart view with settings             |
| `/payment`                 | POST   | Submit payment with screenshot      |
| `/waiting`                 | GET    | Wait for admin approval (WebSocket) |
| `/success`                 | GET    | Success page with print status      |
| `/get-screenshot/<job_id>` | GET    | View payment screenshot             |
| `/test-notifications`      | GET    | Test push notifications page        |

#### Admin Routes

| Route            | Method   | Description                       |
| ---------------- | -------- | --------------------------------- |
| `/admin/login`   | GET/POST | Admin login                       |
| `/admin/logout`  | GET      | Admin logout                      |
| `/admin`         | GET      | Admin dashboard                   |
| `/admin/approve` | POST     | Approve job + WebSocket broadcast |
| `/admin/reject`  | POST     | Reject job + WebSocket broadcast  |
| `/admin/refund`  | POST     | Refund job + WebSocket broadcast  |

#### API Endpoints

| Endpoint                | Method | Description                     |
| ----------------------- | ------ | ------------------------------- |
| `/api/cart-summary`     | GET    | Cart count and total cost       |
| `/api/cart-details`     | GET    | Full cart with all items        |
| `/api/update-cart-item` | POST   | Update copies/orientation       |
| `/api/job-status`       | POST   | Get job status by IDs           |
| `/api/get-screenshot`   | GET    | Get screenshot base64           |
| `/api/subscribe`        | POST   | Subscribe to push notifications |
| `/api/unsubscribe`      | POST   | Unsubscribe from push           |

**Removed Endpoints (obsolete polling):**

- `/api/subscription-status` ❌ Replaced by WebSocket
- `/api/check-status` ❌ Replaced by WebSocket
- `/api/check-all-printing-jobs` ❌ Replaced by background task

### Directory Structure

```
RpiPrint/
├── app.py                      # Main Flask application (1576 lines)
├── requirements.txt            # Python dependencies
├── jobs.db                     # SQLite database
├── vapid.json                  # Push notification keys
├── sw.js                       # Service worker
├── .env                        # Configuration (create manually)
├── venv/                       # Virtual environment
├── uploads/                    # Uploaded PDF/image files
├── screenshots/                # Payment screenshots
├── templates/                  # Jinja2 templates
│   ├── upload.html             # Home/upload page
│   ├── checkout.html           # Cart with payment sidebar
│   ├── waiting.html            # Approval waiting (WebSocket)
│   ├── success.html            # Success with live status
│   ├── status.html             # Print status page
│   ├── admin_dashboard.html    # Admin dashboard (WebSocket)
│   └── test_notifications.html # Push notification testing
├── static/
│   ├── css/
│   │   ├── common.css          # Shared styles (NEW - 195 lines)
│   │   ├── upload.css          # Upload page styles
│   │   ├── checkout.css        # Checkout page styles
│   │   ├── waiting.css         # Waiting page styles (468 lines)
│   │   ├── success.css         # Success page styles
│   │   ├── admin.css           # Admin dashboard styles
│   │   └── cart-widget.css     # Floating cart widget (125 lines)
│   └── js/
│       ├── checkout.js         # Checkout page logic
│       └── cart-widget.js      # Cart widget logic
└── assets/
    └── drop-file.avif          # File upload illustration
```

## 💾 Database Schema

```sql
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,           -- Unique job ID (UUID)
    filename TEXT NOT NULL,        -- Original filename
    stored_path TEXT NOT NULL,     -- Path to uploaded file
    pages INTEGER NOT NULL,        -- Number of pages
    cost REAL NOT NULL,            -- Total cost (pages × copies × rate)
    status TEXT NOT NULL,          -- pending_approval/approved/printing/completed/rejected/refunded
    copies INTEGER DEFAULT 1,      -- Number of copies (1-99)
    orientation TEXT DEFAULT 'portrait', -- portrait/landscape
    payment_screenshot TEXT,       -- Path to payment screenshot
    submitted_at TEXT NOT NULL,    -- ISO timestamp (submission)
    approved_at TEXT,              -- ISO timestamp (approval)
    approved_by TEXT,              -- Admin username
    rejection_reason TEXT,         -- Reason for rejection (if any)
    cups_job_id TEXT               -- CUPS job ID for tracking
);
```

**Status Flow:**

```
pending_approval → approved → printing → completed
                 ↓ rejected (can retry)
                 ↓ refunded (admin action)
```

---

**Made with ❤️ for hassle-free printing | Real-Time Edition** 🖨️⚡✨
