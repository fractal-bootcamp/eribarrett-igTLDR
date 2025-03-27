import json
import time
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from instagrapi.exceptions import (
    ClientError,
    LoginRequired,
    ClientConnectionError,
    ClientThrottledError
)

from core.exceptions import InstagramAuthError

class DirectFeedService:
    """
    Service to fetch feed posts directly using Instagram's private API endpoints
    instead of relying on instagrapi's high-level methods.
    """
    def __init__(
        self,
        client,
        output_dir: str = "data/direct_feed",
        min_delay: int = 3,
        max_delay: int = 10,
        max_retries: int = 3,
        retry_delay: int = 10,
        batch_size: int = 10,
        simulate_browsing: bool = False,
        max_posts_per_file: int = 500
    ):
        self.client = client
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.batch_size = batch_size
        self.simulate_browsing = simulate_browsing
        self.processed_posts: set[str] = set()
        self.max_posts_per_file = max_posts_per_file
        
        # Session info
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_file = None
        self.posts_in_current_file = 0
        
        # Get user info
        try:
            self.user_info = self.client.user_info(self.client.user_id)
            self.username = self.user_info.username
        except Exception as e:
            print(f"Error getting user info: {e}")
            self.username = "unknown_user"

    def _get_random_delay(self) -> float:
        """Get a random delay between min_delay and max_delay seconds."""
        return random.uniform(self.min_delay, self.max_delay)

    def _handle_rate_limit(self, retry_count: int) -> None:
        """Handle rate limiting with exponential backoff."""
        delay = self.retry_delay * (2 ** (retry_count - 1))
        print(f"Rate limited. Waiting {delay} seconds before retry {retry_count}/{self.max_retries}...")
        time.sleep(delay)

    def _save_posts(self, posts: List[Dict[str, Any]]) -> None:
        """
        Save posts to JSON file. Appends to same file during a session until max_posts_per_file is reached.
        """
        if not posts:
            print("No posts to save.")
            return
        
        # If we don't have a current file or we've reached the max posts per file, create a new one
        if self.current_file is None or self.posts_in_current_file >= self.max_posts_per_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Include username in the filename
            filename = self.output_dir / f"{self.username}_feed_posts_{self.session_id}_{timestamp}.json"
            
            # Initialize the file with metadata
            metadata = {
                "collector_info": {
                    "username": self.username,
                    "user_id": str(self.client.user_id),
                    "session_id": self.session_id,
                    "started_at": timestamp
                },
                "posts": []
            }
            
            # Create the directory if it doesn't exist
            filename.parent.mkdir(parents=True, exist_ok=True)
            
            # Write initial file with empty posts array
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, default=str)
            
            # Update current file info
            self.current_file = filename
            self.posts_in_current_file = 0
            
            print(f"\nCreated new feed file: {filename}")
        
        # Now load the current file, append the new posts, and save
        try:
            with open(self.current_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Append new posts
            data["posts"].extend(posts)
            data["last_updated"] = datetime.now().isoformat()
            data["total_posts"] = len(data["posts"])
            
            # Write back to file
            with open(self.current_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            
            # Update count
            self.posts_in_current_file = len(data["posts"])
            
            print(f"Saved {len(posts)} posts to {self.current_file} (Total: {self.posts_in_current_file})")
            
        except Exception as e:
            print(f"Error updating feed file: {e}")
            # Fallback to creating a new file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            fallback_file = self.output_dir / f"{self.username}_feed_posts_{self.session_id}_fallback_{timestamp}.json"
            
            metadata = {
                "collector_info": {
                    "username": self.username,
                    "user_id": str(self.client.user_id),
                    "session_id": self.session_id,
                    "started_at": timestamp,
                    "error": f"Fallback file created due to error: {str(e)}"
                },
                "posts": posts
            }
            
            with open(fallback_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, default=str)
            
            print(f"Created fallback file due to error: {fallback_file}")

    def _parse_post(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse raw post data from API response into a structured format.
        """
        try:
            # Extract user data
            user_data = post_data.get("user", {})
            user = {
                "user_id": str(user_data.get("pk")),
                "username": user_data.get("username", ""),
                "full_name": user_data.get("full_name", ""),
                "profile_pic_url": user_data.get("profile_pic_url", ""),
                "is_private": user_data.get("is_private", False),
                "is_verified": user_data.get("is_verified", False)
            }
            
            # Extract media data
            taken_at = post_data.get("taken_at", 0)
            post_id = str(post_data.get("pk", ""))
            media_type = post_data.get("media_type", 1)
            
            media_types = {1: "photo", 2: "video", 8: "album"}
            media_type_name = media_types.get(media_type, "unknown")
                
            # Caption
            caption_text = ""
            caption_data = post_data.get("caption")
            if caption_data:
                caption_text = caption_data.get("text", "")
            
            # Extract location if available
            location = None
            loc_data = post_data.get("location")
            if loc_data:
                location = {
                    "name": loc_data.get("name", ""),
                    "address": loc_data.get("address", ""),
                    "city": loc_data.get("city", ""),
                    "short_name": loc_data.get("short_name", ""),
                    "lng": loc_data.get("lng", 0),
                    "lat": loc_data.get("lat", 0),
                    "external_id": loc_data.get("external_id", ""),
                    "facebook_places_id": loc_data.get("facebook_places_id", "")
                }
            
            # Collect image URLs
            images = []
            if media_type == 1:  # Photo
                if "image_versions2" in post_data:
                    candidates = post_data.get("image_versions2", {}).get("candidates", [])
                    for img in candidates:
                        images.append({
                            "width": img.get("width"),
                            "height": img.get("height"),
                            "url": img.get("url")
                        })
            
            # Handle carousel/album media
            carousel_media = []
            if media_type == 8 and "carousel_media" in post_data:
                for item in post_data.get("carousel_media", []):
                    carousel_item = {
                        "id": str(item.get("pk", "")),
                        "media_type": item.get("media_type", 1)
                    }
                    
                    # Images for carousel item
                    if "image_versions2" in item:
                        carousel_item["images"] = []
                        candidates = item.get("image_versions2", {}).get("candidates", [])
                        for img in candidates:
                            carousel_item["images"].append({
                                "width": img.get("width"),
                                "height": img.get("height"),
                                "url": img.get("url")
                            })
                    
                    # Videos for carousel item
                    if item.get("media_type") == 2 and "video_versions" in item:
                        carousel_item["videos"] = []
                        for vid in item.get("video_versions", []):
                            carousel_item["videos"].append({
                                "width": vid.get("width"),
                                "height": vid.get("height"),
                                "url": vid.get("url"),
                                "type": vid.get("type", 0)
                            })
                    
                    carousel_media.append(carousel_item)
            
            # Handle videos
            videos = []
            if media_type == 2 and "video_versions" in post_data:
                for vid in post_data.get("video_versions", []):
                    videos.append({
                        "width": vid.get("width"),
                        "height": vid.get("height"),
                        "url": vid.get("url"),
                        "type": vid.get("type", 0)
                    })
            
            # Construct structured post object
            structured_post = {
                "post_id": post_id,
                "shortcode": post_data.get("code", ""),
                "taken_at": datetime.fromtimestamp(taken_at).isoformat(),
                "media_type": media_type_name,
                "like_count": post_data.get("like_count", 0),
                "comment_count": post_data.get("comment_count", 0),
                "caption": caption_text,
                "user": user,
                "location": location,
                "images": images,
                "videos": videos,
                "carousel_media": carousel_media,
                "is_paid_partnership": post_data.get("is_paid_partnership", False),
                "has_liked": post_data.get("has_liked", False)
            }
            
            return structured_post
        
        except Exception as e:
            print(f"Error parsing post data: {e}")
            # Return minimal data to avoid losing the post completely
            return {
                "post_id": str(post_data.get("pk", "")),
                "error": f"Failed to parse: {str(e)}",
                "raw_data": post_data  # Include raw data for debugging
            }

    def _simulate_human_browsing(self) -> None:
        """
        Simulate natural human browsing behavior with random long pauses.
        This mimics a real user who might stop to read content, get distracted,
        or engage with a post before continuing to scroll.
        """
        # 25% chance of a "reading post" pause (5-15 seconds)
        if random.random() < 0.25:
            reading_time = random.uniform(5, 15)
            print(f"Simulating reading a post ({reading_time:.1f}s)...")
            time.sleep(reading_time)
            
        # 15% chance of a "engagement" pause (typing comment, liking, etc.)
        if random.random() < 0.15:
            engagement_time = random.uniform(3, 8)
            print(f"Simulating post engagement ({engagement_time:.1f}s)...")
            time.sleep(engagement_time)
            
        # 10% chance of a "distraction" pause (30-120 seconds)
        # This simulates user getting a notification or briefly using another app
        if random.random() < 0.10:
            distraction_time = random.uniform(30, 120)
            print(f"Simulating user distraction/pause ({distraction_time:.1f}s)...")
            time.sleep(distraction_time)
            
        # 3% chance of a "long break" (2-10 minutes)
        # This simulates user putting phone down for a while then coming back
        if random.random() < 0.03:
            minutes = random.uniform(2, 10)
            break_time = minutes * 60
            print(f"Simulating a longer break ({minutes:.1f} minutes)...")
            # Break the long pause into smaller chunks to allow ctrl+c interruption
            chunk_size = 15
            for _ in range(int(break_time / chunk_size)):
                time.sleep(chunk_size)
            time.sleep(break_time % chunk_size)  # Remainder
            print("Resuming after break...")

    def get_feed(self, max_posts: int = 50) -> List[Dict[str, Any]]:
        """
        Get feed posts directly from Instagram's private API.
        
        Args:
            max_posts: Maximum number of posts to fetch (default: 50)
        
        Returns:
            List of parsed feed posts
        """
        all_posts = []
        next_max_id = None
        retry_count = 0
        
        print(f"Fetching up to {max_posts} feed posts with batch size of {self.batch_size}...")
        
        # Add initial delay to mimic app startup behavior
        initial_delay = random.uniform(3, 8) if self.simulate_browsing else random.uniform(1, 3)
        print(f"Preparing request (delay: {initial_delay:.1f}s)...")
        time.sleep(initial_delay)
        
        # Track time between sessions to prevent too many requests
        session_start = datetime.now()
        posts_collected_this_batch = 0
        
        while len(all_posts) < max_posts:
            try:
                # Check if we should take a longer break between batches
                if posts_collected_this_batch >= self.batch_size:
                    # Longer break between batches
                    if self.simulate_browsing:
                        # In ultra-safe mode, take much longer breaks between batches
                        batch_delay = random.uniform(self.max_delay * 2, self.max_delay * 4)
                    else:
                        batch_delay = random.uniform(self.max_delay * 1.5, self.max_delay * 2.5)
                        
                    print(f"\nCompleted a batch of {posts_collected_this_batch} posts.")
                    print(f"Taking a longer break between batches ({batch_delay:.1f}s)...")
                    time.sleep(batch_delay)
                    posts_collected_this_batch = 0
                
                print(f"Requesting feed posts{' with max_id: ' + next_max_id if next_max_id else ''}...")
                
                # Make the direct API request to the timeline feed endpoint
                feed_response = self.client.private_request(
                    "feed/timeline/", 
                    {
                        "is_pull_to_refresh": "0",
                        "max_id": next_max_id or "",
                        "feed_view_info": "",
                        "is_from_startup": "1" if not next_max_id else "0",
                        "seen_posts": "",
                        "phone_id": self.client.phone_id,
                        "device_id": self.client.uuid
                    }
                )
                
                # Extract feed items
                items = feed_response.get("feed_items", [])
                if not items:
                    print("No more feed items found.")
                    break
                
                # Save pagination token for next request
                next_max_id = feed_response.get("next_max_id")
                
                # Process feed items
                posts_in_batch = 0
                for item in items:
                    # Check if we have a media item
                    if "media_or_ad" not in item:
                        continue
                    
                    post_data = item["media_or_ad"]
                    post_id = str(post_data.get("pk", ""))
                    
                    # Skip already processed posts
                    if post_id in self.processed_posts:
                        continue
                    
                    # Parse the post data
                    parsed_post = self._parse_post(post_data)
                    all_posts.append(parsed_post)
                    self.processed_posts.add(post_id)
                    posts_in_batch += 1
                    posts_collected_this_batch += 1
                    
                    # Simulate human browsing behavior after processing each post
                    if self.simulate_browsing:
                        self._simulate_human_browsing()
                    
                    # Save incrementally every batch_size posts to avoid data loss on interruption
                    if len(all_posts) % self.batch_size == 0:
                        self._save_posts(all_posts)
                        print(f"Saved progress ({len(all_posts)} posts so far)")
                    
                    # Check if we've reached the per-batch limit
                    if posts_in_batch >= self.batch_size:
                        print(f"Reached batch limit of {self.batch_size} posts")
                        break
                        
                    # Check if we've reached the total limit
                    if len(all_posts) >= max_posts:
                        break
                
                print(f"Processed {posts_in_batch} new posts in this batch.")
                
                # Check session duration - if over 10 minutes, warn user about potential risks
                session_duration = (datetime.now() - session_start).total_seconds() / 60
                if session_duration > 10 and len(all_posts) > 20 and not self.simulate_browsing:
                    print("\n⚠️ Warning: This session has been running for {:.1f} minutes.".format(session_duration))
                    print("   Long sessions may increase the risk of detection.")
                    print("   Consider stopping (Ctrl+C) and resuming later.\n")
                
                # Break if we don't have a next page or processed all posts
                if not next_max_id or len(all_posts) >= max_posts:
                    break
                
                # Add delay between requests to avoid rate limiting
                delay = self._get_random_delay()
                print(f"Waiting {delay:.1f} seconds before next request...")
                time.sleep(delay)
                
                # Reset retry counter on successful request
                retry_count = 0
                
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
        
        print(f"Finished collecting {len(all_posts)} feed posts.")
        
        # Save posts to file
        if all_posts:
            self._save_posts(all_posts)
        
        return all_posts 