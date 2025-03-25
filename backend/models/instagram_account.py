import os
import json
import uuid
import datetime
from utils import encrypt_data, decrypt_data
from typing import Dict, List, Optional

ACCOUNTS_FILE = 'instagram_accounts.json'

class InstagramAccount:
    """Instagram account model for storing encrypted session cookies."""
    
    def __init__(self, account_id: str, user_id: str, username: str, user_ip: str, cookies: Dict = None, active: bool = True, last_check: datetime = None, created_at: datetime = None):
        self.account_id = account_id
        self.user_id = user_id
        self.username = username
        self.user_ip = user_ip  # Store user's IP address
        self.cookies = cookies or {}
        self.active = active
        self.last_check = last_check or datetime.datetime.utcnow()
        self.created_at = created_at or datetime.datetime.utcnow()
    
    @classmethod
    def get_accounts(cls):
        """Load all accounts from the file."""
        if not os.path.exists(ACCOUNTS_FILE):
            return []
            
        with open(ACCOUNTS_FILE, 'r') as f:
            try:
                accounts_data = json.load(f)
                return [cls(**account_data) for account_data in accounts_data]
            except json.JSONDecodeError:
                return []
    
    @classmethod
    def save_accounts(cls, accounts):
        """Save all accounts to the file."""
        accounts_data = [account.to_dict() for account in accounts]
        with open(ACCOUNTS_FILE, 'w') as f:
            json.dump(accounts_data, f, indent=2)
    
    @classmethod
    def find_by_id(cls, account_id: str) -> Optional['InstagramAccount']:
        """Find an Instagram account by ID."""
        accounts = cls.get_accounts()
        return next((acc for acc in accounts if acc.account_id == account_id), None)
    
    @classmethod
    def find_by_username(cls, username: str) -> Optional['InstagramAccount']:
        """Find an Instagram account by username."""
        accounts = cls.get_accounts()
        return next((acc for acc in accounts if acc.username == username), None)
    
    @classmethod
    def find_by_user(cls, user_id: str) -> List['InstagramAccount']:
        """Find all Instagram accounts for a user."""
        accounts = cls.get_accounts()
        return [acc for acc in accounts if acc.user_id == user_id]
    
    def save(self):
        """Save the Instagram account data."""
        accounts = self.get_accounts()
        
        # Update existing account or add new one
        found = False
        for i, acc in enumerate(accounts):
            if acc.account_id == self.account_id:
                accounts[i] = self
                found = True
                break
        
        if not found:
            accounts.append(self)
        
        # Save to file
        self.save_accounts(accounts)
        return True
    
    def delete(self):
        """Delete the Instagram account."""
        accounts = self.get_accounts()
        accounts = [acc for acc in accounts if acc.account_id != self.account_id]
        self.save_accounts(accounts)
        return True
    
    def to_dict(self) -> Dict:
        """Convert the account to a dictionary."""
        return {
            'account_id': self.account_id,
            'user_id': self.user_id,
            'username': self.username,
            'user_ip': self.user_ip,
            'active': self.active,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def get_cookies(self) -> Dict:
        """Get the account's cookies."""
        return self.cookies
    
    def update_cookies(self, cookies):
        """Encrypt and update the session cookies."""
        self.cookies = cookies
        return self.save()
    
    def update_last_check(self):
        """Update the last check timestamp."""
        self.last_check = datetime.datetime.utcnow()
        return self.save() 