import json
import time
import random
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from instagrapi.exceptions import (
    ClientError,
    LoginRequired,
    ClientConnectionError,
    ClientThrottledError
)

from data.models import InstagramPost, InstagramUser
from core.exceptions import InstagramAuthError

class UserService:
    def __init__(
        self,
        client,
        output_dir: str = "data/userMedia",
        min_delay: int = 3,
        max_delay: int = 10,
        max_retries: int = 3,
        retry_delay: int = 10
    ):
        self.client = client
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.processed_users: set[str] = set()

    def _get_random_delay(self) -> float:
        """Get a random delay between min_delay and max_delay seconds."""
        return random.uniform(self.min_delay, self.max_delay)

    def _parse_media(self, media) -> Dict[str, Any]:
        """Parse media data into a standardized dictionary."""
        # Extract user data
        user_data = {
            'username': getattr(media.user, 'username', ''),
            'full_name': getattr(media.user, 'full_name', ''),
            'user_id': str(getattr(media.user, 'pk', ''))
        }
        
        # Get media URL based on type
        media_urls = []
        if hasattr(media, 'resources') and media.resources:
            # Carousel - get all resources
            for resource in media.resources:
                if hasattr(resource, 'video_url') and resource.video_url:
                    media_urls.append(str(resource.video_url))
                elif hasattr(resource, 'thumbnail_url') and resource.thumbnail_url:
                    media_urls.append(str(resource.thumbnail_url))
        elif hasattr(media, 'video_url') and media.video_url:
            # Video
            media_urls.append(str(media.video_url))
        elif hasattr(media, 'thumbnail_url') and media.thumbnail_url:
            # Photo
            media_urls.append(str(media.thumbnail_url))
            
        # Determine media type
        media_type = "unknown"
        if hasattr(media, 'media_type'):
            if media.media_type == 1:
                media_type = "image"
            elif media.media_type == 2:
                media_type = "video"
            elif media.media_type == 8:
                media_type = "carousel"

        return {
            'post_id': str(media.pk),
            'code': getattr(media, 'code', ''),
            'user': user_data,
            'caption': getattr(media, 'caption_text', ''),
            'likes_count': getattr(media, 'like_count', 0),
            'media_type': media_type,
            'media_urls': media_urls,
            'taken_at': getattr(media, 'taken_at', datetime.now()).isoformat(),
            'timestamp': datetime.now().isoformat()
        }

    def _save_user_media(self, username: str, posts: List[Dict[str, Any]]) -> None:
        """Save user posts to JSON file."""
        if not posts:
            return
            
        # Create user directory
        user_dir = self.output_dir / username
        user_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = user_dir / f"posts_{timestamp}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(posts, f, indent=2, default=str)
        print(f"Saved {len(posts)} posts to {filename}")

    def _handle_rate_limit(self, retry_count: int) -> None:
        """Handle rate limiting with exponential backoff."""
        delay = self.retry_delay * (2 ** retry_count)  # Exponential backoff
        print(f"Rate limited. Waiting {delay} seconds before retry...")
        time.sleep(delay)

    def get_user_id_by_username(self, username: str) -> Optional[int]:
        """Get user ID from username."""
        try:
            user_info = self.client.user_info_by_username(username)
            return user_info.pk
        except Exception as e:
            print(f"Error getting user ID for {username}: {e}")
            return None

    def collect_user_media(self, username: str, amount: int = 50) -> List[Dict[str, Any]]:
        """
        Collect media posts from a specific user.
        Args:
            username: Instagram username
            amount: Maximum number of posts to collect (default: 50)
        Returns:
            List of collected media posts
        """
        retry_count = 0
        all_media = []
        
        try:
            # Convert username to user_id if needed
            user_id = self.get_user_id_by_username(username)
            if not user_id:
                print(f"Could not find user ID for {username}")
                return []
            
            print(f"Collecting up to {amount} posts from {username} (ID: {user_id})...")
            
            # Try different approaches to get user media
            try:
                # Try using user_medias first
                medias = self.client.user_medias(user_id, amount)
                print(f"Got {len(medias)} media items using user_medias")
            except Exception as e:
                print(f"Error with user_medias: {e}")
                try:
                    # Fall back to user_medias_gql (GraphQL API)
                    medias = self.client.user_medias_gql(user_id, amount)
                    print(f"Got {len(medias)} media items using user_medias_gql")
                except Exception as e2:
                    print(f"Error with user_medias_gql: {e2}")
                    try:
                        # Last resort: user_medias_v1 (Private API)
                        medias = self.client.user_medias_v1(user_id, amount)
                        print(f"Got {len(medias)} media items using user_medias_v1")
                    except Exception as e3:
                        print(f"All methods failed to get user media: {e3}")
                        return []
                
            # Process media items
            for media in medias:
                try:
                    post = self._parse_media(media)
                    all_media.append(post)
                    print(f"Processed post {post['post_id']}")
                except Exception as e:
                    print(f"Error processing media: {e}")
                    continue
                    
            # Save posts to file
            if all_media:
                self._save_user_media(username, all_media)
                
            return all_media
                
        except ClientThrottledError:
            retry_count += 1
            if retry_count > self.max_retries:
                print("Max retries reached. Stopping collection.")
                return all_media
            self._handle_rate_limit(retry_count)
            
        except LoginRequired:
            raise InstagramAuthError("Login required - session expired")
        
        except ClientConnectionError:
            print("Connection error.")
            return all_media
            
        except ClientError as e:
            print(f"Instagram client error: {str(e)}")
            return all_media
            
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return all_media

    def collect_multiple_users(self, usernames: List[str], posts_per_user: int = 20) -> None:
        """
        Collect media from multiple users with delays between requests.
        Args:
            usernames: List of Instagram usernames to collect from
            posts_per_user: Number of posts to collect per user (default: 20)
        """
        for username in usernames:
            if username in self.processed_users:
                print(f"Already processed {username}, skipping")
                continue
                
            print(f"\nCollecting media for {username}")
            self.collect_user_media(username, posts_per_user)
            self.processed_users.add(username)
            
            # Random delay before next user
            if username != usernames[-1]:
                delay = self._get_random_delay()
                print(f"Waiting {delay:.1f} seconds before next user...")
                time.sleep(delay) 