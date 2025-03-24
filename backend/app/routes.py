from flask import request, jsonify, Blueprint
import jwt
from functools import wraps
from config import get_config
from models import User, InstagramAccount, NotificationSettings
from controllers import AuthController, instagram_monitor, InstagramClient

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

# Auth routes
@api.route('/auth/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.get_json()
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
    result = AuthController.register(username, email, password)
    
    if result.get('success'):
        return jsonify(result), 201
    else:
        return jsonify(result), 400

@api.route('/auth/login', methods=['POST'])
def login():
    """Login a user."""
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
    result = AuthController.login(username, password)
    
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 401

@api.route('/auth/instagram', methods=['POST'])
@token_required
def instagram_login(current_user):
    """Login to Instagram and store session cookies."""
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    
    # Check for either username/password or cookie parameters
    cookie_auth = data.get('cookie_auth', False)
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    # If this is a cookie auth request, the sessionid and csrftoken should be provided
    if cookie_auth and (not data.get('sessionid') or not data.get('csrftoken')):
        return jsonify({'success': False, 'error': 'Missing cookie parameters'}), 400
        
    result = AuthController.instagram_login(username, password, current_user.user_id)
    
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 400

# Account routes
@api.route('/accounts', methods=['GET'])
@token_required
def get_accounts(current_user):
    """Get all Instagram accounts for the current user."""
    accounts = InstagramAccount.find_by_user(current_user.user_id)
    
    # Remove sensitive data
    accounts_data = []
    for account in accounts:
        account_data = account.to_dict()
        account_data.pop('encrypted_cookies', None)
        accounts_data.append(account_data)
        
    return jsonify({
        'success': True,
        'accounts': accounts_data
    }), 200

@api.route('/accounts/<account_id>', methods=['GET'])
@token_required
def get_account(current_user, account_id):
    """Get a specific Instagram account."""
    account = InstagramAccount.find_by_id(account_id)
    
    if not account:
        return jsonify({'success': False, 'error': 'Account not found'}), 404
        
    # Check if the account belongs to the current user
    if account.user_id != current_user.user_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    # Remove sensitive data
    account_data = account.to_dict()
    account_data.pop('encrypted_cookies', None)
        
    return jsonify({
        'success': True,
        'account': account_data
    }), 200

@api.route('/accounts/<account_id>', methods=['DELETE'])
@token_required
def delete_account(current_user, account_id):
    """Delete an Instagram account."""
    account = InstagramAccount.find_by_id(account_id)
    
    if not account:
        return jsonify({'success': False, 'error': 'Account not found'}), 404
        
    # Check if the account belongs to the current user
    if account.user_id != current_user.user_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    account.delete()
        
    return jsonify({
        'success': True,
        'message': 'Account deleted'
    }), 200

@api.route('/accounts/<account_id>/check', methods=['POST'])
@token_required
def check_account(current_user, account_id):
    """Check an account for new posts immediately."""
    account = InstagramAccount.find_by_id(account_id)
    
    if not account:
        return jsonify({'success': False, 'error': 'Account not found'}), 404
        
    # Check if the account belongs to the current user
    if account.user_id != current_user.user_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    result = instagram_monitor.check_now(account_id)
        
    return jsonify({
        'success': result,
        'message': 'Account checked' if result else 'Failed to check account'
    }), 200 if result else 500

# Dashboard routes
@api.route('/dashboard/stats', methods=['GET'])
@token_required
def get_dashboard_stats(current_user):
    """Get Instagram account statistics for the dashboard."""
    accounts = InstagramAccount.find_by_user(current_user.user_id)
    
    if not accounts:
        return jsonify({
            'success': True,
            'stats': [],
            'message': 'No Instagram accounts found'
        }), 200
    
    stats = []
    for account in accounts:
        if not account.active:
            continue
            
        # Get account stats
        client = InstagramClient(account.get_cookies())
        if not client.validate_session():
            stats.append({
                'account_id': account.account_id,
                'username': account.username,
                'status': 'error',
                'error': 'Session expired'
            })
            continue
            
        user_info = client.get_user_info(account.username)
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
    
    return jsonify({
        'success': True,
        'stats': stats
    }), 200

# Preferences routes
@api.route('/preferences', methods=['GET'])
@token_required
def get_preferences(current_user):
    """Get notification preferences for the current user."""
    settings = NotificationSettings.find_by_user(current_user.user_id)
    
    return jsonify({
        'success': True,
        'preferences': {
            'email_enabled': settings.email_enabled,
            'telegram_enabled': settings.telegram_enabled,
            'check_interval': settings.check_interval,
            'summary_length': settings.summary_length,
            'include_images': settings.include_images
        }
    }), 200

@api.route('/preferences', methods=['POST'])
@token_required
def update_preferences(current_user):
    """Update notification preferences."""
    data = request.get_json()
    settings = NotificationSettings.find_by_user(current_user.user_id)
    
    # Update settings with provided data
    if 'email_enabled' in data:
        settings.email_enabled = bool(data.get('email_enabled'))
    
    if 'telegram_enabled' in data:
        settings.telegram_enabled = bool(data.get('telegram_enabled'))
    
    if 'check_interval' in data:
        settings.check_interval = int(data.get('check_interval'))
    
    if 'summary_length' in data:
        summary_length = data.get('summary_length')
        if summary_length in ['short', 'medium', 'long']:
            settings.summary_length = summary_length
    
    if 'include_images' in data:
        settings.include_images = bool(data.get('include_images'))
    
    settings.save()
    
    return jsonify({
        'success': True,
        'preferences': {
            'email_enabled': settings.email_enabled,
            'telegram_enabled': settings.telegram_enabled,
            'check_interval': settings.check_interval,
            'summary_length': settings.summary_length,
            'include_images': settings.include_images
        }
    }), 200

# Monitor routes
@api.route('/monitor/manual-check', methods=['POST'])
@token_required
def manual_check(current_user):
    """Manually check all accounts for new posts."""
    data = request.get_json()
    account_id = data.get('account_id')
    
    if account_id:
        # Check specific account
        account = InstagramAccount.find_by_id(account_id)
        
        if not account:
            return jsonify({'success': False, 'error': 'Account not found'}), 404
            
        # Check if the account belongs to the current user
        if account.user_id != current_user.user_id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
            
        result = instagram_monitor.check_now(account_id)
            
        return jsonify({
            'success': result,
            'message': 'Account checked' if result else 'Failed to check account'
        }), 200 if result else 500
    else:
        # Check all accounts
        accounts = InstagramAccount.find_by_user(current_user.user_id)
        results = []
        
        for account in accounts:
            if account.active:
                success = instagram_monitor.check_now(account.account_id)
                results.append({
                    'account_id': account.account_id,
                    'username': account.username,
                    'success': success
                })
        
        return jsonify({
            'success': True,
            'results': results
        }), 200

@api.route('/monitor/status', methods=['GET'])
@token_required
def monitor_status(current_user):
    """Get status of the monitoring service."""
    return jsonify({
        'success': True,
        'running': instagram_monitor.is_running()
    }), 200

@api.route('/monitor/start', methods=['POST'])
@token_required
def start_monitor(current_user):
    """Start the monitoring service."""
    result = instagram_monitor.start()
    
    return jsonify({
        'success': result,
        'message': 'Monitor started' if result else 'Monitor already running'
    }), 200

@api.route('/monitor/stop', methods=['POST'])
@token_required
def stop_monitor(current_user):
    """Stop the monitoring service."""
    result = instagram_monitor.stop()
    
    return jsonify({
        'success': result,
        'message': 'Monitor stopped' if result else 'Monitor not running'
    }), 200 