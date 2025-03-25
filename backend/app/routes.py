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
        user = AuthController.get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
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
@token_required
def instagram_login(current_user):
    """Login to Instagram and store session cookies."""
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
    result = AuthController.instagram_login(username, password, current_user.user_id)
    
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400

def get_user():
    """Get or create the single user instance."""
    return User.get_or_create()

# Account routes
@api.route('/accounts', methods=['GET'])
@require_auth
def get_accounts():
    """Get all Instagram accounts for current user."""
    try:
        user = AuthController.get_current_user()
        monitor = InstagramMonitor()
        accounts = monitor.get_accounts(user.user_id)
        return jsonify(accounts)
    except Exception as e:
        logger.error(f"Error getting accounts: {str(e)}")
        return jsonify({'error': 'Failed to get accounts'}), 500

@api.route('/accounts', methods=['POST'])
@require_auth
def add_account():
    """Add a new Instagram account."""
    try:
        data = request.get_json()
        if not data or not data.get('username') or not data.get('user_ip'):
            return jsonify({'error': 'Username and user IP are required'}), 400
            
        user = AuthController.get_current_user()
        monitor = InstagramMonitor()
        account = monitor.add_account(user.user_id, data['username'], data['user_ip'])
        return jsonify(account), 201
    except Exception as e:
        logger.error(f"Error adding account: {str(e)}")
        return jsonify({'error': 'Failed to add account'}), 500

@api.route('/accounts/<username>', methods=['DELETE'])
@require_auth
def remove_account(username):
    """Remove an Instagram account."""
    try:
        user = AuthController.get_current_user()
        monitor = InstagramMonitor()
        monitor.remove_account(user.user_id, username)
        return jsonify({'message': 'Account removed successfully'})
    except Exception as e:
        logger.error(f"Error removing account: {str(e)}")
        return jsonify({'error': 'Failed to remove account'}), 500

@api.route('/accounts/<username>/status', methods=['GET'])
@require_auth
def get_account_status(username):
    """Get monitoring status for an account."""
    try:
        user = AuthController.get_current_user()
        monitor = InstagramMonitor()
        status = monitor.get_account_status(user.user_id, username)
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting account status: {str(e)}")
        return jsonify({'error': 'Failed to get account status'}), 500

@api.route('/accounts/<username>/start', methods=['POST'])
@require_auth
def start_monitoring(username):
    """Start monitoring an Instagram account."""
    try:
        user = AuthController.get_current_user()
        monitor = InstagramMonitor()
        monitor.start_monitoring(user.user_id, username)
        return jsonify({'message': 'Monitoring started successfully'})
    except Exception as e:
        logger.error(f"Error starting monitoring: {str(e)}")
        return jsonify({'error': 'Failed to start monitoring'}), 500

@api.route('/accounts/<username>/stop', methods=['POST'])
@require_auth
def stop_monitoring(username):
    """Stop monitoring an Instagram account."""
    try:
        user = AuthController.get_current_user()
        monitor = InstagramMonitor()
        monitor.stop_monitoring(user.user_id, username)
        return jsonify({'message': 'Monitoring stopped successfully'})
    except Exception as e:
        logger.error(f"Error stopping monitoring: {str(e)}")
        return jsonify({'error': 'Failed to stop monitoring'}), 500

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