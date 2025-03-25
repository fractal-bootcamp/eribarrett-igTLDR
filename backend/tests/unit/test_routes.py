import pytest
from unittest.mock import Mock, patch
from flask import Flask
from app.routes import api
from models.instagram_account import InstagramAccount
from models.user import User

@pytest.fixture
def app():
    """Create a test Flask application."""
    app = Flask(__name__)
    app.register_blueprint(api, url_prefix='/api')
    return app

@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()

@pytest.fixture
def mock_auth():
    """Mock authentication controller."""
    with patch('app.routes.AuthController') as mock:
        yield mock

@pytest.fixture
def mock_instagram_account():
    """Mock Instagram account model."""
    with patch('app.routes.InstagramAccount') as mock:
        yield mock

@pytest.fixture
def mock_user():
    """Mock user model."""
    with patch('app.routes.User') as mock:
        yield mock

@pytest.fixture
def sample_user():
    """Sample user data."""
    return {
        'user_id': 'test_user_id',
        'username': 'test_user'
    }

@pytest.fixture
def sample_account():
    """Sample Instagram account data."""
    return {
        'username': 'test_instagram',
        'user_id': 'test_user_id',
        'session_cookies': {
            'sessionid': 'test_session_id'
        }
    }

class TestRoutes:
    """Test suite for API routes."""
    
    def test_instagram_login_success(self, client, mock_auth, mock_user, mock_instagram_account, sample_user, sample_account):
        """Test successful Instagram login."""
        # Mock responses
        mock_auth.instagram_login.return_value = Mock(cookie_dict=sample_account['session_cookies'])
        mock_user.find_by_username.return_value = Mock(**sample_user)
        mock_instagram_account.find_by_username.return_value = None
        mock_instagram_account.create.return_value = Mock(**sample_account)
        
        response = client.post('/api/auth/instagram', json={
            'username': 'test_instagram',
            'password': 'test_password'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['user']['username'] == sample_user['username']
    
    def test_instagram_login_missing_credentials(self, client):
        """Test Instagram login with missing credentials."""
        response = client.post('/api/auth/instagram', json={})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_instagram_login_failure(self, client, mock_auth):
        """Test failed Instagram login."""
        mock_auth.instagram_login.return_value = None
        
        response = client.post('/api/auth/instagram', json={
            'username': 'test_instagram',
            'password': 'wrong_password'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
    
    def test_get_accounts_success(self, client, mock_instagram_account, sample_account):
        """Test successful account retrieval."""
        mock_instagram_account.find_by_user.return_value = [Mock(**sample_account)]
        
        response = client.get('/api/accounts', headers={
            'Authorization': 'Bearer test_token'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['accounts']) == 1
    
    def test_get_accounts_unauthorized(self, client):
        """Test account retrieval without authorization."""
        response = client.get('/api/accounts')
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data
    
    def test_add_account_success(self, client, mock_instagram_account, sample_account):
        """Test successful account addition."""
        mock_instagram_account.find_by_username.return_value = None
        mock_instagram_account.create.return_value = Mock(**sample_account)
        
        response = client.post('/api/accounts', 
            headers={'Authorization': 'Bearer test_token'},
            json={'username': 'test_instagram'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['account']['username'] == sample_account['username']
    
    def test_add_account_exists(self, client, mock_instagram_account):
        """Test adding existing account."""
        mock_instagram_account.find_by_username.return_value = Mock()
        
        response = client.post('/api/accounts',
            headers={'Authorization': 'Bearer test_token'},
            json={'username': 'existing_account'}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_delete_account_success(self, client, mock_instagram_account):
        """Test successful account deletion."""
        mock_instagram_account.find_by_username.return_value = Mock(
            username='test_instagram',
            user_id='test_user_id'
        )
        
        response = client.delete('/api/accounts/test_instagram',
            headers={'Authorization': 'Bearer test_token'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
    
    def test_delete_account_not_found(self, client, mock_instagram_account):
        """Test deleting non-existent account."""
        mock_instagram_account.find_by_username.return_value = None
        
        response = client.delete('/api/accounts/nonexistent',
            headers={'Authorization': 'Bearer test_token'}
        )
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
    
    def test_get_account_posts_success(self, client, mock_instagram_account):
        """Test successful post retrieval."""
        mock_account = Mock()
        mock_account.user_id = 'test_user_id'
        mock_account.get_latest_posts.return_value = {
            'success': True,
            'posts': [{'id': 'test_post_id'}]
        }
        mock_instagram_account.find_by_username.return_value = mock_account
        
        response = client.get('/api/accounts/test_instagram/posts',
            headers={'Authorization': 'Bearer test_token'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['posts']) == 1
    
    def test_get_account_posts_not_found(self, client, mock_instagram_account):
        """Test post retrieval for non-existent account."""
        mock_instagram_account.find_by_username.return_value = None
        
        response = client.get('/api/accounts/nonexistent/posts',
            headers={'Authorization': 'Bearer test_token'}
        )
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data 