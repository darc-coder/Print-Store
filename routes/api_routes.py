"""
API endpoints for cart management, job status, notifications, etc.
"""
import sqlite3
from flask import Blueprint, request, jsonify, url_for

from config import Config
from models.database import get_job, update_job_settings
from services.cart_service import get_cart_summary
from utils.print_utils import check_print_job_status
from utils.notification_utils import send_push_notification, push_subscriptions
from models.database import update_job_status

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/cart-summary', methods=['GET'])
def cart_summary():
    """API endpoint to get cart summary for header display"""
    summary = get_cart_summary()
    return jsonify({
        'count': summary['count'],
        'total_cost': summary['total_cost'],
        'total_pages': summary['total_pages']
    })


@api_bp.route('/cart-details', methods=['GET'])
def cart_details():
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


@api_bp.route('/update-cart-item', methods=['POST'])
def update_cart_item():
    """API endpoint to update cart item settings (copies, orientation, color)"""
    data = request.json
    job_id = data.get('job_id')
    copies = data.get('copies')
    orientation = data.get('orientation')
    print_color = data.get('print_color')
    
    if not job_id:
        return jsonify({'error': 'job_id required'}), 400
    
    job = get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    # Get current values
    current_copies = job.get('copies', 1)
    current_orientation = job.get('orientation', 'portrait')
    current_color = job.get('print_color', 'bw')
    
    # Update copies if provided
    if copies is not None:
        current_copies = max(1, min(99, int(copies)))  # Clamp between 1-99
        
        # Recalculate cost (same price for both B&W and Color)
        base_cost = job['pages'] * Config.COST_PER_PAGE
        new_cost = base_cost * current_copies
        
        con = sqlite3.connect(Config.DB_PATH)
        cur = con.cursor()
        cur.execute('UPDATE jobs SET cost = ? WHERE id = ?', (new_cost, job_id))
        con.commit()
        con.close()
    
    # Update orientation if provided
    if orientation is not None:
        current_orientation = orientation
    
    # Update print color if provided
    if print_color is not None:
        current_color = print_color
    
    # Update all settings
    update_job_settings(job_id, current_copies, current_orientation, current_color)
    
    # Return updated cart summary
    summary = get_cart_summary()
    return jsonify({
        'success': True,
        'total_cost': summary['total_cost'],
        'total_pages': summary['total_pages']
    })


@api_bp.route('/get-screenshot', methods=['POST'])
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
                'screenshot_url': url_for('user.serve_screenshot', filename=job['payment_screenshot'])
            })
    
    return jsonify({'has_screenshot': False})


@api_bp.route('/job-status/<job_id>', methods=['GET'])
def job_status(job_id):
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


@api_bp.route('/test-notification', methods=['POST'])
def test_notification():
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


@api_bp.route('/resend-notification', methods=['POST'])
def resend_notification():
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
