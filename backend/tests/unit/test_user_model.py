"""
Unit tests for User model.
"""
import os
import json
import pytest
import tempfile
from datetime import datetime
import time

# Ensure tests use temporary file
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from models.user import User, USER_FILE

class TestUserModel:
    """Tests for User model."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup test user file and clean up after tests."""
        # Use temporary file for users
        users_fd, users_path = tempfile.mkstemp()
        self.original_user_file = USER_FILE
        User.USER_FILE = users_path
        
        yield
        
        # Restore original user file and clean up
        User.USER_FILE = self.original_user_file
        os.close(users_fd)
        os.unlink(users_path)
    
    def test_create_user(self):
        """Test user creation."""
        user = User(username="testuser", email="test@example.com")
        
        # Check attributes
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.user_id is not None
        assert user.created_at is not None
        
        # Check that user_id is a UUID string
        assert len(user.user_id) > 30
    
    def test_save_and_find_user(self):
        """Test saving user and finding it."""
        # Create and save user
        user = User(username="findme", email="find@example.com")
        user.save()
        
        # Find user by username
        found_user = User.find_by_username("findme")
        assert found_user is not None
        assert found_user.username == "findme"
        assert found_user.email == "find@example.com"
        assert found_user.user_id == user.user_id
        
        # Find user by email
        found_user = User.find_by_email("find@example.com")
        assert found_user is not None
        assert found_user.username == "findme"
        
        # Find user by ID
        found_user = User.find_by_id(user.user_id)
        assert found_user is not None
        assert found_user.username == "findme"
    
    def test_to_dict(self):
        """Test converting user to dictionary."""
        user = User(username="dictuser", email="dict@example.com", password_hash="fakehash")
        user_dict = user.to_dict()
        
        assert user_dict["username"] == "dictuser"
        assert user_dict["email"] == "dict@example.com"
        assert user_dict["password_hash"] == "fakehash"
        assert "user_id" in user_dict
        assert "created_at" in user_dict
    
    def test_update_user(self):
        """Test updating existing user."""
        # Create and save user
        user = User(username="updateme", email="update@example.com")
        user.save()
        
        # Modify and save again
        user.email = "updated@example.com"
        user.save()
        
        # Find user and check if updated
        found_user = User.find_by_username("updateme")
        assert found_user.email == "updated@example.com"
    
    def test_delete_user(self):
        """Test deleting a user."""
        # Create and save user
        user = User(username="deleteme", email="delete@example.com")
        user.save()
        
        # Delete user
        user.delete()
        
        # Verify user is deleted
        found_user = User.find_by_username("deleteme")
        assert found_user is None
    
    def test_token_generation_and_verification(self):
        """Test JWT token generation and verification."""
        user = User(username="tokenuser", email="token@example.com")
        user.save()
        
        # Generate token
        token = user.generate_token()
        assert token is not None
        
        # Verify token
        user_id = User.verify_token(token)
        assert user_id == user.user_id
        
        # Test invalid token
        invalid_id = User.verify_token("invalid.token.here")
        assert invalid_id is None 