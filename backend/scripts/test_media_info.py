#!/usr/bin/env python
"""
Test script to troubleshoot Instagram API media info fetching
"""
import sys
import time
import random
import os
from pathlib import Path
import json
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("instagram-session-debug")

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from core.auth import InstagramAuthenticator
from services.direct_feed_service import DirectFeedService

def check_session_file(session_path):
    """Check and print session file details for debugging"""
    if os.path.exists(session_path):
        logger.info(f"Session file exists at: {session_path}")
        try:
            with open(session_path, "r") as f:
                session_data = json.load(f)
                
            # Print session details (excluding sensitive info)
            keys = list(session_data.keys())
            logger.info(f"Session file contains keys: {keys}")
            
            # Check for critical session components
            if "cookie" in session_data and len(session_data["cookie"]) > 0:
                cookie_count = len(session_data["cookie"].split(";"))
                logger.info(f"Cookie string present with {cookie_count} components")
            else:
                logger.warning("Cookie missing or empty in session file")
                
            if "authorization_data" in session_data:
                logger.info("Authorization data present")
            else:
                logger.warning("Authorization data missing")
                
            # Check session freshness
            if "created_ts" in session_data:
                created_time = session_data.get("created_ts", 0)
                current_time = time.time()
                age_hours = (current_time - created_time) / 3600
                logger.info(f"Session age: {age_hours:.1f} hours")
                if age_hours > 24:
                    logger.warning("Session is older than 24 hours, may be expired")
            else:
                logger.warning("Session creation timestamp missing")
                
        except json.JSONDecodeError:
            logger.error("Session file exists but contains invalid JSON")
        except Exception as e:
            logger.error(f"Error reading session file: {e}")
    else:
        logger.warning(f"Session file does not exist at: {session_path}")
    
    return os.path.exists(session_path)

def save_raw_session(auth_client, filename="debug_session.json"):
    """Save raw session data for debugging"""
    try:
        # Directly access client attributes
        session_data = {
            "user_id": auth_client.user_id,
            "uuid": auth_client.uuid,
            "phone_id": auth_client.phone_id,
            "authorization": auth_client.authorization,
            "mid": auth_client.mid,
            "token": auth_client.token,
            "timezone_offset": auth_client.timezone_offset,
            "device_settings": auth_client.device_settings,
        }
        
        # Save to a debug file
        with open(filename, "w") as f:
            json.dump(session_data, f, indent=2)
        
        logger.info(f"Saved raw session data to {filename}")
    except Exception as e:
        logger.error(f"Failed to save raw session: {e}")

def main():
    """Test media info fetching with different methods"""
    logger.info("Testing media info fetching and session management...")
    
    # Initialize authenticator with explicit session path
    session_path = Path(__file__).parent.parent / "session.json"
    session_path_str = str(session_path)
    
    # Check session file before authentication
    logger.info("Checking session file before authentication")
    check_session_file(session_path_str)
    
    auth = InstagramAuthenticator(session_file=session_path_str)
    
    # Try to login with session
    session_login_success = False
    try:
        logger.info("Attempting login with session...")
        session_login_success = auth.login_with_session()
        if session_login_success:
            logger.info("✅ Successfully logged in using session")
            # Save session upon successful login for future debugging
            save_raw_session(auth.client, "successful_session.json")
        else:
            logger.warning("❌ Session login failed")
    except Exception as e:
        logger.error(f"Session login error: {e}")
    
    # If session login failed, try with credentials
    if not session_login_success:
        logger.info("No valid session, please login manually")
        username = input("Enter your Instagram username: ")
        password = input("Enter your Instagram password: ")
        
        try:
            logger.info(f"Attempting login with credentials for {username}...")
            if not auth.login(username, password):
                logger.error("❌ Login with credentials failed")
                return
            logger.info("✅ Login successful with credentials")
            
            # Check if session was saved after successful login
            logger.info("Checking if new session was saved")
            check_session_file(session_path_str)
            save_raw_session(auth.client, "new_login_session.json")
        except Exception as e:
            logger.error(f"Credential login error: {e}")
            return
    
    # Initialize direct feed service
    logger.info("Initializing DirectFeedService...")
    feed_service = DirectFeedService(auth.client)
    
    # Test with a few post codes
    test_posts = [
        {"code": "DHtpc-MyWsV", "type": "shortcode"},
        {"code": "DHadDCQsEWD", "type": "shortcode"},
        {"code": "DHtPf8DR4JU", "type": "shortcode"},
    ]
    
    for post in test_posts:
        shortcode = post["code"]
        logger.info(f"\n===== Testing post: {shortcode} =====")
        
        # Try to get numeric ID from shortcode
        logger.info(f"Trying to convert shortcode to media ID...")
        numeric_id = feed_service._shortcode_to_media_id(shortcode)
        if numeric_id:
            logger.info(f"✅ Converted to numeric ID: {numeric_id}")
        else:
            logger.warning("❌ Failed to convert to numeric ID")
        
        # Try various methods to fetch post info
        logger.info(f"Trying different methods to fetch post info:")
        
        # Method 1: Try with GraphQL API
        try:
            logger.info("Method 1: Using GraphQL API")
            media_info = auth.client.public_request(
                f"api/v1/feed/user/{shortcode}/username/"
            )
            logger.info(f"✅ Success! Response contains {len(json.dumps(media_info))} characters")
            # Print the first few keys to see what's in the response
            if media_info:
                logger.info(f"Keys in response: {list(media_info.keys())}")
        except Exception as e:
            logger.warning(f"❌ Failed: {e}")
        
        # Method 2: Try with instagrapi built-in methods
        try:
            logger.info("Method 2: Using instagrapi's media_info methods")
            
            # Try different helper methods
            if hasattr(auth.client, 'media_info_by_url'):
                try:
                    logger.info("Attempting media_info_by_url...")
                    media_info = auth.client.media_info_by_url(f"https://www.instagram.com/p/{shortcode}/")
                    logger.info(f"✅ Success! Got media info object")
                    if hasattr(media_info, 'dict'):
                        media_dict = media_info.dict()
                        logger.info(f"Media ID: {media_dict.get('id')}")
                        logger.info(f"Media type: {media_dict.get('media_type')}")
                except Exception as e:
                    logger.warning(f"media_info_by_url failed: {e}")
            
            # Try alternative media_pk_from_code
            if hasattr(auth.client, 'media_pk_from_code'):
                try:
                    logger.info("Attempting media_pk_from_code...")
                    media_pk = auth.client.media_pk_from_code(shortcode)
                    logger.info(f"✅ Got media PK: {media_pk}")
                except Exception as e:
                    logger.warning(f"media_pk_from_code failed: {e}")
        except Exception as e:
            logger.warning(f"❌ All instagrapi methods failed: {e}")
        
        # Method 3: Try with direct API endpoint
        if numeric_id:
            try:
                logger.info("Method A: Using Instagram app API without v1 prefix")
                post_data = auth.client.private_request(
                    f"media/{numeric_id}/info/", {}
                )
                logger.info(f"✅ Success! Response contains {len(json.dumps(post_data))} characters")
                if "items" in post_data and post_data["items"]:
                    post_item = post_data["items"][0]
                    logger.info(f"Media ID: {post_item.get('id')}")
                    logger.info(f"Media type: {post_item.get('media_type')}")
            except Exception as e:
                logger.warning(f"❌ Failed method A: {e}")
                
                try:
                    logger.info("Method B: Using alternative API")
                    post_data = auth.client.private_request(
                        f"feed/user/{shortcode}/", {}
                    )
                    logger.info(f"✅ Success! Response contains {len(json.dumps(post_data))} characters")
                except Exception as e:
                    logger.warning(f"❌ Failed method B: {e}")
        
        # Wait a bit before the next request
        time.sleep(random.uniform(3, 6))
    
    logger.info("\nTesting completed")

if __name__ == "__main__":
    main() 