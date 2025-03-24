#!/usr/bin/env python
"""
Instagram Cookie Validator and Profile Checker
No server setup required - just run this script directly.
"""
import json
import requests
import sys
import os
from datetime import datetime

def test_instagram_cookies(username, sessionid, csrftoken):
    """Test if Instagram cookies are valid and fetch basic profile info."""
    print("\n=== Testing Instagram Cookies ===")
    print(f"Testing cookies for: {username}")
    
    # Create direct cookie test data
    cookies = {
        "sessionid": sessionid,
        "csrftoken": csrftoken,
        "ds_user_id": "",  # Will work without this
    }
    
    # Make a direct request to Instagram API to verify cookies
    try:
        # Request user profile to see if cookies work
        session = requests.Session()
        
        # Add cookies to session
        for key, value in cookies.items():
            if value:  # Only set non-empty cookies
                session.cookies.set(key, value, domain=".instagram.com")
        
        # Test by requesting user information
        url = f"https://www.instagram.com/{username}/?__a=1&__d=1"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json",
            "Referer": "https://www.instagram.com/",
        }
        
        print("\nSending test request to Instagram...")
        response = session.get(url, headers=headers)
        
        if response.status_code == 200:
            print("\n✅ SUCCESS! Your Instagram cookies are valid.")
            print(f"Successfully authenticated as: {username}")
            
            try:
                # Try to parse basic profile info
                data = response.json()
                if data and "graphql" in data and "user" in data["graphql"]:
                    user = data["graphql"]["user"]
                    print("\n--- Profile Information ---")
                    print(f"Username: {user.get('username')}")
                    print(f"Full Name: {user.get('full_name')}")
                    print(f"Biography: {user.get('biography')[:50]}..." if len(user.get('biography', '')) > 50 else user.get('biography', 'None'))
                    print(f"Followers: {user.get('edge_followed_by', {}).get('count', 0)}")
                    print(f"Following: {user.get('edge_follow', {}).get('count', 0)}")
                    print(f"Posts: {user.get('edge_owner_to_timeline_media', {}).get('count', 0)}")
                    
                    # Export cookie information for easy use
                    save_cookie_info(username, sessionid, csrftoken)
            except json.JSONDecodeError:
                print("Could not parse profile information, but authentication was successful.")
            return True
        else:
            print(f"\n❌ ERROR: Instagram returned status code {response.status_code}")
            print("Your cookies may be invalid or expired.")
            print("Response:", response.text[:200] + "..." if len(response.text) > 200 else response.text)
            return False
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False

def save_cookie_info(username, sessionid, csrftoken):
    """Save cookie info to a file for easy reference."""
    try:
        filename = f"{username}_cookies.json"
        data = {
            "username": username,
            "cookies": {
                "sessionid": sessionid,
                "csrftoken": csrftoken
            },
            "expires": "These cookies will eventually expire (typically after a few weeks)",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"\nCookie information saved to {filename} for future reference.")
    except Exception as e:
        print(f"Could not save cookie information: {str(e)}")

def main():
    """Main function to collect Instagram cookies and test them."""
    print("=== Instagram Cookie Validator ===")
    print("This tool tests if your Instagram cookies are valid.")
    print("\nFollow these steps to get your Instagram cookies:")
    print("1. Log in to Instagram in your browser")
    print("2. Open developer tools (F12 or right-click → Inspect)")
    print("3. Go to Application tab → Cookies → instagram.com")
    print("4. Find and copy the values for 'sessionid' and 'csrftoken'")
    
    username = input("\nYour Instagram username: ")
    sessionid = input("sessionid cookie: ")
    csrftoken = input("csrftoken cookie: ")
    
    if not username or not sessionid:
        print("Error: Username and sessionid are required.")
        return
    
    test_instagram_cookies(username, sessionid, csrftoken)
    
    print("\n=== Cookie Usage Information ===")
    print("- These cookies can be used with the InstaTLDR application")
    print("- They will eventually expire (typically after a few weeks)")
    print("- When they expire, log in to Instagram again and get fresh cookies")
    print("- Keep your cookies secure as they provide access to your account")

if __name__ == "__main__":
    main() 