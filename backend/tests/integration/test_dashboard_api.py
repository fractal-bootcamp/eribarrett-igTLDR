"""
Integration tests for dashboard API endpoints.
"""
import json
import pytest
from unittest.mock import patch, MagicMock

def test_dashboard_stats_unauthorized(client):
    """Test dashboard stats without authentication."""
    response = client.get('/api/dashboard/stats')
    
    assert response.status_code == 401

def test_dashboard_stats_no_accounts(client, test_user, auth_headers):
    """Test dashboard stats with no accounts."""
    response = client.get(
        '/api/dashboard/stats',
        headers=auth_headers
    )
    
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['success'] is True
    assert 'stats' in data
    assert len(data['stats']) == 0
    assert 'message' in data

@patch('controllers.instagram_client.InstagramClient')
def test_dashboard_stats_with_accounts(mock_client, client, test_user, test_account, auth_headers):
    """Test dashboard stats with accounts."""
    # Setup mock client
    mock_instance = MagicMock()
    mock_instance.validate_session.return_value = True
    mock_instance.get_user_info.return_value = {
        'success': True,
        'user': {
            'pk': 'user_testinstagram',
            'username': 'testinstagram',
            'full_name': 'Test Testinstagram',
            'is_private': False,
            'profile_pic_url': 'https://example.com/testinstagram.jpg',
            'media_count': 42,
            'follower_count': 1000,
            'following_count': 500
        }
    }
    mock_client.return_value = mock_instance
    
    response = client.get(
        '/api/dashboard/stats',
        headers=auth_headers
    )
    
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['success'] is True
    assert 'stats' in data
    assert len(data['stats']) == 1
    
    # Check account stats data
    account_stats = data['stats'][0]
    assert account_stats['username'] == 'testinstagram'
    assert account_stats['follower_count'] == 1000
    assert account_stats['following_count'] == 500
    assert account_stats['media_count'] == 42

@patch('controllers.instagram_client.InstagramClient')
def test_dashboard_stats_session_expired(mock_client, client, test_user, test_account, auth_headers):
    """Test dashboard stats with expired session."""
    # Setup mock client
    mock_instance = MagicMock()
    mock_instance.validate_session.return_value = False
    mock_client.return_value = mock_instance
    
    response = client.get(
        '/api/dashboard/stats',
        headers=auth_headers
    )
    
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['success'] is True
    assert 'stats' in data
    assert len(data['stats']) == 1
    
    # Check account stats data
    account_stats = data['stats'][0]
    assert account_stats['username'] == 'testinstagram'
    assert account_stats['status'] == 'error'
    assert 'error' in account_stats
    assert account_stats['error'] == 'Session expired' 