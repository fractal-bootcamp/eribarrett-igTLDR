# InstaTLDR Tests

This directory contains test suites for the InstaTLDR backend. The tests are organized into unit tests and integration tests.

## Structure

```
tests/
├── __init__.py          # Test package initialization
├── conftest.py          # Pytest configuration and fixtures
├── mocks.py             # Mock classes for Instagram API
├── mocks_utils.py       # Mock utility functions for notifications
├── unit/                # Unit tests
│   ├── test_utils.py    # Tests for encryption and email utilities
│   ├── test_user_model.py # Tests for User model
│   └── test_auth_controller.py # Tests for auth controller
└── integration/         # Integration tests
    ├── test_auth_api.py # Tests for auth API endpoints
    ├── test_dashboard_api.py # Tests for dashboard API
    ├── test_preferences_api.py # Tests for preferences API
    └── test_monitor_api.py # Tests for monitoring API
```

## Running Tests

### Prerequisites

Make sure you have installed all required dependencies:

```bash
pip install pytest pytest-cov
```

### Basic Test Execution

From the backend directory, run:

```bash
./run_tests.sh
```

This will run all tests with verbose output.

### Running Specific Tests

To run only unit tests:

```bash
./run_tests.sh tests/unit
```

To run only integration tests:

```bash
./run_tests.sh tests/integration
```

To run a specific test file:

```bash
./run_tests.sh tests/unit/test_utils.py
```

To run a specific test function:

```bash
./run_tests.sh tests/unit/test_utils.py::TestEncryption::test_encrypt_decrypt_cycle
```

### Running with Coverage

To run tests with coverage information:

```bash
python -m pytest --cov=. tests/
```

To generate an HTML coverage report:

```bash
python -m pytest --cov=. --cov-report=html tests/
```

This will create a `htmlcov` directory with the coverage report.

## Understanding the Tests

### Unit Tests

Unit tests focus on testing individual components in isolation, mocking out dependencies:

- **test_utils.py**: Tests encryption/decryption and email formatting functions
- **test_user_model.py**: Tests User model CRUD operations and token management
- **test_auth_controller.py**: Tests authentication controller

### Integration Tests

Integration tests verify that different components work together correctly:

- **test_auth_api.py**: Tests authentication API endpoints
- **test_dashboard_api.py**: Tests dashboard statistics API endpoints
- **test_preferences_api.py**: Tests user preferences API endpoints
- **test_monitor_api.py**: Tests monitoring API endpoints

### Mocks

To avoid making real API calls during testing, mock classes are provided:

- **mocks.py**: Contains mock implementations of Instagram API client
- **mocks_utils.py**: Contains mock email and Telegram notification functions

### Test Fixtures

Common test fixtures are defined in `conftest.py`, including:

- **app**: Flask test application
- **client**: Flask test client
- **test_user**: Test user for authentication
- **test_token**: Authentication token
- **test_account**: Test Instagram account
- **test_settings**: Test notification settings
- **auth_headers**: Authentication headers for API calls

## Best Practices

1. **Keep tests independent**: Each test should be able to run independently.
2. **Use fixtures**: Reuse common setup via fixtures.
3. **Mock external dependencies**: Avoid making actual API calls.
4. **Test both success and failure paths**: Cover both valid and invalid scenarios.
5. **Maintain test isolation**: Use temporary files for tests instead of actual database files.

## Troubleshooting

If you encounter issues:

1. Ensure your environment variables are set correctly
2. Check that you're using the correct Python environment
3. Verify that all dependencies are installed
4. Run tests with `-v` flag for more detailed output 