#!/usr/bin/env python3
"""
Test script for push notifications
Run this after enabling notifications in the admin dashboard
"""

import json
import os
from pywebpush import webpush, WebPushException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# VAPID keys
VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY', 'BM0FyrpORkg9XWpZMf-eqGsDtjtF-OOB7D60LtmNsCfkpqqWopWkELvNSG1Vs3wUh_VRCxWiYZW3dpCCct1Mw9M')
VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY', '2h5GQNFgJNKihHFQ26ZzHqEzGTnN1aNAZ10GWYkcH7I')
VAPID_CLAIMS = {"sub": "mailto:nitinlakra123@gmail.com"}

def test_notification():
    """Test sending a push notification"""
    print("=" * 60)
    print("🧪 Push Notification Test Script")
    print("=" * 60)
    
    # Check if VAPID keys are set
    print(f"\n✅ VAPID Public Key: {VAPID_PUBLIC_KEY[:20]}...")
    print(f"✅ VAPID Private Key: {VAPID_PRIVATE_KEY[:20]}...")
    print(f"✅ VAPID Claims: {VAPID_CLAIMS}")
    
    # Ask for subscription JSON
    print("\n" + "=" * 60)
    print("📋 INSTRUCTIONS:")
    print("=" * 60)
    print("1. Open admin dashboard: http://localhost:5500/admin")
    print("2. Click 'Enable Notifications' and allow permission")
    print("3. Open browser console (F12 → Console)")
    print("4. First, check if service worker is registered:")
    print("\n   navigator.serviceWorker.getRegistrations().then(regs => console.log('Registrations:', regs.length))")
    print("\n5. Then check for subscription:")
    print("\n   navigator.serviceWorker.ready.then(reg => reg.pushManager.getSubscription().then(sub => console.log('Subscription:', sub)))")
    print("\n6. If subscription exists, get the JSON:")
    print("\n   navigator.serviceWorker.ready.then(reg => reg.pushManager.getSubscription().then(sub => console.log(JSON.stringify(sub))))")
    print("\n7. Copy the entire JSON output")
    print("8. Paste it below (press Enter, then Ctrl+D or Ctrl+Z when done):")
    print("=" * 60)
    print()
    
    # Read subscription JSON from stdin
    print("Paste subscription JSON here:")
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    
    subscription_json = '\n'.join(lines).strip()
    
    if not subscription_json:
        print("\n❌ No subscription provided. Exiting.")
        return
    
    try:
        subscription = json.loads(subscription_json)
        print("\n✅ Subscription parsed successfully!")
        print(f"   Endpoint: {subscription.get('endpoint', 'N/A')[:50]}...")
        
        # Create notification data
        notification_data = {
            'title': '🧪 Test Notification',
            'body': 'If you see this, push notifications are working! 🎉',
            'url': '/admin',
            'icon': '/static/assets/nitzInc.png'
        }
        
        print("\n📤 Sending test notification...")
        print(f"   Title: {notification_data['title']}")
        print(f"   Body: {notification_data['body']}")
        
        # Send the notification
        response = webpush(
            subscription_info=subscription,
            data=json.dumps(notification_data),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS
        )
        
        print("\n✅ SUCCESS! Notification sent!")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text if response.text else 'No response body'}")
        print("\n🔔 Check your browser for the notification!")
        print("   (Make sure the admin tab is minimized or in background)")
        
    except json.JSONDecodeError as e:
        print(f"\n❌ Invalid JSON: {e}")
        print("Make sure you copied the entire subscription object")
    except WebPushException as e:
        print(f"\n❌ WebPush Error: {e}")
        if e.response:
            print(f"   Status: {e.response.status_code}")
            print(f"   Response: {e.response.text}")
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    test_notification()
