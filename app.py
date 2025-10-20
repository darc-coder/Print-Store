#!/usr/bin/env python3
"""
Flask Raspberry Pi Print Service - Modular Version
Main application entry point
"""
import os
import sys
import signal
from datetime import timedelta
from flask import Flask, session
from flask_socketio import SocketIO

# Import configuration
from config import Config

# Import database initialization
from models.database import init_db

# Import utilities
from utils.file_utils import truncate_filename

# Import blueprints
from routes.user_routes import user_bp
from routes.admin_routes import admin_bp
from routes.api_routes import api_bp
from routes.test_routes import test_bp

# Import WebSocket events
from websocket.events import register_socketio_events

# Import CUPS monitor
from services.cups_monitor import start_cups_monitor, stop_cups_monitor


def create_app():
    """Application factory"""
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    
    # Load configuration
    app.config['UPLOAD_FOLDER'] = str(Config.UPLOAD_FOLDER)
    app.config['SESSION_COOKIE_SAMESITE'] = Config.SESSION_COOKIE_SAMESITE
    app.config['SESSION_COOKIE_SECURE'] = Config.SESSION_COOKIE_SECURE
    app.config['PERMANENT_SESSION_LIFETIME'] = Config.PERMANENT_SESSION_LIFETIME
    app.secret_key = Config.SECRET_KEY
    
    # Initialize folders
    Config.init_app()
    
    # Initialize database
    init_db()
    
    # Register Jinja filters
    app.jinja_env.filters['truncate_filename'] = truncate_filename
    
    # Before request handler for session management
    @app.before_request
    def make_session_permanent():
        """Make session permanent so it persists across browser sessions"""
        session.permanent = True
        # Initialize cart if not exists
        if 'cart' not in session:
            session['cart'] = []
    
    # Register blueprints
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(test_bp)
    
    # Initialize SocketIO
    socketio = SocketIO(
        app, 
        cors_allowed_origins=Config.SOCKETIO_CORS_ALLOWED_ORIGINS,
        async_mode=Config.SOCKETIO_ASYNC_MODE
    )
    
    # Store socketio in app extensions for access in routes
    app.extensions['socketio'] = socketio
    
    # Register WebSocket event handlers
    register_socketio_events(socketio)
    
    print("✅ SocketIO initialized with threading async mode")
    
    return app, socketio


def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(sig, frame):
        print("\n\n" + "="*60)
        print("🛑 Shutdown signal received (Ctrl+C)")
        print("="*60)
        print("⏳ Stopping CUPS monitor...")
        stop_cups_monitor()
        print("✅ CUPS monitor stopped")
        print("⏳ Shutting down server...")
        print("="*60 + "\n")
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


if __name__ == '__main__':
    # Setup signal handlers
    setup_signal_handlers()
    
    # Create app and socketio
    app, socketio = create_app()
    
    print("\n" + "="*60)
    print("🚀 Starting Flask-SocketIO server...")
    print("="*60)
    print(f"📡 WebSocket support enabled")
    print(f"🌐 Server: http://0.0.0.0:5500")
    print(f"🔧 Mode: Development (debug=True)")
    print(f"⚡ Async mode: {Config.SOCKETIO_ASYNC_MODE}")
    print("="*60 + "\n")
    
    # Start CUPS monitoring background task ONLY in main process
    # Flask debug mode spawns a reloader process - we only want monitor in the main worker
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        start_cups_monitor(socketio, app)
    else:
        print("ℹ️  Skipping CUPS monitor in reloader process")
    
    try:
        socketio.run(app, host='0.0.0.0', port=5500, debug=True, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        setup_signal_handlers()
