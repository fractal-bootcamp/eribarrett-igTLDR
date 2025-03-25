from flask import request, jsonify, Blueprint
import jwt
from functools import wraps
from config import get_config
from models import User, InstagramAccount, NotificationSettings
from controllers import AuthController, instagram_monitor
from controllers.instagram_crawler import InstagramCrawler
from controllers.instagram_monitor import InstagramMonitor
import logging

logger = logging.getLogger(__name__)
api = Blueprint('api', __name__)
config = get_config()

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check if token is in headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split('Bearer ')[1]
        
        if not token:
            return jsonify({'success': False, 'error': 'Token is missing'}), 401
        
        try:
            # Verify token
            user_id = User.verify_token(token)
            if not user_id:
                return jsonify({'success': False, 'error': 'Invalid token'}), 401
                
            # Get user
            current_user = User.find_by_id(user_id)
            if not current_user:
                return jsonify({'success': False, 'error': 'User not found'}), 401
                
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 401
            
        return f(current_user, *args, **kwargs)
    
    return decorated

def require_auth(f):
    """Decorator to require authentication for routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401
        
        try:
            user_id = AuthController.validate_token(auth_header)
            if not user_id:
                return jsonify({'error': 'Invalid token'}), 401
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Auth error: {str(e)}")
            return jsonify({'error': 'Authentication failed'}), 401
    return decorated

# Auth routes
@api.route('/auth/register', methods=['POST'])
def register():
    """Register a new user."""
    return AuthController.register()

@api.route('/auth/login', methods=['POST'])
def login():
    """Login user."""
    return AuthController.login()

@api.route('/auth/logout', methods=['POST'])
def logout():
    """Logout user."""
    return AuthController.logout()

@api.route('/auth/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current user information."""
    user = AuthController.get_current_user()
    return jsonify({
        'id': user.user_id,
        'username': user.username,
        'email': user.email
    })

@api.route('/auth/instagram', methods=['POST'])
def instagram_login():
    """Login with Instagram credentials and get session cookies."""
    try:
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Missing username or password'}), 400
        
        username = data['username']
        password = data['password']
        
        # Create Instagram client and login
        client = AuthController.instagram_login(username, password)
        if not client:
            return jsonify({'error': 'Failed to login to Instagram'}), 401
        
        # Get session cookies
        cookies = client.cookie_dict
        
        # Create or update user
        user = User.find_by_username(username)
        if not user:
            user = User.create(username=username)
        
        # Create or update Instagram account
        account = InstagramAccount.find_by_username(username)
        if not account:
            account = InstagramAccount.create(
                username=username,
                user_id=user.user_id,
                session_cookies=cookies
            )
        else:
            account.update_session_cookies(cookies)
        
        return jsonify({
            'success': True,
            'user': {
                'user_id': user.user_id,
                'username': user.username
            }
        })
        
    except Exception as e:
        logger.error(f"Instagram login error: {str(e)}")
        return jsonify({'error': str(e)}), 500

def get_user():
    """Get or create the single user instance."""
    return User.get_or_create()

# Account routes
@api.route('/accounts', methods=['GET'])
@require_auth
def get_accounts():
    """Get all Instagram accounts for the current user."""
    try:
        accounts = InstagramAccount.find_by_user(current_user.user_id)
        return jsonify({
            'success': True,
            'accounts': [account.to_dict() for account in accounts]
        })
    except Exception as e:
        logger.error(f"Get accounts error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api.route('/accounts', methods=['POST'])
@require_auth
def add_account():
    """Add a new Instagram account to monitor."""
    try:
        data = request.get_json()
        if not data or 'username' not in data:
            return jsonify({'error': 'Missing username'}), 400
        
        username = data['username']
        
        # Check if account already exists
        existing_account = InstagramAccount.find_by_username(username)
        if existing_account:
            return jsonify({'error': 'Account already exists'}), 400
        
        # Create new account
        account = InstagramAccount.create(
            username=username,
            user_id=current_user.user_id
        )
        
        return jsonify({
            'success': True,
            'account': account.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Add account error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api.route('/accounts/<username>', methods=['DELETE'])
@require_auth
def delete_account(username):
    """Delete an Instagram account."""
    try:
        account = InstagramAccount.find_by_username(username)
        if not account:
            return jsonify({'error': 'Account not found'}), 404
        
        if account.user_id != current_user.user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        account.delete()
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Delete account error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api.route('/accounts/<username>/posts', methods=['GET'])
@require_auth
def get_account_posts(username):
    """Get latest posts from an Instagram account."""
    try:
        account = InstagramAccount.find_by_username(username)
        if not account:
            return jsonify({'error': 'Account not found'}), 404
        
        if account.user_id != current_user.user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get posts since last check
        since_time = request.args.get('since')
        result = account.get_latest_posts(since_time)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        logger.error(f"Get account posts error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Dashboard routes
@api.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get Instagram account statistics for the dashboard."""
    user = get_user()
    accounts = InstagramAccount.find_by_user(user.user_id)
    
    if not accounts:
        return jsonify({
            'stats': [],
            'message': 'No Instagram accounts found'
        }), 200
    
    stats = []
    for account in accounts:
        if not account.active:
            continue
            
        # Get account stats
        crawler = InstagramCrawler(
            session_cookies=account.get_cookies(),
            user_ip=account.user_ip  # Use the user's IP
        )
        
        if not crawler.validate_session():
            stats.append({
                'account_id': account.account_id,
                'username': account.username,
                'status': 'error',
                'error': 'Session expired'
            })
            continue
            
        user_info = crawler.get_user_info(account.username)
        if not user_info.get('success'):
            stats.append({
                'account_id': account.account_id,
                'username': account.username,
                'status': 'error',
                'error': user_info.get('error', 'Failed to get user info')
            })
            continue
            
        # Add account stats
        stats.append({
            'account_id': account.account_id,
            'username': account.username,
            'status': 'active',
            'last_check': account.last_check,
            'follower_count': user_info['user']['follower_count'],
            'following_count': user_info['user']['following_count'],
            'media_count': user_info['user']['media_count'],
            'profile_pic_url': user_info['user']['profile_pic_url']
        })
    
    return jsonify({'stats': stats}), 200

# Monitor routes
@api.route('/monitor/manual-check', methods=['POST'])
@require_auth
def manual_check():
    """Manually check all accounts for new posts."""
    data = request.get_json()
    account_id = data.get('account_id')
    user = AuthController.get_current_user()
    
    if account_id:
        # Check specific account
        account = InstagramAccount.find_by_id(account_id)
        
        if not account:
            return jsonify({'error': 'Account not found'}), 404
            
        result = instagram_monitor.check_now(account_id)
            
        return jsonify({
            'success': result,
            'message': 'Account checked' if result else 'Failed to check account'
        }), 200 if result else 500
    else:
        # Check all accounts
        accounts = InstagramAccount.find_by_user(user.user_id)
        results = []
        
        for account in accounts:
            if account.active:
                success = instagram_monitor.check_now(account.account_id)
                results.append({
                    'account_id': account.account_id,
                    'username': account.username,
                    'success': success
                })
        
        return jsonify({'results': results}), 200

@api.route('/monitor/status', methods=['GET'])
@require_auth
def monitor_status():
    """Get status of the monitoring service."""
    return jsonify({
        'running': instagram_monitor.is_running()
    }), 200

@api.route('/monitor/start', methods=['POST'])
@require_auth
def start_monitor():
    """Start the monitoring service."""
    result = instagram_monitor.start()
    
    return jsonify({
        'success': result,
        'message': 'Monitor started' if result else 'Monitor already running'
    }), 200

@api.route('/monitor/stop', methods=['POST'])
@require_auth
def stop_monitor():
    """Stop the monitoring service."""
    result = instagram_monitor.stop()
    
    return jsonify({
        'success': result,
        'message': 'Monitor stopped' if result else 'Monitor not running'
    }), 200 