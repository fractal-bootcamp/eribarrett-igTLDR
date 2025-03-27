# InstaTLDR TypeScript Services

This package provides TypeScript services that process Instagram data collected by the Python backend.

## Architecture

The project follows a clean separation of concerns:
- **Python backend**: Responsible for collecting data from Instagram API (in `/backend`)
- **TypeScript services**: Responsible for processing, scoring, and exposing data via APIs (this package)

## Setup

```bash
# Install dependencies
bun install

# Build the project
bun run build
```

## Available Scripts

- `bun run build` - Build the TypeScript code
- `bun run start` - Start the API server
- `bun run dev` - Start the API server in development mode with auto-reload
- `bun run score` - Run the post scorer on the latest feed data (CLI output)
- `bun run test:scorer` - Test the post scorer with sample data

## API Endpoints

- `GET /api/feed/scored` - Get all posts scored and sorted by relevance
- `GET /api/feed/events` - Get posts with event indicators scored and sorted by relevance

## Data Flow

1. Python scripts collect data from Instagram and save JSON files in `/backend/data/`
2. TypeScript services read these JSON files
3. Posts are processed through the scoring algorithm
4. Scored data is exposed via REST APIs

## PostScorer

The core of the service is the `PostScorer` class which:
- Analyzes posts for event indicators using regex patterns
- Scores posts based on various signals:
  - User signals (close friend status, verification)
  - Content signals (caption quality, event indicators)
  - Engagement metrics
  - Recency
- Returns a final score and component scores for each post

## Using with the Python Backend

1. First run the Python script to collect Instagram data:
   ```bash
   cd ../backend
   python scripts/collect_direct_feed.py
   ```

2. Then use the TypeScript services to process and score the collected data:
   ```bash
   cd ../ts-services
   bun run score      # to see scores in terminal
   # or
   bun run dev        # to start the API server
   ```

3. Access the scored feed via the API endpoints:
   - http://localhost:3001/api/feed/scored
   - http://localhost:3001/api/feed/events