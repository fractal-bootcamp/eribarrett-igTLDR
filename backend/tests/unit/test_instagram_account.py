import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from models.instagram_account import InstagramAccount

@pytest.fixture
def sample_account_data():
    """Sample Instagram account data."""
    return {
        'username': 'test_user',
        'user_id': 'test_user_id',
        'user_ip': '127.0.0.1',
        'session_cookies': {
            'sessionid': 'test_session_id',
            'ds_user_id': 'test_user_id',
            'csrftoken': 'test_csrf_token'
        },
        'last_check': datetime.now().isoformat()
    }

@pytest.fixture
def mock_crawler():
    """Mock Instagram crawler."""
    with patch('models.instagram_account.InstagramCrawler') as mock:
        crawler = Mock()
        mock.return_value = crawler
        yield crawler

class TestInstagramAccount:
    """Test suite for InstagramAccount model."""
    
    def test_create_account(self, mock_crawler, sample_account_data):
        """Test account creation."""
        account = InstagramAccount.create(
            username=sample_account_data['username'],
            user_id=sample_account_data['user_id'],
            user_ip=sample_account_data['user_ip']
        )
        
        assert account.username == sample_account_data['username']
        assert account.user_id == sample_account_data['user_id']
        assert account.user_ip == sample_account_data['user_ip']
        assert account.session_cookies == {}
        assert account.last_check is not None
    
    def test_find_by_username(self, mock_crawler, sample_account_data):
        """Test finding account by username."""
        # Mock the data file content
        with patch('models.instagram_account._load_data') as mock_load:
            mock_load.return_value = {
                sample_account_data['username']: sample_account_data
            }
            
            account = InstagramAccount.find_by_username(sample_account_data['username'])
            
            assert account is not None
            assert account.username == sample_account_data['username']
            assert account.user_id == sample_account_data['user_id']
            assert account.user_ip == sample_account_data['user_ip']
    
    def test_find_by_user(self, mock_crawler, sample_account_data):
        """Test finding accounts by user ID."""
        # Mock the data file content
        with patch('models.instagram_account._load_data') as mock_load:
            mock_load.return_value = {
                sample_account_data['username']: sample_account_data
            }
            
            accounts = InstagramAccount.find_by_user(sample_account_data['user_id'])
            
            assert len(accounts) == 1
            assert accounts[0].username == sample_account_data['username']
            assert accounts[0].user_id == sample_account_data['user_id']
            assert accounts[0].user_ip == sample_account_data['user_ip']
    
    def test_update_session_cookies(self, mock_crawler, sample_account_data):
        """Test updating session cookies."""
        account = InstagramAccount(
            username=sample_account_data['username'],
            user_id=sample_account_data['user_id'],
            user_ip=sample_account_data['user_ip']
        )
        
        new_cookies = {'sessionid': 'new_session_id'}
        account.update_session_cookies(new_cookies)
        
        assert account.session_cookies == new_cookies
        assert account._crawler is None  # Crawler should be reset
    
    def test_get_latest_posts_success(self, mock_crawler, sample_account_data):
        """Test successful post retrieval."""
        account = InstagramAccount(
            username=sample_account_data['username'],
            user_id=sample_account_data['user_id'],
            user_ip=sample_account_data['user_ip']
        )
        
        mock_crawler.validate_session.return_value = True
        mock_crawler.get_latest_posts.return_value = [{'id': 'test_post_id'}]
        
        result = account.get_latest_posts()
        
        assert result['success'] is True
        assert len(result['posts']) == 1
        assert result['posts'][0]['id'] == 'test_post_id'
        assert account.last_check is not None
    
    def test_get_latest_posts_invalid_session(self, mock_crawler, sample_account_data):
        """Test post retrieval with invalid session."""
        account = InstagramAccount(
            username=sample_account_data['username'],
            user_id=sample_account_data['user_id'],
            user_ip=sample_account_data['user_ip']
        )
        
        mock_crawler.validate_session.return_value = False
        
        result = account.get_latest_posts()
        
        assert result['success'] is False
        assert result['error'] == 'Invalid session'
    
    def test_get_user_info_success(self, mock_crawler, sample_account_data):
        """Test successful user info retrieval."""
        account = InstagramAccount(
            username=sample_account_data['username'],
            user_id=sample_account_data['user_id'],
            session_cookies=sample_account_data['session_cookies']
        )
        
        mock_crawler.validate_session.return_value = True
        mock_crawler.get_user_info.return_value = {
            'success': True,
            'user': {
                'username': 'test_user',
                'follower_count': 1000
            }
        }
        
        result = account.get_user_info()
        
        assert result['success'] is True
        assert result['user']['username'] == 'test_user'
        assert result['user']['follower_count'] == 1000
    
    def test_get_user_info_invalid_session(self, mock_crawler, sample_account_data):
        """Test user info retrieval with invalid session."""
        account = InstagramAccount(
            username=sample_account_data['username'],
            user_id=sample_account_data['user_id'],
            session_cookies=sample_account_data['session_cookies']
        )
        
        mock_crawler.validate_session.return_value = False
        
        result = account.get_user_info()
        
        assert result['success'] is False
        assert result['error'] == 'Invalid session'
    
    def test_delete_account(self, sample_account_data):
        """Test account deletion."""
        with patch('models.instagram_account._load_data') as mock_load, \
             patch('models.instagram_account._save_data') as mock_save:
            
            mock_load.return_value = {
                sample_account_data['username']: sample_account_data
            }
            
            account = InstagramAccount(
                username=sample_account_data['username'],
                user_id=sample_account_data['user_id'],
                user_ip=sample_account_data['user_ip']
            )
            
            account.delete()
            
            mock_save.assert_called_once()
            assert sample_account_data['username'] not in mock_save.call_args[0][0]
    
    def test_save_account(self, sample_account_data):
        """Test account saving."""
        with patch('models.instagram_account._load_data') as mock_load, \
             patch('models.instagram_account._save_data') as mock_save:
            
            mock_load.return_value = {}
            
            account = InstagramAccount(
                username=sample_account_data['username'],
                user_id=sample_account_data['user_id'],
                user_ip=sample_account_data['user_ip']
            )
            
            account.save()
            
            mock_save.assert_called_once()
            saved_data = mock_save.call_args[0][0]
            assert saved_data[sample_account_data['username']]['username'] == sample_account_data['username']
            assert saved_data[sample_account_data['username']]['user_id'] == sample_account_data['user_id']
            assert saved_data[sample_account_data['username']]['user_ip'] == sample_account_data['user_ip'] 