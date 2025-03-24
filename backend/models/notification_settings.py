import os
import json
import uuid
import datetime

SETTINGS_FILE = 'notification_settings.json'

class NotificationSettings:
    """Notification settings model for users."""
    
    def __init__(self, user_id, email_enabled=True, telegram_enabled=False,
                 check_interval=30, summary_length='medium', include_images=True, 
                 settings_id=None, created_at=None, updated_at=None):
        self.settings_id = settings_id or str(uuid.uuid4())
        self.user_id = user_id
        self.email_enabled = email_enabled
        self.telegram_enabled = telegram_enabled
        self.check_interval = check_interval  # in minutes
        self.summary_length = summary_length  # 'short', 'medium', 'long'
        self.include_images = include_images
        self.created_at = created_at or datetime.datetime.utcnow().isoformat()
        self.updated_at = updated_at or self.created_at
    
    @classmethod
    def get_settings(cls):
        """Load all notification settings from the file."""
        if not os.path.exists(SETTINGS_FILE):
            return []
            
        with open(SETTINGS_FILE, 'r') as f:
            try:
                settings_data = json.load(f)
                return [cls(**setting) for setting in settings_data]
            except json.JSONDecodeError:
                return []
    
    @classmethod
    def save_settings(cls, settings_list):
        """Save all notification settings to the file."""
        settings_data = [setting.to_dict() for setting in settings_list]
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings_data, f, indent=2)
    
    @classmethod
    def find_by_user(cls, user_id):
        """Find notification settings for a specific user."""
        settings_list = cls.get_settings()
        for setting in settings_list:
            if setting.user_id == user_id:
                return setting
        
        # Create default settings if not found
        default_settings = cls(user_id=user_id)
        default_settings.save()
        return default_settings
    
    def save(self):
        """Save the notification settings to the database."""
        settings_list = self.get_settings()
        self.updated_at = datetime.datetime.utcnow().isoformat()
        
        # Check if settings already exist
        for i, setting in enumerate(settings_list):
            if setting.user_id == self.user_id:
                # Update existing settings
                settings_list[i] = self
                self.save_settings(settings_list)
                return True
        
        # Add new settings
        settings_list.append(self)
        self.save_settings(settings_list)
        return True
    
    def delete(self):
        """Delete the notification settings from the database."""
        settings_list = self.get_settings()
        settings_list = [setting for setting in settings_list if setting.user_id != self.user_id]
        self.save_settings(settings_list)
        return True
    
    def to_dict(self):
        """Convert notification settings object to dictionary."""
        return {
            'settings_id': self.settings_id,
            'user_id': self.user_id,
            'email_enabled': self.email_enabled,
            'telegram_enabled': self.telegram_enabled,
            'check_interval': self.check_interval,
            'summary_length': self.summary_length,
            'include_images': self.include_images,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        } 