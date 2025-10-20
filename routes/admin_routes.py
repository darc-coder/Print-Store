"""
Admin routes for dashboard, approval, rejection, and management
"""
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, request, redirect, url_for, render_template, session, jsonify

from config import Config
from models.database import get_job, update_job_status
from utils.print_utils import print_file, check_print_job_status
from models.database import update_job_print_id

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


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


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember_me')
        
        if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            
            # Set session expiry
            if remember:
                session.permanent = True
                from flask import current_app
                current_app.permanent_session_lifetime = timedelta(days=7)
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.dashboard'))
        else:
            return render_template('admin_login.jinja', error='Invalid username or password')
    
    return render_template('admin_login.jinja')


@admin_bp.route('/logout')
def logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return redirect(url_for('admin.login'))


@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard showing all jobs"""
    # Get filter status from query parameter
    status_filter = request.args.get('status', 'pending')
    
    con = sqlite3.connect(Config.DB_PATH)
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
                         vapid_public_key=Config.VAPID_PUBLIC_KEY)


@admin_bp.route('/approve/<job_id>', methods=['POST'])
@admin_required
def approve(job_id):
    """Approve a job and send to printer"""
    # Import here to avoid circular dependency
    from websocket.events import broadcast_job_update
    from flask import current_app
    
    job = get_job(job_id)
    if not job:
        from flask import abort
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
    print(f"Color Mode: {job.get('print_color', 'bw')}")
    print(f"Printer: {Config.PRINTER_NAME}")
    print(f"{'='*60}")
    
    result = print_file(job['stored_path'], 
                        printer=Config.PRINTER_NAME,
                        copies=job.get('copies', 1),
                        orientation=job.get('orientation', 'portrait'),
                        color_mode=job.get('print_color', 'bw'))
    
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
    con = sqlite3.connect(Config.DB_PATH)
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
    socketio = current_app.extensions.get('socketio')
    if socketio:
        broadcast_job_update(socketio, job_id, status, 'approved')
    
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/reject/<job_id>', methods=['POST'])
@admin_required
def reject(job_id):
    """Reject a job"""
    # Import here to avoid circular dependency
    from websocket.events import broadcast_job_update
    from flask import current_app
    
    con = sqlite3.connect(Config.DB_PATH)
    cur = con.cursor()
    cur.execute('''UPDATE jobs 
                   SET status = 'rejected',
                       approved_by = ?
                   WHERE id = ?''',
                (session.get('admin_username'), job_id))
    con.commit()
    con.close()
    
    # Broadcast job status update via WebSocket
    socketio = current_app.extensions.get('socketio')
    if socketio:
        broadcast_job_update(socketio, job_id, 'rejected', 'rejected')
    
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/resend-print/<job_id>', methods=['POST'])
@admin_required
def resend_print(job_id):
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
                        printer=Config.PRINTER_NAME,
                        copies=job.get('copies', 1),
                        orientation=job.get('orientation', 'portrait'),
                        color_mode=job.get('print_color', 'bw'))
    
    if result['success']:
        print(f"✅ Print job resent successfully!")
        if result['job_id']:
            print(f"📋 New CUPS Job ID: {result['job_id']}")
            # Update with new CUPS job ID
            update_job_print_id(job_id, result['job_id'])
        
        # Update status to printing
        con = sqlite3.connect(Config.DB_PATH)
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


@admin_bp.route('/refund/<job_id>', methods=['POST'])
@admin_required
def refund(job_id):
    """Mark a job as refunded"""
    # Import here to avoid circular dependency
    from websocket.events import broadcast_job_update
    from flask import current_app
    
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
    con = sqlite3.connect(Config.DB_PATH)
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
    socketio = current_app.extensions.get('socketio')
    if socketio:
        broadcast_job_update(socketio, job_id, 'refunded', 'refunded')
    
    return jsonify({'success': True, 'message': 'Job marked as refunded'})


@admin_bp.route('/subscribe', methods=['POST'])
@admin_required
def subscribe():
    """Subscribe to push notifications"""
    from utils.notification_utils import add_subscription, push_subscriptions
    from websocket.events import broadcast_subscription_status
    from flask import current_app
    
    subscription = request.json
    endpoint = subscription.get('endpoint', 'unknown')
    
    print(f"📱 Subscription request received: {endpoint[:50]}...")
    
    # Add subscription (checks for duplicates internally)
    is_new = add_subscription(subscription)
    
    if is_new:
        print(f"✅ New subscription added. Total subscriptions: {len(push_subscriptions)}")
        # Broadcast update to all connected WebSocket clients
        socketio = current_app.extensions.get('socketio')
        if socketio:
            broadcast_subscription_status(socketio)
    else:
        print(f"ℹ️  Subscription already exists (duplicate prevented)")
    
    return jsonify({'success': True, 'message': 'Subscribed' if is_new else 'Already subscribed'})


@admin_bp.route('/update-print-status/<job_id>', methods=['POST'])
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
