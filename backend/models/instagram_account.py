import os
import json
import uuid
import datetime
from utils import encrypt_data, decrypt_data

ACCOUNTS_FILE = 'instagram_accounts.json'

class InstagramAccount:
    """Instagram account model for storing encrypted session cookies."""
    
    def __init__(self, user_id, username, encrypted_cookies, account_id=None, 
                 last_check=None, created_at=None, active=True):
        self.account_id = account_id or str(uuid.uuid4())
        self.user_id = user_id
        self.username = username
        self.encrypted_cookies = encrypted_cookies
        self.last_check = last_check
        self.created_at = created_at or datetime.datetime.utcnow().isoformat()
        self.active = active
    
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
    def find_by_id(cls, account_id):
        """Find an account by ID."""
        accounts = cls.get_accounts()
        for account in accounts:
            if account.account_id == account_id:
                return account
        return None
    
    @classmethod
    def find_by_username(cls, username, user_id=None):
        """Find an account by username and optionally filter by user_id."""
        accounts = cls.get_accounts()
        for account in accounts:
            if account.username == username:
                if user_id is None or account.user_id == user_id:
                    return account
        return None
    
    @classmethod
    def find_by_user(cls, user_id):
        """Find all accounts for a specific user."""
        accounts = cls.get_accounts()
        return [account for account in accounts if account.user_id == user_id]
    
    def save(self):
        """Save the account to the database."""
        accounts = self.get_accounts()
        
        # Check if account already exists
        for i, account in enumerate(accounts):
            if account.account_id == self.account_id:
                # Update existing account
                accounts[i] = self
                self.save_accounts(accounts)
                return True
        
        # Add new account
        accounts.append(self)
        self.save_accounts(accounts)
        return True
    
    def delete(self):
        """Delete the account from the database."""
        accounts = self.get_accounts()
        accounts = [account for account in accounts if account.account_id != self.account_id]
        self.save_accounts(accounts)
        return True
    
    def to_dict(self):
        """Convert account object to dictionary."""
        return {
            'account_id': self.account_id,
            'user_id': self.user_id,
            'username': self.username,
            'encrypted_cookies': self.encrypted_cookies,
            'last_check': self.last_check,
            'created_at': self.created_at,
            'active': self.active
        }
    
    def get_cookies(self):
        """Decrypt and return the session cookies."""
        if not self.encrypted_cookies:
            return None
        return decrypt_data(self.encrypted_cookies)
    
    def update_cookies(self, cookies):
        """Encrypt and update the session cookies."""
        self.encrypted_cookies = encrypt_data(cookies)
        return self.save()
    
    def update_last_check(self):
        """Update the last check timestamp."""
        self.last_check = datetime.datetime.utcnow().isoformat()
        return self.save() 