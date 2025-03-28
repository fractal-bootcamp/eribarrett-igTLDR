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
            
            # Collect image URLs and accessibility captions
            images = []
            accessibility_captions = []
            
            if media_type == 1:  # Photo
                if "image_versions2" in post_data:
                    candidates = post_data.get("image_versions2", {}).get("candidates", [])
                    for img in candidates:
                        images.append({
                            "width": img.get("width"),
                            "height": img.get("height"),
                            "url": img.get("url")
                        })
                    
                    # Check for accessibility caption in image_versions2
                    accessibility_caption = post_data.get("image_versions2", {}).get("accessibility_caption", "")
                    if accessibility_caption:
                        accessibility_captions.append(accessibility_caption)
                
                # Also check for top-level accessibility_caption
                if "accessibility_caption" in post_data and post_data["accessibility_caption"]:
                    accessibility_captions.append(post_data["accessibility_caption"])
                
                # Check for caption_with_translation_aid
                if "caption_with_translation_aid" in post_data and post_data["caption_with_translation_aid"]:
                    accessibility_captions.append(post_data["caption_with_translation_aid"])
            
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
                    
                    # Check for accessibility caption in carousel item
                    if "accessibility_caption" in item and item["accessibility_caption"]:
                        carousel_item["accessibility_caption"] = item["accessibility_caption"]
                        accessibility_captions.append(item["accessibility_caption"])
                    
                    # Check for accessibility caption in image_versions2 of carousel item
                    carousel_accessibility = item.get("image_versions2", {}).get("accessibility_caption", "")
                    if carousel_accessibility:
                        carousel_item["accessibility_caption"] = carousel_accessibility
                        accessibility_captions.append(carousel_accessibility)
                    
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
                
                # Check for video accessibility captions
                if "accessibility_caption" in post_data and post_data["accessibility_caption"]:
                    accessibility_captions.append(post_data["accessibility_caption"])
            
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
                "accessibility_captions": accessibility_captions,
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
        Uses an ultra-stealthy approach to minimize detection risk.
        
        Args:
            max_posts: Maximum number of posts to fetch (default: 50)
        
        Returns:
            List of parsed feed posts
        """
        all_posts = []
        next_max_id = None
        retry_count = 0
        
        print(f"Fetching up to {max_posts} feed posts in ultra-stealthy mode...")
        
        # Add initial delay with variability to mimic app startup
        initial_delay = random.uniform(5, 15)  # Longer initial delay
        print(f"Starting session (initial delay: {initial_delay:.1f}s)...")
        time.sleep(initial_delay)
        
        # Track time between sessions to prevent too many requests
        session_start = datetime.now()
        posts_processed_count = 0
        
        # Create file before starting to append incrementally
        self._initialize_feed_file()
        
        # Track post IDs to collect
        post_ids_to_process = []
        
        while posts_processed_count < max_posts:
            try:
                # First, we'll just get the minimal feed data with post IDs
                if not post_ids_to_process:
                    print(f"Browsing feed to find posts{' with max_id: ' + next_max_id if next_max_id else ''}...")
                    
                    # Simulate app interaction
                    if random.random() < 0.3:  # 30% chance
                        pre_request_pause = random.uniform(2, 7)
                        print(f"Opening feed ({pre_request_pause:.1f}s)...")
                        time.sleep(pre_request_pause)
                    
                    # Request just 1-2 posts to find IDs
                    request_count = random.randint(1, 2)
                    
                    # Generate request parameters with slight randomness
                    request_params = {
                        "is_pull_to_refresh": "1" if random.random() < 0.3 else "0",
                        "max_id": next_max_id or "",
                        "feed_view_info": "",
                        "is_from_startup": "1" if not next_max_id else "0",
                        "seen_posts": "",
                        "phone_id": self.client.phone_id,
                        "device_id": self.client.uuid,
                        "_uuid": self.client.uuid,
                        "_csrftoken": self.client.token,
                        "count": str(request_count)
                    }
                    
                    # Make the direct API request to the timeline feed endpoint
                    feed_response = self.client.private_request("feed/timeline/", request_params)
                    
                    # Extract feed items
                    items = feed_response.get("feed_items", [])
                    if not items:
                        print("No more feed items found.")
                        break
                    
                    # Save pagination token for next request
                    next_max_id = feed_response.get("next_max_id")
                    
                    # Extract post IDs to process individually
                    for item in items:
                        if "media_or_ad" in item:
                            post_data = item["media_or_ad"]
                            post_id = str(post_data.get("pk", ""))
                            
                            # Skip already processed posts
                            if post_id in self.processed_posts:
                                continue
                                
                            post_ids_to_process.append({
                                "id": post_id,
                                "code": post_data.get("code", ""),
                                "media_type": post_data.get("media_type", 1)
                            })
                    
                    # Simulate browsing behavior
                    self._ultra_realistic_browsing()
                
                # Process one post ID at a time with natural delays between each step
                if post_ids_to_process:
                    post_info = post_ids_to_process.pop(0)
                    post_id = post_info["id"]
                    post_code = post_info["code"]
                    media_type = post_info["media_type"]
                    
                    print(f"Looking at post: {post_code}")
                    
                    # Get basic post info first - simulates opening a post
                    post_data = self._fetch_single_post_info(post_id, post_code)
                    
                    if post_data:
                        # Now fetch additional details for this post using separate requests
                        post_data = self._enrich_post_data(post_data, post_id, post_code, media_type)
                        
                        # Parse the post data
                        parsed_post = self._parse_post(post_data)
                        all_posts.append(parsed_post)
                        self.processed_posts.add(post_id)
                        posts_processed_count += 1
                        
                        # Save each post immediately
                        self._append_post_to_file(parsed_post)
                        print(f"Processed post {posts_processed_count}/{max_posts} (ID: {post_id})")
                        
                        # Check if we've reached the total limit
                        if posts_processed_count >= max_posts:
                            break
                    
                    # Simulate realistic browsing behavior after each post
                    self._ultra_realistic_browsing()
                    
                # If we've processed all post IDs and there's no next page, we're done
                if not post_ids_to_process and not next_max_id:
                    break
                
                # If we've exhausted current batch of post IDs but there are more pages
                if not post_ids_to_process and next_max_id:
                    # Natural delay before getting more post IDs
                    delay = random.uniform(10, 25)
                    print(f"Scrolling for more posts ({delay:.1f}s)...")
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
                print("Connection error. Taking a break before retry...")
                time.sleep(random.uniform(30, 60))
                continue
                
            except ClientError as e:
                print(f"Instagram client error: {str(e)}")
                time.sleep(random.uniform(60, 120))
                continue
                
            except Exception as e:
                print(f"Unexpected error: {str(e)}")
                time.sleep(random.uniform(45, 90))
                continue
        
        print(f"Finished collecting {len(all_posts)} feed posts.")
        print(f"Data saved to {self.current_file}")
        
        return all_posts
    
    def _initialize_client_settings(self):
        """
        Update client settings to improve compatibility with Instagram API changes.
        """
        try:
            # Try to update the client user agent to a newer version
            # Instagram frequently updates API endpoints between versions
            self.client.user_agent = "Instagram 248.0.0.17.109 Android (30/11; 480dpi; 1080x2158; OnePlus; GM1917; OnePlus7Pro; qcom; en_US; 385018104)"
            
            # Enable automatic retries for API calls
            if hasattr(self.client, 'set_retry_delay'):
                self.client.set_retry_delay(True)
            
            print("Client settings initialized with updated user agent")
        except Exception as e:
            print(f"Warning: Could not update client settings: {e}")

    def _fetch_single_post_info(self, post_id: str, post_code: str) -> Optional[Dict[str, Any]]:
        """
        Fetch basic information for a single post using multiple different methods and APIs.
        Includes fallbacks for handling 404 errors with certain endpoints.
        """
        # Initialize client settings if not already done
        if not hasattr(self, '_client_settings_initialized'):
            self._initialize_client_settings()
            self._client_settings_initialized = True
        
        try:
            # Simulate the time it takes to click and load a post
            click_delay = random.uniform(1, 3)
            time.sleep(click_delay)
            
            print(f"Viewing post content...")
            
            # Method 1: Try Instagram mobile API with post ID
            try:
                post_data = self.client.private_request(
                    f"media/{post_id}/info/", {}
                )
                
                # Check response validity
                if post_data and "items" in post_data and post_data["items"]:
                    post_item = post_data.get("items", [{}])[0]
                    if self._is_sponsored_post(post_item):
                        print("Skipping sponsored content...")
                        return None
                    
                    self._check_accessibility_captions(post_item)
                    return post_item
            except Exception as e:
                print(f"Standard API failed: {e}")
            
            # Method 2: Try with a newer graph API endpoint
            try:
                print("Trying newer Graph API endpoint...")
                # This endpoint format is more resilient to API changes
                post_data = self.client.private_request(
                    f"api/v1/media/{post_code}/info/", {}
                )
                
                if post_data and "items" in post_data and post_data["items"]:
                    post_item = post_data.get("items", [{}])[0]
                    if self._is_sponsored_post(post_item):
                        print("Skipping sponsored content...")
                        return None
                    
                    self._check_accessibility_captions(post_item)
                    return post_item
            except Exception as e:
                print(f"Graph API failed: {e}")
            
            # Method 3: Try using web API which might be more stable
            try:
                print("Trying Web API...")
                user_info = self.client.public_request(
                    f"p/{post_code}/",
                    params={"__a": "1", "__d": "dis"}
                )
                
                # Web API returns different structure
                if user_info and "graphql" in user_info:
                    media_info = user_info["graphql"]["shortcode_media"]
                    return self._convert_web_to_api_format(media_info, post_code)
            except Exception as e:
                print(f"Web API failed: {e}")
            
            # Method 4: Try using instagrapi's built-in methods if available
            try:
                print("Trying instagrapi's built-in methods...")
                if hasattr(self.client, 'media_info_by_code'):
                    media_info = self.client.media_info_by_code(post_code)
                    return media_info.dict()
            except Exception as e:
                print(f"Built-in method failed: {e}")
            
            # All methods failed
            print(f"All methods failed to retrieve post. Media ID format may have changed.")
            return None
            
        except Exception as e:
            print(f"Error fetching post info: {e}")
            # Random delay after error to prevent rate limiting
            time.sleep(random.uniform(5, 15))
            return None
    
    def _convert_web_to_api_format(self, web_media: Dict[str, Any], shortcode: str) -> Dict[str, Any]:
        """
        Convert web API format to match mobile API format for consistent processing.
        """
        try:
            # Create a basic object structure that matches the API response
            api_format = {
                "id": web_media.get("id", ""),
                "code": shortcode,
                "taken_at": web_media.get("taken_at_timestamp", int(time.time())),
                "media_type": 1,  # Default to photo
                "user": {
                    "pk": web_media.get("owner", {}).get("id", ""),
                    "username": web_media.get("owner", {}).get("username", ""),
                    "full_name": web_media.get("owner", {}).get("full_name", ""),
                    "is_private": web_media.get("owner", {}).get("is_private", False),
                    "is_verified": web_media.get("owner", {}).get("is_verified", False),
                    "profile_pic_url": web_media.get("owner", {}).get("profile_pic_url", ""),
                },
                "caption": {
                    "text": web_media.get("edge_media_to_caption", {}).get("edges", [{}])[0].get("node", {}).get("text", "") if web_media.get("edge_media_to_caption", {}).get("edges") else ""
                },
                "image_versions2": {
                    "candidates": [
                        {
                            "width": web_media.get("dimensions", {}).get("width", 1080),
                            "height": web_media.get("dimensions", {}).get("height", 1080),
                            "url": web_media.get("display_url", "")
                        }
                    ],
                    "accessibility_caption": web_media.get("accessibility_caption", "")
                },
                "like_count": web_media.get("edge_media_preview_like", {}).get("count", 0),
                "comment_count": web_media.get("edge_media_to_comment", {}).get("count", 0),
                "accessibility_caption": web_media.get("accessibility_caption", "")
            }
            
            # Set media_type based on __typename
            if web_media.get("__typename") == "GraphVideo":
                api_format["media_type"] = 2
                api_format["video_url"] = web_media.get("video_url", "")
            elif web_media.get("__typename") == "GraphSidecar":
                api_format["media_type"] = 8
                
                # Convert carousel items
                if "edge_sidecar_to_children" in web_media:
                    api_format["carousel_media"] = []
                    for edge in web_media["edge_sidecar_to_children"]["edges"]:
                        node = edge["node"]
                        carousel_item = {
                            "id": node.get("id", ""),
                            "media_type": 2 if node.get("__typename") == "GraphVideo" else 1,
                            "image_versions2": {
                                "candidates": [
                                    {
                                        "width": node.get("dimensions", {}).get("width", 1080),
                                        "height": node.get("dimensions", {}).get("height", 1080),
                                        "url": node.get("display_url", "")
                                    }
                                ],
                                "accessibility_caption": node.get("accessibility_caption", "")
                            },
                            "accessibility_caption": node.get("accessibility_caption", "")
                        }
                        
                        # Add video URL if it's a video
                        if node.get("__typename") == "GraphVideo":
                            carousel_item["video_url"] = node.get("video_url", "")
                            
                        api_format["carousel_media"].append(carousel_item)
            
            return api_format
            
        except Exception as e:
            print(f"Error converting web format to API format: {e}")
            # Return the original data as a fallback
            return web_media

    def _check_accessibility_captions(self, post_data: Dict[str, Any]) -> None:
        """
        Check for accessibility captions in a post and log their presence.
        This helps verify we're capturing AI-generated descriptions.
        """
        has_accessibility = False
        
        # Check top-level accessibility caption
        if "accessibility_caption" in post_data:
            print("Found top-level accessibility caption")
            has_accessibility = True
            
        # Check image_versions2 for accessibility caption
        if "image_versions2" in post_data and "accessibility_caption" in post_data.get("image_versions2", {}):
            print("Found image_versions2 accessibility caption")
            has_accessibility = True
            
        # Check caption_with_translation_aid
        if "caption_with_translation_aid" in post_data:
            print("Found caption_with_translation_aid")
            has_accessibility = True
            
        # Check for carousel media accessibility captions
        if "carousel_media" in post_data:
            for idx, item in enumerate(post_data.get("carousel_media", [])):
                if "accessibility_caption" in item:
                    print(f"Found accessibility caption in carousel item {idx+1}")
                    has_accessibility = True
                    
                if "image_versions2" in item and "accessibility_caption" in item.get("image_versions2", {}):
                    print(f"Found image_versions2 accessibility caption in carousel item {idx+1}")
                    has_accessibility = True
        
        # Log summary
        if has_accessibility:
            print("✓ Post contains AI-generated descriptions")
        else:
            print("× No AI-generated descriptions found in this post")

    def _is_sponsored_post(self, post_data: Dict[str, Any]) -> bool:
        """
        Check if a post is sponsored content/advertisement.
        Instagram uses several indicators for sponsored content.
        """
        # Check for direct sponsor indicators
        if post_data.get("is_ad", False):
            return True
            
        if post_data.get("is_paid_partnership", False):
            return True
            
        # Check for injected ad markers
        if post_data.get("injected", {}).get("ad_id"):
            return True
            
        if post_data.get("ad_action", "") != "":
            return True
            
        if post_data.get("ad_id"):
            return True
            
        if post_data.get("ad_link_type"):
            return True
            
        # Check for branded content
        if post_data.get("branded_content_tag_info"):
            return True
            
        # Check for sponsor tags
        if post_data.get("sponsor_tags") and len(post_data.get("sponsor_tags", [])) > 0:
            return True
            
        # Check for specific ad display context
        if "ad_display_context" in post_data:
            return True
            
        # Check for commerce promotion
        if post_data.get("commerce_promotion"):
            return True
        
        # Check for "paid partnership" label
        if post_data.get("label_type") == "PAID_PARTNERSHIP":
            return True
            
        # Check for shopping info (sometimes indicates promotions)
        if post_data.get("product_tags") and post_data.get("shopping_product_tags"):
            # Only consider shopping tags as ads if they're extensive
            if len(post_data.get("product_tags", {}).get("in", [])) > 3:
                return True
        
        # Not identified as sponsored content
        return False

    def _enrich_post_data(self, post_data: Dict[str, Any], post_id: str, post_code: str, media_type: int) -> Dict[str, Any]:
        """
        Fetch additional details for a post using separate requests.
        Adapts to API changes with multiple fallback methods.
        """
        # Random delay to simulate reading the post
        view_delay = random.uniform(3, 12)
        time.sleep(view_delay)
        
        try:
            # Try to get a valid numeric ID for API calls if not already available
            numeric_id = post_id
            if not post_id.isdigit():
                numeric_id_from_shortcode = self._shortcode_to_media_id(post_code)
                if numeric_id_from_shortcode:
                    numeric_id = numeric_id_from_shortcode
            
            # 40% chance to check comments (if applicable)
            if random.random() < 0.4:
                # Fetch a small number of comments
                print("Reading comments...")
                comment_delay = random.uniform(2, 5)
                time.sleep(comment_delay)
                
                try:
                    # Try multiple comment-fetching endpoints for resilience
                    comments_data = None
                    comment_count = 0
                    
                    # Method 1: Standard API
                    try:
                        comments_data = self.client.private_request(
                            f"media/{numeric_id}/comments/", 
                            {"max_id": "", "count": str(random.randint(1, 3))}
                        )
                        if comments_data and "comments" in comments_data:
                            comment_count = len(comments_data.get("comments", []))
                    except Exception as e:
                        print(f"Standard comment API failed: {e}")
                    
                    # Method 2: Web API
                    if not comments_data or "comments" not in comments_data:
                        try:
                            comments_data = self.client.public_request(
                                f"graphql/query/", 
                                params={
                                    "query_hash": "bc3296d1ce80a24b1b6e40b1e72903f5",
                                    "variables": json.dumps({"shortcode": post_code, "first": 3})
                                }
                            )
                            if comments_data and "data" in comments_data:
                                edge_comments = comments_data.get("data", {}).get("shortcode_media", {}).get("edge_media_to_comment", {})
                                if "edges" in edge_comments:
                                    comment_count = len(edge_comments.get("edges", []))
                        except Exception as e:
                            print(f"Web comment API failed: {e}")
                    
                    # Method 3: API v1
                    if not comment_count:
                        try:
                            comments_data = self.client.private_request(
                                f"api/v1/media/{post_code}/comments/", 
                                {"max_id": "", "count": str(random.randint(1, 3))}
                            )
                            if comments_data and "comments" in comments_data:
                                comment_count = len(comments_data.get("comments", []))
                        except Exception as e:
                            print(f"V1 comment API failed: {e}")
                    
                    # Save the comment count to the post data
                    if comment_count:
                        post_data["comment_count"] = comment_count
                    
                except Exception as e:
                    print(f"Could not fetch comments: {e}")
                    # Non-critical failure, continue
                    pass
            
            # 30% chance to check likes
            if random.random() < 0.3:
                print("Viewing likes...")
                like_delay = random.uniform(1, 4)
                time.sleep(like_delay)
                
                like_count = 0
                try:
                    # Try multiple like-fetching methods
                    
                    # Method 1: Direct like count
                    try:
                        like_data = self.client.private_request(
                            f"media/{numeric_id}/like_count/", {}
                        )
                        if like_data and "like_count" in like_data:
                            like_count = like_data.get("like_count", 0)
                            post_data["like_count"] = like_count
                            post_data["has_liked"] = like_data.get("user_likes", False)
                    except Exception as e:
                        print(f"Like count API failed: {e}")
                    
                    # Method 2: Web API
                    if not like_count:
                        try:
                            like_data = self.client.public_request(
                                f"p/{post_code}/",
                                params={"__a": "1", "__d": "dis"}
                            )
                            if like_data and "graphql" in like_data:
                                edge_likes = like_data.get("graphql", {}).get("shortcode_media", {}).get("edge_media_preview_like", {})
                                if "count" in edge_likes:
                                    like_count = edge_likes.get("count", 0)
                                    post_data["like_count"] = like_count
                        except Exception as e:
                            print(f"Web like API failed: {e}")
                    
                except Exception as e:
                    print(f"Could not check like status: {e}")
                    # Non-critical failure, continue
                    pass
            
            # 20% chance to check user info
            if random.random() < 0.2 and "user" in post_data and "pk" in post_data.get("user", {}):
                user_id = post_data.get("user", {}).get("pk")
                if user_id:
                    print("Checking user profile...")
                    profile_delay = random.uniform(2, 6)
                    time.sleep(profile_delay)
                    
                    try:
                        # Try different user info APIs
                        user_info = None
                        
                        # Method 1: Standard API
                        try:
                            user_info = self.client.private_request(
                                f"users/{user_id}/info/", {}
                            )
                        except Exception as e:
                            print(f"User info API failed: {e}")
                        
                        # Method 2: Web API by username
                        if not user_info and "username" in post_data.get("user", {}):
                            username = post_data.get("user", {}).get("username")
                            try:
                                user_info = self.client.public_request(
                                    f"{username}/",
                                    params={"__a": "1", "__d": "dis"}
                                )
                            except Exception as e:
                                print(f"Web user API failed: {e}")
                        
                        # Update user data if we got info
                        if user_info:
                            if "user" in user_info:
                                # Standard API response
                                user_data = user_info.get("user", {})
                                post_data["user"].update({
                                    "follower_count": user_data.get("follower_count", 0),
                                    "following_count": user_data.get("following_count", 0),
                                    "is_business": user_data.get("is_business", False),
                                    "category": user_data.get("category", "")
                                })
                            elif "graphql" in user_info:
                                # Web API response
                                user_data = user_info.get("graphql", {}).get("user", {})
                                post_data["user"].update({
                                    "follower_count": user_data.get("edge_followed_by", {}).get("count", 0),
                                    "following_count": user_data.get("edge_follow", {}).get("count", 0),
                                    "is_business": user_data.get("is_business_account", False),
                                    "category": user_data.get("category_name", "")
                                })
                        
                    except Exception:
                        # Non-critical failure, continue
                        pass
            
            return post_data
            
        except Exception as e:
            print(f"Error enriching post data: {e}")
            # Return the original data if enrichment fails
            return post_data

    def _ultra_realistic_browsing(self) -> None:
        """
        Simulate ultra-realistic human browsing behavior with variable patterns.
        This mimics a real user's session with natural pauses, interactions, and distractions.
        """
        # Simulate normal viewing (100% chance, variable duration)
        view_time = random.uniform(3, 15)  # Normal post viewing time 3-15 seconds
        time.sleep(view_time)
        
        # Simulate actions with natural probabilities
        
        # 35% chance of lingering to read content (higher for text-heavy content)
        if random.random() < 0.35:
            reading_time = random.uniform(5, 25)
            time.sleep(reading_time)
            
        # 25% chance of liking behavior (lingering on like button)
        if random.random() < 0.25:
            time.sleep(random.uniform(1, 3))
            
        # 15% chance of viewing comments
        if random.random() < 0.15:
            comment_view_time = random.uniform(3, 12) 
            time.sleep(comment_view_time)
            
        # 8% chance of profile view diversion
        if random.random() < 0.08:
            profile_view_time = random.uniform(8, 25)
            time.sleep(profile_view_time)
            
        # 5% chance of longer engagement
        if random.random() < 0.05:
            engagement_time = random.uniform(20, 60)
            time.sleep(engagement_time)
            
        # 3% chance of significant distraction (checking other app, notifications, etc)
        if random.random() < 0.03:
            distraction_time = random.uniform(45, 120)  # 45s to 2min
            
            # Break down long waits for better Ctrl+C handling
            chunk_size = 10
            for _ in range(int(distraction_time / chunk_size)):
                time.sleep(chunk_size)
            time.sleep(distraction_time % chunk_size)  # Remainder
    
    def _initialize_feed_file(self) -> None:
        """
        Initialize a new feed file with metadata before starting collection.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
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
        
        # Ensure directory exists
        filename.parent.mkdir(parents=True, exist_ok=True)
        
        # Write initial file with empty posts array
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, default=str)
        
        # Set as current file
        self.current_file = filename
        self.posts_in_current_file = 0
        
        print(f"\nCreated new feed file: {filename}")
    
    def _append_post_to_file(self, post: Dict[str, Any]) -> None:
        """
        Append a single post to the feed file incrementally.
        This allows saving data progressively rather than in batches.
        """
        if not self.current_file:
            self._initialize_feed_file()
            
        try:
            # Load current file
            with open(self.current_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Append single post
            data["posts"].append(post)
            data["last_updated"] = datetime.now().isoformat()
            data["total_posts"] = len(data["posts"])
            
            # Write back to file
            with open(self.current_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            
            # Update count
            self.posts_in_current_file = len(data["posts"])
            
        except Exception as e:
            print(f"Error updating feed file: {e}")
            # Create a recovery file
            self._create_recovery_file([post])

    def _shortcode_to_media_id(self, shortcode: str) -> Optional[str]:
        """
        Convert an Instagram shortcode to a media ID.
        Instagram uses shortcodes in URLs, but some API endpoints need the numeric media ID.
        """
        try:
            # First try using instagrapi's built-in method if available
            if hasattr(self.client, 'media_pk_from_code'):
                try:
                    media_id = self.client.media_pk_from_code(shortcode)
                    return str(media_id)
                except Exception as e:
                    print(f"media_pk_from_code failed: {e}")
                    
            # Try to use Instagram web search API
            try:
                # Use the oembed endpoint to get media info by shortcode
                media_info = self.client.private_request(
                    "oembed/",
                    params={"url": f"https://www.instagram.com/p/{shortcode}/"}
                )
                
                if media_info and "media_id" in media_info:
                    return str(media_info["media_id"])
            except Exception as e:
                print(f"oembed method failed: {e}")
            
            # If nothing else works, try a direct request to get post info
            try:
                # Use the alternate API endpoint
                media_info = self.client.public_request(
                    f"p/{shortcode}/",
                    params={"__a": "1", "__d": "dis"}
                )
                
                # Look for media ID in the GraphQL response
                if media_info and "graphql" in media_info:
                    if "shortcode_media" in media_info["graphql"]:
                        return str(media_info["graphql"]["shortcode_media"]["id"])
            except Exception as e:
                print(f"web_api method failed: {e}")
                
            # Last resort: Try algorithmic conversion 
            # This is a fallback based on how Instagram historically converted between shortcodes and IDs
            # Note: This method may not always work as Instagram could change their algorithm
            try:
                # Attempt to decode the shortcode using Instagram's Base64 variant
                alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
                media_id = 0
                for char in shortcode:
                    media_id = (media_id * 64) + alphabet.index(char)
                
                if media_id > 0:
                    return str(media_id)
            except Exception:
                pass
                
            return None
        except Exception as e:
            print(f"Failed to convert shortcode {shortcode} to media ID: {e}")
            return None 