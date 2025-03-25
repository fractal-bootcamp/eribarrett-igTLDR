import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from controllers.instagram_crawler import InstagramCrawler

@pytest.fixture
def mock_instagram_client():
    """Mock Instagram client for testing."""
    with patch('controllers.instagram_crawler.Client') as mock:
        client = Mock()
        mock.return_value = client
        yield client

@pytest.fixture
def sample_cookies():
    """Sample Instagram session cookies."""
    return {
        'sessionid': 'test_session_id',
        'ds_user_id': 'test_user_id',
        'csrftoken': 'test_csrf_token'
    }

class TestInstagramCrawler:
    """Test suite for InstagramCrawler class."""
    
    def test_init_with_cookies(self, mock_instagram_client, sample_cookies):
        """Test crawler initialization with cookies."""
        crawler = InstagramCrawler(session_cookies=sample_cookies)
        assert crawler.client.cookie_dict == sample_cookies
    
    def test_set_session_cookies_success(self, mock_instagram_client, sample_cookies):
        """Test successful session cookie setting."""
        mock_instagram_client.get_timeline_feed.return_value = True
        mock_instagram_client.user_id = 'test_user_id'
        mock_instagram_client.username = 'test_username'
        
        crawler = InstagramCrawler()
        result = crawler.set_session_cookies(sample_cookies)
        
        assert result is True
        assert crawler.client.cookie_dict == sample_cookies
    
    def test_set_session_cookies_invalid(self, mock_instagram_client, sample_cookies):
        """Test invalid session cookie handling."""
        mock_instagram_client.get_timeline_feed.side_effect = Exception('Invalid session')
        
        crawler = InstagramCrawler()
        result = crawler.set_session_cookies(sample_cookies)
        
        assert result is False
    
    def test_get_user_info_success(self, mock_instagram_client):
        """Test successful user info retrieval."""
        mock_user = Mock()
        mock_user.pk = 'test_pk'
        mock_user.username = 'test_username'
        mock_user.full_name = 'Test User'
        mock_user.is_private = False
        mock_user.profile_pic_url = 'http://example.com/pic.jpg'
        mock_user.media_count = 100
        mock_user.follower_count = 1000
        mock_user.following_count = 500
        
        mock_instagram_client.user_info_by_username.return_value = mock_user
        
        crawler = InstagramCrawler()
        result = crawler.get_user_info('test_username')
        
        assert result['success'] is True
        assert result['user']['username'] == 'test_username'
        assert result['user']['follower_count'] == 1000
    
    def test_get_user_info_failure(self, mock_instagram_client):
        """Test failed user info retrieval."""
        mock_instagram_client.user_info_by_username.side_effect = Exception('User not found')
        
        crawler = InstagramCrawler()
        result = crawler.get_user_info('nonexistent_user')
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_get_latest_posts_success(self, mock_instagram_client):
        """Test successful post retrieval."""
        mock_media = Mock()
        mock_media.id = 'test_id'
        mock_media.code = 'test_code'
        mock_media.taken_at = datetime.now()
        mock_media.media_type = 1
        mock_media.thumbnail_url = 'http://example.com/thumb.jpg'
        mock_media.caption_text = 'Test caption'
        mock_media.like_count = 100
        mock_media.comment_count = 50
        
        mock_instagram_client.user_id_from_username.return_value = 'test_user_id'
        mock_instagram_client.user_medias.return_value = [mock_media]
        
        crawler = InstagramCrawler()
        result = crawler.get_latest_posts('test_username')
        
        assert result['success'] is True
        assert len(result['posts']) == 1
        assert result['posts'][0]['id'] == 'test_id'
    
    def test_get_latest_posts_failure(self, mock_instagram_client):
        """Test failed post retrieval."""
        mock_instagram_client.user_id_from_username.side_effect = Exception('Failed to get user ID')
        
        crawler = InstagramCrawler()
        result = crawler.get_latest_posts('test_username')
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_validate_session_success(self, mock_instagram_client):
        """Test successful session validation."""
        mock_instagram_client.get_timeline_feed.return_value = True
        
        crawler = InstagramCrawler()
        result = crawler.validate_session()
        
        assert result is True
    
    def test_validate_session_failure(self, mock_instagram_client):
        """Test failed session validation."""
        mock_instagram_client.get_timeline_feed.side_effect = Exception('Invalid session')
        
        crawler = InstagramCrawler()
        result = crawler.validate_session()
        
        assert result is False 