"""
Integration tests for authentication API endpoints.
"""
import json
import pytest
from flask import Flask

def test_login_success(client, test_user):
    """Test successful login."""
    # Test user has "fakepasswordhash" as password_hash, which will be rejected
    # Update the user to have a valid password hash
    from controllers.auth_controller import AuthController
    test_user.password_hash = AuthController.hash_password("password123")
    test_user.save()
    
    response = client.post(
        '/api/auth/login',
        data=json.dumps({
            'username': 'testuser',
            'password': 'password123'
        }),
        content_type='application/json'
    )
    
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['success'] is True
    assert 'token' in data
    assert 'user_id' in data

def test_login_missing_fields(client):
    """Test login with missing fields."""
    response = client.post(
        '/api/auth/login',
        data=json.dumps({
            'username': 'testuser'
            # Missing password
        }),
        content_type='application/json'
    )
    
    data = json.loads(response.data)
    
    assert response.status_code == 400
    assert data['success'] is False
    assert 'error' in data

def test_login_invalid_credentials(client, test_user):
    """Test login with invalid credentials."""
    response = client.post(
        '/api/auth/login',
        data=json.dumps({
            'username': 'testuser',
            'password': 'wrongpassword'
        }),
        content_type='application/json'
    )
    
    data = json.loads(response.data)
    
    assert response.status_code == 401
    assert data['success'] is False
    assert 'error' in data

def test_instagram_login_unauthorized(client):
    """Test Instagram login without authentication."""
    response = client.post(
        '/api/auth/instagram',
        data=json.dumps({
            'username': 'instagram_username',
            'password': 'instagram_password'
        }),
        content_type='application/json'
    )
    
    assert response.status_code == 401

def test_instagram_login_success(client, test_user, test_token, monkeypatch):
    """Test successful Instagram login."""
    # Mock InstagramClient for testing
    from unittest.mock import Mock
    
    # Create a mock for instagram_login method
    mock_instagram_login = Mock(return_value={
        'success': True,
        'account_id': 'mock_account_id'
    })
    
    # Patch the AuthController.instagram_login method
    monkeypatch.setattr('controllers.auth_controller.AuthController.instagram_login', mock_instagram_login)
    
    response = client.post(
        '/api/auth/instagram',
        data=json.dumps({
            'username': 'instagram_username',
            'password': 'instagram_password'
        }),
        content_type='application/json',
        headers={'Authorization': f'Bearer {test_token}'}
    )
    
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['success'] is True
    assert 'account_id' in data
    
    # Verify mock was called with correct arguments
    mock_instagram_login.assert_called_once_with(
        'instagram_username', 'instagram_password', test_user.user_id
    ) 