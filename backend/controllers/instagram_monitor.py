import logging
import time
import threading
from datetime import datetime, timedelta
from models import InstagramAccount, NotificationSettings, User
from controllers.instagram_client import InstagramClient

logger = logging.getLogger(__name__)

class InstagramMonitor:
    """Service for monitoring Instagram accounts for new posts."""
    
    def __init__(self):
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
        self._clients = {}  # Cache of Instagram clients
        self._stats_cache = {}  # Cache for stats to avoid rate limiting
        self._rate_limit_window = 3600  # 1 hour in seconds
        self._max_requests_per_window = 100  # Max API requests per hour
        self._request_count = 0
        self._last_reset = datetime.utcnow()
    
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
    
    def _check_rate_limit(self):
        """Check if we're within rate limits, and handle accordingly."""
        now = datetime.utcnow()
        
        # Reset counter if window has passed
        if (now - self._last_reset).total_seconds() > self._rate_limit_window:
            self._request_count = 0
            self._last_reset = now
            
        # Check if we're over the limit
        if self._request_count >= self._max_requests_per_window:
            wait_time = self._rate_limit_window - (now - self._last_reset).total_seconds()
            if wait_time > 0:
                logger.warning(f"Rate limit reached. Waiting {wait_time} seconds.")
                return False, wait_time
        
        # Increment counter and return OK
        self._request_count += 1
        return True, 0
    
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
    
    def collect_account_stats(self, account):
        """Collect comprehensive account statistics."""
        try:
            client = self._get_client(account)
            if not client:
                logger.warning(f"Failed to get client for account {account.username}")
                return None
            
            # Check if we have cached stats that are recent enough
            cache_key = f"{account.account_id}_stats"
            if cache_key in self._stats_cache:
                cached_data = self._stats_cache[cache_key]
                cache_time = datetime.fromisoformat(cached_data['timestamp'])
                if (datetime.utcnow() - cache_time).total_seconds() < 3600:  # 1 hour cache
                    return cached_data
            
            # Check rate limits before making requests
            within_limit, wait_time = self._check_rate_limit()
            if not within_limit:
                time.sleep(wait_time)
            
            # Get account info
            user_info = client.get_user_info(account.username)
            if not user_info.get('success'):
                logger.error(f"Failed to get info for {account.username}: {user_info.get('error')}")
                return None
            
            # Get recent posts (limited to avoid rate limits)
            result = client.get_latest_posts(account.username, since_time=None)
            if not result.get('success'):
                logger.error(f"Failed to get posts for {account.username}: {result.get('error')}")
                return None
            
            posts = result.get('posts', [])[:5]  # Limit to 5 most recent posts for stats
            
            # Collect hashtags from posts
            hashtags = []
            for post in posts:
                caption = post.get('caption_text', '')
                if caption:
                    # Extract hashtags from caption
                    tags = [tag.strip('#') for tag in caption.split() if tag.startswith('#')]
                    hashtags.extend(tags)
            
            # Count hashtag frequency
            hashtag_counts = {}
            for tag in hashtags:
                if tag in hashtag_counts:
                    hashtag_counts[tag] += 1
                else:
                    hashtag_counts[tag] = 1
            
            # Sort hashtags by frequency
            sorted_hashtags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)
            top_hashtags = sorted_hashtags[:10]  # Top 10 hashtags
            
            # Compile stats
            stats = {
                'account_id': account.account_id,
                'username': account.username,
                'follower_count': user_info['user']['follower_count'],
                'following_count': user_info['user']['following_count'],
                'media_count': user_info['user']['media_count'],
                'engagement_rate': self._calculate_engagement_rate(posts, user_info['user']['follower_count']),
                'recent_posts': posts,
                'top_hashtags': top_hashtags,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Cache the stats
            self._stats_cache[cache_key] = stats
            
            return stats
            
        except Exception as e:
            logger.error(f"Error collecting stats for account {account.username}: {str(e)}")
            return None
    
    def _calculate_engagement_rate(self, posts, follower_count):
        """Calculate engagement rate based on likes and comments."""
        if not posts or follower_count <= 0:
            return 0
            
        total_likes = sum(post.get('like_count', 0) for post in posts)
        total_comments = sum(post.get('comment_count', 0) for post in posts)
        total_engagement = total_likes + total_comments
        
        # Average engagement per post divided by follower count
        avg_engagement = total_engagement / len(posts)
        engagement_rate = (avg_engagement / follower_count) * 100
        
        return round(engagement_rate, 2)
    
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
            
            # Check rate limits before making requests
            within_limit, wait_time = self._check_rate_limit()
            if not within_limit:
                time.sleep(wait_time)
                
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
            
            # Log notification for now (instead of sending)
            if settings.email_enabled and user.email:
                subject = f"New Instagram Post from @{account.username}"
                content = notification['text']
                
                # Add image if available and enabled
                if notification.get('image_url') and settings.include_images:
                    content = f'<img src="{notification["image_url"]}" style="max-width: 100%"><br><br>{content}'
                    
                logger.info(f"Would send email to {user.email} with subject: {subject}")
            
            # Log Telegram notification
            if settings.telegram_enabled:
                logger.info(f"Would send Telegram notification: {notification['text'][:50]}...")
            
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
                    
                    # Also collect stats periodically (once per day)
                    if not last_check or (datetime.utcnow() - datetime.fromisoformat(last_check)).total_seconds() > 86400:
                        self.collect_account_stats(account)
                    
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