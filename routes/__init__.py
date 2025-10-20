"""
Routes module initialization
"""
from .user_routes import user_bp
from .admin_routes import admin_bp
from .api_routes import api_bp

__all__ = ['user_bp', 'admin_bp', 'api_bp']
