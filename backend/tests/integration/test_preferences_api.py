"""
Integration tests for preferences API endpoints.
"""
import json
import pytest
from models.notification_settings import NotificationSettings

def test_preferences_unauthorized(client):
    """Test preferences without authentication."""
    response = client.get('/api/preferences')
    
    assert response.status_code == 401

def test_get_preferences(client, test_user, test_settings, auth_headers):
    """Test getting user preferences."""
    response = client.get(
        '/api/preferences',
        headers=auth_headers
    )
    
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['success'] is True
    assert 'preferences' in data
    
    prefs = data['preferences']
    assert prefs['email_enabled'] is True
    assert prefs['telegram_enabled'] is False
    assert prefs['check_interval'] == 30
    assert prefs['summary_length'] == 'medium'
    assert prefs['include_images'] is True

def test_update_preferences(client, test_user, test_settings, auth_headers):
    """Test updating user preferences."""
    new_prefs = {
        'email_enabled': False,
        'telegram_enabled': True,
        'check_interval': 60,
        'summary_length': 'short',
        'include_images': False
    }
    
    response = client.post(
        '/api/preferences',
        data=json.dumps(new_prefs),
        content_type='application/json',
        headers=auth_headers
    )
    
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['success'] is True
    assert 'preferences' in data
    
    # Check that preferences were updated
    prefs = data['preferences']
    assert prefs['email_enabled'] is False
    assert prefs['telegram_enabled'] is True
    assert prefs['check_interval'] == 60
    assert prefs['summary_length'] == 'short'
    assert prefs['include_images'] is False
    
    # Verify in database
    settings = NotificationSettings.find_by_user(test_user.user_id)
    assert settings.email_enabled is False
    assert settings.telegram_enabled is True
    assert settings.check_interval == 60
    assert settings.summary_length == 'short'
    assert settings.include_images is False

def test_update_preferences_partial(client, test_user, test_settings, auth_headers):
    """Test partial update of user preferences."""
    # Only update some fields
    partial_update = {
        'check_interval': 120,
        'summary_length': 'long'
    }
    
    response = client.post(
        '/api/preferences',
        data=json.dumps(partial_update),
        content_type='application/json',
        headers=auth_headers
    )
    
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['success'] is True
    
    # Check that only specified preferences were updated
    prefs = data['preferences']
    assert prefs['email_enabled'] is True  # Unchanged
    assert prefs['telegram_enabled'] is False  # Unchanged
    assert prefs['check_interval'] == 120  # Updated
    assert prefs['summary_length'] == 'long'  # Updated
    assert prefs['include_images'] is True  # Unchanged

def test_update_preferences_invalid_value(client, test_user, test_settings, auth_headers):
    """Test updating preferences with invalid value."""
    invalid_update = {
        'summary_length': 'invalid_value'  # Not one of 'short', 'medium', 'long'
    }
    
    response = client.post(
        '/api/preferences',
        data=json.dumps(invalid_update),
        content_type='application/json',
        headers=auth_headers
    )
    
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data['success'] is True
    
    # Value should remain unchanged
    prefs = data['preferences']
    assert prefs['summary_length'] == 'medium'  # Unchanged 