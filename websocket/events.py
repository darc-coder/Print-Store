"""
WebSocket event handlers and broadcast functions
"""
from flask import request
from models.database import get_job
from utils.notification_utils import push_subscriptions


def register_socketio_events(socketio):
    """Register all SocketIO event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        print(f"🔌 WebSocket client connected: {request.sid}")
        # Send current subscription status to newly connected client
        socketio.emit('subscription_status_update', {
            'connected': len(push_subscriptions) > 0,
            'count': len(push_subscriptions)
        })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        print(f"🔌 WebSocket client disconnected: {request.sid}")
    
    @socketio.on('request_subscription_status')
    def handle_subscription_status_request():
        """Handle explicit request for subscription status"""
        print(f"📊 Client {request.sid} requested subscription status")
        socketio.emit('subscription_status_update', {
            'connected': len(push_subscriptions) > 0,
            'count': len(push_subscriptions)
        }, room=request.sid)


def broadcast_subscription_status(socketio):
    """Broadcast subscription status to all connected WebSocket clients"""
    status_data = {
        'connected': len(push_subscriptions) > 0,
        'count': len(push_subscriptions)
    }
    print(f"📡 Broadcasting subscription status to all clients: {status_data}")
    socketio.emit('subscription_status_update', status_data, namespace='/')


def broadcast_job_update(socketio, job_id, status, action='updated'):
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
