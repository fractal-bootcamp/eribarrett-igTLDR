#!/usr/bin/env python
import os
import sys
import argparse
import getpass
import json
from controllers import AuthController
from models import User, InstagramAccount

def register(args):
    """Register a new user."""
    username = args.username or input("Username: ")
    email = args.email or input("Email: ")
    password = args.password or getpass.getpass("Password: ")
    
    result = AuthController.register(username, email, password)
    
    if result.get('success'):
        print(f"User {username} registered successfully.")
        print(f"User ID: {result['user_id']}")
        print(f"Token: {result['token']}")
    else:
        print(f"Error: {result.get('error', 'Registration failed')}")

def login(args):
    """Login a user."""
    username = args.username or input("Username: ")
    password = args.password or getpass.getpass("Password: ")
    
    result = AuthController.login(username, password)
    
    if result.get('success'):
        print(f"User {username} logged in successfully.")
        print(f"User ID: {result['user_id']}")
        print(f"Token: {result['token']}")
    else:
        print(f"Error: {result.get('error', 'Login failed')}")

def add_instagram(args):
    """Add an Instagram account."""
    user_id = args.user_id or input("User ID: ")
    username = args.username or input("Instagram Username: ")
    password = args.password or getpass.getpass("Instagram Password: ")
    
    result = AuthController.instagram_login(username, password, user_id)
    
    if result.get('success'):
        print(f"Instagram account {username} added successfully.")
        print(f"Account ID: {result['account_id']}")
    else:
        print(f"Error: {result.get('error', 'Instagram login failed')}")

def list_accounts(args):
    """List all Instagram accounts for a user."""
    user_id = args.user_id or input("User ID: ")
    
    # Find user
    user = User.find_by_id(user_id)
    if not user:
        print(f"Error: User {user_id} not found")
        return
    
    # Find accounts
    accounts = InstagramAccount.find_by_user(user_id)
    
    if not accounts:
        print(f"No Instagram accounts found for user {user.username}")
        return
    
    print(f"Instagram accounts for user {user.username}:")
    for i, account in enumerate(accounts, 1):
        last_check = account.last_check or "Never"
        print(f"{i}. @{account.username} (ID: {account.account_id})")
        print(f"   Last checked: {last_check}")
        print(f"   Active: {'Yes' if account.active else 'No'}")
        print()

def delete_account(args):
    """Delete an Instagram account."""
    account_id = args.account_id or input("Account ID: ")
    
    # Find account
    account = InstagramAccount.find_by_id(account_id)
    if not account:
        print(f"Error: Account {account_id} not found")
        return
    
    # Delete account
    account.delete()
    
    print(f"Instagram account @{account.username} deleted successfully.")

def main():
    parser = argparse.ArgumentParser(description='Instagram monitoring system CLI')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Register command
    register_parser = subparsers.add_parser('register', help='Register a new user')
    register_parser.add_argument('--username', help='Username')
    register_parser.add_argument('--email', help='Email')
    register_parser.add_argument('--password', help='Password')
    
    # Login command
    login_parser = subparsers.add_parser('login', help='Login a user')
    login_parser.add_argument('--username', help='Username')
    login_parser.add_argument('--password', help='Password')
    
    # Add Instagram account command
    add_instagram_parser = subparsers.add_parser('add-instagram', help='Add an Instagram account')
    add_instagram_parser.add_argument('--user-id', help='User ID')
    add_instagram_parser.add_argument('--username', help='Instagram Username')
    add_instagram_parser.add_argument('--password', help='Instagram Password')
    
    # List accounts command
    list_accounts_parser = subparsers.add_parser('list-accounts', help='List all Instagram accounts for a user')
    list_accounts_parser.add_argument('--user-id', help='User ID')
    
    # Delete account command
    delete_account_parser = subparsers.add_parser('delete-account', help='Delete an Instagram account')
    delete_account_parser.add_argument('--account-id', help='Account ID')
    
    args = parser.parse_args()
    
    if args.command == 'register':
        register(args)
    elif args.command == 'login':
        login(args)
    elif args.command == 'add-instagram':
        add_instagram(args)
    elif args.command == 'list-accounts':
        list_accounts(args)
    elif args.command == 'delete-account':
        delete_account(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 