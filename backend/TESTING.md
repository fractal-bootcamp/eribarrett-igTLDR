# Testing with Instagram Credentials

This guide explains how to test the InstaTLDR application with your own Instagram credentials.

## Setup

1. Make sure you have installed all the required dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your environment variables in the `.env` file. The following variables are required:
```
FLASK_ENV=development
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key
JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_TOKEN_EXPIRES=86400
```

3. Start the Flask application:
```bash
export FLASK_APP=app
export FLASK_ENV=development
python -m flask run --host=0.0.0.0 --port=5000
```

## Testing with the Script

We've provided a test script `test_instagram.py` to help you test the application with your Instagram credentials. The script allows you to:

1. Register a new user account
2. Login with an existing account
3. Add an Instagram account using username/password
4. Add an Instagram account using browser cookies
5. List all your Instagram accounts

### Using Username/Password

This method uses Instagram's API directly for authentication:

```bash
python test_instagram.py
```

Follow the prompts to register/login and then add your Instagram credentials.

### Using Browser Cookies (Recommended)

This method is more reliable as it bypasses potential Instagram API limitations:

1. Login to Instagram in your web browser
2. Use browser developer tools to get your cookies:
   - Open Developer Tools (F12 or right-click → Inspect)
   - Go to Application tab → Cookies → instagram.com
   - Find and copy the values for `sessionid` and `csrftoken`

3. Run the test script and choose the "Add Instagram account (with cookies)" option:
```bash
python test_instagram.py
```

## Manual Testing with API Endpoints

If you prefer to test manually using API calls, here are the key endpoints:

### Authentication

- Register: `POST /api/auth/register`
  ```json
  {
    "email": "your-email@example.com",
    "password": "your-password",
    "name": "Your Name"
  }
  ```

- Login: `POST /api/auth/login`
  ```json
  {
    "email": "your-email@example.com",
    "password": "your-password"
  }
  ```

### Instagram Accounts

- Add Account: `POST /api/instagram/accounts`
  ```json
  {
    "username": "your_instagram_username",
    "password": "your_instagram_password",
    "via_browser": false
  }
  ```

- Or with cookies:
  ```json
  {
    "username": "your_instagram_username",
    "cookies": {
      "sessionid": "your-session-id",
      "csrftoken": "your-csrf-token"
    },
    "via_browser": true
  }
  ```

- List Accounts: `GET /api/instagram/accounts`

- Check Account: `POST /api/monitor/manual-check`
  ```json
  {
    "account_id": "your-account-id" 
  }
  ```

All endpoints except registration and login require an Authorization header:
```
Authorization: Bearer your-jwt-token
```

## Troubleshooting

- **Login Failures**: Instagram may block login attempts. Using cookies is often more reliable.
- **Rate Limiting**: Instagram might rate-limit frequent requests. The application has built-in rate limiting to help mitigate this.
- **Session Expiration**: Instagram sessions expire. You may need to refresh your cookies periodically.

## Security Note

Your Instagram credentials are encrypted before being stored in the database. The encryption key is defined in your `.env` file. 