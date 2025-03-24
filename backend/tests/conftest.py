import os
import json
import pytest
import tempfile
from datetime import datetime, timedelta
import uuid

# Set test environment
os.environ['FLASK_ENV'] = 'testing'

# Add the project root to Python path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import User, InstagramAccount, NotificationSettings
from utils import encrypt_data

@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    # Use temporary files for test data
    users_fd, users_path = tempfile.mkstemp()
    accounts_fd, accounts_path = tempfile.mkstemp()
    settings_fd, settings_path = tempfile.mkstemp()
    
    # Set temporary file paths in the module
    User.USER_FILE = users_path
    InstagramAccount.ACCOUNTS_FILE = accounts_path
    NotificationSettings.SETTINGS_FILE = settings_path
    
    # Create the app with test config
    app = create_app()
    app.config['TESTING'] = True
    
    # Setup test context
    with app.app_context():
        yield app
    
    # Clean up
    os.close(users_fd)
    os.close(accounts_fd)
    os.close(settings_fd)
    os.unlink(users_path)
    os.unlink(accounts_path)
    os.unlink(settings_path)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def test_user():
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="fakepasswordhash",
    )
    user.save()
    return user

@pytest.fixture
def test_token(test_user):
    """Create an authentication token for the test user."""
    return test_user.generate_token()

@pytest.fixture
def test_account(test_user):
    """Create a test Instagram account."""
    # Create a mock encrypted cookies
    mock_cookies = {
        "sessionid": "fakesessionid",
        "csrftoken": "fakecsrftoken",
        "ds_user_id": "12345678",
        "mid": "fakemid"
    }
    
    account = InstagramAccount(
        user_id=test_user.user_id,
        username="testinstagram",
        encrypted_cookies=encrypt_data(mock_cookies),
        last_check=(datetime.utcnow() - timedelta(hours=1)).isoformat()
    )
    account.save()
    return account

@pytest.fixture
def test_settings(test_user):
    """Create test notification settings."""
    settings = NotificationSettings(
        user_id=test_user.user_id,
        email_enabled=True,
        telegram_enabled=False,
        check_interval=30,
        summary_length='medium',
        include_images=True
    )
    settings.save()
    return settings

@pytest.fixture
def auth_headers(test_token):
    """Create authorization headers."""
    return {
        'Authorization': f'Bearer {test_token}',
        'Content-Type': 'application/json'
    } 