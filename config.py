import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration class."""

    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')

    # Authentication
    APP_PASSWORD = os.getenv('APP_PASSWORD', 'changeme')

    # Database Configuration
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'instance/tracker.db')

    # Cache Configuration
    CACHE_DURATION = int(os.getenv('CACHE_DURATION', 3600))  # 1 hour default

    # Session Configuration
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # In production, set this to True
    SESSION_COOKIE_SECURE = FLASK_ENV == 'production'

    @staticmethod
    def init_app(app):
        """Initialize application with config."""
        pass


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    FLASK_ENV = 'development'


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    FLASK_ENV = 'production'
    SESSION_COOKIE_SECURE = True


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
