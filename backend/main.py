import os
from typing import Optional

from core.auth import InstagramAuthenticator
from core.exceptions import InstagramAuthError

def get_credentials() -> tuple[str, str]:
    """Get Instagram credentials from user input."""
    print("\nInstagram Login")
    print("-" * 20)
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    return username, password

def handle_login_retry() -> bool:
    """Ask user if they want to retry login."""
    while True:
        response = input("\nWould you like to retry login? (y/n): ").strip().lower()
        if response in ['y', 'n']:
            return response == 'y'
        print("Please enter 'y' or 'n'")

def main():
    """Main entry point for the Instagram Data Collector."""
    auth = InstagramAuthenticator()
    
    try:
        # Check if already logged in
        if auth.is_logged_in():
            username = auth.get_current_username()
            if username:
                print(f"\nAlready logged in as: {username}")
            else:
                print("\nAlready logged in!")
            return
        
        print("\nChecking for existing session...")
        # Try to login with session first
        if auth.login_with_session():
            return
        
        print("\nNo valid session found. Please login with your credentials.")
        username, password = get_credentials()
        if auth.login(username, password):
            print("\nLogin successful! Session has been saved.")
    
    except InstagramAuthError as e:
        print(f"\nError: {str(e)}")
        if handle_login_retry():
            main()
        return
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        if handle_login_retry():
            main()
        return

if __name__ == "__main__":
    main()
