#!/usr/bin/env python
"""
Script to collect Instagram feed posts using direct API endpoints.
This approach bypasses instagrapi's high-level methods and directly uses
Instagram's private API endpoints.
"""
import sys
import signal
import argparse
from pathlib import Path

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from core.auth import InstagramAuthenticator
from services.direct_feed_service import DirectFeedService

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully."""
    print("\nStopping feed collection...")
    sys.exit(0)

def main():
    """Main entry point for collecting feed posts."""
    # Register signal handler for CTRL+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Collect Instagram feed posts using direct API endpoints")
    parser.add_argument(
        "-n", "--num-posts",
        help="Maximum number of posts to collect (default: 50)",
        type=int,
        default=50
    )
    parser.add_argument(
        "--min-delay",
        help="Minimum delay between requests in seconds (default: 3)",
        type=int,
        default=3
    )
    parser.add_argument(
        "--max-delay",
        help="Maximum delay between requests in seconds (default: 10)",
        type=int,
        default=10
    )
    parser.add_argument(
        "--output-dir",
        help="Directory to save feed posts (default: data/direct_feed)",
        default="data/direct_feed"
    )
    parser.add_argument(
        "--safe-mode",
        help="Enable extra-safe mode with longer delays and fewer posts per batch",
        action="store_true"
    )
    parser.add_argument(
        "--batch-size",
        help="Number of posts per batch/request (default: 10)",
        type=int,
        default=10
    )
    
    args = parser.parse_args()
    
    # Apply safe mode if requested
    if args.safe_mode:
        args.min_delay = max(args.min_delay, 8)  # At least 8 seconds
        args.max_delay = max(args.max_delay, 15)  # At least 15 seconds
        args.batch_size = min(args.batch_size, 5)  # Maximum 5 posts per batch
        print("\n⚠️ Safe mode enabled - using slower and more careful collection")
    
    try:
        # Initialize authenticator
        auth = InstagramAuthenticator()
        
        # Check if already logged in
        if not auth.login_with_session():
            print("Please login first using main.py")
            return
        
        # Get logged in user info
        current_user = auth.client.user_info(auth.client.user_id)
        if not current_user:
            print("Could not get current user information")
            return
            
        username = current_user.username
        print(f"\nCollecting feed posts for your account (@{username})...")
        
        # Safety warning
        print("\n⚠️ IMPORTANT: Using Instagram's private API endpoints directly")
        print("   carries some risk of triggering temporary restrictions.")
        print("   For safer operation:")
        print("   - Use the --safe-mode flag for more conservative settings")
        print("   - Avoid collecting large numbers of posts in one session")
        print("   - Space out your collection sessions by several hours")
        print("   - Stop collection if you notice any account restrictions\n")
        
        # Prompt for number of posts if not specified in command line
        if args.num_posts == 50:  # Default value
            try:
                user_input = input(f"How many posts would you like to retrieve? (default: {args.num_posts}, recommended: 20-30): ")
                if user_input.strip():
                    args.num_posts = int(user_input)
                    if args.num_posts > 50 and not args.safe_mode:
                        confirm = input(f"Collecting {args.num_posts} posts may increase risk of detection. Continue? (y/n): ")
                        if confirm.lower() != 'y':
                            print("Operation cancelled.")
                            return
                    print(f"Will collect up to {args.num_posts} posts")
            except ValueError:
                print(f"Invalid input. Using default value of {args.num_posts} posts.")
        
        # Initialize direct feed service
        feed_service = DirectFeedService(
            client=auth.client,
            output_dir=args.output_dir,
            min_delay=args.min_delay,
            max_delay=args.max_delay,
            batch_size=args.batch_size
        )
        
        print(f"Will collect up to {args.num_posts} posts with delays between {args.min_delay}-{args.max_delay} seconds")
        print(f"Using batch size of {args.batch_size} posts per request")
        print("Press Ctrl+C to stop collection at any time")
        
        # Get feed posts
        posts = feed_service.get_feed(max_posts=args.num_posts)
        
        # Print summary
        print(f"\nSuccessfully collected {len(posts)} feed posts")
        print(f"Posts saved to {args.output_dir}")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 