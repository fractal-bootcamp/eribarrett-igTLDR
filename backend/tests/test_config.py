import os
import requests
from dotenv import load_dotenv
from controllers.instagram_client import InstagramClient

load_dotenv()

def get_public_ip():
    """Get the public IP address."""
    try:
        response = requests.get('https://api.ipify.org?format=json')
        return response.json()['ip']
    except:
        return '127.0.0.1'  # fallback to localhost if can't get IP

# Test Instagram session cookies - only essential cookies
TEST_INSTAGRAM_COOKIES = {
    'sessionid': os.getenv('TEST_INSTAGRAM_SESSIONID'),
    'csrftoken': os.getenv('TEST_INSTAGRAM_CSRFTOKEN')
}

def get_username_from_session():
    """Get username from session cookies."""
    try:
        client = InstagramClient(TEST_INSTAGRAM_COOKIES)
        user_info = client.get_user_info(client.client.user_id)
        if user_info['success']:
            return user_info['user']['username']
    except:
        pass
    return 'test_user'  # fallback username

# Test Instagram account details
TEST_INSTAGRAM_USERNAME = get_username_from_session()
TEST_INSTAGRAM_USER_IP = get_public_ip()  # automatically get IP

# Test data directory
TEST_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_data')

# Test encryption and authentication settings
TEST_SECRET_KEY = 'test-secret-key-for-jwt'
TEST_ENCRYPTION_KEY = 'test-encryption-key-for-data'

class TestingConfig:
    """Test configuration."""
    DATA_DIR = TEST_DATA_DIR
    SECRET_KEY = TEST_SECRET_KEY
    ENCRYPTION_KEY = TEST_ENCRYPTION_KEY 