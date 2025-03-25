#!/usr/bin/env python
"""
A simple diagnostic script to test Instagram feed access and inspect the response.
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from core.auth import InstagramAuthenticator

def save_response(data, filename):
    """Save API response to a JSON file for inspection."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"Response saved to {filename}")

def main():
    """Main entry point for the script."""
    print("Instagram Feed Test Script")
    print("-" * 50)
    
    # Initialize authenticator
    auth = InstagramAuthenticator()
    
    # Try to login with session
    if not auth.login_with_session():
        print("Failed to login with session. Please login with main.py first.")
        return
    
    print("Successfully logged in")
    
    # Create output directory
    output_dir = Path("data/diagnostics")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Test 1: Get timeline feed
    print("\nTest 1: Get timeline feed")
    try:
        feed_response = auth.client.get_timeline_feed()
        print(f"Response type: {type(feed_response)}")
        
        if isinstance(feed_response, dict):
            print(f"Response keys: {list(feed_response.keys())}")
            
            # Check for items
            if "items" in feed_response:
                items = feed_response.get("items", [])
                print(f"Found {len(items)} items in feed")
                
                # Save detailed response for inspection
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = output_dir / f"feed_response_{timestamp}.json"
                
                # Filter JSON-serializable content
                filtered_response = {}
                for key, value in feed_response.items():
                    try:
                        # Test if value is JSON serializable
                        json.dumps(value)
                        filtered_response[key] = value
                    except (TypeError, OverflowError):
                        filtered_response[key] = str(value)
                
                save_response(filtered_response, filename)
                
                # Save first 5 items for inspection
                if items:
                    first_items = items[:5]
                    first_items_file = output_dir / f"feed_items_{timestamp}.json"
                    save_response(first_items, first_items_file)
            else:
                print("No 'items' key found in response")
        else:
            print("Response is not a dictionary")
            
    except Exception as e:
        print(f"Error getting timeline feed: {str(e)}")
    
    # Test 2: Try direct private API request
    print("\nTest 2: Try direct private API request")
    try:
        results = auth.client.private_request("feed/timeline/")
        print(f"Private API response type: {type(results)}")
        
        if isinstance(results, dict):
            print(f"Response keys: {list(results.keys())}")
            
            # Save response for inspection
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = output_dir / f"private_feed_response_{timestamp}.json"
            
            # Filter JSON-serializable content
            filtered_response = {}
            for key, value in results.items():
                try:
                    # Test if value is JSON serializable
                    json.dumps(value)
                    filtered_response[key] = value
                except (TypeError, OverflowError):
                    filtered_response[key] = str(value)
            
            save_response(filtered_response, filename)
        else:
            print("Private API response is not a dictionary")
            
    except Exception as e:
        print(f"Error with private request: {str(e)}")
    
    # Test 3: Try user's own media
    print("\nTest 3: Try get user's own media")
    try:
        # Get current user info
        user_id = auth.client.user_id
        print(f"Current user ID: {user_id}")
        
        user_info = auth.client.user_info(user_id)
        print(f"Username: {user_info.username}")
        
        # Try to get user's media
        medias = auth.client.user_medias(user_id, 5)
        print(f"Found {len(medias)} media items for current user")
        
        if medias:
            # Save user media for inspection
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = output_dir / f"user_media_{timestamp}.json"
            
            # Convert media objects to dictionaries
            media_dicts = []
            for media in medias:
                try:
                    media_dict = media.dict()
                    media_dicts.append(media_dict)
                except Exception as e:
                    print(f"Error converting media to dict: {e}")
                    # Try manual conversion
                    media_dict = {
                        "pk": str(media.pk),
                        "id": media.id,
                        "code": media.code,
                        "media_type": media.media_type,
                        "taken_at": str(media.taken_at),
                    }
                    media_dicts.append(media_dict)
            
            save_response(media_dicts, filename)
            
    except Exception as e:
        print(f"Error getting user media: {str(e)}")
    
    print("\nDiagnostic tests completed.")
    print("Please check the data/diagnostics directory for the saved responses.")

if __name__ == "__main__":
    main() 