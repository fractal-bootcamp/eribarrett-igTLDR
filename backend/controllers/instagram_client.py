import json
import time
import logging
from datetime import datetime, timedelta
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ClientError

logger = logging.getLogger(__name__)

class InstagramClient:
    """Instagram API client wrapper using instagrapi."""
    
    def __init__(self, cookies=None):
        self.client = Client()
        if cookies:
            self.login_by_cookies(cookies)
    
    def login_by_username_password(self, username, password):
        """Login to Instagram using username and password."""
        try:
            self.client.login(username, password)
            return {
                'success': True,
                'cookies': self.client.get_settings()
            }
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def login_by_cookies(self, cookies):
        """Login to Instagram using session cookies."""
        try:
            if isinstance(cookies, str):
                cookies = json.loads(cookies)
            self.client.set_settings(cookies)
            self.client.login_by_sessionid(cookies.get('sessionid'))
            return True
        except Exception as e:
            logger.error(f"Login by cookies failed: {str(e)}")
            return False
    
    def validate_session(self):
        """Check if the current session is valid."""
        try:
            self.client.get_timeline_feed()
            return True
        except (LoginRequired, ClientError):
            return False
        except Exception as e:
            logger.error(f"Session validation error: {str(e)}")
            return False
    
    def get_user_info(self, username):
        """Get user information by username."""
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
            logger.error(f"Get user info failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_latest_posts(self, username, since_time=None):
        """Get latest posts from a user since a specific time."""
        try:
            user_id = self.client.user_id_from_username(username)
            medias = self.client.user_medias(user_id, 20)  # Get last 20 posts
            
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
                    'product_type': media.product_type if hasattr(media, 'product_type') else None,
                    'thumbnail_url': media.thumbnail_url,
                    'caption_text': media.caption_text if media.caption_text else '',
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
            logger.error(f"Get latest posts failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            } 