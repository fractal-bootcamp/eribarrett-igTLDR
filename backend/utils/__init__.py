import os
import json
import base64
import smtplib
import telegram_send
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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

def send_email_notification(to_email, subject, content):
    """Send email notification."""
    try:
        msg = MIMEMultipart()
        msg['From'] = config.SMTP_USERNAME
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(content, 'html'))
        
        server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT)
        server.starttls()
        server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email sending error: {str(e)}")
        return False

def send_telegram_notification(message):
    """Send Telegram notification."""
    try:
        # Configure telegram-send with environment variables
        # This is a simple implementation; in practice, you might want to use python-telegram-bot directly
        telegram_config = {
            'token': config.TELEGRAM_BOT_TOKEN,
            'chat_id': config.TELEGRAM_CHAT_ID
        }
        
        with open('telegram-send.conf', 'w') as f:
            json.dump(telegram_config, f)
            
        telegram_send.send(messages=[message], conf='telegram-send.conf')
        
        # Clean up
        if os.path.exists('telegram-send.conf'):
            os.remove('telegram-send.conf')
            
        return True
    except Exception as e:
        print(f"Telegram sending error: {str(e)}")
        return False 