"""
Production Configuration for RpiPrint
Optimized for Raspberry Pi 4 with Cloudflare Tunnel
"""
import os
from datetime import timedelta
from pathlib import Path

class ProductionConfig:
    """Production configuration with security hardening"""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'CHANGE-THIS-IN-PRODUCTION-USE-RANDOM-STRING')
    DEBUG = False
    TESTING = False
    
    # Server Configuration
    HOST = '0.0.0.0'  # Listen on all interfaces for Cloudflare tunnel
    PORT = 5500
    
    # Session Configuration
    SESSION_COOKIE_SECURE = True  # HTTPS only (Cloudflare provides HTTPS)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # File Upload Configuration
    BASE_DIR = Path(__file__).parent.absolute()
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    SCREENSHOTS_FOLDER = BASE_DIR / 'screenshots'
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif', 'webp', 'svg'}
    
    # Database Configuration
    DB_PATH = BASE_DIR / 'jobs.db'
    
    # Printer Configuration
    PRINTER_NAME = os.getenv('PRINTER_NAME', 'Canon_G3000_W')
    COST_PER_PAGE = float(os.getenv('COST_PER_PAGE', '5.0'))
    
    # Admin Configuration
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'CHANGE-THIS-PASSWORD')
    
    # SocketIO Configuration
    SOCKETIO_CORS_ALLOWED_ORIGINS = '*'  # Cloudflare tunnel handles CORS
    SOCKETIO_ASYNC_MODE = 'threading'
    
    # Push Notifications (VAPID)
    VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY', '')
    VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY', '')
    VAPID_CLAIMS = {"sub": os.getenv('VAPID_EMAIL', 'mailto:admin@example.com')}
    
    # Security Headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    }
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = BASE_DIR / 'rpiprint.log'
    
    @classmethod
    def init_app(cls):
        """Initialize application directories"""
        cls.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        cls.SCREENSHOTS_FOLDER.mkdir(parents=True, exist_ok=True)
        print(f"✅ Initialized directories:")
        print(f"   - Uploads: {cls.UPLOAD_FOLDER}")
        print(f"   - Screenshots: {cls.SCREENSHOTS_FOLDER}")
        print(f"   - Database: {cls.DB_PATH}")
