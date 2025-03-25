import json
import os
import uuid
import jwt
from datetime import datetime, timedelta
from config import get_config

config = get_config()

class User:
    """User model for authentication and management."""
    
    def __init__(self, username: str, user_id: str = None, created_at: str = None):
        self.user_id = user_id or str(uuid.uuid4())
        self.username = username
        self.created_at = created_at or datetime.utcnow().isoformat()
    
    def save(self):
        """Save user to file."""
        data = self._load_data()
        data[self.user_id] = self.to_dict()
        self._save_data(data)
    
    def delete(self):
        """Delete user from file."""
        data = self._load_data()
        if self.user_id in data:
            del data[self.user_id]
            self._save_data(data)
    
    def generate_token(self) -> str:
        """Generate a JWT token for the user."""
        payload = {
            'user_id': self.user_id,
            'exp': datetime.utcnow() + timedelta(days=1)
        }
        return jwt.encode(payload, config.SECRET_KEY, algorithm='HS256')
    
    def to_dict(self) -> dict:
        """Convert user to dictionary."""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'created_at': self.created_at
        }
    
    @classmethod
    def find_by_id(cls, user_id: str) -> 'User':
        """Find a user by ID."""
        data = cls._load_data()
        user_data = data.get(user_id)
        if user_data:
            return cls(**{k: v for k, v in user_data.items() if k != 'created_at'})
        return None
    
    @classmethod
    def get_by_token(cls, token: str) -> 'User':
        """Get a user by their JWT token."""
        try:
            payload = jwt.decode(token, config.SECRET_KEY, algorithms=['HS256'])
            return cls.find_by_id(payload['user_id'])
        except jwt.InvalidTokenError:
            return None
    
    @classmethod
    def find_by_username(cls, username: str) -> 'User':
        """Find a user by username."""
        data = cls._load_data()
        for user_data in data.values():
            if user_data.get('username') == username:
                return cls(**{k: v for k, v in user_data.items() if k != 'created_at'})
        return None
    
    @classmethod
    def get_or_create(cls, username: str) -> 'User':
        """Get existing user or create new one."""
        user = cls.find_by_username(username)
        if not user:
            user = cls(username=username)
            user.save()
        return user
    
    @staticmethod
    def verify_token(token: str) -> str:
        """Verify a JWT token and return user_id."""
        try:
            payload = jwt.decode(token, config.SECRET_KEY, algorithms=['HS256'])
            return payload['user_id']
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def _load_data() -> dict:
        """Load user data from file."""
        if not os.path.exists(config.DATA_DIR):
            os.makedirs(config.DATA_DIR)
        
        user_file = os.path.join(config.DATA_DIR, 'users.json')
        if os.path.exists(user_file):
            with open(user_file, 'r') as f:
                return json.load(f)
        return {}
    
    @staticmethod
    def _save_data(data: dict):
        """Save user data to file."""
        user_file = os.path.join(config.DATA_DIR, 'users.json')
        with open(user_file, 'w') as f:
            json.dump(data, f, indent=2) 