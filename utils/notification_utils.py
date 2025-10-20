"""
Push notification utilities
"""
import json
from pywebpush import webpush, WebPushException
from config import Config

# Storage for push subscriptions (in production, use database)
push_subscriptions = []


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
                vapid_private_key=Config.VAPID_PRIVATE_KEY,
                vapid_claims=Config.VAPID_CLAIMS
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


def get_subscriptions_count():
    """Get the count of active push subscriptions"""
    return len(push_subscriptions)


def add_subscription(subscription):
    """Add a new push subscription"""
    endpoint = subscription.get('endpoint', 'unknown')
    
    # Check for duplicate subscriptions by endpoint
    for sub in push_subscriptions:
        if sub.get('endpoint') == endpoint:
            return False  # Already exists
    
    push_subscriptions.append(subscription)
    return True  # New subscription added
