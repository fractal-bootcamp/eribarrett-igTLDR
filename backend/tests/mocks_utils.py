"""
Mock utility functions for testing notification functionality without sending real emails or Telegram messages.
"""

# Store sent messages for verification in tests
sent_emails = []
sent_telegrams = []

def reset_mocks():
    """Reset all mock message stores."""
    sent_emails.clear()
    sent_telegrams.clear()

def mock_send_email_notification(to_email, subject, content, image_url=None):
    """Mock email sending that just stores the email for verification."""
    sent_emails.append({
        'to': to_email,
        'subject': subject,
        'content': content,
        'image_url': image_url
    })
    return True

def mock_send_telegram_notification(message, image_url=None):
    """Mock Telegram message sending that just stores the message for verification."""
    sent_telegrams.append({
        'message': message,
        'image_url': image_url
    })
    return True 