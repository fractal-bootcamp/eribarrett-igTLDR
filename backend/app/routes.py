from flask import request, jsonify, Blueprint, current_app
import jwt
from functools import wraps
from config import get_config
from models import User, InstagramAccount
from controllers import AuthController
from controllers.instagram_crawler import InstagramCrawler
from controllers.instagram_monitor import instagram_monitor
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
            token = auth_header.split(' ')[1]
            current_user = User.get_by_token(token)
            if not current_user:
                return jsonify({'error': 'Invalid token'}), 401
            return f(current_user, *args, **kwargs)
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
def get_current_user(current_user):
    """Get current user information."""
    return jsonify({
        'id': current_user.user_id,
        'username': current_user.username,
        'email': current_user.email
    })

@api.route('/auth/instagram', methods=['POST'])
def instagram_login():
    """Login with Instagram credentials."""
    try:
        data = request.get_json()
        username = data.get('username')
        user_ip = data.get('user_ip')
        
        if not username or not user_ip:
            return jsonify({'error': 'Username and user IP are required'}), 400
            
        # Create or get user
        user = User.find_by_username(username)
        if not user:
            user = User(username=username)
            user.save()
        
        # Add Instagram account
        account = instagram_monitor.add_account(user.user_id, username, user_ip)
        if not account:
            return jsonify({'error': 'Failed to add Instagram account'}), 500
            
        return jsonify(account), 200
        
    except Exception as e:
        logger.error(f"Instagram login error: {str(e)}")
        return jsonify({'error': str(e)}), 500

def get_user():
    """Get or create the single user instance."""
    return User.get_or_create()

# Account routes
@api.route('/accounts', methods=['GET'])
@require_auth
def get_accounts(current_user):
    """Get all Instagram accounts for the current user."""
    try:
        accounts = instagram_monitor.get_accounts(current_user.user_id)
        return jsonify(accounts), 200
    except Exception as e:
        logger.error(f"Get accounts error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api.route('/accounts', methods=['POST'])
@require_auth
def add_account(current_user):
    """Add a new Instagram account to monitor."""
    try:
        data = request.get_json()
        username = data.get('username')
        user_ip = data.get('user_ip')
        
        if not username or not user_ip:
            return jsonify({'error': 'Username and user IP are required'}), 400
            
        account = instagram_monitor.add_account(current_user.user_id, username, user_ip)
        if not account:
            return jsonify({'error': 'Failed to add Instagram account'}), 500
            
        return jsonify(account), 201
        
    except Exception as e:
        logger.error(f"Add account error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api.route('/accounts/<username>', methods=['DELETE'])
@require_auth
def delete_account(current_user, username):
    """Delete an Instagram account."""
    try:
        if instagram_monitor.remove_account(current_user.user_id, username):
            return '', 204
        return jsonify({'error': 'Account not found'}), 404
    except Exception as e:
        logger.error(f"Delete account error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api.route('/accounts/<username>/posts', methods=['GET'])
@require_auth
def get_latest_posts(current_user, username):
    """Get latest posts from an Instagram account."""
    try:
        account = InstagramAccount.find_by_username(username)
        if not account or account.user_id != current_user.user_id:
            return jsonify({'error': 'Account not found'}), 404
            
        if instagram_monitor.check_now(account.id):
            return jsonify({'status': 'success'}), 200
        return jsonify({'error': 'Failed to check for new posts'}), 500
        
    except Exception as e:
        logger.error(f"Get latest posts error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Dashboard routes
@api.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get Instagram account statistics for the dashboard."""
    user = get_user()
    accounts = instagram_monitor.get_accounts(user.user_id)
    
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
def manual_check(current_user):
    """Manually check all accounts for new posts."""
    data = request.get_json()
    account_id = data.get('account_id')
    
    if account_id:
        # Check specific account
        account = instagram_monitor.get_account(current_user.user_id, account_id)
        
        if not account:
            return jsonify({'error': 'Account not found'}), 404
            
        result = instagram_monitor.check_now(account.account_id)
            
        return jsonify({
            'success': result,
            'message': 'Account checked' if result else 'Failed to check account'
        }), 200 if result else 500
    else:
        # Check all accounts
        accounts = instagram_monitor.get_accounts(current_user.user_id)
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