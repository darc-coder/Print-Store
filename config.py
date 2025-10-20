"""
Configuration settings for RpiPrint application
"""
import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""
    
    # Admin credentials
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # File upload settings
    UPLOAD_FOLDER = Path(os.getenv('UPLOAD_FOLDER', 'uploads'))
    SCREENSHOTS_FOLDER = Path(os.getenv('SCREENSHOTS_FOLDER', 'screenshots'))
    STATIC_FOLDER = Path('static')
    
    # Database settings
    DB_PATH = Path(os.getenv('DB_PATH', 'jobs.db'))
    
    # Printer settings
    PRINTER_NAME = os.getenv('PRINTER_NAME', 'Canon_G3000_W')
    COST_PER_PAGE = float(os.getenv('COST_PER_PAGE', '5.0'))
    
    # Allowed file extensions
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
    
    # VAPID keys for push notifications
    VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY', 
        'vapid-public-key')
    VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY', 
        'vapid-private-key')
    VAPID_CLAIMS = {"sub": "mailto:nitinlakra123@gmail.com"}
    
    # SocketIO settings
    SOCKETIO_ASYNC_MODE = 'threading'
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
    
    @classmethod
    def init_app(cls):
        """Initialize application folders"""
        cls.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        cls.SCREENSHOTS_FOLDER.mkdir(parents=True, exist_ok=True)
        cls.STATIC_FOLDER.mkdir(parents=True, exist_ok=True)
