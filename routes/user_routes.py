"""
User-facing routes for file upload, checkout, payment, and status
"""
import uuid
import sqlite3
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, redirect, url_for, render_template, abort, send_from_directory
from werkzeug.utils import secure_filename

from config import Config
from models.database import save_job, get_job, update_job_settings, update_job_status
from services.cart_service import (
    get_cart_jobs, add_to_cart, remove_from_cart, clear_cart, get_cart_summary
)
from utils import allowed_file, count_pdf_pages, print_file
from utils.notification_utils import push_subscriptions, send_push_notification

user_bp = Blueprint('user', __name__)


@user_bp.route('/')
def index():
    """Upload page (home)"""
    response = render_template('upload.jinja')
    # Prevent caching so back button works properly
    from flask import make_response
    response = make_response(response)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@user_bp.route('/sw.js')
def service_worker():
    """Serve service worker from root to have proper scope"""
    return send_from_directory('.', 'sw.js', mimetype='application/javascript')


@user_bp.route('/upload', methods=['POST'])
def upload():
    """Handle file upload"""
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
        saved_path = Config.UPLOAD_FOLDER / saved_name
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

        cost = pages * Config.COST_PER_PAGE

        job_id = unique_id
        
        save_job(job_id, filename, stored_for_print, pages, cost, 
                 status='awaiting_payment')
        
        # Add to cart
        add_to_cart(job_id)
        uploaded_count += 1
    
    if uploaded_count == 0:
        abort(400, 'no valid files uploaded')

    return redirect(url_for('user.checkout'))


@user_bp.route('/checkout')
def checkout():
    """Checkout page with cart"""
    cart_summary = get_cart_summary()
    if cart_summary['count'] == 0:
        return redirect(url_for('user.index'))
    
    from flask import make_response
    response = make_response(render_template('checkout.jinja', cart=cart_summary))
    # Prevent caching so back button works properly
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@user_bp.route('/cart/remove/<job_id>', methods=['POST'])
def remove_from_cart_route(job_id):
    """Remove a file from the cart"""
    remove_from_cart(job_id)
    return redirect(url_for('user.checkout'))


@user_bp.route('/checkout/process', methods=['POST'])
def process_checkout():
    """Process all jobs in cart with their settings"""
    cart_job_ids = get_cart_jobs()
    if not cart_job_ids:
        return redirect(url_for('user.index'))
    
    # Update settings for each job based on form data
    for job_id in cart_job_ids:
        copies = int(request.form.get(f'copies_{job_id}', 1))
        orientation = request.form.get(f'orientation_{job_id}', 'portrait')
        print_color = request.form.get(f'print_color_{job_id}', 'bw')
        
        # Update job settings
        update_job_settings(job_id, copies, orientation, print_color)
        
        # Recalculate cost based on copies
        job = get_job(job_id)
        if job:
            # Get base cost (cost per page * pages) - same price for both B&W and Color
            base_cost = job['pages'] * Config.COST_PER_PAGE
            new_cost = base_cost * copies
            
            # Update cost in database
            con = sqlite3.connect(Config.DB_PATH)
            cur = con.cursor()
            cur.execute('UPDATE jobs SET cost = ? WHERE id = ?', (new_cost, job_id))
            con.commit()
            con.close()
    
    # Redirect to payment page with QR code
    return redirect(url_for('user.payment_page'))


@user_bp.route('/uploads/<filename>')
def serve_upload(filename):
    """Serve uploaded files for preview"""
    return send_from_directory(Config.UPLOAD_FOLDER, filename)


@user_bp.route('/payment', methods=['GET', 'POST'])
def payment_page():
    """Payment page (redirects to waiting page for screenshot upload)"""
    cart_summary = get_cart_summary()
    if cart_summary['count'] == 0:
        return redirect(url_for('user.index'))
    
    cart_job_ids = get_cart_jobs()
    jobs = cart_summary['jobs']
    total_pages = cart_summary['total_pages']
    total_cost = cart_summary['total_cost']
    
    return render_template('waiting.jinja', 
                          job_ids=cart_job_ids, 
                          jobs=jobs,
                          total_pages=total_pages,
                          total_cost=total_cost)


@user_bp.route('/submit-payment', methods=['POST'])
def submit_payment():
    """Handle payment screenshot upload and submission"""
    job_ids = request.form.getlist('job_ids[]')
    
    if not job_ids:
        return redirect(url_for('user.index'))
    
    # Handle screenshot upload
    screenshot = request.files.get('screenshot')
    screenshot_path = None
    
    if screenshot and screenshot.filename:
        filename = secure_filename(screenshot.filename)
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        screenshot_path = Config.SCREENSHOTS_FOLDER / unique_name
        screenshot.save(screenshot_path)
    
    # Update all jobs with screenshot and status
    current_time = datetime.now().isoformat()
    con = sqlite3.connect(Config.DB_PATH)
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
    return redirect(url_for('user.waiting_page', job_ids=','.join(job_ids)))


@user_bp.route('/waiting')
def waiting_page():
    """Waiting for approval page"""
    job_ids_str = request.args.get('job_ids', '')
    job_ids = job_ids_str.split(',') if job_ids_str else []
    
    if not job_ids:
        return redirect(url_for('user.index'))
    
    jobs = [get_job(jid) for jid in job_ids if get_job(jid)]
    if not jobs:
        return redirect(url_for('user.index'))
    
    total_pages = sum([j['pages'] * j['copies'] for j in jobs])
    total_cost = sum([j['cost'] for j in jobs])
    
    return render_template('waiting.jinja', jobs=jobs, job_ids=job_ids, 
                         total_pages=total_pages, total_cost=total_cost)


@user_bp.route('/success')
def success_page():
    """Success page after payment approval"""
    job_ids_str = request.args.get('job_ids', '')
    job_ids = job_ids_str.split(',') if job_ids_str else []
    
    if not job_ids:
        return redirect(url_for('user.index'))
    
    jobs = [get_job(jid) for jid in job_ids if get_job(jid)]
    if not jobs:
        return redirect(url_for('user.index'))
    
    total_pages = sum([j['pages'] * j['copies'] for j in jobs])
    total_cost = sum([j['cost'] for j in jobs])
    
    # Clear the cart since payment is complete and approved
    clear_cart()
    
    return render_template('success.jinja', jobs=jobs, 
                         total_pages=total_pages, total_cost=total_cost)


@user_bp.route('/serve-screenshot/<filename>')
def serve_screenshot(filename):
    """Serve payment screenshot"""
    return send_from_directory(Config.SCREENSHOTS_FOLDER, filename)


# ============= LEGACY/TEST ROUTES =============

@user_bp.route('/simulate_pay_cart', methods=['POST', 'GET'])
def simulate_pay_cart():
    """Simulate payment for all jobs in cart (TESTING ONLY)"""
    cart_job_ids = get_cart_jobs()
    if not cart_job_ids:
        return redirect(url_for('user.index'))
    
    # Process all jobs in cart
    for job_id in cart_job_ids:
        job = get_job(job_id)
        if job:
            # Mark paid
            update_job_status(job_id, 'paid')
            # Trigger printing with settings
            result = print_file(job['stored_path'], 
                                copies=job.get('copies', 1),
                                orientation=job.get('orientation', 'portrait'))
            update_job_status(job_id, 'printing' if result['success'] else 'error')
    
    first_job_id = cart_job_ids[0] if cart_job_ids else None
    
    if first_job_id:
        return redirect(url_for('user.waiting_page', job_ids=first_job_id))
    return redirect(url_for('user.index'))


@user_bp.route('/simulate_pay/<job_id>', methods=['POST'])
def simulate_pay(job_id):
    """Simple simulated payment endpoint for testing"""
    job = get_job(job_id)
    if not job:
        abort(404)
    # Mark paid
    update_job_status(job_id, 'paid')
    # Trigger printing with settings
    result = print_file(job['stored_path'], 
                        copies=job.get('copies', 1),
                        orientation=job.get('orientation', 'portrait'))
    update_job_status(job_id, 'printing' if result['success'] else 'error')
    return redirect(url_for('user.waiting_page', job_ids=job_id))


@user_bp.route('/payment_webhook', methods=['POST'])
def payment_webhook():
    """Example webhook endpoint placeholder for payment gateways"""
    from flask import jsonify
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
            result = print_file(job['stored_path'])
            update_job_status(job_id, 'printing' if result['success'] else 'error')
    return jsonify({'ok': True})
