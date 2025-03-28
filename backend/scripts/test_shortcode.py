#!/usr/bin/env python
"""
Test script to verify shortcode to media ID conversion with Instagram API
"""
import sys
import time
import logging
from pathlib import Path

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('instagram-test')

from core.auth import InstagramAuthenticator

def convert_shortcode_to_media_id(shortcode, client):
    """Try various methods to convert a shortcode to a media ID"""
    logger.info(f"Testing conversion for shortcode: {shortcode}")
    
    # Method 1: Direct via library method
    try:
        if hasattr(client, 'media_pk_from_code'):
            media_id = client.media_pk_from_code(shortcode)
            logger.info(f"Method 1 (instagrapi): Success! Media ID: {media_id}")
            return media_id
    except Exception as e:
        logger.warning(f"Method 1 failed: {e}")
    
    # Method 2: Web API
    try:
        info = client.public_request(
            f"p/{shortcode}/",
            params={"__a": "1", "__d": "dis"}
        )
        if "graphql" in info and "shortcode_media" in info["graphql"]:
            media_id = info["graphql"]["shortcode_media"]["id"]
            logger.info(f"Method 2 (web API): Success! Media ID: {media_id}")
            return media_id
    except Exception as e:
        logger.warning(f"Method 2 failed: {e}")
    
    # Method 3: Using oembed
    try:
        oembed_data = client.private_request(
            "oembed/",
            params={"url": f"https://www.instagram.com/p/{shortcode}/"}
        )
        if "media_id" in oembed_data:
            media_id = oembed_data["media_id"]
            logger.info(f"Method 3 (oembed): Success! Media ID: {media_id}")
            return media_id
    except Exception as e:
        logger.warning(f"Method 3 failed: {e}")
    
    # Method 4: Manual Base64 decoding approach
    try:
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        media_id = 0
        for char in shortcode:
            media_id = (media_id * 64) + alphabet.index(char)
        
        if media_id > 0:
            logger.info(f"Method 4 (algorithmic): Success! Media ID: {media_id}")
            return str(media_id)
    except Exception as e:
        logger.warning(f"Method 4 failed: {e}")
    
    logger.error(f"All methods failed for shortcode: {shortcode}")
    return None

def test_direct_media_info(client, media_id, shortcode):
    """Test retrieving media info directly with the ID"""
    logger.info(f"Testing direct media info retrieval with ID: {media_id}")
    
    # Try the standard API first
    try:
        media_info = client.private_request(f"media/{media_id}/info/", {})
        if media_info and "items" in media_info and media_info["items"]:
            logger.info(f"Standard API successful! Includes {len(media_info['items'])} items")
            return True
    except Exception as e:
        logger.warning(f"Standard API failed: {e}")
    
    # Try the API v1 endpoint
    try:
        media_info = client.private_request(f"api/v1/media/{media_id}/info/", {})
        if media_info and "items" in media_info and media_info["items"]:
            logger.info(f"API v1 endpoint successful! Includes {len(media_info['items'])} items")
            return True
    except Exception as e:
        logger.warning(f"API v1 endpoint failed: {e}")
        
    # Try the shortcode version
    try:
        media_info = client.private_request(f"api/v1/media/{shortcode}/info/", {})
        if media_info and "items" in media_info and media_info["items"]:
            logger.info(f"API with shortcode successful! Includes {len(media_info['items'])} items")
            return True
    except Exception as e:
        logger.warning(f"API with shortcode failed: {e}")
    
    logger.error(f"All direct media info retrieval methods failed")
    return False

def main():
    """Main function to test shortcode conversion"""
    logger.info("Starting shortcode to media ID test")
    
    # Initialize authenticator
    session_path = Path(__file__).parent.parent / "session.json"
    auth = InstagramAuthenticator(session_file=str(session_path))
    
    # Try to login
    if not auth.login_with_session():
        logger.warning("Session login failed. Please enter credentials:")
        username = input("Enter Instagram username: ")
        password = input("Enter Instagram password: ")
        if not auth.login(username, password):
            logger.error("Login failed. Exiting.")
            return

    logger.info("Login successful!")
    
    # Test shortcodes
    test_shortcodes = [
        "DHtpc-MyWsV",
        "DHadDCQsEWD", 
        "DHtPf8DR4JU",
        "C8VFqUhvGO5"  # A recent shortcode for comparison
    ]
    
    for shortcode in test_shortcodes:
        try:
            # Try to convert shortcode to media ID
            media_id = convert_shortcode_to_media_id(shortcode, auth.client)
            
            if media_id:
                logger.info(f"Shortcode {shortcode} converted to media ID: {media_id}")
                
                # Test direct media info retrieval using the ID
                test_direct_media_info(auth.client, media_id, shortcode)
            else:
                logger.error(f"Couldn't convert shortcode {shortcode} to media ID")
                
            # Add a delay between requests
            time.sleep(3)
            
        except Exception as e:
            logger.error(f"Error processing shortcode {shortcode}: {e}")
    
    logger.info("Testing completed!")

if __name__ == "__main__":
    main() 