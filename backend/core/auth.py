import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired,
    TwoFactorRequired,
    ClientError,
    ClientLoginRequired
)

from .exceptions import (
    InstagramAuthError,
    LoginError,
    TwoFactorRequiredError,
    SessionError,
    InvalidCredentialsError
)

class InstagramAuthenticator:
    def __init__(self, session_file: str = "session.json"):
        self.client = Client()
        self.session_file = session_file
        self._ensure_session_dir()

    def _ensure_session_dir(self) -> None:
        """Ensure the directory for session file exists."""
        session_path = Path(self.session_file)
        session_path.parent.mkdir(parents=True, exist_ok=True)

    def _save_session(self) -> None:
        """Save session data to file."""
        try:
            self.client.dump_settings(self.session_file)
            print("Session saved successfully!")
        except Exception as e:
            raise SessionError(f"Failed to save session: {str(e)}")

    def _load_session(self) -> Optional[Dict[str, Any]]:
        """Load session data from file if it exists."""
        if not os.path.exists(self.session_file):
            return None
        try:
            return self.client.load_settings(self.session_file)
        except Exception as e:
            raise SessionError(f"Failed to load session: {str(e)}")

    def _handle_2fa(self) -> str:
        """Handle 2FA code input."""
        print("\nTwo-factor authentication required.")
        code = input("Enter your 2FA code: ").strip()
        return code

    def get_current_username(self) -> Optional[str]:
        """Get the username of the currently logged-in user."""
        try:
            return self.client.account_info().username
        except Exception:
            return None

    def login_with_session(self) -> bool:
        """
        Attempt to login using only the saved session data.
        Returns True if successful, False otherwise.
        """
        try:
            session = self._load_session()
            if not session:
                return False

            print("Attempting to use saved session...")
            self.client.set_settings(session)
            
            # Try to access timeline to verify session
            try:
                self.client.get_timeline_feed()
                current_username = self.get_current_username()
                if current_username:
                    print(f"Success! Logged in as: {current_username}")
                else:
                    print("Success! Logged in using saved session!")
                return True
            except LoginRequired:
                # Session exists but is invalid, try to refresh it
                print("Session needs refresh, attempting to refresh...")
                try:
                    # Use the same device uuids across logins
                    old_session = self.client.get_settings()
                    self.client.set_settings({})
                    self.client.set_uuids(old_session["uuids"])
                    
                    # Try to refresh the session
                    self.client.get_timeline_feed()
                    current_username = self.get_current_username()
                    if current_username:
                        print(f"Success! Refreshed session for: {current_username}")
                    else:
                        print("Success! Refreshed session!")
                    return True
                except Exception as e:
                    print(f"Failed to refresh session: {str(e)}")
                    return False
                    
        except Exception as e:
            print(f"Session login failed: {str(e)}")
            return False

    def login(self, username: str, password: str) -> bool:
        """
        Attempt to login to Instagram with the provided credentials.
        First tries to use existing session, then falls back to username/password login.
        """
        login_via_session = False
        login_via_pw = False

        # Try to load existing session
        try:
            session = self._load_session()
            if session:
                print("\nFound existing session. Attempting to use it...")
                try:
                    self.client.set_settings(session)
                    self.client.login(username, password)
                    
                    # Check if session is valid
                    try:
                        self.client.get_timeline_feed()
                        current_username = self.get_current_username()
                        if current_username:
                            print(f"Success! Logged in as: {current_username}")
                        else:
                            print("Success! Logged in using saved session!")
                        login_via_session = True
                    except LoginRequired:
                        print("Session is invalid, attempting new login...")
                        
                        # Use the same device uuids across logins
                        old_session = self.client.get_settings()
                        self.client.set_settings({})
                        self.client.set_uuids(old_session["uuids"])
                        
                        self.client.login(username, password)
                        current_username = self.get_current_username()
                        if current_username:
                            print(f"Success! Logged in as: {current_username}")
                        else:
                            print("Success! Logged in using saved session!")
                        login_via_session = True
                except Exception as e:
                    print(f"Failed to use saved session: {str(e)}")
        except Exception as e:
            print(f"Error loading session: {str(e)}")

        # If session login failed, try username/password login
        if not login_via_session:
            try:
                print("\nAttempting login with username and password...")
                self.client.login(username, password)
                current_username = self.get_current_username()
                if current_username:
                    print(f"Success! Logged in as: {current_username}")
                else:
                    print("Success! Logged in!")
                login_via_pw = True
                
                # Save the new session
                self._save_session()
            except TwoFactorRequired:
                try:
                    code = self._handle_2fa()
                    self.client.login(username, password, verification_code=code)
                    current_username = self.get_current_username()
                    if current_username:
                        print(f"Success! Logged in as: {current_username}")
                    else:
                        print("Success! Logged in with 2FA!")
                    login_via_pw = True
                    
                    # Save the new session after 2FA
                    self._save_session()
                except Exception as e:
                    raise TwoFactorRequiredError(f"2FA verification failed: {str(e)}")
            except ClientLoginRequired:
                raise InvalidCredentialsError("Invalid username or password")
            except Exception as e:
                raise InstagramAuthError(f"Login failed: {str(e)}")

        return login_via_session or login_via_pw

    def is_logged_in(self) -> bool:
        """Check if the client is currently logged in."""
        try:
            self.client.get_timeline_feed()
            return True
        except LoginRequired:
            return False
        except Exception:
            return False

    def logout(self) -> None:
        """Logout from Instagram and clear session data."""
        try:
            self.client.logout()
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
            print("Successfully logged out!")
        except Exception as e:
            raise InstagramAuthError(f"Error during logout: {str(e)}")
