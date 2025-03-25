import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_config():
    """Get application configuration."""
    return {
        # Flask configuration
        'SECRET_KEY': os.getenv('SECRET_KEY', 'dev'),
        'DEBUG': os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
        
        # JWT configuration
        'JWT_SECRET': os.getenv('JWT_SECRET', 'dev'),
        'JWT_ACCESS_TOKEN_EXPIRES': int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 30 * 24 * 60 * 60)),  # 30 days
        
        # Instagram configuration
        'INSTAGRAM_CHECK_INTERVAL': int(os.getenv('INSTAGRAM_CHECK_INTERVAL', 300)),  # 5 minutes
        'INSTAGRAM_MAX_RETRIES': int(os.getenv('INSTAGRAM_MAX_RETRIES', 3)),
        'INSTAGRAM_RETRY_DELAY': int(os.getenv('INSTAGRAM_RETRY_DELAY', 60)),  # 1 minute
        'INSTAGRAM_PROXY': os.getenv('INSTAGRAM_PROXY'),  # Proxy URL (e.g., "http://user:pass@host:port")
        
        # Rate limiting
        'RATELIMIT_ENABLED': os.getenv('RATELIMIT_ENABLED', 'True').lower() == 'true',
        'RATELIMIT_STORAGE_URL': os.getenv('RATELIMIT_STORAGE_URL', 'memory://'),
        'RATELIMIT_STRATEGY': os.getenv('RATELIMIT_STRATEGY', 'fixed-window'),
        'RATELIMIT_DEFAULT': os.getenv('RATELIMIT_DEFAULT', '200 per day'),
        
        # Logging
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
        'LOG_FILE': os.getenv('LOG_FILE', 'app.log'),
        
        # Database
        'DB_PATH': os.getenv('DB_PATH', 'data')
    }

class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-dev-key')
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'default-encryption-key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default-jwt-secret')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    
    # Email configuration
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    
    # Telegram configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # Rate limiting
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '100/hour')
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = False
    TESTING = True
    
class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment."""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default']) 