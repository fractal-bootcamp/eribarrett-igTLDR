import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'
    DATA_DIR = os.environ.get('DATA_DIR') or os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    TESTING = False
    
    # Flask configuration
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # JWT configuration
    JWT_SECRET = os.environ.get('JWT_SECRET', 'dev')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 30 * 24 * 60 * 60))  # 30 days
    
    # Instagram configuration
    INSTAGRAM_CHECK_INTERVAL = int(os.environ.get('INSTAGRAM_CHECK_INTERVAL', 300))  # 5 minutes
    INSTAGRAM_MAX_RETRIES = int(os.environ.get('INSTAGRAM_MAX_RETRIES', 3))
    INSTAGRAM_RETRY_DELAY = int(os.environ.get('INSTAGRAM_RETRY_DELAY', 60))  # 1 minute
    INSTAGRAM_PROXY = os.environ.get('INSTAGRAM_PROXY')  # Proxy URL
    
    # Rate limiting
    RATELIMIT_ENABLED = os.environ.get('RATELIMIT_ENABLED', 'True').lower() == 'true'
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')
    RATELIMIT_STRATEGY = os.environ.get('RATELIMIT_STRATEGY', 'fixed-window')
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '200 per day')
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'app.log')
    
    # Database
    DB_PATH = os.environ.get('DB_PATH', 'data')

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tests', 'data')

def get_config():
    """Get the appropriate configuration."""
    env = os.environ.get('FLASK_ENV', 'development')
    if env == 'testing':
        return TestingConfig
    return DevelopmentConfig 