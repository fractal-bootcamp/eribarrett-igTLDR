import time
import json
import logging
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ClientError, ClientLoginRequired
from typing import Dict, List, Optional, Union
import requests
import socket
import subprocess

logger = logging.getLogger(__name__)

class InstagramCrawler:
    """
    Instagram crawler that uses existing session cookies and routes requests
    through the user's real IP address in a containerized environment.
    """
    
    def __init__(self, session_cookies: Dict = None, user_ip: str = None):
        """
        Initialize the Instagram crawler with session cookies.
        
        Args:
            session_cookies (Dict): Dictionary containing session cookies from Instagram
            user_ip (str): User's real IP address to route requests through
        """
        self.logger = self._setup_logger()
        self.client = Client()
        
        # Set user's IP if provided
        if user_ip:
            self.set_user_ip(user_ip)
            
        # Set session cookies if provided
        if session_cookies:
            self.set_session_cookies(session_cookies)
    
    def _setup_logger(self):
        """Set up logging for the crawler"""
        logger = logging.getLogger("instagram_crawler")
        logger.setLevel(logging.INFO)
        
        # Create console handler
        c_handler = logging.StreamHandler()
        c_handler.setLevel(logging.INFO)
        
        # Create formatter and add to handler
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        c_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(c_handler)
        
        return logger
    
    def set_user_ip(self, user_ip: str) -> bool:
        """
        Set the user's real IP address for routing requests in a container.
        
        Args:
            user_ip (str): User's real IP address
            
        Returns:
            bool: True if IP was set successfully, False otherwise
        """
        try:
            # Configure network namespace for the container
            self._setup_network_namespace(user_ip)
            
            # Test the connection
            self.logger.info(f"Testing connection with user IP {user_ip}...")
            response = requests.get("https://api.ipify.org")
            if response.status_code == 200:
                self.logger.info(f"Successfully set user IP: {response.text}")
                return True
            else:
                self.logger.error(f"Failed to verify user IP: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to set user IP: {e}")
            return False
    
    def _setup_network_namespace(self, user_ip: str):
        """
        Set up network namespace for the container to use the user's IP.
        
        Args:
            user_ip (str): User's real IP address
        """
        try:
            # Create a new network namespace
            namespace = f"ns_{user_ip.replace('.', '_')}"
            subprocess.run(["ip", "netns", "add", namespace], check=True)
            
            # Create a virtual interface
            veth_name = f"veth_{namespace}"
            subprocess.run(["ip", "link", "add", veth_name, "type", "veth", "peer", "name", f"{veth_name}_peer"], check=True)
            
            # Move the peer interface to the namespace
            subprocess.run(["ip", "link", "set", f"{veth_name}_peer", "netns", namespace], check=True)
            
            # Configure IP address in the namespace
            subprocess.run(["ip", "netns", "exec", namespace, "ip", "addr", "add", f"{user_ip}/32", "dev", f"{veth_name}_peer"], check=True)
            subprocess.run(["ip", "netns", "exec", namespace, "ip", "link", "set", f"{veth_name}_peer", "up"], check=True)
            
            # Configure the main interface
            subprocess.run(["ip", "link", "set", veth_name, "up"], check=True)
            
            # Set up routing in the namespace
            subprocess.run(["ip", "netns", "exec", namespace, "ip", "route", "add", "default", "via", "127.0.0.1"], check=True)
            
            # Store namespace for cleanup
            self.namespace = namespace
            self.veth_name = veth_name
            
        except Exception as e:
            self.logger.error(f"Failed to setup network namespace: {e}")
            self._cleanup_network_namespace()
            raise
    
    def _cleanup_network_namespace(self):
        """Clean up network namespace and interfaces."""
        try:
            if hasattr(self, 'namespace'):
                # Delete the namespace and its interfaces
                subprocess.run(["ip", "netns", "delete", self.namespace], check=True)
                subprocess.run(["ip", "link", "delete", self.veth_name], check=True)
        except Exception as e:
            self.logger.error(f"Failed to cleanup network namespace: {e}")
    
    def __del__(self):
        """Cleanup when the crawler is destroyed."""
        self._cleanup_network_namespace()
    
    def set_session_cookies(self, cookies: Dict) -> bool:
        """
        Set session cookies for authentication.
        
        Args:
            cookies (Dict): Dictionary containing Instagram session cookies
            
        Returns:
            bool: True if login was successful, False otherwise
        """
        try:
            self.logger.info("Attempting to login using session cookies")
            self.client.cookie_dict = cookies
            
            # Test if the session is valid
            try:
                self.client.get_timeline_feed()
                user_id = self.client.user_id
                username = self.client.username
                self.logger.info(f"Successfully logged in as {username} (ID: {user_id}) using session cookies")
                return True
            except (LoginRequired, ClientLoginRequired) as e:
                self.logger.error(f"Session cookies are invalid or expired: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to set session cookies: {e}")
            return False
    
    def get_latest_posts(self, username: str, since_time: Optional[str] = None) -> Dict:
        """
        Get latest posts from a user since a specific time.
        
        Args:
            username (str): Instagram username to fetch posts from
            since_time (str, optional): ISO format timestamp to fetch posts since
            
        Returns:
            Dict: Dictionary containing success status and posts data
        """
        try:
            user_id = self.client.user_id_from_username(username)
            medias = self.client.user_medias(user_id, 20)  # Get last 20 posts
            
            if since_time:
                if isinstance(since_time, str):
                    since_time = datetime.fromisoformat(since_time)
                medias = [media for media in medias if media.taken_at > since_time]
            
            result = []
            for media in medias:
                post = {
                    'id': media.id,
                    'code': media.code,
                    'taken_at': media.taken_at.isoformat(),
                    'media_type': media.media_type,
                    'product_type': media.product_type if hasattr(media, 'product_type') else None,
                    'thumbnail_url': media.thumbnail_url,
                    'caption_text': media.caption_text if media.caption_text else '',
                    'like_count': media.like_count,
                    'comment_count': media.comment_count,
                    'url': f"https://www.instagram.com/p/{media.code}/",
                }
                result.append(post)
            
            return {
                'success': True,
                'posts': result
            }
        except Exception as e:
            self.logger.error(f"Get latest posts failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user_info(self, username: str) -> Dict:
        """
        Get user information by username.
        
        Args:
            username (str): Instagram username to fetch info for
            
        Returns:
            Dict: Dictionary containing success status and user data
        """
        try:
            user = self.client.user_info_by_username(username)
            return {
                'success': True,
                'user': {
                    'pk': user.pk,
                    'username': user.username,
                    'full_name': user.full_name,
                    'is_private': user.is_private,
                    'profile_pic_url': user.profile_pic_url,
                    'media_count': user.media_count,
                    'follower_count': user.follower_count,
                    'following_count': user.following_count
                }
            }
        except Exception as e:
            self.logger.error(f"Get user info failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_session(self) -> bool:
        """
        Check if the current session is valid.
        
        Returns:
            bool: True if session is valid, False otherwise
        """
        try:
            self.client.get_timeline_feed()
            return True
        except (LoginRequired, ClientError):
            return False
        except Exception as e:
            self.logger.error(f"Session validation error: {str(e)}")
            return False 