import os
import json
import uuid
import datetime
import jwt
from config import get_config
from utils import encrypt_data, decrypt_data

config = get_config()
USER_FILE = 'users.json'

class User:
    """User model for authentication and session management."""
    
    def __init__(self, username, email, password_hash=None, user_id=None, created_at=None):
        self.user_id = user_id or str(uuid.uuid4())
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at or datetime.datetime.utcnow().isoformat()
    
    @classmethod
    def get_users(cls):
        """Load all users from the file."""
        if not os.path.exists(USER_FILE):
            return []
            
        with open(USER_FILE, 'r') as f:
            try:
                users_data = json.load(f)
                return [cls(**user_data) for user_data in users_data]
            except json.JSONDecodeError:
                return []
    
    @classmethod
    def save_users(cls, users):
        """Save all users to the file."""
        users_data = [user.to_dict() for user in users]
        with open(USER_FILE, 'w') as f:
            json.dump(users_data, f, indent=2)
    
    @classmethod
    def find_by_username(cls, username):
        """Find a user by username."""
        users = cls.get_users()
        for user in users:
            if user.username == username:
                return user
        return None
    
    @classmethod
    def find_by_email(cls, email):
        """Find a user by email."""
        users = cls.get_users()
        for user in users:
            if user.email == email:
                return user
        return None
    
    @classmethod
    def find_by_id(cls, user_id):
        """Find a user by ID."""
        users = cls.get_users()
        for user in users:
            if user.user_id == user_id:
                return user
        return None
    
    def save(self):
        """Save the user to the database."""
        users = self.get_users()
        
        # Check if user already exists
        for i, user in enumerate(users):
            if user.user_id == self.user_id:
                # Update existing user
                users[i] = self
                self.save_users(users)
                return True
        
        # Add new user
        users.append(self)
        self.save_users(users)
        return True
    
    def delete(self):
        """Delete the user from the database."""
        users = self.get_users()
        users = [user for user in users if user.user_id != self.user_id]
        self.save_users(users)
        return True
    
    def to_dict(self):
        """Convert user object to dictionary."""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'created_at': self.created_at
        }
    
    def generate_token(self):
        """Generate JWT token for authentication."""
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=config.JWT_ACCESS_TOKEN_EXPIRES),
            'iat': datetime.datetime.utcnow(),
            'sub': self.user_id
        }
        return jwt.encode(
            payload,
            config.JWT_SECRET_KEY,
            algorithm='HS256'
        )
    
    @staticmethod
    def verify_token(token):
        """Verify JWT token and return user_id if valid."""
        try:
            payload = jwt.decode(
                token,
                config.JWT_SECRET_KEY,
                algorithms=['HS256']
            )
            return payload['sub']
        except jwt.ExpiredSignatureError:
            return None  # Token expired
        except jwt.InvalidTokenError:
            return None  # Invalid token 