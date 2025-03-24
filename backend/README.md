# InstaTLDR Backend

Backend service for Instagram monitoring with cookie-based authentication, built with Flask and Python.

## Features

- Cookie-based Instagram authentication (no password storage)
- Encrypted storage of Instagram session cookies
- Periodic monitoring of Instagram posts
- Post summarization
- Email and Telegram notifications
- Rate limiting and security measures
- REST API for frontend and CLI

## Setup

### Prerequisites

- Python 3.10+
- Miniconda (recommended)

### Installation

1. Create a Conda environment:

```bash
conda create -n instatldr python=3.10 -y
conda activate instatldr
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment variables:

Copy `.env.example` to `.env` and edit it with your settings:

```bash
cp .env.example .env
nano .env
```

### Running the Backend

#### Development mode:

```bash
flask run --debug
```

#### Production mode:

```bash
gunicorn wsgi:app
```

## CLI Usage

The CLI allows you to manage users and Instagram accounts directly from the command line.

### Register a new user

```bash
python cli.py register --username myuser --email user@example.com
```

### Login a user

```bash
python cli.py login --username myuser
```

### Add an Instagram account

```bash
python cli.py add-instagram --user-id USER_ID --username INSTAGRAM_USERNAME
```

### List Instagram accounts

```bash
python cli.py list-accounts --user-id USER_ID
```

### Delete an Instagram account

```bash
python cli.py delete-account --account-id ACCOUNT_ID
```

## API Documentation

The API provides endpoints for the frontend and other clients to interact with the backend.

### Authentication

- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login a user
- `POST /api/auth/instagram` - Add an Instagram account

### Accounts

- `GET /api/accounts` - Get all Instagram accounts for the current user
- `GET /api/accounts/{account_id}` - Get a specific Instagram account
- `DELETE /api/accounts/{account_id}` - Delete an Instagram account
- `POST /api/accounts/{account_id}/check` - Check an account for new posts immediately

### Settings

- `GET /api/settings` - Get notification settings for the current user
- `PUT /api/settings` - Update notification settings

### Monitor

- `GET /api/monitor/status` - Get status of the monitoring service
- `POST /api/monitor/start` - Start the monitoring service
- `POST /api/monitor/stop` - Stop the monitoring service 