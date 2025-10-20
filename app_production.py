#!/usr/bin/env python3
"""
Production Server for RpiPrint
Optimized for Raspberry Pi 4 with Cloudflare Tunnel
"""
import os
import sys
import logging
from pathlib import Path

# Set production environment
os.environ['FLASK_ENV'] = 'production'

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import configuration
from config_production import ProductionConfig

# Import the Flask app
from app import app, socketio

def setup_logging():
    """Configure production logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(ProductionConfig.LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )

def configure_app():
    """Apply production configuration"""
    app.config.update(
        DEBUG=False,
        TESTING=False,
        SECRET_KEY=ProductionConfig.SECRET_KEY,
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        MAX_CONTENT_LENGTH=ProductionConfig.MAX_CONTENT_LENGTH,
    )
    
    # Initialize directories
    ProductionConfig.init_app()
    
    # Add security headers
    @app.after_request
    def add_security_headers(response):
        for header, value in ProductionConfig.SECURITY_HEADERS.items():
            response.headers[header] = value
        return response

def main():
    """Run the production server"""
    print("=" * 70)
    print("🚀 RpiPrint Production Server")
    print("=" * 70)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger('rpiprint')
    
    # Configure app
    configure_app()
    
    # Display configuration
    print(f"\n✅ Server Configuration:")
    print(f"   - Host: {ProductionConfig.HOST} (all interfaces)")
    print(f"   - Port: {ProductionConfig.PORT}")
    print(f"   - Debug: False")
    print(f"   - HTTPS: Enabled (via Cloudflare Tunnel)")
    print(f"   - Printer: {ProductionConfig.PRINTER_NAME}")
    print(f"   - Cost per page: ₹{ProductionConfig.COST_PER_PAGE}")
    print(f"   - Admin user: {ProductionConfig.ADMIN_USERNAME}")
    print(f"   - Log file: {ProductionConfig.LOG_FILE}")
    
    print("\n" + "=" * 70)
    print("🌐 Server Access:")
    print("   - Local: http://localhost:5500")
    print("   - Cloudflare Tunnel: https://your-domain.com")
    print("=" * 70)
    
    print("\n⚠️  Security Notes:")
    print("   - Port 5500 is for Cloudflare Tunnel only")
    print("   - Do NOT expose port 5500 directly to internet")
    print("   - All external access should go through Cloudflare Tunnel")
    print("=" * 70)
    
    logger.info("Starting RpiPrint production server...")
    
    try:
        # Run with SocketIO
        socketio.run(
            app,
            host=ProductionConfig.HOST,
            port=ProductionConfig.PORT,
            debug=False,
            use_reloader=False,  # Disable reloader in production
            log_output=True,
            allow_unsafe_werkzeug=True  # Suppress development server warning
        )
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        print("\n\n👋 Server stopped gracefully")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        print(f"\n❌ Server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
