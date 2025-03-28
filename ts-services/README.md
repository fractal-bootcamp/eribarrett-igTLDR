# InstaTLDR TypeScript Services

TypeScript services layer for processing Instagram data from Python backend.

## Features

- Post scoring and prioritization (high/medium/low)
- Content categorization (Event, Selfie, Food, etc.)
- Top daily posts selection with de-duplication
- OpenAI-powered post summaries with intelligent emoji selection
- Organized data storage with timestamp-based files

## Directory Structure

```
ts-services/
├── data/                     # Data files directory
│   ├── posts/                # Post data storage
│   │   └── daily/            # Daily top posts
│   │       └── latest.json   # Reference to latest posts file
│   └── summaries/            # AI-generated summaries
│       └── latest.json       # Reference to latest summaries file
├── dist/                     # Compiled JavaScript
├── src/                      # TypeScript source code
│   ├── scripts/              # Command line scripts
│   │   ├── generateSummaries.ts  # Generate AI summaries
│   │   ├── topDailyPosts.ts      # Select top posts from feed
│   │   └── ...
│   ├── services/             # Core services
│   │   ├── contentCategorizer.ts # Categorize content
│   │   ├── dataLoader.ts         # Load data from Python backend
│   │   ├── openAiService.ts      # AI summary generation
│   │   ├── postPrioritizer.ts    # Prioritize posts
│   │   ├── postScorer.ts         # Score post importance
│   │   ├── utils.ts              # Shared utility functions
│   │   └── ...
│   └── index.ts              # Main API server
└── ...
```

## Getting Started

### Prerequisites

- Node.js 18+
- Python backend for data collection

### Installation

```bash
# Install dependencies
npm install
```

### Configuration

Create a `.env` file in the root directory:

```
OPENAI_API_KEY=your_openai_api_key
```

### Scripts

```bash
# Build TypeScript
npm run build

# Start API server
npm start

# Get top daily posts
npm run top-daily

# Generate AI summaries for top posts
npm run summarize [count]

# Clean data directories
npm run clean  # Remove all JSON files
npm run clean:keep-latest  # Keep latest.json references
```

## API Endpoints

- `GET /api/feed/scored` - Get scored feed posts
- `GET /api/feed/simple` - Get simplified feed posts
- `GET /api/feed/events` - Get event posts only
- `GET /api/feed/priority/:level` - Get posts by priority level (high/medium/low)
- `GET /api/feed/top-daily` - Get top daily posts with content categories
- `GET /api/feed/summaries` - Get AI-generated summaries for top posts
  - Query params:
    - `count`: Number of summaries to return (default: 5)
    - `detail`: Include original post details (true/false)
    - `cached`: Use cached summaries if available (true/false)
- `POST /api/categorize` - Categorize content by patterns

## Architecture

- **Data Flow**: Python backend → TypeScript services → OpenAI API → Frontend
- **Storage**: Timestamped JSON files with latest.json references
- **Categorization**: Rule-based pattern matching for content types
- **Scoring**: Multi-factor algorithm for post importance
- **Summaries**: OpenAI-generated with weighted emoji selection

## License

This project is private and confidential.