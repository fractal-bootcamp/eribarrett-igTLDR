#!/usr/bin/env python
"""
Test script for adding and authenticating Instagram credentials.
"""
import requests
import json
import getpass
import sys
import os

BASE_URL = "http://localhost:5000/api"

def register_user():
    """Register a new user account."""
    print("\n=== Register New User ===")
    email = input("Email: ")
    password = getpass.getpass("Password: ")
    name = input("Name: ")
    
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": email,
            "password": password,
            "name": name
        }
    )
    
    data = response.json()
    if response.status_code == 201 and data.get("success"):
        print("User registered successfully!")
        return data.get("token")
    else:
        print(f"Registration failed: {data.get('error', 'Unknown error')}")
        return None

def login_user():
    """Login with existing user credentials."""
    print("\n=== Login ===")
    email = input("Email: ")
    password = getpass.getpass("Password: ")
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": email,
            "password": password
        }
    )
    
    data = response.json()
    if response.status_code == 200 and data.get("success"):
        print("Login successful!")
        return data.get("token")
    else:
        print(f"Login failed: {data.get('error', 'Unknown error')}")
        return None

def add_instagram_account(token):
    """Add an Instagram account with user credentials."""
    if not token:
        print("No authentication token provided.")
        return
    
    print("\n=== Add Instagram Account ===")
    username = input("Instagram Username: ")
    password = getpass.getpass("Instagram Password: ")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{BASE_URL}/instagram/accounts",
        headers=headers,
        json={
            "username": username,
            "password": password,
            "via_browser": False
        }
    )
    
    data = response.json()
    if response.status_code == 201 and data.get("success"):
        print("Instagram account added successfully!")
        return data.get("account_id")
    else:
        print(f"Adding Instagram account failed: {data.get('error', 'Unknown error')}")
        return None

def add_instagram_account_with_cookies(token):
    """Add an Instagram account using cookies from a web session."""
    if not token:
        print("No authentication token provided.")
        return
    
    print("\n=== Add Instagram Account Using Cookies ===")
    print("Instructions:")
    print("1. Login to Instagram in your browser")
    print("2. Get the following cookies from your browser:")
    
    username = input("Instagram Username: ")
    sessionid = input("sessionid cookie: ")
    csrftoken = input("csrftoken cookie: ")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{BASE_URL}/instagram/accounts",
        headers=headers,
        json={
            "username": username,
            "cookies": {
                "sessionid": sessionid,
                "csrftoken": csrftoken
            },
            "via_browser": True
        }
    )
    
    data = response.json()
    if response.status_code == 201 and data.get("success"):
        print("Instagram account added successfully!")
        return data.get("account_id")
    else:
        print(f"Adding Instagram account failed: {data.get('error', 'Unknown error')}")
        return None

def list_accounts(token):
    """List all Instagram accounts for the user."""
    if not token:
        print("No authentication token provided.")
        return
    
    print("\n=== Instagram Accounts ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(
        f"{BASE_URL}/instagram/accounts",
        headers=headers
    )
    
    data = response.json()
    if response.status_code == 200 and data.get("success"):
        accounts = data.get("accounts", [])
        if accounts:
            for acc in accounts:
                print(f"ID: {acc['account_id']}")
                print(f"Username: {acc['username']}")
                print(f"Active: {acc['active']}")
                print(f"Last check: {acc.get('last_check', 'Never')}")
                print("-" * 30)
        else:
            print("No accounts found.")
    else:
        print(f"Failed to list accounts: {data.get('error', 'Unknown error')}")

def main():
    """Main function to run the test script."""
    print("===== Instagram Monitoring Test Script =====")
    print("1. Register new user")
    print("2. Login with existing user")
    print("3. Exit")
    
    choice = input("\nSelect option: ")
    
    token = None
    if choice == "1":
        token = register_user()
    elif choice == "2":
        token = login_user()
    else:
        print("Exiting...")
        sys.exit(0)
    
    if not token:
        print("Authentication failed. Exiting...")
        sys.exit(1)
    
    while True:
        print("\n===== Instagram Account Options =====")
        print("1. Add Instagram account (with username/password)")
        print("2. Add Instagram account (with cookies)")
        print("3. List all Instagram accounts")
        print("4. Exit")
        
        choice = input("\nSelect option: ")
        
        if choice == "1":
            add_instagram_account(token)
        elif choice == "2":
            add_instagram_account_with_cookies(token)
        elif choice == "3":
            list_accounts(token)
        else:
            print("Exiting...")
            break

if __name__ == "__main__":
    main()
