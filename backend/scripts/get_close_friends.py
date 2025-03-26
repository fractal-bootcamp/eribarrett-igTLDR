#!/usr/bin/env python
"""
Script to get and display the logged-in user's close friends list.
Note: You can only retrieve your own close friends list, not other users'.
"""
import sys
import json
import argparse
import tabulate
from pathlib import Path
from typing import List, Dict, Any

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from core.auth import InstagramAuthenticator
from services.user_service import UserService

def display_friends_basic(friends: List[Dict[str, Any]]) -> None:
    """Display friends list in a simple formatted way."""
    if not friends:
        print("\nNo close friends found.")
        return
        
    print("\nYour Close Friends List:")
    print("-" * 50)
    
    for i, friend in enumerate(friends, 1):
        verified_badge = "✓" if friend.get('is_verified') else ""
        private_badge = "🔒" if friend.get('is_private') else ""
        
        print(f"{i}. @{friend['username']} {verified_badge} {private_badge}")
        print(f"   Name: {friend['full_name']}")
        print(f"   Profile: {friend['profile_pic_url']}")
        print("-" * 50)

def display_friends_table(friends: List[Dict[str, Any]]) -> None:
    """Display friends list in a table format."""
    if not friends:
        print("\nNo close friends found.")
        return
    
    # Prepare table data
    table_data = []
    headers = ["#", "Username", "Name", "Private", "Verified"]
    
    for i, friend in enumerate(friends, 1):
        verified = "Yes" if friend.get('is_verified') else "No"
        private = "Yes" if friend.get('is_private') else "No"
        
        table_data.append([
            i,
            f"@{friend['username']}",
            friend['full_name'],
            private,
            verified
        ])
    
    # Display table
    print(f"\nFound {len(friends)} close friends:")
    print(tabulate.tabulate(table_data, headers=headers, tablefmt="grid"))

def output_json(friends: List[Dict[str, Any]], output_file: str) -> None:
    """Output friends list to a JSON file."""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(friends, f, indent=2, default=str)
    
    print(f"\nSaved close friends data to: {output_path}")

def output_csv(friends: List[Dict[str, Any]], output_file: str) -> None:
    """Output friends list to a CSV file."""
    import csv
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Define fields to export
    fields = ['username', 'full_name', 'user_id', 'profile_pic_url', 'is_private', 'is_verified']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for friend in friends:
            row = {field: friend.get(field, '') for field in fields}
            writer.writerow(row)
    
    print(f"\nSaved close friends data to: {output_path}")

def main():
    """Main entry point for getting close friends list."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Get your Instagram close friends list. Note: This only works for your own account."
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: none)",
        default=None
    )
    parser.add_argument(
        "-f", "--format",
        help="Output format (json, csv, table, basic)",
        choices=["json", "csv", "table", "basic"],
        default="table"
    )
    parser.add_argument(
        "--min-delay",
        help="Minimum delay between requests in seconds",
        type=int,
        default=3
    )
    parser.add_argument(
        "--max-delay",
        help="Maximum delay between requests in seconds",
        type=int,
        default=10
    )
    
    args = parser.parse_args()
    
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
        print(f"\nGetting close friends list for your account (@{username})...")
        
        # Initialize user service with delay settings
        user_service = UserService(
            client=auth.client,
            min_delay=args.min_delay,
            max_delay=args.max_delay
        )
        
        # Get close friends list for the logged in user
        friends = user_service.get_close_friends(username)
        
        # Handle output format
        if args.format == "basic":
            display_friends_basic(friends)
        elif args.format == "table":
            display_friends_table(friends)
        
        # Handle file output if requested
        if args.output:
            if args.format == "json" or args.output.endswith('.json'):
                output_json(friends, args.output)
            elif args.format == "csv" or args.output.endswith('.csv'):
                output_csv(friends, args.output)
            else:
                # Default to JSON if format not specified in filename
                output_json(friends, args.output)
        
        # Print summary
        print(f"\nFound {len(friends)} close friends for your account (@{username})")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 