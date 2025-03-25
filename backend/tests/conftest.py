import os
import pytest
import tempfile
from flask import Flask
from app.routes import api

# Set test environment
os.environ['FLASK_ENV'] = 'testing'

# Add the project root to Python path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import User, InstagramAccount

@pytest.fixture(scope='session')
def app():
    """Create a test Flask application."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.register_blueprint(api, url_prefix='/api')
    return app

@pytest.fixture(scope='session')
def client(app):
    """Create a test client."""
    return app.test_client()

@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables."""
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ['DATA_DIR'] = temp_dir
        yield

@pytest.fixture
def test_user():
    """Create a test user."""
    user = User(username="testuser")
    user.save()
    return user

@pytest.fixture
def test_account(test_user):
    """Create a test Instagram account."""
    account = InstagramAccount(
        username="testinstagram",
        user_id=test_user.user_id,
        session_cookies={
            "sessionid": "fakesessionid",
            "csrftoken": "fakecsrftoken",
            "ds_user_id": "12345678",
            "mid": "fakemid"
        }
    )
    account.save()
    return account

@pytest.fixture
def auth_headers():
    """Create authorization headers."""
    return {
        'Authorization': 'Bearer test_token',
        'Content-Type': 'application/json'
    } 