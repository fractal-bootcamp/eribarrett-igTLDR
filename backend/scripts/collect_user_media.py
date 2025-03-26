#!/usr/bin/env python
"""
Script to collect Instagram posts from specific users.
"""
import sys
import signal
import argparse
from pathlib import Path

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from core.auth import InstagramAuthenticator
from services.user_service import UserService

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully."""
    print("\nStopping media collection...")
    sys.exit(0)

def main():
    """Main entry point for user media collection."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Collect Instagram posts from specific users")
    parser.add_argument(
        "usernames", 
        nargs="*", 
        help="Instagram usernames to collect posts from"
    )
    parser.add_argument(
        "-f", "--file", 
        help="File containing a list of usernames (one per line)"
    )
    parser.add_argument(
        "-n", "--num-posts", 
        type=int, 
        default=20, 
        help="Number of posts to collect per user (default: 20)"
    )
    parser.add_argument(
        "--min-delay", 
        type=int, 
        default=3, 
        help="Minimum delay between requests in seconds (default: 3)"
    )
    parser.add_argument(
        "--max-delay", 
        type=int, 
        default=10, 
        help="Maximum delay between requests in seconds (default: 10)"
    )
    
    args = parser.parse_args()
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Get list of usernames
    usernames = []
    
    if args.usernames:
        usernames.extend(args.usernames)
        
    if args.file:
        try:
            with open(args.file, 'r') as f:
                file_usernames = [line.strip() for line in f if line.strip()]
                usernames.extend(file_usernames)
        except Exception as e:
            print(f"Error reading username file: {e}")
            return
    
    if not usernames:
        print("No usernames provided. Use command line arguments or a file.")
        parser.print_help()
        return
    
    try:
        # Initialize authenticator
        auth = InstagramAuthenticator()
        
        # Check if already logged in
        if not auth.login_with_session():
            print("Please login first using main.py")
            return
        
        # Initialize user service
        user_service = UserService(
            client=auth.client,
            min_delay=args.min_delay,
            max_delay=args.max_delay
        )
        
        print("\nStarting media collection...")
        print(f"Will collect up to {args.num_posts} posts from {len(usernames)} users")
        print(f"Using random delays between {args.min_delay}-{args.max_delay} seconds")
        print("Press Ctrl+C to stop")
        print("-" * 50)
        
        # Start collecting user media
        user_service.collect_multiple_users(usernames, args.num_posts)
        
        print("\nMedia collection completed!")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 