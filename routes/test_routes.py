"""
Test routes for notifications and development
"""
from flask import Blueprint, render_template
from config import Config

test_bp = Blueprint('test', __name__)


@test_bp.route('/test-notifications')
def test_notifications():
    """Test page for push notifications"""
    return render_template('test_notifications.jinja', vapid_public_key=Config.VAPID_PUBLIC_KEY)


@test_bp.route('/test-simple-notification')
def test_simple_notification():
    """Simple notification test without service worker"""
    return render_template('test_simple_notification.html')
