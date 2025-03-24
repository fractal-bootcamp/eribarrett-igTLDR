"""
Mock classes for testing Instagram API functionality without making real API calls.
"""
import json
from datetime import datetime

class MockInstagrapiClient:
    """Mock implementation of instagrapi.Client for testing."""
    
    def __init__(self, login_success=True, validate_success=True):
        self.login_success = login_success
        self.validate_success = validate_success
        self.settings = {}
        self.calls = []  # Track method calls
    
    def login(self, username, password):
        """Mock login method."""
        self.calls.append(('login', username, password))
        if not self.login_success:
            raise Exception("Mock login failure")
        self.settings = {
            "sessionid": "test_session_id",
            "csrftoken": "test_csrf_token",
            "ds_user_id": "12345678",
            "mid": "test_mid"
        }
        return True
    
    def login_by_sessionid(self, sessionid):
        """Mock login by session ID."""
        self.calls.append(('login_by_sessionid', sessionid))
        if not self.login_success:
            raise Exception("Mock session login failure")
        return True
    
    def get_settings(self):
        """Mock get settings method."""
        return self.settings
    
    def set_settings(self, settings):
        """Mock set settings method."""
        self.settings = settings
        return True
    
    def get_timeline_feed(self):
        """Mock method to validate session."""
        self.calls.append(('get_timeline_feed',))
        if not self.validate_success:
            raise Exception("Mock session validation failure")
        return {"items": []}
    
    def user_info_by_username(self, username):
        """Mock user info retrieval."""
        self.calls.append(('user_info_by_username', username))
        return MockUserInfo(username)
    
    def user_id_from_username(self, username):
        """Mock user ID retrieval."""
        self.calls.append(('user_id_from_username', username))
        return f"user_{username}"
    
    def user_medias(self, user_id, amount=20):
        """Mock user medias retrieval."""
        self.calls.append(('user_medias', user_id, amount))
        return [MockMedia(i) for i in range(min(5, amount))]


class MockUserInfo:
    """Mock user info object."""
    
    def __init__(self, username):
        self.pk = f"user_{username}"
        self.username = username
        self.full_name = f"Test {username.capitalize()}"
        self.is_private = False
        self.profile_pic_url = f"https://example.com/{username}.jpg"
        self.media_count = 42
        self.follower_count = 1000
        self.following_count = 500


class MockMedia:
    """Mock media object."""
    
    def __init__(self, index):
        self.id = f"media_{index}"
        self.code = f"CODE{index}"
        self.taken_at = datetime.utcnow()
        self.media_type = 1  # 1=Photo, 2=Video, 8=Carousel
        self.product_type = "feed"
        self.thumbnail_url = f"https://example.com/media_{index}.jpg"
        self.caption_text = f"Test caption #{index} #test #instagram"
        self.like_count = 100 + index * 10
        self.comment_count = 20 + index * 5


class MockInstagramClient:
    """Mock version of our InstagramClient wrapper."""
    
    def __init__(self, cookies=None, login_success=True, validate_success=True):
        self.client = MockInstagrapiClient(login_success, validate_success)
        self.cookies = cookies
        
    def login_by_username_password(self, username, password):
        """Mock login with username and password."""
        try:
            success = self.client.login(username, password)
            return {
                'success': success,
                'cookies': self.client.get_settings()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def login_by_cookies(self, cookies):
        """Mock login with cookies."""
        try:
            if isinstance(cookies, str):
                cookies = json.loads(cookies)
            self.client.set_settings(cookies)
            self.client.login_by_sessionid(cookies.get('sessionid'))
            return True
        except Exception:
            return False
    
    def validate_session(self):
        """Mock session validation."""
        try:
            self.client.get_timeline_feed()
            return True
        except Exception:
            return False
    
    def get_user_info(self, username):
        """Mock user info retrieval."""
        try:
            user = self.client.user_info_by_username(username)
            return {
                'success': True,
                'user': {
                    'pk': user.pk,
                    'username': user.username,
                    'full_name': user.full_name,
                    'is_private': user.is_private,
                    'profile_pic_url': user.profile_pic_url,
                    'media_count': user.media_count,
                    'follower_count': user.follower_count,
                    'following_count': user.following_count
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_latest_posts(self, username, since_time=None):
        """Mock latest posts retrieval."""
        try:
            user_id = self.client.user_id_from_username(username)
            medias = self.client.user_medias(user_id, 20)
            
            # Filter by time if needed
            if since_time:
                if isinstance(since_time, str):
                    since_time = datetime.fromisoformat(since_time)
                medias = [media for media in medias if media.taken_at > since_time]
            
            result = []
            for media in medias:
                post = {
                    'id': media.id,
                    'code': media.code,
                    'taken_at': media.taken_at.isoformat(),
                    'media_type': media.media_type,
                    'product_type': media.product_type,
                    'thumbnail_url': media.thumbnail_url,
                    'caption_text': media.caption_text,
                    'like_count': media.like_count,
                    'comment_count': media.comment_count,
                    'url': f"https://www.instagram.com/p/{media.code}/",
                }
                result.append(post)
            
            return {
                'success': True,
                'posts': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def summarize_post(self, post, summary_length='medium'):
        """Mock post summary creation."""
        caption = post.get('caption_text', '')
        
        summary = {
            'url': post.get('url', ''),
            'date': post.get('taken_at', ''),
            'media_type': 'Photo' if post.get('media_type') == 1 else 
                         'Video' if post.get('media_type') == 2 else 
                         'Carousel' if post.get('media_type') == 8 else 'Unknown',
            'likes': post.get('like_count', 0),
            'comments': post.get('comment_count', 0),
        }
        
        if summary_length == 'short':
            summary['caption'] = caption[:50] + '...' if len(caption) > 50 else caption
        elif summary_length == 'medium':
            summary['caption'] = caption[:200] + '...' if len(caption) > 200 else caption
        else:  # long
            summary['caption'] = caption
            
        return summary
        
    def format_notification(self, posts, username, summary_length='medium', include_images=True):
        """Mock notification formatting."""
        if not posts:
            return None
            
        if len(posts) == 1:
            post = posts[0]
            summary = self.summarize_post(post, summary_length)
            
            notification = f"📸 New post from @{username}!\n\n"
            notification += f"📅 {summary['date']}\n"
            notification += f"🖼️ {summary['media_type']}\n"
            notification += f"❤️ {summary['likes']} likes | 💬 {summary['comments']} comments\n\n"
            notification += f"📝 {summary['caption']}\n\n"
            notification += f"🔗 {summary['url']}"
            
            return {
                'text': notification,
                'image_url': post.get('thumbnail_url') if include_images else None
            }
        else:
            notification = f"📸 {len(posts)} new posts from @{username}!\n\n"
            
            for i, post in enumerate(posts[:3], 1):
                summary = self.summarize_post(post, 'short')
                notification += f"{i}. {summary['media_type']} ({summary['date']}): "
                notification += f"{summary['caption']}\n"
                notification += f"   ❤️ {summary['likes']} | 💬 {summary['comments']} | 🔗 {summary['url']}\n\n"
                
            if len(posts) > 3:
                notification += f"... and {len(posts) - 3} more posts."
                
            return {
                'text': notification,
                'image_url': posts[0].get('thumbnail_url') if include_images else None
            } 