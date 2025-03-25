import os
import json
import uuid
import datetime
from utils import encrypt_data, decrypt_data
from typing import Dict, List, Optional
from controllers.instagram_crawler import InstagramCrawler

ACCOUNTS_FILE = 'instagram_accounts.json'

class InstagramAccount:
    """Model for Instagram account data."""
    
    def __init__(self, username: str, user_id: str, session_cookies: Dict = None):
        self.username = username
        self.user_id = user_id
        self.session_cookies = session_cookies or {}
        self.last_check = None
        self.crawler = InstagramCrawler(session_cookies=session_cookies)
    
    @classmethod
    def create(cls, username: str, user_id: str, session_cookies: Dict = None) -> 'InstagramAccount':
        """Create a new Instagram account."""
        account = cls(username, user_id, session_cookies)
        account.save()
        return account
    
    @classmethod
    def find_by_username(cls, username: str) -> Optional['InstagramAccount']:
        """Find an Instagram account by username."""
        data = cls._load_data()
        account_data = data.get(username)
        if account_data:
            account = cls(
                username=account_data['username'],
                user_id=account_data['user_id'],
                session_cookies=account_data.get('session_cookies', {})
            )
            account.last_check = account_data.get('last_check')
            return account
        return None
    
    @classmethod
    def find_by_user(cls, user_id: str) -> List['InstagramAccount']:
        """Find all Instagram accounts for a user."""
        data = cls._load_data()
        return [
            cls(
                username=account_data['username'],
                user_id=account_data['user_id'],
                session_cookies=account_data.get('session_cookies', {})
            )
            for account_data in data.values()
            if account_data['user_id'] == user_id
        ]
    
    def update_session_cookies(self, cookies: Dict):
        """Update session cookies for the account."""
        self.session_cookies = cookies
        self.crawler = InstagramCrawler(session_cookies=cookies)
        self.save()
    
    def get_latest_posts(self, since_time: Optional[str] = None) -> Dict:
        """Get latest posts from the account."""
        try:
            # Validate session
            if not self.crawler.validate_session():
                return {
                    'success': False,
                    'error': 'Invalid session'
                }
            
            # Get posts
            result = self.crawler.get_latest_posts(self.username, since_time)
            
            if result['success']:
                self.last_check = datetime.now().isoformat()
                self.save()
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user_info(self) -> Dict:
        """Get user information."""
        try:
            # Validate session
            if not self.crawler.validate_session():
                return {
                    'success': False,
                    'error': 'Invalid session'
                }
            
            return self.crawler.get_user_info(self.username)
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete(self):
        """Delete the Instagram account."""
        data = self._load_data()
        if self.username in data:
            del data[self.username]
            self._save_data(data)
    
    def save(self):
        """Save the Instagram account data."""
        data = self._load_data()
        data[self.username] = {
            'username': self.username,
            'user_id': self.user_id,
            'session_cookies': self.session_cookies,
            'last_check': self.last_check
        }
        self._save_data(data)
    
    def to_dict(self) -> Dict:
        """Convert account to dictionary."""
        return {
            'username': self.username,
            'user_id': self.user_id,
            'last_check': self.last_check
        }
    
    @staticmethod
    def _load_data() -> Dict:
        """Load Instagram account data from file."""
        data_file = 'data/instagram_accounts.json'
        if os.path.exists(data_file):
            with open(data_file, 'r') as f:
                return json.load(f)
        return {}
    
    @staticmethod
    def _save_data(data: Dict):
        """Save Instagram account data to file."""
        os.makedirs('data', exist_ok=True)
        with open('data/instagram_accounts.json', 'w') as f:
            json.dump(data, f, indent=2) 