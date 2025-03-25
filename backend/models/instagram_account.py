import os
import json
from datetime import datetime
from config import get_config

config = get_config()

def _load_data() -> dict:
    """Load account data from file."""
    data_file = os.path.join(config.DATA_DIR, 'instagram_accounts.json')
    if os.path.exists(data_file):
        with open(data_file, 'r') as f:
            return json.load(f)
    return {}

def _save_data(data: dict):
    """Save account data to file."""
    data_file = os.path.join(config.DATA_DIR, 'instagram_accounts.json')
    os.makedirs(os.path.dirname(data_file), exist_ok=True)
    with open(data_file, 'w') as f:
        json.dump(data, f, indent=2)

class InstagramAccount:
    """Model for Instagram account data."""
    
    def __init__(self, username: str, user_id: str, user_ip: str = None):
        self.username = username
        self.user_id = user_id
        self.user_ip = user_ip
        self.session_cookies = {}
        self.last_check = datetime.utcnow().isoformat()
        self._crawler = None
    
    @property
    def crawler(self):
        """Lazy load the crawler to avoid circular imports."""
        if self._crawler is None:
            from controllers.instagram_crawler import InstagramCrawler
            self._crawler = InstagramCrawler(self.session_cookies, self.user_ip)
        return self._crawler
    
    def save(self):
        """Save account to file."""
        data = _load_data()
        data[self.username] = self.to_dict()
        _save_data(data)
    
    def delete(self):
        """Delete account from file."""
        data = _load_data()
        if self.username in data:
            del data[self.username]
            _save_data(data)
    
    def update_session_cookies(self, cookies: dict):
        """Update session cookies."""
        self.session_cookies = cookies
        self._crawler = None  # Reset crawler to use new cookies
        self.save()
    
    def get_latest_posts(self):
        """Get latest posts using crawler."""
        if not self.crawler.validate_session():
            return {
                'success': False,
                'error': 'Invalid session'
            }
        
        try:
            posts = self.crawler.get_latest_posts()
            self.last_check = datetime.utcnow().isoformat()
            self.save()
            return {
                'success': True,
                'posts': posts
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def to_dict(self) -> dict:
        """Convert account to dictionary."""
        return {
            'username': self.username,
            'user_id': self.user_id,
            'user_ip': self.user_ip,
            'session_cookies': self.session_cookies,
            'last_check': self.last_check
        }
    
    @classmethod
    def create(cls, username: str, user_id: str, user_ip: str = None) -> 'InstagramAccount':
        """Create a new Instagram account."""
        account = cls(username=username, user_id=user_id, user_ip=user_ip)
        account.save()
        return account
    
    @classmethod
    def find_by_username(cls, username: str) -> 'InstagramAccount':
        """Find an account by username."""
        data = _load_data()
        account_data = data.get(username)
        if account_data:
            return cls(**account_data)
        return None
    
    @classmethod
    def find_by_user(cls, user_id: str) -> list:
        """Find all accounts for a user."""
        data = _load_data()
        return [
            cls(**account_data)
            for account_data in data.values()
            if account_data.get('user_id') == user_id
        ] 