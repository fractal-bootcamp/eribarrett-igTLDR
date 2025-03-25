import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from controllers.instagram_crawler import InstagramCrawler
from tests.test_config import TEST_INSTAGRAM_COOKIES, TEST_INSTAGRAM_USERNAME, TEST_INSTAGRAM_USER_IP

@pytest.fixture
def mock_instagram_client():
    """Mock Instagram client."""
    with patch('controllers.instagram_crawler.Client') as mock:
        client = Mock()
        mock.return_value = client
        yield client

@pytest.fixture
def mock_requests():
    """Mock requests library."""
    with patch('controllers.instagram_crawler.requests') as mock:
        yield mock

@pytest.fixture
def mock_subprocess():
    """Mock subprocess for network namespace operations."""
    with patch('controllers.instagram_crawler.subprocess') as mock:
        yield mock

@pytest.fixture
def sample_cookies():
    """Sample Instagram session cookies."""
    return TEST_INSTAGRAM_COOKIES

@pytest.fixture
def user_ip():
    """Test user IP."""
    return TEST_INSTAGRAM_USER_IP

class TestInstagramCrawler:
    """Test cases for InstagramCrawler."""
    
    def test_init_with_cookies(self, mock_instagram_client, sample_cookies):
        """Test crawler initialization with cookies."""
        crawler = InstagramCrawler(sample_cookies)
        mock_instagram_client.cookie_dict = sample_cookies
        assert crawler.client.cookie_dict == sample_cookies
    
    def test_session_cookie_management(self, mock_instagram_client, sample_cookies):
        """Test session cookie management."""
        crawler = InstagramCrawler(sample_cookies)
        mock_instagram_client.get_timeline_feed.return_value = True
        mock_instagram_client.user_id = '123'
        mock_instagram_client.username = TEST_INSTAGRAM_USERNAME
        
        # Test successful cookie login
        assert crawler.set_session_cookies(sample_cookies) is True
        
        # Test failed cookie login
        mock_instagram_client.get_timeline_feed.side_effect = Exception('Invalid session')
        assert crawler.set_session_cookies(sample_cookies) is False
    
    def test_user_ip_management(self, mock_subprocess, user_ip):
        """Test user IP management."""
        crawler = InstagramCrawler({}, user_ip)
        mock_subprocess.run.return_value.returncode = 0
        
        # Test successful IP setup
        assert crawler.setup_user_ip() is True
        
        # Test failed IP setup
        mock_subprocess.run.return_value.returncode = 1
        assert crawler.setup_user_ip() is False
    
    def test_user_info_retrieval(self, mock_instagram_client, sample_cookies):
        """Test user info retrieval."""
        crawler = InstagramCrawler(sample_cookies)
        mock_user = Mock()
        mock_user.pk = '123'
        mock_user.username = TEST_INSTAGRAM_USERNAME
        mock_user.full_name = 'Test User'
        mock_user.is_private = False
        mock_user.profile_pic_url = 'http://example.com/pic.jpg'
        mock_user.media_count = 100
        mock_user.follower_count = 1000
        mock_user.following_count = 500
        
        mock_instagram_client.user_info_by_username.return_value = mock_user
        
        result = crawler.get_user_info(TEST_INSTAGRAM_USERNAME)
        assert result['success'] is True
        assert result['user']['username'] == TEST_INSTAGRAM_USERNAME
    
    def test_latest_posts_retrieval(self, mock_instagram_client, sample_cookies):
        """Test latest posts retrieval."""
        crawler = InstagramCrawler(sample_cookies)
        mock_instagram_client.user_id_from_username.return_value = '123'
        
        # Mock media items
        mock_media = Mock()
        mock_media.id = '456'
        mock_media.code = 'abc123'
        mock_media.taken_at = datetime.now()
        mock_media.media_type = 1
        mock_media.thumbnail_url = 'http://example.com/thumb.jpg'
        mock_media.caption_text = 'Test post'
        mock_media.like_count = 100
        mock_media.comment_count = 10
        
        mock_instagram_client.user_medias.return_value = [mock_media]
        
        result = crawler.get_latest_posts(TEST_INSTAGRAM_USERNAME)
        assert result['success'] is True
        assert len(result['posts']) == 1
        assert result['posts'][0]['code'] == 'abc123'
    
    def test_session_validation(self, mock_instagram_client, sample_cookies):
        """Test session validation."""
        crawler = InstagramCrawler(sample_cookies)
        
        # Test valid session
        mock_instagram_client.get_timeline_feed.return_value = True
        assert crawler.validate_session() is True
        
        # Test invalid session
        mock_instagram_client.get_timeline_feed.side_effect = Exception('Invalid session')
        assert crawler.validate_session() is False
    
    def test_cleanup_network_namespace(self, mock_subprocess, user_ip):
        """Test network namespace cleanup."""
        crawler = InstagramCrawler({}, user_ip)
        mock_subprocess.run.return_value.returncode = 0
        
        # Test successful cleanup
        assert crawler.cleanup_network_namespace() is True
        
        # Test failed cleanup
        mock_subprocess.run.return_value.returncode = 1
        assert crawler.cleanup_network_namespace() is False 