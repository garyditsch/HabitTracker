"""Main Flask application entry point."""

import os
from datetime import timedelta
from flask import Flask
from config import config
from models import init_database


def create_app(config_name=None):
    """
    Application factory pattern for creating Flask app.

    Args:
        config_name: Configuration name ('development', 'production', or None for auto-detect)

    Returns:
        Configured Flask application
    """
    app = Flask(__name__)

    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app.config.from_object(config[config_name])

    # Session configuration for security
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
    app.config['SESSION_COOKIE_SECURE'] = config_name == 'production'  # HTTPS only in production
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Session timeout

    # Initialize database
    with app.app_context():
        init_database()

    # Register blueprints
    from routes.auth import auth_bp
    from routes.public import public_bp
    from routes.admin import admin_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)

    # Basic health check route
    @app.route('/health')
    def health():
        """Health check endpoint."""
        return {'status': 'healthy', 'app': 'health-tracker'}, 200

    return app


# Create application instance
app = create_app()


if __name__ == '__main__':
    # Run development server
    # Use port 5001 to avoid conflict with macOS AirPlay Receiver on port 5000
    app.run(debug=True, host='0.0.0.0', port=5001)
