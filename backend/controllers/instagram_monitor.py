import logging
import time
from datetime import datetime, timedelta
from threading import Thread, Event
from models import InstagramAccount, User
from controllers.instagram_crawler import InstagramCrawler
from config import get_config
import threading

logger = logging.getLogger(__name__)
config = get_config()

class InstagramMonitor:
    """Monitor Instagram accounts for new posts."""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.check_interval = config.INSTAGRAM_CHECK_INTERVAL
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._monitored_accounts = set()
    
    def start(self):
        """Start the monitoring service."""
        if self.running:
            return False
            
        self.running = True
        self._stop_event.clear()
        self.thread = Thread(target=self._monitor_loop)
        self.thread.daemon = True
        self.thread.start()
        
        logger.info("Instagram monitor started")
        return True
    
    def stop(self):
        """Stop the monitoring service."""
        if not self.running:
            return False
            
        self._stop_event.set()
        if self.thread:
            self.thread.join()
        self.running = False
        
        logger.info("Instagram monitor stopped")
        return True
    
    def is_running(self):
        """Check if the monitor is running."""
        return self.running
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while not self._stop_event.is_set():
            try:
                self._check_all_accounts()
            except Exception as e:
                logger.error(f"Error in monitor loop: {str(e)}")
            
            # Wait for next check or stop event
            self._stop_event.wait(self.check_interval)
    
    def _check_all_accounts(self):
        """Check all active accounts for new posts."""
        accounts = InstagramAccount.get_all_active()
        
        for account in accounts:
            try:
                self._check_account(account)
            except Exception as e:
                logger.error(f"Error checking account {account.username}: {str(e)}")
    
    def _check_account(self, account):
        """Check an account for new posts."""
        try:
            # Get crawler with account cookies and user's IP
            crawler = InstagramCrawler(
                session_cookies=account.get_cookies(),
                user_ip=account.user_ip  # Use the user's IP from the account
            )
            
            if not crawler.validate_session():
                logger.error(f"Invalid session for account {account.username}")
                return False
            
            # Get latest posts since last check
            since_time = account.last_check or (datetime.utcnow() - timedelta(hours=24))
            result = crawler.get_latest_posts(account.username, since_time)
            
            if not result.get('success'):
                logger.error(f"Failed to get posts for {account.username}: {result.get('error')}")
                return False
            
            new_posts = result.get('posts', [])
            if new_posts:
                logger.info(f"Found {len(new_posts)} new posts for {account.username}")
                # Update last check time
                account.last_check = datetime.utcnow()
                account.save()
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking account {account.username}: {str(e)}")
            return False
    
    def check_now(self, account_id):
        """Check an account for new posts immediately."""
        account = InstagramAccount.find_by_id(account_id)
        if not account:
            return False
            
        return self._check_account(account)
    
    def get_accounts(self, user_id):
        """Get all Instagram accounts for a user."""
        accounts = InstagramAccount.find_by_user(user_id)
        return [account.to_dict() for account in accounts]
    
    def add_account(self, user_id, username, user_ip):
        """Add a new Instagram account to monitor."""
        # Check if account already exists
        existing = InstagramAccount.find_by_username(username)
        if existing:
            return existing.to_dict()
        
        # Create new account
        account = InstagramAccount(
            user_id=user_id,
            username=username,
            user_ip=user_ip,  # Store the user's IP
            active=True,
            last_check=datetime.utcnow()
        )
        account.save()
        
        return account.to_dict()
    
    def remove_account(self, user_id, username):
        """Remove an Instagram account."""
        account = InstagramAccount.find_by_username(username)
        if account and account.user_id == user_id:
            account.delete()
            return True
        return False
    
    def get_account_status(self, user_id, username):
        """Get monitoring status for an account."""
        account = InstagramAccount.find_by_username(username)
        if not account or account.user_id != user_id:
            return None
            
        return {
            'username': account.username,
            'active': account.active,
            'last_check': account.last_check,
            'created_at': account.created_at
        }
    
    def start_monitoring(self, user_id, username):
        """Start monitoring an Instagram account."""
        account = InstagramAccount.find_by_username(username)
        if not account or account.user_id != user_id:
            return False
            
        account.active = True
        account.save()
        return True
    
    def stop_monitoring(self, user_id, username):
        """Stop monitoring an Instagram account."""
        account = InstagramAccount.find_by_username(username)
        if not account or account.user_id != user_id:
            return False
            
        account.active = False
        account.save()
        return True

# Create singleton instance
instagram_monitor = InstagramMonitor() 