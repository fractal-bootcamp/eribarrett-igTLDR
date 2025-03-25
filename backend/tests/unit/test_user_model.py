"""
Unit tests for User model.
"""
import os
import json
import pytest
from datetime import datetime
from models.user import User
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
    if os.path.exists(user_file):
        os.remove(user_file)

def test_create_user():
    """Test user creation."""
    user = User(username='test_user')
    assert user.username == 'test_user'
    assert user.user_id is not None
    assert user.created_at is not None

def test_save_and_load_user():
    """Test user save and load."""
    user = User(username='test_user')
    user.save()
    
    loaded_user = User.find_by_id(user.user_id)
    assert loaded_user is not None
    assert loaded_user.username == user.username
    assert loaded_user.user_id == user.user_id

def test_find_by_username():
    """Test finding user by username."""
    user = User(username='test_user')
    user.save()
    
    found_user = User.find_by_username('test_user')
    assert found_user is not None
    assert found_user.user_id == user.user_id

def test_get_or_create():
    """Test get or create user."""
    # Test creating new user
    user1 = User.get_or_create('test_user')
    assert user1.username == 'test_user'
    
    # Test getting existing user
    user2 = User.get_or_create('test_user')
    assert user2.user_id == user1.user_id

def test_delete_user():
    """Test user deletion."""
    user = User(username='test_user')
    user.save()
    
    user.delete()
    assert User.find_by_id(user.user_id) is None

def test_token_generation():
    """Test JWT token generation."""
    user = User(username='test_user')
    token = user.generate_token()
    assert token is not None
    
    # Verify token
    user_id = User.verify_token(token)
    assert user_id == user.user_id

def test_invalid_token():
    """Test invalid token handling."""
    assert User.verify_token('invalid_token') is None

def test_to_dict():
    """Test user to dictionary conversion."""
    user = User(username='test_user')
    user_dict = user.to_dict()
    assert user_dict['username'] == user.username
    assert user_dict['user_id'] == user.user_id
    assert user_dict['created_at'] == user.created_at 