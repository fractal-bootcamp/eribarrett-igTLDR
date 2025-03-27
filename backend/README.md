# InstaTLDR Backend

A robust Instagram data collection system using the Instagrapi library in conjunction with up-to-date reverse-engineered API endpoints.

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

3. Session will be saved for future use, avoiding multiple login instances


## Collecting Feed Data

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

You can get your own close friends list to use as a filter for your daily TLDR:

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

## Collecting Feed Posts Directly

You can collect your Instagram feed posts directly using Instagram's private API endpoints:

```bash
python scripts/collect_direct_feed.py
```

When running the script, you'll be presented with an interactive menu to select an operation mode:

- **<span style="color:green">• Safe Mode</span>** - Slower collection with better safety (default, recommended)
- **<span style="color:blue">• Ultra-Safe Mode</span>** - Very slow collection with maximum safety
- **<span style="color:red">• Standard Mode</span>** - Faster collection with moderate safety (for burner accounts only)
- **<span style="color:gray">• Custom Mode</span>** - Manually set delay and batch parameters

Simply use the ↑ and ↓ arrows to navigate, then press Enter to select.

Alternatively, you can specify a mode directly using command-line options:

Options:
- `-n`, `--num-posts`: Maximum number of posts to collect (default: 50)
- `--min-delay`: Minimum delay between requests in seconds (default: 3)
- `--max-delay`: Maximum delay between requests in seconds (default: 10)
- `--output-dir`: Directory to save feed posts (default: data/direct_feed)
- `--batch-size`: Number of posts per batch/request (default: 10)
- `--safe-mode`: Enable safe mode with longer delays and smaller batches
- `--ultra-safe-mode`: Enable ultra-safe mode that mimics natural user behavior
- `--simulate-browsing`: Simulate realistic browsing with random pauses
- `--max-posts-per-file`: Maximum number of posts to store in a single JSON file (default: 500)

Examples:
```bash
# Collect with interactive menu selection (recommended)
python scripts/collect_direct_feed.py

# Specify mode directly: collect 30 posts with safe mode
python scripts/collect_direct_feed.py --safe-mode -n 30

# Specify mode directly: use ultra-safe mode
python scripts/collect_direct_feed.py --ultra-safe-mode -n 20

# Specify mode directly: custom settings
python scripts/collect_direct_feed.py --min-delay 10 --max-delay 30 --batch-size 5 --simulate-browsing
```

This approach:
- Bypasses instagrapi's high-level methods
- Directly uses Instagram's private API endpoints
- Provides more detailed post data
- Includes all media types (photos, videos, albums, etc.)
- Handles pagination to collect multiple batches of posts
- Saves data with the logged-in username in the filename
- Appends posts to the same file during a session (until max limit)

⚠️ **Safety Recommendations**:
- Use `--ultra-safe-mode` when account safety is critical - this mode:
  - Uses very long delays (15-45 seconds between requests)
  - Uses tiny batch sizes (only 3 posts per batch)
  - Simulates realistic human browsing patterns
  - Adds random pauses that mimic reading and engagement
  - Can run all day in the background like a real user session
- Use `--safe-mode` for more conservative settings but faster collection
- Keep collection sessions short (20-30 posts recommended)
- Space out your collection sessions by several hours
- Avoid collecting large volumes of data in a short time period

The collected data is saved to JSON files in the specified output directory with the following naming pattern:
`{username}_feed_posts_{session_id}_{timestamp}.json`

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
