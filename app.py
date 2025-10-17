#!/usr/bin/env python3
"""
Flask Raspberry Pi Print Service - starter app (PDFs & images only)
"""
import os
import sqlite3
import uuid
import subprocess
import json
import threading
import time
import signal
import sys
import warnings
from pathlib import Path
from datetime import datetime, timedelta
from functools import wraps
from flask import (
    Flask, request, redirect, url_for, render_template, abort, jsonify, send_from_directory, session
)
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from pywebpush import webpush, WebPushException
from flask_socketio import SocketIO, emit

load_dotenv()

# Admin credentials
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

# VAPID keys for push notifications
VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY', 'BM0FyrpORkg9XWpZMf-eqGsDtjtF-OOB7D60LtmNsCfkpqqWopWkELvNSG1Vs3wUh_VRCxWiYZW3dpCCct1Mw9M')
VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY', '2h5GQNFgJNKihHFQ26ZzHqEzGTnN1aNAZ10GWYkcH7I')
VAPID_CLAIMS = {"sub": "mailto:nitinlakra123@gmail.com"}

# Storage for push subscriptions (in production, use database)
push_subscriptions = []

# Screenshot folder
SCREENSHOTS_FOLDER = Path(os.getenv('SCREENSHOTS_FOLDER', 'screenshots'))
SCREENSHOTS_FOLDER.mkdir(parents=True, exist_ok=True)

UPLOAD_FOLDER = Path(os.getenv('UPLOAD_FOLDER', 'uploads'))
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
STATIC_FOLDER = Path('static')
STATIC_FOLDER.mkdir(parents=True, exist_ok=True)
DB_PATH = Path(os.getenv('DB_PATH', 'jobs.db'))
PRINTER_NAME = os.getenv('PRINTER_NAME', 'Canon_G3000_W')  # change to your CUPS printer name
COST_PER_PAGE = float(os.getenv('COST_PER_PAGE', '5.0'))  # currency units per page
ALLOWED_EXTENSIONS = {
    'pdf',           # PDF documents
    'jpg', 'jpeg',   # JPEG images
    'png',           # PNG images
    'gif',           # GIF images
    'bmp',           # Bitmap images
    'tiff', 'tif',   # TIFF images
    'webp',          # WebP images
    'svg'            # SVG vector images
}

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize SocketIO for WebSocket support (using threading mode for Python 3.13 compatibility)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
print("✅ SocketIO initialized with threading async mode")

# Global flag to control background task
cups_monitor_running = False


@app.before_request
def make_session_permanent():
    """Make session permanent so it persists across browser sessions"""
    session.permanent = True
    # Initialize cart if not exists
    if 'cart' not in session:
        session['cart'] = []

# DB helpers

def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            filename TEXT,
            stored_path TEXT,
            pages INTEGER,
            cost REAL,
            status TEXT,
            copies INTEGER DEFAULT 1,
            orientation TEXT DEFAULT 'portrait',
            payment_screenshot TEXT,
            submitted_at TEXT,
            approved_at TEXT,
            approved_by TEXT
        )
    ''')
    con.commit()
    con.close()

init_db()


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def truncate_filename(filename: str, max_length: int = 20) -> str:
    """Smart filename truncation that preserves extension"""
    if len(filename) <= max_length:
        return filename
    
    # Get filename without extension
    last_dot_index = filename.rfind('.')
    if last_dot_index > 0:
        name = filename[:last_dot_index]
        extension = filename[last_dot_index:]
    else:
        name = filename
        extension = ''
    
    # Truncate name only, keep extension
    available_length = max_length - len(extension) - 3  # 3 for "..."
    if available_length > 0:
        return name[:available_length] + '...' + extension
    else:
        # Extension too long, truncate everything
        return filename[:max_length - 3] + '...'


# Register Jinja filter
app.jinja_env.filters['truncate_filename'] = truncate_filename


# Admin authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def count_pdf_pages(pdf_path: str) -> int:
    # Use PyPDF2 to count pages
    try:
        reader = PdfReader(pdf_path)
        return len(reader.pages)
    except Exception as e:
        app.logger.exception('PDF page count failed: %s', e)
        return 0


def save_job(job_id, filename, stored_path, pages, cost, status='pending', copies=1, orientation='portrait'):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('''INSERT INTO jobs 
                   (id, filename, stored_path, pages, cost, status, copies, orientation) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (job_id, filename, stored_path, pages, cost, status, copies, orientation))
    con.commit()
    con.close()


def update_job_print_id(job_id, print_job_id):
    """Store the CUPS print job ID for status tracking"""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    # Check if column exists, if not add it
    cur.execute("PRAGMA table_info(jobs)")
    columns = [col[1] for col in cur.fetchall()]
    if 'print_job_id' not in columns:
        cur.execute('ALTER TABLE jobs ADD COLUMN print_job_id TEXT')
    cur.execute('UPDATE jobs SET print_job_id = ? WHERE id = ?', (print_job_id, job_id))
    con.commit()
    con.close()


def update_job_status(job_id, status):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('UPDATE jobs SET status = ? WHERE id = ?', (status, job_id))
    con.commit()
    con.close()
    
    # Broadcast status update via WebSocket
    broadcast_job_update(job_id, status, f'status_changed_to_{status}')


def update_job_settings(job_id, copies, orientation):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('UPDATE jobs SET copies = ?, orientation = ? WHERE id = ?', (copies, orientation, job_id))
    con.commit()
    con.close()


def get_job(job_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    
    # Check if print_job_id and payment_screenshot columns exist
    cur.execute("PRAGMA table_info(jobs)")
    columns = [col[1] for col in cur.fetchall()]
    
    # Build SELECT query based on available columns
    base_fields = 'id, filename, stored_path, pages, cost, status, copies, orientation'
    has_print_job_id = 'print_job_id' in columns
    has_payment_screenshot = 'payment_screenshot' in columns
    
    if has_print_job_id and has_payment_screenshot:
        cur.execute(f'''SELECT {base_fields}, print_job_id, payment_screenshot 
                       FROM jobs WHERE id = ?''', (job_id,))
        row = cur.fetchone()
        print_job_id = row[8] if row and len(row) > 8 else None
        payment_screenshot = row[9] if row and len(row) > 9 else None
    elif has_print_job_id:
        cur.execute(f'''SELECT {base_fields}, print_job_id 
                       FROM jobs WHERE id = ?''', (job_id,))
        row = cur.fetchone()
        print_job_id = row[8] if row and len(row) > 8 else None
        payment_screenshot = None
    elif has_payment_screenshot:
        cur.execute(f'''SELECT {base_fields}, payment_screenshot 
                       FROM jobs WHERE id = ?''', (job_id,))
        row = cur.fetchone()
        print_job_id = None
        payment_screenshot = row[8] if row and len(row) > 8 else None
    else:
        cur.execute(f'''SELECT {base_fields} 
                       FROM jobs WHERE id = ?''', (job_id,))
        row = cur.fetchone()
        print_job_id = None
        payment_screenshot = None
    
    con.close()
    if not row:
        return None
    
    # Generate preview_url from stored_path
    filename = Path(row[2]).name if row[2] else None
    preview_url = url_for('serve_upload', filename=filename) if filename else None
    
    return dict(
        id=row[0], 
        filename=row[1], 
        stored_path=row[2], 
        pages=row[3], 
        cost=row[4], 
        status=row[5],
        copies=row[6] or 1,
        orientation=row[7] or 'portrait',
        print_job_id=print_job_id,
        payment_screenshot=payment_screenshot,
        preview_url=preview_url,  # Generated on-the-fly
        file_number=1
    )


def print_file(file_path, printer="G3000-series", copies=1, orientation="portrait"):
    """Send file to printer and return job ID if successful"""
    print(f"\n{'='*60}")
    print(f"🖨️  PRINT_FILE FUNCTION CALLED")
    print(f"{'='*60}")
    print(f"📄 File: {file_path}")
    print(f"🖨️  Printer: {printer}")
    print(f"📋 Copies: {copies}")
    print(f"📐 Orientation: {orientation}")
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"❌ ERROR: File does not exist!")
        print(f"{'='*60}\n")
        return {'success': False, 'job_id': None, 'error': 'File not found'}
    
    print(f"✅ File exists, size: {os.path.getsize(file_path)} bytes")
    
    # Send the file to CUPS using lp with options
    cmd = ['lp', '-d', printer, '-n', str(copies)]
    
    # Add orientation option
    if orientation == 'landscape':
        cmd.extend(['-o', 'landscape'])
    else:
        cmd.extend(['-o', 'portrait'])
    
    cmd.append(file_path)
    
    print(f"💻 Executing command: {' '.join(cmd)}")
    
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    print(f"📊 Return code: {proc.returncode}")
    
    if proc.returncode == 0:
        # Extract job ID from output: "request id is Canon_G3000_W-123 (1 file(s))"
        output = proc.stdout.strip()
        print(f"✅ SUCCESS!")
        print(f"📤 STDOUT: {output}")
        
        if 'request id is' in output:
            try:
                job_id = output.split('request id is ')[1].split(' ')[0]
                print(f"🎫 CUPS Job ID: {job_id}")
                print(f"{'='*60}\n")
                return {'success': True, 'job_id': job_id}
            except Exception as e:
                print(f"⚠️  Could not extract job ID: {e}")
                print(f"{'='*60}\n")
                return {'success': True, 'job_id': None}
        print(f"⚠️  No job ID in output")
        print(f"{'='*60}\n")
        return {'success': True, 'job_id': None}
    else:
        error = proc.stderr.strip()
        print(f"❌ PRINT FAILED!")
        print(f"📥 STDERR: {error}")
        print(f"{'='*60}\n")
        return {'success': False, 'job_id': None, 'error': error}


def check_print_job_status(job_id):
    """Check the status of a CUPS print job"""
    print(f"\n🔍 Checking CUPS status for job: {job_id}")
    
    if not job_id:
        print(f"❌ No job ID provided")
        return 'unknown'
    
    # First, check if job is in the ACTIVE queue (not completed)
    cmd_active = ['lpstat', '-o']
    print(f"💻 Running: {' '.join(cmd_active)}")
    
    proc_active = subprocess.run(cmd_active, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if proc_active.returncode != 0:
        print(f"❌ lpstat failed with return code {proc_active.returncode}")
        print(f"STDERR: {proc_active.stderr}")
        return 'unknown'
    
    active_output = proc_active.stdout
    print(f"📊 Active jobs output: {len(active_output)} chars")
    
    # Check if job is in active queue
    if job_id in active_output:
        print(f"✅ Job {job_id} found in ACTIVE queue")
        
        # Get detailed status with lpstat -l
        cmd_detail = ['lpstat', '-l', '-o', job_id]
        proc_detail = subprocess.run(cmd_detail, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        detail_output = proc_detail.stdout.lower()
        
        print(f"📋 Job details:\n{proc_detail.stdout}")
        
        # Check for specific status keywords
        if 'processing' in detail_output or 'printing' in detail_output:
            print(f"📋 Status: printing (actively processing)")
            return 'printing'
        elif 'pending' in detail_output or 'held' in detail_output or 'waiting' in detail_output:
            print(f"📋 Status: pending (waiting in queue)")
            return 'pending'
        else:
            # Job is in active queue but no specific status - assume printing
            print(f"📋 Status: printing (in active queue)")
            return 'printing'
    else:
        print(f"❌ Job {job_id} NOT in active queue")
        
        # Job not in active queue - check completed jobs
        cmd_completed = ['lpstat', '-W', 'completed', '-o']
        print(f"💻 Running: {' '.join(cmd_completed)}")
        
        proc_completed = subprocess.run(cmd_completed, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        completed_output = proc_completed.stdout
        
        if proc_completed.returncode == 0 and job_id in completed_output:
            print(f"✅ Job {job_id} found in COMPLETED jobs")
            print(f"📋 Status: completed")
            return 'completed'
        else:
            print(f"ℹ️  Job {job_id} not found in completed jobs either")
            print(f"📋 Status: completed (assumed - not in any queue)")
            # Job not found anywhere - assume completed
            return 'completed'


# Cart management helpers
def get_cart_jobs():
    """Get all job IDs from the current session cart"""
    return session.get('cart', [])


def add_to_cart(job_id):
    """Add a job ID to the session cart"""
    cart = session.get('cart', [])
    if job_id not in cart:
        cart.append(job_id)
        session['cart'] = cart


def remove_from_cart(job_id):
    """Remove a job ID from the session cart"""
    cart = session.get('cart', [])
    if job_id in cart:
        cart.remove(job_id)
        session['cart'] = cart


def clear_cart():
    """Clear all items from the cart"""
    session['cart'] = []


def get_cart_summary():
    """Get summary of all jobs in cart"""
    cart_job_ids = get_cart_jobs()
    jobs = []
    total_pages = 0
    total_cost = 0
    
    for job_id in cart_job_ids:
        job = get_job(job_id)
        if job:
            jobs.append(job)
            copies = job.get('copies', 1)
            total_pages += job['pages'] * copies
            # job['cost'] already includes copies, so don't multiply again
            total_cost += job['cost']
    
    return {
        'jobs': jobs,
        'total_pages': total_pages,
        'total_cost': total_cost,
        'count': len(jobs)
    }


# Helper functions for admin
def get_time_ago(timestamp_str):
    """Convert timestamp to human-readable 'time ago' format"""
    if not timestamp_str:
        return "Just now"
    
    try:
        timestamp = datetime.fromisoformat(timestamp_str)
        now = datetime.now()
        diff = now - timestamp
        
        seconds = diff.total_seconds()
        if seconds < 60:
            return f"{int(seconds)} seconds ago"
        elif seconds < 3600:
            return f"{int(seconds / 60)} minutes ago"
        elif seconds < 86400:
            return f"{int(seconds / 3600)} hours ago"
        else:
            return f"{int(seconds / 86400)} days ago"
    except:
        return "Recently"


def send_push_notification(title, body, url='/admin', job_id=None):
    """Send push notification to all subscribed admins"""
    print(f"📧 Attempting to send notification: {title} - {body}")
    print(f"📊 Active subscriptions: {len(push_subscriptions)}")
    
    if len(push_subscriptions) == 0:
        print("⚠️  No subscriptions found. Admin needs to enable notifications.")
        return
    
    notification_data = {
        'title': title,
        'body': body,
        'url': url,
        'job_id': job_id,
        'icon': '/static/assets/nitzInc.png'
    }
    
    for i, subscription in enumerate(push_subscriptions):
        try:
            print(f"📤 Sending to subscription {i+1}/{len(push_subscriptions)}...")
            webpush(
                subscription_info=subscription,
                data=json.dumps(notification_data),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS
            )
            print(f"✅ Notification sent successfully!")
        except WebPushException as e:
            print(f"❌ WebPushException: {e}")
            print(f"Response: {e.response if hasattr(e, 'response') else 'No response'}")
            # Remove invalid subscriptions
            if hasattr(e, 'response') and e.response and e.response.status_code == 410:
                push_subscriptions.remove(subscription)
                print(f"🗑️  Removed invalid subscription")
        except Exception as e:
            print(f"❌ Unexpected error sending notification: {type(e).__name__}: {e}")
            print(f"Subscription data: {subscription}")


@app.route('/')
def index():
    # Don't clear cart - let users navigate freely
    # Cart will be cleared only after successful payment completion
    response = render_template('upload.jinja')
    # Prevent caching so back button works properly
    response = app.make_response(response)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/sw.js')
def service_worker():
    """Serve service worker from root to have proper scope"""
    return send_from_directory('.', 'sw.js', mimetype='application/javascript')


@app.route('/upload', methods=['POST'])
def upload():
    # Handle multiple files
    files = request.files.getlist('file')
    
    if not files or len(files) == 0:
        abort(400, 'no file part')
    
    uploaded_count = 0
    for file in files:
        if file.filename == '':
            continue
        if not allowed_file(file.filename):
            continue
        
        filename = secure_filename(file.filename)
        unique_id = uuid.uuid4().hex
        saved_name = f"{unique_id}_{filename}"
        saved_path = UPLOAD_FOLDER / saved_name
        file.save(saved_path)

        # Determine page count
        ext = filename.rsplit('.', 1)[1].lower()
        pages = 0
        stored_for_print = str(saved_path)

        if ext == 'pdf':
            pages = count_pdf_pages(str(saved_path))
        else:
            # Images: treat as single-page documents
            pages = 1

        cost = pages * COST_PER_PAGE

        job_id = unique_id
        
        save_job(job_id, filename, stored_for_print, pages, cost, 
                 status='awaiting_payment')
        
        # Add to cart
        add_to_cart(job_id)
        uploaded_count += 1
    
    if uploaded_count == 0:
        abort(400, 'no valid files uploaded')

    return redirect(url_for('checkout'))


@app.route('/checkout')
def checkout():
    cart_summary = get_cart_summary()
    if cart_summary['count'] == 0:
        return redirect(url_for('index'))
    response = render_template('checkout.jinja', cart=cart_summary)
    # Prevent caching so back button works properly
    response = app.make_response(response)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/cart/remove/<job_id>', methods=['POST'])
def remove_from_cart_route(job_id):
    """Remove a file from the cart"""
    remove_from_cart(job_id)
    return redirect(url_for('checkout'))


@app.route('/checkout/process', methods=['POST'])
def process_checkout():
    """Process all jobs in cart with their settings"""
    cart_job_ids = get_cart_jobs()
    if not cart_job_ids:
        return redirect(url_for('index'))
    
    # Update settings for each job based on form data
    for job_id in cart_job_ids:
        copies = int(request.form.get(f'copies_{job_id}', 1))
        orientation = request.form.get(f'orientation_{job_id}', 'portrait')
        
        # Update job settings
        update_job_settings(job_id, copies, orientation)
        
        # Recalculate cost based on copies
        job = get_job(job_id)
        if job:
            # Get base cost (cost per page * pages)
            base_cost = job['pages'] * COST_PER_PAGE
            new_cost = base_cost * copies
            
            # Update cost in database
            con = sqlite3.connect(DB_PATH)
            cur = con.cursor()
            cur.execute('UPDATE jobs SET cost = ? WHERE id = ?', (new_cost, job_id))
            con.commit()
            con.close()
    
    # Redirect to payment page with QR code
    return redirect(url_for('payment_page'))


@app.route('/uploads/<filename>')
def serve_upload(filename):
    """Serve uploaded files for preview"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/simulate_pay_cart', methods=['POST', 'GET'])
def simulate_pay_cart():
    """Simulate payment for all jobs in cart"""
    cart_job_ids = get_cart_jobs()
    if not cart_job_ids:
        return redirect(url_for('index'))
    
    # Process all jobs in cart
    for job_id in cart_job_ids:
        job = get_job(job_id)
        if job:
            # Mark paid
            update_job_status(job_id, 'paid')
            # Trigger printing with settings
            success = print_file(job['stored_path'], 
                                copies=job.get('copies', 1),
                                orientation=job.get('orientation', 'portrait'))
            update_job_status(job_id, 'printing' if success else 'error')
    
    # Don't clear cart in old flow - it's handled in success page now
    first_job_id = cart_job_ids[0] if cart_job_ids else None
    
    # Redirect to waiting page (old flow compatibility)
    if first_job_id:
        return redirect(url_for('waiting_page', job_ids=first_job_id))
    return redirect(url_for('index'))


@app.route('/simulate_pay/<job_id>', methods=['POST'])
def simulate_pay(job_id):
    # Simple simulated payment endpoint for testing
    job = get_job(job_id)
    if not job:
        abort(404)
    # Mark paid
    update_job_status(job_id, 'paid')
    # Trigger printing with settings
    success = print_file(job['stored_path'], 
                        copies=job.get('copies', 1),
                        orientation=job.get('orientation', 'portrait'))
    update_job_status(job_id, 'printing' if success else 'error')
    return redirect(url_for('waiting_page', job_ids=job_id))


# Removed old status route - now using waiting_page with real-time updates

# Example webhook endpoint placeholder for payment gateways
@app.route('/payment_webhook', methods=['POST'])
def payment_webhook():
    data = request.json or {}
    # TODO: verify signature from gateway
    job_id = data.get('job_id')
    paid = data.get('paid')
    if not job_id:
        return jsonify({'error': 'no job_id'}), 400
    if paid:
        update_job_status(job_id, 'paid')
        job = get_job(job_id)
        if job:
            success = print_file(job['stored_path'])
            update_job_status(job_id, 'printing' if success else 'error')
    return jsonify({'ok': True})


# ============= NEW PAYMENT & ADMIN ROUTES =============

@app.route('/payment', methods=['GET', 'POST'])
def payment_page():
    """Redirect to waiting page for screenshot upload"""
    cart_summary = get_cart_summary()
    if cart_summary['count'] == 0:
        return redirect(url_for('index'))
    
    cart_job_ids = get_cart_jobs()
    jobs = cart_summary['jobs']
    total_pages = cart_summary['total_pages']
    total_cost = cart_summary['total_cost']
    
    return render_template('waiting.jinja', 
                          job_ids=cart_job_ids, 
                          jobs=jobs,
                          total_pages=total_pages,
                          total_cost=total_cost)


@app.route('/submit-payment', methods=['POST'])
def submit_payment():
    """Handle payment screenshot upload and submission"""
    job_ids = request.form.getlist('job_ids[]')
    
    if not job_ids:
        return redirect(url_for('index'))
    
    # Handle screenshot upload
    screenshot = request.files.get('screenshot')
    screenshot_path = None
    
    if screenshot and screenshot.filename:
        filename = secure_filename(screenshot.filename)
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        screenshot_path = SCREENSHOTS_FOLDER / unique_name
        screenshot.save(screenshot_path)
    
    # Update all jobs with screenshot and status
    current_time = datetime.now().isoformat()
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    
    for job_id in job_ids:
        cur.execute('''UPDATE jobs 
                       SET payment_screenshot = ?, 
                           submitted_at = ?,
                           status = 'pending_approval'
                       WHERE id = ?''',
                    (str(screenshot_path.name) if screenshot_path else None, current_time, job_id))
    
    con.commit()
    con.close()
    
    # Send push notification to admin
    print(f"\n{'='*60}")
    print(f"📸 PAYMENT SCREENSHOT SUBMITTED")
    print(f"{'='*60}")
    print(f"Job IDs: {job_ids}")
    print(f"Screenshot: {screenshot_path.name if screenshot_path else 'None'}")
    
    total_cost = sum([get_job(jid)['cost'] for jid in job_ids if get_job(jid)])
    print(f"Total cost: ₹{total_cost}")
    print(f"Sending notification to {len(push_subscriptions)} admin(s)...")
    
    send_push_notification(
        title='💰 New Payment Received!',
        body=f'{len(job_ids)} file(s) - ₹{total_cost}',
        url='/admin',
        job_id=job_ids[0]
    )
    
    print(f"{'='*60}\n")
    
    # Don't clear cart here - keep it until success page
    # User might refresh or go back during payment flow
    return redirect(url_for('waiting_page', job_ids=','.join(job_ids)))


@app.route('/waiting')
def waiting_page():
    """Waiting for approval page"""
    job_ids_str = request.args.get('job_ids', '')
    job_ids = job_ids_str.split(',') if job_ids_str else []
    
    if not job_ids:
        return redirect(url_for('index'))
    
    jobs = [get_job(jid) for jid in job_ids if get_job(jid)]
    if not jobs:
        return redirect(url_for('index'))
    
    total_pages = sum([j['pages'] * j['copies'] for j in jobs])
    total_cost = sum([j['cost'] for j in jobs])
    
    return render_template('waiting.jinja', jobs=jobs, job_ids=job_ids, 
                         total_pages=total_pages, total_cost=total_cost)


@app.route('/api/get-screenshot', methods=['POST'])
def get_screenshot():
    """API endpoint to get existing screenshot for job IDs"""
    data = request.json
    job_ids = data.get('job_ids', [])
    
    if not job_ids:
        return jsonify({'has_screenshot': False})
    
    # Check if any job has a screenshot
    for job_id in job_ids:
        job = get_job(job_id)
        if job and job.get('payment_screenshot'):
            return jsonify({
                'has_screenshot': True,
                'screenshot_url': url_for('serve_screenshot', filename=job['payment_screenshot'])
            })
    
    return jsonify({'has_screenshot': False})


@app.route('/api/job-status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """API endpoint to get individual job status"""
    job = get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    # If job has a CUPS job ID and is marked as printing, check actual status
    if job.get('print_job_id') and job['status'] == 'printing':
        actual_status = check_print_job_status(job['print_job_id'])
        if actual_status != job['status']:
            # Update status in database
            update_job_status(job_id, actual_status)
            job['status'] = actual_status
    
    return jsonify({
        'job_id': job_id,
        'status': job['status'],
        'filename': job['filename'],
        'pages': job['pages'],
        'copies': job.get('copies', 1)
    })


@app.route('/api/cart-summary', methods=['GET'])
def cart_summary_api():
    """API endpoint to get cart summary for header display"""
    summary = get_cart_summary()
    return jsonify({
        'count': summary['count'],
        'total_cost': summary['total_cost'],
        'total_pages': summary['total_pages']
    })


@app.route('/api/cart-details', methods=['GET'])
def cart_details_api():
    """API endpoint to get full cart details for sidebar"""
    summary = get_cart_summary()
    jobs_data = []
    for job in summary['jobs']:
        jobs_data.append({
            'id': job['id'],
            'filename': job['filename'],
            'pages': job['pages'],
            'cost': job['cost'],
            'copies': job.get('copies', 1),
            'orientation': job.get('orientation', 'portrait')
        })
    return jsonify({
        'jobs': jobs_data,
        'count': summary['count'],
        'total_cost': summary['total_cost'],
        'total_pages': summary['total_pages']
    })


@app.route('/api/update-cart-item', methods=['POST'])
def update_cart_item():
    """API endpoint to update cart item settings (copies, orientation)"""
    data = request.json
    job_id = data.get('job_id')
    copies = data.get('copies')
    orientation = data.get('orientation')
    
    if not job_id:
        return jsonify({'error': 'job_id required'}), 400
    
    job = get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    # Update copies and orientation if provided
    if copies is not None:
        copies = max(1, min(99, int(copies)))  # Clamp between 1-99
        update_job_settings(job_id, copies, job.get('orientation', 'portrait'))
        
        # Recalculate cost
        base_cost = job['pages'] * COST_PER_PAGE
        new_cost = base_cost * copies
        
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute('UPDATE jobs SET cost = ? WHERE id = ?', (new_cost, job_id))
        con.commit()
        con.close()
    
    if orientation is not None:
        current_copies = job.get('copies', 1)
        update_job_settings(job_id, current_copies, orientation)
    
    # Return updated cart summary
    summary = get_cart_summary()
    return jsonify({
        'success': True,
        'total_cost': summary['total_cost'],
        'total_pages': summary['total_pages']
    })


@app.route('/success')
def success_page():
    """Success page after payment approval"""
    job_ids_str = request.args.get('job_ids', '')
    job_ids = job_ids_str.split(',') if job_ids_str else []
    
    if not job_ids:
        return redirect(url_for('index'))
    
    jobs = [get_job(jid) for jid in job_ids if get_job(jid)]
    if not jobs:
        return redirect(url_for('index'))
    
    total_pages = sum([j['pages'] * j['copies'] for j in jobs])
    total_cost = sum([j['cost'] for j in jobs])
    
    # Clear the cart since payment is complete and approved
    clear_cart()
    
    return render_template('success.jinja', jobs=jobs, 
                         total_pages=total_pages, total_cost=total_cost)
    
    total_pages = sum([j['pages'] * j['copies'] for j in jobs])
    total_cost = sum([j['cost'] for j in jobs])
    
    return render_template('success.jinja', jobs=jobs, 
                         total_pages=total_pages, total_cost=total_cost)


@app.route('/serve-screenshot/<filename>')
def serve_screenshot(filename):
    """Serve payment screenshot"""
    return send_from_directory(SCREENSHOTS_FOLDER, filename)


# ============= ADMIN ROUTES =============

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember_me')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            
            # Set session expiry
            if remember:
                session.permanent = True
                app.permanent_session_lifetime = timedelta(days=7)
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin_dashboard'))
        else:
            return render_template('admin_login.jinja', error='Invalid username or password')
    
    return render_template('admin_login.jinja')


@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return redirect(url_for('admin_login'))


@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard showing all jobs"""
    # Get filter status from query parameter
    status_filter = request.args.get('status', 'pending')
    
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    
    # Build query based on filter
    if status_filter == 'pending':
        cur.execute('''SELECT * FROM jobs 
                       WHERE status = 'pending_approval' 
                       ORDER BY submitted_at DESC''')
    elif status_filter == 'printing':
        cur.execute('''SELECT * FROM jobs 
                       WHERE status = 'printing' 
                       ORDER BY approved_at DESC''')
    elif status_filter == 'completed':
        cur.execute('''SELECT * FROM jobs 
                       WHERE status IN ('completed', 'refunded') 
                       ORDER BY approved_at DESC 
                       LIMIT 50''')
    else:  # all
        cur.execute('''SELECT * FROM jobs 
                       ORDER BY submitted_at DESC 
                       LIMIT 100''')
    
    rows = cur.fetchall()
    
    jobs = []
    for row in rows:
        job_dict = dict(row)
        job_dict['time_ago'] = get_time_ago(job_dict.get('submitted_at'))
        jobs.append(job_dict)
    
    # Get statistics
    cur.execute("SELECT COUNT(*) FROM jobs WHERE status = 'pending_approval'")
    pending_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM jobs WHERE status = 'printing'")
    printing_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM jobs WHERE status IN ('completed', 'refunded')")
    completed_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM jobs WHERE DATE(submitted_at) = DATE('now')")
    today_count = cur.fetchone()[0]
    
    cur.execute("SELECT COALESCE(SUM(cost), 0) FROM jobs WHERE DATE(submitted_at) = DATE('now') AND status IN ('printing', 'completed')")
    today_revenue = cur.fetchone()[0]
    
    con.close()
    
    stats = {
        'pending': pending_count,
        'printing': printing_count,
        'completed': completed_count,
        'today': today_count,
        'revenue': int(today_revenue)
    }
    
    return render_template('admin_dashboard.jinja', 
                         jobs=jobs, 
                         stats=stats,
                         current_filter=status_filter,
                         admin_username=session.get('admin_username'),
                         vapid_public_key=VAPID_PUBLIC_KEY)


@app.route('/admin/approve/<job_id>', methods=['POST'])
@admin_required
def admin_approve(job_id):
    """Approve a job and send to printer"""
    job = get_job(job_id)
    if not job:
        abort(404)
    
    # Send to printer
    print(f"\n{'='*60}")
    print(f"🖨️  PRINTING JOB")
    print(f"{'='*60}")
    print(f"Job ID: {job_id}")
    print(f"File: {job['filename']}")
    print(f"Path: {job['stored_path']}")
    print(f"Pages: {job['pages']}")
    print(f"Copies: {job.get('copies', 1)}")
    print(f"Orientation: {job.get('orientation', 'portrait')}")
    print(f"Printer: {PRINTER_NAME}")
    print(f"{'='*60}")
    
    result = print_file(job['stored_path'], 
                        printer=PRINTER_NAME,
                        copies=job.get('copies', 1),
                        orientation=job.get('orientation', 'portrait'))
    
    if result['success']:
        print(f"✅ Print job sent successfully!")
        if result['job_id']:
            print(f"📋 CUPS Job ID: {result['job_id']}")
            # Store the CUPS job ID for status tracking
            update_job_print_id(job_id, result['job_id'])
        status = 'printing'
    else:
        print(f"❌ Print job failed!")
        if 'error' in result:
            print(f"Error: {result['error']}")
        status = 'error'
    print(f"{'='*60}\n")
    
    # Update job status
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('''UPDATE jobs 
                   SET status = ?,
                       approved_at = ?,
                       approved_by = ?
                   WHERE id = ?''',
                (status, datetime.now().isoformat(), session.get('admin_username'), job_id))
    con.commit()
    con.close()
    
    # Broadcast job status update via WebSocket
    broadcast_job_update(job_id, status, 'approved')
    
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/reject/<job_id>', methods=['POST'])
@admin_required
def admin_reject(job_id):
    """Reject a job"""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('''UPDATE jobs 
                   SET status = 'rejected',
                       approved_by = ?
                   WHERE id = ?''',
                (session.get('admin_username'), job_id))
    con.commit()
    con.close()
    
    # Broadcast job status update via WebSocket
    broadcast_job_update(job_id, 'rejected', 'rejected')
    
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/resend-print/<job_id>', methods=['POST'])
@admin_required
def admin_resend_print(job_id):
    """Resend a stuck print job"""
    job = get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    print(f"\n{'='*60}")
    print(f"🔄 RESENDING PRINT JOB")
    print(f"{'='*60}")
    print(f"Job ID: {job_id}")
    print(f"Previous Status: {job['status']}")
    print(f"Previous CUPS Job ID: {job.get('print_job_id', 'None')}")
    print(f"{'='*60}")
    
    # Resend to printer
    result = print_file(job['stored_path'], 
                        printer=PRINTER_NAME,
                        copies=job.get('copies', 1),
                        orientation=job.get('orientation', 'portrait'))
    
    if result['success']:
        print(f"✅ Print job resent successfully!")
        if result['job_id']:
            print(f"📋 New CUPS Job ID: {result['job_id']}")
            # Update with new CUPS job ID
            update_job_print_id(job_id, result['job_id'])
        
        # Update status to printing
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute('''UPDATE jobs 
                       SET status = 'printing',
                           approved_at = ?
                       WHERE id = ?''',
                    (datetime.now().isoformat(), job_id))
        con.commit()
        con.close()
        
        print(f"✅ Status updated to 'printing'")
        print(f"{'='*60}\n")
        
        return jsonify({'success': True, 'message': 'Print job resent successfully'})
    else:
        print(f"❌ Resend failed!")
        if 'error' in result:
            print(f"Error: {result['error']}")
        print(f"{'='*60}\n")
        
        return jsonify({'success': False, 'error': result.get('error', 'Print failed')}), 500


@app.route('/admin/refund/<job_id>', methods=['POST'])
@admin_required
def admin_refund(job_id):
    """Mark a job as refunded"""
    job = get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    print(f"\n{'='*60}")
    print(f"💰 REFUNDING JOB")
    print(f"{'='*60}")
    print(f"Job ID: {job_id}")
    print(f"Filename: {job['filename']}")
    print(f"Previous Status: {job['status']}")
    print(f"Amount: ₹{job['cost']}")
    print(f"Refunded by: {session.get('admin_username')}")
    print(f"{'='*60}")
    
    # Update job status to refunded
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    
    # Add refunded_at and refunded_by columns if they don't exist
    cur.execute("PRAGMA table_info(jobs)")
    columns = [col[1] for col in cur.fetchall()]
    
    if 'refunded_at' not in columns:
        cur.execute('ALTER TABLE jobs ADD COLUMN refunded_at TEXT')
    if 'refunded_by' not in columns:
        cur.execute('ALTER TABLE jobs ADD COLUMN refunded_by TEXT')
    
    cur.execute('''UPDATE jobs 
                   SET status = 'refunded',
                       refunded_at = ?,
                       refunded_by = ?
                   WHERE id = ?''',
                (datetime.now().isoformat(), session.get('admin_username'), job_id))
    con.commit()
    con.close()
    
    print(f"✅ Job marked as refunded")
    print(f"{'='*60}\n")
    
    # Broadcast job status update via WebSocket
    broadcast_job_update(job_id, 'refunded', 'refunded')
    
    return jsonify({'success': True, 'message': 'Job marked as refunded'})


# ============================================
# WebSocket Event Handlers
# ============================================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"🔌 WebSocket client connected: {request.sid}")
    # Send current subscription status to newly connected client
    emit('subscription_status_update', {
        'connected': len(push_subscriptions) > 0,
        'count': len(push_subscriptions)
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"🔌 WebSocket client disconnected: {request.sid}")


def broadcast_subscription_status():
    """Broadcast subscription status to all connected WebSocket clients"""
    status_data = {
        'connected': len(push_subscriptions) > 0,
        'count': len(push_subscriptions)
    }
    print(f"📡 Broadcasting subscription status to all clients: {status_data}")
    # Use namespace to broadcast to all clients (no broadcast parameter needed)
    socketio.emit('subscription_status_update', status_data, namespace='/')


def broadcast_job_update(job_id, status, action='updated'):
    """Broadcast job status update to all connected admin clients"""
    job = get_job(job_id)
    if not job:
        return
    
    update_data = {
        'job_id': job_id,
        'status': status,
        'action': action,  # 'approved', 'rejected', 'refunded', 'updated'
        'job_data': {
            'id': job['id'],
            'filename': job['filename'],
            'pages': job['pages'],
            'cost': job['cost'],
            'copies': job.get('copies', 1),
            'orientation': job.get('orientation', 'portrait'),
            'status': status
        }
    }
    print(f"📡 Broadcasting job update: {job_id} - {status} ({action})")
    socketio.emit('job_status_update', update_data, namespace='/')


def monitor_cups_jobs():
    """Background task to monitor CUPS job status and broadcast updates via WebSocket"""
    global cups_monitor_running
    
    print("\n" + "="*60)
    print("🔄 CUPS Monitor Background Task Started")
    print("="*60)
    print("📊 Checking print jobs every 30 seconds...")
    print("="*60 + "\n")
    
    while cups_monitor_running:
        try:
            # Get all jobs currently marked as 'printing'
            con = sqlite3.connect(DB_PATH)
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            
            # Check if print_job_id column exists
            cur.execute("PRAGMA table_info(jobs)")
            columns = [col[1] for col in cur.fetchall()]
            
            if 'print_job_id' not in columns:
                con.close()
                # Sleep in smaller intervals to be responsive to shutdown
                for _ in range(30):
                    if not cups_monitor_running:
                        break
                    time.sleep(1)
                continue
            
            cur.execute('''SELECT id, print_job_id, status, filename FROM jobs 
                           WHERE status = 'printing' AND print_job_id IS NOT NULL''')
            printing_jobs = cur.fetchall()
            con.close()
            
            if len(printing_jobs) > 0:
                print(f"\n{'='*60}")
                print(f"🔍 CUPS Monitor Check - {datetime.now().strftime('%H:%M:%S')}")
                print(f"{'='*60}")
                print(f"📋 Found {len(printing_jobs)} job(s) in 'printing' status")
            
            # Check each printing job
            for job in printing_jobs:
                if not cups_monitor_running:
                    break
                    
                job_id = job['id']
                print_job_id = job['print_job_id']
                old_status = job['status']
                filename = job['filename']
                
                print(f"\n📄 Checking: {filename} (Job ID: {job_id[:8]}...)")
                print(f"   CUPS Job: {print_job_id}")
                print(f"   DB Status: {old_status}")
                
                # Check actual status from CUPS
                actual_status = check_print_job_status(print_job_id)
                
                print(f"   CUPS Status: {actual_status}")
                
                # If status changed, update database and broadcast
                if actual_status != old_status and actual_status != 'unknown':
                    print(f"\n✅ Status Changed: {old_status} → {actual_status}")
                    update_job_status(job_id, actual_status)
                    print(f"📡 Broadcasting update to all connected clients...")
                    # Note: update_job_status already calls broadcast_job_update
                elif actual_status == old_status:
                    print(f"   ℹ️  No change (still {actual_status})")
            
            if len(printing_jobs) > 0:
                print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"\n❌ Error in CUPS monitor: {e}")
        
        # Wait 30 seconds before next check, but check shutdown flag every second
        for _ in range(30):
            if not cups_monitor_running:
                break
            time.sleep(1)
    
    print("\n🛑 CUPS Monitor Background Task Stopped\n")


def start_cups_monitor():
    """Start the CUPS monitoring background task"""
    global cups_monitor_running
    
    if not cups_monitor_running:
        cups_monitor_running = True
        monitor_thread = threading.Thread(target=monitor_cups_jobs, daemon=True)
        monitor_thread.start()
        print("✅ CUPS monitoring thread started")


def stop_cups_monitor():
    """Stop the CUPS monitoring background task"""
    global cups_monitor_running
    cups_monitor_running = False
    print("🛑 CUPS monitoring thread stopping...")


# ============================================
# Push Notification Endpoints
# ============================================

@app.route('/admin/subscribe', methods=['POST'])
@admin_required
def admin_subscribe():
    """Subscribe to push notifications"""
    subscription = request.json
    endpoint = subscription.get('endpoint', 'unknown')
    
    print(f"📱 Subscription request received: {endpoint[:50]}...")
    
    # Check for duplicate subscriptions by endpoint
    existing = False
    for sub in push_subscriptions:
        if sub.get('endpoint') == endpoint:
            existing = True
            print(f"ℹ️  Subscription already exists (duplicate prevented)")
            break
    
    # Add subscription if not duplicate
    if not existing:
        push_subscriptions.append(subscription)
        print(f"✅ New subscription added. Total subscriptions: {len(push_subscriptions)}")
        # Broadcast update to all connected WebSocket clients
        broadcast_subscription_status()
    
    return jsonify({'success': True, 'message': 'Subscribed' if not existing else 'Already subscribed'})


@app.route('/test-notifications')
def test_notifications():
    """Test page for push notifications"""
    return render_template('test_notifications.jinja')


@app.route('/test-simple-notification')
def test_simple_notification():
    """Simple notification test without service worker"""
    return render_template('test_simple_notification.html')


@app.route('/api/test-notification', methods=['POST'])
def api_test_notification():
    """API endpoint to send a test notification"""
    data = request.json or {}
    title = data.get('title', '🧪 Test Notification')
    body = data.get('body', 'This is a test notification!')
    
    print(f"\n{'='*60}")
    print(f"🧪 TEST NOTIFICATION REQUEST")
    print(f"{'='*60}")
    print(f"Title: {title}")
    print(f"Body: {body}")
    print(f"Active subscriptions: {len(push_subscriptions)}")
    print(f"{'='*60}\n")
    
    if len(push_subscriptions) == 0:
        print("❌ No subscriptions found!")
        return jsonify({'success': False, 'error': 'No subscriptions found'}), 400
    
    send_push_notification(title, body, url='/admin')
    
    return jsonify({'success': True, 'message': 'Notification sent'})


@app.route('/api/resend-notification', methods=['POST'])
def api_resend_notification():
    """API endpoint to resend notification for pending payment"""
    data = request.json or {}
    job_ids = data.get('job_ids', [])
    
    if not job_ids:
        return jsonify({'success': False, 'error': 'No job IDs provided'}), 400
    
    print(f"\n{'='*60}")
    print(f"🔔 RESEND NOTIFICATION REQUEST")
    print(f"{'='*60}")
    print(f"Job IDs: {job_ids}")
    
    # Calculate total cost
    total_cost = sum([get_job(jid)['cost'] for jid in job_ids if get_job(jid)])
    print(f"Total cost: ₹{total_cost}")
    print(f"Active subscriptions: {len(push_subscriptions)}")
    
    if len(push_subscriptions) == 0:
        print("❌ No subscriptions found!")
        return jsonify({'success': False, 'error': 'No admin subscriptions available'}), 400
    
    # Send notification
    send_push_notification(
        title='🔔 Payment Reminder!',
        body=f'{len(job_ids)} file(s) waiting for approval - ₹{total_cost}',
        url='/admin',
        job_id=job_ids[0]
    )
    
    print(f"✅ Resend notification sent!")
    print(f"{'='*60}\n")
    
    return jsonify({'success': True, 'message': 'Notification resent successfully'})


@app.route('/api/update-print-status/<job_id>', methods=['POST'])
@admin_required
def update_print_status(job_id):
    """Check and update the actual print job status from CUPS"""
    job = get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    print_job_id = job.get('print_job_id')
    if not print_job_id:
        return jsonify({'status': job['status'], 'message': 'No print job ID found'})
    
    # Check actual status from CUPS
    actual_status = check_print_job_status(print_job_id)
    
    print(f"📊 Status check for {job_id}: CUPS={actual_status}, DB={job['status']}")
    
    # Update database if status changed
    if actual_status != job['status'] and actual_status != 'unknown':
        update_job_status(job_id, actual_status)
        print(f"✅ Updated status to: {actual_status}")
    
    return jsonify({
        'job_id': job_id,
        'print_job_id': print_job_id,
        'status': actual_status,
        'previous_status': job['status']
    })


if __name__ == '__main__':
    # Signal handler for graceful shutdown
    def signal_handler(sig, frame):
        print("\n\n" + "="*60)
        print("🛑 Shutdown signal received (Ctrl+C)")
        print("="*60)
        print("⏳ Stopping CUPS monitor...")
        stop_cups_monitor()
        print("✅ CUPS monitor stopped")
        print("⏳ Shutting down server...")
        print("="*60 + "\n")
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    init_db()
    
    print("\n" + "="*60)
    print("🚀 Starting Flask-SocketIO server...")
    print("="*60)
    print(f"📡 WebSocket support enabled")
    print(f"🌐 Server: http://0.0.0.0:5500")
    print(f"🔧 Mode: Development (debug=True)")
    print(f"⚡ Async mode: threading")
    print("="*60 + "\n")
    
    # Start CUPS monitoring background task ONLY in main process
    # Flask debug mode spawns a reloader process - we only want monitor in the main worker
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        start_cups_monitor()
    else:
        print("ℹ️  Skipping CUPS monitor in reloader process")
    
    try:
        socketio.run(app, host='0.0.0.0', port=5500, debug=True, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        signal_handler(None, None)