// Service Worker for Push Notifications
// Version 9.0 - Removed action buttons for macOS compatibility

self.addEventListener('install', function(event) {
    console.log('Service Worker installing...');
    console.log('Platform:', navigator.userAgent);
    self.skipWaiting(); // Activate immediately
});

self.addEventListener('activate', function(event) {
    console.log('Service Worker activating...');
    console.log('SW location.origin:', self.location.origin);
    console.log('SW location.href:', self.location.href);
    console.log('SW scope:', self.registration.scope);
    console.log('✅ notificationclick handler will be registered');
    event.waitUntil(self.clients.claim()); // Take control immediately
});

// Handle push notifications
self.addEventListener('push', function(event) {
    console.log('Push notification received:', event);
    
    if (!event.data) {
        console.log('Push event but no data');
        return;
    }

    let data;
    try {
        // Try to parse as JSON
        data = event.data.json();
        console.log('Push data parsed:', data);
    } catch (error) {
        console.error('Failed to parse push data as JSON:', error);
        // Fallback: try as text
        try {
            const textData = event.data.text();
            console.log('Push data as text:', textData);
            // Try to parse the text as JSON
            data = JSON.parse(textData);
        } catch (e) {
            console.error('Failed to parse push data at all:', e);
            // Use default notification
            data = {
                title: 'Print Store',
                body: event.data.text() || 'You have a new notification'
            };
        }
    }
    
    const options = {
        body: data.body || 'You have a new notification',
        icon: data.icon || '/static/assets/nitzInc.png',
        badge: '/static/assets/nitzInc.png',
        data: {
            url: data.url || '/admin',
            job_id: data.job_id
        },
        // Remove actions for macOS compatibility - they don't trigger click events reliably
        // requireInteraction: false allows notification to auto-dismiss
        tag: 'print-job-notification', // Replace previous notifications
        renotify: true, // Notify even if replacing old notification
        // Force browser notification instead of macOS native
        silent: false
    };
    
    console.log('Showing notification with options:', options);
    
    event.waitUntil(
        self.registration.showNotification(data.title || 'Print Store', options)
    );
});

// Handle notification click
self.addEventListener('notificationclick', function(event) {
    console.error('🚨🚨🚨 NOTIFICATION WAS CLICKED 🚨🚨🚨'); // Use error to make it stand out
    console.log('=== NOTIFICATION CLICK START ===');
    console.log('Raw event received');
    
    // Immediately try to open something to test if handler is even called
    console.log('Testing if handler executes at all...');
    
    console.log('Full event:', event);
    console.log('Action clicked:', event.action);
    console.log('Notification object:', event.notification);
    console.log('Notification title:', event.notification.title);
    console.log('Notification body:', event.notification.body);
    console.log('Notification data type:', typeof event.notification.data);
    console.log('Notification data:', event.notification.data);
    
    event.notification.close();
    console.log('Notification closed');
    
    // Force open admin page regardless of action
    const urlToOpen = self.location.origin + '/admin';
    console.log('Force opening:', urlToOpen);
    
    event.waitUntil(
        clients.openWindow(urlToOpen).then(function(windowClient) {
            console.log('Window opened!', windowClient);
            return windowClient;
        }).catch(function(err) {
            console.error('Failed to open window:', err);
        })
    );
    
    console.log('=== NOTIFICATION CLICK END ===');
});

// Handle notification close
self.addEventListener('notificationclose', function(event) {
    console.log('Notification closed:', event);
});
