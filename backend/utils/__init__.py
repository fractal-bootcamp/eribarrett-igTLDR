import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from config import get_config

config = get_config()

def get_encryption_key():
    """Generate a Fernet key from the environment variable."""
    password = config.ENCRYPTION_KEY.encode()
    salt = b'instatldr_salt'  # Fixed salt for consistency
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return key

def encrypt_data(data):
    """Encrypt data using Fernet symmetric encryption."""
    if not data:
        return None
    
    key = get_encryption_key()
    f = Fernet(key)
    json_data = json.dumps(data)
    encrypted_data = f.encrypt(json_data.encode())
    return encrypted_data.decode()

def decrypt_data(encrypted_data):
    """Decrypt data using Fernet symmetric encryption."""
    if not encrypted_data:
        return None
    
    key = get_encryption_key()
    f = Fernet(key)
    decrypted_data = f.decrypt(encrypted_data.encode())
    return json.loads(decrypted_data.decode()) 