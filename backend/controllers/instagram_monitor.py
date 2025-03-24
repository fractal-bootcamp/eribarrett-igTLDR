import logging
import time
import threading
from datetime import datetime, timedelta
from models import InstagramAccount, NotificationSettings, User
from controllers.instagram_client import InstagramClient
from utils import send_email_notification, send_telegram_notification

logger = logging.getLogger(__name__)

class InstagramMonitor:
    """Service for monitoring Instagram accounts for new posts."""
    
    def __init__(self):
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
        self._clients = {}  # Cache of Instagram clients
    
    def start(self):
        """Start the monitoring service."""
        with self._lock:
            if self._running:
                return False
                
            self._running = True
            self._thread = threading.Thread(target=self._monitor_loop)
            self._thread.daemon = True
            self._thread.start()
            logger.info("Instagram monitor started")
            return True
    
    def stop(self):
        """Stop the monitoring service."""
        with self._lock:
            if not self._running:
                return False
                
            self._running = False
            if self._thread:
                self._thread.join(timeout=1.0)
                self._thread = None
            logger.info("Instagram monitor stopped")
            return True
    
    def is_running(self):
        """Check if the monitoring service is running."""
        with self._lock:
            return self._running
    
    def _get_client(self, account):
        """Get or create an Instagram client for the account."""
        if account.account_id in self._clients:
            client = self._clients[account.account_id]
            # Validate session
            if client.validate_session():
                return client
            else:
                # Session expired, try to login again
                cookies = account.get_cookies()
                if cookies and client.login_by_cookies(cookies):
                    return client
                else:
                    # Login failed, remove client from cache
                    del self._clients[account.account_id]
                    return None
        else:
            # Create new client
            cookies = account.get_cookies()
            if not cookies:
                return None
                
            client = InstagramClient()
            if client.login_by_cookies(cookies):
                self._clients[account.account_id] = client
                return client
            return None
    
    def _check_account(self, account):
        """Check an account for new posts and send notifications."""
        try:
            client = self._get_client(account)
            if not client:
                logger.warning(f"Failed to get client for account {account.username}")
                return False
            
            # Get last check time (or use 24 hours ago if none)
            last_check = account.last_check
            if not last_check:
                last_check = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            
            # Get user's notification settings
            settings = NotificationSettings.find_by_user(account.user_id)
            
            # Get latest posts
            result = client.get_latest_posts(account.username, since_time=last_check)
            if not result.get('success'):
                logger.error(f"Failed to get posts for {account.username}: {result.get('error')}")
                return False
            
            new_posts = result.get('posts', [])
            if not new_posts:
                logger.info(f"No new posts for {account.username}")
                account.update_last_check()
                return True
            
            # Found new posts, send notifications based on user settings
            logger.info(f"Found {len(new_posts)} new posts for {account.username}")
            
            # Get user for email notifications
            user = User.find_by_id(account.user_id)
            if not user:
                logger.error(f"User {account.user_id} not found")
                return False
            
            # Format notification
            notification = client.format_notification(
                new_posts, 
                account.username,
                settings.summary_length,
                settings.include_images
            )
            
            # Send email notification
            if settings.email_enabled and user.email:
                subject = f"New Instagram Post from @{account.username}"
                content = notification['text']
                
                # Add image if available and enabled
                if notification.get('image_url') and settings.include_images:
                    content = f'<img src="{notification["image_url"]}" style="max-width: 100%"><br><br>{content}'
                    
                send_email_notification(user.email, subject, content)
                
            # Send Telegram notification
            if settings.telegram_enabled:
                send_telegram_notification(notification['text'])
            
            # Update last check time
            account.update_last_check()
            return True
            
        except Exception as e:
            logger.error(f"Error checking account {account.username}: {str(e)}")
            return False
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                # Get all active Instagram accounts
                accounts = InstagramAccount.get_accounts()
                active_accounts = [account for account in accounts if account.active]
                
                for account in active_accounts:
                    # Skip if no settings or account is paused
                    settings = NotificationSettings.find_by_user(account.user_id)
                    if not settings:
                        continue
                    
                    # Only check if enough time has passed since last check
                    last_check = account.last_check
                    if last_check:
                        last_check_time = datetime.fromisoformat(last_check)
                        next_check_time = last_check_time + timedelta(minutes=settings.check_interval)
                        if datetime.utcnow() < next_check_time:
                            continue
                    
                    # Check the account for new posts
                    self._check_account(account)
                    
                    # Sleep briefly between accounts to avoid rate limiting
                    time.sleep(5)
                
                # Sleep before next round of checks
                time.sleep(60)  # 1 minute
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {str(e)}")
                time.sleep(60)  # Wait a minute before retrying
    
    def check_now(self, account_id):
        """Force check an account immediately."""
        account = InstagramAccount.find_by_id(account_id)
        if not account:
            return False
        return self._check_account(account)

# Create singleton instance
instagram_monitor = InstagramMonitor() 