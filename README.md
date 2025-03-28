# InstaTLDR 

InstaTLDR is a comprehensive Instagram analytics tool that collects, processes, and summarizes your Instagram feed, highlighting the most important content through AI-powered summaries.

## Features

- **Instagram Feed Collection**: Automatically collect your Instagram feed data
- **Content Scoring & Prioritization**: Identify high-priority content
- **AI-Powered Summaries**: Generate human-readable summaries of top posts
- **Event Detection**: Identify and extract events from your feed
- **Calendar Integration**: Add events to your calendar
- **Beautiful Web Interface**: Clean, modern design to view your feed summaries

## System Architecture

```
┌─────────────┐    ┌───────────────┐    ┌─────────────┐
│             │    │               │    │             │
│  Python     │    │  TypeScript   │    │  Next.js    │
│  Backend    │──▶ │  Services     │──▶ │  Frontend   │
│             │    │               │    │             │
└─────────────┘    └───────────────┘    └─────────────┘
  Data Collection    Data Processing      User Interface
```

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 14+
- npm or yarn
- Instagram account cookies

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/instaTLDR.git
cd instaTLDR
```

2. Set up the environment:

```bash
# Make the CLI executable
chmod +x instatldr.py

# Set up the environment (installs all dependencies)
./instatldr.py setup
```

3. Check your environment:

```bash
./instatldr.py check
```

### Usage

#### Using the CLI

InstaTLDR comes with a convenient CLI tool that helps you manage all aspects of the application.

```bash
# Collect your Instagram feed
./instatldr.py collect direct-feed

# Process the collected data
./instatldr.py process

# Start the frontend to view your summaries
./instatldr.py frontend

# Start all services at once
./instatldr.py start all

# Check the status of services
./instatldr.py status

# Stop all services
./instatldr.py stop all
```

#### Manual Installation

If you prefer to set up components manually:

1. Set up the Python backend:

```bash
cd backend
pip install -r requirements.txt
python main.py
```

2. Set up TypeScript services:

```bash
cd ts-services
npm install
npm start
```

3. Set up the frontend:

```bash
cd frontend
npm install
npm run dev
```

## CLI Commands

```
instatldr.py <command> [options]
```

Available commands:

- `start [service]`: Start services (all, backend, ts-services, frontend)
- `stop [service]`: Stop services (all, backend, ts-services, frontend)
- `collect <data_type>`: Collect Instagram data (direct-feed, user-media)
- `process`: Process collected data and generate summaries
- `frontend`: Start the frontend server
- `check`: Check environment for dependencies
- `setup`: Set up the environment by installing dependencies
- `status`: Check the status of all services

## Components

### Python Backend

- Handles Instagram API authentication
- Collects feed data and user media
- Stores raw data in the data directory

### TypeScript Services

- Scores and prioritizes content
- Categorizes posts by content type
- Generates OpenAI-powered summaries
- Provides an API for the frontend

### Next.js Frontend

- Displays daily summaries of top content
- Shows calendar with detected events
- Provides interface for managing Instagram session

## Development

### Directory Structure

```
instaTLDR/
├── backend/                  # Python backend for data collection
│   ├── scripts/              # Collection scripts
│   ├── services/             # Instagram API services
│   └── requirements.txt      # Python dependencies
├── ts-services/              # TypeScript processing services
│   ├── src/                  # Source code
│   │   ├── services/         # Core services
│   │   └── scripts/          # Processing scripts
│   └── package.json          # Node.js dependencies
├── frontend/                 # Next.js frontend
│   ├── app/                  # Next.js app
│   ├── components/           # React components
│   └── lib/                  # Utility functions
└── instatldr.py              # CLI wrapper
```

## License

This project is private and confidential.

## Contributing

For internal contributors only. Please follow the established code style and commit message conventions.