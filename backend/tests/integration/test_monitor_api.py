"""
Integration tests for monitoring API endpoints.
"""
import json
import pytest
from unittest.mock import patch, MagicMock

def test_monitor_status_unauthorized(client):
    """Test getting monitor status without authentication."""
    response = client.get('/api/monitor/status')
    
    assert response.status_code == 401

def test_monitor_status(client, test_user, auth_headers):
    """Test getting monitor status."""
    response = client.get(
        '/api/monitor/status',
        headers=auth_headers
    )
    
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['success'] is True
    assert 'running' in data
    assert isinstance(data['running'], bool)

@patch('controllers.instagram_monitor.start')
def test_start_monitor(mock_start, client, test_user, auth_headers):
    """Test starting the monitor."""
    # Mock successful start
    mock_start.return_value = True
    
    response = client.post(
        '/api/monitor/start',
        headers=auth_headers
    )
    
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['success'] is True
    assert 'message' in data
    assert mock_start.called

@patch('controllers.instagram_monitor.stop')
def test_stop_monitor(mock_stop, client, test_user, auth_headers):
    """Test stopping the monitor."""
    # Mock successful stop
    mock_stop.return_value = True
    
    response = client.post(
        '/api/monitor/stop',
        headers=auth_headers
    )
    
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['success'] is True
    assert 'message' in data
    assert mock_stop.called

def test_manual_check_unauthorized(client):
    """Test manual check without authentication."""
    response = client.post('/api/monitor/manual-check')
    
    assert response.status_code == 401

@patch('controllers.instagram_monitor.check_now')
def test_manual_check_specific_account(mock_check, client, test_user, test_account, auth_headers):
    """Test manual check for a specific account."""
    # Mock successful check
    mock_check.return_value = True
    
    response = client.post(
        '/api/monitor/manual-check',
        data=json.dumps({
            'account_id': test_account.account_id
        }),
        content_type='application/json',
        headers=auth_headers
    )
    
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['success'] is True
    assert 'message' in data
    mock_check.assert_called_once_with(test_account.account_id)

@patch('controllers.instagram_monitor.check_now')
def test_manual_check_all_accounts(mock_check, client, test_user, test_account, auth_headers):
    """Test manual check for all accounts."""
    # Mock successful check
    mock_check.return_value = True
    
    response = client.post(
        '/api/monitor/manual-check',
        data=json.dumps({}),  # No specific account_id
        content_type='application/json',
        headers=auth_headers
    )
    
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['success'] is True
    assert 'results' in data
    assert len(data['results']) == 1  # Only have one test account
    assert data['results'][0]['account_id'] == test_account.account_id
    assert data['results'][0]['username'] == test_account.username
    assert data['results'][0]['success'] is True
    mock_check.assert_called_once_with(test_account.account_id)

@patch('controllers.instagram_monitor.check_now')
def test_manual_check_nonexistent_account(mock_check, client, test_user, auth_headers):
    """Test manual check for a nonexistent account."""
    response = client.post(
        '/api/monitor/manual-check',
        data=json.dumps({
            'account_id': 'fake_account_id'
        }),
        content_type='application/json',
        headers=auth_headers
    )
    
    data = json.loads(response.data)
    
    assert response.status_code == 404
    assert data['success'] is False
    assert 'error' in data
    assert not mock_check.called 