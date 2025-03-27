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
import os
import time

# Try to import colorama for cross-platform color support
try:
    from colorama import init, Fore, Style
    init()  # Initialize colorama
    HAS_COLOR = True
except ImportError:
    # Create dummy color constants if colorama is not available
    class DummyFore:
        def __getattr__(self, name):
            return ""
    class DummyStyle:
        def __getattr__(self, name):
            return ""
    Fore = DummyFore()
    Style = DummyStyle()
    HAS_COLOR = False

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from core.auth import InstagramAuthenticator
from services.direct_feed_service import DirectFeedService

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully."""
    print("\nStopping feed collection...")
    sys.exit(0)

# Custom simple interactive menu
def show_interactive_menu(options, descriptions, default_selection=0):
    """
    Display an interactive menu with arrow key navigation.
    
    Args:
        options: List of menu options to display
        descriptions: List of descriptions for each option
        default_selection: Default selected index
    
    Returns:
        Selected index
    """
    import readchar
    
    current_selection = default_selection
    
    # Function to clear the screen if supported
    def clear_screen():
        os.system('cls' if os.name == 'nt' else 'clear')
    
    # Function to display the menu
    def display_menu():
        clear_screen()
        print("\nMode SELECT ( ↑↓ to navigate, press Enter to select):\n")
        
        for i, option in enumerate(options):
            prefix = "→ " if i == current_selection else "  "
            print(f"{prefix}{option}")
        
        # Display description of current selection
        if 0 <= current_selection < len(descriptions):
            print("\n" + "-" * 60)
            print(descriptions[current_selection])
            print("-" * 60)
    
    # Display initial menu
    display_menu()
    
    # Handle key presses
    while True:
        key = readchar.readkey()
        
        if key == readchar.key.UP or key == 'k':  # Up arrow or k
            current_selection = (current_selection - 1) % len(options)
            display_menu()
        elif key == readchar.key.DOWN or key == 'j':  # Down arrow or j
            current_selection = (current_selection + 1) % len(options)
            display_menu()
        elif key == readchar.key.ENTER:  # Enter key
            return current_selection
        elif key == '\x03':  # Ctrl+C
            raise KeyboardInterrupt
        # Ignore other keys

def main():
    """Main entry point for collecting feed posts."""
    # Register signal handler for CTRL+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Collect Instagram feed posts using direct API endpoints. "
                                              "Posts are saved to JSON files with the logged-in username and session ID. "
                                              "During a single session, posts are appended to the same file until the maximum "
                                              "posts per file limit is reached.")
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
        "--ultra-safe-mode",
        help="Enable ultra-safe mode that mimics natural user behavior with very long delays",
        action="store_true"
    )
    parser.add_argument(
        "--batch-size",
        help="Number of posts per batch/request (default: 10)",
        type=int,
        default=10
    )
    parser.add_argument(
        "--simulate-browsing",
        help="Simulate realistic browsing by adding random long pauses",
        action="store_true"
    )
    parser.add_argument(
        "--max-posts-per-file",
        help="Maximum number of posts to store in a single JSON file (default: 500)",
        type=int,
        default=500
    )
    
    args = parser.parse_args()
    
    # Apply ultra-safe mode if requested (highest priority)
    if args.ultra_safe_mode:
        # Very conservative settings
        args.min_delay = 15  # Minimum 15 seconds between requests
        args.max_delay = 45  # Up to 45 seconds between requests
        args.batch_size = 3  # Only 3 posts per batch
        args.simulate_browsing = True  # Enable browsing simulation
        print("\n⚠️ ULTRA-SAFE MODE ENABLED - using extremely conservative settings")
        print("   This mode mimics natural human browsing with long pauses")
    # Apply safe mode if requested and ultra-safe not enabled
    elif args.safe_mode:
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
        print("   - Use safer modes for more conservative settings")
        print("   - Avoid collecting large numbers of posts in one session")
        print("   - Space out your collection sessions by several hours")
        print("   - Stop collection if you notice any account restrictions\n")
        
        # Mode selection prompt if no mode is specified via command line
        if not (args.safe_mode or args.ultra_safe_mode or args.simulate_browsing):
            # Define menu options with colors
            menu_options = [
                f"{Fore.GREEN}• Safe Mode{Style.RESET_ALL}",
                f"{Fore.LIGHTBLUE_EX}• Ultra-Safe Mode{Style.RESET_ALL}",
                f"{Fore.RED}• Standard Mode{Style.RESET_ALL}",
                f"{Fore.LIGHTBLACK_EX}• Custom Mode{Style.RESET_ALL}"
            ]
            
            # Define descriptions for each mode
            menu_descriptions = [
                f"{Fore.GREEN}SAFE MODE:{Style.RESET_ALL} Recommended for most users\n- 8-15 second delays between requests\n- 5 posts per batch\n- Good balance of safety and speed",
                f"{Fore.LIGHTBLUE_EX}ULTRA-SAFE MODE:{Style.RESET_ALL} For maximum account protection\n- 15-45 second delays between requests\n- Only 3 posts per batch\n- Simulates realistic browsing patterns\n- Very slow but extremely safe",
                f"{Fore.RED}STANDARD MODE:{Style.RESET_ALL} For burner accounts only\n- 3-10 second delays between requests\n- 10 posts per batch\n- Higher risk of detection\n- NOT recommended for main accounts",
                f"{Fore.LIGHTBLACK_EX}CUSTOM MODE:{Style.RESET_ALL} For advanced users\n- Manually configure all parameters\n- Set your own risk tolerance\n- For users who understand the Instagram API limits"
            ]
            
            # Default selection index (0-based, so 0 = safe mode)
            default_menu_index = 0
            selected_index = default_menu_index
            
            try:
                # Try to use our custom interactive menu
                try:
                    import readchar
                    selected_index = show_interactive_menu(menu_options, menu_descriptions, default_menu_index)
                except (ImportError, Exception) as e:
                    print(f"\nFallback to text menu: {e}")
                    
                    # Fallback to simple text menu
                    print("\nMode SELECT (enter number, press Enter to select):\n")
                    for i, option in enumerate(menu_options):
                        print(f"{i+1}. {option}")
                    
                    # Print description for default option
                    print("\n" + "-" * 60)
                    print(menu_descriptions[default_menu_index])
                    print("-" * 60 + "\n")
                    
                    user_input = input(f"Select mode [1-4] (default: 1 - Safe Mode): ").strip()
                    if user_input:
                        selected_index = int(user_input) - 1
                        if selected_index < 0 or selected_index >= len(menu_options):
                            selected_index = default_menu_index
                    else:
                        selected_index = default_menu_index
            except Exception as e:
                print(f"\nError during mode selection: {e}")
                print(f"Defaulting to Safe Mode")
                selected_index = 0  # Default to Safe Mode
            
            # Process the user's selection
            if selected_index == 0:  # Safe Mode
                print(f"\n{Fore.GREEN}Selected Safe Mode{Style.RESET_ALL}")
                args.safe_mode = True
                args.min_delay = max(args.min_delay, 8)  # At least 8 seconds
                args.max_delay = max(args.max_delay, 15)  # At least 15 seconds
                args.batch_size = min(args.batch_size, 5)  # Maximum 5 posts per batch
                args.num_posts = 20  # Set fixed number of posts for safe mode
            elif selected_index == 1:  # Ultra-Safe Mode
                print(f"\n{Fore.LIGHTBLUE_EX}Selected Ultra-Safe Mode{Style.RESET_ALL}")
                args.ultra_safe_mode = True
                args.min_delay = 15  # Minimum 15 seconds between requests
                args.max_delay = 45  # Up to 45 seconds between requests
                args.batch_size = 3  # Only 3 posts per batch
                args.simulate_browsing = True  # Enable browsing simulation
                args.num_posts = 15  # Set fixed number of posts for ultra-safe mode
            elif selected_index == 2:  # Standard Mode
                print(f"\n{Fore.RED}Selected Standard Mode (Not Recommended for Main Accounts){Style.RESET_ALL}")
                confirm = input("This mode has higher risk of triggering restrictions. Continue? (y/n): ")
                if confirm.lower() != 'y':
                    print("Operation cancelled.")
                    return
                args.num_posts = 30  # Set fixed number of posts for standard mode
            elif selected_index == 3:  # Custom Mode
                print(f"\n{Fore.LIGHTBLACK_EX}Selected Custom Mode{Style.RESET_ALL}")
                # Get custom delay parameters
                try:
                    min_delay_input = input(f"Minimum delay in seconds (current: {args.min_delay}): ")
                    if min_delay_input.strip():
                        args.min_delay = int(min_delay_input)
                        
                    max_delay_input = input(f"Maximum delay in seconds (current: {args.max_delay}): ")
                    if max_delay_input.strip():
                        args.max_delay = int(max_delay_input)
                        
                    batch_size_input = input(f"Batch size (current: {args.batch_size}): ")
                    if batch_size_input.strip():
                        args.batch_size = int(batch_size_input)
                    
                    # Only ask for post count in custom mode
                    post_count_input = input(f"How many posts would you like to retrieve? (default: 50, recommended: 20-30): ")
                    if post_count_input.strip():
                        args.num_posts = int(post_count_input)
                        if args.num_posts > 50:
                            confirm = input(f"Collecting {args.num_posts} posts may increase risk of detection. Continue? (y/n): ")
                            if confirm.lower() != 'y':
                                print("Operation cancelled.")
                                return
                        
                    simulate_input = input("Simulate browsing behavior? (y/n): ")
                    args.simulate_browsing = simulate_input.lower() == 'y'
                except ValueError:
                    print("Invalid input. Using default values.")
            else:
                # Fallback to safe mode if something unexpected happens
                print(f"Defaulting to Safe Mode")
                args.safe_mode = True
                args.min_delay = max(args.min_delay, 8)
                args.max_delay = max(args.max_delay, 15)
                args.batch_size = min(args.batch_size, 5)
                args.num_posts = 20  # Set fixed number of posts for safe mode
        
        # Only prompt for number of posts if specified on command line and not in interactive mode
        if args.num_posts == 50 and (args.safe_mode or args.ultra_safe_mode or args.simulate_browsing):
            # If command line arguments were used (not interactive menu), use those values
            pass
        
        # Initialize direct feed service
        feed_service = DirectFeedService(
            client=auth.client,
            output_dir=args.output_dir,
            min_delay=args.min_delay,
            max_delay=args.max_delay,
            batch_size=args.batch_size,
            simulate_browsing=args.simulate_browsing,
            max_posts_per_file=args.max_posts_per_file
        )
        
        print(f"Will collect up to {args.num_posts} posts with delays between {args.min_delay}-{args.max_delay} seconds")
        print(f"Using batch size of {args.batch_size} posts per request")
        if args.simulate_browsing:
            print("Simulating natural browsing patterns with random long pauses")
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