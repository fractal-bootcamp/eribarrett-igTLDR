"""
Unit tests for AuthController.
"""
import os
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from models.user import User
from models.instagram_account import InstagramAccount
from controllers.auth_controller import AuthController
from tests.mocks import MockInstagramClient
from config import get_config

config = get_config()

@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment."""
    # Create test data directory
    os.makedirs(config.DATA_DIR, exist_ok=True)
    yield
    # Cleanup after tests
    user_file = os.path.join(config.DATA_DIR, 'users.json')
    account_file = os.path.join(config.DATA_DIR, 'instagram_accounts.json')
    if os.path.exists(user_file):
        os.remove(user_file)
    if os.path.exists(account_file):
        os.remove(account_file)

@pytest.fixture
def mock_instagram_client():
    """Mock Instagram client."""
    with patch('controllers.auth_controller.Client') as mock:
        client = Mock()
        mock.return_value = client
        yield client

@pytest.fixture
def sample_user():
    """Sample user data."""
    return {
        'user_id': 'test_user_id',
        'username': 'test_user'
    }

@pytest.fixture
def sample_cookies():
    """Sample Instagram session cookies."""
    return {
        'sessionid': 'test_session_id',
        'csrftoken': 'test_csrf_token'
    }

def test_register():
    """Test user registration."""
    result = AuthController.register('test_user')
    assert result['success'] is True
    assert result['user']['username'] == 'test_user'
    
    # Test duplicate registration
    result = AuthController.register('test_user')
    assert result['success'] is False
    assert 'error' in result

def test_login():
    """Test user login."""
    # Register user first
    AuthController.register('test_user')
    
    # Test successful login
    result = AuthController.login('test_user')
    assert result['success'] is True
    assert 'token' in result
    assert result['user']['username'] == 'test_user'
    
    # Test login with non-existent user
    result = AuthController.login('nonexistent')
    assert result['success'] is False
    assert 'error' in result

def test_logout():
    """Test user logout."""
    # Register and login user
    AuthController.register('test_user')
    login_result = AuthController.login('test_user')
    token = login_result['token']
    
    # Test successful logout
    result = AuthController.logout(token)
    assert result['success'] is True
    
    # Test logout with invalid token
    result = AuthController.logout('invalid_token')
    assert result['success'] is False
    assert 'error' in result

def test_get_current_user():
    """Test getting current user."""
    # Register and login user
    AuthController.register('test_user')
    login_result = AuthController.login('test_user')
    token = login_result['token']
    
    # Test getting current user
    result = AuthController.get_current_user(token)
    assert result['success'] is True
    assert result['user']['username'] == 'test_user'
    
    # Test with invalid token
    result = AuthController.get_current_user('invalid_token')
    assert result['success'] is False
    assert 'error' in result

def test_instagram_login():
    """Test Instagram login."""
    result = AuthController.instagram_login('test_user', '127.0.0.1')
    assert result['success'] is True
    assert result['account']['username'] == 'test_user'
    assert result['account']['user_ip'] == '127.0.0.1' 