import json
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import logging

from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired,
    TwoFactorRequired,
    ClientError,
    ClientLoginRequired,
    ClientConnectionError,
    ClientThrottledError
)

from .exceptions import (
    InstagramAuthError,
    LoginError,
    TwoFactorRequiredError,
    SessionError,
    InvalidCredentialsError
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('instagram-auth')

class InstagramAuthenticator:
    def __init__(self, session_file: str = "session.json", backup_dir: str = "session_backups"):
        self.client = Client()
        self.session_file = session_file
        self.backup_dir = backup_dir
        self._ensure_session_dir()

    def _ensure_session_dir(self) -> None:
        """Ensure the directory for session file exists."""
        session_path = Path(self.session_file)
        session_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Also create backup directory
        backup_path = Path(self.backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)

    def _save_session(self) -> None:
        """Save session data to file and create a backup."""
        try:
            # Save main session
            self.client.dump_settings(self.session_file)
            logger.info(f"Session saved to {self.session_file}")
            
            # Create timestamped backup
            timestamp = int(time.time())
            backup_file = os.path.join(self.backup_dir, f"session_{timestamp}.json")
            self.client.dump_settings(backup_file)
            logger.info(f"Session backup created at {backup_file}")
            
            # Add timestamp to the session data for age tracking
            session_data = self.client.get_settings()
            session_data["created_ts"] = timestamp
            
            with open(self.session_file, "w") as f:
                json.dump(session_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save session: {str(e)}")
            raise SessionError(f"Failed to save session: {str(e)}")

    def _load_session(self) -> Optional[Dict[str, Any]]:
        """Load session data from file if it exists."""
        if not os.path.exists(self.session_file):
            logger.warning(f"Session file not found: {self.session_file}")
            return self._try_recover_from_backup()
            
        try:
            # Load the session file
            with open(self.session_file, "r") as f:
                session_data = json.load(f)
            
            # Check session age
            current_time = time.time()
            session_age = 0
            if "created_ts" in session_data:
                created_ts = session_data.get("created_ts", current_time)
                session_age = (current_time - created_ts) / 3600  # in hours
                
                if session_age > 24:
                    logger.warning(f"Session is {session_age:.1f} hours old (older than 24h)")
                else:
                    logger.info(f"Session age: {session_age:.1f} hours")
            
            logger.info(f"Loaded session from {self.session_file}")
            return self.client.load_settings(self.session_file)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in session file: {str(e)}")
            return self._try_recover_from_backup()
        except Exception as e:
            logger.error(f"Failed to load session: {str(e)}")
            return self._try_recover_from_backup()

    def _try_recover_from_backup(self) -> Optional[Dict[str, Any]]:
        """Try to recover session from the most recent backup."""
        try:
            backup_path = Path(self.backup_dir)
            if not backup_path.exists():
                logger.warning("No backup directory found")
                return None
                
            backup_files = list(backup_path.glob("session_*.json"))
            if not backup_files:
                logger.warning("No backup files found")
                return None
                
            # Sort by modification time, newest first
            latest_backup = max(backup_files, key=lambda p: p.stat().st_mtime)
            logger.info(f"Attempting to recover from backup: {latest_backup}")
            
            return self.client.load_settings(str(latest_backup))
        except Exception as e:
            logger.error(f"Failed to recover from backup: {str(e)}")
            return None

    def _handle_2fa(self) -> str:
        """Handle 2FA code input."""
        logger.info("Two-factor authentication required")
        print("\nTwo-factor authentication required.")
        code = input("Enter your 2FA code: ").strip()
        return code

    def get_current_username(self) -> Optional[str]:
        """Get the username of the currently logged-in user."""
        try:
            user_info = self.client.account_info()
            logger.info(f"Current user: {user_info.username}")
            return user_info.username
        except Exception as e:
            logger.error(f"Failed to get username: {str(e)}")
            return None

    def login_with_session(self) -> bool:
        """
        Attempt to login using only the saved session data.
        Returns True if successful, False otherwise.
        """
        try:
            session = self._load_session()
            if not session:
                logger.warning("No session data found")
                return False

            logger.info("Attempting to use saved session...")
            self.client.set_settings(session)
            
            # Try to access timeline to verify session
            try:
                # First, try a simple endpoint to verify session
                self.client.get_timeline_feed()  # Remove the amount parameter
                current_username = self.get_current_username()
                if current_username:
                    logger.info(f"Session validated, logged in as: {current_username}")
                    return True
                else:
                    logger.warning("Got timeline but couldn't get username")
                    return False
                    
            except (LoginRequired, ClientConnectionError) as e:
                # Session exists but is invalid, try to refresh it
                logger.warning(f"Session invalid: {str(e)}")
                logger.info("Attempting to refresh session...")
                
                try:
                    # Save the device IDs for continuity
                    old_session = self.client.get_settings()
                    device_uuids = {
                        "phone_id": old_session.get("phone_id", ""),
                        "uuid": old_session.get("uuid", ""),
                        "client_session_id": old_session.get("client_session_id", ""),
                        "advertising_id": old_session.get("advertising_id", ""),
                        "device_id": old_session.get("device_id", "")
                    }
                    
                    # Try session refresh without full relogin
                    # This uses existing cookies but refreshes auth tokens
                    self.client.login_flow(relogin=True)
                    
                    # Verify the refreshed session
                    self.client.get_timeline_feed()
                    current_username = self.get_current_username()
                    
                    if current_username:
                        logger.info(f"Session refreshed successfully, logged in as: {current_username}")
                        self._save_session()  # Save the refreshed session
                        return True
                    else:
                        logger.warning("Session refresh seemed to work but couldn't verify username")
                        return False
                        
                except Exception as e:
                    logger.error(f"Failed to refresh session: {str(e)}")
                    return False
                    
            except ClientThrottledError:
                logger.warning("Rate limited by Instagram. Session may be valid but we're throttled")
                # Session might be valid, but we're rate limited
                return True
                
            except ClientConnectionError:
                logger.error("Connection error while validating session")
                # Can't determine if session is valid due to connection issues
                return False
                
        except Exception as e:
            logger.error(f"Session login failed with unexpected error: {str(e)}")
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
                logger.info("Found existing session, attempting to use it...")
                try:
                    self.client.set_settings(session)
                    self.client.login(username, password, relogin=True)
                    
                    # Check if session is valid
                    try:
                        self.client.get_timeline_feed()
                        current_username = self.get_current_username()
                        if current_username:
                            logger.info(f"Session login successful as: {current_username}")
                            login_via_session = True
                            # Update the session timestamp
                            self._save_session()
                        else:
                            logger.warning("Got timeline but couldn't get username")
                    except (LoginRequired, ClientConnectionError):
                        logger.warning("Session is invalid, attempting new login...")
                        
                        # Preserve device identifiers across logins
                        old_session = self.client.get_settings()
                        device_settings = {k: v for k, v in old_session.items() 
                                          if k in ['phone_id', 'uuid', 'device_id', 'android_device_id']}
                        
                        # Reset client but keep device identifiers
                        self.client = Client()
                        self.client.set_settings(device_settings)
                        
                        # Perform a fresh login
                        self.client.login(username, password, relogin=False)
                        current_username = self.get_current_username()
                        if current_username:
                            logger.info(f"Fresh login successful as: {current_username}")
                            login_via_pw = True
                            self._save_session()
                except Exception as e:
                    logger.error(f"Failed to use saved session: {str(e)}")
        except Exception as e:
            logger.error(f"Error loading session: {str(e)}")

        # If session login failed, try username/password login
        if not (login_via_session or login_via_pw):
            try:
                logger.info("Attempting fresh login with username and password...")
                # Clear any existing settings but keep device info if possible
                old_settings = {}
                try:
                    old_settings = self.client.get_settings()
                except:
                    pass
                
                # Create a new client instance
                self.client = Client()
                
                # Transfer any device identifiers
                if old_settings:
                    device_settings = {k: v for k, v in old_settings.items() 
                                      if k in ['phone_id', 'uuid', 'device_id', 'android_device_id']}
                    if device_settings:
                        logger.info("Preserving device identifiers")
                        self.client.set_settings(device_settings)
                
                # Perform the login
                self.client.login(username, password)
                current_username = self.get_current_username()
                if current_username:
                    logger.info(f"Fresh login successful as: {current_username}")
                    login_via_pw = True
                    # Save the new session
                    self._save_session()
                else:
                    logger.warning("Login seemed to work but couldn't verify username")
            except TwoFactorRequired:
                try:
                    logger.info("2FA required, prompting for code")
                    code = self._handle_2fa()
                    self.client.login(username, password, verification_code=code)
                    current_username = self.get_current_username()
                    if current_username:
                        logger.info(f"2FA login successful as: {current_username}")
                        login_via_pw = True
                        # Save the new session after 2FA
                        self._save_session()
                    else:
                        logger.warning("2FA login seemed to work but couldn't verify username")
                except Exception as e:
                    logger.error(f"2FA verification failed: {str(e)}")
                    raise TwoFactorRequiredError(f"2FA verification failed: {str(e)}")
            except ClientLoginRequired:
                logger.error("Login failed - invalid credentials")
                raise InvalidCredentialsError("Invalid username or password")
            except Exception as e:
                logger.error(f"Login failed with unexpected error: {str(e)}")
                raise InstagramAuthError(f"Login failed: {str(e)}")

        return login_via_session or login_via_pw

    def is_logged_in(self) -> bool:
        """Check if the client is currently logged in."""
        try:
            self.client.get_timeline_feed()
            return True
        except LoginRequired:
            return False
        except Exception as e:
            logger.warning(f"Error checking login status: {str(e)}")
            return False

    def logout(self) -> None:
        """Logout from Instagram and clear session data."""
        try:
            self.client.logout()
            # Don't delete the session file, just backup it
            if os.path.exists(self.session_file):
                timestamp = int(time.time())
                backup_file = os.path.join(self.backup_dir, f"session_logout_{timestamp}.json")
                os.rename(self.session_file, backup_file)
                logger.info(f"Session file backed up to {backup_file}")
            logger.info("Successfully logged out")
        except Exception as e:
            logger.error(f"Error during logout: {str(e)}")
            raise InstagramAuthError(f"Error during logout: {str(e)}")
            
    def switch_to_alternative_client(self) -> None:
        """
        Switch to an alternative client implementation that might use different API endpoints.
        This can be helpful when specific API endpoints are down or changed.
        """
        try:
            # Save current settings to transfer to new client
            old_settings = self.client.get_settings()
            
            # Initialize a new client that might use different API endpoints
            # Note: This is a placeholder for any alternative client implementation
            # You might need to implement an AlternativeClient class or modify instagrapi
            from instagrapi import Client as StandardClient
            
            # Try with different User-Agent or API version
            new_client = StandardClient()
            new_client.set_settings(old_settings)
            
            # Use a different User-Agent to simulate a different client version
            new_client.user_agent = "Instagram 219.0.0.12.117 Android (30/11; 480dpi; 1080x2158; OnePlus; GM1917; OnePlus7Pro; qcom; en_US; 346138317)"
            
            # Test the new client
            new_client.get_timeline_feed()
            
            # If successful, replace the client
            self.client = new_client
            logger.info("Successfully switched to alternative client")
            
            # Save this configuration
            self._save_session()
            return True
        except Exception as e:
            logger.error(f"Failed to switch to alternative client: {str(e)}")
            return False
