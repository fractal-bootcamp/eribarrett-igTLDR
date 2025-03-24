# Instagram Cookie Authentication

This guide explains how to test Instagram connectivity using browser cookies, with no need to run the full InstaTLDR application.

## What You Need

To authenticate with Instagram, you'll need:
- Your Instagram username
- Browser cookies from an authenticated Instagram session

## Getting Instagram Cookies

Follow these steps to obtain your Instagram cookies:

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

4. **Copy the values**
   - Double-click the Value column for each cookie
   - Copy the full text (it may be quite long)

## Testing Instagram Cookies

We've provided a simple standalone script to test your Instagram cookies without needing to run the full application:

```bash
python insta_setup.py
```

This script will:
1. Ask for your Instagram username
2. Ask for your sessionid and csrftoken cookies
3. Test if the cookies are valid by making a direct request to Instagram
4. Display your basic profile information if successful
5. Save the cookies to a JSON file for future reference

## Cookie Security and Expiration

- **Security**: Cookies provide direct access to your Instagram account. Keep them secure.
- **Expiration**: Instagram cookies typically expire after a few weeks.
- **Refreshing**: When cookies expire, simply log in to Instagram again and get fresh cookies.

## What's Next?

Once you've verified your cookies work with `insta_setup.py`, you can:

1. Use the saved cookie JSON file as a reference
2. See your basic profile information
3. Build applications that interact with Instagram using these cookies

This standalone approach lets you test Instagram connectivity without needing to run the full InstaTLDR application with Flask.

## Troubleshooting

If your cookies don't work:
- Make sure you're still logged in to Instagram in your browser
- Try logging out and back in to get fresh cookies
- Check if you've copied the complete cookie values 