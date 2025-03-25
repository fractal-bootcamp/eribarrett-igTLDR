class InstagramAuthError(Exception):
    """Base exception for Instagram authentication errors."""
    pass

class LoginError(InstagramAuthError):
    """Raised when login fails."""
    pass

class TwoFactorRequiredError(InstagramAuthError):
    """Raised when 2FA is required."""
    pass

class SessionError(InstagramAuthError):
    """Raised when there are issues with session management."""
    pass

class InvalidCredentialsError(InstagramAuthError):
    """Raised when credentials are invalid."""
    pass
