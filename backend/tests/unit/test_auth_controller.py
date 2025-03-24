"""
Unit tests for AuthController.
"""
import os
import pytest
import tempfile
import unittest.mock as mock
from datetime import datetime

# Ensure tests use temporary file
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from models.user import User, USER_FILE
from models.instagram_account import InstagramAccount, ACCOUNTS_FILE
from controllers.auth_controller import AuthController
from tests.mocks import MockInstagramClient

class TestAuthController:
    """Tests for AuthController."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup test files and clean up after tests."""
        # Use temporary files for users and accounts
        users_fd, users_path = tempfile.mkstemp()
        accounts_fd, accounts_path = tempfile.mkstemp()
        
        self.original_user_file = USER_FILE
        self.original_accounts_file = ACCOUNTS_FILE
        
        User.USER_FILE = users_path
        InstagramAccount.ACCOUNTS_FILE = accounts_path
        
        yield
        
        # Restore original files and clean up
        User.USER_FILE = self.original_user_file
        InstagramAccount.ACCOUNTS_FILE = self.original_accounts_file
        
        os.close(users_fd)
        os.close(accounts_fd)
        os.unlink(users_path)
        os.unlink(accounts_path)
    
    def test_register_new_user(self):
        """Test registering a new user."""
        result = AuthController.register("newuser", "new@example.com", "password123")
        
        assert result["success"] is True
        assert "user_id" in result
        assert "token" in result
        
        # Verify user was created
        user = User.find_by_username("newuser")
        assert user is not None
        assert user.email == "new@example.com"
        assert user.password_hash is not None
    
    def test_register_existing_username(self):
        """Test registering with an existing username."""
        # Create a user first
        AuthController.register("existinguser", "existing@example.com", "password123")
        
        # Try to register with same username
        result = AuthController.register("existinguser", "another@example.com", "password456")
        
        assert result["success"] is False
        assert "error" in result
        assert "Username already exists" in result["error"]
    
    def test_register_existing_email(self):
        """Test registering with an existing email."""
        # Create a user first
        AuthController.register("emailuser", "duplicate@example.com", "password123")
        
        # Try to register with same email
        result = AuthController.register("another", "duplicate@example.com", "password456")
        
        assert result["success"] is False
        assert "error" in result
        assert "Email already exists" in result["error"]
    
    def test_login_valid(self):
        """Test logging in with valid credentials."""
        # Create a user first
        AuthController.register("loginuser", "login@example.com", "correctpassword")
        
        # Login with correct credentials
        result = AuthController.login("loginuser", "correctpassword")
        
        assert result["success"] is True
        assert "user_id" in result
        assert "token" in result
    
    def test_login_invalid_username(self):
        """Test logging in with invalid username."""
        result = AuthController.login("nonexistent", "anypassword")
        
        assert result["success"] is False
        assert "error" in result
    
    def test_login_invalid_password(self):
        """Test logging in with invalid password."""
        # Create a user first
        AuthController.register("passworduser", "pwd@example.com", "correctpassword")
        
        # Login with incorrect password
        result = AuthController.login("passworduser", "wrongpassword")
        
        assert result["success"] is False
        assert "error" in result
    
    @mock.patch('controllers.auth_controller.InstagramClient')
    def test_instagram_login(self, mock_instagram_client):
        """Test Instagram login functionality."""
        # Setup mock
        mock_client_instance = MockInstagramClient()
        mock_instagram_client.return_value = mock_client_instance
        
        # Create a user
        user_result = AuthController.register("instauser", "insta@example.com", "password123")
        user_id = user_result["user_id"]
        
        # Login to Instagram
        result = AuthController.instagram_login("instagram_username", "instagram_password", user_id)
        
        assert result["success"] is True
        assert "account_id" in result
        
        # Verify account was created
        accounts = InstagramAccount.find_by_user(user_id)
        assert len(accounts) == 1
        assert accounts[0].username == "instagram_username"
    
    @mock.patch('controllers.auth_controller.InstagramClient')
    def test_instagram_login_failure(self, mock_instagram_client):
        """Test Instagram login failure handling."""
        # Setup mock to fail
        mock_client_instance = MockInstagramClient(login_success=False)
        mock_instagram_client.return_value = mock_client_instance
        
        # Create a user
        user_result = AuthController.register("failuser", "fail@example.com", "password123")
        user_id = user_result["user_id"]
        
        # Attempt login to Instagram
        result = AuthController.instagram_login("instagram_username", "wrong_password", user_id)
        
        assert result["success"] is False
        assert "error" in result
    
    def test_instagram_login_nonexistent_user(self):
        """Test Instagram login with nonexistent user."""
        result = AuthController.instagram_login("instagram_username", "instagram_password", "fake_user_id")
        
        assert result["success"] is False
        assert "error" in result
        assert "User not found" in result["error"] 