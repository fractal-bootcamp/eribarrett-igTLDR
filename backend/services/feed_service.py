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

class FeedService:
    def __init__(
        self,
        client,
        output_dir: str = "data/feed",
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
        self.processed_posts: set[str] = set()

    def _get_random_delay(self) -> float:
        """Get a random delay between min_delay and max_delay seconds."""
        return random.uniform(self.min_delay, self.max_delay)

    def _parse_post(self, media) -> Dict[str, Any]:
        """Parse post data to get only the required fields."""
        # Get tagged users
        tagged_users = []
        if hasattr(media, 'usertags') and media.usertags:
            for tag in media.usertags:
                if hasattr(tag, 'user'):
                    tagged_users.append({
                        'username': tag.user.username,
                        'full_name': tag.user.full_name
                    })

        # Get media URL based on type
        media_url = None
        if media.media_type == 1:  # Photo
            if hasattr(media, 'thumbnail_url'):
                media_url = str(media.thumbnail_url)
        elif media.media_type == 2:  # Video
            if hasattr(media, 'video_url'):
                media_url = str(media.video_url)
        elif media.media_type == 8:  # Album/Carousel
            if hasattr(media, 'resources') and media.resources:
                # Get the first resource's URL
                if hasattr(media.resources[0], 'video_url') and media.resources[0].video_url:
                    media_url = str(media.resources[0].video_url)
                elif hasattr(media.resources[0], 'thumbnail_url') and media.resources[0].thumbnail_url:
                    media_url = str(media.resources[0].thumbnail_url)

        return {
            'post_id': str(media.pk),
            'code': media.code,
            'username': media.user.username,
            'full_name': media.user.full_name,
            'caption': media.caption_text if hasattr(media, 'caption_text') else '',
            'likes_count': media.like_count if hasattr(media, 'like_count') else 0,
            'tagged_users': tagged_users,
            'media_url': media_url,
            'taken_at': media.taken_at.isoformat() if hasattr(media, 'taken_at') else None
        }

    def _save_posts(self, posts: List[Dict[str, Any]]) -> None:
        """Save posts to JSON file."""
        if not posts:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"feed_{timestamp}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(posts, f, indent=2)
        print(f"Saved {len(posts)} posts to {filename}")

    def _handle_rate_limit(self, retry_count: int) -> None:
        """Handle rate limiting with exponential backoff."""
        delay = self.retry_delay * (2 ** retry_count)  # Exponential backoff
        print(f"Rate limited. Waiting {delay} seconds before retry...")
        time.sleep(delay)

    def collect_feed(self, max_posts: Optional[int] = None) -> None:
        """
        Collect feed data continuously until stopped or max_posts reached.
        Implements proper rate limiting and error handling.
        """
        posts_collected = 0
        retry_count = 0

        while True:
            try:
                # Try to get timeline using available method
                try:
                    print("Fetching timeline feed...")
                    # Try with get_timeline_feed
                    feed_response = self.client.get_timeline_feed()
                    
                    # Get media items from the response
                    if isinstance(feed_response, dict):
                        medias = []
                        # Raw API response
                        if "items" in feed_response:
                            items = feed_response.get("items", [])
                            print(f"Found {len(items)} raw items in feed")
                            
                            for item in items:
                                try:
                                    # Minimal media object creation
                                    # You can adjust the fields as needed
                                    from instagrapi.types import Media, UserShort
                                    user_data = item.get("user", {})
                                    user = UserShort(
                                        pk=user_data.get("pk"),
                                        username=user_data.get("username", ""),
                                        full_name=user_data.get("full_name", "")
                                    )
                                    
                                    media = Media(
                                        pk=item.get("pk"),
                                        id=item.get("id", ""),
                                        code=item.get("code", ""),
                                        user=user,
                                        media_type=item.get("media_type", 1),
                                        caption_text=item.get("caption", {}).get("text", "") if item.get("caption") else "",
                                        like_count=item.get("like_count", 0),
                                        taken_at=datetime.fromtimestamp(item.get("taken_at", 0))
                                    )
                                    medias.append(media)
                                except Exception as e:
                                    print(f"Error creating media object: {e}")
                                    continue
                    else:
                        # Already processed response
                        medias = feed_response
                        
                except Exception as e:
                    print(f"Error fetching timeline feed: {e}")
                    print("Trying alternative approach...")
                    
                    # Try with private_request (without method parameter)
                    try:
                        results = self.client.private_request("feed/timeline/")
                        
                        if not isinstance(results, dict):
                            print("Invalid feed response format")
                            time.sleep(self._get_random_delay())
                            continue
                            
                        # Process feed items
                        feed_items = results.get("feed_items", [])
                        if not feed_items:
                            items = results.get("items", [])
                            if items:
                                feed_items = [{"media_or_ad": item} for item in items]
                            
                        if not feed_items:
                            print("No feed items found")
                            time.sleep(self._get_random_delay())
                            continue
                            
                        print(f"Found {len(feed_items)} feed items")
                        
                        # Process media items
                        medias = []
                        for feed_item in feed_items:
                            # Skip non-media items
                            if "media_or_ad" not in feed_item:
                                continue
                            
                            item = feed_item["media_or_ad"]
                            try:
                                # Create a basic Media object manually
                                from instagrapi.types import Media, UserShort
                                user_data = item.get("user", {})
                                user = UserShort(
                                    pk=user_data.get("pk"),
                                    username=user_data.get("username", ""),
                                    full_name=user_data.get("full_name", "")
                                )
                                
                                media = Media(
                                    pk=item.get("pk"),
                                    id=item.get("id", ""),
                                    code=item.get("code", ""),
                                    user=user,
                                    media_type=item.get("media_type", 1),
                                    caption_text=item.get("caption", {}).get("text", "") if item.get("caption") else "",
                                    like_count=item.get("like_count", 0),
                                    taken_at=datetime.fromtimestamp(item.get("taken_at", 0))
                                )
                                medias.append(media)
                            except Exception as e:
                                print(f"Error processing item: {e}")
                                continue
                    except Exception as e:
                        print(f"Error with private request: {e}")
                        medias = []
                
                if not medias:
                    print("No posts found in feed. Waiting before next check...")
                    time.sleep(self._get_random_delay())
                    continue

                print(f"Found {len(medias)} posts to process")

                posts = []
                for media in medias:
                    try:
                        # Check if we've already processed this post
                        media_id = str(getattr(media, 'pk', ''))
                        if not media_id:
                            continue
                            
                        if media_id in self.processed_posts:
                            continue

                        post = self._parse_post(media)
                        posts.append(post)
                        self.processed_posts.add(post['post_id'])
                        posts_collected += 1
                        print(f"Processed post {post['post_id']} from {post['username']}")
                    except Exception as e:
                        print(f"Error parsing post: {str(e)}")
                        continue

                if posts:
                    self._save_posts(posts)
                    print(f"Saved {len(posts)} new posts")

                # Check if we've reached max_posts
                if max_posts and posts_collected >= max_posts:
                    print(f"Reached maximum posts limit ({max_posts})")
                    break

                # Reset retry count on successful request
                retry_count = 0
                delay = self._get_random_delay()
                print(f"Waiting {delay:.1f} seconds before next request...")
                time.sleep(delay)

            except ClientThrottledError:
                retry_count += 1
                if retry_count > self.max_retries:
                    print("Max retries reached. Stopping collection.")
                    break
                self._handle_rate_limit(retry_count)

            except LoginRequired:
                raise InstagramAuthError("Login required - session expired")
            
            except ClientConnectionError:
                print("Connection error. Retrying...")
                time.sleep(self.retry_delay)
                continue

            except ClientError as e:
                print(f"Instagram client error: {str(e)}")
                time.sleep(self.retry_delay)
                continue

            except Exception as e:
                print(f"Unexpected error: {str(e)}")
                time.sleep(self.retry_delay)
                continue
