# InstaTLDR Backend

A robust Instagram data collection system using the Instagrapi library.

## Setup

1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your Instagram credentials:
   ```
   IG_USERNAME=your_username
   IG_PASSWORD=your_password
   ```

## Authentication

The system uses a secure authentication system that saves the session to avoid repeated logins:

1. Login using username and password from `.env`:
   ```bash
   python main.py
   ```

2. If 2FA is enabled, you'll be prompted to enter the code

3. Session will be saved for future use

## Collecting Feed Data

> Note: Feed collection is currently not working reliably due to Instagram API limitations.

To collect your Instagram feed data:

```bash
python scripts/collect_feed.py
```

This will:
- Use your saved session to access Instagram
- Collect posts from your feed
- Save them to `data/feed/` as JSON files
- Automatically handle rate limiting and errors
- Continue until you press Ctrl+C to stop

## Collecting User Media

You can collect posts from specific Instagram users:

```bash
python scripts/collect_user_media.py username1 username2 username3
```

Options:
- `-f`, `--file`: Read usernames from a file (one per line)
- `-n`, `--num-posts`: Number of posts to collect per user (default: 20)
- `--min-delay`: Minimum delay between requests in seconds (default: 3)
- `--max-delay`: Maximum delay between requests in seconds (default: 10)

Example with file input:
```bash
python scripts/collect_user_media.py -f usernames.txt -n 50
```

Data will be saved to:
- `data/userMedia/{username}/posts_{timestamp}.json`

## Getting Close Friends List

You can get your own close friends list (not available for other users):

```bash
python scripts/get_close_friends.py
```

Options:
- `-f`, `--format`: Output format (table, basic, json, csv)
- `-o`, `--output`: Output file path to save results
- `--min-delay`: Minimum delay between requests in seconds (default: 3)
- `--max-delay`: Maximum delay between requests in seconds (default: 10)

Examples:
```bash
# Get your close friends with table output (default)
python scripts/get_close_friends.py

# Get your close friends with simple output
python scripts/get_close_friends.py -f basic

# Save your close friends to a JSON file
python scripts/get_close_friends.py -o friends.json

# Save your close friends to a CSV file
python scripts/get_close_friends.py -f csv -o friends.csv
```

This will:
- Fetch the close friends list for your logged-in account
- Display the list in the CLI with selected format
- Save the data to the specified output file (if provided)
- Default data is also saved to `data/userMedia/{your_username}/close_friends_{timestamp}.json`

Note: Close friends is a private list and can only be accessed for your own account when logged in. You cannot view other users' close friends lists.

The collected data includes:
- Username and full name
- User ID
- Profile picture URL
- Verification status
- Private account status

## Features

- Secure authentication with session storage
- Robust error handling and rate limiting
- Random delays between requests to mimic human behavior
- Graceful termination with Ctrl+C
- Structured JSON output

## Data Structure

The collected posts are saved in JSON files with the following structure:

```json
{
  "post_id": "123456789",
  "code": "ABC123",
  "user": {
    "username": "example_user",
    "full_name": "Example User",
    "user_id": "1234567"
  },
  "caption": "Post caption text",
  "likes_count": 100,
  "media_type": "image",
  "media_urls": ["https://example.com/media.jpg"],
  "taken_at": "2024-03-25T12:00:00",
  "timestamp": "2024-03-25T12:05:00"
}
```

## Project Structure

```
instagram_data_collector/
├── config/           # Configuration settings
├── core/            # Core functionality
├── data/            # Data models and processing
├── services/        # Business logic services
└── main.py          # Application entry point
```

## Development

[Development guidelines will be added as the implementation progresses]

## License

[License information to be added]
