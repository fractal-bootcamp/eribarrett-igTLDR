import os
import json
import uuid
from datetime import datetime

class User:
    """Simple user model for Instagram account monitoring."""
    
    def __init__(self, user_id=None):
        self.user_id = user_id or str(uuid.uuid4())
        self.created_at = datetime.utcnow().isoformat()
    
    @classmethod
    def get_or_create(cls):
        """Get existing user or create a new one."""
        users = cls.get_users()
        if users:
            return users[0]  # Return first user or create new one
        return cls()
    
    @classmethod
    def get_users(cls):
        """Load all users from the file."""
        if not os.path.exists('users.json'):
            return []
            
        with open('users.json', 'r') as f:
            try:
                users_data = json.load(f)
                return [cls(**user_data) for user_data in users_data]
            except json.JSONDecodeError:
                return []
    
    @classmethod
    def save_users(cls, users):
        """Save all users to the file."""
        users_data = [user.to_dict() for user in users]
        with open('users.json', 'w') as f:
            json.dump(users_data, f, indent=2)
    
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
    
    def to_dict(self):
        """Convert user object to dictionary."""
        return {
            'user_id': self.user_id,
            'created_at': self.created_at
        } 