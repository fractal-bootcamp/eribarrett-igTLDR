import hashlib
import secrets
import logging
from models import User
from controllers.instagram_client import InstagramClient
from models import InstagramAccount

logger = logging.getLogger(__name__)

class AuthController:
    """Authentication controller for user management."""
    
    @staticmethod
    def hash_password(password, salt=None):
        """Hash a password with a salt."""
        if not salt:
            salt = secrets.token_hex(16)
            
        # Combine password and salt, then hash
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}${password_hash}"
    
    @staticmethod
    def verify_password(password, password_hash):
        """Verify a password against a hash."""
        if not password_hash or '$' not in password_hash:
            return False
            
        salt, hash_value = password_hash.split('$', 1)
        return hashlib.sha256((password + salt).encode()).hexdigest() == hash_value
    
    @staticmethod
    def register(username, email, password):
        """Register a new user."""
        try:
            # Check if username or email already exists
            if User.find_by_username(username):
                return {
                    'success': False,
                    'error': 'Username already exists'
                }
                
            if User.find_by_email(email):
                return {
                    'success': False,
                    'error': 'Email already exists'
                }
                
            # Hash password
            password_hash = AuthController.hash_password(password)
            
            # Create user
            user = User(username=username, email=email, password_hash=password_hash)
            user.save()
            
            return {
                'success': True,
                'user_id': user.user_id,
                'token': user.generate_token()
            }
            
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return {
                'success': False,
                'error': 'Registration failed'
            }
    
    @staticmethod
    def login(username, password):
        """Login a user with username and password."""
        try:
            # Find user
            user = User.find_by_username(username)
            if not user:
                return {
                    'success': False,
                    'error': 'Invalid username or password'
                }
                
            # Verify password
            if not AuthController.verify_password(password, user.password_hash):
                return {
                    'success': False,
                    'error': 'Invalid username or password'
                }
                
            # Generate token
            token = user.generate_token()
            
            return {
                'success': True,
                'user_id': user.user_id,
                'token': token
            }
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return {
                'success': False,
                'error': 'Login failed'
            }
    
    @staticmethod
    def instagram_login(username, password, user_id):
        """Login to Instagram and store session cookies."""
        try:
            # Check if user exists
            user = User.find_by_id(user_id)
            if not user:
                return {
                    'success': False,
                    'error': 'User not found'
                }
                
            # Login to Instagram
            client = InstagramClient()
            result = client.login_by_username_password(username, password)
            
            if not result.get('success'):
                return {
                    'success': False,
                    'error': result.get('error', 'Instagram login failed')
                }
                
            # Get cookies from result
            cookies = result.get('cookies')
            
            # Store encrypted cookies
            existing_account = InstagramAccount.find_by_username(username, user_id)
            
            if existing_account:
                # Update existing account
                existing_account.update_cookies(cookies)
                account_id = existing_account.account_id
            else:
                # Create new account
                account = InstagramAccount(
                    user_id=user_id,
                    username=username,
                    encrypted_cookies=None  # Will be set by update_cookies
                )
                account.update_cookies(cookies)
                account_id = account.account_id
                
            return {
                'success': True,
                'account_id': account_id
            }
            
        except Exception as e:
            logger.error(f"Instagram login error: {str(e)}")
            return {
                'success': False,
                'error': 'Instagram login failed'
            } 