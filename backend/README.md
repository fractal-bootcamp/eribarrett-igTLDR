# Instagram Cookie Validator

A simple tool to validate Instagram cookies without needing to run a full application server.

## What This Tool Does

This tool allows you to:
1. Validate Instagram cookies obtained from your browser
2. Check if they provide successful authentication to Instagram
3. View basic profile information when available
4. Save cookie information to a JSON file for future use

## Getting Started

### Prerequisites
- Python 3.6 or higher
- Required packages: `requests`

### Installation
1. Clone this repository or download the `insta_setup.py` file
2. Install required packages:
   ```bash
   pip install requests
   ```

## Usage

Run the script directly:
```bash
python insta_setup.py
```

### What You'll Need
- Your Instagram username
- Browser cookies from an authenticated Instagram session:
  - `sessionid` (required)
  - `csrftoken` (optional but recommended)

### Getting Instagram Cookies

1. **Log in to Instagram in your web browser**
   - Go to https://www.instagram.com and log in

2. **Access your browser cookies**
   - Open Developer Tools (F12 or right-click → Inspect)
   - Navigate to:
     - **Chrome/Edge**: Application tab → Cookies → instagram.com
     - **Firefox**: Storage tab → Cookies → instagram.com
     - **Safari**: Storage tab → Cookies

3. **Find these specific cookies**
   - `sessionid` - Most important cookie, represents your authenticated session
   - `csrftoken` - Secondary cookie, provides CSRF protection

## How It Works

The script makes a direct API request to Instagram using your cookies to validate authentication. No complex setup is required - it simply tests if your cookies allow access to your Instagram account.

## Cookie Security and Expiration

- **Security**: Cookies provide direct access to your Instagram account. Keep them secure.
- **Expiration**: Instagram cookies typically expire after a few weeks.
- **Refreshing**: When cookies expire, simply log in to Instagram again and get fresh cookies.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- This tool is intended for educational purposes only
- Use responsibly and respect Instagram's terms of service 