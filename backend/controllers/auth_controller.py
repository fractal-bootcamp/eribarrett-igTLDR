import jwt
from datetime import datetime, timedelta
from models import User, InstagramAccount
from config import get_config
import logging

logger = logging.getLogger(__name__)
config = get_config()

class AuthController:
    """Handles user authentication and authorization."""
    
    @staticmethod
    def register(username):
        """Register a new user."""
        try:
            # Check if user exists
            existing_user = User.find_by_username(username)
            if existing_user:
                return {
                    'success': False,
                    'error': 'Username already exists'
                }
            
            # Create new user
            user = User(username=username)
            user.save()
            
            return {
                'success': True,
                'user': user.to_dict()
            }
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def login(username):
        """Login a user."""
        try:
            user = User.find_by_username(username)
            if not user:
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            token = user.generate_token()
            return {
                'success': True,
                'token': token,
                'user': user.to_dict()
            }
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def logout(token):
        """Logout a user."""
        try:
            user_id = User.verify_token(token)
            if not user_id:
                return {
                    'success': False,
                    'error': 'Invalid token'
                }
            return {'success': True}
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_current_user(token):
        """Get the current user from a token."""
        try:
            user_id = User.verify_token(token)
            if not user_id:
                return {
                    'success': False,
                    'error': 'Invalid token'
                }
            
            user = User.find_by_id(user_id)
            if not user:
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            return {
                'success': True,
                'user': user.to_dict()
            }
        except Exception as e:
            logger.error(f"Get current user error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def instagram_login(username, user_ip):
        """Login to Instagram and get session cookies."""
        try:
            # Create or get user
            user = User.find_by_username(username)
            if not user:
                user = User(username=username)
                user.save()
            
            # Create Instagram account
            account = InstagramAccount(
                username=username,
                user_id=user.user_id,
                user_ip=user_ip
            )
            account.save()
            
            return {
                'success': True,
                'account': account.to_dict()
            }
        except Exception as e:
            logger.error(f"Instagram login error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def validate_token(token: str) -> str:
        """Validate JWT token and return user ID."""
        try:
            payload = jwt.decode(token, config.SECRET_KEY, algorithms=['HS256'])
            return payload.get('user_id')
        except Exception as e:
            logger.error(f"Token validation failed: {str(e)}")
            return None 